"""Client config loading and validation (spec section 2).

Every client value comes from config/<client>.yaml (spec rule 7). A required value that is missing or null is an
error. The defaults below are product rules stated in the spec, not client values.
"""
import copy

import numpy as np
import yaml

from . import CASES
from . import labels


class ConfigError(ValueError):
    pass


REQUIRED = [
    "client.id", "client.name", "client.vertical", "client.small_cell_policy",
    "cycle.base_cycle", "cycle.plan_cycle", "cycle.history",
    "tuition_by_cohort", "tuition_base", "tuition_rounding_usd",
    "score.measure", "score.bands", "score.pool_threshold", "score.floor",
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
    "pool_ytd_as_of": None,                       # [v0.6.3, BM-6] date of pool_ytd_growth (display only)
    "tuition_increase_by_year": {},               # [v0.6.3, BM-2] optional when tuition_by_year_usd covers the years
    "tuition_by_year_usd": {},                    # [v0.6.3, BM-2] takes precedence over tuition_increase_by_year
    "ntr_goal_basis": "entering_y1",              # [v0.6.3, BM-4] entering_y1 or all_jd
    "continuing_ntr_usd": None,                   # [v0.6.3, BM-4] required under all_jd
    "mode": "live",                               # live or reproduce (spec section 9); reproduce builds come from
                                                  # sw/reproduce.py, which sets it
    "reproduce": None,                            # reproduce-mode settings (spec section 9; DECISIONS Nov 18)
    "aba_509_by_cohort": None,                    # optional public ABA 509 figures per history cohort (R3-4)
}

REPRODUCE_KEYS = {"tuition_increase_pct", "unscored_in_median", "round_apps_after_pool"}
ABA_509_KEYS = ("first_year_class", "without_score", "without_gpa", "score_p25", "score_p50", "score_p75",
                "gpa_p25", "gpa_p50", "gpa_p75")

SHOCK_SOURCES = ("illustrative", "public", "client")
PROTECT_SEGMENT = ("below_threshold", "above_floor", "none")     # [v0.6.3, BM-5]
NTR_GOAL_BASES = ("entering_y1", "all_jd")                       # [v0.6.3, BM-4]
SCORE_GROUPS = ("upper", "lower")


def _get(d, dotted):
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None, False
        cur = cur[part]
    return cur, True


def excel_round0(x):
    """Round to a whole number as Excel's and LibreOffice's ROUND(x, 0) do: x taken at 15 significant digits, then half
    away from zero. A value one binary step below a half rounds up (LibreOffice ROUND(2.4999999999999996, 0) = 3, where
    floor(x + 0.5) gives 2); found while exercising the integer-admit branches (Phase 3)."""
    a = np.asarray(x, float)
    x15 = np.vectorize(lambda v: float(f"{v:.15g}") if np.isfinite(v) else v, otypes=[float])(a)
    return np.sign(x15) * np.floor(np.abs(x15) + 0.5)


def round_apps_after_pool(cfg):
    """True when the ledger rounds applications to whole numbers after the pool multiplier: reproduce mode with
    reproduce.round_apps_after_pool set (DECISIONS Nov 18; the fixture's arithmetic). Live mode never rounds them
    (spec section 3)."""
    return cfg.get("mode") == "reproduce" and bool((cfg.get("reproduce") or {}).get("round_apps_after_pool", False))


