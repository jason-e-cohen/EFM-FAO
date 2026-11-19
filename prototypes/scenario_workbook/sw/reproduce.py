"""Reproduce mode (spec section 9): load the validation fixture and build a workbook whose Ledgers run on the
fixture's admit rates, awards, yields, pool settings and tuition as loaded values; compare with the fixture.

    python -m sw.reproduce --out output/ [--sentinel]        (reads YA_FIXTURE_PATH)
    python -m sw.reproduce --out output/ --synthetic 101 [--sentinel]   (synthetic reproduce build, no fixture)

Rules (spec rule 3, section 14). The fixture is read at run time only, read-only. Nothing in this module holds a
fixture value: the constants below are the layout stated in spec section 9 (sheet names, panel columns, row ranges),
checked on load. Everything the loader reads, and every workbook and report built from it, goes under output/
(git-ignored). The fixture's wording is parsed, never reproduced: the workbook uses our own layout and labels.

What is loaded and how (each rule is reported in the run's notes):
- Cells: one per labelled row of the panels (in-state and out-of-state). The score part of the label gives score_lo
  (a range or "N+" gives its lower bound; "<N" gives the lowest configured band; a non-numeric part, another test or
  none, is unscored); the GPA part gives the class (lower bound at or above gpa.hi_at_or_above: hi; blank: blank;
  otherwise lo). The fixture has residency only, so every cell's segment is blank.
- History: admits, award $ and enrolled per cohort; applications = admits / admit rate, rounded to whole applications
  when within 1e-6 of an integer (counts). Where the admit rate is 0 or blank the applications are unknown: History
  shows them blank ("not in file") and the ledger reads 0 (DECISIONS Nov 18).
- Unknown base-cycle applications in a cell that some scenario admits students to are recovered from the scenario
  columns: the whole number c with round(round(c x pool_s) x rate_s) = admits_s in every scenario (applications
  rounded as reproduce.round_apps_after_pool says). Loaded only when exactly one c fits; otherwise the cell is "not
  reproducible from the file", excluded from the pass criteria (file and ledger alike) and counted in the report.
- Tuition by cohort and each scenario's tuition: award $ / award % (the column's median; the spread is reported).
- Scenarios: the panel columns after the cohorts with any admits; the summary sheet's block of the same name gives the
  description (lineage and pool assumption), the money rows, the count rows and the narrative.
  - parent: the first scenario name the description mentions, else the previous scenario.
  - pool multiplier: the description's "+P% <pool_threshold>+" figure, else the parent's (Baseline: 1).
  - specialty_usd: the specialty row. need_total: config need.total, less any departure of the need row from the
    fixture's own need rule (need rate rounded to whole dollars x class), which is how a scenario's need change shows.
  - admit rates, awards and yields: the scenario's panel columns (blank as 0). full_tuition: award at or above the
    scenario's tuition. Children carry only the cells that differ from the parent (spec section 2).
- Settings: mode reproduce, integer admits and enrolled, tuition_increase_by_year, unscored_in_median and
  round_apps_after_pool from the config's `reproduce` block (spec sections 2 and 9; DECISIONS Nov 18). The fixture's
  own counting rule is detected from its count rows and reported; it does not change the setting.
"""
import argparse
import copy
import hashlib
import io
import json
import math
import os
import re

import numpy as np
import pandas as pd
import yaml

from . import CASES
from . import ledger as L
from . import response
from .cells import COLUMNS, from_long
from .config import ConfigError, round_apps_after_pool, round_to, scenario_tuition, validate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = "YA_FIXTURE_PATH"

# Layout (spec section 9, verified October 30 file); checked on load.
PANEL_SHEET = "Client Strategy Comparison"
SUMMARY_SHEET = "Client Scenarios"
PANELS = {"rate": "B", "admits": "O", "pct": "AB", "award": "AO", "yield": "BB", "enrolled": "BO"}
PANEL_WIDTH = 12
HEADER_ROW = 4
CELL_ROWS = {"in": (7, 40), "out": (59, 92)}
SUMMARY_HEADER_ROW = 4
SUMMARY_DESCRIPTION_ROW = 5
SUMMARY_BLOCK_WIDTH = 8
SUMMARY_SCAN_ROWS = (100, 204)
SUMMARY_NARRATIVE_ROW = 189

NOT_REPRODUCIBLE = "not reproducible from the file"

CRITERIA = ["class", "merit", "ntr", "at_or_above_score", "below_floor", "gpa_hi", "full_tuition", "no_merit_award",
            "margin_score", "margin_gpa"]


class FixtureError(ValueError):
    pass


def _col(letter):
    from openpyxl.utils import column_index_from_string
    return column_index_from_string(letter) - 1


def _num(v):
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def _z(v):
    x = _num(v)
    return 0.0 if x is None else x


# ---------------------------------------------------------------------------------------------------------------
# Labels

def parse_label(label, cfg):
    """(score_lo, gpa_class) for a panel row label 'score part, GPA part' (rules in the module docstring)."""
    if "," not in label:
        raise FixtureError(f"cell label without a score and GPA part: {label!r}")
    sp, gp = [x.strip() for x in label.split(",", 1)]
    bands = [float(b) for b in cfg["score"]["bands"]]
    m = re.fullmatch(r"(\d+)(?:\+|-\d+)?", sp)
    if m:
        lo = float(m.group(1))
        if lo not in bands:
            raise FixtureError(f"score band {sp!r} has a lower bound outside score.bands")
    elif re.fullmatch(r"<\s*\d+", sp):
        lo = min(bands)
    elif re.search(r"\d", sp):
        raise FixtureError(f"score part not understood: {sp!r}")
    else:
        lo = float("nan")
    hi_t = float(cfg["gpa"]["hi_at_or_above"])
    if "blank" in gp.lower():
        g = "blank"
    else:
        m = re.fullmatch(r"([\d.]+)\s*(\+|-\s*[\d.]+)", gp)
        if m:
            g = "hi" if float(m.group(1)) >= hi_t - 1e-9 else "lo"
        elif re.fullmatch(r"<\s*[\d.]+", gp):
            g = "lo"
        else:
            raise FixtureError(f"GPA part not understood: {gp!r}")
    return lo, g


# ---------------------------------------------------------------------------------------------------------------
# Loader

