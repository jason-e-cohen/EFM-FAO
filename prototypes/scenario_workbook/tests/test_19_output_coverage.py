"""Test 19: output coverage [v0.6.1, R-02, R-03, R-04].

Every interface-contract figure (spec section 15 item 11) gets a value worked out by hand, or an exact identity
against an independent ledger run, at a point where its formula can fail. Hand values use the six-cell toy grid
(tests/toy.py), Middle case, slope 1.0 point per $1,000, s = 0.10, tuition 53,000, need 1,000 per enrollee.

Toy Baseline, worked once and reused below (c1 to c6):
  awards     53,000 (c1 is flagged full tuition, follows T), 10,000, 30,000, 20,000, 45,000, 0
  admits     20, 30, 20, 30, 20, 5            (sum 125)
  yields     0.23, 0.40, 0.15, 0.25, 0.10, 0.30   (c1: 0.20 + 0.01 x 3)
  enrolled   4.6, 12, 3, 7.5, 2, 1.5          (class 30.6)
  v = A y (1 - y)   3.542, 7.2, 2.55, 5.625, 1.8, 1.05   (sum 21.767)
  w = T - award - 1,000   -1,000, 42,000, 22,000, 32,000, 7,000, 52,000
  sum w mu = 897,400 = ntr_y1 (specialty 0); sum w^2 v = 22,625,942,000; sum w A = 3,040,000
"""
import copy
import math
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from sw import CASES, cells as C, config, labels, ledger as L, response, risk, strip, trim
from sw.config import ConfigError
from toy import toy_cells, toy_cfg, toy_override

Z = 1.645
S = 0.10


def _setup(segment_mode="one", **cfg_over):
    cfg = toy_cfg(**cfg_over)
    cells = toy_cells(cfg, segment_mode=segment_mode)
    base = response.base_yield(cells, cfg, base_override=toy_override())
    return cfg, cells, base


def _risk(**over):
    r = copy.deepcopy(toy_cfg()["risk"])
    r.update(over)
    return r


def _trim(**over):
    t = {"protect_segment": "below_threshold", "floor_rate": 0.0, "exempt_cells": []}
    t.update(over)
    return t


def _i(cells, *ids):
    return [cells.index(c) for c in ids]


# ---------------------------------------------------------------------------------------------------------------
# Class: class_mean, class_lo90, class_hi90, p_class_over_cap, p_class_in_band

def test_class_range_and_probabilities():
    cfg, cells, base = _setup()
    lc = L.evaluate(cells, cfg, L.baseline(cells, cfg), base, "middle")
    V = 21.767 + S ** 2 * 30.6 ** 2                     # 31.1306
    sd = math.sqrt(V)
    d = risk.class_dist(lc)
    assert d["class_mean"] == pytest.approx(30.6, abs=1e-12)
    assert d["class_lo90"] == pytest.approx(30.6 - Z * sd, abs=1e-9)          # 21.4218
    assert d["class_hi90"] == pytest.approx(30.6 + Z * sd, abs=1e-9)          # 39.7782
    p = risk.class_probs(lc)                                                   # cap 40, target 40, band 3
    assert p["p_class_over_cap"] == pytest.approx(1 - norm.cdf((40.5 - 30.6) / sd), abs=1e-12)
    assert p["p_class_in_band"] == pytest.approx(norm.cdf((43.5 - 30.6) / sd) - norm.cdf((36.5 - 30.6) / sd),
                                                 abs=1e-12)


def test_class_lo90_clipped_at_zero():
    """R-08b: the lower end of the class range is clipped at zero."""
    A = np.array([3.0])
    y = np.array([0.2])
    r = risk.cf_class(A, y, 0.5, 5, 5, 1)          # M 0.6, V 0.48 + 0.25 x 0.36 = 0.57
    assert r["class_lo90"] == 0.0
    assert r["class_hi90"] == pytest.approx(0.6 + Z * math.sqrt(0.57), abs=1e-12)


# ---------------------------------------------------------------------------------------------------------------
# NTR: ntr_lo90, ntr_hi90 (range kind of the narrative), p_ntr_y1_ge_target

def test_ntr_range_and_probability():
    cfg, cells, base = _setup()
    lc = L.evaluate(cells, cfg, L.baseline(cells, cfg), base, "middle")
    Vn = 22_625_942_000 + S ** 2 * 897_400 ** 2          # 30,679,209,600
    sd = math.sqrt(Vn)                                  # 175,154.8
    n = risk.ntr(lc, 1_000_000)
    assert n["ntr_mean"] == pytest.approx(897_400, abs=1e-6)
    assert n["ntr_sd"] == pytest.approx(sd, rel=1e-12)
    assert n["ntr_lo90"] == pytest.approx(897_400 - Z * sd, rel=1e-12)
    assert n["ntr_hi90"] == pytest.approx(897_400 + Z * sd, rel=1e-12)
    assert n["p_ntr_y1_ge_target"] == pytest.approx(1 - norm.cdf((1_000_000 - 897_400) / sd), abs=1e-12)


# ---------------------------------------------------------------------------------------------------------------
# Median: p_median_t, p_median_t_rho05

