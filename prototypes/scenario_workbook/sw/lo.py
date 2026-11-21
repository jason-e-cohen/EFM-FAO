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
# Summary render (spec test 10; Phase 4; Review_Phase4_Build.md R4-01, R4-02; Phase 4.2, Review_Phase4_FixPass.md
# section 7)
#
# Geometry in points. Text widths come from Arial's glyph widths (the Helvetica metrics, which Arial and Liberation
# Sans share), at the cell's font size and weight. A column of width w (Excel units: the default font's digit width,
# 7 px) is 7w + 5 px = col_pt(w) points. The render leaves PAD_PT for the cell margins and GAP_PT between a text and its
# neighbour, plus INDENT_PT per indent level; wrapped text takes LINE_PT per line (at 9 pt). Text in a figure column
# (C onward) never runs on into the next column: it wraps in its own cell (Phase 4.2). A landscape Letter page at the
# default margins (0.75 in each side) is PAGE_WIDTH_PT wide. Sections that fit at MIN_SCALE or larger print fit to one
# page width; wider sections print at MIN_SCALE and continue across pages, with columns A and B and the section's
# header row repeated, and their title and notes wrapped within A:B so a continued page shows them whole.

LINE_PT = 12.0
PAGE_WIDTH_PT = 684.0
MIN_SCALE = 0.75
MAX_PAGES_ACROSS = 3
PAD_PT = 3.0
GAP_PT = 4.0
INDENT_PT = 9.0
FIG_TEXT_PT = 72.0      # a figure column's text (notes, flags, statuses) wraps past about 16 characters
LO_PAD_PT = 2.8         # LibreOffice's own cell margins, left and right together: it wraps text at the width less these
SKIP_PREFIX = ("Working values", "Interface contract")     # not printed (R4-01; Phase 4.2: the contract ranges)

_ASCII = "".join(chr(c) for c in range(32, 127))
# Helvetica (= Arial) advance widths per 1000 em, for characters 32 to 126
_W_REG = [278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278] + [556] * 10 + \
    [278, 278, 584, 584, 584, 556, 1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
     667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556, 333, 556, 556, 500, 556, 556, 278,
     556, 556, 222, 222, 500, 222, 833, 556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334,
     584]
_W_BOLD = [278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278] + [556] * 10 + \
    [333, 333, 584, 584, 584, 611, 975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778,
     667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556, 333, 556, 611, 556, 611, 556, 333,
     611, 611, 278, 278, 556, 278, 889, 611, 611, 611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389,
     584]
_AFM = {False: dict(zip(_ASCII, _W_REG)), True: dict(zip(_ASCII, _W_BOLD))}


def text_pt(t, bold=False, size=9.0):
    """Width of one line of text in points (Arial glyph widths; other characters at a digit's width)."""
    w = _AFM[bool(bold)]
    return sum(w.get(ch, 556) for ch in str(t)) * float(size) / 1000.0


def line_widths(t, cap, bold=False, size=9.0):
    """Widths of the lines a greedy word wrap at cap points makes (a word longer than a line is one line)."""
    sp = text_pt(" ", bold, size)
    out, cur = [], 0.0
    for word in str(t).split():
        n = text_pt(word, bold, size)
        if cur and cur + sp + n <= cap:
            cur += sp + n
        else:
            if cur:
                out.append(cur)
            cur = n
    out.append(cur)
    return out


def lines_pt(t, cap, bold=False, size=9.0):
    """Lines a word-wrapped text takes at cap points a line (a word longer than a line breaks)."""
    sp = text_pt(" ", bold, size)
    lines, cur = 1, 0.0
    cap = max(cap, 1.0)
    for word in str(t).split():
        n = text_pt(word, bold, size)
        if cur == 0:
            cur = n
        elif cur + sp + n <= cap:
            cur += sp + n
        else:
            lines += 1
            cur = n
        while cur > cap:
            lines += 1
            cur -= cap
    return lines


def font_of(cell):
    """(bold, size, indent points) of a cell."""
    bold = bool(cell.font is not None and cell.font.b)
    size = float(cell.font.sz) if cell.font is not None and cell.font.sz else 9.0
    ind = INDENT_PT * float(cell.alignment.indent or 0) if cell.alignment is not None else 0.0
    return bold, size, ind