def load_fixture(path, cfg_raw):
    """Read the fixture. Returns a dict: cells (long DataFrame), cohorts, tuition_by_cohort, scenarios (ordered list
    of dicts), summary figures per scenario, the detected counting rule, and notes."""
    import openpyxl
    if not path or not os.path.exists(path):
        raise FixtureError(f"fixture not found: {path!r}")
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sh in (PANEL_SHEET, SUMMARY_SHEET):
        if sh not in wb.sheetnames:
            raise FixtureError(f"sheet {sh!r} not in the fixture")
    notes = []
    ws = wb[PANEL_SHEET]
    last_row = max(r1 for _, r1 in CELL_ROWS.values())
    last_col = max(_col(c) for c in PANELS.values()) + PANEL_WIDTH
    rows = list(ws.iter_rows(min_row=1, max_row=last_row, max_col=last_col, values_only=True))
    # headers: every panel carries the same column names
    names = None
    for p, c in PANELS.items():
        hdr = [str(v).strip() if v is not None else "" for v in rows[HEADER_ROW - 1][_col(c):_col(c) + PANEL_WIDTH]]
        if names is None:
            names = hdr
        elif hdr != names:
            raise FixtureError(f"panel {p} has different column headers")
    history = [int(y) for y in cfg_raw["cycle"]["history"]]
    if names[:len(history)] != [str(y) for y in history]:
        raise FixtureError(f"the first panel columns {names[:len(history)]} are not cycle.history {history}")
    nh = len(history)
    scen_names = names[nh:]

    # cells
    cells, pan = [], {p: [] for p in PANELS}
    for res, (r0, r1) in CELL_ROWS.items():
        for r in range(r0, r1 + 1):
            lab = rows[r - 1][0]
            if not isinstance(lab, str) or not lab.strip() or lab.strip().startswith("#"):
                raise FixtureError(f"panel row {r} has no cell label")
            lo, g = parse_label(lab.strip(), cfg_raw)
            cells.append({"cell_id": f"{res}|{lab.strip()}", "residency": res, "score_lo": lo, "gpa_class": g})
            for p, c in PANELS.items():
                pan[p].append([rows[r - 1][_col(c) + j] for j in range(PANEL_WIDTH)])
    n = len(cells)
    if len({c["cell_id"] for c in cells}) != n:
        raise FixtureError("duplicate cell labels within a residency")
    raw = {p: pan[p] for p in PANELS}

    # tuition per column: award $ / award %
    tuition = []
    for j in range(PANEL_WIDTH):
        ratios = [_num(raw["award"][i][j]) / _num(raw["pct"][i][j]) for i in range(n)
                  if _num(raw["award"][i][j]) and _num(raw["pct"][i][j])]
        if not ratios:
            tuition.append(None)
            continue
        med = float(np.median(ratios))
        spread = max(abs(x - med) for x in ratios)
        if spread > 1.0:
            notes.append(f"tuition in column {names[j]!r}: award $ / award % varies by up to ${spread:,.2f}")
        tuition.append(round(med, 2))
    tbc = {}
    for j, y in enumerate(history):
        if tuition[j] is None:
            raise FixtureError(f"no tuition recoverable for cohort {y}")
        tbc[y] = tuition[j]

    # history long table
    long_rows, unrec, unknown, nonint = [], [], [], 0
    for i, c in enumerate(cells):
        for j, y in enumerate(history):
            rate, adm = _num(raw["rate"][i][j]), _z(raw["admits"][i][j])
            if rate and rate > 0:
                apps = adm / rate
                if abs(apps - round(apps)) <= 1e-6:
                    apps = float(round(apps))
                else:
                    nonint += 1
            else:
                if adm > 0:
                    raise FixtureError(f"{c['cell_id']} {y}: admits with no admit rate")
                apps = 0.0
                unknown.append((c["cell_id"], y))
                if rate == 0:
                    unrec.append(f"{c['cell_id']} {y}")
            long_rows.append({"cell_id": c["cell_id"], "residency": c["residency"], "segment": "",
                              "score_lo": c["score_lo"], "gpa_class": c["gpa_class"], "cohort": y, "apps": apps,
                              "admits": adm, "award_usd": _z(raw["award"][i][j]), "enrolled": _z(raw["enrolled"][i][j])})
    if nonint:
        notes.append(f"{nonint} cell-cohorts: admits / admit rate is not within 1e-6 of a whole number; kept as is")
    df = pd.DataFrame(long_rows, columns=COLUMNS)

    # summary sheet: blocks by header
    ws1 = wb[SUMMARY_SHEET]
    max_c = SUMMARY_BLOCK_WIDTH * (nh + len(scen_names)) + SUMMARY_BLOCK_WIDTH
    srows = list(ws1.iter_rows(min_row=1, max_row=SUMMARY_SCAN_ROWS[1], max_col=max_c, values_only=True))
    blocks = {}
    for c0 in range(0, max_c, SUMMARY_BLOCK_WIDTH):
        h = srows[SUMMARY_HEADER_ROW - 1][c0] if c0 < len(srows[SUMMARY_HEADER_ROW - 1]) else None
        if not isinstance(h, str):
            continue
        for nm in scen_names:
            if nm and re.search(r"\b" + re.escape(nm) + r"\b", h, re.I):
                blocks.setdefault(nm, c0)
    scen = []
    for k, nm in enumerate(scen_names):
        j = nh + k
        active = any(_z(raw["admits"][i][j]) > 0 for i in range(n))
        if not nm or not active:
            continue
        sd = {"name": nm, "column": j, "tuition": tuition[j],
              "admit_rate": np.array([_z(raw["rate"][i][j]) for i in range(n)]),
              "award_usd": np.array([_z(raw["award"][i][j]) for i in range(n)]),
              "yield": np.array([_z(raw["yield"][i][j]) for i in range(n)]),
              "admits": np.array([_z(raw["admits"][i][j]) for i in range(n)]),
              "enrolled": np.array([_z(raw["enrolled"][i][j]) for i in range(n)]),
              "yield_blank_with_admits": int(sum(1 for i in range(n) if _num(raw["yield"][i][j]) is None
                                                 and _z(raw["admits"][i][j]) > 0))}
        sd["summary"] = _summary_block(srows, blocks.get(nm), nm, cfg_raw) if nm in blocks else None
        scen.append(sd)
    if not scen:
        raise FixtureError("no scenario columns with admits")
    rule = detect_counting_rule([s["summary"] for s in scen if s["summary"]])
    if unknown:
        notes.append(f"applications unknown (admit rate 0 or blank): {len(unknown)} cell-cohorts ({len(unrec)} with "
                     f"rate 0); History shows them blank, the ledger reads 0")
    return {"path": path, "cells": df, "cohorts": history, "tuition_by_cohort": tbc, "scenarios": scen,
            "counting_rule": rule, "notes": notes, "unrecoverable_apps": unrec, "apps_unknown": unknown, "n_cells": n,
            "cell_ids": [c["cell_id"] for c in cells]}


