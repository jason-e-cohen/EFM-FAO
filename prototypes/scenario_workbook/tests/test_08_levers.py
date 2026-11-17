"""Test 8: levers (spec section 11), checked in the recalculated workbook.

A dedicated workbook (world seed 101) carries scenarios built for each property:
  Zero bonus      child of Baseline with bonus_usd 0 (scope segment, minimum score 161) and the parent's tuition
                  increase: equals its parent in every Ledger column and every contract figure
  Shift 0         yield_shift_pts 0 entered explicitly: equals its parent
  Class 120       class_target 120: need_rate unchanged
  Shift +1        yield_shift_pts 1: equals the Baseline yield-strip row at d = 1 (no cell clips there)
  Break-even      yield_shift_pts = Baseline's class break-even shift: expected class equals the target (no clip)
  Overrides       shift 1, out-of-state 2, segment -1: each override applies only to its cells and replaces
  Tuition 5.5     tuition_increase_pct 5.5 (a tuition_grid value)
plus: the tuition what-if row at each scenario's own increase equals its Ledger ntr_y1.
"""
import os

import numpy as np
import pytest
import yaml

from conftest import PHASE2, _build_and_recalc, close, read_range
from sw import CASES, ledger as L, response, strip, synth_cells
from sw.config import load as load_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def levers_wb(lo_profile):
    cfg = load_config(os.path.join(ROOT, "config", "synthetic.yaml"))
    cells = synth_cells.generate(cfg, 101)
    base = response.base_yield(cells, cfg)
    b = L.baseline(cells, cfg)
    lc = L.evaluate(cells, cfg, b, base, "middle")
    be = strip.yield_strip(lc)["breakeven_shift_class"]
    act = lc.admits > 0
    for d in (1.0, be):   # precondition: no active cell clips at these shifts
        y = lc.yld + d / 100.0
        assert ((y[act] <= lc.ycap[act]) & (y[act] >= lc.yfloor[act])).all(), d
    specs = [
        {"name": "Baseline"},
        {"name": "Zero bonus", "parent": "Baseline", "bonus_usd": 0, "bonus_scope": "segment",
         "bonus_min_score": 161},
        {"name": "Shift 0", "parent": "Baseline", "yield_shift_pts": 0},
        {"name": "Class 120", "parent": "Baseline", "class_target": 120},
        {"name": "Shift +1", "parent": "Baseline", "yield_shift_pts": 1},
        {"name": "Break-even", "parent": "Baseline", "yield_shift_pts": float(be)},
        {"name": "Overrides", "parent": "Baseline", "yield_shift_pts": 1, "yield_shift_pts_out": 2,
         "yield_shift_pts_segment": -1},
        {"name": "Tuition 5.5", "parent": "Baseline", "tuition_increase_pct": 5.5},
    ]
    os.makedirs(PHASE2, exist_ok=True)
    path = os.path.join(PHASE2, "scenarios_test08.yaml")
    with open(path, "w") as f:
        yaml.safe_dump({"scenarios": specs}, f, sort_keys=False)
    bundle = _build_and_recalc("levers", path, lo_profile)
    bundle["be"] = be
    return bundle


def _col(bundle, k, s, key):
    lay = bundle["info"]["layout"]
    ws = bundle["values"][lay["case_sheet"][k]]
    c = lay["lblock"][(k, s)][key] + 1
    return [ws.cell(lay["r0l"] + 1 + i, c).value for i in range(lay["n"])]


def _head(bundle, k, s, key):
    lay = bundle["info"]["layout"]
    ws = bundle["values"][lay["case_sheet"][k]]
    return ws.cell(lay["ledger_head_rows"][key] + 1, lay["lblock"][(k, s)]["in_seg"] + 2).value


def _static(bundle, key):
    lay = bundle["info"]["layout"]
    ws = bundle["values"]["Ledger_Middle"]
    return [ws.cell(lay["r0l"] + 1 + i, lay["lstat"][key] + 1).value for i in range(lay["n"])]


def _sk(bundle, name, s, k="middle"):
    run = bundle["info"]["run"]
    j = [x.name for x in run.scenarios].index(s)
    return read_range(bundle["values"], name)[CASES.index(k)][j]