def round_to(x, unit):
    """Round half up to a multiple of unit, as Excel ROUND(x / unit, 0) x unit does."""
    return unit * float(excel_round0(x / unit))


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
    cfg["tuition_increase_by_year"] = {int(k): float(v) for k, v in (cfg["tuition_increase_by_year"] or {}).items()
                                       if v is not None}
    # [v0.6.3, BM-2] tuition in dollars by plan year; precedence over the increase for the same year
    tby = {int(k): float(v) for k, v in (cfg["tuition_by_year_usd"] or {}).items() if v is not None}
    unit = float(cfg["tuition_rounding_usd"])
    for y, v in tby.items():
        if y <= cyc["base_cycle"]:
            raise ConfigError(f"tuition_by_year_usd: {y} is not a plan year (after base_cycle)")
        if v <= 0:
            raise ConfigError("tuition_by_year_usd values must be positive")
        if abs(v / unit - round(v / unit)) > 1e-9:
            raise ConfigError(f"tuition_by_year_usd {y}: {v:g} is not a multiple of tuition_rounding_usd ({unit:g}), "
                              "so the implied increase cannot reproduce it")
    cfg["tuition_by_year_usd"] = tby
    if cyc["plan_cycle"] not in cfg["tuition_increase_by_year"] and cyc["plan_cycle"] not in tby:
        raise ConfigError("tuition_increase_by_year (or tuition_by_year_usd) has no value for plan_cycle")

    # score and GPA
    sc = cfg["score"]
    bands = list(sc["bands"])
    if bands != sorted(bands, reverse=True):
        raise ConfigError("score.bands must be ordered lower bounds, descending")
    for key in ("pool_threshold", "floor"):
        if sc[key] not in bands:
            raise ConfigError(f"score.{key} must be one of score.bands")
    _percentile_targets(sc, bands)
    g = cfg["gpa"]
    if list(g["classes"]) != ["hi", "lo", "blank"]:
        raise ConfigError("gpa.classes must be [hi, lo, blank]")
    if abs(float(g["median_threshold"]) - float(g["hi_at_or_above"])) > 1e-9:
        raise ConfigError("gpa.median_threshold must equal gpa.hi_at_or_above (one GPA boundary in the cell schema)")
    if cfg["unscored_in_median"] not in ("excluded", "below"):
        raise ConfigError("unscored_in_median must be 'excluded' or 'below'")
    if cfg["mode"] not in ("live", "reproduce"):
        raise ConfigError("mode must be 'live' or 'reproduce'")
    rp = cfg["reproduce"]
    if rp is not None:
        if not isinstance(rp, dict) or set(rp) - REPRODUCE_KEYS:
            raise ConfigError(f"reproduce: allowed keys are {sorted(REPRODUCE_KEYS)}")
        if rp.get("unscored_in_median") not in (None, "excluded", "below"):
            raise ConfigError("reproduce.unscored_in_median must be 'excluded' or 'below'")
        if not isinstance(rp.get("round_apps_after_pool", False), bool):
            raise ConfigError("reproduce.round_apps_after_pool must be true or false")
    a5 = cfg["aba_509_by_cohort"]
    if a5 is not None:
        out = {}
        for y, row in a5.items():
            if int(y) not in cyc["history"]:
                raise ConfigError(f"aba_509_by_cohort: {y} is not a history cohort")
            if not isinstance(row, dict) or set(row) - set(ABA_509_KEYS):
                raise ConfigError(f"aba_509_by_cohort {y}: allowed keys are {list(ABA_509_KEYS)}")
            out[int(y)] = {k: (None if v is None else float(v)) for k, v in row.items()}
        cfg["aba_509_by_cohort"] = out

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
    if cfg["trim"]["protect_segment"] not in PROTECT_SEGMENT:
        raise ConfigError(f"trim.protect_segment must be one of {PROTECT_SEGMENT}")

    # NTR goal basis [v0.6.3, BM-4]
    if cfg["ntr_goal_basis"] not in NTR_GOAL_BASES:
        raise ConfigError(f"ntr_goal_basis must be one of {NTR_GOAL_BASES}")
    if cfg["continuing_ntr_usd"] is not None:
        cfg["continuing_ntr_usd"] = float(cfg["continuing_ntr_usd"])
    if cfg["ntr_goal_basis"] == "all_jd" and cfg["continuing_ntr_usd"] is None:
        raise ConfigError("ntr_goal_basis all_jd needs continuing_ntr_usd (continuing-student net tuition, "
                          "client-supplied)")

    # pool growth to date [v0.6.3, BM-6]: the as-of date is text on Inputs (ISO date when YAML gives a date)
    if cfg["pool_ytd_as_of"] is not None:
        a = cfg["pool_ytd_as_of"]
        cfg["pool_ytd_as_of"] = a.isoformat() if hasattr(a, "isoformat") else str(a)
    pg = [float(x) for x in cfg["risk"]["pool_grid"]]
    if pg != sorted(pg) or len(set(pg)) != len(pg):
        raise ConfigError("risk.pool_grid must be strictly ascending (the growth-to-date marker reads it in order)")

    if float(cfg["marginal_admit_yield_slope"]) != 0.0:
        notes.append(labels.MARGINAL_ADMIT_NOTE.format(x=cfg["marginal_admit_yield_slope"]))
    cfg["_notes"] = notes
    return cfg


