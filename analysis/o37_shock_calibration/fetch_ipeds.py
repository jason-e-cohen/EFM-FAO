"""Download IPEDS admissions (ADM) and institutional characteristics (HD) files from NCES.

Files land in data/ipeds_raw/<FILE>/ (git-ignored), one directory per archive. The
archives are data only; nothing in them is executed. Run with -I:
  .venv/bin/python -I analysis/o37_shock_calibration/fetch_ipeds.py
"""
from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "ipeds_raw"
BASE = "https://nces.ed.gov/ipeds/datacenter/data/"
YEARS = range(2014, 2025)  # ADM files start with the 2014-15 collection (fall 2014)
UA = {"User-Agent": "python-urllib (research script)"}


def fetch(name: str) -> str:
    dest = RAW / name
    if dest.exists() and any(dest.glob("*.csv")):
        return "cached"
    req = urllib.request.Request(BASE + name + ".zip", headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            blob = r.read()
    except Exception as e:  # noqa: BLE001
        return f"failed: {e}"
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for m in z.namelist():
            if m.lower().endswith(".csv") and "/" not in m and ".." not in m:
                (dest / Path(m).name).write_bytes(z.read(m))
    return "ok"


def main() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    for y in YEARS:
        for stem in (f"ADM{y}", f"HD{y}"):
            print(stem, fetch(stem), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
