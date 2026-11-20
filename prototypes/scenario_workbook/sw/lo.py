"""LibreOffice helpers for the workbook tests and the Summary render (spec tests 3 and 10).

soffice is resolved from env var SOFFICE_PATH, then config/tools.yaml `soffice_path`, then `soffice` on PATH. Every
call uses a dedicated profile whose registrymodifications.xcu sets
/org.openoffice.Office.Calc/Formula/Load/OOXMLRecalcMode to 0 (always recalculate on load), so cached values in the
file are never trusted.
"""
import os
import shutil
import subprocess
import tempfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

XCU = """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" \
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="OOXMLRecalcMode" oor:op="fuse">\
<value>0</value></prop></item>
<item oor:path="/org.openoffice.Office.Calc/Formula/Load"><prop oor:name="ODFRecalcMode" oor:op="fuse">\
<value>0</value></prop></item>
<item oor:path="/org.openoffice.Office.Common/Misc"><prop oor:name="UseOpenCL" oor:op="fuse"><value>false</value>\
</prop></item>
<item oor:path="/org.openoffice.Setup/L10N"><prop oor:name="ooLocale" oor:op="fuse"><value>en-US</value></prop></item>
</oor:items>
"""


def soffice_path():
    p = os.environ.get("SOFFICE_PATH")
    if p:
        return p if os.path.exists(p) else None
    tools = os.path.join(ROOT, "config", "tools.yaml")
    if os.path.exists(tools):
        with open(tools) as f:
            p = (yaml.safe_load(f) or {}).get("soffice_path")
        if p and os.path.exists(p):
            return p
    return shutil.which("soffice")


def _tools():
    p = os.path.join(ROOT, "config", "tools.yaml")
    if not os.path.exists(p):
        return {}
    with open(p) as f:
        return yaml.safe_load(f) or {}


def acceptance_version():
    """R4-17: the LibreOffice version used for acceptance (config/tools.yaml libreoffice_acceptance_version)."""
    v = _tools().get("libreoffice_acceptance_version")
    return None if v is None else str(v)


def installed_version(exe=None):
    """The version soffice reports (for example '26.8.3.1'), or None."""
    import re
    exe = exe or soffice_path()
    if not exe:
        return None
    prof = make_profile()
    try:
        r = subprocess.run([exe, f"-env:UserInstallation=file://{prof}", "--headless", "--version"],
                           capture_output=True, text=True, timeout=120)
    finally:
        shutil.rmtree(prof, ignore_errors=True)
    m = re.search(r"LibreOffice\s+([0-9][0-9.]*)", r.stdout or "")
    return m.group(1) if m else None


def make_profile(parent=None, recalc=True):
    """A fresh LibreOffice user profile with forced recalculation on load (recalc=False: never recalculate, used only
    to test that the desktop Excel check refuses an unrecalculated copy). Returns its directory."""
    d = tempfile.mkdtemp(prefix="sw_lo_profile_", dir=parent)
    os.makedirs(os.path.join(d, "user"), exist_ok=True)
    xcu = XCU if recalc else XCU.replace("<value>0</value></prop></item>", "<value>1</value></prop></item>", 2)
    with open(os.path.join(d, "user", "registrymodifications.xcu"), "w") as f:
        f.write(xcu)
    return d


def _convert(src, out_dir, target, profile=None, timeout=600):
    exe = soffice_path()
    if not exe:
        raise FileNotFoundError("soffice not found (SOFFICE_PATH, config/tools.yaml, PATH)")
    own = profile is None
    profile = profile or make_profile()
    try:
        os.makedirs(out_dir, exist_ok=True)
        cmd = [exe, f"-env:UserInstallation=file://{profile}", "--headless", "--norestore", "--nologo",
               "--convert-to", target, "--outdir", out_dir, src]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        stem = os.path.splitext(os.path.basename(src))[0]
        ext = target.split(":")[0]
        out = os.path.join(out_dir, f"{stem}.{ext}")
        if r.returncode != 0 or not os.path.exists(out):
            raise RuntimeError(f"soffice conversion failed ({r.returncode}): {r.stdout} {r.stderr}")
        return out
    finally:
        if own:
            shutil.rmtree(profile, ignore_errors=True)


