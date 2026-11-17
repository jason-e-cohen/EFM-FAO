"""Test 3: Excel equals Python (spec section 11, [v0.6, B1-25]).

Build from a synthetic world, recalculate with a dedicated LibreOffice profile whose registrymodifications.xcu sets
/org.openoffice.Office.Calc/Formula/Load/OOXMLRecalcMode to 0, read with openpyxl(data_only=True), and compare every
formula cell to the Python value the builder recorded from the reference functions. The spec asks for every Ledger and
Summary numeric cell; this test compares every formula cell on every sheet (numbers, and text such as evidence labels,
statuses and narratives). Integers exact; floats within 1e-6 relative (1e-9 absolute near zero).

Guard: a copy built with every cached value set to -999 must show no -999 after recalculation, which proves
LibreOffice recalculated every formula rather than reading cached values. Skips, with the reason, if soffice is missing.

Edge workbook [v0.6.2, P2-01]: a third workbook (tests/edge.py) built to reach the branches the main and test 8
workbooks never take (clips at the floor and cap, inner clip, unflagged award above tuition, in-state override,
need_total override, non-integer goal, a child differing only in one full_tuition flag, a segment pool exactly at the
pooling threshold, rho 0.5, floor_rate with exempt cells, a shortfall, budget basis merit, the history reconciliation)
is compared cell by cell like the main one; `test_edge_inputs_reach_every_branch` keeps it an edge workbook.
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


def test_edge_workbook_equals_python(edge_wb):
    count, bad = _compare(edge_wb)
    report = {"workbook": edge_wb["path"], "cells_compared": dict(count),
              "mismatches": {k: v[:20] for k, v in bad.items()}}
    with open(os.path.join(PHASE2, "test03_edge_report.json"), "w") as f:
        json.dump(report, f, indent=1, default=str)
    assert sum(count.values()) > 10_000
    assert not bad, {k: v[:5] for k, v in bad.items()}


def test_edge_inputs_reach_every_branch(edge_wb):
    """The edge inputs still reach each branch they were built for (Review_Phase2_Build.md section 2)."""
    import numpy as np
    from sw import labels, ledger as L, strip, trim
    run, cfg, cells, base = edge_wb["info"]["run"], edge_wb["info"]["run"].cfg, edge_wb["info"]["run"].cells, \
        edge_wb["info"]["run"].base
    lc = run.lcs
    # outer clip: active cells at the cap and at the floor
    c = lc["Clip at floor and cap"]["middle"]
    act = c.admits > 0
    assert (np.isclose(c.yld, base.cap) & act).sum() > 0 and (np.isclose(c.yld, base.floor) & act).sum() > 0
    # inner clip: the response before the shift is above the cap at in-0-hi and below the floor at out-167-hi
    ic = lc["Inner clip"]["middle"]
    raw = base.y0["middle"] + cfg["risk"]["sensitivity_slopes"]["middle"] / 100 * (ic.award - base.a0) / 1000
    i_hi, i_lo = cells.index("in-0-hi"), cells.index("out-167-hi")
    assert raw[i_hi] > base.cap[i_hi] and ic.shift[i_hi] < 0 and ic.yld[i_hi] < base.cap[i_hi]
    assert raw[i_lo] < base.floor[i_lo] and ic.shift[i_lo] > 0 and ic.yld[i_lo] > base.floor[i_lo]
    # unflagged award above tuition, capped
    s = run.scen("Inner clip")
    assert s.award_usd[i_hi] > ic.tuition and not s.full_tuition[i_hi] and ic.award_base[i_hi] == ic.tuition
    assert s.yield_shift_pts_in is not None
    # [v0.6.2, P21-02] an in-state override with a non-zero global shift: the override replaces the global shift
    go = run.scen("Global shift, in-state override")
    gl = lc["Global shift, in-state override"]["middle"]
    ins = (cells.residency == "in") & ~gl.in_segment
    assert go.yield_shift_pts != 0 and go.yield_shift_pts_in not in (None, 0, go.yield_shift_pts)
    assert ins.any() and (gl.shift[ins] == go.yield_shift_pts_in).all()
    assert (gl.shift[cells.residency == "out"] == go.yield_shift_pts).all()
    # need_total override; non-integer goal; flag-only child is not valid
    assert lc["Need override"]["middle"].need_rate != lc["Baseline"]["middle"].need_rate
    g = run.scen("Goal 24.3").segment_goal
    assert g != int(g)
    fo, gp = run.scen("Flag only"), run.scen("Goal 24.3")
    assert (fo.full_tuition != gp.full_tuition).sum() == 1
    assert np.array_equal(fo.award_usd, gp.award_usd) and np.array_equal(fo.admit_rate, gp.admit_rate)
    assert L.incentive(lc["Flag only"]["middle"], lc["Goal 24.3"]["middle"])["incentive_valid"] \
        == labels.INCENTIVE_NOT_VALID
    # a segment pool exactly at the pooling threshold, pooled at the segment level
    import edge
    assert edge.segment_pool_min(cells, cfg) == cfg["pooling_min_admits"]
    assert "segment" in set(base.pool_level)
    # rho below 1; floor_rate with exempt cells; shortfall and above-cap statuses; trimmed rates at the floor
    assert cfg["risk"]["shock_corr_above_below"] == 0.5
    assert cfg["trim"]["floor_rate"] > 0 and cfg["trim"]["exempt_cells"]
    st = {r["status"] for s_ in run.scenarios for r in trim.class_table(cells, cfg, s_, base)["class_table"]}
    assert any(x.startswith("N not reachable") for x in st) and labels.CT_ABOVE_CAP in st and labels.CT_OK in st
    tr = trim.trim_rates(lc["Baseline"]["middle"], 80)
    assert (np.isclose(tr["rates"], cfg["trim"]["floor_rate"]) & (tr["removed_share"] == 1)).any()
    # yield-strip clip count above 0
    assert strip.yield_strip(c)["clip_count"] > 0
    # budget basis merit and both history-reconciliation branches
    assert cfg["budget_basis"] == "merit" and cfg["budget_total"] is not None
    rec = L.history_reconciliation(cells, cfg)
    assert any(h["actual"] is None for h in rec) and any(h["actual"] is not None for h in rec)
    assert run.scen("Goal 24.3").bonus_pool_usd is not None
    # Q-5 example award: flagged zero-award cells and an unflagged award between base-cycle and plan tuition are left
    # out, and leaving them out changes the rounded example award either way
    ea = run.scen("Example award edges")
    le = lc["Example award edges"]["middle"]
    e = le.enrolled
    tb = float(cfg["tuition_base"])
    assert ((ea.award_usd >= tb) & (ea.award_usd < le.tuition) & ~ea.full_tuition & (e > 0)).any()
    assert (ea.full_tuition & (ea.award_usd < tb) & (e > 0)).any()
    got = strip.tuition(le)["example_award"]

    def ex(mask):
        return float(L.xround((e[mask] * ea.award_usd[mask]).sum() / e[mask].sum() / 1000.0) * 1000.0)
    assert ex((ea.award_usd < tb) & (e > 0)) != got                          # flag ignored
    assert ex(~ea.full_tuition & (ea.award_usd < le.tuition) & (e > 0)) != got   # plan-year tuition


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


# ---------------------------------------------------------------------------------------------------------------
# Desktop Excel check guards [v0.6.2, P21-01]: tests/compare_excel_saved.py accepts only a recalculated sentinel build
# of the current build id. A LibreOffice-recalculated sentinel copy stands in for the Excel-saved copy.

def _replace_formula(src, dst, sheet, coord, new_formula):
    """Copy an xlsx, replacing one cell's formula text in the sheet XML and keeping its cached value."""
    import re
    import zipfile
    with zipfile.ZipFile(src) as z:
        wbx = z.read("xl/workbook.xml").decode()
        rels = z.read("xl/_rels/workbook.xml.rels").decode()
        rid = re.search(r'<sheet [^>]*name="%s"[^>]*r:id="([^"]+)"' % sheet, wbx).group(1)
        target = re.search(r'<Relationship [^>]*Id="%s"[^>]*Target="([^"]+)"' % rid, rels) or \
            re.search(r'<Relationship [^>]*Target="([^"]+)"[^>]*Id="%s"' % rid, rels)
        part = "xl/" + target.group(1).lstrip("/").replace("xl/", "", 1)
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as out:
            for item in z.infolist():
                data = z.read(item.filename)
                if item.filename == part:
                    xml = data.decode()
                    pat = re.compile(r'(<c r="%s"[^>]*>(?:(?!</c>).)*?<f[^>]*>)([^<]*)(</f>)' % coord, re.S)
                    xml, n = pat.subn(lambda m: m.group(1) + new_formula + m.group(3), xml)
                    assert n == 1, (part, coord)
                    data = xml.encode()
                out.writestr(item, data)


