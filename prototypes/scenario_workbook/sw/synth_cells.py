"""Cell-level synthetic generator (stopgap until the law world W0L exists; spec sections 10 and 15 item 7).

Three cohorts of cell-level counts on a law-style band grid, with a hidden true response slope used only to make
enrolled counts. Seeds are fixed. Shape parameters and their provenance: config/shape_targets.yaml and
docs/shape_targets.md. Does not use efa_fao/src/synth.

Construction, per cohort:
1. Applications: cohort total, score-group share and out-of-state share (centers plus small noise); within each
   residency x score group, a multinomial over band x GPA (x segment for out-of-state) with seed-perturbed weights.
2. Admits: logit admit rate = group intercept + band effect + GPA effect; the intercept is solved so each
   residency x score group hits the group's admit rate; integer counts by controlled rounding that keeps block totals.
3. Awards: share of tuition = band level + GPA adjustment + cohort generosity (solved to the group's admit-weighted
   target) + persistent cell noise; fixed-dollar rungs; shares at or above the full-tuition cut take tuition.
4. Yield: intrinsic yield falls with the cell's typical award (the planted confound), plus the hidden true slope on
   the cell's award change across cohorts. Group factors are raked so residency, score-group and GPA yields hit
   their targets; enrolled counts by hierarchical controlled rounding (residency, score group, GPA, cell).
Group-level yields are calibrated by construction: binomial noise at this class size (SD about 0.016 on overall
yield) is wider than several asserted ranges, so independent draws could not meet them in 18 of 20 seeds.
"""
import math

import numpy as np
import pandas as pd

from .cells import COLUMNS, from_long

UNSCORED = "unscored"


def _band_key(b):
    return UNSCORED if b == UNSCORED else int(b)


def controlled_round(x, total, rng, cap=None):
    """Integers that are floor or ceil of x (rescaled to sum to total), summing to total, each at most cap."""
    x = np.asarray(x, float).copy()
    n = len(x)
    total = int(total)
    if total == 0 or n == 0:
        return np.zeros(n, dtype=int)
    cap = np.full(n, np.inf) if cap is None else np.asarray(cap, float)
    if cap.sum() < total - 1e-9:
        raise ValueError("block total exceeds the caps")
    if x.sum() <= 0:
        x = np.where(cap > 0, 1.0, 0.0)
    x = x * total / x.sum()
    for _ in range(50):
        over = x > cap
        if not over.any():
            break
        excess = (x[over] - cap[over]).sum()
        x[over] = cap[over]
        room = (~over) & (x < cap)
        if not room.any():
            break
        x[room] += excess * x[room] / x[room].sum() if x[room].sum() > 0 else excess / room.sum()
    fl = np.floor(x + 1e-12)
    fl = np.minimum(fl, cap)
    rem = int(round(total - fl.sum()))
    frac = np.where(fl + 1 <= cap, x - fl, 0.0)
    frac = np.clip(frac, 0, None)
    out = fl.copy()
    if rem > 0:
        cand = np.flatnonzero(frac > 1e-12)
        if len(cand) < rem:
            cand = np.flatnonzero(fl + 1 <= cap)
            p = np.ones(len(cand)) / len(cand)
        else:
            p = frac[cand] / frac[cand].sum()
        pick = rng.choice(cand, size=rem, replace=False, p=p)
        out[pick] += 1
    return out.astype(int)


