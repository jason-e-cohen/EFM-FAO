"""Risk functions (spec section 5): closed forms, and exact distributions for validation and the segment probability.

Model: independent binomial enrollment by cell given admits and yield, plus a common multiplicative year shock
e ~ Normal(1, s); a cell's yield in a year is clip(e x y_c, 0, 1). For the median sensitivity, cells at or above and
below the threshold get shocks with correlation rho.

Non-integer admits (integer_admits false) enter the exact and simulated models as Binomial(floor(A), p) plus
Bernoulli(frac(A) x p), which keeps the expected count A x p exactly.
"""
import math

import numpy as np
from scipy.special import ndtr as Phi
from scipy.stats import binom

from . import labels

Z90 = 1.645


# ---------------------------------------------------------------------------------------------------------------
# Closed forms on arrays (used by the ledger outputs, the strips and the tests)

def cf_class(A, y, s, cap, target, band):
    mu = A * y
    M = float(mu.sum())
    V = float((A * y * (1 - y)).sum() + s * s * M * M)
    sd = math.sqrt(max(V, 1e-300))
    return {
        "class_mean": M,
        "class_sd": math.sqrt(max(V, 0.0)),
        "class_lo90": max(0.0, M - Z90 * math.sqrt(max(V, 0.0))),
        "class_hi90": M + Z90 * math.sqrt(max(V, 0.0)),
        "p_class_over_cap": float(1 - Phi((cap + 0.5 - M) / sd)),
        "p_class_in_band": float(Phi((target + band + 0.5 - M) / sd) - Phi((target - band - 0.5 - M) / sd)),
    }


def cf_median(A, y, g, s, rho):
    """Margin m = sum g mu; V_m = sum_{g != 0} v + s^2 (G+^2 + G-^2 - 2 rho G+ G-); P(margin >= 0)."""
    mu = A * y
    v = A * y * (1 - y)
    gp = float(mu[g > 0].sum())
    gm = float(mu[g < 0].sum())
    m = gp - gm
    Vm = float(v[g != 0].sum() + s * s * (gp * gp + gm * gm - 2 * rho * gp * gm))
    p = float(1 - Phi((-0.5 - m) / math.sqrt(max(Vm, 1e-300))))
    return {"margin_expected": m, "g_plus": gp, "g_minus": gm, "v_m": Vm, "p": p}


def cf_ntr(A, y, w, s, specialty, target):
    mu = A * y
    v = A * y * (1 - y)
    sw = float((w * mu).sum())
    mean = sw - specialty
    Vn = float((w * w * v).sum() + s * s * sw * sw)
    sd = math.sqrt(max(Vn, 0.0))
    out = {"ntr_mean": mean, "ntr_sd": sd, "ntr_lo90": mean - Z90 * sd, "ntr_hi90": mean + Z90 * sd}
    if target is not None:
        out["p_ntr_y1_ge_target"] = float(1 - Phi((target - mean) / max(sd, 1e-300)))
    return out


def segment_normal(M, V, goal):
    """Excel form: 1 - Phi((goal - 0.5 - M_S) / sqrt(V_S))."""
    return float(1 - Phi((goal - 0.5 - M) / math.sqrt(max(V, 1e-300))))


# ---------------------------------------------------------------------------------------------------------------
# Ledger-facing functions (interface contract names)

def _s(lc):
    return float(lc.cfg["risk"]["common_shock_sd"])


def _shock_labels(lc):
    cfg = lc.cfg
    return [labels.shock_label(_s(lc))] if cfg["risk"]["shock_source"] == "illustrative" else []


def class_dist(lc):
    r = cf_class(lc.admits, lc.yld, _s(lc), lc.scenario.class_cap, lc.scenario.class_target, lc.cfg["class"]["band"])
    return {k: r[k] for k in ("class_mean", "class_sd", "class_lo90", "class_hi90")} | {"labels": _shock_labels(lc)}


def class_probs(lc):
    r = cf_class(lc.admits, lc.yld, _s(lc), lc.scenario.class_cap, lc.scenario.class_target, lc.cfg["class"]["band"])
    return {"p_class_over_cap": r["p_class_over_cap"], "p_class_in_band": r["p_class_in_band"],
            "labels": _shock_labels(lc)}


def median_signs(cells, cfg, measure, t):
    """g_c = +1 at or above t, -1 below, and 0 (excluded) or -1 (below) for unscored or blank-GPA cells."""
    unscored_g = 0.0 if cfg["unscored_in_median"] == "excluded" else -1.0
    if measure == "score":
        s = cells.score_lo
        with np.errstate(invalid="ignore"):
            g = np.where(np.isnan(s), unscored_g, np.where(s >= t, 1.0, -1.0))
    elif measure == "gpa":
        gc = cells.gpa_class
        g = np.where(gc == "hi", 1.0, np.where(gc == "lo", -1.0, unscored_g))
    else:
        raise ValueError(measure)
    return g


def median_targets(cfg):
    """(measure, threshold) pairs: each score median threshold, then the GPA threshold."""
    return [("score", t) for t in cfg["score"]["median_thresholds"]] + [("gpa", cfg["gpa"]["median_threshold"])]


