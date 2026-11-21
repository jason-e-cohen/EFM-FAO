"""Render the scenario-workbook data dictionary from dictionary.csv (the single source).

Writes docs/data_dictionary/Data_Dictionary.md (grouped by layer, with a contents list and an index by analyst name)
and output/data_dictionary/Data_Dictionary.xlsx (one sheet, frozen header, filters). Both are generated; edit
dictionary.csv and rerun:

    ../../.venv/bin/python docs/data_dictionary/build_dictionary.py           (from prototypes/scenario_workbook)
    ../../.venv/bin/python docs/data_dictionary/build_dictionary.py --check   (exit 1 if the markdown is stale)

The helpers below (vocabularies, required columns, the client-safe text checks) are shared with
tests/test_28_dictionary.py.
"""
import argparse
import csv
import datetime
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CSV_PATH = os.path.join(HERE, "dictionary.csv")
MD_PATH = os.path.join(HERE, "Data_Dictionary.md")
XLSX_PATH = os.path.join(ROOT, "output", "data_dictionary", "Data_Dictionary.xlsx")

COLUMNS = ["id", "layer", "analyst_name", "excel_location", "client_label", "client_label_status", "plain_name",
           "description", "unit", "dimensions", "formula", "fed_by", "feeds", "role", "depends_on_response",
           "depends_on_shock", "detail_level", "client_safe", "status", "references", "tests"]
# Blank allowed: excel_location (Python only), fed_by (inputs, fixed text, build metadata), feeds (terminal figures).
REQUIRED = [c for c in COLUMNS if c not in ("excel_location", "fed_by", "feeds")]

LAYERS = [("input_config", "Inputs: client config", "Keys of config/<client>.yaml that the loader names or the "
                                                     "configs carry."),
          ("input_scenario", "Inputs: scenario levers", "Fields of the scenario file and the Levers sheet."),
          ("input_data", "Inputs: cell data", "Columns of the cell data (cells.csv)."),
          ("input_workbook", "Inputs: other workbook cells", "Editable workbook cells that are not config keys or "
                                                             "levers (the case selector and the Reproduce sheet)."),
          ("ledger", "Ledger columns", "Columns of Ledger_Low, Ledger_Middle and Ledger_High (one row per header; "
                                       "the three sheets share them)."),
          ("output", "Outputs", "Summary figures and contract ranges, strips, class-size table, segment and "
                                "incentive blocks, narratives, History, Levers counts, Distribution, RunLog and the "
                                "label constants."),
          ("check", "Checks", "Checks sheet rows and the check messages."),
          ("internal", "Internals", "Python and Excel intermediates. Not client-facing; listed so a reader can see "
                                    "what each does and what it feeds.")]
LAYER_IDS = {"input_config": "IN", "input_scenario": "IN", "input_data": "IN", "input_workbook": "IN", "ledger": "LG",
             "output": "OUT", "check": "CK", "internal": "INT"}
VOCAB = {
    "layer": [x[0] for x in LAYERS],
    "client_label_status": ["as_built", "proposed"],
    "unit": ["count", "rate", "ratio", "USD", "percent", "points", "points per $1,000", "probability", "score", "GPA",
             "multiplier", "year", "date", "text", "flag", "list"],
    "role": ["primary", "derived", "display", "input", "internal"],
    "depends_on_response": ["Y", "N"],
    "depends_on_shock": ["Y", "N"],
    "detail_level": ["core", "supporting", "internal"],
    "client_safe": ["Y", "N"],
    "status": ["live", "held under hold_position_rows", "reproduce only", "display only"],
}
ID_RE = re.compile(r"^(IN|LG|OUT|CK|INT)-\d{3}$")

