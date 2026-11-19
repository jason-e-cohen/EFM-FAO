"""Test 26 [v0.6.3, BM-6] (Review_Phase2_2_Plan.md section 4, task 6): growth to date is display only.

On a copy of the main workbook, edit Inputs pool_ytd_growth (0.12 to 0.33) and recalculate in LibreOffice; a second copy
is saved the same way without the edit. Only the marker cells change: the growth shown beside the pool strip, the
nearest-row cell and the marker column (every other formula cell is identical), and the marker moves from the row of
m = 1.1 to the row of m = 1.3 in every scenario's block.
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
    assert base[sh].cell(r + 1, c + 1).value == grid.index(1.1) + 1
    assert edit[sh].cell(r + 1, c + 1).value == grid.index(1.3) + 1