def _summary_block(srows, c0, name, cfg_raw):
    """Description, money rows, count groups and narrative of one summary-sheet block."""
    lab = lambda r: srows[r - 1][c0] if c0 < len(srows[r - 1]) else None  # noqa: E731
    val = lambda r, off=1: srows[r - 1][c0 + off] if c0 + off < len(srows[r - 1]) else None  # noqa: E731
    desc = lab(SUMMARY_DESCRIPTION_ROW)
    desc = re.sub(r"^\s*[A-Za-z]+:\s*", "", desc) if isinstance(desc, str) else ""
    out = {"description": desc, "money": {}, "groups": {}, "narrative": None, "rows": {}}
    keys = [("gross", "gross"), ("merit", "merit"), ("need", "need"), ("specialty", "specialty"),
            ("ntr", "net tuition")]
    r = SUMMARY_SCAN_ROWS[0]
    while r <= SUMMARY_SCAN_ROWS[1]:
        lb = lab(r)
        s = lb.strip().lower() if isinstance(lb, str) else ""
        for key, needle in keys:
            if needle in s and key not in out["money"] and _num(val(r)) is not None:
                out["money"][key] = _num(val(r))
                out["rows"][key] = r
        m = re.fullmatch(r">=\s*([\d.]+)", s)
        if m:
            t = float(m.group(1))
            grp = {"at": _num(val(r)), "row": r, "others": {}}
            q = r + 1
            while q <= SUMMARY_SCAN_ROWS[1]:
                l2 = lab(q)
                s2 = l2.strip().lower() if isinstance(l2, str) else ""
                if not s2:
                    break
                if "total" in s2:
                    grp["total"] = _num(val(q))
                    break
                if re.fullmatch(r"<\s*[\d.]+", s2):
                    grp["below"] = _num(val(q))
                else:
                    grp["others"][s2] = _z(val(q))
                q += 1
            if t not in out["groups"] and grp.get("total") is not None and grp.get("below") is not None:
                out["groups"][t] = grp
            r = q
        r += 1
    nar = lab(SUMMARY_NARRATIVE_ROW)
    out["narrative"] = nar if isinstance(nar, str) and nar.strip() else None
    out["parsed"] = parse_narrative(out["narrative"], cfg_raw) if out["narrative"] else {}
    out["class"] = None
    for g in out["groups"].values():
        out["class"] = g["total"]
        break
    return out


def parse_narrative(text, cfg_raw):
    """Figures stated in a scenario's narrative: class, the score and GPA medians with their margins, the count below
    a score, full-tuition and no-merit-award (full-pay) counts. Missing figures are left out."""
    out = {}
    m = re.search(r"[Cc]lass\D{0,20}?(\d+)", text)
    if m:
        out["class"] = float(m.group(1))
    for t, mg in re.findall(r"(\d+(?:\.\d+)?)\s*\(\s*(-?\d+)\s*-?\s*person", text):
        t = float(t)
        key = "median_gpa" if t < 10 else "median_score"
        out.setdefault(key, (t, float(mg)))
    m = re.search(r"(\d+)\s+enrolled\s*<\s*(\d+)", text)
    if m:
        out["below"] = (float(m.group(2)), float(m.group(1)))
    m = re.search(r"full-tuition[^0-9]*(\d+)", text)
    if m:
        out["full_tuition"] = float(m.group(1))
    m = re.search(r"full-pay[^0-9]*(\d+)", text)
    if m:
        out["no_merit_award"] = float(m.group(1))
    return out


def detect_counting_rule(summaries):
    """The fixture's rule for unscored (and blank-GPA) enrollees in the median margins, from its count rows: in each
    group 'at or above t', 'below t', the other rows (unscored or blank) and the total. 'excluded' when at + below +
    others = total with others > 0 (the others sit in neither term); 'below' when at + below = total with others > 0
    (the others are inside 'below'). Groups with no others say nothing. Returns a dict with the rule (excluded, below,
    mixed or undetermined) and the evidence."""
    ev = []
    for s in summaries:
        for t, g in s["groups"].items():
            oth = sum(g["others"].values())
            if oth <= 0:
                continue
            if abs(g["at"] + g["below"] + oth - g["total"]) < 0.5:
                ev.append(("excluded", t))
            elif abs(g["at"] + g["below"] - g["total"]) < 0.5:
                ev.append(("below", t))
            else:
                ev.append(("inconsistent", t))
    kinds = {k for k, _ in ev}
    rule = "undetermined" if not kinds else (kinds.pop() if len(kinds) == 1 else "mixed")
    return {"rule": rule, "groups_with_unscored_or_blank": len(ev),
            "by_kind": {k: sum(1 for x, _ in ev if x == k) for k in ("excluded", "below", "inconsistent")}}


# ---------------------------------------------------------------------------------------------------------------
# Config and scenarios

def reproduce_config(cfg_raw, fx):
    """The client config with the fixture's tuition (loaded values, in memory only) and the reproduce settings."""
    raw = copy.deepcopy(cfg_raw)
    rp = raw.get("reproduce") or {}
    for key in ("tuition_increase_pct", "unscored_in_median"):
        if rp.get(key) is None:
            raise ConfigError(f"config reproduce.{key} is required for reproduce mode")
    base = int(raw["cycle"]["base_cycle"])
    plan = int(raw["cycle"]["plan_cycle"])
    raw["tuition_by_cohort"] = dict(fx["tuition_by_cohort"])
    raw["tuition_base"] = fx["tuition_by_cohort"][base]
    raw["tuition_increase_by_year"] = {plan: float(rp["tuition_increase_pct"])}
    if plan - base != 1:
        raise ConfigError("reproduce mode supports one plan year after base_cycle")
    raw["unscored_in_median"] = rp["unscored_in_median"]
    raw["integer_admits"] = True
    raw["integer_enrolled"] = True
    raw["mode"] = "reproduce"
    return validate(raw)


def _need_total(cfg, sd):
    """need_total for a scenario: config need.total less any departure of the fixture's need row from its own rule
    (need rate rounded to whole dollars x class). Returns (value, note)."""
    total = float(cfg["need"]["total"])
    sm = sd.get("summary")
    if not sm or sm["money"].get("need") is None or not sm.get("class"):
        return total, "need_total: config need.total (no need row)"
    whole = float(L.xround(total / float(cfg["need"]["reference_class"])))
    cut = whole * sm["class"] - sm["money"]["need"]
    if abs(cut - round(cut)) > 0.5:
        return total, f"need_total: config need.total (need row departs from the rule by a fraction: {cut:.2f})"
    if round(cut) == 0:
        return total, "need_total: config need.total (need row follows the rule)"
    return total - round(cut), f"need_total: config need.total less {round(cut):,.0f} (need row below the rule)"


def _pool(desc, cfg):
    """Pool multiplier stated in a description ('+P% <pool_threshold>+'), or None."""
    t = int(cfg["score"]["pool_threshold"])
    for pct, thr in re.findall(r"([+-]?\d+(?:\.\d+)?)\s*%\s*(\d+)\s*\+", desc or ""):
        if int(thr) == t:
            return 1.0 + float(pct) / 100.0
    return None


