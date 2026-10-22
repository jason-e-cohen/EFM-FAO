"""Synthetic institution generator.

Seeded from aggregate distributions observed in two prior engagements (residency mix,
athlete share, funnel conversion, merit-award clustering, discount levels), then deliberately
strengthened so that causal structure is present and *recoverable*:

  1. A published merit grid (sharp thresholds on HS GPA)  -> regression-discontinuity variation.
  2. A randomized, positive-only "bonus aid" price test    -> experimental variation.
  3. Discretionary aid targeted on staff-perceived fit     -> realistic negative selection that
     makes the naive aid coefficient misleading (the legacy "aid lowers yield" puzzle).
  4. Aid components recorded as offered / accepted / disbursed, with some recorded only after
     enrollment                                            -> reproduces the legacy leakage trap.

Latent truth lives in truth_admits.csv, which is for validation only.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from scipy.optimize import brentq
from scipy.special import expit

from . import world

SOURCES = ["Purchased list", "Test-score search", "Event or visit", "Inquiry form",
           "Referral", "Application-originated", "Other"]
SRC_P = np.array([0.34, 0.20, 0.09, 0.15, 0.04, 0.06, 0.12]); SRC_P = SRC_P / SRC_P.sum()
SRC_APPLY_FX = {"Purchased list": -0.6, "Test-score search": -0.2, "Event or visit": 0.9,
                "Inquiry form": 0.6, "Referral": 0.5, "Application-originated": 0.0, "Other": 0.0}
SRC_U_SHIFT = {"Purchased list": -0.3, "Test-score search": -0.2, "Event or visit": 0.5,
               "Inquiry form": 0.3, "Referral": 0.4, "Application-originated": 0.3, "Other": 0.0}
RACES = ["White", "Black or African American", "Hispanic/Latino", "Asian", "Two or more races", "Unknown"]
RACE_P = np.array([0.64, 0.085, 0.10, 0.04, 0.06, 0.075]); RACE_P = RACE_P / RACE_P.sum()
RACE_NEED_SHIFT = {"White": 0.0, "Black or African American": 0.55, "Hispanic/Latino": 0.40,
                   "Asian": -0.10, "Two or more races": 0.15, "Unknown": 0.05, "Nonresident alien": -0.3}
PROGRAMS = ["Health", "STEM", "Business", "Education", "Arts & Humanities", "Social Sciences", "Undecided"]
PROG_P = np.array([0.22, 0.15, 0.17, 0.10, 0.10, 0.12, 0.14])
N_INQ = {2022: 22500, 2023: 23200, 2024: 23800, 2025: 24200, 2026: 24600, 2027: 24900}
TARGET_APPLY = 0.032        # share of non-application-originated inquiries who apply
TARGET_ADMIT = 0.89
TARGET_YIELD_FTF = 0.205
TARGET_FAFSA = 0.74


def merit_grid_ftf(gpa: np.ndarray, grid) -> np.ndarray:
    out = np.full(len(gpa), float(grid[-1][1]))
    for lo, amt in reversed(grid):
        out = np.where(gpa >= lo, amt, out)
    return out


def merit_transfer(gpa: np.ndarray) -> np.ndarray:
    return np.where(gpa >= 3.5, 8000.0, np.where(gpa >= 3.0, 5000.0, 2500.0))


def _calibrate_intercept(score: np.ndarray, target: float) -> float:
    return brentq(lambda c: expit(score + c).mean() - target, -25, 25)


def build_cohort(y: int, rng: np.random.Generator, cfg: dict) -> pd.DataFrame:
    n = N_INQ[y]
    tuition = cfg["pricing"]["tuition_fees"][y]
    coa = tuition + cfg["pricing"]["room_board"]
    df = pd.DataFrame(index=range(n))
    df["cohort"] = y
    df["student_key"] = [f"LS{y}{i:06d}" for i in range(n)]
    df["student_type"] = np.where(rng.random(n) < 0.085, "Transfer", "First-time freshman")
    r = rng.random(n)
    df["residency"] = np.where(r < 0.62, "In-state", np.where(r < 0.95, "Out-of-state", "International"))
    reg_in = rng.choice([f"R{i:02d}" for i in range(1, 7)], size=n, p=[.30, .22, .16, .14, .10, .08])
    reg_out = rng.choice([f"R{i:02d}" for i in range(7, 12)], size=n)
    df["region"] = np.where(df.residency == "In-state", reg_in, np.where(df.residency == "Out-of-state", reg_out, "R12"))
    df["ability"] = rng.normal(0, 1, n) + np.where(df.residency == "Out-of-state", 0.1, 0.0)
    race = rng.choice(RACES, size=n, p=RACE_P)
    race = np.where(df.residency == "International", "Nonresident alien", race)
    df["race_ethnicity"] = race
    df["need_latent"] = rng.normal(0, 1, n) + pd.Series(race).map(RACE_NEED_SHIFT).to_numpy()
    df["first_gen"] = (rng.random(n) < expit(-0.9 + 0.7 * df.need_latent)).astype(int)
    df["gender"] = rng.choice(["Female", "Male", "Another or unknown"], size=n, p=[0.58, 0.39, 0.03])
    df["athlete"] = (rng.random(n) < 0.046).astype(int)
    df["program_area"] = rng.choice(PROGRAMS, size=n, p=PROG_P / PROG_P.sum())
    df["source_category"] = rng.choice(SOURCES, size=n, p=SRC_P)
    df["first_touch_is_application"] = (df.source_category == "Application-originated").astype(int)
    df["u"] = rng.normal(0, 1, n) + df.source_category.map(SRC_U_SHIFT).to_numpy()
    df["campus_visit"] = (rng.random(n) < expit(-1.6 + 0.9 * df.u + 0.8 * (df.source_category == "Event or visit"))).astype(int)
    df["engagement_touches"] = rng.poisson(np.exp(0.7 + 0.5 * df.u + 0.5 * df.campus_visit))
    gpa = np.clip(np.round(3.25 + 0.42 * df.ability + 0.12 * rng.normal(0, 1, n), 2), 2.0, 4.0)
    df["gpa_true"] = gpa
    act = np.clip(np.round(21.5 + 4.2 * df.ability + 1.5 * rng.normal(0, 1, n)), 12, 36)
    df["act_true"] = act
    df["inquiry_lead_days"] = np.round(np.exp(6.0 + 0.3 * rng.normal(0, 1, n) + 0.15 * df.u)).astype(int)
    # --- application ---
    score = (SRC_APPLY_FX_arr(df.source_category) + 0.55 * df.u + 0.25 * df.ability
             + np.where(df.residency == "In-state", 0.4, np.where(df.residency == "Out-of-state", -0.2, -0.7))
             + 1.3 * df.athlete + 0.3 * (df.inquiry_lead_days > 365)).to_numpy()
    non_app = (df.first_touch_is_application == 0).to_numpy()
    c = _calibrate_intercept(score[non_app], TARGET_APPLY)
    p_apply = np.where(non_app, expit(score + c), 1.0)
    df["applied"] = (rng.random(n) < p_apply).astype(int)
    app_lead = np.exp(5.0 + 0.2 * df.u + 0.5 * rng.normal(0, 1, n))
    app_lead = np.where(non_app, np.minimum(df.inquiry_lead_days * rng.uniform(0.25, 0.9, n), app_lead * 1.4), app_lead)
    df["app_lead_days"] = np.maximum(14, np.round(app_lead)).astype(int)
    df.loc[df.applied == 0, "app_lead_days"] = np.nan
    # --- admission ---
    a_score = (1.4 * df.ability + 0.2 * df.u + 0.5 * df.athlete).to_numpy()
    app_mask = (df.applied == 1).to_numpy()
    c2 = _calibrate_intercept(a_score[app_mask], TARGET_ADMIT)
    df["admitted"] = 0
    df.loc[app_mask, "admitted"] = (rng.random(app_mask.sum()) < expit(a_score[app_mask] + c2)).astype(int)
    adm = (df.admitted == 1).to_numpy()
    # --- need / FAFSA (admits only) ---
    f_score = (0.8 * df.need_latent + 0.5 * df.u).to_numpy()
    c3 = _calibrate_intercept(f_score[adm], TARGET_FAFSA)
    df["fafsa_filed"] = np.nan
    df.loc[adm, "fafsa_filed"] = (rng.random(adm.sum()) < expit(f_score[adm] + c3)).astype(int)
    raw_need = 16000 - 11500 * df.need_latent + 6000 * rng.normal(0, 1, n)
    efc_like = np.maximum(0, raw_need) if y <= 2023 else np.maximum(-1500, raw_need - 1500)
    df["need_index"] = np.where(df.fafsa_filed == 1, np.round(efc_like), np.nan)
    df["need_index_type"] = np.where(df.fafsa_filed == 1, "EFC" if y <= 2023 else "SAI", None)
    df["tuition"] = tuition; df["coa"] = coa
    return df


def SRC_APPLY_FX_arr(s: pd.Series) -> pd.Series:
    return s.map(SRC_APPLY_FX)


def add_aid(df: pd.DataFrame, rng: np.random.Generator, cfg: dict) -> pd.DataFrame:
    """Aid offered at the decision point (known), plus latent bookkeeping."""
    n = len(df); grid = cfg["aid_policy"]["merit_grid_ftf"]
    adm = (df.admitted == 1).to_numpy()
    fafsa = (df.fafsa_filed == 1).to_numpy()
    is_tr = (df.student_type == "Transfer").to_numpy()
    merit = np.where(is_tr, merit_transfer(df.gpa_true.to_numpy()), merit_grid_ftf(df.gpa_true.to_numpy(), grid))
    df["inst_merit"] = np.where(adm, merit, 0.0)
    ni = df.need_index.fillna(1e6).to_numpy()
    gap = np.maximum(0, df.coa.to_numpy() - np.maximum(ni, 0))
    need_grant = np.minimum(9000, np.round(0.25 * np.maximum(0, gap - 20000), -2))
    df["inst_need"] = np.where(adm & fafsa, need_grant, 0.0)
    ath_amt = rng.choice([0, 4000, 8000, 12000], size=n, p=[0.2, 0.3, 0.3, 0.2])
    df["inst_athletic"] = np.where(adm & (df.athlete == 1), ath_amt, 0.0)
    n_obs = np.where(fafsa, df.need_latent.to_numpy(), 0.0)
    perceived_fit = df.u.to_numpy() + rng.normal(0, 0.8, n)
    dscore = 1.1 * np.clip(df.ability.to_numpy(), -1, 2) + 0.8 * n_obs - 0.9 * perceived_fit + rng.normal(0, 0.7, n)
    disc = np.clip(np.round((2200 + 1800 * dscore) / 500) * 500, 0, cfg["aid_policy"]["discretionary_max"])
    df["inst_discretionary_base"] = np.where(adm & (df.athlete == 0), disc, 0.0)
    df["state_grant"] = np.where(adm & fafsa & (df.residency == "In-state") & (ni < 12000),
                                 np.round(rng.uniform(1500, 3500, n), -2), 0.0)
    pell = np.clip(7395 * (1 - np.maximum(ni, 0) / 6700), 0, 7395)
    df["pell"] = np.where(adm & fafsa & (df.residency != "International") & (pell >= 740), np.round(pell, -2), 0.0)
    df["seog"] = np.where((df.pell >= 5000) & (rng.random(n) < 0.25), 1000.0, 0.0)
    ext_has = (rng.random(n) < 0.10) & adm
    df["ext_amt"] = np.where(ext_has, np.round(rng.uniform(500, 5000, n) / 250) * 250, 0.0)
    df["ext_known"] = (ext_has & (rng.random(n) < 0.35)).astype(int)
    ftf_f = adm & fafsa & ~is_tr
    df["sub_loan"] = np.where(ftf_f & (ni < df.coa.to_numpy()), 3500.0, 0.0)
    df["unsub_loan"] = np.where(ftf_f, 2000.0, 0.0)
    df["parent_plus"] = np.where(ftf_f & (rng.random(n) < 0.30), 10000.0, 0.0)
    df["work_study"] = np.where(adm & fafsa & (ni < 12000), 2500.0, 0.0)
    df["loans_offered"] = df.sub_loan + df.unsub_loan + df.parent_plus
    return df


def assign_price_test(df: pd.DataFrame, rng: np.random.Generator, cfg: dict) -> pd.DataFrame:
    ex = cfg["experiment"]; n = len(df)
    elig = ((df.admitted == 1) & (df.athlete == 0) & (df.student_type == "First-time freshman")
            & df.cohort.isin(ex["price_test_cohorts"])).to_numpy()
    flag = elig & (rng.random(n) < ex["share_of_eligible"])
    off = rng.choice(ex["offsets_usd"], size=n)
    df["in_price_test"] = flag.astype(int)
    df["test_offset"] = np.where(flag, off, 0.0)
    df["inst_discretionary"] = df.inst_discretionary_base + df.test_offset
    return df


def finalize_truth_fields(df: pd.DataFrame) -> pd.DataFrame:
    df["nondisc_gift_known"] = (df.inst_merit + df.inst_need + df.inst_athletic + df.state_grant
                                + df.pell + df.seog + df.ext_amt * df.ext_known)
    df["gift_known"] = df.nondisc_gift_known + df.inst_discretionary
    return df


def generate(cfg: dict, seed: int = 20261014) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    cohorts = cfg["cycle"]["historical_cohorts"] + [cfg["cycle"]["live_cohort"]]
    frames = []
    for y in cohorts:
        d = build_cohort(y, rng, cfg); d = add_aid(d, rng, cfg); d = assign_price_test(d, rng, cfg)
        if y == cfg["cycle"]["live_cohort"]:
            d["in_price_test"] = 0; d["test_offset"] = 0.0; d["inst_discretionary"] = d.inst_discretionary_base
        frames.append(finalize_truth_fields(d))
    full = pd.concat(frames, ignore_index=True)
    hist_adm = full[(full.admitted == 1) & (full.cohort <= cfg["cycle"]["historical_cohorts"][-1])
                    & (full.student_type == "First-time freshman")]
    b0 = world.calibrate_b0(hist_adm, hist_adm.gift_known.to_numpy(), TARGET_YIELD_FTF)
    adm = (full.admitted == 1).to_numpy()
    sub = full[adm]
    p_true = world.p_enroll(sub, b0, sub.gift_known.to_numpy())
    p_dep = world.p_deposit(sub, b0, sub.gift_known.to_numpy())
    melt = world.melt_prob(sub)
    ame = world.true_ame_per_1k(sub, b0, sub.gift_known.to_numpy())
    full["p_enroll_true"] = np.nan; full.loc[adm, "p_enroll_true"] = p_true
    full["true_ame_per_1k"] = np.nan; full.loc[adm, "true_ame_per_1k"] = ame
    live = (full.cohort == cfg["cycle"]["live_cohort"]).to_numpy()
    dep = rng.random(adm.sum()) < p_dep
    mel = rng.random(adm.sum()) < melt
    full["deposited"] = np.nan; full["enrolled"] = np.nan; full["retained_y2"] = np.nan
    full.loc[adm, "deposited"] = dep.astype(int)
    full.loc[adm, "enrolled"] = (dep & ~mel).astype(int)
    full.loc[live, ["deposited", "enrolled"]] = np.nan          # live cycle: outcomes unknown
    enr = (full.enrolled == 1).to_numpy()
    p_ret = expit(1.1 + 0.5 * full.ability + 0.3 * full.campus_visit - 0.25 * full.need_latent)
    ret = rng.random(len(full)) < p_ret
    known_ret = enr & (full.cohort <= cfg["cycle"]["historical_cohorts"][-2]).to_numpy()
    full.loc[known_ret, "retained_y2"] = ret[known_ret].astype(int)
    # observed-data masking
    app = (full.applied == 1).to_numpy()
    miss_gpa = rng.random(len(full)) < np.where(app, 0.05, 0.30)
    ftf = (full.student_type == "First-time freshman").to_numpy()
    full["hs_gpa"] = np.where(ftf & ~miss_gpa, full.gpa_true, np.nan)
    full["transfer_gpa"] = np.where(~ftf & ~miss_gpa, full.gpa_true, np.nan)
    sub_act = rng.random(len(full)) < np.where(app, expit(0.2 + 0.5 * full.ability), 0.55)
    full["act"] = np.where(sub_act, full.act_true, np.nan)
    full.attrs["b0"] = float(b0)
    return {"full": full}


def to_tables(full: pd.DataFrame, cfg: dict) -> dict[str, pd.DataFrame]:
    """Split the wide simulation frame into the tables the improved data request asks clients for."""
    rng = np.random.default_rng(7)
    stu_cols = ["student_key", "cohort", "student_type", "residency", "region", "source_category",
                "first_touch_is_application", "inquiry_lead_days", "engagement_touches", "campus_visit",
                "first_gen", "race_ethnicity", "gender", "athlete", "program_area", "hs_gpa", "transfer_gpa",
                "act", "applied", "app_lead_days", "admitted", "fafsa_filed", "need_index", "need_index_type",
                "deposited", "enrolled", "retained_y2"]
    students = full[stu_cols].copy()
    enr = (full.enrolled == 1).to_numpy(); adm = (full.admitted == 1).to_numpy()
    rows = []
    comps = [("inst_merit", "Gift", "Institutional"), ("inst_need", "Gift", "Institutional"),
             ("inst_athletic", "Gift", "Institutional"), ("inst_discretionary", "Gift", "Institutional"),
             ("state_grant", "Gift", "State"), ("pell", "Gift", "Federal"), ("seog", "Gift", "Federal"),
             ("sub_loan", "Self-help", "Federal"), ("unsub_loan", "Self-help", "Federal"),
             ("parent_plus", "Self-help", "Federal"), ("work_study", "Self-help", "Federal")]
    for comp, cat, lvl in comps:
        amt = full[comp].to_numpy(); m = adm & (amt > 0)
        t = full.loc[m, ["student_key", "cohort"]].copy()
        t["component"] = comp; t["aid_category"] = cat; t["funding_source"] = lvl
        t["offered_amount"] = amt[m]; t["known_at_decision"] = 1
        e = enr[m]
        t["accepted_amount"] = np.where(e, amt[m], np.nan)      # recorded only after the student responds
        t["disbursed_amount"] = np.where(e, amt[m], np.nan)     # exists only for enrolled students
        rows.append(t)
    ext = adm & (full.ext_amt.to_numpy() > 0)
    reported = ext & ((full.ext_known.to_numpy() == 1) | (enr & (rng.random(len(full)) < 0.8)))
    t = full.loc[reported, ["student_key", "cohort"]].copy()
    t["component"] = "external_scholarship"; t["aid_category"] = "Gift"; t["funding_source"] = "External"
    t["offered_amount"] = full.loc[reported, "ext_amt"].to_numpy()
    t["known_at_decision"] = full.loc[reported, "ext_known"].to_numpy()
    t["accepted_amount"] = np.where(enr[reported], t.offered_amount, np.nan)
    t["disbursed_amount"] = t["accepted_amount"]
    rows.append(t)
    aid = pd.concat(rows, ignore_index=True)
    pt = full.loc[full.in_price_test == 1, ["student_key", "cohort", "test_offset"]].rename(columns={"test_offset": "offset_usd"})
    pt["randomization_batch"] = "RB-" + pt.cohort.astype(str)
    pricing = pd.DataFrame({"cohort": list(cfg["pricing"]["tuition_fees"].keys()),
                            "tuition_fees": list(cfg["pricing"]["tuition_fees"].values())})
    pricing["room_board"] = cfg["pricing"]["room_board"]
    tcols = ["student_key", "cohort", "u", "ability", "need_latent", "gpa_true", "residency", "first_gen", "athlete",
             "student_type", "campus_visit", "engagement_touches", "fafsa_filed", "app_lead_days", "program_area",
             "loans_offered", "coa", "tuition", "nondisc_gift_known", "inst_merit", "inst_need", "inst_athletic",
             "inst_discretionary", "p_enroll_true", "true_ame_per_1k", "admitted", "in_price_test"]
    truth = full.loc[adm, tcols].copy()
    return {"students": students, "aid_offers": aid, "price_test": pt, "pricing": pricing, "truth_admits": truth}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/institution.yaml")
    ap.add_argument("--out", default="data/synthetic")
    ap.add_argument("--seed", type=int, default=20261014)
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config))
    full = generate(cfg, a.seed)["full"]
    tabs = to_tables(full, cfg)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    for k, v in tabs.items():
        v.to_csv(out / f"{k}.csv", index=False)
    json.dump({"b0": full.attrs["b0"], "seed": a.seed, "synthetic": True}, open(out / "world_meta.json", "w"))
    print({k: v.shape for k, v in tabs.items()})


if __name__ == "__main__":
    main()
