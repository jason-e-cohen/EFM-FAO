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

Integer branches (Phase 3): a reproduce-mode workbook built from the same synthetic world with integer admits and
enrolled and loaded yields and tuition (conftest `repro_syn_wb`, a sentinel build) is compared cell by cell. It reaches
the Excel branches Phase 2 could not (Review_Phase2_Build.md item 8b): IF(in_integer_admits=1, ROUND(...)) in the
admits and admits-at-pool-1 columns, IF(in_integer_enrolled=1, ROUND(...)) in enrolled, and the mode switch's
Reproduce branch for yield and tuition. `test_integer_branches_reached` keeps the rounding visible, and
`test_mode_switch_live_in_a_reproduce_build` sets the switch to Live in a copy and checks the Ledgers follow it.
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
    for sheet in ("Ledger_Low", "Ledger_Middle", "Ledger_High", "Summary", "Distribution"):
        assert count[sheet] > 0, f"no formula cells recorded on {sheet}"
    assert not bad, {k: v[:5] for k, v in bad.items()}


def test_edge_workbook_equals_python(edge_wb):
    count, bad = _compare(edge_wb)
    report = {"workbook": edge_wb["path"], "cells_compared": dict(count),
              "mismatches": {k: v[:20] for k, v in bad.items()}}
    with open(os.path.join(PHASE2, "test03_edge_report.json"), "w") as f:
        json.dump(report, f, indent=1, default=str)
    assert sum(count.values()) > 10_000
    assert count["Distribution"] > 0
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
    # need_total override (R4-07: a fixed departure, the rate unchanged); non-integer goal; flag-only child is not valid
    no, nb = lc["Need override"]["middle"], lc["Baseline"]["middle"]
    assert no.need_rate == nb.need_rate and no.need_lump == run.scen("Need override").need_total - cfg["need"]["total"]
    assert no.need_lump != 0 and nb.need_lump == 0
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


def test_edge_below_workbook_equals_python(edge_below_wb):
    """[R4-09] The edge inputs under unscored_in_median: below, compared cell by cell: the Ledger percentile and median
    signs give unscored -1, and the spread bands count unscored below every bound (mutants RX01, RX02)."""
    count, bad = _compare(edge_below_wb)
    with open(os.path.join(PHASE2, "test03_edge_below_report.json"), "w") as f:
        json.dump({"workbook": edge_below_wb["path"], "cells_compared": dict(count),
                   "mismatches": {k: v[:20] for k, v in bad.items()}}, f, indent=1, default=str)
    assert sum(count.values()) > 10_000
    assert not bad, {k: v[:5] for k, v in bad.items()}


def test_below_and_lowest_band_branches_reached(edge_wb, edge_below_wb):
    """[R4-09, R4-10] Under 'below' unscored enrollees change a percentile probability and a spread band against the
    same inputs under 'excluded'; the 'Lowest band' scenario puts the 25th and 75th percentile bands in the lowest band
    in both workbooks, and the Summary shows its text ('below <next bound>')."""
    from sw import risk
    re_, rb = edge_wb["info"]["run"], edge_below_wb["info"]["run"]
    assert re_.cfg["unscored_in_median"] == "excluded" and rb.cfg["unscored_in_median"] == "below"
    diff_p, diff_band = 0, 0
    for s in rb.scenarios:
        le, lb = re_.lcs[s.name]["middle"], rb.lcs[s.name]["middle"]
        assert (lb.enrolled[~rb.cells.scored] > 0).any()
        for q, t in risk.pct_targets(rb.cfg):
            diff_p += risk.pct(le, q, t)["p_pct_q_t"] != risk.pct(lb, q, t)["p_pct_q_t"]
        for q in risk.SPREAD_QS:
            diff_band += risk.pct_band(le, q) != risk.pct_band(lb, q)
    assert diff_p > 0 and diff_band > 0
    un = [risk.pct_band(r.lcs["Unscored near the 25th"]["middle"], 0.25) for r in (re_, rb)]
    assert un[0] > un[1], un
    lows = sorted(float(b) for b in rb.cfg["score"]["bands"])
    for bundle in (edge_wb, edge_below_wb):
        run = bundle["info"]["run"]
        lc = run.lcs["Lowest band"]["middle"]
        assert risk.pct_band(lc, 0.25) == lows[0] and risk.pct_band(lc, 0.75) == lows[0]
        ws = bundle["values"]["Summary"]
        j = [s.name for s in run.scenarios].index("Lowest band")
        texts = [ws.cell(r, 3 + j).value for r in range(1, ws.max_row + 1)
                 if str(ws.cell(r, 1).value or "").startswith("Spread: ") and "lower bound" not in ws.cell(r, 1).value]
        assert texts == [f"below {lows[1]:g}"] * 2, texts


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


