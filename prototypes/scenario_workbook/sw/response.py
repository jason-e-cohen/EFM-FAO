"""Placeholder response, base yield and evidence labels (spec section 4).

Every output that depends on the placeholder slopes carries RESPONSE_LABEL. The pipeline replaces this module's
slopes and base yields later; the interface (y0 by case, a0, slopes, floor and cap per cell) stays.
"""
from dataclasses import dataclass

import numpy as np

from . import CASES
from . import labels


@dataclass
class ResponseBase:
    a0: np.ndarray                 # latest-cohort award per cell
    y0: dict                       # case -> base yield per cell, re-centered at a0
    slopes: dict                   # case -> yield points per $1,000
    floor: np.ndarray              # yield floor per cell (by score group)
    cap: np.ndarray                # yield cap per cell (by score group)
    ybar: np.ndarray
    abar: np.ndarray
    n: np.ndarray
    ypool: np.ndarray
    pool_level: np.ndarray         # which pool each cell used: "segment", "residency", "group", "all", "override"
    award_lo: np.ndarray           # observed award range over history cohorts with admits (nan if none)
    award_hi: np.ndarray
    source_label: str = labels.RESPONSE_LABEL


def score_group_upper(cells, cfg):
    """Upper score group: score_lo at or above score.pool_threshold. Unscored cells join the lower group."""
    s = cells.score_lo
    return np.where(np.isnan(s), False, s >= cfg["score"]["pool_threshold"])


def _pool_yields(cells, cfg, upper):
    """Admits-weighted pool yield per cell: (residency, segment, group) when that pool has enough admits, else
    (residency, group). Fallbacks beyond the spec, used only when a pool has no admits: (group), then all cells."""
    adm = cells.admits.sum(axis=1)
    enr = cells.enrolled.sum(axis=1)
    min_adm = cfg["pooling_min_admits"]
    keys = {
        "segment": list(zip(cells.residency, cells.segment, upper)),
        "residency": list(zip(cells.residency, upper)),
        "group": list(upper),
        "all": [0] * cells.n,
    }
    sums = {}
    for lvl, ks in keys.items():
        d = {}
        for i, k in enumerate(ks):
            a, e = d.get(k, (0.0, 0.0))
            d[k] = (a + adm[i], e + enr[i])
        sums[lvl] = d
    ypool = np.zeros(cells.n)
    level = np.empty(cells.n, dtype=object)
    for i in range(cells.n):
        a, e = sums["segment"][keys["segment"][i]]
        if a >= min_adm:
            ypool[i], level[i] = e / a, "segment"
            continue
        for lvl in ("residency", "group", "all"):
            a, e = sums[lvl][keys[lvl][i]]
            if a > 0:
                ypool[i], level[i] = e / a, lvl
                break
        else:
            raise ValueError("no admits in any history cohort; base yield cannot be pooled")
    return ypool, level


def base_yield(cells, cfg, base_override=None):
    """Base yield by partial pooling, re-centered at the latest award (spec section 4; [v0.6, B4-5, B1-15]).

    y0_ck = (n_c (ybar_c + (b_k/100)(a0_c - abar_c)/1000) + k ypool_c) / (n_c + k); a cell with no admits takes ypool_c.

    base_override (test only): mapping cell_id -> ({case: y0}, a0). Cells in the mapping skip pooling. Production
    code never sets it.
    """
    upper = score_group_upper(cells, cfg)
    j = cells.col(cfg["cycle"]["base_cycle"])
    a0 = cells.award[:, j].astype(float).copy()
    adm = cells.admits
    n = adm.sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        ybar = np.where(n > 0, cells.enrolled.sum(axis=1) / n, np.nan)
        abar = np.where(n > 0, (adm * cells.award).sum(axis=1) / n, np.nan)
    ypool, level = _pool_yields(cells, cfg, upper)
    k = float(cfg["pooling_k"])
    slopes = {c: float(cfg["risk"]["sensitivity_slopes"][c]) for c in CASES}
    y0 = {}
    for c in CASES:
        b = slopes[c]
        centered = np.where(n > 0, ybar + (b / 100.0) * (a0 - np.nan_to_num(abar)) / 1000.0, 0.0)
        y0[c] = np.where(n > 0, (n * centered + k * ypool) / (n + k), ypool)
    if base_override:
        for cid, (yk, a0o) in base_override.items():
            i = cells.index(cid)
            a0[i] = a0o
            for c in CASES:
                y0[c][i] = yk[c]
            level[i] = "override"
    rk = cfg["risk"]
    floor = np.where(upper, rk["yield_floor"]["upper"], rk["yield_floor"]["lower"]).astype(float)
    cap = np.where(upper, rk["yield_cap"]["upper"], rk["yield_cap"]["lower"]).astype(float)
    has = adm > 0
    lo = np.where(has, cells.award, np.inf).min(axis=1)
    hi = np.where(has, cells.award, -np.inf).max(axis=1)
    lo = np.where(np.isfinite(lo), lo, np.nan)
    hi = np.where(np.isfinite(hi), hi, np.nan)
    return ResponseBase(a0=a0, y0=y0, slopes=slopes, floor=floor, cap=cap, ybar=ybar, abar=abar, n=n,
                        ypool=ypool, pool_level=level, award_lo=lo, award_hi=hi)


def yield_at(base, award, case):
    """Response before the scenario shift: clip(y0_ck + (b_k/100)(a - a0_c)/1000, floor, cap)."""
    raw = base.y0[case] + (base.slopes[case] / 100.0) * (np.asarray(award, float) - base.a0) / 1000.0
    return np.clip(raw, base.floor, base.cap)


def evidence_labels(base, award, cfg):
    """'observed' if the award lies within the cell's historical award range plus the tolerance, else 'extrapolated'.
    Describes how well the yield is known, never the award."""
    tol = float(cfg["evidence_tolerance_usd"])
    award = np.asarray(award, float)
    with np.errstate(invalid="ignore"):
        obs = (award >= base.award_lo - tol) & (award <= base.award_hi + tol)
    obs = np.where(np.isnan(base.award_lo), False, obs)
    return np.where(obs, labels.EVIDENCE_OBSERVED, labels.EVIDENCE_EXTRAPOLATED)


def evidence(lc, base, cfg):
    """Interface: `evidence_extrapolated_share` = expected enrolled in extrapolated cells / expected class."""
    lab = evidence_labels(base, lc.award, cfg)
    total = lc.mu.sum()
    ext = lc.mu[lab == labels.EVIDENCE_EXTRAPOLATED].sum()
    return {"evidence_labels": lab, "evidence_extrapolated_share": (ext / total) if total > 0 else 0.0}