def _excel_check(path):
    import compare_excel_saved
    return compare_excel_saved.main([path, "--show", "2"])


def test_excel_check_passes_on_a_recalculated_sentinel_copy(sentinel_wb):
    assert _excel_check(sentinel_wb["recalc_path"]) == 0


def test_excel_check_refuses_unrecalculated_or_altered_copies(sentinel_wb, main_wb, tmp_path):
    from sw import lo
    lay = sentinel_wb["info"]["layout"]
    # the tuition formula of the first scenario on Ledger_Middle
    from xlsxwriter.utility import xl_rowcol_to_cell
    coord = xl_rowcol_to_cell(3, lay["lblock"][("middle", "Baseline")]["in_seg"] + 1)
    # (a) the sentinel workbook as built, never opened
    assert _excel_check(sentinel_wb["path"]) != 0
    # (b) resaved by LibreOffice without recalculation
    prof = lo.make_profile(str(tmp_path), recalc=False)
    resave = lo.recalc(sentinel_wb["path"], str(tmp_path / "norecalc"), profile=prof)
    assert _excel_check(resave) != 0
    # (c) that resave with one Ledger formula replaced by =0
    alt = str(tmp_path / "norecalc_zero.xlsx")
    _replace_formula(resave, alt, "Ledger_Middle", coord, "0")
    assert _excel_check(alt) != 0
    # also: the normal (non-sentinel) build, and a recalculated sentinel copy with one formula typed over but its
    # correct value kept (only the formula-text check can see it)
    assert _excel_check(main_wb["path"]) != 0
    alt2 = str(tmp_path / "recalc_zero.xlsx")
    _replace_formula(sentinel_wb["recalc_path"], alt2, "Ledger_Middle", coord, "0")
    assert _excel_check(alt2) == 1


