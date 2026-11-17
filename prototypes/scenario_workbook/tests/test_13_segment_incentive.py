"""Test 13: segment and incentive blocks.

- segment_pool_lift_pct changes applications in segment cells only, and 0 equals the parent.
- Python's exact P(E_S >= goal) matches simulation within 0.01; the Excel normal form's gap is reported.
- On a scenario that differs from its parent only by the incentive: dSpend = sum e_s (a_s - a_p) + sum (e_s - e_p) a_p
  cell by cell; C_any <= C; C_any equals the cell-level sum (cells where the cap binds and cells below
  bonus_min_score included).
- The validity flag turns "not valid" when any other lever differs.
"""
import json
import math
import os

import numpy as np
import pytest

from sw import labels, ledger as L, mc, response, risk
from toy import toy_cells, toy_cfg, toy_override


@pytest.fixture(scope="module")
def toy():
    cfg = toy_cfg()
    cells = toy_cells(cfg)
    base = response.base_yield(cells, cfg, base_override=toy_override())
    return cfg, cells, base


def test_segment_lift(toy):
    cfg, cells, base = toy
    b = L.baseline(cells, cfg)
    lb = L.evaluate(cells, cfg, b, base, "middle")
    s = L.derive(b, "lift", cfg, cells, segment_pool_lift_pct=20.0)
    ls = L.evaluate(cells, cfg, s, base, "middle")
    seg = ls.in_segment
    np.testing.assert_allclose(ls.apps[~seg], lb.apps[~seg])
    np.testing.assert_allclose(ls.apps[seg], lb.apps[seg] * 1.2)
    z = L.derive(b, "zero", cfg, cells, segment_pool_lift_pct=0.0)
    lz = L.evaluate(cells, cfg, z, base, "middle")
    np.testing.assert_array_equal(lz.apps, lb.apps)
    assert L.money(lz) == L.money(lb)
    assert labels.ASSUMPTION_LABEL in L.scenario_labels(s, cfg)
    assert labels.ASSUMPTION_LABEL not in L.scenario_labels(z, cfg)


def test_segment_exact_vs_simulation(syn_cfg, worlds, report_dir):
    cfg = syn_cfg
    rows = []
    for seed in cfg["generator"]["seeds"][:5]:
        cells = worlds[seed]
        base = response.base_yield(cells, cfg)
        s = L.derive(L.baseline(cells, cfg), "seg", cfg, cells, bonus_usd=8000.0, bonus_scope="segment",
                     segment_pool_lift_pct=10.0)
        lc = L.evaluate(cells, cfg, s, base, "middle")
        m = lc.in_segment
        M = float(lc.mu[m].sum())
        sd = float(cfg["risk"]["common_shock_sd"])
        V = float((lc.admits[m] * lc.yld[m] * (1 - lc.yld[m])).sum() + sd ** 2 * M ** 2)
        sim = mc.simulate(lc.admits, lc.yld, sd, {"seg": m.astype(float)}, 200_000, seed=seed)["seg"]
        for goal in (math.ceil(M) - 4, math.ceil(M), math.ceil(M) + 4):
            ex = risk.segment_exact(lc, goal)
            nm = risk.segment_normal(M, V, goal)
            sm = float((sim >= goal).mean())
            rows.append({"seed": seed, "M_S": M, "goal": goal, "exact": ex, "sim": sm, "normal": nm,
                         "exact_sim_gap": abs(ex - sm), "normal_exact_gap": abs(nm - ex)})
    with open(os.path.join(report_dir, "test13_segment.json"), "w") as f:
        json.dump(rows, f, indent=1)
    assert max(r["exact_sim_gap"] for r in rows) <= 0.01


def test_segment_block(toy):
    cfg, cells, base = toy
    s = L.derive(L.baseline(cells, cfg), "g", cfg, cells, segment_goal=1.2)
    lc = L.evaluate(cells, cfg, s, base, "middle")
    blk = L.segment(lc)
    assert blk["segment_goal"] == 2                                 # rounded up
    assert blk["approximate"] == labels.SEGMENT_APPROX              # fewer than 30 expected [v0.6.1, OP-3]
    assert labels.SEGMENT_SHARE_LABEL in blk["labels"]              # share_source: assumed
    assert labels.RESPONSE_LABEL in blk["labels"]
    assert 0.0 <= blk["p_segment_goal"] <= 1.0
    assert blk["segment_lo90"] >= 0.0


def _incentive_pair(cfg, cells, min_score=None):
    p = L.derive(L.baseline(cells, cfg), "parent", cfg, cells, pool_multiplier=1.1, yield_shift_pts=0.5)
    s = L.derive(p, "child", cfg, cells, bonus_usd=10000.0, bonus_scope="residency_out", bonus_min_score=min_score)
    return p, s


