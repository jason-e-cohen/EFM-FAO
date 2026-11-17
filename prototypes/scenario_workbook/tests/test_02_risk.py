"""Test 2: on a toy grid with expected class at least 25, the closed forms against the exact convolution
(tolerance 0.01; the class-band probability is asserted only where the expected class is at least 50 and reported
below that [v0.6.1, OP-3]) and the simulation against the exact convolution (tolerance 0.005, 200,000 draws)."""
import json
import os

import numpy as np
import pytest

from sw import ledger as L, mc, response, risk
from toy import toy_cells, toy_cfg, toy_override

S_SD = 0.10
DRAWS = 200_000
BAND_MIN_CLASS = 50          # band probability asserted at expected class 50 or more [v0.6.1, OP-3]
BAL_A = np.array([150.0, 150.0, 150.0, 150.0])      # admits at 170, 166, 165, 161
BAL_Y = np.array([0.30, 0.30, 0.28, 0.28])


@pytest.fixture(scope="module")
def grid():
    cfg = toy_cfg()
    cells = toy_cells(cfg)
    base = response.base_yield(cells, cfg, base_override=toy_override())
    lc = L.evaluate(cells, cfg, L.baseline(cells, cfg), base, "middle")
    assert lc.mu.sum() >= 25
    assert np.allclose(lc.admits, np.round(lc.admits))
    return cfg, cells, lc


def _record(report_dir, name, rows):
    with open(os.path.join(report_dir, f"{name}.json"), "w") as f:
        json.dump(rows, f, indent=1)


def test_closed_vs_exact_vs_sim(grid, report_dir):
    cfg, cells, lc = grid
    A, y = lc.admits, lc.yld
    M = float((A * y).sum())
    rows = []
    sims = mc.simulate(A, y, S_SD, {"class": np.ones(len(A))}, DRAWS, seed=11)
    cls = sims["class"]
    for cap in (int(M) - 5, int(M), int(M) + 5):
        cf = risk.cf_class(A, y, S_SD, cap, cap, 3)
        ex = risk.exact_class(A, y, S_SD, cap, cap, 3)
        sim_over = float((cls > cap).mean())
        sim_band = float((np.abs(cls - cap) <= 3).mean())
        rows.append({"what": f"class>cap {cap}", "closed": cf["p_class_over_cap"], "exact": ex["p_class_over_cap"],
                     "sim": sim_over})
        # The band probability's closed form is asserted only at expected class 50 or more and reported below that
        # [v0.6.1, OP-3]: at about 31 the normal form misses the exact value by up to 0.012 (shock skew).
        rows.append({"what": f"class within 3 of {cap}", "closed": cf["p_class_in_band"],
                     "exact": ex["p_class_in_band"], "sim": sim_band, "assert_closed": M >= BAND_MIN_CLASS})

    # Same grid with admits doubled (expected class about 61): band probability at targets M - 8 to M + 8.
    A2 = 2 * A
    M2 = float((A2 * y).sum())
    assert M2 >= BAND_MIN_CLASS
    for off in range(-8, 9, 2):
        t = round(M2) + off
        cf = risk.cf_class(A2, y, S_SD, t, t, 3)
        ex = risk.exact_class(A2, y, S_SD, t, t, 3)
        rows.append({"what": f"doubled grid: class within 3 of {t}", "closed": cf["p_class_in_band"],
                     "exact": ex["p_class_in_band"], "sim": None, "assert_closed": M2 >= BAND_MIN_CLASS})

    # Balanced median grid: the toy grid has no cell between 161 and 170, so its score medians sit in the tail.
    # Four cells at 170, 166, 165, 161 put P(median at 166) near 0.65, where the rho 0.5 shock structure matters
    # (independent shocks would move it by about 0.025) [Review R-04, K9].
    Ab, yb = BAL_A, BAL_Y
    gb = np.array([1, 1, -1, -1])
    for rho in (1.0, 0.5):
        cf = risk.cf_median(Ab, yb, gb, S_SD, rho)["p"]
        ex = risk.exact_median(Ab, yb, gb, S_SD, rho)
        groups = None if rho >= 1 else (gb > 0)
        sm = mc.simulate(Ab, yb, S_SD, {"m": gb}, DRAWS, seed=14, groups=groups, rho=rho)["m"]
        rows.append({"what": f"balanced median rho {rho}", "closed": cf, "exact": ex, "sim": float((sm >= 0).mean())})

    for meas, t in (("score", 166), ("score", 165), ("gpa", 3.83)):
        g = risk.median_signs(cells, cfg, meas, t)
        for rho in (1.0, 0.5):
            cf = risk.cf_median(A, y, g, S_SD, rho)["p"]
            ex = risk.exact_median(A, y, g, S_SD, rho)
            groups = None if rho >= 1 else (g > 0)
            sm = mc.simulate(A, y, S_SD, {"m": g}, DRAWS, seed=12, groups=groups, rho=rho)["m"]
            rows.append({"what": f"median {meas} {t} rho {rho}", "closed": cf, "exact": ex,
                         "sim": float((sm >= 0).mean())})

    w = lc.w
    n = risk.cf_ntr(A, y, w, S_SD, 0.0, None)
    sn = mc.simulate(A, y, S_SD, {"ntr": w}, DRAWS, seed=13)["ntr"]
    for z in (-1.0, 0.0, 1.0):
        target = round((n["ntr_mean"] + z * n["ntr_sd"]) / 1000) * 1000
        cf = risk.cf_ntr(A, y, w, S_SD, 0.0, target)["p_ntr_y1_ge_target"]
        ex = risk.exact_ntr(A, y, w, S_SD, 0.0, target, unit=1000)
        rows.append({"what": f"ntr >= {target:.0f}", "closed": cf, "exact": ex,
                     "sim": float((sn >= target - 1e-6).mean())})

    _record(report_dir, "test02_risk", rows)
    for r in rows:
        if r.get("assert_closed", True):
            assert abs(r["closed"] - r["exact"]) <= 0.01, r
        if r["sim"] is not None:
            assert abs(r["sim"] - r["exact"]) <= 0.005, r