def recalc(xlsx, out_dir, profile=None):
    """Open xlsx in LibreOffice with forced recalculation and save it as xlsx in out_dir. Returns the new path."""
    return _convert(xlsx, out_dir, "xlsx:Calc MS Excel 2007 XML", profile=profile)


# ---------------------------------------------------------------------------------------------------------------
# Summary render (spec test 10; Phase 4; Review_Phase4_Build.md R4-01, R4-02)
#
# Character and page geometry, approximate and conservative. A column of width w (Excel units: the default font's digit
# width, 7 px) is 7w + 5 px; Arial 9 runs about 5 px a character, so a line holds about 1.4w characters. The render
# wraps at RENDER_CHARS_PER_UNIT x w (fewer, so wrapped lines rarely overflow) and gives LINE_PT per line. A landscape
# Letter page at the default margins (0.75 in each side) is PAGE_WIDTH_PT wide. Sections that fit at MIN_SCALE or
# larger print fit to one page width; wider sections print at MIN_SCALE and continue across pages, with columns A and
# B and the section's header row repeated.

RENDER_CHARS_PER_UNIT = 1.3
LINE_PT = 12.0
PAGE_WIDTH_PT = 684.0
MIN_SCALE = 0.75
MAX_PAGES_ACROSS = 3
SKIP_PREFIX = "Working values"          # the pool strip's split at m = 1: not printed (R4-01)


def eff_len(t, bold=False):
    """Characters a text takes, in average-character units: names in capitals and underscores and bold text run
    wider than ordinary text."""
    if not t:
        return 0.0
    caps = sum(1 for ch in t if ch.isupper() or ch == "_" or ch.isdigit()) / len(t)
    return len(t) * (1.25 if caps > 0.6 else 1.0) * (1.1 if bold else 1.0)


def col_pt(w):
    return (7.0 * w + 5.0) * 0.75


def display_text(v, fmt):
    """The text a cell shows (approximately), for width decisions."""
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, bool):
        return str(v)
    x = float(v)
    f = fmt or "General"
    try:
        if f.startswith("$"):
            return f"${x:,.0f}"
        if f == "#,##0.0":
            return f"{x:,.1f}"
        if f == "#,##0":
            return f"{x:,.0f}"
        if f.endswith("%"):
            nd = f.count("0") - 1
            return f"{100 * x:.{max(nd, 0)}f}%"
        if "E+" in f:
            return f"{x:.2E}"
        if f[0] == "0":
            nd = len(f.split(".")[1]) if "." in f else 0
            return f"{x:.{nd}f}"
    except (ValueError, IndexError):
        pass
    return f"{x:.10g}"


def _is_header(c):
    return bool(c.font is not None and c.font.b and c.border is not None and c.border.bottom is not None
                and c.border.bottom.style)


def _merged_at(ws):
    """{(row, col): (min_col, max_col)} for the top-left cell of each merged range; and the set of covered cells."""
    top, covered = {}, set()
    for m in ws.merged_cells.ranges:
        top[(m.min_row, m.min_col)] = (m.min_col, m.max_col)
        for r in range(m.min_row, m.max_row + 1):
            for c in range(m.min_col, m.max_col + 1):
                if (r, c) != (m.min_row, m.min_col):
                    covered.add((r, c))
    return top, covered


def merge_held(ws, maxc, nrows):
    """R4-06 in the PDF copy only: a run of two or more adjacent cells in a row that read labels.HOLD_POSITION is shown
    as one merged cell, so a held strip row stays one or two lines high. The workbook keeps the text in every cell (the
    contract ranges)."""
    from . import labels
    top, covered = _merged_at(ws)
    H = labels.HOLD_POSITION
    for r in range(2, nrows + 1):
        c = 3
        while c <= maxc:
            if ws.cell(r, c).value == H and (r, c) not in top and (r, c) not in covered:
                c1 = c
                while (c1 + 1 <= maxc and ws.cell(r, c1 + 1).value == H and (r, c1 + 1) not in top
                       and (r, c1 + 1) not in covered):
                    c1 += 1
                if c1 > c:
                    for k in range(c + 1, c1 + 1):
                        ws.cell(r, k).value = None
                    ws.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c1)
                c = c1 + 1
            else:
                c += 1


