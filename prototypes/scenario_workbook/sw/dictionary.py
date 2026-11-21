"""Client text from the data dictionary (spec v0.6.4 section 0B, CP-1).

`docs/data_dictionary/dictionary.csv` is the one source of every client-visible label, definition, section, order and
tier the workbook prints. The workbook reads it at build time through this module; the build id hashes the CSV
(sw/build.py), so a wording change is a CSV edit and a rebuild. Labels may be templates: `{name}` placeholders are
filled from keyword arguments (score measure, threshold, ordinal, segment, figure, ...).

Sections (CP-3): A class size, B revenue and aid, C academic profile, D priority segment, E incentive, F what-if
tables, G award distribution, H technical detail. Tiers: headline (Overview and the top of each section), standard,
technical (moved to section H).
"""
import csv
import hashlib
import os
import string

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "docs", "data_dictionary", "dictionary.csv")
SECTIONS = ["A", "B", "C", "D", "E", "F", "G", "H"]
TIERS = ["headline", "standard", "technical"]
TIER_RANK = {t: i for i, t in enumerate(TIERS)}

_cache = {}


def _load(path=CSV_PATH):
    key = os.path.abspath(path)
    if key not in _cache:
        with open(path, newline="") as fh:
            rows = list(csv.DictReader(fh))
        _cache[key] = {r["id"]: r for r in rows}
    return _cache[key]


def rows():
    return list(_load().values())


def row(rid):
    try:
        return _load()[rid]
    except KeyError:
        raise KeyError(f"dictionary.csv has no row {rid}") from None


class _Fill(string.Formatter):
    """str.format that requires every placeholder (a missing one is a build error, never silent text)."""

    def get_value(self, key, args, kwargs):
        if key not in kwargs:
            raise KeyError(f"placeholder {{{key}}} not given")
        return kwargs[key]


def fill(template, **kw):
    return _Fill().format(template, **kw) if "{" in template else template


def label(rid, **kw):
    """The plain label of row rid (CP-1), placeholders filled."""
    return fill(row(rid)["client_label"], **kw)


def definition(rid, **kw):
    return fill(row(rid)["client_definition"], **kw)


def section(rid):
    return row(rid)["client_section"]


def tier(rid):
    return row(rid)["client_tier"]


def order(rid):
    v = row(rid)["client_order"]
    return float(v) if v else 1e9


def sort_key(rid, inst=0):
    return (TIER_RANK.get(tier(rid), 9), order(rid), inst)


def csv_hash(path=CSV_PATH):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def rid(name, layer="output"):
    """The id of the row with this analyst name in `layer` (the Phase 5 display rows: section titles, chart titles)."""
    hits = [r["id"] for r in _load().values() if r["analyst_name"] == name and r["layer"] == layer]
    if len(hits) != 1:
        raise KeyError(f"dictionary.csv: {len(hits)} {layer} rows named {name!r}")
    return hits[0]


def lab(name, **kw):
    """label(rid(name)): the plain label of a display row named by its analyst name."""
    return label(rid(name), **kw)