def loaded_specs(fx, cfg):
    """Ordered scenario specs (Baseline first) with parent, pool, money inputs and loaded columns."""
    specs = []
    names = [s["name"] for s in fx["scenarios"]]
    for k, sd in enumerate(fx["scenarios"]):
        desc = (sd["summary"] or {}).get("description", "")
        src = []
        parent = None
        if k > 0:
            for m in re.finditer(r"\b(Baseline|Scenario\s+\d+)\b", desc, re.I):
                cand = [x for x in names[:k] if x.lower() == re.sub(r"\s+", " ", m.group(1)).lower()]
                if cand:
                    parent = cand[0]
                    break
            if parent is None:
                parent = names[k - 1]
                src.append("parent: previous scenario (description names none)")
            else:
                src.append(f"parent: {parent} (description)")
        pool = _pool(desc, cfg)
        if pool is None:
            pool = 1.0 if parent is None else next(s["pool_multiplier"] for s in specs if s["name"] == parent)
            src.append("pool: " + ("1 (no pool change stated)" if parent is None else f"inherited from {parent}"))
        else:
            src.append(f"pool: {pool:g} (description)")
        need, nnote = _need_total(cfg, sd)
        src.append(nnote)
        spec_money = (sd["summary"] or {}).get("money", {})
        specs.append({"name": sd["name"], "parent": parent, "description": desc, "pool_multiplier": pool,
                      "specialty_usd": float(spec_money.get("specialty") or 0.0), "need_total": need,
                      "tuition": float(sd["tuition"]), "admit_rate": sd["admit_rate"], "award_usd": sd["award_usd"],
                      "yield": sd["yield"], "sources": src})
    return specs


def _admits_hat(c, rate, m, rnd):
    """Integer admits from c base applications at pool multiplier m and admit rate (the reproduce ledger's rule)."""
    a = c * m
    if rnd:
        a = float(L.xround(a))
    return float(L.xround(a * rate))


def recover_apps(cells, cfg, fx, specs):
    """Unknown applications (DECISIONS Nov 18). Marks unknown cell-cohorts in cells.meta["apps_unknown"]; for a cell
    whose base-cycle applications are unknown and that some scenario admits students to, recovers them from the
    scenario columns when exactly one whole number fits every scenario (cells.apps is set and
    cells.meta["apps_recovered"] marks it); otherwise lists the cell in cells.meta["not_reproducible"] with the reason.
    The fixture has no segment, so no segment lift enters. Returns the meta dict."""
    j = cells.col(cfg["cycle"]["base_cycle"])
    t = len(cells.cohorts)
    pos = {c: i for i, c in enumerate(cells.cell_id)}
    unknown = np.zeros((cells.n, t), dtype=bool)
    for cid, y in fx.get("apps_unknown", []):
        unknown[pos[cid], cells.col(int(y))] = True
    recovered = np.zeros((cells.n, t), dtype=bool)
    not_rep = []
    upper = response.score_group_upper(cells, cfg)
    rnd = round_apps_after_pool(cfg)
    by = {sd["name"]: sd for sd in fx["scenarios"]}
    for i in np.flatnonzero(unknown[:, j]):
        pairs = [(sp, by[sp["name"]]) for sp in specs]
        if not any(sd["admits"][i] > 0 for _, sd in pairs):
            continue                                   # no scenario admits anyone here: nothing depends on it
        ms = [(float(sp["pool_multiplier"]) if upper[i] else 1.0) for sp, _ in pairs]
        hi = max(((sd["admits"][i] + 1.0) / (sp["admit_rate"][i] * m) for (sp, sd), m in zip(pairs, ms)
                  if sp["admit_rate"][i] > 0), default=0.0)
        cands = [c for c in range(0, int(math.ceil(hi)) + 3)
                 if all(_admits_hat(c, sp["admit_rate"][i], m, rnd) == sd["admits"][i]
                        for (sp, sd), m in zip(pairs, ms))]
        if len(cands) == 1:
            cells.apps[i, j] = float(cands[0])
            unknown[i, j] = False
            recovered[i, j] = True
        else:
            why = ("the scenarios imply different applications" if not cands else
                   f"the scenario columns fit {len(cands)} values, not one")
            not_rep.append({"cell": cells.cell_id[i], "reason": f"{NOT_REPRODUCIBLE}: base-cycle applications "
                                                                 f"unknown and {why}"})
    cells.meta.update({"apps_unknown": unknown, "apps_recovered": recovered, "not_reproducible": not_rep})
    return cells.meta


def scenarios_from_specs(cells, cfg, specs):
    """Scenario objects from loaded specs (Baseline first). Baseline's need_total must equal need.total (Levers
    reads it from Inputs). Returns (scenarios, loaded)."""
    j = cells.col(cfg["cycle"]["base_cycle"])
    hist_award = cells.award[:, j]
    out, loaded, by = [], {}, {}
    for sp in specs:
        T = float(sp["tuition"])
        flag = np.asarray(sp["award_usd"], float) >= T - 0.5
        if sp["parent"] is None:
            if abs(sp["need_total"] - float(cfg["need"]["total"])) > 1e-9:
                raise ConfigError("reproduce: Baseline need_total must equal config need.total")
            s = L.baseline(cells, cfg, name=sp["name"])
            s.description = sp["description"]
            s.admit_rate = np.asarray(sp["admit_rate"], float).copy()
            s.full_tuition = flag.copy()
            # flagged cells keep the inherited award (the base-cycle award), so no entry is ignored under the flag
            s.award_usd = np.where(flag, hist_award, np.asarray(sp["award_usd"], float))
            s.pool_multiplier = float(sp["pool_multiplier"])
            s.specialty_usd = float(sp["specialty_usd"])
            s.yield_loaded = np.asarray(sp["yield"], float).copy()
            s.tuition_loaded_usd = T
            s.notices = []
            L._validate_scenario(cells, cfg, s)
        else:
            p = by[sp["parent"]]
            ids = cells.cell_id
            rate = np.asarray(sp["admit_rate"], float)
            aw = np.asarray(sp["award_usd"], float)
            ov_rate = {ids[i]: rate[i] for i in range(cells.n) if rate[i] != p.admit_rate[i]}
            ov_flag = {ids[i]: bool(flag[i]) for i in range(cells.n) if bool(flag[i]) != bool(p.full_tuition[i])}
            ov_award = {ids[i]: aw[i] for i in range(cells.n) if not flag[i] and aw[i] != p.award_usd[i]}
            s = L.derive(p, sp["name"], cfg, cells, admit_rate=ov_rate, award=ov_award, full_tuition=ov_flag,
                         description=sp["description"], pool_multiplier=float(sp["pool_multiplier"]),
                         specialty_usd=float(sp["specialty_usd"]), need_total=float(sp["need_total"]),
                         yield_loaded=np.asarray(sp["yield"], float).copy(), tuition_loaded_usd=T)
        out.append(s)
        by[s.name] = s
        loaded[s.name] = {"admit_rate": np.asarray(sp["admit_rate"], float).copy(),
                          "award_usd": np.asarray(sp["award_usd"], float).copy(),
                          "yield": np.asarray(sp["yield"], float).copy(), "tuition": T,
                          "pool_multiplier": float(sp["pool_multiplier"]), "specialty_usd": float(sp["specialty_usd"]),
                          "need_total": float(sp["need_total"]), "sources": list(sp.get("sources", []))}
    return out, loaded


