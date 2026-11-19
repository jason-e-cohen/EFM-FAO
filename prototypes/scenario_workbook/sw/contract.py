"""Interface contract (spec section 15 item 11): the Python dump keyed by the same names as the Summary named ranges.

Named ranges: each name is the Source prefix plus the contract name in upper case (`class_lo90` -> `SUM_CLASS_LO90`).
Scenario, case and grid value are the range's rows and columns, never part of the name. Layouts, shared by the
workbook and the tests:

  grain s x k      rows: cases (low, middle, high); columns: scenarios (Baseline first)
  grain s x k x t  rows: for each threshold t (median targets, or score thresholds for shares), the three cases
  grain s x k x target  rows: for each percentile target (q, t) in config order, the three cases [v0.6.3, BM-1]
  PCT_BAND_Q       rows: q = 0.25, 0.75; columns: scenarios; the spread band's lower bound (Middle case)
  POOL_BREAKEVEN_M rows: scenarios; columns: m_class, then m_q for each percentile target [v0.6.3, BM-6]
  strips (s x p, s x d, s x m, s x N)  rows: for each scenario, the grid values; columns: the fields in STRIP_COLUMNS
  per-scenario lines and break-evens   rows: scenarios; one column
  AWARD_MATRIX     rows: cells (workbook order); columns: scenarios; the resolved award (plan-year dollars)

Names are canonical: one range per figure, no aliases [v0.6.2, Q-1]; a short form in the spec's Source column (for
example SUM_PCAP) is read as the prefix only. `p_segment_goal` in the workbook is the normal form (spec section 3);
`p_segment_goal_exact` is Python only (`risk.segment_exact`) and the workbook shows a static copy with a stale flag
[v0.6.2, Q-2, P2-06]. Values: numbers, text, or None (an empty cell in Excel).
"""
import math

import numpy as np

from . import CASES
from . import labels
from . import ledger as L
from . import response
from . import risk
from . import strip
from . import trim

SK = [  # (name, prefix, python source)
    ("class_mean", "SUM", "risk.class_dist"), ("class_lo90", "SUM", "risk.class_dist"),
    ("class_hi90", "SUM", "risk.class_dist"),
    ("p_class_over_cap", "SUM", "risk.class_probs"), ("p_class_in_band", "SUM", "risk.class_probs"),
    ("unscored_count", "SUM", "ledger.kpis"),
    ("gross_y1", "SUM", "ledger.money"), ("merit", "SUM", "ledger.money"), ("need", "SUM", "ledger.money"),
    ("specialty", "SUM", "ledger.money"), ("aid", "SUM", "ledger.money"), ("ntr_y1", "SUM", "ledger.money"),
    ("discount_entering_y1", "SUM", "ledger.money"), ("avg_aid", "SUM", "ledger.money"),
    ("p_ntr_y1_ge_target", "SUM", "risk.ntr"), ("p_jd_ntr_ge_goal", "SUM", "risk.ntr (all_jd)"),
    ("full_tuition_n", "SUM", "ledger.kpis"), ("no_merit_award_n", "SUM", "ledger.kpis"),
    ("barbell", "SUM", "ledger.kpis"),
    ("evidence_extrapolated_share", "SUM", "response.evidence"),
    ("segment_enrolled", "SEG", "ledger.segment"), ("segment_lo90", "SEG", "ledger.segment"),
    ("segment_hi90", "SEG", "ledger.segment"), ("p_segment_goal", "SEG", "ledger.segment (normal form)"),
    ("segment_share", "SEG", "ledger.segment"),
    ("incentive_cost", "INC", "ledger.incentive"), ("incentive_paid_anyway", "INC", "ledger.incentive"),
    ("incentive_paid_anyway_share", "INC", "ledger.incentive"), ("additional_enrollees", "INC", "ledger.incentive"),
    ("aid_per_additional", "INC", "ledger.incentive"), ("ntr_per_additional", "INC", "ledger.incentive"),
    ("incentive_valid", "INC", "ledger.incentive"),
]
SKT = [("margin_t", "SUM", "risk.median"), ("p_median_t", "SUM", "risk.median"),
       ("p_median_t_rho05", "SUM", "risk.median")]
