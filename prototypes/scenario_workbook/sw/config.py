"""Client config loading and validation (spec section 2).

Every client value comes from config/<client>.yaml (spec rule 7). A required value that is missing or null is an
error. The defaults below are product rules stated in the spec, not client values.
"""
import copy
import math

import yaml

from . import CASES
from . import labels


class ConfigError(ValueError):
    pass


REQUIRED = [
    "client.id", "client.name", "client.vertical", "client.small_cell_policy",
    "cycle.base_cycle", "cycle.plan_cycle", "cycle.history",
    "tuition_by_cohort", "tuition_base", "tuition_increase_by_year", "tuition_rounding_usd",
    "score.measure", "score.bands", "score.pool_threshold", "score.floor", "score.median_thresholds",
    "gpa.measure", "gpa.hi_at_or_above", "gpa.classes", "gpa.median_threshold",
    "class.cap", "class.target", "class.band", "class.what_if",
    "need.total", "need.reference_class",
    "risk.common_shock_sd", "risk.shock_source", "risk.shock_corr_above_below", "risk.sensitivity_slopes",
    "risk.yield_floor", "risk.yield_cap", "risk.yield_shift_grid", "risk.pool_grid", "risk.tuition_grid",
    "pooling_k", "integer_admits", "integer_enrolled", "evidence_tolerance_usd", "segments",
]

# Product defaults stated in the spec (not client values).
DEFAULTS = {
    "unscored_in_median": "excluded",            # [v0.6, B3-3]
    "pooling_min_admits": 30,                     # section 4: pool with at least 30 admits
    "trim": {"protect_segment": "below_threshold", "floor_rate": 0.0, "exempt_cells": []},
    "marginal_admit_yield_slope": 0.0,
    "ntr_target": None,
    "discount_target": None,
    "budget_total": None,
    "budget_basis": "total_aid",                  # [v0.6.2, Q-8e] total aid (merit + need + specialty) or merit
    "merit_actual_by_cohort": None,               # [v0.6.2, Q-8f] optional; feeds the history reconciliation
    "pool_ytd_growth": None,
}

SHOCK_SOURCES = ("illustrative", "public", "client")
SCORE_GROUPS = ("upper", "lower")


def _get(d, dotted):
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None, False
        cur = cur[part]
    return cur, True


def round_to(x, unit):
    """Round half up to a multiple of unit (matches Excel ROUND for positive values)."""
    return unit * math.floor(x / unit + 0.5)


def load(path):
    with open(path) as f:
        raw = yaml.safe_load(f)
    return validate(raw)


