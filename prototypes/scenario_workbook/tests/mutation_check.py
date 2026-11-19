"""Test 20: mutation check [v0.6.1, v0.6.2] (spec section 11). Run on demand; pytest does not collect this file.

Applies each mutant below, one at a time, to a scratch copy of the prototype (everything except output/), runs the
suite there (stopping at the first failure, slow tests last) and reports which mutants survive. Acceptance: no
survivor except those listed in EQUIVALENT, each with the reason it cannot change any result on valid input.

Two modes:
  Python (default)  the Python mutants (MUTANTS) against every test, with SW_SKIP_EXCEL set (the workbook tests
                    compare Excel with Python, so any Python mutant would fail them for a trivial reason)
  Excel (--excel)   the workbook-formula mutants (EXCEL_MUTANTS, sw/workbook.py) against tests 3, 6, 8, 9 and 18,
                    with LibreOffice recalculating every build [v0.6.2, P2-01]

    cd prototypes/scenario_workbook
    ../../.venv/bin/python tests/mutation_check.py
    ../../.venv/bin/python tests/mutation_check.py --excel --jobs 6
    ../../.venv/bin/python tests/mutation_check.py --jobs 6 --only L8,P3

Guards [v0.6.2, P2-02]: the unmutated baseline always runs, in a copy made the same way as the mutant copies, and
must pass; every mutant run must collect the same number of tests as the baseline ("count mismatch" otherwise); the
report warns when one test accounts for more than half of the catches.

Mutant sources:
  A    the 24 survivors in Review_Phase1_Build.md Appendix A (their IDs)
  A+   the 46 mutants Appendix A lists as caught, reconstructed from its one-line descriptions (the review's own
       mutant code was not saved), IDs X01 to X45
  1.1  mutants of the Phase 1.1 changes and of the choices recorded in spec v0.6.1 (R-05, R-07, R-08, OP-1, OP-3,
       OP-5), IDs N01 to N17
  2.1  mutants of the Phase 2.1 Python changes (spec v0.6.2), IDs N18 to N22; P21-03, N23
  P3   mutants of the Phase 3 changes (reproduce mode, the loader, integer counts, Excel-style rounding), IDs N24
       to N39
  P3.1 mutants of the Phase 3 completion (application rounding, unknown applications, exclusion, 509 block), IDs
       N40 to N46
  P2.2 mutants of the Phase 2.2 changes (spec v0.6.3 section 0A: percentile targets, tuition in dollars, the class-
       table P(cap), the revenue goal basis, above_floor, the pool strip's percentile columns, marker and break-evens,
       the reproduce whole-dollar need rule), IDs N47 to N76; Excel E76 to E104
  XL, XL+, 2.1, P21, P3, P3.1, P2.2 (Excel mode)  see EXCEL_MUTANTS, IDs E01 to E104

--deselect PREFIX (repeatable) leaves tests out of every run, baseline included; not used by default (R3-5: the
fixture's pass-criterion tests pass since the Nov 18 decisions). Test 6's fixture tests run when YA_FIXTURE_PATH is
set (absolute path).
Exit status: 0 when every survivor is in EQUIVALENT, every mutant applied and every run collected the baseline's test
count; 1 otherwise. Report JSON: output/mutation/report.json (Python) or report_excel.json (Excel).
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SLOW_LAST = ["test_13_segment_incentive.py", "test_05_shape.py", "test_04_cf_vs_sim.py"]
EXCEL_TESTS = ["test_03_excel_equals_python.py", "test_06_reproduce.py", "test_08_levers.py",
               "test_09_reconciliation.py", "test_18_v06_blocks.py", "test_23_above_floor.py",
               "test_26_marker_excel.py"]
DESELECT = []          # node-id prefixes passed to pytest --deselect (set from the command line)

# (id, source, file, old, new, description). `old` must occur exactly once in the file.
MUTANTS = [
    # ---- A: Appendix A survivors ----------------------------------------------------------------------------
    ("L8", "A", "sw/ledger.py",
     "            out[cells.residency == res] = float(val)",
     "            out[cells.residency == res] += float(val)",
     "Residency yield-shift override adds instead of replacing"),
    ("L9", "A", "sw/ledger.py",
     "    yld = np.clip(response.yield_at(base, award, case) + shift / 100.0, base.floor, base.cap)",
     "    yld = response.yield_at(base, award, case) + shift / 100.0",
     "No clip after the shift"),
    ("L13", "A", "sw/ledger.py",
     "    C_any = float((np.minimum(e_p, e_s) * inc)[pop].sum())",
     "    C_any = float((e_p * inc)[pop].sum())",
     "C_any without min (uses the parent's enrolled)"),
    ("L15", "A", "sw/ledger.py",
     "    dNTR = float((e_s * lc_s.w - e_p * lc_p.w)[pop].sum())",
     "    dNTR = float((e_s * lc_s.w - e_p * lc_s.w)[pop].sum())",
     "dNTR prices the parent with the child's weights"),
    ("L17", "A", "sw/ledger.py",
     "    V = float((lc.admits[m] * lc.yld[m] * (1 - lc.yld[m])).sum() + s * s * M * M)",
     "    V = float((lc.admits[m] * lc.yld[m] * (1 - lc.yld[m])).sum())",
     "Segment V_S without the shock term"),
    ("L19", "A", "sw/ledger.py",
     '    out["full_tuition_n"] = float(e[lc.award >= lc.tuition - 1e-6].sum())',
     '    out["full_tuition_n"] = float(e[lc.award >= lc.tuition - 10000].sum())',
     "Full-tuition count tolerance of $10,000"),
    ("R3", "A", "sw/response.py",
     "        if a >= min_adm:",
     "        if a > min_adm:",
     "Segment pool needs more than 30 admits"),
    ("R6", "A", "sw/response.py",
     '    tol = float(cfg["evidence_tolerance_usd"])',
     "    tol = 0.0",
     "Evidence tolerance ignored"),
    ("K9", "A", "sw/risk.py",
     "            out.append((1 + s * zi, 1 + s * (rho * zi + c * zj), wi * wj / math.pi))",
     "            out.append((1 + s * zi, 1 + s * zj, wi * wj / math.pi))",
     "Exact two-group shocks independent"),
    ("K10", "A", "sw/risk.py",
     "Z90 = 1.645",
     "Z90 = 1.96",
     "90% ranges use 1.96 (class, NTR and segment share the constant)"),
    ("K13", "A", "sw/risk.py",
     "    r05 = cf_median(lc.admits, lc.yld, g, s, 0.5)",
     "    r05 = cf_median(lc.admits, lc.yld, g, s, rho)",
     "rho 0.5 sensitivity uses the configured rho"),
    ("T2", "A", "sw/trim.py",
     "    rates = r - (r - f) * share",
     "    rates = r - r * share",
     "Trimmed rate ignores floor_rate"),
    ("T6", "A", "sw/trim.py",
     "        rates = _settle_integer(lc, rates, share, order, N, f)",
     "        rates = rates",
     "Integer settling removed"),
    ("T6b", "A", "sw/trim.py",
     "            admits[last] = np.clip(admits[last] - L.xround(resid / y_last), lo, lc.admits[last])",
     "            admits[last] = np.clip(admits[last], lo, lc.admits[last])",
     "Integer settling step idle"),
    ("T8", "A", "sw/trim.py",
     "float(lc.cells.score_lo[adm & scored].min())",
     "float(lc.cells.score_lo[scored].min())",
     "Lowest band admitted ignores admits"),
    ("P3", "A", "sw/strip.py",
     "        Vm = P[\"Vm\"] + m * Q[\"Vm\"] + s * s * (Gp * Gp + Gm * Gm - 2 * rho * Gp * Gm)",
     "        Vm = P[\"Vm\"] + m * Q[\"Vm\"] + s * s * (Gp * Gp + Gm * Gm - 2 * Gp * Gm)",
     "Pool strip median ignores rho"),
    ("P4", "A", "sw/strip.py",
     "        Vn = P[\"Vn\"] + m * Q[\"Vn\"] + s * s * Wm * Wm",
     "        Vn = P[\"Vn\"] + m * Q[\"Vn\"]",
     "Pool strip NTR SD without the shock"),
    ("P6", "A", "sw/strip.py",
     "    be_ntr = (ntr_target - mean_ntr) / sumwA * 100.0",
     "    be_ntr = (ntr_target - mean_ntr) / sumA * 100.0",
     "NTR break-even uses the wrong denominator"),
    ("P7", "A", "sw/strip.py",
     '        "clip_count": int(binds.sum()),',
     '        "clip_count": 0,',
     "Clip count always 0"),
    ("P8", "A", "sw/strip.py",
     '            "discount_entering_y1": (gross - ntr) / gross if gross > 0 else 0.0,',
     '            "discount_entering_y1": (gross - ntr - lc.specialty) / gross if gross > 0 else 0.0,',
     "Tuition what-if discount column wrong (specialty left out of aid)"),
    ("P9", "A", "sw/strip.py",
     "    x = lc.p * (t_base - example_award)",
     "    x = lc.p * t_base",
     "Scaled net-tuition line ignores the award"),
    ("P10", "A", "sw/strip.py",
     "        _, award = L.resolve_awards(scen, T, pct / 100.0, lc.eligible)",
     "        award = lc.award",
     "Tuition what-if awards not recomputed at T(p)"),
    ("P12", "A", "sw/strip.py",
     "            r = risk.cf_median(A, yd, g, s, rho)",
     "            r = risk.cf_median(A, y, g, s, rho)",
     "Yield-strip medians ignore the shift"),
    ("C3", "A", "sw/config.py",
     '        f *= 1.0 + cfg["tuition_increase_by_year"][y] / 100.0',
     '        f += cfg["tuition_increase_by_year"][y] / 100.0',
     "Multi-year tuition increase added instead of compounded"),

    # ---- A+: Appendix A "caught" list, reconstructed ----------------------------------------------------------
    ("X01", "A+", "sw/ledger.py",
     "    pool = np.where(upper, scen.pool_multiplier, 1.0)",
     "    pool = np.full(cells.n, scen.pool_multiplier)",
     "Pool multiplier applied below the pool threshold"),
    ("X02", "A+", "sw/ledger.py",
     "(1.0 + (scen.segment_pool_lift_pct / 100.0) * in_seg)",
     "(1.0 + (scen.segment_pool_lift_pct / 100.0))",
     "Segment lift applied outside the segment"),
    ("X03", "A+", "sw/ledger.py",
     "    base = np.minimum(base, tuition)",
     "    base = base",
     "award_base not capped at tuition"),
    ("X04", "A+", "sw/ledger.py",
     "    award = np.minimum(base + scen.bonus_usd * eligible, tuition)",
     "    award = base + scen.bonus_usd * eligible",
     "Award with incentive not capped at tuition"),
    ("X05", "A+", "sw/ledger.py",
     '    full = award >= float(cfg["tuition_base"]) - 1e-6',
     "    full = np.zeros(len(award), dtype=bool)",
     "Baseline sets no full-tuition flag"),
    ("X06", "A+", "sw/ledger.py",
     "            child.full_tuition[cells.index(cid)] = bool(flag)",
     "            pass",
     "Full-tuition flag override ignored"),
    ("X07", "A+", "sw/ledger.py",
     "    lever = scen.award_usd * (1.0 + p) if scen.award_scale_with_tuition else scen.award_usd",
     "    lever = scen.award_usd",
     "award_scale_with_tuition ignored"),
    ("X08", "A+", "sw/ledger.py",
     "        out[in_seg] = float(scen.yield_shift_pts_segment)",
     "        out[in_seg] += float(scen.yield_shift_pts_segment)",
     "Segment yield-shift override adds instead of replacing"),
    ("X09", "A+", "sw/ledger.py",
     "    need = lc.need_rate * cls",
     '    need = float(lc.cfg["need"]["total"])',
     "Need aid does not scale with the class"),
    ("X10", "A+", "sw/ledger.py",
     '        "discount_entering_y1": aid / gross if gross > 0 else 0.0,',
     '        "discount_entering_y1": (merit + need) / gross if gross > 0 else 0.0,',
     "Discount rate leaves out specialty"),
    ("X11", "A+", "sw/ledger.py",
     "    if scen.bonus_min_score is not None:",
     "    if False:",
     "bonus_min_score ignored"),
    ("X12", "A+", "sw/ledger.py",
     "    if dE >= 0.5:",
     "    if dE > 0:",
     "Aid-per-additional threshold of half a student dropped"),
    ("X13", "A+", "sw/ledger.py",
     '    "pool_multiplier", "specialty_usd",',
     '    "specialty_usd",',
     "Validity check drops pool_multiplier"),
    ("X14", "A+", "sw/ledger.py",
     '        "segment_lo90": max(0.0, M - risk.Z90 * sd),',
     '        "segment_lo90": M - risk.Z90 * sd,',
     "Segment lo90 not clipped at zero"),
    ("X15", "A+", "sw/ledger.py",
     '            out["share_at_or_above_t"][t] = at / e_scored if e_scored > 0 else 0.0',
     '            out["share_at_or_above_t"][t] = at / out["class_n"] if e_scored > 0 else 0.0',
     "Share at or above t over the whole class, not the scored class"),
    ("X16", "A+", "sw/ledger.py",
     "        admits = xround(admits)",
     "        admits = admits",
     "integer_admits does not round"),
    ("X17", "A+", "sw/response.py",
     "        y0[c] = np.where(n > 0, (n * centered + k * ypool) / (n + k), ypool)",
     "        y0[c] = np.where(n > 0, (n * centered + k * ypool) / (n + k + 1), ypool)",
     "Pooling denominator"),
    ("X18", "A+", "sw/response.py",
     "(a0 - np.nan_to_num(abar))",
     "(np.nan_to_num(abar) - a0)",
     "Re-centering sign"),
    ("X19", "A+", "sw/response.py",
     "        if a >= min_adm:",
     "        if False:",
     "Segment pool never used"),
    ("X20", "A+", "sw/response.py",
     "        y0[c] = np.where(n > 0, (n * centered + k * ypool) / (n + k), ypool)",
     "        y0[c] = np.where(n > 0, (n * centered + k * ypool) / (n + k), 0.0)",
     "Zero-admit cells get yield 0 instead of the pool"),
    ("X21", "A+", "sw/response.py",
     "        ybar = np.where(n > 0, cells.enrolled.sum(axis=1) / n, np.nan)",
     "        ybar = np.where(n > 0, (cells.enrolled / np.where(adm > 0, adm, 1.0)).mean(axis=1), np.nan)",
     "ybar unweighted across cohorts"),
    ("X22", "A+", "sw/risk.py",
     "    V = float((A * y * (1 - y)).sum() + s * s * M * M)",
     "    V = float((A * y * (1 - y)).sum())",
     "Class variance without the shock"),
    ("X23", "A+", "sw/risk.py",
     '"p_class_over_cap": float(1 - Phi((cap + 0.5 - M) / sd)),',
     '"p_class_over_cap": float(1 - Phi((cap - M) / sd)),',
     "Cap probability without continuity correction"),
    ("X24", "A+", "sw/risk.py",
     "Phi((target + band + 0.5 - M) / sd)",
     "Phi((target + band - M) / sd)",
     "Band upper edge without continuity correction"),
    ("X25", "A+", "sw/risk.py",
     "    Vm = float(v[g != 0].sum() + s * s * (gp * gp + gm * gm - 2 * rho * gp * gm))",
     "    Vm = float(v[g != 0].sum() + s * s * (gp * gp + gm * gm - 2 * gp * gm))",
     "Median variance ignores rho"),
    ("X26", "A+", "sw/risk.py",
     "    p = float(1 - Phi((-0.5 - m) / math.sqrt(max(Vm, 1e-300))))",
     "    p = float(1 - Phi((0.5 - m) / math.sqrt(max(Vm, 1e-300))))",
     "Median tie rule (holds at a margin of zero) broken"),
    ("X27", "A+", "sw/risk.py",
     "    Vn = float((w * w * v).sum() + s * s * sw * sw)",
     "    Vn = float((w * w * v).sum())",
     "NTR variance without the shock"),
    ("X28", "A+", "sw/risk.py",
     '    unscored_g = 0.0 if cfg["unscored_in_median"] == "excluded" else -1.0',
     "    unscored_g = -1.0",
     "Unscored counted below under 'excluded'"),
    ("X29", "A+", "sw/risk.py",
     "    z = math.sqrt(2.0) * x",
     "    z = x",
     "Gauss-Hermite node scaling"),
    ("X30", "A+", "sw/risk.py",
     "    if f > 0:\n        q = f * p",
     "    if False:\n        q = f * p",
     "Fractional admits: Bernoulli part dropped in the exact model"),
    ("X31", "A+", "sw/risk.py",
     "    return float(pmf[vals >= goal].sum())",
     "    return float(pmf[vals > goal].sum())",
     "Segment probability uses > instead of >="),
    ("X32", "A+", "sw/trim.py",
     "A * y * np.maximum(0.0, r - f) / np.where(r > 0, r, 1.0)",
     "A * y * np.maximum(0.0, r) / np.where(r > 0, r, 1.0)",
     "Removable enrollment ignores floor_rate"),
    ("X33", "A+", "sw/trim.py",
     "        if protect and below and seg[i] and (mode == \"below_threshold\" or (not np.isnan(s) and s >= floor)):",
     "        if False:",
     "Segment protection off"),
    ("X34", "A+", "sw/trim.py",
     '        tie = 2 if seg[i] else (0 if cells.residency[i] == "out" else 1)',
     '        tie = 2 if seg[i] else (1 if cells.residency[i] == "out" else 0)',
     "Residency tie order reversed"),
    ("X35", "A+", "sw/trim.py",
     "        shortfall = need - R_K",
     "        shortfall = need",
     "Shortfall amount wrong"),
    ("X36", "A+", "sw/trim.py",
     '    t = cfg["score"]["median_thresholds"][0]',
     '    t = cfg["score"]["median_thresholds"][1]',
     "Protection threshold is the second median threshold"),
    ("X37", "A+", "sw/trim.py",
     "        if N > scen.class_cap:",
     "        if False:",
     "Above-cap rows not marked"),
    ("X38", "A+", "sw/strip.py",
     "        Gm = P[\"Gm\"] + m * Q[\"Gm\"]",
     "        Gm = P[\"Gm\"] + Q[\"Gm\"]",
     "Pool strip G_- does not scale with m"),
    ("X39", "A+", "sw/strip.py",
     "        V = P[\"V\"] + m * Q[\"V\"] + s * s * M * M",
     "        V = P[\"V\"] + Q[\"V\"] + s * s * M * M",
     "Pool strip class variance does not scale with m"),
    ("X40", "A+", "sw/strip.py",
     "replace(scen, pool_multiplier=1.0)",
     "replace(scen, pool_multiplier=1.0, segment_pool_lift_pct=0.0)",
     "Pool strip drops the segment lift"),
    ("X41", "A+", "sw/strip.py",
     "        ntr = float((e * (T - award)).sum()) - need - lc.ntr_const",
     "        ntr = float((e * (T - award)).sum()) - need",
     "Tuition what-if leaves out specialty"),
    ("X42", "A+", "sw/strip.py",
     "    be_class = (scen.class_target - M) / sumA * 100.0 if sumA > 0 else None",
     "    be_class = (scen.class_target - M) / M * 100.0 if sumA > 0 else None",
     "Class break-even denominator"),
    ("X43", "A+", "sw/mc.py",
     "            e = (1 + s * z1)[:, None] * np.ones(len(A))[None, :]",
     "            e = np.ones((m, len(A)))",
     "Simulation without the year shock"),
    ("X44", "A+", "sw/config.py",
     "    if target > cap:",
     "    if False:",
     "Class target above the cap accepted"),
    ("X45", "A+", "sw/config.py",
     "    return unit * float(excel_round0(x / unit))",
     "    return x",
     "Tuition not rounded"),

    # ---- 1.1: Phase 1.1 changes and v0.6.1 recorded choices --------------------------------------------------
    ("N01", "1.1", "sw/trim.py",
     "    return np.where(share > 0, settled, lc.rate)",
     "    return settled",
     "R-05 reverted: integer settling rewrites uncut cells' rates"),
    ("N02", "1.1", "sw/strip.py",
     "(e[below] * scen.award_usd[below])",
     "(e[below] * lc.award_base[below])",
     "R-07 reverted: example award in plan-year dollars (award_base)"),
    ("N03", "1.1", "sw/strip.py",
     "        below = (~np.asarray(scen.full_tuition, bool)) & (scen.award_usd < t_base - 1e-6) & (e > 0)",
     "        below = (~np.asarray(scen.full_tuition, bool)) & (scen.award_usd < t_base - 1e-6) & (lc.award > 0) & "
     "(e > 0)",
     "R-07 reverted: example award excludes zero awards"),
    ("N04", "1.1", "sw/ledger.py",
     "SEGMENT_APPROX_BELOW = 30",
     "SEGMENT_APPROX_BELOW = 20",
     "OP-3 reverted: approximate flag below 20"),
    ("N05", "1.1", "sw/ledger.py",
     "            child.award_usd[cells.index(cid)] = float(a)",
     "            child.award_usd[cells.index(cid)] = float(a)\n"
     "            child.full_tuition[cells.index(cid)] = float(a) >= "
     "scenario_tuition(cfg, parent.tuition_increase_pct) - 1e-6",
     "OP-1 reverted: an award override at or above the parent's tuition sets the flag"),
    ("N06", "1.1", "sw/ledger.py",
     '        raise ConfigError("more than one segment is configured; the scenario must name its active segment")',
     '        return cfg["segments"][0]["name"]',
     "OP-5: several segments and none named silently takes the first"),
    ("N07", "1.1", "sw/ledger.py",
     "cells.score_lo >= scen.bonus_min_score",
     "cells.score_lo > scen.bonus_min_score",
     "bonus_min_score exclusive"),
    ("N08", "1.1", "sw/strip.py",
     "    be_class = (scen.class_target - M)",
     "    be_class = (scen.class_cap - M)",
     "Class break-even aims at the cap"),
    ("N09", "1.1", "sw/ledger.py",
     '"plan_year", "segment",',
     '"plan_year",',
     "Validity check drops segment"),
    ("N10", "1.1", "sw/ledger.py",
     '    for arr in ("admit_rate", "award_usd", "full_tuition"):',
     '    for arr in ("admit_rate", "award_usd"):',
     "Validity check drops the full_tuition column"),
    ("N11", "1.1", "sw/risk.py",
     '"class_lo90": max(0.0, M - Z90 * math.sqrt(max(V, 0.0))),',
     '"class_lo90": M - Z90 * math.sqrt(max(V, 0.0)),',
     "R-08b: class lo90 not clipped at zero"),
    ("N12", "1.1", "sw/response.py",
     "    return np.clip(raw, base.floor, base.cap)",
     "    return raw",
     "R-08a: response not clipped before the shift (single clip)"),
    ("N13", "1.1", "sw/response.py",
     '        for lvl in ("residency", "group", "all"):',
     '        for lvl in ("residency", "all"):',
     "R-08c: pooling fallback skips the score group"),
    ("N14", "1.1", "sw/strip.py",
     "        below = (~np.asarray(scen.full_tuition, bool)) & (scen.award_usd < t_base - 1e-6) & (e > 0)",
     "        below = (~np.asarray(scen.full_tuition, bool)) & (lc.award < t_base - 1e-6) & (e > 0)",
     "P1.1-4 reverted: example-award membership judged on the award after the incentive"),
    ("N15", "1.1", "sw/strip.py",
     "        below = (~np.asarray(scen.full_tuition, bool)) & (scen.award_usd < t_base - 1e-6) & (e > 0)",
     "        below = (scen.award_usd < t_base - 1e-6) & (e > 0)",
     "Q-5: flagged (full-tuition) cells included in the example award"),
    ("N16", "1.1", "sw/ledger.py",
     "    return np.asarray(scen.full_tuition, bool) & (np.asarray(scen.award_usd, float) != np.asarray(ref, float))",
     "    return np.asarray(scen.full_tuition, bool)",
     "P1.1-1: every flagged cell listed as a conflict"),
    ("N17", "1.1", "sw/ledger.py",
     "        ref = parent.award_usd",
     "        ref = cells.award[:, cells.col(cfg[\"cycle\"][\"base_cycle\"])]",
     "P1.1-1: child conflicts judged against the latest-cohort award, not the parent's"),

    # ---- 2.1: Phase 2.1 Python changes [v0.6.2] ----------------------------------------------------------------
    ("N18", "2.1", "sw/strip.py",
     "        below = (~np.asarray(scen.full_tuition, bool)) & (scen.award_usd < t_base - 1e-6) & (e > 0)",
     "        below = (lc.award_base < lc.tuition - 1e-6) & (e > 0)",
     "Q-5 reverted to the P1.1-4 rule (award_base below plan-year tuition)"),
    ("N19", "2.1", "sw/ledger.py",
     "    changed = (ft != np.asarray(parent.full_tuition, bool)) | ((scen.award_usd != parent.award_usd) & ~ft)",
     "    changed = (ft != np.asarray(parent.full_tuition, bool)) | (scen.award_usd != parent.award_usd)",
     "P2-03: ignored award entries counted as award changes"),
    ("N20", "2.1", "sw/ledger.py",
     '                    "gap": None if a is None else (implied - float(a)) / float(a)})',
     '                    "gap": None if a is None else (float(a) - implied) / float(a)})',
     "Q-8f: history reconciliation gap with the wrong sign"),
    ("N21", "2.1", "sw/narrative.py",
     '        return ["Baseline: no parent scenario.", ("awards_ignored", "ignored")]',
     '        return ["Baseline: no parent scenario."]',
     "Q-6, P2-03: Baseline narrative drops ignored award entries"),
    ("N22", "2.1", "sw/config.py",
     '    "budget_basis": "total_aid",',
     '    "budget_basis": "merit",',
     "Q-8e: budget basis defaults to merit"),
    ("N23", "P21", "sw/build.py",
     '    build_id = _sha("|".join([cfg_h, data_h, scen_h, lock_h, code_h]).encode())[:12]',
     '    build_id = _sha("|".join([cfg_h, data_h, scen_h, lock_h]).encode())[:12]',
     "P21-03 reverted: build id ignores the generator code"),
    # ---- P3: Phase 3 (reproduce mode, integer counts, Excel-style rounding) -----------------------------------
    ("N24", "P3", "sw/ledger.py",
     "        yld = np.asarray(scen.yield_loaded, float).copy()",
     "        yld = np.clip(response.yield_at(base, award, case) + shift / 100.0, base.floor, base.cap)",
     "Reproduce mode ignores the loaded yields"),
    ("N25", "P3", "sw/ledger.py",
     "    tuition = float(scen.tuition_loaded_usd) if rep else scenario_tuition(cfg, scen.tuition_increase_pct)",
     "    tuition = scenario_tuition(cfg, scen.tuition_increase_pct)",
     "Reproduce mode ignores the loaded tuition"),
    ("N26", "P3", "sw/ledger.py",
     '        raise ConfigError(f"{scen.name}: reproduce mode needs loaded yields and tuition for every scenario")',
     "        return False",
     "Reproduce mode silently falls back to the response when loaded values are missing"),
    ("N27", "P3", "sw/build.py",
     '    if cfg["mode"] == "live" and (cfg["integer_admits"] or cfg["integer_enrolled"]):',
     '    if cfg["mode"] == "live" and cfg["integer_admits"]:',
     "Live build accepts integer enrolled"),
    ("N28", "P3", "sw/reproduce.py",
     "                    apps = float(round(apps))",
     "                    apps = apps",
     "Loader keeps float noise in implied applications"),
    ("N29", "P3", "sw/reproduce.py",
     "        lo = min(bands)",
     '        lo = float(re.sub(r"\\D", "", sp))',
     "'<N' score labels load at N instead of the lowest band"),
    ("N30", "P3", "sw/reproduce.py",
     '            g = "hi" if float(m.group(1)) >= hi_t - 1e-9 else "lo"',
     '            g = "hi" if float(m.group(1)) > hi_t else "lo"',
     "GPA label at the boundary loads as lo"),
    ("N31", "P3", "sw/reproduce.py",
     '                ev.append(("excluded", t))',
     '                ev.append(("below", t))',
     "Counting-rule detection mislabels 'excluded'"),
    ("N32", "P3", "sw/reproduce.py",
     "    return total - round(cut), ",
     "    return total + round(cut), ",
     "need_total adds the need cut instead of subtracting it"),
    ("N33", "P3", "sw/reproduce.py",
     "            return 1.0 + float(pct) / 100.0",
     "            return 1.0 + float(pct)",
     "Pool multiplier from the description not converted from percent"),
    ("N34", "P3", "sw/reproduce.py",
     "                    parent = cand[0]",
     "                    parent = names[k - 1]",
     "Lineage ignores the parent named in the description"),
    ("N35", "P3", "sw/reproduce.py",
     '            ok = abs(ov - fv) <= 100.0 if key == "ntr" else abs(ov - fv) < 1e-6',
     '            ok = abs(ov - fv) <= 1000.0 if key == "ntr" else abs(ov - fv) < 1e-6',
     "NTR pass tolerance widened from $100"),
    ("N36", "P3", "sw/reproduce.py",
     "                    if abs(alt_v - fv) < 1e-6:",
     "                    if False:",
     "Margin mismatch not attributed to the counting rule"),
    ("N37", "P3", "sw/reproduce.py",
     '            elif other[i] == sd["admits"][i]:',
     "            elif False:",
     "Admits difference not attributed to the other application-rounding rule"),
    ("N38", "P3", "sw/config.py",
     '    x15 = np.vectorize(lambda v: float(f"{v:.15g}") if np.isfinite(v) else v, otypes=[float])(a)',
     "    x15 = a",
     "Ledger rounding without the 15-significant-digit step (floor(x + 0.5))"),
    ("N39", "P3", "sw/labels.py",
     "    d = Decimal(format(v, \".15g\")).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)",
     "    d = Decimal(format(v, \".15g\")).quantize(Decimal(1).scaleb(-nd), rounding=\"ROUND_HALF_EVEN\")",
     "Text rounding half to even (Python's own) instead of Excel's half away from zero"),
    # ---- P3.1: Phase 3 completion (DECISIONS Nov 18; R3-3, R3-4) --------------------------------------------
    ("N40", "P3.1", "sw/ledger.py",
     "        apps = xround(apps)",
     "        apps = apps",
     "Reproduce mode does not round applications after the pool multiplier"),
    ("N41", "P3.1", "sw/config.py",
     '    return cfg.get("mode") == "reproduce" and bool((cfg.get("reproduce") or {}).get("round_apps_after_pool", False))',
     '    return bool((cfg.get("reproduce") or {}).get("round_apps_after_pool", False))',
     "Live mode rounds applications when the reproduce setting is on"),
    ("N42", "P3.1", "sw/reproduce.py",
     "        if len(cands) == 1:",
     "        if len(cands) >= 1:",
     "Unknown applications loaded although several values fit (invented)"),
    ("N43", "P3.1", "sw/reproduce.py",
     '                unknown.append((c["cell_id"], y))',
     "                pass",
     "Unknown applications load as known zeros"),
    ("N44", "P3.1", "sw/reproduce.py",
     "            fv = fv - c_file.get(key, 0.0)",
     "            fv = fv",
     "Non-reproducible cells left in the file's figures"),
    ("N45", "P3.1", "sw/ledger.py",
     "                labels.ABA509_AGREES if abs(grid[key] - v) < 1e-6 else labels.ABA509_DIFFERS)",
     "                labels.ABA509_AGREES if abs(grid[key] - v) < 1.5 else labels.ABA509_DIFFERS)",
     "509 counts agree within one student"),
    ("N46", "P3.1", "sw/ledger.py",
     "        if c > 0 and below <= qn + 1e-9 and below + c >= qn - 1e-9:",
     "        if c > 0 and below < qn and below + c >= qn - 1e-9:",
     "509 quartile on a band boundary allows only the lower band"),
    # ---- P2.2: Phase 2.2 (spec v0.6.3 section 0A: BM-1 to BM-6, item B5) ------------------------------------
    ("N47", "P2.2", "sw/risk.py", "    corr = 1.0 / (2 * pct_lattice_n(q))", "    corr = 0.5",
     "Percentile continuity correction 0.5 in place of 1/(2n) (must fail test 2 at q = 0.10)"),
    ("N48", "P2.2", "sw/risk.py", "    E = q * gp - (1 - q) * gm", "    E = q * gp - q * gm",
     "Percentile expected margin weights below t by q"),
    ("N49", "P2.2", "sw/risk.py",
     "    Vq = float(q * q * v[g > 0].sum() + (1 - q) * (1 - q) * v[g < 0].sum()",
     "    Vq = float(v[g > 0].sum() + v[g < 0].sum()",
     "Percentile binomial variance unweighted"),
    ("N50", "P2.2", "sw/risk.py",
     '        "margin_q_t": q * float(lc.enrolled[g > 0].sum()) - (1 - q) * float(lc.enrolled[g < 0].sum()),',
     '        "margin_q_t": float(lc.enrolled[g > 0].sum()) - float(lc.enrolled[g < 0].sum()),',
     "Percentile margin readout is the median margin"),
    ("N51", "P2.2", "sw/risk.py", "    r05 = cf_pct(lc.admits, lc.yld, g, q, s, 0.5)",
     "    r05 = cf_pct(lc.admits, lc.yld, g, q, s, rho)", "Percentile rho 0.5 line uses the configured rho"),
    ("N52", "P2.2", "sw/risk.py", "PCT_APPROX_BELOW = 20 ", "PCT_APPROX_BELOW = 10 ",
     "Approximate flag below 10 expected instead of 20"),
    ("N53", "P2.2", "sw/risk.py", '    for b in sorted(float(x) for x in cfg["score"]["bands"]):',
     '    for b in sorted((float(x) for x in cfg["score"]["bands"]), reverse=True):',
     "Spread band takes the smallest qualifying bound"),
    ("N54", "P2.2", "sw/risk.py",
     '    uns = float(e[~scored].sum()) if cfg["unscored_in_median"] == "below" else 0.0', "    uns = 0.0",
     "Spread band ignores unscored under 'below'"),
    ("N55", "P2.2", "sw/risk.py", "            k = np.minimum(-((-(n_ - m_) * j) // m_), len(pp))",
     "            k = np.minimum(((n_ - m_) * j) // m_, len(pp))", "Exact percentile event uses floor, not ceil"),
    ("N56", "P2.2", "sw/trim.py", '(mode == "below_threshold" or (not np.isnan(s) and s >= floor))',
     '(mode == "below_threshold" or True)', "above_floor protects segment cells below the floor"),
    ("N57", "P2.2", "sw/trim.py", '    protect = mode in ("below_threshold", "above_floor")',
     '    protect = mode == "below_threshold"', "above_floor protects nothing"),
    ("N58", "P2.2", "sw/trim.py", '"p_class_over_cap": risk.class_probs(lc)["p_class_over_cap"]}',
     '"p_class_over_cap": risk.class_probs(lc)["p_class_in_band"]}',
     "Class-size table P(class > cap) is the band probability"),
    ("N59", "P2.2", "sw/strip.py",
     '    be = {"class": (scen.class_target - P["M"]) / Q["M"] if Q["M"] != 0 else None}',
     '    be = {"class": (scen.class_cap - P["M"]) / Q["M"] if Q["M"] != 0 else None}',
     "Break-even pool multiplier aims at the cap, not the target"),
    ("N60", "P2.2", "sw/strip.py", "        be[key] = -e_lo / e_hi if e_hi != 0 else None",
     "        be[key] = e_lo / e_hi if e_hi != 0 else None", "Break-even percentile multiplier sign"),
    ("N61", "P2.2", "sw/strip.py", "    corr = 1.0 / (2 * pct_lattice_n(q))", "    corr = 0.5",
     "Pool-strip percentile correction 0.5"),
    ("N62", "P2.2", "sw/strip.py", "                                                       - 2 * rho * q * (1 - q) * gp * gm)",
     "                                                       - 2 * q * (1 - q) * gp * gm)",
     "Pool-strip percentile ignores rho"),
    ("N63", "P2.2", "sw/strip.py", "if (a + b) / 2 < target)", "if a < target)",
     "Growth marker picks the row below, not the nearest"),
    ("N64", "P2.2", "sw/risk.py", "    target = ntr_target_effective(lc.cfg) if target is None else target",
     '    target = lc.cfg.get("ntr_target") if target is None else target',
     "Summary P(ntr_y1) ignores the all_jd effective target"),
    ("N65", "P2.2", "sw/strip.py", "        n = risk.cf_ntr(A, yd, lc.w, s, lc.ntr_const, ntr_target)",
     '        n = risk.cf_ntr(A, yd, lc.w, s, lc.ntr_const, cfg.get("ntr_target"))',
     "Yield-strip probability ignores the effective target"),
    ("N66", "P2.2", "sw/strip.py", "    be_ntr = (ntr_target - mean_ntr) / sumwA * 100.0 if",
     '    be_ntr = (cfg.get("ntr_target") - mean_ntr) / sumwA * 100.0 if',
     "Yield-strip NTR break-even ignores the effective target"),
    ("N67", "P2.2", "sw/config.py", '        return float(target) - float(cfg["continuing_ntr_usd"])',
     "        return float(target)", "Effective target does not subtract continuing revenue"),
    ("N68", "P2.2", "sw/config.py", "        if y in usd:\n",
     '        if y in usd and y not in cfg["tuition_increase_by_year"]:\n',
     "Tuition increase takes precedence over tuition_by_year_usd"),
    ("N69", "P2.2", "sw/ledger.py",
     '        need_rate = float(xround(float(cfg["need"]["total"]) / float(cfg["need"]["reference_class"])))',
     '        need_rate = float(need_total) / float(cfg["need"]["reference_class"])',
     "Reproduce need rate not rounded to whole dollars (B5)"),
    ("N70", "P2.2", "sw/ledger.py", '        need_lump = float(need_total) - float(cfg["need"]["total"])',
     "        need_lump = 0.0", "Reproduce need departure dropped (B5)"),
    ("N71", "P2.2", "sw/risk.py", "    r = cf_ntr(lc.admits, lc.yld, lc.w, _s(lc), lc.ntr_const, target)",
     "    r = cf_ntr(lc.admits, lc.yld, lc.w, _s(lc), lc.specialty, target)",
     "NTR distribution leaves out the need departure"),
    ("N72", "P2.2", "sw/strip.py", "    mean_ntr = float((lc.w * A * y).sum()) - lc.ntr_const",
     "    mean_ntr = float((lc.w * A * y).sum()) - lc.specialty",
     "Yield-strip NTR mean leaves out the need departure"),
    ("N73", "P2.2", "sw/config.py",
     '    if cfg["ntr_goal_basis"] == "all_jd" and cfg["continuing_ntr_usd"] is None:', "    if False:",
     "all_jd accepted without continuing_ntr_usd"),
    ("N74", "P2.2", "sw/config.py", "        if abs(q * 100 - round(q * 100)) > 1e-9:", "        if False:",
     "q with three decimals accepted"),
    ("N75", "P2.2", "sw/config.py", '        if t not in bands:\n            raise ConfigError(f"score.percentile_targets',
     '        if False:\n            raise ConfigError(f"score.percentile_targets', "Percentile t outside the bands accepted"),
    ("N76", "P2.2", "sw/strip.py", "        ntr = float((e * (T - award)).sum()) - need - lc.ntr_const",
     "        ntr = float((e * (T - award)).sum()) - need - lc.specialty",
     "Tuition what-if leaves out the need departure"),
]

# Excel-formula mutants [v0.6.2, P2-01] (spec section 11, test 20; run with --excel). Each changes one formula string in
# sw/workbook.py; the workbook is rebuilt, recalculated in LibreOffice and run against tests 3, 8, 9 and 18. Sources:
#   XL   the 13 survivors of Review_Phase2_Build.md section 2, reconstructed from its table (the review's own mutant
#        code was not saved); E-number = the review's X-number
#   XL+  the review's 34 caught mutants, reconstructed from its scope (formula strings in sw/workbook.py; their
#        descriptions were not published), numbered in the remaining slots E02 to E46
#   2.1  mutants of the Phase 2.1 workbook changes, E48 to E59
#   P21  the review's X09 as worded in Review_Phase2_1_Fix_Pass.md (override adds instead of replacing), E60 to E62
W = "sw/workbook.py"
EXCEL_MUTANTS = [
    ("E01", "XL", W, '''f"IF({ft_c}=1,{T},MIN({lever},{T}))"''', '''f"IF({ft_c}=1,{T},{lever})"''',
     "Award base not capped at tuition for an unflagged cell (review X01)"),
    ("E02", "XL+", W, '''f'*IF({LVf("bonus_min_score")}="",1,IF(''', '''f'*IF(1,1,IF(''',
     "Incentive eligibility ignores bonus_min_score"),
    ("E03", "XL+", W, '''IF({S_("upper")}=1,{LVf("pool_multiplier")},1)*\'''', '''{LVf("pool_multiplier")}*\'''',
     "Pool multiplier applied below the pool threshold"),
    ("E04", "XL+", W, '''f'(1+{LVf("segment_pool_lift_pct")}/100*{B("in_seg")})')''',
     '''f'(1+{LVf("segment_pool_lift_pct")}/100)')''', "Segment lift applied outside the segment"),
    ("E05", "XL", W,
     '''            yf = (f'MIN({S_("cap")},MAX({S_("floor")},MIN({S_("cap")},MAX({S_("floor")},{S_("y0")}+in_slope_{k}/100*'
                  f'({B("award")}-{S_("a0")})/1000))+{B("shift")}/100))')''',
     '''            yf = (f'MIN({S_("cap")},MAX({S_("floor")},{S_("y0")}+in_slope_{k}/100*'
                  f'({B("award")}-{S_("a0")})/1000))+{B("shift")}/100')''',
     "Yield: outer clip (after the shift) removed (review X05)"),
    ("E06", "XL", W,
     '''            yf = (f'MIN({S_("cap")},MAX({S_("floor")},MIN({S_("cap")},MAX({S_("floor")},{S_("y0")}+in_slope_{k}/100*'
                  f'({B("award")}-{S_("a0")})/1000))+{B("shift")}/100))')''',
     '''            yf = (f'MIN({S_("cap")},MAX({S_("floor")},{S_("y0")}+in_slope_{k}/100*'
                  f'({B("award")}-{S_("a0")})/1000+{B("shift")}/100))')''',
     "Yield: inner clip (response, before the shift) removed (review X06)"),
    ("E07", "XL+", W, '''f'MIN({B("award_base")}+{bonus_usd}*{B("elig")},{T})\'''', '''f'{B("award_base")}+{bonus_usd}*{B("elig")}\'''',
     "Award with incentive not capped at tuition"),
    ("E08", "XL+", W, '''lever = f'IF({LVf("award_scale_with_tuition")}=1,{aw_c}*(1+{P}/100),{aw_c})\'''', '''lever = f'{aw_c}\'''',
     "Awards never scale with tuition"),
    ("E09", "XL", W, '''IF({LVf("yield_shift_pts_in")}<>"",{LVf("yield_shift_pts_in")},\'''', '''IF(0,0,\'''',
     "In-state yield-shift override ignored (review X09)"),
    ("E10", "XL", W, '''f'IF({nt}="",in_need_total,{nt})/in_need_reference_class\'''', '''f'in_need_total/in_need_reference_class\'''',
     "need_total override on Levers ignored (review X10)"),
    ("E11", "XL+", W, '''f'IF({B("in_seg")}*({LVf("yield_shift_pts_segment")}<>"")=1,{LVf("yield_shift_pts_segment")},\'''',
     '''f'IF(0,0,\'''', "Segment yield-shift override ignored"),
    ("E12", "XL+", W, '''IF({LVf("yield_shift_pts_out")}<>"",{LVf("yield_shift_pts_out")},\'''', '''IF(0,0,\'''',
     "Out-of-state yield-shift override ignored"),
    ("E13", "XL+", W, '''IF(({B("award")}>={S_("award_lo")}-\'''', '''IF(({B("award")}>={S_("award_lo")}-0*\'''',
     "Evidence tolerance ignored below the observed range"),
    ("E14", "XL+", W, '''f'{T}-{B("award")}-{NR}\'''', '''f'{T}-{B("award")}\'''', "Net tuition weight without need"),
    ("E15", "XL+", W, '''f"ROUND(in_tuition_base*(1+{LVf('tuition_increase_pct')}/100)/in_tuition_rounding_usd,0)"''',
     '''f"ROUND(in_tuition_base*(1+{LVf('tuition_increase_pct')}/100)/in_tuition_rounding_usd+0.5,0)"''',
     "Scenario tuition rounded up instead of to the nearest step"),
    ("E16", "XL+", W, '''return f"1-NORMSDIST(({d['CAP']}+0.5-{M})/{SDV})"''', '''return f"1-NORMSDIST(({d['CAP']}-{M})/{SDV})"''',
     "P(class over cap) without the continuity correction"),
    ("E17", "XL+", W, '''        V = f"(SUMPRODUCT({A},{Y},1-{Y})+{sd}^2*{M}^2)"''', '''        V = f"(SUMPRODUCT({A},{Y},1-{Y}))"''',
     "Class variance without the shock term"),
    ("E18", "XL+", W, '''return f"IF({gross}>0,{aid}/({gross}),0)"''', '''return f"IF({gross}>0,{merit}/({gross}),0)"''',
     "Discount rate counts merit only"),
    ("E19", "XL+", W, '''return f"SUMPRODUCT(({AW}>={d['T']}-0.000001)*{E})"''', '''return f"SUMPRODUCT(({AW}>={d['T']}-10000)*{E})"''',
     "Full-tuition count with a $10,000 tolerance"),
    ("E20", "XL+", W, '''Ca = f"SUMPRODUCT(({I}>0)*(({Ep}<={Es})*{Ep}+({Ep}>{Es})*{Es})*{I})"''',
     '''Ca = f"SUMPRODUCT(({I}>0)*{Ep}*{I})"''', "C_any without the elementwise minimum"),
    ("E21", "XL+", W, '''-{Ep}*{dp['w']}))"''', '''-{Ep}*{d['w']}))"''', "dNTR prices the parent with the child's weights"),
    ("E22", "XL+", W, '''VS = f"(SUMPRODUCT({SEG},{A},{Y},1-{Y})+{sd}^2*{MS}^2)"''', '''VS = f"(SUMPRODUCT({SEG},{A},{Y},1-{Y}))"''',
     "Segment variance without the shock term"),
    ("E23", "XL", W, '''1-NORMSDIST(({ceil_x(gl)}-0.5-{MS})/\'''', '''1-NORMSDIST(({gl}-0.5-{MS})/\'''',
     "Segment goal not rounded up in P(segment goal) (review X23)"),
    ("E24", "XL+", W, '''r_ = rho if name == "p_median_t" else "0.5"''', '''r_ = rho''',
     "rho 0.5 sensitivity uses the configured rho"),
    ("E25", "XL+", W, '''return f"1-NORMSDIST((-0.5-({gp}-{gm}))/SQRT(MAX({vm},1E-300)))"''',
     '''return f"1-NORMSDIST((0-({gp}-{gm}))/SQRT(MAX({vm},1E-300)))"''', "P(median) without the continuity correction"),
    ("E26", "XL+", W, '''es = f"SUMPRODUCT(({d['scored']}=1)*{E})"''', '''es = f"SUM({E})"''',
     "Share at or above t over all enrolled, not enrolled with a score"),
    ("E27", "XL+", W, '''f = (f'IF({c("scored")}=0,IF(in_unscored_in_median="excluded",0,-1),\'''', '''f = (f'IF({c("scored")}=0,-1,\'''',
     "Unscored counted below the score median whatever unscored_in_median says"),
    ("E28", "XL", W, '''for key in ("rate", "award", "ft"))''', '''for key in ("rate", "award"))''',
     "Validity check ignores the full_tuition column (review X28)"),
    ("E29", "XL+", W, '''for f in L.VALIDITY_FIELDS)''', '''for f in L.VALIDITY_FIELDS[:1])''',
     "Validity check compares the pool multiplier only"),
    ("E30", "XL+", W, '''M = f"({P('lo', 'M')}+{m}*{P('hi', 'M')})"''', '''M = f"({P('lo', 'M')}+{P('hi', 'M')})"''',
     "Pool strip: class ignores the multiplier"),
    ("E31", "XL+", W, '''V = f"({P('lo', 'V')}+{m}*{P('hi', 'V')}+{sd}^2*{M}^2)"''', '''V = f"({P('lo', 'V')}+{m}*{P('hi', 'V')})"''',
     "Pool strip: class variance without the shock"),
    ("E32", "XL", W, '''{C(4)}*{C(5)}*MAX(0,{C(3)}-{fr})/{C(3)},0)"''', '''{C(4)}*{C(5)},0)"''',
     "Trim: removable enrollment ignores floor_rate (review X32)"),
    ("E33", "XL+", W, '''({info['M']}-{Nref}-{C(8)})/{C(7)}''', '''({info['M']}-{Nref})/{C(7)}''',
     "Trim: removed share ignores what earlier cells removed"),
    ("E34", "XL", W, '''f"{rL}-({rL}-{fr})*INDEX(''', '''f"{rL}-{rL}*INDEX(''', "Trim: trimmed rate ignores floor_rate (review X34)"),
    ("E35", "XL+", W, '''f = f"SUMPRODUCT(({d['scored']}=1)*({d['score_lo']}={b:g})*({AB}-{AN}))"''',
     '''f = f"SUMPRODUCT(({d['scored']}=1)*({d['score_lo']}={b:g})*({AN}-{AB}))"''', "Class table: admits cut with the wrong sign"),
    ("E36", "XL", W, '''f"IF({sa}>=in_pooling_min_admits,{se}/{sa},''', '''f"IF({sa}>in_pooling_min_admits,{se}/{sa},''',
     "Segment pool needs more than the pool size (review X36)"),
    ("E37", "XL+", W, '''+in_pooling_k*{c('ypool')})/({c('n')}+in_pooling_k),''', '''+in_pooling_k*{c('ypool')})/({c('n')}),''',
     "Partial pooling denominator without k"),
    ("E38", "XL", W, '''-2*in_shock_corr*{Gp}*{Gm}))"''', '''-2*{Gp}*{Gm}))"''', "Pool strip median ignores rho (review X38)"),
    ("E39", "XL+", W, '''self.fx(sheet, r, cc, f'MIN(IF({ft_c}=1,{Tp},MIN({lev},{Tp}))+{bonus_usd}*{B("elig")},{Tp})',''',
     '''self.fx(sheet, r, cc, f'{B("award")}',''', "Tuition what-if: awards not recomputed at T(p)"),
    ("E40", "XL+", W, '''(SUM({E})*{Tp}-{ntr})/(SUM({E})*{Tp})''', '''(SUM({E})*{Tp}-{ntr}-{SP})/(SUM({E})*{Tp})''',
     "Tuition what-if discount column wrong"),
    ("E41", "XL+", W, '''cond = f"({FT}=0)*({LEV}<in_tuition_base-0.000001)*({E}>0)"''',
     '''cond = f"({LEV}<in_tuition_base-0.000001)*({E}>0)"''', "Example award: flagged cells included"),
    ("E42", "XL", W, '''self.s_fx(self.sr, 1, f"SUMPRODUCT(({A}>0)*''', '''self.s_fx(self.sr, 1, f"0*SUMPRODUCT(({A}>0)*''',
     "Yield-strip clip count always 0 (review X42)"),
    ("E43", "XL+", W, '''({d["TGT"]}-SUMPRODUCT({A},{Y}))/SUM({A})*100''', '''({d["CAP"]}-SUMPRODUCT({A},{Y}))/SUM({A})*100''',
     "Class break-even aims at the cap"),
    ("E44", "XL+", W, '''/SUMPRODUCT({W},{A})*100,""))\'''', '''/SUM({A})*100,""))\'''', "NTR break-even with the wrong denominator"),
    ("E45", "XL+", W, '''f"SUMPRODUCT(({Rs}<>{Rp})*1)"''', '''f"SUMPRODUCT(({Rs}<{Rp})*1)"''',
     "Admit rates changed counts decreases only"),
    ("E46", "XL+", W, '''f"IF(({ft}=1)*({aw}<>{refv})=1,1,0)"''', '''f"IF(({ft}=1)=1,1,0)"''',
     "P1.1-1 conflict flag on every flagged cell"),
    ("E47", "XL", W, '''f'IF({Mref}-{N}>{RK}+0.000000001,"N not reachable''', '''f'IF({Mref}-{N}>{Mref}+0.000000001,"N not reachable''',
     "Class table never reports the shortfall (review X47)"),
    # ---- 2.1 ----
    ("E48", "2.1", W, '''({LEV}<in_tuition_base-0.000001)''', '''({LEV}<{T}-0.000001)''',
     "Q-5: example award judged against plan-year tuition"),
    ("E49", "2.1", W, '''aw_terms = f"({Fs}<>{Fp})+({As}<>{Ap})*({Fs}=0)"''', '''aw_terms = f"({Fs}<>{Fp})+({As}<>{Ap})"''',
     "P2-03: ignored award entries counted as changes on Levers"),
    ("E50", "2.1", W, '''f"SUMPRODUCT(({Fs}=1)*({As}<>{Aref}))"''', '''f"SUMPRODUCT(({Fs}=1)*1)"''',
     "P2-03: ignored count includes every flagged cell"),
    ("E51", "2.1", W, '''default = "INDEX(in_seg_names,1)" if len(cfg["segments"]) == 1 else '""\'''', '''default = '""\'''',
     "P2-07: blank Levers segment means no segment"),
    ("E52", "2.1", W, '''xr = f'IF(in_budget_basis="merit",{mr},{ar})\'''', '''xr = ar''', "Q-8e: budget_basis ignored"),
    ("E53", "2.1", W, '''TEXT(({imp}-{act})/{act}*100,"0.0")''', '''TEXT(({act}-{imp})/{act}*100,"0.0")''',
     "Q-8f: reconciliation gap with the wrong sign"),
    ("E54", "2.1", W, '''{PL}/SUMPRODUCT({E0},{EL})''', '''{PL}/SUM({E0})''',
     "Q-8d: implied bonus over all Baseline enrolled, not those in scope"),
    ("E55", "2.1", W, '''{stale},{xs(labels.EXACT_CURRENT)})))\'''', '''{xs(labels.EXACT_CURRENT)},{xs(labels.EXACT_CURRENT)})))\'''',
     "P2-06: exact probability never marked stale"),
    ("E56", "2.1", W, '''f'IF({self.inp_list["median_thresholds"][0]}={t0:g},"OK",{rb(f"{t0:g}")})\'''', '''f'"OK"\'''',
     "P2-06: rebuild check on the first median threshold never fires"),
    ("E57", "2.1", W, '''{xs(labels.SCOPE_ERROR)},"OK")\'''', '''"OK","OK")\'''', "P2-07: scope error never shown"),
    ("E58", "2.1", W, '''f'IF(({a1(r, c0 + 2, False)}=1)*({a1(r, c0 + 1, False)}<>{aref})=1,\'''',
     '''f'IF(({a1(r, c0 + 2, False)}=1)=1,\'''', "P2-03: note marks every flagged cell"),
    ("E59", "2.1", W, '''f'IF(in_protect_segment={xs(ps)},"OK",{rb(ps)})\'''', '''f'"OK"\'''',
     "P2-06: rebuild check on protect_segment never fires"),
    # ---- P21: the review's X09 as it was meant [v0.6.2, P21-02] ----
    ("E60", "P21", W, '''IF({LVf("yield_shift_pts_in")}<>"",{LVf("yield_shift_pts_in")},\'''',
     '''IF({LVf("yield_shift_pts_in")}<>"",{LVf("yield_shift_pts_in")}+{LVf("yield_shift_pts")},\'''',
     "In-state override adds to the global shift instead of replacing it (review X09)"),
    ("E61", "P21", W, '''IF({LVf("yield_shift_pts_out")}<>"",{LVf("yield_shift_pts_out")},\'''',
     '''IF({LVf("yield_shift_pts_out")}<>"",{LVf("yield_shift_pts_out")}+{LVf("yield_shift_pts")},\'''',
     "Out-of-state override adds to the global shift"),
    ("E62", "P21", W, '''=1,{LVf("yield_shift_pts_segment")},\'''',
     '''=1,{LVf("yield_shift_pts_segment")}+{LVf("yield_shift_pts")},\'''',
     "Segment override adds to the global shift"),
    # ---- P3: Phase 3 (reproduce builds, integer branches, mode switch) ----------------------------------------
    ("E63", "P3", W, '''                yf = (f'IF(in_mode="Reproduce",{ref("Reproduce", self.r0p + i, self.pblock[s.name] + 2)},{yf})')''',
     "                yf = yf", "Ledger yield ignores the Reproduce sheet in mode Reproduce"),
    ("E64", "P3", W, """            tf = f'IF(in_mode="Reproduce",{ref("Reproduce", self.prow["tuition"], self.pblock[s.name])},{tf})'""",
     "            tf = tf", "Ledger tuition ignores the loaded tuition in mode Reproduce"),
    ("E65", "P3", W, """f'IF(in_integer_admits=1,ROUND({B("apps")}*{B("rate")},0),'""",
     """f'IF(in_integer_admits=1,({B("apps")}*{B("rate")}),'""", "Integer admits not rounded"),
    ("E66", "P3", W, """f'IF(in_integer_enrolled=1,ROUND({B("mu")},0),{B("mu")})'""",
     """f'IF(in_integer_enrolled=1,{B("mu")},{B("mu")})'""", "Integer enrolled not rounded"),
    ("E67", "P3", W, """f'IF(in_integer_admits=1,ROUND({a1f}*{B("rate")},0),{a1f}*{B("rate")})'""",
     """f'IF(in_integer_admits=1,({a1f}*{B("rate")}),{a1f}*{B("rate")})'""", "Admits at pool multiplier 1 not rounded"),
    ("E68", "P3", W, "                nbad = int(sum(int(pyc(run.lcs[s][k]).sum()) for s in S))",
     "                nbad = 0", "Checks expect OK for the integrity counts whatever the ledger holds"),
    ("E69", "P3", W, '''-{self.PR(s.name, 'award')})^2>0.25)*1)"''',
     '''-{self.PR(s.name, 'rate')})^2>0.25)*1)"''', "Reproduce check compares awards with admit rates"),
    ("E70", "P3", W, '''f'IF(in_mode="Live","OK",{xs(labels.MODE_LIVE_BUILD)})', "OK")''',
     '''f'IF(in_mode="Reproduce","OK",{xs(labels.MODE_LIVE_BUILD)})', "OK")''', "Live-build mode check inverted"),
    ("E71", "P3", W, '''self.val("Reproduce", r, c0 + 2, float(ld["yield"][i]), "in_r4")''',
     '''self.val("Reproduce", r, c0 + 2, float(ld["yield"][i]) + 0.01, "in_r4")''', "Reproduce sheet shows other yields than the ledger's"),
    # ---- P3.1: Phase 3 completion (DECISIONS Nov 18; R3-3, R3-4) --------------------------------------------
    ("E72", "P3.1", W, """        return f'IF((in_mode="Reproduce")*(in_round_apps_after_pool=1)=1,ROUND({f},0),{f})'""",
     """        return f'IF((in_mode="Reproduce")*(in_round_apps_after_pool=1)=1,({f}),{f})'""",
     "Ledger applications not rounded in mode Reproduce"),
    ("E73", "P3.1", W, """                         "" if unknown is not None and unknown[i, j] else apps, "n0")""",
     """                         apps, "n0")""", "History shows unknown applications as 0"),
    ("E74", "P3.1", W, """IF(({C}-{A})^2<1E-12,""", """IF(({C}-{A})^2>1E-12,""", "509 count verdict inverted"),
    ("E75", "P3.1", W, """                f'IF({given}=0,{xs(labels.ABA509_NOT_RUN.format(y=y))},""",
     """                f'IF({given}<0,{xs(labels.ABA509_NOT_RUN.format(y=y))},""",
     "509 Checks row never reports 'not run'"),
    # ---- P2.2 (spec v0.6.3 section 0A) ----------------------------------------------------------------------
    ("E76", "P2.2", W, '    return f"1/(2*{f})"', '    return "0.5"', "Excel continuity correction 0.5"),
    ("E77", "P2.2", W, """f'IF({c("score_lo")}>={self.inp_list["pct_t"][j]},1,-1))')""",
     """f'IF({c("score_lo")}>{self.inp_list["pct_t"][j]},1,-1))')""", "Percentile sign: a cell at t counts below"),
    ("E78", "P2.2", W, '            return f"1-NORMSDIST((-{cr}-({q}*{gp}-(1-{q})*{gm}))/SQRT(MAX({vq},1E-300)))"',
     '            return f"1-NORMSDIST((-0.5-({q}*{gp}-(1-{q})*{gm}))/SQRT(MAX({vq},1E-300)))"',
     "Summary percentile probability uses 0.5"),
    ("E79", "P2.2", W, 'return f"{q}*SUMPRODUCT(({G}=1)*{E})-(1-{q})*SUMPRODUCT(({G}=-1)*{E})"',
     'return f"{q}*SUMPRODUCT(({G}=1)*{E})-{q}*SUMPRODUCT(({G}=-1)*{E})"', "Summary percentile margin weights"),
    ("E80", "P2.2", W, '(wrap(f"1-NORMSDIST(({CAP}+0.5-{cls})/SQRT(MAX({Vc},1E-300)))"), row_vals[2])]',
     '(wrap(f"1-NORMSDIST(({CAP}-0.5-{cls})/SQRT(MAX({Vc},1E-300)))"), row_vals[2])]',
     "Class-table P(class > cap) continuity correction"),
    ("E81", "P2.2", W, 'out.append((wrap(f"1-NORMSDIST((-{cr}-({q}*{gp}-(1-{q})*{gm}))/SQRT(MAX({vq},1E-300)))"),',
     'out.append((wrap(f"1-NORMSDIST((-0.5-({q}*{gp}-(1-{q})*{gm}))/SQRT(MAX({vq},1E-300)))"),',
     "Class-table percentile probability uses 0.5"),
    ("E82", "P2.2", W, '-2*in_shock_corr*{q}*(1-{q})"', '-2*{q}*(1-{q})"', "Pool-strip percentile ignores rho"),
    ("E83", "P2.2", W, """f'IF({P("hi", "M")}<>0,({self.LV(s, "class_target")}-{P("lo", "M")})/'""",
     """f'IF({P("hi", "M")}<>0,({self.LV(s, "class_cap")}-{P("lo", "M")})/'""",
     "Break-even pool multiplier aims at the cap"),
    ("E84", "P2.2", W, """f'IF({ehi}<>0,-{elo}/{ehi},"")'""", """f'IF({ehi}<>0,{elo}/{ehi},"")'""",
     "Break-even percentile multiplier sign"),
    ("E85", "P2.2", W, """/2<1+in_pool_ytd_growth)*1))'""", """/2<in_pool_ytd_growth)*1))'""",
     "Growth marker compares with growth, not 1 + growth"),
    ("E86", "P2.2", W, "IF({self.pool_nearest}={gi + 1},", "IF({self.pool_nearest}={gi},",
     "Growth marker one row off"),
    ("E87", "P2.2", W, """IF(in_ntr_goal_basis="all_jd",in_ntr_target-in_continuing_ntr_usd,'""",
     """IF(in_ntr_goal_basis="all_jd",in_ntr_target,'""", "Effective target ignores continuing revenue"),
    ("E88", "P2.2", W, """f = (f'IF(in_ntr_target_eff="","",1-NORMSDIST((in_ntr_target_eff-""",
     """f = (f'IF(in_ntr_target_eff="","",1-NORMSDIST((in_ntr_target-""",
     "Summary P(ntr_y1) reads ntr_target"),
    ("E89", "P2.2", W, """                   (f'IF(in_ntr_target_eff="","",1-NORMSDIST((in_ntr_target_eff-""",
     """                   (f'IF(in_ntr_target_eff="","",1-NORMSDIST((in_ntr_target-""",
     "Yield-strip P(ntr_y1) reads ntr_target"),
    ("E90", "P2.2", W, """IF(SUMPRODUCT({W},{A})<>0,(in_ntr_target_eff-'""", """IF(SUMPRODUCT({W},{A})<>0,(in_ntr_target-'""",
     "Yield-strip NTR break-even reads ntr_target"),
    ("E91", "P2.2", W, """            f = f'IF({usd}="",{f}*(1+{inc}/100),{usd}/in_tuition_base)'""",
     """            f = f'{f}*(1+{inc}/100)'""", "Levers tuition ignores tuition_by_year_usd"),
    ("E92", "P2.2", W, """f'IF(SUMPRODUCT((in_score_bands={tr})*1)>0,"OK","t "&{tr}&" is not a band lower bound")', "OK")""",
     """'"OK"', "OK")""", "Band-bound check never fires"),
    ("E93", "P2.2", W, """f'IF(in_score_floor={fl:g},"OK",{rb(f"{fl:g}")})', "OK")""", """'"OK"', "OK")""",
     "Floor rebuild check never fires"),
    ("E94", "P2.2", W, """f'IF({qr}={q!r},"OK",{rb(f"{q:g}")})', "OK")""", """'"OK"', "OK")""",
     "q rebuild check never fires"),
    ("E95", "P2.2", W, """nrf = f'IF(in_mode="Reproduce",ROUND(in_need_total/in_need_reference_class,0),{nrf})'""",
     """nrf = f'IF(in_mode="Reproduce",in_need_total/in_need_reference_class,{nrf})'""",
     "Reproduce need rate not rounded (B5)"),
    ("E96", "P2.2", W, """f'IF(in_mode="Reproduce",IF({nt}="",0,{nt}-in_need_total),0)'""", """'0'""",
     "Reproduce need departure dropped (B5)"),
    ("E97", "P2.2", W, """        aid = f"({merit}+{d['NR']}*{cls}+{d['K']})\"""",
     """        aid = f"({merit}+{d['NR']}*{cls}+{d['SPEC']})\"""", "Aid leaves out the need departure"),
    ("E98", "P2.2", W, '*{E})+{U})/{N}<={q},{b},-1)"', '*{E})+{U})/{N}>={q},{b},-1)"',
     "Spread band comparison reversed"),
    ("E99", "P2.2", W, """{c}&" to below "&INDEX(in_score_bands,{k}-1))))')""",
     """{c}&" to below "&INDEX(in_score_bands,{k}+1))))')""", "Spread band text names the band below"),
    ("E100", "P2.2", W, "return f'IF({gm}<{risk.PCT_APPROX_BELOW},", "return f'IF({gm}>{risk.PCT_APPROX_BELOW},",
     "Approximation flag reversed"),
    ("E101", "P2.2", W, """in_continuing_ntr_usd+{gross}-{aid},"")'""", """{gross}-{aid},"")'""",
     "Projected JD net tuition leaves out continuing revenue"),
    ("E102", "P2.2", W, '            SP = self.g("middle", s)["K"]', '            SP = "0"',
     "Tuition what-if leaves out specialty"),
    ("E103", "P2.2", W, """(f"{Wm}-{self.g('middle', s)['K']}", row["ntr_mean"])""", """(f"{Wm}", row["ntr_mean"])""",
     "Pool-strip NTR mean leaves out specialty"),
    ("E104", "P2.2", W, """            nrf = f'IF(in_mode="Reproduce",""", """            nrf = f'IF(in_mode="Live",""",
     "Reproduce need rule behind the wrong mode"),
]

