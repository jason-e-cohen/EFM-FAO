"""Aggregation and disclosure control. Student-level rows never leave the compute environment.

Rules: (1) cells with fewer than k students are suppressed; (2) complementary suppression prevents
back-solving a suppressed cell from published totals; (3) no ZIP5, no exact dates, no student keys;
(4) protected attributes are published for audit views only and flagged as such.
"""
from __future__ import annotations
import itertools
import numpy as np
import pandas as pd

FUNNEL_DIMS = ["student_type", "residency", "source_category", "first_gen", "program_area", "region",
               "athlete", "need_band", "gpa_band"]
PROTECTED_DIMS = ["race_ethnicity", "gender"]
STAGES = ["inquiries", "applications", "admits", "deposits", "enrolled"]


def _cell(g: pd.DataFrame) -> pd.Series:
    return pd.Series({"inquiries": len(g), "applications": int(g.applied.sum()), "admits": int(g.admitted.sum()),
                      "deposits": int(g.deposited.fillna(0).sum()), "enrolled": int(g.enrolled.fillna(0).sum())})


def _rates(df: pd.DataFrame, k: int) -> pd.DataFrame:
    for num, den, nm in [("applications", "inquiries", "apply_rate"), ("admits", "applications", "admit_rate"),
                         ("enrolled", "admits", "yield_rate"), ("enrolled", "inquiries", "inquiry_to_enroll")]:
        ok = df[den] >= k
        df[nm] = np.where(ok, df[num] / df[den].where(df[den] > 0), np.nan)
    return df


def funnel_cells(students: pd.DataFrame, admit_bands: pd.DataFrame, k: int, cohorts: list[int]) -> pd.DataFrame:
    s = students[students.cohort.isin(cohorts)].merge(admit_bands[["student_key", "need_band", "gpa_band"]], on="student_key", how="left")
    s["need_band"] = s.need_band.fillna("Not applicable (not admitted)"); s["gpa_band"] = s.gpa_band.fillna("Not applicable (not admitted)")
    s["first_gen"] = s.first_gen.map({1: "First-generation", 0: "Not first-generation"}); s["athlete"] = s.athlete.map({1: "Athlete", 0: "Non-athlete"})
    dims = FUNNEL_DIMS + PROTECTED_DIMS
    rows = []
    for d in dims:                                                       # one-way, by cohort and pooled
        g = s.groupby(["cohort", d]).apply(_cell, include_groups=False).reset_index().rename(columns={d: "val1"})
        g["dim1"] = d; g["dim2"] = None; g["val2"] = None; rows.append(g)
        p = s.groupby(d).apply(_cell, include_groups=False).reset_index().rename(columns={d: "val1"})
        p["cohort"] = 0; p["dim1"] = d; p["dim2"] = None; p["val2"] = None; rows.append(p)
    for d1, d2 in itertools.combinations(FUNNEL_DIMS, 2):                # two-way, pooled across cohorts
        g = s.groupby([d1, d2]).apply(_cell, include_groups=False).reset_index().rename(columns={d1: "val1", d2: "val2"})
        g["cohort"] = 0; g["dim1"] = d1; g["dim2"] = d2; rows.append(g)
    out = pd.concat(rows, ignore_index=True)
    out["protected_dimension"] = out.dim1.isin(PROTECTED_DIMS).astype(int)
    out["suppressed"] = 0
    out.loc[out.inquiries < k, "suppressed"] = 1
    # complementary suppression within each one-way table: if exactly one cell is suppressed, hide the next smallest
    one = out[out.dim2.isna()]
    for _, idx in one.groupby(["cohort", "dim1"]).groups.items():
        sub = out.loc[idx]
        if sub.suppressed.sum() == 1:
            nxt = sub[sub.suppressed == 0].inquiries.idxmin(); out.loc[nxt, "suppressed"] = 1
    out = _rates(out, k)
    out.loc[out.suppressed == 1, STAGES + ["apply_rate", "admit_rate", "yield_rate", "inquiry_to_enroll"]] = np.nan
    return out[["cohort", "dim1", "val1", "dim2", "val2", *STAGES, "apply_rate", "admit_rate", "yield_rate",
                "inquiry_to_enroll", "suppressed", "protected_dimension"]]


def suppress_counts(df: pd.DataFrame, count_col: str, k: int, value_cols: list[str]) -> pd.DataFrame:
    df = df.copy(); m = df[count_col] < k
    df["suppressed"] = m.astype(int); df.loc[m, value_cols] = np.nan
    return df
