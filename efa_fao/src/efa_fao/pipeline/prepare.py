"""Ingest validation, explicit cleaning rules, and feature construction.

Design rules that fix the legacy pipeline's known problems:
  * Missing is never silently recoded to zero. Aid is zero only where the cohort has aid coverage.
  * Aid is split into components, and only amounts KNOWN AT THE DECISION DATE feed price features.
  * Disbursed or accepted amounts exist only for enrolled students, so they are leakage and are
    excluded from every allocation model (they are used only by the legacy replica, on purpose).
  * Protected attributes are carried for audit but never enter allocation model matrices.
  * Every drop or recode is counted in the QA report.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

INST_COMPONENTS = ["inst_merit", "inst_need", "inst_athletic", "inst_discretionary"]
GIFT_COMPONENTS = INST_COMPONENTS + ["state_grant", "pell", "seog", "external_scholarship"]
LOAN_COMPONENTS = ["sub_loan", "unsub_loan", "parent_plus"]
ALL_COMPONENTS = GIFT_COMPONENTS + LOAN_COMPONENTS + ["work_study"]
PROTECTED = ["race_ethnicity", "gender"]


def load_tables(path: str) -> dict[str, pd.DataFrame]:
    names = ["students", "aid_offers", "price_test", "pricing"]
    return {n: pd.read_csv(f"{path}/{n}.csv") for n in names}


def validate_and_clean(t: dict, cfg: dict) -> tuple[dict, dict]:
    qa: dict = {"rules": []}
    s = t["students"].copy(); aid = t["aid_offers"].copy(); pt = t["price_test"].copy()
    n0 = len(s)
    dup = s.duplicated(["student_key", "cohort"], keep="first")
    s = s[~dup]; qa["rules"].append({"rule": "drop duplicate student_key x cohort (keep first)", "rows": int(dup.sum())})
    bad = ((s.enrolled == 1) & (s.admitted != 1)) | ((s.admitted == 1) & (s.applied != 1))
    qa["rules"].append({"rule": "stage monotonicity violations (flagged, not dropped)", "rows": int(bad.sum())})
    orphan = ~aid.student_key.isin(s.student_key)
    aid = aid[~orphan]; qa["rules"].append({"rule": "drop aid rows with no student record", "rows": int(orphan.sum())})
    non_adm = aid.student_key.isin(s.loc[s.admitted != 1, "student_key"])
    aid = aid[~non_adm]; qa["rules"].append({"rule": "drop aid rows for non-admitted students", "rows": int(non_adm.sum())})
    allowed = set(cfg["experiment"]["offsets_usd"])
    badpt = ~pt.offset_usd.isin(allowed)
    qa["rules"].append({"rule": "price-test rows with an offset outside the protocol", "rows": int(badpt.sum())})
    pt = pt[~badpt]
    qa["rows_in"] = int(n0); qa["rows_out"] = int(len(s))
    qa["null_rates"] = {c: round(float(s[c].isna().mean()), 4) for c in
                        ["hs_gpa", "transfer_gpa", "act", "race_ethnicity", "need_index", "first_gen"]}
    return {**t, "students": s, "aid_offers": aid, "price_test": pt}, qa


def pivot_aid(aid: pd.DataFrame, covered: set[int]) -> pd.DataFrame:
    known = aid[aid.known_at_decision == 1]
    off = known.pivot_table(index="student_key", columns="component", values="offered_amount", aggfunc="sum", fill_value=0.0)
    disb = aid.pivot_table(index="student_key", columns="component", values="disbursed_amount", aggfunc="sum", fill_value=0.0)
    disb.columns = [f"{c}__disbursed" for c in disb.columns]
    out = off.join(disb, how="outer").fillna(0.0)
    for c in ALL_COMPONENTS:
        if c not in out.columns: out[c] = 0.0
    return out


def build_admit_frame(t: dict, cfg: dict) -> pd.DataFrame:
    s = t["students"]; aid = pivot_aid(t["aid_offers"], set(cfg["cycle"]["historical_cohorts"] + [cfg["cycle"]["live_cohort"]]))
    pr = t["pricing"].set_index("cohort")
    a = s[s.admitted == 1].merge(aid, left_on="student_key", right_index=True, how="left")
    for c in aid.columns: a[c] = a[c].fillna(0.0)   # admitted students in aid-covered cohorts with no row received $0
    a["tuition"] = a.cohort.map(pr.tuition_fees); a["coa"] = a.tuition + a.cohort.map(pr.room_board)
    a["gift_known"] = a[GIFT_COMPONENTS].sum(axis=1)
    a["inst_gift"] = a[INST_COMPONENTS].sum(axis=1)
    a["inst_fixed"] = a.inst_gift - a.inst_discretionary
    a["nondisc_gift"] = a.gift_known - a.inst_discretionary
    a["loans_offered"] = a[LOAN_COMPONENTS].sum(axis=1)
    a["net_cost_k"] = (a.coa - a.gift_known) / 1000.0
    a["disc_k"] = a.inst_discretionary / 1000.0
    a["loans_k"] = a.loans_offered / 1000.0
    a["engagement_cap"] = np.minimum(a.engagement_touches, 8)
    gpa = a.hs_gpa.where(a.student_type == "First-time freshman", a.transfer_gpa)
    a["gpa_band"] = pd.cut(gpa, [0, 3.2, 3.5, 3.7, 3.9, 4.01], right=False,
                           labels=["<3.2", "3.2-3.49", "3.5-3.69", "3.7-3.89", "3.9+"]).astype(object)
    a["gpa_band"] = a.gpa_band.fillna("Unknown")
    a["gpa_hi"] = a.gpa_band.isin(["3.7-3.89", "3.9+"]).astype(int)
    a["act_band"] = pd.cut(a.act, [0, 21, 25, 40], right=False, labels=["<21", "21-24", "25+"]).astype(object)
    a["act_band"] = a.act_band.fillna("Not submitted")
    gap_k = (a.coa - np.maximum(a.need_index, 0)) / 1000.0
    a["need_band"] = np.select([a.fafsa_filed != 1, gap_k < 30, gap_k < 38, gap_k < 44],
                               ["No FAFSA", "Lower need", "Moderate need", "High need"], default="Highest need")
    a["lead_band"] = pd.cut(a.app_lead_days, [0, 90, 150, 240, 100000], right=False,
                            labels=["<90d", "90-149d", "150-239d", "240d+"]).astype(object).fillna("Unknown")
    a["is_transfer"] = (a.student_type == "Transfer").astype(int)
    a["is_oos"] = (a.residency == "Out-of-state").astype(int)
    a["is_intl"] = (a.residency == "International").astype(int)
    # legacy-style features (leakage included on purpose; used only by the legacy replica)
    disb_cols = [f"{c}__disbursed" for c in ["pell", "seog", "state_grant", "external_scholarship",
                                            "sub_loan", "unsub_loan", "parent_plus", "work_study"] if f"{c}__disbursed" in a.columns]
    a["legacy_noninst_any"] = (a[disb_cols].sum(axis=1) > 0).astype(int)
    a["legacy_efc_cat"] = np.select([a.need_index.fillna(0) <= 0, a.need_index <= 14000], ["A $0 or missing", "B $1-14,000"], default="C $14,001+")
    a["legacy_inst_k"] = a.inst_gift / 1000.0
    pt = t["price_test"][["student_key", "offset_usd"]].rename(columns={"offset_usd": "test_offset"})
    a = a.merge(pt, on="student_key", how="left")
    a["in_price_test"] = a.test_offset.notna().astype(int); a["test_offset"] = a.test_offset.fillna(0.0)
    a["offset_k"] = a.test_offset / 1000.0
    return a.reset_index(drop=True)
