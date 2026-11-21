"""Test 28: the data dictionary (docs/data_dictionary/dictionary.csv) matches the code, the configs and a fresh
synthetic build, and the rendered markdown is current.

Fails when a config key the loader names or the configs carry, a scenario lever, a cell-data column, a Ledger header, an
Inputs name, a Summary or Checks label, a contract range or a label constant has no row; when a row names something that
no longer exists; when a fed_by or feeds id is missing or the two disagree; when a required column is blank or off its
vocabulary; when a client-safe row carries a review ID, a config key or a number outside the product-rule allowlist (or,
with YA_FIXTURE_PATH set, a number found in the fixture); or when Data_Dictionary.md differs from a fresh render.
No LibreOffice: the builds are read for their text, labels and names only.
"""
import glob
import os
import re
import sys

import openpyxl
import pytest
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DD = os.path.join(ROOT, "docs", "data_dictionary")
sys.path.insert(0, DD)

import build_dictionary as B  # noqa: E402
from sw import build, cells as cells_mod, config, contract, labels  # noqa: E402
from sw import workbook as wbmod  # noqa: E402

MAP_KEYS = {"tuition_by_cohort", "tuition_increase_by_year", "tuition_by_year_usd", "merit_actual_by_cohort",
            "aba_509_by_cohort"}
BLOCK_KEYS = {"generator", "test4", "reproduce", "aba_509_by_cohort"}   # a row for the block and for its keys
LABEL_LOC = "sw/labels.py constant"
STRIP_TABLES = {"tuition_whatif", "yield_strip", "pool_strip", "class_table", "pool_breakeven_m"}


@pytest.fixture(scope="module")
def rows():
    return B.load()


@pytest.fixture(scope="module")
def by_id(rows):
    return {r["id"]: r for r in rows}


@pytest.fixture(scope="module")
def builds(tmp_path_factory):
    """A fresh live synthetic build and a synthetic reproduce build (Python only; cached values are read)."""
    from sw import reproduce
    out = tmp_path_factory.mktemp("dd_builds")
    live, _ = build.build(os.path.join(ROOT, "config", "synthetic.yaml"), "synthetic",
                          os.path.join(ROOT, "config", "scenarios_synthetic.yaml"), str(out / "live"), seed=101)
    rep, _ = reproduce.build_synthetic(str(out / "repro"), 101)
    return {"live": openpyxl.load_workbook(live, data_only=False), "repro": openpyxl.load_workbook(rep, data_only=False)}


def texts(ws, col=None, row=None):
    out = []
    for r in ws.iter_rows():
        for c in r:
            if isinstance(c.value, str) and not c.value.startswith("=") and (col is None or c.column == col) \
                    and (row is None or c.row == row):
                out.append(c.value)
    return out


def template_re(t):
    """A client label template as a regex: {placeholders} match any text."""
    parts = re.split(r"\{[^{}]*\}", t)
    return re.compile("^" + ".+?".join(re.escape(p) for p in parts) + "$", re.S)


def alternatives(row):
    """Templates a workbook text may match for this row: the client label (split on ' / '), and every quoted
    'text' in excel_location (a figure shown under another label)."""
    alts = [row["client_label"]] + [a for a in row["client_label"].split(" / ") if a != row["client_label"]]
    alts += re.findall(r"'([^']+)'", row["excel_location"])
    return [template_re(a) for a in alts if a]


def matches(text, rs):
    return any(rx.match(text) for r in rs for rx in alternatives(r))


# --- structure ---------------------------------------------------------------------------------------------------

def test_columns_ids_and_vocabulary(rows):
    with open(B.CSV_PATH) as fh:
        assert fh.readline().strip().split(",") == B.COLUMNS
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate ids"
    bad = []
    for r in rows:
        if not B.ID_RE.match(r["id"]) or r["id"].split("-")[0] != B.LAYER_IDS.get(r["layer"]):
            bad.append((r["id"], "id/layer"))
        for c in B.REQUIRED:
            if not r[c].strip():
                bad.append((r["id"], f"blank {c}"))
        for c, vocab in B.VOCAB.items():
            if r[c] not in vocab:
                bad.append((r["id"], f"{c}={r[c]!r}"))
        if r["layer"].startswith("input") and r["formula"] != "input":
            bad.append((r["id"], "input formula must be 'input'"))
        if not r["layer"].startswith("input") and r["role"] != "display" and not r["formula"].startswith("fixed") \
                and not r["fed_by"].strip():
            bad.append((r["id"], "blank fed_by"))
        if r["layer"] == "internal" and r["client_safe"] != "N":
            bad.append((r["id"], "internal rows are not client-safe"))
    assert not bad, bad