def hier_round(x, total, levels, rng, cap):
    """Controlled rounding down a hierarchy: block totals at each level are kept, then cells."""
    x = np.asarray(x, float)
    cap = np.asarray(cap, float)
    out = np.zeros(len(x), dtype=int)

    def rec(idx, tot, depth):
        if depth == len(levels):
            out[idx] = controlled_round(x[idx], tot, rng, cap[idx])
            return
        keys = levels[depth][idx]
        uniq = list(dict.fromkeys(keys.tolist()))
        groups = [idx[keys == k] for k in uniq]
        sums = np.array([x[g].sum() for g in groups])
        caps = np.array([cap[g].sum() for g in groups])
        tots = controlled_round(sums, tot, rng, caps)
        for g, t in zip(groups, tots):
            rec(g, int(t), depth + 1)

    rec(np.arange(len(x)), int(total), 0)
    return out


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def _solve_intercept(apps, beta, target_rate):
    """Logit intercept so that sum apps x sigmoid(a + beta) = target_rate x sum apps."""
    tot = apps.sum()
    if tot <= 0:
        return 0.0
    lo, hi = -20.0, 20.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if (apps * _sigmoid(mid + beta)).sum() / tot < target_rate:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _award_usd(share, tuition, rung, ft_cut):
    if share >= ft_cut:
        return float(tuition)
    a = rung * math.floor(max(share, 0.0) * tuition / rung + 0.5)
    return float(min(a, tuition - rung)) if a >= tuition else float(a)


def cell_grid(cfg):
    """Cell definitions: residency x (segment for out-of-state) x band (plus unscored) x GPA class."""
    bands = list(cfg["score"]["bands"]) + [UNSCORED]
    seg_name = cfg["segments"][0]["name"] if cfg["segments"] else None
    rows = []
    for res in ("in", "out"):
        segs = [""] + ([seg_name] if (seg_name and cfg["segments"][0]["within"]["residency"] == res) else [])
        for seg in segs:
            for b in bands:
                for k in ("hi", "lo", "blank"):
                    rows.append({"residency": res, "segment": seg, "band": b, "gpa_class": k})
    df = pd.DataFrame(rows)
    pt = cfg["score"]["pool_threshold"]
    df["group"] = ["lower" if b == UNSCORED or b < pt else "upper" for b in df["band"]]
    df["cell_id"] = [f"{r.residency}{'-' + r.segment if r.segment else ''}-{r.band}-{r.gpa_class}"
                     for r in df.itertuples()]
    return df


