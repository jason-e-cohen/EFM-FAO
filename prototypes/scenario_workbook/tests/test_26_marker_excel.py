"""Test 26 [v0.6.3, BM-6] (Review_Phase2_2_Plan.md section 4, task 6): growth to date is display only.

On a copy of the main workbook, edit Inputs pool_ytd_growth (0.12 to 0.33) and recalculate in LibreOffice; a second copy
is saved the same way without the edit. Only the marker cells change: the growth shown beside the pool strip, the
nearest-row cell (Phase 4.2: it shows that row's pool multiplier) and the marker column (every other formula cell is
identical), and the marker moves from the row of m = 1.1 to the row of m = 1.3 in every scenario's block.

R4-13: growth 0.15 (an exact midpoint) marks the 1.2 row in Excel. R4-10, R4-11: in an edited copy, a q = 0.5 target's t
follows the median threshold, the implied tuition increase follows tuition_by_year_usd, and Checks reports all_jd with
a blank continuing_ntr_usd.
"""
import os

import openpyxl

from conftest import PHASE2


def _copy(src, out, growth, profile):
    from sw import lo
    wb = openpyxl.load_workbook(src)
    if growth is not None:
        (sheet, coord), = list(wb.defined_names["in_pool_ytd_growth"].destinations)
        wb[sheet][coord.replace("$", "")].value = growth
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, "copy.xlsx")
    wb.save(p)
    return openpyxl.load_workbook(lo.recalc(p, os.path.join(out, "recalculated"), profile=profile), data_only=True)


def test_only_the_marker_cells_change(main_wb, lo_profile):
    from sw import labels
    run, info = main_wb["info"]["run"], main_wb["info"]
    assert run.cfg["pool_ytd_growth"] == 0.12
    base = _copy(main_wb["path"], os.path.join(PHASE2, "marker_base"), None, lo_profile)
    edit = _copy(main_wb["path"], os.path.join(PHASE2, "marker_edit"), 0.33, lo_profile)
    marker = set(info["layout"]["marker_cells"])
    grid = run.cfg["risk"]["pool_grid"]
    assert len(marker) == 2 + len(grid) * len(run.scenarios)
    changed = set()
    for (sheet, r, c) in info["expected"]:
        if base[sheet].cell(r + 1, c + 1).value != edit[sheet].cell(r + 1, c + 1).value:
            changed.add((sheet, r, c))
    assert changed and changed <= marker, sorted(changed - marker)[:5]
    text = labels.POOL_YTD_MARKER.format(as_of="2026-11-15")
    mcells = [m for m in info["layout"]["marker_cells"][2:]]
    for wb, row in ((base, grid.index(1.1)), (edit, grid.index(1.3))):
        for j in range(len(run.scenarios)):
            vals = [wb[sh].cell(r + 1, c + 1).value or "" for sh, r, c in mcells[j * len(grid):(j + 1) * len(grid)]]
            assert vals == [text if i == row else "" for i in range(len(grid))]
    sh, r, c = info["layout"]["marker_cells"][1]
    assert base[sh].cell(r + 1, c + 1).value == 1.1                     # Phase 4.2: the multiplier, not the row
    assert edit[sh].cell(r + 1, c + 1).value == 1.3


def _edit(src, out, edits, profile):
    """Copy src with {defined name or (name, index): value} edits on Inputs, recalculate, return values."""
    from sw import lo
    wb = openpyxl.load_workbook(src)
    for key, v in edits.items():
        name, i = key if isinstance(key, tuple) else (key, 0)
        (sheet, coord), = list(wb.defined_names[name].destinations)
        cells = wb[sheet][coord.replace("$", "")]
        cell = cells[0][i] if isinstance(cells, tuple) else cells
        cell.value = v
    os.makedirs(out, exist_ok=True)
    p = os.path.join(out, "copy.xlsx")
    wb.save(p)
    return openpyxl.load_workbook(lo.recalc(p, os.path.join(out, "recalculated"), profile=profile), data_only=True)


