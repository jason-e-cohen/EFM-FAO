"""Reference ledger and KPIs (spec section 3). Python is the definition; the workbook mirrors it.

Metric names follow methodology Appendix F (`ntr_y1`, `discount_entering_y1`, ...). Ratios are ratios of expected
values, E[X] / E[Y], everywhere [v0.6, B3-5].
"""
import copy
import math
from dataclasses import dataclass, field, fields, replace

import numpy as np

from . import CASES
from . import labels
from . import response
from .config import ConfigError, check_class_target, plan_increase_pct, scenario_tuition, segment_def

# Levers that must equal the parent's for the incentive decomposition to be valid (section 3, incentive block).
VALIDITY_FIELDS = (
    "pool_multiplier", "specialty_usd", "need_total", "tuition_increase_pct", "award_scale_with_tuition",
    "class_target", "class_cap", "segment_pool_lift_pct", "yield_shift_pts", "yield_shift_pts_in",
    "yield_shift_pts_out", "yield_shift_pts_segment", "plan_year", "segment",
)
BONUS_SCOPES = ("residency_out", "segment", "none")


def xround(x):
    """Round half up (Excel ROUND for non-negative values)."""
    return np.floor(np.asarray(x, float) + 0.5)


@dataclass
class Scenario:
    name: str
    parent: str | None
    admit_rate: np.ndarray
    award_usd: np.ndarray            # lever dollars (base-cycle dollars when awards scale with tuition)
    full_tuition: np.ndarray         # full-tuition rung: the award equals tuition_s whatever tuition_s is
    tuition_increase_pct: float
    class_target: float
    class_cap: float
    plan_year: int
    description: str = ""
    pool_multiplier: float = 1.0
    specialty_usd: float = 0.0
    need_total: float | None = None
    award_scale_with_tuition: bool = False
    bonus_usd: float = 0.0
    bonus_scope: str = "residency_out"
    bonus_min_score: float | None = None
    segment: str | None = None       # active segment (at most one per scenario)
    segment_pool_lift_pct: float = 0.0
    segment_goal: float | None = None
    yield_shift_pts: float = 0.0
    yield_shift_pts_in: float | None = None
    yield_shift_pts_out: float | None = None
    yield_shift_pts_segment: float | None = None
    discount_target: float | None = None
    notices: list = field(default_factory=list)


@dataclass
class LedgerCase:
    scenario: Scenario
    case: str
    tuition: float
    p: float
    need_rate: float
    specialty: float
    in_segment: np.ndarray
    upper: np.ndarray
    eligible: np.ndarray
    apps: np.ndarray
    rate: np.ndarray
    admits: np.ndarray
    award_base: np.ndarray
    incentive: np.ndarray
    award: np.ndarray
    shift: np.ndarray
    yld: np.ndarray
    mu: np.ndarray                   # admits x yield (expected, unrounded): the risk functions use it
    enrolled: np.ndarray             # mu, rounded when integer_enrolled
    yfloor: np.ndarray
    ycap: np.ndarray
    cells: object
    cfg: dict

    @property
    def w(self):
        """NTR weight per enrollee: tuition - award - need_rate (section 5)."""
        return self.tuition - self.award - self.need_rate

    @property
    def class_n(self):
        return float(self.enrolled.sum())


def active_segment(cfg, scen):
    if scen.segment is not None:
        segment_def(cfg, scen.segment)
        return scen.segment
    if len(cfg["segments"]) == 1:
        return cfg["segments"][0]["name"]
    if len(cfg["segments"]) > 1:
        raise ConfigError("more than one segment is configured; the scenario must name its active segment")
    return None


def segment_mask(cells, cfg, scen):
    name = active_segment(cfg, scen)
    if name is None:
        return np.zeros(cells.n, dtype=bool)
    return cells.segment == name


