"""Test 29 (spec v0.6.4 section 0B, CP-5 and CP-6): the charts and the Overview links.

Reads each chart's XML in the built workbook (xl/charts/chartN.xml, mapped to the Charts sheet through its drawing) and
checks that every series references the intended range. The intended ranges are found here independently of the
builder's records: Summary rows by their printed label (the dictionary's plain label), the strips by their named
ranges, the chart-data rows on the Charts sheet by their labels, and the merit-by-band table on Distribution by its
title. The chart-data cells are checked too: each chance cell reads the Summary row whose label is its category, the
error-bar lengths read the likely-range rows. The Overview: every figure is a formula on the Summary row whose label is
the Overview row's label (or, for a likely range, the low and high rows). Also: nine charts with the CP-5 titles; one
color per scenario across the charts, Baseline grey; under hold_position_rows no series reads a median or percentile
row. No LibreOffice: the builds are read for their formulas and XML only.
"""
import os
import re
import zipfile

import openpyxl
import pytest
from openpyxl.utils import get_column_letter

from conftest import ROOT
from sw import build, contract, dictionary as DD

NS = {"c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("charts")
    res = {}
    for name, hold in (("main", False), ("hold", True)):
        cfgp = os.path.join(ROOT, "config", "synthetic.yaml")
        if hold:
            import yaml
            raw = yaml.safe_load(open(cfgp))
            raw["hold_position_rows"] = True
            cfgp = str(out / "hold.yaml")
            yaml.safe_dump(raw, open(cfgp, "w"), sort_keys=False)
        path, info = build.build(cfgp, "synthetic", os.path.join(ROOT, "config", "scenarios_synthetic.yaml"),
                                 str(out / name), seed=101)
        res[name] = {"path": path, "info": info, "wb": openpyxl.load_workbook(path), "charts": charts_of(path)}
    return res


def charts_of(path):
    """[(title, [series dict])] for the charts on the Charts sheet, in drawing order. A series dict holds its formulas:
    name, cat, val, x, y, plus, minus, and its fill color."""
    import xml.etree.ElementTree as ET
    z = zipfile.ZipFile(path)
    wbx = z.read("xl/workbook.xml").decode()
    rels = z.read("xl/_rels/workbook.xml.rels").decode()
    rid = re.search(r'<sheet name="Charts" sheetId="\d+" r:id="(rId\d+)"', wbx).group(1)
    sheet = re.search(rf'Id="{rid}"[^>]*Target="worksheets/(sheet\d+\.xml)"', rels)
    sheet = sheet.group(1) if sheet else re.search(rf'Target="worksheets/(sheet\d+\.xml)"[^>]*Id="{rid}"',
                                                   rels).group(1)
    srels = z.read(f"xl/worksheets/_rels/{sheet}.rels").decode()
    drawing = re.search(r'Target="../drawings/(drawing\d+\.xml)"', srels).group(1)
    drels = z.read(f"xl/drawings/_rels/{drawing}.rels").decode()
    dxml = z.read(f"xl/drawings/{drawing}").decode()
    order = re.findall(r'<c:chart [^>]*r:id="(rId\d+)"', dxml)
    targets = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="../charts/(chart\d+\.xml)"', drels))
    out = []
    for r in order:
        root = ET.fromstring(z.read(f"xl/charts/{targets[r]}"))
        title = "".join(t.text or "" for t in root.find("c:chart/c:title", NS).iter(f"{{{NS['a']}}}t"))
        series = []
        for ser in root.iter(f"{{{NS['c']}}}ser"):
            def f(path_):
                e = ser.find(path_, NS)
                return e.text if e is not None else None
            d = {"name": f("c:tx/c:strRef/c:f") or f("c:tx/c:v"), "cat": f("c:cat/c:strRef/c:f") or
                 f("c:cat/c:numRef/c:f"), "val": f("c:val/c:numRef/c:f"), "x": f("c:xVal/c:numRef/c:f"),
                 "y": f("c:yVal/c:numRef/c:f"), "plus": f("c:errBars/c:plus/c:numRef/c:f"),
                 "minus": f("c:errBars/c:minus/c:numRef/c:f")}
            fills = [e.get("val") for e in ser.findall("c:spPr/a:solidFill/a:srgbClr", NS)]
            fills += [e.get("val") for e in ser.findall("c:spPr/a:ln/a:solidFill/a:srgbClr", NS)]
            d["color"] = fills[0] if fills else None
            d["points"] = [e.get("val") for e in ser.findall("c:dPt/c:spPr/a:solidFill/a:srgbClr", NS)]
            series.append(d)
        out.append((title, series))
    return out


def rng(sheet, r0, c0, r1, c1):
    """An absolute range in openpyxl's 1-based rows and columns, as XlsxWriter writes it."""
    q = f"'{sheet}'" if " " in sheet else sheet
    a = f"${get_column_letter(c0)}${r0}"
    b = f"${get_column_letter(c1)}${r1}"
    return f"{q}!{a}:{b}" if (r0, c0) != (r1, c1) else f"{q}!{a}"


def summary_row(ws, label, start=1):
    """The first Summary row (1-based) at or after `start` whose column A reads `label`."""
    for r in range(start, ws.max_row + 1):
        if ws.cell(r, 1).value == label:
            return r
    raise AssertionError(f"Summary has no row labelled {label!r}")


def named(wb, name):
    (sheet, coord), = list(wb.defined_names[name].destinations)
    from openpyxl.utils import range_boundaries
    c0, r0, c1, r1 = range_boundaries(coord.replace("$", ""))
    return sheet, r0, c0, r1, c1


def charts_col_a(wb, text):
    ws = wb["Charts"]
    for r in range(1, ws.max_row + 1):
        if ws.cell(r, 1).value == text:
            return r
    raise AssertionError(f"Charts has no chart-data row {text!r}")


def test_nine_charts_with_their_questions(built):
    want = [DD.lab(x) for x in ("chart_class", "chart_ntr", "chart_chances", "chart_pool", "chart_pool_cap",
                                "chart_class_size", "chart_tuition", "chart_yield", "chart_merit")]
    for b in built.values():
        titles = sorted(t for t, _ in b["charts"])
        assert titles == sorted(want), titles


def _by_title(b, rid_name):
    t = DD.lab(rid_name)
    return next(s for title, s in b["charts"] if title == t)


@pytest.mark.parametrize("which", ["main", "hold"])
def test_class_and_revenue_charts_read_the_summary_rows(built, which):
    b = built[which]
    wb, run = b["wb"], b["info"]["run"]
    ws = wb["Summary"]
    nS = len(run.scenarios)
    c0, c1 = 3, 2 + nS
    cats_row = charts_col_a(wb, "scenario")
    cats = rng("Charts", cats_row, 2, cats_row, 1 + nS)
    a0 = summary_row(ws, DD.lab("sec_title_A"))
    b0 = summary_row(ws, DD.lab("sec_title_B"))
    for chart, mean, lo, hi, refs in (("chart_class", "OUT-008", "OUT-009", "OUT-010", ("IN-099", "IN-098")),
                                      ("chart_ntr", "OUT-038", "OUT-039", "OUT-040", ())):
        start = a0 if chart == "chart_class" else b0
        ser = _by_title(b, chart)
        rm = summary_row(ws, DD.label(mean), start)
        assert ser[0]["val"] == rng("Summary", rm, c0, rm, c1), (chart, ser[0]["val"])
        assert ser[0]["cat"] == cats
        assert len(ser[0]["points"]) == nS and ser[0]["points"][0].upper() == "8C8C8C"
        rp = charts_col_a(wb, f"{DD.label(hi)}: distance above the expected value")
        rmn = charts_col_a(wb, f"{DD.label(lo)}: distance below the expected value")
        assert ser[0]["plus"] == rng("Charts", rp, 2, rp, 1 + nS)
        assert ser[0]["minus"] == rng("Charts", rmn, 2, rmn, 1 + nS)
        fw = wb["Charts"]
        rh, rl = summary_row(ws, DD.label(hi), start), summary_row(ws, DD.label(lo), start)
        for j in range(nS):
            col = get_column_letter(3 + j)
            assert fw.cell(rp, 2 + j).value == f"=Summary!${col}${rh}-Summary!${col}${rm}"
            assert fw.cell(rmn, 2 + j).value == f"=Summary!${col}${rm}-Summary!${col}${rl}"
        for k, rid_ in enumerate(refs):
            rr = summary_row(ws, DD.label(rid_), start)
            assert ser[1 + k]["val"] == rng("Summary", rr, c0, rr, c1), (rid_, ser[1 + k]["val"])
        if chart == "chart_ntr" and run.cfg.get("ntr_target") is not None:
            rg = charts_col_a(wb, DD.label("OUT-042"))
            assert ser[1]["val"] == rng("Charts", rg, 2, rg, 1 + nS)
            rs = summary_row(ws, DD.label("OUT-042"), start)
            for j in range(nS):
                col = get_column_letter(3 + j)
                assert fw.cell(rg, 2 + j).value == f"=IF(ISNUMBER(Summary!${col}${rs}),Summary!${col}${rs},NA())"


@pytest.mark.parametrize("which", ["main", "hold"])
def test_chance_chart_reads_each_outcomes_row(built, which):
    b = built[which]
    wb, run = b["wb"], b["info"]["run"]
    ws, fw = wb["Summary"], wb["Charts"]
    nS = len(run.scenarios)
    ser = _by_title(b, "chart_chances")
    assert len(ser) == nS
    cat = ser[0]["cat"]
    m = re.match(r"Charts!\$A\$(\d+):\$A\$(\d+)", cat)
    r0, r1 = int(m.group(1)), int(m.group(2))
    from sw import risk
    held = {DD.label("OUT-020", measure="GPA" if m_ == "gpa" else run.cfg["score"]["measure"], t=f"{t:g}")
            for m_, t in risk.median_targets(run.cfg)}
    for j, s in enumerate(ser):
        assert s["cat"] == cat
        assert s["val"] == rng("Charts", r0, 2 + j, r1, 2 + j)
        if j == 0:
            assert (s["color"] or "").upper() == "8C8C8C"
    labels_ = [fw.cell(r, 1).value for r in range(r0, r1 + 1)]
    assert DD.label("OUT-011") in labels_
    if run.cfg.get("hold_position_rows"):
        assert not (held & set(labels_)), "a held median is drawn"
    else:
        assert held <= set(labels_)
    sec_c = summary_row(ws, DD.lab("sec_title_C", measure=run.cfg["score"]["measure"]))
    for r, lab in zip(range(r0, r1 + 1), labels_):
        rs = summary_row(ws, lab)
        assert rs < summary_row(ws, DD.lab("sec_title_H")), lab       # the section row, not a technical copy
        for j in range(nS):
            col = get_column_letter(3 + j)
            assert fw.cell(r, 2 + j).value == f"=IF(ISNUMBER(Summary!${col}${rs}),Summary!${col}${rs},NA())", \
                (lab, j)
    assert sec_c > 0


@pytest.mark.parametrize("which", ["main", "hold"])
def test_strip_charts_read_each_scenarios_rows(built, which):
    b = built[which]
    wb, run = b["wb"], b["info"]["run"]
    cfg = run.cfg
    nS = len(run.scenarios)
    cols = contract.strip_columns(cfg)
    for chart, rname, which_, col in (("chart_pool", "PS_POOL_STRIP", "pool_strip", "class_mean"),
                                      ("chart_pool_cap", "PS_POOL_STRIP", "pool_strip", "p_class_over_cap"),
                                      ("chart_tuition", "TW_TUITION_WHATIF", "tuition_whatif", "ntr_y1"),
                                      ("chart_yield", "YS_YIELD_STRIP", "yield_strip", "class_mean")):
        sh, r0, c0, r1, c1 = named(wb, rname)
        ng = (r1 - r0 + 1) // nS
        ci = c0 + cols[which_].index(col)
        ser = _by_title(b, chart)
        for j in range(nS):
            ra, rb = r0 + j * ng, r0 + (j + 1) * ng - 1
            assert ser[j]["x"] == rng("Summary", ra, 2, rb, 2), (chart, j, ser[j]["x"])
            assert ser[j]["y"] == rng("Summary", ra, ci, rb, ci), (chart, j, ser[j]["y"])
        for s in ser[nS:]:
            assert s["x"] and s["x"].startswith("Charts!") and s["y"].startswith("Charts!")


def test_class_size_and_merit_charts(built):
    b = built["main"]
    wb, run = b["wb"], b["info"]["run"]
    nS = len(run.scenarios)
    fw = wb["Charts"]
    ser = _by_title(b, "chart_class_size")
    assert len(ser) == 1
    m = re.match(r"Charts!\$B\$(\d+):\$B\$(\d+)", ser[0]["val"])
    r0, r1 = int(m.group(1)), int(m.group(2))
    sh, c0r, c0c, c1r, c1c = named(wb, "CT_CLASS_TABLE")
    ntr_col = get_column_letter(c0c + contract.strip_columns(run.cfg)["class_table"].index("ntr_y1"))
    ct = f"Summary!${ntr_col}${c0r}:${ntr_col}${c1r}"
    for r in range(r0, r1 + 1):
        assert ct in fw.cell(r, 2).value and "in_chart_scenario" in fw.cell(r, 2).value
    assert r1 - r0 + 1 == len(run.cfg["class"]["what_if"])
    ser = _by_title(b, "chart_merit")
    dw = wb["Distribution"]
    title = DD.label(DD.rid("merit_by_band"), measure=run.cfg["score"]["measure"])
    rt = next(r for r in range(1, dw.max_row + 1) if dw.cell(r, 1).value == title)
    first = rt + 3
    last = first + len(run.cfg["score"]["bands"])            # every band, then no score
    assert len(ser) == nS
    for j, s in enumerate(ser):
        assert s["val"] == rng("Distribution", first, 3 + j, last, 3 + j), s["val"]
        assert s["cat"] == rng("Distribution", first, 1, last, 1)


def test_one_color_per_scenario(built):
    """CP-5: a scenario has one color in every chart; Baseline is neutral grey; no two scenarios share a color."""
    b = built["main"]
    S = [s.name for s in b["info"]["run"].scenarios]
    seen = {}
    for title, ser in b["charts"]:
        for s in ser:
            name = s["name"]
            if name in S and s["color"]:
                seen.setdefault(name, set()).add(s["color"].upper())
        if ser and ser[0]["points"]:
            for j, c in enumerate(ser[0]["points"]):
                seen.setdefault(S[j], set()).add(c.upper())
    assert all(len(v) == 1 for v in seen.values()), seen
    assert seen[S[0]] == {"8C8C8C"}
    colors = [next(iter(v)) for v in seen.values()]
    assert len(colors) == len(set(colors))


@pytest.mark.parametrize("which", ["main", "hold"])
def test_overview_links_point_at_the_labelled_summary_rows(built, which):
    """CP-4: each Overview figure is =Summary!<cell> on the row whose label is the Overview row's label (the likely
    range rows join the low and high rows); a held row reads the Summary's hold cell."""
    b = built[which]
    wb, run = b["wb"], b["info"]["run"]
    ov, ws = wb["Overview"], wb["Summary"]
    nS = len(run.scenarios)
    rng_labels = {DD.lab("overview_range_class"): ("OUT-009", "OUT-010"),
                  DD.lab("overview_range_ntr"): ("OUT-039", "OUT-040")}
    n = 0
    stop = summary_row(ws, DD.lab("sec_title_H"))
    for r in range(4, ov.max_row + 1):
        lab = ov.cell(r, 1).value
        f = ov.cell(r, 3).value
        if not isinstance(f, str) or not f.startswith("="):
            continue
        n += 1
        if lab in rng_labels:
            lo_, hi_ = (summary_row(ws, DD.label(x)) for x in rng_labels[lab])
            for j in range(nS):
                col = get_column_letter(3 + j)
                fj = ov.cell(r, 3 + j).value
                assert f"Summary!${col}${lo_}" in fj and f"Summary!${col}${hi_}" in fj, (lab, j)
            continue
        rs = summary_row(ws, lab)
        assert rs < stop, lab
        if ov.cell(r, 4).value is None:                          # a held row: one merged cell
            assert f == f"=Summary!$C${rs}", (lab, f)
            continue
        for j in range(nS):
            col = get_column_letter(3 + j)
            assert ov.cell(r, 3 + j).value == f"=Summary!${col}${rs}", (lab, j)
    assert 12 <= n <= 20, n
