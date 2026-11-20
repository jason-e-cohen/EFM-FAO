"""Edge workbook inputs for test 3 [v0.6.2, P2-01] (spec test 3, "Edge workbook").

A config and a scenario file built so the workbook formulas take the branches the main and test 8 workbooks never reach
(Review_Phase2_Build.md section 2). Every value is synthetic. `write(out_dir)` writes both files and returns their paths;
`world(cfg)` is the synthetic world they are built on (seed 101).

Branch                                              How the edge inputs reach it
yield at the cap and at the floor (outer clip)     "Clip at floor and cap": in-state shift -30, out-of-state +45
response clipped before the shift (inner clip)     "Inner clip": in-0-hi award raised to 90,000 (yield above the cap
                                                    before the -10 shift); out-167-hi award cut to 0 (below the floor
                                                    before the +5 shift)
unflagged award above tuition                       "Inner clip": in-0-hi lever 90,000 against tuition 57,000
in-state yield-shift override                       both scenarios above; "Global shift, in-state override" sets a
                                                    non-zero global shift too, so replacing and adding differ
                                                    [v0.6.2, P21-02]
need_total override                                 "Need override"
non-integer segment goal                            "Goal 24.3"
child differing only in one full_tuition flag       "Flag only" (child of "Goal 24.3")
segment pool exactly at the pooling threshold       pooling_min_admits = the smallest segment-level pool's admits
pool strip and medians at rho below 1               risk.shock_corr_above_below 0.5
shrink path with floor_rate above 0, exempt cells   trim.floor_rate 0.2, two exempt cells
"N not reachable" shortfall, "above cap"            class.what_if includes 60 and 150
yield-strip clip count above 0                      cells at the cap in "Clip at floor and cap"
budget basis merit, history reconciliation          budget_total and budget_basis merit; merit_actual_by_cohort for
                                                    two of the three cohorts
bonus_pool_usd, named segment on Baseline           "Goal 24.3"; Baseline names its segment
scaled-line example award (Q-5)                     "Example award edges": zero-award cells flagged (left out), an
                                                    unflagged award between base-cycle and plan tuition (left out)
[v0.6.3] revenue goal under all_jd                  ntr_goal_basis all_jd with continuing_ntr_usd (BM-4)
[v0.6.3] segment protection above the floor         trim.protect_segment above_floor (BM-5)
[v0.6.3] tuition in dollars                         tuition_by_year_usd for the plan year (BM-2)
[v0.6.3] growth to date without a date              pool_ytd_growth set, pool_ytd_as_of blank (BM-6)
[v0.6.3] percentile targets                         synthetic.yaml's four, one with fewer than 20 expected below t
[Phase 4] Distribution: merit of zero               "No merit awards": every award 0 and no full-tuition flag (the
                                                    top-quartile share's zero-merit branch); positions with no
                                                    enrolled (the fraction's zero branch) occur in every scenario
[R4-10] spread band in the lowest band              "Lowest band": admit rates 0.9 in the lowest score band and 0.02
                                                    elsewhere, so the 25th and 75th percentile bands are the lowest
                                                    ("below 152" text)
[R4-09] unscored_in_median: below                   `write(out_dir, below=True)`: the same inputs under 'below'
                                                    (the percentile sign and spread-band branches for unscored);
                                                    "Unscored near the 25th": unscored admit rates 1.0 and the two
                                                    lowest scored bands' rates x 1.8, so counting unscored below moves
                                                    the 25th percentile band (158 excluded, 154 below)
"""
import copy
import os

import numpy as np
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = 101
EXEMPT = ["out-0-lo", "in-unscored-lo"]
CONTINUING = 8000000          # synthetic continuing-student net tuition (all_jd)
TUITION_2027 = 57000          # synthetic plan-year tuition in dollars (a multiple of tuition_rounding_usd)


def world(cfg):
    from sw import synth_cells
    return synth_cells.generate(cfg, SEED)


def segment_pool_min(cells, cfg):
    """Admits (all cohorts) of the smallest (residency, segment, score group) pool that has a segment."""
    from sw import response
    up = response.score_group_upper(cells, cfg)
    adm = cells.admits.sum(axis=1)
    pools = {}
    for i in range(cells.n):
        if cells.segment[i]:
            k = (cells.residency[i], cells.segment[i], bool(up[i]))
            pools[k] = pools.get(k, 0.0) + float(adm[i])
    return min(pools.values())


def config_dict(below=False):
    from sw import config
    with open(os.path.join(ROOT, "config", "synthetic.yaml")) as f:
        raw = yaml.safe_load(f)
    cfg = config.validate(raw)
    cells = world(cfg)
    e = copy.deepcopy(raw)
    e["client"]["id"] = "synthetic_edge"
    e["client"]["name"] = "Synthetic law world (edge workbook)"
    e["risk"]["shock_corr_above_below"] = 0.5
    e["trim"] = {"protect_segment": "above_floor", "floor_rate": 0.2, "exempt_cells": list(EXEMPT)}
    e["pooling_min_admits"] = segment_pool_min(cells, cfg)
    e["class"]["what_if"] = [60, 80, 100, 120, 130, 150]
    e["budget_total"] = 1500000
    e["budget_basis"] = "merit"
    e["merit_actual_by_cohort"] = {2024: 1900000, 2025: 2100000}
    # [v0.6.3] Phase 2.2 branches
    e["ntr_goal_basis"] = "all_jd"
    e["continuing_ntr_usd"] = CONTINUING
    e["ntr_target"] = raw["ntr_target"] + CONTINUING
    e["tuition_by_year_usd"] = {2027: TUITION_2027}
    e["pool_ytd_growth"] = 0.33
    e["pool_ytd_as_of"] = None
    if below:                                                   # R4-09
        e["client"]["id"] = "synthetic_edge_below"
        e["client"]["name"] = "Synthetic law world (edge workbook, unscored below)"
        e["unscored_in_median"] = "below"
    for c in EXEMPT:
        assert c in list(cells.cell_id), c
    return e