def test_median_rho05_on_a_rho_one_config():
    """Score median at 166: G+ = 4.6 + 3 + 2 = 9.6 (c1, c3, c5), G- = 12 + 7.5 = 19.5 (c2, c4), c6 excluded.
    sum v over scored cells = 21.767 - 1.05 = 20.717."""
    cfg, cells, base = _setup()
    assert cfg["risk"]["shock_corr_above_below"] == 1.0
    lc = L.evaluate(cells, cfg, L.baseline(cells, cfg), base, "middle")
    md = risk.median(lc, "score", 166)
    gp, gm = 9.6, 19.5
    v1 = 20.717 + S ** 2 * (gp - gm) ** 2                                       # 21.6971
    v05 = 20.717 + S ** 2 * (gp ** 2 + gm ** 2 - 2 * 0.5 * gp * gm)            # 23.5691
    assert md["margin_t"] == pytest.approx(-9.9, abs=1e-12)
    assert md["p_median_t"] == pytest.approx(1 - norm.cdf((-0.5 + 9.9) / math.sqrt(v1)), abs=1e-12)     # 0.0218
    assert md["p_median_t_rho05"] == pytest.approx(1 - norm.cdf((-0.5 + 9.9) / math.sqrt(v05)), abs=1e-12)  # 0.0264
    # with rho 0.5 configured, the main probability uses it
    cfg5, cells5, base5 = _setup(risk=_risk(shock_corr_above_below=0.5))
    md5 = risk.median(L.evaluate(cells5, cfg5, L.baseline(cells5, cfg5), base5, "middle"), "score", 166)
    assert md5["p_median_t"] == pytest.approx(md["p_median_t_rho05"], abs=1e-12)


# ---------------------------------------------------------------------------------------------------------------
# Segment block: segment_enrolled, segment V_S, segment_lo90, segment_hi90, segment_share, p_segment_goal (normal form)

def test_segment_block_one_cell():
    """Segment = c5: M_S = 2, V_S = 1.8 + 0.01 x 4 = 1.84; the lower end clips at zero."""
    cfg, cells, base = _setup()
    blk = L.segment(L.evaluate(cells, cfg, L.baseline(cells, cfg), base, "middle"))
    assert blk["segment_apps"] == 25.0 and blk["segment_admits"] == 20.0
    assert blk["segment_enrolled"] == pytest.approx(2.0, abs=1e-12)
    assert blk["segment_v"] == pytest.approx(1.84, abs=1e-12)
    assert blk["segment_lo90"] == 0.0
    assert blk["segment_hi90"] == pytest.approx(2 + Z * math.sqrt(1.84), abs=1e-12)          # 4.2314
    assert blk["segment_share"] == pytest.approx(2 / 30.6, abs=1e-12)
    assert blk["segment_merit"] == pytest.approx(90_000, abs=1e-6)


def test_segment_block_all_out():
    """Segment = c3, c4, c5: M_S = 3 + 7.5 + 2 = 12.5; V_S = 2.55 + 5.625 + 1.8 + 0.01 x 156.25 = 11.5375."""
    cfg, cells, base = _setup(segment_mode="all_out")
    s = L.derive(L.baseline(cells, cfg), "g", cfg, cells, segment_goal=9.2)
    blk = L.segment(L.evaluate(cells, cfg, s, base, "middle"))
    sd = math.sqrt(11.5375)
    assert blk["segment_v"] == pytest.approx(11.5375, abs=1e-12)
    assert blk["segment_lo90"] == pytest.approx(12.5 - Z * sd, abs=1e-12)                    # 6.9124
    assert blk["segment_hi90"] == pytest.approx(12.5 + Z * sd, abs=1e-12)
    assert blk["segment_goal"] == 10                                                          # rounded up
    assert blk["p_segment_goal_normal"] == pytest.approx(1 - norm.cdf((10 - 0.5 - 12.5) / sd), abs=1e-12)


@pytest.mark.parametrize("lift, M_S, flagged", [(100.0, 25.0, True), (150.0, 31.25, False)])
def test_segment_approximate_flag_at_30(lift, M_S, flagged):
    """[v0.6.1, OP-3]: "approximate (fewer than 30 expected)" below 30 expected; the lift scales M_S = 12.5."""
    cfg, cells, base = _setup(segment_mode="all_out")
    s = L.derive(L.baseline(cells, cfg), "lift", cfg, cells, segment_pool_lift_pct=lift)
    blk = L.segment(L.evaluate(cells, cfg, s, base, "middle"))
    assert blk["segment_enrolled"] == pytest.approx(M_S, abs=1e-9)
    assert blk["approximate"] == (labels.SEGMENT_APPROX if flagged else "")
    assert labels.SEGMENT_APPROX == "approximate (fewer than 30 expected)"


# ---------------------------------------------------------------------------------------------------------------
# Evidence: evidence label and evidence_extrapolated_share

