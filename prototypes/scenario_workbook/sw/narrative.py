"""Narratives (spec section 8): two templates per scenario, in a Python form and an Excel form built from the same parts.

A template is a list of parts: literal text, or (key, format). `text(parts, values)` renders it from Python values;
`formula(parts, refs)` renders an Excel formula from cell references, using only `&`, `TEXT` and `IF`. Both forms use
the same formats, so the workbook's narrative cells equal the Python text after recalculation (test 18).

Formats: raw (text as is), g (number, general), d1 (one decimal), usd (whole dollars), musd ($ millions, two
decimals), pct0 and pct1 (ratio shown as percent), pp1 (a value already in percent, one decimal), prob (probability;
"under 5%" and "over 95%" while the shock is illustrative), seg_d1 (one decimal, or the segment's text when the segment
has no cells).
"""
import string

from . import labels
from . import ledger as L
from . import risk


def xs(text):
    """Excel string literal."""
    return '"' + str(text).replace('"', '""') + '"'


# ---------------------------------------------------------------------------------------------------------------
# Formats

def _py(v, fmt, ctx):
    if fmt == "raw":
        return "" if v is None else str(v)
    if fmt == "g":
        return f"{v:g}"
    if fmt == "d1":
        return f"{v:,.1f}"
    if fmt == "usd":
        return f"${v:,.0f}"
    if fmt == "musd":
        return f"${v / 1e6:,.2f}M"
    if fmt == "pct0":
        return f"{100 * v:.0f}%"
    if fmt == "pct1":
        return f"{100 * v:.1f}%"
    if fmt == "pp1":
        return f"{v:.1f}"
    if fmt == "prob":
        return labels.fmt_prob(v, ctx["shock_source"])
    if fmt == "seg_d1":
        return v if isinstance(v, str) else f"{v:,.1f}"
    raise ValueError(fmt)


def _xl(r, fmt, ctx):
    if fmt == "raw":
        return f"{r}"
    if fmt == "g":
        return f'{r}&""'
    if fmt == "d1":
        return f'TEXT({r},"#,##0.0")'
    if fmt == "usd":
        return f'"$"&TEXT({r},"#,##0")'
    if fmt == "musd":
        return f'"$"&TEXT({r}/1000000,"#,##0.00")&"M"'
    if fmt == "pct0":
        return f'TEXT({r}*100,"0")&"%"'
    if fmt == "pct1":
        return f'TEXT({r}*100,"0.0")&"%"'
    if fmt == "pp1":
        return f'TEXT({r},"0.0")'
    if fmt == "prob":
        pct = f'TEXT({r}*100,"0")&"%"'
        return (f'IF({ctx["shock_source"]}="illustrative",IF({r}<0.05,{xs(labels.PROB_UNDER)},'
                f'IF({r}>0.95,{xs(labels.PROB_OVER)},{pct})),{pct})')
    if fmt == "seg_d1":
        return f'IF({r}={xs(labels.NO_SEGMENT_CELLS)},{r},TEXT({r},"#,##0.0"))'
    raise ValueError(fmt)


def text(parts, values, ctx):
    out = []
    for p in parts:
        out.append(p if isinstance(p, str) else _py(values[p[0]], p[1], ctx))
    return "".join(out)


def formula(parts, refs, ctx):
    out = []
    for p in parts:
        out.append(xs(p) if isinstance(p, str) else _xl(refs[p[0]], p[1], ctx))
    return "=" + "&".join(out)


# ---------------------------------------------------------------------------------------------------------------
# Templates

def changes_parts(has_parent):
    if not has_parent:
        return ["Pool multiplier ", ("pool_multiplier", "g"), ". Baseline: no parent scenario."]
    return ["Pool multiplier ", ("pool_multiplier", "g"), ". Awards changed in ", ("awards_changed", "g"),
            " cells; admit rates changed in ", ("rates_changed", "g"), " cells."]


def outcome_parts(n_score_thresholds):
    parts = ["Class ", ("class_mean", "d1"), " (90% outcome range ", ("class_lo90", "d1"), " to ",
             ("class_hi90", "d1"), "). "]
    for i in range(n_score_thresholds):
        parts += [("score_measure", "raw"), " median ", (f"t{i}", "g"), ": margin ", (f"margin{i}", "d1"),
                  ", probability ", (f"p{i}", "prob"), ". "]
    parts += ["GPA median ", ("gpa_t", "g"), ": margin ", ("gpa_margin", "d1"), ", probability ", ("gpa_p", "prob"),
              ". ", ("below_floor", "d1"), " enrolled below ", ("floor", "g"), ". Full-tuition ", ("ft", "d1"),
              ", no merit award ", ("nm", "d1"), ". First-year NTR ", ("ntr", "musd"), " (90% outcome range ",
              ("ntr_lo", "musd"), " to ", ("ntr_hi", "musd"), "), discount rate (entering class, first year) ",
              ("discount", "pct1"), ". Tuition ", ("tuition", "usd"), " (+", ("p", "pp1"), "%); class target ",
              ("target", "g"), " (cap ", ("cap", "g"), "); incentive ", ("bonus", "usd"), " (", ("scope", "raw"),
              "); ", ("segment_name", "raw"), " enrolled ", ("segment_enrolled", "seg_d1"), ". Evidence: ",
              ("evidence", "pct0"), " of enrolled in cells where the yield is extrapolated."]
    return parts