def col_pt(w):
    return (7.0 * w + 5.0) * 0.75


def width_for_pt(pt):
    """The column width (Excel units) whose col_pt is pt."""
    return (pt / 0.75 - 5.0) / 7.0


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
    if f.startswith("[="):                      # a conditional section, '[=v]"text";rest' (the lowest score band)
        cond, _, rest = f.partition(";")
        try:
            if x == float(cond[2:cond.index("]")]):
                return cond[cond.index("]") + 1:].strip('"')
        except ValueError:
            pass
        f = rest or "General"
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


def is_title(c):
    """A section title cell (grey fill): it may run on across its row."""
    return bool(c.fill is not None and c.fill.fgColor is not None
                and str(c.fill.fgColor.rgb).upper().endswith("E8E8E8"))


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
    as one merged cell, so a held row stays one or two lines high. The workbook keeps the text in every cell (the
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


def held_runs(src_ws, header_row, r1, maxc):
    """Phase 4.2: runs of two or more adjacent figure columns (C onward) in which every table row below the header
    reads labels.HOLD_POSITION (the held median and percentile columns of a strip). [[c, ...], ...]"""
    from . import labels
    H = labels.HOLD_POSITION
    rows = [r for r in range(header_row + 1, r1 + 1) if src_ws.cell(r, 1).value not in (None, "")]
    if not rows:
        return []
    cols = [c for c in range(3, maxc + 1) if all(src_ws.cell(r, c).value == H for r in rows)]
    runs = []
    for c in cols:
        if runs and runs[-1][-1] == c - 1:
            runs[-1].append(c)
        else:
            runs.append([c])
    return [r for r in runs if len(r) >= 2]


def fit_columns(ws, maxc, nrows):
    """Narrow each column to its content (never wider than in the workbook): numbers at their formatted width, text that
    would wrap anyway capped at the workbook width (columns A and B) or FIG_TEXT_PT (figure columns), header words kept
    whole, the hold text on one line. Row 1 (the section title) and merged cells do not count."""
    from openpyxl.utils import get_column_letter
    from . import labels
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
            bold, size, ind = font_of(cell)
            if _is_header(cell):
                # headers wrap by word, in at most about four lines
                need = max([need] + [text_pt(x, True, size) for x in t.split()] + [text_pt(t, True, size) / 4.0])
            elif isinstance(cell.value, str):
                full = text_pt(t, bold, size) + ind
                if cell.value == labels.HOLD_POSITION:
                    texts.append(full)                                      # the hold text stays on one line
                else:
                    texts.append(min(full, col_pt(w0) if c <= 2 else FIG_TEXT_PT))
                need = max([need] + [min(text_pt(x, bold, size) + ind, col_pt(w0)) for x in t.split()])
            else:
                need = max(need, text_pt(t, bold, size))                    # a number never wraps
        if texts:
            # labels (columns A and B) set the width their longer entries need (the 80th percentile; the rest wraps);
            # in a figure column the longest text sets it
            texts.sort()
            need = max(need, texts[int(0.8 * (len(texts) - 1))] if c <= 2 else texts[-1])
        if need == 0:
            continue
        w = width_for_pt(need + PAD_PT + GAP_PT)
        ws.column_dimensions[key].width = round(min(w0, max(6.0, w)) + 0.05, 1)


def settle_gaps(ws, maxc, nrows):
    """Phase 4.2 (section 7, colliding headers): a text whose right-hand neighbour also holds text must end at least
    GAP_PT short of its cell's edge on every line LibreOffice lays out (it wraps at the width less LO_PAD_PT, so a line
    can otherwise run to within a hair of the next cell's text). Widen the column until that holds."""
    from openpyxl.utils import get_column_letter
    top, covered = _merged_at(ws)
    for c in range(1, maxc):
        key = get_column_letter(c)
        for _ in range(6):
            w = ws.column_dimensions[key].width or 10
            worst = 0.0
            for r in range(2, nrows + 1):
                cell, nb = ws.cell(r, c), ws.cell(r, c + 1)
                if (r, c) in top or (r, c) in covered or (r, c + 1) in covered:
                    continue
                if not isinstance(cell.value, str) or not cell.value or not isinstance(nb.value, str) or not nb.value:
                    continue
                bold, size, ind = font_of(cell)
                cap = col_pt(w) - LO_PAD_PT - ind
                wrap = cell.alignment is not None and cell.alignment.wrap_text
                lw = line_widths(cell.value, cap, bold, size) if wrap else [text_pt(cell.value, bold, size)]
                over = max(x for x in lw if x <= cap) if any(x <= cap for x in lw) else 0.0
                if over > cap - GAP_PT:
                    worst = max(worst, over + LO_PAD_PT + GAP_PT + ind)
            if not worst:
                break
            ws.column_dimensions[key].width = round(width_for_pt(worst) + 0.1, 1)


def wrap_overflow(ws, maxc, nrows):
    """Wrap every text cell longer than its rendered width (merged cells: the merged width) and give its row a height
    that holds the lines (R4-02). Unwrapped text in column A may run on into an empty column B; text in a figure
    column wraps in its own cell (Phase 4.2)."""
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
            if (r, c) not in top and not (cell.alignment is not None and cell.alignment.wrap_text) and c == 1:
                # column A may run on into an empty column B; a section title across its whole (empty) row
                last = maxc if is_title(cell) else 2
                while c1 + 1 <= last and ws.cell(r, c1 + 1).value in (None, "") and (r, c1 + 1) not in covered \
                        and (r, c1 + 1) not in top:
                    c1 += 1
            bold, size, ind = font_of(cell)
            cap = sum(col_pt(width[k]) for k in range(c0, c1 + 1)) - PAD_PT - GAP_PT - ind
            if text_pt(t, bold, size) > cap:
                al = copy(cell.alignment)
                al.wrap_text = True
                if not _is_header(cell):
                    al.vertical = "top"
                cell.alignment = al
            lines = 1
            if cell.alignment is not None and cell.alignment.wrap_text:
                lines = lines_pt(t, cap, bold, size)
            need_h = max(need_h, LINE_PT * size / 9.0 * lines)
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


def fit_heading_to_ab(ws, header_row):
    """Phase 4.2: in a section printed across pages, the title (row 1) and the notes above the header row are merged
    within A:B and wrapped, so the continued pages, which repeat only columns A and B, show them whole."""
    from copy import copy
    last = (header_row or 2) - 1
    cap = col_pt(ws.column_dimensions["A"].width or 10) + col_pt(ws.column_dimensions["B"].width or 10)
    cap -= PAD_PT + GAP_PT
    for m in list(ws.merged_cells.ranges):
        if m.min_row <= last and m.min_col == 1:
            ws.unmerge_cells(str(m))
    for r in range(1, last + 1):
        cell = ws.cell(r, 1)
        if not isinstance(cell.value, str) or not cell.value:
            continue
        if any(ws.cell(r, c).value not in (None, "") for c in range(2, 4)):
            continue                                       # a labelled row with figures (pool growth to date)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
        al = copy(cell.alignment)
        al.wrap_text, al.vertical = True, "top"
        cell.alignment = al
        bold, size, _ = font_of(cell)
        ws.row_dimensions[r].height = LINE_PT * size / 9.0 * lines_pt(cell.value, cap, bold, size)


def pad_after_numbers(ws, maxc, nrows):
    """Phase 4.2 (section 7): in a figure column where a left-aligned text follows a number (a status after a count, a
    flag after a dollar figure, the hold text after a probability), every left-aligned text is indented one level, so
    none sits against the number to its left and the column reads aligned."""
    from copy import copy

    def is_num(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    for c in range(4, maxc + 1):
        cells = [ws.cell(r, c) for r in range(2, nrows + 1)]
        texts = [x for x in cells if isinstance(x.value, str) and x.value and not _is_header(x)
                 and (x.alignment is None or x.alignment.horizontal in (None, "general", "left"))]
        if not any(is_num(ws.cell(x.row, c - 1).value) for x in texts):
            continue
        for x in texts:
            al = copy(x.alignment)
            if not al.indent:
                al.horizontal, al.indent = "left", 1          # an indent shows only on a left-aligned cell
                x.alignment = al


def fit_title(ws, maxc):
    """Phase 4.2: the section title (row 1) merged across the section's columns and wrapped, so a title longer than the
    section (the Summary title on page 1) is not cut at the print area."""
    from copy import copy
    from openpyxl.utils import get_column_letter
    cell = ws.cell(1, 1)
    if not isinstance(cell.value, str) or (1, 1) in _merged_at(ws)[0]:
        return
    bold, size, _ = font_of(cell)
    cap = sum(col_pt(ws.column_dimensions[get_column_letter(c)].width or 10) for c in range(1, maxc + 1))
    cap -= PAD_PT + GAP_PT
    ab = sum(col_pt(ws.column_dimensions[get_column_letter(c)].width or 10) for c in (1, 2)) - PAD_PT - GAP_PT
    # Phase 5: a title without the grey fill (the workbook title) may run on only into column B, so it is merged
    # across the section once it is wider than A:B; a grey section title runs across its empty row
    if text_pt(cell.value, bold, size) <= (cap if is_title(cell) else ab):
        return
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=maxc)
    al = copy(cell.alignment)
    al.wrap_text, al.vertical = True, "top"
    cell.alignment = al
    ws.row_dimensions[1].height = LINE_PT * size / 9.0 * lines_pt(cell.value, cap, bold, size) + 2


def _section_copy(src_ws, wb_out, shock_illustrative):
    """Copy Summary (values and formats) into one sheet per section of wb_out. Each section is laid out on its own:
    columns narrowed to their content, overflowing text wrapped with row heights that hold it, the header row and (for
    wide sections) columns A:B repeated on every page, printed landscape at MIN_SCALE or larger (R4-01, R4-02). The
    sections titled with SKIP_PREFIX are left out. Probability cells (format 0%) show 'under 5%' and 'over 95%'
    while the shock is illustrative (the workbook does this with conditional formats, which a values-only copy cannot
    carry). Phase 4.2: the title's grey fill runs across the section; adjacent held columns (every table row reads
    labels.HOLD_POSITION) collapse into one column headed labels.HELD_COLUMNS, so a held strip prints no wider than
    the unheld one. Returns [(sheet name, section title, scale, pages across)]."""
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
        src_head = next((r for r in range(r0 + 1, r1 + 1) if _is_header(src_ws.cell(r, 1))), None)
        runs = held_runs(src_ws, src_head, r1, src_ws.max_column) if src_head else []
        drop = {c for run in runs for c in run[1:]}
        first = {run[0]: run for run in runs}
        cmap, k = {}, 0
        for c in range(1, src_ws.max_column + 2):
            if c in drop:
                continue
            k += 1
            cmap[c] = k
        maxc = 1
        header_row = None
        for r in range(r0, r1 + 1):
            for c in range(1, src_ws.max_column + 1):
                if c in drop:
                    continue
                sc = src_ws.cell(r, c)
                if sc.value is None and not sc.has_style:
                    continue
                v = sc.value
                if c in first and r == src_head:
                    v = labels.HELD_COLUMNS
                clamped = False
                if (shock_illustrative and isinstance(v, (int, float)) and not isinstance(v, bool)
                        and sc.number_format == "0%"):
                    clamped = v < 0.05 or v > 0.95
                    v = labels.PROB_UNDER if v < 0.05 else labels.PROB_OVER if v > 0.95 else v
                dc = ws.cell(r - r0 + 1, cmap[c], v)
                if sc.has_style:
                    dc.font, dc.fill, dc.border = copy(sc.font), copy(sc.fill), copy(sc.border)
                    dc.alignment, dc.number_format = copy(sc.alignment), sc.number_format
                if clamped:
                    # the clamp text replaces a number: keep it right-aligned with the other percentages (Phase 4
                    # render review)
                    dc.alignment = Alignment(horizontal="right", vertical=dc.alignment.vertical)
                if sc.value not in (None, ""):
                    maxc = max(maxc, cmap[c])
            if header_row is None and r > r0 and _is_header(src_ws.cell(r, 1)):
                header_row = r - r0 + 1
            if src_ws.row_dimensions[r].height:
                ws.row_dimensions[r - r0 + 1].height = src_ws.row_dimensions[r].height
        for m in merges:
            if r0 <= m.min_row <= r1:
                c0 = next(cmap[c] for c in range(m.min_col, src_ws.max_column + 2) if c in cmap)
                c1 = max(cmap[c] for c in range(1, m.max_col + 1) if c in cmap)
                if c1 > c0 or m.max_row > m.min_row:
                    ws.merge_cells(start_row=m.min_row - r0 + 1, start_column=c0, end_row=m.max_row - r0 + 1,
                                   end_column=c1)
                maxc = max(maxc, c1)
        for key, dim in src_ws.column_dimensions.items():
            nd = ws.column_dimensions[key]
            nd.width, nd.min, nd.max = dim.width, dim.min, dim.max
        nrows = r1 - r0 + 1
        _split_column_dims(ws, maxc, src_ws, cmap, first)
        pad_after_numbers(ws, maxc, nrows)
        merge_held(ws, maxc, nrows)
        fit_columns(ws, maxc, nrows)
        wrap_overflow(ws, maxc, nrows)
        settle_gaps(ws, maxc, nrows)
        wrap_overflow(ws, maxc, nrows)
        ws.print_area = f"A1:{ws.cell(1, maxc).column_letter}{nrows}"
        scale, across = page_setup(ws, maxc, header_row)
        if across > 1:
            fit_heading_to_ab(ws, header_row)
        else:
            fit_title(ws, maxc)
        t1 = ws.cell(1, 1)
        for c in range(2, maxc + 1):                       # the title's grey fill across the section
            ws.cell(1, c).fill = copy(t1.fill)
        ws.oddHeader.center.text = str(title)[:120]
        ws.oddFooter.center.text = "page &P of &N"
        layout.append((ws.title, str(title), scale, across))
    return layout


def _split_column_dims(ws, maxc, src_ws=None, cmap=None, first=None):
    """Give each column up to maxc its own width entry (a copied range entry such as C:AO would otherwise be resized
    as one). With cmap (source column -> section column), widths come from the source columns; a collapsed held run
    (first: its first source column -> the run) takes the run's total width."""
    from openpyxl.utils import get_column_letter
    widths = {}
    dims = src_ws.column_dimensions if src_ws is not None else ws.column_dimensions
    for key, dim in list(dims.items()):
        lo_, hi_ = dim.min or 0, dim.max or 0
        for c in range(max(lo_, 1), hi_ + 1):
            widths[c] = dim.width
    inv = {v: k for k, v in (cmap or {}).items()}
    for c in range(1, maxc + 1):
        key = get_column_letter(c)
        sc = inv.get(c, c)
        w = widths.get(sc) or ws.column_dimensions[key].width or 10
        if first and sc in first:
            w = sum(widths.get(x) or 10 for x in first[sc])
        d = ws.column_dimensions[key]
        d.min, d.max, d.width = c, c, w


# ---------------------------------------------------------------------------------------------------------------
# Spec v0.6.4 section 0B (CP-4, CP-5): the PDF opens with the Overview and the charts, then the Summary sections. Without
# a PDF library the parts cannot be joined after conversion, so one XlsxWriter workbook carries them all: the Overview
# and the Charts sheet copied from the recalculated workbook (values and formats), the charts drawn again from the
# build's chart specification (sw/charts.py) on those values, and the Summary sections copied from the section
# workbook below. Summary and Distribution values sit in hidden sheets that the charts read; LibreOffice does not print
# hidden sheets.

def _rgb(color):
    if color is None or color.type != "rgb" or not isinstance(color.rgb, str):
        return None
    v = color.rgb[-6:]
    return None if color.rgb.upper() in ("00000000",) else "#" + v


def _xw_format(wb, cache, cell, num_format=None, align=None):
    """An XlsxWriter format equal to an openpyxl cell's font, fill, bottom border, alignment and number format."""
    f, fl, al, bd = cell.font, cell.fill, cell.alignment, cell.border
    d = {}
    if f is not None:
        d.update({"font_name": f.name or "Arial", "font_size": f.sz or 9, "bold": bool(f.b), "italic": bool(f.i),
                  "font_strikeout": bool(f.strike)})
        c = _rgb(f.color)
        if c and c.upper() != "#000000":
            d["font_color"] = c
    if fl is not None and fl.fill_type == "solid":
        c = _rgb(fl.fgColor)
        if c:
            d["bg_color"] = c
    if bd is not None and bd.bottom is not None and bd.bottom.style:
        d["bottom"] = 1
    al = align or al
    if al is not None:
        if al.horizontal and al.horizontal != "general":
            d["align"] = {"centerContinuous": "center_across"}.get(al.horizontal, al.horizontal)
        if al.vertical:
            d["valign"] = {"center": "vcenter"}.get(al.vertical, al.vertical)
        if al.wrap_text:
            d["text_wrap"] = True
        if al.indent:
            d["indent"] = int(al.indent)
    nf = num_format if num_format is not None else cell.number_format
    if nf and nf != "General":
        d["num_format"] = nf
    key = tuple(sorted((k, str(v)) for k, v in d.items()))
    if key not in cache:
        cache[key] = wb.add_format(d)
    return cache[key]


def _col_widths(src_ws):
    from openpyxl.utils import column_index_from_string
    widths = {}
    for key, dim in src_ws.column_dimensions.items():
        lo_, hi_ = dim.min, dim.max
        if not lo_:
            lo_ = hi_ = column_index_from_string(key)
        for c in range(lo_, (hi_ or lo_) + 1):
            if dim.width:
                widths[c] = dim.width
    return widths


def _transcribe(src_ws, wb, name, cache, clamp=False, rows=None, cols=None, values_only=False):
    """Copy src_ws (openpyxl) into a new XlsxWriter sheet: values, formats, merges, widths and heights. clamp: show
    probability cells (format 0%) as 'under 5%' / 'over 95%' beyond those bounds, right-aligned (as _section_copy)."""
    from openpyxl.styles import Alignment
    from . import labels
    ws = wb.add_worksheet(name)
    r_max = rows or src_ws.max_row
    c_max = cols or src_ws.max_column
    merged = {}
    covered = set()
    if not values_only:
        for m in src_ws.merged_cells.ranges:
            if m.min_row > r_max:
                continue
            merged[(m.min_row, m.min_col)] = m
            for r in range(m.min_row, m.max_row + 1):
                for c in range(m.min_col, m.max_col + 1):
                    covered.add((r, c))
        for c, w in _col_widths(src_ws).items():
            if c <= c_max + 1:
                ws.set_column(c - 1, c - 1, w)
        for r in range(1, r_max + 1):
            h = src_ws.row_dimensions[r].height
            if h:
                ws.set_row(r - 1, h)
    for row in src_ws.iter_rows(min_row=1, max_row=r_max, max_col=c_max):
        for cell in row:
            r, c = cell.row, cell.column
            if (r, c) in covered and (r, c) not in merged:
                continue
            v = cell.value
            fmt = None
            if not values_only and cell.has_style:
                nf, al = None, None
                if (clamp and isinstance(v, (int, float)) and not isinstance(v, bool) and cell.number_format == "0%"
                        and (v < 0.05 or v > 0.95)):
                    v = labels.PROB_UNDER if v < 0.05 else labels.PROB_OVER
                    al = Alignment(horizontal="right", vertical=cell.alignment.vertical if cell.alignment else None)
                fmt = _xw_format(wb, cache, cell, nf, al)
            if (r, c) in merged:
                m = merged[(r, c)]
                if m.max_row > m.min_row or m.max_col > m.min_col:
                    ws.merge_range(m.min_row - 1, m.min_col - 1, m.max_row - 1, m.max_col - 1,
                                   "" if v is None else v, fmt)
                    continue
            if v is None:
                if fmt is not None:
                    ws.write_blank(r - 1, c - 1, None, fmt)
            elif isinstance(v, bool):
                ws.write_boolean(r - 1, c - 1, v, fmt)
            elif isinstance(v, (int, float)):
                ws.write_number(r - 1, c - 1, v, fmt)
            else:
                ws.write_string(r - 1, c - 1, str(v), fmt)
    return ws


def _header_text(t):
    return (t or "").replace("&", "&&")


def _page_from(src_ws, ws):
    """Carry an openpyxl section sheet's print setup to the XlsxWriter copy."""
    import re
    ws.set_landscape()
    ws.set_paper(1)
    pm = src_ws.page_margins
    ws.set_margins(left=pm.left, right=pm.right, top=pm.top, bottom=pm.bottom)
    if src_ws.print_area:
        pa = src_ws.print_area if isinstance(src_ws.print_area, str) else src_ws.print_area[0]
        ws.print_area(pa.split("!")[-1].replace("$", ""))
    if src_ws.print_title_rows:
        nums = [int(x) for x in re.findall(r"\d+", src_ws.print_title_rows)]
        ws.repeat_rows(nums[0] - 1, nums[-1] - 1)
    if src_ws.print_title_cols:
        ws.repeat_columns("A:B")
    if src_ws.sheet_properties.pageSetUpPr is not None and src_ws.sheet_properties.pageSetUpPr.fitToPage:
        ws.fit_to_pages(src_ws.page_setup.fitToWidth or 1, src_ws.page_setup.fitToHeight or 0)
    elif src_ws.page_setup.scale:
        ws.set_print_scale(int(src_ws.page_setup.scale))
    if src_ws.page_setup.pageOrder == "overThenDown":
        ws.print_across()
    ws.set_header("&C" + _header_text(src_ws.oddHeader.center.text), {"margin": pm.header})
    ws.set_footer("&C" + (src_ws.oddFooter.center.text or ""), {"margin": pm.footer})


def _render_book(path, rc_wb, sections_wb, spec, illustrative):
    """The combined render workbook: Overview, Charts, the Summary sections, then hidden value sheets."""
    import xlsxwriter
    from . import charts as CH
    wb = xlsxwriter.Workbook(path, {"strings_to_numbers": False, "strings_to_formulas": False,
                                    "strings_to_urls": False})
    cache = {}
    ov_rows, ov_cols = spec["overview_print_rows"], spec["overview_cols"]
    ws = _transcribe(rc_wb["Overview"], wb, "Overview", cache, clamp=illustrative, rows=ov_rows, cols=ov_cols)
    for c, w in enumerate(spec["overview_widths"]):      # the build's widths (LibreOffice saves its own units)
        ws.set_column(c, c, w)
    ws.set_landscape()
    ws.set_paper(1)
    ws.fit_to_pages(1, 0)
    ws.repeat_rows(3)
    ws.print_area(0, 0, ov_rows - 1, ov_cols - 1)
    ws.set_footer("&COverview: page &P of &N")
    pr = spec["print"]
    ws = _transcribe(rc_wb["Charts"], wb, "Charts", cache)
    ws.set_column(0, pr["cols"] - 1, pr["col_width"])    # the build's widths, so the charts keep their size
    CH.draw(wb, ws, spec["inserts"])
    ws.set_landscape()
    ws.set_paper(1)
    ws.print_area(0, 0, pr["rows"] - 1, pr["cols"] - 1)
    ws.set_h_pagebreaks(pr["breaks"])
    ws.set_print_scale(pr["scale"])
    ws.set_footer("&CCharts: page &P of &N")
    for sw_ in sections_wb.worksheets:
        ws = _transcribe(sw_, wb, sw_.title, cache)
        _page_from(sw_, ws)
    for name in ("Summary", "Distribution"):              # the values the charts read; hidden, not printed
        ws = _transcribe(rc_wb[name], wb, name, cache, values_only=True)
        ws.hide()
    wb.close()


def render_summary_pdf(xlsx, out_dir, profile=None, keep_sections=None, keep_render=None):
    """Spec test 10: recalculate, copy Summary's values and formats into one page group per section, convert to PDF.
    A live build (one with an Overview sheet and a chart specification beside it) opens the PDF with the Overview and
    the charts (spec v0.6.4, CP-4 and CP-5). The workbook itself is unchanged. keep_sections: a path where the section
    workbook is saved, for test 10's layout checks; keep_render: a path for the combined render workbook. Returns the
    PDF path."""
    import openpyxl
    from . import charts as CH
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
        spec = CH.load(xlsx)
        if spec is not None and "Overview" in wb.sheetnames:
            src = os.path.join(tmp, f"{stem}_render.xlsx")
            sections = openpyxl.load_workbook(only)
            _render_book(src, wb, sections, spec, illustrative)
            if keep_render:
                shutil.copyfile(src, keep_render)
            pdf = _convert(src, out_dir, "pdf:calc_pdf_Export", profile=prof)
            final = os.path.join(out_dir, f"{stem}_Summary.pdf")
            shutil.move(pdf, final)
            return final
        return _convert(only, out_dir, "pdf:calc_pdf_Export", profile=prof)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