# ---------------------------------------------------------------------------------------------------------------
# Building

def _hashes(cfg, cells, loaded):
    from . import build
    cfg_b = yaml.safe_dump({k: v for k, v in cfg.items() if not k.startswith("_")}, sort_keys=True).encode()
    buf = io.StringIO()
    cells.to_long().to_csv(buf, index=False, float_format="%.10g")
    scen_b = json.dumps({k: {kk: (vv.tolist() if isinstance(vv, np.ndarray) else vv) for kk, vv in v.items()}
                         for k, v in loaded.items()}, sort_keys=True).encode()
    return build.hashes_from_bytes(cfg_b, buf.getvalue().encode(), scen_b)


def build_workbook(cfg, cells, scenarios, loaded, out_root, meta=None, sentinel=False, name=None,
                   pdf=False, profile=None):
    """Build a reproduce-mode workbook from loaded values (fixture or synthetic). Returns (path, info). The file is
    workbook_reproduce.xlsx, or workbook_reproduce_sentinel.xlsx for a sentinel copy, so the two builds of one build id
    sit side by side."""
    from . import build, workbook
    name = name or ("workbook_reproduce_sentinel.xlsx" if sentinel else "workbook_reproduce.xlsx")
    meta = dict(meta or {})
    meta.update(_hashes(cfg, cells, loaded))
    meta["baseline_segment_named"] = False
    meta["git_commit"] = build.git_commit()
    meta["uncommitted_files"] = build.uncommitted_files()
    meta["cached_values"] = "sentinel" if sentinel else "python"
    run = build.make_run(cfg, cells, scenarios, meta, loaded=loaded)
    out_dir = os.path.join(out_root, cfg["client"]["id"], str(cfg["cycle"]["plan_cycle"]), meta["build_id"])
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name)
    info = workbook.write(run, path, sentinel=sentinel)
    if pdf:
        from . import lo
        info["pdf"] = lo.render_summary_pdf(path, out_dir, profile=profile)
    return path, info


def synthetic_loaded(cfg_live, cells, scenarios, decimals=3):
    """Loaded values for a synthetic reproduce build (test 3, integer branches): each scenario's Middle live yield
    rounded to `decimals`, and a loaded tuition one rounding step above the formula's, so the Ledgers' use of the
    loaded tuition is visible. Returns (cfg, scenarios, loaded) in reproduce mode with integer admits and enrolled and
    applications rounded after the pool multiplier."""
    from . import response
    base = response.base_yield(cells, cfg_live)
    raw = {k: v for k, v in cfg_live.items() if not k.startswith("_")}
    raw = copy.deepcopy(raw)
    raw.update({"mode": "reproduce", "integer_admits": True, "integer_enrolled": True,
                "reproduce": {"round_apps_after_pool": True}})
    cfg = validate(raw)
    out, loaded = [], {}
    for s in scenarios:
        lc = L.evaluate(cells, cfg_live, s, base, "middle")
        y = np.round(lc.yld, decimals)
        T = scenario_tuition(cfg_live, s.tuition_increase_pct) + float(cfg_live["tuition_rounding_usd"])
        c = copy.copy(s)
        c.yield_loaded, c.tuition_loaded_usd = y, T
        out.append(c)
        award = L.evaluate(cells, cfg, c, base, "middle").award
        loaded[s.name] = {"admit_rate": s.admit_rate.copy(), "award_usd": award, "yield": y, "tuition": T,
                          "pool_multiplier": float(s.pool_multiplier), "specialty_usd": float(s.specialty_usd),
                          "need_total": float(cfg["need"]["total"] if s.need_total is None else s.need_total),
                          "sources": ["synthetic: Middle live yield rounded to %d decimals" % decimals]}
    return cfg, out, loaded


def synthetic_509(cells, cfg):
    """Synthetic 509 figures for the synthetic reproduce build (test 3 covers the History 509 block's formulas): the
    first cohort agrees on the counts, the second differs by one on the class and gives a score median just below the
    top band, the third gives none. Computed from the generated cells; not client figures."""
    e0, e1 = cells.enrolled[:, 0], cells.enrolled[:, 1]
    c = list(cells.cohorts)
    return {c[0]: {"first_year_class": float(e0.sum()), "without_score": float(e0[np.isnan(cells.score_lo)].sum()),
                   "without_gpa": float(e0[cells.gpa_class == "blank"].sum())},
            c[1]: {"first_year_class": float(e1.sum()) + 1, "score_p50": float(max(cfg["score"]["bands"])) - 0.5}}


def synthetic_inputs(seed=101, cfg_path=None, scenarios_path=None):
    """Inputs of the synthetic reproduce build (test 3, integer branches; tests/compare_excel_saved.py rebuilds it):
    the scenarios of config/scenarios_synthetic.yaml on world `seed` with synthetic_loaded values and synthetic_509
    figures. Returns (cfg_live, cfg, cells, scenarios, loaded)."""
    from . import build, synth_cells
    from .config import load
    cfg_live = load(cfg_path or os.path.join(ROOT, "config", "synthetic.yaml"))
    cells = synth_cells.generate(cfg_live, seed)
    with open(scenarios_path or os.path.join(ROOT, "config", "scenarios_synthetic.yaml")) as f:
        specs = yaml.safe_load(f)["scenarios"]
    scen = build.scenarios_from_specs(specs, cells, cfg_live)
    cfg, scen_r, loaded = synthetic_loaded(cfg_live, cells, scen)
    raw = {k: v for k, v in cfg.items() if not k.startswith("_")}
    cfg = validate(raw | {"aba_509_by_cohort": synthetic_509(cells, cfg)})
    return cfg_live, cfg, cells, scen_r, loaded


def build_synthetic(out_root, seed=101, sentinel=False, name=None):
    """Build the synthetic reproduce workbook (no fixture). Returns (path, info)."""
    cfg_live, cfg, cells, scen, loaded = synthetic_inputs(seed)
    return build_workbook(cfg, cells, scen, loaded, out_root, {"data_source": f"synthetic (seed {seed})",
                                                               "config_path": "config/synthetic.yaml",
                                                               "scenarios_path": "config/scenarios_synthetic.yaml",
                                                               "reproduce_source": "synthetic loaded values"},
                          sentinel=sentinel, name=name)


