"""Build the law school-by-year yield panel from public ABA 509 data (O37).

Inputs (read only, from the 509 dashboard repo; no other file there is opened):
  data/First_Year_Class_<year>.xlsx  ABA First Year Class compilations (2021 to 2024;
                                     any other year dropped in by hand is read too)
  data/aba509_all_schools_2025.csv   fall 2025 entering class, keyed by aba_school_id
  data/crosswalk_review_needed.csv   hand resolutions of ambiguous raw names

The 509 repo's own crosswalk lives in Supabase, which this analysis does not touch, so
the name match is rebuilt here: the repo's normalize() rules (copied, not imported),
then exact match on the normalized name, then the review file's resolutions, then
difflib similarity with a margin, then the manual table below. Every match and its
method is written to data/law_crosswalk.csv for checking.

Output (git-ignored): data/law_panel.csv, one row per school and entering class.

Run from the project root:
  .venv/bin/python analysis/o37_shock_calibration/build_law_panel.py
"""
from __future__ import annotations

import csv
import difflib
import re
import sys
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

REPO = Path("/Users/jasoncohen/projects/aba-509-saas")
SRC = REPO / "data"
HERE = Path(__file__).resolve().parent
OUT = HERE / "data"

# Raw-name fragments the automatic steps cannot place; filled after inspecting
# data/law_unmatched.csv. Keys are normalized raw names (core), values aba_school_id.
# Ids 9001 and up are schools with no fall 2025 report (closed, or merged into another id).
MANUAL: dict[str, int] = {
    "university of arkansas fayetteville": 5, "university of arkansas little rock": 6,
    "university of arkansas at little rock": 6, "brigham young university": 150,
    "university of california los angeles": 9, "catholic university of america": 29,
    "chicago kent illinois institute of technology": 45, "university of florida": 34,
    "university of hawaii": 41, "indiana university bloomington": 51,
    "indiana university indianapolis": 52, "louisiana state university": 62,
    "university of louisville": 61, "loyola marymount university los angeles": 10,
    "university of memphis": 140, "ohio state university": 119, "pepperdine university": 19,
    "pacific university of": 13, "southern illinois university carbondale": 43,
    "southern methodist university": 143, "st thomas university florida": 177,
    "st thomas university miami": 177, "university of texas at austin": 142,
    "texas southern university": 146, "university of buffalo suny": 98, "unt dallas": 225,
    "new york university": 105, "new york law school": 104, "washington university": 88,
    "university of washington": 158, "pennsylvania state dickinson": 219,
    "pennsylvania state pennsylvania state": 9003, "pennsylvania state university": 9003,
    "florida coastal": 9001, "golden gate university": 9002,
}

# ---------------------------------------------------------------- normalization
# Copied from scraper/build_school_crosswalk.py (normalize), unchanged in effect.
BOILERPLATE_SUFFIXES = ["school of law", "college of law", "law school", "law center"]
COMMA_UNIV_RE = re.compile(r"^(.+?),\s*(?:the\s+)?university of$", re.IGNORECASE)
COMMA_COLL_RE = re.compile(r"^(.+?),\s*(?:the\s+)?college of$", re.IGNORECASE)


def normalize(raw: str) -> tuple[str, str]:
    s = raw.strip()
    m = COMMA_UNIV_RE.match(s)
    if m:
        s = f"university of {m.group(1).strip()}"
    else:
        m = COMMA_COLL_RE.match(s)
        if m:
            s = f"college of {m.group(1).strip()}"
    s = s.lower().replace("&", "and")
    for ch in "-/|":
        s = s.replace(ch, " ")
    s = re.sub(r"[.,'\(\)]", "", s)
    s = " ".join(s.split())
    s = re.sub(r"\bthe\b", "", s)
    s = " ".join(s.split())
    s = re.sub(r"\buniv\b", "university", s)
    s = re.sub(r"\bcoll\b", "college", s)
    s = re.sub(r"\bpenn\b", "pennsylvania", s)
    full = " ".join(s.split())
    core = full
    for bp in BOILERPLATE_SUFFIXES:
        if core.endswith(bp):
            core = core[: -len(bp)].strip()
            break
    core = re.sub(r"\blaw\s*$", "", core).strip()
    return full, core


def is_junk(raw: str) -> bool:
    return (not raw) or raw.startswith("*") or raw.upper().startswith("Z-SAMPLE") or len(raw) > 200


def to_int(v):
    if v is None:
        return None
    try:
        return int(float(str(v).replace(",", "").strip()))
    except (ValueError, TypeError):
        return None