def generate(cfg, seed, scale=1.0):
    """Return Cells for one synthetic world (three history cohorts)."""
    g = cfg["generator"]
    rng = np.random.default_rng(seed)
    grid = cell_grid(cfg)
    n = len(grid)
    res = grid["residency"].to_numpy()
    seg = grid["segment"].to_numpy()
    band = grid["band"].to_numpy()
    gpa = grid["gpa_class"].to_numpy()
    grp = grid["group"].to_numpy()
    is_seg = seg != ""
    hist = list(cfg["cycle"]["history"])
    tuition = cfg["tuition_by_cohort"]

    # persistent per-world perturbations
    bw = {}
    for gr in ("upper", "lower"):
        keys = list(g["band_weights"][gr].keys())
        base = np.array([g["band_weights"][gr][k] for k in keys], float)
        pert = rng.dirichlet(base * g["band_dirichlet_conc"])
        for k, v in zip(keys, pert):
            bw[_band_key(k)] = v
    twin = np.array([f"{r}-{b}-{k}" for r, b, k in zip(res, band, gpa)])
    award_noise = {}
    for tkey in dict.fromkeys(twin):
        award_noise[tkey] = rng.normal(0.0, g["award_share_noise_sd"])
    noise = np.array([award_noise[t] for t in twin])

    apps = np.zeros((n, len(hist)))
    admits = np.zeros((n, len(hist)))
    award = np.zeros((n, len(hist)))
    seg_share_cfg = g["segment_share_of_out"]
    for j, coh in enumerate(hist):
        N = int(round(g["apps_total"][coh] * scale * (1 + g["apps_total_sd_share"] * rng.standard_normal())))
        u = g["upper_share_of_apps"][coh] + g["upper_share_sd"] * rng.standard_normal()
        o = g["out_share_of_apps"] + g["out_share_sd"] * rng.standard_normal()
        blocks = [("in", "upper"), ("in", "lower"), ("out", "upper"), ("out", "lower")]
        bshare = np.array([(1 - o) * u, (1 - o) * (1 - u), o * u, o * (1 - u)])
        btot = controlled_round(bshare * N, N, rng)
        for (r, gr), tot in zip(blocks, btot):
            idx = np.flatnonzero((res == r) & (grp == gr))
            w = np.array([bw[_band_key(b)] * g["gpa_mix"][gr][k] for b, k in zip(band[idx], gpa[idx])])
            if r == "out" and is_seg.any():
                sh = seg_share_cfg[gr] * (1 + g["segment_apps_trend"]) ** j
                w = w * np.where(is_seg[idx], sh, 1 - sh)
            apps[idx, j] = rng.multinomial(int(tot), w / w.sum())

        # admits
        beta = np.array([g["admit_logit_band"][_band_key(b) if b == UNSCORED else int(b)] for b in band]) + \
            np.array([g["admit_logit_gpa"][k] for k in gpa])
        exp_adm = np.zeros(n)
        block_tot = {}
        for r in ("in", "out"):
            for gr in ("upper", "lower"):
                idx = np.flatnonzero((res == r) & (grp == gr))
                rate = g["admit_rate_group"][gr][coh]
                a = _solve_intercept(apps[idx, j], beta[idx], rate)
                exp_adm[idx] = apps[idx, j] * _sigmoid(a + beta[idx])
                block_tot[(r, gr)] = int(round(rate * apps[idx, j].sum()))
        rg = np.array([f"{r}|{gr}" for r, gr in zip(res, grp)])
        for key, tot in block_tot.items():
            idx = np.flatnonzero(rg == f"{key[0]}|{key[1]}")
            sub = hier_round(exp_adm[idx], tot, [gpa[idx]], rng, apps[idx, j])
            admits[idx, j] = sub

        # awards
        T = tuition[coh]
        lvl = np.array([g["award_share_band"][_band_key(b) if b == UNSCORED else int(b)] for b in band]) + \
            np.array([g["award_share_gpa"][k] for k in gpa]) + noise + \
            np.array([g["award_share_res"][r] for r in res])
        for gr in ("upper", "lower"):
            idx = np.flatnonzero(grp == gr)
            target = g["award_share_target"][gr][coh]
            wts = admits[idx, j]
            if wts.sum() <= 0:
                continue
            lo, hi = -1.5, 1.5
            for _ in range(60):
                mid = 0.5 * (lo + hi)
                aw = np.array([_award_usd(min(1.0, s + mid), T, g["award_rung_usd"], g["full_tuition_share"])
                               for s in lvl[idx]])
                if (wts * aw).sum() / wts.sum() / T < target:
                    lo = mid
                else:
                    hi = mid
            award[idx, j] = [_award_usd(min(1.0, s + hi), T, g["award_rung_usd"], g["full_tuition_share"])
                             for s in lvl[idx]]

    enrolled = _enroll(cfg, rng, res, seg, grp, gpa, is_seg, admits, award)
    df = pd.DataFrame([
        {"cell_id": grid["cell_id"][i], "residency": res[i], "segment": seg[i],
         "score_lo": np.nan if band[i] == UNSCORED else float(band[i]), "gpa_class": gpa[i], "cohort": coh,
         "apps": apps[i, j], "admits": admits[i, j], "award_usd": award[i, j], "enrolled": enrolled[i, j]}
        for i in range(n) for j, coh in enumerate(hist)
    ], columns=COLUMNS)
    cells = from_long(df, cfg)
    cells.meta = {"seed": seed, "scale": scale, "true_slope_pts_per_1000": g["true_slope_pts_per_1000"]}
    return cells


