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


def _section_copy(src_ws, wb_out, shock_illustrative):
    """Copy Summary (values and formats) into one sheet per section of wb_out, each printed landscape and fit to its
    own width, so narrow blocks are not shrunk to the width of the widest table. Probability cells (format 0%) show
    'under 5%' and 'over 95%' while the shock is illustrative (the workbook does this with conditional formats, which
    a values-only copy cannot carry)."""
    from copy import copy
    from . import labels
    rows = list(range(1, src_ws.max_row + 1))
    starts = [r for r in rows if (src_ws.cell(r, 1).fill is not None and src_ws.cell(r, 1).fill.fgColor is not None
                                  and str(src_ws.cell(r, 1).fill.fgColor.rgb).upper().endswith("E8E8E8"))]
    bounds = [1] + starts[1:] + [src_ws.max_row + 1]
    merges = [m for m in src_ws.merged_cells.ranges]
    for si in range(len(bounds) - 1):
        r0, r1 = bounds[si], bounds[si + 1] - 1
        title = src_ws.cell(bounds[si], 1).value or "Summary"
        ws = wb_out.create_sheet(f"S{si + 1:02d}")
        maxc = 1
        for r in range(r0, r1 + 1):
            for c in range(1, src_ws.max_column + 1):
                sc = src_ws.cell(r, c)
                if sc.value is None and not sc.has_style:
                    continue
                v = sc.value
                if (shock_illustrative and isinstance(v, (int, float)) and not isinstance(v, bool)
                        and sc.number_format == "0%"):
                    v = labels.PROB_UNDER if v < 0.05 else labels.PROB_OVER if v > 0.95 else v
                dc = ws.cell(r - r0 + 1, c, v)
                if sc.has_style:
                    dc.font, dc.fill, dc.border = copy(sc.font), copy(sc.fill), copy(sc.border)
                    dc.alignment, dc.number_format = copy(sc.alignment), sc.number_format
                if sc.value not in (None, ""):
                    maxc = max(maxc, c)
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
        ws.print_area = f"A1:{ws.cell(1, maxc).column_letter}{r1 - r0 + 1}"
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.oddHeader.center.text = str(title)[:120]


def render_summary_pdf(xlsx, out_dir, profile=None):
    """Spec test 10: recalculate, copy Summary's values and formats into one page group per section, convert to PDF.
    The workbook itself is unchanged."""
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
        return _convert(only, out_dir, "pdf:calc_pdf_Export", profile=prof)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