def test_fed_by_and_feeds_agree(rows, by_id):
    bad = []
    for r in rows:
        for col, other in (("fed_by", "feeds"), ("feeds", "fed_by")):
            for i in B.split_ids(r[col]):
                if i not in by_id:
                    bad.append((r["id"], col, i, "missing"))
                elif r["id"] not in B.split_ids(by_id[i][other]):
                    bad.append((r["id"], col, i, f"not in its {other}"))
    assert not bad, bad[:20]


def test_tests_column_names_real_tests(rows):
    have = {int(re.match(r"test_(\d+)_", os.path.basename(p)).group(1))
            for p in glob.glob(os.path.join(ROOT, "tests", "test_*.py"))} | {20}      # 20: tests/mutation_check.py
    bad = [(r["id"], t) for r in rows for t in B.split_ids(r["tests"]) if not t.isdigit() or int(t) not in have]
    assert not bad, bad


# --- inputs ------------------------------------------------------------------------------------------------------

def _flatten(d, prefix=""):
    out = set()
    for k, v in d.items():
        key = f"{prefix}{k}"
        out.add(key)
        if k in MAP_KEYS or (prefix == "" and k in ("generator", "test4")):
            continue
        if isinstance(v, dict):
            out |= _flatten(v, key + ".")
        elif isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
            for x in v:
                out |= _flatten(x, key + ".")
    return out


def config_universe():
    keys = set(config.REQUIRED)
    for k, v in config.DEFAULTS.items():
        keys.add(k)
        if isinstance(v, dict):
            keys |= {f"{k}.{kk}" for kk in v}
    keys |= {f"reproduce.{k}" for k in config.REPRODUCE_KEYS}
    keys |= {f"aba_509_by_cohort.{k}" for k in config.ABA_509_KEYS}
    keys |= {"score.percentile_targets.q", "score.percentile_targets.t", "score.median_thresholds",
             "class.supported_range", "class.reject_range"}
    keys |= {f"risk.sensitivity_slopes.{c}" for c in ("low", "middle", "high")}
    keys |= {f"risk.{b}.{g}" for b in ("yield_floor", "yield_cap") for g in config.SCORE_GROUPS}
    keys |= {f"segments.{k}" for k in ("name", "members_label", "share_source")} | {"segments.within.residency"}
    for name in ("synthetic.yaml", "richmond.yaml"):
        with open(os.path.join(ROOT, "config", name)) as fh:
            keys |= _flatten(yaml.safe_load(fh))
    parents = {k.rsplit(".", 1)[0] for k in keys if "." in k}
    # a parent key with child keys has no row of its own (client, cycle, score, ...), except the blocks and segments
    return {k for k in keys if k not in parents or k in BLOCK_KEYS | {"segments", "score.percentile_targets"}} \
        - {"segments.within"}


def test_every_config_key_has_a_row_and_no_row_is_stale(rows):
    have = {r["analyst_name"] for r in rows if r["layer"] == "input_config"}
    want = config_universe()
    assert not want - have, f"config keys without a row: {sorted(want - have)}"
    assert not have - want, f"input_config rows naming no config key: {sorted(have - want)}"


def test_every_scenario_lever_has_a_row(rows):
    have = {r["analyst_name"] for r in rows if r["layer"] == "input_scenario"}
    want = set(build.SCENARIO_FIELDS) | {"name", "parent", "admit_rate", "award_usd", "full_tuition"}
    assert {f for f, _, _ in wbmod.LEVER_FIELDS} <= want
    assert have == want, (sorted(want - have), sorted(have - want))


