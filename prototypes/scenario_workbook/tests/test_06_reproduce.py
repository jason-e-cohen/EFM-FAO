"""Test 6: reproduce mode (spec section 9; Phase 3).

Synthetic part (always runs; no fixture, no LibreOffice): the ledger takes loaded yields and tuition in reproduce
mode and only there; integer counts; applications rounded after the pool multiplier in reproduce mode only; the
loader's rules (labels, narrative figures, pool, lineage, need, counting rule, recovery of unknown applications) on
values written here; the comparison logic, including the exclusion of non-reproducible cells, on a fixture-shaped dict
built from a synthetic run. Strings here are our own; none comes from the fixture.

Fixture part (skips without YA_FIXTURE_PATH): the loader reads the layout; the counting rule is detected and matches
the setting (reproduce.unscored_in_median: excluded, DECISIONS Nov 18); unknown applications are blank on History and
each cell that depends on them is recovered or counted as not reproducible; the loaded values reach the Ledgers; the
tuition formula at 6.0% reproduces the fixture's tuition; the fixture's own enrolled follow the ledger's rounding rule;
its summary rows agree with its panels; the reproduce workbook equals Python cell by cell after recalculation
(LibreOffice); and `test_pass_criterion`, one test per scenario and section 9 criterion (Scenario 4 first), compares
the reproduce ledger with the file.
Every value compared is read from the fixture at run time; nothing is typed in. A failing `test_pass_criterion` is a
reported mismatch: its message carries the likeliest cause, and output/phase3/reproduce_report.json has the detail.
"""
import copy
import json
import os

import numpy as np
import pytest
import yaml

from conftest import PHASE3, ROOT, repro_synthetic
from sw import CASES, labels
from sw import ledger as L
from sw import reproduce as R
from sw.config import ConfigError, scenario_tuition, validate


# ---------------------------------------------------------------------------------------------------------------
# Synthetic part

@pytest.fixture(scope="module")
def syn():
    cfg_live, cfg, cells, scen, loaded = repro_synthetic()
    from sw import build
    run = build.make_run(cfg, cells, scen, {"build_id": "test"}, loaded=loaded)
    return {"cfg_live": cfg_live, "cfg": cfg, "cells": cells, "scen": scen, "loaded": loaded, "run": run}


def test_ledger_takes_loaded_values_in_reproduce_mode_only(syn):
    """Reproduce: yield is the loaded value in every case, as entered (no shift, floor or cap); tuition is the loaded
    tuition. Live mode with the same scenario objects: the response and the formula."""
    from sw import response
    cfg, cells, run = syn["cfg"], syn["cells"], syn["run"]
    s = copy.copy(run.scenarios[1])
    y = s.yield_loaded.copy()
    y[0] = 0.95                                     # above every yield cap
    s.yield_loaded = y
    s.tuition_loaded_usd = 12_345.0                 # not a formula value
    s.yield_shift_pts = 2.0
    for k in CASES:
        lc = L.evaluate(cells, cfg, s, run.base, k)
        assert np.array_equal(lc.yld, y) and lc.tuition == 12_345.0
        assert np.array_equal(lc.mu, lc.admits * y)
    live = validate({k: v for k, v in cfg.items() if not k.startswith("_")} | {"mode": "live"})
    lc = L.evaluate(cells, live, s, run.base, "middle")
    assert lc.tuition == scenario_tuition(live, s.tuition_increase_pct)
    exp = np.clip(response.yield_at(run.base, lc.award, "middle") + lc.shift / 100, run.base.floor, run.base.cap)
    assert np.array_equal(lc.yld, exp) and not np.array_equal(lc.yld, y)


def test_reproduce_needs_loaded_values(syn):
    s = copy.copy(syn["run"].scenarios[0])
    s.yield_loaded = None
    with pytest.raises(ConfigError):
        L.evaluate(syn["cells"], syn["cfg"], s, syn["run"].base, "middle")
    s = copy.copy(syn["run"].scenarios[0])
    s.tuition_loaded_usd = None
    with pytest.raises(ConfigError):
        L.evaluate(syn["cells"], syn["cfg"], s, syn["run"].base, "middle")