def test_evidence_label_at_tolerance_edges():
    """Toy award histories are constant, so each cell's observed range is its award; tolerance 2,500.
    c1 (53,000 vs 50,000), c4 (22,501 vs 20,000) and c5 (42,499 vs 45,000) are extrapolated; c2 (12,500), c3 (27,500)
    and c6 (0) are observed. Enrolled: 4.6, 12.75, 2.5, 8.2503, 1.4998, 1.5 (total 31.1001)."""
    cfg, cells, base = _setup()
    s = L.derive(L.baseline(cells, cfg), "E", cfg, cells,
                 award={"c2": 12500.0, "c3": 27500.0, "c4": 22501.0, "c5": 42499.0})
    lc = L.evaluate(cells, cfg, s, base, "middle")
    ev = response.evidence(lc, base, cfg)
    lab = dict(zip(cells.cell_id, ev["evidence_labels"]))
    assert lab == {"c1": "extrapolated", "c2": "observed", "c3": "observed", "c4": "extrapolated",
                   "c5": "extrapolated", "c6": "observed"}
    assert ev["evidence_extrapolated_share"] == pytest.approx((4.6 + 8.2503 + 1.4998) / 31.1001, rel=1e-12)


# ---------------------------------------------------------------------------------------------------------------
# Incentive block: every figure, including incentive_paid_anyway, ntr_change and ntr_per_additional

def test_incentive_block_added_bonus():
    """Parent: Baseline. Child: + $10,000 to out-of-state (c3, c4, c5; the cap binds at c5: incentive 8,000).
    Parent enrolled 3, 7.5, 2; child 5, 10.5, 3.6 (yields 0.25, 0.35, 0.18).
    C = 50,000 + 105,000 + 28,800 = 183,800; C_any = 30,000 + 75,000 + 16,000 = 121,000; dE = 6.6;
    dSpend = 110,000 + 165,000 + 100,800 = 375,800; child w 12,000, 22,000, -1,000 against parent 22,000, 32,000,
    7,000: dNTR = -6,000 - 9,000 - 17,600 = -32,600."""
    cfg, cells, base = _setup()
    b = L.baseline(cells, cfg)
    lp = L.evaluate(cells, cfg, b, base, "middle")
    ls = L.evaluate(cells, cfg, L.derive(b, "inc", cfg, cells, bonus_usd=10000.0), base, "middle")
    blk = L.incentive(ls, lp)
    assert blk["incentive_cost"] == pytest.approx(183_800, abs=1e-6)
    assert blk["incentive_paid_anyway"] == pytest.approx(121_000, abs=1e-6)
    assert blk["incentive_paid_anyway_share"] == pytest.approx(121_000 / 183_800, abs=1e-12)
    assert blk["additional_enrollees"] == pytest.approx(6.6, abs=1e-12)
    assert blk["merit_change"] == pytest.approx(375_800, abs=1e-6)
    assert blk["ntr_change"] == pytest.approx(-32_600, abs=1e-6)
    assert blk["aid_per_additional_kind"] == labels.AID_PER_ADDITIONAL
    assert blk["aid_per_additional"] == pytest.approx(375_800 / 6.6, abs=1e-6)               # 56,939
    assert blk["ntr_per_additional"] == pytest.approx(-32_600 / 6.6, abs=1e-6)                # -4,939
    assert blk["incentive_valid"] == labels.INCENTIVE_VALID
    assert L.price_of_target(lp, ls) == pytest.approx(32_600, abs=1e-6)
    assert L.bonus_implied_by_pool(100_000, lp, ls.scenario) == pytest.approx(100_000 / 12.5, abs=1e-9)


def test_incentive_block_reduced_bonus():
    """Parent: + $10,000 out-of-state. Child: + $5,000 (incentive 5,000 in c3, c4, c5; no cap).
    Child enrolled 4, 9, 3 against the parent's 5, 10.5, 3.6, so min(e_p, e_s) = e_s and C_any = C = 80,000.
    dE = -3.1; dSpend = -60,000 - 90,000 - 40,800 = -190,800; child w 17,000, 27,000, 2,000:
    dNTR = 8,000 + 12,000 + 9,600 = 29,600."""
    cfg, cells, base = _setup()
    p = L.derive(L.baseline(cells, cfg), "p", cfg, cells, bonus_usd=10000.0)
    lp = L.evaluate(cells, cfg, p, base, "middle")
    ls = L.evaluate(cells, cfg, L.derive(p, "c", cfg, cells, bonus_usd=5000.0), base, "middle")
    blk = L.incentive(ls, lp)
    assert blk["incentive_cost"] == pytest.approx(80_000, abs=1e-6)
    assert blk["incentive_paid_anyway"] == pytest.approx(80_000, abs=1e-6)
    assert blk["additional_enrollees"] == pytest.approx(-3.1, abs=1e-12)
    assert blk["merit_change"] == pytest.approx(-190_800, abs=1e-6)
    assert blk["ntr_change"] == pytest.approx(29_600, abs=1e-6)
    assert blk["aid_per_additional_kind"] == labels.SAVINGS_PER_LOST
    assert blk["aid_per_additional"] == pytest.approx(-190_800 / -3.1, abs=1e-6)
    assert blk["ntr_per_additional"] == pytest.approx(29_600 / -3.1, abs=1e-6)


def test_bonus_min_score_boundary():
    """bonus_min_score is inclusive: at 170, c3 and c5 (score 170) are eligible and c4 (161) is not."""
    cfg, cells, base = _setup()
    s = L.derive(L.baseline(cells, cfg), "m", cfg, cells, bonus_usd=10000.0, bonus_min_score=170)
    lc = L.evaluate(cells, cfg, s, base, "middle")
    assert dict(zip(cells.cell_id, lc.incentive)) == {"c1": 0, "c2": 0, "c3": 10000, "c4": 0, "c5": 8000, "c6": 0}


