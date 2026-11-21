"""Check that the estimators recover a known s on simulated panels shaped like the law panel.

Each world: 195 schools x 5 years, offers drawn around the law panel's spread (median about
600), base yield 0.2 to 0.5, a school-specific linear trend, a national year effect, and
enrollment ~ Binomial(offers, yield). Shocks are either iid each year around the school's
level (the workbook's model) or a random walk (persistent). 200 worlds each.

  .venv/bin/python -I analysis/o37_shock_calibration/validate_estimators.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estimators as E  # noqa: E402


def world(rng, s_u, s_n, kind, n=195, years=range(2021, 2026)):
    years = list(years)
    T = len(years)
    nat = rng.normal(0, s_n, T)
    rows = []
    for i in range(n):
        offers = np.maximum(80, rng.lognormal(np.log(600), 0.5) * np.exp(rng.normal(0, 0.08, T))).round()
        base = np.log(rng.uniform(0.2, 0.5))
        trend = rng.normal(0, 0.01)
        if kind == "iid":
            u = rng.normal(0, s_u, T)
        else:
            u = np.cumsum(rng.normal(0, s_u, T))
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