def baseline(cells, cfg, name="Baseline"):
    """Scenario 0: admit rate and award from the latest cohort, tuition at the plan year, yield from the response base."""
    j = cells.col(cfg["cycle"]["base_cycle"])
    apps = cells.apps[:, j]
    with np.errstate(invalid="ignore", divide="ignore"):
        rate = np.where(apps > 0, cells.admits[:, j] / np.where(apps > 0, apps, 1.0), 0.0)
    award = cells.award[:, j].astype(float).copy()
    full = award >= float(cfg["tuition_base"]) - 1e-6
    plan_year = cfg["cycle"]["plan_cycle"]
    scen = Scenario(
        name=name, parent=None, admit_rate=rate, award_usd=award, full_tuition=full,
        tuition_increase_pct=plan_increase_pct(cfg, plan_year), class_target=float(cfg["class"]["target"]),
        class_cap=float(cfg["class"]["cap"]), plan_year=plan_year,
        need_total=float(cfg["need"]["total"]), discount_target=cfg.get("discount_target"),
    )
    _validate_scenario(cells, cfg, scen)
    return scen


def derive(parent, name, cfg, cells, admit_rate=None, award=None, **changes):
    """Child scenario: copies the parent's levers and applies changes.

    admit_rate, award: mappings cell_id -> value (overrides relative to the parent); full columns are materialized.
    An award override at or above the parent's tuition is the full-tuition rung (section 3, step 4).
    """
    unknown = set(changes) - {f.name for f in fields(Scenario)}
    if unknown:
        raise ConfigError(f"unknown scenario fields: {sorted(unknown)}")
    child = replace(parent, name=name, parent=parent.name, admit_rate=parent.admit_rate.copy(),
                    award_usd=parent.award_usd.copy(), full_tuition=parent.full_tuition.copy(),
                    notices=[], **changes)
    if admit_rate:
        for cid, r in admit_rate.items():
            child.admit_rate[cells.index(cid)] = float(r)
    if award:
        t_parent = scenario_tuition(cfg, parent.tuition_increase_pct)
        for cid, a in award.items():
            i = cells.index(cid)
            child.award_usd[i] = float(a)
            child.full_tuition[i] = float(a) >= t_parent - 1e-6
    _validate_scenario(cells, cfg, child)
    return child


def with_rates(scen, rates, name=None):
    """Copy of a scenario with a full admit-rate column (used by the shrink path)."""
    s = copy.copy(scen)
    s.admit_rate = np.asarray(rates, float).copy()
    if name:
        s.name = name
    return s


def _validate_scenario(cells, cfg, scen):
    if scen.bonus_scope not in BONUS_SCOPES:
        raise ConfigError(f"bonus_scope must be one of {BONUS_SCOPES}")
    if ((scen.admit_rate < 0) | (scen.admit_rate > 1)).any():
        raise ConfigError(f"{scen.name}: admit rates must lie in [0, 1]")
    if (scen.award_usd < 0).any():
        raise ConfigError(f"{scen.name}: awards must be non-negative")
    notice = check_class_target(cfg, scen.class_target, scen.class_cap)
    if notice:
        scen.notices.append(notice)
    seg = segment_mask(cells, cfg, scen)
    if scen.bonus_scope == "segment" and not seg.any():
        if scen.bonus_usd > 0 or scen.segment_pool_lift_pct != 0 or scen.segment_goal is not None:
            raise ConfigError(f"{scen.name}: bonus scope 'segment' with no segment cells in the data")


def _shift(cells, scen, in_seg):
    out = np.full(cells.n, float(scen.yield_shift_pts))
    for res, val in (("in", scen.yield_shift_pts_in), ("out", scen.yield_shift_pts_out)):
        if val is not None:
            out[cells.residency == res] = float(val)
    if scen.yield_shift_pts_segment is not None:
        out[in_seg] = float(scen.yield_shift_pts_segment)
    return out


def eligibility(cells, scen, in_seg):
    if scen.bonus_scope == "residency_out":
        el = cells.residency == "out"
    elif scen.bonus_scope == "segment":
        el = in_seg.copy()
    else:
        el = np.zeros(cells.n, dtype=bool)
    if scen.bonus_min_score is not None:
        with np.errstate(invalid="ignore"):
            el = el & np.where(np.isnan(cells.score_lo), False, cells.score_lo >= scen.bonus_min_score)
    return el.astype(bool)