def fit_columns(ws, maxc, nrows):
    """Narrow each column to its content (never wider than in the workbook): numbers at their formatted width, text that
    would wrap anyway capped at the workbook width, header words kept whole. Row 1 (the section title) and merged
    cells do not count."""
    from openpyxl.utils import get_column_letter
    top, covered = _merged_at(ws)
    for c in range(1, maxc + 1):
        key = get_column_letter(c)
        w0 = ws.column_dimensions[key].width or 10
        need, texts = 0.0, []
        for r in range(2, nrows + 1):
            if (r, c) in top or (r, c) in covered:
                continue
            cell = ws.cell(r, c)
            t = display_text(cell.value, cell.number_format)
            if not t:
                continue
            bold = bool(cell.font is not None and cell.font.b)
            if _is_header(cell):
                # headers wrap by word, in at most about four lines
                need = max([need] + [eff_len(x, True) for x in t.split()] + [eff_len(t, True) / 4.0])
            elif isinstance(cell.value, str):
                # columns A and B hold labels; a figure column's text (notes, flags, statuses) wraps past 16
                # characters; a word is never broken
                texts.append(min(eff_len(t, bold), 1.3 * w0 if c <= 2 else 16))
                need = max([need] + [min(eff_len(x, bold), 1.3 * w0) for x in t.split()])
            else:
                need = max(need, len(t))                                      # a number never wraps
        if texts:
            # labels (columns A and B) set the width their longer entries need (the 80th percentile; the rest wraps);
            # in a figure column the longest text sets it, up to 16 characters
            texts.sort()
            need = max(need, texts[int(0.8 * (len(texts) - 1))] if c <= 2 else texts[-1])
        if need == 0:
            continue
        w = need / 1.3 + 1.5
        ws.column_dimensions[key].width = round(min(w0, max(6.0, w)), 1)


def wrap_overflow(ws, maxc, nrows):
    """Wrap every text cell longer than its rendered width (merged cells: the merged width) and give its row a height
    that holds the lines (R4-02)."""
    from copy import copy
    from openpyxl.utils import get_column_letter
    top, covered = _merged_at(ws)
    width = {c: ws.column_dimensions[get_column_letter(c)].width or 10 for c in range(1, maxc + 2)}
    for r in range(2, nrows + 1):
        need_h = 0.0
        for c in range(1, maxc + 1):
            if (r, c) in covered:
                continue
            cell = ws.cell(r, c)
            t = display_text(cell.value, cell.number_format)
            if not t or not isinstance(cell.value, str):
                continue
            c0, c1 = top.get((r, c), (c, c))
            if (r, c) not in top and not (cell.alignment is not None and cell.alignment.wrap_text):
                # unwrapped text runs on into empty cells to its right (section titles, short notes)
                while c1 + 1 <= maxc and ws.cell(r, c1 + 1).value in (None, "") and (r, c1 + 1) not in covered \
                        and (r, c1 + 1) not in top:
                    c1 += 1
            cap = RENDER_CHARS_PER_UNIT * sum(width[k] for k in range(c0, c1 + 1))
            bold = bool(cell.font is not None and cell.font.b)
            k = eff_len(t, bold) / len(t)
            cap = cap / k                                       # in characters of this text
            lines = 1
            if len(t) > cap:
                al = copy(cell.alignment)
                al.wrap_text = True
                if not _is_header(cell):
                    al.vertical = "top"
                cell.alignment = al
            if cell.alignment is not None and cell.alignment.wrap_text:
                lines = _lines(t, cap)
            need_h = max(need_h, LINE_PT * lines)
        cur = ws.row_dimensions[r].height
        if not _is_header(ws.cell(r, 1)):
            # the lines the row's text takes at the rendered widths (the workbook's own heights assume its widths)
            ws.row_dimensions[r].height = max(LINE_PT, need_h)
        elif need_h > (cur or LINE_PT):
            ws.row_dimensions[r].height = need_h
        if need_h > LINE_PT and not _is_header(ws.cell(r, 1)):
            # a row with wrapped text reads top-aligned across (label and figures on the same line)
            for c in range(1, maxc + 1):
                cell = ws.cell(r, c)
                if (r, c) not in covered and cell.value is not None:
                    al = copy(cell.alignment)
                    al.vertical = "top"
                    cell.alignment = al