def from_fixture(path, cfg_path=None):
    """Load the fixture and return (cfg, cells, scenarios, loaded, fx)."""
    cfg_path = cfg_path or os.path.join(ROOT, "config", "richmond.yaml")
    with open(cfg_path) as f:
        cfg_raw = yaml.safe_load(f)
    fx = load_fixture(path, cfg_raw)
    cfg = reproduce_config(cfg_raw, fx)
    cells = from_long(fx["cells"], cfg)
    # the scenario columns are in fixture row order; reorder them to the standard cell order
    pos = [fx["cell_ids"].index(c) for c in cells.cell_id]
    for sd in fx["scenarios"]:
        for key in ("admit_rate", "award_usd", "yield", "admits", "enrolled"):
            sd[key] = sd[key][pos]
    specs = loaded_specs(fx, cfg)
    recover_apps(cells, cfg, fx, specs)
    scenarios, loaded = scenarios_from_specs(cells, cfg, specs)
    return cfg, cells, scenarios, loaded, fx


# ---------------------------------------------------------------------------------------------------------------
# Comparison (spec section 9 pass criteria)

def file_figures(fx, sd, cfg):
    """The fixture's own figures for one scenario. Summary-sheet rows and the narrative where the block has them;
    otherwise figures derivable from the panels (class, merit, counts, full-tuition and no-merit counts). Returns
    {criterion: (value, source)}; criteria the file does not give are absent."""
    out = {}
    sm = sd.get("summary")
    E, A = sd["enrolled"], sd["award_usd"]
    sc = np.asarray(fx["_score_lo"], float)
    gp = np.asarray(fx["_gpa"], object)
    T = sd["tuition"]
    scored = ~np.isnan(sc)
    if sm and sm.get("class") is not None:
        out["class"] = (sm["class"], "summary sheet: total class")
        if sm["money"].get("merit") is not None:
            out["merit"] = (sm["money"]["merit"], "summary sheet: merit row")
        if sm["money"].get("ntr") is not None:
            out["ntr"] = (sm["money"]["ntr"], "summary sheet: net tuition row")
        for t, g in sm["groups"].items():
            if t > 10:
                out[("at_or_above_score", t)] = (g["at"], "summary sheet: count row")
                if t == float(cfg["score"]["floor"]):
                    out["below_floor"] = (g["below"], "summary sheet: count row")
            elif abs(t - float(cfg["gpa"]["hi_at_or_above"])) < 1e-9:
                out["gpa_hi"] = (g["at"], "summary sheet: count row")
        pz = sm.get("parsed", {})
        if "full_tuition" in pz:
            out["full_tuition"] = (pz["full_tuition"], "narrative")
        if "no_merit_award" in pz:
            out["no_merit_award"] = (pz["no_merit_award"], "narrative")
        if "median_score" in pz:
            out["margin_score"] = (pz["median_score"][1], f"narrative (median {pz['median_score'][0]:g})")
            out["_median_score_t"] = pz["median_score"][0]
        if "median_gpa" in pz:
            out["margin_gpa"] = (pz["median_gpa"][1], "narrative")
        if "below" in pz and pz["below"][0] == float(cfg["score"]["floor"]):
            out["below_floor_narrative"] = (pz["below"][1], "narrative")
        if "class" in pz:
            out["class_narrative"] = (pz["class"], "narrative")
    else:
        out["class"] = (float(E.sum()), "panels: sum of enrolled")
        out["merit"] = (float((E * A).sum()), "panels: enrolled x award")
        for t in L.score_thresholds(cfg):
            out[("at_or_above_score", t)] = (float(E[scored & (sc >= t)].sum()), "panels")
        out["below_floor"] = (float(E[scored & (sc < float(cfg["score"]["floor"]))].sum()), "panels")
        out["gpa_hi"] = (float(E[gp == "hi"].sum()), "panels")
        out["full_tuition"] = (float(E[A >= T - 0.5].sum()), "panels: award at or above tuition")
        out["no_merit_award"] = (float(E[A <= 0].sum()), "panels: award of zero")
    return out


def our_figures(run, name, t_score=None):
    """The reproduce ledger's figures for one scenario (Middle case; reproduce yields are the same in every case)."""
    from . import risk
    lc = run.lcs[name]["middle"]
    kp, mo = L.kpis(lc), L.money(lc)
    cfg = run.cfg
    out = {"class": kp["class_n"], "merit": mo["merit"], "ntr": mo["ntr_y1"], "below_floor": kp["enrolled_below_floor"],
           "gpa_hi": kp["enrolled_gpa_hi"], "full_tuition": kp["full_tuition_n"],
           "no_merit_award": kp["no_merit_award_n"]}
    for t, v in kp["enrolled_at_or_above"].items():
        out[("at_or_above_score", float(t))] = v
    t = t_score if t_score is not None else cfg["score"]["median_thresholds"][0]
    out["margin_score"] = risk.median(lc, "score", t)["margin_t"]
    out["margin_gpa"] = risk.median(lc, "gpa", float(cfg["gpa"]["median_threshold"]))["margin_t"]
    return out


def _alt_margins(lc, t, excl=()):
    """Margins on the ledger's enrolled counts under each counting rule, cells `excl` left out (diagnostic)."""
    e = np.asarray(lc.enrolled, float).copy()
    e[np.asarray(excl, dtype=int)] = 0.0
    sc = lc.cells.score_lo
    scored = ~np.isnan(sc)
    at = float(e[scored & (sc >= t)].sum())
    bel_scored = float(e[scored & (sc < t)].sum())
    uns = float(e[~scored].sum())
    g = lc.cells.gpa_class
    hi, lo_, bl = float(e[g == "hi"].sum()), float(e[g == "lo"].sum()), float(e[g == "blank"].sum())
    return {"score": {"excluded": at - bel_scored, "below": at - bel_scored - uns},
            "gpa": {"excluded": hi - lo_, "below": hi - lo_ - bl}}


def _excluded(cells):
    """Indices of cells not reproducible from the file (excluded from the pass criteria)."""
    ids = {d["cell"] for d in cells.meta.get("not_reproducible", [])}
    return np.array([i for i in range(cells.n) if cells.cell_id[i] in ids], dtype=int)


def _contrib(cells, cfg, idx, E, A, T, need_per, t_score):
    """What cells `idx` add to each criterion, given their enrolled E and awards A (arrays over all cells), tuition T
    and need per enrollee. Used to take non-reproducible cells out of the file's and the ledger's figures alike."""
    from . import risk
    out = {}
    if len(idx) == 0:
        return out
    e, a = np.asarray(E, float)[idx], np.asarray(A, float)[idx]
    sc = cells.score_lo[idx]
    scored = ~np.isnan(sc)
    gc = cells.gpa_class[idx]
    out["class"] = float(e.sum())
    out["merit"] = float((e * a).sum())
    out["ntr"] = float((e * (T - a - need_per)).sum())
    for t in L.score_thresholds(cfg):
        out[("at_or_above_score", float(t))] = float(e[scored & (sc >= t)].sum()) if scored.any() else 0.0
    fl = float(cfg["score"]["floor"])
    out["below_floor"] = float(e[scored & (sc < fl)].sum()) if scored.any() else 0.0
    out["gpa_hi"] = float(e[gc == "hi"].sum())
    out["full_tuition"] = float(e[a >= T - 0.5].sum())
    out["no_merit_award"] = float(e[a <= 1e-9].sum())
    out["margin_score"] = float((risk.median_signs(cells, cfg, "score", t_score)[idx] * e).sum())
    out["margin_gpa"] = float((risk.median_signs(cells, cfg, "gpa", float(cfg["gpa"]["median_threshold"]))[idx]
                               * e).sum())
    out["class_narrative"] = out["class"]
    out["below_floor_narrative"] = out["below_floor"]
    return out