# ---------------------------------------------------------------------------------------------------------------
# Labels that apply (section 4), appended to the projected outcome

def label_list(run, s):
    cfg = run.cfg
    lc = run.lcs[s.name]["middle"]
    out = [labels.RESPONSE_LABEL]
    shifts = [s.yield_shift_pts, s.yield_shift_pts_in, s.yield_shift_pts_out, s.yield_shift_pts_segment]
    if any(v not in (None, 0, 0.0) for v in shifts) or s.segment_pool_lift_pct != 0:
        out.append(labels.ASSUMPTION_LABEL)
    if cfg["risk"]["shock_source"] == "illustrative":
        out.append(labels.shock_label(cfg["risk"]["common_shock_sd"]))
    seg = L.active_segment(cfg, s)
    if seg is not None and lc.in_segment.any():
        if L.segment_def(cfg, seg)["share_source"] == "assumed":
            out.append(labels.SEGMENT_SHARE_LABEL)
    out += list(s.notices)
    return out


def labels_text(run, s):
    return " Labels: " + "; ".join(label_list(run, s)) + "."


def template_formula(template, refs):
    """Excel expression for a labels.py template with {name} fields: literal pieces and `refs[name] & ""`."""
    out = []
    for lit, name, _, _ in string.Formatter().parse(template):
        if lit:
            out.append(xs(lit))
        if name:
            out.append(f'{refs[name]}&""')
    return "&".join(out)


def labels_formula_parts(r):
    """Excel expression (no leading '=') for labels_text. r: references (see workbook)."""
    def blank0(x):
        return f'IF({x}="",0,{x})'
    assume = "+".join(f"({blank0(r[k])}<>0)" for k in ("shift", "shift_in", "shift_out", "shift_segment", "lift"))
    shock = f'IF({r["shock_source"]}="illustrative","; "&{template_formula(labels.SHOCK_LABEL, {"s": r["s"]})},"")'
    seg = (f'IF({r["segment_name"]}="","",IF({r["segment_cells"]}=0,"",'
           f'IF({r["share_source"]}="assumed","; "&{xs(labels.SEGMENT_SHARE_LABEL)},"")))')
    notice_text = template_formula(labels.CLASS_TARGET_NOTICE,
                                   {"target": r["target"], "lo": r["sup_lo"], "hi": r["sup_hi"]})
    notice = f'IF(({r["target"]}<{r["sup_lo"]})+({r["target"]}>{r["sup_hi"]})>0,"; "&{notice_text},"")'
    return (f'" Labels: "&{xs(labels.RESPONSE_LABEL)}&IF(({assume})>0,"; "&{xs(labels.ASSUMPTION_LABEL)},"")'
            f'&{shock}&{seg}&{notice}&"."')


# ---------------------------------------------------------------------------------------------------------------
# Python values for one scenario (Middle case)

def values(run, vals, s):
    cfg = run.cfg
    d = vals["sk"][(s.name, "middle")]
    lv = run.lcs[s.name]["middle"]
    p = run.parents[s.name]
    v = {
        "pool_multiplier": s.pool_multiplier,
        "class_mean": d["class_mean"], "class_lo90": d["class_lo90"], "class_hi90": d["class_hi90"],
        "score_measure": cfg["score"]["measure"],
        "gpa_t": cfg["gpa"]["median_threshold"],
        "below_floor": d["kpis"]["enrolled_below_floor"], "floor": cfg["score"]["floor"],
        "ft": d["full_tuition_n"], "nm": d["no_merit_award_n"],
        "ntr": d["ntr_y1"], "ntr_lo": d["ntr_lo90"], "ntr_hi": d["ntr_hi90"],
        "discount": d["discount_entering_y1"], "tuition": lv.tuition, "p": s.tuition_increase_pct,
        "target": s.class_target, "cap": s.class_cap, "bonus": s.bonus_usd, "scope": s.bonus_scope,
        "segment_name": L.active_segment(cfg, s) or "", "segment_enrolled": d["segment_enrolled"],
        "evidence": d["evidence_extrapolated_share"],
    }
    for i, t in enumerate(cfg["score"]["median_thresholds"]):
        md = d["median"][("score", t)]
        v[f"t{i}"], v[f"margin{i}"], v[f"p{i}"] = t, md["margin_t"], md["p_median_t"]
    gm = d["median"][("gpa", cfg["gpa"]["median_threshold"])]
    v["gpa_margin"], v["gpa_p"] = gm["margin_t"], gm["p_median_t"]
    if p is not None:
        v["awards_changed"] = int(((s.award_usd != p.award_usd) | (s.full_tuition != p.full_tuition)).sum())
        v["rates_changed"] = int((s.admit_rate != p.admit_rate).sum())
    return v


def changes(run, vals, s):
    ctx = {"shock_source": run.cfg["risk"]["shock_source"]}
    return text(changes_parts(run.parents[s.name] is not None), values(run, vals, s), ctx)


def outcome(run, vals, s):
    ctx = {"shock_source": run.cfg["risk"]["shock_source"]}
    parts = outcome_parts(len(run.cfg["score"]["median_thresholds"]))
    return text(parts, values(run, vals, s), ctx) + labels_text(run, s)


__all__ = ["changes", "outcome", "values", "changes_parts", "outcome_parts", "label_list", "labels_text",
           "labels_formula_parts", "formula", "text", "xs", "risk"]