def test_integer_counts_belong_to_reproduce_mode(syn):
    """A live build refuses integer admits or enrolled (the Trim sheet does not settle them); a reproduce build
    rounds both, half up."""
    from sw import build
    for key in ("integer_admits", "integer_enrolled"):
        live = validate({k: v for k, v in syn["cfg_live"].items() if not k.startswith("_")} | {key: True})
        with pytest.raises(ConfigError):
            build.make_run(live, syn["cells"], syn["scen"])
    with pytest.raises(ConfigError):                 # reproduce without loaded values
        build.make_run(syn["cfg"], syn["cells"], syn["scen"], loaded={})
    for s in syn["run"].scenarios:
        lc = syn["run"].lcs[s.name]["middle"]
        assert np.array_equal(lc.admits, np.floor(lc.apps * lc.rate + 0.5))
        assert np.array_equal(lc.enrolled, np.floor(lc.admits * lc.yld + 0.5))


def test_applications_rounded_after_pool_in_reproduce_mode_only(syn):
    """DECISIONS Nov 18: with reproduce.round_apps_after_pool, applications are whole numbers after the pool multiplier
    in reproduce mode; with the setting off, or in live mode, they are not rounded (spec section 3)."""
    cfg, cells, run = syn["cfg"], syn["cells"], syn["run"]
    s = copy.copy(run.scenarios[1])
    s.pool_multiplier = 1.37                       # makes fractional applications
    j = cells.col(cfg["cycle"]["base_cycle"])
    lc = L.evaluate(cells, cfg, s, run.base, "middle")
    raw = cells.apps[:, j] * np.where(lc.upper, 1.37, 1.0) * (1 + s.segment_pool_lift_pct / 100 * lc.in_segment)
    assert (raw != np.round(raw)).any()
    assert np.array_equal(lc.apps, L.xround(raw)) and np.array_equal(lc.admits, L.xround(lc.apps * lc.rate))
    raw_cfg = {k: v for k, v in cfg.items() if not k.startswith("_")}
    off = validate(raw_cfg | {"reproduce": {"round_apps_after_pool": False}})
    assert np.array_equal(L.evaluate(cells, off, s, run.base, "middle").apps, raw)
    live = validate(raw_cfg | {"mode": "live"})
    assert np.array_equal(L.evaluate(cells, live, s, run.base, "middle").apps, raw)
    from sw.config import round_apps_after_pool
    assert round_apps_after_pool(cfg) and not round_apps_after_pool(off) and not round_apps_after_pool(live)
    with pytest.raises(ConfigError):
        validate(raw_cfg | {"reproduce": {"round_apps_after_pool": "yes"}})
    with pytest.raises(ConfigError):
        validate(raw_cfg | {"reproduce": {"unknown_key": 1}})


def test_unknown_applications_recovered_only_when_one_value_fits(syn):
    """DECISIONS Nov 18: unknown base-cycle applications are recovered from the scenario columns only when exactly one
    whole number fits every scenario's admits; otherwise the cell is not reproducible from the file, with the reason."""
    cfg, cells0 = syn["cfg"], syn["cells"]
    j = cells0.col(cfg["cycle"]["base_cycle"])
    cid = cells0.cell_id[0]
    n = cells0.n

    def case(rates, admits):
        cells = copy.deepcopy(cells0)
        cells.meta = {}
        cells.apps[0, j] = 0.0
        specs, scen = [], []
        for k, (r, a) in enumerate(zip(rates, admits)):
            ra, ad = np.zeros(n), np.zeros(n)
            ra[0], ad[0] = r, a
            specs.append({"name": f"S{k}", "admit_rate": ra, "pool_multiplier": 1.0})
            scen.append({"name": f"S{k}", "admits": ad})
        fx = {"apps_unknown": [(cid, cfg["cycle"]["base_cycle"])], "scenarios": scen}
        R.recover_apps(cells, cfg, fx, specs)
        return cells
    c = case([1.0, 0.5], [37.0, 19.0])             # only 37 fits both
    assert c.apps[0, j] == 37.0 and c.meta["apps_recovered"][0, j] and not c.meta["apps_unknown"][0, j]
    assert c.meta["not_reproducible"] == []
    c = case([0.5], [19.0])                         # 37 and 38 both give 19
    assert c.apps[0, j] == 0.0 and c.meta["apps_unknown"][0, j]
    assert c.meta["not_reproducible"][0]["cell"] == cid
    assert c.meta["not_reproducible"][0]["reason"].startswith(R.NOT_REPRODUCIBLE) and "2 values" in \
        c.meta["not_reproducible"][0]["reason"]
    c = case([1.0, 1.0], [37.0, 40.0])             # no value fits both
    assert "different applications" in c.meta["not_reproducible"][0]["reason"]
    c = case([0.5], [0.0])                          # no scenario admits anyone: nothing to recover
    assert c.meta["not_reproducible"] == [] and c.meta["apps_unknown"][0, j]


