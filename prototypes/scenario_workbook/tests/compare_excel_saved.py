"""Desktop Excel parity [v0.6.2, P2-01] (spec test 3, "Desktop Excel"; Phase 2 acceptance). Run by hand.

Open a built workbook in desktop Excel, let it recalculate, Save As a copy (.xlsx), then:

    cd prototypes/scenario_workbook
    ../../.venv/bin/python tests/compare_excel_saved.py <saved copy.xlsx>

The script rebuilds the same workbook from the inputs named on its RunLog sheet (config, scenarios, synthetic seed),
checks that the build id matches, and compares every formula cell's value as Excel saved it with the Python value, at
test 3's tolerances (strings and integers exact; floats within 1e-6 relative, 1e-9 absolute near zero). It also lists
input cells (Inputs, Levers) that differ from the build, since an edited input changes the results it feeds.
Mismatches are printed and written to output/phase2/excel_compare_report.json. Exit status 0 when every cell matches,
1 otherwise, 2 when the copy cannot be compared (build id differs, the layout differs from the current generator's, the
file is the workbook as built rather than a saved copy, or it holds no saved values).

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

    with tempfile.TemporaryDirectory(prefix="sw_excel_compare_") as tmp:
        path, info = build.build(cfg_path, data, scen_path, tmp, seed=seed)
        built = openpyxl.load_workbook(path, data_only=False)
        if info["build_id"] != log.get("build id"):
            print(f"build id differs: saved copy {log.get('build id')!r}, rebuilt {info['build_id']!r}. The inputs "
                  "(config, scenarios, data or requirements.lock) changed since that build; rebuild and save again.")
            return 2
        # A file as built (never saved by Excel) carries the Python values as its cached values and would match
        # trivially; its sheets are byte-identical to the rebuild's (xlsxwriter also names "Microsoft Excel" in
        # docProps/app.xml, so the application name cannot tell them apart).
        with zipfile.ZipFile(path) as zb, zipfile.ZipFile(args.saved) as zs:
            sheets = [n for n in zb.namelist() if n.startswith("xl/worksheets/sheet")]
            same = [n for n in sheets if n in zs.namelist() and zs.read(n) == zb.read(n)]
        if sheets and len(same) == len(sheets):
            print("this is the workbook as built, not a copy saved after recalculation: its sheets are identical to "
                  "the rebuild. Open it in Excel, let it recalculate, Save As a copy and compare that copy.")
            return 2

        # inputs edited in the saved copy (constants on Inputs and Levers that differ from the build)
        edited = []
        for sheet in ("Inputs", "Levers"):
            wb_, ws_ = built[sheet], forms[sheet]
            for row in wb_.iter_rows():
                for c in row:
                    v = c.value
                    got = ws_[c.coordinate].value
                    if isinstance(v, str) and v.startswith("="):
                        if not (isinstance(got, str) and got.startswith("=")):
                            edited.append((sheet, c.coordinate, "formula (inherited or computed)", got))
                        continue
                    if isinstance(got, str) and got.startswith("="):
                        edited.append((sheet, c.coordinate, v, "formula"))
                    elif not close(got, v, rel=1e-12, abs_=1e-15):     # saved constants may carry 15 digits
                        edited.append((sheet, c.coordinate, v, got))
            for row in ws_.iter_rows():
                for c in row:
                    if c.value is not None and wb_[c.coordinate].value is None:
                        edited.append((sheet, c.coordinate, None, c.value))
        expected = info["expected"]

    count = collections.Counter()
    empty = collections.Counter()
    bad = collections.defaultdict(list)
    for (sheet, r, c), v in expected.items():
        cell = vals[sheet].cell(r + 1, c + 1)
        got = cell.value
        count[sheet] += 1
        if got is None and v not in ("", None):
            empty[sheet] += 1
        if not close(got, v):
            bad[sheet].append({"cell": cell.coordinate, "python": v, "excel": got})
    total = sum(count.values())
    # The build id hashes the inputs, not the generator code: a copy saved from a workbook built by another version of
    # sw/workbook.py has the same id but a different layout. Formula cells of the rebuild that are not formulas in the
    # copy (beyond inputs typed over) show it.
    typed = {(s, c) for s, c, was, _ in edited if str(was).startswith("formula")}
    moved = [(s, r, c) for (s, r, c) in expected
             if not (isinstance(forms[s].cell(r + 1, c + 1).value, str)
                     and forms[s].cell(r + 1, c + 1).value.startswith("="))
             and (s, forms[s].cell(r + 1, c + 1).coordinate) not in typed]
    if moved:
        print(f"layout differs: {len(moved):,} formula cells of the rebuild are not formulas in the copy (first: "
              f"{moved[0][0]}!{forms[moved[0][0]].cell(moved[0][1] + 1, moved[0][2] + 1).coordinate}). The copy was "
              "probably built by another version of the generator; rebuild with the current code and save again.")
        return 2
    if sum(empty.values()) == total:
        print("no saved values: every formula cell is empty. Let Excel recalculate, then Save As .xlsx.")
        return 2

    n_bad = sum(len(v) for v in bad.values())
    print(f"build {info['build_id']}; data {src}; {total:,} formula cells compared")
    for sheet in sorted(count, key=lambda s: list(vals.sheetnames).index(s)):
        print(f"  {sheet:<14} {count[sheet]:>7,} cells  {len(bad.get(sheet, [])):>6,} mismatches")
    if edited:
        print(f"\n{len(edited)} input cells differ from the build (results that depend on them will differ):")
        for sheet, coord, was, now in edited[:20]:
            print(f"  {sheet}!{coord}: built {was!r}, saved {now!r}")
    for sheet, rows in bad.items():
        print(f"\n{sheet}: first {min(args.show, len(rows))} of {len(rows)} mismatches (cell, Python, Excel)")
        for b in rows[:args.show]:
            print(f"  {b['cell']:<10} {b['python']!r:<40} {b['excel']!r}")
    out = os.path.join(ROOT, "output", "phase2")
    os.makedirs(out, exist_ok=True)
    rep = os.path.join(out, "excel_compare_report.json")
    with open(rep, "w") as f:
        json.dump({"saved": os.path.abspath(args.saved), "application": app, "build_id": info["build_id"],
                   "cells_compared": dict(count), "mismatches": dict(bad), "edited_inputs": edited}, f, indent=1,
                  default=str)
    print(f"\n{'OK: every formula cell matches Python' if not n_bad else f'{n_bad:,} mismatches'}; report: {rep}")
    return 0 if not n_bad else 1


if __name__ == "__main__":
    sys.exit(main())
