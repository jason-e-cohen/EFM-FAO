"""Desktop Excel parity [v0.6.2, P2-01] (spec test 3, "Desktop Excel"; Phase 2 acceptance). Run by hand.

Build the sentinel copy (every cached value -999), open it in desktop Excel, let it recalculate, Save As a copy
(.xlsx), then:

    cd prototypes/scenario_workbook
    ../../.venv/bin/python -m sw.build --config config/synthetic.yaml --data synthetic --seed 101 \
        --scenarios config/scenarios_synthetic.yaml --out output/ --sentinel
    ../../.venv/bin/python tests/compare_excel_saved.py <saved copy.xlsx>

The script refuses a file that is not a recalculated sentinel build of the current build id [v0.6.2, P21-01]: RunLog
must say the cached values are sentinels, the build id (inputs and sw/*.py) must match a fresh sentinel rebuild, and
a file in which every formula cell still holds -999 is refused as not recalculated. It then compares every formula
cell, as Excel saved it, with the Python value at test 3's tolerances (strings and integers exact; floats within 1e-6
relative, 1e-9 absolute near zero); a cell still holding -999 fails. It also compares each cell's formula text with the
rebuild's (case, spacing, the _xlfn. prefix and the printing of numeric literals ignored), so a formula typed over
shows even when its value happens to match, and it lists input cells (Inputs, Levers) that differ from the build.
Results go to output/phase2/excel_compare_report.json. Exit status 0 when every cell was recalculated, has the built
formula and matches; 1 otherwise; 2 when the file is refused.

For a non-synthetic build (data from a CSV), pass --data with the CSV path. --config and --scenarios override the
paths on RunLog.
"""
import argparse
import collections
import json
import os
import re
import sys
import tempfile
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)


def close(a, b, rel=1e-6, abs_=1e-9):
    """Test 3 tolerance (same rule as tests/conftest.py close)."""
    import math
    a = "" if a is None else a
    b = "" if b is None else b
    if isinstance(a, str) or isinstance(b, str):
        return str(a) == str(b)
    if isinstance(b, int) and not isinstance(b, bool):
        return float(a) == float(b)
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=abs_)


def runlog(wb):
    ws = wb["RunLog"]
    return {ws.cell(r, 1).value: ws.cell(r, 2).value for r in range(1, ws.max_row + 1) if ws.cell(r, 1).value}


def application(path):
    """The application that last saved the file (docProps/app.xml), or ''."""
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("docProps/app.xml").decode("utf-8", "replace")
    except (KeyError, zipfile.BadZipFile):
        return ""
    m = re.search(r"<Application>([^<]*)</Application>", xml)
    v = re.search(r"<AppVersion>([^<]*)</AppVersion>", xml)
    return (m.group(1) if m else "") + (f" {v.group(1)}" if v else "")