def test_compare_excludes_non_reproducible_cells(syn):
    """A cell marked not reproducible is taken out of both sides: a file that differs only there passes, and the
    criterion rows count the excluded cells."""
    run = syn["run"]
    fx = _fake_fx(run)
    sd = fx["scenarios"][1]
    i = int(np.argmax(sd["enrolled"]))
    sd["enrolled"][i] += 3
    assert any(r["pass"] is False for r in R.compare(run, fx) if r["scenario"] == sd["name"])
    saved = dict(run.cells.meta)
    try:
        run.cells.meta["not_reproducible"] = [{"cell": run.cells.cell_id[i], "reason": R.NOT_REPRODUCIBLE}]
        rows = R.compare(run, fx)
        assert all(r["pass"] is not False for r in rows), [r for r in rows if r["pass"] is False][:3]
        assert all(r["excluded_cells"] == 1 for r in rows)
    finally:
        run.cells.meta.clear()
        run.cells.meta.update(saved)


def test_cell_causes_name_the_application_rule(syn):
    """A file whose admits follow the other application rule (applications not rounded after the pool multiplier)
    in some cell: cell_causes names that rule, not an unexplained difference."""
    run, cells, cfg = syn["run"], syn["cells"], syn["cfg"]
    j = cells.col(cfg["cycle"]["base_cycle"])
    fx = _fake_fx(run)
    hits = 0
    for sd, s in zip(fx["scenarios"], run.scenarios):
        lc = run.lcs[s.name]["middle"]
        raw = cells.apps[:, j] * np.where(lc.upper, s.pool_multiplier, 1.0) * \
            (1 + s.segment_pool_lift_pct / 100 * lc.in_segment)
        other = L.xround(raw * s.admit_rate)
        diff = other != lc.admits
        if not diff.any():
            continue
        sd["admits"] = np.where(diff, other, sd["admits"])
        causes = R.cell_causes(run, fx, s.name)
        flagged = [c for c in causes if c["admits"] != c["fixture_admits"]]
        assert len(flagged) == int(diff.sum())
        assert all("round_apps_after_pool false" in c["cause"] for c in flagged), flagged[:2]
        hits += 1
    assert hits, "no synthetic scenario where the application rule changes admits"


def test_checks_count_admits_above_applications(syn, tmp_path):
    """Integer admits on unrounded applications (reproduce mode with round_apps_after_pool off) can exceed the
    applications; the Checks integrity row then expects the ledger's count, not "OK". Python expectations only (test 3
    compares them with the recalculated workbook)."""
    from sw import build, workbook
    cfg, cells, run = syn["cfg"], syn["cells"], syn["run"]
    raw = {k: v for k, v in cfg.items() if not k.startswith("_")}
    off = validate(raw | {"reproduce": {"round_apps_after_pool": False}})
    scen = []
    for s0 in run.scenarios:
        s1 = copy.copy(s0)
        if s1.parent is not None:
            s1.pool_multiplier = 1.37                  # fractional applications
        scen.append(s1)
    r2 = build.make_run(off, cells, scen, {"build_id": "0000000000ab"}, loaded=syn["loaded"])
    n = sum(int((r2.lcs[s.name]["middle"].admits > r2.lcs[s.name]["middle"].apps + 1e-9).sum()) for s in scen)
    assert n > 0
    info = workbook.write(r2, str(tmp_path / "wb.xlsx"))
    vals = [v for (sh, r, c), v in info["expected"].items() if sh == "Checks" and isinstance(v, str)
            and v.endswith("cells with admits above applications")]
    assert f"{n} cells with admits above applications" in vals, vals