def test_cell_data_columns(rows):
    assert {r["analyst_name"] for r in rows if r["layer"] == "input_data"} == set(cells_mod.COLUMNS)


def test_inputs_names(rows, builds):
    names = {n for b in builds.values() for n in b.defined_names if n.startswith("in_")}
    mentioned = set(re.findall(r"\bin_[a-z0-9_]+", " ".join(r["excel_location"] + " " + r["analyst_name"]
                                                             for r in rows)))
    assert not names - mentioned, f"Inputs names without a row: {sorted(names - mentioned)}"
    assert not mentioned - names, f"rows naming Inputs names that do not exist: {sorted(mentioned - names)}"


# --- Ledger, Summary, Checks --------------------------------------------------------------------------------------

def ledger_headers(wb):
    ws = wb["Ledger_Middle"]
    heads = set(texts(ws, row=8))
    for r in range(3, 8):
        heads |= {t for t in texts(ws, row=r)}
    return heads | ({"Total"} & set(texts(ws, col=1)))


def test_ledger_headers(rows, builds):
    lg = [r for r in rows if r["layer"] == "ledger"]
    heads = ledger_headers(builds["live"]) | ledger_headers(builds["repro"])
    missing = sorted(h for h in heads if not matches(h, lg))
    assert not missing, f"Ledger headers without a row: {missing}"
    stale = [r["id"] for r in lg if not any(template_re(r["client_label"]).match(h) for h in heads)]
    assert not stale, f"ledger rows whose header is not in the build: {stale}"


def summary_labels(wb):
    """Figure labels (column A of the figure tables) and strip column headers on the Summary."""
    ws = wb["Summary"]
    a = {c.row: c.value for c in ws["A"] if isinstance(c.value, str)}
    out = set()
    stop = next(r for r, v in a.items() if v.startswith("Interface contract ranges"))
    in_table = False
    for r in range(1, stop):
        v = a.get(r)
        if v in ("figure",):
            in_table = True
            continue
        if v is None or v == "":
            in_table = False if v is None else in_table
            continue
        if v in ("scenario", "scenario: split at m = 1"):
            out |= set(t for t in texts(ws, row=r) if t != v)
            in_table = False
            continue
        if in_table and len(v) <= 200:
            out.add(v)
    return out


def test_summary_labels(rows, builds):
    outs = rows                                         # echoes of levers sit on their input rows
    scen = {s for b in builds.values() for s in texts(b["Levers"], row=4)}
    labs = (summary_labels(builds["live"]) | summary_labels(builds["repro"])) - scen - {"case", "unit", "part"}
    missing = sorted(t for t in labs if not matches(t, outs))
    assert not missing, f"Summary labels without a row: {missing}"


def check_labels(wb):
    return {t for t in texts(wb["Checks"], col=1)[2:] if not t.startswith(("  conflict", "  more"))}


def test_checks_rows(rows, builds):
    cks = [r for r in rows if r["layer"] == "check" and not r["excel_location"].startswith(LABEL_LOC)]
    labs = check_labels(builds["live"]) | check_labels(builds["repro"])
    missing = sorted(t for t in labs if not matches(t, cks))
    assert not missing, f"Checks rows without a dictionary row: {missing}"
    src = open(os.path.join(ROOT, "sw", "workbook.py")).read()
    stale = []
    for r in cks:
        if any(template_re(r["client_label"]).match(t) for t in labs):
            continue
        frag = re.split(r"\{|\.\.\.", r["client_label"])[0][:40]
        if frag not in src:
            stale.append(r["id"])
    assert not stale, f"check rows found neither in the builds nor in sw/workbook.py: {stale}"


# --- contract names and label constants ---------------------------------------------------------------------------

def test_contract_names(rows, builds):
    names = {r["analyst_name"] for r in rows}
    locs = " ".join(r["excel_location"] for r in rows)
    bad = []
    for rng, name, _, _ in contract.contract_table():
        base = name.split("[")[0]
        if rng not in locs and rng not in names:
            bad.append(rng)
        if base not in names and rng not in names:
            bad.append(name)
    for name in contract.PYTHON_ONLY:
        if name not in names:
            bad.append(name)
    assert not bad, f"contract names without a row: {bad}"
    defined = {n for b in builds.values() for n in b.defined_names}
    cited = set(re.findall(r"named range ([A-Z][A-Z0-9_]+)", locs))
    assert not cited - defined, f"rows citing named ranges that do not exist: {sorted(cited - defined)}"