SCENARIOS = [
    {"name": "Baseline", "description": "Edge workbook: Baseline names its segment", "segment": "priority"},
    {"name": "Clip at floor and cap", "parent": "Baseline",
     "description": "In-state yield -30 points, out-of-state +45: cells at the floor and at the cap",
     "yield_shift_pts_in": -30, "yield_shift_pts_out": 45},
    {"name": "Inner clip", "parent": "Baseline",
     "description": "Response clipped before the shift; an unflagged award above tuition",
     "yield_shift_pts_in": -10, "yield_shift_pts_out": 5,
     "overrides": {"award_usd": {"in-0-hi": 90000, "out-167-hi": 0}}},
    {"name": "Need override", "parent": "Baseline", "description": "need_total override only", "need_total": 210000},
    {"name": "Global shift, in-state override", "parent": "Baseline",
     "description": "Global yield shift +2 with an in-state override of -1: the override replaces the global shift",
     "yield_shift_pts": 2, "yield_shift_pts_in": -1},
    {"name": "Goal 24.3", "parent": "Baseline", "description": "Segment incentive, goal 24.3, a dollar pool",
     "bonus_usd": 6000, "bonus_scope": "segment", "segment_goal": 24.3, "bonus_pool_usd": 150000},
    {"name": "Flag only", "parent": "Goal 24.3", "description": "Differs from its parent in one full_tuition flag",
     "overrides": {"full_tuition": {"out-priority-161-hi": 1}}},
    {"name": "Example award edges", "parent": "Baseline", "award_scale_with_tuition": True,
     "description": "Scaled-line example award: zero-award cells flagged; an unflagged award between base-cycle and "
                    "plan-year tuition",
     "overrides": {"full_tuition": {"in-0-lo": 1, "in-0-hi": 1, "out-0-hi": 1, "out-152-lo": 1},
                   "award_usd": {"out-158-lo": 55000}}},
]


def no_merit_scenario(cells):
    """[Phase 4] Every award 0 and every full-tuition flag cleared: merit is 0 (Distribution, zero-merit branch)."""
    ids = list(cells.cell_id)
    return {"name": "No merit awards", "parent": "Baseline",
            "description": "Every award 0 and no full-tuition flag: merit dollars are zero",
            "overrides": {"award_usd": {c: 0 for c in ids}, "full_tuition": {c: 0 for c in ids}}}


def lowest_band_scenario(cells):
    """[R4-10] Admit rates 0.9 in the lowest score band and 0.02 elsewhere: most of the class is in the lowest band, so
    the spread rows reach the lowest band's text ("below <next bound>")."""
    lo = float(np.nanmin(cells.score_lo))
    rate = {c: (0.9 if s == lo else 0.02) for c, s in zip(cells.cell_id, cells.score_lo) if not np.isnan(s)}
    return {"name": "Lowest band", "parent": "Baseline",
            "description": "Admit rates 0.9 in the lowest score band, 0.02 elsewhere: the spread bands are the lowest",
            "overrides": {"admit_rate": rate}}


def unscored_near_scenario(cells, cfg):
    """[R4-09] Unscored admit rates 1.0 and the two lowest scored bands' rates x 1.8 (at most 1): the 25th percentile
    band is 158 when unscored are excluded and 154 when they count below every bound."""
    from sw import ledger as L
    b0 = L.baseline(cells, cfg)
    low2 = sorted({float(x) for x in cells.score_lo if not np.isnan(x)})[1:3]
    rate = {}
    for i, (c, s) in enumerate(zip(cells.cell_id, cells.score_lo)):
        if np.isnan(s):
            rate[c] = 1.0
        elif float(s) in low2:
            rate[c] = float(min(1.0, b0.admit_rate[i] * 1.8))
    return {"name": "Unscored near the 25th", "parent": "Baseline",
            "description": "Unscored admit rates 1.0; the two lowest scored bands x 1.8: 'below' moves the 25th band",
            "overrides": {"admit_rate": rate}}


def scenarios():
    from sw import config
    cfg = config.validate(config_dict())
    cells = world(cfg)
    return SCENARIOS + [no_merit_scenario(cells), lowest_band_scenario(cells), unscored_near_scenario(cells, cfg)]


def write(out_dir, below=False):
    os.makedirs(out_dir, exist_ok=True)
    cp = os.path.join(out_dir, "edge_config.yaml")
    sp = os.path.join(out_dir, "edge_scenarios.yaml")
    with open(cp, "w") as f:
        f.write("# Edge workbook config (tests/edge.py): synthetic.yaml with edge settings. Every value is synthetic.\n")
        yaml.safe_dump(config_dict(below), f, sort_keys=False)
    with open(sp, "w") as f:
        f.write("# Edge workbook scenarios (tests/edge.py). Every value is synthetic.\n")
        yaml.safe_dump({"scenarios": scenarios()}, f, sort_keys=False)
    return cp, sp


__all__ = ["write", "world", "config_dict", "SCENARIOS", "scenarios", "no_merit_scenario", "lowest_band_scenario",
           "unscored_near_scenario",
           "EXEMPT", "segment_pool_min", "np"]
