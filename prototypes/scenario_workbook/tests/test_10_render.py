"""Test 10: rendering (spec section 11; Phase 4). Convert Summary to PDF with LibreOffice and save it to
output/phase4/Summary_render.pdf for visual review (Jason reviews the render: Phase 4 acceptance). The render carries the
two Review_Phase2_Build.md cosmetic fixes (parent names wrap; "under 5%" / "over 95%" right-aligned) and the Phase 4
review fixes (Review_Phase4_Build.md R4-01, R4-02): each section laid out on its own, columns narrowed to their content,
long text wrapped with row heights that hold it, the section's header row repeated on every page, wide sections printed
at no less than lo.MIN_SCALE with columns A and B repeated, and the pool strip's working values left out.

The layout checks read the section workbook the PDF is made from (output/phase4/Summary_render_sections.xlsx). They use
Arial's glyph widths (lo.text_pt; the physical font data) but their own margins, LibreOffice's cell margins and one
space of clearance, rather than the render's padding, so they fail on text the render left too long for its cell
rather than repeating the render's own arithmetic. Phase 4.2 (Review_Phase4_FixPass.md item 6): text in a figure column
(C onward) must fit its own cell. The earlier check let unwrapped text run on into empty cells as far as the section's
last used column, and the notes are merged two columns past the last scenario column, so "not used (entering_y1)",
"approximate (fewer than 30 expected)" and "change under half a student" in the last scenario column passed while they
printed past it (pp. 4, 6 and 7 of the Nov 20 render). A text whose right-hand neighbour holds text must also end a
space short of its cell on every line LibreOffice lays out (the Nov 20 headers "mean ntr_y1" and "ntr_y1 SD" ran into
their neighbours). R4-17: the installed LibreOffice must be the acceptance version in config/tools.yaml.
"""
import math
import os
import shutil

import openpyxl
import pytest
from openpyxl.utils import get_column_letter

from conftest import ROOT
from sw import lo