# Survivors accepted because they cannot change any result on valid input: id -> reason. Empty unless a run shows
# a survivor that meets that bar.
EQUIVALENT = {}


def _copy_tree(dst):
    """Copy the prototype, everything except output/ and caches [v0.6.2, P2-02]: requirements.lock feeds the build id,
    so a partial copy fails test 3's two-builds test in every run."""
    ign = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc", ".DS_Store")
    for name in os.listdir(ROOT):
        if name in ("output", "__pycache__", ".pytest_cache", ".DS_Store"):
            continue
        s, d = os.path.join(ROOT, name), os.path.join(dst, name)
        if os.path.isdir(s):
            shutil.copytree(s, d, ignore=ign)
        else:
            shutil.copy2(s, d)


def _test_files(excel=False):
    if excel:
        return [f"tests/{n}" for n in EXCEL_TESTS]
    names = sorted(f for f in os.listdir(os.path.join(ROOT, "tests")) if f.startswith("test_") and f.endswith(".py"))
    return [f"tests/{n}" for n in names if n not in SLOW_LAST] + [f"tests/{n}" for n in SLOW_LAST if n in names]


def _env(excel=False, count_file=None):
    # Python mode sets SW_SKIP_EXCEL: the workbook tests (3, 8, 9, 10, 18) compare Excel with Python, so any Python
    # mutant would fail them; that mode measures the Python tests only. Excel mode runs the workbook tests.
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               VECLIB_MAXIMUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
    env.pop("SW_SKIP_EXCEL", None)
    if not excel:
        env["SW_SKIP_EXCEL"] = "1"
    if count_file:
        env["SW_COLLECT_COUNT_FILE"] = count_file
    return env