def _enroll(cfg, rng, res, seg, grp, gpa, is_seg, admits, award):
    g = cfg["generator"]
    yt = g["yield_targets"]
    b = g["true_slope_pts_per_1000"] / 100.0
    hist = list(cfg["cycle"]["history"])
    abar = award.mean(axis=1)
    base = np.exp(-g["yield_award_decay_per_1000"] * abar / 1000.0)
    enrolled = np.zeros_like(admits)
    for j, coh in enumerate(hist):
        A = admits[:, j]
        add = b * (award[:, j] - abar) / 1000.0 + is_seg * g["segment_yield_offset_pts"] / 100.0
        tot_adm = A.sum()
        E = int(round(yt["overall"] * tot_adm))
        out_E = int(round(yt["out_share_of_enrolled"][coh] * E))
        low_E = int(round(yt["lower_group"] * A[grp == "lower"].sum()))
        targets = {
            "res": {"out": out_E, "in": E - out_E},
            "grp": {"lower": low_E, "upper": E - low_E},
            "gpa": {"hi": yt["gpa_hi"][coh] * A[gpa == "hi"].sum(), "blank": yt["overall"] * A[gpa == "blank"].sum()},
        }
        targets["gpa"]["lo"] = E - targets["gpa"]["hi"] - targets["gpa"]["blank"]
        keys = {"res": res, "grp": grp, "gpa": gpa}
        F = np.ones(len(A))
        for _ in range(300):
            for dim in ("res", "grp", "gpa"):
                for k, tgt in targets[dim].items():
                    m = keys[dim] == k
                    cur_mult = (A[m] * F[m] * base[m]).sum()
                    if cur_mult <= 0:
                        continue
                    need = tgt - (A[m] * add[m]).sum()
                    F[m] *= max(need, 1e-9) / cur_mult
        y = np.clip(F * base + add, 0.005, 0.9)
        expected = A * y
        # 2 x 2 integer table (residency x score group) that keeps both margins exactly, then GPA, then cells.
        low_in = int(round(expected[(res == "in") & (grp == "lower")].sum()))
        low_in = min(max(low_in, low_E - out_E, 0), low_E, E - out_E)
        block = {("in", "lower"): low_in, ("out", "lower"): low_E - low_in,
                 ("in", "upper"): E - out_E - low_in, ("out", "upper"): out_E - (low_E - low_in)}
        out = np.zeros(len(A), dtype=int)
        for (r, gr), tot in block.items():
            idx = np.flatnonzero((res == r) & (grp == gr))
            out[idx] = hier_round(expected[idx], tot, [gpa[idx]], rng, A[idx])
        enrolled[:, j] = out
    return enrolled


# -------------------------------------------------------------------------------------------------------------
# Shape metrics (spec section 10) on the residency-only view: segment cells merged back into their out-of-state
# twins, which is the basis of the fixture's ranges.

def merged_view(cells):
    df = cells.to_long()
    df["key"] = df["residency"] + "|" + df["score_lo"].fillna(-1).astype(str) + "|" + df["gpa_class"]
    agg = df.groupby(["key", "cohort"]).agg(
        residency=("residency", "first"), score_lo=("score_lo", "first"), gpa_class=("gpa_class", "first"),
        apps=("apps", "sum"), admits=("admits", "sum"), enrolled=("enrolled", "sum"),
        award_usd=("award_usd", "first"),
    ).reset_index()
    return agg


def _wls(y, X, w):
    sw = np.sqrt(w)
    coef, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    return coef


