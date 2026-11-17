"""XlsxWriter generator for the scenario workbook (spec sections 6 to 8, 15 item 11). Live mode only.

Sheets: README, Inputs, History, Response, Levers, Ledger_Low, Ledger_Middle, Ledger_High, Summary, Trim, Checks,
RunLog. Reproduce mode (the Reproduce sheet and mode switch) is Phase 3 and the Distribution sheet is Phase 4; neither
is built here.

Every computed cell is a live formula written with its cached value from the Python reference functions (spec
section 6), and the builder records that value as the expected result for test 3. With sentinel=True every cached value
is -999 instead, so a recalculation that leaves any cell untouched shows up (test 3 guard).

Formulas use ROUND, SUM, SUMPRODUCT, INDEX, MATCH, MIN, MAX, IF, SQRT, NORMSDIST, TEXT and &, plus comparison
arithmetic inside SUMPRODUCT; no array IF, no dynamic arrays, no volatile functions, no macros.
"""
import datetime as _dt
import math
import platform
from dataclasses import replace

import numpy as np
import xlsxwriter
from xlsxwriter.utility import quote_sheetname, xl_col_to_name, xl_rowcol_to_cell

from . import CASES
from . import contract as K
from . import labels
from . import ledger as L
from . import narrative as NAR
from . import response
from . import risk
from . import trim
from .config import plan_increase_pct, round_to, scenario_tuition

CASE_SHEET = {"low": "Ledger_Low", "middle": "Ledger_Middle", "high": "Ledger_High"}
CASE_TITLE = {"low": "Low", "middle": "Middle", "high": "High"}
SEG_NONE = "(none)"
BIG = "1E+99"
SHEETS = ["README", "Inputs", "History", "Response", "Levers", "Ledger_Low", "Ledger_Middle", "Ledger_High",
          "Summary", "Trim", "Checks", "RunLog"]