# ---------------------------------------------------------------------------------------------------------------
# Tuition what-if: every grid value, awards recomputed at T(p), discount column, both net-tuition lines

def test_tuition_whatif_every_grid_value():
    """Scenario W: Baseline + $10,000 out-of-state + specialty 5,000. Ledger at 6.0%: enrolled 4.6, 12, 5, 10.5,
    3.6, 1.5 (class 37.2; need 37,200). At T(p) the full-tuition cell c1 and the capped cell c5 (45,000 + 10,000)
    both pay nothing, so NTR(p) = (12 + 5 + 10.5 + 1.5) T - (120,000 + 200,000 + 315,000) - 42,200 = 29 T - 677,200."""
    cfg, cells, base = _setup()
    W = L.derive(L.baseline(cells, cfg), "W", cfg, cells, bonus_usd=10000.0, specialty_usd=5000.0)
    lc = L.evaluate(cells, cfg, W, base, "middle")
    tw = strip.tuition(lc)
    expect = {5.0: (52_500, 845_300), 5.5: (52_750, 852_550), 6.0: (53_000, 859_800), 6.5: (53_250, 867_050)}
    assert [r["tuition_increase_pct"] for r in tw["tuition_whatif"]] == list(expect)
    for r in tw["tuition_whatif"]:
        T, ntr = expect[r["tuition_increase_pct"]]
        assert r["tuition"] == T
        assert r["ntr_y1"] == pytest.approx(ntr, abs=1e-6)
        assert r["net_tuition_per_student"] == pytest.approx(ntr / 37.2, abs=1e-9)
        assert r["discount_entering_y1"] == pytest.approx(1 - ntr / (37.2 * T), abs=1e-12)   # 0.5672 at 5.0%
        assert r["label"] == labels.STICKER_LABEL
    assert expect[6.0][1] == pytest.approx(L.money(lc)["ntr_y1"], abs=1e-6)
    # net-tuition lines: fixed 53,000 - 50,000; scaled 0.06 x (50,000 - 17,000), the example award being
    # (12 x 10,000 + 5 x 30,000 + 10.5 x 20,000 + 1.5 x 0) / 29 = 16,552 -> 17,000
    assert tw["net_tuition_line_fixed"] == 3000.0
    assert tw["example_award"] == 17000.0
    assert tw["net_tuition_line_scaled"] == pytest.approx(1980.0, abs=1e-9)
    assert tw["net_tuition_line_scaled_text"] == labels.NET_TUITION_SCALED.format(p="6.0%", x="$1,980",
                                                                                   award="$17,000")


def test_tuition_whatif_scaled_awards():
    """Scenario W with award_scale_with_tuition. Ledger at 6.0%: c2 10,600, c3 31,800 + 10,000, c4 21,200 + 10,000;
    enrolled 4.6, 12.18, 5.36, 10.86, 3.6, 1.5 (class 38.1). NTR(p) = 29.9 T - 499,800 (1 + p) - 162,200 - 43,100.
    Example award: base-cycle levers (121,800 + 160,800 + 217,200) / 29.9 = 16,716 -> 17,000. With award_base
    (plan-year dollars) it would be 17,719 -> 18,000; without zero awards, 17,599 -> 18,000 [v0.6.1, R-07]."""
    cfg, cells, base = _setup()
    W = L.derive(L.baseline(cells, cfg), "W", cfg, cells, bonus_usd=10000.0, specialty_usd=5000.0,
                 award_scale_with_tuition=True)
    lc = L.evaluate(cells, cfg, W, base, "middle")
    rows = {r["tuition_increase_pct"]: r for r in strip.tuition(lc)["tuition_whatif"]}
    assert rows[5.0]["ntr_y1"] == pytest.approx(29.9 * 52_500 - 499_800 * 1.05 - 205_300, abs=1e-6)   # 839,660
    assert rows[6.0]["ntr_y1"] == pytest.approx(29.9 * 53_000 - 499_800 * 1.06 - 205_300, abs=1e-6)   # 849,612
    assert rows[6.0]["ntr_y1"] == pytest.approx(L.money(lc)["ntr_y1"], abs=1e-6)
    tw = strip.tuition(lc)
    assert tw["example_award"] == 17000.0
    assert tw["net_tuition_line_scaled"] == pytest.approx(0.06 * 33_000, abs=1e-9)


# ---------------------------------------------------------------------------------------------------------------
# Yield strip: medians at each shift, clip count, both break-evens