def test_acceptance_order_puts_scenario_4_first():
    assert R.acceptance_order(["Baseline", "Scenario 1", "Scenario 4", "Scenario 2"]) == \
        ["Scenario 4", "Baseline", "Scenario 1", "Scenario 2"]


def test_scenario_file_cannot_set_loaded_values(syn):
    from sw import build
    spec = [{"name": "Baseline"}, {"name": "Child", "parent": "Baseline", "yield_loaded": [0.1]}]
    with pytest.raises(ConfigError):
        build.scenarios_from_specs(spec, syn["cells"], syn["cfg_live"])


def test_parse_label():
    cfg = {"score": {"bands": [170, 167, 166, 165, 161, 158, 154, 152, 0]}, "gpa": {"hi_at_or_above": 3.83}}
    assert R.parse_label("170+, 3.83+", cfg) == (170.0, "hi")
    assert R.parse_label("167-169, 3.0-3.82", cfg) == (167.0, "lo")
    assert R.parse_label("166, <3.0", cfg) == (166.0, "lo")
    assert R.parse_label("154-164, <3.83", cfg) == (154.0, "lo")
    assert R.parse_label("<152, 3.83+", cfg) == (0.0, "hi")
    assert R.parse_label("<154, blank GPA", cfg) == (0.0, "blank")
    lo, g = R.parse_label("Other test, 3.9+", cfg)
    assert np.isnan(lo) and g == "hi"
    lo, g = R.parse_label("no score, blank GPA", cfg)
    assert np.isnan(lo) and g == "blank"
    with pytest.raises(R.FixtureError):
        R.parse_label("163, 3.83+", cfg)            # not a configured band
    with pytest.raises(R.FixtureError):
        R.parse_label("170+", cfg)


def test_parse_narrative():
    t = ("Projected: the class is 120. Medians are 160 (3-person margin) and 3.5 (-2-person margin). There are 4 "
         "enrolled <150. The full-tuition count is 7 and full-pay count is 9.")
    p = R.parse_narrative(t, {})
    assert p["class"] == 120 and p["median_score"] == (160, 3) and p["median_gpa"] == (3.5, -2)
    assert p["below"] == (150, 4) and p["full_tuition"] == 7 and p["no_merit_award"] == 9
    assert R.parse_narrative("nothing stated", {}) == {}


def test_pool_lineage_and_need_rules():
    cfg = {"score": {"pool_threshold": 160}, "need": {"total": 70_000, "reference_class": 70}}
    assert R._pool("grow the pool +25% 160+ only", cfg) == 1.25
    assert R._pool("grow the pool +25% 165+ only", cfg) is None       # another threshold
    assert R._pool("flat pool", cfg) is None
    # need rule: whole-dollar rate (1,000) x class; a departure is a change in need_total
    sd = {"summary": {"money": {"need": 1000 * 64}, "class": 64}}
    assert R._need_total(cfg, sd)[0] == 70_000
    sd = {"summary": {"money": {"need": 1000 * 64 - 5_000}, "class": 64}}
    assert R._need_total(cfg, sd)[0] == 65_000
    assert R._need_total(cfg, {"summary": None})[0] == 70_000
    fx = {"scenarios": [
        {"name": "Baseline", "tuition": 1.0, "admit_rate": 0, "award_usd": 0, "yield": 0, "summary": None},
        {"name": "Scenario 1", "tuition": 1.0, "admit_rate": 0, "award_usd": 0, "yield": 0,
         "summary": {"description": "From Baseline, +20% 160+ pool", "money": {}}},
        {"name": "Scenario 2", "tuition": 1.0, "admit_rate": 0, "award_usd": 0, "yield": 0,
         "summary": {"description": "As Scenario 1 with the same pool", "money": {}}},
        {"name": "Scenario 3", "tuition": 1.0, "admit_rate": 0, "award_usd": 0, "yield": 0,
         "summary": {"description": "Back to Scenario 1, pool +30% 160+", "money": {}}},
        {"name": "Scenario 4", "tuition": 1.0, "admit_rate": 0, "award_usd": 0, "yield": 0,
         "summary": {"description": "names no scenario", "money": {}}}]}
    sp = R.loaded_specs(fx, cfg)
    assert [s["parent"] for s in sp] == [None, "Baseline", "Scenario 1", "Scenario 1", "Scenario 3"]
    assert [s["pool_multiplier"] for s in sp] == [1.0, 1.2, 1.2, 1.3, 1.3]


