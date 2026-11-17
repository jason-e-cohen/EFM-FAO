"""Test 20: mutation check [v0.6.1] (spec section 11). Run on demand; pytest does not collect this file.

Applies each mutant below, one at a time, to a scratch copy of sw/, tests/ and config/, runs the full suite there
(stopping at the first failure, slow tests last) and reports which mutants survive. Acceptance: no survivor except
those listed in EQUIVALENT, each with the reason it cannot change any result on valid input.

    cd prototypes/scenario_workbook
    ../../.venv/bin/python tests/mutation_check.py
    ../../.venv/bin/python tests/mutation_check.py --jobs 6 --only L8,P3

Mutant sources:
  A    the 24 survivors in Review_Phase1_Build.md Appendix A (their IDs)
  A+   the 46 mutants Appendix A lists as caught, reconstructed from its one-line descriptions (the review's own
       mutant code was not saved), IDs X01 to X45
  1.1  mutants of the Phase 1.1 changes and of the choices recorded in spec v0.6.1 (R-05, R-07, R-08, OP-1, OP-3,
       OP-5), IDs N01 to N13
Exit status: 0 when every survivor is in EQUIVALENT and every mutant applied; 1 otherwise. Report JSON:
output/mutation/report.json.
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
     "        if protect and below and seg[i]:",
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
     "        ntr = float((e * (T - award)).sum()) - need - lc.specialty",
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
     "    return unit * math.floor(x / unit + 0.5)",
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
     "        below = (lc.award_base < lc.tuition - 1e-6) & (e > 0)",
     "        below = (lc.award_base < lc.tuition - 1e-6) & (lc.award > 0) & (e > 0)",
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
     "        below = (lc.award_base < lc.tuition - 1e-6) & (e > 0)",
     "        below = (lc.award < lc.tuition - 1e-6) & (e > 0)",
     "P1.1-4 reverted: example-award membership judged on the award after the incentive"),
    ("N15", "1.1", "sw/strip.py",
     "        below = (lc.award_base < lc.tuition - 1e-6) & (e > 0)",
     "        below = (lc.award_base <= lc.tuition) & (e > 0)",
     "P1.1-4: flagged (full-tuition) cells included in the example award"),
    ("N16", "1.1", "sw/ledger.py",
     "    return np.asarray(scen.full_tuition, bool) & (np.asarray(scen.award_usd, float) != np.asarray(ref, float))",
     "    return np.asarray(scen.full_tuition, bool)",
     "P1.1-1: every flagged cell listed as a conflict"),
    ("N17", "1.1", "sw/ledger.py",
     "        ref = parent.award_usd",
     "        ref = cells.award[:, cells.col(cfg[\"cycle\"][\"base_cycle\"])]",
     "P1.1-1: child conflicts judged against the latest-cohort award, not the parent's"),
]

# Survivors accepted because they cannot change any result on valid input: id -> reason. Empty unless a run shows
# a survivor that meets that bar.
EQUIVALENT = {}


def _copy_tree(dst):
    ign = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc", "mutation_check.py")
    for d in ("sw", "tests", "config"):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(dst, d), ignore=ign)


def _test_files():
    names = sorted(f for f in os.listdir(os.path.join(ROOT, "tests")) if f.startswith("test_") and f.endswith(".py"))
    return [f"tests/{n}" for n in names if n not in SLOW_LAST] + [f"tests/{n}" for n in SLOW_LAST if n in names]


def _env():
    # SW_SKIP_EXCEL: the workbook tests (3, 8, 9, 10, 18) compare Excel with Python, so any Python mutant would fail
    # them; the check measures the Python tests only.
    return dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                VECLIB_MAXIMUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1", SW_SKIP_EXCEL="1")


def _first_failure(stdout):
    for ln in stdout.splitlines():
        if ln.startswith(("FAILED", "ERROR")):
            return ln
    return ""


def run_one(m, timeout):
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
        cmd = [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", *_test_files()]
        t0 = time.time()
        try:
            r = subprocess.run(cmd, cwd=work, env=_env(), capture_output=True, text=True, timeout=timeout)
            code, out = r.returncode, r.stdout
        except subprocess.TimeoutExpired:
            code, out = "timeout", ""
        secs = round(time.time() - t0, 1)
        if code == 0:
            status = "equivalent" if mid in EQUIVALENT else "survived"
        else:
            status = "caught"
        return {"id": mid, "source": src, "file": path, "description": desc, "status": status, "seconds": secs,
                "caught_by": _first_failure(out) if code not in (0, "timeout") else ("timeout" if code == "timeout"
                                                                                     else ""),
                "reason": EQUIVALENT.get(mid, "")}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def baseline_ok(timeout):
    work = tempfile.mkdtemp(prefix="sw_mut_base_")
    try:
        _copy_tree(work)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", SW_SKIP_EXCEL="1")
        cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *_test_files()]
        r = subprocess.run(cmd, cwd=work, env=env, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--only", default="", help="comma-separated mutant IDs")
    ap.add_argument("--timeout", type=int, default=900, help="seconds per suite run")
    ap.add_argument("--skip-baseline", action="store_true")
    args = ap.parse_args()

    ids = [m[0] for m in MUTANTS]
    assert len(ids) == len(set(ids)), "duplicate mutant IDs"
    chosen = MUTANTS
    if args.only:
        want = set(args.only.split(","))
        unknown = want - set(ids)
        if unknown:
            sys.exit(f"unknown mutant IDs: {sorted(unknown)}")
        chosen = [m for m in MUTANTS if m[0] in want]

    if not args.skip_baseline:
        ok, line = baseline_ok(args.timeout)
        print(f"unmutated suite: {line}")
        if not ok:
            sys.exit("the unmutated suite fails; fix it before running the mutation check")

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        results = list(ex.map(lambda m: run_one(m, args.timeout), chosen))
    wall = round(time.time() - t0, 1)

    print(f"\n{'ID':<5} {'src':<4} {'status':<12} {'sec':>6}  description / caught by")
    for r in results:
        extra = r.get("reason") or r.get("caught_by") or r.get("detail", "")
        print(f"{r['id']:<5} {r['source']:<4} {r['status']:<12} {r.get('seconds', 0):>6}  {r['description']}"
              + (f"\n{'':<30}{extra}" if extra else ""))
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"\n{len(results)} mutants: " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
          + f" ({wall} s, {args.jobs} jobs)")

    out_dir = os.path.join(ROOT, "output", "mutation")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "report.json"), "w") as f:
        json.dump({"counts": counts, "wall_seconds": wall, "jobs": args.jobs, "results": results,
                   "equivalent": EQUIVALENT}, f, indent=1)
    bad = [r for r in results if r["status"] in ("survived", "not applied")]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
