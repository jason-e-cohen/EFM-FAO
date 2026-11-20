"""Test 24 [v0.6.3, BM-6] (Review_Phase2_2_Plan.md section 4, task 4): pool strip, percentile columns, break-evens and
the growth-to-date marker.

On synthetic worlds and several scenarios: m_class evaluated through the ledger gives expected class equal to the
target within 1e-9; m_q gives expected M_q of 0 within 1e-9; the percentile probability at each pool multiplier equals
a ledger evaluation at that multiplier (risk.pct). The marker sits on the grid row nearest 1 + pool_ytd_growth (R4-13:
a tie goes to the upper row; 1 + 0.05, 1 + 0.15 and 1 + 0.25 are exact midpoints) and is absent without growth.

R4-04: a break-even that is not a pool size on the grid is a note (strip.breakeven_m): "holds at any pool size" when the
target holds with no top-pool growth, "not reached by growth", "above the pool grid", "below the pool grid". Every
number and every grid note is checked through the ledger at the unclipped multiplier; low targets (q 0.25 at 154, q 0.10
at 152) fall below the grid on worlds 101 to 105, where the unclipped multiplier is often negative ("holds at any pool
size").
"""
import copy
from dataclasses import replace

import numpy as np
import pytest

from sw import labels, ledger as L, response, risk, strip
from sw.config import validate

SCENARIOS = [dict(), dict(pool_multiplier=1.3, yield_shift_pts=-1.0),
             dict(bonus_usd=8000.0, bonus_scope="segment", segment_pool_lift_pct=10.0, class_target=120.0)]


def _cases(syn_cfg, worlds, n=6):
    for seed in list(worlds)[:n]:
        cells = worlds[seed]
        base = response.base_yield(cells, syn_cfg)
        for k, lev in enumerate(SCENARIOS):
            yield seed, cells, base, L.derive(L.baseline(cells, syn_cfg), f"s{k}", syn_cfg, cells, **lev)


def _check_note(got, e_lo, e_hi, grid):
    """got (strip.breakeven_m) against the unclipped multiplier -e_lo / e_hi; returns that multiplier or None."""
    if e_hi == 0:
        assert got == (labels.POOL_BE_ANY if e_lo >= 0 else labels.POOL_BE_NOT_REACHED)
        return None
    m = -e_lo / e_hi
    if m <= 0:
        assert got == (labels.POOL_BE_ANY if e_hi > 0 else labels.POOL_BE_NOT_REACHED)
        return None
    if m > max(grid):
        assert got == labels.POOL_BE_ABOVE_GRID
    elif m < min(grid):
        assert got == labels.POOL_BE_BELOW_GRID
    else:
        assert isinstance(got, float) and got == m
    return m


def test_breakeven_multipliers_through_the_ledger(syn_cfg, worlds):
    cfg = syn_cfg
    s = cfg["risk"]["common_shock_sd"]
    rho = cfg["risk"]["shock_corr_above_below"]
    grid = cfg["risk"]["pool_grid"]
    kinds = set()
    for seed, cells, base, sc in _cases(cfg, worlds):
        ps = strip.pool_strip(cells, cfg, sc, base)
        be = ps["pool_breakeven_m"]
        assert ps["pool_breakeven_label"] == labels.POOL_BREAKEVEN_LABEL
        P, Q = ps["parts"]["lo"], ps["parts"]["hi"]
        m = _check_note(be["class"], P["M"] - sc.class_target, Q["M"], grid)
        kinds.add(be["class"] if isinstance(be["class"], str) else "number")
        if m is not None:
            lc = L.evaluate(cells, cfg, replace(sc, pool_multiplier=m), base, "middle")
            assert lc.mu.sum() == pytest.approx(sc.class_target, abs=1e-9), seed
        for q, t in risk.pct_targets(cfg):
            pp = ps["pct_parts"][(q, t)]
            e_lo = q * pp["lo"]["Gp"] - (1 - q) * pp["lo"]["Gm"]
            e_hi = q * pp["hi"]["Gp"] - (1 - q) * pp["hi"]["Gm"]
            m = _check_note(be[(q, t)], e_lo, e_hi, grid)
            kinds.add(be[(q, t)] if isinstance(be[(q, t)], str) else "number")
            if m is None:
                continue
            lc = L.evaluate(cells, cfg, replace(sc, pool_multiplier=m), base, "middle")
            g = risk.median_signs(cells, cfg, "score", t)
            assert risk.cf_pct(lc.admits, lc.yld, g, q, s, rho)["margin_expected"] == pytest.approx(0.0, abs=1e-9)
    # the synthetic targets reach numbers and both grid notes
    assert {"number", labels.POOL_BE_ABOVE_GRID, labels.POOL_BE_BELOW_GRID} <= kinds, kinds


