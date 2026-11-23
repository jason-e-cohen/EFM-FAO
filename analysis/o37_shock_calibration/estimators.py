"""Estimators for the year-level yield shock s (O37; methodology section 6, [v2.8, B4-1]).

Model. A unit's realized yield is y_it = p_it * e_it with e_it ~ N(1, s), on top of
binomial enrollment noise given offers. On the log scale, log e ~ (0, s^2) for small s, and
the binomial term for log(E/O) is about (1 - y) / (O y). The shock splits into a national
year component n_t (common to every unit) and a unit-specific component u_it:
s^2 = sigma_n^2 + sigma_u^2.

(a) First differences. Var(d_it) = 2 s^2 + b_it + b_i,t-1 with d = change in log yield.
    total: d centered at its overall mean (a deterministic national drift is removed);
    unit-specific: d centered at its year mean; national = total - unit-specific.
(b) Levels around a unit-specific level and linear trend (units with 3 or more years).
    E[RSS] = sum (1 - h) (s^2 + b) per unit, with h the hat values, so
    s^2 = (RSS - sum (1 - h) b) / dof. total: no year effects; unit-specific: year effects
    added (identified up to a constant and trend); national: from the year effects,
    sampling variance removed.
(c) (a) and (b) with the change (a) or level (b) of log admit rate as a regressor with a
    common slope.
Diagnostics: persistence of the shocks (iid around a level versus random walk) from the
autocovariance of first differences, one-year-ahead forecast errors with k-year means, and
whether the excess spread is multiplicative (constant on the log scale across yield levels).

Trend versus persistent shock (added Nov 23, 2026, for the 2011 to 2025 panel). With
d_it = g_i + n_t + eta_it + (eps_it - eps_i,t-1) + binomial terms (g a school trend, eta a
random-walk innovation, eps an independent shock around the level), the autocovariances of
year-centered d at lag k are: gamma_0 = sg2 + seta2 + 2 seps2 + B, gamma_1 = sg2 - seps2 - b,
gamma_k = sg2 for k >= 2. Lags 2 and up therefore identify the trend variance; a mean-reverting
(AR) persistent part would make them negative and decaying instead. persistence_lags() returns
the autocovariances and this three-way split. forecast_rows_trend() adds the forecast a
trend-follower would make (a least-squares line through the last n years).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ------------------------------------------------------------------ preparation
def prep(df: pd.DataFrame, min_offers: int = 50, min_enrolled: int = 10) -> pd.DataFrame:
    """df: unit, year, offers, enrollees, apps (and any extra columns)."""
    d = df.copy()
    d = d[(d["offers"] >= min_offers) & (d["enrollees"] >= min_enrolled) & (d["enrollees"] <= d["offers"])]
    y = d["enrollees"] / d["offers"]
    d["y"] = y
    d["l"] = np.log(y)
    d["b"] = (1 - y) / (d["offers"] * y)
    d["b_level"] = y * (1 - y) / d["offers"]
    d["la"] = np.log(d["offers"] / d["apps"].where(d["apps"] > 0))
    return d.sort_values(["unit", "year"]).reset_index(drop=True)


def flag_implausible(d: pd.DataFrame, thr: float = 0.5, local: int | None = None) -> pd.Series:
    """A unit-year whose log yield is more than thr from the unit's median log yield.
    local=k (Nov 23, 2026, for the 15-year law panel): the median of the k years nearest the
    year (a k-year window shifted to stay inside the unit's years), so a genuine level shift over
    a decade is not trimmed while one-year spikes still are. On a panel of k or fewer years this is
    the whole-panel rule."""
    n = d.groupby("unit")["l"].transform("size")
    if local is None:
        med = d.groupby("unit")["l"].transform("median")
    else:
        def loc_med(x: pd.Series) -> pd.Series:
            v = x.to_numpy()
            m = len(v)
            out = np.empty(m)
            for i in range(m):
                lo = max(0, min(i - local // 2, m - local))
                out[i] = np.median(v[lo:lo + local])
            return pd.Series(out, index=x.index)
        med = d.groupby("unit", group_keys=False)["l"].apply(loc_med)
    return ((d["l"] - med).abs() > thr) & (n >= 3)


def first_differences(d: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby("unit")
    f = d.assign(l0=g["l"].shift(), b0=g["b"].shift(), la0=g["la"].shift(), y0=g["y"].shift(),
                 bl0=g["b_level"].shift(), year0=g["year"].shift())
    f = f[f["year"] - f["year0"] == 1].copy()
    f["d"] = f["l"] - f["l0"]
    f["B"] = f["b"] + f["b0"]
    f["dla"] = f["la"] - f["la0"]
    f["dy"] = f["y"] - f["y0"]
    f["Bl"] = f["b_level"] + f["bl0"]
    return f[["unit", "year", "d", "B", "b", "b0", "dla", "dy", "Bl", "y", "y0"]].dropna(subset=["d"])


def _resid(yv: np.ndarray, X: np.ndarray):
    beta, *_ = np.linalg.lstsq(X, yv, rcond=None)
    r = yv - X @ beta
    return r, np.linalg.matrix_rank(X), beta


def _year_dummies(years: np.ndarray, levels) -> np.ndarray:
    return (years[:, None] == np.asarray(levels)[None, :]).astype(float)


# ------------------------------------------------------------------ (a) first differences
def est_fd(f: pd.DataFrame, control: bool = False) -> dict:
    if control:
        f = f.dropna(subset=["dla"])
    n = len(f)
    if n < 10:
        return {}
    dv, Bm = f["d"].to_numpy(), f["B"].mean()
    yrs = np.sort(f["year"].unique())
    Xt = np.ones((n, 1))
    Xs = _year_dummies(f["year"].to_numpy(), yrs)
    if control:
        Xt = np.column_stack([Xt, f["dla"].to_numpy()])
        Xs = np.column_stack([Xs, f["dla"].to_numpy()])
    rt, kt, bt = _resid(dv, Xt)
    rs, ks, bs = _resid(dv, Xs)
    s2t = (rt @ rt / (n - kt) - Bm) / 2
    s2u = (rs @ rs / (n - ks) - Bm) / 2
    out = {"s2_total": s2t, "s2_unit": s2u, "s2_national": s2t - s2u, "n_obs": n,
           "n_units": f["unit"].nunique(), "binom_share_total": (Bm / 2) / ((rt @ rt / (n - kt)) / 2)}
    if control:
        out["slope_admit"] = bs[-1]
    return out


# ------------------------------------------------------------------ (b) levels with unit trend
def level_pieces(d: pd.DataFrame, years) -> list[dict]:
    """Per unit with 3 or more years: data projected off the unit's own level and trend."""
    out = []
    for u, g in d.groupby("unit", sort=False):
        if len(g) < 3:
            continue
        t = g["year"].to_numpy(float)
        Z = np.column_stack([np.ones_like(t), t - t.mean()])
        H = Z @ np.linalg.solve(Z.T @ Z, Z.T)
        M = np.eye(len(t)) - H
        D = _year_dummies(g["year"].to_numpy(), years)
        out.append({"unit": u, "lt": M @ g["l"].to_numpy(), "D": M @ D, "la": M @ g["la"].to_numpy(),
                    "b": g["b"].to_numpy(), "omh": 1 - np.diag(H), "T": len(t),
                    "has_la": bool(np.isfinite(g["la"]).all())})
    return out


def est_lv(pieces: list[dict], years, control: bool = False) -> dict:
    if control:
        pieces = [p for p in pieces if p["has_la"]]
    if len(pieces) < 5:
        return {}
    lt = np.concatenate([p["lt"] for p in pieces])
    b = np.concatenate([p["b"] for p in pieces])
    omh = np.concatenate([p["omh"] for p in pieces])
    D = np.vstack([p["D"] for p in pieces])
    la = np.concatenate([p["la"] for p in pieces])
    dof0 = sum(p["T"] - 2 for p in pieces)
    out = {"n_units": len(pieces), "n_obs": len(lt)}

    def fit(X):
        if X is None:
            return lt, np.zeros_like(lt), 0, None
        pinv = np.linalg.pinv(X, rcond=1e-9)
        beta = pinv @ lt
        r = lt - X @ beta
        h = np.einsum("ij,ji->i", X, pinv)
        return r, h, int(round(h.sum())), beta

    Xt = la[:, None] if control else None
    r, h, k, beta_t = fit(Xt)
    out["s2_total"] = (r @ r - ((omh - h) * b).sum()) / (dof0 - k)
    Xs = np.column_stack([D, la]) if control else D
    r, h, k, beta = fit(Xs)
    s2u = (r @ r - ((omh - h) * b).sum()) / (dof0 - k)
    out["s2_unit"] = s2u
    T = len(years)
    nyr = beta[:T]
    gram_pinv = np.linalg.pinv(Xs.T @ Xs, rcond=1e-9)[:T, :T]
    sig_e = s2u + b.mean()
    out["s2_national_yeareff"] = (nyr @ nyr - sig_e * np.trace(gram_pinv)) / max(T - 2, 1)
    out["s2_national"] = out["s2_total"] - s2u
    out["year_effects"] = dict(zip([int(y) for y in years], nyr.round(4)))
    if control:
        out["slope_admit"] = beta[-1]
    return out


# ------------------------------------------------------------------ diagnostics
def persistence(f: pd.DataFrame) -> dict:
    """Split first-difference variance into iid-around-a-level and random-walk parts."""
    f = f.copy()
    f["dr"] = f["d"] - f.groupby("year")["d"].transform("mean")
    g = f.groupby("unit")
    f["dr_prev"] = g["dr"].shift()
    f["yprev"] = g["year"].shift()
    pairs = f[f["year"] - f["yprev"] == 1]
    if len(pairs) < 10:
        return {}
    cov = (pairs["dr"] * pairs["dr_prev"]).mean()
    s2_iid = -cov - pairs["b0"].mean()
    var_d = (f["dr"] ** 2).mean()
    s2_rw = var_d - 2 * s2_iid - f["B"].mean()
    corr = cov / var_d
    return {"autocorr_d": corr, "s2_iid": s2_iid, "s2_rw": s2_rw, "n_pairs": len(pairs)}


def persistence_lags(f: pd.DataFrame, K: int = 4) -> dict:
    """Autocovariances of year-centered first differences at lags 0..K, and the split into trend,
    independent and random-walk parts (module note). Lags 2..K are averaged for the trend part,
    weighted by pair counts."""
    f = f.copy()
    f["dr"] = f["d"] - f.groupby("year")["d"].transform("mean")
    g = f.groupby("unit")
    out = {"gamma_0": float((f["dr"] ** 2).mean())}
    num = den = 0.0
    b0_lag1 = np.nan
    for k in range(1, K + 1):
        prev = g["dr"].shift(k)
        ok = (f["year"] - g["year"].shift(k) == k) & prev.notna()
        if ok.sum() < 10:
            break
        gk = float((f["dr"][ok] * prev[ok]).mean())
        out[f"gamma_{k}"] = gk
        out[f"n_{k}"] = int(ok.sum())
        if k == 1:
            b0_lag1 = float(f["b0"][ok].mean())
        else:
            num += gk * ok.sum()
            den += ok.sum()
    if den == 0 or "gamma_1" not in out:
        return out
    s2_trend = num / den
    s2_iid = s2_trend - out["gamma_1"] - b0_lag1
    s2_rw = out["gamma_0"] - s2_trend - 2 * s2_iid - f["B"].mean()
    out.update({"s2_trend": s2_trend, "s2_iid": s2_iid, "s2_rw": s2_rw,
                "autocorr_2plus": s2_trend / out["gamma_0"]})
    return out


def forecast_rows_trend(d: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """One-year-ahead forecast of log yield by a least-squares line through the previous n
    consecutive years, extrapolated one year: error e and its binomial variance bn."""
    g = d.groupby("unit")
    x = np.arange(n, dtype=float)
    xb, sxx = x.mean(), ((x - x.mean()) ** 2).sum()
    w = 1 / n + (n - xb) * (x - xb) / sxx  # weight on the year t-n+j, j = 0..n-1
    ok = (d["year"] - g["year"].shift(n) == n)
    pred = 0.0
    bn = d["b"].copy()
    for j in range(n):
        lag = n - j
        L = g["l"].shift(lag)
        ok &= L.notna()
        pred = pred + w[j] * L
        bn = bn + w[j] ** 2 * g["b"].shift(lag)
    return pd.DataFrame({"unit": d["unit"][ok], "year": d["year"][ok], "e": (d["l"] - pred)[ok], "bn": bn[ok]})


def by_target_year(d: pd.DataFrame) -> pd.DataFrame:
    """Point estimates per year: year-over-year change (school-specific excess SD, national mean
    change) and the three-cohort forecast error (excess SD around the year's mean error, mean
    error). SDs on the log scale, binomial removed."""
    f = first_differences(d)
    r3 = forecast_rows(d, 3)
    rows = []
    for y in sorted(set(f["year"]) | set(r3["year"])):
        row = {"year": int(y)}
        g = f[f["year"] == y]
        if len(g) >= 10:
            row.update({"fd_n": len(g), "fd_mean": g["d"].mean(),
                        "fd_s_unit": np.sqrt(max((g["d"].var() - g["B"].mean()) / 2, 0))})
        h = r3[r3["year"] == y]
        if len(h) >= 10:
            row.update({"fe3_n": len(h), "fe3_mean": h["e"].mean(),
                        "fe3_s_unit": np.sqrt(max(h["e"].var() - h["bn"].mean(), 0)),
                        "fe3_s_total_about0": np.sqrt(max((h["e"] ** 2).mean() - h["bn"].mean(), 0))})
        rows.append(row)
    return pd.DataFrame(rows)


def forecast_rows(d: pd.DataFrame, k: int) -> pd.DataFrame:
    """One-year-ahead forecast of log yield by the mean of the previous k consecutive years:
    error e and its binomial variance bn (target year plus the k inputs)."""
    g = d.groupby("unit")
    lags = [g["l"].shift(j) for j in range(1, k + 1)]
    blags = [g["b"].shift(j) for j in range(1, k + 1)]
    alags = [g["la"].shift(j) for j in range(1, k + 1)]
    ok = (d["year"] - g["year"].shift(k) == k)
    for L in lags:
        ok &= L.notna()
    return pd.DataFrame({"unit": d["unit"][ok], "year": d["year"][ok],
                         "e": (d["l"] - sum(lags) / k)[ok], "bn": (d["b"] + sum(blags) / k**2)[ok],
                         "x": (d["la"] - sum(alags) / k)[ok]})


def fe_stats(r: pd.DataFrame, control: bool = False) -> dict:
    """Excess forecast-error variance. total: national shocks kept (overall mean error removed);
    unit: each target year's mean error removed. control: the error is first regressed on the
    change in log admit rate from the same base (common slope), as estimator (c) does for
    first differences, so planned admit-rate changes are taken out."""
    if control:
        r = r[np.isfinite(r["x"])] if "x" in r else r.iloc[0:0]
    n = len(r)
    if n < 10:
        return {}
    if control:
        x = r["x"].to_numpy()
        e = r["e"].to_numpy()
        X = np.column_stack([np.ones(n), x])
        rt, _, bt = _resid(e, X)
        Xs = np.column_stack([_year_dummies(r["year"].to_numpy(), np.sort(r["year"].unique())), x])
        rs, ks, _ = _resid(e, Xs)
        return {"n": n, "targets": sorted(int(v) for v in r["year"].unique()), "slope_admit": bt[1],
                "s2_total": rt @ rt / (n - 2) - r["bn"].mean(), "s2_unit": rs @ rs / (n - ks) - r["bn"].mean()}
    et = r["e"] - r["e"].mean()
    eu = r["e"] - r.groupby("year")["e"].transform("mean")
    return {"n": n, "targets": sorted(int(x) for x in r["year"].unique()),
            "s2_total": (et**2).sum() / (n - 1) - r["bn"].mean(),
            "s2_unit": (eu**2).sum() / (n - r["year"].nunique()) - r["bn"].mean()}


def forecast_errors(d: pd.DataFrame, ks=(1, 2, 3)) -> dict:
    return {k: fe_stats(forecast_rows(d, k)) for k in ks}


def multiplicative_check(f: pd.DataFrame, d: pd.DataFrame, nbins: int = 5) -> pd.DataFrame:
    """Unit-specific excess spread of yield changes by bins of the unit's mean yield, on the log
    scale (constant if multiplicative) and in levels (constant if additive)."""
    ym = d.groupby("unit")["y"].mean()
    bins = pd.qcut(ym, nbins, labels=False, duplicates="drop")
    f = f.copy()
    f["bin"] = f["unit"].map(bins)
    f["dr"] = f["d"] - f.groupby("year")["d"].transform("mean")
    f["dyr"] = f["dy"] - f.groupby("year")["dy"].transform("mean")
    rows = []
    for bn, g in f.groupby("bin"):
        units = g["unit"].unique()
        rows.append({"bin": int(bn), "units": len(units), "mean_yield": ym.loc[units].mean(),
                     "s2_log": ((g["dr"] ** 2).mean() - g["B"].mean()) / 2,
                     "s2_level": ((g["dyr"] ** 2).mean() - g["Bl"].mean()) / 2})
    out = pd.DataFrame(rows)
    out["s_log"] = np.sqrt(out["s2_log"].clip(lower=0))
    out["s_level_pp"] = 100 * np.sqrt(out["s2_level"].clip(lower=0))
    out["s_level_over_mean"] = np.sqrt(out["s2_level"].clip(lower=0)) / out["mean_yield"]
    return out


def mult_slope(mc: pd.DataFrame) -> float:
    """Slope of log(level excess variance) on log(mean yield): 2 if multiplicative, 0 if additive."""
    ok = mc["s2_level"] > 0
    if ok.sum() < 3:
        return float("nan")
    return float(np.polyfit(np.log(mc.loc[ok, "mean_yield"]), np.log(mc.loc[ok, "s2_level"]), 1)[0])


# ------------------------------------------------------------------ fast core (point and bootstrap)
class Prepared:
    """Per-unit arrays built once, so a bootstrap draw only concatenates."""

    def __init__(self, d: pd.DataFrame, years):
        self.years = list(years)
        f = first_differences(d)
        self.fd = {u: {k: g[k].to_numpy() for k in ("year", "d", "B", "b0", "dla")}
                   for u, g in f.groupby("unit", sort=False)}
        self.lv = {p["unit"]: p for p in level_pieces(d, self.years)}
        self.fe = {}
        for k in (1, 2, 3, 5, "t5"):
            r = forecast_rows_trend(d, 5) if k == "t5" else forecast_rows(d, k)
            cols = ("year", "e", "bn") + (("x",) if "x" in r else ())
            self.fe[k] = {u: {c: g[c].to_numpy() for c in cols} for u, g in r.groupby("unit", sort=False)}
        self.units = np.array(sorted(set(self.fd) | set(self.lv)), dtype=object)

    def stats(self, pick) -> dict:
        fd = [self.fd[u] for u in pick if u in self.fd]
        out = {}
        if fd:
            cat = {k: np.concatenate([x[k] for x in fd]) for k in ("year", "d", "B", "b0", "dla")}
            uid = np.concatenate([np.full(len(x["d"]), i) for i, x in enumerate(fd)])
            ff = pd.DataFrame({"unit": uid, **cat})
            out["a"] = est_fd(ff)
            out["c_fd"] = est_fd(ff, control=True)
            out["persist"] = persistence(ff)
            if len(self.years) >= 5:
                out["persist2"] = persistence_lags(ff)
        pcs = [self.lv[u] for u in pick if u in self.lv]
        out["b"] = est_lv(pcs, self.years)
        out["c_lv"] = est_lv(pcs, self.years, control=True)
        for k, byu in self.fe.items():
            xs = [byu[u] for u in pick if u in byu]
            if xs:
                fr = pd.DataFrame({c: np.concatenate([x[c] for x in xs]) for c in xs[0]})
                out[f"fe{k}"] = fe_stats(fr)
                if k in (1, 3):
                    out[f"fe{k}c"] = fe_stats(fr, control=True)
        return out


KEYS = [("a", "s2_total"), ("a", "s2_unit"), ("a", "s2_national"),
        ("b", "s2_total"), ("b", "s2_unit"), ("b", "s2_national"), ("b", "s2_national_yeareff"),
        ("c_fd", "s2_total"), ("c_fd", "s2_unit"), ("c_fd", "slope_admit"),
        ("c_lv", "s2_total"), ("c_lv", "s2_unit"), ("c_lv", "slope_admit"),
        ("persist", "s2_iid"), ("persist", "s2_rw"), ("persist", "autocorr_d"),
        ("fe1", "s2_total"), ("fe1", "s2_unit"), ("fe2", "s2_total"), ("fe2", "s2_unit"),
        ("fe3", "s2_total"), ("fe3", "s2_unit"), ("fe5", "s2_total"), ("fe5", "s2_unit"),
        ("fet5", "s2_total"), ("fet5", "s2_unit"), ("fe1c", "s2_total"), ("fe1c", "s2_unit"), ("fe1c", "slope_admit"),
        ("fe3c", "s2_total"), ("fe3c", "s2_unit"), ("fe3c", "slope_admit"),
        ("persist2", "s2_trend"), ("persist2", "s2_iid"), ("persist2", "s2_rw"),
        ("persist2", "gamma_1"), ("persist2", "gamma_2"), ("persist2", "gamma_3"), ("persist2", "gamma_4")]


def sd(x):
    return float(np.sqrt(max(x, 0.0))) if x is not None and np.isfinite(x) else float("nan")


def point_and_boot(d: pd.DataFrame, years, reps: int = 2000, seed: int = 37) -> tuple[dict, dict]:
    """Point estimates and school-resampling percentile 95% intervals (s2 keys as SDs)."""
    P = Prepared(d, years)
    point = P.stats(P.units)
    rng = np.random.default_rng(seed)
    draws = {k: [] for k in KEYS}
    for _ in range(reps):
        res = P.stats(rng.choice(P.units, size=len(P.units), replace=True))
        for k in KEYS:
            draws[k].append(res.get(k[0], {}).get(k[1], np.nan))
    ci = {}
    for k, v in draws.items():
        v = np.asarray(v, float)
        if k[1].startswith("s2"):
            v = np.sqrt(np.clip(v, 0, None))
        v = v[np.isfinite(v)]
        ci[k] = (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) else (np.nan, np.nan)
    return point, ci