def test_exact_mean_and_moments(grid):
    """The exact distribution reproduces the expected class and the s^2 M^2 variance up to the stated
    overstatement s^2 sum A y^2 (section 5)."""
    cfg, cells, lc = grid
    A, y = lc.admits, lc.yld
    vals, pmf = risk.exact_pmf(A, y, np.ones(len(A), int), S_SD)
    mean = (vals * pmf).sum()
    var = ((vals - mean) ** 2 * pmf).sum()
    M = (A * y).sum()
    V_cf = (A * y * (1 - y)).sum() + S_SD ** 2 * M ** 2
    assert mean == pytest.approx(M, abs=1e-6)
    assert V_cf - var == pytest.approx(S_SD ** 2 * (A * y * y).sum(), rel=1e-3)


def test_rho_one_reduces(grid):
    """At rho = 1, V_m equals sum v + s^2 m^2."""
    cfg, cells, lc = grid
    A, y = lc.admits, lc.yld
    g = risk.median_signs(cells, cfg, "score", 166)
    r = risk.cf_median(A, y, g, S_SD, 1.0)
    v = (A * y * (1 - y))[g != 0].sum()
    assert r["v_m"] == pytest.approx(v + S_SD ** 2 * r["margin_expected"] ** 2, rel=1e-12)


def test_fractional_admits_exact_matches_sim():
    """Non-integer admits: Binomial(floor A) + Bernoulli(frac A x p) in both the exact and simulated models."""
    A = np.array([10.4, 7.7, 22.5, 3.2])
    y = np.array([0.3, 0.2, 0.25, 0.5])
    vals, pmf = risk.exact_pmf(A, y, np.ones(4, int), S_SD)
    assert (vals * pmf).sum() == pytest.approx((A * y).sum(), abs=1e-9)
    sim = mc.simulate(A, y, S_SD, {"c": np.ones(4)}, DRAWS, seed=3)["c"]
    for k in (8, 10, 12):
        assert abs(float((sim >= k).mean()) - float(pmf[vals >= k].sum())) <= 0.005