def test_growth_tie_marks_the_upper_row_in_excel(main_wb, lo_profile):
    """R4-13: 1 + 0.15 is the midpoint of 1.1 and 1.2; the marker goes to the 1.2 row in Excel as in Python."""
    info = main_wb["info"]
    grid = info["run"].cfg["risk"]["pool_grid"]
    wb = _edit(main_wb["path"], os.path.join(PHASE2, "marker_tie"), {"in_pool_ytd_growth": 0.15}, lo_profile)
    sh, r, c = info["layout"]["marker_cells"][1]
    assert wb[sh].cell(r + 1, c + 1).value == grid[grid.index(1.2)]


def test_live_inputs_median_tuition_and_goal_basis(main_wb, lo_profile):
    """R4-10, R4-11. In one edited copy of the main workbook: (a) the first median threshold moved from 166 to 165:
    the q = 0.5 percentile target that reads it follows (Inputs pct_t), and P(median) at the first threshold now equals
    P(median) at the second, also 165 (F-4: q = 0.5 targets have no percentile range of their own); (b) tuition_by_year_usd for the plan year set: the implied increase on Inputs is
    100 x (dollars / tuition_base - 1) and Baseline's Ledger tuition is the dollar figure; (c) ntr_goal_basis set to
    all_jd with continuing_ntr_usd blank: the Checks row reports it."""
    from conftest import close, read_range
    from sw import labels
    run, info = main_wb["info"]["run"], main_wb["info"]
    cfg = run.cfg
    assert cfg["score"]["median_thresholds"][0] == 166 and cfg.get("continuing_ntr_usd") is None
    plan = cfg["cycle"]["plan_cycle"]
    yrs = sorted(set(cfg["tuition_increase_by_year"]) | set(cfg.get("tuition_by_year_usd") or {}))
    usd = 58000.0
    wb = _edit(main_wb["path"], os.path.join(PHASE2, "live_inputs"),
               {("in_median_thresholds", 0): 165, ("in_tuition_by_year_usd", yrs.index(plan)): usd,
                "in_ntr_goal_basis": "all_jd"}, lo_profile)
    # (a)
    pt = read_range(wb, "in_pct_t")[0]
    jq = [i for i, p in enumerate(cfg["score"]["percentile_targets"]) if p["q"] == 0.5][0]
    assert pt[jq] == 165
    nS, nc = len(run.scenarios), 3
    assert cfg["score"]["median_thresholds"][1] == 165
    pm = read_range(wb, "SUM_P_MEDIAN_T")
    assert all(close(a, b) for ra, rb in zip(pm[0:nc], pm[nc:2 * nc]) for a, b in zip(ra, rb))
    assert not all(close(a, b) for ra, rb in zip(read_range(main_wb["values"], "SUM_P_MEDIAN_T")[0:nc],
                                                 pm[0:nc]) for a, b in zip(ra, rb))      # the edit moved it
    # (b)
    tb = float(cfg["tuition_base"])
    imp = read_range(wb, "in_tuition_implied_pct")[0][yrs.index(plan)]
    assert close(imp, 100 * (usd / tb - 1))
    lay = info["layout"]
    ws = wb[lay["case_sheet"]["middle"]]
    assert close(ws.cell(lay["ledger_head_rows"]["T"] + 1, lay["lblock"][("middle", run.scenarios[0].name)]["in_seg"]
                         + 2).value, usd)
    # (c)
    texts = [wb["Checks"].cell(r, 3).value for r in range(1, wb["Checks"].max_row + 1)]
    assert labels.ALL_JD_NEEDS_CONTINUING in texts
    base = openpyxl.load_workbook(main_wb["recalc_path"], data_only=True)
    assert labels.ALL_JD_NEEDS_CONTINUING not in [base["Checks"].cell(r, 3).value
                                                   for r in range(1, base["Checks"].max_row + 1)]
    assert nS > 0