def test_counting_rule_detection():
    def grp(at, below, others, total):
        return {"at": at, "below": below, "others": others, "total": total}
    exc = {"groups": {160.0: grp(30, 28, {"other test": 2}, 60)}}
    bel = {"groups": {160.0: grp(30, 30, {"other test": 2}, 60)}}
    none = {"groups": {160.0: grp(30, 30, {}, 60)}}
    assert R.detect_counting_rule([exc])["rule"] == "excluded"
    assert R.detect_counting_rule([bel])["rule"] == "below"
    assert R.detect_counting_rule([exc, bel])["rule"] == "mixed"
    assert R.detect_counting_rule([none])["rule"] == "undetermined"


def _fake_fx(run):
    """A fixture-shaped dict from a synthetic reproduce run: panel figures equal to the ledger's."""
    scen = []
    for s in run.scenarios:
        lc = run.lcs[s.name]["middle"]
        scen.append({"name": s.name, "tuition": lc.tuition, "admit_rate": s.admit_rate.copy(),
                     "award_usd": lc.award.copy(), "yield": lc.yld.copy(), "admits": lc.admits.copy(),
                     "enrolled": lc.enrolled.copy(), "summary": None})
    return {"scenarios": scen}


def test_compare_passes_equal_figures_and_reports_differences(syn):
    run = syn["run"]
    fx = _fake_fx(run)
    rows = R.compare(run, fx)
    assert all(r["pass"] is True for r in rows if r["file"] is not None)
    assert {r["criterion"] for r in rows if r["pass"] is None} == {"ntr", "margin_score", "margin_gpa"}
    # one more enrolled in one cell: class and merit fail, with a cause
    fx = _fake_fx(run)
    sd = fx["scenarios"][1]
    i = int(np.argmax(sd["award_usd"] * (sd["enrolled"] > 0)))
    sd["enrolled"][i] += 1
    bad = {r["criterion"]: r for r in R.compare(run, fx) if r["scenario"] == sd["name"] and r["pass"] is False}
    assert {"class", "merit"} <= set(bad) and all(r["cause"] for r in bad.values())


def test_compare_summary_path_tolerance_and_counting_cause(syn):
    """Summary-sheet figures: NTR passes within $100 and fails beyond; a margin that equals the ledger's counts under
    the other counting rule is attributed to the counting rule."""
    run = syn["run"]
    cfg = run.cfg
    # a scenario with blank-GPA enrollees, so the two counting rules give different GPA margins
    blank = run.cells.gpa_class == "blank"
    hits = [x for x in run.scenarios if run.lcs[x.name]["middle"].enrolled[blank].sum() > 0]
    assert hits, "the synthetic world needs blank-GPA enrollees for this test"
    s = hits[0]
    k_s = [x.name for x in run.scenarios].index(s.name)
    lc = run.lcs[s.name]["middle"]
    ours = R.our_figures(run, s.name)
    t = float(cfg["score"]["median_thresholds"][0])
    alt = R._alt_margins(lc, t)
    other = "excluded" if cfg["unscored_in_median"] == "below" else "below"
    fx = _fake_fx(run)
    groups = {float(tt): {"at": ours[("at_or_above_score", float(tt))], "below": 0.0, "others": {}, "total": 0.0}
              for tt in L.score_thresholds(cfg)}
    groups[float(cfg["score"]["floor"])]["below"] = ours["below_floor"]
    groups[float(cfg["gpa"]["hi_at_or_above"])] = {"at": ours["gpa_hi"], "below": 0.0, "others": {}, "total": 0.0}
    for ntr_gap, ok in ((99.0, True), (101.0, False)):
        fx["scenarios"][k_s]["summary"] = {
            "class": ours["class"], "money": {"merit": ours["merit"], "ntr": ours["ntr"] + ntr_gap}, "groups": groups,
            "parsed": {"full_tuition": ours["full_tuition"], "no_merit_award": ours["no_merit_award"],
                       "median_score": (t, ours["margin_score"]), "median_gpa": (3.5, alt["gpa"][other])}}
        rows = {r["criterion"]: r for r in R.compare(run, fx) if r["scenario"] == s.name}
        assert rows["ntr"]["pass"] is ok
        assert rows["class"]["pass"] and rows["merit"]["pass"] and rows["margin_score"]["pass"]
    assert alt["gpa"][other] != ours["margin_gpa"]
    assert rows["margin_gpa"]["pass"] is False
    assert "matches the ledger's counts under unscored_in_median" in rows["margin_gpa"]["cause"]


