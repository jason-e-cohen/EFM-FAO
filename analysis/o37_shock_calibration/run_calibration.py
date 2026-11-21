"""Estimate s (O37) on the law and undergraduate panels; write results/ tables.

  .venv/bin/python -I analysis/o37_shock_calibration/run_calibration.py [--reps-law 2000] [--reps-ug 400]

Reads data/law_panel.csv and data/ug_panel.csv (build_law_panel.py, build_ug_panel.py).
Writes results/estimates.csv (every configuration x estimator x component, point SD and
school-resampling 95% interval), results/multiplicative.csv, results/year_effects.csv,
results/exclusions.csv and results/summary.json. Results are aggregates of public data and
name no school.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import estimators as E  # noqa: E402

DATA = HERE / "data"
RES = HERE / "results"

# Law exclusions (ids from the local crosswalk; see build_law_panel.py). Reasons, no names.
LAW_CLOSED = {9001: "closed (one compilation year, zero offers)", 9002: "closed (teach-out; class fell from about 120 to 25 over 2021 to 2023)"}
LAW_CONSOLIDATION = {(219, 2025): "consolidation: absorbed a campus that stopped reporting in 2025 (class up 0.70 in log)"}

LAW_BANDS = [("under 100", 0, 99.5), ("100 to 200 (peer band)", 99.5, 200.5), ("201 to 299", 200.5, 299.5), ("300 and over", 299.5, 1e9)]
UG_BANDS = [("under 300", 0, 299.5), ("300 to 999", 299.5, 999.5), ("1,000 to 2,999", 999.5, 2999.5), ("3,000 and over", 2999.5, 1e9)]

ROWS = [  # (estimator label, result key, component key)
    ("(a) first differences", "a", "s2_total"), ("(a) first differences", "a", "s2_unit"), ("(a) first differences", "a", "s2_national"),
    ("(b) level and trend", "b", "s2_total"), ("(b) level and trend", "b", "s2_unit"), ("(b) level and trend", "b", "s2_national_yeareff"),
    ("(c) first differences + admit rate", "c_fd", "s2_total"), ("(c) first differences + admit rate", "c_fd", "s2_unit"),
    ("(c) level and trend + admit rate", "c_lv", "s2_total"), ("(c) level and trend + admit rate", "c_lv", "s2_unit"),
    ("persistence: iid part", "persist", "s2_iid"), ("persistence: random-walk part", "persist", "s2_rw"),
    ("forecast error, last year (k=1)", "fe1", "s2_total"), ("forecast error, last year (k=1)", "fe1", "s2_unit"),
    ("forecast error, 2-year mean (k=2)", "fe2", "s2_total"), ("forecast error, 2-year mean (k=2)", "fe2", "s2_unit"),
    ("forecast error, 3-year mean (k=3)", "fe3", "s2_total"), ("forecast error, 3-year mean (k=3)", "fe3", "s2_unit"),
]
COMP = {"s2_total": "total", "s2_unit": "school-specific", "s2_national": "national", "s2_national_yeareff": "national",
        "s2_iid": "school-specific", "s2_rw": "school-specific"}


def law_frame(rule_implausible=True, scraped_2025=False):
    p = pd.read_csv(DATA / "law_panel.csv").rename(columns={"aba_school_id": "unit"})
    log = []
    if scraped_2025:
        p["enrollees"] = p["enrollees_scraped"]
    n0 = len(p)
    p = p[~p["unit"].isin(LAW_CLOSED)]
    log.append(("closures", n0 - len(p)))
    n1 = len(p)
    p = p[~p.apply(lambda r: (r["unit"], r["year"]) in LAW_CONSOLIDATION, axis=1)]
    log.append(("consolidation", n1 - len(p)))
    n2 = len(p)
    d = E.prep(p)
    log.append(("offers under 50 or enrollees under 10 (zero-offer rows)", n2 - len(d)))
    fl = E.flag_implausible(d)
    log.append(("implausible (log yield more than 0.5 from the school's median)", int(fl.sum())))
    if rule_implausible:
        d = d[~fl]
    size = d.groupby("unit")["total_fy"].median()
    d["size"] = d["unit"].map(size)
    return d.reset_index(drop=True), log


def ug_frame(rule_implausible=True):
    p = pd.read_csv(DATA / "ug_panel.csv").rename(columns={"unitid": "unit"})
    log = []
    n0 = len(p)
    d = E.prep(p, min_offers=100, min_enrolled=50)
    log.append(("offers under 100 or enrolled under 50", n0 - len(d)))
    fl = E.flag_implausible(d)
    log.append(("implausible (log yield more than 0.5 from the institution's median)", int(fl.sum())))
    if rule_implausible:
        d = d[~fl]
    size = d.groupby("unit")["enrollees"].median()
    d["size"] = d["unit"].map(size)
    return d.reset_index(drop=True), log


def run_config(vertical, name, d, reps, seed=37):
    years = sorted(d["year"].unique())
    t0 = time.time()
    point, ci = E.point_and_boot(d, years, reps=reps, seed=seed)
    rows = []
    for lab, k, c in ROWS:
        res = point.get(k, {})
        if c not in res:
            continue
        rows.append({"vertical": vertical, "config": name, "estimator": lab, "component": COMP.get(c, c),
                     "s": E.sd(res[c]), "lo95": ci.get((k, c), (np.nan, np.nan))[0], "hi95": ci.get((k, c), (np.nan, np.nan))[1],
                     "n_units": res.get("n_units", np.nan), "n_obs": res.get("n_obs", res.get("n", np.nan))})
    extra = {"autocorr_d": point.get("persist", {}).get("autocorr_d"), "autocorr_ci": ci.get(("persist", "autocorr_d")),
             "slope_admit_fd": point.get("c_fd", {}).get("slope_admit"), "slope_admit_fd_ci": ci.get(("c_fd", "slope_admit")),
             "slope_admit_lv": point.get("c_lv", {}).get("slope_admit"), "slope_admit_lv_ci": ci.get(("c_lv", "slope_admit")),
             "binom_share_fd": point.get("a", {}).get("binom_share_total"),
             "years": [int(y) for y in years], "n_units": int(d["unit"].nunique()), "n_unit_years": int(len(d)),
             "median_offers": float(d["offers"].median()), "median_yield": float(d["y"].median()),
             "median_class": float(d["enrollees"].median()),
             "fe_targets": {k: point.get(f"fe{k}", {}).get("targets") for k in (1, 2, 3)}}
    b = point.get("b", {})
    if "s2_national_yeareff" in b:
        df_ = max(len(years) - 2, 1)
        s2 = max(b["s2_national_yeareff"], 0)
        extra["national_chi2_95"] = (float(np.sqrt(s2 * df_ / st.chi2.ppf(0.975, df_))), float(np.sqrt(s2 * df_ / st.chi2.ppf(0.025, df_))))
        extra["year_effects"] = {int(k): float(v) for k, v in b["year_effects"].items()}
    print(f"  {vertical} | {name}: units {extra['n_units']}, unit-years {extra['n_unit_years']}, {time.time() - t0:.0f} s", flush=True)
    return rows, extra


def band_of(size, bands):
    for lab, lo, hi in bands:
        if lo <= size < hi:
            return lab
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps-law", type=int, default=2000)
    ap.add_argument("--reps-ug", type=int, default=400)
    a = ap.parse_args()
    RES.mkdir(exist_ok=True)
    rows, summary, mult, excl = [], {}, [], []

    law, log = law_frame()
    excl += [{"vertical": "law", "rule": r, "unit_years_removed": n} for r, n in log]
    law["band"] = law["size"].map(lambda s: band_of(s, LAW_BANDS))
    cfgs = [("main: all schools, 2021-2025", law)]
    for lab, _, _ in LAW_BANDS:
        cfgs.append((f"band {lab}, 2021-2025", law[law["band"] == lab]))
    late = law[law["year"] >= 2023]
    cfgs.append(("all schools, 2023-2025 (without 2021, 2022)", late))
    cfgs.append(("band 100 to 200 (peer band), 2023-2025", late[late["band"] == "100 to 200 (peer band)"]))
    cfgs.append(("all schools, 2022-2025 (without 2021)", law[law["year"] >= 2022]))
    for typ in ("private", "public"):
        cfgs.append((f"{typ} schools, 2021-2025", law[law["school_type"] == typ]))
    noflag, _ = law_frame(rule_implausible=False)
    cfgs.append(("sensitivity: implausible-jump rule off", noflag))
    scr, _ = law_frame(scraped_2025=True)
    cfgs.append(("sensitivity: 2025 scraped enrollee counts", scr))
    for name, d in cfgs:
        r, ex = run_config("law", name, d, a.reps_law)
        rows += r
        summary[f"law | {name}"] = ex
    for name, d in [("main: all schools, 2021-2025", law), ("band 100 to 200 (peer band), 2021-2025", law[law["band"] == "100 to 200 (peer band)"])]:
        mc = E.multiplicative_check(E.first_differences(d), d)
        mc.insert(0, "config", name)
        mc.insert(0, "vertical", "law")
        mult.append(mc)
        summary[f"law | {name}"]["mult_slope"] = E.mult_slope(mc)

    ug, log = ug_frame()
    excl += [{"vertical": "ug", "rule": r, "unit_years_removed": n} for r, n in log]
    ug["band"] = ug["size"].map(lambda s: band_of(s, UG_BANDS))
    ucfgs = [("main: four-year public and nonprofit, 2014-2023", ug)]
    for c, lab in ((2, "private nonprofit"), (1, "public")):
        ucfgs.append((f"{lab}, 2014-2023", ug[ug["control"] == c]))
    for lab, _, _ in UG_BANDS:
        ucfgs.append((f"band {lab} first-time enrolled, 2014-2023", ug[ug["band"] == lab]))
    ucfgs.append(("private nonprofit, 300 to 999 first-time enrolled, 2014-2023", ug[(ug["control"] == 2) & (ug["band"] == "300 to 999")]))
    ucfgs.append(("all, without 2020 and 2021", ug[~ug["year"].isin([2020, 2021])]))
    ucfgs.append(("all, 2019-2023 (five years, as law)", ug[ug["year"] >= 2019]))
    noflag, _ = ug_frame(rule_implausible=False)
    ucfgs.append(("sensitivity: implausible-jump rule off", noflag))
    for name, d in ucfgs:
        r, ex = run_config("ug", name, d, a.reps_ug)
        rows += r
        summary[f"ug | {name}"] = ex
    mc = E.multiplicative_check(E.first_differences(ug), ug)
    mc.insert(0, "config", "main")
    mc.insert(0, "vertical", "ug")
    mult.append(mc)
    summary["ug | main: four-year public and nonprofit, 2014-2023"]["mult_slope"] = E.mult_slope(mc)

    pd.DataFrame(rows).to_csv(RES / "estimates.csv", index=False)
    pd.concat(mult).to_csv(RES / "multiplicative.csv", index=False)
    pd.DataFrame(excl).to_csv(RES / "exclusions.csv", index=False)
    with open(RES / "summary.json", "w") as f:
        json.dump(summary, f, indent=1, default=lambda o: o if not isinstance(o, (np.floating, np.integer)) else o.item())
    print("wrote", RES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
