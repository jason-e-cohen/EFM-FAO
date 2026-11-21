"""Test 18: Excel equals Python for the v0.6 blocks (spec section 11): segment block, incentive block, class-size table,
pool strip and the two net-tuition lines, each against a fresh call of the Python reference function. Also the two
narratives per scenario (spec section 8), Excel text against `sw.narrative`.

The Excel segment probability is the normal form; its gap to the Python exact value is reported in
output/phase2/test18_report.json, not asserted (spec test 13).

Phase 2.1 [v0.6.2]: ignored award entries counted and marked separately (P2-03), no unfilled template text (P2-04),
number formats (P2-05), the rebuild-needed, stale and scope-error Checks rows on an edited copy (P2-06, P2-07), and
bonus_pool_usd (Q-8d).
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
            want = [row["class_mean"], row["p_class_over_cap"]]                    # [v0.6.3, BM-3]
            for key in targets:
                want += [row["median"][key]["margin"], row["median"][key]["p"]]
            for key in risk.pct_targets(cfg):                                       # [v0.6.3, BM-1]
                if key[0] != 0.5:                                                   # R4-03: q = 0.5 left out
                    want += [row["pct"][key]["margin"], row["pct"][key]["p"]]
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
            want = ([row["growth"], row["class_mean"], row["p_class_over_cap"], row["ntr_mean"], row["ntr_sd"]]
                    + [x for t in run.cfg["score"]["median_thresholds"]                     # F-4: every median,
                       for x in (row["median"][t]["margin"], row["median"][t]["p"])]       # then q other than 0.5
                    + [row["pct"][k]["p"] for k in risk.pct_targets(run.cfg) if k[0] != 0.5] + [row["marker"]])
            assert len(got) == len(want)
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
    # R4-02: the two sentences follow the figures, two rows per scenario, merged from column B
    r1 = r0 + len(run.scenarios)
    for j, s in enumerate(run.scenarios):
        tw = strip.tuition(run.lcs[s.name]["middle"])
        assert ws.cell(r1 + 2 * j, 1).value == s.name
        assert ws.cell(r1 + 2 * j, 2).value == tw["net_tuition_line_fixed_text"]
        assert ws.cell(r1 + 2 * j + 1, 2).value == tw["net_tuition_line_scaled_text"]


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


# ---------------------------------------------------------------------------------------------------------------
# Phase 2.1 [v0.6.2]

def _levers_row(bundle, r):
    lay = bundle["info"]["layout"]
    ws = bundle["values"]["Levers"]
    return {s.name: ws.cell(r + 1, lay["vblock"][s.name] + 1).value for s in bundle["info"]["run"].scenarios}


def test_ignored_award_entries_counted_separately(main_wb):
    """P2-03: the award typed on the full-tuition cell in-170-hi is not an award change; it is counted, marked in the
    note column beside the cell and reported in the narrative."""
    run, wb, info = main_wb["info"]["run"], main_wb["values"], main_wb["info"]
    lay = info["layout"]
    ws = wb["Levers"]
    labels_col = {ws.cell(r, 1).value: r for r in range(1, lay["r0v"] + 1)}
    changed = _levers_row(main_wb, labels_col["awards changed from parent (cells)"] - 1)
    ignored = _levers_row(main_wb, labels_col["award entries ignored (full-tuition flag set)"] - 1)
    for s in run.scenarios:
        ch, ig = L.award_changes(run.cells, run.cfg, s, run.parents[s.name])
        assert ignored[s.name] == int(ig.sum())
        if run.parents[s.name] is not None:
            assert changed[s.name] == int(ch.sum())
    assert changed["Smaller class, scaled awards"] == 2 and ignored["Smaller class, scaled awards"] == 1
    c0 = lay["vblock"]["Smaller class, scaled awards"]
    marks = {run.cells.cell_id[i]: ws.cell(lay["r0v"] + 1 + i, c0 + 4).value for i in range(run.cells.n)}
    assert {k for k, v in marks.items() if v} == {"in-170-hi"}
    assert marks["in-170-hi"] == labels.AWARD_IGNORED
    assert narrative.changes(run, info["vals"], run.scen("Smaller class, scaled awards")).endswith(
        " " + labels.AWARDS_IGNORED_ONE)


def test_no_unfilled_template_text(main_wb, edge_wb):
    """P2-04: no cell shows a template field such as '{s}'."""
    import re
    pat = re.compile(r"\{[a-z_]+\}")
    for bundle in (main_wb, edge_wb):
        for ws in bundle["values"].worksheets:
            for row in ws.iter_rows():
                for c in row:
                    assert not (isinstance(c.value, str) and pat.search(c.value)), (ws.title, c.coordinate, c.value)
    ws = main_wb["values"]["Summary"]
    shock = [ws.cell(r, 2).value for r in range(1, ws.max_row + 1)
             if ws.cell(r, 1).value == labels.LEGEND_NAMES["SHOCK_LABEL"]]
    assert shock == [labels.shock_label(main_wb["info"]["run"].cfg["risk"]["common_shock_sd"])]


def test_number_formats(main_wb):
    """P2-05: no format with a trailing optional decimal; counts #,##0, dollars $#,##0, scores and flags 0, rates
    0.0000."""
    import openpyxl
    wb = openpyxl.load_workbook(main_wb["path"])
    lay = main_wb["info"]["layout"]
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                assert ".#" not in (c.number_format or ""), (ws.title, c.coordinate, c.number_format)
    h = wb["History"]
    first = h.cell(7, 1).value
    assert first == main_wb["info"]["run"].cells.cell_id[0]
    fmts = {h.cell(4, c).value: h.cell(7, c).number_format for c in range(8, h.max_column + 1)
            if h.cell(4, c).value in ("Applications", "Award $", "Admit rate", "Yield")}
    assert fmts == {"Applications": "#,##0", "Award $": "$#,##0", "Admit rate": "0.0000", "Yield": "0.0000"}
    assert h.cell(7, 4).number_format == "0" and h.cell(7, 5).number_format == "0"     # score_lo, scored
    lv = wb["Levers"]
    c0 = lay["vblock"]["Baseline"] + 1
    r = lay["r0v"] + 1
    assert (lv.cell(r, c0).number_format, lv.cell(r, c0 + 1).number_format, lv.cell(r, c0 + 2).number_format) \
        == ("0.0000", "$#,##0", "0")


def _check_rows(ws):
    out = {}
    for r in range(1, ws.max_row + 1):
        out.setdefault((ws.cell(r, 1).value, ws.cell(r, 2).value), ws.cell(r, 3).value)
    return out


def test_new_checks_rows_ok_on_the_built_workbook(main_wb, edge_wb):
    for bundle in (main_wb, edge_wb):
        rows = _check_rows(bundle["values"]["Checks"])
        for (chk, scope), v in rows.items():
            if isinstance(chk, str) and (chk.startswith("Trim") or chk.startswith("Static exact")
                                         or chk.startswith("Bonus scope")):
                assert v == "OK", (chk, scope, v)
    rows = _check_rows(edge_wb["values"]["Checks"])
    budget = [v for (c, s), v in rows.items() if isinstance(c, str) and c.startswith("Spend against budget_total")]
    assert budget and all(v.startswith(("OK: merit $", "merit $")) for v in budget)
    rec = [v for (c, s), v in rows.items() if isinstance(c, str) and c.startswith("History reconciliation")]
    assert sum(v.startswith("grid-implied $") for v in rec) == 2 and sum(v.startswith("not run") for v in rec) == 1


def test_checks_flag_rebuild_stale_and_scope_error(main_wb, lo_profile):
    """P2-06, P2-07 on an edited copy of the main workbook: change the first median threshold and protect_segment on
    Inputs, the segment goal of 'Segment incentive', and give 'Out-of-state incentive' scope 'segment' with a segment
    no cell carries. After recalculation Checks shows 'rebuild needed', the stale exact probability and the scope
    error; Ledger shows the default segment where Levers is blank."""
    import openpyxl
    from sw import lo
    run, lay = main_wb["info"]["run"], main_wb["info"]["layout"]
    wb = openpyxl.load_workbook(main_wb["path"])

    def first(name):
        (sheet, coord), = list(wb.defined_names[name].destinations)
        return wb[sheet][coord.replace("$", "").split(":")[0]]
    first("in_median_thresholds").value = 165
    first("in_protect_segment").value = "none"
    lv = wb["Levers"]
    vr = lay["vfield_row"]
    lv.cell(vr["segment_goal"] + 1, lay["vblock"]["Segment incentive"] + 1).value = 30
    lv.cell(vr["bonus_scope"] + 1, lay["vblock"]["Out-of-state incentive"] + 1).value = "segment"
    lv.cell(vr["segment"] + 1, lay["vblock"]["Out-of-state incentive"] + 1).value = "nobody"
    assert lv.cell(vr["segment"] + 1, lay["vblock"]["Baseline"] + 1).value in (None, "")
    out = os.path.join(PHASE2, "edited")
    os.makedirs(out, exist_ok=True)
    src = os.path.join(out, "edited.xlsx")
    wb.save(src)
    rc = lo.recalc(src, os.path.join(out, "recalculated"), profile=lo_profile)
    vals = openpyxl.load_workbook(rc, data_only=True)
    rows = _check_rows(vals["Checks"])
    rb = labels.REBUILD_NEEDED
    assert rows[("Trim order: first median threshold equals its value at build", "Inputs")] == rb.format(build="166")
    assert rows[("Trim order: trim.protect_segment equals its value at build", "Inputs")] == rb.format(
        build="below_threshold")
    assert rows[("Trim order: active segment equals its value at build", "Out-of-state incentive")] == rb.format(
        build="priority")
    assert rows[("Trim order: active segment equals its value at build", "Baseline")] == "OK"
    assert rows[("Static exact segment probability is current (Summary segment block)", "Segment incentive")] \
        == labels.EXACT_STALE
    assert rows[("Static exact segment probability is current (Summary segment block)", "Baseline")] == "OK"
    chk = "Bonus scope 'segment' has segment cells when a bonus, lift or goal is set"
    assert rows[(chk, "Out-of-state incentive")] == labels.SCOPE_ERROR
    assert rows[(chk, "Segment incentive")] == "OK"
    led = vals["Ledger_Middle"]
    assert led.cell(7, lay["lblock"][("middle", "Baseline")]["in_seg"] + 2).value == "priority"
