"""Shrink path and class-size table (spec section 3, [v0.6, B1-5, B1-16, B7-7]).

Deterministic and evaluator-only: it writes admit rates the analyst may overwrite; yield is constant when admit
rates change (D1). Uses the Middle case. Trimming unscored applicants first is a policy choice with access
implications [v0.6, B1-24].
"""
import numpy as np

from . import labels
from . import ledger as L
from . import risk

GPA_TRIM = {"blank": 0, "lo": 1, "hi": 2}


def trim_order(lc):
    """Ascending score_lo (unscored first), then GPA (blank, lo, hi); ties: out of state outside the segment, in-state
    outside the segment, segment. With protect_segment: below_threshold, segment cells below the first median
    threshold go after all non-segment cells below it and before any cell at or above it."""
    cells, cfg = lc.cells, lc.cfg
    t = cfg["score"]["median_thresholds"][0]
    protect = cfg["trim"]["protect_segment"] == "below_threshold"
    seg = lc.in_segment
    keys = []
    for i in range(cells.n):
        s = cells.score_lo[i]
        below = np.isnan(s) or s < t
        tier = 0 if below else 2
        if protect and below and seg[i]:
            tier = 1
        tie = 2 if seg[i] else (0 if cells.residency[i] == "out" else 1)
        keys.append((tier, -np.inf if np.isnan(s) else s, GPA_TRIM[cells.gpa_class[i]], tie, i))
    return np.array([k[-1] for k in sorted(keys)], dtype=int)


def trim_rates(lc, N):
    """Admit rates after trimming the Middle expected class M to N. Returns a dict with rates and the walk."""
    cfg = lc.cfg
    f = float(cfg["trim"]["floor_rate"])
    exempt = np.isin(lc.cells.cell_id, list(cfg["trim"]["exempt_cells"]))
    r = lc.rate.astype(float)
    A, y = lc.admits, lc.yld
    with np.errstate(invalid="ignore", divide="ignore"):
        rm = np.where((~exempt) & (r > 0), A * y * np.maximum(0.0, r - f) / np.where(r > 0, r, 1.0), 0.0)
    order = trim_order(lc)
    rm_o = rm[order]
    R_o = np.cumsum(rm_o)
    R_prev = R_o - rm_o
    M = float(lc.mu.sum())
    need = M - N
    share_o = np.zeros_like(rm_o)
    if need > 0:
        with np.errstate(invalid="ignore", divide="ignore"):
            share_o = np.where(rm_o > 0, np.clip((need - R_prev) / np.where(rm_o > 0, rm_o, 1.0), 0.0, 1.0), 0.0)
    share = np.zeros(lc.cells.n)
    share[order] = share_o
    rates = r - (r - f) * share
    rates = np.where(rm > 0, rates, r)
    R_K = float(R_o[-1]) if len(R_o) else 0.0
    status = labels.CT_OK
    shortfall = 0.0
    if need > R_K + 1e-9:
        shortfall = need - R_K
        status = labels.CT_SHORTFALL.format(shortfall=f"{labels.xl(shortfall, 1):.1f}")
    if cfg["integer_admits"] and need > 0:
        rates = _settle_integer(lc, rates, share, order, N, f)
    return {"rates": rates, "removed_share": share, "rm": rm, "order": order, "R": R_o, "M": M,
            "status": status, "shortfall": shortfall}


def _settle_integer(lc, rates, share, order, N, f):
    """Round admits and settle the residual in the last cell cut. Cells the walk does not cut keep their input
    admit rates exactly; only cut cells get rates from their rounded admits [v0.6.1, R-05]."""
    apps = lc.apps
    admits = L.xround(apps * rates)
    cut = [i for i in order if share[i] > 0]
    if cut:
        last = cut[-1]
        y_last = lc.yld[last]
        if y_last > 0:
            resid = float((admits * lc.yld).sum()) - N
            lo = L.xround(apps[last] * f)
            admits[last] = np.clip(admits[last] - L.xround(resid / y_last), lo, lc.admits[last])
    with np.errstate(invalid="ignore", divide="ignore"):
        settled = np.where(apps > 0, admits / np.where(apps > 0, apps, 1.0), rates)
    return np.where(share > 0, settled, lc.rate)


def _row_figures(lc):
    cfg = lc.cfg
    m = L.money(lc)
    row = {"class_mean": float(lc.mu.sum()), "ntr_y1": m["ntr_y1"],
           "discount_entering_y1": m["discount_entering_y1"], "median": {}}
    for meas, t in risk.median_targets(cfg):
        md = risk.median(lc, meas, t)
        row["median"][(meas, t)] = {"margin": md["margin_t"], "p": md["p_median_t"]}
    row["segment_enrolled"] = float(lc.enrolled[lc.in_segment].sum()) if lc.in_segment.any() \
        else labels.NO_SEGMENT_CELLS
    adm = lc.admits > 0
    scored = ~np.isnan(lc.cells.score_lo)
    row["lowest_band_admitted"] = float(lc.cells.score_lo[adm & scored].min()) if (adm & scored).any() else None
    return row


def class_table(cells, cfg, scen, base, Ns=None):
    """Class-size table: for each N in class.what_if, the shrink path's figures (Middle case)."""
    Ns = cfg["class"]["what_if"] if Ns is None else Ns
    lc = L.evaluate(cells, cfg, scen, base, "middle")
    M = float(lc.mu.sum())
    rows = []
    for N in Ns:
        row = {"N": N, "f": N / M if M > 0 else None}
        if N > scen.class_cap:
            row["status"] = labels.CT_ABOVE_CAP
            rows.append(row)
            continue
        if N >= M:
            row["status"] = labels.CT_NOT_APPLICABLE
            row.update(_row_figures(lc))
            row["rates"] = lc.rate.copy()
            row["admits_cut_by_band"] = {}
            rows.append(row)
            continue
        tr = trim_rates(lc, N)
        lcN = L.evaluate(cells, cfg, L.with_rates(scen, tr["rates"], name=f"{scen.name} N={N}"), base, "middle")
        row["status"] = tr["status"]
        row.update(_row_figures(lcN))
        row["rates"] = tr["rates"]
        cut = lc.admits - lcN.admits
        by_band = {}
        for i in range(cells.n):
            if cut[i] > 0:
                key = "unscored" if np.isnan(cells.score_lo[i]) else float(cells.score_lo[i])
                by_band[key] = by_band.get(key, 0.0) + float(cut[i])
        row["admits_cut_by_band"] = by_band
        rows.append(row)
    return {"class_table": rows, "M": M, "policy_note": labels.POLICY_UNSCORED_TRIMMED_FIRST}