SKT_SHARE = [("share_at_or_above_t", "SUM", "ledger.kpis")]
SKQ = [("margin_q_t", "SUM", "risk.pct"), ("p_pct_q_t", "SUM", "risk.pct"),           # [v0.6.3, BM-1]
       ("p_pct_q_t_rho05", "SUM", "risk.pct")]
PER_SCENARIO_Q = [("pct_band_q", "SUM", "risk.pct_band")]                              # rows q, columns s
POOL_BE = [("pool_breakeven_m", "PS", "strip.pool_strip")]                            # rows s, columns m_class, m_q
PER_SCENARIO = [("net_tuition_line_fixed", "TW", "strip.tuition"), ("net_tuition_line_scaled", "TW", "strip.tuition"),
                ("breakeven_shift_class", "YS", "strip.yield_strip"),
                ("breakeven_shift_ntr", "YS", "strip.yield_strip")]
STRIPS = [("tuition_whatif", "TW", "strip.tuition"), ("yield_strip", "YS", "strip.yield_strip"),
          ("pool_strip", "PS", "strip.pool_strip"), ("class_table", "CT", "trim.class_table")]
# Contract figures with no workbook range (spec section 15 item 11): name -> python source. The dump carries them under
# the contract name.
PYTHON_ONLY = {"p_segment_goal_exact": "risk.segment_exact"}

PARENT_ONLY = {"incentive_paid_anyway", "incentive_paid_anyway_share", "additional_enrollees", "aid_per_additional",
               "ntr_per_additional", "incentive_valid"}


def range_name(name, prefix):
    return f"{prefix}_{name.upper()}"


def band_keys(cfg):
    """Columns of 'admits cut by band' in the class-size table: each score band, then unscored."""
    return [float(b) for b in cfg["score"]["bands"]] + ["unscored"]


def strip_columns(cfg):
    targets = risk.median_targets(cfg)
    med = []
    for meas, t in targets:
        med += [f"margin_{meas}_{t:g}", f"p_median_{meas}_{t:g}"]
    pq = [(q, t) for q, t in risk.pct_targets(cfg)]
    pct_cols = []
    for q, t in pq:
        pct_cols += [f"margin_q{q:g}_{t:g}", f"p_pct_q{q:g}_{t:g}"]
    return {
        "tuition_whatif": ["tuition", "ntr_y1", "net_tuition_per_student", "discount_entering_y1"],
        "yield_strip": ["class_mean", "p_class_over_cap", "p_class_in_band", "ntr_mean", "p_ntr_y1_ge_target"] + med,
        "pool_strip": (["growth", "class_mean", "p_class_over_cap", "margin", "p_median", "ntr_mean", "ntr_sd"]
                       + [f"p_pct_q{q:g}_{t:g}" for q, t in pq] + ["marker"]),          # [v0.6.3, BM-6]
        "class_table": (["f", "class_mean", "p_class_over_cap"] + med + pct_cols          # [v0.6.3, BM-3, BM-1]
                        + ["ntr_y1", "discount_entering_y1", "segment_enrolled", "lowest_band_admitted"]
                        + [f"cut_{'unscored' if b == 'unscored' else format(b, 'g')}" for b in band_keys(cfg)]
                        + ["status"]),
    }


def strip_grid(cfg, scen, which):
    rk = cfg["risk"]
    return {"tuition_whatif": rk["tuition_grid"], "yield_strip": rk["yield_shift_grid"],
            "pool_strip": rk["pool_grid"], "class_table": cfg["class"]["what_if"]}[which]


def _num(x):
    if x is None or isinstance(x, str):
        return x
    if isinstance(x, (bool, np.bool_)):
        return int(x)
    x = float(x)
    return None if math.isnan(x) else x


