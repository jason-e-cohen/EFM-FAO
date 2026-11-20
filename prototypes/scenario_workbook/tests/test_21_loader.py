"""Test 21 [v0.6.3, BM-1, BM-2, BM-4, BM-5, BM-6] (Review_Phase2_2_Plan.md section 4, task 1): the loader.

score.percentile_targets: a t outside the bands is rejected; q outside (0, 1) or with three or more decimals is
rejected; the legacy score.median_thresholds loads as {q: 0.5, t} and median_thresholds stays available as the derived
list of q = 0.5 thresholds. ntr_goal_basis all_jd without continuing_ntr_usd is rejected. tuition_by_year_usd takes
precedence over tuition_increase_by_year and, for 200 random bases, round_to(base x (1 + implied), 50) returns the
dollar figure exactly. protect_segment above_floor and pool_ytd_as_of load; reproduce mode drops tuition_by_year_usd.
"""
import copy
import datetime
import os

import numpy as np
import pytest
import yaml

from sw import config
from sw.config import ConfigError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def raw():
    with open(os.path.join(ROOT, "config", "synthetic.yaml")) as f:
        return yaml.safe_load(f)


def _with(raw, **over):
    r = copy.deepcopy(raw)
    for k, v in over.items():
        if k == "score":
            r["score"].update(v)
        else:
            r[k] = v
    return r


def _targets(*pairs):
    return {"percentile_targets": [{"q": q, "t": t} for q, t in pairs]}


def test_percentile_targets_load(raw):
    cfg = config.validate(raw)
    pts = cfg["score"]["percentile_targets"]
    assert [(p["q"], p["t"]) for p in pts] == [(0.5, 166), (0.5, 165), (0.25, 161), (0.10, 154)]
    assert cfg["score"]["median_thresholds"] == [166, 165]
    # idempotent: a validated config (both keys present and agreeing) validates again
    again = config.validate({k: v for k, v in cfg.items() if not k.startswith("_")})
    assert again["score"]["percentile_targets"] == pts and again["score"]["median_thresholds"] == [166, 165]


@pytest.mark.parametrize("t", [163, 160.5, 171, -1])
def test_t_outside_the_bands_rejected(raw, t):
    sc = {k: v for k, v in raw["score"].items() if k != "percentile_targets"} | _targets((0.5, 166), (0.25, t))
    r = copy.deepcopy(raw)
    r["score"] = sc
    with pytest.raises(ConfigError, match="band lower bound"):
        config.validate(r)


@pytest.mark.parametrize("q", [0.0, 1.0, 1.2, -0.1, 0.125, 0.333, 0.001])
def test_q_outside_the_unit_interval_or_three_decimals_rejected(raw, q):
    r = copy.deepcopy(raw)
    r["score"].update(_targets((0.5, 166), (q, 158)))
    with pytest.raises(ConfigError, match="strictly between|more than two decimals"):
        config.validate(r)


@pytest.mark.parametrize("q", [0.01, 0.1, 0.25, 0.33, 0.75, 0.99])
def test_two_decimal_q_accepted(raw, q):
    r = copy.deepcopy(raw)
    r["score"].update(_targets((0.5, 166), (q, 158)))
    assert config.validate(r)["score"]["percentile_targets"][1]["q"] == q


def test_legacy_median_thresholds_load_as_q_half(raw):
    r = copy.deepcopy(raw)
    del r["score"]["percentile_targets"]
    r["score"]["median_thresholds"] = [166, 165]
    cfg = config.validate(r)
    assert cfg["score"]["percentile_targets"] == [{"q": 0.5, "t": 166}, {"q": 0.5, "t": 165}]
    assert cfg["score"]["median_thresholds"] == [166, 165]