def _lines(t, cap):
    """Lines a word-wrapped text takes at cap characters a line."""
    cap = max(int(cap), 1)
    lines, cur = 1, 0
    for word in t.split():
        n = len(word)
        if cur == 0:
            cur = n
        elif cur + 1 + n <= cap:
            cur += 1 + n
        else:
            lines += 1
            cur = n
        while cur > cap:
            lines += 1
            cur -= cap
    return lines


def page_setup(ws, maxc, header_row):
    """Fit to one page width when that leaves the scale at MIN_SCALE or above; otherwise print at MIN_SCALE across
    several pages with columns A:B repeated. The section's header row repeats on every page. Returns (scale, pages
    across)."""
    import math
    from openpyxl.utils import get_column_letter
    total = sum(col_pt(ws.column_dimensions[get_column_letter(c)].width or 10) for c in range(1, maxc + 1))
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_LETTER
    if header_row:
        ws.print_title_rows = f"{header_row}:{header_row}"
    fit = PAGE_WIDTH_PT / total
    if fit >= MIN_SCALE:
        ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        return min(1.0, fit), 1
    ws.sheet_properties.pageSetUpPr.fitToPage = False
    ws.page_setup.scale = int(MIN_SCALE * 100)
    ws.print_title_cols = "A:B"
    ws.page_setup.pageOrder = "overThenDown"
    ab = col_pt(ws.column_dimensions["A"].width or 10) + col_pt(ws.column_dimensions["B"].width or 10)
    rest = total - ab
    per_page = PAGE_WIDTH_PT / MIN_SCALE - ab
    return MIN_SCALE, max(1, math.ceil(rest / per_page))