def compute(run):
    """Every figure the workbook shows, from the Python reference functions. Returns a nested dict."""
    cfg, cells, base = run.cfg, run.cells, run.base
    targets = risk.median_targets(cfg)
    ptargets = risk.pct_targets(cfg)
    out = {"sk": {}, "strips": {}, "lines": {}, "parts": {}, "ct_rates": {}, "seg_exact": {}, "conflicts": {},
           "targets": targets, "ptargets": ptargets, "score_ts": L.score_thresholds(cfg), "pct_band": {},
           "pool_be": {},
           "history_reconciliation": L.history_reconciliation(cells, cfg),
           "aba509_reconciliation": L.aba509_reconciliation(cells, cfg)}
    for s in run.scenarios:
        p = run.parents[s.name]
        for k in CASES:
            lc = run.lcs[s.name][k]
            cd, cp, kp, mo = risk.class_dist(lc), risk.class_probs(lc), L.kpis(lc), L.money(lc)
            nt = risk.ntr(lc)
            sg = L.segment(lc)
            ev = response.evidence(lc, base, cfg)
            d = {
                "class_mean": cd["class_mean"], "class_lo90": cd["class_lo90"], "class_hi90": cd["class_hi90"],
                "p_class_over_cap": cp["p_class_over_cap"], "p_class_in_band": cp["p_class_in_band"],
                "unscored_count": kp["unscored_count"],
                "p_ntr_y1_ge_target": nt.get("p_ntr_y1_ge_target"),
                "ntr_lo90": nt["ntr_lo90"], "ntr_hi90": nt["ntr_hi90"], "ntr_mean": nt["ntr_mean"],
                "full_tuition_n": kp["full_tuition_n"], "no_merit_award_n": kp["no_merit_award_n"],
                "barbell": kp["barbell"], "evidence_extrapolated_share": ev["evidence_extrapolated_share"],
                "evidence_labels": ev["evidence_labels"],
                "segment_enrolled": sg["segment_enrolled"], "segment_lo90": sg["segment_lo90"],
                "segment_hi90": sg["segment_hi90"], "p_segment_goal": sg["p_segment_goal_normal"],
                "p_segment_goal_exact": sg["p_segment_goal"], "segment_share": sg["segment_share"],
                "segment_apps": sg["segment_apps"], "segment_admits": sg["segment_admits"],
                "segment_merit": sg["segment_merit"], "segment_goal": sg["segment_goal"],
                "segment_approximate": sg["approximate"],
                "kpis": kp, "money": mo,
                "median": {(m, t): risk.median(lc, m, t) for m, t in targets},
                "pct": {(q, t): risk.pct(lc, q, t) for q, t in ptargets},
                "incentive_cost": mo["incentive_cost"],
                # [v0.6.3, BM-4] P(continuing + ntr_y1 >= ntr_target) under all_jd: the same event as ntr_y1 >= the
                # effective target; None under entering_y1
                "p_jd_ntr_ge_goal": (nt.get("p_ntr_y1_ge_target") if cfg.get("ntr_goal_basis") == "all_jd"
                                     else None),
                "jd_ntr": (cfg["continuing_ntr_usd"] + mo["ntr_y1"] if cfg.get("ntr_goal_basis") == "all_jd"
                           else None),
            }
            for key in ("gross_y1", "merit", "need", "specialty", "aid", "ntr_y1", "discount_entering_y1", "avg_aid"):
                d[key] = mo[key]
            if p is not None:
                inc = L.incentive(lc, run.lcs[p.name][k])
                d.update({kk: inc[kk] for kk in PARENT_ONLY})
                d["incentive_cost"] = inc["incentive_cost"]
                d["merit_change"] = inc["merit_change"]
                d["ntr_change"] = inc["ntr_change"]
                d["aid_per_additional_kind"] = inc["aid_per_additional_kind"]
            else:
                for kk in PARENT_ONLY | {"merit_change", "ntr_change", "aid_per_additional_kind"}:
                    d[kk] = None
            out["sk"][(s.name, k)] = d
        out["seg_exact"][s.name] = out["sk"][(s.name, "middle")]["p_segment_goal_exact"]
        lcm = run.lcs[s.name]["middle"]
        out["pct_band"][s.name] = {q: risk.pct_band(lcm, q) for q in risk.SPREAD_QS}
        tw = strip.tuition(lcm)
        ys = strip.yield_strip(lcm)
        ps = strip.pool_strip(cells, cfg, s, base)
        ct = trim.class_table(cells, cfg, s, base)
        out["strips"][s.name] = {"tuition_whatif": tw, "yield_strip": ys, "pool_strip": ps, "class_table": ct}
        out["lines"][s.name] = {"net_tuition_line_fixed": tw["net_tuition_line_fixed"],
                                "net_tuition_line_scaled": tw["net_tuition_line_scaled"],
                                "breakeven_shift_class": ys["breakeven_shift_class"],
                                "breakeven_shift_ntr": ys["breakeven_shift_ntr"]}
        out["parts"][s.name] = ps["parts"]
        out["pool_be"][s.name] = [ps["pool_breakeven_m"]["class"]] + [ps["pool_breakeven_m"][k] for k in ptargets]
        out["conflicts"][s.name] = L.full_tuition_conflicts(cells, cfg, s, p)
        out.setdefault("award_changes", {})[s.name] = L.award_changes(cells, cfg, s, p)
        out["price_of_target"] = out.get("price_of_target", {})
        out["price_of_target"][s.name] = L.price_of_target(run.lcs[run.scenarios[0].name]["middle"], lcm)
    return out