def test_formula_vocabulary(main_wb, repro_syn_wb):
    """Spec section 6: no external references, no volatile or dynamic-array functions, no LET or LAMBDA, no AND or
    OR (comparison arithmetic instead). Live and reproduce builds."""
    _vocabulary(main_wb["path"])
    _vocabulary(repro_syn_wb["path"])


def _vocabulary(path):
    import re
    import openpyxl
    wb = openpyxl.load_workbook(path)          # the file as built (what Excel opens)
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


def _excel_check(path, report):
    """R4-15: tests write the comparison report to a temporary file, never to output/excel_check/."""
    import compare_excel_saved
    return compare_excel_saved.main([path, "--show", "2", "--report", str(report)])


def test_excel_check_passes_on_a_recalculated_sentinel_copy(sentinel_wb, tmp_path):
    rep = tmp_path / "report.json"
    assert _excel_check(sentinel_wb["recalc_path"], rep) == 0
    assert json.load(open(rep))["build_id"] == sentinel_wb["info"]["build_id"]


def test_excel_check_report_path(tmp_path):
    """R4-15: a hand run writes output/excel_check/<build_id>.json (reproduce builds: <build_id>_reproduce.json); the
    tests pass --report."""
    import compare_excel_saved
    from conftest import ROOT
    assert compare_excel_saved.report_path(None, "abc123def456", False) == os.path.join(
        ROOT, "output", "excel_check", "abc123def456.json")
    assert compare_excel_saved.report_path(None, "abc123def456", True).endswith("abc123def456_reproduce.json")
    assert compare_excel_saved.report_path(str(tmp_path / "x.json"), "abc", False) == str(tmp_path / "x.json")


def test_excel_check_refuses_unrecalculated_or_altered_copies(sentinel_wb, main_wb, tmp_path):
    from sw import lo
    lay = sentinel_wb["info"]["layout"]
    # the tuition formula of the first scenario on Ledger_Middle
    from xlsxwriter.utility import xl_rowcol_to_cell
    coord = xl_rowcol_to_cell(3, lay["lblock"][("middle", "Baseline")]["in_seg"] + 1)
    rep = tmp_path / "report.json"
    # (a) the sentinel workbook as built, never opened
    assert _excel_check(sentinel_wb["path"], rep) != 0
    # (b) resaved by LibreOffice without recalculation
    prof = lo.make_profile(str(tmp_path), recalc=False)
    resave = lo.recalc(sentinel_wb["path"], str(tmp_path / "norecalc"), profile=prof)
    assert _excel_check(resave, rep) != 0
    # (c) that resave with one Ledger formula replaced by =0
    alt = str(tmp_path / "norecalc_zero.xlsx")
    _replace_formula(resave, alt, "Ledger_Middle", coord, "0")
    assert _excel_check(alt, rep) != 0
    # also: the normal (non-sentinel) build, and a recalculated sentinel copy with one formula typed over but its
    # correct value kept (only the formula-text check can see it)
    assert _excel_check(main_wb["path"], rep) != 0
    alt2 = str(tmp_path / "recalc_zero.xlsx")
    _replace_formula(sentinel_wb["recalc_path"], alt2, "Ledger_Middle", coord, "0")
    assert _excel_check(alt2, rep) == 1


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