def median(lc, measure, t):
    """Median at threshold t: margin (from enrolled), P(median holds) at the configured rho and at rho 0.5."""
    cfg = lc.cfg
    g = median_signs(lc.cells, cfg, measure, t)
    s = _s(lc)
    rho = float(cfg["risk"]["shock_corr_above_below"])
    r = cf_median(lc.admits, lc.yld, g, s, rho)
    r05 = cf_median(lc.admits, lc.yld, g, s, 0.5)
    excluded = g == 0
    return {
        "margin_t": float((g * lc.enrolled).sum()),
        "margin_expected": r["margin_expected"],
        "p_median_t": r["p"],
        "p_median_t_rho05": r05["p"],
        "unscored_count": float(lc.enrolled[excluded].sum()),
        "g_plus": r["g_plus"], "g_minus": r["g_minus"],
        "rho05_note": labels.RHO_SENSITIVITY,
        "labels": _shock_labels(lc),
    }


def ntr(lc, target=None):
    target = lc.cfg.get("ntr_target") if target is None else target
    r = cf_ntr(lc.admits, lc.yld, lc.w, _s(lc), lc.specialty, target)
    r["labels"] = _shock_labels(lc) + [labels.RESPONSE_LABEL]
    return r


# ---------------------------------------------------------------------------------------------------------------
# Exact distributions (convolution of cell binomials, mixed over the shock by Gauss-Hermite quadrature)

def _split(A):
    A = np.asarray(A, float)
    n = np.floor(A + 1e-9)
    f = A - n
    f[f < 1e-9] = 0.0
    return n.astype(int), f


def _cell_pmf(n, f, p):
    pmf = binom.pmf(np.arange(n + 1), n, p) if n > 0 else np.array([1.0])
    if f > 0:
        q = f * p
        pmf = np.convolve(pmf, [1 - q, q])
    return pmf


def _shock_nodes(s, rho, two_groups, nodes):
    x, wt = np.polynomial.hermite.hermgauss(nodes)
    z = math.sqrt(2.0) * x
    if not two_groups or rho >= 1.0:
        return [(1 + s * zi, 1 + s * zi, wi / math.sqrt(math.pi)) for zi, wi in zip(z, wt)]
    out = []
    c = math.sqrt(max(0.0, 1 - rho * rho))
    for zi, wi in zip(z, wt):
        for zj, wj in zip(z, wt):
            out.append((1 + s * zi, 1 + s * (rho * zi + c * zj), wi * wj / math.pi))
    return out


def exact_pmf(A, y, weights, s, groups=None, rho=1.0, nodes=20):
    """Distribution of S = sum_c weights_c X_c (integer weights). Returns (values, pmf).

    groups: boolean array; True cells take shock e1, False cells take e2 (correlation rho). None: one shock.
    """
    A = np.asarray(A, float)
    y = np.asarray(y, float)
    w = np.asarray(weights, int)
    n, f = _split(A)
    nmax = n + (f > 0)
    keep = (w != 0) & (nmax > 0)
    lo = int((np.minimum(w, 0) * nmax)[keep].sum())
    hi = int((np.maximum(w, 0) * nmax)[keep].sum())
    total = np.zeros(hi - lo + 1)
    grp = np.ones(len(A), dtype=bool) if groups is None else np.asarray(groups, bool)
    for e1, e2, wt in _shock_nodes(s, rho, groups is not None, nodes):
        dist = np.array([1.0])
        off = 0
        for c in np.flatnonzero(keep):
            e = e1 if grp[c] else e2
            p = min(1.0, max(0.0, e * y[c]))
            pmf = _cell_pmf(n[c], f[c], p)
            aw = abs(int(w[c]))
            spread = np.zeros(aw * (len(pmf) - 1) + 1)
            spread[::aw] = pmf
            if w[c] < 0:
                spread = spread[::-1]
                off += int(w[c]) * (len(pmf) - 1)
            dist = np.convolve(dist, spread)
        total[off - lo: off - lo + len(dist)] += wt * dist
    return np.arange(lo, hi + 1), total


def exact_class(A, y, s, cap, target, band, nodes=20):
    vals, pmf = exact_pmf(A, y, np.ones(len(A), int), s, nodes=nodes)
    return {
        "class_mean": float((vals * pmf).sum()),
        "p_class_over_cap": float(pmf[vals > cap].sum()),
        "p_class_in_band": float(pmf[(vals >= target - band) & (vals <= target + band)].sum()),
    }


def exact_median(A, y, g, s, rho, nodes=20):
    groups = None if rho >= 1.0 else (np.asarray(g) > 0)
    vals, pmf = exact_pmf(A, y, np.asarray(g, int), s, groups=groups, rho=rho, nodes=nodes)
    return float(pmf[vals >= 0].sum())


def exact_ntr(A, y, w, s, specialty, target, unit, nodes=20):
    """P(NTR >= target) with NTR = sum w X - specialty; w must be integer multiples of unit."""
    wu = np.asarray(w, float) / unit
    if not np.allclose(wu, np.round(wu)):
        raise ValueError("exact NTR needs weights that are integer multiples of unit")
    vals, pmf = exact_pmf(A, y, np.round(wu).astype(int), s, nodes=nodes)
    return float(pmf[vals * unit - specialty >= target - 1e-6].sum())


def segment_exact(lc, goal, nodes=20):
    """P(E_S >= goal), exact (section 3 segment block)."""
    m = lc.in_segment
    if not m.any():
        return labels.NO_SEGMENT_CELLS
    vals, pmf = exact_pmf(lc.admits[m], lc.yld[m], np.ones(int(m.sum()), int), _s(lc), nodes=nodes)
    return float(pmf[vals >= goal].sum())