# --- client-safe text checks (client_label, plain_name, description) -------------------------------------------
SAFE_FIELDS = ("client_label", "plain_name", "description")
# Review, decision and finding IDs: R4-06, P2-03, P1.1-1, Q-8e, BM-1, OD-14, B3-1, V27-01, R-01, F-4, R3-4; O37; D13
RID_RE = re.compile(r"\b(?:[A-Z]{1,3}\d*(?:\.\d+)?-\d+[a-z]?|O\d{2}|D\d{1,2})\b")
NUM_RE = re.compile(r"(?<![A-Za-z0-9_.])\d[\d,]*(?:\.\d+)?(?![A-Za-z0-9])")
# Numbers a client-safe text may contain: 0 and 1, the public ABA 509 form name, and product rules stated in the spec
# (90% range, 5% / 95% display bounds, rho 0.5, the 0.25 / 0.75 spread shares, the $1,000 slope unit, the 20 and 30
# approximation thresholds). Never a client or fixture figure; ordinals such as 25th are not numbers here.
ALLOWED_NUMBERS = {"0", "1", "5", "20", "30", "90", "95", "0.5", "0.25", "0.75", "1,000", "509"}


def rid_hits(text):
    return RID_RE.findall(text)


def key_tokens(rows):
    """Config and scenario key names that must not appear in client-safe text: every input_config and input_scenario
    analyst name that contains '_' or '.', and each dotted name's last part when it contains '_'."""
    out = set()
    for row in rows:
        if row["layer"] in ("input_config", "input_scenario"):
            n = row["analyst_name"]
            if "_" in n or "." in n:
                out.add(n)
            last = n.split(".")[-1]
            if "_" in last:
                out.add(last)
    return out


def key_hits(text, tokens):
    words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_.]*[A-Za-z0-9_]", text))
    dotted = set(re.findall(r"\b[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*\b", text))
    return sorted((words & tokens) | {d for d in dotted if d.split(".")[0] in {t.split(".")[0] for t in tokens}})


def number_hits(text):
    return [n for n in NUM_RE.findall(text) if n.rstrip(".") not in ALLOWED_NUMBERS]


def safe_problems(row, tokens):
    """Reasons a row marked client_safe = Y fails the client-safe rule (empty when it passes)."""
    out = []
    for f in SAFE_FIELDS:
        t = row[f]
        if rid_hits(t):
            out.append(f"{f}: review ID {rid_hits(t)}")
        if key_hits(t, tokens):
            out.append(f"{f}: config key {key_hits(t, tokens)}")
        if number_hits(t):
            out.append(f"{f}: number {number_hits(t)}")
    return out


# --- load and render ----------------------------------------------------------------------------------------------

def load(path=CSV_PATH):
    with open(path, newline="") as fh:
        rows = list(csv.DictReader(fh))
    return rows


def split_ids(v):
    return [x.strip() for x in v.split(";") if x.strip()]


def _md(t):
    return t.replace("|", "\\|").replace("\n", " ")


def render_markdown(rows):
    by_layer = {k: [r for r in rows if r["layer"] == k] for k, _, _ in LAYERS}
    lines = ["# Scenario-workbook data dictionary", "",
             "Generated from `dictionary.csv` by `build_dictionary.py`; do not edit by hand. One entry per variable, "
             "grouped by layer. Client labels with `{braces}` are templates: the workbook fills in the score measure, "
             "a threshold t, a share q, a case or a year from the config. A label marked *proposed* is not shown in "
             "the workbook. Test 28 checks this file against the code, the configs and a fresh synthetic build.", "",
             "Columns: `role` follows Methods_Reference section 8 (primary, derived, display; plus input and "
             "internal). `response` and `shock` say whether the figure depends on the placeholder response slopes and "
             "on the year-shock settings (s, rho). `client-safe` Y means the label, name and description carry no "
             "review IDs, config key names or internals. Client-facing work still needs human review before it is "
             "sent.", "", "## Contents", "",
             "| Layer | Rows | Core | Supporting | Internal |", "|---|---:|---:|---:|---:|"]
    for k, title, _ in LAYERS:
        rs = by_layer[k]
        n = {d: sum(1 for r in rs if r["detail_level"] == d) for d in VOCAB["detail_level"]}
        anchor = "layer-" + k.replace("_", "-")
        lines.append(f"| [{title}](#{anchor}) | {len(rs)} | {n['core']} | {n['supporting']} | {n['internal']} |")
    lines += [f"| Total | {len(rows)} | " + " | ".join(
        str(sum(1 for r in rows if r["detail_level"] == d)) for d in VOCAB["detail_level"]) + " |", "",
              "- [Index by analyst name](#index-by-analyst-name)", ""]
    for k, title, blurb in LAYERS:
        lines += [f'<a id="layer-{k.replace("_", "-")}"></a>', "", f"## {title}", "", blurb, ""]
        for r in by_layer[k]:
            lines += _entry(r)
    lines += ['<a id="index-by-analyst-name"></a>', "", "## Index by analyst name", "", "| Analyst name | Rows |",
              "|---|---|"]
    idx = {}
    for r in rows:
        idx.setdefault(r["analyst_name"], []).append(r["id"])
    for name in sorted(idx, key=lambda s: (s.lower(), s)):
        lines.append(f"| `{_md(name)}` | " + ", ".join(f"[{i}](#{i})" for i in idx[name]) + " |")
    return "\n".join(lines) + "\n"