# ---------------------------------------------------------------------------------------------------------------
# Integer branches and the mode switch (Phase 3)

def test_integer_reproduce_workbook_equals_python(repro_syn_wb):
    """The reproduce-mode workbook (integer admits and enrolled, loaded yields and tuition) equals Python on every
    formula cell; it was built with every cached value at -999, so none may survive."""
    wb = repro_syn_wb["values"]
    expected = repro_syn_wb["info"]["expected"]
    left = [(sh, r, c) for (sh, r, c) in expected if wb[sh].cell(r + 1, c + 1).value in (-999, "-999")]
    count, bad = _compare(repro_syn_wb)
    with open(os.path.join(os.path.dirname(repro_syn_wb["path"]), "test03_integer_report.json"), "w") as f:
        json.dump({"workbook": repro_syn_wb["path"], "cells_compared": dict(count),
                   "mismatches": {k: v[:20] for k, v in bad.items()}, "sentinels_left": len(left)}, f, indent=1,
                  default=str)
    assert sum(count.values()) > 10_000
    assert not left, left[:10]
    assert not bad, {k: v[:5] for k, v in bad.items()}
    assert "Reproduce" in wb.sheetnames and "Trim" not in wb.sheetnames
    assert "CT_CLASS_TABLE" not in repro_syn_wb["info"]["names"]
    assert count["Distribution"] > 0 and "STEP_SIZES" in repro_syn_wb["info"]["names"]


def test_integer_branches_reached(repro_syn_wb):
    """The comparison above covers the integer branches: some cell's applications (rounded after the pool multiplier,
    reproduce.round_apps_after_pool), admits and admits at pool multiplier 1 are changed by rounding, enrolled in
    every scenario, and the Ledger formulas carry both branches."""
    import numpy as np
    from dataclasses import replace
    from sw import ledger as L
    info = repro_syn_wb["info"]
    run = info["run"]
    assert run.cfg["integer_admits"] and run.cfg["integer_enrolled"] and run.cfg["mode"] == "reproduce"
    assert run.cfg["reproduce"]["round_apps_after_pool"]
    changed = {"admits": 0, "admits_pool1": 0, "apps": 0}
    j = run.cells.col(run.cfg["cycle"]["base_cycle"])
    for s in run.scenarios:
        lc = run.lcs[s.name]["middle"]
        apps_raw = run.cells.apps[:, j] * np.where(lc.upper, s.pool_multiplier, 1.0) * \
            (1.0 + s.segment_pool_lift_pct / 100.0 * lc.in_segment)
        assert np.array_equal(lc.apps, L.xround(apps_raw))
        changed["apps"] += int((lc.apps != apps_raw).sum())
        raw = lc.apps * lc.rate
        assert np.array_equal(lc.admits, L.xround(raw))
        changed["admits"] += int((lc.admits != raw).sum())
        # enrolled rounding changes some cell in every scenario
        assert (lc.enrolled != lc.mu).any() and np.array_equal(lc.enrolled, L.xround(lc.mu))
        lc1 = L.evaluate(run.cells, run.cfg, replace(s, pool_multiplier=1.0), run.base, "middle")
        changed["admits_pool1"] += int((lc1.admits != lc1.apps * lc1.rate).sum())
        assert np.array_equal(lc.yld, s.yield_loaded) and lc.tuition == s.tuition_loaded_usd
    # Baseline's rates are admits / applications, so rounding leaves its admits; the children's do not
    assert changed["admits"] > 0 and changed["admits_pool1"] > 0 and changed["apps"] > 0, changed
    lay = info["layout"]
    ws = repro_syn_wb["formulas"]["Ledger_Middle"]
    blk = lay["lblock"][("middle", run.scenarios[0].name)]
    r = lay["r0l"] + 1
    for key, needle in (("admits", "IF(in_integer_admits=1,ROUND("), ("enrolled", "IF(in_integer_enrolled=1,ROUND("),
                        ("admits_pool1", "IF(in_integer_admits=1,ROUND("), ("yield", 'IF(in_mode="Reproduce",'),
                        ("apps", 'IF((in_mode="Reproduce")*(in_round_apps_after_pool=1)=1,ROUND('),
                        ("admits_pool1", 'IF((in_mode="Reproduce")*(in_round_apps_after_pool=1)=1,ROUND(')):
        f = ws.cell(r, blk[key] + 1).value
        assert isinstance(f, str) and needle in f, (key, f)
    assert 'IF(in_mode="Reproduce",' in ws.cell(lay["ledger_head_rows"]["T"] + 1, blk["in_seg"] + 2).value