def resolve_awards(scen, tuition, p, eligible):
    """Section 3, step 4. Returns (award_base, award)."""
    lever = scen.award_usd * (1.0 + p) if scen.award_scale_with_tuition else scen.award_usd
    base = np.where(scen.full_tuition, tuition, lever)
    base = np.minimum(base, tuition)
    award = np.minimum(base + scen.bonus_usd * eligible, tuition)
    return base, award


def evaluate(cells, cfg, scen, base, case):
    """One scenario, one case. Section 3, steps 1 to 6."""
    if case not in CASES:
        raise ValueError(case)
    j = cells.col(cfg["cycle"]["base_cycle"])
    p = scen.tuition_increase_pct / 100.0
    tuition = scenario_tuition(cfg, scen.tuition_increase_pct)
    upper = response.score_group_upper(cells, cfg)
    in_seg = segment_mask(cells, cfg, scen)
    # 2. applications
    pool = np.where(upper, scen.pool_multiplier, 1.0)
    apps = cells.apps[:, j] * pool * (1.0 + (scen.segment_pool_lift_pct / 100.0) * in_seg)
    # 3. admits
    admits = apps * scen.admit_rate
    if cfg["integer_admits"]:
        admits = xround(admits)
    # 4. awards
    elig = eligibility(cells, scen, in_seg)
    award_base, award = resolve_awards(scen, tuition, p, elig)
    incentive = award - award_base
    # 5. yield
    shift = _shift(cells, scen, in_seg)
    yld = np.clip(response.yield_at(base, award, case) + shift / 100.0, base.floor, base.cap)
    # 6. enrolled
    mu = admits * yld
    enrolled = xround(mu) if cfg["integer_enrolled"] else mu.copy()
    need_total = cfg["need"]["total"] if scen.need_total is None else scen.need_total
    need_rate = float(need_total) / float(cfg["need"]["reference_class"])
    return LedgerCase(
        scenario=scen, case=case, tuition=tuition, p=p, need_rate=need_rate, specialty=float(scen.specialty_usd),
        in_segment=in_seg, upper=upper, eligible=elig, apps=apps, rate=scen.admit_rate.copy(), admits=admits,
        award_base=award_base, incentive=incentive, award=award, shift=shift, yld=yld, mu=mu, enrolled=enrolled,
        yfloor=base.floor, ycap=base.cap, cells=cells, cfg=cfg,
    )


def evaluate_all(cells, cfg, scen, base):
    return {k: evaluate(cells, cfg, scen, base, k) for k in CASES}


# ---------------------------------------------------------------------------------------------------------------
# Outputs (interface contract names, spec section 15 item 11)

def money(lc):
    """Steps 7 and 8: gross_y1, merit, need, specialty, aid, ntr_y1, discount_entering_y1, avg_aid."""
    e = lc.enrolled
    cls = float(e.sum())
    merit = float((e * lc.award).sum())
    need = lc.need_rate * cls
    gross = cls * lc.tuition
    aid = merit + need + lc.specialty
    return {
        "class_n": cls,
        "gross_y1": gross,
        "merit": merit,
        "incentive_cost": float((e * lc.incentive).sum()),
        "need": need,
        "need_rate": lc.need_rate,
        "specialty": lc.specialty,
        "aid": aid,
        "ntr_y1": gross - aid,
        "discount_entering_y1": aid / gross if gross > 0 else 0.0,
        "avg_aid": aid / cls if cls > 0 else 0.0,
        "tuition": lc.tuition,
        "labels": [labels.RESPONSE_LABEL],
    }


def score_thresholds(cfg):
    sc = cfg["score"]
    return sorted(set(sc["median_thresholds"]) | {sc["pool_threshold"], sc["floor"]}, reverse=True)