PHASE4 = os.path.join(ROOT, "output", "phase4")
LINE_PT = 11.0          # a line of 9 pt text
CHECK_PAD_PT = 2.8      # LibreOffice's cell margins, left and right together
CLEAR_PT = 2.5          # one space at 9 pt: closer than this, two cells' texts read as one


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
        if not ws.sheet_properties.pageSetUpPr.fitToPage:
            # Phase 4.2: a section continued across pages repeats only A:B, so its title and notes sit within A:B
            hr = heads[0] if heads else ws.max_row + 1
            for (r, c0), (_, c1) in top.items():
                if r < hr and c0 == 1 and c1 > 2:
                    bad.append((title, "heading wider than A:B on a section continued across pages", r))
            if (1, 1) not in top and isinstance(ws.cell(1, 1).value, str):
                b1, s1, _ = lo.font_of(ws.cell(1, 1))
                if lo.text_pt(ws.cell(1, 1).value, b1, s1) > lo.col_pt(width[1]) + lo.col_pt(width[2]) - CHECK_PAD_PT:
                    bad.append((title, "title wider than A:B on a section continued across pages", 1))
        for r in range(1, ws.max_row + 1):                 # Phase 4.2: the title row too
            h = ws.row_dimensions[r].height or 12.0
            for c in range(1, maxc + 1):
                cell = ws.cell(r, c)
                if (r, c) in covered or not isinstance(cell.value, str) or not cell.value:
                    continue
                c0, c1 = top.get((r, c), (c, c))
                wrap = cell.alignment is not None and cell.alignment.wrap_text
                # only column A's unwrapped text may run on: into an empty column B, or a section title across its
                # empty row
                if (r, c) not in top and not wrap and c == 1:
                    last = maxc if lo.is_title(cell) else 2
                    while c1 + 1 <= last and ws.cell(r, c1 + 1).value in (None, "") and (r, c1 + 1) not in covered \
                            and (r, c1 + 1) not in top:
                        c1 += 1
                bold, size, ind = lo.font_of(cell)
                cap = sum(lo.col_pt(wid(k)) for k in range(c0, c1 + 1)) - CHECK_PAD_PT - ind
                nb = ws.cell(r, c1 + 1) if c1 + 1 <= maxc and (r, c1 + 1) not in covered else None
                text_nb = nb is not None and isinstance(nb.value, str) and nb.value != ""
                lines = lo.line_widths(cell.value, cap, bold, size) if wrap else [lo.text_pt(cell.value, bold, size)]
                avail = max(1, int(h // (LINE_PT * size / 9.0))) if wrap else 1
                room = cap - (CLEAR_PT if text_nb else 0.0)
                if len(lines) > avail or max(lines) > room:
                    bad.append((title, cell.coordinate, cell.value[:60], len(lines), avail, round(max(lines)),
                                round(room)))
    return bad


def test_render_summary_pdf(main_wb, lo_profile):
    dst, keep = render(main_wb, lo_profile, "Summary_render")
    assert os.path.getsize(dst) > 10_000
    bad = layout_problems(keep)
    assert not bad, bad[:10]
    wb = openpyxl.load_workbook(keep)
    titles = [ws.oddHeader.center.text for ws in wb.worksheets]
    assert not any(t.startswith(lo.SKIP_PREFIX) for t in titles)          # R4-01: working values not printed
    assert not any(t.startswith("Interface contract") for t in titles)     # Phase 4.2: nor the contract ranges
    # the Summary sheet itself: the working values and the contract ranges lie below its print area
    ws = openpyxl.load_workbook(main_wb["path"])["Summary"]
    area = ws.print_area[0] if isinstance(ws.print_area, (list, tuple)) else ws.print_area
    last = int(str(area).split("$")[-1])
    for prefix in lo.SKIP_PREFIX:
        rows = [r for r in range(1, ws.max_row + 1) if str(ws.cell(r, 1).value or "").startswith(prefix)]
        assert rows and rows[0] > last, prefix
    for rn in ("SUM_CLASS_MEAN", "PS_POOL_STRIP", "SUM_P_PCT_Q_T"):
        (_, coord), = list(main_wb["values"].defined_names[rn].destinations)
        r = int("".join(ch for ch in coord.split(":")[0] if ch.isdigit()))
        assert (r > last) == rn.startswith("SUM_"), rn       # contract ranges below; the strips stay printed
    # Phase 4.2: each section title's grey fill runs across the section's printed columns
    wb = openpyxl.load_workbook(keep)
    filled = 0
    for sh in wb.worksheets:
        if not lo.is_title(sh.cell(1, 1)):
            continue
        maxc = max(c for c in range(1, sh.max_column + 1)
                   if any(sh.cell(r, c).value not in (None, "") for r in range(1, sh.max_row + 1)))
        cov = lo._merged_at(sh)[1]
        assert all(lo.is_title(sh.cell(1, c)) for c in range(1, maxc + 1) if (1, c) not in cov), \
            sh.oddHeader.center.text
        filled += 1
    assert filled >= 10


def test_layout_check_catches_cut_text(main_wb, lo_profile, tmp_path):
    """The layout check fails a section whose long label is not wrapped (a copy with one label's wrap removed)."""
    keep = os.path.join(PHASE4, "Summary_render_sections.xlsx")
    if not os.path.exists(keep):
        render(main_wb, lo_profile, "Summary_render")
    wb = openpyxl.load_workbook(keep)
    from copy import copy
    # Phase 5: figure rows leave column B empty (units are in the label), so the sample is a long label in section C
    ws = next(w for w in wb.worksheets if w.oddHeader.center.text.startswith("C. "))
    top, _ = lo._merged_at(ws)
    r = next(r for r in range(2, ws.max_row + 1) if isinstance(ws.cell(r, 1).value, str)
             and len(ws.cell(r, 1).value) > 80 and (r, 1) not in top and ws.cell(r, 3).value is not None)
    al = copy(ws.cell(r, 1).alignment)
    al.wrap_text = False
    ws.cell(r, 1).alignment = al
    p = str(tmp_path / "cut.xlsx")
    wb.save(p)
    assert any(b[1] == ws.cell(r, 1).coordinate for b in layout_problems(p))


@pytest.fixture(scope="module")
def py_sections(tmp_path_factory):
    """Phase 4.2: the section layout without LibreOffice, so the Python mutation check reaches the render code. The
    synthetic workbook is built held and unheld; its cached values are the Python values (the build writes them as each
    formula's cached result), and lo._section_copy lays its Summary out exactly as the render does."""
    import yaml
    from sw import build
    tmp = str(tmp_path_factory.mktemp("py_sections"))
    with open(os.path.join(ROOT, "config", "synthetic.yaml")) as f:
        raw = yaml.safe_load(f)
    out = {}
    for hold in (False, True):
        raw["hold_position_rows"] = hold
        cp = os.path.join(tmp, f"cfg_{hold}.yaml")
        with open(cp, "w") as f:
            yaml.safe_dump(raw, f, sort_keys=False)
        path, _ = build.build(cp, "synthetic", os.path.join(ROOT, "config", "scenarios_synthetic.yaml"),
                              os.path.join(tmp, f"out_{hold}"))
        wb = openpyxl.load_workbook(path, data_only=True)
        sec = openpyxl.Workbook()
        sec.remove(sec.active)
        layout = lo._section_copy(wb["Summary"], sec, True)
        p = os.path.join(tmp, f"sections_{hold}.xlsx")
        sec.save(p)
        out[hold] = (p, layout, openpyxl.load_workbook(path)["Summary"])
    return out


def _by_title(path):
    return {ws.oddHeader.center.text: ws for ws in openpyxl.load_workbook(path).worksheets}


def test_section_layout_without_libreoffice(py_sections):
    """Phase 4.2: the layout of both builds passes the layout check; every section title's grey fill runs across the
    section (and across the workbook's title row); the working values and the contract ranges are left out; the
    figure columns' texts after a number are indented; the held strips collapse their held columns into one, and the
    held pool strip is no wider and no taller than the unheld one."""
    from sw import labels
    for hold in (False, True):
        p, layout, src = py_sections[hold]
        assert not layout_problems(p), (hold, layout_problems(p)[:5])
        titles = [t for _, t, _, _ in layout]
        assert not any(t.startswith(lo.SKIP_PREFIX) for t in titles)
        secs = _by_title(p)
        for t, ws in secs.items():
            if lo.is_title(ws.cell(1, 1)):
                maxc = max(c for c in range(1, ws.max_column + 1)
                           if any(ws.cell(r, c).value not in (None, "") for r in range(1, ws.max_row + 1)))
                cov = lo._merged_at(ws)[1]
                assert all(lo.is_title(ws.cell(1, c)) for c in range(1, maxc + 1) if (1, c) not in cov), t
        # Phase 4.2 (E141): the header's shock label is merged across the scenario columns, in the workbook and in
        # the first section, so it reads on one line (unmerged, the wrap pass stacks it in column C)
        first = openpyxl.load_workbook(p).worksheets[0]
        r_sh = next(r for r in range(1, 6) if first.cell(r, 1).value == labels.RESPONSE_LABEL)
        span = lo._merged_at(first)[0].get((r_sh, 3))
        assert span and span[1] - span[0] >= 3, (hold, span)
        assert any(m.min_row == r_sh and m.min_col == 3 and m.max_col >= 6 for m in src.merged_cells.ranges)
        # the workbook's own title rows carry the fill across the scenario columns
        trows = [r for r in range(1, src.max_row + 1) if lo.is_title(src.cell(r, 1))]
        assert len(trows) >= 10 and all(lo.is_title(src.cell(r, 4)) for r in trows)
        from sw import dictionary as DD
        ct = next(ws for t, ws in secs.items() if t == "F. " + DD.label("OUT-115"))
        hr = next(r for r in range(2, ct.max_row + 1) if lo._is_header(ct.cell(r, 1)))
        sc = next(c for c in range(1, ct.max_column + 1) if ct.cell(hr, c).value == DD.label("OUT-128"))
        assert all(ct.cell(r, sc).alignment.indent == 1 for r in range(hr + 1, ct.max_row + 1)
                   if isinstance(ct.cell(r, sc).value, str) and ct.cell(r, sc).value)
    from sw import dictionary as DD
    u, h = _by_title(py_sections[False][0]), _by_title(py_sections[True][0])
    held_secs = ["F. " + DD.label(x) for x in ("OUT-099", "OUT-087", "OUT-115", "OUT-111")]
    assert set(held_secs) <= set(u)
    for t in held_secs:
        heads_h = [c.value for row in h[t].iter_rows() for c in row if lo._is_header(c)]
        assert labels.HELD_COLUMNS in heads_h, t
    t = "F. " + DD.label("OUT-099")

    def width(ws):
        maxc = max(c for c in range(1, ws.max_column + 1)
                   if any(ws.cell(r, c).value not in (None, "") for r in range(1, ws.max_row + 1)))
        return sum(lo.col_pt(ws.column_dimensions[get_column_letter(c)].width or 8.43) for c in range(1, maxc + 1))
    assert width(h[t]) <= width(u[t])
    hh = sum(h[t].row_dimensions[r].height or 12 for r in range(1, h[t].max_row + 1))
    hu = sum(u[t].row_dimensions[r].height or 12 for r in range(1, u[t].max_row + 1))
    assert hh <= hu + 1e-6, (hh, hu)


def test_render_rules_without_libreoffice():
    """Phase 4.2: Arial glyph widths at 9 pt (Helvetica metrics); the lowest band's number format reads 'below 152';
    greedy word wrap."""
    import pytest as _pt
    assert lo.text_pt("0", False, 9.0) == _pt.approx(5.004)
    assert lo.text_pt("mean ntr_y1", True, 9.0) == _pt.approx(53.019)
    assert lo.text_pt("mean ntr_y1", False, 9.0) == _pt.approx(50.022)
    assert lo.text_pt("W", True, 11.0) == _pt.approx(10.384)
    fmt = '[=0]"below 152";General'
    assert lo.display_text(0, fmt) == "below 152" and lo.display_text(161.0, fmt) == "161"
    assert lo.line_widths("aa aa", lo.text_pt("aa aa")) == [_pt.approx(lo.text_pt("aa aa"))]
    assert len(lo.line_widths("aa aa", lo.text_pt("aa aa") - 0.1)) == 2
    assert lo.lines_pt("aa aa aa", lo.text_pt("aa aa") + 0.1) == 2


def _sections(main_wb, lo_profile):
    keep = os.path.join(PHASE4, "Summary_render_sections.xlsx")
    if not os.path.exists(keep):
        render(main_wb, lo_profile, "Summary_render")
    return keep


def test_layout_check_catches_figure_column_run_on(main_wb, lo_profile, tmp_path):
    """Phase 4.2, item 6: a text in the last scenario column, unwrapped, with an empty column to its right inside the
    notes' merged span (the Nov 20 render's "not used (entering_y1)", pp. 4, 6 and 7) is a layout problem. The earlier
    check let it run on into the empty column and passed it."""
    from copy import copy
    from sw import labels
    wb = openpyxl.load_workbook(_sections(main_wb, lo_profile))
    ws = next(w for w in wb.worksheets if w.oddHeader.center.text.startswith("B. "))
    hits = [(r, c) for r in range(2, ws.max_row + 1) for c in range(3, ws.max_column + 1)
            if ws.cell(r, c).value == labels.NOT_USED_ENTERING and ws.cell(r, c + 1).value in (None, "")]
    assert hits
    r, c = max(hits, key=lambda x: x[1])
    span = max(m.max_col for m in ws.merged_cells.ranges)
    assert span > c                      # the notes run past the last scenario column: the old run-on room
    al = copy(ws.cell(r, c).alignment)
    al.wrap_text = False
    ws.cell(r, c).alignment = al
    ws.row_dimensions[r].height = 12.0
    p = str(tmp_path / "runon.xlsx")
    wb.save(p)
    assert any(b[1] == ws.cell(r, c).coordinate for b in layout_problems(p))


def test_layout_check_catches_crowded_header(main_wb, lo_profile, tmp_path):
    """Phase 4.2, section 7: a header that fits its column only to within less than a space of the next header's text
    (the Nov 20 "mean ntr_y1" beside "P(ntr_y1 at or above target)") is a layout problem."""
    wb = openpyxl.load_workbook(_sections(main_wb, lo_profile))
    from sw import dictionary as DD
    ws = next(w for w in wb.worksheets if w.oddHeader.center.text == "F. " + DD.label("OUT-087"))
    hr = next(r for r in range(2, ws.max_row + 1) if lo._is_header(ws.cell(r, 1)))
    head = DD.label("OUT-088")                                   # Phase 5: "Expected class"
    c = next(c for c in range(2, ws.max_column) if ws.cell(hr, c).value == head)
    assert isinstance(ws.cell(hr, c + 1).value, str)
    t = lo.text_pt(head, True, 9.0)
    # LibreOffice keeps it on one line (it fits the cell less its margins) but leaves under a space before the next
    ws.column_dimensions[get_column_letter(c)].width = round(lo.width_for_pt(t + CHECK_PAD_PT + 0.5), 2)
    p = str(tmp_path / "crowded.xlsx")
    wb.save(p)
    assert any(b[1] == ws.cell(hr, c).coordinate for b in layout_problems(p))
    assert not any(b[1] == ws.cell(hr, c).coordinate for b in layout_problems(_sections(main_wb, lo_profile)))


def test_libreoffice_is_the_acceptance_version(soffice):
    """R4-17 (DECISIONS Nov 19: LibreOffice 26.8 is the acceptance version): results can depend on the engine version
    (the Checks rounding probe), so the installed soffice must report the pinned version."""
    pinned = lo.acceptance_version()
    assert pinned, "config/tools.yaml has no libreoffice_acceptance_version"
    assert lo.installed_version(soffice) == pinned


import re  # noqa: E402


def _pdf_pages(path):
    """Pages in a LibreOffice PDF: its page objects (LibreOffice writes no object streams, so they are plain text)."""
    import re
    with open(path, "rb") as fh:
        return len(re.findall(rb"/Type\s*/Page[^s]", fh.read()))


def test_render_overview_and_charts(main_wb, lo_profile, tmp_path):
    """Spec v0.6.4 CP-4 to CP-6: the PDF opens with the Overview, then the charts, then the Summary sections. The
    render workbook (output/phase4/Summary_render_book.xlsx) has Overview and Charts as its first two sheets, both
    visible, the section sheets after them, and the value sheets the charts read hidden; it carries the nine charts.
    The Overview prints on at most two pages (counted in a PDF of the Overview alone); its probabilities beyond 5% and
    95% read 'under 5%' and 'over 95%' while the variation is illustrative. The charts print at lo.MIN_SCALE or larger
    and fit the page width at LibreOffice's column widths."""
    import zipfile
    from sw import labels
    os.makedirs(PHASE4, exist_ok=True)
    book = os.path.join(PHASE4, "Summary_render_book.xlsx")
    pdf = lo.render_summary_pdf(main_wb["path"], str(tmp_path / "pdf"), profile=lo_profile, keep_render=book)
    assert os.path.getsize(pdf) > 10_000
    wb = openpyxl.load_workbook(book)
    names = wb.sheetnames
    assert names[:2] == ["Overview", "Charts"] and names[2] == "S01", names[:3]
    assert [wb[n].sheet_state for n in names[:2]] == ["visible", "visible"]
    assert wb["Summary"].sheet_state == "hidden" and wb["Distribution"].sheet_state == "hidden"
    assert all(wb[n].sheet_state == "visible" for n in names if re.match(r"^S\d+$", n))
    with zipfile.ZipFile(book) as z:
        assert len([n for n in z.namelist() if n.startswith("xl/charts/chart")]) == 9
    ch = wb["Charts"]
    assert ch.page_setup.scale is not None and ch.page_setup.scale >= 100 * lo.MIN_SCALE
    from openpyxl.utils import range_boundaries
    area = ch.print_area[0] if isinstance(ch.print_area, (list, tuple)) else ch.print_area
    _, _, used, _ = range_boundaries(str(area).split("!")[-1].replace("$", ""))
    widths = lo._col_widths(ch)                     # grouped <col min max> entries, expanded per column
    total = sum(lo.col_pt(widths.get(c, 8.43)) for c in range(1, used + 1))
    assert total * ch.page_setup.scale / 100 <= lo.PAGE_WIDTH_PT, (total, ch.page_setup.scale)
    ov = wb["Overview"]
    texts = [ov.cell(r, c).value for r in range(1, ov.max_row + 1) for c in range(3, ov.max_column + 1)]
    assert labels.PROB_UNDER in texts                                 # the synthetic GPA median is under 5%
    probs = [ov.cell(r, c) for r in range(1, ov.max_row + 1) for c in range(3, ov.max_column + 1)
             if ov.cell(r, c).number_format == "0%" and isinstance(ov.cell(r, c).value, (int, float))]
    assert probs and all(0.05 <= x.value <= 0.95 for x in probs)       # the rest are clamped to text
    # the Overview alone, through LibreOffice: at most two pages
    only = openpyxl.load_workbook(book)
    for n in list(only.sheetnames):
        if n != "Overview":
            del only[n]
    p = str(tmp_path / "overview_only.xlsx")
    only.save(p)
    out = lo._convert(p, str(tmp_path / "ov"), "pdf:calc_pdf_Export", profile=lo_profile)
    assert 1 <= _pdf_pages(out) <= 2, _pdf_pages(out)
