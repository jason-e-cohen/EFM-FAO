"""Tuition, yield and pool what-if strips (spec section 3). Middle case. Each strip is closed form over Ledger columns.
"""
import math
from dataclasses import replace

import numpy as np

from . import labels
from . import ledger as L
from . import risk
from .config import scenario_tuition


def tuition(lc, grid=None, example_award=None):
    """Tuition what-if: for each p in tuition_grid, ntr_y1, net tuition per student and the discount rate, with the
    scenario's class and mix held fixed and the award rule applied at T(p). Plus the two net-tuition lines."""
    cfg = lc.cfg
    scen = lc.scenario
    grid = cfg["risk"]["tuition_grid"] if grid is None else grid
    e = lc.enrolled
    cls = float(e.sum())
    need = lc.need_rate * cls
    rows = []
    for pct in grid:
        T = scenario_tuition(cfg, pct)
        _, award = L.resolve_awards(scen, T, pct / 100.0, lc.eligible)
        ntr = float((e * (T - award)).sum()) - need - lc.specialty
        gross = cls * T
        rows.append({
            "tuition_increase_pct": pct, "tuition": T, "ntr_y1": ntr,
            "net_tuition_per_student": ntr / cls if cls > 0 else 0.0,
            "discount_entering_y1": (gross - ntr) / gross if gross > 0 else 0.0,
            "label": labels.STICKER_LABEL,
        })
    t_base = float(cfg["tuition_base"])
    diff = lc.tuition - t_base
    if example_award is None:
        # Enrolled-weighted mean base-cycle lever award (award_usd, not award_base) over enrollees whose base-cycle
        # lever award, before any incentive, is below base-cycle tuition and whose cell has no full_tuition flag, zero
        # awards included, rounded to $1,000 [v0.6.1, R-07, OP-7c; v0.6.2, Q-5; P1.1-4]. An unflagged award typed at
        # or above base-cycle tuition is a full-tuition student; an incentive that lifts a cell to the cap does not
        # drop it.
        below = (~np.asarray(scen.full_tuition, bool)) & (scen.award_usd < t_base - 1e-6) & (e > 0)
        example_award = float(L.xround((e[below] * scen.award_usd[below]).sum() / e[below].sum() / 1000.0) * 1000.0) \
            if below.any() else 0.0
    x = lc.p * (t_base - example_award)
    return {
        "tuition_whatif": rows,
        "net_tuition_line_fixed": diff,
        "net_tuition_line_scaled": x,
        "example_award": example_award,
        "net_tuition_line_fixed_text": labels.NET_TUITION_FIXED.format(diff=f"${labels.xl(diff):,.0f}"),
        "net_tuition_line_scaled_text": labels.NET_TUITION_SCALED.format(
            p=f"{labels.xl(100 * lc.p, 1):.1f}%", x=f"${labels.xl(x):,.0f}",
            award=f"${labels.xl(example_award):,.0f}"),
        "labels": [labels.STICKER_LABEL],
    }


def yield_strip(lc, grid=None):
    """Yield what-if strip: shift d (points) on top of the scenario's own shift; floor and cap ignored."""
    cfg = lc.cfg
    scen = lc.scenario
    s = float(cfg["risk"]["common_shock_sd"])
    rho = float(cfg["risk"]["shock_corr_above_below"])
    grid = cfg["risk"]["yield_shift_grid"] if grid is None else grid
    A, y = lc.admits, lc.yld
    targets = risk.median_targets(cfg)
    signs = {(m, t): risk.median_signs(lc.cells, cfg, m, t) for m, t in targets}
    ntr_target = cfg.get("ntr_target")
    rows = []
    for d in grid:
        yd = y + d / 100.0
        c = risk.cf_class(A, yd, s, scen.class_cap, scen.class_target, cfg["class"]["band"])
        n = risk.cf_ntr(A, yd, lc.w, s, lc.specialty, ntr_target)
        row = {"shift_pts": d, "class_mean": c["class_mean"], "p_class_over_cap": c["p_class_over_cap"],
               "p_class_in_band": c["p_class_in_band"], "ntr_mean": n["ntr_mean"],
               "p_ntr_y1_ge_target": n.get("p_ntr_y1_ge_target"), "median": {}}
        for key, g in signs.items():
            r = risk.cf_median(A, yd, g, s, rho)
            row["median"][key] = {"margin": r["margin_expected"], "p": r["p"]}
        rows.append(row)
    active = A > 0
    dmax, dmin = max(grid) / 100.0, min(grid) / 100.0
    binds = active & ((y + dmax > lc.ycap) | (y + dmin < lc.yfloor))
    sumA = float(A.sum())
    M = float((A * y).sum())
    sumwA = float((lc.w * A).sum())
    mean_ntr = float((lc.w * A * y).sum()) - lc.specialty
    be_class = (scen.class_target - M) / sumA * 100.0 if sumA > 0 else None
    be_ntr = (ntr_target - mean_ntr) / sumwA * 100.0 if (ntr_target is not None and sumwA != 0) else None
    return {
        "yield_strip": rows,
        "clip_count": int(binds.sum()),
        "breakeven_shift_class": be_class,
        "breakeven_shift_ntr": be_ntr,
        "breakeven_label": labels.LINEAR_APPROX,
        "labels": [labels.ASSUMPTION_LABEL] + ([labels.shock_label(s)] if cfg["risk"]["shock_source"] == "illustrative"
                                               else []),
    }