LEVER_FIELDS = [  # (field, label, kind): kind num, int01, text, opt (optional number)
    ("description", "description", "text"), ("plan_year", "plan_year (label)", "num"),
    ("tuition_increase_pct", "tuition_increase_pct", "num"),
    ("award_scale_with_tuition", "award_scale_with_tuition (1 = scale)", "int01"),
    ("pool_multiplier", "pool_multiplier", "num"), ("specialty_usd", "specialty_usd", "num"),
    ("need_total", "need_total", "num"), ("class_target", "class_target", "num"), ("class_cap", "class_cap", "num"),
    ("bonus_usd", "bonus_usd", "num"), ("bonus_scope", "bonus_scope", "text"),
    ("bonus_min_score", "bonus_min_score (blank = none)", "opt"),
    ("bonus_pool_usd", "bonus_pool_usd (dollar pool, informational; blank = none)", "opt"),
    ("segment", "segment (active; blank = the only configured segment)", "text"),
    ("segment_pool_lift_pct", "segment_pool_lift_pct", "num"), ("segment_goal", "segment_goal (blank = none)", "opt"),
    ("yield_shift_pts", "yield_shift_pts", "num"), ("yield_shift_pts_in", "yield_shift_pts_in (blank inherits)", "opt"),
    ("yield_shift_pts_out", "yield_shift_pts_out (blank inherits)", "opt"),
    ("yield_shift_pts_segment", "yield_shift_pts_segment (blank inherits)", "opt"),
    ("discount_target", "discount_target (blank = none)", "opt"),
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
        self.ws = {name: self.wb.add_worksheet(name) for name in SHEETS}
        self._formats()
        self.cohorts = list(self.cells.cohorts)
        self.jbase = self.cells.col(self.cfg["cycle"]["base_cycle"])
        self.targets = risk.median_targets(self.cfg)
        self.score_ts = L.score_thresholds(self.cfg)
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
            "note": F(dict(base, italic=True, font_color="#555555")),
            "notew": F(dict(base, italic=True, font_color="#555555", text_wrap=True, valign="top")),
            "data": F(dict(base, num_format="#,##0")),           # counts [v0.6.2, P2-05]
            "datat": F(base),
        }
        nums = {"num": "General", "usd": "$#,##0", "n1": "#,##0.0", "n0": "#,##0", "r3": "0.000", "r4": "0.0000",
                "pct1": "0.0%", "prob": "0%", "int": "0", "text": "@", "pp": "0.0"}
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
        for k in CASES:
            self.w_ledger(k)
        self.w_trim()
        self.w_summary(dry=True)
        self.w_summary(dry=False)
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
        for name in ("Summary", "Inputs", "Checks", "README", "RunLog"):
            self.ws[name].fit_to_pages(1, 0)

    # ------------------------------------------------------------------------------------------------------------
    # Inputs

    def w_inputs(self):
        cfg = self.cfg
        ws = self.ws["Inputs"]
        ws.set_column(0, 0, 44)
        lists = [len(cfg["score"]["bands"]), len(cfg["risk"]["pool_grid"]), len(cfg["class"]["what_if"]),
                 len(cfg["risk"]["yield_shift_grid"]), len(cfg["risk"]["tuition_grid"]), len(self.cohorts), 4]
        self.inote = 2 + max(lists)
        ws.set_column(1, self.inote - 1, 11)
        ws.set_column(self.inote, self.inote, 70)
        self.txt("Inputs", 0, 0, "Inputs", "title")
        self.txt("Inputs", 1, 0, "Blue cells are inputs. 'live' inputs drive formulas; 'build-time' inputs are shown "
                                 "for reference and need a rebuild to apply. Live mode (Reproduce mode is Phase 3 and is "
                                 "not built).", "note")
        self.ir = 3

        def sec(t):
            self.ir += 1
            self.txt("Inputs", self.ir, 0, t, "sec")
            self.ir += 1

        def one(key, label, v, fmt="in_num", note="live", formula=None):
            r = self.ir
            self.ir += 1
            self.txt("Inputs", r, 0, label)
            if formula:
                self.fx("Inputs", r, 1, formula, v, fmt)
            else:
                self.val("Inputs", r, 1, v, fmt)
            self.txt("Inputs", r, self.inote, note, "note")
            nm = f"in_{key}"
            self.name(nm, "Inputs", r, 1)
            self.inp[key] = nm
            return r

        def many(key, label, vs, fmt="in_num", note="live"):
            r = self.ir
            self.ir += 1
            self.txt("Inputs", r, 0, label)
            for i, v in enumerate(vs):
                self.val("Inputs", r, 1 + i, v, fmt)
            self.txt("Inputs", r, self.inote, note, "note")
            nm = f"in_{key}"
            self.name(nm, "Inputs", r, 1, r, len(vs))
            self.inp[key] = nm
            self.inp_list[key] = [ref("Inputs", r, 1 + i) for i in range(len(vs))]
            return r

        sec("Client")
        one("client_id", "client.id", cfg["client"]["id"], "in_text", "build-time")
        one("client_name", "client.name", cfg["client"]["name"], "in_text", "build-time")
        one("vertical", "client.vertical", cfg["client"]["vertical"], "in_text", "build-time")
        one("small_cell_policy", "client.small_cell_policy", cfg["client"]["small_cell_policy"], "in_text",
            "build-time; methodology section 9")
        sec("Cycle and tuition")
        one("base_cycle", "cycle.base_cycle", cfg["cycle"]["base_cycle"], "in_int", "build-time")
        one("plan_cycle", "cycle.plan_cycle", cfg["cycle"]["plan_cycle"], "in_int", "build-time")
        many("history", "cycle.history", self.cohorts, "in_int", "build-time")
        tbc = [cfg["tuition_by_cohort"][y] for y in self.cohorts]
        many("tuition_by_cohort", "tuition_by_cohort (published first-year tuition; fees excluded)", tbc, "in_usd")
        one("tuition_base", "tuition_base (tuition at base_cycle)", cfg["tuition_base"], "usd",
            "formula: tuition_by_cohort at base_cycle",
            formula=f"INDEX(in_tuition_by_cohort,MATCH(in_base_cycle,in_history,0))")
        yrs = sorted(cfg["tuition_increase_by_year"])
        many("tuition_increase_years", "tuition_increase_by_year: plan year", yrs, "in_int", "build-time")
        many("tuition_increase_pct", "tuition_increase_by_year: increase (%)",
             [cfg["tuition_increase_by_year"][y] for y in yrs], "in_pp",
             "live (Baseline's tuition_increase_pct reads it)")
        one("tuition_rounding_usd", "tuition_rounding_usd", cfg["tuition_rounding_usd"], "in_usd")
        sec("Score and GPA")
        one("score_measure", "score.measure", cfg["score"]["measure"], "in_text", "build-time")
        many("score_bands", "score.bands (lower bounds)", cfg["score"]["bands"], "in_int", "build-time")
        one("pool_threshold", "score.pool_threshold", cfg["score"]["pool_threshold"], "in_int")
        one("score_floor", "score.floor", cfg["score"]["floor"], "in_int")
        many("median_thresholds", "score.median_thresholds", cfg["score"]["median_thresholds"], "in_int",
             "live in the Ledger and Summary; the Trim order uses the build's first threshold")
        one("gpa_measure", "gpa.measure", cfg["gpa"]["measure"], "in_text", "build-time")
        one("gpa_hi_at_or_above", "gpa.hi_at_or_above (class boundary)", cfg["gpa"]["hi_at_or_above"], "in_num",
            "build-time (GPA classes are in the cell data)")
        one("gpa_median_threshold", "gpa.median_threshold (equals the class boundary)",
            cfg["gpa"]["median_threshold"], "in_num", "build-time")
        one("unscored_in_median", "unscored_in_median (excluded or below)", cfg["unscored_in_median"], "in_text",
            "live; " + labels.POLICY_UNSCORED_EXCLUDED)
        self.ws["Inputs"].data_validation(self.ir - 1, 1, self.ir - 1, 1,
                                          {"validate": "list", "source": ["excluded", "below"]})
        sec("Class")
        cl = cfg["class"]
        one("class_cap", "class.cap (hard this cycle)", cl["cap"], "in_num", "live (Baseline reads it)")
        one("class_target", "class.target", cl["target"], "in_num", "live (Baseline reads it)")
        one("class_band", "class.band", cl["band"])
        many("class_what_if", "class.what_if (class-size table)", cl["what_if"], "in_num")
        many("supported_range", "class.supported_range (low, high)", cl["supported_range"], "in_num")
        many("reject_range", "class.reject_range (low, high)", cl["reject_range"], "in_num",
             "build-time (checked when scenarios are built)")
        sec("Need aid")
        one("need_total", "need.total", cfg["need"]["total"], "in_usd", "live (Baseline reads it)")
        one("need_reference_class", "need.reference_class", cfg["need"]["reference_class"], "in_num")
        nr = float(cfg["need"]["total"]) / float(cfg["need"]["reference_class"])
        one("need_rate", "need rate per enrollee", nr, "usd", "formula", formula="in_need_total/in_need_reference_class")
        need_lbl = labels.NEED_LABEL.format(total=f"${cfg['need']['total']:,.0f}",
                                            ref=f"{cfg['need']['reference_class']:g}", rate=f"${nr:,.0f}")
        r = self.ir
        self.ir += 1
        self.txt("Inputs", r, 0, "label")
        self.fx("Inputs", r, 1, '"Need aid: $"&TEXT(in_need_total,"#,##0")&" at a class of "&in_need_reference_class'
                                '&" ($"&TEXT(in_need_rate,"#,##0")&" per enrollee; scales with class)"', need_lbl, "t")
        sec("Targets")
        one("ntr_target", "ntr_target (ntr_y1; blank = none)", cfg.get("ntr_target"), "in_usd")
        one("discount_target", "discount_target (blank = none)", cfg.get("discount_target"), "in_pct1",
            "live (Baseline reads it)")
        one("budget_total", "budget_total (blank = none)", cfg.get("budget_total"), "in_usd", "live (Checks)")
        one("budget_basis", "budget_basis (total_aid or merit)", cfg["budget_basis"], "in_text",
            "live (Checks): total_aid compares merit + need + specialty; merit compares merit only (OD-10)")
        self.ws["Inputs"].data_validation(self.ir - 1, 1, self.ir - 1, 1,
                                          {"validate": "list", "source": ["total_aid", "merit"]})
        mab = cfg.get("merit_actual_by_cohort") or {}
        many("merit_actual_by_cohort", "merit_actual_by_cohort (reported merit; blank = not given)",
             [mab.get(int(y)) for y in self.cohorts], "in_usd", "live (Checks: history reconciliation)")
        sec("Risk and response (placeholders until calibrated)")
        rk = cfg["risk"]
        one("common_shock_sd", "risk.common_shock_sd (s)", rk["common_shock_sd"], "in_num",
            "live; illustrative until calibrated (methodology O37)")
        one("shock_source", "risk.shock_source", rk["shock_source"], "in_text", "live")
        self.ws["Inputs"].data_validation(self.ir - 1, 1, self.ir - 1, 1,
                                          {"validate": "list", "source": ["illustrative", "public", "client"]})
        one("shock_corr", "risk.shock_corr_above_below (rho)", rk["shock_corr_above_below"], "in_num")
        for c in CASES:
            one(f"slope_{c}", f"risk.sensitivity_slopes.{c} (yield points per $1,000)", rk["sensitivity_slopes"][c],
                "in_num", "live; placeholder (D6); " + labels.RESPONSE_LABEL)
        for g in ("upper", "lower"):
            one(f"yield_floor_{g}", f"risk.yield_floor.{g}", rk["yield_floor"][g], "in_num")
            one(f"yield_cap_{g}", f"risk.yield_cap.{g}", rk["yield_cap"][g], "in_num")
        many("yield_shift_grid", "risk.yield_shift_grid (points)", rk["yield_shift_grid"], "in_num")
        many("pool_grid", "risk.pool_grid (pool multiplier)", rk["pool_grid"], "in_num")
        many("tuition_grid", "risk.tuition_grid (increase %)", rk["tuition_grid"], "in_pp")
        one("pooling_k", "pooling_k (prior weight, admits)", cfg["pooling_k"], "in_num")
        one("pooling_min_admits", "pool size for the segment pool (admits)", cfg["pooling_min_admits"], "in_num",
            "product rule (spec section 4)")
        one("evidence_tolerance_usd", "evidence_tolerance_usd", cfg["evidence_tolerance_usd"], "in_usd")
        one("marginal_admit_yield_slope", "marginal_admit_yield_slope", cfg["marginal_admit_yield_slope"], "in_num",
            "read and ignored: marginal-admit yield is not modeled")
        one("integer_admits", "integer_admits (1 = round)", int(cfg["integer_admits"]), "in_int",
            "live mode uses 0 (spec section 2)")
        one("integer_enrolled", "integer_enrolled (1 = round)", int(cfg["integer_enrolled"]), "in_int",
            "live mode uses 0 (spec section 2)")
        sec("Segments (one active per scenario; Levers row 'segment')")
        segs = cfg["segments"]
        hdr = self.ir
        self.ir += 1
        for i, h in enumerate(["name", "within residency", "members label", "share source"]):
            self.txt("Inputs", hdr, 1 + i, h, "h")
        self.txt("Inputs", hdr, 0, "segment")
        r0 = self.ir
        for sg in segs or [{"name": "", "within": {"residency": ""}, "members_label": "", "share_source": ""}]:
            r = self.ir
            self.ir += 1
            self.txt("Inputs", r, 0, "segment")
            for i, v in enumerate([sg["name"], sg["within"]["residency"], sg["members_label"], sg["share_source"]]):
                self.val("Inputs", r, 1 + i, v, "in_text")
            self.txt("Inputs", r, self.inote, "build-time (cells carry the segment)", "note")
        r1 = self.ir - 1
        for i, key in enumerate(["seg_names", "seg_within", "seg_members", "seg_share_source"]):
            self.name(f"in_{key}", "Inputs", r0, 1 + i, r1, 1 + i)
            self.inp[key] = f"in_{key}"
        sec("Shrink path (class-size table)")
        one("protect_segment", "trim.protect_segment", cfg["trim"]["protect_segment"], "in_text",
            "build-time (sets the Trim order)")
        one("trim_floor_rate", "trim.floor_rate (absolute admit rate)", cfg["trim"]["floor_rate"], "in_num")
        one("exempt_cells", "trim.exempt_cells", ", ".join(cfg["trim"]["exempt_cells"]) or "", "in_text",
            "build-time")
        sec("Pool")
        one("pool_ytd_growth", "pool_ytd_growth (annotation; no logic reads it)", cfg.get("pool_ytd_growth"),
            "in_pct1", labels.POOL_YTD_LABEL)
        sec("Display")
        one("case_selector", "case selector (Low, Middle, High)", "Middle", "in_text",
            "live: the 'Selected case' block on Summary")
        self.ws["Inputs"].data_validation(self.ir - 1, 1, self.ir - 1, 1,
                                          {"validate": "list", "source": ["Low", "Middle", "High"]})
        self.ws["Inputs"].freeze_panes(3, 1)

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
        for i in range(self.n):
            r = self.r0h + i
            for j in range(nc):
                apps, adm = cells.apps[i, j], cells.admits[i, j]
                aw, en = cells.award[i, j], cells.enrolled[i, j]
                self.val("History", r, self.hcol["apps"] + j, apps, "n0")
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
        ws.freeze_panes(self.r0h, 1)

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
                                   "grid on the right is for display only (R-01); no Ledger formula reads it.", "note")
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
        self.txt("Response", self.r0r - 3, c, "Yield at award rungs (display only; R-01). Full-tuition rung = "
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
        ws.set_column(0, 0, 30)
        ws.set_column(1, 4, 8)
        ws.set_column(5, 5, 2)
        ws.set_column(6, self.vmatrix + len(self.S), 11)
        self.txt("Levers", self.vrow_name, 0, "Scenario", "hl")
        self.txt("Levers", self.vrow_parent, 0, "parent", "hl")
        for f, lab, _ in LEVER_FIELDS:
            self.txt("Levers", self.vfield_row[f], 0, lab)
        self.txt("Levers", self.vrow_awards_changed, 0, "awards changed from parent (cells)")
        self.txt("Levers", self.vrow_rates_changed, 0, "admit rates changed from parent (cells)")
        self.txt("Levers", self.vrow_cells_changed, 0, "cells changed from parent (any lever)")
        self.txt("Levers", self.vrow_ignored, 0, "award entries ignored (full-tuition flag set)")
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
            for f, lab, kind in LEVER_FIELDS:
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
                        yrs = range(cfg["cycle"]["base_cycle"] + 1, s.plan_year + 1)
                        prod = "*".join(f"(1+INDEX(in_tuition_increase_pct,MATCH({y},in_tuition_increase_years,0))/100)"
                                        for y in yrs)
                        self.fx("Levers", r, c0, f"({prod}-1)*100", plan_increase_pct(cfg, s.plan_year), "inh_pp")
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
            for k, h in enumerate(["admit_rate", "award_usd", "full_tuition (1/0)", "note"]):
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
        self.txt("Levers", self.vrow_colhead - 1, cm, "Award matrix (resolved award, plan-year dollars: after the "
                                                      "full-tuition flag and the incentive). Named range AWARD_MATRIX.",
                 "hl")
        for j, s in enumerate(self.S):
            self.txt("Levers", self.vrow_colhead, cm + j, s.name, "h")
            lc = run.lcs[s.name]["middle"]
            colL = self.lblock[("middle", s.name)]["award"]
            for i in range(self.n):
                self.fx("Levers", self.r0v + i, cm + j, ref("Ledger_Middle", self.r0l + i, colL), lc.award[i], "usd")
        self.name("AWARD_MATRIX", "Levers", self.r0v, cm, self.r0v + self.n - 1, cm + len(self.S) - 1)
        ws.freeze_panes(self.r0v, 1)

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
                              "column (R-01): clip(clip(y0 + b/100 (award - a0)/1000, floor, cap) + shift/100, floor, "
                              "cap).", "note")
        st = self.lstat
        heads = {"upper": "upper group (1/0)", "floor": "yield floor", "cap": "yield cap", "a0": "a0", "y0": f"y0 {k}",
                 "award_lo": "award low (observed)", "award_hi": "award high (observed)",
                 "apps_base": "applications (base cycle)"}
        for j, (meas, t) in enumerate(self.targets):
            heads[f"g{j}"] = f"median sign {'GPA' if meas == 'gpa' else 'score'} {t:g}"
        self._static_heads(sheet, self.r0l - 1)
        for key, h in heads.items():
            self.txt(sheet, self.r0l - 1, st[key], h, "h")
        ws.set_column(0, 0, 24)
        ws.set_column(1, len(st), 8)
        self._cell_static(sheet, self.r0l)
        upper = response.score_group_upper(cells, cfg).astype(int)
        signs = [risk.median_signs(cells, cfg, m, t) for m, t in self.targets]
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
        self.fx(sheet, 3, c0 + 1, f"ROUND(in_tuition_base*(1+{LVf('tuition_increase_pct')}/100)/in_tuition_rounding_usd,"
                                  f"0)*in_tuition_rounding_usd", lc.tuition, "usd")
        self.txt(sheet, 4, c0, "increase %")
        self.fx(sheet, 4, c0 + 1, LVf("tuition_increase_pct"), s.tuition_increase_pct, "pp")
        self.txt(sheet, 5, c0, "need rate")
        nt = LVf("need_total")
        self.fx(sheet, 5, c0 + 1, f'IF({nt}="",in_need_total,{nt})/in_need_reference_class', lc.need_rate, "usd")
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
            self.fx(sheet, r, col["apps"], f'{S_("apps_base")}*IF({S_("upper")}=1,{LVf("pool_multiplier")},1)*'
                                           f'(1+{LVf("segment_pool_lift_pct")}/100*{B("in_seg")})', lc.apps[i], "n1")
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
                self.fx(sheet, r, col["admits_pool1"],
                        f'IF(in_integer_admits=1,ROUND({S_("apps_base")}*(1+{LVf("segment_pool_lift_pct")}/100*'
                        f'{B("in_seg")})*{B("rate")},0),{S_("apps_base")}*(1+{LVf("segment_pool_lift_pct")}/100*'
                        f'{B("in_seg")})*{B("rate")})', lc1.admits[i], "n1")
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
        self.txt("Trim", 0, 0, "Trim: shrink path (live mode), Middle case. " + labels.POLICY_UNSCORED_TRIMMED_FIRST,
                 "title")
        self.txt("Trim", 1, 0, "Left: cells in trim order (fixed at build from the first median threshold and "
                               "trim.protect_segment); rm_k = A y max(0, r - floor_rate) / r; removed_share_k(N) = "
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
        for key in ("scored", "score_lo", "upper", "residency", "floor", "cap", "gpa_class"):
            d[key] = self.LSR(k, key)
        d["T"], d["NR"] = self.LH(k, s, "T"), self.LH(k, s, "need_rate")
        d["SPEC"], d["CAP"], d["TGT"] = self.LV(s, "specialty_usd"), self.LV(s, "class_cap"), self.LV(s, "class_target")
        d["GOAL"] = self.LV(s, "segment_goal")
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
        need = f"{d['NR']}*{cls}"
        gross = f"{cls}*{d['T']}"
        aid = f"({merit}+{need}+{d['SPEC']})"
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
        if name == "p_ntr_y1_ge_target":
            return (f'IF(in_ntr_target="","",1-NORMSDIST((in_ntr_target-({SW}-{d["SPEC"]}))/'
                    f"MAX(SQRT(MAX({VN},0)),1E-300)))")
        if name == "ntr_lo90":
            return f"{SW}-{d['SPEC']}-1.645*SQRT(MAX({VN},0))"
        if name == "ntr_hi90":
            return f"{SW}-{d['SPEC']}+1.645*SQRT(MAX({VN},0))"
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
        self.dry = dry
        self.sr = 0
        if not dry:
            ws = self.ws["Summary"]
            ws.set_column(0, 0, 46)
            ws.set_column(1, 1, 10)
            ws.set_column(2, 40, 14)
        else:
            self.cpos = {}
        S = [s.name for s in self.S]
        self.sw_head()
        self.sw_selected(S)
        self.sw_main(S)
        self.sw_lowhigh(S)
        self.sw_segment(S)
        self.sw_incentive(S)
        self.sw_tuition(S)
        self.sw_yield(S)
        self.sw_pool(S)
        self.sw_class_table(S)
        self.sw_narratives(S)
        self.sw_labels()
        self.sw_contract(S)
        if not dry:
            self.ws["Summary"].freeze_panes(4, 2)

    # writing helpers that respect the dry pass
    def s_txt(self, r, c, t, fmt="t"):
        if not self.dry:
            self.txt("Summary", r, c, t, fmt)

    def s_fx(self, r, c, f, v, fmt="num"):
        if not self.dry:
            self.fx("Summary", r, c, f, v, fmt)

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

    def s_sec(self, title, note=None):
        self.sr += 1
        self.s_txt(self.sr, 0, title, "sec")
        self.sr += 1
        if note:
            self.s_note(note)

    def s_scen_head(self, S, label="", case_label=""):
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
        self.s_txt(0, 0, "Summary: scenario evaluator (scores the scenarios written in Levers; recommends nothing)",
                   "title")
        self.s_note(f"Build {bid}; data: {self.run.meta.get('data_source', '')}. Main block: Middle "
                    f"price-response case. {labels.RANGE_OUTCOME}: {labels.RANGE_OUTCOME_NOTE}. "
                    f"{labels.RANGE_CASES}: {labels.RANGE_CASES_NOTE}. The two kinds are never combined.", r=1)
        r = 2
        sh = labels.shock_label(self.cfg["risk"]["common_shock_sd"]) \
            if self.cfg["risk"]["shock_source"] == "illustrative" else ""
        self.s_txt(r, 0, labels.RESPONSE_LABEL, "hl")
        self.s_fx(r, 2, f'IF(in_shock_source="illustrative",{NAR.template_formula(labels.SHOCK_LABEL, {"s": "in_common_shock_sd"})},"")',
                  sh, "t")
        self.sr = 3

    def sw_selected(self, S):
        self.s_sec("Selected case (Inputs case selector)")
        self.s_scen_head(S, "figure", "case")
        sel = 'IF(in_case_selector="Low",1,IF(in_case_selector="High",3,2))'
        for lab, nm, fmt, ti in [("Expected class", "class_mean", "n1", None), ("ntr_y1", "ntr_y1", "usd", None),
                                 (f"P(median holds) {self.cfg['score']['measure']} "
                                  f"{self.targets[0][1]:g}", "p_median_t", "prob", 0)]:
            self.s_txt(self.sr, 0, lab)
            self.s_fx(self.sr, 1, "in_case_selector", "Middle", "t")
            for j, s in enumerate(S):
                if self.dry:
                    continue
                base_row, col = self.cpos[(nm, "low", s, ti)]
                rr = rng("Summary", base_row, col, base_row + 2, col)
                self.s_fx(self.sr, 2 + j, f"INDEX({rr},{sel})", self.pv(nm, "middle", s, ti), fmt)
            self.sr += 1

    def _row(self, S, label, unit, gen, fmt):
        """One Summary row across scenarios. gen(s) -> (formula, value)."""
        self.s_txt(self.sr, 0, label)
        self.s_txt(self.sr, 1, unit)
        for j, s in enumerate(S):
            f, v = gen(s)
            self.s_fx(self.sr, 2 + j, f, v, fmt)
        self.sr += 1

    def _cref_row(self, S, label, unit, name, fmt, k="middle", t=None):
        def gen(s):
            if self.dry:
                return "0", 0
            return self.cref(name, k, s, t), self.pv(name, k, s, t)
        self._row(S, label, unit, gen, fmt)

    def _direct_row(self, S, label, unit, name, fmt, k="middle", t=None):
        self._row(S, label, unit, lambda s: (self.fm(name, k, s, t), self.pv(name, k, s, t)), fmt)

    def sw_main(self, S):
        cfg = self.cfg
        self.s_sec("Main results (Middle case)", labels.RESPONSE_LABEL + ". Probabilities and ranges: "
                   + labels.shock_label(cfg["risk"]["common_shock_sd"]) + " (while shock_source is illustrative).")
        self.s_scen_head(S, "figure", "unit")
        lv = lambda f: (lambda s: (self.LV(s, f), _clean(getattr(self.run.scen(s), f))))  # noqa: E731
        self._row(S, "parent", "", lambda s: (f'"{self.run.parents[s].name}"' if self.run.parents[s] else '"(none)"',
                                              self.run.parents[s].name if self.run.parents[s] else "(none)"), "t")
        self._row(S, "Tuition (plan year)", "USD", lambda s: (self.LH("middle", s, "T"),
                                                              self.run.lcs[s]["middle"].tuition), "usd")
        self._row(S, "Tuition increase", "%", lv("tuition_increase_pct"), "pp")
        self._row(S, "Class target", "students", lv("class_target"), "n0")
        self._row(S, "Class cap", "students", lv("class_cap"), "n0")
        for nm, lab in [("apps_total", "Applications"), ("apps_in", "Applications, in-state"),
                        ("apps_out", "Applications, out-of-state"), ("admits_total", "Admits"),
                        ("admits_in", "Admits, in-state"), ("admits_out", "Admits, out-of-state")]:
            self._direct_row(S, lab, "students", nm, "n1")
        self._cref_row(S, "Expected class", "students", "class_mean", "n1")
        self._cref_row(S, f"Class, {labels.RANGE_OUTCOME}: low", "students", "class_lo90", "n1")
        self._cref_row(S, f"Class, {labels.RANGE_OUTCOME}: high", "students", "class_hi90", "n1")
        self._cref_row(S, "P(class above cap)", "probability", "p_class_over_cap", "prob")
        self._cref_row(S, "P(class within target band)", "probability", "p_class_in_band", "prob")
        meas = cfg["score"]["measure"]
        for ti, t in enumerate(self.score_ts):
            self._direct_row(S, f"Enrolled at or above {meas} {t:g}", "students", "enrolled_at_or_above", "n1", t=ti)
            self._cref_row(S, f"Share at or above {meas} {t:g} (of enrolled with a score)", "ratio",
                           "share_at_or_above_t", "pct1", t=ti)
        self._direct_row(S, f"Enrolled below {meas} floor", "students", "enrolled_below_floor", "n1")
        self._direct_row(S, "Enrolled with GPA class hi", "students", "enrolled_gpa_hi", "n1")
        self._cref_row(S, "Unscored enrolled (outside the score margins)", "students", "unscored_count", "n1")
        self._direct_row(S, "Blank-GPA enrolled (outside the GPA margin)", "students", "gpa_blank_count", "n1")
        for ti, (m, t) in enumerate(self.targets):
            nm = "GPA" if m == "gpa" else meas
            self._cref_row(S, f"Median margin, {nm} {t:g}", "students", "margin_t", "n1", t=ti)
            self._cref_row(S, f"P(median holds), {nm} {t:g}", "probability", "p_median_t", "prob", t=ti)
            self._cref_row(S, f"P(median holds), {nm} {t:g}, rho 0.5: {labels.RHO_SENSITIVITY}", "probability",
                           "p_median_t_rho05", "prob", t=ti)
        self._cref_row(S, "Full-tuition enrolled (award at or above tuition)", "students", "full_tuition_n", "n1")
        self._cref_row(S, "No-merit-award enrolled (award zero)", "students", "no_merit_award_n", "n1")
        self._cref_row(S, "Barbell index", "ratio", "barbell", "r3")
        self._cref_row(S, "gross_y1", "USD", "gross_y1", "usd")
        self._cref_row(S, "Merit", "USD", "merit", "usd")
        self._cref_row(S, "of which incentive cost", "USD", "incentive_cost", "usd")
        self._cref_row(S, "Need aid", "USD", "need", "usd")
        self._cref_row(S, "Specialty", "USD", "specialty", "usd")
        self._cref_row(S, "Aid (merit + need + specialty)", "USD", "aid", "usd")
        self._cref_row(S, "ntr_y1 (first-year net tuition revenue, entering class)", "USD", "ntr_y1", "usd")
        self._direct_row(S, f"ntr_y1, {labels.RANGE_OUTCOME}: low", "USD", "ntr_lo90", "usd")
        self._direct_row(S, f"ntr_y1, {labels.RANGE_OUTCOME}: high", "USD", "ntr_hi90", "usd")
        self._cref_row(S, "P(ntr_y1 at or above ntr_target)", "probability", "p_ntr_y1_ge_target", "prob")
        self._cref_row(S, labels.DISCOUNT_LABEL, "ratio", "discount_entering_y1", "pct1")
        self._cref_row(S, "Average aid per enrollee", "USD", "avg_aid", "usd")
        base0 = self.S[0].name

        def pot(s):
            if self.dry:
                return "0", 0
            return (f"{self.cref('ntr_y1', 'middle', base0)}-{self.cref('ntr_y1', 'middle', s)}",
                    self.vals["price_of_target"][s])
        self._row(S, "Price of the target (Baseline ntr_y1 minus scenario ntr_y1)", "USD", pot, "usd")
        self._row(S, "Discount target", "ratio", lv("discount_target"), "pct1")

        def dmargin(s):
            if self.dry:
                return "0", 0
            t = self.LV(s, "discount_target")
            sc = self.run.scen(s)
            d = self.pv("discount_entering_y1", "middle", s)
            return (f'IF({t}="","",{t}-{self.cref("discount_entering_y1", "middle", s)})',
                    None if sc.discount_target is None else sc.discount_target - d)
        self._row(S, "Margin to discount target (target minus rate)", "ratio", dmargin, "pct1")
        self._cref_row(S, "Share of enrolled in cells where the yield is extrapolated", "ratio",
                       "evidence_extrapolated_share", "pct1")

    def sw_lowhigh(self, S):
        self.s_sec(f"{labels.RANGE_CASES} ({labels.RANGE_CASES_NOTE})")
        self.s_scen_head(S, "figure", "case")
        meas = self.cfg["score"]["measure"]
        rows = [("Expected class", "class_mean", "n1", None), ("ntr_y1", "ntr_y1", "usd", None)]
        for ti, (m, t) in enumerate(self.targets):
            rows.append((f"P(median holds), {'GPA' if m == 'gpa' else meas} {t:g}", "p_median_t", "prob", ti))
        for lab, nm, fmt, ti in rows:
            for k in ("low", "high"):
                self.s_txt(self.sr, 0, lab)
                self.s_txt(self.sr, 1, CASE_TITLE[k])
                for j, s in enumerate(S):
                    if not self.dry:
                        self.s_fx(self.sr, 2 + j, self.cref(nm, k, s, ti), self.pv(nm, k, s, ti), fmt)
                self.sr += 1

    def sw_segment(self, S):
        cfg = self.cfg
        seg_lab = ""
        if cfg["segments"] and cfg["segments"][0]["share_source"] == "assumed":
            seg_lab = labels.SEGMENT_SHARE_LABEL + ". "
        self.s_sec("Segment block (Middle case)", seg_lab + labels.RESPONSE_LABEL + ". Excel shows the normal form of "
                   "P(segment enrolled at or above goal); the exact value (convolution, from the build) is static.")
        self.s_scen_head(S, "figure", "unit")
        self._row(S, "Active segment", "", lambda s: (self.LH("middle", s, "seg"),
                                                      L.active_segment(cfg, self.run.scen(s)) or ""), "t")
        for nm, lab, fmt in [("segment_apps", "Segment applications", "n1"),
                             ("segment_admits", "Segment admits", "n1")]:
            self._direct_row(S, lab, "students", nm, fmt)
        self._cref_row(S, "Segment enrolled (E_S)", "students", "segment_enrolled", "n1")
        self._cref_row(S, "Segment share of class", "ratio", "segment_share", "pct1")
        self._direct_row(S, "Segment merit dollars", "USD", "segment_merit", "usd")
        self._cref_row(S, f"Segment enrolled, {labels.RANGE_OUTCOME}: low", "students", "segment_lo90", "n1")
        self._cref_row(S, f"Segment enrolled, {labels.RANGE_OUTCOME}: high", "students", "segment_hi90", "n1")
        self._direct_row(S, "Segment goal (rounded up)", "students", "segment_goal", "n0")
        self._cref_row(S, "P(segment enrolled at or above goal), normal form", "probability", "p_segment_goal", "prob")

        def exact(s):
            v = self.vals["seg_exact"][s]
            if v is None:
                return '""', None
            if isinstance(v, str):
                return xs(v), v
            return f"{v!r}", v
        self._row(S, "P(segment enrolled at or above goal), exact (static, from the build)", "probability", exact,
                  "prob")

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
        self.exact_status_row = self.sr
        self._row(S, "Exact value status (static value against the current segment enrollment and goal)", "",
                  status, "t")
        self._direct_row(S, "Approximation flag", "", "segment_approximate", "t")

    def sw_incentive(self, S):
        self.s_sec("Incentive block (Middle case; against the parent)",
                   labels.RESPONSE_LABEL + ". The figures are what the assumed response implies, not estimates of what "
                   "an incentive causes.")
        self.s_scen_head(S, "figure", "unit")
        self._cref_row(S, "Incentive cost (C)", "USD", "incentive_cost", "usd")
        self._cref_row(S, "of which paid to students the parent already enrolled (C_any)", "USD",
                       "incentive_paid_anyway", "usd")
        self._cref_row(S, "Paid-anyway share (C_any / C)", "ratio", "incentive_paid_anyway_share", "pct1")
        self._cref_row(S, "Additional enrollees (dE)", "students", "additional_enrollees", "n1")
        self._direct_row(S, "Change in merit dollars (dSpend)", "USD", "merit_change", "usd")
        self._direct_row(S, "Change in ntr_y1 over the same cells (dNTR)", "USD", "ntr_change", "usd")
        self._cref_row(S, "Aid per additional enrollee (dSpend / dE)", "USD", "aid_per_additional", "usd")
        self._direct_row(S, "  reading", "", "aid_per_additional_kind", "t")
        self._cref_row(S, "ntr_y1 change per additional enrollee (dNTR / dE)", "USD", "ntr_per_additional", "usd")
        self._direct_row(S, "Cells with an incentive", "cells", "incentive_cells", "int")
        self._cref_row(S, "Validity", "", "incentive_valid", "t")
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
        self._row(S, "Bonus implied by a dollar pool (pool / Baseline enrolled in scope; informational)", "USD",
                  implied, "usd")

    def _strip_table(self, S, which, keycol_label, key_fmt, grid_refs, colheads, fmts, gen):
        """Rows (s, grid value); gen(s, gi) -> list of (formula, value)."""
        self.s_txt(self.sr, 0, "scenario", "h")
        self.s_txt(self.sr, 1, keycol_label, "h")
        for c, h in enumerate(colheads):
            self.s_txt(self.sr, 2 + c, h, "h")
        if not self.dry:
            self.ws["Summary"].set_row(self.sr, 48)
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
                        self.s_fx(self.sr, 2 + c, f, v, fmts[c])
                    expect = rows[idx][2]
                    assert len(expect) == len(colheads)
                idx += 1
                self.sr += 1
        return r0, self.sr - 1

    def sw_tuition(self, S):
        cfg = self.cfg
        self.s_sec("Tuition what-if (Middle case; class and mix held fixed)", labels.STICKER_LABEL
                   + " Awards are recomputed at T(p) under the scenario's award rule.")
        grid = self.inp_list["tuition_grid"]
        cols = K.strip_columns(cfg)["tuition_whatif"]

        def gen(s, gi):
            st = self.vals["strips"][s]["tuition_whatif"]["tuition_whatif"][gi]
            col = self.lblock[("middle", s)][f"tw{gi}"]
            Tp = ref("Ledger_Middle", 3, col)
            AWp = rng("Ledger_Middle", self.r0l, col, self.r0l + self.n - 1, col)
            E = self.LR("middle", s, "enrolled")
            NR = self.LH("middle", s, "need_rate")
            SP = self.LV(s, "specialty_usd")
            ntr = f"({Tp}*SUM({E})-SUMPRODUCT({E},{AWp})-{NR}*SUM({E})-{SP})"
            return [(Tp, st["tuition"]), (ntr, st["ntr_y1"]),
                    (f"IF(SUM({E})>0,{ntr}/SUM({E}),0)", st["net_tuition_per_student"]),
                    (f"IF(SUM({E})*{Tp}>0,(SUM({E})*{Tp}-{ntr})/(SUM({E})*{Tp}),0)", st["discount_entering_y1"])]
        r0, r1 = self._strip_table(S, "tuition_whatif", "increase %", "pp", grid,
                                   ["tuition T(p)", "ntr_y1", "net tuition per student", labels.DISCOUNT_LABEL],
                                   ["usd", "usd", "usd", "pct1"], gen)
        self.s_name("TW_TUITION_WHATIF", r0, 2, r1, 2 + len(cols) - 1)
        self.sr += 1
        # the two net-tuition lines
        self.s_txt(self.sr, 0, "scenario", "h")
        for c, h in enumerate(["fixed-dollar line (T_s - T_base)", "example award A", "scaled line p (T_base - A)",
                               "Awards fixed in dollars", "Awards scaled with tuition"]):
            self.s_txt(self.sr, 1 + c, h, "h")
        self.sr += 1
        r0 = self.sr
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
                self.s_fx(r, 4, fixed_t, tw["net_tuition_line_fixed_text"], "t")
                scaled_t = NAR.template_formula(labels.NET_TUITION_SCALED, {
                    "p": f'TEXT({P},"0.0")&"%"', "x": f'"$"&TEXT({a1(r, 3)},"#,##0")',
                    "award": f'"$"&TEXT({a1(r, 2)},"#,##0")'})
                self.s_fx(r, 5, scaled_t, tw["net_tuition_line_scaled_text"], "t")
            self.sr += 1
        self.s_name("TW_NET_TUITION_LINE_FIXED", r0, 1, self.sr - 1, 1)
        self.s_name("TW_NET_TUITION_LINE_SCALED", r0, 3, self.sr - 1, 3)
        self.s_note("Both lines are arithmetic at constant award; neither changes yield. Example award: "
                    "enrolled-weighted mean base-cycle lever award over enrollees whose lever award, before any "
                    "incentive, is below base-cycle tuition and whose cell has no full-tuition flag, zero awards "
                    "included, rounded to $1,000.")

    def sw_yield(self, S):
        cfg = self.cfg
        self.s_sec("Yield what-if strip (Middle case; shift on top of the scenario's own shift)",
                   labels.ASSUMPTION_LABEL + ". The strip ignores the yield floor and cap; see the clip count. "
                   + (labels.shock_label(cfg["risk"]["common_shock_sd"])
                      if cfg["risk"]["shock_source"] == "illustrative" else ""))
        cols = K.strip_columns(cfg)["yield_strip"]
        meas = cfg["score"]["measure"]
        heads = ["expected class", "P(class above cap)", "P(class within band)", "mean ntr_y1",
                 "P(ntr_y1 at or above target)"]
        fmts = ["n1", "prob", "prob", "usd", "prob"]
        for m, t in self.targets:
            nm = "GPA" if m == "gpa" else meas
            heads += [f"margin {nm} {t:g}", f"P(median) {nm} {t:g}"]
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
                   (f"{SW}-{d['SPEC']}", row["ntr_mean"]),
                   (f'IF(in_ntr_target="","",1-NORMSDIST((in_ntr_target-({SW}-{d["SPEC"]}))/'
                    f"MAX(SQRT(MAX({VN},0)),1E-300)))", row["p_ntr_y1_ge_target"])]
            for ti, key in enumerate(self.targets):
                G = d[f"g{ti}"]
                gp, gm = f"SUMPRODUCT(({G}=1)*{A}*{Yd})", f"SUMPRODUCT(({G}=-1)*{A}*{Yd})"
                vm = f"(SUMPRODUCT(({G}<>0)*{A}*{Yd}*(1-{Yd}))+{sd}^2*({gp}^2+{gm}^2-2*{rho}*{gp}*{gm}))"
                out.append((f"{gp}-{gm}", row["median"][key]["margin"]))
                out.append((f"1-NORMSDIST((-0.5-({gp}-{gm}))/SQRT(MAX({vm},1E-300)))", row["median"][key]["p"]))
            return out
        r0, r1 = self._strip_table(S, "yield_strip", "shift (pts)", "pp", self.inp_list["yield_shift_grid"], heads,
                                   fmts, gen)
        self.s_name("YS_YIELD_STRIP", r0, 2, r1, 2 + len(cols) - 1)
        self.sr += 1
        self.s_txt(self.sr, 0, "scenario", "h")
        for c, h in enumerate(["cells where a bound would bind at the largest shift",
                               f"shift that moves the expected class to target ({labels.LINEAR_APPROX})",
                               f"shift that moves mean ntr_y1 to ntr_target ({labels.LINEAR_APPROX})"]):
            self.s_txt(self.sr, 1 + c, h, "h")
        self.sr += 1
        r0 = self.sr
        for s in S:
            self.s_txt(self.sr, 0, s)
            if not self.dry:
                ys = self.vals["strips"][s]["yield_strip"]
                d = self.g("middle", s)
                A, Y, W = d["admits"], d["yield"], d["w"]
                g = "in_yield_shift_grid"
                self.s_fx(self.sr, 1, f"SUMPRODUCT(({A}>0)*((({Y}+MAX({g})/100>{d['cap']})+({Y}+MIN({g})/100<"
                                      f"{d['floor']}))>0))", ys["clip_count"], "int")
                self.s_fx(self.sr, 2, f'IF(SUM({A})>0,({d["TGT"]}-SUMPRODUCT({A},{Y}))/SUM({A})*100,"")',
                          ys["breakeven_shift_class"], "r3")
                self.s_fx(self.sr, 3, f'IF(in_ntr_target="","",IF(SUMPRODUCT({W},{A})<>0,(in_ntr_target-'
                                      f'(SUMPRODUCT({W},{A},{Y})-{d["SPEC"]}))/SUMPRODUCT({W},{A})*100,""))',
                          ys["breakeven_shift_ntr"], "r3")
            self.sr += 1
        self.s_name("YS_BREAKEVEN_SHIFT_CLASS", r0, 2, self.sr - 1, 2)
        self.s_name("YS_BREAKEVEN_SHIFT_NTR", r0, 3, self.sr - 1, 3)

    def sw_pool(self, S):
        cfg = self.cfg
        t0 = cfg["score"]["median_thresholds"][0]
        self.s_sec(f"Pool strip (Middle case): {labels.POOL_STRIP_LABEL}",
                   f"Every lever applied except the pool multiplier, which m replaces (the segment lift stays). Median "
                   f"at {cfg['score']['measure']} {t0:g}. Pool growth to date: see Inputs pool_ytd_growth ("
                   f"{labels.POOL_YTD_LABEL}).")
        self.s_txt(self.sr, 0, "Pool growth to date (pool_ytd_growth)")
        self.s_fx(self.sr, 2, 'IF(in_pool_ytd_growth="","not set",in_pool_ytd_growth)',
                  "not set" if cfg.get("pool_ytd_growth") is None else cfg["pool_ytd_growth"], "pct1")
        self.sr += 1
        # parts at m = 1
        pk = ["M", "V", "Gp", "Gm", "Vm", "W", "Vn"]
        self.s_txt(self.sr, 0, "scenario: split at m = 1", "h")
        self.s_txt(self.sr, 1, "part", "h")
        for c, h in enumerate(pk):
            self.s_txt(self.sr, 2 + c, h, "h")
        self.sr += 1
        self.pool_parts = {}
        sd = "in_common_shock_sd"
        for s in S:
            d = self.g("middle", s)
            A1 = self.LR("middle", s, "admits_pool1")
            Y, W, U, G = d["yield"], d["w"], d["upper"], d["g0"]
            for part, u in (("lo", 0), ("hi", 1)):
                self.s_txt(self.sr, 0, s)
                self.s_txt(self.sr, 1, part)
                m = f"({U}={u})"
                fs = {"M": f"SUMPRODUCT({m}*{A1}*{Y})", "V": f"SUMPRODUCT({m}*{A1}*{Y}*(1-{Y}))",
                      "Gp": f"SUMPRODUCT({m}*({G}=1)*{A1}*{Y})", "Gm": f"SUMPRODUCT({m}*({G}=-1)*{A1}*{Y})",
                      "Vm": f"SUMPRODUCT({m}*({G}<>0)*{A1}*{Y}*(1-{Y}))", "W": f"SUMPRODUCT({m}*{W}*{A1}*{Y})",
                      "Vn": f"SUMPRODUCT({m}*{W}*{W}*{A1}*{Y}*(1-{Y}))"}
                for c, key in enumerate(pk):
                    v = self.vals["parts"][s][part][key] if not self.dry else 0
                    self.s_fx(self.sr, 2 + c, fs[key], v, "usd" if key in ("W", "Vn") else "num")
                    self.pool_parts[(s, part, key)] = a1(self.sr, 2 + c)
                self.sr += 1
        self.sr += 1
        cols = K.strip_columns(cfg)["pool_strip"]
        heads = ["growth (m - 1)", "expected class", "P(class above cap)", f"median margin {t0:g}",
                 f"P(median) {t0:g}", "mean ntr_y1", "ntr_y1 SD"]
        fmts = ["pct1", "n1", "prob", "n1", "prob", "usd", "usd"]

        def gen(s, gi):
            row = self.vals["strips"][s]["pool_strip"]["pool_strip"][gi]
            P = lambda part, key: self.pool_parts[(s, part, key)]  # noqa: E731
            m = self.inp_list["pool_grid"][gi]
            M = f"({P('lo', 'M')}+{m}*{P('hi', 'M')})"
            V = f"({P('lo', 'V')}+{m}*{P('hi', 'V')}+{sd}^2*{M}^2)"
            Gp = f"({P('lo', 'Gp')}+{m}*{P('hi', 'Gp')})"
            Gm = f"({P('lo', 'Gm')}+{m}*{P('hi', 'Gm')})"
            Vm = f"({P('lo', 'Vm')}+{m}*{P('hi', 'Vm')}+{sd}^2*({Gp}^2+{Gm}^2-2*in_shock_corr*{Gp}*{Gm}))"
            Wm = f"({P('lo', 'W')}+{m}*{P('hi', 'W')})"
            Vn = f"({P('lo', 'Vn')}+{m}*{P('hi', 'Vn')}+{sd}^2*{Wm}^2)"
            CAP = self.LV(s, "class_cap")
            return [(f"{m}-1", row["growth"]), (M, row["class_mean"]),
                    (f"1-NORMSDIST(({CAP}+0.5-{M})/SQRT(MAX({V},1E-300)))", row["p_class_over_cap"]),
                    (f"{Gp}-{Gm}", row["margin"]),
                    (f"1-NORMSDIST((-0.5-({Gp}-{Gm}))/SQRT(MAX({Vm},1E-300)))", row["p_median"]),
                    (f"{Wm}-{self.LV(s, 'specialty_usd')}", row["ntr_mean"]), (f"SQRT(MAX({Vn},0))", row["ntr_sd"])]
        r0, r1 = self._strip_table(S, "pool_strip", "pool multiplier m", "num", self.inp_list["pool_grid"], heads,
                                   fmts, gen)
        self.s_name("PS_POOL_STRIP", r0, 2, r1, 2 + len(cols) - 1)

    def sw_class_table(self, S):
        cfg = self.cfg
        self.s_sec("Class-size table (shrink path; Middle case)",
                   "The shrink path writes admit rates (Trim sheet); yield is constant when admit rates change (D1). "
                   + labels.POLICY_UNSCORED_TRIMMED_FIRST + " f = N / M is the factor a uniform cut would apply.")
        cols = K.strip_columns(cfg)["class_table"]
        meas = cfg["score"]["measure"]
        heads = ["f = N / M", "expected class"]
        fmts = ["r3", "n1"]
        for m, t in self.targets:
            nm = "GPA" if m == "gpa" else meas
            heads += [f"margin {nm} {t:g}", f"P(median) {nm} {t:g}"]
            fmts += ["n1", "prob"]
        heads += ["ntr_y1", labels.DISCOUNT_LABEL, "segment enrolled", "lowest band admitted"]
        fmts += ["usd", "pct1", "n1", "num"]
        bands = K.band_keys(cfg)
        heads += [f"admits cut, {b if b == 'unscored' else format(b, 'g')}" for b in bands]
        fmts += ["n1"] * len(bands)
        heads += ["status"]
        fmts += ["t"]
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
            ct = self.vals["strips"][s]["class_table"]["class_table"][gi]
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
            T, NR, SP = d["T"], d["NR"], d["SPEC"]
            ntr = f"({cls}*{T}-SUMPRODUCT({AN},{Y},{AW})-{NR}*{cls}-{SP})"
            status = (f'IF({cap_},{xs(labels.CT_ABOVE_CAP)},IF({N}>={Mref},{xs(labels.CT_NOT_APPLICABLE)},'
                      f'IF({Mref}-{N}>{RK}+0.000000001,"N not reachable: shortfall "&TEXT({Mref}-{N}-{RK},"0.0"),'
                      f'{xs(labels.CT_OK)})))')
            row_vals = ct_rows[(s, gi)]
            out = [(f'IF({Mref}>0,{N}/{Mref},"")', row_vals[0]), (wrap(cls), row_vals[1])]
            ci = 2
            for ti, key in enumerate(self.targets):
                G = d[f"g{ti}"]
                gp = f"SUMPRODUCT(({G}=1)*{AN}*{Y})"
                gm = f"SUMPRODUCT(({G}=-1)*{AN}*{Y})"
                vm = f"(SUMPRODUCT(({G}<>0)*{AN}*{Y}*(1-{Y}))+{sd}^2*({gp}^2+{gm}^2-2*{rho}*{gp}*{gm}))"
                out.append((wrap(f"SUMPRODUCT({G},{AN},{Y})"), row_vals[ci]))
                out.append((wrap(f"1-NORMSDIST((-0.5-({gp}-{gm}))/SQRT(MAX({vm},1E-300)))"), row_vals[ci + 1]))
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
        r0, r1 = self._strip_table(S, "class_table", "N", "n0", self.inp_list["class_what_if"], heads, fmts, gen)
        self.s_name("CT_CLASS_TABLE", r0, 2, r1, 2 + len(cols) - 1)

    def sw_narratives(self, S):
        cfg = self.cfg
        self.s_sec("Narratives (Middle case)")
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
                self.s_txt(self.sr, 1, "Changes from parent" if kind == "changes" else "Projected outcome", "tw")
                if not self.dry:
                    ws = self.ws["Summary"]
                    if kind == "changes":
                        f = NAR.formula(NAR.changes_parts(p is not None), r, ctx_x)
                        v = NAR.changes(self.run, self.vals, sc)
                    else:
                        f = NAR.formula(NAR.outcome_parts(nt), r, ctx_x) + "&" + NAR.labels_formula_parts(lr)
                        v = NAR.outcome(self.run, self.vals, sc)
                    ws.merge_range(self.sr, 2, self.sr, width, "", self.f["mergew"])
                    self.expected[("Summary", self.sr, 2)] = v
                    ws.write_formula(self.sr, 2, f, self.f["mergew"], -999 if self.sentinel else v)
                    ws.set_row(self.sr, 24 if kind == "changes" else 78)
                self.sr += 1

    def sw_labels(self):
        self.s_sec("Labels and range kinds")
        self.s_txt(self.sr, 0, "SHOCK_LABEL", "hl")
        # [v0.6.2, P2-04] the template filled in from Inputs (live)
        self.s_fx(self.sr, 1, NAR.template_formula(labels.SHOCK_LABEL, {"s": "in_common_shock_sd"}),
                  labels.shock_label(self.cfg["risk"]["common_shock_sd"]), "t")
        self.sr += 1
        items = [("RESPONSE_LABEL", labels.RESPONSE_LABEL), ("ASSUMPTION_LABEL", labels.ASSUMPTION_LABEL),
                 ("SEGMENT_SHARE_LABEL", labels.SEGMENT_SHARE_LABEL),
                 ("Range kind", f"{labels.RANGE_OUTCOME} ({labels.RANGE_OUTCOME_NOTE})"),
                 ("Range kind", f"{labels.RANGE_CASES} ({labels.RANGE_CASES_NOTE})"),
                 ("Probability display", f"while shock_source is illustrative: '{labels.PROB_UNDER}' and "
                                         f"'{labels.PROB_OVER}' beyond 5% and 95%"),
                 ("Need aid", "see Inputs (need aid scales with class; need_rate does not change with the class "
                              "target)")]
        for a, b in items:
            self.s_txt(self.sr, 0, a, "hl")
            self.s_txt(self.sr, 1, b)
            self.sr += 1

    def sw_contract(self, S):
        self.s_sec("Interface contract outputs (spec section 15 item 11), every case",
                   "Named ranges: prefix plus the contract name in upper case; rows are cases (and thresholds), "
                   "columns are scenarios. The policy document and any later dashboard read these ranges.")
        self.s_scen_head(S, "contract name (range)", "case")
        for name, prefix, _ in K.SK:
            self._contract_block(S, name, prefix, None)
        for name, prefix, _ in K.SKT:
            self._contract_block(S, name, prefix, list(range(len(self.targets))))
        self._contract_block(S, "share_at_or_above_t", "SUM", list(range(len(self.score_ts))))

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
                    else:
                        m, t = self.targets[ti]
                        lab = f"{rn} [{'GPA ' if m == 'gpa' else ''}{t:g}]"
                self.s_txt(self.sr, 0, lab)
                self.s_txt(self.sr, 1, CASE_TITLE[k])
                for j, s in enumerate(S):
                    if self.dry:
                        self.cpos[(name, k, s, ti)] = (self.sr, 2 + j)
                    else:
                        self.s_fx(self.sr, 2 + j, self.fm(name, k, s, ti), self.pv(name, k, s, ti), fmt)
                self.sr += 1
        self.s_name(rn, r0, 2, self.sr - 1, 2 + len(S) - 1)

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
            for lab, cond, msg in [
                    ("admits at most applications", lambda s: f"({self.LR(k, s, 'admits')}>{self.LR(k, s, 'apps')}+"
                                                              f"0.000000001)", "cells with admits above applications"),
                    ("enrolled at most admits", lambda s: f"({self.LR(k, s, 'enrolled')}>{self.LR(k, s, 'admits')}+"
                                                          f"0.000000001)", "cells with enrolled above admits"),
                    ("award at least zero and at most tuition after the incentive",
                     lambda s: f"(({self.LR(k, s, 'award')}<0)+({self.LR(k, s, 'award')}>{self.LH(k, s, 'T')}+"
                               f"0.000001)>0)", "cells with an award outside [0, tuition]"),
                    ("yield between 0 and 1", lambda s: f"(({self.LR(k, s, 'yield')}<0)+({self.LR(k, s, 'yield')}>1)"
                                                        f">0)", "cells with a yield outside [0, 1]")]:
                cnt = "+".join(f"SUMPRODUCT({cond(s)}*1)" for s in S)
                row(f"Ledger: {lab}", CASE_SHEET[k], f'IF({cnt}=0,"OK",({cnt})&" {msg}")', "OK")
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
            v = (f"class {M:,.1f}; cap {sc.class_cap:g} ({'above cap' if M > sc.class_cap else 'at or below cap'}); "
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
                f"OK: {kind} ${x:,.0f} within budget" if x <= b else f"{kind} ${x:,.0f} above budget")
            ar = self.sref("aid", "middle", s)
            mr = self.sref("merit", "middle", s)
            xr = f'IF(in_budget_basis="merit",{mr},{ar})'
            kr = 'IF(in_budget_basis="merit","merit","aid")'
            row("Spend against budget_total (Middle case; budget_basis: total aid, or merit only)", s,
                f'IF(in_budget_total="","not set (budget_total blank)",IF({xr}<=in_budget_total,"OK: "&{kr}&" $"&'
                f'TEXT({xr},"#,##0")&" within budget",{kr}&" $"&TEXT({xr},"#,##0")&" above budget"))', v)
        # history reconciliation [v0.6.2, Q-8f]
        for j, h in enumerate(self.vals["history_reconciliation"]):
            act = self.inp_list["merit_actual_by_cohort"][j]
            imp = f"SUMPRODUCT({self.HR('enrolled', j)},{self.HR('award', j)})"
            y = h["cohort"]
            v = (f"not run: merit_actual_by_cohort not given for {y}" if h["actual"] is None else
                 f"grid-implied ${h['implied']:,.0f} against reported ${h['actual']:,.0f}: gap {100 * h['gap']:.1f}%")
            row(f"History reconciliation {y}: grid-implied merit (enrolled x award over cells) against reported "
                "merit (merit_actual_by_cohort; percent gap)", "History",
                f'IF({act}="","not run: merit_actual_by_cohort not given for {y}","grid-implied $"&TEXT({imp},'
                f'"#,##0")&" against reported $"&TEXT({act},"#,##0")&": gap "&TEXT(({imp}-{act})/{act}*100,"0.0")&"%")',
                v)
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
        t0 = cfg["score"]["median_thresholds"][0]
        row("Trim order: first median threshold equals its value at build", "Inputs",
            f'IF({self.inp_list["median_thresholds"][0]}={t0:g},"OK",{rb(f"{t0:g}")})', "OK")
        ps = cfg["trim"]["protect_segment"]
        row("Trim order: trim.protect_segment equals its value at build", "Inputs",
            f'IF(in_protect_segment={xs(ps)},"OK",{rb(ps)})', "OK")
        ex = ", ".join(cfg["trim"]["exempt_cells"])
        row("Trim: trim.exempt_cells equals its value at build", "Inputs",
            f'IF(in_exempt_cells={xs(ex)},"OK",{rb(ex or "none")})', "OK")
        for s in S:
            seg = L.active_segment(cfg, run.scen(s)) or ""
            row("Trim order: active segment equals its value at build", s,
                f'IF({self.LH("middle", s, "seg")}={xs(seg)},"OK",{rb(seg or "none")})', "OK")
        for j, s in enumerate(S):
            st = ref("Summary", self.exact_status_row, 2 + j)
            row("Static exact segment probability is current (Summary segment block)", s,
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
            row("Full-tuition award conflicts (P1.1-1)", s, f'IF({tref}=0,"OK",{tref}&" cells: {msg}")', v)
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
                ("uncommitted files", m.get("uncommitted_files", "")),
                ("cached values", "sentinel: every formula cell holds -999 until recalculated (use this copy for the "
                                  "desktop Excel check)" if self.sentinel else "Python values (the build's results)"),
                ("timestamp", _dt.datetime.now().astimezone().isoformat(timespec="seconds")),
                ("response source", self.run.base.source_label + " (placeholder slopes; sw/response.py)"),
                ("shock source", f"{self.cfg['risk']['shock_source']} (s = {self.cfg['risk']['common_shock_sd']:g})"),
                ("mode", "Live (reproduce mode is Phase 3; not built)"),
                ("python", platform.python_version()), ("xlsxwriter", xlsxwriter.__version__)]
        for i, (a, b) in enumerate(rows):
            self.txt("RunLog", 2 + i, 0, a, "hl")
            self.txt("RunLog", 2 + i, 1, str(b))

    def w_readme(self):
        cfg = self.cfg
        ws = self.ws["README"]
        ws.set_column(0, 0, 34)
        ws.set_column(1, 1, 120)
        r = 0
        self.txt("README", r, 0, "Scenario workbook (prototype, spec v0.6.2): README", "title")
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
             "with a score below t. Share at or above t: over expected enrolled with a score. E_S: segment enrolled. "
             "Incentive cost, paid-anyway share, aid per additional enrollee (items 19 to 21); evidence share (item "
             "24). Ratios are ratios of expected values, E[X] / E[Y], everywhere."),
            ("Static and live", "Live: everything on History (rates), Response, Levers, the Ledgers, Summary, Trim and "
                                "Checks recalculates from Inputs and Levers. Static: cell counts (History data), the "
                                "trim order (fixed at build from the first median threshold, protect_segment, the "
                                "exempt cells and each scenario's active segment), the number of grid values, the exact "
                                "segment probability (labelled 'static, from the build'), RunLog. Inputs marked "
                                "'build-time' need a rebuild; Checks shows 'rebuild needed' when a trim-order input "
                                "differs from its value at build, and Summary marks the exact probability stale when "
                                "the segment's expected enrollment or goal changes."),
            ("Policy choices", labels.POLICY_UNSCORED_TRIMMED_FIRST + " " + labels.POLICY_UNSCORED_EXCLUDED
             + " (unscored_in_median = " + cfg["unscored_in_median"] + ")."),
            ("Yield", "One Ledger column per case: clip(clip(y0 + b/100 (award - a0)/1000, floor, cap) + shift/100, "
                      "floor, cap). The Response rung grid is display only (R-01). Yield is constant when admit rates "
                      "change (D1); sticker price does not move applications or yield (D10)."),
            ("Not built here", "Reproduce mode and the Reproduce sheet (Phase 3); the Distribution sheet with step "
                               "sizes and the barbell detail (Phase 4); anything deferred in DECISIONS.md."),
            ("Interface contract", "Named ranges (spec section 15 item 11; canonical names, no aliases): " + ", ".join(
                rn for rn, _, _, _ in K.contract_table()) + ". AWARD_MATRIX is on Levers (resolved award). "
                "p_segment_goal_exact is Python only (the Summary shows a static copy). step_sizes waits for the "
                "Distribution sheet."),
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
    """Write the workbook. Returns a dict: expected values per formula cell, the contract dump, named ranges."""
    bk = Book(run, path, sentinel=sentinel)
    bk.write()
    layout = {"r0l": bk.r0l, "ltot": bk.ltot, "lblock": bk.lblock, "lstat": bk.lstat, "r0v": bk.r0v,
              "vblock": bk.vblock, "vfield_row": bk.vfield_row, "n": bk.n, "case_sheet": dict(CASE_SHEET),
              "ledger_head_rows": {"name": 2, "T": 3, "p": 4, "need_rate": 5, "seg": 6}}
    return {"expected": bk.expected, "dump": bk.dump, "names": bk.names, "vals": bk.vals,
            "build_id": run.meta.get("build_id"), "layout": layout, "run": run}