def _section_copy(src_ws, wb_out, shock_illustrative):
    """Copy Summary (values and formats) into one sheet per section of wb_out. Each section is laid out on its own:
    columns narrowed to their content, overflowing text wrapped with row heights that hold it, the header row and (for
    wide sections) columns A:B repeated on every page, printed landscape at MIN_SCALE or larger (R4-01, R4-02). The
    working-values section (SKIP_PREFIX) is left out. Probability cells (format 0%) show 'under 5%' and 'over 95%'
    while the shock is illustrative (the workbook does this with conditional formats, which a values-only copy cannot
    carry). Returns [(sheet name, section title, scale, pages across)]."""
    from copy import copy
    from openpyxl.styles import Alignment
    from . import labels
    rows = list(range(1, src_ws.max_row + 1))
    starts = [r for r in rows if (src_ws.cell(r, 1).fill is not None and src_ws.cell(r, 1).fill.fgColor is not None
                                  and str(src_ws.cell(r, 1).fill.fgColor.rgb).upper().endswith("E8E8E8"))]
    bounds = [1] + starts[1:] + [src_ws.max_row + 1]
    merges = [m for m in src_ws.merged_cells.ranges]
    layout = []
    for si in range(len(bounds) - 1):
        r0, r1 = bounds[si], bounds[si + 1] - 1
        title = src_ws.cell(bounds[si], 1).value or "Summary"
        if str(title).startswith(SKIP_PREFIX):
            continue
        ws = wb_out.create_sheet(f"S{si + 1:02d}")
        maxc = 1
        header_row = None
        for r in range(r0, r1 + 1):
            for c in range(1, src_ws.max_column + 1):
                sc = src_ws.cell(r, c)
                if sc.value is None and not sc.has_style:
                    continue
                v = sc.value
                clamped = False
                if (shock_illustrative and isinstance(v, (int, float)) and not isinstance(v, bool)
                        and sc.number_format == "0%"):
                    clamped = v < 0.05 or v > 0.95
                    v = labels.PROB_UNDER if v < 0.05 else labels.PROB_OVER if v > 0.95 else v
                dc = ws.cell(r - r0 + 1, c, v)
                if sc.has_style:
                    dc.font, dc.fill, dc.border = copy(sc.font), copy(sc.fill), copy(sc.border)
                    dc.alignment, dc.number_format = copy(sc.alignment), sc.number_format
                if clamped:
                    # the clamp text replaces a number: keep it right-aligned with the other percentages (Phase 4
                    # render review)
                    dc.alignment = Alignment(horizontal="right", vertical=dc.alignment.vertical)
                if sc.value not in (None, ""):
                    maxc = max(maxc, c)
            if header_row is None and r > r0 and _is_header(src_ws.cell(r, 1)):
                header_row = r - r0 + 1
            if src_ws.row_dimensions[r].height:
                ws.row_dimensions[r - r0 + 1].height = src_ws.row_dimensions[r].height
        for m in merges:
            if r0 <= m.min_row <= r1:
                ws.merge_cells(start_row=m.min_row - r0 + 1, start_column=m.min_col, end_row=m.max_row - r0 + 1,
                               end_column=m.max_col)
                maxc = max(maxc, m.max_col)
        for key, dim in src_ws.column_dimensions.items():
            nd = ws.column_dimensions[key]
            nd.width, nd.min, nd.max = dim.width, dim.min, dim.max
        nrows = r1 - r0 + 1
        _split_column_dims(ws, maxc)
        merge_held(ws, maxc, nrows)
        fit_columns(ws, maxc, nrows)
        wrap_overflow(ws, maxc, nrows)
        ws.print_area = f"A1:{ws.cell(1, maxc).column_letter}{nrows}"
        scale, across = page_setup(ws, maxc, header_row)
        ws.oddHeader.center.text = str(title)[:120]
        ws.oddFooter.center.text = "page &P of &N"
        layout.append((ws.title, str(title), scale, across))
    return layout


def _split_column_dims(ws, maxc):
    """Give each column up to maxc its own width entry (a copied range entry such as C:AO would otherwise be resized
    as one)."""
    from openpyxl.utils import get_column_letter
    widths = {}
    for key, dim in list(ws.column_dimensions.items()):
        lo_, hi_ = dim.min or 0, dim.max or 0
        for c in range(max(lo_, 1), min(hi_, maxc) + 1):
            widths[c] = dim.width
    for c in range(1, maxc + 1):
        key = get_column_letter(c)
        w = widths.get(c) or ws.column_dimensions[key].width or 10
        d = ws.column_dimensions[key]
        d.min, d.max, d.width = c, c, w


def render_summary_pdf(xlsx, out_dir, profile=None, keep_sections=None):
    """Spec test 10: recalculate, copy Summary's values and formats into one page group per section, convert to PDF.
    The workbook itself is unchanged. keep_sections: a path where the section workbook (the PDF's source) is saved, for
    test 10's layout checks. Returns the PDF path."""
    import openpyxl
    tmp = tempfile.mkdtemp(prefix="sw_pdf_")
    try:
        prof = profile or make_profile(tmp)
        rc = recalc(xlsx, os.path.join(tmp, "recalc"), profile=prof)
        wb = openpyxl.load_workbook(rc, data_only=True)
        (sh, coord), = list(wb.defined_names["in_shock_source"].destinations)
        illustrative = wb[sh][coord.replace("$", "")].value == "illustrative"
        out = openpyxl.Workbook()
        out.remove(out.active)
        _section_copy(wb["Summary"], out, illustrative)
        stem = os.path.splitext(os.path.basename(xlsx))[0]
        only = os.path.join(tmp, f"{stem}_Summary.xlsx")
        out.save(only)
        if keep_sections:
            shutil.copyfile(only, keep_sections)
        return _convert(only, out_dir, "pdf:calc_pdf_Export", profile=prof)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