def cell_causes(run, fx, name):
    """Cells whose ledger admits or enrolled differ from the fixture's, each with its likeliest cause."""
    cells, cfg = run.cells, run.cfg
    lc = run.lcs[name]["middle"]
    sd = next(s for s in fx["scenarios"] if s["name"] == name)
    sc = run.scen(name)
    j = cells.col(cfg["cycle"]["base_cycle"])
    apps = cells.apps[:, j]
    m = np.where(lc.upper, sc.pool_multiplier, 1.0) * (1.0 + sc.segment_pool_lift_pct / 100.0 * lc.in_segment)
    rnd = round_apps_after_pool(cfg)
    other = L.xround((apps * m if rnd else L.xround(apps * m)) * sc.admit_rate)   # the other application rule
    nonrep = {d["cell"]: d["reason"] for d in cells.meta.get("not_reproducible", [])}
    unknown = cells.meta.get("apps_unknown")
    out = []
    for i in np.flatnonzero((lc.admits != sd["admits"]) | (lc.enrolled != sd["enrolled"])):
        if cells.cell_id[i] in nonrep:
            cause = nonrep[cells.cell_id[i]]
        elif lc.admits[i] != sd["admits"][i]:
            if unknown is not None and unknown[i, j] and sd["admits"][i] > 0:
                cause = "applications unknown (base-cycle admit rate 0 or blank)"
            elif other[i] == sd["admits"][i]:
                cause = (f"the file's admits follow round_apps_after_pool {'false' if rnd else 'true'} here "
                         f"(setting: {'true' if rnd else 'false'})")
            else:
                cause = "unexplained admits difference"
        else:
            cause = "enrolled rounding with equal admits" if lc.enrolled[i] != sd["enrolled"][i] else ""
        out.append({"cell": cells.cell_id[i], "admits": float(lc.admits[i]), "fixture_admits": float(sd["admits"][i]),
                    "enrolled": float(lc.enrolled[i]), "fixture_enrolled": float(sd["enrolled"][i]), "cause": cause})
    return out


def compare(run, fx):
    """Pass criteria (spec section 9) for every loaded scenario. Cells not reproducible from the file are taken out
    of both sides (their panel values from the file's figures, their ledger values from ours). Returns a list of rows:
    scenario, criterion, ours, file, source, pass, cause, excluded_cells."""
    cfg, cells = run.cfg, run.cells
    fx["_score_lo"] = list(cells.score_lo)
    fx["_gpa"] = list(cells.gpa_class)
    excl = _excluded(cells)
    whole_need = float(L.xround(float(cfg["need"]["total"]) / float(cfg["need"]["reference_class"])))
    rows = []
    for sd in fx["scenarios"]:
        name = sd["name"]
        lc = run.lcs[name]["middle"]
        ff = file_figures(fx, sd, cfg)
        t_med = ff.get("_median_score_t")
        t_use = t_med or cfg["score"]["median_thresholds"][0]
        ours = our_figures(run, name, t_med)
        # the file's need is its whole-dollar need rate x class (less any fixed cut), so a cell's enrollees carry
        # the whole-dollar rate
        c_file = _contrib(cells, cfg, excl, sd["enrolled"], sd["award_usd"], sd["tuition"], whole_need, t_use)
        c_ours = _contrib(cells, cfg, excl, lc.enrolled, lc.award, lc.tuition, lc.need_rate, t_use)
        causes = [c for c in cell_causes(run, fx, name) if c["cell"] not in set(cells.cell_id[excl])]
        kinds = sorted({c["cause"] for c in causes if c["cause"]})
        n_adm = sum(1 for c in causes if c["admits"] != c["fixture_admits"])
        cell_note = (f"admits differ in {n_adm} cells (" + "; ".join(kinds) + ")") if n_adm else ""
        alt = _alt_margins(lc, t_use, excl)
        keys = ["class", "merit", "ntr"] + [("at_or_above_score", float(t)) for t in L.score_thresholds(cfg)] + \
            ["below_floor", "gpa_hi", "full_tuition", "no_merit_award", "margin_score", "margin_gpa"]
        for key in keys:
            crit = f"at_or_above_{key[1]:g}" if isinstance(key, tuple) else key
            ov = ours.get(key)
            if ov is not None:
                ov = ov - c_ours.get(key, 0.0)
            if key not in ff:
                rows.append({"scenario": name, "criterion": crit, "ours": ov, "file": None,
                             "source": "not derivable from the file", "pass": None, "cause": "",
                             "excluded_cells": len(excl)})
                continue
            fv, src = ff[key]
            fv = fv - c_file.get(key, 0.0)
            if len(excl) and c_file.get(key, 0.0) != 0.0:
                src += f" less {len(excl)} non-reproducible cells"
            ok = abs(ov - fv) <= 100.0 if key == "ntr" else abs(ov - fv) < 1e-6
            cause = ""
            if not ok:
                parts = []
                if key in ("margin_score", "margin_gpa"):
                    which = "score" if key == "margin_score" else "gpa"
                    other = "excluded" if cfg["unscored_in_median"] == "below" else "below"
                    alt_v = alt[which][other]
                    if abs(alt_v - fv) < 1e-6:
                        parts.append(f"counting rule: the file's margin matches the ledger's counts under "
                                     f"unscored_in_median '{other}' (setting: '{cfg['unscored_in_median']}')")
                    elif abs(alt_v - fv) < abs(ov - fv):
                        parts.append(f"counting rule: '{other}' would narrow the gap to {abs(alt_v - fv):g}")
                if cell_note:
                    parts.append(cell_note)
                if key == "ntr" and not parts:
                    parts.append("need or specialty bookkeeping")
                cause = "; ".join(parts) or "unexplained"
            rows.append({"scenario": name, "criterion": crit, "ours": ov, "file": fv, "source": src, "pass": ok,
                         "cause": cause, "excluded_cells": len(excl)})
        for extra, key in (("class_narrative", "class"), ("below_floor_narrative", "below_floor")):
            if extra in ff and ff[extra][0] != ff.get(key, (None,))[0]:
                fv = ff[extra][0] - c_file.get(extra, 0.0)
                ov = ours[key] - c_ours.get(key, 0.0)
                rows.append({"scenario": name, "criterion": extra, "ours": ov, "file": fv,
                             "source": "narrative differs from the summary rows", "pass": abs(ov - fv) < 1e-6,
                             "cause": "file is internally inconsistent", "excluded_cells": len(excl)})
    return rows