def to_float(v):
    if v is None:
        return None
    try:
        return float(str(v).strip().rstrip("%"))
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------- readers
# Schema A (2021, 2022) and schema B (2023, 2024), per ingest_historical_backfill.py.
COLS = {
    "apps": ["Applications", "CompletedApplications"],
    "offers": ["Offers", "OffersAdmission"],
    "enrollees": ["Enrollees", "EnrolleesFromApplicantPool"],
    "other_fy": ["OtherFirstYearEnrollees", "OtherFirstYearEnrolles"],
    "total_fy": ["TotalEnrollees", "TotalFYClassAll"],
    "aba_yield_pct": ["EnrollOfferRate", "EnrollmentRateFromOffers"],
    "aba_admit_pct": ["AcceptanceRate"],
    "school_year": ["SchoolYear"],
}


def read_fyc(path: Path, label_year: int) -> pd.DataFrame:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    hdr = [str(h).strip() if h is not None else "" for h in rows[0]]
    idx = {h: i for i, h in enumerate(hdr)}

    def get(row, key):
        for n in COLS[key]:
            if n in idx and idx[n] < len(row):
                return row[idx[n]]
        return None

    recs = []
    for row in rows[1:]:
        raw = str(row[0]).strip() if row[0] is not None else ""
        if is_junk(raw):
            continue
        recs.append({
            "raw_name": raw,
            "file_year": label_year,
            "school_year_col": to_int(get(row, "school_year")),
            "apps": to_int(get(row, "apps")),
            "offers": to_int(get(row, "offers")),
            "enrollees": to_int(get(row, "enrollees")),
            "other_fy": to_int(get(row, "other_fy")),
            "total_fy": to_int(get(row, "total_fy")),
            "aba_yield_pct": to_float(get(row, "aba_yield_pct")),
            "aba_admit_pct": to_float(get(row, "aba_admit_pct")),
            "deferred": None,
        })
    return pd.DataFrame(recs)


def read_2025() -> pd.DataFrame:
    df = pd.read_csv(SRC / "aba509_all_schools_2025.csv")
    df = df[df["school_name"].notna()]  # ids with no 2025 report (blank rows)
    out = pd.DataFrame({
        "aba_school_id": df["aba_school_id"],
        "csv_name": df["school_name"],
        "file_year": df["report_year"],
        "school_year_col": df["report_year"],
        "apps": pd.to_numeric(df["apps_completed"], errors="coerce"),
        "offers": pd.to_numeric(df["apps_offered"], errors="coerce"),
        "enrollees": pd.to_numeric(df["enrollees_from_pool"], errors="coerce"),
        "other_fy": None,
        "total_fy": pd.to_numeric(df["class_size_total"], errors="coerce"),
        "aba_yield_pct": pd.to_numeric(df["enrollment_rate_from_offers_pct"], errors="coerce"),
        "aba_admit_pct": pd.to_numeric(df["acceptance_rate_pct"], errors="coerce"),
        "deferred": pd.to_numeric(df["enrollees_deferred"], errors="coerce"),
        "school_type": df["school_type"],
        "state": df["state"],
    })
    return out


# ---------------------------------------------------------------- crosswalk
STOP = {"university", "of", "the", "college", "law", "school", "at", "and", "center", "in",
        "a", "iit", "sandra", "day"}
EXPAND = {"st": "saint", "pr": "puerto rico", "suny": "suny", "ny": "new york"}


def tokens(name: str) -> set[str]:
    nf, _ = normalize(name)
    out = set()
    for t in nf.split():
        out.update(EXPAND.get(t, t).split())
    return {t for t in out if t not in STOP}