def strip_rows(run, vals, which):
    """Rows (s, grid value) and values in STRIP_COLUMNS order for one strip."""
    cfg = run.cfg
    cols = strip_columns(cfg)[which]
    targets = vals["targets"]
    rows = []
    for s in run.scenarios:
        st = vals["strips"][s.name][which]
        if which == "tuition_whatif":
            for r in st["tuition_whatif"]:
                rows.append((s.name, r["tuition_increase_pct"],
                             [r["tuition"], r["ntr_y1"], r["net_tuition_per_student"], r["discount_entering_y1"]]))
        elif which == "yield_strip":
            for r in st["yield_strip"]:
                v = [r["class_mean"], r["p_class_over_cap"], r["p_class_in_band"], r["ntr_mean"],
                     r["p_ntr_y1_ge_target"]]
                for key in targets:
                    v += [r["median"][key]["margin"], r["median"][key]["p"]]
                rows.append((s.name, r["shift_pts"], v))
        elif which == "pool_strip":
            for r in st["pool_strip"]:
                rows.append((s.name, r["pool_multiplier"],
                             [r["growth"], r["class_mean"], r["p_class_over_cap"], r["margin"], r["p_median"],
                              r["ntr_mean"], r["ntr_sd"]] + [r["pct"][k]["p"] for k in vals["ptargets"]]
                             + [r["marker"]]))
        else:
            for r in st["class_table"]:
                if "class_mean" not in r:
                    v = [r["f"]] + [None] * (len(cols) - 2) + [r["status"]]
                else:
                    v = [r["f"], r["class_mean"], r["p_class_over_cap"]]
                    for key in targets:
                        v += [r["median"][key]["margin"], r["median"][key]["p"]]
                    for key in vals["ptargets"]:
                        v += [r["pct"][key]["margin"], r["pct"][key]["p"]]
                    v += [r["ntr_y1"], r["discount_entering_y1"], r["segment_enrolled"], r["lowest_band_admitted"]]
                    cut = r["admits_cut_by_band"]
                    v += [cut.get(b, 0.0) for b in band_keys(cfg)]
                    v += [r["status"]]
                rows.append((s.name, r["N"], v))
        assert all(len(r[2]) == len(cols) for r in rows)
    return rows