def test_label_constants(rows):
    consts = {k: v for k, v in vars(labels).items() if k.isupper()}
    lab_rows = {r["analyst_name"]: r for r in rows if r["excel_location"].startswith(LABEL_LOC)}
    assert set(lab_rows) == set(consts), (sorted(set(consts) - set(lab_rows)), sorted(set(lab_rows) - set(consts)))
    for k, v in consts.items():
        text = "; ".join(f"{a}: {b}" for a, b in v.items()) if isinstance(v, dict) else v
        assert lab_rows[k]["client_label"] == text, f"{k}: text changed in sw/labels.py"


# --- every row names something that exists -------------------------------------------------------------------------

def test_strip_columns_exist(rows):
    cfg = config.load(os.path.join(ROOT, "config", "synthetic.yaml"))
    cols = contract.strip_columns(cfg)
    cols["pool_breakeven_m"] = ["m_class", "m_median", "m_q"]
    for r in rows:
        m = re.match(r"^([a-z_]+)\[(.+)\]$", r["analyst_name"])
        if not m or m.group(1) not in cols:
            continue
        rx = template_re(m.group(2))
        assert any(rx.match(c) for c in cols[m.group(1)]), f"{r['id']}: {r['analyst_name']} is not a strip column"


def test_names_exist(rows, builds):
    src = " ".join(open(p).read() for p in glob.glob(os.path.join(ROOT, "sw", "*.py")))
    built = set()
    for b in builds.values():
        for ws in b.worksheets:
            built |= set(texts(ws))
    tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", src))
    bad = []
    for r in rows:
        n = r["analyst_name"]
        if r["layer"] in ("input_config", "input_scenario", "input_data", "ledger") or n.startswith("in_"):
            continue                                    # checked exactly above
        m = re.match(r"^([a-z_]+)\[", n)
        if m and m.group(1) in STRIP_TABLES:
            continue                                    # checked in test_strip_columns_exist
        rx = template_re(n)
        if any(rx.match(t) for t in built):
            continue
        words = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", re.sub(r"\{[^}]*\}", "", n))
        if not words or any(w not in tokens for w in words):
            bad.append((r["id"], n))
    assert not bad, f"rows naming nothing in sw/*.py or the build: {bad}"


# --- client-safe rows ----------------------------------------------------------------------------------------------

def test_client_safe_rows(rows):
    tokens = B.key_tokens(rows)
    bad = [(r["id"], B.safe_problems(r, tokens)) for r in rows if r["client_safe"] == "Y" and B.safe_problems(r, tokens)]
    assert not bad, bad


def test_no_fixture_number(rows):
    """With the fixture: no distinctive number from it (three or more significant digits) appears in any text column.
    Without it, test_client_safe_rows already limits client-safe text to product-rule numbers."""
    p = os.environ.get("YA_FIXTURE_PATH")
    if not p or not os.path.exists(p):
        pytest.skip("YA_FIXTURE_PATH not set: fixture-number scan skipped")
    wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
    fx = set()
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            for v in row:
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    for s in {f"{v:g}", f"{v:,.0f}", f"{v:.0f}", f"{v:.2f}", f"{v:.3f}", f"{v:.4f}"}:
                        if len(re.sub(r"[^0-9]", "", s).strip("0")) >= 3:
                            fx.add(s)
    wb.close()
    cols = ("client_label", "plain_name", "description", "formula", "excel_location")
    hits = [(r["id"], n) for r in rows for c in cols for n in B.NUM_RE.findall(r[c])
            if n not in B.ALLOWED_NUMBERS and n in fx]
    assert not hits, f"fixture-derived numbers in the dictionary: {hits}"


# --- rendered markdown ---------------------------------------------------------------------------------------------

def test_markdown_is_current(rows):
    with open(B.MD_PATH) as fh:
        assert fh.read() == B.render_markdown(rows), "Data_Dictionary.md is stale: run build_dictionary.py"
