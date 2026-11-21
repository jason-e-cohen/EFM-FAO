"""XlsxWriter generator for the scenario workbook (spec sections 6 to 9, 15 item 11).

Sheets: README, Inputs, History, Response, Levers, Ledger_Low, Ledger_Middle, Ledger_High, Summary, Trim,
Distribution, Checks, RunLog. A reproduce build (cfg mode "reproduce", from sw/reproduce.py) adds the Reproduce sheet (loaded yields, admit
rates, awards, pool settings and tuition) and leaves out Trim, which is live mode only (spec section 6). The Inputs
mode switch (Live, Reproduce) selects, in a reproduce build, the loaded yields and tuition or the response yields and
the tuition formula; a live build has no loaded values and Checks flags the switch if it is set to Reproduce. The
Distribution sheet (Phase 4; both builds) shows the full-tuition and no-merit-award counts, the barbell index, the
top-quartile merit share with its academic-position table, and the step sizes (named range STEP_SIZES).

Every computed cell is a live formula written with its cached value from the Python reference functions (spec
section 6), and the builder records that value as the expected result for test 3. With sentinel=True every cached value
is -999 instead, so a recalculation that leaves any cell untouched shows up (test 3 guard).

Formulas use ROUND, SUM, SUMPRODUCT, INDEX, MATCH, MIN, MAX, IF, SQRT, NORMSDIST, TEXT and &, plus comparison
arithmetic inside SUMPRODUCT; no array IF, no dynamic arrays, no volatile functions, no macros.
"""
import datetime as _dt
import math
import re
import platform
from dataclasses import replace

import numpy as np
import xlsxwriter
from xlsxwriter.utility import quote_sheetname, xl_col_to_name, xl_rowcol_to_cell

from . import CASES
from . import charts as CH
from . import contract as K
from . import dictionary as DD
from . import labels
from . import ledger as L
from . import lo as LO
from . import narrative as NAR
from . import response
from . import risk
from . import trim
from .config import (excel_round0, ntr_target_effective, pct_lattice_n, plan_increase_pct, round_apps_after_pool,
                     round_to, scenario_tuition)

CASE_SHEET = {"low": "Ledger_Low", "middle": "Ledger_Middle", "high": "Ledger_High"}
CASE_TITLE = {"low": "Low", "middle": "Middle", "high": "High"}
SEG_NONE = "(none)"
BIG = "1E+99"
SHEETS = ["README", "Overview", "Charts", "Inputs", "History", "Response", "Levers", "Ledger_Low", "Ledger_Middle",
          "Ledger_High", "Summary", "Trim", "Distribution", "Checks", "RunLog"]          # CP-4: Overview after README
PROBE_A, PROBE_B = 0.35, 0.14        # 0.35 / 0.14 = 2.4999999999999996 in IEEE double (R3-3 rounding probe)
PROBE_EXPR = "0.35/0.14"
REPRO_SHEETS = ["README", "Inputs", "History", "Response", "Levers", "Ledger_Low", "Ledger_Middle", "Ledger_High",
                "Summary", "Distribution", "Checks", "Reproduce", "RunLog"]
MODE_LABEL = {"live": "Live", "reproduce": "Reproduce"}
LABEL_CHARS = 62        # characters per line of a column-A Summary label (46 wide, Arial 9) [R4-02]
SCEN_CHARS = 17.5       # characters per line of a scenario column (14 wide, Arial 9)
POOL_PARTS_TITLE = "Working values: pool strip split at m = 1 (not printed)"        # R4-01
CONTRACT_TITLE = "Interface contract ranges (spec section 15 item 11), every case (not printed)"   # Phase 4.2
LEVER_FIELDS = [  # (field, dictionary id of its plain label, kind): kind num, int01, text, opt (optional number)
    ("description", "IN-091", "text"), ("plan_year", "IN-092", "num"), ("tuition_increase_pct", "IN-093", "num"),
    ("award_scale_with_tuition", "IN-094", "int01"), ("pool_multiplier", "IN-095", "num"),
    ("specialty_usd", "IN-096", "num"), ("need_total", "IN-097", "num"), ("class_target", "IN-098", "num"),
    ("class_cap", "IN-099", "num"), ("bonus_usd", "IN-100", "num"), ("bonus_scope", "IN-101", "text"),
    ("bonus_min_score", "IN-102", "opt"), ("bonus_pool_usd", "IN-103", "opt"), ("segment", "IN-104", "text"),
    ("segment_pool_lift_pct", "IN-105", "num"), ("segment_goal", "IN-106", "opt"), ("yield_shift_pts", "IN-107", "num"),
    ("yield_shift_pts_in", "IN-108", "opt"), ("yield_shift_pts_out", "IN-109", "opt"),
    ("yield_shift_pts_segment", "IN-110", "opt"), ("discount_target", "IN-111", "opt"),
]
BLOCK = ["in_seg", "elig", "apps", "rate", "admits", "award_base", "incentive", "award", "shift", "yield", "evidence",
         "mu", "enrolled", "spend", "w"]
BLOCK_HEAD = {"in_seg": "in segment", "elig": "incentive eligible", "apps": "applications", "rate": "admit rate",
              "admits": "admits", "award_base": "award base", "incentive": "incentive", "award": "award",
              "shift": "yield shift (pts)", "yield": "yield", "evidence": "evidence", "mu": "expected enrolled",
              "enrolled": "enrolled", "spend": "merit $", "w": "net tuition weight"}


def a1(r, c, abs_=True):
    return xl_rowcol_to_cell(r, c, row_abs=abs_, col_abs=abs_)


def ref(sheet, r, c):
    return f"{quote_sheetname(sheet)}!{a1(r, c)}"


def rng(sheet, r0, c0, r1, c1):
    return f"{quote_sheetname(sheet)}!{a1(r0, c0)}:{a1(r1, c1)}"


def xs(t):
    return NAR.xs(t)


def ceil_x(x):
    return f"IF(ROUND({x},0)>={x},ROUND({x},0),ROUND({x},0)+1)"


def lattice_corr_x(q):
    """1/(2n) for q = m/n in lowest terms, as an Excel formula over the q cell [v0.6.3, BM-1]: n is the smallest
    divisor k of 100 with q x k whole (q has at most two decimals), found with nested IF and ROUND."""
    f = "100"
    for k in (50, 25, 20, 10, 5, 4, 2, 1):
        f = f"IF(ROUND({q}*{k},9)=ROUND({q}*{k},0),{k},{f})"
    return f"1/(2*{f})"


def ordinal(q):
    """'25th' for q = 0.25; '10th', '50th', '33rd', '1st'."""
    k = int(round(100 * q))
    suf = "th" if 10 <= k % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(k % 10, "th")
    return f"{k}{suf}"