def dump(run, vals=None):
    """The Python dump: range name -> 2-D list in the workbook layout (see module docstring)."""
    vals = vals or compute(run)
    names = [s.name for s in run.scenarios]
    out = {}
    for name, prefix, _ in SK:
        out[range_name(name, prefix)] = [[_num(vals["sk"][(s, k)][name]) for s in names] for k in CASES]
    for name, prefix, _ in SKT:
        key = {"margin_t": "margin_t", "p_median_t": "p_median_t", "p_median_t_rho05": "p_median_t_rho05"}[name]
        out[range_name(name, prefix)] = [[_num(vals["sk"][(s, k)]["median"][tg][key]) for s in names]
                                         for tg in vals["targets"] for k in CASES]
    out["SUM_SHARE_AT_OR_ABOVE_T"] = [[_num(vals["sk"][(s, k)]["kpis"]["share_at_or_above_t"][t]) for s in names]
                                      for t in vals["score_ts"] for k in CASES]
    for name, prefix, _ in SKQ:
        out[range_name(name, prefix)] = [[_num(vals["sk"][(s, k)]["pct"][tg][name]) for s in names]
                                         for tg in vals["ptargets"] for k in CASES]
    out["SUM_PCT_BAND_Q"] = [[_num(vals["pct_band"][s][q]) for s in names] for q in risk.SPREAD_QS]
    out["PS_POOL_BREAKEVEN_M"] = [[_num(x) for x in vals["pool_be"][s]] for s in names]
    for name, prefix, _ in PER_SCENARIO:
        out[range_name(name, prefix)] = [[_num(vals["lines"][s][name])] for s in names]
    for which, prefix, _ in STRIPS:
        out[range_name(which, prefix)] = [[_num(x) for x in r[2]] for r in strip_rows(run, vals, which)]
    out["AWARD_MATRIX"] = [[_num(run.lcs[s]["middle"].award[i]) for s in names] for i in range(run.cells.n)]
    out["p_segment_goal_exact"] = [[_num(vals["sk"][(s, k)]["p_segment_goal_exact"]) for s in names] for k in CASES]
    return out


def contract_table():
    """(range name, contract name, grain, python source) for the README and test 9."""
    rows = [(range_name(n, p), n, "s x k", src) for n, p, src in SK]
    rows += [(range_name(n, p), n, "s x k x t", src) for n, p, src in SKT + SKT_SHARE]
    rows += [(range_name(n, p), n, "s x k x target", src) for n, p, src in SKQ]
    rows += [(range_name(n, p), n, "s x q", src) for n, p, src in PER_SCENARIO_Q]
    rows += [(range_name(n, p), n, "s x (class, target)", src) for n, p, src in POOL_BE]
    rows += [(range_name(n, p), n, "s", src) for n, p, src in PER_SCENARIO]
    rows += [(range_name(n, p), f"{n}[grid]", "s x grid", src) for n, p, src in STRIPS]
    rows += [("AWARD_MATRIX", "award_matrix", "s x cell", "ledger.awards")]
    return rows


def python_only_table():
    """(contract name, grain, python source) for figures the workbook does not carry as a range."""
    return [(n, "s x k", src) for n, src in PYTHON_ONLY.items()]


def label_for(name):
    if name in ("p_class_over_cap", "p_class_in_band", "class_mean", "class_lo90", "class_hi90", "margin_t",
                "p_median_t", "p_median_t_rho05", "p_ntr_y1_ge_target", "margin_q_t", "p_pct_q_t",
                "p_pct_q_t_rho05", "p_jd_ntr_ge_goal"):
        return "SHOCK_LABEL"
    if name.startswith("segment") or name == "p_segment_goal":
        return "RESPONSE_LABEL, SEGMENT_SHARE_LABEL"
    if name.startswith("incentive") or name in PARENT_ONLY:
        return "RESPONSE_LABEL"
    return ""


__all__ = ["compute", "dump", "contract_table", "python_only_table", "strip_columns", "strip_rows", "band_keys",
           "range_name", "PYTHON_ONLY", "labels"]