def kpis(lc):
    """KPIs per scenario and case (section 3). Counts use enrolled; shares are ratios of expected values."""
    cells, cfg = lc.cells, lc.cfg
    e = lc.enrolled
    s = cells.score_lo
    scored = ~np.isnan(s)
    e_scored = float(e[scored].sum())
    out = {
        "class_n": float(e.sum()),
        "apps_total": float(lc.apps.sum()),
        "apps_in": float(lc.apps[cells.residency == "in"].sum()),
        "apps_out": float(lc.apps[cells.residency == "out"].sum()),
        "admits_total": float(lc.admits.sum()),
        "admits_in": float(lc.admits[cells.residency == "in"].sum()),
        "admits_out": float(lc.admits[cells.residency == "out"].sum()),
        "enrolled_at_or_above": {},
        "share_at_or_above_t": {},
        "unscored_count": float(e[~scored].sum()),
        "gpa_blank_count": float(e[cells.gpa_class == "blank"].sum()),
        "enrolled_gpa_hi": float(e[cells.gpa_class == "hi"].sum()),
    }
    with np.errstate(invalid="ignore"):
        for t in score_thresholds(cfg):
            at = float(e[scored & (s >= t)].sum())
            out["enrolled_at_or_above"][t] = at
            out["share_at_or_above_t"][t] = at / e_scored if e_scored > 0 else 0.0
        out["enrolled_below_floor"] = float(e[scored & (s < cfg["score"]["floor"])].sum())
    cls = out["class_n"]
    out["full_tuition_n"] = float(e[lc.award >= lc.tuition - 1e-6].sum())
    out["no_merit_award_n"] = float(e[lc.award <= 1e-9].sum())
    out["barbell"] = (out["full_tuition_n"] + out["no_merit_award_n"]) / cls if cls > 0 else 0.0
    return out


def price_of_target(base_lc, lc):
    """Baseline ntr_y1 minus scenario ntr_y1."""
    return money(base_lc)["ntr_y1"] - money(lc)["ntr_y1"]


def discount_row(lc):
    t = lc.scenario.discount_target
    if t is None:
        return None
    d = money(lc)["discount_entering_y1"]
    return {"discount_entering_y1": d, "discount_target": t, "margin_to_target": t - d}


def scenario_labels(scen, cfg):
    """Labels that apply to a scenario's response-dependent outputs (section 4)."""
    out = [labels.RESPONSE_LABEL]
    shifts = [scen.yield_shift_pts, scen.yield_shift_pts_in, scen.yield_shift_pts_out, scen.yield_shift_pts_segment]
    if any(v not in (None, 0, 0.0) for v in shifts) or scen.segment_pool_lift_pct != 0:
        out.append(labels.ASSUMPTION_LABEL)
    if cfg["risk"]["shock_source"] == "illustrative":
        out.append(labels.shock_label(cfg["risk"]["common_shock_sd"]))
    return out


def segment(lc, goal=None):
    """Segment block (section 3). Every figure is the 'no segment cells' text when the segment is empty."""
    from . import risk
    cfg = lc.cfg
    keys = ("segment_apps", "segment_admits", "segment_enrolled", "segment_share", "segment_merit",
            "segment_lo90", "segment_hi90", "p_segment_goal", "p_segment_goal_normal", "segment_goal")
    goal = lc.scenario.segment_goal if goal is None else goal
    m = lc.in_segment
    if not m.any():
        out = {k: labels.NO_SEGMENT_CELLS for k in keys}
        out["labels"] = []
        out["approximate"] = labels.NO_SEGMENT_CELLS
        return out
    s = float(cfg["risk"]["common_shock_sd"])
    mu = lc.mu[m]
    M = float(mu.sum())
    V = float((lc.admits[m] * lc.yld[m] * (1 - lc.yld[m])).sum() + s * s * M * M)
    sd = math.sqrt(max(V, 0.0))
    cls = float(lc.enrolled.sum())
    out = {
        "segment_apps": float(lc.apps[m].sum()),
        "segment_admits": float(lc.admits[m].sum()),
        "segment_enrolled": float(lc.enrolled[m].sum()),
        "segment_share": float(lc.enrolled[m].sum()) / cls if cls > 0 else 0.0,
        "segment_merit": float((lc.enrolled[m] * lc.award[m]).sum()),
        "segment_lo90": max(0.0, M - 1.645 * sd),
        "segment_hi90": M + 1.645 * sd,
        "segment_goal": None,
        "p_segment_goal": None,
        "p_segment_goal_normal": None,
        "approximate": labels.SEGMENT_APPROX if M < 20 else "",
    }
    if goal is not None:
        g = math.ceil(goal)
        out["segment_goal"] = g
        out["p_segment_goal"] = risk.segment_exact(lc, g)
        out["p_segment_goal_normal"] = risk.segment_normal(M, V, g)
    lab = [labels.RESPONSE_LABEL]
    sd_cfg = segment_def(cfg, active_segment(cfg, lc.scenario))
    if sd_cfg["share_source"] == "assumed":
        lab.append(labels.SEGMENT_SHARE_LABEL)
    if cfg["risk"]["shock_source"] == "illustrative":
        lab.append(labels.shock_label(s))
    out["labels"] = lab
    return out


