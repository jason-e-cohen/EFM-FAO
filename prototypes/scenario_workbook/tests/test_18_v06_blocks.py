"""Test 18: Excel equals Python for the v0.6 blocks (spec section 11): segment block, incentive block, class-size table,
pool strip and the two net-tuition lines, each against a fresh call of the Python reference function. Also the two
narratives per scenario (spec section 8), Excel text against `sw.narrative`.

The Excel segment probability is the normal form; its gap to the Python exact value is reported in
output/phase2/test18_report.json, not asserted (spec test 13).
"""
import json
import os

import pytest

from conftest import PHASE2, close, read_range
from sw import CASES, labels, ledger as L, narrative, risk, strip, trim


def _summary_row(wb, label, n):
    ws = wb["Summary"]
    for r in range(1, ws.max_row + 1):
        if ws.cell(r, 1).value == label:
            return [ws.cell(r, 3 + j).value for j in range(n)]
    raise KeyError(label)


def test_segment_block(main_wb):
    run, wb = main_wb["info"]["run"], main_wb["values"]
    S = run.scenarios
    rows = {n: read_range(wb, f"SEG_{n.upper()}") for n in ("segment_enrolled", "segment_lo90", "segment_hi90",
                                                            "p_segment_goal", "segment_share")}
    gaps = []
    for ki, k in enumerate(CASES):
        for j, s in enumerate(S):
            sg = L.segment(run.lcs[s.name][k])
            for n in ("segment_enrolled", "segment_lo90", "segment_hi90", "segment_share"):
                assert close(rows[n][ki][j], sg[n]), (n, k, s.name)
            if s.segment_goal is None:
                assert rows["p_segment_goal"][ki][j] == ""
            else:
                assert close(rows["p_segment_goal"][ki][j], sg["p_segment_goal_normal"]), (k, s.name)
                gaps.append({"scenario": s.name, "case": k, "goal": sg["segment_goal"],
                             "expected": sg["segment_enrolled"], "excel_normal": rows["p_segment_goal"][ki][j],
                             "python_exact": sg["p_segment_goal"],
                             "gap": rows["p_segment_goal"][ki][j] - sg["p_segment_goal"]})
    with open(os.path.join(PHASE2, "test18_report.json"), "w") as f:
        json.dump({"segment_normal_vs_exact": gaps}, f, indent=1)
    assert gaps, "the synthetic scenarios set a segment goal"
    n = len(S)
    mid = {s.name: L.segment(run.lcs[s.name]["middle"]) for s in S}
    for label, key in [("Segment applications", "segment_apps"), ("Segment admits", "segment_admits"),
                       ("Segment merit dollars", "segment_merit"), ("Segment goal (rounded up)", "segment_goal")]:
        got = _summary_row(wb, label, n)
        for j, s in enumerate(S):
            assert close(got[j], "" if mid[s.name][key] is None else mid[s.name][key]), (label, s.name)
    exact = _summary_row(wb, "P(segment enrolled at or above goal), exact (static, from the build)", n)
    for j, s in enumerate(S):
        if s.segment_goal is not None:
            assert exact[j] == pytest.approx(risk.segment_exact(run.lcs[s.name]["middle"], mid[s.name]["segment_goal"]),
                                             abs=1e-12)
    flag = _summary_row(wb, "Approximation flag", n)
    for j, s in enumerate(S):
        assert flag[j] in ("", None) if mid[s.name]["segment_enrolled"] >= 30 else flag[j] == labels.SEGMENT_APPROX


def test_incentive_block(main_wb):
    run, wb = main_wb["info"]["run"], main_wb["values"]
    S = run.scenarios
    names = ("incentive_cost", "incentive_paid_anyway", "incentive_paid_anyway_share", "additional_enrollees",
             "aid_per_additional", "ntr_per_additional", "incentive_valid")
    rows = {n: read_range(wb, f"INC_{n.upper()}") for n in names}
    seen_valid = set()
    for ki, k in enumerate(CASES):
        for j, s in enumerate(S):
            p = run.parents[s.name]
            if p is None:
                assert close(rows["incentive_cost"][ki][j], L.money(run.lcs[s.name][k])["incentive_cost"])
                for n in names[1:]:
                    assert rows[n][ki][j] == ""
                continue
            inc = L.incentive(run.lcs[s.name][k], run.lcs[p.name][k])
            for n in names:
                assert close(rows[n][ki][j], inc[n]), (n, k, s.name)
            seen_valid.add(inc["incentive_valid"])
    assert seen_valid == {labels.INCENTIVE_VALID, labels.INCENTIVE_NOT_VALID}
    n = len(S)
    for label, key in [("Change in merit dollars (dSpend)", "merit_change"),
                       ("Change in ntr_y1 over the same cells (dNTR)", "ntr_change")]:
        got = _summary_row(wb, label, n)
        for j, s in enumerate(S):
            p = run.parents[s.name]
            want = "" if p is None else L.incentive(run.lcs[s.name]["middle"], run.lcs[p.name]["middle"])[key]
            assert close(got[j], want), (label, s.name)