def _links(v):
    ids = split_ids(v)
    return ", ".join(f"[{i}](#{i})" for i in ids) if ids else "none"


def _entry(r):
    lab = f'"{_md(r["client_label"])}"' + (" (proposed)" if r["client_label_status"] == "proposed" else "")
    return [f'<a id="{r["id"]}"></a>', "", f'#### {r["id"]} `{_md(r["analyst_name"])}`: {_md(r["plain_name"])}', "",
            _md(r["description"]), "",
            f'- Client label: {lab}',
            f'- Excel: {_md(r["excel_location"]) or "Python only"}',
            f'- Unit: {r["unit"]}; dimensions: {r["dimensions"]}',
            f'- Formula: {_md(r["formula"])}',
            f'- Fed by: {_links(r["fed_by"])}',
            f'- Feeds: {_links(r["feeds"])}',
            f'- Role: {r["role"]}; response: {r["depends_on_response"]}; shock: {r["depends_on_shock"]}; detail: '
            f'{r["detail_level"]}; client-safe: {r["client_safe"]}; status: {r["status"]}',
            f'- References: {_md(r["references"])}; tests: {r["tests"]}', ""]


def write_xlsx(rows, path=XLSX_PATH):
    import xlsxwriter
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wb = xlsxwriter.Workbook(path)
    wb.set_properties({"title": "Scenario-workbook data dictionary", "created": datetime.datetime(2026, 1, 1)})
    ws = wb.add_worksheet("Dictionary")
    head = wb.add_format({"bold": True, "bg_color": "#D9E1F2", "border": 1, "text_wrap": True, "valign": "top",
                          "font_name": "Arial", "font_size": 9})
    body = wb.add_format({"text_wrap": True, "valign": "top", "font_name": "Arial", "font_size": 9})
    widths = {"id": 9, "layer": 13, "analyst_name": 26, "excel_location": 34, "client_label": 40,
              "client_label_status": 10, "plain_name": 26, "description": 60, "unit": 10, "dimensions": 18,
              "formula": 40, "fed_by": 22, "feeds": 22, "role": 9, "depends_on_response": 9, "depends_on_shock": 9,
              "detail_level": 10, "client_safe": 8, "status": 14, "references": 34, "tests": 12}
    for j, c in enumerate(COLUMNS):
        ws.write(0, j, c, head)
        ws.set_column(j, j, widths[c])
    for i, r in enumerate(rows, start=1):
        for j, c in enumerate(COLUMNS):
            ws.write_string(i, j, r[c], body)
    ws.freeze_panes(1, 2)
    ws.autofilter(0, 0, len(rows), len(COLUMNS) - 1)
    wb.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if Data_Dictionary.md differs from a fresh render")
    a = ap.parse_args(argv)
    rows = load()
    md = render_markdown(rows)
    if a.check:
        with open(MD_PATH) as fh:
            same = fh.read() == md
        print("Data_Dictionary.md is current" if same else "Data_Dictionary.md is stale: rerun build_dictionary.py")
        return 0 if same else 1
    with open(MD_PATH, "w") as fh:
        fh.write(md)
    write_xlsx(rows)
    print(f"{len(rows)} rows -> {os.path.relpath(MD_PATH, ROOT)}, {os.path.relpath(XLSX_PATH, ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
