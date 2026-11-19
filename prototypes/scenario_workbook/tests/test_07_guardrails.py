"""Test 7: guardrails (spec section 11; Phase 4).

Checked on the main, edge and synthetic reproduce workbooks (live and reproduce builds; conftest main_wb, edge_wb,
repro_syn_wb), on every config file and on the cell schema:

1. No column named race, ethnicity or gender (or sex) in any input or output: config keys, the cell schema, every text
   cell of the workbooks, the contract dump's names.
2. No student-level fields: the cell schema is the section 2 cell-level schema; a cell file with a student-level
   column is refused; no workbook text names a student-level identifier.
3. No formula references an external file; no external links; no defined name points outside the workbook.
4. No hidden sheets, rows or columns.
5. No conditional format or cell text labels an award exceptional, anomalous, out of bounds or beyond a limit: every
   conditional format is one of the three neutral kinds (the 'under 5%' / 'over 95%' display, the grey highlight of a
   change from the parent, the strikeout of an ignored award entry), and no text, formula literal or label uses the
   guardrail vocabulary.
6. Every label in sw/labels.py appears where spec section 4 requires it: RESPONSE_LABEL on every sheet with
   response-dependent outputs and in every Summary section; SHOCK_LABEL in every Summary section with a probability
   or a range and in the Summary header; the 'under 5%' and 'over 95%' display on every probability cell;
   ASSUMPTION_LABEL in the projected-outcome narrative of exactly the scenarios with a non-zero shift or lift;
   SEGMENT_SHARE_LABEL in the segment block while the share is assumed; the two range kinds in the README and in every
   range row label. Every label constant is used by the generator code.
"""
import glob
import os
import re

import pytest
import yaml

from conftest import ROOT
from sw import cells as C, labels, ledger as L

PROTECTED = re.compile(r"\b(race|races|racial|ethnicity|ethnic|gender|sex)\b", re.I)
STUDENT = re.compile(r"\b(student_id|student id|first_name|last_name|full_name|e-?mail|date_of_birth|birth ?date|"
                     r"dob|ssn|social security|street address|zip5|lsac account|applicant_id)\b", re.I)
GUARDRAIL = re.compile(r"exceptional|anomal|out[ -]of[ -]bounds|beyond (a|the) limit|outlier|unusual|excessive|"
                       r"abnormal|extreme|too high|too low|suspicious|red flag|over the limit|above the limit",
                       re.I)
RESPONSE_SHEETS = ("Response", "Ledger_Low", "Ledger_Middle", "Ledger_High", "Summary", "Trim", "Distribution")


@pytest.fixture(scope="module")
def books(main_wb, edge_wb, repro_syn_wb):
    import openpyxl
    out = []
    for name, b in (("main", main_wb), ("edge", edge_wb), ("reproduce", repro_syn_wb)):
        out.append({"name": name, "bundle": b, "built": openpyxl.load_workbook(b["path"]),
                    "values": b["values"]})
    return out


def _strings(wb):
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str):
                    yield ws.title, c.coordinate, c.value