def build_crosswalk(raw_names: list[str], ref: pd.DataFrame) -> pd.DataFrame:
    ref = ref.copy()
    ref["tok"] = ref["csv_name"].map(tokens)
    ref["nf"], ref["nc"] = zip(*ref["csv_name"].map(normalize))
    resolutions = {}
    with open(SRC / "crosswalk_review_needed.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("resolution"):
                resolutions[r["raw_name"].strip()] = r["resolution"].strip()

    def best(tok: set[str]):
        sc = []
        for sid, b in zip(ref["aba_school_id"], ref["tok"]):
            if not tok:
                continue
            cov = len(tok & b) / len(tok)
            jac = len(tok & b) / len(tok | b)
            sc.append((cov, jac, int(sid)))
        sc.sort(reverse=True)
        return sc

    out = []
    for raw in raw_names:
        nf, nc = normalize(raw)
        method, sid, score = None, None, None
        if nc in MANUAL:
            sid, method = MANUAL[nc], "manual"
        hit = ref[(ref["nc"] == nc) | (ref["nf"] == nf)]
        if sid is None and len(hit) == 1:
            method, sid = "exact", int(hit["aba_school_id"].iloc[0])
        if sid is None:
            for src, tok in (("tokens", tokens(raw)), ("review_file_tokens", tokens(resolutions.get(raw, "")))):
                sc = best(tok)
                if not sc:
                    continue
                full = [x for x in sc if x[0] == 1.0]
                if len(full) == 1 or (len(full) > 1 and full[0][1] - full[1][1] >= 0.15):
                    method, sid, score = src, full[0][2], round(full[0][1], 3)
                    break
                score = round(sc[0][0], 3)
        if sid is None:
            method = "unmatched"
        out.append({"raw_name": raw, "norm_core": nc, "aba_school_id": sid, "method": method, "score": score})
    return pd.DataFrame(out)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    d25 = read_2025()
    # Older compilations downloaded by hand go in data/aba_extra/ (the 509 repo stays read only).
    files = sorted(SRC.glob("First_Year_Class_*.xlsx")) + sorted((OUT / "aba_extra").glob("First_Year_Class_*.xlsx"))
    parts = []
    for p in files:
        y = int(re.search(r"(\d{4})", p.stem).group(1))
        parts.append(read_fyc(p, y))
    xl = pd.concat(parts, ignore_index=True)

    cw = build_crosswalk(sorted(xl["raw_name"].unique()), d25[["aba_school_id", "csv_name"]])
    cw.to_csv(OUT / "law_crosswalk.csv", index=False)
    un = cw[cw["method"] == "unmatched"]
    if len(un):
        un.to_csv(OUT / "law_unmatched.csv", index=False)
    print("crosswalk methods:", cw["method"].value_counts().to_dict())

    xl = xl.merge(cw[["raw_name", "aba_school_id"]], on="raw_name", how="left")
    meta = d25[["aba_school_id", "school_type", "state"]]
    xl = xl.merge(meta, on="aba_school_id", how="left")
    d25 = d25.drop(columns=["csv_name"])
    d25["raw_name"] = None
    panel = pd.concat([xl, d25], ignore_index=True)
    panel["year"] = panel["file_year"].astype(int)

    # Duplicate (school, year) rows would mean two raw names mapped to one id.
    m = panel[panel["aba_school_id"].notna()]
    dup = m[m.duplicated(["aba_school_id", "year"], keep=False)]
    if len(dup):
        print("WARNING duplicate school-years:", len(dup))
        dup[["raw_name", "aba_school_id", "year"]].to_csv(OUT / "law_duplicates.csv", index=False)

    # Plausibility: the same id should not jump in size between consecutive years.
    pm = panel.dropna(subset=["aba_school_id"]).sort_values(["aba_school_id", "year"]).copy()
    for c in ("total_fy", "apps", "offers"):
        pm["lr_" + c] = np.log(pm[c].where(pm[c] > 0)).groupby(pm["aba_school_id"]).diff()
    jumps = pm[(pm[["lr_total_fy", "lr_apps", "lr_offers"]].abs() > 0.5).any(axis=1)]
    jumps[["aba_school_id", "year", "raw_name", "apps", "offers", "enrollees", "total_fy",
           "lr_total_fy", "lr_apps", "lr_offers"]].to_csv(OUT / "law_jumps.csv", index=False)
    print("school-years with a size jump over 0.5 in log (check the match):", len(jumps))

    # 2025: the scraped enrollees_from_pool exceeds the count implied by the ABA's own
    # published rates (offers x EnrollOfferRate = applications x EnrollAppRate) at 45 schools,
    # by 2 to 16. In 2021 to 2024 the published rate equals Enrollees / Offers exactly. The
    # main yield uses the ABA-implied count for 2025 (consistent with earlier years);
    # enrollees_scraped keeps the CSV value for the sensitivity run.
    panel["enrollees_scraped"] = panel["enrollees"]
    implied = (panel["aba_yield_pct"] * panel["offers"] / 100).round()
    use = (panel["year"] == 2025) & implied.notna() & ((panel["enrollees"] - implied).abs() >= 1.5)
    panel.loc[use, "enrollees"] = implied[use]
    panel["enrollees_adjusted_2025"] = use
    print("2025 rows using the ABA-implied enrollee count:", int(use.sum()))

    panel["yield"] = panel["enrollees"] / panel["offers"]
    panel["admit_rate"] = panel["offers"] / panel["apps"]
    panel["yield_diff_vs_aba_pp"] = 100 * panel["yield"] - panel["aba_yield_pct"]
    cols = ["aba_school_id", "year", "raw_name", "school_type", "state", "apps", "offers", "enrollees",
            "enrollees_scraped", "enrollees_adjusted_2025", "other_fy", "total_fy", "deferred", "yield", "admit_rate", "aba_yield_pct", "aba_admit_pct",
            "yield_diff_vs_aba_pp", "school_year_col", "file_year"]
    panel = panel[cols].sort_values(["aba_school_id", "year"])
    panel.to_csv(OUT / "law_panel.csv", index=False)
    print("rows:", len(panel), "matched rows:", int(panel["aba_school_id"].notna().sum()))
    print(panel.groupby("year").agg(n=("offers", "size"), offers=("offers", "sum"),
                                    enrollees=("enrollees", "sum"), total_fy=("total_fy", "sum")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