def test_yield_strip_medians_and_breakevens():
    cfg, cells, base = _setup(ntr_target=1_000_000)
    b = L.baseline(cells, cfg)
    lc = L.evaluate(cells, cfg, b, base, "middle")
    ys = strip.yield_strip(lc)
    assert ys["clip_count"] == 0
    for row in ys["yield_strip"]:
        d = row["shift_pts"]
        lcd = L.evaluate(cells, cfg, replace(b, yield_shift_pts=d), base, "middle")
        for meas, t in risk.median_targets(cfg):
            md = risk.median(lcd, meas, t)
            assert row["median"][(meas, t)]["margin"] == pytest.approx(md["margin_expected"], abs=1e-12)
            assert row["median"][(meas, t)]["p"] == pytest.approx(md["p_median_t"], abs=1e-12)
        assert row["p_ntr_y1_ge_target"] == pytest.approx(risk.ntr(lcd)["p_ntr_y1_ge_target"], abs=1e-12)
    # GPA margin: hi c1, c4, c5 (admits 70, mu 14.1); lo c2, c3 (admits 50, mu 15): -0.9 + d (70 - 50)
    by_d = {r["shift_pts"]: r for r in ys["yield_strip"]}
    assert by_d[2]["median"][("gpa", 3.83)]["margin"] == pytest.approx(-0.5, abs=1e-12)
    # break-evens: class (40 - 30.6) / 125 = 7.52 points; NTR (1,000,000 - 897,400) / 3,040,000 = 3.375 points
    assert ys["breakeven_shift_class"] == pytest.approx(7.52, abs=1e-12)
    assert ys["breakeven_shift_ntr"] == pytest.approx(3.375, abs=1e-12)
    assert ys["breakeven_label"] == labels.LINEAR_APPROX
    lb = L.evaluate(cells, cfg, replace(b, yield_shift_pts=3.375), base, "middle")
    assert L.money(lb)["ntr_y1"] == pytest.approx(1_000_000, abs=1e-6)


def test_class_breakeven_uses_target_not_cap():
    cfg, cells, base = _setup()
    s = L.derive(L.baseline(cells, cfg), "t35", cfg, cells, class_target=35.0)
    ys = strip.yield_strip(L.evaluate(cells, cfg, s, base, "middle"))
    assert ys["breakeven_shift_class"] == pytest.approx((35 - 30.6) / 125 * 100, abs=1e-12)    # 3.52


def test_yield_strip_clip_count():
    """c2 at 28,000 has yield 0.58 (+0.03 passes the 0.60 cap); c5 at 0 sits at the 0.03 floor (-0.03 passes it)."""
    cfg, cells, base = _setup()
    s = L.derive(L.baseline(cells, cfg), "clip", cfg, cells, award={"c2": 28000.0, "c5": 0.0})
    lc = L.evaluate(cells, cfg, s, base, "middle")
    assert lc.yld[cells.index("c2")] == pytest.approx(0.58) and lc.yld[cells.index("c5")] == pytest.approx(0.03)
    assert strip.yield_strip(lc)["clip_count"] == 2


# ---------------------------------------------------------------------------------------------------------------
# Pool strip at rho below 1, and its NTR spread

def test_pool_strip_rho05_and_ntr_sd():
    cfg, cells, base = _setup(risk=_risk(shock_corr_above_below=0.5))
    b = L.baseline(cells, cfg)
    # at m = 1 on Baseline: the hand values of the NTR and median tests above
    row1 = next(r for r in strip.pool_strip(cells, cfg, b, base)["pool_strip"] if r["pool_multiplier"] == 1.0)
    assert row1["ntr_sd"] == pytest.approx(math.sqrt(22_625_942_000 + S ** 2 * 897_400 ** 2), rel=1e-12)
    v05 = 20.717 + S ** 2 * (9.6 ** 2 + 19.5 ** 2 - 9.6 * 19.5)
    assert row1["p_median"] == pytest.approx(1 - norm.cdf(9.4 / math.sqrt(v05)), abs=1e-12)
    # every m against the ledger run with that multiplier
    s = L.derive(b, "S", cfg, cells, pool_multiplier=1.3, bonus_usd=5000.0, segment_pool_lift_pct=10.0,
                 yield_shift_pts=0.5, specialty_usd=2000.0)
    for row in strip.pool_strip(cells, cfg, s, base)["pool_strip"]:
        lc = L.evaluate(cells, cfg, replace(s, pool_multiplier=row["pool_multiplier"]), base, "middle")
        assert row["p_median"] == pytest.approx(risk.median(lc, "score", 166)["p_median_t"], abs=1e-12)
        assert row["ntr_sd"] == pytest.approx(risk.ntr(lc)["ntr_sd"], rel=1e-12)
        assert row["ntr_mean"] == pytest.approx(risk.ntr(lc)["ntr_mean"], rel=1e-12)


def test_pool_strip_rho05_synthetic(syn_cfg, worlds):
    """Same identity on a synthetic world, where cells at 165 sit below t = 166 but scale with the pool."""
    raw = copy.deepcopy({k: v for k, v in syn_cfg.items() if not k.startswith("_")})
    raw["risk"]["shock_corr_above_below"] = 0.5
    cfg = config.validate(raw)
    cells = worlds[cfg["generator"]["seeds"][0]]
    base = response.base_yield(cells, cfg)
    s = L.derive(L.baseline(cells, cfg), "S", cfg, cells, pool_multiplier=1.2, bonus_usd=4000.0)
    for row in strip.pool_strip(cells, cfg, s, base)["pool_strip"]:
        lc = L.evaluate(cells, cfg, replace(s, pool_multiplier=row["pool_multiplier"]), base, "middle")
        assert row["p_median"] == pytest.approx(risk.median(lc, "score", 166)["p_median_t"], abs=1e-12)
        assert row["ntr_sd"] == pytest.approx(risk.ntr(lc)["ntr_sd"], rel=1e-12)


# ---------------------------------------------------------------------------------------------------------------
# Yield shift: residency override replaces; clip after the shift (R-08a)