def main(argv=None):
    import openpyxl
    from sw import build

    ap = argparse.ArgumentParser(description="Compare a workbook saved by desktop Excel with Python (spec test 3).")
    ap.add_argument("saved", help="the copy saved by Excel after recalculation")
    ap.add_argument("--config", help="config path (default: RunLog 'config', relative to the prototype)")
    ap.add_argument("--scenarios", help="scenario file (default: RunLog 'scenarios')")
    ap.add_argument("--data", help="cells CSV for a non-synthetic build (default: the synthetic seed on RunLog)")
    ap.add_argument("--show", type=int, default=15, help="mismatches to print per sheet")
    args = ap.parse_args(argv)

    vals = openpyxl.load_workbook(args.saved, data_only=True)
    forms = openpyxl.load_workbook(args.saved, data_only=False)
    log = runlog(vals)
    app = application(args.saved)
    print(f"saved copy: {args.saved}")
    print(f"saved by: {app or 'unknown'}")
    if "Excel" not in app:
        print("note: the file was not last saved by Microsoft Excel; the comparison still runs on its stored values")

    cfg_path = args.config or os.path.join(ROOT, log.get("config", ""))
    scen_path = args.scenarios or os.path.join(ROOT, log.get("scenarios", ""))
    src = log.get("data source", "")
    m = re.search(r"seed (\d+)", src or "")
    if args.data:
        data, seed = args.data, 101
    elif src.startswith("synthetic") and m:
        data, seed = "synthetic", int(m.group(1))
    else:
        print(f"cannot tell the data source from RunLog ({src!r}); pass --data")
        return 2
    for p in (cfg_path, scen_path):
        if not os.path.exists(p):
            print(f"missing input: {p} (pass --config or --scenarios)")
            return 2

    # [v0.6.2, P21-01] The copy must start from the sentinel build: every cached value -999, so any cell Excel did not
    # recalculate still holds -999. A copy of the normal build carries the Python values and could match without any
    # recalculation, so it is refused.
    cached = str(log.get("cached values", ""))
    if not cached.startswith("sentinel"):
        print("refused: not a sentinel build (RunLog 'cached values' is "
              f"{cached or 'missing'!r}). Build the sentinel copy (python -m sw.build ... --sentinel), open it in "
              "Excel, let it recalculate, Save As a copy and compare that copy.")
        return 2

    with tempfile.TemporaryDirectory(prefix="sw_excel_compare_") as tmp:
        path, info = build.build(cfg_path, data, scen_path, tmp, seed=seed, sentinel=True)
        if info["build_id"] != log.get("build id"):
            print(f"refused: build id differs: saved copy {log.get('build id')!r}, rebuilt {info['build_id']!r}. The "
                  "inputs or the generator code (sw/*.py) changed since that build; rebuild and save again.")
            return 2
        built = openpyxl.load_workbook(path, data_only=False)

        # inputs edited in the saved copy (constants on Inputs and Levers that differ from the build)
        edited = []
        for sheet in ("Inputs", "Levers"):
            wb_, ws_ = built[sheet], forms[sheet]
            for row in wb_.iter_rows():
                for c in row:
                    v = c.value
                    got = ws_[c.coordinate].value
                    if _is_formula(v):
                        if not _is_formula(got):
                            edited.append((sheet, c.coordinate, "formula (inherited or computed)", got))
                        continue
                    if _is_formula(got):
                        edited.append((sheet, c.coordinate, v, "formula"))
                    elif not close(got, v, rel=1e-12, abs_=1e-15):     # saved constants may carry 15 digits
                        edited.append((sheet, c.coordinate, v, got))
            for row in ws_.iter_rows():
                for c in row:
                    if c.value is not None and wb_[c.coordinate].value is None:
                        edited.append((sheet, c.coordinate, None, c.value))
        expected = info["expected"]
        built_f = {(s, r, c): _text(built[s].cell(r + 1, c + 1).value) for (s, r, c) in expected}

    count = collections.Counter()
    sentinel_left = collections.Counter()
    bad = collections.defaultdict(list)
    fdiff = collections.defaultdict(list)
    for (sheet, r, c), v in expected.items():
        cell = vals[sheet].cell(r + 1, c + 1)
        got = cell.value
        count[sheet] += 1
        if got in (-999, "-999"):
            sentinel_left[sheet] += 1
        if not close(got, v):
            bad[sheet].append({"cell": cell.coordinate, "python": v, "excel": got})
        saved_f = _text(forms[sheet].cell(r + 1, c + 1).value)
        if not same_formula(saved_f, built_f[(sheet, r, c)]):
            fdiff[sheet].append({"cell": cell.coordinate, "built": built_f[(sheet, r, c)], "saved": saved_f})
    total = sum(count.values())
    n_left = sum(sentinel_left.values())
    if n_left == total:
        print("refused: not recalculated: every formula cell still holds the sentinel -999. Open the copy in Excel, "
              "let it recalculate, Save As a copy and compare that copy.")
        return 2

    n_bad = sum(len(v) for v in bad.values())
    n_fd = sum(len(v) for v in fdiff.values())
    print(f"build {info['build_id']}; data {src}; {total:,} formula cells compared")
    print(f"  {'sheet':<14} {'cells':>7}  {'value mismatches':>16}  {'still -999':>10}  {'formula differs':>15}")
    for sheet in sorted(count, key=lambda s: list(vals.sheetnames).index(s)):
        print(f"  {sheet:<14} {count[sheet]:>7,}  {len(bad.get(sheet, [])):>16,}  {sentinel_left[sheet]:>10,}  "
              f"{len(fdiff.get(sheet, [])):>15,}")
    if edited:
        print(f"\n{len(edited)} input cells differ from the build (results that depend on them will differ):")
        for sheet, coord, was, now in edited[:20]:
            print(f"  {sheet}!{coord}: built {was!r}, saved {now!r}")
    for sheet, rows in fdiff.items():
        print(f"\n{sheet}: first {min(args.show, len(rows))} of {len(rows)} formula differences (cell, built, saved)")
        for b in rows[:args.show]:
            print(f"  {b['cell']:<10} {b['built'][:70]!r:<72} {b['saved'][:70]!r}")
    for sheet, rows in bad.items():
        print(f"\n{sheet}: first {min(args.show, len(rows))} of {len(rows)} value mismatches (cell, Python, Excel)")
        for b in rows[:args.show]:
            print(f"  {b['cell']:<10} {b['python']!r:<40} {b['excel']!r}")
    out = os.path.join(ROOT, "output", "phase2")
    os.makedirs(out, exist_ok=True)
    rep = os.path.join(out, "excel_compare_report.json")
    with open(rep, "w") as f:
        json.dump({"saved": os.path.abspath(args.saved), "application": app, "build_id": info["build_id"],
                   "cells_compared": dict(count), "still_sentinel": dict(sentinel_left), "mismatches": dict(bad),
                   "formula_differences": dict(fdiff), "edited_inputs": edited}, f, indent=1, default=str)
    ok = not n_bad and not n_fd and not n_left
    verdict = ("OK: every formula cell was recalculated, has the built formula and matches Python" if ok else
               f"FAILED: {n_bad:,} value mismatches, {n_left:,} cells still -999, {n_fd:,} formula differences")
    print(f"\n{verdict}; report: {rep}")
    return 0 if ok else 1