def incentive_valid(scen_s, scen_p):
    for f in VALIDITY_FIELDS:
        if getattr(scen_s, f) != getattr(scen_p, f):
            return False
    for arr in ("admit_rate", "award_usd", "full_tuition"):
        a, b = getattr(scen_s, arr), getattr(scen_p, arr)
        if a.shape != b.shape or not np.array_equal(a, b):
            return False
    return True


def incentive(lc_s, lc_p):
    """Incentive block: one decomposition over the cells with incentive > 0, against the parent (section 3)."""
    pop = lc_s.incentive > 0
    e_s, e_p = lc_s.enrolled, lc_p.enrolled
    a_s, a_p = lc_s.award, lc_p.award
    inc = lc_s.incentive
    C = float((e_s * inc)[pop].sum())
    C_any = float((np.minimum(e_p, e_s) * inc)[pop].sum())
    dE = float((e_s - e_p)[pop].sum())
    dSpend = float((e_s * a_s - e_p * a_p)[pop].sum())
    dNTR = float((e_s * lc_s.w - e_p * lc_p.w)[pop].sum())
    valid = incentive_valid(lc_s.scenario, lc_p.scenario)
    out = {
        "incentive_cost": C,
        "incentive_paid_anyway": C_any,
        "incentive_paid_anyway_share": C_any / C if C > 0 else 0.0,
        "additional_enrollees": dE,
        "merit_change": dSpend,
        "ntr_change": dNTR,
        "incentive_cells": int(pop.sum()),
        "incentive_valid": labels.INCENTIVE_VALID if valid else labels.INCENTIVE_NOT_VALID,
        "labels": [labels.RESPONSE_LABEL],
    }
    if dE >= 0.5:
        out["aid_per_additional"] = dSpend / dE
        out["aid_per_additional_kind"] = labels.AID_PER_ADDITIONAL
        out["ntr_per_additional"] = dNTR / dE
    elif dE <= -0.5:
        out["aid_per_additional"] = dSpend / dE
        out["aid_per_additional_kind"] = labels.SAVINGS_PER_LOST
        out["ntr_per_additional"] = dNTR / dE
    else:
        out["aid_per_additional"] = labels.UNDER_HALF
        out["aid_per_additional_kind"] = labels.UNDER_HALF
        out["ntr_per_additional"] = labels.UNDER_HALF
    return out


def bonus_implied_by_pool(pool_usd, base_lc, scen):
    """Informational: dollar pool / baseline expected enrolled in the scope."""
    el = eligibility(base_lc.cells, scen, base_lc.in_segment)
    n = float(base_lc.enrolled[el].sum())
    return pool_usd / n if n > 0 else None


def awards(lc):
    """Award matrix and step sizes (award difference between adjacent score bands within residency x segment x GPA
    class). A plain table: no threshold, flag or message."""
    cells = lc.cells
    matrix = {cid: float(a) for cid, a in zip(cells.cell_id, lc.award)}
    steps = []
    groups = {}
    for i in range(cells.n):
        if np.isnan(cells.score_lo[i]):
            continue
        groups.setdefault((cells.residency[i], cells.segment[i], cells.gpa_class[i]), []).append(i)
    for key, idx in groups.items():
        idx = sorted(idx, key=lambda i: -cells.score_lo[i])
        for hi_i, lo_i in zip(idx[:-1], idx[1:]):
            steps.append({"residency": key[0], "segment": key[1], "gpa_class": key[2],
                          "band_upper": float(cells.score_lo[hi_i]), "band_lower": float(cells.score_lo[lo_i]),
                          "step_usd": float(lc.award[hi_i] - lc.award[lo_i])})
    return {"award_matrix": matrix, "step_sizes": steps}