def _yaml_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{path}.{k}"
            yield from _yaml_keys(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for v in obj:
            yield from _yaml_keys(v, path)


# 1 and 2 ---------------------------------------------------------------------------------------------------------

def test_no_protected_attribute_columns(books, tmp_path):
    import edge
    cfgs = glob.glob(os.path.join(ROOT, "config", "*.yaml"))
    cp, sp = edge.write(str(tmp_path))
    for f in cfgs + [cp, sp]:
        with open(f) as fh:
            for k in _yaml_keys(yaml.safe_load(fh) or {}):
                assert not PROTECTED.search(k.rsplit(".", 1)[-1]), (f, k)
    for col in C.COLUMNS:
        assert not PROTECTED.search(col)
    for bk in books:
        for sheet, coord, v in _strings(bk["values"]):
            assert not PROTECTED.search(v), (bk["name"], sheet, coord, v[:120])
        for rn in bk["bundle"]["info"]["dump"]:
            assert not PROTECTED.search(rn)
        df = bk["bundle"]["info"]["run"].cells
        assert not any(PROTECTED.search(str(c)) for c in C.COLUMNS + list(vars(df)))


def test_no_student_level_fields(books, tmp_path, syn_cfg):
    assert C.COLUMNS == ["cell_id", "residency", "segment", "score_lo", "gpa_class", "cohort", "apps", "admits",
                         "award_usd", "enrolled"]
    from sw.config import ConfigError
    p = tmp_path / "cells.csv"
    p.write_text("cell_id,residency,segment,score_lo,gpa_class,cohort,apps,admits,award_usd,enrolled,student_id\n"
                 "a,in,,170,hi,2024,10,5,1000,1,s1\n")
    with pytest.raises(ConfigError, match="outside the schema"):
        C.read_csv(str(p), syn_cfg)
    for bk in books:
        for sheet, coord, v in _strings(bk["values"]):
            assert not STUDENT.search(v), (bk["name"], sheet, coord, v[:120])
        # every Ledger row is a cell, not a student
        lay = bk["bundle"]["info"]["layout"]
        ws = bk["values"]["Ledger_Middle"]
        ids = [ws.cell(lay["r0l"] + 1 + i, 1).value for i in range(lay["n"])]
        assert ids == list(bk["bundle"]["info"]["run"].cells.cell_id)


# 3 and 4 ---------------------------------------------------------------------------------------------------------

def test_no_external_references(books):
    for bk in books:
        wb = bk["built"]
        assert not wb._external_links, bk["name"]
        for nm in wb.defined_names:
            dest = wb.defined_names[nm].attr_text
            assert "[" not in dest and ".xls" not in dest.lower(), (nm, dest)
        for ws in wb.worksheets:
            for row in ws.iter_rows():
                for c in row:
                    f = c.value
                    if isinstance(f, str) and f.startswith("="):
                        g = re.sub(r'"[^"]*"', '""', f)
                        assert "[" not in g and ".xls" not in g.lower() and "://" not in g, \
                            (bk["name"], ws.title, c.coordinate)


def test_no_hidden_sheets_rows_columns(books):
    for bk in books:
        wb = bk["built"]
        for ws in wb.worksheets:
            assert ws.sheet_state == "visible", (bk["name"], ws.title)
            for k, d in ws.row_dimensions.items():
                assert not d.hidden, (bk["name"], ws.title, "row", k)
            for k, d in ws.column_dimensions.items():
                assert not d.hidden, (bk["name"], ws.title, "column", k)


# 5 ---------------------------------------------------------------------------------------------------------------

def _cf_kind(rule):
    dxf = rule.dxf
    nf = dxf.numFmt.formatCode if dxf is not None and dxf.numFmt is not None else None
    fill = None
    if dxf is not None and dxf.fill is not None:
        fill = str(dxf.fill.bgColor.rgb if dxf.fill.bgColor is not None else "") or \
            str(dxf.fill.fgColor.rgb if dxf.fill.fgColor is not None else "")
    font = dxf.font if dxf is not None else None
    if nf in (f'"{labels.PROB_UNDER}"', f'"{labels.PROB_OVER}"') and not fill and font is None:
        return "clamp"
    if fill and fill.upper().endswith("D9D9D9") and nf is None and (font is None or font.color is None):
        return "changed"
    if font is not None and font.strike and fill in (None, "", "00000000") and nf is None:
        return "ignored"
    return None


def test_no_award_characterization(books):
    kinds = set()
    for bk in books:
        wb = bk["built"]
        for ws in wb.worksheets:
            for cf in ws.conditional_formatting:
                for rule in cf.rules:
                    k = _cf_kind(rule)
                    assert k, (bk["name"], ws.title, str(cf.sqref), rule.formula)
                    kinds.add(k)
                    for f in rule.formula or []:
                        assert not GUARDRAIL.search(f)
                    if k in ("changed", "ignored"):
                        assert ws.title == "Levers", (ws.title, k)
            for row in ws.iter_rows():
                for c in row:
                    if isinstance(c.value, str):
                        for lit in (re.findall(r'"([^"]*)"', c.value) if c.value.startswith("=") else [c.value]):
                            assert not GUARDRAIL.search(lit), (bk["name"], ws.title, c.coordinate, lit[:120])
        for sheet, coord, v in _strings(bk["values"]):
            assert not GUARDRAIL.search(v), (bk["name"], sheet, coord, v[:120])
    assert kinds == {"clamp", "changed", "ignored"}
    text = " ".join(v for k, v in vars(labels).items() if k.isupper() and isinstance(v, str))
    assert not GUARDRAIL.search(text)


# 6 ---------------------------------------------------------------------------------------------------------------

def _summary_sections(ws):
    secs, cur = [], None
    for r in range(1, ws.max_row + 1):
        a = ws.cell(r, 1)
        if a.fill is not None and a.fill.fgColor is not None and str(a.fill.fgColor.rgb).upper().endswith("E8E8E8"):
            cur = {"title": a.value, "text": [], "prob": 0, "nums": 0, "range_rows": []}
            secs.append(cur)
            continue
        if cur is None:
            continue
        for c in range(1, ws.max_column + 1):
            cell = ws.cell(r, c)
            if isinstance(cell.value, str):
                cur["text"].append(cell.value)
            if cell.number_format == "0%" and c > 2:
                cur["prob"] += 1
            if isinstance(cell.value, (int, float)) and c > 2:
                cur["nums"] += 1
        if isinstance(a.value, str) and re.search(r"\brange\b|LO90|HI90", a.value.replace("(range)", ""), re.I):
            cur["range_rows"].append(a.value)
    return secs


def test_labels_where_section_4_requires(books):
    import openpyxl.utils
    for bk in books:
        wb, run = bk["values"], bk["bundle"]["info"]["run"]
        cfg = run.cfg
        shock = labels.shock_label(cfg["risk"]["common_shock_sd"])
        illustrative = cfg["risk"]["shock_source"] == "illustrative"
        # RESPONSE_LABEL on every sheet with response-dependent outputs (title or note rows)
        for sh in RESPONSE_SHEETS:
            if sh not in wb.sheetnames:
                continue
            top = " ".join(str(wb[sh].cell(r, c).value) for r in range(1, 4) for c in range(1, 4))
            assert labels.RESPONSE_LABEL in top, (bk["name"], sh)
        ws = wb["Summary"]
        head = " ".join(str(ws.cell(3, c).value) for c in range(1, 5))
        assert labels.RESPONSE_LABEL in head and (shock in head) == illustrative
        secs = _summary_sections(ws)
        assert len(secs) >= 10
        for sec in secs:
            txt = " | ".join(sec["text"])
            if sec["title"] == "Labels and range kinds":
                continue
            if not sec["nums"] and not sec["title"].startswith("Narratives"):
                continue            # no figures (the reproduce build's class-size placeholder)
            assert labels.RESPONSE_LABEL in txt, (bk["name"], sec["title"])
            if sec["prob"] or sec["range_rows"]:
                assert shock in txt, (bk["name"], sec["title"])
            for lab in sec["range_rows"]:
                # a range row names its kind; rows labeled by a contract range name (..._LO90, ..._HI90) take it
                # from the section note
                if re.search(r"LO90|HI90", lab):
                    assert labels.RANGE_OUTCOME in txt, (bk["name"], lab)
                else:
                    assert labels.RANGE_OUTCOME in lab or labels.RANGE_CASES in lab, (bk["name"], lab)
            if sec["title"].startswith("Segment block") and cfg["segments"] \
                    and cfg["segments"][0]["share_source"] == "assumed":
                assert labels.SEGMENT_SHARE_LABEL in txt
        # the 'under 5%' / 'over 95%' display covers every probability cell on every sheet
        built = bk["built"]
        for wsb in built.worksheets:
            covered = set()
            for cf in wsb.conditional_formatting:
                if any(_cf_kind(r) == "clamp" for r in cf.rules):
                    kinds = {r.dxf.numFmt.formatCode for r in cf.rules if _cf_kind(r) == "clamp"}
                    for rg in str(cf.sqref).split():
                        c0, r0, c1, r1 = openpyxl.utils.range_boundaries(rg)
                        for rr in range(r0, r1 + 1):
                            for cc in range(c0, c1 + 1):
                                covered.add((rr, cc, frozenset(kinds)))
            cov = {(r, c) for r, c, k in covered if len(k) == 2}
            for row in wsb.iter_rows():
                for c in row:
                    if c.number_format == "0%" and isinstance(c.value, str) and c.value.startswith("="):
                        assert (c.row, c.column) in cov, (bk["name"], wsb.title, c.coordinate)
        # ASSUMPTION_LABEL in the projected outcome of exactly the scenarios with a shift or lift
        outcome = {}
        cur = None
        for r in range(1, ws.max_row + 1):
            if ws.cell(r, 2).value == "Changes from parent":
                cur = ws.cell(r, 1).value
            elif ws.cell(r, 2).value == "Projected outcome":
                outcome[cur] = str(ws.cell(r, 3).value)
        assert set(outcome) == {s.name for s in run.scenarios}
        flagged = 0
        for s in run.scenarios:
            want = labels.ASSUMPTION_LABEL in L.scenario_labels(s, cfg)
            flagged += want
            assert (labels.ASSUMPTION_LABEL in outcome[s.name]) == want, (bk["name"], s.name)
            assert labels.RESPONSE_LABEL in outcome[s.name]
            assert (shock in outcome[s.name]) == illustrative
        if bk["name"] == "edge":
            assert 0 < flagged < len(run.scenarios)
    # README: every label and both range kinds
    readme = " ".join(v for sh, _, v in _strings(books[0]["values"]) if sh == "README")
    for t in (labels.RESPONSE_LABEL, labels.ASSUMPTION_LABEL, labels.SEGMENT_SHARE_LABEL, labels.RANGE_OUTCOME,
              labels.RANGE_CASES, labels.PROB_UNDER, labels.PROB_OVER, "Year-to-year variation assumed"):
        assert t in readme, t


def test_every_label_constant_is_used():
    src = "".join(open(f).read() for f in glob.glob(os.path.join(ROOT, "sw", "*.py"))
                  if not f.endswith("labels.py"))
    unused = [k for k, v in vars(labels).items() if k.isupper() and isinstance(v, str) and f"labels.{k}" not in src]
    assert not unused, unused
