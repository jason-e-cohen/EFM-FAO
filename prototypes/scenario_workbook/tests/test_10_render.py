"""Test 10: rendering (spec section 11; Phase 4). Convert Summary to PDF with LibreOffice and save it to
output/phase4/Summary_render.pdf for visual review (Jason reviews the render: Phase 4 acceptance). The render carries the
two Review_Phase2_Build.md cosmetic fixes (parent names wrap; "under 5%" / "over 95%" right-aligned) and the Phase 4
review fixes (Review_Phase4_Build.md R4-01, R4-02): each section laid out on its own, columns narrowed to their content,
long text wrapped with row heights that hold it, the section's header row repeated on every page, wide sections printed
at no less than lo.MIN_SCALE with columns A and B repeated, and the pool strip's working values left out.

The layout checks read the section workbook the PDF is made from (output/phase4/Summary_render_sections.xlsx) and use
their own, more generous character width (1.4 characters per width unit, against the render's 1.3), so they fail on text
the render left too long for its cell rather than repeating the render's own arithmetic. R4-17: the installed
LibreOffice must be the acceptance version in config/tools.yaml.
"""
import math
import os
import shutil

import openpyxl
from openpyxl.utils import get_column_letter

from conftest import ROOT
from sw import lo

PHASE4 = os.path.join(ROOT, "output", "phase4")
CHARS_PER_UNIT = 1.4
LINE_PT = 11.0


def render(bundle, profile, stem):
    os.makedirs(PHASE4, exist_ok=True)
    keep = os.path.join(PHASE4, f"{stem}_sections.xlsx")
    pdf = lo.render_summary_pdf(bundle["path"], os.path.join(PHASE4, "render"), profile=profile, keep_sections=keep)
    dst = os.path.join(PHASE4, f"{stem}.pdf")
    shutil.copyfile(pdf, dst)
    return dst, keep


def layout_problems(sections_path):
    """Sections printed below MIN_SCALE or across too many pages, sections without a repeated header row, and text
    cells longer than their rendered cell (by this test's own width rule)."""
    wb = openpyxl.load_workbook(sections_path)
    bad = []
    for ws in wb.worksheets:
        title = ws.oddHeader.center.text
        maxc = max([c for c in range(1, ws.max_column + 1)
                    if any(ws.cell(r, c).value not in (None, "") for r in range(1, ws.max_row + 1))]
                   + [m.max_col for m in ws.merged_cells.ranges])                 # the printed columns
        def wid(c):
            return ws.column_dimensions[get_column_letter(c)].width or 8.43
        width = {c: wid(c) for c in range(1, maxc + 1)}
        total = sum(lo.col_pt(w) for w in width.values())
        if ws.sheet_properties.pageSetUpPr.fitToPage:
            if lo.PAGE_WIDTH_PT / total < lo.MIN_SCALE:
                bad.append((title, "fit to width below the minimum scale", round(lo.PAGE_WIDTH_PT / total, 2)))
        else:
            if (ws.page_setup.scale or 100) < 100 * lo.MIN_SCALE:
                bad.append((title, "scale", ws.page_setup.scale))
            if ws.print_title_cols != "$A:$B":
                bad.append((title, "columns A:B not repeated", ws.print_title_cols))
            ab = lo.col_pt(width[1]) + lo.col_pt(width[2])
            across = math.ceil((total - ab) / (lo.PAGE_WIDTH_PT / (ws.page_setup.scale / 100) - ab))
            if across > lo.MAX_PAGES_ACROSS:
                bad.append((title, "pages across", across))
        heads = [r for r in range(2, ws.max_row + 1) if lo._is_header(ws.cell(r, 1))]
        if heads and not ws.print_title_rows:
            bad.append((title, "header row not repeated", heads[0]))
        top, covered = lo._merged_at(ws)
        for r in range(2, ws.max_row + 1):
            h = ws.row_dimensions[r].height or 12.0
            for c in range(1, maxc + 1):
                cell = ws.cell(r, c)
                if (r, c) in covered or not isinstance(cell.value, str) or not cell.value:
                    continue
                c0, c1 = top.get((r, c), (c, c))
                wrap = cell.alignment is not None and cell.alignment.wrap_text
                if (r, c) not in top and not wrap:            # unwrapped text may run on into empty cells
                    while c1 + 1 <= maxc and ws.cell(r, c1 + 1).value in (None, "") and (r, c1 + 1) not in covered \
                            and (r, c1 + 1) not in top:
                        c1 += 1
                cap = CHARS_PER_UNIT * sum(wid(k) for k in range(c0, c1 + 1))
                bold = bool(cell.font is not None and cell.font.b)
                n = lo.eff_len(cell.value, bold)
                lines = max(1, int(h // LINE_PT)) if wrap else 1
                words_fit = all(lo.eff_len(w, bold) <= cap for w in cell.value.split())
                if n > cap * lines or not words_fit:
                    bad.append((title, cell.coordinate, cell.value[:60], round(n), round(cap * lines)))
    return bad


def test_render_summary_pdf(main_wb, lo_profile):
    dst, keep = render(main_wb, lo_profile, "Summary_render")
    assert os.path.getsize(dst) > 10_000
    bad = layout_problems(keep)
    assert not bad, bad[:10]
    wb = openpyxl.load_workbook(keep)
    titles = [ws.oddHeader.center.text for ws in wb.worksheets]
    assert not any(t.startswith(lo.SKIP_PREFIX) for t in titles)          # R4-01: working values not printed
    # the Summary sheet itself: the working values lie below its print area
    ws = openpyxl.load_workbook(main_wb["path"])["Summary"]
    area = ws.print_area[0] if isinstance(ws.print_area, (list, tuple)) else ws.print_area
    last = int(str(area).split("$")[-1])
    rows = [r for r in range(1, ws.max_row + 1) if str(ws.cell(r, 1).value or "").startswith(lo.SKIP_PREFIX)]
    assert rows and rows[0] > last


def test_layout_check_catches_cut_text(main_wb, lo_profile, tmp_path):
    """The layout check fails a section whose long label is not wrapped (a copy with one label's wrap removed)."""
    keep = os.path.join(PHASE4, "Summary_render_sections.xlsx")
    if not os.path.exists(keep):
        render(main_wb, lo_profile, "Summary_render")
    wb = openpyxl.load_workbook(keep)
    from copy import copy
    ws = wb.worksheets[1]
    top, _ = lo._merged_at(ws)
    r = next(r for r in range(2, ws.max_row + 1) if isinstance(ws.cell(r, 1).value, str)
             and len(ws.cell(r, 1).value) > 80 and (r, 1) not in top and ws.cell(r, 2).value)
    al = copy(ws.cell(r, 1).alignment)
    al.wrap_text = False
    ws.cell(r, 1).alignment = al
    p = str(tmp_path / "cut.xlsx")
    wb.save(p)
    assert any(b[1] == ws.cell(r, 1).coordinate for b in layout_problems(p))


def test_libreoffice_is_the_acceptance_version(soffice):
    """R4-17 (DECISIONS Nov 19: LibreOffice 26.8 is the acceptance version): results can depend on the engine version
    (the Checks rounding probe), so the installed soffice must report the pinned version."""
    pinned = lo.acceptance_version()
    assert pinned, "config/tools.yaml has no libreoffice_acceptance_version"
    assert lo.installed_version(soffice) == pinned