# ---------------------------------------------------------------------------------------------------------------
# Fixture part (skips without YA_FIXTURE_PATH)

@pytest.fixture(scope="module")
def fxr(ya_path):
    """Load the fixture, build the ledger run (no workbook) and write the report to output/phase3/."""
    res = R.run_fixture(ya_path, os.path.join(PHASE3, "fixture_python"), write=False)
    R.write_report(res["report"], os.path.join(ROOT, "output"))
    return res


@pytest.fixture(scope="module")
def fx_wb(ya_path, lo_profile):
    """The reproduce workbook from the fixture, built as a sentinel copy and recalculated."""
    import shutil
    import openpyxl
    from sw import lo
    out = os.path.join(PHASE3, "fixture_workbook")
    shutil.rmtree(out, ignore_errors=True)
    res = R.run_fixture(ya_path, out, sentinel=True)
    rc = lo.recalc(res["path"], os.path.join(out, "recalculated"), profile=lo_profile)
    res["values"] = openpyxl.load_workbook(rc, data_only=True)
    return res


def test_normal_and_sentinel_builds_keep_both_files(ya_path, fx_wb):
    """A fixture build after the sentinel build (same build id) writes workbook_reproduce.xlsx beside
    workbook_reproduce_sentinel.xlsx; neither overwrites the other, and each RunLog says which it is."""
    import openpyxl
    res = R.run_fixture(ya_path, os.path.join(PHASE3, "fixture_workbook"))
    sent, norm = fx_wb["path"], res["path"]
    assert os.path.basename(sent) == "workbook_reproduce_sentinel.xlsx"
    assert os.path.basename(norm) == "workbook_reproduce.xlsx"
    assert os.path.dirname(sent) == os.path.dirname(norm)
    for p, want in ((sent, "sentinel"), (norm, "Python values")):
        assert os.path.isfile(p)
        log = {r[0]: r[1] for r in openpyxl.load_workbook(p, read_only=True)["RunLog"].iter_rows(values_only=True)
               if r and r[0]}
        assert str(log["cached values"]).startswith(want), (p, log["cached values"])


def test_fixture_layout_and_loader(fxr):
    fx, cfg, run = fxr["fx"], fxr["cfg"], fxr["run"]
    assert fx["cohorts"] == list(cfg["cycle"]["history"])
    assert run.scenarios[0].parent is None and len(run.scenarios) >= 2
    assert all(run.parents[s.name] is not None for s in run.scenarios[1:])
    assert run.cells.n == fx["n_cells"] and set(run.cells.cell_id) == set(fx["cell_ids"])
    assert (run.cells.segment == "").all()                       # residency only in the file
    assert not any("not within 1e-6" in n for n in fx["notes"])
    j = run.cells.col(cfg["cycle"]["base_cycle"])
    rec = run.cells.apps[:, j] > 0
    assert np.array_equal(run.cells.apps[rec, j], np.round(run.cells.apps[rec, j]))   # whole applications
    for k, sd in enumerate(fx["scenarios"]):
        assert sd["tuition"]
        if k > 0:                                  # every child has a summary block with a class count
            assert sd["summary"] and sd["summary"]["class"] is not None, sd["name"]