def test_residency_override_replaces():
    """Global +1 with out-of-state override -1: in-state cells +1, out-of-state cells -1 (not 0); a segment override
    of +2 then replaces the out-of-state value in c5."""
    cfg, cells, base = _setup()
    b = L.baseline(cells, cfg)
    lc = L.evaluate(cells, cfg, L.derive(b, "r", cfg, cells, yield_shift_pts=1.0, yield_shift_pts_out=-1.0),
                    base, "middle")
    np.testing.assert_allclose(lc.yld[_i(cells, "c1", "c2", "c3", "c4", "c5", "c6")],
                               [0.24, 0.41, 0.14, 0.24, 0.09, 0.31], atol=1e-12)
    lc2 = L.evaluate(cells, cfg, L.derive(b, "r2", cfg, cells, yield_shift_pts=1.0, yield_shift_pts_out=-1.0,
                                          yield_shift_pts_segment=2.0), base, "middle")
    assert lc2.yld[cells.index("c5")] == pytest.approx(0.12, abs=1e-12)
    assert lc2.yld[cells.index("c4")] == pytest.approx(0.24, abs=1e-12)


def test_clip_after_shift():
    """Cap 0.60, floor 0.03. (a) c2 at 28,000: response 0.58, +3 points -> 0.61 -> 0.60. (b) c2 at 35,000: response
    0.65 clipped to 0.60 first, then -2 points -> 0.58 (double clip, R-08a). (c) c5 at 0: response -0.35 clipped to
    0.03, then +2 points (segment override) -> 0.05."""
    cfg, cells, base = _setup()
    b = L.baseline(cells, cfg)
    i2, i5 = cells.index("c2"), cells.index("c5")
    a = L.evaluate(cells, cfg, L.derive(b, "a", cfg, cells, award={"c2": 28000.0}, yield_shift_pts_in=3.0),
                   base, "middle")
    assert a.yld[i2] == pytest.approx(0.60, abs=1e-12)
    bb = L.evaluate(cells, cfg, L.derive(b, "b", cfg, cells, award={"c2": 35000.0}, yield_shift_pts_in=-2.0),
                    base, "middle")
    assert bb.yld[i2] == pytest.approx(0.58, abs=1e-12)
    c = L.evaluate(cells, cfg, L.derive(b, "c", cfg, cells, award={"c5": 0.0}, yield_shift_pts_segment=2.0),
                   base, "middle")
    assert c.yld[i5] == pytest.approx(0.05, abs=1e-12)


# ---------------------------------------------------------------------------------------------------------------
# KPIs: full-tuition count; award matrix and step sizes

def test_full_tuition_count_baseline():
    """Only c1 is at tuition (4.6 enrolled); c5's 45,000 is 8,000 below 53,000 and is not counted."""
    cfg, cells, base = _setup()
    k = L.kpis(L.evaluate(cells, cfg, L.baseline(cells, cfg), base, "middle"))
    assert k["full_tuition_n"] == pytest.approx(4.6, abs=1e-12)
    assert k["no_merit_award_n"] == pytest.approx(1.5, abs=1e-12)
    assert k["barbell"] == pytest.approx(6.1 / 30.6, abs=1e-12)


def test_award_matrix_and_step_sizes():
    """No segment cells: out-of-state GPA hi holds c5 (170, 45,000) and c4 (161, 20,000): one step of 25,000. Every
    other residency x segment x GPA group has one scored cell; c6 is unscored."""
    cfg, cells, base = _setup(segment_mode="none")
    aw = L.awards(L.evaluate(cells, cfg, L.baseline(cells, cfg), base, "middle"))
    assert aw["award_matrix"] == {"c1": 53000.0, "c2": 10000.0, "c3": 30000.0, "c4": 20000.0, "c5": 45000.0,
                                  "c6": 0.0}
    assert aw["step_sizes"] == [{"residency": "out", "segment": "", "gpa_class": "hi", "band_upper": 170.0,
                                 "band_lower": 161.0, "step_usd": 25000.0}]


def test_discount_row():
    cfg, cells, base = _setup()
    s = L.derive(L.baseline(cells, cfg), "d", cfg, cells, discount_target=0.5)
    lc = L.evaluate(cells, cfg, s, base, "middle")
    # aid = 693,800 merit + 30,600 need; gross = 30.6 x 53,000 = 1,621,800
    row = L.discount_row(lc)
    assert row["discount_entering_y1"] == pytest.approx(724_400 / 1_621_800, abs=1e-12)
    assert row["margin_to_target"] == pytest.approx(0.5 - 724_400 / 1_621_800, abs=1e-12)


# ---------------------------------------------------------------------------------------------------------------
# Shrink path and class-size table: trimmed rates at a positive floor_rate; lowest band admitted; integer settling