def pool_strip(cells, cfg, scen, base, grid=None):
    """Pool strip: every lever applied except the pool multiplier, which m replaces (the segment lift stays).

    Splits the Ledger at m = 1 into a lo part (score below score.pool_threshold) and a hi part; the hi part scales
    with m. Exact for the ledger without rounding; with integer_admits the ledger rounds and the strip does not.
    """
    s = float(cfg["risk"]["common_shock_sd"])
    rho = float(cfg["risk"]["shock_corr_above_below"])
    grid = cfg["risk"]["pool_grid"] if grid is None else grid
    lc1 = L.evaluate(cells, cfg, replace(scen, pool_multiplier=1.0), base, "middle")
    hi = lc1.upper
    lo = ~hi
    mu = lc1.admits * lc1.yld
    v = lc1.admits * lc1.yld * (1 - lc1.yld)
    w = lc1.w
    t = cfg["score"]["median_thresholds"][0]
    g = risk.median_signs(cells, cfg, "score", t)
    parts = {}
    for name, msk in (("lo", lo), ("hi", hi)):
        parts[name] = {
            "M": float(mu[msk].sum()), "V": float(v[msk].sum()),
            "Gp": float(mu[msk & (g > 0)].sum()), "Gm": float(mu[msk & (g < 0)].sum()),
            "Vm": float(v[msk & (g != 0)].sum()),
            "W": float((w * mu)[msk].sum()), "Vn": float((w * w * v)[msk].sum()),
        }
    P, Q = parts["lo"], parts["hi"]
    rows = []
    for m in grid:
        M = P["M"] + m * Q["M"]
        V = P["V"] + m * Q["V"] + s * s * M * M
        Gp = P["Gp"] + m * Q["Gp"]
        Gm = P["Gm"] + m * Q["Gm"]
        Vm = P["Vm"] + m * Q["Vm"] + s * s * (Gp * Gp + Gm * Gm - 2 * rho * Gp * Gm)
        Wm = P["W"] + m * Q["W"]
        Vn = P["Vn"] + m * Q["Vn"] + s * s * Wm * Wm
        cap = scen.class_cap
        rows.append({
            "pool_multiplier": m, "growth": m - 1.0, "class_mean": M,
            "p_class_over_cap": float(1 - risk.Phi((cap + 0.5 - M) / math.sqrt(max(V, 1e-300)))),
            "margin": Gp - Gm, "p_median": float(1 - risk.Phi((-0.5 - (Gp - Gm)) / math.sqrt(max(Vm, 1e-300)))),
            "ntr_mean": Wm - lc1.specialty, "ntr_sd": math.sqrt(max(Vn, 0.0)),
        })
    return {
        "pool_strip": rows,
        "threshold": t,
        "parts": parts,
        "pool_ytd_growth": cfg.get("pool_ytd_growth"),
        "pool_ytd_label": labels.POOL_YTD_LABEL,
        "label": labels.POOL_STRIP_LABEL,
        "rounding_note": "ledger rounds admits; strip does not" if cfg["integer_admits"] else "",
    }