@pytest.mark.parametrize("min_score", [None, 165])
def test_incentive_decomposition(toy, min_score):
    cfg, cells, base = toy
    p, s = _incentive_pair(cfg, cells, min_score)
    lp = L.evaluate(cells, cfg, p, base, "middle")
    ls = L.evaluate(cells, cfg, s, base, "middle")
    blk = L.incentive(ls, lp)
    pop = ls.incentive > 0
    e_s, e_p, a_s, a_p = ls.enrolled, lp.enrolled, ls.award, lp.award
    lhs = e_s * a_s - e_p * a_p
    rhs = e_s * (a_s - a_p) + (e_s - e_p) * a_p
    np.testing.assert_allclose(lhs, rhs, atol=1e-6)
    assert blk["merit_change"] == pytest.approx(lhs[pop].sum())
    C_any_cells = (np.minimum(e_p, e_s) * ls.incentive)[pop].sum()
    assert blk["incentive_paid_anyway"] == pytest.approx(C_any_cells)
    assert blk["incentive_paid_anyway"] <= blk["incentive_cost"] + 1e-9
    i5 = cells.index("c5")
    assert pop[i5] and ls.incentive[i5] == 8000.0                   # cap binds
    if min_score is not None:
        i4 = cells.index("c4")                                     # out-of-state, score 161: below the floor
        assert not pop[i4] and ls.incentive[i4] == 0.0
    assert blk["incentive_valid"] == labels.INCENTIVE_VALID
    assert labels.RESPONSE_LABEL in blk["labels"]


CHANGES = {
    "pool_multiplier": 1.2, "specialty_usd": 1000.0, "need_total": 30000.0, "tuition_increase_pct": 5.0,
    "award_scale_with_tuition": True, "class_target": 35.0, "class_cap": 42.0, "segment_pool_lift_pct": 5.0,
    "yield_shift_pts": 1.0, "yield_shift_pts_in": 1.0, "yield_shift_pts_out": -1.0, "yield_shift_pts_segment": 2.0,
    "plan_year": 2028,
}


@pytest.mark.parametrize("field", list(CHANGES) + ["admit_rate", "award_usd", "full_tuition", "segment"])
def test_validity_flag(toy, field):
    cfg, cells, base = toy
    cfg = dict(cfg)
    cfg["tuition_increase_by_year"] = {2027: 6.0, 2028: 5.0}
    if field == "segment":
        # a second configured segment; the scenario names the active one [v0.6.1, OP-5]
        cfg["segments"] = cfg["segments"] + [{"name": "other", "within": {"residency": "in"},
                                              "members_label": "x", "share_source": "assumed"}]
        p = L.derive(L.baseline(cells, cfg, segment="priority"), "parent", cfg, cells, pool_multiplier=1.1,
                     yield_shift_pts=0.5)
        s = L.derive(p, "child", cfg, cells, bonus_usd=10000.0, bonus_scope="residency_out")
    else:
        p, s = _incentive_pair(cfg, cells)
    if field == "admit_rate":
        s2 = L.derive(s, "x", cfg, cells, admit_rate={"c2": 0.45})
    elif field == "award_usd":
        s2 = L.derive(s, "x", cfg, cells, award={"c2": 12000.0})
    elif field == "full_tuition":
        s2 = L.derive(s, "x", cfg, cells, full_tuition={"c2": True})
    elif field == "segment":
        s2 = L.derive(s, "x", cfg, cells, segment="other")
    else:
        s2 = L.derive(s, "x", cfg, cells, **{field: CHANGES[field]})
    lp = L.evaluate(cells, cfg, p, base, "middle")
    ls = L.evaluate(cells, cfg, s2, base, "middle")
    assert L.incentive(ls, lp)["incentive_valid"] == labels.INCENTIVE_NOT_VALID
    # targets are not levers: changing them keeps the decomposition valid
    s3 = L.derive(s, "y", cfg, cells, segment_goal=3, discount_target=0.5)
    assert L.incentive(L.evaluate(cells, cfg, s3, base, "middle"), lp)["incentive_valid"] == labels.INCENTIVE_VALID


def test_aid_per_additional_rules(toy):
    cfg, cells, base = toy
    p, s = _incentive_pair(cfg, cells)
    lp = L.evaluate(cells, cfg, p, base, "middle")
    blk = L.incentive(L.evaluate(cells, cfg, s, base, "middle"), lp)
    assert blk["additional_enrollees"] >= 0.5
    assert blk["aid_per_additional_kind"] == labels.AID_PER_ADDITIONAL
    assert blk["aid_per_additional"] == pytest.approx(blk["merit_change"] / blk["additional_enrollees"])
    # a tiny bonus moves enrollment by under half a student
    s_small = L.derive(p, "small", cfg, cells, bonus_usd=200.0)
    blk2 = L.incentive(L.evaluate(cells, cfg, s_small, base, "middle"), lp)
    assert blk2["aid_per_additional"] == labels.UNDER_HALF