def test_trimmed_rates_with_floor_rate():
    """floor_rate 0.10. Trim order: c6 (unscored), c2 (161 lo), c4 (161 hi), c3 (170 lo), c1 (170 hi), c5 (segment).
    rm = A y (r - 0.1) / r: 0.9, 9.6, 6.25, 2.25, 3.68, 1.75.
    N = 20 (cut 10.6): c6 and c2 to 0.10; c4 share 0.1 / 6.25 = 0.016, rate 0.6 - 0.5 x 0.016 = 0.592.
    N = 10 (cut 20.6): c6, c2, c4, c3 to 0.10; c1 share 1.6 / 3.68, rate 0.5 - 0.4 x 1.6 / 3.68 = 0.326087."""
    cfg, cells, base = _setup(trim=_trim(floor_rate=0.1))
    lc = L.evaluate(cells, cfg, L.baseline(cells, cfg), base, "middle")
    ids = ("c1", "c2", "c3", "c4", "c5", "c6")
    assert [cells.cell_id[i] for i in trim.trim_order(lc)] == ["c6", "c2", "c4", "c3", "c1", "c5"]
    np.testing.assert_allclose(trim.trim_rates(lc, 20)["rm"][_i(cells, *ids)], [3.68, 9.6, 2.25, 6.25, 1.75, 0.9],
                               atol=1e-12)
    r20 = trim.trim_rates(lc, 20)["rates"][_i(cells, *ids)]
    np.testing.assert_allclose(r20, [0.5, 0.1, 0.4, 0.592, 0.8, 0.1], atol=1e-12)
    r10 = trim.trim_rates(lc, 10)["rates"][_i(cells, *ids)]
    np.testing.assert_allclose(r10, [0.5 - 0.4 * 1.6 / 3.68, 0.1, 0.1, 0.1, 0.8, 0.1], atol=1e-12)
    for N, r in ((20, r20), (10, r10)):
        lcN = L.evaluate(cells, cfg, L.with_rates(lc.scenario, trim.trim_rates(lc, N)["rates"]), base, "middle")
        assert lcN.mu.sum() == pytest.approx(N, abs=1e-9)


def test_class_table_rows():
    """floor_rate 0. N = 9 (cut 21.6): c6, c2, c4 fully cut (1.5 + 12 + 7.5); c3 share 0.6 / 3 = 0.2, rate 0.32.
    Lowest band still admitted: 170. Admits cut: unscored 5, band 161 60 (30 + 30), band 170 4.
    N = 20 (cut 10.6): c6 cut; c2 share 9.1 / 12, rate 0.5 x (1 - 9.1 / 12); lowest band 161."""
    cfg, cells, base = _setup()
    b = L.baseline(cells, cfg)
    ct = trim.class_table(cells, cfg, b, base, Ns=[9, 20, 35, 45])
    rows = {r["N"]: r for r in ct["class_table"]}
    assert ct["M"] == pytest.approx(30.6, abs=1e-12)
    r9 = rows[9]
    assert r9["status"] == labels.CT_OK and r9["f"] == pytest.approx(9 / 30.6, abs=1e-12)
    assert r9["class_mean"] == pytest.approx(9.0, abs=1e-9)
    np.testing.assert_allclose(r9["rates"][_i(cells, "c1", "c2", "c3", "c4", "c5", "c6")],
                               [0.5, 0.0, 0.32, 0.0, 0.8, 0.0], atol=1e-12)
    assert r9["lowest_band_admitted"] == 170.0
    assert r9["admits_cut_by_band"] == pytest.approx({"unscored": 5.0, 161.0: 60.0, 170.0: 4.0})
    r20 = rows[20]
    assert r20["rates"][cells.index("c2")] == pytest.approx(0.5 * (1 - 9.1 / 12), abs=1e-12)
    assert r20["lowest_band_admitted"] == 161.0
    assert rows[35]["status"] == labels.CT_NOT_APPLICABLE
    assert rows[45]["status"] == labels.CT_ABOVE_CAP


def test_integer_settling_and_uncut_rates():
    """integer_admits, floor_rate 0.13, c3's rate set to 0.43 (50 x 0.43 = 21.5 admits, rounded to 22).
    M = 4.6 + 12 + 3.3 + 7.5 + 2 + 1.5 = 30.9; N = 20 (cut 10.9).
    rm: c6 1.5 x 0.12 / 0.25 = 0.72; c2 12 x 0.37 / 0.5 = 8.88; c4 7.5 x 0.47 / 0.6 = 5.875.
    c4 share 1.3 / 5.875; rate 0.6 - 0.47 x 1.3 / 5.875 = 0.496 (24.8 admits).
    Rounded: c6 2.6 -> 3, c2 7.8 -> 8, c4 24.8 -> 25; class 20.25, residual 0.25 = one c4 admit (yield 0.25), so
    c4 settles at 24 and the class is 20.0. Without settling it would be 20.25, more than half c4's yield from N.
    Uncut cells keep their input rates exactly: c3 stays 0.43, not 22 / 50 = 0.44 [v0.6.1, R-05]."""
    cfg, cells, base = _setup(integer_admits=True, trim=_trim(floor_rate=0.13))
    s = L.derive(L.baseline(cells, cfg), "s", cfg, cells, admit_rate={"c3": 0.43})
    lc = L.evaluate(cells, cfg, s, base, "middle")
    assert lc.admits[cells.index("c3")] == 22.0 and lc.mu.sum() == pytest.approx(30.9, abs=1e-12)
    tr = trim.trim_rates(lc, 20)
    rates = dict(zip(cells.cell_id, tr["rates"]))
    assert rates["c3"] == 0.43 and rates["c1"] == 0.5 and rates["c5"] == 0.8
    assert rates["c6"] == pytest.approx(3 / 20) and rates["c2"] == pytest.approx(8 / 60)
    assert rates["c4"] == pytest.approx(24 / 50)
    lcN = L.evaluate(cells, cfg, L.with_rates(s, tr["rates"]), base, "middle")
    assert lcN.mu.sum() == pytest.approx(20.0, abs=1e-9)
    assert abs(lcN.mu.sum() - 20) <= lcN.yld[cells.index("c4")] / 2