def test_mode_switch_live_in_a_reproduce_build(repro_syn_wb, lo_profile, tmp_path):
    """Set the Inputs mode to Live in a copy of the reproduce build: after recalculation every Ledger's yield, tuition,
    applications (not rounded in Live), admits and enrolled equal the live ledger (response yields, tuition formula)
    with integer counts."""
    import openpyxl
    from sw import config, ledger as L, lo
    from conftest import close
    info = repro_syn_wb["info"]
    run = info["run"]
    sheet, r0, c0 = info["names"]["in_mode"][:3]
    # the file as built (full-precision inputs; a LibreOffice-saved copy may round stored input values)
    wb = openpyxl.load_workbook(repro_syn_wb["path"])
    assert wb[sheet].cell(r0 + 1, c0 + 1).value == "Reproduce"
    wb[sheet].cell(r0 + 1, c0 + 1).value = "Live"
    src = str(tmp_path / "live_switch.xlsx")
    wb.save(src)
    vals = openpyxl.load_workbook(lo.recalc(src, str(tmp_path / "recalc"), profile=lo_profile), data_only=True)
    cfg_live_int = config.validate({k: v for k, v in run.cfg.items() if not k.startswith("_")} | {"mode": "live"})
    lay = info["layout"]
    bad = []
    for k in ("low", "middle", "high"):
        ws = vals[lay["case_sheet"][k]]
        for s in run.scenarios:
            lc = L.evaluate(run.cells, cfg_live_int, s, run.base, k)
            blk = lay["lblock"][(k, s.name)]
            if not close(ws.cell(lay["ledger_head_rows"]["T"] + 1, blk["in_seg"] + 2).value, lc.tuition):
                bad.append((k, s.name, "tuition"))
            for i in range(run.cells.n):
                r = lay["r0l"] + i + 1
                for key, arr in (("yield", lc.yld), ("apps", lc.apps), ("admits", lc.admits),
                                 ("enrolled", lc.enrolled)):
                    if not close(ws.cell(r, blk[key] + 1).value, float(arr[i])):
                        bad.append((k, s.name, key, run.cells.cell_id[i]))
    assert not bad, bad[:10]
    # the live yields differ from the loaded ones somewhere, so the switch is visible
    lcm = L.evaluate(run.cells, cfg_live_int, run.scenarios[0], run.base, "middle")
    assert (lcm.yld != run.scenarios[0].yield_loaded).any()


def test_history_509_block_reached(repro_syn_wb):
    """R3-4: the History 509 reconciliation block (report only) is covered by the comparison above: the synthetic 509
    figures give an agreeing cohort, a differing cohort and one with no figures, and each cohort's Checks row reports
    without asserting."""
    from sw import labels
    run = repro_syn_wb["info"]["run"]
    from sw import contract as K
    rec = K.compute(run)["aba509_reconciliation"]
    verdicts = [{r["verdict"] for r in h["rows"]} for h in rec]
    assert labels.ABA509_AGREES in verdicts[0] and labels.ABA509_DIFFERS in verdicts[1]
    assert verdicts[2] == {labels.ABA509_NOT_GIVEN}
    summaries = [h["summary"] for h in rec]
    assert summaries[0] == labels.ABA509_ALL_AGREE and summaries[1].startswith("report only:")
    assert summaries[2].startswith("not run")
    ws = repro_syn_wb["values"]["Checks"]
    texts = [ws.cell(r, 3).value for r in range(1, ws.max_row + 1)]
    for sm in summaries:
        assert sm in texts


