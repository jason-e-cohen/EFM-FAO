"""Test 3: Excel equals Python (spec section 11, [v0.6, B1-25]).

Build from a synthetic world, recalculate with a dedicated LibreOffice profile whose registrymodifications.xcu sets
/org.openoffice.Office.Calc/Formula/Load/OOXMLRecalcMode to 0, read with openpyxl(data_only=True), and compare every
formula cell to the Python value the builder recorded from the reference functions. The spec asks for every Ledger and
Summary numeric cell; this test compares every formula cell on every sheet (numbers, and text such as evidence labels,
statuses and narratives). Integers exact; floats within 1e-6 relative (1e-9 absolute near zero).

Guard: a copy built with every cached value set to -999 must show no -999 after recalculation, which proves
LibreOffice recalculated every formula rather than reading cached values. Skips, with the reason, if soffice is missing.
"""
import collections
import json
import os

from conftest import PHASE2, close


def _compare(bundle):
    wb = bundle["values"]
    bad = collections.defaultdict(list)
    count = collections.Counter()
    for (sheet, r, c), v in bundle["info"]["expected"].items():
        got = wb[sheet].cell(r + 1, c + 1).value
        count[sheet] += 1
        if not close(got, v):
            bad[sheet].append({"cell": wb[sheet].cell(r + 1, c + 1).coordinate, "python": v, "excel": got})
    return count, bad


def test_excel_equals_python(main_wb):
    count, bad = _compare(main_wb)
    report = {"workbook": main_wb["path"], "cells_compared": dict(count),
              "mismatches": {k: v[:20] for k, v in bad.items()}}
    with open(os.path.join(PHASE2, "test03_report.json"), "w") as f:
        json.dump(report, f, indent=1, default=str)
    for sheet in ("Ledger_Low", "Ledger_Middle", "Ledger_High", "Summary"):
        assert count[sheet] > 0, f"no formula cells recorded on {sheet}"
    assert not bad, {k: v[:5] for k, v in bad.items()}


def test_sentinel_guard(sentinel_wb):
    """Every cached value was -999; none may survive the recalculation."""
    wb = sentinel_wb["values"]
    expected = sentinel_wb["info"]["expected"]
    left = [(s, r, c) for (s, r, c) in expected if wb[s].cell(r + 1, c + 1).value in (-999, "-999")]
    assert len(expected) > 10_000
    assert not left, left[:10]
    # The sentinel copy recalculates to the same values as the normal build.
    count, bad = _compare(sentinel_wb)
    assert not bad, {k: v[:5] for k, v in bad.items()}


def test_profile_forces_recalculation(lo_profile):
    with open(os.path.join(lo_profile, "user", "registrymodifications.xcu")) as f:
        xcu = f.read()
    assert '/org.openoffice.Office.Calc/Formula/Load' in xcu
    assert '<prop oor:name="OOXMLRecalcMode" oor:op="fuse"><value>0</value>' in xcu


def test_formula_vocabulary(main_wb):
    """Spec section 6: no external references, no volatile or dynamic-array functions, no LET or LAMBDA, no AND or
    OR (comparison arithmetic instead)."""
    import re
    import openpyxl
    wb = openpyxl.load_workbook(main_wb["path"])          # the file as built (what Excel opens)
    banned = re.compile(r"\b(INDIRECT|OFFSET|NOW|TODAY|RAND|RANDBETWEEN|LET|LAMBDA|FILTER|SORT|UNIQUE|SEQUENCE|"
                        r"XLOOKUP|TEXTJOIN|AND|OR|CELL|INFO)\(", re.I)
    allowed = {"ROUND", "SUM", "SUMPRODUCT", "INDEX", "MATCH", "MIN", "MAX", "IF", "SQRT", "NORMSDIST", "TEXT"}
    seen = set()
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                f = c.value
                if isinstance(f, str) and f.startswith("="):
                    f = re.sub(r'"[^"]*"', '""', f)          # string literals out
                    assert "[" not in f, f"external reference in {ws.title}!{c.coordinate}"
                    assert not banned.search(f), f"{ws.title}!{c.coordinate}: {f[:120]}"
                    seen |= set(re.findall(r"([A-Z][A-Z0-9.]*)\(", f))
    extra = {s for s in seen if s.replace("LEGACY.", "").replace("_XLFN.", "") not in allowed}
    assert not extra, sorted(extra)


def test_two_builds_differ_only_in_runlog(tmp_path):
    """Spec section 6 [v0.6, B5-3]: document properties use a fixed creation time from the build id, so two builds of
    the same inputs differ only in RunLog (its timestamp, a shared string). Needs no LibreOffice."""
    import re
    import time
    import zipfile
    from conftest import ROOT
    from sw import build
    args = (os.path.join(ROOT, "config", "synthetic.yaml"), "synthetic",
            os.path.join(ROOT, "config", "scenarios_synthetic.yaml"))
    a, ia = build.build(*args, str(tmp_path / "a"))
    time.sleep(1.1)
    b, ib = build.build(*args, str(tmp_path / "b"))
    assert ia["build_id"] == ib["build_id"]
    za, zb = zipfile.ZipFile(a), zipfile.ZipFile(b)
    assert za.namelist() == zb.namelist()
    diff = [n for n in za.namelist() if za.read(n) != zb.read(n)]
    assert diff in ([], ["xl/sharedStrings.xml"])
    if diff:
        sa = re.findall(r"<t[^>]*>([^<]*)</t>", za.read(diff[0]).decode())
        sb = re.findall(r"<t[^>]*>([^<]*)</t>", zb.read(diff[0]).decode())
        changed = [(x, y) for x, y in zip(sa, sb) if x != y]
        assert len(sa) == len(sb) and len(changed) == 1
        assert re.match(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d", changed[0][0])     # the RunLog timestamp