def test_class_size_table(main_wb):
    run, wb = main_wb["info"]["run"], main_wb["values"]
    cfg = run.cfg
    ct = read_range(wb, "CT_CLASS_TABLE")
    Ns = cfg["class"]["what_if"]
    targets = risk.median_targets(cfg)
    bands = [float(b) for b in cfg["score"]["bands"]] + ["unscored"]
    statuses = set()
    for j, s in enumerate(run.scenarios):
        py = trim.class_table(run.cells, cfg, s, run.base)["class_table"]
        for g, row in enumerate(py):
            got = ct[j * len(Ns) + g]
            assert close(got[0], row["f"]) and got[-1] == row["status"], (s.name, row["N"])
            statuses.add(row["status"])
            got = got[:-1]
            if "class_mean" not in row:
                assert all(v == "" for v in got[1:])
                continue
            want = [row["class_mean"]]
            for key in targets:
                want += [row["median"][key]["margin"], row["median"][key]["p"]]
            want += [row["ntr_y1"], row["discount_entering_y1"], row["segment_enrolled"],
                     "" if row["lowest_band_admitted"] is None else row["lowest_band_admitted"]]
            want += [row["admits_cut_by_band"].get(b, 0.0) for b in bands]
            assert len(got[1:]) == len(want)
            for c, (gv, wv) in enumerate(zip(got[1:], want)):
                assert close(gv, wv), (s.name, row["N"], c, wv, gv)
    assert labels.CT_OK in statuses and labels.CT_NOT_APPLICABLE in statuses


def test_pool_strip(main_wb):
    run, wb = main_wb["info"]["run"], main_wb["values"]
    ps = read_range(wb, "PS_POOL_STRIP")
    grid = run.cfg["risk"]["pool_grid"]
    for j, s in enumerate(run.scenarios):
        py = strip.pool_strip(run.cells, run.cfg, s, run.base)["pool_strip"]
        for g, row in enumerate(py):
            got = ps[j * len(grid) + g]
            want = [row["growth"], row["class_mean"], row["p_class_over_cap"], row["margin"], row["p_median"],
                    row["ntr_mean"], row["ntr_sd"]]
            for gv, wv in zip(got, want):
                assert close(gv, wv), (s.name, row["pool_multiplier"])


def test_net_tuition_lines(main_wb):
    run, wb = main_wb["info"]["run"], main_wb["values"]
    fixed = read_range(wb, "TW_NET_TUITION_LINE_FIXED")
    scaled = read_range(wb, "TW_NET_TUITION_LINE_SCALED")
    ws = wb["Summary"]
    (sheet, coord), = list(wb.defined_names["TW_NET_TUITION_LINE_FIXED"].destinations)
    r0 = ws[coord.replace("$", "").split(":")[0]].row
    for j, s in enumerate(run.scenarios):
        tw = strip.tuition(run.lcs[s.name]["middle"])
        assert close(fixed[j][0], tw["net_tuition_line_fixed"])
        assert close(scaled[j][0], tw["net_tuition_line_scaled"])
        assert close(ws.cell(r0 + j, 3).value, tw["example_award"])
        assert ws.cell(r0 + j, 5).value == tw["net_tuition_line_fixed_text"]
        assert ws.cell(r0 + j, 6).value == tw["net_tuition_line_scaled_text"]


def test_narratives(main_wb):
    run, wb = main_wb["info"]["run"], main_wb["values"]
    vals = main_wb["info"]["vals"]
    ws = wb["Summary"]
    found, current = {}, None
    for r in range(1, ws.max_row + 1):
        kind = ws.cell(r, 2).value
        if kind in ("Changes from parent", "Projected outcome"):
            current = ws.cell(r, 1).value or current       # the name is on the first row of each pair
            found[(current, kind)] = ws.cell(r, 3).value
    for s in run.scenarios:
        assert found[(s.name, "Changes from parent")] == narrative.changes(run, vals, s)
        out = found[(s.name, "Projected outcome")]
        assert out == narrative.outcome(run, vals, s)
        assert labels.RESPONSE_LABEL in out
        if s.yield_shift_pts or s.yield_shift_pts_out or s.segment_pool_lift_pct:
            assert labels.ASSUMPTION_LABEL in out


def test_full_tuition_conflict_listed(main_wb):
    """P1.1-1: the Checks sheet lists each cell where an award is entered on a full-tuition cell. The synthetic
    'Smaller class, scaled awards' scenario types an award on in-170-hi, which carries the flag."""
    run, wb = main_wb["info"]["run"], main_wb["values"]
    ws = wb["Checks"]
    listed, result = {}, {}
    for r in range(1, ws.max_row + 1):
        a, b, c = ws.cell(r, 1).value, ws.cell(r, 2).value, ws.cell(r, 3).value
        if a == "Full-tuition award conflicts (P1.1-1)":
            result[b] = c
        if isinstance(a, str) and a.strip().startswith("conflict ") and c:
            listed.setdefault(b, []).append(c)
    for s in run.scenarios:
        conf = L.full_tuition_conflicts(run.cells, run.cfg, s, run.parents[s.name])
        want = list(run.cells.cell_id[conf])
        assert listed.get(s.name, []) == want, s.name
        assert (result[s.name] == "OK") == (not want)
    assert listed["Smaller class, scaled awards"] == ["in-170-hi"]
    # the entered award is ignored: the Ledger award there is tuition
    lc = run.lcs["Smaller class, scaled awards"]["middle"]
    i = run.cells.index("in-170-hi")
    assert lc.award_base[i] == lc.tuition