def test_counting_rule_confirmed_and_reported(fxr):
    """Reproduce mode uses the config's reproduce.unscored_in_median (DECISIONS Nov 18: excluded, the fixture's rule
    and the ABA 509 basis). The rule detected from the fixture's count rows matches the setting and is reported in
    output/phase3/reproduce_report.json."""
    rep = fxr["report"]
    with open(os.path.join(ROOT, "config", "richmond.yaml")) as f:
        assert fxr["cfg"]["unscored_in_median"] == yaml.safe_load(f)["reproduce"]["unscored_in_median"]
    assert rep["counting_rule"]["groups_with_unscored_or_blank"] > 0
    assert rep["counting_rule"]["rule"] == fxr["cfg"]["unscored_in_median"], rep["counting_rule"]
    with open(os.path.join(ROOT, "output", "phase3", "reproduce_report.json")) as f:
        on_disk = json.load(f)
    assert on_disk["counting_rule"]["rule"] == rep["counting_rule"]["rule"]
    assert on_disk["counting_rule_matches_setting"] is True


def test_unknown_applications_recovered_or_counted(fxr):
    """DECISIONS Nov 18: every cell whose base-cycle applications are unknown and that some scenario admits students
    to is either recovered (one value fits every scenario) or listed as not reproducible from the file, with a reason;
    the report counts them and every criterion row carries the count of excluded cells."""
    run, fx, rep = fxr["run"], fxr["fx"], fxr["report"]
    cells = run.cells
    j = cells.col(fxr["cfg"]["cycle"]["base_cycle"])
    unk, recd = cells.meta["apps_unknown"], cells.meta["apps_recovered"]
    assert unk.sum() + recd.sum() == len(fx["apps_unknown"])
    nonrep = {d["cell"] for d in cells.meta["not_reproducible"]}
    for i in range(cells.n):
        admitted = any(sd["admits"][i] > 0 for sd in fx["scenarios"])
        if unk[i, j] and admitted:
            assert cells.cell_id[i] in nonrep
        if cells.cell_id[i] in nonrep:
            assert unk[i, j] and admitted
    assert rep["not_reproducible_count"] == len(nonrep)
    assert all(d["reason"].startswith(R.NOT_REPRODUCIBLE) for d in rep["not_reproducible"])
    assert all(r["excluded_cells"] == len(nonrep) for r in rep["criteria"])


def test_unknown_applications_blank_on_history(fx_wb):
    """History shows unknown applications blank ("not in file"), not 0; known ones as numbers."""
    run, info = fx_wb["run"], fx_wb["info"]
    lay = info["layout"]
    ws = fx_wb["values"]["History"]
    unk = run.cells.meta["apps_unknown"]
    assert unk.any()
    for i in range(run.cells.n):
        for j in range(len(run.cells.cohorts)):
            v = ws.cell(lay["r0h"] + i + 1, lay["hcol"]["apps"] + j + 1).value
            if unk[i, j]:
                assert v is None, (i, j, v)
            else:
                assert v == run.cells.apps[i, j], (i, j, v)


def test_loaded_values_reach_the_ledger(fxr):
    run = fxr["run"]
    for s in run.scenarios:
        ld = run.loaded[s.name]
        sd = next(x for x in fxr["fx"]["scenarios"] if x["name"] == s.name)
        assert np.array_equal(ld["yield"], sd["yield"]) and np.array_equal(ld["admit_rate"], sd["admit_rate"])
        assert np.array_equal(s.admit_rate, sd["admit_rate"]) and s.pool_multiplier == ld["pool_multiplier"]
        for k in CASES:
            lc = run.lcs[s.name][k]
            assert np.array_equal(lc.yld, sd["yield"]) and lc.tuition == sd["tuition"]
            assert np.allclose(lc.award, sd["award_usd"], atol=0.5)
        assert not L.full_tuition_conflicts(run.cells, run.cfg, s, run.parents[s.name]).any()


def test_tuition_formula_reproduces_fixture_tuition(fxr):
    """Spec section 2: with tuition_rounding_usd and the increase rounded to 0.1%, the formula reproduces every
    history step; at the reproduce increase it reproduces each scenario's loaded tuition."""
    from sw.config import round_to
    cfg, fx = fxr["cfg"], fxr["fx"]
    tb = fx["tuition_by_cohort"]
    ys = sorted(tb)
    for a, b in zip(ys[:-1], ys[1:]):
        pct = float(L.xround((tb[b] / tb[a] - 1) * 1000)) / 10
        assert round_to(tb[a] * (1 + pct / 100), cfg["tuition_rounding_usd"]) == tb[b], (a, b, pct)
    for s in fxr["run"].scenarios:
        assert scenario_tuition(cfg, s.tuition_increase_pct) == s.tuition_loaded_usd, s.name


