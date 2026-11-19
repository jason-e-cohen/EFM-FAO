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
from .config import ntr_target_effective, pct_lattice_n

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


def pct_targets(cfg):
    """(q, t) pairs of score.percentile_targets, in config order [v0.6.3, BM-1]."""
    return [(float(p["q"]), p["t"]) for p in cfg["score"]["percentile_targets"]]


def cf_pct(A, y, g, q, s, rho):
    """Percentile q at or above t [v0.6.3, BM-1; Review_Phase2_2_Plan.md section 2]. g: median signs (+1 at or above
    t, -1 below, 0 excluded). M_q = q G+ - (1 - q) G-; V_q = q^2 sum_above v + (1-q)^2 sum_below v + s^2 (q^2 G+^2 +
    (1-q)^2 G-^2 - 2 rho q (1-q) G+ G-); P = 1 - Phi((-1/(2n) - E[M_q]) / sqrt(V_q)) with q = m/n in lowest terms
    (half the lattice step of M_q). At q = 0.5 this equals cf_median's probability."""
    mu = A * y
    v = A * y * (1 - y)
    gp = float(mu[g > 0].sum())
    gm = float(mu[g < 0].sum())
    E = q * gp - (1 - q) * gm
    Vq = float(q * q * v[g > 0].sum() + (1 - q) * (1 - q) * v[g < 0].sum()
               + s * s * (q * q * gp * gp + (1 - q) * (1 - q) * gm * gm - 2 * rho * q * (1 - q) * gp * gm))
    corr = 1.0 / (2 * pct_lattice_n(q))
    p = float(1 - Phi((-corr - E) / math.sqrt(max(Vq, 1e-300))))
    return {"margin_expected": E, "g_plus": gp, "g_minus": gm, "v_q": Vq, "p": p, "correction": corr}


def pct(lc, q, t):
    """Percentile target (q, t): margin_q_t = q x N_scored - G- from enrolled (swaps at the same class size; the sum of
    g_c e_c with g = q at or above t and -(1 - q) below), P(percentile q at or above t) at the configured rho and at
    rho 0.5, the expected count below t and the "approximate" flag (fewer than PCT_APPROX_BELOW expected below t)."""
    cfg = lc.cfg
    g = median_signs(lc.cells, cfg, "score", t)
    s = _s(lc)
    rho = float(cfg["risk"]["shock_corr_above_below"])
    r = cf_pct(lc.admits, lc.yld, g, q, s, rho)
    r05 = cf_pct(lc.admits, lc.yld, g, q, s, 0.5)
    return {
        "margin_q_t": q * float(lc.enrolled[g > 0].sum()) - (1 - q) * float(lc.enrolled[g < 0].sum()),
        "margin_expected": r["margin_expected"],
        "p_pct_q_t": r["p"],
        "p_pct_q_t_rho05": r05["p"],
        "expected_below": r["g_minus"],
        "approximate": labels.PCT_APPROX_LABEL if r["g_minus"] < PCT_APPROX_BELOW else "",
        "labels": _shock_labels(lc),
    }


PCT_APPROX_BELOW = 20          # [v0.6.3, BM-1] "approximate" below 20 expected below t
SPREAD_QS = (0.25, 0.75)       # [v0.6.3, BM-1] spread bands


def pct_band(lc, q):
    """Spread readout [v0.6.3, BM-1]: the score band whose lower bound is the largest band bound t with share below t
    at most q (ratio of enrolled counts over enrollees with a score; unscored count below every t under
    unscored_in_median 'below'). Returns t, or None when no one is counted or no bound qualifies. "band, not a
    score"."""
    cells, cfg = lc.cells, lc.cfg
    e = lc.enrolled
    sc = cells.score_lo
    scored = ~np.isnan(sc)
    uns = float(e[~scored].sum()) if cfg["unscored_in_median"] == "below" else 0.0
    N = float(e[scored].sum()) + uns
    if N <= 0:
        return None
    best = None
    for b in sorted(float(x) for x in cfg["score"]["bands"]):
        below = float(e[scored & (sc < b)].sum()) + uns
        if below / N <= q:
            best = b
    return best


def ntr(lc, target=None):
    """NTR distribution and P(ntr_y1 >= target). The target defaults to the effective ntr_target: under ntr_goal_basis
    all_jd, ntr_target - continuing_ntr_usd [v0.6.3, BM-4]. An explicit target is used as given."""
    target = ntr_target_effective(lc.cfg) if target is None else target
    r = cf_ntr(lc.admits, lc.yld, lc.w, _s(lc), lc.ntr_const, target)
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


def exact_pct(A, y, g, q, s, rho, nodes=20):
    """P(percentile q at or above t), exact [Review_Phase2_2_Plan.md section 2]: with q = m/n in lowest terms, the event
    m G+ >= (n - m) G-. Given the shocks, G+ (cells with g > 0) and G- (g < 0) are independent sums of cell binomials,
    so the probability comes from their two one-dimensional distributions, mixed over 20-node Gauss-Hermite nodes
    (20 x 20 at rho below 1). q may be a list: the distributions are computed once per node for every q."""
    qs = list(q) if isinstance(q, (list, tuple, np.ndarray)) else [q]
    A = np.asarray(A, float)
    y = np.asarray(y, float)
    g = np.asarray(g)
    nn, f = _split(A)
    up, dn = np.flatnonzero(g > 0), np.flatnonzero(g < 0)
    mn = []
    for qq in qs:
        n_ = pct_lattice_n(qq)
        mn.append((int(round(qq * n_)), n_))
    cache = {}

    def pmf(idx, e, key):
        if key in cache:
            return cache[key]
        d = np.array([1.0])
        for c in idx:
            if nn[c] + (f[c] > 0) == 0:
                continue
            d = np.convolve(d, _cell_pmf(nn[c], f[c], min(1.0, max(0.0, e * y[c]))))
        cache[key] = d
        return d
    total = np.zeros(len(qs))
    for e1, e2, wt in _shock_nodes(s, rho, rho < 1.0, nodes):
        pp, pm = pmf(up, e1, ("+", e1)), pmf(dn, e2, ("-", e2))
        tail = np.concatenate([np.cumsum(pp[::-1])[::-1], [0.0]])     # tail[k] = P(G+ >= k)
        j = np.arange(len(pm))
        for i, (m_, n_) in enumerate(mn):
            k = np.minimum(-((-(n_ - m_) * j) // m_), len(pp))           # ceil((n - m) j / m), exact
            total[i] += wt * float((pm * tail[k]).sum())
    return [float(x) for x in total] if len(qs) > 1 or isinstance(q, (list, tuple, np.ndarray)) else float(total[0])


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