# ---------------------------------------------------------------------------------------------------------------
# Base-yield pooling at exactly 30 admits; multi-year tuition compounding; the segment scenario field

def test_segment_pool_of_exactly_30_admits():
    """Segment pool S1 + S2: 18 + 12 = 30 admits, 6 + 3 = 9 enrolled (0.30): used, since it has at least 30.
    The (out, upper) residency pool would give (12 + 9) / 60 = 0.35. Awards are constant, so no re-centering:
    y0(S1) = (18 x 6/18 + 20 x 0.30) / 38 = 12 / 38."""
    cfg = toy_cfg()
    spec = [("D", "out", "", 170.0, [10, 10, 10], [4, 4, 4]),
            ("S1", "out", "priority", 170.0, [6, 6, 6], [2, 2, 2]),
            ("S2", "out", "priority", 167.0, [4, 4, 4], [1, 1, 1]),
            ("I", "in", "", 170.0, [20, 20, 20], [10, 10, 10])]
    rows = []
    for cid, res, seg, sc, adm, enr in spec:
        for j, coh in enumerate((2024, 2025, 2026)):
            rows.append({"cell_id": cid, "residency": res, "segment": seg, "score_lo": sc, "gpa_class": "hi",
                         "cohort": coh, "apps": 2 * adm[j], "admits": adm[j], "award_usd": 20000.0,
                         "enrolled": enr[j]})
    cells = C.from_long(pd.DataFrame(rows, columns=C.COLUMNS), cfg)
    base = response.base_yield(cells, cfg)
    i = cells.index("S1")
    assert base.pool_level[i] == "segment"
    for k in CASES:
        assert base.y0[k][i] == pytest.approx(12 / 38, abs=1e-12)


def test_pooling_fallback_to_score_group():
    """R-08c: U_in (in-state, upper) has no admits and neither does its (in, upper) pool, so it takes the upper score
    group across residencies: U_out's 9 / 30 = 0.30. Skipping that level would give all cells: (9 + 18) / 60 = 0.45."""
    cfg = toy_cfg()
    spec = [("U_out", "out", 170.0, [10, 10, 10], [3, 3, 3]),
            ("U_in", "in", 170.0, [0, 0, 0], [0, 0, 0]),
            ("L_in", "in", 161.0, [10, 10, 10], [6, 6, 6])]
    rows = []
    for cid, res, sc, adm, enr in spec:
        for j, coh in enumerate((2024, 2025, 2026)):
            rows.append({"cell_id": cid, "residency": res, "segment": "", "score_lo": sc, "gpa_class": "hi",
                         "cohort": coh, "apps": 2 * adm[j] + 1, "admits": adm[j], "award_usd": 20000.0,
                         "enrolled": enr[j]})
    cells = C.from_long(pd.DataFrame(rows, columns=C.COLUMNS), cfg)
    base = response.base_yield(cells, cfg)
    i = cells.index("U_in")
    assert base.pool_level[i] == "group"
    assert base.y0["middle"][i] == pytest.approx(0.30, abs=1e-12)


def test_plan_year_two_years_out_compounds():
    """6.0% then 5.0%: 1.06 x 1.05 = 1.113 (11.3%, not 11.0%); T = round_to(50,000 x 1.113, 50) = 55,650."""
    cfg = toy_cfg(tuition_increase_by_year={2027: 6.0, 2028: 5.0},
                  cycle={"base_cycle": 2026, "plan_cycle": 2028, "history": [2024, 2025, 2026]})
    assert config.plan_increase_pct(cfg, 2028) == pytest.approx(11.3, abs=1e-9)
    cells = toy_cells(cfg)
    base = response.base_yield(cells, cfg, base_override=toy_override())
    lc = L.evaluate(cells, cfg, L.baseline(cells, cfg), base, "middle")
    assert lc.tuition == 55650.0


def test_segment_scenario_field():
    """[v0.6.1, OP-5]: `segment` defaults to the only configured segment; with several configured, a scenario that
    names none is an error, and a named one must be configured."""
    cfg, cells, base = _setup()
    assert L.baseline(cells, cfg).segment == "priority"
    two = dict(cfg)
    two["segments"] = cfg["segments"] + [{"name": "other", "within": {"residency": "in"}, "members_label": "x",
                                          "share_source": "assumed"}]
    with pytest.raises(ConfigError):
        L.baseline(cells, two)
    b = L.baseline(cells, two, segment="priority")
    assert L.derive(b, "child", two, cells, bonus_usd=1000.0).segment == "priority"
    with pytest.raises(ConfigError):
        L.derive(b, "bad", two, cells, segment="missing")
    # naming the other segment: no cell carries it, so the segment block is empty
    o = L.derive(b, "o", two, cells, segment="other")
    assert L.segment(L.evaluate(cells, two, o, base, "middle"))["segment_enrolled"] == labels.NO_SEGMENT_CELLS
