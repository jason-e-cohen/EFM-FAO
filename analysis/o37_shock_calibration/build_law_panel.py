"""Build the law school-by-year yield panel from public ABA 509 data (O37).

Inputs (read only, from the 509 dashboard repo; no other file there is opened):
  data/First_Year_Class_<year>.xlsx  ABA First Year Class compilations (2021 to 2024;
                                     any other year dropped in by hand is read too)
  data/aba509_all_schools_2025.csv   fall 2025 entering class, keyed by aba_school_id
  data/crosswalk_review_needed.csv   hand resolutions of ambiguous raw names
Inputs (read only, downloaded by hand into the project's aba509data/, Nov 23, 2026):
  First_Year_Class_<year>.xlsx       2017 to 2020 compilations (two more column schemas)
  GPA_and_LSAT_Scores_(calendar_year)_<year>.xlsx
                                     2011 to 2016: applications, offers and matriculants
                                     (full-time, part-time, total; the totals are used)

Definition break at 2017. Before 2017 the ABA reports "matriculants", which national totals
show to be the whole first-year class (it matches the ABA's published first-year enrollment
for fall 2013 to 2016 within 0.5%); from 2017 it reports enrollees from the applicant pool
and other first-year enrollees separately. The main yield uses pool enrollees throughout:
for 2011 to 2016 the matriculant count is scaled by (1 - the school's mean share of "other"
enrollees in 2017 to 2020). enrollees_matric_raw keeps the unscaled count and
enrollees_total the whole-class count (matriculants before 2017, total first-year class
after) for the sensitivity runs.

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
ABA_OLD = HERE.parents[1] / "aba509data"  # 2011 to 2020 compilations (read only)
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
    # 2011 to 2020 compilations: schools with no 2025 report (closed, left ABA accreditation,
    # or merged into another id; predecessors keep their own id up to the merger).
    "arizona summit": 9004, "charlotte": 9005, "concordia": 9006, "indiana tech": 9007,
    "rutgers university camden": 9008, "rutgers university newark": 9009, "thomas jefferson": 9010,
    "university of la verne": 9011, "valparaiso university": 9012, "whittier": 9013,
    "william mitchell": 9014, "hamline university": 9015,
}

# Merger and split overrides, filled after inspecting data/law_jumps.csv: (normalized raw name,
# first year of the successor) -> predecessor id used for that raw name's earlier rows.
# The pre-split two-campus school (2011 to 2014) is not the later single-campus school.
SPLIT_BEFORE: dict[tuple[str, int], int] = {("pennsylvania state university", 2015): 9016}

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
# Schema C (2017 to 2019): "Completed Apps", "Offer", "Enrollees from App pool", ...
# (2020 uses schema A). Headers are compared after collapsing whitespace.
COLS = {
    "apps": ["Applications", "CompletedApplications", "Completed Apps"],
    "offers": ["Offers", "OffersAdmission", "Offer"],
    "enrollees": ["Enrollees", "EnrolleesFromApplicantPool", "Enrollees from App pool"],
    "other_fy": ["OtherFirstYearEnrollees", "OtherFirstYearEnrolles", "Other FY enrollees"],
    "total_fy": ["TotalEnrollees", "TotalFYClassAll", "Total FY class", "Total FY class ALL"],
    "aba_yield_pct": ["EnrollOfferRate", "EnrollmentRateFromOffers", "Enrollment rate from Offers"],
    "aba_admit_pct": ["AcceptanceRate", "Acceptence Rate"],
    "school_year": ["SchoolYear"],
}


def read_fyc(path: Path, label_year: int) -> pd.DataFrame:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    hdr = [" ".join(str(h).split()) if h is not None else "" for h in rows[0]]
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
            "matric_def": "pool",
        })
    return pd.DataFrame(recs)


def read_gpa(path: Path, label_year: int) -> pd.DataFrame:
    """2011 to 2016 'GPA and LSAT Scores (calendar year)': totals of applications, offers and
    matriculants. Matriculants are the whole first-year class (see the module note)."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = list(wb.active.iter_rows(values_only=True))
    wb.close()
    hdr = [" ".join(str(h).split()) if h is not None else "" for h in rows[0]]
    i = {h: k for k, h in enumerate(hdr)}
    recs = []
    for row in rows[1:]:
        raw = str(row[0]).strip() if row[0] is not None else ""
        if is_junk(raw):
            continue
        ry = to_int(row[i["Reporting Year"]])
        if ry != label_year:
            raise ValueError(f"{path.name}: Reporting Year {ry} differs from the file year")
        m = to_int(row[i["# Of Matriculants Total"]])
        recs.append({
            "raw_name": raw, "file_year": label_year, "school_year_col": ry,
            "apps": to_int(row[i["# Of Apps Total"]]), "offers": to_int(row[i["# Of Offers Total"]]),
            "enrollees": m, "other_fy": None, "total_fy": m,
            "aba_yield_pct": None, "aba_admit_pct": None, "deferred": None, "matric_def": "matriculants",
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
    files = (sorted(SRC.glob("First_Year_Class_*.xlsx")) + sorted(ABA_OLD.glob("First_Year_Class_*.xlsx"))
             + sorted((OUT / "aba_extra").glob("First_Year_Class_*.xlsx")))
    parts, seen = [], set()
    for p in files:
        y = int(re.search(r"(\d{4})", p.stem).group(1))
        if y in seen:
            continue
        seen.add(y)
        parts.append(read_fyc(p, y))
    for p in sorted(ABA_OLD.glob("GPA_and_LSAT_Scores_(calendar_year)_*.xlsx")):
        y = int(re.search(r"(\d{4})", p.stem).group(1))
        if y not in seen:
            seen.add(y)
            parts.append(read_gpa(p, y))
    print("compilation years read:", sorted(seen))
    missing = [y for y in range(2011, 2025) if y not in seen]
    if missing:
        print("MISSING compilation years:", missing)
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
    d25["matric_def"] = "pool"
    panel = pd.concat([xl, d25], ignore_index=True)
    panel["year"] = panel["file_year"].astype(int)
    for c in ("apps", "offers", "enrollees", "other_fy", "total_fy", "aba_yield_pct", "aba_admit_pct", "deferred"):
        panel[c] = pd.to_numeric(panel[c], errors="coerce").astype(float)
    # Merger/split overrides: a raw name whose rows belong to a predecessor id before a year.
    for (nc, before), sid in SPLIT_BEFORE.items():
        hit = panel["raw_name"].map(lambda r: r is not None and isinstance(r, str) and normalize(r)[1] == nc)
        panel.loc[hit & (panel["year"] < before), "aba_school_id"] = sid

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

    # Definition break at 2017 (module note). enrollees_total: whole first-year class in every
    # year. enrollees_matric_raw: before 2017 the unscaled matriculant count. Main enrollees:
    # pool enrollees; before 2017 matriculants x (1 - the school's mean "other" share, 2017-2020),
    # or the national 2017-2020 share for a school with no 2017-2020 row.
    panel["enrollees_total"] = np.where(panel["matric_def"] == "matriculants", panel["enrollees"],
                                        panel["total_fy"].where(panel["total_fy"].notna(), panel["enrollees"]))
    panel["enrollees_matric_raw"] = panel["enrollees"]
    w = panel[(panel["year"].between(2017, 2020)) & (panel["total_fy"] > 0) & panel["other_fy"].notna()]
    share = (w["other_fy"] / w["total_fy"]).groupby(w["aba_school_id"]).mean()
    nat_share = float(w["other_fy"].sum() / w["total_fy"].sum())
    old = panel["matric_def"] == "matriculants"
    sh = panel.loc[old, "aba_school_id"].map(share).fillna(nat_share)
    panel["other_share_used"] = np.nan
    panel.loc[old, "other_share_used"] = sh
    panel.loc[old, "enrollees"] = (panel.loc[old, "enrollees"] * (1 - sh)).round()
    print(f"pre-2017 matriculants scaled to pool enrollees: national other share 2017-2020 {nat_share:.4f}, "
          f"schools with their own share {int(panel.loc[old, 'aba_school_id'].map(share).notna().sum())} of {int(old.sum())} rows")

    panel["yield"] = panel["enrollees"] / panel["offers"]
    panel["admit_rate"] = panel["offers"] / panel["apps"]
    panel["yield_diff_vs_aba_pp"] = 100 * panel["yield"] - panel["aba_yield_pct"]
    cols = ["aba_school_id", "year", "raw_name", "school_type", "state", "apps", "offers", "enrollees",
            "enrollees_scraped", "enrollees_adjusted_2025", "enrollees_total", "enrollees_matric_raw",
            "other_share_used", "matric_def", "other_fy", "total_fy", "deferred", "yield", "admit_rate", "aba_yield_pct", "aba_admit_pct",
            "yield_diff_vs_aba_pp", "school_year_col", "file_year"]
    panel = panel[cols].sort_values(["aba_school_id", "year"])
    panel.to_csv(OUT / "law_panel.csv", index=False)
    print("rows:", len(panel), "matched rows:", int(panel["aba_school_id"].notna().sum()))
    print(panel.groupby("year").agg(n=("offers", "size"), offers=("offers", "sum"),
                                    enrollees=("enrollees", "sum"), total_fy=("total_fy", "sum")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