def test_phase22_coverage(main_wb, edge_wb):
    """[v0.6.3] The main and edge workbooks cover at least three percentile targets, one with fewer than 20 expected
    below t (the 'approximate' label); the edge config adds all_jd, above_floor and a tuition_by_year_usd year, and its
    growth to date has no as-of date."""
    from sw import labels, risk
    for bundle in (main_wb, edge_wb):
        run = bundle["info"]["run"]
        targets = risk.pct_targets(run.cfg)
        assert len(targets) >= 3 and {q for q, _ in targets} - {0.5}
        lc = run.lcs[run.scenarios[0].name]["middle"]
        flags = [risk.pct(lc, q, t)["approximate"] for q, t in targets]
        assert labels.PCT_APPROX_LABEL in flags and "" in flags
    cfg = edge_wb["info"]["run"].cfg
    assert cfg["ntr_goal_basis"] == "all_jd" and cfg["continuing_ntr_usd"] > 0
    assert cfg["trim"]["protect_segment"] == "above_floor"
    assert cfg["tuition_by_year_usd"] and cfg["cycle"]["plan_cycle"] in cfg["tuition_by_year_usd"]
    assert cfg["pool_ytd_growth"] is not None and cfg["pool_ytd_as_of"] is None
    base = edge_wb["info"]["run"].scenarios[0]
    assert edge_wb["info"]["run"].lcs[base.name]["middle"].tuition == cfg["tuition_by_year_usd"][2027]
    d = edge_wb["info"]["vals"]["sk"][(base.name, "middle")]
    assert d["p_jd_ntr_ge_goal"] is not None and d["jd_ntr"] is not None


def test_distribution_branches_reached(main_wb, edge_wb, repro_syn_wb):
    """[Phase 4] The Distribution formulas compared above take each branch: positions wholly inside, wholly outside and
    straddling the top quartile; positions with no enrolled (the fraction's zero branch); an unscored position; a
    scenario with merit of zero (edge "No merit awards"); full-tuition and no-merit-award counts above zero; non-zero
    step sizes of both signs across the three workbooks; integer enrolled (reproduce build)."""
    from sw import ledger as L
    fr, zero_e, unscored, zero_merit, ft, nm, steps = set(), 0, 0, 0, 0, 0, []
    for bundle in (main_wb, edge_wb, repro_syn_wb):
        run = bundle["info"]["run"]
        for s in run.scenarios:
            for lc in run.lcs[s.name].values():
                q = L.top_quartile_merit(lc)
                for p in q["positions"]:
                    fr.add("in" if p["fraction"] == 1 else "out" if p["fraction"] == 0 else "straddle")
                    zero_e += p["enrolled"] <= 0
                    unscored += p["score_lo"] is None and p["enrolled"] > 0
                zero_merit += q["merit"] == 0
                k = L.kpis(lc)
                ft += k["full_tuition_n"] > 0
                nm += k["no_merit_award_n"] > 0
            steps += [st["step_usd"] for st in L.awards(run.lcs[s.name]["middle"])["step_sizes"]]
    assert fr == {"in", "out", "straddle"}
    assert zero_e and unscored and zero_merit and ft and nm
    assert min(steps) < 0 < max(steps)
    nb = edge_wb["info"]["run"].lcs["No merit awards"]["middle"]
    assert L.money(nb)["merit"] == 0 and L.kpis(nb)["top_quartile_merit_share"] == 0