def _first_failure(stdout):
    for ln in stdout.splitlines():
        if ln.startswith(("FAILED", "ERROR")):
            return ln
    return ""


def _test_id(caught_by):
    """'FAILED tests/x.py::test_y - msg' -> 'tests/x.py::test_y'."""
    s = caught_by.split(" ", 1)[1] if " " in caught_by else caught_by
    return s.split(" - ", 1)[0].strip()


def _run_suite(work, excel, timeout, stop_first):
    count_file = os.path.join(work, "collected.txt")
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *(["-x"] if stop_first else []),
           *_test_files(excel), *[a for d in DESELECT for a in ("--deselect", d)]]
    try:
        r = subprocess.run(cmd, cwd=work, env=_env(excel, count_file), capture_output=True, text=True,
                           timeout=timeout)
        code, out = r.returncode, r.stdout
    except subprocess.TimeoutExpired:
        code, out = "timeout", ""
    collected = None
    if os.path.exists(count_file):
        with open(count_file) as f:
            collected = int(f.read().strip() or -1)
    return code, out, collected


def run_one(m, timeout, excel, base_count):
    mid, src, path, old, new, desc = m
    work = tempfile.mkdtemp(prefix=f"sw_mut_{mid}_")
    try:
        _copy_tree(work)
        f = os.path.join(work, path)
        text = open(f).read()
        n = text.count(old)
        if n != 1:
            return {"id": mid, "source": src, "file": path, "description": desc, "status": "not applied",
                    "detail": f"pattern found {n} times"}
        with open(f, "w") as fh:
            fh.write(text.replace(old, new))
        t0 = time.time()
        code, out, collected = _run_suite(work, excel, timeout, stop_first=True)
        secs = round(time.time() - t0, 1)
        if collected != base_count:
            status = "count mismatch"
        elif code == 0:
            status = "equivalent" if mid in EQUIVALENT else "survived"
        else:
            status = "caught"
        return {"id": mid, "source": src, "file": path, "description": desc, "status": status, "seconds": secs,
                "collected": collected,
                "caught_by": _first_failure(out) if code not in (0, "timeout") else ("timeout" if code == "timeout"
                                                                                     else ""),
                "reason": EQUIVALENT.get(mid, "")}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def baseline(timeout, excel):
    """The unmutated suite in a scratch copy made the same way as the mutant copies. Returns (ok, summary, count)."""
    work = tempfile.mkdtemp(prefix="sw_mut_base_")
    try:
        _copy_tree(work)
        code, out, collected = _run_suite(work, excel, timeout, stop_first=False)
        line = out.strip().splitlines()[-1] if out.strip() else ""
        return code == 0, line, collected, _first_failure(out)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--only", default="", help="comma-separated mutant IDs")
    ap.add_argument("--timeout", type=int, default=900, help="seconds per suite run")
    ap.add_argument("--excel", action="store_true",
                    help="run the Excel-formula mutants (sw/workbook.py) against tests 3, 6, 8, 9 and 18 in "
                         "LibreOffice")
    ap.add_argument("--deselect", action="append", default=[],
                    help="pytest node-id prefix to leave out of every run, baseline included (repeatable); for "
                         "example the reproduce pass-criterion tests while they report known mismatches")
    args = ap.parse_args()
    DESELECT.extend(args.deselect)

    pool = EXCEL_MUTANTS if args.excel else MUTANTS
    ids = [m[0] for m in MUTANTS + EXCEL_MUTANTS]
    assert len(ids) == len(set(ids)), "duplicate mutant IDs"
    chosen = pool
    if args.only:
        want = set(args.only.split(","))
        unknown = want - {m[0] for m in pool}
        if unknown:
            sys.exit(f"unknown mutant IDs for this mode: {sorted(unknown)}")
        chosen = [m for m in pool if m[0] in want]

    # Baseline [v0.6.2, P2-02]: always run, in a copy made like the mutant copies; its collected-test count is the
    # count every mutant run must match.
    ok, line, base_count, fail = baseline(args.timeout, args.excel)
    print(f"unmutated suite ({'Excel' if args.excel else 'Python'} mode): {line}; {base_count} tests collected")
    if not ok:
        sys.exit(f"the unmutated suite fails in the scratch copy ({fail}); fix it before running the mutation check")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        results = list(ex.map(lambda m: run_one(m, args.timeout, args.excel, base_count), chosen))
    wall = round(time.time() - t0, 1)

    print(f"\n{'ID':<5} {'src':<4} {'status':<14} {'sec':>6}  description / caught by")
    for r in results:
        extra = r.get("reason") or r.get("caught_by") or r.get("detail", "")
        if r["status"] == "count mismatch":
            extra = f"collected {r.get('collected')} tests, baseline {base_count}"
        print(f"{r['id']:<5} {r['source']:<4} {r['status']:<14} {r.get('seconds', 0):>6}  {r['description']}"
              + (f"\n{'':<32}{extra}" if extra else ""))
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"\n{len(results)} mutants: " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
          + f" ({wall} s, {args.jobs} jobs)")

    # Which tests catch the mutants; warn when one test accounts for most catches [v0.6.2, P2-02].
    by_test = {}
    for r in results:
        if r["status"] == "caught" and r["caught_by"] not in ("", "timeout"):
            by_test[_test_id(r["caught_by"])] = by_test.get(_test_id(r["caught_by"]), 0) + 1
    caught = sum(by_test.values())
    warning = ""
    if caught:
        top, top_n = max(by_test.items(), key=lambda kv: kv[1])
        print(f"catching tests: {len(by_test)}; most catches: {top} ({top_n} of {caught})")
        if caught >= 5 and top_n > caught / 2:
            warning = (f"WARNING: one test accounts for {top_n} of {caught} catches ({top}). Check that it tests the "
                       "mutated logic rather than failing for an unrelated reason.")
            print(warning)

    out_dir = os.path.join(ROOT, "output", "mutation")
    os.makedirs(out_dir, exist_ok=True)
    name = "report_excel.json" if args.excel else "report.json"
    with open(os.path.join(out_dir, name), "w") as f:
        json.dump({"mode": "excel" if args.excel else "python", "baseline": line, "baseline_collected": base_count,
                   "deselected": DESELECT, "fixture": os.environ.get("YA_FIXTURE_PATH") is not None,
                   "counts": counts, "catches_by_test": by_test, "warning": warning, "wall_seconds": wall,
                   "jobs": args.jobs, "results": results, "equivalent": EQUIVALENT}, f, indent=1)
    bad = [r for r in results if r["status"] in ("survived", "not applied", "count mismatch")]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