def _clean(v):
    if isinstance(v, (bool, np.bool_)):
        return int(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        v = float(v)
        return "" if math.isnan(v) else v
    if v is None:
        return ""
    return v


class Book:
    def __init__(self, run, path, sentinel=False):
        self.run, self.cfg, self.cells = run, run.cfg, run.cells
        self.S = run.scenarios
        self.n = run.cells.n
        self.sentinel = sentinel
        self.vals = K.compute(run)
        self.dump = K.dump(run, self.vals)
        self.expected = {}
        self.names = {}
        self.prob_rects = {}
        self.wb = xlsxwriter.Workbook(path, {"strings_to_numbers": False, "strings_to_formulas": False,
                                             "strings_to_urls": False})
        bid = run.meta.get("build_id", "000000000000")
        created = _dt.datetime(2020, 1, 1) + _dt.timedelta(seconds=int(bid, 16) % (10 * 365 * 86400))
        self.wb.set_properties({"title": "Scenario workbook", "subject": "Scenario evaluator (recommends nothing)",
                                "comments": f"build {bid}", "created": created})
        self.repro = run.cfg["mode"] == "reproduce"
        self.sheets = REPRO_SHEETS if self.repro else SHEETS
        self.ws = {name: self.wb.add_worksheet(name) for name in self.sheets}
        self._formats()
        self.cohorts = list(self.cells.cohorts)
        self.jbase = self.cells.col(self.cfg["cycle"]["base_cycle"])
        self.targets = risk.median_targets(self.cfg)
        self.ptargets = risk.pct_targets(self.cfg)               # [v0.6.3, BM-1]
        self.score_ts = L.score_thresholds(self.cfg)
        self.hold = K.hold(self.cfg)                               # R4-06
        self.row_h = {}                                           # Summary row heights (max of every request)
        self.srow = {}                                            # CP-3: (dictionary id, instance) -> Summary row
        self.inp = {}
        self.inp_list = {}

    # ------------------------------------------------------------------------------------------------------------
    # formats and writing

    def _formats(self):
        F = self.wb.add_format
        base = {"font_name": "Arial", "font_size": 9}
        inp = dict(base, font_color="#0000FF", locked=False, bg_color="#EEF3FB")
        inh = dict(base, font_color="#0000FF", locked=False, italic=True, bg_color="#F7F9FD")
        self.f = {
            "title": F(dict(base, bold=True, font_size=13)),
            "h": F(dict(base, bold=True, bottom=1, text_wrap=True, valign="bottom")),
            "hl": F(dict(base, bold=True)),
            "hlt": F(dict(base, bold=True, valign="top")),
            "sec": F(dict(base, bold=True, font_size=11, bg_color="#E8E8E8")),
            "t": F(base), "tw": F(dict(base, text_wrap=True, valign="top")),
            "lw": F(dict(base, text_wrap=True)),                 # wrapped label, bottom-aligned with its row [R4-02]
            "note": F(dict(base, italic=True, font_color="#555555")),
            "notew": F(dict(base, italic=True, font_color="#555555", text_wrap=True, valign="top")),
            "data": F(dict(base, num_format="#,##0")),           # counts [v0.6.2, P2-05]
            "datat": F(base),
        }
        nums = {"num": "General", "usd": "$#,##0", "n1": "#,##0.0", "n0": "#,##0", "r3": "0.000", "r4": "0.0000",
                "pct1": "0.0%", "prob": "0%", "int": "0", "text": "@", "pp": "0.0", "sci": "0.00E+00"}
        for k, nf in nums.items():
            self.f[k] = F(dict(base, num_format=nf))
            self.f["in_" + k] = F(dict(inp, num_format=nf))
            self.f["inh_" + k] = F(dict(inh, num_format=nf))
        self.f["in_textw"] = F(dict(inp, text_wrap=True))
        self.f["changed"] = F({"bg_color": "#D9D9D9"})
        self.f["ignored"] = F({"font_strikeout": True, "font_color": "#555555"})
        self.f["clamp_lo"] = F({"num_format": '"under 5%"'})
        self.f["clamp_hi"] = F({"num_format": '"over 95%"'})
        self.f["mergew"] = F(dict(base, text_wrap=True, valign="top"))
        self.f["hold"] = F(dict(base, text_wrap=True, valign="top", align="left", indent=1))  # Phase 4.2: padded
        self.f["tr"] = F(dict(base, align="right"))                          # CP-4: Overview range text
        self.f["setting"] = F(dict(base, font_color="#7F7F7F", font_size=8))   # CP-1: the grey setting column
        # Phase 4.2: a score-band lower bound, with the lowest band (lower bound 0 or less) shown as "below {next}"
        lows = sorted(float(b) for b in self.cfg["score"]["bands"])
        bf = "General"
        if len(lows) > 1 and lows[0] <= 0:
            bf = f'[={lows[0]:g}]"{labels.LOWEST_BAND.format(b=format(lows[1], "g"))}";General'
        self.f["band"] = F(dict(base, num_format=bf))

    def fx(self, sheet, r, c, formula, value, fmt="num"):
        v = _clean(value)
        self.expected[(sheet, r, c)] = v
        cached = -999 if self.sentinel else v
        if not formula.startswith("="):
            formula = "=" + formula
        self.ws[sheet].write_formula(r, c, formula, self.f[fmt], cached)
        if fmt == "prob":
            self.prob_rects.setdefault(sheet, []).append((r, c))

    def val(self, sheet, r, c, v, fmt="n0"):
        v = _clean(v)
        ws = self.ws[sheet]
        if v == "":
            ws.write_blank(r, c, None, self.f[fmt])
        elif isinstance(v, str):
            ws.write_string(r, c, v, self.f[fmt])
        else:
            ws.write_number(r, c, v, self.f[fmt])

    def txt(self, sheet, r, c, t, fmt="t"):
        self.ws[sheet].write_string(r, c, str(t), self.f[fmt])

    def name(self, nm, sheet, r0, c0, r1=None, c1=None):
        r1 = r0 if r1 is None else r1
        c1 = c0 if c1 is None else c1
        tgt = ref(sheet, r0, c0) if (r0, c0) == (r1, c1) else rng(sheet, r0, c0, r1, c1)
        self.wb.define_name(nm, "=" + tgt)
        self.names[nm] = (sheet, r0, c0, r1, c1)

    # ------------------------------------------------------------------------------------------------------------
    # layout planning

    def plan(self):
        n, S = self.n, self.S
        # History: data rows from 6; panels
        self.r0h = 6
        self.hpanels = ["apps", "admits", "rate", "award", "award_pct", "yield", "enrolled"]
        nc = len(self.cohorts)
        self.hcol = {}
        c = 7
        for p in self.hpanels:
            self.hcol[p] = c
            c += nc + 1
        # Response
        self.r0r = 6
        self.rkeys = ["cell_id", "residency", "segment", "score_lo", "scored", "gpa_class", "upper", "n", "e", "a0",
                      "ybar", "abar", "seg_adm", "seg_enr", "res_adm", "res_enr", "grp_adm", "grp_enr", "all_adm",
                      "all_enr", "ypool", "pool_level", "y0_low", "y0_middle", "y0_high", "floor", "cap",
                      "award_lo", "award_hi"]
        self.rcol = {k: i for i, k in enumerate(self.rkeys)}
        # Levers
        self.vhead0 = 3
        self.vfield_row = {f: self.vhead0 + 2 + i for i, (f, _, _) in enumerate(LEVER_FIELDS)}
        self.vrow_name = self.vhead0
        self.vrow_parent = self.vhead0 + 1
        last = max(self.vfield_row.values())
        self.vrow_awards_changed = last + 1
        self.vrow_rates_changed = last + 2
        self.vrow_cells_changed = last + 3
        self.vrow_ignored = last + 4
        self.vrow_colhead = last + 6
        self.r0v = last + 7
        self.vblock = {s.name: 6 + 4 * j for j, s in enumerate(S)}
        self.vmatrix = 6 + 4 * len(S) + 1
        # Ledger
        self.r0l = 8
        stat = ["cell_id", "residency", "segment", "score_lo", "scored", "gpa_class", "upper"]
        stat += [f"g{j}" for j in range(len(self.targets))]
        stat += [f"p{j}" for j in range(len(self.ptargets))]                 # [v0.6.3, BM-1] signs at each target t
        stat += ["floor", "cap", "a0", "y0", "award_lo", "award_hi", "apps_base"]
        self.lstat = {k: i for i, k in enumerate(stat)}
        self.ltw = [f"tw{i}" for i in range(len(self.cfg["risk"]["tuition_grid"]))]
        self.lblock = {}
        for k in CASES:
            c = len(stat) + 1
            keys = BLOCK + (self.ltw + ["admits_pool1"] if k == "middle" else [])
            for s in S:
                self.lblock[(k, s.name)] = {key: c + i for i, key in enumerate(keys)}
                c += len(keys) + 1
        self.ltot = self.r0l + n + 1
        # Trim
        nN = len(self.cfg["class"]["what_if"])
        self.tN = nN
        self.tblock = {}
        top = 3
        for s in S:
            self.tblock[s.name] = top
            top += n + 8
        self.tc_share0 = 10
        self.tc_lc0 = 10 + nN + 1
        # Reproduce (reproduce builds only): header rows per scenario, then per cell admit_rate, award_usd, yield
        self.prow = {"name": 3, "parent": 4, "pool_multiplier": 5, "tuition": 6, "specialty_usd": 7, "need_total": 8}
        self.pcolhead = 11
        self.r0p = 12
        self.pblock = {s.name: 6 + 4 * j for j, s in enumerate(S)}

    # convenience references --------------------------------------------------------------------------------------
    def HR(self, panel, j):  # History column range over cells for cohort j
        c = self.hcol[panel] + j
        return rng("History", self.r0h, c, self.r0h + self.n - 1, c)

    def RR(self, key):
        c = self.rcol[key]
        return rng("Response", self.r0r, c, self.r0r + self.n - 1, c)

    def Rc(self, key, i):
        return ref("Response", self.r0r + i, self.rcol[key])

    def LV(self, s, field):
        return ref("Levers", self.vfield_row[field], self.vblock[s])

    def LVc(self, s, key, i):
        off = {"rate": 0, "award": 1, "ft": 2}[key]
        return ref("Levers", self.r0v + i, self.vblock[s] + off)

    def LVR(self, s, key):
        off = {"rate": 0, "award": 1, "ft": 2}[key]
        c = self.vblock[s] + off
        return rng("Levers", self.r0v, c, self.r0v + self.n - 1, c)

    def LR(self, k, s, key):
        c = self.lblock[(k, s)][key]
        return rng(CASE_SHEET[k], self.r0l, c, self.r0l + self.n - 1, c)

    def LSR(self, k, key):
        c = self.lstat[key]
        return rng(CASE_SHEET[k], self.r0l, c, self.r0l + self.n - 1, c)

    def LH(self, k, s, key):
        if key == "need_lump":                       # the need departure (spec section 0A item B5; R4-07)
            return ref(CASE_SHEET[k], 5, self.lblock[(k, s)]["in_seg"] + 3)
        row = {"name": 2, "T": 3, "p": 4, "need_rate": 5, "seg": 6}[key]
        return ref(CASE_SHEET[k], row, self.lblock[(k, s)]["in_seg"] + 1)

    def LT(self, k, s, key):  # totals row cell
        return ref(CASE_SHEET[k], self.ltot, self.lblock[(k, s)][key])

    # ------------------------------------------------------------------------------------------------------------
    def write(self):
        self.plan()
        self.w_inputs()
        self.w_history()
        self.w_response()
        self.w_levers()
        if self.repro:
            self.w_reproduce()
        for k in CASES:
            self.w_ledger(k)
        if not self.repro:
            self.w_trim()
        self.w_summary(dry=True)
        self.w_summary(dry=False)
        self.w_distribution()
        if not self.repro:                    # CP-6: reproduce builds keep the plain labels, no Overview or charts
            self.w_overview()
            self.w_charts()
        self.w_checks()
        self.w_runlog()
        self.w_readme()
        self.finish()
        self.wb.close()

    def finish(self):
        for sheet, cells in self.prob_rects.items():
            ws = self.ws[sheet]
            runs = []
            for r, c in sorted(set(cells)):
                if runs and runs[-1][0] == r and runs[-1][2] == c - 1:
                    runs[-1][2] = c
                else:
                    runs.append([r, c, c])
            for r, c, c1 in runs:
                cell = a1(r, c, abs_=False)
                ws.conditional_format(r, c, r, c1, {
                    "type": "formula", "format": self.f["clamp_lo"],
                    "criteria": f'=(in_shock_source="illustrative")*ISNUMBER({cell})*({cell}<0.05)'})
                ws.conditional_format(r, c, r, c1, {
                    "type": "formula", "format": self.f["clamp_hi"],
                    "criteria": f'=(in_shock_source="illustrative")*ISNUMBER({cell})*({cell}>0.95)'})
        for name, ws in self.ws.items():
            ws.protect("", {"format_columns": True, "format_rows": True})
            ws.set_landscape()
            ws.set_paper(1)
        for name in ("Inputs", "Checks", "README", "RunLog", "Overview"):
            if name in self.ws:
                self.ws[name].fit_to_pages(1, 0)
        # R4-01, R4-02: Summary prints at a readable scale, wide tables continuing across pages with columns A and B
        # repeated (the PDF render, sw/lo.py, sets each section separately)
        self.ws["Summary"].set_print_scale(70)

    # ------------------------------------------------------------------------------------------------------------
    # Inputs

    def w_inputs(self):
        cfg = self.cfg
        ws = self.ws["Inputs"]
        VC = 2                                   # CP-1: values from column C; column B is the grey setting column
        self.inputs_vc = VC

        def plain_note(t):
            """Inputs notes without review or decision IDs (CP-2)."""
            t = re.sub(r"\s*\[v0\.[^\]]*\]", "", t)
            return re.sub(r"\s*\((?:OD-\d+|D\d+|methodology O\d+|R-\d+)\)", "", t)
        ws.set_column(0, 0, 44)
        ws.set_column(1, 1, 18)
        self.tyears = sorted(set(cfg["tuition_increase_by_year"]) | set(cfg.get("tuition_by_year_usd") or {}))
        lists = [len(cfg["score"]["bands"]), len(cfg["risk"]["pool_grid"]), len(cfg["class"]["what_if"]),
                 len(cfg["risk"]["yield_shift_grid"]), len(cfg["risk"]["tuition_grid"]), len(self.cohorts), 4,
                 len(self.tyears), len(self.ptargets)]
        self.inote = VC + 1 + max(lists)
        ws.set_column(VC, self.inote - 1, 11)
        ws.set_column(self.inote, self.inote, 70)
        self.txt("Inputs", 0, 0, "Inputs", "title")
        self.txt("Inputs", 2, 0, "Setting names (grey, column B) are the configuration keys the analyst uses; the "
                                 "plain label is in column A.", "note")
        self.txt("Inputs", 1, 0, "Blue cells are inputs. 'live' inputs drive formulas; 'build-time' inputs are shown "
                                 "for reference and need a rebuild to apply. Mode: " + MODE_LABEL[cfg["mode"]]
                 + (" (reproduce build; see the Reproduce sheet)." if self.repro else " (live build)."), "note")
        self.ir = 3

        def sec(t):
            self.ir += 1
            self.txt("Inputs", self.ir, 0, t, "sec")
            self.ir += 1

        def lab(r, rid, setting=None):
            """CP-1: the plain label from the dictionary in column A, the code name in the grey setting column."""
            row = DD.row(rid)
            self.txt("Inputs", r, 0, row["plain_name"] if "{" in row["client_label"] else DD.label(rid), "lw")
            self.txt("Inputs", r, 1, setting or DD.row(rid)["analyst_name"], "setting")

        def one(key, rid, v, fmt="in_num", note="live", formula=None):
            r = self.ir
            self.ir += 1
            lab(r, rid)
            if formula:
                self.fx("Inputs", r, VC, formula, v, fmt)
            else:
                self.val("Inputs", r, VC, v, fmt)
            self.txt("Inputs", r, self.inote, plain_note(note), "note")
            nm = f"in_{key}"
            self.name(nm, "Inputs", r, VC)
            self.inp[key] = nm
            return r

        def many(key, rid, vs, fmt="in_num", note="live", setting=None):
            r = self.ir
            self.ir += 1
            lab(r, rid, setting)
            for i, v in enumerate(vs):
                self.val("Inputs", r, VC + i, v, fmt)
            self.txt("Inputs", r, self.inote, plain_note(note), "note")
            nm = f"in_{key}"
            self.name(nm, "Inputs", r, VC, r, VC + len(vs) - 1)
            self.inp[key] = nm
            self.inp_list[key] = [ref("Inputs", r, VC + i) for i in range(len(vs))]
            return r

        sec("Client")
        one("client_id", "IN-001", cfg["client"]["id"], "in_text", "build-time")
        one("client_name", "IN-002", cfg["client"]["name"], "in_text", "build-time")
        one("vertical", "IN-003", cfg["client"]["vertical"], "in_text", "build-time")
        one("small_cell_policy", "IN-004", cfg["client"]["small_cell_policy"], "in_text",
            "build-time; methodology section 9")
        sec("Mode")
        mode_note = ("live: Reproduce takes the loaded yields and tuition on the Reproduce sheet; Live takes the "
                     "response yields and the tuition formula" if self.repro else
                     "live build: there are no loaded values, so the Ledger always uses the response yields and the "
                     "tuition formula (Checks flags Reproduce)")
        one("mode", "IN-070", MODE_LABEL[cfg["mode"]], "in_text", mode_note)
        self.ws["Inputs"].data_validation(self.ir - 1, VC, self.ir - 1, VC,
                                          {"validate": "list", "source": ["Live", "Reproduce"]})
        if self.repro:
            one("round_apps_after_pool", "IN-074", int(round_apps_after_pool(cfg)), "in_int",
                "live; read only while the mode is Reproduce (the fixture's arithmetic; live mode never rounds "
                "applications, spec section 3)")
        sec("Cycle and tuition")
        one("base_cycle", "IN-005", cfg["cycle"]["base_cycle"], "in_int", "build-time")
        one("plan_cycle", "IN-006", cfg["cycle"]["plan_cycle"], "in_int", "build-time")
        many("history", "IN-007", self.cohorts, "in_int", "build-time")
        tbc = [cfg["tuition_by_cohort"][y] for y in self.cohorts]
        many("tuition_by_cohort", "IN-008", tbc, "in_usd")
        one("tuition_base", "IN-009", cfg["tuition_base"], "usd",
            "formula: tuition_by_cohort at base_cycle",
            formula=f"INDEX(in_tuition_by_cohort,MATCH(in_base_cycle,in_history,0))")
        yrs = self.tyears
        many("tuition_increase_years", "IN-010", yrs, "in_int", "build-time")
        many("tuition_increase_pct", "IN-010",
             [cfg["tuition_increase_by_year"].get(y) for y in yrs], "in_pp",
             "live (Baseline's tuition_increase_pct reads it, unless tuition_by_year_usd is set for the year)")
        usd = cfg.get("tuition_by_year_usd") or {}
        many("tuition_by_year_usd", "IN-011", [usd.get(y) for y in yrs], "in_usd",
             "live [v0.6.3, BM-2]: the implied increase is 100 x (tuition_by_year_usd / tuition_base - 1), unrounded")
        one("tuition_rounding_usd", "IN-012", cfg["tuition_rounding_usd"], "in_usd")
        r = self.ir
        self.ir += 1
        lab(r, "INT-021", "in_tuition_implied_pct")
        for i, y in enumerate(yrs):
            self.fx("Inputs", r, VC + i, f"({self.tuition_factor_x(y)}-1)*100", plan_increase_pct(cfg, y), "pp")
        self.txt("Inputs", r, self.inote, "formula: cumulative from base_cycle; a year with tuition_by_year_usd "
                                          "resets to that figure", "note")
        self.name("in_tuition_implied_pct", "Inputs", r, VC, r, VC + len(yrs) - 1)
        sec("Score and GPA")
        one("score_measure", "IN-013", cfg["score"]["measure"], "in_text", "build-time")
        many("score_bands", "IN-014", cfg["score"]["bands"], "in_int", "build-time")
        one("pool_threshold", "IN-015", cfg["score"]["pool_threshold"], "in_int")
        one("score_floor", "IN-016", cfg["score"]["floor"], "in_int",
            "live; under trim.protect_segment above_floor the Trim order uses the build's floor (Checks flags a change)")
        many("median_thresholds", "IN-020",
             cfg["score"]["median_thresholds"], "in_int",
             "live in the Ledger and Summary; the Trim order uses the build's first threshold")
        # [v0.6.3, BM-1] percentile targets: q build-time (labels and layout), t live (a q = 0.5 target's t reads its
        # median threshold), the continuity correction 1/(2n) by formula
        med_i = 0
        rq, rt, rc = self.ir, self.ir + 1, self.ir + 2
        self.ir += 3
        lab(rq, "IN-018", "score.percentile_targets.q")
        lab(rt, "IN-019", "score.percentile_targets.t")
        lab(rc, "INT-022", "in_pct_corr")
        self.inp_list["pct_q"], self.inp_list["pct_t"], self.inp_list["pct_corr"] = [], [], []
        for i, (q, t) in enumerate(self.ptargets):
            self.val("Inputs", rq, VC + i, q, "in_num")
            if q == 0.5:
                self.fx("Inputs", rt, VC + i, self.inp_list["median_thresholds"][med_i], t, "inh_int")
                med_i += 1
            else:
                self.val("Inputs", rt, VC + i, t, "in_int")
            self.fx("Inputs", rc, VC + i, lattice_corr_x(a1(rq, VC + i)), 1.0 / (2 * pct_lattice_n(q)), "r4")
            for key, rr in (("pct_q", rq), ("pct_t", rt), ("pct_corr", rc)):
                self.inp_list[key].append(ref("Inputs", rr, VC + i))
        self.txt("Inputs", rq, self.inote, "build-time (sets the rows and labels; Checks flags a change)", "note")
        self.txt("Inputs", rt, self.inote, "live; a q = 0.5 target reads its median threshold (italic); Checks lists a t "
                                           "that is not a band bound. " + labels.GPA_PCT_NOTE, "note")
        self.txt("Inputs", rc, self.inote, "formula; half the lattice step of the margin (Review_Phase2_2_Plan.md "
                                           "section 2)", "note")
        n_p = len(self.ptargets)
        for key, rr in (("pct_q", rq), ("pct_t", rt), ("pct_corr", rc)):
            self.name(f"in_{key}", "Inputs", rr, VC, rr, VC + n_p - 1)
            self.inp[key] = f"in_{key}"
        one("gpa_measure", "IN-021", cfg["gpa"]["measure"], "in_text", "build-time")
        one("gpa_hi_at_or_above", "IN-022", cfg["gpa"]["hi_at_or_above"], "in_num",
            "build-time (GPA classes are in the cell data)")
        one("gpa_median_threshold", "IN-024",
            cfg["gpa"]["median_threshold"], "in_num", "build-time")
        one("unscored_in_median", "IN-025", cfg["unscored_in_median"], "in_text",
            "live; " + labels.POLICY_UNSCORED_EXCLUDED)
        self.ws["Inputs"].data_validation(self.ir - 1, VC, self.ir - 1, VC,
                                          {"validate": "list", "source": ["excluded", "below"]})
        sec("Class")
        cl = cfg["class"]
        one("class_cap", "IN-026", cl["cap"], "in_num", "live (Baseline reads it)")
        one("class_target", "IN-027", cl["target"], "in_num", "live (Baseline reads it)")
        one("class_band", "IN-028", cl["band"])
        many("class_what_if", "IN-029", cl["what_if"], "in_num")
        many("supported_range", "IN-030", cl["supported_range"], "in_num")
        many("reject_range", "IN-031", cl["reject_range"], "in_num",
             "build-time (checked when scenarios are built)")
        sec("Need aid")
        one("need_total", "IN-032", cfg["need"]["total"], "in_usd", "live (Baseline reads it)")
        one("need_reference_class", "IN-033", cfg["need"]["reference_class"], "in_num")
        nr = float(cfg["need"]["total"]) / float(cfg["need"]["reference_class"])
        one("need_rate", "INT-019", nr, "usd", "formula", formula="in_need_total/in_need_reference_class")
        need_lbl = labels.NEED_LABEL.format(total=f"${labels.xl(cfg['need']['total']):,.0f}",
                                            ref=f"{cfg['need']['reference_class']:g}", rate=f"${labels.xl(nr):,.0f}")
        r = self.ir
        self.ir += 1
        lab(r, "OUT-186", "NEED_LABEL")
        self.fx("Inputs", r, VC, '"Need aid: $"&TEXT(in_need_total,"#,##0")&" at a class of "&in_need_reference_class'
                                '&" ($"&TEXT(in_need_rate,"#,##0")&" per enrollee; scales with class)"', need_lbl, "t")
        sec("Targets")
        one("ntr_target", "IN-034", cfg.get("ntr_target"), "in_usd")
        one("ntr_goal_basis", "IN-035", cfg.get("ntr_goal_basis", "entering_y1"),
            "in_text", "live [v0.6.3, BM-4]: all_jd compares continuing + ntr_y1 with ntr_target")
        self.ws["Inputs"].data_validation(self.ir - 1, VC, self.ir - 1, VC,
                                          {"validate": "list", "source": ["entering_y1", "all_jd"]})
        one("continuing_ntr_usd", "IN-036",
            cfg.get("continuing_ntr_usd"), "in_usd", "live; " + labels.CONTINUING_LABEL)
        one("ntr_target_eff", "INT-020",
            ntr_target_effective(cfg), "usd",
            "formula: ntr_target under entering_y1; ntr_target - continuing_ntr_usd under all_jd",
            formula='IF(in_ntr_target="","",IF(in_ntr_goal_basis="all_jd",in_ntr_target-in_continuing_ntr_usd,'
                    'in_ntr_target))')
        one("discount_target", "IN-037", cfg.get("discount_target"), "in_pct1",
            "live (Baseline reads it)")
        one("budget_total", "IN-038", cfg.get("budget_total"), "in_usd", "live (Checks)")
        one("budget_basis", "IN-039", cfg["budget_basis"], "in_text",
            "live (Checks): total_aid compares merit + need + specialty; merit compares merit only (OD-10)")
        self.ws["Inputs"].data_validation(self.ir - 1, VC, self.ir - 1, VC,
                                          {"validate": "list", "source": ["total_aid", "merit"]})
        mab = cfg.get("merit_actual_by_cohort") or {}
        many("merit_actual_by_cohort", "IN-040",
             [mab.get(int(y)) for y in self.cohorts], "in_usd", "live (Checks: history reconciliation)")
        sec("Risk and response (placeholders until calibrated)")
        rk = cfg["risk"]
        one("common_shock_sd", "IN-041", rk["common_shock_sd"], "in_num",
            "live; illustrative until calibrated (methodology O37)")
        one("shock_source", "IN-042", rk["shock_source"], "in_text", "live")
        self.ws["Inputs"].data_validation(self.ir - 1, VC, self.ir - 1, VC,
                                          {"validate": "list", "source": ["illustrative", "public", "client"]})
        one("shock_corr", "IN-043", rk["shock_corr_above_below"], "in_num")
        for c in CASES:
            one(f"slope_{c}", {"low": "IN-044", "middle": "IN-045", "high": "IN-046"}[c], rk["sensitivity_slopes"][c],
                "in_num", "live; placeholder (D6); " + labels.RESPONSE_LABEL)
        for g in ("upper", "lower"):
            one(f"yield_floor_{g}", {"upper": "IN-047", "lower": "IN-049"}[g], rk["yield_floor"][g], "in_num")
            one(f"yield_cap_{g}", {"upper": "IN-048", "lower": "IN-050"}[g], rk["yield_cap"][g], "in_num")
        many("yield_shift_grid", "IN-051", rk["yield_shift_grid"], "in_num")
        many("pool_grid", "IN-052", rk["pool_grid"], "in_num")
        many("tuition_grid", "IN-053", rk["tuition_grid"], "in_pp")
        one("pooling_k", "IN-054", cfg["pooling_k"], "in_num")
        one("pooling_min_admits", "IN-055", cfg["pooling_min_admits"], "in_num",
            "product rule (spec section 4)")
        one("evidence_tolerance_usd", "IN-058", cfg["evidence_tolerance_usd"], "in_usd")
        one("marginal_admit_yield_slope", "IN-059", cfg["marginal_admit_yield_slope"], "in_num",
            "read and ignored: marginal-admit yield is not modeled")
        one("integer_admits", "IN-056", int(cfg["integer_admits"]), "in_int",
            "live; reproduce mode uses 1, live mode 0 (spec section 2)")
        one("integer_enrolled", "IN-057", int(cfg["integer_enrolled"]), "in_int",
            "live; reproduce mode uses 1, live mode 0 (spec section 2)")
        sec("Segments (one active per scenario, chosen on Levers)")
        segs = cfg["segments"]
        hdr = self.ir
        self.ir += 1
        for i, h in enumerate([DD.label(x) for x in ("IN-061", "IN-062", "IN-063", "IN-064")]):
            self.txt("Inputs", hdr, VC + i, h, "h")
        lab(hdr, "IN-060", "segments")
        r0 = self.ir
        for sg in segs or [{"name": "", "within": {"residency": ""}, "members_label": "", "share_source": ""}]:
            r = self.ir
            self.ir += 1
            lab(r, "IN-060", "segments")
            for i, v in enumerate([sg["name"], sg["within"]["residency"], sg["members_label"], sg["share_source"]]):
                self.val("Inputs", r, VC + i, v, "in_text")
            self.txt("Inputs", r, self.inote, "build-time (cells carry the segment)", "note")
        r1 = self.ir - 1
        for i, key in enumerate(["seg_names", "seg_within", "seg_members", "seg_share_source"]):
            self.name(f"in_{key}", "Inputs", r0, VC + i, r1, VC + i)
            self.inp[key] = f"in_{key}"
        sec("Trimming for the class-size table")
        one("protect_segment", "IN-065",
            cfg["trim"]["protect_segment"], "in_text", "build-time (sets the Trim order)")
        one("trim_floor_rate", "IN-066", cfg["trim"]["floor_rate"], "in_num")
        one("exempt_cells", "IN-067", ", ".join(cfg["trim"]["exempt_cells"]) or "", "in_text",
            "build-time")
        sec("Pool")
        one("pool_ytd_growth", "IN-068", cfg.get("pool_ytd_growth"),
            "in_pct1", "complete applications at or above score.pool_threshold against the same week of the prior "
                       "cycle [v0.6.3, BM-6]; " + labels.POOL_YTD_LABEL)
        one("pool_ytd_as_of", "IN-069", cfg.get("pool_ytd_as_of"), "in_text",
            "display only")
        sec("Display")
        one("case_selector", "IN-125", "Middle", "in_text",
            "live: the rows 'for the case chosen on Inputs' in Summary section H")
        self.ws["Inputs"].data_validation(self.ir - 1, VC, self.ir - 1, VC,
                                          {"validate": "list", "source": ["Low", "Middle", "High"]})
        one("chart_scenario", DD.rid("in_chart_scenario", "input_workbook"), self.S[0].name, "in_text",
            "live: the scenario the class-size chart on the Charts sheet shows")
        self.ws["Inputs"].data_validation(self.ir - 1, VC, self.ir - 1, VC,
                                          {"validate": "list", "source": [s.name for s in self.S]})
        self.ws["Inputs"].freeze_panes(3, VC)

    def tuition_factor_x(self, year):
        """Excel factor tuition(year) / tuition_base, as config.plan_increase_pct computes it [v0.6.3, BM-2]: the
        increases compound; a year with tuition_by_year_usd resets the factor to tuition_by_year_usd / tuition_base.
        R4-14: a year with no row on Inputs (no increase and no dollar figure in the config) breaks the chain; a later
        dollar figure restarts it, and clearing that figure gives a blank factor (an error downstream, never a silent
        1)."""
        f = "1"
        for y in range(self.cfg["cycle"]["base_cycle"] + 1, year + 1):
            if y not in self.tyears:
                f = None
                continue
            i = self.tyears.index(y)
            inc, usd = self.inp_list["tuition_increase_pct"][i], self.inp_list["tuition_by_year_usd"][i]
            prev = '""' if f is None else f"{f}*(1+{inc}/100)"
            f = f'IF({usd}="",{prev},{usd}/in_tuition_base)'
        return f

    # ------------------------------------------------------------------------------------------------------------
    # History

    def _cell_static(self, sheet, r0, with_upper=False):
        cells = self.cells
        for i in range(self.n):
            r = r0 + i
            self.val(sheet, r, 0, cells.cell_id[i], "datat")
            self.val(sheet, r, 1, cells.residency[i], "datat")
            self.val(sheet, r, 2, cells.segment[i] or SEG_NONE, "datat")
            s = cells.score_lo[i]
            self.val(sheet, r, 3, None if np.isnan(s) else float(s), "int")
            self.val(sheet, r, 4, 0 if np.isnan(s) else 1, "int")
            self.val(sheet, r, 5, cells.gpa_class[i], "datat")

    def _static_heads(self, sheet, row):
        for c, h in enumerate(["cell_id", "residency", "segment", "score_lo (blank = unscored)", "scored (1/0)",
                               "gpa_class"]):
            self.txt(sheet, row, c, h, "h")

    def w_history(self):
        cells, cfg = self.cells, self.cfg
        ws = self.ws["History"]
        nc = len(self.cohorts)
        self.txt("History", 0, 0, "History: cell x cohort (complete applications; admits include waitlist admits, in "
                                  "the cohort applied to; enrolled at census)", "title")
        self.txt("History", 1, 0, "Cell-level counts (data). Admit rate, award % of tuition and yield are formulas.",
                 "note")
        ws.set_column(0, 0, 24)
        ws.set_column(1, 6, 9)
        ws.set_column(7, self.hcol["enrolled"] + nc, 8)
        titles = {"apps": "Applications", "admits": "Admits", "rate": "Admit rate", "award": "Award $",
                  "award_pct": "Award % of tuition", "yield": "Yield", "enrolled": "Enrolled"}
        self._static_heads("History", self.r0h - 1)
        tbc = self.inp_list["tuition_by_cohort"]
        for p in self.hpanels:
            self.txt("History", self.r0h - 3, self.hcol[p], titles[p], "hl")
            for j, coh in enumerate(self.cohorts):
                self.fx("History", self.r0h - 2, self.hcol[p] + j, self.inp_list["history"][j], coh, "int")
                self.txt("History", self.r0h - 1, self.hcol[p] + j, str(coh), "h")
        self._cell_static("History", self.r0h)
        T = [cfg["tuition_by_cohort"][y] for y in self.cohorts]
        unknown = cells.meta.get("apps_unknown")
        for i in range(self.n):
            r = self.r0h + i
            for j in range(nc):
                apps, adm = cells.apps[i, j], cells.admits[i, j]
                aw, en = cells.award[i, j], cells.enrolled[i, j]
                # unknown applications (not in the file) are blank, not 0; formulas read a blank as 0
                self.val("History", r, self.hcol["apps"] + j,
                         "" if unknown is not None and unknown[i, j] else apps, "n0")
                self.val("History", r, self.hcol["admits"] + j, adm, "n0")
                self.val("History", r, self.hcol["award"] + j, aw, "usd")
                self.val("History", r, self.hcol["enrolled"] + j, en, "n0")
                A = a1(r, self.hcol["apps"] + j, False)
                D = a1(r, self.hcol["admits"] + j, False)
                W = a1(r, self.hcol["award"] + j, False)
                E = a1(r, self.hcol["enrolled"] + j, False)
                self.fx("History", r, self.hcol["rate"] + j, f'IF({A}>0,{D}/{A},"")', adm / apps if apps > 0 else "",
                        "r4")
                self.fx("History", r, self.hcol["award_pct"] + j, f"{W}/{tbc[j]}", aw / T[j], "pct1")
                self.fx("History", r, self.hcol["yield"] + j, f'IF({D}>0,{E}/{D},"")', en / adm if adm > 0 else "",
                        "r4")
        # totals
        r = self.r0h + self.n + 1
        groups = [("Total in-state", f'(RES="in")', cells.residency == "in"),
                  ("Total out-of-state", f'(RES="out")', cells.residency == "out")]
        for sg in cfg["segments"]:
            groups.append((f"Total segment {sg['name']}", f'(SEG={xs(sg["name"])})', cells.segment == sg["name"]))
        groups.append((f"Total outside any segment", f'(SEG={xs(SEG_NONE)})', cells.segment == ""))
        groups.append(("Total", None, np.ones(self.n, bool)))
        RES = rng("History", self.r0h, 1, self.r0h + self.n - 1, 1)
        SEG = rng("History", self.r0h, 2, self.r0h + self.n - 1, 2)
        self.htot = {}
        for lab, crit, mask in groups:
            self.txt("History", r, 0, lab, "hl")
            crit = None if crit is None else crit.replace("RES", RES).replace("SEG", SEG)
            for j in range(nc):
                rowv = {}
                for p in ("apps", "admits", "enrolled"):
                    col = self.HR(p, j)
                    f = f"SUM({col})" if crit is None else f"SUMPRODUCT({crit}*{col})"
                    arr = {"apps": cells.apps, "admits": cells.admits, "enrolled": cells.enrolled}[p][:, j]
                    rowv[p] = float(arr[mask].sum())
                    self.fx("History", r, self.hcol[p] + j, f, rowv[p], "n0")
                A = a1(r, self.hcol["apps"] + j, False)
                D = a1(r, self.hcol["admits"] + j, False)
                E = a1(r, self.hcol["enrolled"] + j, False)
                self.fx("History", r, self.hcol["rate"] + j, f'IF({A}>0,{D}/{A},"")',
                        rowv["admits"] / rowv["apps"] if rowv["apps"] > 0 else "", "r4")
                self.fx("History", r, self.hcol["yield"] + j, f'IF({D}>0,{E}/{D},"")',
                        rowv["enrolled"] / rowv["admits"] if rowv["admits"] > 0 else "", "r4")
                adm, aw = self.HR("admits", j), self.HR("award", j)
                m = (cells.admits[:, j] * cells.award[:, j])[mask].sum()
                d = cells.admits[mask, j].sum()
                num = f"SUMPRODUCT({adm},{aw})" if crit is None else f"SUMPRODUCT({crit}*{adm}*{aw})"
                self.fx("History", r, self.hcol["award"] + j, f'IF({D}>0,{num}/{D},"")', m / d if d > 0 else "",
                        "usd")
                W = a1(r, self.hcol["award"] + j, False)
                self.fx("History", r, self.hcol["award_pct"] + j, f'IF({D}>0,{W}/{tbc[j]},"")',
                        (m / d) / T[j] if d > 0 else "", "pct1")
            self.htot[lab] = r
            r += 1
        self.txt("History", r, 0, "Tuition (published, first year)", "hl")
        for j in range(nc):
            self.fx("History", r, self.hcol["award"] + j, tbc[j], T[j], "usd")
        self.txt("History", r + 1, 0, "Award $ in totals rows: admit-weighted mean. Segment '(none)': outside every "
                                      "segment.", "note")
        rec = cells.meta.get("apps_recovered")
        n_unk = 0 if unknown is None else int(unknown.sum())
        n_rec = 0 if rec is None else int(rec.sum())
        if n_unk or n_rec:
            self.txt("History", r + 2, 0, f"Applications: {n_unk} cell-cohorts blank (not in the file; admit rate 0 or "
                                          f"blank there), read as 0 by the Ledgers; {n_rec} recovered from the scenario "
                                          f"columns (one value fits every scenario; DECISIONS Nov 18).", "note")
        self._history_509(r + 4)
        ws.freeze_panes(self.r0h, 1)

    def _history_509(self, r):
        """ABA 509 reconciliation block (R3-4): report only, never asserted. Count rows are formulas over History;
        percentile rows are computed at build from the band shares."""
        cells = self.cells
        rec = self.vals["aba509_reconciliation"]
        self.txt("History", r, 0, "ABA 509 reconciliation (report only; not asserted; R3-4)", "hl")
        self.txt("History", r + 1, 0, "Counts are formulas over the cell data. Percentile rows give the range the "
                                      "band shares allow for enrollees with a score (with a GPA), the ABA 509 basis; "
                                      "computed at build. 509 figures: aba_509_by_cohort in config (public).", "note")
        c0 = self.hcol["apps"]
        for j, y in enumerate(self.cohorts):
            for kk, h in enumerate(("cells", "509", "verdict")):
                self.txt("History", r + 2, c0 + 3 * j + kk, f"{y} {h}", "h")
        SC = rng("History", self.r0h, 4, self.r0h + self.n - 1, 4)
        GP = rng("History", self.r0h, 5, self.r0h + self.n - 1, 5)
        self.h509 = {}
        for t, row0 in enumerate(rec[0]["rows"]):
            rr = r + 3 + t
            self.txt("History", rr, 0, row0["label"])
            for j, y in enumerate(self.cohorts):
                x = rec[j]["rows"][t]
                cc, ca, cv = c0 + 3 * j, c0 + 3 * j + 1, c0 + 3 * j + 2
                self.val("History", rr, ca, "" if x["aba"] is None else x["aba"], "in_num")
                if x["key"] in ("first_year_class", "without_score", "without_gpa"):
                    E = self.HR("enrolled", j)
                    f = {"first_year_class": f"SUM({E})", "without_score": f"SUMPRODUCT(({SC}=0)*{E})",
                         "without_gpa": f'SUMPRODUCT(({GP}="blank")*{E})'}[x["key"]]
                    self.fx("History", rr, cc, f, x["cells"], "n0")
                    C, A = a1(rr, cc, False), a1(rr, ca, False)
                    self.fx("History", rr, cv, f'IF({A}="",{xs(labels.ABA509_NOT_GIVEN)},IF(({C}-{A})^2<1E-12,'
                                               f'{xs(labels.ABA509_AGREES)},{xs(labels.ABA509_DIFFERS)}))',
                            x["verdict"], "t")
                else:
                    self.val("History", rr, cc, x["cells"], "t")
                    self.val("History", rr, cv, x["verdict"], "t")
        nrow = len(rec[0]["rows"])
        for j, y in enumerate(self.cohorts):
            cv = c0 + 3 * j + 2
            self.h509[y] = rng("History", r + 3, cv, r + 2 + nrow, cv)

    # ------------------------------------------------------------------------------------------------------------
    # Response

    def w_response(self):
        cells, cfg, base = self.cells, self.cfg, self.run.base
        ws = self.ws["Response"]
        n = self.n
        self.txt("Response", 0, 0, "Response (placeholder): base yield by partial pooling, re-centered at the latest "
                                   "award; " + labels.RESPONSE_LABEL, "title")
        self.txt("Response", 1, 0, "y0 = (n (ybar + b/100 (a0 - abar)/1000) + k ypool) / (n + k); a cell with no "
                                   "admits takes ypool. Pool: (residency, segment, score group) with at least the "
                                   "pool size in admits, else (residency, score group), else score group, else all.",
                 "note")
        self.txt("Response", 2, 0, "Yield at a candidate award a: clip(y0 + (b/100)(a - a0)/1000, floor, cap). The rung "
                                   "grid on the right is for display only; no Ledger formula reads it.", "note")
        heads = {"upper": "upper score group (1/0)", "n": "n (admits, all cohorts)", "e": "enrolled, all cohorts",
                 "a0": "a0 (latest award)", "ybar": "ybar", "abar": "abar", "seg_adm": "pool admits: res x seg x group",
                 "seg_enr": "pool enrolled: res x seg x group", "res_adm": "pool admits: res x group",
                 "res_enr": "pool enrolled: res x group", "grp_adm": "pool admits: group",
                 "grp_enr": "pool enrolled: group", "all_adm": "pool admits: all", "all_enr": "pool enrolled: all",
                 "ypool": "ypool", "pool_level": "pool used", "y0_low": "y0 Low", "y0_middle": "y0 Middle",
                 "y0_high": "y0 High", "floor": "yield floor", "cap": "yield cap",
                 "award_lo": "observed award low", "award_hi": "observed award high"}
        self._static_heads("Response", self.r0r - 1)
        for k, h in heads.items():
            self.txt("Response", self.r0r - 1, self.rcol[k], h, "h")
        ws.set_column(0, 0, 24)
        ws.set_column(1, 60, 9)
        self._cell_static("Response", self.r0r)
        upper = response.score_group_upper(cells, cfg).astype(int)
        adm_tot = cells.admits.sum(axis=1)
        enr_tot = cells.enrolled.sum(axis=1)
        keys = {"seg": list(zip(cells.residency, cells.segment, upper)), "res": list(zip(cells.residency, upper)),
                "grp": list(upper)}
        sums = {}
        for lvl, ks in keys.items():
            d = {}
            for i, kk in enumerate(ks):
                a, e = d.get(kk, (0.0, 0.0))
                d[kk] = (a + adm_tot[i], e + enr_tot[i])
            sums[lvl] = d
        nc = len(self.cohorts)
        RESr, SEGr, UPr = self.RR("residency"), self.RR("segment"), self.RR("upper")
        Nr, Er = self.RR("n"), self.RR("e")
        for i in range(n):
            r = self.r0r + i
            c = lambda k: a1(r, self.rcol[k], False)  # noqa: E731
            self.fx("Response", r, self.rcol["upper"],
                    f"IF({c('scored')}=1,IF({c('score_lo')}>=in_pool_threshold,1,0),0)", upper[i], "int")
            hr = self.r0h + i
            adm_row = rng("History", hr, self.hcol["admits"], hr, self.hcol["admits"] + nc - 1)
            enr_row = rng("History", hr, self.hcol["enrolled"], hr, self.hcol["enrolled"] + nc - 1)
            aw_row = rng("History", hr, self.hcol["award"], hr, self.hcol["award"] + nc - 1)
            self.fx("Response", r, self.rcol["n"], f"SUM({adm_row})", base.n[i], "n1")
            self.fx("Response", r, self.rcol["e"], f"SUM({enr_row})", enr_tot[i], "n1")
            self.fx("Response", r, self.rcol["a0"], ref("History", hr, self.hcol["award"] + self.jbase), base.a0[i],
                    "usd")
            self.fx("Response", r, self.rcol["ybar"], f'IF({c("n")}>0,{c("e")}/{c("n")},"")', base.ybar[i], "r4")
            self.fx("Response", r, self.rcol["abar"], f'IF({c("n")}>0,SUMPRODUCT({adm_row},{aw_row})/{c("n")},"")',
                    base.abar[i], "usd")
            crits = {"seg": f"({RESr}={c('residency')})*({SEGr}={c('segment')})*({UPr}={c('upper')})",
                     "res": f"({RESr}={c('residency')})*({UPr}={c('upper')})", "grp": f"({UPr}={c('upper')})"}
            for lvl in ("seg", "res", "grp"):
                a, e = sums[lvl][keys[lvl][i]]
                self.fx("Response", r, self.rcol[f"{lvl}_adm"], f"SUMPRODUCT({crits[lvl]}*{Nr})", a, "n1")
                self.fx("Response", r, self.rcol[f"{lvl}_enr"], f"SUMPRODUCT({crits[lvl]}*{Er})", e, "n1")
            self.fx("Response", r, self.rcol["all_adm"], f"SUM({Nr})", adm_tot.sum(), "n1")
            self.fx("Response", r, self.rcol["all_enr"], f"SUM({Er})", enr_tot.sum(), "n1")
            sa, se, ra, re_ = c("seg_adm"), c("seg_enr"), c("res_adm"), c("res_enr")
            ga, ge, aa, ae = c("grp_adm"), c("grp_enr"), c("all_adm"), c("all_enr")
            self.fx("Response", r, self.rcol["ypool"],
                    f"IF({sa}>=in_pooling_min_admits,{se}/{sa},IF({ra}>0,{re_}/{ra},IF({ga}>0,{ge}/{ga},{ae}/{aa})))",
                    base.ypool[i], "r4")
            lvl_name = {"segment": "segment", "residency": "residency", "group": "group", "all": "all"}
            self.fx("Response", r, self.rcol["pool_level"],
                    f'IF({sa}>=in_pooling_min_admits,"segment",IF({ra}>0,"residency",IF({ga}>0,"group","all")))',
                    lvl_name[base.pool_level[i]], "t")
            for k in CASES:
                f = (f"IF({c('n')}>0,({c('n')}*({c('ybar')}+in_slope_{k}/100*({c('a0')}-{c('abar')})/1000)"
                     f"+in_pooling_k*{c('ypool')})/({c('n')}+in_pooling_k),{c('ypool')})")
                self.fx("Response", r, self.rcol[f"y0_{k}"], f, base.y0[k][i], "r4")
            self.fx("Response", r, self.rcol["floor"],
                    f"IF({c('upper')}=1,in_yield_floor_upper,in_yield_floor_lower)", base.floor[i], "r4")
            self.fx("Response", r, self.rcol["cap"], f"IF({c('upper')}=1,in_yield_cap_upper,in_yield_cap_lower)",
                    base.cap[i], "r4")
            lo_terms = ",".join(f"IF({ref('History', hr, self.hcol['admits'] + j)}>0,"
                                f"{ref('History', hr, self.hcol['award'] + j)},{BIG})" for j in range(nc))
            hi_terms = ",".join(f"IF({ref('History', hr, self.hcol['admits'] + j)}>0,"
                                f"{ref('History', hr, self.hcol['award'] + j)},-{BIG})" for j in range(nc))
            self.fx("Response", r, self.rcol["award_lo"], f'IF({c("n")}=0,"",MIN({lo_terms}))', base.award_lo[i],
                    "usd")
            self.fx("Response", r, self.rcol["award_hi"], f'IF({c("n")}=0,"",MAX({hi_terms}))', base.award_hi[i],
                    "usd")
        # rung grid (display only)
        T = self.run.lcs[self.S[0].name]["middle"].tuition
        rungs = [float(x) for x in range(0, int(T), 5000)]
        self.rung0 = len(self.rkeys) + 1
        c = self.rung0
        self.txt("Response", self.r0r - 3, c, "Yield at award rungs (display only). Full-tuition rung = "
                                              "Baseline tuition in the plan year.", "hl")
        TB = self.LH("middle", self.S[0].name, "T")
        for k in CASES:
            self.txt("Response", self.r0r - 2, c, f"{CASE_TITLE[k]} case", "hl")
            for j, rg in enumerate(rungs + [T]):
                col = c + j
                if j < len(rungs):
                    self.val("Response", self.r0r - 1, col, rg, "usd")
                    rref = a1(self.r0r - 1, col)
                else:
                    self.fx("Response", self.r0r - 1, col, TB, T, "usd")
                    rref = a1(self.r0r - 1, col)
                vals = response.yield_at(base, np.full(n, rg), k)
                for i in range(n):
                    r = self.r0r + i
                    cc = lambda kk: a1(r, self.rcol[kk], False)  # noqa: E731
                    self.fx("Response", r, col, f"MIN({cc('cap')},MAX({cc('floor')},{cc('y0_' + k)}+in_slope_{k}/100*"
                                                f"({rref}-{cc('a0')})/1000))", vals[i], "r4")
            c += len(rungs) + 2
        ws.freeze_panes(self.r0r, 1)

    # ------------------------------------------------------------------------------------------------------------
    # Levers

    def w_levers(self):
        run, cells, cfg = self.run, self.cells, self.cfg
        ws = self.ws["Levers"]
        self.txt("Levers", 0, 0, "Levers: scenario inputs (Baseline is scenario 0)", "title")
        self.txt("Levers", 1, 0, "Blue: input. Italic blue: inherited from the parent by formula; type over it to "
                                 "override. Grey fill: differs from the parent. While full_tuition is 1 the award is "
                                 "tuition and award_usd is ignored: such an entry is struck through, marked in the note "
                                 "column, counted separately and listed on Checks.", "note")
        ws.set_column(0, 0, 44)
        ws.set_column(1, 4, 8)
        ws.set_column(5, 5, 2)
        ws.set_column(6, self.vmatrix + len(self.S), 11)
        # CP-1: the plain label from the dictionary in column A; the code name in grey beside it (column B)
        self.txt("Levers", self.vrow_name, 0, DD.label("IN-089"), "hl")
        self.txt("Levers", self.vrow_parent, 0, DD.label("IN-090"), "hl")
        self.txt("Levers", self.vrow_parent, 1, "parent", "setting")
        for f, rid_, _ in LEVER_FIELDS:
            self.txt("Levers", self.vfield_row[f], 0, DD.label(rid_))
            self.txt("Levers", self.vfield_row[f], 1, f, "setting")
        self.txt("Levers", self.vrow_awards_changed, 0, DD.label("OUT-132"))
        self.txt("Levers", self.vrow_rates_changed, 0, DD.label("OUT-133"))
        self.txt("Levers", self.vrow_cells_changed, 0, DD.label("OUT-134"))
        self.txt("Levers", self.vrow_ignored, 0, DD.label("OUT-135"))
        self._static_heads("Levers", self.vrow_colhead)
        for i in range(self.n):
            r = self.r0v + i
            self.val("Levers", r, 0, cells.cell_id[i], "datat")
            self.val("Levers", r, 1, cells.residency[i], "datat")
            self.val("Levers", r, 2, cells.segment[i] or SEG_NONE, "datat")
            s_ = cells.score_lo[i]
            self.val("Levers", r, 3, None if np.isnan(s_) else float(s_), "int")
            self.val("Levers", r, 4, cells.gpa_class[i], "datat")
        self.txt("Levers", self.vrow_colhead, 4, "gpa_class", "h")
        self.txt("Levers", self.vrow_colhead, 3, "score_lo", "h")
        self.txt("Levers", self.vrow_colhead, 5, "", "h")
        seg_names = [sg["name"] for sg in cfg["segments"]]
        # A blank segment cell means the default, the only configured segment [v0.6.2, P2-07]. Baseline shows it blank
        # unless the scenario file names a segment; children inherit it.
        seg_blank = len(seg_names) == 1 and not run.meta.get("baseline_segment_named", True)
        hist_award = rng("History", self.r0h, self.hcol["award"] + self.jbase, self.r0h + self.n - 1,
                         self.hcol["award"] + self.jbase)
        for j, s in enumerate(self.S):
            c0 = self.vblock[s.name]
            p = run.parents[s.name]
            ws.set_column(c0 + 3, c0 + 3, 34)
            self.txt("Levers", self.vrow_name, c0, s.name, "hl")
            self.txt("Levers", self.vrow_parent, c0, p.name if p else "(none)")
            for f, _, kind in LEVER_FIELDS:
                r = self.vfield_row[f]
                v = getattr(s, f)
                if kind == "int01":
                    v = int(bool(v))
                if f == "segment":
                    v = "" if (seg_blank and v == seg_names[0]) else (v or "")
                fmt_kind = ("text" if kind == "text" else "pct1" if f == "discount_target"
                            else "usd" if f == "bonus_pool_usd" else "num")
                if p is None:
                    if f == "tuition_increase_pct":
                        # [v0.6.3, BM-2] cumulative increase; a year with tuition_by_year_usd takes its dollar figure
                        self.fx("Levers", r, c0, f"({self.tuition_factor_x(s.plan_year)}-1)*100",
                                plan_increase_pct(cfg, s.plan_year), "inh_pp")
                    elif f in ("need_total", "class_target", "class_cap"):
                        src = {"need_total": "in_need_total", "class_target": "in_class_target",
                               "class_cap": "in_class_cap"}[f]
                        self.fx("Levers", r, c0, src, v, "inh_num")
                    elif f == "discount_target":
                        self.fx("Levers", r, c0, 'IF(in_discount_target="","",in_discount_target)', v, "inh_pct1")
                    else:
                        self.val("Levers", r, c0, v, "in_" + fmt_kind)
                else:
                    pv = getattr(p, f)
                    if kind == "int01":
                        pv = int(bool(pv))
                    if f == "segment":
                        pv = "" if (seg_blank and pv == seg_names[0]) else (pv or "")
                    pref = a1(r, self.vblock[p.name])
                    if v == pv or (v is None and pv is None):
                        frm = f'IF({pref}="","",{pref})' if kind in ("opt", "text") else pref
                        self.fx("Levers", r, c0, frm, v, "inh_" + fmt_kind)
                    else:
                        self.val("Levers", r, c0, v, "in_" + fmt_kind)
                if f == "bonus_scope":
                    ws.data_validation(r, c0, r, c0, {"validate": "list", "source": list(L.BONUS_SCOPES)})
                if f == "segment" and seg_names:
                    ws.data_validation(r, c0, r, c0, {"validate": "list", "source": seg_names, "ignore_blank": True})
                if kind == "int01":
                    ws.data_validation(r, c0, r, c0, {"validate": "list", "source": ["0", "1"]})
            for k, h in enumerate([DD.label("IN-112"), DD.label("IN-113"), DD.label("IN-114"), "note"]):
                self.txt("Levers", self.vrow_colhead, c0 + k, h, "h")
            changed, ignored = self.vals["award_changes"][s.name]
            arrs = [s.admit_rate, s.award_usd, s.full_tuition.astype(int)]
            fmts = ["r4", "usd", "int"]
            for i in range(self.n):
                r = self.r0v + i
                for k in range(3):
                    v = float(arrs[k][i]) if k < 2 else int(arrs[k][i])
                    if p is None:
                        self.val("Levers", r, c0 + k, v, "in_" + fmts[k])
                    else:
                        pv = [p.admit_rate, p.award_usd, p.full_tuition.astype(int)][k][i]
                        if (v == pv):
                            self.fx("Levers", r, c0 + k, a1(r, self.vblock[p.name] + k, False), v, "inh_" + fmts[k])
                        else:
                            self.val("Levers", r, c0 + k, v, "in_" + fmts[k])
            ws.data_validation(self.r0v, c0 + 2, self.r0v + self.n - 1, c0 + 2,
                               {"validate": "list", "source": ["0", "1"]})
            # Award entries ignored under the full-tuition flag [v0.6.2, P2-03]: struck through and marked in the note
            # column; counted separately, not as changes. The reference is the inherited award (the parent's; for
            # Baseline, the latest-cohort award on History).
            As, Fs = self.LVR(s.name, "award"), self.LVR(s.name, "ft")
            Aref = hist_award if p is None else self.LVR(p.name, "award")
            for i in range(self.n):
                r = self.r0v + i
                aref = (ref("History", self.r0h + i, self.hcol["award"] + self.jbase) if p is None
                        else a1(r, self.vblock[p.name] + 1, False))
                self.fx("Levers", r, c0 + 3, f'IF(({a1(r, c0 + 2, False)}=1)*({a1(r, c0 + 1, False)}<>{aref})=1,'
                                             f'{xs(labels.AWARD_IGNORED)},"")',
                        labels.AWARD_IGNORED if ignored[i] else "", "note")
            r0a = a1(self.r0v, c0 + 1, False)
            aref0 = (ref("History", self.r0h, self.hcol["award"] + self.jbase).replace("$", "") if p is None
                     else a1(self.r0v, self.vblock[p.name] + 1, False))
            ws.conditional_format(self.r0v, c0 + 1, self.r0v + self.n - 1, c0 + 1, {
                "type": "formula", "format": self.f["ignored"],
                "criteria": f"=({a1(self.r0v, c0 + 2, False)}=1)*({r0a}<>{aref0})"})
            self.fx("Levers", self.vrow_ignored, c0, f"SUMPRODUCT(({Fs}=1)*({As}<>{Aref}))", int(ignored.sum()), "int")
            if p is not None:
                pc = self.vblock[p.name]
                ws.conditional_format(self.r0v, c0, self.r0v + self.n - 1, c0 + 2, {
                    "type": "formula", "format": self.f["changed"],
                    "criteria": f"={a1(self.r0v, c0, False)}<>{a1(self.r0v, pc, False)}"})
                Rs, Rp = self.LVR(s.name, "rate"), self.LVR(p.name, "rate")
                Ap, Fp = self.LVR(p.name, "award"), self.LVR(p.name, "ft")
                aw_ch = int(changed.sum())
                rt_ch = int((s.admit_rate != p.admit_rate).sum())
                any_ch = int((changed | (s.admit_rate != p.admit_rate)).sum())
                aw_terms = f"({Fs}<>{Fp})+({As}<>{Ap})*({Fs}=0)"
                self.fx("Levers", self.vrow_awards_changed, c0, f"SUMPRODUCT((({aw_terms})>0)*1)", aw_ch, "int")
                self.fx("Levers", self.vrow_rates_changed, c0, f"SUMPRODUCT(({Rs}<>{Rp})*1)", rt_ch, "int")
                self.fx("Levers", self.vrow_cells_changed, c0, f"SUMPRODUCT((({Rs}<>{Rp})+{aw_terms}>0)*1)", any_ch,
                        "int")
            else:
                for rr in (self.vrow_awards_changed, self.vrow_rates_changed, self.vrow_cells_changed):
                    self.txt("Levers", rr, c0, "(no parent)", "note")
        # resolved award matrix (interface contract award_matrix)
        cm = self.vmatrix
        self.txt("Levers", self.vrow_colhead - 1, cm, DD.label("OUT-136"), "hl")
        for j, s in enumerate(self.S):
            self.txt("Levers", self.vrow_colhead, cm + j, s.name, "h")
            lc = run.lcs[s.name]["middle"]
            colL = self.lblock[("middle", s.name)]["award"]
            for i in range(self.n):
                self.fx("Levers", self.r0v + i, cm + j, ref("Ledger_Middle", self.r0l + i, colL), lc.award[i], "usd")
        self.name("AWARD_MATRIX", "Levers", self.r0v, cm, self.r0v + self.n - 1, cm + len(self.S) - 1)
        ws.freeze_panes(self.r0v, 1)

    # ------------------------------------------------------------------------------------------------------------
    # Reproduce (reproduce builds only; spec section 9)

    def w_reproduce(self):
        run, cells = self.run, self.cells
        ws = self.ws["Reproduce"]
        self.txt("Reproduce", 0, 0, "Reproduce: loaded values (reproduce build)", "title")
        self.txt("Reproduce", 1, 0, "Loaded from " + run.meta.get("data_source", "the fixture") + ". While the Inputs "
                 "mode is Reproduce, the Ledgers take each scenario's yield (all three cases) and tuition from here, as "
                 "entered: the response, the yield shift, the floor and the cap do not apply. Admit rates, awards and "
                 "the pool multiplier are scenario inputs on Levers; Checks compares Levers with the loaded values "
                 "below.", "note")
        ws.set_column(0, 0, 24)
        ws.set_column(1, 5, 9)
        heads = {"name": "Scenario", "parent": "parent (loaded lineage)", "pool_multiplier": "pool multiplier",
                 "tuition": "tuition (loaded, plan year)", "specialty_usd": "specialty_usd",
                 "need_total": "need_total"}
        for key, h in heads.items():
            self.txt("Reproduce", self.prow[key], 0, h, "hl")
        self.txt("Reproduce", self.prow["need_total"] + 1, 0, "source notes", "hl")
        nonrep = cells.meta.get("not_reproducible", [])
        rec = cells.meta.get("apps_recovered")
        self.txt("Reproduce", self.prow["need_total"] + 2, 0,
                 f"Cells not reproducible from the file: {len(nonrep)}"
                 + (" (" + "; ".join(d["cell"] for d in nonrep) + ")" if nonrep else "")
                 + "; excluded from the pass criteria, reasons in the reproduce report. Applications recovered from "
                 f"the scenario columns: {0 if rec is None else int(rec.sum())}.", "note")
        self._static_heads("Reproduce", self.pcolhead)
        self._cell_static("Reproduce", self.r0p)
        for s in self.S:
            c0 = self.pblock[s.name]
            ld = run.loaded[s.name]
            ws.set_column(c0, c0 + 2, 11)
            ws.set_column(c0 + 3, c0 + 3, 2)
            self.txt("Reproduce", self.prow["name"], c0, s.name, "hl")
            p = run.parents[s.name]
            self.txt("Reproduce", self.prow["parent"], c0, p.name if p else "(none)")
            self.val("Reproduce", self.prow["pool_multiplier"], c0, ld["pool_multiplier"], "in_num")
            self.val("Reproduce", self.prow["tuition"], c0, ld["tuition"], "in_usd")
            self.val("Reproduce", self.prow["specialty_usd"], c0, ld["specialty_usd"], "in_usd")
            self.val("Reproduce", self.prow["need_total"], c0, ld["need_total"], "in_usd")
            self.txt("Reproduce", self.prow["need_total"] + 1, c0, "; ".join(ld.get("sources", [])), "note")
            for kk, h in enumerate(["admit_rate", "award_usd", "yield"]):
                self.txt("Reproduce", self.pcolhead, c0 + kk, h, "h")
            for i in range(self.n):
                r = self.r0p + i
                self.val("Reproduce", r, c0, float(ld["admit_rate"][i]), "in_r4")
                self.val("Reproduce", r, c0 + 1, float(ld["award_usd"][i]), "in_usd")
                self.val("Reproduce", r, c0 + 2, float(ld["yield"][i]), "in_r4")
        ws.freeze_panes(self.r0p, 1)

    def PR(self, s, key):
        """Reproduce column range over cells: admit_rate, award_usd or yield."""
        c = self.pblock[s] + {"rate": 0, "award": 1, "yield": 2}[key]
        return rng("Reproduce", self.r0p, c, self.r0p + self.n - 1, c)

    # ------------------------------------------------------------------------------------------------------------
    # Ledger

    def w_ledger(self, k):
        sheet = CASE_SHEET[k]
        run, cells, cfg, base = self.run, self.cells, self.cfg, self.run.base
        ws = self.ws[sheet]
        n = self.n
        self.txt(sheet, 0, 0, f"Ledger, {CASE_TITLE[k]} price-response case (slope from Inputs: "
                              f"in_slope_{k}). " + labels.RESPONSE_LABEL, "title")
        self.txt(sheet, 1, 0, "Per cell and scenario: section 3 of the spec. Yield is the response formula in one "
                              "column: clip(clip(y0 + b/100 (award - a0)/1000, floor, cap) + shift/100, floor, "
                              "cap)." + (" Mode Reproduce: yield and tuition are the loaded values on the Reproduce "
                                         "sheet (no response, shift, floor or cap)." if self.repro else ""), "note")
        st = self.lstat
        heads = {"upper": "upper group (1/0)", "floor": "yield floor", "cap": "yield cap", "a0": "a0", "y0": f"y0 {k}",
                 "award_lo": "award low (observed)", "award_hi": "award high (observed)",
                 "apps_base": "applications (base cycle)"}
        for j, (meas, t) in enumerate(self.targets):
            heads[f"g{j}"] = f"median sign {'GPA' if meas == 'gpa' else 'score'} {t:g}"
        for j, (q, t) in enumerate(self.ptargets):
            heads[f"p{j}"] = f"percentile sign q {q:g}, t {t:g}"
        self._static_heads(sheet, self.r0l - 1)
        for key, h in heads.items():
            self.txt(sheet, self.r0l - 1, st[key], h, "h")
        ws.set_column(0, 0, 24)
        ws.set_column(1, len(st), 8)
        self._cell_static(sheet, self.r0l)
        upper = response.score_group_upper(cells, cfg).astype(int)
        signs = [risk.median_signs(cells, cfg, m, t) for m, t in self.targets]
        psigns = [risk.median_signs(cells, cfg, "score", t) for q, t in self.ptargets]
        med_refs = self.inp_list["median_thresholds"]
        for i in range(n):
            r = self.r0l + i
            c = lambda key: "$" + xl_col_to_name(st[key]) + str(r + 1)  # noqa: E731
            self.fx(sheet, r, st["upper"], self.Rc("upper", i), upper[i], "int")
            for j, (meas, t) in enumerate(self.targets):
                if meas == "score":
                    f = (f'IF({c("scored")}=0,IF(in_unscored_in_median="excluded",0,-1),'
                         f'IF({c("score_lo")}>={med_refs[j]},1,-1))')
                else:
                    f = (f'IF({c("gpa_class")}="hi",1,IF({c("gpa_class")}="lo",-1,'
                         f'IF(in_unscored_in_median="excluded",0,-1)))')
                self.fx(sheet, r, st[f"g{j}"], f, signs[j][i], "int")
            for j in range(len(self.ptargets)):
                fp = (f'IF({c("scored")}=0,IF(in_unscored_in_median="excluded",0,-1),'
                      f'IF({c("score_lo")}>={self.inp_list["pct_t"][j]},1,-1))')
                self.fx(sheet, r, st[f"p{j}"], fp, psigns[j][i], "int")
            self.fx(sheet, r, st["floor"], self.Rc("floor", i), base.floor[i], "r4")
            self.fx(sheet, r, st["cap"], self.Rc("cap", i), base.cap[i], "r4")
            self.fx(sheet, r, st["a0"], self.Rc("a0", i), base.a0[i], "usd")
            self.fx(sheet, r, st["y0"], self.Rc(f"y0_{k}", i), base.y0[k][i], "r4")
            self.fx(sheet, r, st["award_lo"], self.Rc("award_lo", i), base.award_lo[i], "usd")
            self.fx(sheet, r, st["award_hi"], self.Rc("award_hi", i), base.award_hi[i], "usd")
            self.fx(sheet, r, st["apps_base"], ref("History", self.r0h + i, self.hcol["apps"] + self.jbase),
                    cells.apps[i, self.jbase], "n1")
        self.txt(sheet, self.ltot, 0, "Total", "hl")
        for s in self.S:
            self._ledger_block(k, s)
        ws.freeze_panes(self.r0l, 1)

    def _apps_round(self, f):
        """Applications formula; in reproduce builds, whole applications while the mode is Reproduce and
        in_round_apps_after_pool is 1 (DECISIONS Nov 18)."""
        if not self.repro:
            return f
        return f'IF((in_mode="Reproduce")*(in_round_apps_after_pool=1)=1,ROUND({f},0),{f})'

    def _ledger_block(self, k, s):
        sheet = CASE_SHEET[k]
        run, cells, cfg = self.run, self.cells, self.cfg
        lc = run.lcs[s.name][k]
        col = self.lblock[(k, s.name)]
        c0 = col["in_seg"]
        st = self.lstat
        p_ = run.parents[s.name]
        self.txt(sheet, 2, c0, "Scenario", "hl")
        self.fx(sheet, 2, c0 + 1, ref("Levers", self.vrow_name, self.vblock[s.name]), s.name, "t")
        self.txt(sheet, 3, c0, "tuition")
        LVf = lambda f: self.LV(s.name, f)  # noqa: E731
        tf = (f"ROUND(in_tuition_base*(1+{LVf('tuition_increase_pct')}/100)/in_tuition_rounding_usd,0)"
              f"*in_tuition_rounding_usd")
        if self.repro:
            tf = f'IF(in_mode="Reproduce",{ref("Reproduce", self.prow["tuition"], self.pblock[s.name])},{tf})'
        self.fx(sheet, 3, c0 + 1, tf, lc.tuition, "usd")
        self.txt(sheet, 4, c0, "increase %")
        self.fx(sheet, 4, c0 + 1, LVf("tuition_increase_pct"), s.tuition_increase_pct, "pp")
        self.txt(sheet, 5, c0, "need rate")
        nt = LVf("need_total")
        # R4-07: need.total scales with class (the rate per enrollee); a scenario's need_total departure from need.total
        # is a fixed amount, in live and reproduce modes
        nrf = "in_need_total/in_need_reference_class"
        if self.repro:
            # spec section 0A item B5: reproduce mode takes the need rate rounded to whole dollars per enrollee
            nrf = f'IF(in_mode="Reproduce",ROUND(in_need_total/in_need_reference_class,0),{nrf})'
        self.txt(sheet, 5, c0 + 2, "need departure")
        self.fx(sheet, 5, c0 + 3, f'IF({nt}="",0,{nt}-in_need_total)', lc.need_lump, "usd")
        self.fx(sheet, 5, c0 + 1, nrf, lc.need_rate, "usd")
        self.txt(sheet, 6, c0, "segment")
        sg = LVf("segment")
        # blank: the only configured segment; none when no segment or several are configured [v0.6.2, P2-07]
        default = "INDEX(in_seg_names,1)" if len(cfg["segments"]) == 1 else '""'
        self.fx(sheet, 6, c0 + 1, f'IF({sg}="",{default},{sg})', L.active_segment(cfg, s) or "", "t")
        for key, cc in col.items():
            h = BLOCK_HEAD.get(key)
            if key.startswith("tw"):
                h = "award at T(p)"
            if key == "admits_pool1":
                h = "admits at pool multiplier 1"
            self.txt(sheet, self.r0l - 1, cc, h, "h")
        T = self.LH(k, s.name, "T")
        P = self.LH(k, s.name, "p")
        NR = self.LH(k, s.name, "need_rate")
        SEGN = self.LH(k, s.name, "seg")
        scope, bonus_usd = LVf("bonus_scope"), LVf("bonus_usd")
        tw_vals = []
        if k == "middle":
            grid = cfg["risk"]["tuition_grid"]
            for gi, pct in enumerate(grid):
                cc = col[f"tw{gi}"]
                Tp = scenario_tuition(cfg, pct)
                self.fx(sheet, 3, cc, f"ROUND(in_tuition_base*(1+{self.inp_list['tuition_grid'][gi]}/100)"
                                      f"/in_tuition_rounding_usd,0)*in_tuition_rounding_usd", Tp, "usd")
                self.fx(sheet, 4, cc, self.inp_list["tuition_grid"][gi], pct, "pp")
                tw_vals.append(L.resolve_awards(s, Tp, pct / 100.0, lc.eligible)[1])
            lc1 = L.evaluate(cells, cfg, replace(s, pool_multiplier=1.0), run.base, "middle")
        ev = response.evidence_labels(run.base, lc.award, cfg)
        for i in range(self.n):
            r = self.r0l + i
            S_ = lambda key: "$" + xl_col_to_name(st[key]) + str(r + 1)  # noqa: E731
            B = lambda key: a1(r, col[key], False)  # noqa: E731
            rate_c, aw_c, ft_c = self.LVc(s.name, "rate", i), self.LVc(s.name, "award", i), self.LVc(s.name, "ft", i)
            self.fx(sheet, r, col["in_seg"], f'IF({SEGN}="",0,IF({S_("segment")}={SEGN},1,0))', int(lc.in_segment[i]),
                    "int")
            elig = (f'IF({scope}="residency_out",IF({S_("residency")}="out",1,0),IF({scope}="segment",{B("in_seg")},0))'
                    f'*IF({LVf("bonus_min_score")}="",1,IF({S_("scored")}=1,IF({S_("score_lo")}>='
                    f'{LVf("bonus_min_score")},1,0),0))')
            self.fx(sheet, r, col["elig"], elig, int(lc.eligible[i]), "int")
            af = (f'{S_("apps_base")}*IF({S_("upper")}=1,{LVf("pool_multiplier")},1)*'
                  f'(1+{LVf("segment_pool_lift_pct")}/100*{B("in_seg")})')
            self.fx(sheet, r, col["apps"], self._apps_round(af), lc.apps[i], "n1")
            self.fx(sheet, r, col["rate"], rate_c, lc.rate[i], "r4")
            self.fx(sheet, r, col["admits"], f'IF(in_integer_admits=1,ROUND({B("apps")}*{B("rate")},0),'
                                             f'{B("apps")}*{B("rate")})', lc.admits[i], "n1")
            lever = f'IF({LVf("award_scale_with_tuition")}=1,{aw_c}*(1+{P}/100),{aw_c})'
            self.fx(sheet, r, col["award_base"], f"IF({ft_c}=1,{T},MIN({lever},{T}))", lc.award_base[i], "usd")
            self.fx(sheet, r, col["award"], f'MIN({B("award_base")}+{bonus_usd}*{B("elig")},{T})', lc.award[i], "usd")
            self.fx(sheet, r, col["incentive"], f'{B("award")}-{B("award_base")}', lc.incentive[i], "usd")
            sh = (f'IF({B("in_seg")}*({LVf("yield_shift_pts_segment")}<>"")=1,{LVf("yield_shift_pts_segment")},'
                  f'IF({S_("residency")}="in",IF({LVf("yield_shift_pts_in")}<>"",{LVf("yield_shift_pts_in")},'
                  f'{LVf("yield_shift_pts")}),IF({LVf("yield_shift_pts_out")}<>"",{LVf("yield_shift_pts_out")},'
                  f'{LVf("yield_shift_pts")})))')
            self.fx(sheet, r, col["shift"], sh, lc.shift[i], "pp")
            yf = (f'MIN({S_("cap")},MAX({S_("floor")},MIN({S_("cap")},MAX({S_("floor")},{S_("y0")}+in_slope_{k}/100*'
                  f'({B("award")}-{S_("a0")})/1000))+{B("shift")}/100))')
            if self.repro:
                yf = (f'IF(in_mode="Reproduce",{ref("Reproduce", self.r0p + i, self.pblock[s.name] + 2)},{yf})')
            self.fx(sheet, r, col["yield"], yf, lc.yld[i], "r4")
            evf = (f'IF({S_("award_lo")}="",{xs(labels.EVIDENCE_EXTRAPOLATED)},IF(({B("award")}>={S_("award_lo")}-'
                   f'in_evidence_tolerance_usd)*({B("award")}<={S_("award_hi")}+in_evidence_tolerance_usd)=1,'
                   f'{xs(labels.EVIDENCE_OBSERVED)},{xs(labels.EVIDENCE_EXTRAPOLATED)}))')
            self.fx(sheet, r, col["evidence"], evf, ev[i], "t")
            self.fx(sheet, r, col["mu"], f'{B("admits")}*{B("yield")}', lc.mu[i], "n1")
            self.fx(sheet, r, col["enrolled"], f'IF(in_integer_enrolled=1,ROUND({B("mu")},0),{B("mu")})',
                    lc.enrolled[i], "n1")
            self.fx(sheet, r, col["spend"], f'{B("enrolled")}*{B("award")}', lc.enrolled[i] * lc.award[i], "usd")
            self.fx(sheet, r, col["w"], f'{T}-{B("award")}-{NR}', lc.w[i], "usd")
            if k == "middle":
                for gi in range(len(cfg["risk"]["tuition_grid"])):
                    cc = col[f"tw{gi}"]
                    Tp = a1(3, cc)
                    gp = a1(4, cc)
                    lev = f'IF({LVf("award_scale_with_tuition")}=1,{aw_c}*(1+{gp}/100),{aw_c})'
                    self.fx(sheet, r, cc, f'MIN(IF({ft_c}=1,{Tp},MIN({lev},{Tp}))+{bonus_usd}*{B("elig")},{Tp})',
                            tw_vals[gi][i], "usd")
                a1f = self._apps_round(f'{S_("apps_base")}*(1+{LVf("segment_pool_lift_pct")}/100*{B("in_seg")})')
                self.fx(sheet, r, col["admits_pool1"],
                        f'IF(in_integer_admits=1,ROUND({a1f}*{B("rate")},0),{a1f}*{B("rate")})', lc1.admits[i], "n1")
        tot = {"apps": lc.apps.sum(), "admits": lc.admits.sum(), "mu": lc.mu.sum(), "enrolled": lc.enrolled.sum(),
               "spend": (lc.enrolled * lc.award).sum()}
        for key, v in tot.items():
            self.fx(sheet, self.ltot, col[key], f"SUM({self.LR(k, s.name, key)})", v, "n1" if key != "spend" else "usd")
        self.fx(sheet, self.ltot, col["incentive"],
                f"SUMPRODUCT({self.LR(k, s.name, 'enrolled')},{self.LR(k, s.name, 'incentive')})",
                (lc.enrolled * lc.incentive).sum(), "usd")

    # ------------------------------------------------------------------------------------------------------------
    # Trim

    def w_trim(self):
        run, cells, cfg = self.run, self.cells, self.cfg
        ws = self.ws["Trim"]
        n = self.n
        Ns = cfg["class"]["what_if"]
        self.txt("Trim", 0, 0, "Trim: shrink path (live mode), Middle case. " + labels.RESPONSE_LABEL + ". "
                 + labels.POLICY_UNSCORED_TRIMMED_FIRST,
                 "title")
        self.txt("Trim", 1, 0, "Left: cells in trim order (fixed at build from the first median threshold, "
                               "trim.protect_segment and, under above_floor, score.floor); rm_k = A y max(0, r - floor_rate) / r; removed_share_k(N) = "
                               "MIN(1, MAX(0, (M - N - R_(k-1)) / rm_k)). Right: per N, rate_k(N) = r - (r - floor_rate)"
                               " x removed_share, admits and a helper for the lowest band admitted, in Ledger order.",
                 "note")
        ws.set_column(0, 0, 6)
        ws.set_column(1, 1, 24)
        ws.set_column(2, self.tc_lc0 + 2 + 3 * len(Ns), 9)
        ws.set_column(self.tc_lc0, self.tc_lc0, 24)
        self.trim_info = {}
        for s in self.S:
            top = self.tblock[s.name]
            lc = run.lcs[s.name]["middle"]
            info = {"top": top}
            self.trim_info[s.name] = info
            self.txt("Trim", top, 0, f"Scenario: {s.name}", "sec")
            self.txt("Trim", top + 1, 1, "M (Middle expected class)")
            M = float(lc.mu.sum())
            self.fx("Trim", top + 1, 2, f"SUM({self.LR('middle', s.name, 'mu')})", M, "n1")
            info["M"] = ref("Trim", top + 1, 2)
            self.txt("Trim", top + 1, 4, "floor_rate")
            self.fx("Trim", top + 1, 5, "in_trim_floor_rate", cfg["trim"]["floor_rate"], "r4")
            fr = ref("Trim", top + 1, 5)
            hr = top + 3
            d0 = top + 4
            for c, h in enumerate(["k", "cell_id", "Ledger row", "r", "A", "y", "exempt", "rm_k", "R_(k-1)", "R_k"]):
                self.txt("Trim", hr, c, h, "h")
            trs = [trim.trim_rates(lc, N) for N in Ns]
            order = trs[0]["order"]
            pos = np.empty(n, int)
            pos[order] = np.arange(n)
            exempt = np.isin(cells.cell_id, list(cfg["trim"]["exempt_cells"])).astype(int)
            rm_o = trs[0]["rm"][order]
            R_o = trs[0]["R"]
            Rprev = R_o - rm_o
            ratec = self.lblock[("middle", s.name)]["rate"]
            admc = self.lblock[("middle", s.name)]["admits"]
            yc = self.lblock[("middle", s.name)]["yield"]
            Lrng = lambda cc: rng("Ledger_Middle", self.r0l, cc, self.r0l + n - 1, cc)  # noqa: E731
            for q in range(n):
                r = d0 + q
                i = order[q]
                self.val("Trim", r, 0, q + 1, "int")
                self.val("Trim", r, 1, cells.cell_id[i], "datat")
                self.val("Trim", r, 2, i + 1, "int")
                C = lambda c: a1(r, c, False)  # noqa: E731
                self.fx("Trim", r, 3, f"INDEX({Lrng(ratec)},{C(2)})", lc.rate[i], "r4")
                self.fx("Trim", r, 4, f"INDEX({Lrng(admc)},{C(2)})", lc.admits[i], "n1")
                self.fx("Trim", r, 5, f"INDEX({Lrng(yc)},{C(2)})", lc.yld[i], "r4")
                self.val("Trim", r, 6, int(exempt[i]), "int")
                self.fx("Trim", r, 7, f"IF(({C(6)}=0)*({C(3)}>0)=1,{C(4)}*{C(5)}*MAX(0,{C(3)}-{fr})/{C(3)},0)",
                        rm_o[q], "r4")
                self.fx("Trim", r, 8, "0" if q == 0 else a1(r - 1, 9, False), Rprev[q], "r4")
                self.fx("Trim", r, 9, f"{C(8)}+{C(7)}", R_o[q], "r4")
                for g, N in enumerate(Ns):
                    cc = self.tc_share0 + g
                    Nref = a1(hr - 1, cc)
                    self.fx("Trim", r, cc, f"IF({C(7)}=0,0,MIN(1,MAX(0,({info['M']}-{Nref}-{C(8)})/{C(7)})))",
                            trs[g]["removed_share"][i], "r4")
            info["RK"] = ref("Trim", d0 + n - 1, 9)
            self.txt("Trim", top + 1, 7, "R_K")
            self.fx("Trim", top + 1, 8, info["RK"], float(R_o[-1]) if n else 0.0, "r4")
            info["RK"] = ref("Trim", top + 1, 8)
            self.txt("Trim", hr - 1, self.tc_share0 - 1, "N:", "hl")
            for g, N in enumerate(Ns):
                cc = self.tc_share0 + g
                self.fx("Trim", hr - 1, cc, self.inp_list["class_what_if"][g], N, "n0")
                self.txt("Trim", hr, cc, "removed share", "h")
            # ledger-order area
            lc0 = self.tc_lc0
            self.txt("Trim", hr, lc0, "cell_id (Ledger order)", "h")
            self.txt("Trim", hr, lc0 + 1, "trim position", "h")
            appc = self.lblock[("middle", s.name)]["apps"]
            info["rate"], info["admits"], info["low"] = {}, {}, {}
            for g, N in enumerate(Ns):
                cc = lc0 + 2 + 3 * g
                self.fx("Trim", hr - 1, cc, self.inp_list["class_what_if"][g], N, "n0")
                for k_, h in enumerate(["rate(N)", "admits(N)", "low band helper"]):
                    self.txt("Trim", hr, cc + k_, h, "h")
                info["rate"][g] = rng("Trim", d0, cc, d0 + n - 1, cc)
                info["admits"][g] = rng("Trim", d0, cc + 1, d0 + n - 1, cc + 1)
                info["low"][g] = rng("Trim", d0, cc + 2, d0 + n - 1, cc + 2)
            sc_c, scd_c = self.lstat["score_lo"], self.lstat["scored"]
            for i in range(n):
                r = d0 + i
                self.val("Trim", r, lc0, cells.cell_id[i], "datat")
                self.val("Trim", r, lc0 + 1, int(pos[i]) + 1, "int")
                rL = ref("Ledger_Middle", self.r0l + i, ratec)
                aL = ref("Ledger_Middle", self.r0l + i, appc)
                for g, N in enumerate(Ns):
                    cc = lc0 + 2 + 3 * g
                    share_col = rng("Trim", d0, self.tc_share0 + g, d0 + n - 1, self.tc_share0 + g)
                    rate_v = trs[g]["rates"][i]
                    self.fx("Trim", r, cc, f"{rL}-({rL}-{fr})*INDEX({share_col},{a1(r, lc0 + 1, False)})", rate_v,
                            "r4")
                    adm_v = lc.apps[i] * rate_v
                    self.fx("Trim", r, cc + 1, f"{aL}*{a1(r, cc, False)}", adm_v, "n1")
                    scored = not np.isnan(cells.score_lo[i])
                    low_v = float(cells.score_lo[i]) if (adm_v > 0 and scored) else 1e99
                    self.fx("Trim", r, cc + 2,
                            f"IF(({a1(r, cc + 1, False)}>0)*({ref('Ledger_Middle', self.r0l + i, scd_c)}=1)=1,"
                            f"{ref('Ledger_Middle', self.r0l + i, sc_c)},{BIG})", low_v, "num")
            info["trs"] = trs
        ws.freeze_panes(3, 2)

    # ------------------------------------------------------------------------------------------------------------
    # Summary formula generators (scenario s, case k)

    def g(self, k, s):
        """Ranges and scalars for scenario s in case k."""
        R = lambda key: self.LR(k, s, key)  # noqa: E731
        d = {key: R(key) for key in BLOCK}
        d.update({f"g{j}": self.LSR(k, f"g{j}") for j in range(len(self.targets))})
        d.update({f"p{j}": self.LSR(k, f"p{j}") for j in range(len(self.ptargets))})
        for key in ("scored", "score_lo", "upper", "residency", "floor", "cap", "gpa_class"):
            d[key] = self.LSR(k, key)
        d["T"], d["NR"] = self.LH(k, s, "T"), self.LH(k, s, "need_rate")
        d["SPEC"], d["CAP"], d["TGT"] = self.LV(s, "specialty_usd"), self.LV(s, "class_cap"), self.LV(s, "class_target")
        d["GOAL"] = self.LV(s, "segment_goal")
        # K: the constant subtracted from sum w e for ntr_y1: specialty plus the need departure (spec section 0A item
        # B5; R4-07, live and reproduce). NL: that departure.
        d["NL"] = self.LH(k, s, "need_lump")
        d["K"] = f"({d['SPEC']}+{d['NL']})"
        return d

    def fm(self, name, k, s, t_index=None):
        """Formula for a contract metric (or a supporting figure) for scenario s, case k."""
        d = self.g(k, s)
        A, Y, MU, E, AW = d["admits"], d["yield"], d["mu"], d["enrolled"], d["award"]
        sd, rho = "in_common_shock_sd", "in_shock_corr"
        M = f"SUM({MU})"
        V = f"(SUMPRODUCT({A},{Y},1-{Y})+{sd}^2*{M}^2)"
        SDV = f"SQRT(MAX({V},1E-300))"
        cls = f"SUM({E})"
        merit = f"SUM({d['spend']})"
        need = f"{d['NR']}*{cls}+{d['NL']}"
        gross = f"{cls}*{d['T']}"
        aid = f"({merit}+{d['NR']}*{cls}+{d['K']})"
        SW = f"SUMPRODUCT({d['w']},{MU})"
        VN = f"(SUMPRODUCT({d['w']},{d['w']},{A},{Y},1-{Y})+{sd}^2*{SW}^2)"
        SEG = d["in_seg"]
        noseg = f"SUM({SEG})=0"
        MS = f"SUMPRODUCT({SEG},{MU})"
        VS = f"(SUMPRODUCT({SEG},{A},{Y},1-{Y})+{sd}^2*{MS}^2)"
        NS = xs(labels.NO_SEGMENT_CELLS)
        if name == "class_mean":
            return M
        if name == "class_lo90":
            return f"MAX(0,{M}-1.645*SQRT(MAX({V},0)))"
        if name == "class_hi90":
            return f"{M}+1.645*SQRT(MAX({V},0))"
        if name == "p_class_over_cap":
            return f"1-NORMSDIST(({d['CAP']}+0.5-{M})/{SDV})"
        if name == "p_class_in_band":
            return (f"NORMSDIST(({d['TGT']}+in_class_band+0.5-{M})/{SDV})-NORMSDIST(({d['TGT']}-in_class_band-0.5-{M})"
                    f"/{SDV})")
        if name == "unscored_count":
            return f"SUMPRODUCT(({d['scored']}=0)*{E})"
        if name == "gross_y1":
            return gross
        if name == "merit":
            return merit
        if name == "need":
            return need
        if name == "specialty":
            return d["SPEC"]
        if name == "aid":
            return aid
        if name == "ntr_y1":
            return f"{gross}-{aid}"
        if name == "discount_entering_y1":
            return f"IF({gross}>0,{aid}/({gross}),0)"
        if name == "avg_aid":
            return f"IF({cls}>0,{aid}/{cls},0)"
        if name in ("p_ntr_y1_ge_target", "p_jd_ntr_ge_goal"):
            # [v0.6.3, BM-4] the effective target: ntr_target - continuing_ntr_usd under all_jd. P(continuing + ntr_y1
            # >= ntr_target) is the same event; it shows only under all_jd
            f = (f'IF(in_ntr_target_eff="","",1-NORMSDIST((in_ntr_target_eff-({SW}-{d["K"]}))/'
                 f"MAX(SQRT(MAX({VN},0)),1E-300)))")
            return f if name == "p_ntr_y1_ge_target" else f'IF(in_ntr_goal_basis="all_jd",{f},"")'
        if name == "jd_ntr":
            return (f'IF(in_ntr_goal_basis="all_jd",in_continuing_ntr_usd+{gross}-{aid},'
                    f'{xs(labels.NOT_USED_ENTERING)})')
        if name == "ntr_lo90":
            return f"{SW}-{d['K']}-1.645*SQRT(MAX({VN},0))"
        if name == "ntr_hi90":
            return f"{SW}-{d['K']}+1.645*SQRT(MAX({VN},0))"
        if name == "full_tuition_n":
            return f"SUMPRODUCT(({AW}>={d['T']}-0.000001)*{E})"
        if name == "no_merit_award_n":
            return f"SUMPRODUCT(({AW}<=0.000000001)*{E})"
        if name == "barbell":
            return (f"IF({cls}>0,(SUMPRODUCT(({AW}>={d['T']}-0.000001)*{E})+SUMPRODUCT(({AW}<=0.000000001)*{E}))"
                    f"/{cls},0)")
        if name == "evidence_extrapolated_share":
            return f'IF({M}>0,SUMPRODUCT(({d["evidence"]}={xs(labels.EVIDENCE_EXTRAPOLATED)})*{MU})/{M},0)'
        if name == "segment_enrolled":
            return f"IF({noseg},{NS},SUMPRODUCT({SEG},{E}))"
        if name == "segment_lo90":
            return f"IF({noseg},{NS},MAX(0,{MS}-1.645*SQRT(MAX({VS},0))))"
        if name == "segment_hi90":
            return f"IF({noseg},{NS},{MS}+1.645*SQRT(MAX({VS},0)))"
        if name == "p_segment_goal":
            gl = d["GOAL"]
            return (f'IF({noseg},{NS},IF({gl}="","",1-NORMSDIST(({ceil_x(gl)}-0.5-{MS})/'
                    f"SQRT(MAX({VS},1E-300)))))")
        if name == "segment_share":
            return f"IF({noseg},{NS},IF({cls}>0,SUMPRODUCT({SEG},{E})/{cls},0))"
        if name == "segment_apps":
            return f"IF({noseg},{NS},SUMPRODUCT({SEG},{d['apps']}))"
        if name == "segment_admits":
            return f"IF({noseg},{NS},SUMPRODUCT({SEG},{A}))"
        if name == "segment_merit":
            return f"IF({noseg},{NS},SUMPRODUCT({SEG},{E},{AW}))"
        if name == "segment_goal":
            gl = d["GOAL"]
            return f'IF({noseg},{NS},IF({gl}="","",{ceil_x(gl)}))'
        if name == "segment_approximate":
            return f'IF({noseg},{NS},IF({MS}<{L.SEGMENT_APPROX_BELOW},{xs(labels.SEGMENT_APPROX)},""))'
        if name == "segment_v":
            return f"IF({noseg},{NS},{VS})"
        if name == "incentive_cost":
            return f"SUMPRODUCT(({d['incentive']}>0)*{E}*{d['incentive']})"
        # incentive against the parent
        p = self.run.parents[s]
        if name in K.PARENT_ONLY | {"merit_change", "ntr_change", "aid_per_additional_kind", "incentive_cells"}:
            if p is None:
                return '""'
            dp = self.g(k, p.name)
            I = d["incentive"]
            Es, Ep = E, dp["enrolled"]
            dE = f"SUMPRODUCT(({I}>0)*({Es}-{Ep}))"
            dS = f"SUMPRODUCT(({I}>0)*({Es}*{AW}-{Ep}*{dp['award']}))"
            dN = f"SUMPRODUCT(({I}>0)*({Es}*{d['w']}-{Ep}*{dp['w']}))"
            C = f"SUMPRODUCT(({I}>0)*{Es}*{I})"
            Ca = f"SUMPRODUCT(({I}>0)*(({Ep}<={Es})*{Ep}+({Ep}>{Es})*{Es})*{I})"
            UH = xs(labels.UNDER_HALF)
            if name == "incentive_paid_anyway":
                return Ca
            if name == "incentive_paid_anyway_share":
                return f"IF({C}>0,{Ca}/{C},0)"
            if name == "additional_enrollees":
                return dE
            if name == "merit_change":
                return dS
            if name == "ntr_change":
                return dN
            if name == "incentive_cells":
                return f"SUMPRODUCT(({I}>0)*1)"
            if name == "aid_per_additional":
                return f"IF({dE}>=0.5,{dS}/{dE},IF({dE}<=-0.5,{dS}/{dE},{UH}))"
            if name == "ntr_per_additional":
                return f"IF({dE}>=0.5,{dN}/{dE},IF({dE}<=-0.5,{dN}/{dE},{UH}))"
            if name == "aid_per_additional_kind":
                return (f"IF({dE}>=0.5,{xs(labels.AID_PER_ADDITIONAL)},IF({dE}<=-0.5,{xs(labels.SAVINGS_PER_LOST)},"
                        f"{UH}))")
            if name == "incentive_valid":
                eqs = "*".join(f"({self.LH('middle', s, 'seg')}={self.LH('middle', p.name, 'seg')})" if f == "segment"
                               else f"({self.LV(s, f)}={self.LV(p.name, f)})" for f in L.VALIDITY_FIELDS)
                arr = "+".join(f"({self.LVR(s, key)}<>{self.LVR(p.name, key)})" for key in ("rate", "award", "ft"))
                return (f"IF({eqs}*(SUMPRODUCT(({arr}>0)*1)=0)=1,{xs(labels.INCENTIVE_VALID)},"
                        f"{xs(labels.INCENTIVE_NOT_VALID)})")
        # medians
        if name in ("margin_t", "p_median_t", "p_median_t_rho05"):
            G = d[f"g{t_index}"]
            if name == "margin_t":
                return f"SUMPRODUCT({G},{E})"
            r_ = rho if name == "p_median_t" else "0.5"
            gp, gm = f"SUMPRODUCT(({G}=1)*{MU})", f"SUMPRODUCT(({G}=-1)*{MU})"
            vm = f"(SUMPRODUCT(({G}<>0)*{A}*{Y}*(1-{Y}))+{sd}^2*({gp}^2+{gm}^2-2*{r_}*{gp}*{gm}))"
            return f"1-NORMSDIST((-0.5-({gp}-{gm}))/SQRT(MAX({vm},1E-300)))"
        if name in ("margin_q_t", "p_pct_q_t", "p_pct_q_t_rho05", "pct_expected_below", "pct_approximate"):
            # [v0.6.3, BM-1] percentile target t_index: weights q at or above t, -(1 - q) below
            G = d[f"p{t_index}"]
            q, cr = self.inp_list["pct_q"][t_index], self.inp_list["pct_corr"][t_index]
            gp, gm = f"SUMPRODUCT(({G}=1)*{MU})", f"SUMPRODUCT(({G}=-1)*{MU})"
            if name == "margin_q_t":
                return f"{q}*SUMPRODUCT(({G}=1)*{E})-(1-{q})*SUMPRODUCT(({G}=-1)*{E})"
            if name == "pct_expected_below":
                return gm
            if name == "pct_approximate":
                return f'IF({gm}<{risk.PCT_APPROX_BELOW},{xs(labels.PCT_APPROX_LABEL)},"")'
            r_ = rho if name == "p_pct_q_t" else "0.5"
            vq = (f"({q}^2*SUMPRODUCT(({G}=1)*{A}*{Y}*(1-{Y}))+(1-{q})^2*SUMPRODUCT(({G}=-1)*{A}*{Y}*(1-{Y}))"
                  f"+{sd}^2*({q}^2*{gp}^2+(1-{q})^2*{gm}^2-2*{r_}*{q}*(1-{q})*{gp}*{gm}))")
            return f"1-NORMSDIST((-{cr}-({q}*{gp}-(1-{q})*{gm}))/SQRT(MAX({vq},1E-300)))"
        if name == "share_at_or_above_t":
            t = self.score_ts[t_index]
            es = f"SUMPRODUCT(({d['scored']}=1)*{E})"
            return f"IF({es}>0,SUMPRODUCT(({d['scored']}=1)*({d['score_lo']}>={t})*{E})/{es},0)"
        if name == "enrolled_at_or_above":
            t = self.score_ts[t_index]
            return f"SUMPRODUCT(({d['scored']}=1)*({d['score_lo']}>={t})*{E})"
        if name == "enrolled_below_floor":
            return f"SUMPRODUCT(({d['scored']}=1)*({d['score_lo']}<in_score_floor)*{E})"
        if name == "enrolled_gpa_hi":
            return f'SUMPRODUCT(({d["gpa_class"]}="hi")*{E})'
        if name == "gpa_blank_count":
            return f'SUMPRODUCT(({d["gpa_class"]}="blank")*{E})'
        if name in ("apps_total", "admits_total"):
            return f"SUM({d['apps' if name == 'apps_total' else 'admits']})"
        if name in ("apps_in", "apps_out", "admits_in", "admits_out"):
            col = d["apps"] if name.startswith("apps") else A
            return f'SUMPRODUCT(({d["residency"]}="{name.split("_")[1]}")*{col})'
        raise KeyError(name)

    def pv(self, name, k, s, t_index=None):
        """Python value for fm(name, ...)."""
        v = self.vals["sk"][(s, k)]
        kp = v["kpis"]
        if name in ("margin_t", "p_median_t", "p_median_t_rho05"):
            return v["median"][self.targets[t_index]][name]
        if name in ("margin_q_t", "p_pct_q_t", "p_pct_q_t_rho05"):
            return v["pct"][self.ptargets[t_index]][name]
        if name == "pct_expected_below":
            return v["pct"][self.ptargets[t_index]]["expected_below"]
        if name == "pct_approximate":
            return v["pct"][self.ptargets[t_index]]["approximate"]
        if name == "share_at_or_above_t":
            return kp["share_at_or_above_t"][self.score_ts[t_index]]
        if name == "enrolled_at_or_above":
            return kp["enrolled_at_or_above"][self.score_ts[t_index]]
        if name in kp and name not in v:
            return kp[name]
        if name == "incentive_cells":
            if self.run.parents[s] is None:
                return None
            return int((self.run.lcs[s][k].incentive > 0).sum())
        if name == "segment_v":
            lc = self.run.lcs[s][k]
            return L.segment(lc)["segment_v"]
        return v[name]

    # ------------------------------------------------------------------------------------------------------------
    # Summary

    def w_summary(self, dry):
        """Summary (spec v0.6.4 section 0B, CP-3): sections A class size, B revenue and aid, C academic profile, D
        priority segment, E incentive, F what-if tables, G award distribution, then the scenarios in words, H technical
        detail, Definitions and Notes on method. Every label, its section, order and tier come from the dictionary
        (sw/dictionary.py); within a section headline rows come first, then standard rows; technical rows move to H.
        Below the print area: the interface-contract ranges and the pool strip's working values."""
        self.dry = dry
        self.sr = 0
        if not dry:
            ws = self.ws["Summary"]
            ws.set_column(0, 0, 46)
            ws.set_column(1, 1, 10)
            ws.set_column(2, 40, 14)
            self.srow_dry = dict(self.srow)
        else:
            self.cpos = {}
            self.pool_parts = {}
            self.srow_dry = {}
        self.srow = {}                 # (row id, instance) -> (Summary row, format, held)
        self.queue = []
        self.h_rows = []               # technical rows waiting for section H
        self.printed = []              # (section, row id, label) in print order, for Definitions
        self.strip_pos = {}
        self.sum_maxc = 1 + max(len(self.S), 8)
        S = [s.name for s in self.S]
        self.sw_head()
        for sec in "ABCDEFG":
            getattr(self, f"sec_{sec}")(S)
        self.sw_narratives(S)
        self.sec_H(S)
        self.sw_definitions()
        self.sw_notes()
        # R4-01, Phase 4.2: the contract ranges and the working values below are outside the print area
        r_print, c_print = self.sr, self.sum_maxc
        self.sw_contract(S)
        self.sw_pool_parts(S)
        if not dry:
            ws = self.ws["Summary"]
            ws.freeze_panes(4, 2)
            ws.print_area(0, 0, r_print - 1, c_print)
            ws.repeat_columns(0, 1)
            self.summary_print_rows = r_print

    # writing helpers that respect the dry pass
    def s_txt(self, r, c, t, fmt="t"):
        if not self.dry:
            self.txt("Summary", r, c, t, fmt)
            self.sum_maxc = max(self.sum_maxc, c)

    def s_fx(self, r, c, f, v, fmt="num"):
        if not self.dry:
            self.fx("Summary", r, c, f, v, fmt)
            self.sum_maxc = max(self.sum_maxc, c)

    def s_name(self, nm, r0, c0, r1, c1):
        if not self.dry:
            self.name(nm, "Summary", r0, c0, r1, c1)

    def s_note(self, text, r=None):
        """A note row merged across the scenario columns, wrapped, with a height that fits the text."""
        r = self.sr if r is None else r
        if not self.dry:
            last = 1 + max(len(self.S), 6)
            ws = self.ws["Summary"]
            ws.merge_range(r, 0, r, last, text, self.f["notew"])
            ws.set_row(r, 12 * max(1, math.ceil(len(text) / 150)))
        if r == self.sr:
            self.sr += 1

    def lab_note(self, shock=True):
        """Section note with the section 4 labels that apply to every figure in the section [Phase 4, test 7]:
        RESPONSE_LABEL, and SHOCK_LABEL for sections with probabilities or ranges (shown while the year-to-year
        variation is illustrative; the Summary header row carries the live form)."""
        t = labels.RESPONSE_LABEL + "."
        if shock:
            t += (" Chances and likely ranges: " + labels.shock_label(self.cfg["risk"]["common_shock_sd"])
                  + " (while it is illustrative).")
        return t

    def s_sec(self, title, note=None):
        self.sr += 1
        self.s_txt(self.sr, 0, title, "sec")
        if not self.dry:                     # Phase 4.2: the grey fill runs across the section, not column A only
            for c in range(1, 2 + max(len(self.S), 6)):
                self.ws["Summary"].write_blank(self.sr, c, None, self.f["sec"])
        self.sr += 1
        if note:
            self.s_note(note)

    def s_scen_head(self, S, label="figure", case_label=""):
        self.s_txt(self.sr, 0, label, "h")
        self.s_txt(self.sr, 1, case_label, "h")
        for j, s in enumerate(S):
            self.s_txt(self.sr, 2 + j, s, "h")
        if not self.dry:
            self.ws["Summary"].set_row(self.sr, 48)
        self.sr += 1

    def cref(self, name, k, s, t=None):
        """Reference to a contract cell (registered in the dry pass)."""
        return a1(*self.cpos[(name, k, s, t)])

    def sref(self, name, k, s, t=None):
        """Sheet-qualified reference to a contract cell, for formulas on other sheets."""
        return ref("Summary", *self.cpos[(name, k, s, t)])

    def sw_head(self):
        bid = self.run.meta.get("build_id", "")
        self.s_txt(0, 0, "Summary: scenario evaluator (scores the scenarios written on Levers; recommends nothing)",
                   "title")
        mode_txt = (" Mode: Reproduce (yields and tuition from the Reproduce sheet while the Inputs mode is Reproduce)."
                    if self.repro else "")
        self.s_note(f"Build {bid}; data: {self.run.meta.get('data_source', '')}.{mode_txt} Figures are the middle "
                    f"case unless a row says otherwise. {labels.RANGE_OUTCOME}: {labels.RANGE_OUTCOME_NOTE}. "
                    f"{labels.RANGE_CASES}: {labels.RANGE_CASES_NOTE}; their rows read 'if admitted students respond "
                    "less (more) to aid'. The two kinds are never combined. Definitions and notes on method follow "
                    "the tables.", r=1)
        r = 2
        sh = labels.shock_label(self.cfg["risk"]["common_shock_sd"]) \
            if self.cfg["risk"]["shock_source"] == "illustrative" else ""
        self.s_txt(r, 0, labels.RESPONSE_LABEL, "hl")
        if not self.dry:                     # Phase 4.2: merged across the scenario columns, so the label is not cut
            self.ws["Summary"].merge_range(r, 2, r, 1 + max(len(self.S), 6), "", self.f["t"])
        self.s_fx(r, 2, f'IF(in_shock_source="illustrative",{NAR.template_formula(labels.SHOCK_LABEL, {"s": "in_common_shock_sd"})},"")',
                  sh, "t")
        self.sr = 3

    # ---- row queue (CP-3): rows are queued with their dictionary id and written sorted by tier and order ----------

    def add(self, rid, write, inst=0, **kw):
        """Queue a row of the current section: write(label) writes it at self.sr. kw fills the label's template."""
        self.queue.append((rid, inst, DD.label(rid, **kw), write))

    def flush(self, sec):
        """Write the queued rows: headline, then standard, in dictionary order; technical rows wait for section H."""
        for rid, inst, lab, write in sorted(self.queue, key=lambda x: DD.sort_key(x[0], x[1])):
            if DD.tier(rid) == "technical" and sec != "H":
                self.h_rows.append((sec, rid, inst, lab, write))
                continue
            self._emit(sec, rid, inst, lab, write)
        self.queue = []

    def _emit(self, sec, rid, inst, lab, write):
        self._cur = (rid, inst)
        self.printed.append((sec, rid, lab))
        write(lab)
        if (rid, inst) in self.srow:
            self.srow[(rid, inst)] = self.srow[(rid, inst)][:3] + (lab,)
        self._cur = None

    def q_cref(self, rid, name, fmt, k="middle", ti=None, inst=0, **kw):
        """Queue a row reading contract figure `name` (threshold index ti); kw fills the label's template."""
        self.add(rid, lambda lab: self._cref_row(self.Sn, lab, "", name, fmt, k, ti), inst, **kw)

    def q_direct(self, rid, name, fmt, k="middle", ti=None, inst=0, **kw):
        self.add(rid, lambda lab: self._direct_row(self.Sn, lab, "", name, fmt, k, ti), inst, **kw)

    def q_row(self, rid, gen, fmt, held=False, merge=True, inst=0, **kw):
        self.add(rid, lambda lab: self._row(self.Sn, lab, "", gen, fmt, held, merge), inst, **kw)

    def q_case(self, rid, name, fmt, k, ti=None, inst=0, **kw):
        """A Low or High price-response row (CP-2: 'if admitted students respond less (more) to aid')."""
        def write(lab):
            self.s_label(self.sr, lab)
            if self._held(name, ti):
                self.s_hold_cells(self.sr, 2, len(self.Sn))
            else:
                for j, s in enumerate(self.Sn):
                    if not self.dry:
                        self.s_fx(self.sr, 2 + j, self.cref(name, k, s, ti), self.pv(name, k, s, ti), fmt)
            self._mark(fmt, self._held(name, ti))
            self.sr += 1
        self.add(rid, write, inst, **kw)

    def q_selected(self, rid, nm, fmt, ti=None, **kw):
        """A row of the case chosen on Inputs (technical; section H)."""
        sel = 'IF(in_case_selector="Low",1,IF(in_case_selector="High",3,2))'

        def write(lab):
            self.s_label(self.sr, lab)
            self.s_fx(self.sr, 1, "in_case_selector", "Middle", "t")
            held = self._held(nm, ti)
            if held:
                self.s_hold_cells(self.sr, 2, len(self.Sn))
            else:
                for j, s in enumerate(self.Sn):
                    if self.dry:
                        continue
                    base_row, col = self.cpos[(nm, "low", s, ti)]
                    rr = rng("Summary", base_row, col, base_row + 2, col)
                    self.s_fx(self.sr, 2 + j, f"INDEX({rr},{sel})", self.pv(nm, "middle", s, ti), fmt)
            self._mark(fmt, held)
            self.sr += 1
        self.add(rid, write, 0, **kw)

    def _mark(self, fmt, held):
        if getattr(self, "_cur", None) is not None:
            self.srow[self._cur] = (self.sr, fmt, held)

    def s_height(self, r, h):
        """Summary row height: the largest requested (R4-02)."""
        if self.dry:
            return
        self.row_h[r] = max(self.row_h.get(r, 0), h)
        self.ws["Summary"].set_row(r, self.row_h[r])

    def s_label(self, r, label, fmt="lw"):
        """Column-A label, wrapped within column A (46 wide) with a row height that fits it (R4-02)."""
        self.s_txt(r, 0, label, fmt)
        if label and len(label) > LABEL_CHARS:
            self.s_height(r, 12 * math.ceil(len(label) / LABEL_CHARS))

    def s_hold_cells(self, r, c0, n, merge=True):
        """R4-06: labels.HOLD_POSITION in place of the figures in columns c0 .. c0 + n - 1: one merged cell for a
        display row, or every cell (merge=False) for a contract range, wrapped."""
        if self.dry or n <= 0:
            return
        ws = self.ws["Summary"]
        if merge and n > 1:
            ws.merge_range(r, c0, r, c0 + n - 1, labels.HOLD_POSITION, self.f["hold"])
            per_line = int(SCEN_CHARS * n)
        else:
            for c in range(c0, c0 + n):
                ws.write_string(r, c, labels.HOLD_POSITION, self.f["hold"])
            per_line = int(SCEN_CHARS)
        self.s_height(r, 12 * math.ceil(len(labels.HOLD_POSITION) * 1.1 / per_line))

    def _row(self, S, label, unit, gen, fmt, held=False, merge=True):
        """One Summary row across scenarios. gen(s) -> (formula, value). held (R4-06): the scenario columns carry
        labels.HOLD_POSITION instead of the figures (merged unless the row is a contract range)."""
        self.s_label(self.sr, label)
        if unit:
            self.s_txt(self.sr, 1, unit)
        if held:
            self.s_hold_cells(self.sr, 2, len(S), merge)
        else:
            for j, s in enumerate(S):
                f, v = gen(s)
                self.s_fx(self.sr, 2 + j, f, v, fmt)
        self._mark(fmt, held)
        self.sr += 1

    def _held(self, name, t=None):
        """R4-06: is the figure held (t: the index into score_ts for the share and count at or above t)."""
        tv = self.score_ts[t] if (name in ("share_at_or_above_t", "enrolled_at_or_above") and t is not None) else None
        return K.is_held(self.cfg, name, tv)

    def _cref_row(self, S, label, unit, name, fmt, k="middle", t=None):
        def gen(s):
            if self.dry:
                return "0", 0
            return self.cref(name, k, s, t), self.pv(name, k, s, t)
        self._row(S, label, unit, gen, fmt, held=self._held(name, t))

    def _direct_row(self, S, label, unit, name, fmt, k="middle", t=None):
        self._row(S, label, unit, lambda s: (self.fm(name, k, s, t), self.pv(name, k, s, t)), fmt,
                  held=self._held(name, t))

    def _lv(self, f):
        return lambda s: (self.LV(s, f), _clean(getattr(self.run.scen(s), f)))

    def seg_title(self):
        segs = self.cfg["segments"]
        return segs[0]["members_label"] if segs else labels.NO_SEGMENT_CELLS

    SEC_TITLES = {"A": "sec_title_A", "B": "sec_title_B", "C": "sec_title_C", "D": "sec_title_D", "E": "sec_title_E",
                  "F": "sec_title_F", "G": "sec_title_G", "H": "sec_title_H"}

    def sec_title(self, letter):
        return DD.lab(self.SEC_TITLES[letter], measure=self.cfg["score"]["measure"], segment=self.seg_title())

    # ---- sections ------------------------------------------------------------------------------------------------

    def sec_A(self, S):
        self.Sn = S
        self.s_sec(self.sec_title("A"), self.lab_note())
        self.s_scen_head(S)

        def parent(lab):
            # parent names wrap within the scenario column (Phase 4 render review); the row fits the longest name
            self._row(S, lab, "", lambda s: (f'"{self.run.parents[s].name}"' if self.run.parents[s] else '"(none)"',
                                             self.run.parents[s].name if self.run.parents[s] else "(none)"), "tw")
            if not self.dry:
                longest = max([len(p.name) for p in self.run.parents.values() if p] + [6])
                self.ws["Summary"].set_row(self.sr - 1, 12 * max(1, math.ceil(longest / 15)))
                self.txt("Summary", self.sr - 1, 0, lab, "tw")
        self.add("IN-090", parent)
        self.q_cref("OUT-008", "class_mean", "n1")
        self.q_cref("OUT-009", "class_lo90", "n1")
        self.q_cref("OUT-010", "class_hi90", "n1")
        self.q_cref("OUT-011", "p_class_over_cap", "prob")
        self.q_cref("OUT-012", "p_class_in_band", "prob")
        self.q_row("IN-098", self._lv("class_target"), "n0")
        self.q_row("IN-099", self._lv("class_cap"), "n0")
        for rid, nm in (("OUT-002", "apps_total"), ("OUT-003", "apps_in"), ("OUT-004", "apps_out"),
                        ("OUT-005", "admits_total"), ("OUT-006", "admits_in"), ("OUT-007", "admits_out")):
            self.q_direct(rid, nm, "n1")
        self.q_case(DD.rid("class_mean_low"), "class_mean", "n1", "low")
        self.q_case(DD.rid("class_mean_high"), "class_mean", "n1", "high")
        self.q_selected(DD.rid("sel_class"), "class_mean", "n1")
        self.flush("A")

    def sec_B(self, S):
        cfg = self.cfg
        self.s_sec(self.sec_title("B"), self.lab_note())
        self.s_scen_head(S)
        self.q_row(DD.rid("tuition_echo"), lambda s: (self.LH("middle", s, "T"), self.run.lcs[s]["middle"].tuition),
                   "usd")
        self.q_row("IN-093", self._lv("tuition_increase_pct"), "pp")
        for rid, nm in (("OUT-032", "gross_y1"), ("OUT-033", "merit"), ("OUT-034", "incentive_cost"),
                        ("OUT-035", "need"), ("OUT-036", "specialty"), ("OUT-037", "aid"), ("OUT-038", "ntr_y1"),
                        ("OUT-048", "avg_aid")):
            self.q_cref(rid, nm, "usd")
        self.q_direct("OUT-039", "ntr_lo90", "usd")
        self.q_direct("OUT-040", "ntr_hi90", "usd")
        # R4-12: the target itself and the effective entering target the probability reads
        tgt, eff = cfg.get("ntr_target"), ntr_target_effective(cfg)
        self.q_row("OUT-041", lambda s: ('IF(in_ntr_target="","none",in_ntr_target)',
                                         "none" if tgt is None else tgt), "usd")
        self.q_row("OUT-042", lambda s: ('IF(in_ntr_target_eff="","none",in_ntr_target_eff)',
                                         "none" if eff is None else eff), "usd")
        self.q_cref("OUT-043", "p_ntr_y1_ge_target", "prob")
        # [v0.6.3, BM-4] JD revenue goal; R4-12: labels.NOT_USED_ENTERING under the entering-class basis
        all_jd = cfg.get("ntr_goal_basis") == "all_jd"
        NU = xs(labels.NOT_USED_ENTERING)
        self.q_row("OUT-044", lambda s: (f'IF(in_ntr_goal_basis="all_jd",in_continuing_ntr_usd,{NU})',
                                         cfg.get("continuing_ntr_usd") if all_jd else labels.NOT_USED_ENTERING),
                   "usd")

        def jd(s):
            v = self.pv("jd_ntr", "middle", s)
            return self.fm("jd_ntr", "middle", s), (v if all_jd else labels.NOT_USED_ENTERING)
        self.q_row("OUT-045", jd, "usd")

        def pjd(s):
            if self.dry:
                return "0", 0
            v = self.pv("p_jd_ntr_ge_goal", "middle", s)
            return (f'IF(in_ntr_goal_basis="all_jd",{self.cref("p_jd_ntr_ge_goal", "middle", s)},{NU})',
                    v if all_jd else labels.NOT_USED_ENTERING)
        self.q_row("OUT-046", pjd, "prob")
        self.q_cref("OUT-047", "discount_entering_y1", "pct1")
        base0 = self.S[0].name

        def pot(s):
            if self.dry:
                return "0", 0
            return (f"{self.cref('ntr_y1', 'middle', base0)}-{self.cref('ntr_y1', 'middle', s)}",
                    self.vals["price_of_target"][s])
        self.q_row("OUT-049", pot, "usd")
        self.q_row("IN-111", self._lv("discount_target"), "pct1")

        def dmargin(s):
            if self.dry:
                return "0", 0
            t = self.LV(s, "discount_target")
            sc = self.run.scen(s)
            d = self.pv("discount_entering_y1", "middle", s)
            return (f'IF({t}="","",{t}-{self.cref("discount_entering_y1", "middle", s)})',
                    None if sc.discount_target is None else sc.discount_target - d)
        self.q_row("OUT-050", dmargin, "pct1")
        self.q_case(DD.rid("ntr_low"), "ntr_y1", "usd", "low")
        self.q_case(DD.rid("ntr_high"), "ntr_y1", "usd", "high")
        self.q_selected(DD.rid("sel_ntr"), "ntr_y1", "usd")
        self.flush("B")

    def _tkw(self, ti):
        """Template fields of median target ti: the measure (score measure or GPA) and the threshold."""
        m, t = self.targets[ti]
        return {"measure": "GPA" if m == "gpa" else self.cfg["score"]["measure"], "t": f"{t:g}"}

    def sec_C(self, S):
        cfg = self.cfg
        meas = cfg["score"]["measure"]
        self.s_sec(self.sec_title("C"), self.lab_note() + f" Tie rule: a median or percentile target "
                   f"{labels.PCT_TIE_RULE}. The median cushion is students at or above the target minus students "
                   f"below it (one swap moves it by two); a percentile cushion counts swaps "
                   f"({labels.PCT_MARGIN_UNIT}). {labels.GPA_PCT_NOTE}")
        self.s_scen_head(S)
        for ti in range(len(self.targets)):
            kw = self._tkw(ti)
            self.q_cref("OUT-020", "p_median_t", "prob", ti=ti, inst=ti, **kw)
            self.q_cref("OUT-019", "margin_t", "n1", ti=ti, inst=ti, **kw)
            self.q_cref("OUT-021", "p_median_t_rho05", "prob", ti=ti, inst=ti, **kw)
            self.q_case(DD.rid("p_median_low"), "p_median_t", "prob", "low", ti=ti, inst=ti, **kw)
            self.q_case(DD.rid("p_median_high"), "p_median_t", "prob", "high", ti=ti, inst=ti, **kw)
        self.q_selected(DD.rid("sel_median"), "p_median_t", "prob", 0, **self._tkw(0))
        for ti, t in enumerate(self.score_ts):
            self.add("OUT-013", (lambda ti_: lambda lab: self._direct_row(S, lab, "", "enrolled_at_or_above", "n1",
                                                                          t=ti_))(ti), ti, measure=meas,
                     t=f"{t:g}")
            self.add("OUT-014", (lambda ti_: lambda lab: self._cref_row(S, lab, "", "share_at_or_above_t", "pct1",
                                                                        t=ti_))(ti), ti, measure=meas, t=f"{t:g}")
        self.q_direct("OUT-015", "enrolled_below_floor", "n1", measure=meas, t=f"{cfg['score']['floor']:g}")
        self.q_direct("OUT-016", "enrolled_gpa_hi", "n1", gpa=f"{cfg['gpa']['hi_at_or_above']:g}")
        self.q_cref("OUT-017", "unscored_count", "n1", measure=meas)
        self.q_direct("OUT-018", "gpa_blank_count", "n1")
        # [v0.6.3, BM-1] percentile targets other than the median (R4-03: q = 0.5 targets are the median rows)
        for ti, (q, t) in enumerate(self.ptargets):
            if q == 0.5:
                continue
            kw = {"ordinal": ordinal(q), "measure": meas, "t": f"{t:g}"}
            self.q_cref("OUT-023", "p_pct_q_t", "prob", ti=ti, inst=ti, **kw)
            self.q_cref("OUT-022", "margin_q_t", "n1", ti=ti, inst=ti, **kw)
            self.q_cref("OUT-024", "p_pct_q_t_rho05", "prob", ti=ti, inst=ti, **kw)
            self.q_direct("OUT-025", "pct_expected_below", "n1", ti=ti, inst=ti, **kw)
            self.q_direct("OUT-026", "pct_approximate", "t", ti=ti, inst=ti, **kw)
            self.q_case(DD.rid("p_pct_low"), "p_pct_q_t", "prob", "low", ti=ti, inst=ti, **kw)
            self.q_case(DD.rid("p_pct_high"), "p_pct_q_t", "prob", "high", ti=ti, inst=ti, **kw)
        # spread bands: the lower bound (technical, SUM_PCT_BAND_Q) and the band as text (standard), which reads it
        lows = sorted(float(b) for b in cfg["score"]["bands"])
        for qi, q in enumerate(risk.SPREAD_QS):
            def gen(s, q=q):
                d = self.g("middle", s)
                E, SC, SL = d["enrolled"], d["scored"], d["score_lo"]
                U = f'IF(in_unscored_in_median="below",SUMPRODUCT(({SC}=0)*{E}),0)'
                N = f"(SUMPRODUCT(({SC}=1)*{E})+{U})"
                terms = ",".join(f"IF((SUMPRODUCT(({SC}=1)*({SL}<{b})*{E})+{U})/{N}<={q},{b},-1)"
                                 for b in self.inp_list["score_bands"])
                return f'IF({N}<=0,"",IF(MAX({terms})<0,"",MAX({terms})))', self.vals["pct_band"][s][q]
            self.q_row("OUT-027", gen, "band", held=self._held("pct_band_q"), merge=False, inst=qi, measure=meas,
                       ordinal=ordinal(q))

            def gen_t(s, q=q, qi=qi):
                t = self.vals["pct_band"][s][q]
                v = "" if t is None else L._range_text(lows, lows.index(t), lows.index(t), lambda x: f"{x:g}")
                br = self.srow_dry.get(("OUT-027", qi), (0,))[0]
                c = a1(br, 2 + S.index(s))
                k = f"MATCH({c},in_score_bands,0)"
                lo0 = min(lows)
                f = (f'IF({c}="","",IF({k}=1,{c}&"+",IF(({c}={lo0:g})*({c}<=0)=1,"below "&INDEX(in_score_bands,{k}-1),'
                     f'{c}&" to below "&INDEX(in_score_bands,{k}-1))))')
                return f, v
            self.q_row("OUT-028", gen_t, "t", held=self._held("pct_band_q"), inst=qi, measure=meas,
                       ordinal=ordinal(q))
        self.flush("C")

    def sec_D(self, S):
        cfg = self.cfg
        seg_lab = ""
        if cfg["segments"] and cfg["segments"][0]["share_source"] == "assumed":
            seg_lab = labels.SEGMENT_SHARE_LABEL + ". "
        self.s_sec(self.sec_title("D"), seg_lab + self.lab_note() + " The chance the segment goal is met uses a "
                   "normal approximation; the exact calculation, made when the workbook was built, is in section H.")
        self.s_scen_head(S)
        self.q_row("OUT-052", lambda s: (self.LH("middle", s, "seg"), L.active_segment(cfg, self.run.scen(s)) or ""),
                   "t")
        self.q_direct("OUT-053", "segment_apps", "n1")
        self.q_direct("OUT-054", "segment_admits", "n1")
        self.q_cref("OUT-055", "segment_enrolled", "n1")
        self.q_cref("OUT-056", "segment_share", "pct1")
        self.q_direct("OUT-057", "segment_merit", "usd")
        self.q_cref("OUT-058", "segment_lo90", "n1")
        self.q_cref("OUT-059", "segment_hi90", "n1")
        self.q_direct("OUT-060", "segment_goal", "n0")
        self.q_cref("OUT-061", "p_segment_goal", "prob")

        def exact(s):
            v = self.vals["seg_exact"][s]
            if v is None:
                return '""', None
            if isinstance(v, str):
                return xs(v), v
            return f"{v!r}", v
        self.q_row("OUT-062", exact, "prob")

        def status(s):
            # [v0.6.2, P2-06] the static exact value is stale once the segment's expected enrollment or goal differs
            # from its value at build
            d = self.g("middle", s)
            SEG, MU, GL = d["in_seg"], d["mu"], d["GOAL"]
            v = self.vals["seg_exact"][s]
            stale = xs(labels.EXACT_STALE)
            if isinstance(v, float):
                # stale when the expected enrollment, the goal or the set of segment cells (fixed by the active
                # segment's name; cells carry their segment) differs from the build [v0.6.2, P21 call 1]
                lc = self.run.lcs[s]["middle"]
                b = float(lc.mu[lc.in_segment].sum())
                gb = int(math.ceil(self.run.scen(s).segment_goal))
                seg_b = L.active_segment(self.cfg, self.run.scen(s)) or ""
                MS = f"SUMPRODUCT({SEG},{MU})"
                return (f'IF(SUM({SEG})=0,{stale},IF({GL}="",{stale},IF((MAX({MS}-{b!r},{b!r}-{MS})>'
                        f'1E-9*MAX(1,{b!r}))+({ceil_x(GL)}<>{gb})+({self.LH("middle", s, "seg")}<>{xs(seg_b)})>0,'
                        f'{stale},{xs(labels.EXACT_CURRENT)})))', labels.EXACT_CURRENT)
            return f'IF((SUM({SEG})>0)*({GL}<>"")=1,{stale},"")', ""

        def status_row(lab):
            self.exact_status_row = self.sr
            self._row(S, lab, "", status, "t")
        self.add("OUT-063", status_row)
        self.q_direct("OUT-064", "segment_approximate", "t")
        self.flush("D")

    def sec_E(self, S):
        self.s_sec(self.sec_title("E"), labels.RESPONSE_LABEL + ". The figures are what the assumed response "
                   "implies, not estimates of what an incentive causes. Each scenario is compared with the scenario "
                   "it is built from; Baseline has none.")
        self.s_scen_head(S)
        self.q_cref(DD.rid("incentive_cost_e"), "incentive_cost", "usd")
        self.q_cref("OUT-065", "incentive_paid_anyway", "usd")
        self.q_cref("OUT-066", "incentive_paid_anyway_share", "pct1")
        self.q_cref("OUT-067", "additional_enrollees", "n1")
        self.q_direct("OUT-068", "merit_change", "usd")
        self.q_direct("OUT-069", "ntr_change", "usd")
        self.q_cref("OUT-070", "aid_per_additional", "usd")
        self.q_direct("OUT-071", "aid_per_additional_kind", "t")
        self.q_cref("OUT-072", "ntr_per_additional", "usd")
        self.q_direct("OUT-073", "incentive_cells", "int")
        self.q_cref("OUT-074", "incentive_valid", "t")
        b0 = self.S[0].name

        def implied(s):
            # [v0.6.2, Q-8d] scenario input bonus_pool_usd (Levers)
            sc = self.run.scen(s)
            pool = sc.bonus_pool_usd
            v = None if pool is None else L.bonus_implied_by_pool(pool, self.run.lcs[b0]["middle"], sc)
            E0 = self.LR("middle", b0, "enrolled")
            EL = self.LR("middle", s, "elig")
            PL = self.LV(s, "bonus_pool_usd")
            return f'IF({PL}="","",IF(SUMPRODUCT({E0},{EL})>0,{PL}/SUMPRODUCT({E0},{EL}),""))', v
        self.q_row("OUT-075", implied, "usd")
        self.flush("E")

    def _strip_table(self, S, which, keycol_label, key_fmt, grid_refs, colheads, fmts, gen):
        """Rows (s, grid value); gen(s, gi) -> list of (formula, value). R4-06: under hold, the median and percentile
        columns (contract.held_strip_col) carry labels.HOLD_POSITION in every cell."""
        cols = K.strip_columns(self.cfg)[which]
        held = {i for i, c in enumerate(cols) if self.hold and K.held_strip_col(c)}
        self.s_txt(self.sr, 0, "scenario", "h")
        self.s_txt(self.sr, 1, keycol_label, "h")
        for c, h in enumerate(colheads):
            self.s_txt(self.sr, 2 + c, h, "h")
        if not self.dry:
            self.ws["Summary"].set_row(self.sr, 60)
        self.sr += 1
        r0 = self.sr
        rows = K.strip_rows(self.run, self.vals, which) if not self.dry else None
        idx = 0
        for s in S:
            for gi, gref in enumerate(grid_refs):
                self.s_txt(self.sr, 0, s)
                if not self.dry:
                    self.s_fx(self.sr, 1, gref, rows[idx][1], key_fmt)
                    for c, (f, v) in enumerate(gen(s, gi)):
                        if c in held:
                            self.s_hold_cells(self.sr, 2 + c, 1, merge=False)
                        else:
                            self.s_fx(self.sr, 2 + c, f, v, fmts[c])
                    expect = rows[idx][2]
                    assert len(expect) == len(colheads)
                idx += 1
                self.sr += 1
        self.strip_pos[which] = (r0, self.sr - 1, len(grid_refs))
        return r0, self.sr - 1

    def f_title(self, rid, **kw):
        """A section F block title: 'F. ' and the block's dictionary label (each block is its own printed section,
        so the render lays out and repeats each table's own header; CP-3)."""
        lab = DD.label(rid, **kw)
        self.printed.append(("F", rid, lab))
        return "F. " + lab

    def head(self, rid, sec="F", **kw):
        """A table column heading from the dictionary, recorded for Definitions."""
        lab = DD.label(rid, **kw)
        self.printed.append((sec, rid, lab))
        return lab

    def sec_F(self, S):
        self.sw_tuition(S)
        self.sw_yield(S)
        self.sw_pool(S)
        self.sw_class_table(S)

    def sw_tuition(self, S):
        cfg = self.cfg
        self.s_sec(self.f_title("OUT-076"), self.lab_note(shock=False) + " " + labels.STICKER_LABEL
                   + " Awards are recomputed at each tuition under the scenario's award rule.")
        grid = self.inp_list["tuition_grid"]
        cols = K.strip_columns(cfg)["tuition_whatif"]

        def gen(s, gi):
            st = self.vals["strips"][s]["tuition_whatif"]["tuition_whatif"][gi]
            col = self.lblock[("middle", s)][f"tw{gi}"]
            Tp = ref("Ledger_Middle", 3, col)
            AWp = rng("Ledger_Middle", self.r0l, col, self.r0l + self.n - 1, col)
            E = self.LR("middle", s, "enrolled")
            NR = self.LH("middle", s, "need_rate")
            SP = self.g("middle", s)["K"]
            ntr = f"({Tp}*SUM({E})-SUMPRODUCT({E},{AWp})-{NR}*SUM({E})-{SP})"
            return [(Tp, st["tuition"]), (ntr, st["ntr_y1"]),
                    (f"IF(SUM({E})>0,{ntr}/SUM({E}),0)", st["net_tuition_per_student"]),
                    (f"IF(SUM({E})*{Tp}>0,(SUM({E})*{Tp}-{ntr})/(SUM({E})*{Tp}),0)", st["discount_entering_y1"])]
        r0, r1 = self._strip_table(S, "tuition_whatif", self.head("OUT-081"), "pp", grid,
                                   [self.head(x) for x in ("OUT-077", "OUT-078", "OUT-079", "OUT-080")],
                                   ["usd", "usd", "usd", "pct1"], gen)
        self.s_name("TW_TUITION_WHATIF", r0, 2, r1, 2 + len(cols) - 1)
        # [v0.6.3, BM-4] under all_jd the what-if shows first-year revenue only, with continuing revenue held fixed
        self.s_txt(self.sr, 0, self.head("OUT-082"))
        self.s_fx(self.sr, 2, f'IF(in_ntr_goal_basis="all_jd",{xs(labels.CONTINUING_HELD)},'
                              f'{xs(labels.NOT_USED_ENTERING)})',
                  labels.CONTINUING_HELD if cfg.get("ntr_goal_basis") == "all_jd" else labels.NOT_USED_ENTERING, "t")
        self.sr += 1
        # the two net-tuition lines (R4-02: a section of their own, so a continued page repeats their own header)
        self.s_sec(self.f_title(DD.rid("net_tuition_lines_title")), self.lab_note(shock=False))
        self.s_txt(self.sr, 0, "scenario", "h")
        for c, h in enumerate(("OUT-083", "OUT-084", "OUT-085")):
            self.s_txt(self.sr, 1 + c, self.head(h), "h")
        self.s_height(self.sr, 60)
        self.sr += 1
        r0 = self.sr
        line_txt = []
        for s in S:
            self.s_txt(self.sr, 0, s)
            if not self.dry:
                tw = self.vals["strips"][s]["tuition_whatif"]
                T = self.LH("middle", s, "T")
                E = self.LR("middle", s, "enrolled")
                LEV = self.LVR(s, "award")
                FT = self.LVR(s, "ft")
                P = self.LV(s, "tuition_increase_pct")
                # [v0.6.2, Q-5; P1.1-4] base-cycle lever award below base-cycle tuition, cells without the flag
                cond = f"({FT}=0)*({LEV}<in_tuition_base-0.000001)*({E}>0)"
                den = f"SUMPRODUCT({E}*{cond})"
                r = self.sr
                self.s_fx(r, 1, f"{T}-in_tuition_base", tw["net_tuition_line_fixed"], "usd")
                self.s_fx(r, 2, f"IF({den}>0,ROUND(SUMPRODUCT({E}*{LEV}*{cond})/{den}/1000,0)*1000,0)",
                          tw["example_award"], "usd")
                self.s_fx(r, 3, f"{P}/100*(in_tuition_base-{a1(r, 2)})", tw["net_tuition_line_scaled"], "usd")
                fixed_t = NAR.template_formula(labels.NET_TUITION_FIXED,
                                               {"diff": f'"$"&TEXT({a1(r, 1)},"#,##0")&""'})
                scaled_t = NAR.template_formula(labels.NET_TUITION_SCALED, {
                    "p": f'TEXT({P},"0.0")&"%"', "x": f'"$"&TEXT({a1(r, 3)},"#,##0")',
                    "award": f'"$"&TEXT({a1(r, 2)},"#,##0")'})
                line_txt.append((s, fixed_t, tw["net_tuition_line_fixed_text"], scaled_t,
                                 tw["net_tuition_line_scaled_text"]))
            self.sr += 1
        self.s_name("TW_NET_TUITION_LINE_FIXED", r0, 1, self.sr - 1, 1)
        self.s_name("TW_NET_TUITION_LINE_SCALED", r0, 3, self.sr - 1, 3)
        # R4-02: the two lines as sentences, merged across columns B to the last scenario column so the text is not cut
        last = 1 + max(len(S), 6)
        for s in S:
            for kind in ("fixed", "scaled"):
                self.s_txt(self.sr, 0, s if kind == "fixed" else "")
                if not self.dry:
                    _, ff, fv, sf, sv = next(x for x in line_txt if x[0] == s)
                    f, v = (ff, fv) if kind == "fixed" else (sf, sv)
                    self.ws["Summary"].merge_range(self.sr, 1, self.sr, last, "", self.f["mergew"])
                    self.s_fx(self.sr, 1, f, v, "mergew")
                    self.s_height(self.sr, 24)
                self.sr += 1
        self.s_note("Both lines are arithmetic at a constant award; neither changes yield. Example award: the "
                    "enrolled-weighted average base-year award among students whose award, before any incentive, is "
                    "below base-year tuition and whose group has no full-tuition flag, zero awards included, rounded "
                    "to $1,000.")

    def sw_yield(self, S):
        cfg = self.cfg
        self.s_sec(self.f_title("OUT-087"), self.lab_note() + " " + labels.ASSUMPTION_LABEL + ". The table ignores "
                   "the yield floor and cap; section H counts the groups where a bound would bind.")
        cols = K.strip_columns(cfg)["yield_strip"]
        heads = [self.head(x) for x in ("OUT-088", "OUT-089", "OUT-090", "OUT-091", "OUT-092")]
        fmts = ["n1", "prob", "prob", "usd", "prob"]
        for ti in range(len(self.targets)):
            kw = self._tkw(ti)
            heads += [self.head("OUT-093", **kw), self.head("OUT-094", **kw)]
            fmts += ["n1", "prob"]
        sd, rho = "in_common_shock_sd", "in_shock_corr"

        def gen(s, gi):
            row = self.vals["strips"][s]["yield_strip"]["yield_strip"][gi]
            d = self.g("middle", s)
            A, Y, W = d["admits"], d["yield"], d["w"]
            dd = f"({self.inp_list['yield_shift_grid'][gi]}/100)"
            Yd = f"({Y}+{dd})"
            M = f"SUMPRODUCT({A},{Yd})"
            V = f"(SUMPRODUCT({A},{Yd},1-{Yd})+{sd}^2*{M}^2)"
            SDV = f"SQRT(MAX({V},1E-300))"
            SW = f"SUMPRODUCT({W},{A},{Yd})"
            VN = f"(SUMPRODUCT({W},{W},{A},{Yd},1-{Yd})+{sd}^2*{SW}^2)"
            out = [(M, row["class_mean"]),
                   (f"1-NORMSDIST(({d['CAP']}+0.5-{M})/{SDV})", row["p_class_over_cap"]),
                   (f"NORMSDIST(({d['TGT']}+in_class_band+0.5-{M})/{SDV})-NORMSDIST(({d['TGT']}-in_class_band-0.5-{M})"
                    f"/{SDV})", row["p_class_in_band"]),
                   (f"{SW}-{d['K']}", row["ntr_mean"]),
                   (f'IF(in_ntr_target_eff="","",1-NORMSDIST((in_ntr_target_eff-({SW}-{d["K"]}))/'
                    f"MAX(SQRT(MAX({VN},0)),1E-300)))", row["p_ntr_y1_ge_target"])]
            for ti, key in enumerate(self.targets):
                G = d[f"g{ti}"]
                gp, gm = f"SUMPRODUCT(({G}=1)*{A}*{Yd})", f"SUMPRODUCT(({G}=-1)*{A}*{Yd})"
                vm = f"(SUMPRODUCT(({G}<>0)*{A}*{Yd}*(1-{Yd}))+{sd}^2*({gp}^2+{gm}^2-2*{rho}*{gp}*{gm}))"
                out.append((f"{gp}-{gm}", row["median"][key]["margin"]))
                out.append((f"1-NORMSDIST((-0.5-({gp}-{gm}))/SQRT(MAX({vm},1E-300)))", row["median"][key]["p"]))
            return out
        r0, r1 = self._strip_table(S, "yield_strip", self.head("OUT-095"), "pp", self.inp_list["yield_shift_grid"],
                                   heads, fmts, gen)                     # R4-06: median columns held under hold
        self.s_name("YS_YIELD_STRIP", r0, 2, r1, 2 + len(cols) - 1)
        self.s_sec(self.f_title(DD.rid("yield_breakeven_title")),
                   self.lab_note(shock=False) + " " + labels.ASSUMPTION_LABEL + ". Both figures are a "
                   + labels.LINEAR_APPROX + ".")
        self.s_txt(self.sr, 0, "scenario", "h")
        self.s_txt(self.sr, 1, self.head("OUT-097"), "h")
        self.s_txt(self.sr, 2, self.head("OUT-098"), "h")
        self.s_height(self.sr, 60)
        self.sr += 1
        r0 = self.sr
        for s in S:
            self.s_txt(self.sr, 0, s)
            if not self.dry:
                ys = self.vals["strips"][s]["yield_strip"]
                d = self.g("middle", s)
                A, Y, W = d["admits"], d["yield"], d["w"]
                self.s_fx(self.sr, 1, f'IF(SUM({A})>0,({d["TGT"]}-SUMPRODUCT({A},{Y}))/SUM({A})*100,"")',
                          ys["breakeven_shift_class"], "r3")
                self.s_fx(self.sr, 2, f'IF(in_ntr_target_eff="","",IF(SUMPRODUCT({W},{A})<>0,(in_ntr_target_eff-'
                                      f'(SUMPRODUCT({W},{A},{Y})-{d["K"]}))/SUMPRODUCT({W},{A})*100,""))',
                          ys["breakeven_shift_ntr"], "r3")
            self.sr += 1
        self.s_name("YS_BREAKEVEN_SHIFT_CLASS", r0, 1, self.sr - 1, 1)
        self.s_name("YS_BREAKEVEN_SHIFT_NTR", r0, 2, self.sr - 1, 2)

    def sw_clip(self, S):
        """Section H: the yield what-if's clip count (groups where a bound would bind at the largest shift)."""
        self.s_sec("H. " + DD.lab("clip_title"), self.lab_note(shock=False) + " " + labels.ASSUMPTION_LABEL + ".")
        self.printed.append(("H", DD.rid("clip_title"), DD.lab("clip_title")))
        self.s_txt(self.sr, 0, "scenario", "h")
        self.s_txt(self.sr, 1, self.head("OUT-096", sec="H"), "h")
        self.s_height(self.sr, 60)
        self.sr += 1
        for s in S:
            self.s_txt(self.sr, 0, s)
            if not self.dry:
                ys = self.vals["strips"][s]["yield_strip"]
                d = self.g("middle", s)
                A, Y = d["admits"], d["yield"]
                g = "in_yield_shift_grid"
                self.s_fx(self.sr, 1, f"SUMPRODUCT(({A}>0)*((({Y}+MAX({g})/100>{d['cap']})+({Y}+MIN({g})/100<"
                                      f"{d['floor']}))>0))", ys["clip_count"], "int")
            self.sr += 1

    def sw_pool(self, S):
        cfg = self.cfg
        meds = cfg["score"]["median_thresholds"]
        meas = cfg["score"]["measure"]
        pq = K.ct_ptargets(cfg)                       # F-4: q = 0.5 targets are the median columns
        pth = format(cfg["score"]["pool_threshold"], "g")
        self.s_sec(self.f_title("OUT-099"),
                   self.lab_note() + " "
                   f"The application multiple applies to applications at {meas} {pth} or higher ({labels.POOL_STRIP_LABEL}); "
                   f"every other lever stays as the scenario sets it. Growth to date (complete applications at "
                   f"{meas} {pth} or higher against the same week of the prior cycle; {labels.POOL_YTD_LABEL}) marks "
                   f"the row nearest 1 + growth ({labels.POOL_YTD_TIE}).")
        self.s_label(self.sr, self.head("OUT-110"))
        self.s_fx(self.sr, 2, 'IF(in_pool_ytd_growth="","not set",in_pool_ytd_growth)',
                  "not set" if cfg.get("pool_ytd_growth") is None else cfg["pool_ytd_growth"], "pct1")
        self.s_fx(self.sr, 3, f'IF(in_pool_ytd_as_of="",{xs(labels.POOL_YTD_NO_DATE)},in_pool_ytd_as_of)',
                  cfg.get("pool_ytd_as_of") or labels.POOL_YTD_NO_DATE, "t")
        # [v0.6.3, BM-6] nearest grid row: 1 + the number of midpoints between adjacent grid values at or below
        # 1 + growth (the grid is ascending; R4-13: a tie goes to the upper row, within 1e-9). Phase 4.2: the cell shows
        # that row's pool multiplier, not the row index
        gsh, gr, gc0, _, gc1 = self.names["in_pool_grid"]
        if gc1 > gc0:
            lo_r, hi_r = rng(gsh, gr, gc0, gr, gc1 - 1), rng(gsh, gr, gc0 + 1, gr, gc1)
            nf = (f'IF(in_pool_ytd_growth="","",INDEX(in_pool_grid,1+SUMPRODUCT(((({lo_r}+{hi_r})/2'
                  f'-(1+in_pool_ytd_growth))<=0.000000001)*1)))')
        else:
            nf = 'IF(in_pool_ytd_growth="","",INDEX(in_pool_grid,1))'
        nearest = self.vals["strips"][S[0]]["pool_strip"]["nearest_m"] if S else None
        self.s_fx(self.sr, 4, nf, nearest, "num")
        self.pool_nearest = a1(self.sr, 4)
        self.pool_nearest_row = self.sr
        self.marker_cells = [("Summary", self.sr, 2), ("Summary", self.sr, 4)]
        self.sr += 1
        sd = "in_common_shock_sd"
        cols = K.strip_columns(cfg)["pool_strip"]
        heads = [self.head(x) for x in ("OUT-100", "OUT-101", "OUT-102", "OUT-103", "OUT-104")]
        fmts = ["pct1", "n1", "prob", "usd", "usd"]
        for t in meds:
            heads += [self.head("OUT-105", measure=meas, t=f"{t:g}"), self.head("OUT-106", measure=meas, t=f"{t:g}")]
            fmts += ["n1", "prob"]
        heads += [self.head("OUT-107", ordinal=ordinal(q), measure=meas, t=f"{t:g}") for _, (q, t) in pq]
        heads += [self.head("OUT-108")]
        fmts += ["prob"] * len(pq) + ["tw"]
        marker_txt = (f'"growth to date ("&IF(in_pool_ytd_as_of="",{xs(labels.POOL_YTD_NO_DATE)},in_pool_ytd_as_of)'
                      f'&") is about here"')
        mcol = 2 + len(cols) - 1

        def gen(s, gi):
            row = self.vals["strips"][s]["pool_strip"]["pool_strip"][gi]
            P = lambda part, key: self.pool_parts[(s, part, key)]  # noqa: E731
            m = self.inp_list["pool_grid"][gi]
            M = f"({P('lo', 'M')}+{m}*{P('hi', 'M')})"
            V = f"({P('lo', 'V')}+{m}*{P('hi', 'V')}+{sd}^2*{M}^2)"
            Wm = f"({P('lo', 'W')}+{m}*{P('hi', 'W')})"
            Vn = f"({P('lo', 'Vn')}+{m}*{P('hi', 'Vn')}+{sd}^2*{Wm}^2)"
            CAP = self.LV(s, "class_cap")
            out = [(f"{m}-1", row["growth"]), (M, row["class_mean"]),
                   (f"1-NORMSDIST(({CAP}+0.5-{M})/SQRT(MAX({V},1E-300)))", row["p_class_over_cap"]),
                   (f"{Wm}-{self.g('middle', s)['K']}", row["ntr_mean"]), (f"SQRT(MAX({Vn},0))", row["ntr_sd"])]
            for i, t in enumerate(meds):                                              # F-4: every median
                Gp = f"({P('lo', f'Gp_m{i}')}+{m}*{P('hi', f'Gp_m{i}')})"
                Gm = f"({P('lo', f'Gm_m{i}')}+{m}*{P('hi', f'Gm_m{i}')})"
                Vm = (f"({P('lo', f'Vm_m{i}')}+{m}*{P('hi', f'Vm_m{i}')}+{sd}^2*({Gp}^2+{Gm}^2"
                      f"-2*in_shock_corr*{Gp}*{Gm}))")
                out.append((f"{Gp}-{Gm}", row["median"][t]["margin"]))
                out.append((f"1-NORMSDIST((-0.5-({Gp}-{Gm}))/SQRT(MAX({Vm},1E-300)))", row["median"][t]["p"]))
            for j, key in pq:
                q, cr = self.inp_list["pct_q"][j], self.inp_list["pct_corr"][j]
                gp = f"({P('lo', f'Gp{j}')}+{m}*{P('hi', f'Gp{j}')})"
                gm = f"({P('lo', f'Gm{j}')}+{m}*{P('hi', f'Gm{j}')})"
                vp = f"({P('lo', f'Vp{j}')}+{m}*{P('hi', f'Vp{j}')})"
                vm = f"({P('lo', f'Vm{j}')}+{m}*{P('hi', f'Vm{j}')})"
                vq = (f"({q}^2*{vp}+(1-{q})^2*{vm}+{sd}^2*({q}^2*{gp}^2+(1-{q})^2*{gm}^2-2*in_shock_corr*{q}*(1-{q})"
                      f"*{gp}*{gm}))")
                out.append((f"1-NORMSDIST((-{cr}-({q}*{gp}-(1-{q})*{gm}))/SQRT(MAX({vq},1E-300)))",
                            row["pct"][key]["p"]))
            out.append((f'IF({self.pool_nearest}="","",IF({self.pool_nearest}={m},{marker_txt},""))',
                        row["marker"]))
            if not self.dry:
                self.marker_cells.append(("Summary", self.sr, mcol))
            return out
        r0, r1 = self._strip_table(S, "pool_strip", self.head("OUT-109", measure=meas, pth=pth), "num",
                                   self.inp_list["pool_grid"], heads, fmts, gen)
        self.s_name("PS_POOL_STRIP", r0, 2, r1, 2 + len(cols) - 1)
        # [v0.6.3, BM-6] break-even pool multipliers (expectations, not probabilities); R4-04: a note in place of a
        # number when the break-even is not a pool size on the grid (strip.breakeven_m); F-2: a ceiling reads
        # "at most m"; F-3: the figures start in column B (no empty heading column); F-4: the medians, then the
        # percentile targets other than q = 0.5
        self.s_sec(self.f_title("OUT-111"), self.lab_note(shock=False))
        at_most = labels.POOL_BE_AT_MOST.format(m="x")
        self.s_note(labels.POOL_BREAKEVEN_LABEL[0].upper() + labels.POOL_BREAKEVEN_LABEL[1:] + ". A plain number is "
                    "a floor: the target holds from that multiple up. "
                    f"'{at_most}' is a ceiling: the target holds up to that multiple and fails beyond it, because "
                    "growth among top-score applicants lowers the cushion. In place of a number: "
                    f"'{labels.POOL_BE_ANY}' when the target holds with no growth at all; "
                    f"'{labels.POOL_BE_NOT_REACHED}' when growth does not bring it to the target; "
                    f"'{labels.POOL_BE_ABOVE_GRID}' or '{labels.POOL_BE_BELOW_GRID}' when the multiple lies outside "
                    "the multiples in the table.")
        self.s_txt(self.sr, 0, "scenario", "h")
        self.s_txt(self.sr, 1, self.head("OUT-112"), "h")
        for i, t in enumerate(meds):
            self.s_txt(self.sr, 2 + i, self.head("OUT-113", measure=meas, t=f"{t:g}"), "h")
        for c, (_, (q, t)) in enumerate(pq):
            self.s_txt(self.sr, 2 + len(meds) + c, self.head("OUT-114", ordinal=ordinal(q), measure=meas,
                                                             t=f"{t:g}"), "h")
        self.s_height(self.sr, 60)
        self.sr += 1
        r0 = self.sr
        ANY, NOT = xs(labels.POOL_BE_ANY), xs(labels.POOL_BE_NOT_REACHED)
        ABV, BLW = xs(labels.POOL_BE_ABOVE_GRID), xs(labels.POOL_BE_BELOW_GRID)
        pre, post = labels.POOL_BE_AT_MOST.split("{m}")

        def be_x(elo, ehi):
            """strip.breakeven_m in Excel."""
            m = f"(-{elo}/{ehi})"
            return (f"IF({ehi}=0,IF({elo}>=0,{ANY},{NOT}),IF({m}<=0,IF({ehi}>0,{ANY},{NOT}),"
                    f"IF({m}>MAX(in_pool_grid),{ABV},IF({m}<MIN(in_pool_grid),{BLW},"
                    f'IF({ehi}<0,{xs(pre)}&TEXT({m},"0.000")&{xs(post)},{m})))))')
        nb = 1 + len(meds) + len(pq)
        for s in S:
            self.s_txt(self.sr, 0, s)
            if not self.dry:
                P = lambda part, key: self.pool_parts[(s, part, key)]  # noqa: E731
                be = self.vals["pool_be"][s]
                self.s_fx(self.sr, 1, be_x(f"({P('lo', 'M')}-{self.LV(s, 'class_target')})", P("hi", "M")), be[0],
                          "r3")
                if self.hold:                                                   # R4-06
                    self.s_hold_cells(self.sr, 2, nb - 1, merge=False)
                else:
                    for i in range(len(meds)):
                        elo = f"({P('lo', f'Gp_m{i}')}-{P('lo', f'Gm_m{i}')})"
                        ehi = f"({P('hi', f'Gp_m{i}')}-{P('hi', f'Gm_m{i}')})"
                        self.s_fx(self.sr, 2 + i, be_x(elo, ehi), be[1 + i], "r3")
                    for c, (j, _) in enumerate(pq):
                        q = self.inp_list["pct_q"][j]
                        elo = f"({q}*{P('lo', f'Gp{j}')}-(1-{q})*{P('lo', f'Gm{j}')})"
                        ehi = f"({q}*{P('hi', f'Gp{j}')}-(1-{q})*{P('hi', f'Gm{j}')})"
                        self.s_fx(self.sr, 2 + len(meds) + c, be_x(elo, ehi), be[1 + len(meds) + c], "r3")
            self.sr += 1
        self.s_name("PS_POOL_BREAKEVEN_M", r0, 1, self.sr - 1, nb)

    def band_text(self, b):
        """A score band by its lower bound, the lowest (lower bound 0 or less) as labels.LOWEST_BAND (Phase 4.2)."""
        if b == "unscored":
            return b
        lows = sorted(float(x) for x in self.cfg["score"]["bands"])
        if float(b) == lows[0] and lows[0] <= 0 and len(lows) > 1:
            return labels.LOWEST_BAND.format(b=format(lows[1], "g"))
        return format(b, "g")

    def sw_class_table(self, S):
        cfg = self.cfg
        if self.repro:
            self.s_sec(self.f_title("OUT-115"),
                       "Live mode only (spec section 6): a reproduce build has no Trim sheet, because the shrink path "
                       "does not settle integer admits in the workbook. Build in live mode for the class-size table.")
            return
        self.s_sec(self.f_title("OUT-115"),
                   self.lab_note() + " "
                   "Trimming lowers admit rates (Trim sheet); yield stays the same when admit rates change. "
                   + labels.POLICY_UNSCORED_TRIMMED_FIRST)
        cols = K.strip_columns(cfg)["class_table"]
        meas = cfg["score"]["measure"]
        heads = [self.head(x) for x in ("OUT-116", "OUT-117", "OUT-118")]                 # [v0.6.3, BM-3]
        fmts = ["r3", "n1", "prob"]
        for ti in range(len(self.targets)):
            kw = self._tkw(ti)
            heads += [self.head("OUT-119", **kw), self.head("OUT-120", **kw)]
            fmts += ["n1", "prob"]
        for _, (q, t) in K.ct_ptargets(cfg):                       # [v0.6.3, BM-1]; R4-03: q = 0.5 left out
            kw = {"ordinal": ordinal(q), "measure": meas, "t": f"{t:g}"}
            heads += [self.head("OUT-121", **kw), self.head("OUT-122", **kw)]
            fmts += ["n1", "prob"]
        heads += [self.head(x, measure=meas) for x in ("OUT-123", "OUT-124", "OUT-125", "OUT-126")]
        fmts += ["usd", "pct1", "n1", "band"]                       # Phase 4.2: the lowest band reads "below {next}"
        bands = K.band_keys(cfg)
        heads += [self.head("OUT-127", band=self.band_text(b)) for b in bands]
        fmts += ["n1"] * len(bands)
        heads += [self.head("OUT-128")]
        fmts += ["tw"]
        sd, rho = "in_common_shock_sd", "in_shock_corr"
        NS = xs(labels.NO_SEGMENT_CELLS)
        ct_rows = {}
        if not self.dry:
            per = {}
            for rs, gv, vv in K.strip_rows(self.run, self.vals, "class_table"):
                per.setdefault(rs, []).append(vv)
            ct_rows = {(rs, gi): vv for rs, lst in per.items() for gi, vv in enumerate(lst)}

        def gen(s, gi):
            info = self.trim_info[s]
            N = self.inp_list["class_what_if"][gi]
            d = self.g("middle", s)
            Y, AW, SEG = d["yield"], d["award"], d["in_seg"]
            AN = info["admits"][gi]
            LOW = info["low"][gi]
            Mref, RK = info["M"], info["RK"]
            CAP = self.LV(s, "class_cap")
            cap_ = f"{N}>{CAP}"
            wrap = lambda f: f'IF({cap_},"",{f})'  # noqa: E731
            cls = f"SUMPRODUCT({AN},{Y})"
            T, NR, SP = d["T"], d["NR"], d["K"]
            ntr = f"({cls}*{T}-SUMPRODUCT({AN},{Y},{AW})-{NR}*{cls}-{SP})"
            status = (f'IF({cap_},{xs(labels.CT_ABOVE_CAP)},IF({N}>={Mref},{xs(labels.CT_NOT_APPLICABLE)},'
                      f'IF({Mref}-{N}>{RK}+0.000000001,{xs(labels.CT_SHORTFALL.split("{shortfall}")[0])}&TEXT({Mref}-{N}-{RK},"0.0"),'
                      f'{xs(labels.CT_OK)})))')
            row_vals = ct_rows[(s, gi)]
            Vc = f"(SUMPRODUCT({AN},{Y},1-{Y})+{sd}^2*{cls}^2)"
            out = [(f'IF({Mref}>0,{N}/{Mref},"")', row_vals[0]), (wrap(cls), row_vals[1]),
                   (wrap(f"1-NORMSDIST(({CAP}+0.5-{cls})/SQRT(MAX({Vc},1E-300)))"), row_vals[2])]
            ci = 3
            for ti, key in enumerate(self.targets):
                G = d[f"g{ti}"]
                gp = f"SUMPRODUCT(({G}=1)*{AN}*{Y})"
                gm = f"SUMPRODUCT(({G}=-1)*{AN}*{Y})"
                vm = f"(SUMPRODUCT(({G}<>0)*{AN}*{Y}*(1-{Y}))+{sd}^2*({gp}^2+{gm}^2-2*{rho}*{gp}*{gm}))"
                out.append((wrap(f"SUMPRODUCT({G},{AN},{Y})"), row_vals[ci]))
                out.append((wrap(f"1-NORMSDIST((-0.5-({gp}-{gm}))/SQRT(MAX({vm},1E-300)))"), row_vals[ci + 1]))
                ci += 2
            for tj, _ in K.ct_ptargets(cfg):
                Pq = d[f"p{tj}"]
                q, cr = self.inp_list["pct_q"][tj], self.inp_list["pct_corr"][tj]
                gp = f"SUMPRODUCT(({Pq}=1)*{AN}*{Y})"
                gm = f"SUMPRODUCT(({Pq}=-1)*{AN}*{Y})"
                vq = (f"({q}^2*SUMPRODUCT(({Pq}=1)*{AN}*{Y}*(1-{Y}))+(1-{q})^2*SUMPRODUCT(({Pq}=-1)*{AN}*{Y}*(1-{Y}))"
                      f"+{sd}^2*({q}^2*{gp}^2+(1-{q})^2*{gm}^2-2*{rho}*{q}*(1-{q})*{gp}*{gm}))")
                out.append((wrap(f"{q}*{gp}-(1-{q})*{gm}"), row_vals[ci]))
                out.append((wrap(f"1-NORMSDIST((-{cr}-({q}*{gp}-(1-{q})*{gm}))/SQRT(MAX({vq},1E-300)))"),
                            row_vals[ci + 1]))
                ci += 2
            out.append((wrap(ntr), row_vals[ci]))
            out.append((wrap(f"IF({cls}*{T}>0,(SUMPRODUCT({AN},{Y},{AW})+{NR}*{cls}+{SP})/({cls}*{T}),0)"),
                        row_vals[ci + 1]))
            out.append((wrap(f"IF(SUM({SEG})=0,{NS},SUMPRODUCT({SEG},{AN},{Y}))"), row_vals[ci + 2]))
            out.append((wrap(f'IF(MIN({LOW})>=1E+98,"",MIN({LOW}))'), row_vals[ci + 3]))
            ci += 4
            AB = d["admits"]
            for b in bands:
                if b == "unscored":
                    f = f"SUMPRODUCT(({d['scored']}=0)*({AB}-{AN}))"
                else:
                    f = f"SUMPRODUCT(({d['scored']}=1)*({d['score_lo']}={b:g})*({AB}-{AN}))"
                out.append((wrap(f), row_vals[ci]))
                ci += 1
            out.append((status, row_vals[ci]))
            return out
        r0, r1 = self._strip_table(S, "class_table", self.head("OUT-129"), "n0", self.inp_list["class_what_if"],
                                   heads, fmts, gen)
        self.s_name("CT_CLASS_TABLE", r0, 2, r1, 2 + len(cols) - 1)

    def dist_cell(self, key, k, j):
        """Distribution's summary block cell of figure key, case k, scenario j (see w_distribution)."""
        i = [x[0] for x in self.DIST_ROWS].index(key)
        return ref("Distribution", 6 + i * len(CASES) + CASES.index(k), 2 + j)

    def sec_G(self, S):
        self.s_sec(self.sec_title("G"), self.lab_note(shock=False) + " Ratios are ratios of expected values. The "
                   "Distribution sheet has the full tables, merit aid by score band and the award steps.")
        self.s_scen_head(S)
        self.q_cref("OUT-029", "full_tuition_n", "n1")
        self.q_cref("OUT-030", "no_merit_award_n", "n1")
        self.q_cref("OUT-031", "barbell", "pct1")

        def tq(s):
            v = L.top_quartile_merit(self.run.lcs[s]["middle"])["top_quartile_merit_share"]
            return self.dist_cell("top_quartile_merit_share", "middle", S.index(s)), v
        self.q_row("OUT-153", tq, "pct1")
        self.flush("G")

    def sw_narratives(self, S):
        cfg = self.cfg
        self.s_sec(DD.lab("narratives_title"))
        width = 2 + max(len(S), 8)
        nt = len(cfg["score"]["median_thresholds"])
        ctx_x = {"shock_source": "in_shock_source"}
        for s in S:
            sc = self.run.scen(s)
            p = self.run.parents[s]
            # references
            r = {"pool_multiplier": self.LV(s, "pool_multiplier"),
                 "awards_ignored": ref("Levers", self.vrow_ignored, self.vblock[s])}
            if p is not None:
                r["awards_changed"] = ref("Levers", self.vrow_awards_changed, self.vblock[s])
                r["rates_changed"] = ref("Levers", self.vrow_rates_changed, self.vblock[s])
            if not self.dry:
                r.update({
                    "class_mean": self.cref("class_mean", "middle", s), "class_lo90": self.cref("class_lo90", "middle", s),
                    "class_hi90": self.cref("class_hi90", "middle", s), "score_measure": "in_score_measure",
                    "gpa_t": "in_gpa_median_threshold", "floor": "in_score_floor",
                    "below_floor": f"({self.fm('enrolled_below_floor', 'middle', s)})",
                    "ft": self.cref("full_tuition_n", "middle", s), "nm": self.cref("no_merit_award_n", "middle", s),
                    "ntr": self.cref("ntr_y1", "middle", s),
                    "ntr_lo": f"({self.fm('ntr_lo90', 'middle', s)})", "ntr_hi": f"({self.fm('ntr_hi90', 'middle', s)})",
                    "discount": self.cref("discount_entering_y1", "middle", s), "tuition": self.LH("middle", s, "T"),
                    "p": self.LV(s, "tuition_increase_pct"), "target": self.LV(s, "class_target"),
                    "cap": self.LV(s, "class_cap"), "bonus": self.LV(s, "bonus_usd"),
                    "scope": self.LV(s, "bonus_scope"), "segment_name": self.LH("middle", s, "seg"),
                    "segment_enrolled": self.cref("segment_enrolled", "middle", s),
                    "evidence": self.cref("evidence_extrapolated_share", "middle", s),
                })
                for i in range(nt):
                    r[f"t{i}"] = self.inp_list["median_thresholds"][i]
                    r[f"margin{i}"] = self.cref("margin_t", "middle", s, i)
                    r[f"p{i}"] = self.cref("p_median_t", "middle", s, i)
                gi = len(self.targets) - 1
                r["gpa_margin"] = self.cref("margin_t", "middle", s, gi)
                r["gpa_p"] = self.cref("p_median_t", "middle", s, gi)
            lr = {"shift": self.LV(s, "yield_shift_pts"), "shift_in": self.LV(s, "yield_shift_pts_in"),
                  "shift_out": self.LV(s, "yield_shift_pts_out"), "shift_segment": self.LV(s, "yield_shift_pts_segment"),
                  "lift": self.LV(s, "segment_pool_lift_pct"), "shock_source": "in_shock_source",
                  "s": "in_common_shock_sd", "segment_name": self.LH("middle", s, "seg"),
                  "segment_cells": f"SUM({self.LR('middle', s, 'in_seg')})",
                  "share_source": f'IF({self.LH("middle", s, "seg")}="","",INDEX(in_seg_share_source,'
                                  f'MATCH({self.LH("middle", s, "seg")},in_seg_names,0)))',
                  "target": self.LV(s, "class_target"), "sup_lo": self.inp_list["supported_range"][0],
                  "sup_hi": self.inp_list["supported_range"][1]}
            for kind in ("changes", "outcome"):
                self.s_txt(self.sr, 0, s if kind == "changes" else "", "hlt")
                self.s_txt(self.sr, 1, DD.label("OUT-130" if kind == "changes" else "OUT-131"), "tw")
                if not self.dry:
                    ws = self.ws["Summary"]
                    if kind == "changes":
                        f = NAR.formula(NAR.changes_parts(p is not None), r, ctx_x)
                        v = NAR.changes(self.run, self.vals, sc)
                    else:
                        f = NAR.formula(NAR.outcome_parts(nt, self.hold, self._held("enrolled_below_floor")), r,
                                        ctx_x) + "&" + \
                            NAR.labels_formula_parts(lr)
                        v = NAR.outcome(self.run, self.vals, sc)
                    ws.merge_range(self.sr, 2, self.sr, width, "", self.f["mergew"])
                    self.expected[("Summary", self.sr, 2)] = v
                    ws.write_formula(self.sr, 2, f, self.f["mergew"], -999 if self.sentinel else v)
                    ws.set_row(self.sr, 24 if kind == "changes" else 90)
                self.sr += 1
        for rid in ("OUT-130", "OUT-131"):
            self.printed.append(("H", rid, DD.label(rid)))

    def sec_H(self, S):
        self.Sn = S
        self.s_sec(self.sec_title("H"), self.lab_note() + " Rows moved here from sections A to G are grouped by the "
                   "section they belong to.")
        self.s_scen_head(S)
        self.q_cref("OUT-051", "evidence_extrapolated_share", "pct1")
        own, self.queue = self.queue, []
        for letter in "ABCDEFG":
            rows = sorted((x for x in self.h_rows if x[0] == letter), key=lambda x: DD.sort_key(x[1], x[2]))
            if not rows:
                continue
            self.s_txt(self.sr, 0, DD.lab("h_from", section=self.sec_title(letter)), "hl")
            self.sr += 1
            for _, rid, inst, lab, write in rows:
                self._emit("H", rid, inst, lab, write)
        if own:
            self.s_txt(self.sr, 0, DD.lab("h_response"), "hl")
            self.sr += 1
            for rid, inst, lab, write in sorted(own, key=lambda x: DD.sort_key(x[0], x[1])):
                self._emit("H", rid, inst, lab, write)
        r0, r1 = self.srow.get(("OUT-027", 0), (None,))[0], self.srow.get(("OUT-027", 1), (None,))[0]
        if r0 is not None:
            assert r1 == r0 + 1, "the spread band rows must be adjacent (SUM_PCT_BAND_Q)"
            self.s_name("SUM_PCT_BAND_Q", r0, 2, r1, 2 + len(S) - 1)
        self.sw_clip(S)

    def sw_definitions(self):
        """CP-3: every printed label with its plain definition (client_definition), by section."""
        self.s_sec(DD.lab("definitions_title"), DD.definition(DD.rid("definitions_title")))
        last = 1 + max(len(self.S), 6)
        seen = set()
        for letter in "ABCDEFGH":
            items = [(rid, lab) for sec, rid, lab in self.printed if sec == letter]
            if not items:
                continue
            self.s_txt(self.sr, 0, self.sec_title(letter), "hl")
            self.sr += 1
            for rid, lab in items:
                if lab in seen:
                    continue
                seen.add(lab)
                df = DD.definition(rid)
                self.s_label(self.sr, lab)
                if not self.dry:
                    # column B is left empty as a gutter, so a wrapped label never runs up against its definition
                    self.ws["Summary"].merge_range(self.sr, 2, self.sr, last, df, self.f["mergew"])
                    self.s_height(self.sr, 12 * max(1, math.ceil(len(df) * 1.1 / (SCEN_CHARS * (last - 1))),
                                                    math.ceil(len(lab) / LABEL_CHARS)))
                self.sr += 1

    def sw_notes(self):
        """Notes on method (CP-3): the section 4 labels in plain words and how ranges, ties and holds are read; no
        review IDs or config keys (Phase 4.2, section 7)."""
        N = labels.LEGEND_NAMES
        self.s_sec(DD.lab("notes_title"))
        self.s_txt(self.sr, 0, N["SHOCK_LABEL"], "hl")
        # [v0.6.2, P2-04] the template filled in from Inputs (live)
        last = 1 + max(len(self.S), 6)
        if not self.dry:
            self.ws["Summary"].merge_range(self.sr, 1, self.sr, last, "", self.f["mergew"])
        self.s_fx(self.sr, 1, NAR.template_formula(labels.SHOCK_LABEL, {"s": "in_common_shock_sd"}),
                  labels.shock_label(self.cfg["risk"]["common_shock_sd"]), "mergew")
        self.sr += 1
        items = [(N[k], getattr(labels, k)) for k in ("RESPONSE_LABEL", "ASSUMPTION_LABEL", "SEGMENT_SHARE_LABEL",
                                                       "PCT_APPROX_LABEL", "BAND_NOT_SCORE_LABEL", "CONTINUING_LABEL",
                                                       "POOL_BREAKEVEN_LABEL")]
        items += [("Range kind", f"{labels.RANGE_OUTCOME} ({labels.RANGE_OUTCOME_NOTE})"),
                  ("Range kind", f"{labels.RANGE_CASES} ({labels.RANGE_CASES_NOTE}); their rows read 'if admitted "
                                 "students respond less to aid' (Low) and 'if admitted students respond more to aid' "
                                 "(High)"),
                  ("Probability display", labels.LEGEND_PROB.format(under=labels.PROB_UNDER, over=labels.PROB_OVER)),
                  ("Need aid", labels.LEGEND_NEED),
                  ("Tie rule", labels.LEGEND_TIE.format(rule=labels.PCT_TIE_RULE)),
                  ("Cushion", "a median cushion is students at or above the target minus students below it; a "
                              "percentile cushion counts " + labels.PCT_MARGIN_SWAPS),
                  ("Held figures", labels.LEGEND_HELD.format(hold=labels.HOLD_POSITION,
                                                             state="held" if self.hold else "not held"))]
        # R4-02: the explanation is merged across the scenario columns and wrapped, so it is not cut
        for a, b in items:
            self.s_txt(self.sr, 0, a, "hl")
            if not self.dry:
                self.ws["Summary"].merge_range(self.sr, 1, self.sr, last, b, self.f["mergew"])
                self.s_height(self.sr, 12 * max(1, math.ceil(len(b) * 1.1 / (10 * 1.1 + SCEN_CHARS * (last - 1)))))
            self.sr += 1


    def sw_pool_parts(self, S):
        """R4-01: the pool strip's split at m = 1 (lo part below score.pool_threshold, hi part at or above), working
        values the strip and the break-evens read. Last on Summary, outside its print area and the PDF render. F-1:
        under hold_position_rows the median and percentile parts (Gp, Gm, Vm, Vp) read labels.HOLD_POSITION; the strip's
        held columns and m_median, m_q do not read them."""
        cfg = self.cfg
        meds = cfg["score"]["median_thresholds"]
        pq = K.ct_ptargets(cfg)
        self.s_sec(POOL_PARTS_TITLE, self.lab_note() + " Working values for the pool strip: each scenario's Ledger "
                   "(Middle case) at pool multiplier 1, split into the part below score.pool_threshold (lo) and the "
                   "part at or above it (hi). M expected class, V binomial variance, W expected sum of (tuition - "
                   "award - need rate), Vn its variance; then, for each median threshold, Gp and Gm expected enrolled "
                   "at or above and below it and Vm their variance; then Gp, Gm, Vp and Vm for each percentile target "
                   "other than the median.")
        self.pool_parts_row = self.sr
        pk = ["M", "V", "W", "Vn"]
        pfmt = {"M": "n1", "V": "n1", "W": "usd", "Vn": "sci"}
        mk = [(i, x) for i in range(len(meds)) for x in ("Gp", "Gm", "Vm")]
        qk = [(j, x) for j, _ in pq for x in ("Gp", "Gm", "Vp", "Vm")]
        self.s_txt(self.sr, 0, "scenario: split at m = 1", "h")
        self.s_txt(self.sr, 1, "part", "h")
        for c, h in enumerate(pk):
            self.s_txt(self.sr, 2 + c, h, "h")
        for c, (i, x) in enumerate(mk):
            self.s_txt(self.sr, 2 + len(pk) + c, f"{x} median {meds[i]:g}", "h")
        for c, (j, x) in enumerate(qk):
            q, t = self.ptargets[j]
            self.s_txt(self.sr, 2 + len(pk) + len(mk) + c, f"{x} q {q:g}, t {t:g}", "h")
        self.s_height(self.sr, 36)
        self.sr += 1
        for s in S:
            d = self.g("middle", s)
            A1 = self.LR("middle", s, "admits_pool1")
            Y, W, U = d["yield"], d["w"], d["upper"]
            ps = self.vals["strips"][s]["pool_strip"] if not self.dry else None
            for part, u in (("lo", 0), ("hi", 1)):
                self.s_txt(self.sr, 0, s)
                self.s_txt(self.sr, 1, part)
                m = f"({U}={u})"
                fs = {"M": f"SUMPRODUCT({m}*{A1}*{Y})", "V": f"SUMPRODUCT({m}*{A1}*{Y}*(1-{Y}))",
                      "W": f"SUMPRODUCT({m}*{W}*{A1}*{Y})", "Vn": f"SUMPRODUCT({m}*{W}*{W}*{A1}*{Y}*(1-{Y}))"}
                for c, key in enumerate(pk):
                    v = ps["parts"][part][key] if not self.dry else 0
                    self.s_fx(self.sr, 2 + c, fs[key], v, pfmt[key])
                    self.pool_parts[(s, part, key)] = a1(self.sr, 2 + c)
                c0 = 2 + len(pk)
                for c, (i, x) in enumerate(mk):
                    G = d[f"g{i}"]
                    f = {"Gp": f"SUMPRODUCT({m}*({G}=1)*{A1}*{Y})", "Gm": f"SUMPRODUCT({m}*({G}=-1)*{A1}*{Y})",
                         "Vm": f"SUMPRODUCT({m}*({G}<>0)*{A1}*{Y}*(1-{Y}))"}[x]
                    self.pool_parts[(s, part, f"{x}_m{i}")] = a1(self.sr, c0 + c)
                    if self.hold:                                                     # F-1
                        self.s_hold_cells(self.sr, c0 + c, 1, merge=False)
                    else:
                        v = ps["med_parts"][meds[i]][part][x] if not self.dry else 0
                        self.s_fx(self.sr, c0 + c, f, v, "n1")
                c0 += len(mk)
                for c, (j, x) in enumerate(qk):
                    P_ = d[f"p{j}"]
                    sgn = "=1" if x in ("Gp", "Vp") else "=-1"
                    var = f"*(1-{Y})" if x in ("Vp", "Vm") else ""
                    self.pool_parts[(s, part, f"{x}{j}")] = a1(self.sr, c0 + c)
                    if self.hold:                                                     # F-1
                        self.s_hold_cells(self.sr, c0 + c, 1, merge=False)
                    else:
                        v = ps["pct_parts"][self.ptargets[j]][part][x] if not self.dry else 0
                        self.s_fx(self.sr, c0 + c, f"SUMPRODUCT({m}*({P_}{sgn})*{A1}*{Y}{var})", v, "n1")
                self.sr += 1

    def sw_contract(self, S):
        self.s_sec(CONTRACT_TITLE,
                   self.lab_note() + " "
                   "Named ranges: prefix plus the contract name in upper case; rows are cases (and thresholds), "
                   "columns are scenarios. The policy document and any later dashboard read these ranges. The "
                   f"_LO90 and _HI90 rows are the {labels.RANGE_OUTCOME} ({labels.RANGE_OUTCOME_NOTE}); the Low "
                   f"and High rows are the {labels.RANGE_CASES} ({labels.RANGE_CASES_NOTE}).")
        self.s_scen_head(S, "contract name (range)", "case")
        for name, prefix, _ in K.SK:
            self._contract_block(S, name, prefix, None)
        for name, prefix, _ in K.SKT:
            self._contract_block(S, name, prefix, list(range(len(self.targets))))
        self._contract_block(S, "share_at_or_above_t", "SUM", list(range(len(self.score_ts))))
        for name, prefix, _ in K.SKQ:                                        # [v0.6.3, BM-1]; F-4: q = 0.5 left out
            self._contract_block(S, name, prefix, [j for j, _ in K.ct_ptargets(self.cfg)])

    def _contract_block(self, S, name, prefix, tis):
        rn = K.range_name(name, prefix)
        r0 = self.sr
        fmt = ("prob" if name.startswith("p_") else "pct1" if ("share" in name or "discount" in name)
               else "usd" if name in ("gross_y1", "merit", "need", "specialty", "aid", "ntr_y1", "avg_aid",
                                      "incentive_cost", "incentive_paid_anyway", "aid_per_additional",
                                      "ntr_per_additional")
               else "r3" if name == "barbell" else "t" if name == "incentive_valid" else "n1")
        for ti in (tis if tis is not None else [None]):
            for k in CASES:
                if ti is None:
                    lab = rn
                else:
                    if name == "share_at_or_above_t":
                        lab = f"{rn} [{self.score_ts[ti]:g}]"
                    elif name in ("margin_q_t", "p_pct_q_t", "p_pct_q_t_rho05"):
                        q, t = self.ptargets[ti]
                        lab = f"{rn} [q {q:g}, t {t:g}]"
                    else:
                        m, t = self.targets[ti]
                        lab = f"{rn} [{'GPA ' if m == 'gpa' else ''}{t:g}]"
                self.s_txt(self.sr, 0, lab)
                self.s_txt(self.sr, 1, CASE_TITLE[k])
                held = self._held(name, ti)                               # R4-06: every cell of the range
                for j, s in enumerate(S):
                    if self.dry:
                        self.cpos[(name, k, s, ti)] = (self.sr, 2 + j)
                    elif not held:
                        self.s_fx(self.sr, 2 + j, self.fm(name, k, s, ti), self.pv(name, k, s, ti), fmt)
                if held:
                    self.s_hold_cells(self.sr, 2, len(S), merge=False)
                self.sr += 1
        self.s_name(rn, r0, 2, self.sr - 1, 2 + len(S) - 1)

    # ------------------------------------------------------------------------------------------------------------
    # Overview and Charts (spec v0.6.4 section 0B, CP-4 and CP-5; live builds only)

    # One color per scenario, the same in every chart; Baseline neutral grey; the rest the Okabe-Ito color-blind-safe
    # palette (no red and green coding of good and bad: colors name scenarios, never outcomes)
    PALETTE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000"]
    BASE_GREY = "#8C8C8C"
    REF_LINE = "#404040"

    def scen_color(self, j):
        return self.BASE_GREY if j == 0 else self.PALETTE[(j - 1) % len(self.PALETTE)]

    def ow_fmt(self, fmt):
        """CP-4: an Overview figure format that wraps, so a text result (a note in a figure column) stays in its cell;
        probabilities keep format 'prob' (the clamp display reads it)."""
        if fmt == "prob":
            return fmt
        key = f"ow_{fmt}"
        if key not in self.f:
            nf = {"usd": "$#,##0", "n1": "#,##0.0", "n0": "#,##0", "pct1": "0.0%", "pp": "0.0", "r3": "0.000",
                  "int": "0"}.get(fmt, "General")
            self.f[key] = self.wb.add_format({"font_name": "Arial", "font_size": 9, "num_format": nf,
                                              "text_wrap": True, "align": "right"})
        return key

    def overview_rows(self):
        """CP-4: the headline rows of sections A to E as (section, row id, instance), in section and dictionary order;
        the likely-range pairs become one 'lo to hi' row; section D only with a segment configured, section E only
        when some scenario has an incentive."""
        has_seg = bool(self.cfg["segments"])
        has_inc = any((s.bonus_usd or 0) > 0 for s in self.S)
        keys = [k for k in self.srow if DD.tier(k[0]) == "headline" and DD.section(k[0]) in "ABCDE"
                and not k[0].startswith("IN-")]
        keys = [k for k in keys if k[0] not in ("OUT-009", "OUT-010", "OUT-039", "OUT-040")]
        keys = [k for k in keys if (DD.section(k[0]) != "D" or has_seg) and (DD.section(k[0]) != "E" or has_inc)]
        keys += [(DD.rid("overview_range_class"), 0), (DD.rid("overview_range_ntr"), 0)]
        return sorted(keys, key=lambda k: (DD.section(k[0]), DD.order(k[0]), k[1]))

    def w_overview(self):
        sh = "Overview"
        ws = self.ws[sh]
        S = [s.name for s in self.S]
        nS = len(S)
        last = 1 + nS
        ws.set_column(0, 0, 40)
        ws.set_column(1, 1, 46)
        ws.set_column(2, last, 14)
        self.txt(sh, 0, 0, DD.lab("overview_title"), "title")
        note = (labels.RESPONSE_LABEL + ". " + DD.lab("case_note") + " Every figure is a formula on the Summary "
                "sheet, which has the full tables, the definitions and the notes on method; charts are on the Charts "
                "sheet.")
        if self.cfg["risk"]["shock_source"] == "illustrative":
            note += " " + labels.shock_label(self.cfg["risk"]["common_shock_sd"]) + "; " + labels.LEGEND_PROB.format(
                under=labels.PROB_UNDER, over=labels.PROB_OVER) + "."
        ws.merge_range(1, 0, 1, last, note, self.f["notew"])
        ws.set_row(1, 12 * max(2, math.ceil(len(note) / 170)))
        hr = 2
        self.txt(sh, hr, 0, "figure", "h")
        self.txt(sh, hr, 1, DD.lab("overview_meaning_head"), "h")
        for j, s in enumerate(S):
            self.txt(sh, hr, 2 + j, s, "h")
        ws.set_row(hr, 36)
        r = hr + 1
        cur = None
        self.overview_cells = {}
        for rid_, inst in self.overview_rows():
            sec = DD.section(rid_)
            if sec != cur:
                cur = sec
                self.txt(sh, r, 0, self.sec_title(sec), "sec")
                for c in range(1, last + 1):
                    ws.write_blank(r, c, None, self.f["sec"])
                r += 1
            df = DD.definition(rid_)
            if rid_ in (DD.rid("overview_range_class"), DD.rid("overview_range_ntr")):
                lab = DD.label(rid_)
                lo_k, hi_k = (("OUT-009", "OUT-010") if rid_ == DD.rid("overview_range_class") else
                              ("OUT-039", "OUT-040"))
                rlo, rhi = self.srow[(lo_k, 0)][0], self.srow[(hi_k, 0)][0]
                money = lo_k == "OUT-039"
                for j in range(nS):
                    clo, chi = ref("Summary", rlo, 2 + j), ref("Summary", rhi, 2 + j)
                    vlo, vhi = self.expected[("Summary", rlo, 2 + j)], self.expected[("Summary", rhi, 2 + j)]
                    if money:
                        f = (f'"$"&TEXT({clo}/1000000,"#,##0.00")&"M to $"&TEXT({chi}/1000000,"#,##0.00")&"M"')
                        v = f"${labels.xl(vlo / 1e6, 2):,.2f}M to ${labels.xl(vhi / 1e6, 2):,.2f}M"
                    else:
                        f = f'TEXT({clo},"#,##0")&" to "&TEXT({chi},"#,##0")'
                        v = f"{labels.xl(vlo):,.0f} to {labels.xl(vhi):,.0f}"
                    self.fx(sh, r, 2 + j, f, v, "tr")
                    self.overview_cells[(rid_, inst, j)] = (r, 2 + j)
            else:
                srow, fmt, held, lab = self.srow[(rid_, inst)]
                if held:
                    # R4-06: a held figure reads the hold text, one formula on the Summary's merged hold cell
                    ws.merge_range(r, 2, r, last, "", self.f["hold"])
                    self.fx(sh, r, 2, ref("Summary", srow, 2), labels.HOLD_POSITION, "hold")
                    self.overview_cells[(rid_, inst, 0)] = (r, 2)
                else:
                    for j in range(nS):
                        self.fx(sh, r, 2 + j, ref("Summary", srow, 2 + j), self.expected[("Summary", srow, 2 + j)],
                                self.ow_fmt(fmt))
                        self.overview_cells[(rid_, inst, j)] = (r, 2 + j)
            self.txt(sh, r, 0, lab, "lw")
            self.txt(sh, r, 1, df, "lw")
            lines = max(math.ceil(len(df) / 60), math.ceil(len(lab) / 52), 1)
            ws.set_row(r, 12 * lines + 2)
            r += 1
        self.overview_last_row = r - 1
        ws.repeat_rows(hr)
        ws.print_area(0, 0, r - 1, last)
        ws.freeze_panes(hr + 1, 2)

    def _chart_note(self, *parts):
        """A chart's note: the section 4 labels that apply and how to read the chart, as sentences."""
        out = []
        for p in parts:
            if p:
                p = p[0].upper() + p[1:]
                out.append(p if p.endswith(".") else p + ".")
        return " ".join(out)

    def w_charts(self):
        """CP-5: eight native charts (chart 4 with its companion), linked to Summary, strip and Distribution cells
        through the chart-data block below the print area (every cell there a formula), printed in the PDF."""
        sh = "Charts"
        ws = self.ws[sh]
        cfg = self.cfg
        S = [s.name for s in self.S]
        nS = len(S)
        meas = cfg["score"]["measure"]
        illus = cfg["risk"]["shock_source"] == "illustrative"
        shock = labels.shock_label(cfg["risk"]["common_shock_sd"]) if illus else ""
        # 15 columns of width 9 (68 px in Excel; LibreOffice draws them about 13% wider and stretches the charts with
        # them, so the print scale below leaves room for that)
        for c in range(0, 15):
            ws.set_column(c, c, 9)
        self.txt(sh, 0, 0, DD.lab("charts_title"), "title")
        top_note = self._chart_note(labels.RESPONSE_LABEL, DD.lab("case_note"), shock)
        ws.merge_range(1, 0, 1, 14, top_note, self.f["notew"])
        ws.set_row(1, 24)
        # ---- chart data (below the print area) ------------------------------------------------------------------
        # page 1: class and revenue side by side, the chances full width; page 2: applications (and its companion),
        # yield and tuition; page 3: class size and merit. A normal chart is 13 rows tall, the chances chart 16;
        # each note takes the three rows under its chart
        N_H, W_H = 17, 20
        P1, P2, P3 = 3, 3 + N_H + W_H, 3 + N_H + W_H + 2 * N_H
        r_end = P3 + N_H
        r_data = r_end + 2
        self.txt(sh, r_data, 0, DD.lab("chart_data"), "hl")
        r = r_data + 1
        self.chart_data = {}
        # scenario names (categories)
        self.txt(sh, r, 0, "scenario", "h")
        for j, s in enumerate(S):
            self.txt(sh, r, 1 + j, s, "h")
        r_names = r
        names_rng = rng(sh, r, 1, r, nS)
        r += 1

        def srow(k, inst=0):
            return self.srow[(k, inst)][0]

        def data_row(label, cells_values, fmt="num", key=None):
            """One chart-data row: label in column A, one formula per scenario."""
            nonlocal r
            self.txt(sh, r, 0, label)
            for j, (f, v) in enumerate(cells_values):
                self.fx(sh, r, 1 + j, f, v, fmt)
            if key:
                self.chart_data[key] = (r, 1, r, len(cells_values))
            r += 1
            return r - 1

        def num_or_na(cell, v):
            return f"IF(ISNUMBER({cell}),{cell},NA())", (v if isinstance(v, (int, float)) and v != "" else "#N/A")

        def ex(row, j):
            return self.expected.get(("Summary", row, 2 + j))
        # error bars: likely range (90%) as distances from the expected value
        for key, mk, lok, hik in (("class", "OUT-008", "OUT-009", "OUT-010"), ("ntr", "OUT-038", "OUT-039", "OUT-040")):
            rm, rl, rh = srow(mk), srow(lok), srow(hik)
            data_row(f"{DD.label(hik)}: distance above the expected value",
                     [(f"{ref('Summary', rh, 2 + j)}-{ref('Summary', rm, 2 + j)}", ex(rh, j) - ex(rm, j))
                      for j in range(nS)], "num", f"{key}_plus")
            data_row(f"{DD.label(lok)}: distance below the expected value",
                     [(f"{ref('Summary', rm, 2 + j)}-{ref('Summary', rl, 2 + j)}", ex(rm, j) - ex(rl, j))
                      for j in range(nS)], "num", f"{key}_minus")
        rg = srow("OUT-042")
        data_row(DD.label("OUT-042"), [num_or_na(ref("Summary", rg, 2 + j), ex(rg, j)) for j in range(nS)], "num",
                 "goal")
        # chance matrix (chart 3): rows are outcomes, columns scenarios; held measures are left out (R4-06)
        outcomes = [("OUT-011", 0, DD.label("OUT-011"))]
        if cfg.get("ntr_target") is not None:
            outcomes.append(("OUT-043", 0, DD.label("OUT-043")))
        seg_goal = bool(cfg["segments"]) and any(s.segment_goal is not None for s in self.S)
        if seg_goal:
            outcomes.append(("OUT-061", 0, DD.label("OUT-061")))
        if not self.hold:
            for ti in range(len(self.targets)):
                outcomes.append(("OUT-020", ti, self.srow[("OUT-020", ti)][3]))
        r_ch0 = r
        for k, inst, lab in outcomes:
            rr = srow(k, inst)
            data_row(lab, [num_or_na(ref("Summary", rr, 2 + j), ex(rr, j)) for j in range(nS)], "prob")
        self.chart_data["chances"] = (r_ch0, 0, r - 1, nS)
        # reference lines on the strip charts: the cap across the grid, the growth-to-date marker
        cap = cfg["class"]["cap"]
        pg, yg = cfg["risk"]["pool_grid"], cfg["risk"]["yield_shift_grid"]
        r_cap = r
        self.txt(sh, r, 0, "Class cap line: application multiple, yield change, class cap")
        self.fx(sh, r, 1, "MIN(in_pool_grid)", min(pg), "num")
        self.fx(sh, r, 2, "MAX(in_pool_grid)", max(pg), "num")
        self.fx(sh, r, 3, "MIN(in_yield_shift_grid)", min(yg), "num")
        self.fx(sh, r, 4, "MAX(in_yield_shift_grid)", max(yg), "num")
        self.fx(sh, r, 5, "in_class_cap", cap, "num")
        self.fx(sh, r, 6, "in_class_cap", cap, "num")
        r += 1
        p0, p1, ng = self.strip_pos["pool_strip"]
        pc = rng("Summary", p0, 3, p1, 3)
        vals_pc = [self.expected[("Summary", rr, 3)] for rr in range(p0, p1 + 1)]
        nearest = self.vals["strips"][S[0]]["pool_strip"]["nearest_m"]
        nv = nearest if isinstance(nearest, (int, float)) else "#N/A"
        nc = ref("Summary", self.pool_nearest_row, 4)
        r_mark = r
        self.txt(sh, r, 0, "Growth-to-date marker: application multiple (twice), low and high end of the line")
        self.chart_marker_cells = [(sh, r, 1), (sh, r, 2)]
        self.fx(sh, r, 1, f"IF(ISNUMBER({nc}),{nc},NA())", nv, "num")
        self.fx(sh, r, 2, f"IF(ISNUMBER({nc}),{nc},NA())", nv, "num")
        self.fx(sh, r, 3, f"MIN({pc})*0.97", min(vals_pc) * 0.97, "num")
        self.fx(sh, r, 4, f"MAX({pc})*1.03", max(vals_pc) * 1.03, "num")
        r += 1
        # class-size chart: the scenario chosen on Inputs (in_chart_scenario)
        r_cs = None
        if "class_table" in self.strip_pos:
            c0, c1, nN = self.strip_pos["class_table"]
            ncols = K.strip_columns(cfg)["class_table"]
            ci = 2 + ncols.index("ntr_y1")
            col = rng("Summary", c0, ci, c1, ci)
            sel0 = 0                                            # Inputs in_chart_scenario starts at Baseline
            r_cs = r
            self.txt(sh, r, 0, "Class-size chart: class size, first-year net tuition revenue ($) for the scenario "
                               "chosen on Inputs")
            self.fx(sh, r, 1, "in_chart_scenario", S[sel0], "t")
            r += 1
            for gi in range(nN):
                v = self.expected[("Summary", c0 + sel0 * nN + gi, ci)]
                self.fx(sh, r, 0, self.inp_list["class_what_if"][gi], cfg["class"]["what_if"][gi], "n0")
                self.fx(sh, r, 1, f"IF(ISNUMBER(MATCH(in_chart_scenario,{names_rng},0)),IF(ISNUMBER(INDEX({col},"
                                  f"(MATCH(in_chart_scenario,{names_rng},0)-1)*{nN}+{gi + 1})),INDEX({col},"
                                  f"(MATCH(in_chart_scenario,{names_rng},0)-1)*{nN}+{gi + 1}),NA()),NA())",
                        v if isinstance(v, (int, float)) else "#N/A", "usd")
                r += 1
        self.chart_data_end = r - 1
        # ---- charts -------------------------------------------------------------------------------------------------
        wb = CH.Recorder()                      # recorded, then drawn here and (from the sidecar) in the PDF render
        # chart number (spec order, chart 4 then its companion) -> (row, column, width, height in pixels)
        W1, W2 = 462, 940
        pos = {0: (P1, 0, W1, 260), 1: (P1, 7, W1, 260), 2: (P1 + N_H, 0, W2, 320),
               3: (P2, 0, W1, 260), 4: (P2, 7, W1, 260), 6: (P2 + N_H, 7, W1, 260), 7: (P2 + N_H, 0, W1, 260),
               5: (P3, 0, W1, 260), 8: (P3, 7, W1, 260)}
        self.chart_meta = []
        clamp = '[<0.05]"under 5%";[>0.95]"over 95%";0%' if illus else "0%"
        tfont = {"name": "Arial", "size": 11, "bold": True}
        afont = {"name": "Arial", "size": 8}

        def place(k, chart, title_rid, note, refs, legend=True):
            row, col, w, h = pos[k]
            chart.set_title({"name": DD.label(title_rid), "name_font": tfont})
            chart.set_size({"width": w, "height": h})
            chart.set_chartarea({"border": {"none": True}})
            chart.set_legend({"position": "bottom", "font": afont} if legend else {"none": True})
            wb.insert(row, col, chart, {"x_offset": 6, "y_offset": 2, "object_position": 1})
            nr = (h + 19) // 20
            ws.merge_range(row + nr, col, row + nr + 2, col + (13 if w > 600 else 6), note, self.f["notew"])
            self.chart_meta.append({"title": DD.label(title_rid), "note": note, "refs": refs, "pos": (row, col)})

        Q = lambda r0_, c0_, r1_, c1_, s_=sh: rng(s_, r0_, c0_, r1_, c1_)  # noqa: E731
        short = lambda t: t.split(" (")[0]  # noqa: E731   a reference line's name without its unit
        sumrow = lambda k, inst=0: rng("Summary", srow(k, inst), 2, srow(k, inst), 1 + nS)  # noqa: E731
        cats = names_rng
        case_note = DD.lab("case_note")
        # 1. How large will the class be?
        ch = wb.add_chart({"type": "column"})
        cp, cm = self.chart_data["class_plus"], self.chart_data["class_minus"]
        ch.add_series({"name": DD.label("OUT-008"), "categories": cats, "values": sumrow("OUT-008"),
                       "points": [{"fill": {"color": self.scen_color(j)}} for j in range(nS)],
                       "y_error_bars": {"type": "custom", "plus_values": Q(*cp), "minus_values": Q(*cm),
                                        "end_style": 1, "line": {"color": self.REF_LINE, "width": 1}},
                       "gap": 80})
        ln = wb.add_chart({"type": "line"})
        lab_last = {"series_name": True, "position": "above", "font": afont,
                    "custom": [{"delete": True}] * (nS - 1) + [None]}
        lab_first = {"series_name": True, "position": "below", "font": afont,
                     "custom": [None] + [{"delete": True}] * (nS - 1)}
        # the cap as a line across the scenarios, labelled above its last point; each scenario's target as a short
        # dash on its bar, labelled below the first
        ln.add_series({"name": short(DD.label("IN-099")), "categories": cats, "values": sumrow("IN-099"),
                       "line": {"color": self.REF_LINE, "dash_type": "dash", "width": 1.5}, "marker": {"type": "none"},
                       "data_labels": lab_last})
        ln.add_series({"name": short(DD.label("IN-098")), "categories": cats, "values": sumrow("IN-098"),
                       "line": {"none": True},
                       "marker": {"type": "dash", "size": 14, "fill": {"color": self.REF_LINE},
                                  "border": {"color": self.REF_LINE}}, "data_labels": lab_first})
        ch.combine(ln)
        ch.set_y_axis({"min": 0, "num_format": "#,##0", "num_font": afont, "major_gridlines": {"visible": True,
                       "line": {"color": "#D9D9D9"}}})
        ch.set_x_axis({"num_font": afont})
        place(0, ch, DD.rid("chart_class"), self._chart_note(labels.RESPONSE_LABEL, shock, case_note),
              {"values": sumrow("OUT-008"), "plus": Q(*cp), "minus": Q(*cm), "cap": sumrow("IN-099"),
               "target": sumrow("IN-098"), "categories": cats}, legend=False)
        # 2. How much first-year net tuition revenue?
        ch = wb.add_chart({"type": "column"})
        npl, nmi = self.chart_data["ntr_plus"], self.chart_data["ntr_minus"]
        ch.add_series({"name": DD.label("OUT-038"), "categories": cats, "values": sumrow("OUT-038"),
                       "points": [{"fill": {"color": self.scen_color(j)}} for j in range(nS)],
                       "y_error_bars": {"type": "custom", "plus_values": Q(*npl), "minus_values": Q(*nmi),
                                        "end_style": 1, "line": {"color": self.REF_LINE, "width": 1}},
                       "gap": 80})
        refs2 = {"values": sumrow("OUT-038"), "plus": Q(*npl), "minus": Q(*nmi), "categories": cats}
        if cfg.get("ntr_target") is not None:
            ln = wb.add_chart({"type": "line"})
            ln.add_series({"name": short(DD.label("OUT-042")), "categories": cats,
                           "values": Q(*self.chart_data["goal"]),
                           "line": {"color": self.REF_LINE, "dash_type": "dash", "width": 1.5},
                           "marker": {"type": "none"}, "data_labels": lab_last})
            ch.combine(ln)
            refs2["goal"] = Q(*self.chart_data["goal"])
        ch.set_y_axis({"min": 0, "num_format": '"$"#,##0.0,,"M"', "num_font": afont,
                       "major_gridlines": {"visible": True, "line": {"color": "#D9D9D9"}}})
        ch.set_x_axis({"num_font": afont})
        place(1, ch, DD.rid("chart_ntr"), self._chart_note(labels.RESPONSE_LABEL, shock, case_note), refs2,
              legend=False)
        # 3. How likely is each outcome?
        ch = wb.add_chart({"type": "bar"})
        a0, _, a1_, _ = self.chart_data["chances"]
        refs3 = {"categories": Q(a0, 0, a1_, 0), "series": []}
        for j in range(nS):
            v = Q(a0, 1 + j, a1_, 1 + j)
            ch.add_series({"name": S[j], "categories": Q(a0, 0, a1_, 0), "values": v,
                           "fill": {"color": self.scen_color(j)}, "border": {"none": True},
                           "data_labels": {"value": True, "num_format": clamp,
                                           "font": {"name": "Arial", "size": 7}, "position": "outside_end"}})
            refs3["series"].append(v)
        # XlsxWriter's bar chart: x_axis is the horizontal value axis, y_axis the vertical category axis (outcomes
        # top to bottom in list order, the value axis kept at the foot)
        ch.set_x_axis({"min": 0, "max": 1, "num_format": "0%", "num_font": afont,
                       "major_gridlines": {"visible": True, "line": {"color": "#D9D9D9"}}})
        ch.set_y_axis({"reverse": True, "num_font": afont, "crossing": "max"})
        n3 = [labels.RESPONSE_LABEL, shock, case_note]
        if illus:
            n3.append(labels.LEGEND_PROB.format(under=labels.PROB_UNDER, over=labels.PROB_OVER))
        if seg_goal and cfg["segments"][0]["share_source"] == "assumed":
            n3.append(labels.SEGMENT_SHARE_LABEL)
        if self.hold:
            n3.append("Median and percentile targets are not drawn: " + labels.HOLD_POSITION)
        place(2, ch, DD.rid("chart_chances"), self._chart_note(*n3), refs3)
        # strip charts: one series per scenario over its own rows of the strip table
        def strip_series(which, col_name):
            r0_, _, ng_ = self.strip_pos[which]
            ci_ = 2 + K.strip_columns(cfg)[which].index(col_name)
            out = []
            for j in range(nS):
                ra, rb = r0_ + j * ng_, r0_ + (j + 1) * ng_ - 1
                out.append((rng("Summary", ra, 1, rb, 1), rng("Summary", ra, ci_, rb, ci_)))
            return out

        def scatter(which, col_name, title_rid, note, k, y_fmt, x_fmt, cap_x=None, y01=False, marker=False,
                    xgrid=(0, 1), y_min=None):
            c = wb.add_chart({"type": "scatter", "subtype": "straight_with_markers"})
            refs = {"series": []}
            for j, (xr, yr) in enumerate(strip_series(which, col_name)):
                c.add_series({"name": S[j], "categories": xr, "values": yr,
                              "line": {"color": self.scen_color(j), "width": 2},
                              "marker": {"type": "circle", "size": 4, "fill": {"color": self.scen_color(j)},
                                         "border": {"color": self.scen_color(j)}}})
                refs["series"].append((xr, yr))
            if cap_x is not None:
                xr = Q(r_cap, cap_x, r_cap, cap_x + 1)
                yr = Q(r_cap, 5, r_cap, 6)
                c.add_series({"name": short(DD.label("IN-099")), "categories": xr, "values": yr,
                              "line": {"color": self.REF_LINE, "dash_type": "dash", "width": 1.5},
                              "marker": {"type": "none"},
                              "data_labels": {"series_name": True, "position": "above", "font": afont,
                                              "custom": [{"delete": True}, None]}})
                refs["cap"] = (xr, yr)
            if marker:
                xr, yr = Q(r_mark, 1, r_mark, 2), Q(r_mark, 3, r_mark, 4)
                c.add_series({"name": DD.label("OUT-108"), "categories": xr, "values": yr,
                              "line": {"color": self.REF_LINE, "dash_type": "round_dot", "width": 1.25},
                              "marker": {"type": "none"},
                              "data_labels": {"series_name": True, "position": "right", "font": afont,
                                              "custom": [{"delete": True}, None]}})
                refs["marker"] = (xr, yr)
            ya = {"num_format": y_fmt, "num_font": afont, "major_gridlines": {"visible": True,
                                                                          "line": {"color": "#D9D9D9"}}}
            if y01:
                ya.update({"min": 0, "max": 1})
            elif y_min is not None:
                ya["min"] = y_min
            c.set_y_axis(ya)
            c.set_x_axis({"num_format": x_fmt, "num_font": afont, "crossing": "min",
                          "min": min(xgrid), "max": max(xgrid)})
            place(k, c, title_rid, note, refs)
        pth = format(cfg["score"]["pool_threshold"], "g")
        pool_note = self._chart_note(labels.RESPONSE_LABEL, shock, case_note, labels.POOL_STRIP_LABEL[0].upper()
                                     + labels.POOL_STRIP_LABEL[1:], f"Horizontal axis: applications at {meas} {pth} "
                                     "or higher as a multiple of last year", labels.POOL_YTD_LABEL[0].upper()
                                     + labels.POOL_YTD_LABEL[1:])
        # 4. What if applications grow more or less? and its companion
        def floor10(vals):
            """A fixed lower axis bound under the build's values (a line chart need not start at zero)."""
            v = [x for x in vals if isinstance(x, (int, float))]
            return 10 * math.floor(0.85 * min(v + [cap]) / 10) if v else None
        ys = [self.expected[("Summary", rr, 3)] for rr in range(p0, p1 + 1)]
        scatter("pool_strip", "class_mean", DD.rid("chart_pool"), pool_note, 3, "#,##0", "0.0", cap_x=1, marker=True,
                xgrid=pg, y_min=floor10(ys))
        scatter("pool_strip", "p_class_over_cap", DD.rid("chart_pool_cap"), pool_note, 4, "0%", "0.0", y01=True,
                xgrid=pg)
        # 5. What does a smaller class cost?
        if r_cs is not None:
            c = wb.add_chart({"type": "line"})
            xr, yr = Q(r_cs + 1, 0, r_cs + nN, 0), Q(r_cs + 1, 1, r_cs + nN, 1)
            c.add_series({"name": [sh, r_cs, 1], "categories": xr, "values": yr,
                          "line": {"color": "#333333", "width": 2},
                          "marker": {"type": "circle", "size": 5, "fill": {"color": "#333333"},
                                     "border": {"color": "#333333"}}})
            c.set_y_axis({"num_format": '"$"#,##0.0,,"M"', "num_font": afont,
                          "major_gridlines": {"visible": True, "line": {"color": "#D9D9D9"}}})
            c.set_x_axis({"name": DD.label("OUT-129"), "name_font": afont, "num_font": afont})
            place(5, c, DD.rid("chart_class_size"),
                  self._chart_note(labels.RESPONSE_LABEL, case_note, "The scenario is the one chosen on Inputs ("
                                   + DD.label("IN-135") + "); blank above the class cap",
                                   labels.POLICY_UNSCORED_TRIMMED_FIRST),
                  {"categories": xr, "values": yr, "selector": ref(sh, r_cs, 1)})
        # 6. What if tuition rises more or less?
        scatter("tuition_whatif", "ntr_y1", DD.rid("chart_tuition"),
                self._chart_note(labels.RESPONSE_LABEL, case_note, labels.STICKER_LABEL,
                                 "Horizontal axis: tuition increase (%)"), 6, '"$"#,##0.00,,"M"', "0.0",
                xgrid=cfg["risk"]["tuition_grid"])
        # 7. What if more or fewer admits enroll?
        scatter("yield_strip", "class_mean", DD.rid("chart_yield"),
                self._chart_note(labels.RESPONSE_LABEL, labels.ASSUMPTION_LABEL, case_note,
                                 "Horizontal axis: change in yield (points), on top of the scenario's own change"),
                7, "#,##0", "0", cap_x=3, xgrid=yg,
                y_min=floor10([self.expected[("Summary", rr, 2)] for rr in range(self.strip_pos["yield_strip"][0],
                                                                                 self.strip_pos["yield_strip"][1] + 1)]))
        # 8. Where do merit dollars go?
        ch = wb.add_chart({"type": "column"})
        m0, m1 = self.merit_band_rows
        refs8 = {"categories": rng("Distribution", m0, 0, m1, 0), "series": []}
        for j in range(nS):
            v = rng("Distribution", m0, 2 + j, m1, 2 + j)
            ch.add_series({"name": S[j], "categories": refs8["categories"], "values": v,
                           "fill": {"color": self.scen_color(j)}, "border": {"none": True}})
            refs8["series"].append(v)
        ch.set_y_axis({"min": 0, "num_format": '"$"#,##0.0,,"M"', "num_font": afont,
                       "major_gridlines": {"visible": True, "line": {"color": "#D9D9D9"}}})
        ch.set_x_axis({"name": f"{meas} band (lower bound)", "name_font": afont, "num_font": afont})
        place(8, ch, DD.rid("chart_merit"), self._chart_note(labels.RESPONSE_LABEL, case_note), refs8)
        CH.draw(self.wb, ws, wb.inserts)
        # print: landscape at 78% (at least lo.MIN_SCALE), one page per group of charts
        self.chart_print = {"rows": r_end, "cols": 15, "breaks": [P2, P3], "scale": 78, "col_width": 9}
        self.chart_inserts = wb.inserts
        ws.print_area(0, 0, self.chart_print["rows"] - 1, self.chart_print["cols"] - 1)
        ws.set_h_pagebreaks(self.chart_print["breaks"])
        ws.set_print_scale(self.chart_print["scale"])

    # ------------------------------------------------------------------------------------------------------------
    # Distribution (spec section 6; Phase 4)

    DIST_ROWS = [  # (key, dictionary id of the plain label, unit, format); CP-1
        ("full_tuition_n", "OUT-029", "students", "n1"),
        ("no_merit_award_n", "OUT-030", "students", "n1"),
        ("barbell", "OUT-031", "ratio", "r3"),
        ("merit", "OUT-152", "USD", "usd"),
        ("top_quartile_merit", "OUT-151", "USD", "usd"),
        ("top_quartile_merit_share", "OUT-153", "ratio", "pct1"),
    ]

    def w_distribution(self):
        """Full-tuition and no-merit-award counts, the barbell index and the top-quartile merit share per scenario and
        case; the academic-position table behind the top quartile; step sizes per scenario. Plain tables: no
        threshold, color or message (D2; spec section 15 item 6)."""
        sh = "Distribution"
        ws = self.ws[sh]
        run, cells, S = self.run, self.cells, self.S
        nS = len(S)
        ws.set_column(0, 0, 58)
        ws.set_column(1, 1, 12)
        ws.set_column(2, 3, 10)
        ws.set_column(4, 4 + 4 * nS * len(CASES), 13)
        self.txt(sh, 0, 0, "Distribution: awards across the enrolled class (plain tables; no threshold, flag or "
                           "message)", "title")
        self.txt(sh, 1, 0, labels.RESPONSE_LABEL + " (every figure below except the step sizes depends on the "
                           "placeholder response through expected enrollment). Ratios are ratios of expected values.",
                 "note")
        self.txt(sh, 2, 0, "Top quartile: the first class / 4 enrollees when academic positions are ordered by "
                           "score_lo (highest first), then GPA class (hi, lo, blank), unscored last, weighted by "
                           "enrolled. The position that straddles the boundary counts the fraction of its enrolled "
                           "inside it, applied to its merit dollars; cells sharing a position are taken in the same "
                           "proportion.", "note")
        groups = L.position_groups(cells)
        tq = {(s.name, k): L.top_quartile_merit(run.lcs[s.name][k]) for s in S for k in CASES}

        # position table (rows below the summary block); laid out first so the summary rows can reference it
        r_sum = 4
        n_sum = len(self.DIST_ROWS) * len(CASES)
        r_pos = r_sum + 2 + n_sum + 2          # section title row
        hp = r_pos + 4                          # column-head row (scenario and case rows above it)
        d0 = hp + 1                             # first position row
        ng = len(groups)
        pos_cols = {}
        c = 4
        for k in CASES:
            for s in S:
                pos_cols[(k, s.name)] = c
                c += 4
        top_merit_ref = {}
        self.txt(sh, r_pos, 0, "Top quartile by academic position", "sec")
        self.txt(sh, r_pos + 1, 0, "Per scenario and case: enrolled and merit dollars at each position, enrolled at "
                                   "higher positions, and the share of the position inside the top quartile "
                                   "(MIN(1, MAX(0, (class / 4 - enrolled above) / enrolled))).", "note")
        for cc, h in enumerate(["position (highest first)", "score_lo (lower bound)", "gpa_class", "cells"]):
            self.txt(sh, hp, cc, h, "h")
        for g, (sc, gp, idx) in enumerate(groups):
            r = d0 + g
            self.val(sh, r, 0, g + 1, "int")
            self.val(sh, r, 1, "unscored" if sc is None else sc, "datat" if sc is None else "int")
            self.val(sh, r, 2, gp, "datat")
            self.val(sh, r, 3, len(idx), "int")
        for k in CASES:
            for s in S:
                c0 = pos_cols[(k, s.name)]
                d = self.g(k, s.name)
                E, SP, SC, SL, GP = d["enrolled"], d["spend"], d["scored"], d["score_lo"], d["gpa_class"]
                q = tq[(s.name, k)]
                self.txt(sh, hp - 2, c0, f"{s.name}", "hl")
                self.txt(sh, hp - 1, c0, f"{CASE_TITLE[k]} case; class / 4:", "t")
                self.fx(sh, hp - 1, c0 + 2, f"SUM({E})/4", q["top_quartile_enrolled"], "n1")
                qref = a1(hp - 1, c0 + 2)
                for cc, h in enumerate(["enrolled", "merit $", "enrolled above", "share in top quartile"]):
                    self.txt(sh, hp, c0 + cc, h, "h")
                for g, (sc, gp, idx) in enumerate(groups):
                    r = d0 + g
                    row = q["positions"][g]
                    bcell, gcell = a1(r, 1, False), a1(r, 2, False)
                    cond = (f"({SC}=0)*({GP}={gcell})" if sc is None
                            else f"({SC}=1)*({SL}={bcell})*({GP}={gcell})")
                    Ec, Mc, Cc, Fc = (a1(r, c0 + j, False) for j in range(4))
                    self.fx(sh, r, c0, f"SUMPRODUCT({cond}*{E})", row["enrolled"], "n1")
                    self.fx(sh, r, c0 + 1, f"SUMPRODUCT({cond}*{SP})", row["merit"], "usd")
                    self.fx(sh, r, c0 + 2, "0" if g == 0 else f"{a1(r - 1, c0 + 2, False)}+{a1(r - 1, c0, False)}",
                            row["cum_before"], "n1")
                    self.fx(sh, r, c0 + 3, f"IF({Ec}<=0,0,MIN(1,MAX(0,({qref}-{Cc})/{Ec})))", row["fraction"], "r4")
                fcol = rng(sh, d0, c0 + 3, d0 + ng - 1, c0 + 3)
                mcol = rng(sh, d0, c0 + 1, d0 + ng - 1, c0 + 1)
                top_merit_ref[(k, s.name)] = f"SUMPRODUCT({fcol},{mcol})"

        # summary block: figure x case rows, scenario columns
        self.txt(sh, r_sum, 0, "Counts and shares by scenario", "sec")
        self.txt(sh, r_sum + 1, 0, "figure", "h")
        self.txt(sh, r_sum + 1, 1, "case", "h")
        for j, s in enumerate(S):
            self.txt(sh, r_sum + 1, 2 + j, s.name, "h")
        ws.set_row(r_sum + 1, 36)
        r = r_sum + 2
        self.dist_rows = {}
        for key, rid_, unit, fmt in self.DIST_ROWS:
            r0 = r
            for k in CASES:
                self.txt(sh, r, 0, DD.label(rid_))
                self.txt(sh, r, 1, CASE_TITLE[k])
                for j, s in enumerate(S):
                    q = tq[(s.name, k)]
                    if key == "top_quartile_merit":
                        f, v = top_merit_ref[(k, s.name)], q["top_quartile_merit"]
                    elif key == "top_quartile_merit_share":
                        m, tm = a1(r0 - 2 * len(CASES) + CASES.index(k), 2 + j), a1(r0 - len(CASES) + CASES.index(k),
                                                                                    2 + j)
                        f, v = f"IF({m}>0,{tm}/{m},0)", q["top_quartile_merit_share"]
                    elif key == "merit":
                        f, v = self.fm("merit", k, s.name), q["merit"]
                    else:
                        f, v = self.fm(key, k, s.name), self.pv(key, k, s.name)
                    self.fx(sh, r, 2 + j, f, v, fmt)
                r += 1
            self.dist_rows[key] = r0
            if key == "top_quartile_merit_share":                        # R4-05: contract range, s x k
                self.name(K.range_name("top_quartile_merit_share", "DIST"), sh, r0, 2, r0 + len(CASES) - 1, 1 + nS)

        # step sizes (Middle-case resolved award; awards do not depend on the case)
        r_st = d0 + ng + 2
        steps = L.awards(run.lcs[S[0].name]["middle"])["step_sizes"]
        self.txt(sh, r_st, 0, DD.label("OUT-154"), "sec")
        self.txt(sh, r_st + 1, 0, "Award at a score band minus the award at the next lower band present, within each "
                                  "residency x segment x GPA class; resolved award in plan-year dollars (after the "
                                  "full-tuition flag and the incentive; AWARD_MATRIX on Levers). Named range "
                                  "STEP_SIZES.", "note")
        hs = r_st + 2
        for cc, h in enumerate(["residency, segment, GPA class", "band (upper)", "band (lower)"]):
            self.txt(sh, hs, cc, h, "h")
        for j, s in enumerate(S):
            self.txt(sh, hs, 4 + j, s.name, "h")
        ws.set_row(hs, 36)
        ws.freeze_panes(r_sum + 2, 2)
        if not steps:
            self.txt(sh, hs + 1, 0, "no group has two scored cells", "note")
            self._merit_by_band(hs + 3)
            return
        cid = list(cells.cell_id)
        groups_by = {}
        for i in range(cells.n):
            if not np.isnan(cells.score_lo[i]):
                groups_by.setdefault((cells.residency[i], cells.segment[i], cells.gpa_class[i]), []).append(i)
        pairs = []
        for key, idx in groups_by.items():
            idx = sorted(idx, key=lambda i: -cells.score_lo[i])
            pairs += [(key, a, b) for a, b in zip(idx[:-1], idx[1:])]
        assert len(pairs) == len(steps)
        cm = self.vmatrix
        for p_i, ((res, seg, gp), hi_i, lo_i) in enumerate(pairs):
            r = hs + 1 + p_i
            self.txt(sh, r, 0, f"{res}, {seg or SEG_NONE}, {gp}  ({cid[hi_i]} - {cid[lo_i]})")
            self.val(sh, r, 1, float(cells.score_lo[hi_i]), "int")
            self.val(sh, r, 2, float(cells.score_lo[lo_i]), "int")
            for j, s in enumerate(S):
                lc = run.lcs[s.name]["middle"]
                self.fx(sh, r, 4 + j, f"{ref('Levers', self.r0v + hi_i, cm + j)}-{ref('Levers', self.r0v + lo_i, cm + j)}",
                        float(lc.award[hi_i] - lc.award[lo_i]), "usd")
        self.name("STEP_SIZES", sh, hs + 1, 4, hs + len(pairs), 4 + nS - 1)
        self._merit_by_band(hs + len(pairs) + 3)

    def _merit_by_band(self, r0):
        """CP-5 chart 8: merit dollars by score band (unscored last) per scenario, Middle case. Rows: bands highest
        first, then no score; columns C onward: scenarios. Plain table (D2)."""
        sh = "Distribution"
        meas = self.cfg["score"]["measure"]
        self.txt(sh, r0, 0, DD.label(DD.rid("merit_by_band"), measure=meas), "sec")
        self.txt(sh, r0 + 1, 0, labels.RESPONSE_LABEL + ". Merit dollars (enrolled times award) summed over the "
                                "groups of each band.", "note")
        self.txt(sh, r0 + 2, 0, f"{meas} band (lower bound)", "h")
        for j, s in enumerate(self.S):
            self.txt(sh, r0 + 2, 2 + j, s.name, "h")
        bands = sorted({float(b) for b in self.cfg["score"]["bands"]}, reverse=True)
        r = r0 + 3
        for b in bands + ["unscored"]:
            self.txt(sh, r, 0, self.band_text(b) if b != "unscored" else "no score")
            for j, s in enumerate(self.S):
                d = self.g("middle", s.name)
                lc = self.run.lcs[s.name]["middle"]
                sc = np.asarray(lc.cells.score_lo, dtype=float)
                if b == "unscored":
                    f = f"SUMPRODUCT(({d['scored']}=0)*{d['spend']})"
                    m = np.isnan(sc)
                else:
                    f = f"SUMPRODUCT(({d['scored']}=1)*({d['score_lo']}={b:g})*{d['spend']})"
                    m = ~np.isnan(sc) & (np.nan_to_num(sc, nan=-1e9) == b)
                self.fx(sh, r, 2 + j, f, float((lc.enrolled * lc.award)[m].sum()), "usd")
            r += 1
        self.merit_band_rows = (r0 + 3, r - 1)

    # ------------------------------------------------------------------------------------------------------------
    # Checks

    def w_checks(self):
        run, cells, cfg = self.run, self.cells, self.cfg
        ws = self.ws["Checks"]
        ws.set_column(0, 0, 60)
        ws.set_column(1, 1, 22)
        ws.set_column(2, 2, 90)
        self.txt("Checks", 0, 0, "Checks (integrity only; nothing here comments on an award). Each returns OK or a "
                                 "message.", "title")
        for c, h in enumerate(["check", "scope", "result"]):
            self.txt("Checks", 2, c, h, "h")
        self.cr = 3
        S = [s.name for s in self.S]
        n = self.n

        def row(check, scope, f, v):
            self.txt("Checks", self.cr, 0, check, "tw")
            self.txt("Checks", self.cr, 1, scope)
            self.fx("Checks", self.cr, 2, f, v, "tw")
            self.cr += 1

        # Mode switch (spec section 9)
        if self.repro:
            row("Mode: the Ledgers take the loaded yields and tuition (Reproduce) or the response (Live)", "Inputs",
                f'IF(in_mode="Reproduce",{xs(labels.MODE_REPRO_OK)},IF(in_mode="Live",{xs(labels.MODE_REPRO_LIVE)},'
                f'{xs(labels.MODE_UNKNOWN)}))', labels.MODE_REPRO_OK)
        else:
            row("Mode: a live build has no loaded values", "Inputs",
                f'IF(in_mode="Live","OK",{xs(labels.MODE_LIVE_BUILD)})', "OK")
        if self.repro:
            self._checks_reproduce(row)
            # R3-3: a ROUND whose argument is one binary step below 2.5 (0.35 / 0.14 = 2.4999999999999996). Python
            # (config.excel_round0) and LibreOffice give 3; the desktop Excel comparison reports what Excel gives
            self.probe_cell = ("Checks", self.cr, 2)
            row(f"Rounding probe: ROUND({PROBE_EXPR}, 0); the argument is one binary step below 2.5. Python and "
                "LibreOffice give 3; tests/compare_excel_saved.py reports what desktop Excel gives", "Checks",
                f"ROUND({PROBE_EXPR},0)", float(excel_round0(PROBE_A / PROBE_B)))
        # History totals
        nc = len(self.cohorts)
        terms_res, terms_seg = [], []
        for p in ("apps", "admits", "enrolled"):
            for j in range(nc):
                c = self.hcol[p] + j
                tin = ref("History", self.htot["Total in-state"], c)
                tout = ref("History", self.htot["Total out-of-state"], c)
                tall = ref("History", self.htot["Total"], c)
                terms_res.append(f"({tin}+{tout}-{tall})^2")
                segs = [ref("History", self.htot[f"Total segment {sg['name']}"], c) for sg in cfg["segments"]]
                none = ref("History", self.htot["Total outside any segment"], c)
                terms_seg.append(f"({'+'.join(segs + [none])}-{tall})^2")
        row("History: in-state plus out-of-state totals equal the overall total", "History",
            f'IF({"+".join(terms_res)}<=0.000001,"OK","totals do not add up")', "OK")
        row("History: segment totals plus cells outside any segment equal the overall total", "History",
            f'IF({"+".join(terms_seg)}<=0.000001,"OK","totals do not add up")', "OK")
        for k in CASES:
            terms = []
            for s in S:
                E = self.LR(k, s, "enrolled")
                R = self.LSR(k, "residency")
                terms.append(f"({self.LT(k, s, 'enrolled')}-SUMPRODUCT(({R}=\"in\")*{E})-SUMPRODUCT(({R}=\"out\")*{E}))^2")
            row("Ledger: totals row equals the sum of in-state and out-of-state cell rows (enrolled)", CASE_SHEET[k],
                f'IF({"+".join(terms)}<=0.000001,"OK","totals do not add up")', "OK")
        for k in CASES:
            # Python counts the same cells (with integer admits, rounded admits can exceed fractional applications)
            for lab, cond, msg, pyc in [
                    ("admits at most applications", lambda s: f"({self.LR(k, s, 'admits')}>{self.LR(k, s, 'apps')}+"
                                                              f"0.000000001)", "cells with admits above applications",
                     lambda lc: lc.admits > lc.apps + 1e-9),
                    ("enrolled at most admits", lambda s: f"({self.LR(k, s, 'enrolled')}>{self.LR(k, s, 'admits')}+"
                                                          f"0.000000001)", "cells with enrolled above admits",
                     lambda lc: lc.enrolled > lc.admits + 1e-9),
                    ("award at least zero and at most tuition after the incentive",
                     lambda s: f"(({self.LR(k, s, 'award')}<0)+({self.LR(k, s, 'award')}>{self.LH(k, s, 'T')}+"
                               f"0.000001)>0)", "cells with an award outside [0, tuition]",
                     lambda lc: (lc.award < 0) | (lc.award > lc.tuition + 1e-6)),
                    ("yield between 0 and 1", lambda s: f"(({self.LR(k, s, 'yield')}<0)+({self.LR(k, s, 'yield')}>1)"
                                                        f">0)", "cells with a yield outside [0, 1]",
                     lambda lc: (lc.yld < 0) | (lc.yld > 1))]:
                cnt = "+".join(f"SUMPRODUCT({cond(s)}*1)" for s in S)
                nbad = int(sum(int(pyc(run.lcs[s][k]).sum()) for s in S))
                row(f"Ledger: {lab}", CASE_SHEET[k], f'IF({cnt}=0,"OK",({cnt})&" {msg}")',
                    "OK" if nbad == 0 else f"{nbad} {msg}")
        # tuition steps
        tb = self.inp_list["tuition_by_cohort"]
        for j in range(1, nc):
            T0, T1 = cfg["tuition_by_cohort"][self.cohorts[j - 1]], cfg["tuition_by_cohort"][self.cohorts[j]]
            pct = float(L.xround((T1 / T0 - 1) * 1000)) / 10.0
            ok = round_to(T0 * (1 + pct / 100), cfg["tuition_rounding_usd"]) == T1
            v = f"OK (+{pct:.1f}%)" if ok else f"not reproduced at +{pct:.1f}%"
            pc = f"ROUND(({tb[j]}/{tb[j - 1]}-1)*100,1)"
            f = (f'IF(ROUND({tb[j - 1]}*(1+{pc}/100)/in_tuition_rounding_usd,0)*in_tuition_rounding_usd={tb[j]},'
                 f'"OK (+"&TEXT({pc},"0.0")&"%)","not reproduced at +"&TEXT({pc},"0.0")&"%")')
            row(f"Tuition formula reproduces the step {self.cohorts[j - 1]} to {self.cohorts[j]} (increase rounded to "
                f"0.1%, tuition to tuition_rounding_usd)", "Inputs", f, v)
        # class against cap and band; target vs cap and range
        for s in S:
            sc = run.scen(s)
            M = self.vals["sk"][(s, "middle")]["class_mean"]
            band = cfg["class"]["band"]
            v = (f"class {labels.xl(M, 1):,.1f}; cap {sc.class_cap:g} ({'above cap' if M > sc.class_cap else 'at or below cap'}); "
                 f"target band {sc.class_target - band:g} to {sc.class_target + band:g} "
                 f"({'within band' if abs(M - sc.class_target) <= band else 'outside band'})")
            Mr = self.sref("class_mean", "middle", s)
            cap, tgt = self.LV(s, "class_cap"), self.LV(s, "class_target")
            f = (f'"class "&TEXT({Mr},"#,##0.0")&"; cap "&{cap}&" ("&IF({Mr}>{cap},"above cap","at or below cap")&'
                 f'"); target band "&({tgt}-in_class_band)&" to "&({tgt}+in_class_band)&" ("&IF(({Mr}-{tgt}<='
                 f'in_class_band)*({tgt}-{Mr}<=in_class_band)=1,"within band","outside band")&")"')
            row("Class against cap and target band (a result, not a warning; Middle case)", s, f, v)
        for s in S:
            sc = run.scen(s)
            row("Class target at most the cap", s,
                f'IF({self.LV(s, "class_target")}<={self.LV(s, "class_cap")},"OK","class target above the cap")',
                "OK" if sc.class_target <= sc.class_cap else "class target above the cap")
            lo, hi = cfg["class"]["supported_range"]
            tgt = self.LV(s, "class_target")
            notice = NAR.template_formula(labels.CLASS_TARGET_NOTICE,
                                          {"target": tgt, "lo": self.inp_list["supported_range"][0],
                                           "hi": self.inp_list["supported_range"][1]})
            v = "OK" if lo <= sc.class_target <= hi else labels.CLASS_TARGET_NOTICE.format(
                target=f"{sc.class_target:g}", lo=f"{lo:g}", hi=f"{hi:g}")
            row("Class target within the supported range", s,
                f'IF(({tgt}>={self.inp_list["supported_range"][0]})*({tgt}<={self.inp_list["supported_range"][1]})=1,'
                f'"OK",{notice})', v)
        # budget [v0.6.2, Q-8e]: total aid by default, merit only when budget_basis is merit
        for s in S:
            sk = self.vals["sk"][(s, "middle")]
            b = cfg.get("budget_total")
            kind = "merit" if cfg["budget_basis"] == "merit" else "aid"
            x = sk[kind]
            v = "not set (budget_total blank)" if b is None else (
                f"OK: {kind} ${labels.xl(x):,.0f} within budget" if x <= b
                else f"{kind} ${labels.xl(x):,.0f} above budget")
            ar = self.sref("aid", "middle", s)
            mr = self.sref("merit", "middle", s)
            xr = f'IF(in_budget_basis="merit",{mr},{ar})'
            kr = 'IF(in_budget_basis="merit","merit","aid")'
            row("Spend against budget_total (Middle case; budget_basis: total aid, or merit only)", s,
                f'IF(in_budget_total="","not set (budget_total blank)",IF({xr}<=in_budget_total,"OK: "&{kr}&" $"&'
                f'TEXT({xr},"#,##0")&" within budget",{kr}&" $"&TEXT({xr},"#,##0")&" above budget"))', v)
        # R4-11: ntr_goal_basis is a live drop-down; all_jd with a blank continuing_ntr_usd would count it as 0
        row("Revenue goal: " + labels.ALL_JD_NEEDS_CONTINUING, "Inputs",
            f'IF((in_ntr_goal_basis="all_jd")*(in_continuing_ntr_usd="")=1,{xs(labels.ALL_JD_NEEDS_CONTINUING)},"OK")',
            "OK")
        # history reconciliation [v0.6.2, Q-8f]
        for j, h in enumerate(self.vals["history_reconciliation"]):
            act = self.inp_list["merit_actual_by_cohort"][j]
            imp = f"SUMPRODUCT({self.HR('enrolled', j)},{self.HR('award', j)})"
            y = h["cohort"]
            v = (f"not run: merit_actual_by_cohort not given for {y}" if h["actual"] is None else
                 f"grid-implied ${labels.xl(h['implied']):,.0f} against reported ${labels.xl(h['actual']):,.0f}: "
                 f"gap {labels.xl(100 * h['gap'], 1):.1f}%")
            row(f"History reconciliation {y}: grid-implied merit (enrolled x award over cells) against reported "
                "merit (merit_actual_by_cohort; percent gap)", "History",
                f'IF({act}="","not run: merit_actual_by_cohort not given for {y}","grid-implied $"&TEXT({imp},'
                f'"#,##0")&" against reported $"&TEXT({act},"#,##0")&": gap "&TEXT(({imp}-{act})/{act}*100,"0.0")&"%")',
                v)
        for h in self.vals["aba509_reconciliation"]:
            y = h["cohort"]
            V = self.h509[y]
            nrow = len(h["rows"])
            given = f'({nrow}-SUMPRODUCT(({V}={xs(labels.ABA509_NOT_GIVEN)})*1))'
            bad = (f'SUMPRODUCT((({V}={xs(labels.ABA509_DIFFERS)})+({V}={xs(labels.ABA509_INCONSISTENT)}))*1)')
            msg = NAR.template_formula(labels.ABA509_SOME_DIFFER, {"k": bad, "n": given})
            row(f"History 509 reconciliation {y}: cell data against the public ABA 509 (class, without a score or GPA, "
                "quartiles; reported, not asserted)", "History",
                f'IF({given}=0,{xs(labels.ABA509_NOT_RUN.format(y=y))},IF({bad}=0,{xs(labels.ABA509_ALL_AGREE)},'
                f'{msg}))', h["summary"])
        for k in CASES:
            terms = [f"({self.sref('class_mean', k, s)}-{self.LT(k, s, 'mu')})^2" for s in S]
            row("Summary expected class equals the Ledger total", CASE_SHEET[k],
                f'IF({"+".join(terms)}<=0.000001,"OK","Summary and Ledger differ")', "OK")
        RES = self.LSR("middle", "residency")
        SEGc = self.LSR("middle", "segment")
        for i, sg in enumerate(cfg["segments"]):
            within = self.names[f"in_seg_within"]
            wref = ref("Inputs", within[1] + i, within[2])
            nref = ref("Inputs", within[1] + i, within[2] - 1)
            row(f"Segment cells lie within their residency", sg["name"],
                f'IF(SUMPRODUCT(({SEGc}={nref})*({RES}<>{wref}))=0,"OK",SUMPRODUCT(({SEGc}={nref})*({RES}<>{wref}))'
                f'&" segment cells outside their residency")', "OK")
        # empty-segment scope error and unnamed segment [v0.6.2, P2-07]
        nseg = len(cfg["segments"])
        for s in S:
            SEG = self.LR("middle", s, "in_seg")
            f = (f'IF(({self.LV(s, "bonus_scope")}="segment")*(SUM({SEG})=0)*(({self.LV(s, "bonus_usd")}>0)+'
                 f'({self.LV(s, "segment_pool_lift_pct")}<>0)+({self.LV(s, "segment_goal")}<>"")>0)=1,'
                 f'{xs(labels.SCOPE_ERROR)},"OK")')
            row("Bonus scope 'segment' has segment cells when a bonus, lift or goal is set", s, f, "OK")
            if nseg > 1:
                row("Active segment named (several segments configured)", s,
                    f'IF({self.LV(s, "segment")}="",{xs(labels.SEGMENT_UNNAMED)},"OK")', "OK")
        # build-time inputs and the static exact probability [v0.6.2, P2-06]
        rb = lambda b: xs(labels.REBUILD_NEEDED.format(build=b))  # noqa: E731
        if not self.repro:            # the Trim sheet is live mode only
            t0 = cfg["score"]["median_thresholds"][0]
            row("Trim order: first median threshold equals its value at build", "Inputs",
                f'IF({self.inp_list["median_thresholds"][0]}={t0:g},"OK",{rb(f"{t0:g}")})', "OK")
            ps = cfg["trim"]["protect_segment"]
            row("Trim order: trim.protect_segment equals its value at build", "Inputs",
                f'IF(in_protect_segment={xs(ps)},"OK",{rb(ps)})', "OK")
            ex = ", ".join(cfg["trim"]["exempt_cells"])
            row("Trim: trim.exempt_cells equals its value at build", "Inputs",
                f'IF(in_exempt_cells={xs(ex)},"OK",{rb(ex or "none")})', "OK")
            if ps == "above_floor":
                # [v0.6.3, BM-5] under above_floor the Trim order depends on score.floor
                fl = cfg["score"]["floor"]
                row("Trim order: score.floor equals its value at build (protect_segment above_floor)", "Inputs",
                    f'IF(in_score_floor={fl:g},"OK",{rb(f"{fl:g}")})', "OK")
            for s in S:
                seg = L.active_segment(cfg, run.scen(s)) or ""
                row("Trim order: active segment equals its value at build", s,
                    f'IF({self.LH("middle", s, "seg")}={xs(seg)},"OK",{rb(seg or "none")})', "OK")
        # [v0.6.3, BM-1] percentile targets: each t a band bound (live); q fixed at build (labels and layout)
        for j, (q, t) in enumerate(self.ptargets):
            tr = self.inp_list["pct_t"][j]
            row(DD.label("CK-042", j=j + 1), "Inputs",
                f'IF(SUMPRODUCT((in_score_bands={tr})*1)>0,"OK","target score "&{tr}&" is not a band lower bound")', "OK")
            qr = self.inp_list["pct_q"][j]
            row(DD.label("CK-043", j=j + 1), "Inputs",
                f'IF({qr}={q!r},"OK",{rb(f"{q:g}")})', "OK")
        for j, s in enumerate(S):
            st = ref("Summary", self.exact_status_row, 2 + j)
            row(DD.label("CK-044"), s,
                f'IF({st}={xs(labels.EXACT_STALE)},{xs(labels.EXACT_STALE)},"OK")', "OK")
        # full-tuition conflicts (P1.1-1)
        K_LIST = 10
        helper0 = 5
        self.txt("Checks", 1, helper0, "Helper: full-tuition conflict flags and running counts per scenario (cells in "
                                       "Ledger order)", "note")
        self.txt("Checks", 2, helper0, "cell_id", "h")
        ids = rng("Checks", 3, helper0, 3 + n - 1, helper0)
        for i in range(n):
            self.val("Checks", 3 + i, helper0, cells.cell_id[i], "datat")
        self.ws["Checks"].set_column(helper0, helper0, 22)
        msg = labels.FT_CONFLICT_CHECK
        for j, s in enumerate(S):
            sc = run.scen(s)
            p = run.parents[s]
            fc, cc = helper0 + 1 + 2 * j, helper0 + 2 + 2 * j
            self.txt("Checks", 2, fc, f"{s}: flag", "h")
            self.txt("Checks", 2, cc, f"{s}: running count", "h")
            conf = self.vals["conflicts"][s]
            cum = np.cumsum(conf.astype(int))
            for i in range(n):
                ft, aw = self.LVc(s, "ft", i), self.LVc(s, "award", i)
                refv = (ref("History", self.r0h + i, self.hcol["award"] + self.jbase) if p is None
                        else self.LVc(p.name, "award", i))
                self.fx("Checks", 3 + i, fc, f"IF(({ft}=1)*({aw}<>{refv})=1,1,0)", int(conf[i]), "int")
                self.fx("Checks", 3 + i, cc, (a1(3 + i, fc, False) if i == 0
                                              else f"{a1(2 + i, cc, False)}+{a1(3 + i, fc, False)}"), int(cum[i]),
                        "int")
            total = int(conf.sum())
            tref = a1(3 + n - 1, cc)
            v = "OK" if total == 0 else f"{total} cells: {msg}"
            row(DD.label("CK-045"), s, f'IF({tref}=0,"OK",{tref}&" cells: {msg}")', v)
            cumr = rng("Checks", 3, cc, 3 + n - 1, cc)
            hits = list(cells.cell_id[conf])
            for q in range(1, K_LIST + 1):
                vq = hits[q - 1] if q <= total else ""
                self.txt("Checks", self.cr, 0, f"  conflict {q}", "note")
                self.txt("Checks", self.cr, 1, s)
                self.fx("Checks", self.cr, 2, f'IF({q}<={tref},INDEX({ids},MATCH({q},{cumr},0)),"")', vq, "t")
                self.cr += 1
            self.txt("Checks", self.cr, 0, "  more", "note")
            self.fx("Checks", self.cr, 2, f'IF({tref}>{K_LIST},"and "&({tref}-{K_LIST})&" more","")',
                    f"and {total - K_LIST} more" if total > K_LIST else "", "t")
            self.cr += 1
        self.ws["Checks"].freeze_panes(3, 0)

    def _checks_reproduce(self, row):
        """Reproduce builds: Levers against the loaded values, and the tuition formula against the loaded tuition."""
        run, cfg = self.run, self.cfg
        for s in self.S:
            sc = run.scen(s.name)
            ld = run.loaded[s.name]
            lc = run.lcs[s.name]["middle"]
            n_rate = int(((sc.admit_rate - ld["admit_rate"]) ** 2 > 1e-18).sum())
            n_award = int(((lc.award - ld["award_usd"]) ** 2 > 0.25).sum())
            pool_diff = int(sc.pool_multiplier != ld["pool_multiplier"])
            v = "OK" if n_rate + n_award + pool_diff == 0 else labels.REPRO_LEVERS_DIFFER.format(
                rates=n_rate, awards=n_award, pool="differs" if pool_diff else "matches")
            fr = f"SUMPRODUCT((({self.LVR(s.name, 'rate')}-{self.PR(s.name, 'rate')})^2>1E-18)*1)"
            fa = f"SUMPRODUCT((({self.LR('middle', s.name, 'award')}-{self.PR(s.name, 'award')})^2>0.25)*1)"
            pref = ref("Reproduce", self.prow["pool_multiplier"], self.pblock[s.name])
            fp = f"IF({self.LV(s.name, 'pool_multiplier')}<>{pref},1,0)"
            msg = NAR.template_formula(labels.REPRO_LEVERS_DIFFER, {
                "rates": fr, "awards": fa, "pool": f'IF({fp}=1,"differs","matches")'})
            row("Reproduce: Levers admit rates, resolved awards (Middle) and pool multiplier equal the loaded values",
                s.name, f'IF({fr}+{fa}+{fp}=0,"OK",{msg})', v)
        for s in self.S:
            sc = run.scen(s.name)
            ld = run.loaded[s.name]
            Tf = scenario_tuition(cfg, sc.tuition_increase_pct)
            v = "OK" if Tf == ld["tuition"] else labels.REPRO_TUITION_DIFFERS.format(
                formula=f"${labels.xl(Tf):,.0f}", loaded=f"${labels.xl(ld['tuition']):,.0f}")
            tf = (f"ROUND(in_tuition_base*(1+{self.LV(s.name, 'tuition_increase_pct')}/100)/in_tuition_rounding_usd,0)"
                  f"*in_tuition_rounding_usd")
            tl = ref("Reproduce", self.prow["tuition"], self.pblock[s.name])
            msg = NAR.template_formula(labels.REPRO_TUITION_DIFFERS, {"formula": f'"$"&TEXT({tf},"#,##0")',
                                                                      "loaded": f'"$"&TEXT({tl},"#,##0")'})
            row("Reproduce: the tuition formula at the scenario's increase equals the loaded tuition", s.name,
                f'IF({tf}={tl},"OK",{msg})', v)

    # ------------------------------------------------------------------------------------------------------------
    def w_runlog(self):
        m = self.run.meta
        self.ws["RunLog"].set_column(0, 0, 28)
        self.ws["RunLog"].set_column(1, 1, 90)
        self.txt("RunLog", 0, 0, "RunLog", "title")
        rows = [("build id", m.get("build_id", "")), ("git commit", m.get("git_commit", "")),
                ("config", m.get("config_path", "")), ("config hash (sha256)", m.get("config_hash", "")),
                ("data source", m.get("data_source", "")), ("data hash (sha256 of the cell table)", m.get("data_hash", "")),
                ("scenarios", m.get("scenarios_path", "")), ("scenarios hash (sha256)", m.get("scenarios_hash", "")),
                ("requirements.lock hash (sha256)", m.get("requirements_lock_hash", "")),
                ("code hash (sha256 of sw/*.py)", m.get("code_hash", "")),
                ("dictionary hash (sha256 of dictionary.csv)", m.get("dictionary_hash", "")),
                ("uncommitted files", m.get("uncommitted_files", "")),
                ("cached values", "sentinel: every formula cell holds -999 until recalculated (use this copy for the "
                                  "desktop Excel check)" if self.sentinel else "Python values (the build's results)"),
                ("timestamp", _dt.datetime.now().astimezone().isoformat(timespec="seconds")),
                ("response source", self.run.base.source_label + " (placeholder slopes; sw/response.py)"),
                ("shock source", f"{self.cfg['risk']['shock_source']} (s = {self.cfg['risk']['common_shock_sd']:g})"),
                ("mode", MODE_LABEL[self.cfg["mode"]] + (" (reproduce build: loaded values on the Reproduce sheet; "
                                                          + m.get("reproduce_source", "") + ")" if self.repro
                                                          else " (live build)")),
                ("python", platform.python_version()), ("xlsxwriter", xlsxwriter.__version__),
                ("LibreOffice acceptance version (config/tools.yaml)", LO.acceptance_version() or "not set"),
                ("hold_position_rows", "held: every median and percentile figure reads '" + labels.HOLD_POSITION
                 + "'" if self.hold else "not held")]
        for i, (a, b) in enumerate(rows):
            self.txt("RunLog", 2 + i, 0, a, "hl")
            self.txt("RunLog", 2 + i, 1, str(b))

    def w_readme(self):
        cfg = self.cfg
        ws = self.ws["README"]
        ws.set_column(0, 0, 34)
        ws.set_column(1, 1, 120)
        r = 0
        self.txt("README", r, 0, "Scenario workbook (prototype, spec v0.6.4): README", "title")
        r += 2
        sections = [
            ("Purpose", "Scores the scenarios written on Levers with live formulas and shows the results with their "
                        "uncertainty. It recommends nothing. Every figure that depends on the placeholder response "
                        "slopes carries '" + labels.RESPONSE_LABEL + "'."),
            ("Build", f"build {self.run.meta.get('build_id', '')}; data {self.run.meta.get('data_source', '')}; "
                      "see RunLog."),
            ("How to use", "Change blue cells on Inputs and Levers; every sheet recalculates. A child scenario "
                           "inherits each lever from its parent by formula (italic blue) until you type over it. Grey "
                           "fill on Levers marks cells that differ from the parent. Sheets are protected without a "
                           "password (Review > Unprotect Sheet)."),
            ("Overview and charts", "Overview (after this sheet): the headline figures of each scenario with what "
                                    "each means, every cell a formula on the Summary. Charts: eight charts of the "
                                    "main results and the what-if tables, linked to the Summary and Distribution "
                                    "through the chart data below them; one color per scenario, Baseline grey; middle "
                                    "case throughout. The Summary is ordered by question: A class size, B revenue and "
                                    "aid, C academic profile, D priority segment, E incentive, F what-if tables, G "
                                    "award distribution, H technical detail, then Definitions and Notes on method. "
                                    "Every label is plain text from the data dictionary; the code names stay in the "
                                    "grey setting column on Inputs and Levers, the named ranges and the Ledgers."
                                    if not self.repro else
                                    "A reproduce build (validation only) has no Overview or charts; its labels are the "
                                    "same plain labels."),
            ("Color key", "Blue on light blue: input. Italic blue: inherited input (formula to the parent; type over "
                          "it to override). Black: formula (locked). Grey fill: differs from the parent."),
            ("Labels", f"{labels.RESPONSE_LABEL}: every response-dependent output. {labels.ASSUMPTION_LABEL}: any "
                       f"scenario with a non-zero yield shift or application lift. "
                       f"{labels.SHOCK_LABEL.format(s='risk.common_shock_sd on Inputs')}: beside every "
                       "probability and range while shock_source is illustrative; probabilities below 5% or above "
                       f"95% then show as '{labels.PROB_UNDER}' or '{labels.PROB_OVER}'. "
                       f"{labels.SEGMENT_SHARE_LABEL}: every segment figure while share_source is assumed."),
            ("Range kinds", f"'{labels.RANGE_OUTCOME}' ({labels.RANGE_OUTCOME_NOTE}); '{labels.RANGE_CASES}' "
                            f"({labels.RANGE_CASES_NOTE}). The kinds are never combined."),
            ("Metric names (methodology Appendix F)",
             "ntr_y1: entering class, first year: gross_y1 minus merit, need and specialty. gross_y1: enrolled times "
             "published first-year tuition (fees excluded). discount_entering_y1: aid over gross_y1 (label '"
             + labels.DISCOUNT_LABEL + "'). Median margin at t: enrolled with a score at or above t minus enrolled "
             "with a score below t. Share at or above t: over expected enrolled with a score. Percentile q at or "
             "above t: at most a share q of scored enrollees below t (the median is q = 0.5); its margin q x N_scored "
             "- G- counts swaps at the same class size (" + labels.PCT_MARGIN_UNIT + "); "
             + labels.PCT_APPROX_LABEL + " below 20 expected below t; the spread rows are a '"
             + labels.BAND_NOT_SCORE_LABEL + "'. " + labels.GPA_PCT_NOTE + " E_S: segment enrolled. "
             "Incentive cost, paid-anyway share, aid per additional enrollee (items 19 to 21); evidence share (item "
             "24). Ratios are ratios of expected values, E[X] / E[Y], everywhere."),
            ("Mode", ("Reproduce build: the Reproduce sheet holds loaded yields, admit rates, awards, pool settings and "
                      "tuition. With the Inputs mode at Reproduce the Ledgers take the loaded yields (all three cases, no "
                      "response, shift, floor or cap) and the loaded tuition; at Live they take the response yields and "
                      "the tuition formula. Integer admits and enrolled. No Trim sheet and no class-size table (live "
                      "mode only)." if self.repro else
                      "Live build: the Ledgers use the response yields and the tuition formula. Reproduce mode needs a "
                      "reproduce build (python -m sw.reproduce), which adds the Reproduce sheet.")),
            ("Static and live", "Live: everything on History (rates), Response, Levers, the Ledgers, Summary, Trim, "
                                "Distribution and Checks recalculates from Inputs and Levers. Static: cell counts "
                                "(History data), the academic positions and step-size pairs on Distribution (from the "
                                "cell data), the "
                                "trim order (fixed at build from the first median threshold, protect_segment, the "
                                "exempt cells and each scenario's active segment), the number of grid values, the exact "
                                "segment probability (labelled 'static, from the build'), RunLog. Inputs marked "
                                "'build-time' need a rebuild; Checks shows 'rebuild needed' when a trim-order input "
                                "differs from its value at build, and Summary marks the exact probability stale when "
                                "the segment's expected enrollment or goal changes."),
            ("Policy choices", labels.POLICY_UNSCORED_TRIMMED_FIRST + " " + labels.POLICY_UNSCORED_EXCLUDED
             + " (unscored_in_median = " + cfg["unscored_in_median"] + "). Segment protection on the shrink path: "
             + cfg["trim"]["protect_segment"] + " (above_floor protects segment cells from score.floor up to the first "
             "median threshold; segment cells below the floor and unscored segment cells are trimmed in normal "
             "order)."),
            ("Revenue goal and tuition", "ntr_goal_basis " + cfg.get("ntr_goal_basis", "entering_y1") + ": under "
             "all_jd, ntr_target is the total JD goal and every ntr_target figure reads ntr_target - "
             "continuing_ntr_usd (" + labels.CONTINUING_LABEL + "). tuition_by_year_usd, when set for a year, takes "
             "precedence over tuition_increase_by_year; Inputs shows the implied increase. Pool growth to date marks "
             "the pool-strip row nearest 1 + growth (" + labels.POOL_YTD_TIE + ") and shows that row's pool multiplier; "
             "the break-even pool multipliers are expectations (" + labels.POOL_BREAKEVEN_LABEL + "): a plain number "
             "is a floor, '" + labels.POOL_BE_AT_MOST.format(m="m") + "' a ceiling (the target fails beyond m), and "
             "a note stands in when the multiplier is not a pool size on the grid. Need aid: "
             + labels.NEED_DEPARTURE_NOTE + "."),
            ("Medians and percentiles", "A median or percentile target " + labels.PCT_TIE_RULE + ". The median "
             "margin is enrolled at or above t minus enrolled below; the percentile margin counts "
             + labels.PCT_MARGIN_SWAPS + "; the Summary shows one margin per event: q = 0.5 targets are the median "
             "rows, strip columns and ranges, and are left out of the percentile rows, the percentile contract "
             "ranges, the strips and the break-evens. hold_position_rows: "
             + ("true, so every median and percentile figure, and the working values and counts it could be read "
                "from, reads '" + labels.HOLD_POSITION + "'" if self.hold else "false") + "."),
            ("Yield", "One Ledger column per case: clip(clip(y0 + b/100 (award - a0)/1000, floor, cap) + shift/100, "
                      "floor, cap). The Response rung grid is display only. Yield is constant when admit rates "
                      "change; sticker price does not move applications or yield."),
            ("Distribution", "Full-tuition and no-merit-award counts, the barbell index, the share of merit dollars "
                             "to the top quartile of enrolled by academic position (score_lo, then GPA class; unscored "
                             "last; weighted by enrolled; the position that straddles the boundary counts in "
                             "proportion), and step sizes (award difference between adjacent score bands within each "
                             "residency x segment x GPA class, per scenario). Plain tables: no threshold, color or "
                             "message."),
            ("Not built here", "Anything deferred in DECISIONS.md."),
            ("Interface contract", "Named ranges (spec section 15 item 11; canonical names, no aliases): " + ", ".join(
                rn for rn, _, _, _ in K.contract_table()) + ". The Summary ranges sit below its print area with the "
                "pool strip's working values (not printed). AWARD_MATRIX is on Levers (resolved award); STEP_SIZES "
                "is on Distribution. p_segment_goal_exact is Python only (the Summary shows a static copy)."),
            ("Handling", "Small cells are shown (small_cell_policy: " + cfg["client"]["small_cell_policy"]
             + "). Files go only to the client's named roles through the secure channel (methodology section 9). "
               "Client-facing use needs Jason's review first."),
        ]
        for a, b in sections:
            self.txt("README", r, 0, a, "hl")
            self.txt("README", r, 1, b, "tw")
            ws.set_row(r, 15 * max(1, math.ceil(len(b) / 150)))
            r += 1


def write(run, path, sentinel=False):
    """Write the workbook. Returns a dict: expected values per formula cell, the contract dump, named ranges. A live
    build also writes the chart specification beside the workbook (sw/charts.py; the PDF render draws from it)."""
    bk = Book(run, path, sentinel=sentinel)
    bk.write()
    if getattr(bk, "chart_inserts", None) is not None:
        CH.save(path, bk.chart_inserts, {"print": bk.chart_print, "overview_print_rows": bk.overview_last_row + 1,
                                         "overview_cols": 2 + len(bk.S),
                                         "overview_widths": [40, 46] + [14] * len(bk.S)})
    layout = {"r0l": bk.r0l, "ltot": bk.ltot, "lblock": bk.lblock, "lstat": bk.lstat, "r0v": bk.r0v,
              "vblock": bk.vblock, "vfield_row": bk.vfield_row, "n": bk.n, "case_sheet": dict(CASE_SHEET),
              "r0h": bk.r0h, "hcol": dict(bk.hcol), "probe_cell": getattr(bk, "probe_cell", None),
              "marker_cells": list(getattr(bk, "marker_cells", [])),     # [v0.6.3, BM-6] growth-to-date cells
              "pool_parts": dict(getattr(bk, "pool_parts", {})),         # Phase 4.2: working-value cells (A1)
              "summary_print_rows": getattr(bk, "summary_print_rows", None),  # rows 1 .. this are printed
              "ledger_head_rows": {"name": 2, "T": 3, "p": 4, "need_rate": 5, "seg": 6},
              # CP-3 to CP-5: Summary rows by dictionary id and instance; Overview cells; chart titles, notes, refs
              "srow": {k: v[0] for k, v in getattr(bk, "srow", {}).items()},
              "overview_cells": dict(getattr(bk, "overview_cells", {})),
              "chart_meta": list(getattr(bk, "chart_meta", [])),
              "strip_pos": dict(getattr(bk, "strip_pos", {})),
              "merit_band_rows": getattr(bk, "merit_band_rows", None),
              "chart_marker_cells": list(getattr(bk, "chart_marker_cells", []))}
    return {"expected": bk.expected, "dump": bk.dump, "names": bk.names, "vals": bk.vals,
            "build_id": run.meta.get("build_id"), "layout": layout, "run": run}