def _percentile_targets(sc, bands):
    """[v0.6.3, BM-1] score.percentile_targets: list of {q, t}; q in (0, 1) with at most two decimals, t a band lower
    bound. The legacy score.median_thresholds [t, ...] loads as {q: 0.5, t} each. median_thresholds is kept as the
    derived list of q = 0.5 thresholds (reproduce mode and the median rows read it). Both may be given only when they
    agree (a validated config carries both, so validation is idempotent). At least one q = 0.5 target is required:
    the Trim threshold is the first one."""
    pts = sc.get("percentile_targets")
    legacy = sc.get("median_thresholds")
    if pts is None and legacy is None:
        raise ConfigError("missing required config values: score.percentile_targets (or the legacy "
                          "score.median_thresholds)")
    if pts is None:
        pts = [{"q": 0.5, "t": t} for t in legacy]
    out = []
    for p in pts:
        if not isinstance(p, dict) or set(p) != {"q", "t"}:
            raise ConfigError("each score.percentile_targets entry is {q, t}")
        q, t = float(p["q"]), p["t"]
        if not 0.0 < q < 1.0:
            raise ConfigError(f"score.percentile_targets: q = {q:g} must lie strictly between 0 and 1")
        if abs(q * 100 - round(q * 100)) > 1e-9:
            raise ConfigError(f"score.percentile_targets: q = {q!r} has more than two decimals")
        if t not in bands:
            raise ConfigError(f"score.percentile_targets: t = {t} must be one of score.bands (a band lower bound)")
        out.append({"q": round(q, 2), "t": t})
    keys = [(p["q"], p["t"]) for p in out]
    if len(set(keys)) != len(keys):
        raise ConfigError("score.percentile_targets lists a target twice")
    med = [p["t"] for p in out if p["q"] == 0.5]
    if not med:
        raise ConfigError("score.percentile_targets needs at least one q = 0.5 target (the median; the Trim order's "
                          "threshold is the first one)")
    if legacy is not None and list(legacy) != med:
        raise ConfigError("score.median_thresholds and score.percentile_targets disagree; give percentile_targets "
                          "only (median_thresholds is derived from its q = 0.5 targets)")
    sc["percentile_targets"] = out
    sc["median_thresholds"] = med


def pct_lattice_n(q):
    """Denominator n of q = m/n in lowest terms (q has at most two decimals, so n divides 100): the smallest divisor
    k of 100 with q x k a whole number. The continuity correction is 1/(2n) [v0.6.3, BM-1]."""
    for k in (1, 2, 4, 5, 10, 20, 25, 50, 100):
        if abs(q * k - round(q * k)) < 1e-9:
            return k
    raise ConfigError(f"q = {q!r} has more than two decimals")


def ntr_target_effective(cfg, target=None):
    """The target every ntr_target figure reads [v0.6.3, BM-4]: ntr_target under entering_y1; under all_jd (ntr_target
    is the total JD goal) ntr_target - continuing_ntr_usd. None when no target is set."""
    target = cfg.get("ntr_target") if target is None else target
    if target is None:
        return None
    if cfg.get("ntr_goal_basis", "entering_y1") == "all_jd":
        return float(target) - float(cfg["continuing_ntr_usd"])
    return float(target)


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
    """Cumulative tuition increase (percent) from base_cycle to plan_year from tuition_increase_by_year.

    [v0.6.3, BM-2] A year in tuition_by_year_usd takes precedence: the factor relative to tuition_base becomes
    tuition_by_year_usd / tuition_base there, so the implied increase 100 x (tuition_by_year_usd / tuition_base - 1)
    is stored unrounded and round_to(tuition_base x (1 + p), tuition_rounding_usd) returns the dollar figure."""
    base = cfg["cycle"]["base_cycle"]
    usd = cfg.get("tuition_by_year_usd") or {}
    f = 1.0
    for y in range(base + 1, plan_year + 1):
        if y in usd:
            f = usd[y] / float(cfg["tuition_base"])
            continue
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