def diagnostics(run, fx):
    """Not used by any criterion: admits matching cell by cell under the ledger's application rule and under the
    other one (round_apps_after_pool flipped), per scenario; and the fixture's own enrolled-rounding consistency."""
    cfg, cells = run.cfg, run.cells
    j = cells.col(cfg["cycle"]["base_cycle"])
    apps = cells.apps[:, j]
    rnd = round_apps_after_pool(cfg)
    out = {}
    for sd in fx["scenarios"]:
        sc = run.scen(sd["name"])
        lc = run.lcs[sd["name"]]["middle"]
        m = np.where(lc.upper, sc.pool_multiplier, 1.0) * (1.0 + sc.segment_pool_lift_pct / 100.0 * lc.in_segment)
        A = L.xround((apps * m if rnd else L.xround(apps * m)) * sc.admit_rate)
        E = L.xround(A * lc.yld)
        out[sd["name"]] = {
            "ledger": {"round_apps_after_pool": rnd, "admits_matching_cells": int((lc.admits == sd["admits"]).sum()),
                       "class": float(lc.enrolled.sum())},
            "other_application_rule": {"round_apps_after_pool": not rnd,
                                       "admits_matching_cells": int((A == sd["admits"]).sum()),
                                       "class": float(E.sum())},
            "fixture_enrolled_equals_round_admits_x_yield": int(
                (L.xround(sd["admits"] * sd["yield"]) == sd["enrolled"]).sum()),
            "cells": cells.n,
        }
    return out


def acceptance_order(names):
    """Scenario 4 first (BM-7, R3-1), then Baseline and the other scenarios in file order."""
    first = [n for n in names if re.fullmatch(r"Scenario\s+4", n, re.I)]
    return first + [n for n in names if n not in first]


def run_fixture(path, out_root, cfg_path=None, sentinel=False, pdf=False, profile=None, write=True):
    """Load, build and compare. Returns a dict: path, info, rows, report."""
    cfg, cells, scenarios, loaded, fx = from_fixture(path, cfg_path)
    meta = {"data_source": f"{os.path.basename(path)} (validation fixture, read at run time)",
            "config_path": os.path.relpath(cfg_path or os.path.join(ROOT, "config", "richmond.yaml"), ROOT),
            "scenarios_path": "loaded from the fixture",
            "reproduce_source": "fixture read from " + ENV}
    if write:
        wpath, info = build_workbook(cfg, cells, scenarios, loaded, out_root, meta, sentinel=sentinel, pdf=pdf,
                                     profile=profile)
        run = info["run"]
    else:
        from . import build
        wpath, info = None, None
        run = build.make_run(cfg, cells, scenarios, dict(meta, build_id="nobuild"), loaded=loaded)
    rows = compare(run, fx)
    report = {
        "workbook": wpath,
        "settings": {"unscored_in_median": cfg["unscored_in_median"], "integer_admits": cfg["integer_admits"],
                     "integer_enrolled": cfg["integer_enrolled"], "round_apps_after_pool": round_apps_after_pool(cfg),
                     "tuition_increase_pct": cfg["tuition_increase_by_year"][cfg["cycle"]["plan_cycle"]]},
        "acceptance_order": acceptance_order([s.name for s in run.scenarios]),
        "not_reproducible": list(cells.meta.get("not_reproducible", [])),
        "not_reproducible_count": len(cells.meta.get("not_reproducible", [])),
        "apps_recovered": [cells.cell_id[i] for i in np.flatnonzero(
            cells.meta.get("apps_recovered", np.zeros((cells.n, 1), bool)).any(axis=1))],
        "apps_unknown_cell_cohorts": int(cells.meta.get("apps_unknown", np.zeros(1, bool)).sum()),
        "counting_rule": fx["counting_rule"],
        "counting_rule_matches_setting": fx["counting_rule"]["rule"] == cfg["unscored_in_median"],
        "loader_notes": fx["notes"],
        "scenarios": [{"name": s.name, "parent": run.parents[s.name].name if run.parents[s.name] else None,
                       "sources": loaded[s.name]["sources"]} for s in run.scenarios],
        "criteria": rows,
        "failures": [r for r in rows if r["pass"] is False],
        "cell_differences": {s.name: cell_causes(run, fx, s.name) for s in run.scenarios},
        "diagnostics": diagnostics(run, fx),
    }
    return {"path": wpath, "info": info, "run": run, "rows": rows, "report": report, "fx": fx, "cfg": cfg}


def write_report(report, out_root):
    d = os.path.join(out_root, "phase3")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "reproduce_report.json")
    with open(p, "w") as f:
        json.dump(report, f, indent=1, default=lambda o: o.tolist() if isinstance(o, np.ndarray) else str(o))
    return p


def main():
    ap = argparse.ArgumentParser(description="Build the reproduce-mode workbook from the validation fixture.")
    ap.add_argument("--out", default=os.path.join(ROOT, "output"))
    ap.add_argument("--config", default=os.path.join(ROOT, "config", "richmond.yaml"))
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--sentinel", action="store_true")
    ap.add_argument("--synthetic", type=int, metavar="SEED",
                    help="build the synthetic reproduce workbook on world SEED instead (no fixture)")
    args = ap.parse_args()
    if args.synthetic is not None:
        p, _ = build_synthetic(args.out, args.synthetic, sentinel=args.sentinel)
        print(p)
        return
    path = os.environ.get(ENV)
    if not path:
        raise SystemExit(f"set {ENV} to the fixture's path")
    res = run_fixture(path, args.out, args.config, sentinel=args.sentinel, pdf=args.pdf)
    rp = write_report(res["report"], args.out)
    print(res["path"])
    print(rp)
    fails = res["report"]["failures"]
    print(f"counting rule in the file: {res['report']['counting_rule']['rule']}; setting: "
          f"{res['report']['settings']['unscored_in_median']}")
    for nm in res["report"]["acceptance_order"]:
        rr = [r for r in res["rows"] if r["scenario"] == nm]
        print(f"{nm}: {sum(1 for r in rr if r['pass'])} pass, {sum(1 for r in rr if r['pass'] is False)} fail, "
              f"{sum(1 for r in rr if r['pass'] is None)} not derivable")
    print(f"criteria: {sum(1 for r in res['rows'] if r['pass'])} pass, {len(fails)} fail, "
          f"{sum(1 for r in res['rows'] if r['pass'] is None)} not derivable; cells not reproducible from the file: "
          f"{res['report']['not_reproducible_count']}")


if __name__ == "__main__":
    main()