def test_low_targets_hold_at_any_pool_size(syn_cfg, worlds):
    """R4-04: with a low target the expected margin is often positive with no top-pool applicants at all, so the
    unclipped multiplier is negative and the strip shows 'holds at any pool size' (otherwise 'below the pool grid'). A break-even with e_hi = 0 or a negative e_hi
    and e_lo takes the other notes (strip.breakeven_m directly)."""
    raw = copy.deepcopy({k: v for k, v in syn_cfg.items() if not k.startswith("_")})
    raw["score"].pop("median_thresholds", None)
    raw["score"]["percentile_targets"] = [{"q": 0.5, "t": 166}, {"q": 0.25, "t": 154}, {"q": 0.10, "t": 152}]
    cfg = validate(raw)
    seen = set()
    for seed in [101, 102, 103, 104, 105]:
        cells = worlds[seed]
        base = response.base_yield(cells, cfg)
        ps = strip.pool_strip(cells, cfg, L.baseline(cells, cfg), base)
        for key in ((0.25, 154), (0.10, 152)):
            pp = ps["pct_parts"][key]
            q = key[0]
            e_lo = q * pp["lo"]["Gp"] - (1 - q) * pp["lo"]["Gm"]
            e_hi = q * pp["hi"]["Gp"] - (1 - q) * pp["hi"]["Gm"]
            m = -e_lo / e_hi
            assert e_hi > 0 and m < min(cfg["risk"]["pool_grid"]), (seed, key, m)
            assert ps["pool_breakeven_m"][key] == (labels.POOL_BE_ANY if m <= 0 else labels.POOL_BE_BELOW_GRID)
            seen.add(ps["pool_breakeven_m"][key])
    assert labels.POOL_BE_ANY in seen
    g = [0.8, 1.6]
    assert strip.breakeven_m(-1.0, 0.0, g) == labels.POOL_BE_NOT_REACHED
    assert strip.breakeven_m(0.0, 0.0, g) == labels.POOL_BE_ANY
    assert strip.breakeven_m(-1.0, -2.0, g) == labels.POOL_BE_NOT_REACHED
    assert strip.breakeven_m(2.4, -2.0, g) == 1.2                   # growth lowers the margin to zero at 1.2
    assert strip.breakeven_m(-4.0, 2.0, g) == labels.POOL_BE_ABOVE_GRID
    assert strip.breakeven_m(-1.0, 2.0, g) == labels.POOL_BE_BELOW_GRID
    assert strip.breakeven_m(-1.6, 1.0, g) == 1.6 and strip.breakeven_m(-0.8, 1.0, g) == 0.8


def test_percentile_columns_equal_ledger_evaluations(syn_cfg, worlds):
    for rho in (1.0, 0.5):
        raw = copy.deepcopy({k: v for k, v in syn_cfg.items() if not k.startswith("_")})
        raw["risk"]["shock_corr_above_below"] = rho
        cfg = validate(raw)
        for seed, cells, base, sc in _cases(cfg, worlds, n=3):
            ps = strip.pool_strip(cells, cfg, sc, base)
            for row in ps["pool_strip"]:
                lc = L.evaluate(cells, cfg, replace(sc, pool_multiplier=row["pool_multiplier"]), base, "middle")
                for q, t in risk.pct_targets(cfg):
                    pc = risk.pct(lc, q, t)
                    assert row["pct"][(q, t)]["p"] == pytest.approx(pc["p_pct_q_t"], abs=1e-9), (seed, rho, q, t)
                    assert row["pct"][(q, t)]["margin"] == pytest.approx(pc["margin_expected"], abs=1e-9)
                    assert 0.0 <= row["pct"][(q, t)]["p"] <= 1.0


@pytest.mark.parametrize("growth,row", [(0.12, 4), (0.0, 3), (-0.5, 1), (0.9, 9), (0.33, 6), (0.149, 4),
                                        (0.151, 5), (0.05, 4), (0.15, 5), (0.25, 6), (-0.05, 3), (None, None)])
def test_marker_row(syn_cfg, worlds, growth, row):
    """pool_grid 0.8 to 1.6 by 0.1: growth 0.12 marks 1.1 (row 4); 0.149 marks 1.1, 0.151 marks 1.2; R4-13: a tie goes to
    the upper row (0.05 marks 1.1, 0.15 marks 1.2, 0.25 marks 1.3, -0.05 marks 1.0); beyond the grid the end rows; no
    growth, no marker."""
    raw = copy.deepcopy({k: v for k, v in syn_cfg.items() if not k.startswith("_")})
    raw["pool_ytd_growth"] = growth
    cfg = validate(raw)
    cells = worlds[cfg["generator"]["seeds"][0]]
    base = response.base_yield(cells, cfg)
    ps = strip.pool_strip(cells, cfg, L.baseline(cells, cfg), base)
    assert ps["nearest_row"] == row
    marks = [i + 1 for i, r in enumerate(ps["pool_strip"]) if r["marker"]]
    assert marks == ([] if row is None else [row])
    if row is not None:
        assert ps["pool_strip"][row - 1]["marker"] == labels.POOL_YTD_MARKER.format(as_of="2026-11-15")
    raw["pool_ytd_as_of"] = None
    cfg2 = validate(raw)
    ps2 = strip.pool_strip(cells, cfg2, L.baseline(cells, cfg2), base)
    if row is not None:
        assert ps2["pool_strip"][row - 1]["marker"] == labels.POOL_YTD_MARKER.format(as_of=labels.POOL_YTD_NO_DATE)