def test_legacy_and_targets_must_agree_and_a_median_is_required(raw):
    r = copy.deepcopy(raw)
    r["score"]["median_thresholds"] = [165]
    with pytest.raises(ConfigError, match="disagree"):
        config.validate(r)
    r = copy.deepcopy(raw)
    r["score"].update(_targets((0.25, 161)))
    with pytest.raises(ConfigError, match="q = 0.5"):
        config.validate(r)
    r = copy.deepcopy(raw)
    del r["score"]["percentile_targets"]
    with pytest.raises(ConfigError, match="percentile_targets"):
        config.validate(r)
    r = copy.deepcopy(raw)
    r["score"].update(_targets((0.5, 166), (0.5, 166)))
    with pytest.raises(ConfigError, match="twice"):
        config.validate(r)


def test_pct_lattice_n():
    assert [config.pct_lattice_n(q) for q in (0.5, 0.25, 0.75, 0.1, 0.2, 0.05, 0.33, 0.01, 0.4)] == \
        [2, 4, 4, 10, 5, 20, 100, 100, 5]


def test_all_jd_needs_continuing(raw):
    with pytest.raises(ConfigError, match="continuing_ntr_usd"):
        config.validate(_with(raw, ntr_goal_basis="all_jd"))
    with pytest.raises(ConfigError, match="ntr_goal_basis"):
        config.validate(_with(raw, ntr_goal_basis="total"))
    cfg = config.validate(_with(raw, ntr_goal_basis="all_jd", continuing_ntr_usd=1_000_000))
    assert config.ntr_target_effective(cfg) == raw["ntr_target"] - 1_000_000
    assert config.ntr_target_effective(config.validate(raw)) == raw["ntr_target"]
    assert config.ntr_target_effective(config.validate(_with(raw, ntr_target=None))) is None


def test_tuition_by_year_usd_precedence_and_round_trip(raw):
    rng = np.random.default_rng(21)
    for _ in range(200):
        base = float(rng.uniform(30_000, 90_000))
        usd = 50.0 * int(rng.integers(int(base / 50) - 400, int(base / 50) + 600))
        r = copy.deepcopy(raw)
        r["tuition_by_cohort"] = {2024: base * 0.9, 2025: base * 0.95, 2026: base}
        r["tuition_base"] = base
        r["tuition_increase_by_year"] = {2027: 6.0}          # overridden by the dollar figure
        r["tuition_by_year_usd"] = {2027: usd}
        cfg = config.validate(r)
        p = config.plan_increase_pct(cfg, 2027)
        assert p == 100.0 * (usd / base - 1.0)                # stored unrounded
        assert config.round_to(base * (1 + p / 100.0), 50) == usd
        assert config.scenario_tuition(cfg, p) == usd


def test_tuition_by_year_usd_validation(raw):
    with pytest.raises(ConfigError, match="multiple of tuition_rounding_usd"):
        config.validate(_with(raw, tuition_by_year_usd={2027: 57_123}))
    with pytest.raises(ConfigError, match="not a plan year"):
        config.validate(_with(raw, tuition_by_year_usd={2026: 57_000}))
    # the dollar figure alone covers the plan year; a later year compounds from it
    cfg = config.validate(_with(raw, tuition_increase_by_year={2028: 5.0}, tuition_by_year_usd={2027: 57_000}))
    assert config.plan_increase_pct(cfg, 2028) == pytest.approx(100 * (57_000 / 53_900 * 1.05 - 1), rel=1e-12)
    with pytest.raises(ConfigError, match="plan_cycle"):
        config.validate(_with(raw, tuition_increase_by_year={}))