def shape_metrics(cells, cfg):
    d = merged_view(cells)
    pt = cfg["score"]["pool_threshold"]
    d["upper"] = d["score_lo"].fillna(-1) >= pt
    hist = list(cfg["cycle"]["history"])
    out = {"per_cohort": {}}
    for coh in hist:
        c = d[d["cohort"] == coh]
        o = c["residency"] == "out"
        up = c["upper"]
        hi = c["gpa_class"] == "hi"
        lo = c["gpa_class"] == "lo"
        A = c["admits"]
        E = c["enrolled"]
        P = c["apps"]
        T = cfg["tuition_by_cohort"][coh]
        act = A > 0

        def r(num, den):
            return float(num.sum() / den.sum()) if den.sum() > 0 else float("nan")
        out["per_cohort"][coh] = {
            "out_share_apps": r(P[o], P), "out_share_admits": r(A[o], A), "out_share_enrolled": r(E[o], E),
            "yield_out": r(E[o], A[o]), "yield_in": r(E[~o], A[~o]),
            "admit_rate_upper": r(A[up], P[up]), "admit_rate_lower": r(A[~up], P[~up]),
            "admit_rate_gpa_hi": r(A[hi], P[hi]), "admit_rate_gpa_lo": r(A[lo], P[lo]),
            "yield_upper": r(E[up], A[up]), "yield_lower": r(E[~up], A[~up]),
            "yield_gpa_hi": r(E[hi], A[hi]), "yield_gpa_lo": r(E[lo], A[lo]), "yield_overall": r(E, A),
            "apps_total": float(P.sum()), "upper_share_apps": r(P[up], P),
            "award_share_upper": float((A[up] * c["award_usd"][up]).sum() / A[up].sum() / T),
            "award_share_lower": float((A[~up] * c["award_usd"][~up]).sum() / A[~up].sum() / T),
            "class": float(E.sum()), "upper_share_enrolled": r(E[up], E),
            "median_admits_active": float(np.median(A[act])),
            "share_active_under10_admits": float((A[act] < 10).mean()),
            "share_active_under10_enrolled": float((E[act] < 10).mean()),
        }
    # tuition growth
    tg = [100 * (cfg["tuition_by_cohort"][b] / cfg["tuition_by_cohort"][a] - 1) for a, b in zip(hist[:-1], hist[1:])]
    out["tuition_growth_pct"] = tg
    out["top_rung_equals_tuition"] = all(
        abs(d[d["cohort"] == coh]["award_usd"].max() - cfg["tuition_by_cohort"][coh]) < 0.5 for coh in hist)
    # confounding: admit-weighted slope of cell yield (points) on award ($1,000), pooled over cohorts
    a = d[d["admits"] > 0]
    yv = 100 * a["enrolled"].to_numpy() / a["admits"].to_numpy()
    x = a["award_usd"].to_numpy() / 1000.0
    w = a["admits"].to_numpy(float)
    raw = _wls(yv, np.column_stack([np.ones(len(x)), x]), w)[1]
    dummies = [np.ones(len(x)), x, a["upper"].to_numpy(float), (a["residency"] == "out").to_numpy(float),
               (a["gpa_class"] == "lo").to_numpy(float), (a["gpa_class"] == "blank").to_numpy(float)]
    adj = _wls(yv, np.column_stack(dummies), w)[1]
    out["confounding_raw"] = float(raw)
    out["confounding_adjusted"] = float(adj)
    return out


def evaluate_targets(metrics, targets, cfg):
    """Return {row_name: (passed, details)} for each shape-target row."""
    hist = list(cfg["cycle"]["history"])
    pc = metrics["per_cohort"]
    res = {}
    for row in targets["rows"]:
        ok = True
        detail = {}
        for chk in row["checks"]:
            kind = chk["kind"]
            m = chk["metric"]
            if kind == "range_each_cohort":
                vals = [pc[c][m] for c in hist]
                good = all(chk["min"] <= v <= chk["max"] for v in vals)
            elif kind == "falling":
                vals = [pc[c][m] for c in hist]
                good = vals[-1] < vals[0]
            elif kind == "near_by_cohort":
                vals = [pc[c][m] for c in hist]
                good = all(abs(v - t) <= chk["tol"] for v, t in zip(vals, chk["values"]))
            elif kind == "range_pooled":
                vals = metrics[m]
                good = chk["min"] <= vals <= chk["max"]
            elif kind == "near_list":
                vals = metrics[m]
                good = all(abs(v - t) <= chk["tol"] for v, t in zip(vals, chk["values"]))
            elif kind == "flag":
                vals = metrics[m]
                good = bool(vals)
            elif kind == "min_each_cohort":
                vals = [pc[c][m] for c in hist]
                good = all(v >= chk["min"] for v in vals)
            else:
                raise ValueError(kind)
            detail[f"{m}:{kind}"] = (good, vals)
            ok = ok and good
        res[row["name"]] = (ok, detail)
    return res


def scenario_draws(cfg, seed):
    """Pool multiplier, bonus and yield shift for test 4, drawn from the ranges in config/synthetic.yaml."""
    t4 = cfg["test4"]
    rng = np.random.default_rng(10_000 + seed)
    return {
        "pool_multiplier": float(rng.uniform(*t4["pool_multiplier"])),
        "bonus_usd": float(1000 * round(rng.uniform(*t4["bonus_usd"]) / 1000)),
        "yield_shift_pts": float(rng.uniform(*t4["yield_shift_pts"])),
    }