def _equal_to_parent(bundle, s, p):
    keys = ["apps", "rate", "admits", "award_base", "incentive", "award", "yield", "mu", "enrolled", "spend", "w"]
    for k in CASES:
        for key in keys:
            a, b = _col(bundle, k, s, key), _col(bundle, k, p, key)
            assert all(close(x, y, rel=0, abs_=0) for x, y in zip(a, b)), (s, k, key)
    for name in ("SUM_CLASS_MEAN", "SUM_NTR_Y1", "SUM_P_CLASS_OVER_CAP", "SUM_P_MEDIAN_T", "SEG_SEGMENT_ENROLLED"):
        got = read_range(bundle["values"], name)
        run = bundle["info"]["run"]
        names = [x.name for x in run.scenarios]
        js, jp = names.index(s), names.index(p)
        for row in got:
            assert close(row[js], row[jp], rel=0, abs_=0), (s, name)


def test_zero_bonus_child_equals_parent(levers_wb):
    _equal_to_parent(levers_wb, "Zero bonus", "Baseline")
    assert _sk(levers_wb, "INC_INCENTIVE_COST", "Zero bonus") == 0


def test_shift_zero_equals_parent(levers_wb):
    _equal_to_parent(levers_wb, "Shift 0", "Baseline")


def test_need_rate_unchanged_by_class_target(levers_wb):
    for k in CASES:
        assert _head(levers_wb, k, "Class 120", "need_rate") == _head(levers_wb, k, "Baseline", "need_rate")
    e = sum(_col(levers_wb, "middle", "Class 120", "enrolled"))
    assert close(_sk(levers_wb, "SUM_NEED", "Class 120"), _head(levers_wb, "middle", "Class 120", "need_rate") * e)


def test_shift_equals_yield_strip(levers_wb):
    run = levers_wb["info"]["run"]
    grid = run.cfg["risk"]["yield_shift_grid"]
    ys = read_range(levers_wb["values"], "YS_YIELD_STRIP")
    row = ys[grid.index(1)]                       # Baseline block is first
    assert close(row[0], _sk(levers_wb, "SUM_CLASS_MEAN", "Shift +1"))
    assert close(row[1], _sk(levers_wb, "SUM_P_CLASS_OVER_CAP", "Shift +1"))
    assert close(row[3], _sk(levers_wb, "SUM_NTR_Y1", "Shift +1"))
    assert close(row[6], read_range(levers_wb["values"], "SUM_P_MEDIAN_T")[1][4])  # first threshold, Shift +1
    # strip at d = 0 equals the scenario itself
    row0 = ys[grid.index(0)]
    assert close(row0[0], _sk(levers_wb, "SUM_CLASS_MEAN", "Baseline"))


def test_class_breakeven(levers_wb):
    be = read_range(levers_wb["values"], "YS_BREAKEVEN_SHIFT_CLASS")[0][0]
    assert close(be, levers_wb["be"])
    run = levers_wb["info"]["run"]
    target = run.scen("Break-even").class_target
    assert _sk(levers_wb, "SUM_CLASS_MEAN", "Break-even") == pytest.approx(target, rel=1e-9)


def test_overrides_apply_to_their_cells_and_replace(levers_wb):
    res = _static(levers_wb, "residency")
    for k in CASES:
        seg = _col(levers_wb, k, "Overrides", "in_seg")
        sh = _col(levers_wb, k, "Overrides", "shift")
        y1 = np.array(_col(levers_wb, k, "Overrides", "yield"), float)
        y0 = np.array(_col(levers_wb, k, "Baseline", "yield"), float)
        for i, (r, sg, d) in enumerate(zip(res, seg, sh)):
            want = -1 if sg == 1 else (2 if r == "out" else 1)
            assert d == want, (i, r, sg, d)
            assert y1[i] == pytest.approx(y0[i] + want / 100.0, abs=1e-12)


def test_tuition_whatif_at_own_increase_equals_ledger(levers_wb):
    run = levers_wb["info"]["run"]
    grid = run.cfg["risk"]["tuition_grid"]
    tw = read_range(levers_wb["values"], "TW_TUITION_WHATIF")
    names = [s.name for s in run.scenarios]
    checked = 0
    for j, s in enumerate(run.scenarios):
        hit = [g for g, pct in enumerate(grid) if abs(pct - s.tuition_increase_pct) < 1e-9]
        if hit:   # Baseline's increase compounds to 6.000000000000005, so match within 1e-9
            row = tw[j * len(grid) + hit[0]]
            assert close(row[0], _head(levers_wb, "middle", s.name, "T"))
            assert close(row[1], _sk(levers_wb, "SUM_NTR_Y1", s.name))
            checked += 1
    assert checked == len(names)