def test_tuition_by_year_usd_later_year_needs_no_earlier_increase(raw):
    """R4-14: a dollar figure resets the factor, so the years before it need no increase: {2028: 60,000} with plan 2028
    and no 2027 value loads and gives the dollar figure; a year after it still needs an increase (the message says
    so). The Excel builder handles the missing year."""
    import tempfile
    from sw import build
    r = _with(raw, tuition_increase_by_year={}, tuition_by_year_usd={2028: 60_000},
              cycle=dict(raw["cycle"], plan_cycle=2028))
    cfg = config.validate(r)
    assert config.plan_increase_pct(cfg, 2028) == 100.0 * (60_000 / 53_900 - 1.0)
    assert config.scenario_tuition(cfg, config.plan_increase_pct(cfg, 2028)) == 60_000
    with pytest.raises(ConfigError, match="unless a later year"):
        config.plan_increase_pct(cfg, 2027)                    # 2027 alone: no increase and no dollar figure
    d = tempfile.mkdtemp()
    cp = os.path.join(d, "cfg.yaml")
    with open(cp, "w") as f:
        yaml.safe_dump(r, f)
    path, info = build.build(cp, "synthetic", os.path.join(ROOT, "config", "scenarios_synthetic.yaml"), d)
    assert info["run"].lcs[info["run"].scenarios[0].name]["middle"].tuition == 60_000


def test_hold_position_rows_setting(raw):
    """R4-06: hold_position_rows is false by default and must be true or false; Richmond holds (OD-14)."""
    assert config.validate(raw)["hold_position_rows"] is False
    assert config.validate(_with(raw, hold_position_rows=True))["hold_position_rows"] is True
    with pytest.raises(ConfigError, match="hold_position_rows"):
        config.validate(_with(raw, hold_position_rows="yes"))
    with open(os.path.join(ROOT, "config", "richmond.yaml")) as f:
        assert yaml.safe_load(f)["hold_position_rows"] is True


def test_protect_segment_and_pool_date(raw):
    cfg = config.validate(_with(raw, trim={"protect_segment": "above_floor", "floor_rate": 0.0, "exempt_cells": []}))
    assert cfg["trim"]["protect_segment"] == "above_floor"
    with pytest.raises(ConfigError, match="protect_segment"):
        config.validate(_with(raw, trim={"protect_segment": "floor", "floor_rate": 0.0, "exempt_cells": []}))
    assert config.validate(raw)["pool_ytd_as_of"] == "2026-11-15"
    assert config.validate(_with(raw, pool_ytd_as_of=datetime.date(2026, 10, 1)))["pool_ytd_as_of"] == "2026-10-01"
    with pytest.raises(ConfigError, match="pool_grid"):
        config.validate(_with(raw, risk=dict(raw["risk"], pool_grid=[1.0, 0.9])))


def test_reproduce_config_drops_tuition_in_dollars(raw):
    """Reproduce mode takes the fixture's tuition and the reproduce increase; the live dollar figure must not override
    it (a synthetic stand-in for the fixture's tuition by cohort)."""
    from sw import reproduce
    r = _with(raw, tuition_by_year_usd={2027: 60_000}, reproduce={"tuition_increase_pct": 6.0,
                                                                    "unscored_in_median": "excluded"})
    fx = {"tuition_by_cohort": {2024: 50_000.0, 2025: 51_850.0, 2026: 53_900.0}}
    cfg = reproduce.reproduce_config(r, fx)
    assert cfg["tuition_by_year_usd"] == {}
    assert config.plan_increase_pct(cfg, 2027) == pytest.approx(6.0, abs=1e-12)


def test_richmond_config_carries_the_v063_values():
    """Section 0A item A9 (read as YAML; the config still waits for the published tuition, test 0)."""
    with open(os.path.join(ROOT, "config", "richmond.yaml")) as f:
        r = yaml.safe_load(f)
    assert [(p["q"], p["t"]) for p in r["score"]["percentile_targets"]] == [(0.5, 166), (0.5, 165), (0.25, 158)]
    assert "median_thresholds" not in r["score"]
    assert r["tuition_by_year_usd"] == {2027: 63500}
    assert "tuition_increase_by_year" not in r                 # the 5.5% placeholder is retired
    assert r["trim"]["protect_segment"] == "above_floor"
    assert r["ntr_goal_basis"] == "entering_y1"
