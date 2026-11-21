"""Build the undergraduate institution-by-year yield panel from IPEDS (O37).

Reads data/ipeds_raw/ADM<year>/ (the revised _rv file when present) and HD<year>/.
ADM<year> is the fall <year> entering class (collected the following winter).
Yield = ENRLT / ADMSSN (first-time degree-seeking enrolled / admitted), the CDS C1 basis
of methodology Appendix F item 4.

Kept: four-year (ICLEVEL 1), public or private nonprofit (CONTROL 1, 2), degree-granting,
values reported by the institution (X flag R) for APPLCN, ADMSSN and ENRLT.

Output (git-ignored): data/ug_panel.csv.
  .venv/bin/python -I analysis/o37_shock_calibration/build_ug_panel.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "ipeds_raw"


def read_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="latin-1", low_memory=False)
    df.columns = [c.replace("\ufeff", "").replace("ï»¿", "").strip().upper() for c in df.columns]
    return df


def main() -> int:
    parts = []
    for d in sorted(RAW.glob("ADM*")):
        y = int(d.name[3:])
        files = sorted(d.glob("*.csv"))
        rv = [f for f in files if f.stem.lower().endswith("_rv")]
        adm = read_csv(rv[0] if rv else files[0])
        hd_dir = RAW / f"HD{y}"
        hd = read_csv(sorted(hd_dir.glob("*.csv"))[0])
        hd = hd[["UNITID", "ICLEVEL", "CONTROL", "DEGGRANT", "STABBR"]]
        a = adm[["UNITID", "APPLCN", "ADMSSN", "ENRLT", "XAPPLCN", "XADMSSN", "XENRLT"]].copy()
        for c in ("APPLCN", "ADMSSN", "ENRLT"):
            a[c] = pd.to_numeric(a[c], errors="coerce")
        a["reported"] = (a[["XAPPLCN", "XADMSSN", "XENRLT"]].astype(str).apply(lambda s: s.str.strip()) == "R").all(axis=1)
        a = a.merge(hd, on="UNITID", how="left")
        a["year"] = y
        a["source_file"] = (rv[0] if rv else files[0]).name
        parts.append(a)
    p = pd.concat(parts, ignore_index=True)
    n0 = len(p)
    p = p[(p["ICLEVEL"] == 1) & (p["CONTROL"].isin([1, 2])) & (p["DEGGRANT"] == 1)]
    n1 = len(p)
    p = p[p["reported"]]
    n2 = len(p)
    p = p.rename(columns={"UNITID": "unitid", "APPLCN": "apps", "ADMSSN": "offers", "ENRLT": "enrollees",
                          "CONTROL": "control", "STABBR": "state"})
    p["yield"] = p["enrollees"] / p["offers"]
    p["admit_rate"] = p["offers"] / p["apps"]
    cols = ["unitid", "year", "control", "state", "apps", "offers", "enrollees", "yield", "admit_rate", "source_file"]
    p = p[cols].sort_values(["unitid", "year"])
    p.to_csv(HERE / "data" / "ug_panel.csv", index=False)
    print(f"rows read {n0}; four-year public or nonprofit degree-granting {n1}; all three values reported {n2}")
    print(p.groupby("year").agg(n=("unitid", "size"), offers=("offers", "sum"), enrollees=("enrollees", "sum"),
                                files=("source_file", "first")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
