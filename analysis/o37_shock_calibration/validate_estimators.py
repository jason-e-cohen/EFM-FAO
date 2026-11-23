"""Check that the estimators recover a known s on simulated panels shaped like the law panel.

Each world: 195 schools x 5 years, offers drawn around the law panel's spread (median about
600), base yield 0.2 to 0.5, a school-specific linear trend, a national year effect, and
enrollment ~ Binomial(offers, yield). Shocks are either iid each year around the school's
level (the workbook's model) or a random walk (persistent). 200 worlds each.

Second block (Nov 23, 2026; results/validation_15yr.csv): 15-year panels like the 2011-2025
law panel, 100 worlds each, to check that the lag autocovariances separate school trends from
random-walk shocks (estimators.persistence_lags) and to see the forecast errors under each.

  .venv/bin/python -I analysis/o37_shock_calibration/validate_estimators.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estimators as E  # noqa: E402


def world(rng, s_u, s_n, kind, n=195, years=range(2021, 2026), trend_sd=0.01, s_rw=0.0, phi=0.6):
    years = list(years)
    T = len(years)
    nat = rng.normal(0, s_n, T)
    rows = []
    for i in range(n):
        offers = np.maximum(80, rng.lognormal(np.log(600), 0.5) * np.exp(rng.normal(0, 0.08, T))).round()
        base = np.log(rng.uniform(0.2, 0.5))
        trend = rng.normal(0, trend_sd)
        if kind == "iid":
            u = rng.normal(0, s_u, T)
        elif kind == "ar":
            u = np.zeros(T)
            u[0] = rng.normal(0, s_u / np.sqrt(1 - phi**2))
            for t in range(1, T):
                u[t] = phi * u[t - 1] + rng.normal(0, s_u)
        else:
            u = np.cumsum(rng.normal(0, s_u, T))
        if s_rw:
            u = u + np.cumsum(rng.normal(0, s_rw, T))
        p = np.clip(np.exp(base + trend * np.arange(T) + nat + u), 0.01, 0.95)
        enr = rng.binomial(offers.astype(int), p)
        apps = (offers / rng.uniform(0.2, 0.6)).round()
        for t, y in enumerate(years):
            rows.append({"unit": i, "year": y, "offers": offers[t], "enrollees": enr[t], "apps": apps[t]})
    return pd.DataFrame(rows)


def main() -> int:
    rng = np.random.default_rng(2026)
    out = []
    for kind, s_u, s_n in (("iid", 0.06, 0.03), ("iid", 0.10, 0.0), ("rw", 0.06, 0.03)):
        res = []
        for _ in range(200):
            d = E.prep(world(rng, s_u, s_n, kind))
            years = sorted(d["year"].unique())
            st = E.Prepared(d, years).stats(d["unit"].unique())
            res.append({"a_unit": st["a"]["s2_unit"], "a_total": st["a"]["s2_total"], "b_unit": st["b"]["s2_unit"],
                        "b_total": st["b"]["s2_total"], "persist_iid": st["persist"]["s2_iid"],
                        "persist_rw": st["persist"]["s2_rw"], "autocorr": st["persist"]["autocorr_d"],
                        "fe1_unit": st["fe1"]["s2_unit"], "fe3_unit": st["fe3"]["s2_unit"]})
        r = pd.DataFrame(res)
        summ = {k: (float(np.sqrt(max(r[k].mean(), 0))) if k != "autocorr" else float(r[k].mean())) for k in r}
        summ.update({"kind": kind, "true_s_unit": s_u, "true_s_national": s_n})
        out.append(summ)
    df = pd.DataFrame(out).set_index(["kind", "true_s_unit", "true_s_national"])
    print(df.round(4).T.to_string())
    (Path(__file__).resolve().parent / "results").mkdir(exist_ok=True)
    df.to_csv(Path(__file__).resolve().parent / "results" / "validation.csv")

    out = []
    worlds = [  # (label, kind, s_u, trend_sd, s_rw)
        ("iid 0.06, no trend", "iid", 0.06, 0.0, 0.0),
        ("random walk 0.06, no trend", "rw", 0.06, 0.0, 0.0),
        ("iid 0.04 + trends sd 0.02/yr", "iid", 0.04, 0.02, 0.0),
        ("iid 0.03 + random walk 0.06 + trends sd 0.01/yr", "iid", 0.03, 0.01, 0.06),
        ("AR(1) phi 0.6, innovation 0.06", "ar", 0.06, 0.0, 0.0),
    ]
    for lab, kind, s_u, tsd, srw in worlds:
        res = []
        for _ in range(100):
            d = E.prep(world(rng, s_u, 0.03, kind, years=range(2011, 2026), trend_sd=tsd, s_rw=srw))
            st = E.Prepared(d, sorted(d["year"].unique())).stats(d["unit"].unique())
            p2 = st["persist2"]
            res.append({"trend": p2["s2_trend"], "iid": p2["s2_iid"], "rw": p2["s2_rw"],
                        "gamma_2_x1000": 1000 * p2["gamma_2"], "gamma_3_x1000": 1000 * p2["gamma_3"],
                        "a_total": st["a"]["s2_total"], "fe1_total": st["fe1"]["s2_total"],
                        "fe3_total": st["fe3"]["s2_total"], "fet5_total": st["fet5"]["s2_total"]})
        r = pd.DataFrame(res)
        summ = {k: (float(np.sqrt(max(r[k].mean(), 0))) if not k.startswith("gamma") else float(r[k].mean())) for k in r}
        summ["trend_signed_mean"] = float(r["trend"].mean())
        summ.update({"world": lab, "true_trend_sd": tsd})
        out.append(summ)
    df = pd.DataFrame(out).set_index("world")
    print(df.round(4).T.to_string())
    df.to_csv(Path(__file__).resolve().parent / "results" / "validation_15yr.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