def test_build_id_hashes_the_generator_code(tmp_path):
    """[v0.6.2, P21-03] The build id hashes config, data, scenarios, requirements.lock and sw/*.py; RunLog shows the
    code hash, the uncommitted files and whether the cached values are sentinels. Needs no LibreOffice."""
    import hashlib
    import openpyxl
    from conftest import ROOT
    from sw import build
    h = hashlib.sha256()
    d = os.path.join(ROOT, "sw")
    for name in sorted(f for f in os.listdir(d) if f.endswith(".py")):
        with open(os.path.join(d, name), "rb") as f:
            h.update(name.encode() + b"\0" + f.read() + b"\0")
    path, info = build.build(os.path.join(ROOT, "config", "synthetic.yaml"), "synthetic",
                             os.path.join(ROOT, "config", "scenarios_synthetic.yaml"), str(tmp_path), sentinel=True)
    m = info["run"].meta
    assert m["code_hash"] == h.hexdigest()
    parts = [m["config_hash"], m["data_hash"], m["scenarios_hash"], m["requirements_lock_hash"], m["code_hash"]]
    assert info["build_id"] == hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]
    ws = openpyxl.load_workbook(path)["RunLog"]
    log = {ws.cell(r, 1).value: ws.cell(r, 2).value for r in range(1, ws.max_row + 1)}
    assert log["code hash (sha256 of sw/*.py)"] == m["code_hash"]
    assert log["uncommitted files"] == m["uncommitted_files"] and log["uncommitted files"]
    assert log["cached values"].startswith("sentinel")