def _is_formula(v):
    return isinstance(_text(v), str) and _text(v).startswith("=")


def _text(v):
    """A cell's formula text (openpyxl gives array formulas as objects with .text)."""
    return getattr(v, "text", v)


_NUM = re.compile(r"(?<![A-Za-z0-9_$.])(\d+\.?\d*(?:[Ee][+-]?\d+)?)")
_STR = re.compile(r'"(?:[^"]|"")*"')


def _norm(f):
    """Formula text for comparison: string literals kept as they are; elsewhere case, spaces and the _xlfn., _xlws.
    and LEGACY. prefixes ignored; numeric literals parsed (Excel and LibreOffice rewrite 17 digits as 15 and 1E+99 as
    1E+099). Returns (text with numbers replaced by #, list of numbers)."""
    if not isinstance(f, str):
        return (repr(f), [])
    f = f.lstrip("=")
    parts, nums, pos = [], [], 0
    for m in _STR.finditer(f):
        parts.append(("code", f[pos:m.start()]))
        parts.append(("str", m.group(0)))
        pos = m.end()
    parts.append(("code", f[pos:]))
    out = []
    for kind, s in parts:
        if kind == "str":
            out.append(s)
            continue
        s = re.sub(r"\s+", "", s).upper()
        for pre in ("_XLFN.", "_XLWS.", "LEGACY."):
            s = s.replace(pre, "")
        nums += [float(x) for x in _NUM.findall(s)]
        out.append(_NUM.sub("#", s))
    return ("".join(out), nums)


def same_formula(a, b):
    if not (isinstance(a, str) and isinstance(b, str)):
        return a == b
    ta, na = _norm(a)
    tb, nb = _norm(b)
    import math
    return ta == tb and len(na) == len(nb) and all(math.isclose(x, y, rel_tol=1e-12, abs_tol=0) for x, y in zip(na, nb))

if __name__ == "__main__":
    sys.exit(main())