def test_fixture_enrolled_follow_the_ledger_rounding(fxr):
    """The file's enrolled equal round(admits x yield) on its own admits and yields, cell by cell: the ledger's
    integer-enrolled rule (section 3 step 6) matches the file's."""
    for sd in fxr["fx"]["scenarios"]:
        assert np.array_equal(L.xround(sd["admits"] * sd["yield"]), sd["enrolled"]), sd["name"]


def test_fixture_summary_rows_agree_with_its_panels(fxr):
    """The loader reads the right summary block: its class and merit rows equal the panel sums."""
    for sd in fxr["fx"]["scenarios"]:
        sm = sd["summary"]
        if not sm or sm.get("class") is None:
            continue
        assert sm["class"] == float(sd["enrolled"].sum()), sd["name"]
        assert abs(sm["money"]["merit"] - float((sd["enrolled"] * sd["award_usd"]).sum())) < 0.5, sd["name"]


def test_every_cell_difference_has_a_cause(fxr):
    """Each cell whose ledger admits or enrolled differ from the file's is attributed to an identified cause; with the
    Nov 18 decisions the only remaining one is a cell not reproducible from the file."""
    diffs = [c for v in fxr["report"]["cell_differences"].values() for c in v]
    assert all(c["cause"] and not c["cause"].startswith("unexplained") for c in diffs), \
        [c for c in diffs if not c["cause"] or c["cause"].startswith("unexplained")][:5]


def test_reproduce_workbook_equals_python(fx_wb):
    """Every formula cell of the fixture's reproduce workbook (sentinel build) equals Python after recalculation."""
    from conftest import close
    wb = fx_wb["values"]
    exp = fx_wb["info"]["expected"]
    bad = [(sh, wb[sh].cell(r + 1, c + 1).coordinate, v, wb[sh].cell(r + 1, c + 1).value)
           for (sh, r, c), v in exp.items() if not close(wb[sh].cell(r + 1, c + 1).value, v)]
    assert len(exp) > 10_000
    assert not bad, bad[:5]
    assert "Reproduce" in wb.sheetnames and "Trim" not in wb.sheetnames
    sheet, r0, c0 = fx_wb["info"]["names"]["in_mode"][:3]
    assert wb[sheet].cell(r0 + 1, c0 + 1).value == "Reproduce"


def _criteria_ids():
    with open(os.path.join(ROOT, "config", "richmond.yaml")) as f:
        cfg = yaml.safe_load(f)
    ts = sorted(set(cfg["score"]["median_thresholds"]) | {cfg["score"]["pool_threshold"], cfg["score"]["floor"]},
                reverse=True)
    crit = ["class", "merit", "ntr"] + [f"at_or_above_{t:g}" for t in ts] + \
        ["below_floor", "gpa_hi", "full_tuition", "no_merit_award", "margin_score", "margin_gpa"]
    return [(i, c) for i in (4, 0, 1, 2, 3) for c in crit]      # Scenario 4 first (BM-7, R3-1)


@pytest.mark.parametrize("idx,criterion", _criteria_ids(), ids=[f"s{i}-{c}" for i, c in _criteria_ids()])
def test_pass_criterion(fxr, idx, criterion):
    """Spec section 9 pass criteria, Scenario 4 (s4) first, then Baseline (s0) and Scenarios 1 to 3: class, merit
    spend and counts equal; NTR within $100; full-tuition and no-merit-award counts and the margins equal to the
    narrative. Cells not reproducible from the file are left out of both sides (DECISIONS Nov 18). A criterion the file
    does not give is skipped (Baseline has no summary block)."""
    names = [s.name for s in fxr["run"].scenarios]
    if idx >= len(names):
        pytest.skip("the fixture has fewer scenarios")
    row = next(r for r in fxr["rows"] if r["scenario"] == names[idx] and r["criterion"] == criterion)
    if row["pass"] is None:
        pytest.skip(f"{names[idx]} {criterion}: not derivable from the file")
    assert row["pass"], (f"{names[idx]} {criterion}: ledger {row['ours']:g}, file {row['file']:g} ({row['source']}). "
                         f"Likeliest cause: {row['cause']}")