def validate(raw):
    """Return a validated copy of a config dict with product defaults filled in."""
    cfg = copy.deepcopy(raw)
    missing = [k for k in REQUIRED if _get(cfg, k)[0] is None and k != "segments"]
    if _get(cfg, "segments")[1] is False:
        missing.append("segments")
    if missing:
        raise ConfigError("missing required config values: " + ", ".join(missing))

    for k, v in DEFAULTS.items():
        if k not in cfg:
            cfg[k] = copy.deepcopy(v)
    for k, v in DEFAULTS["trim"].items():
        cfg["trim"].setdefault(k, copy.deepcopy(v))
    notes = []

    # cycle
    cyc = cfg["cycle"]
    if cyc["base_cycle"] not in cyc["history"]:
        raise ConfigError("cycle.base_cycle must be one of cycle.history")
    if cyc["base_cycle"] != max(cyc["history"]):
        raise ConfigError("cycle.base_cycle must be the latest history cohort")
    if cyc["plan_cycle"] <= cyc["base_cycle"]:
        raise ConfigError("cycle.plan_cycle must follow cycle.base_cycle")

    # tuition
    tbc = {int(k): float(v) for k, v in cfg["tuition_by_cohort"].items()}
    cfg["tuition_by_cohort"] = tbc
    for y in cyc["history"]:
        if y not in tbc:
            raise ConfigError(f"tuition_by_cohort has no value for history cohort {y}")
    if abs(tbc[cyc["base_cycle"]] - float(cfg["tuition_base"])) > 0.5:
        raise ConfigError("tuition_base must equal tuition_by_cohort at base_cycle")
    cfg["tuition_increase_by_year"] = {int(k): float(v) for k, v in cfg["tuition_increase_by_year"].items()}
    if cyc["plan_cycle"] not in cfg["tuition_increase_by_year"]:
        raise ConfigError("tuition_increase_by_year has no value for plan_cycle")

    # score and GPA
    sc = cfg["score"]
    bands = list(sc["bands"])
    if bands != sorted(bands, reverse=True):
        raise ConfigError("score.bands must be ordered lower bounds, descending")
    for key in ("pool_threshold", "floor"):
        if sc[key] not in bands:
            raise ConfigError(f"score.{key} must be one of score.bands")
    for t in sc["median_thresholds"]:
        if t not in bands:
            raise ConfigError("each score.median_thresholds value must be one of score.bands")
    g = cfg["gpa"]
    if list(g["classes"]) != ["hi", "lo", "blank"]:
        raise ConfigError("gpa.classes must be [hi, lo, blank]")
    if abs(float(g["median_threshold"]) - float(g["hi_at_or_above"])) > 1e-9:
        raise ConfigError("gpa.median_threshold must equal gpa.hi_at_or_above (one GPA boundary in the cell schema)")
    if cfg["unscored_in_median"] not in ("excluded", "below"):
        raise ConfigError("unscored_in_median must be 'excluded' or 'below'")

    # class
    cl = cfg["class"]
    cap = float(cl["cap"])
    cl.setdefault("supported_range", [0.7 * cap, cap])
    cl.setdefault("reject_range", [0.6 * cap, 1.1 * cap])
    check_class_target(cfg, cl["target"], cap)

    # risk
    rk = cfg["risk"]
    if rk["shock_source"] not in SHOCK_SOURCES:
        raise ConfigError(f"risk.shock_source must be one of {SHOCK_SOURCES}")
    if set(rk["sensitivity_slopes"]) != set(CASES):
        raise ConfigError("risk.sensitivity_slopes must give low, middle and high")
    for key in ("yield_floor", "yield_cap"):
        if set(rk[key]) != set(SCORE_GROUPS):
            raise ConfigError(f"risk.{key} must give upper and lower score groups")
    if not 0.0 <= float(rk["shock_corr_above_below"]) <= 1.0:
        raise ConfigError("risk.shock_corr_above_below must lie in [0, 1]")

    # segments [v0.6, B5-1, D13]
    for s in cfg["segments"] or []:
        for key in ("name", "within", "members_label", "share_source"):
            if key not in s or s[key] is None:
                raise ConfigError(f"segment is missing {key}")
        if s["within"].get("residency") not in ("in", "out"):
            raise ConfigError("segment.within.residency must be 'in' or 'out'")
        if s["share_source"] not in ("client_counts", "assumed"):
            raise ConfigError("segment.share_source must be 'client_counts' or 'assumed'")
    cfg["segments"] = cfg["segments"] or []

    # budget basis and reported merit [v0.6.2, Q-8e, Q-8f]
    if cfg["budget_basis"] not in ("total_aid", "merit"):
        raise ConfigError("budget_basis must be 'total_aid' or 'merit'")
    if cfg["merit_actual_by_cohort"] is not None:
        mab = {int(k): float(v) for k, v in cfg["merit_actual_by_cohort"].items() if v is not None}
        for y in mab:
            if y not in cyc["history"]:
                raise ConfigError(f"merit_actual_by_cohort: {y} is not a history cohort")
            if mab[y] <= 0:
                raise ConfigError("merit_actual_by_cohort values must be positive")
        cfg["merit_actual_by_cohort"] = mab

    # trim
    if cfg["trim"]["protect_segment"] not in ("below_threshold", "none"):
        raise ConfigError("trim.protect_segment must be 'below_threshold' or 'none'")

    if float(cfg["marginal_admit_yield_slope"]) != 0.0:
        notes.append(labels.MARGINAL_ADMIT_NOTE.format(x=cfg["marginal_admit_yield_slope"]))
    cfg["_notes"] = notes
    return cfg


def check_class_target(cfg, target, cap):
    """Validate a class target under a hard cap (spec section 2). Returns a notice string or None; raises on reject."""
    cl = cfg["class"]
    target = float(target)
    cap = float(cap)
    if target > cap:
        raise ConfigError(f"class target {target:g} exceeds the cap {cap:g}")
    rlo, rhi = cl.get("reject_range", [0.6 * cap, 1.1 * cap])
    if not rlo <= target <= rhi:
        raise ConfigError(f"class target {target:g} is outside the reject range ({rlo:g} to {rhi:g})")
    slo, shi = cl.get("supported_range", [0.7 * cap, cap])
    if not slo <= target <= shi:
        return labels.CLASS_TARGET_NOTICE.format(target=f"{target:g}", lo=f"{slo:g}", hi=f"{shi:g}")
    return None


def plan_increase_pct(cfg, plan_year):
    """Cumulative tuition increase (percent) from base_cycle to plan_year from tuition_increase_by_year."""
    base = cfg["cycle"]["base_cycle"]
    f = 1.0
    for y in range(base + 1, plan_year + 1):
        if y not in cfg["tuition_increase_by_year"]:
            raise ConfigError(f"tuition_increase_by_year has no value for {y}")
        f *= 1.0 + cfg["tuition_increase_by_year"][y] / 100.0
    return 100.0 * (f - 1.0)


def scenario_tuition(cfg, increase_pct):
    """tuition_s = round_to(tuition_base x (1 + p_s), tuition_rounding_usd)."""
    return float(round_to(float(cfg["tuition_base"]) * (1.0 + increase_pct / 100.0), cfg["tuition_rounding_usd"]))


def segment_def(cfg, name):
    for s in cfg["segments"]:
        if s["name"] == name:
            return s
    raise ConfigError(f"segment {name!r} is not configured")
