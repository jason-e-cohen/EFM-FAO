"""Render the scenario-workbook data dictionary from dictionary.csv (the single source).

Writes docs/data_dictionary/Data_Dictionary.md (grouped by layer, with a contents list and an index by analyst name)
and output/data_dictionary/Data_Dictionary.xlsx (one sheet, frozen header, filters). Both are generated; edit
dictionary.csv and rerun:

    ../../.venv/bin/python docs/data_dictionary/build_dictionary.py           (from prototypes/scenario_workbook)
    ../../.venv/bin/python docs/data_dictionary/build_dictionary.py --check   (exit 1 if the markdown is stale)
    ../../.venv/bin/python docs/data_dictionary/build_dictionary.py --review  (also output/client_labels_review.xlsx)

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

COLUMNS = ["id", "layer", "analyst_name", "excel_location", "client_label", "client_definition", "client_section",
           "client_order", "client_tier", "client_label_status", "plain_name", "description", "unit", "dimensions",
           "formula", "fed_by", "feeds", "role", "depends_on_response", "depends_on_shock", "detail_level",
           "client_safe", "status", "references", "tests"]
# Spec v0.6.4 section 0B (CP-1): client_label is the plain label the workbook prints; client_definition one plain
# sentence; client_section A to H (CP-3), client_order the sort key within the section, client_tier headline, standard
# or technical. The workbook reads them through sw/dictionary.py.
CLIENT_COLUMNS = ["client_label", "client_definition", "client_section", "client_order", "client_tier"]
# Blank allowed: excel_location (Python only), fed_by (inputs, fixed text, build metadata), feeds (terminal figures),
# client_definition (rows that are not client-safe).
REQUIRED = [c for c in COLUMNS if c not in ("excel_location", "fed_by", "feeds", "client_definition")]

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
    "client_label_status": ["as_built", "drafted", "proposed"],
    "client_section": ["A", "B", "C", "D", "E", "F", "G", "H"],
    "client_tier": ["headline", "standard", "technical"],
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
SAFE_FIELDS = ("client_label", "client_definition", "plain_name", "description")
PLAIN_FIELDS = ("client_label", "client_definition")
# CP-2: code names a client label or definition must not carry (any name with '_' is one too). Single letters are the
# model's symbols (q share, t threshold, m pool multiplier, N class size, M expected class, f, p increase, T tuition);
# section letters (A. to H.) are not checked because they are never followed by a space and a lower-case word alone.
CODE_TOKENS = {"q", "t", "m", "f", "p", "N", "M", "T", "rho", "dE", "dSpend", "dNTR", "ntr", "gross", "jd", "Gp",
               "Gm", "Vm", "Vp", "Vn"}
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


def code_hits(text):
    """CP-2: code names in a client text ({placeholders} are filled at build and are not checked)."""
    t = re.sub(r"\{[^{}]*\}", " ", text)
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", t)
    return sorted({w for w in words if "_" in w or w in CODE_TOKENS})


def safe_problems(row, tokens):
    """Reasons a row marked client_safe = Y fails the client-safe rule (empty when it passes)."""
    out = []
    for f in PLAIN_FIELDS:
        if code_hits(row[f]):
            out.append(f"{f}: code name {code_hits(row[f])}")
    for f in ("client_label", "client_definition", "client_section", "client_order", "client_tier"):
        if not row[f].strip():
            out.append(f"{f}: blank")
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
             "a threshold t, a share q, a case or a year from the config. Spec v0.6.4 section 0B: the client label is "
             "the plain text the workbook prints, with a one-sentence client definition, a section (A to H), an order "
             "and a tier; *drafted* marks a label written in Phase 5 for review. A label marked *proposed* is not shown in "
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
    lab = f'"{_md(r["client_label"])}"' + (" (proposed)" if r["client_label_status"] == "proposed" else
                                           " (drafted, for review)" if r["client_label_status"] == "drafted" else "")
    return [f'<a id="{r["id"]}"></a>', "", f'#### {r["id"]} `{_md(r["analyst_name"])}`: {_md(r["plain_name"])}', "",
            _md(r["description"]), "",
            f'- Client label: {lab}',
            f'- Client definition: {_md(r["client_definition"]) or "none"}',
            f'- Section {r["client_section"]}, order {r["client_order"]}, tier {r["client_tier"]}',
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
              "client_definition": 50, "client_section": 8, "client_order": 8, "client_tier": 10,
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


REVIEW_PATH = os.path.join(ROOT, "output", "client_labels_review.xlsx")


def old_labels(ref="HEAD"):
    """The as-built client labels at a git ref (the text before the Phase 5 plain-label pass), by id."""
    import io
    import subprocess
    rel = os.path.relpath(CSV_PATH, os.path.dirname(os.path.dirname(ROOT)))
    try:
        txt = subprocess.run(["git", "show", f"{ref}:prototypes/scenario_workbook/docs/data_dictionary/dictionary.csv"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return {}
    return {r["id"]: r["client_label"] for r in csv.DictReader(io.StringIO(txt))} if rel else {}


def write_review(rows, path=REVIEW_PATH, ref="HEAD"):
    """CP-1: output/client_labels_review.xlsx for Jason's review: per client-visible row the old text (the label at
    `ref`), the new label, its definition, section, tier and order, sorted as the workbook prints them."""
    import xlsxwriter
    old = old_labels(ref)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    wb = xlsxwriter.Workbook(path)
    wb.set_properties({"title": "Client labels for review", "created": datetime.datetime(2026, 1, 1)})
    ws = wb.add_worksheet("Labels")
    head = wb.add_format({"bold": True, "bg_color": "#D9E1F2", "border": 1, "text_wrap": True, "valign": "top",
                          "font_name": "Arial", "font_size": 9})
    body = wb.add_format({"text_wrap": True, "valign": "top", "font_name": "Arial", "font_size": 9})
    chg = wb.add_format({"text_wrap": True, "valign": "top", "font_name": "Arial", "font_size": 9,
                         "bg_color": "#FFF2CC"})
    cols = [("id", 9), ("section", 7), ("tier", 10), ("order", 7), ("old text", 40), ("new label", 44),
            ("definition", 60), ("changed", 8), ("setting (code name)", 26), ("where shown", 34), ("status", 10)]
    for j, (c, w) in enumerate(cols):
        ws.write(0, j, c, head)
        ws.set_column(j, j, w)
    shown = [r for r in rows if r["client_safe"] == "Y" or r["client_label_status"] == "drafted"
             or r["excel_location"].startswith(("Inputs", "Levers", "Summary", "Overview", "Charts"))]
    tr = {"headline": 0, "standard": 1, "technical": 2}
    shown.sort(key=lambda r: (r["client_section"], tr.get(r["client_tier"], 9), float(r["client_order"] or 1e9),
                              r["id"]))
    for i, r in enumerate(shown, start=1):
        o = old.get(r["id"], "(new row)")
        changed = "Y" if o != r["client_label"] else "N"
        vals = [r["id"], r["client_section"], r["client_tier"], r["client_order"], o, r["client_label"],
                r["client_definition"], changed, r["analyst_name"], r["excel_location"], r["client_label_status"]]
        for j, v in enumerate(vals):
            ws.write_string(i, j, v, chg if (changed == "Y" and j == 5) else body)
    ws.freeze_panes(1, 1)
    ws.autofilter(0, 0, len(shown), len(cols) - 1)
    wb.close()
    return path, len(shown)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="exit 1 if Data_Dictionary.md differs from a fresh render")
    ap.add_argument("--review", action="store_true",
                    help="also write output/client_labels_review.xlsx (old text from git HEAD; spec 0B CP-1)")
    a = ap.parse_args(argv)
    rows = load()
    if a.review:
        path, n = write_review(rows)
        print(f"{n} client-visible rows -> {os.path.relpath(path, ROOT)}")
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
