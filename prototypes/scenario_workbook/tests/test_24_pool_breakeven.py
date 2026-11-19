"""Test 24 [v0.6.3, BM-6] (Review_Phase2_2_Plan.md section 4, task 4): pool strip, percentile columns, break-evens and
the growth-to-date marker.

On synthetic worlds and several scenarios: m_class evaluated through the ledger gives expected class equal to the
target within 1e-9; m_q gives expected M_q of 0 within 1e-9; the percentile probability at each pool multiplier equals
a ledger evaluation at that multiplier (risk.pct). The marker sits on the grid row nearest 1 + pool_ytd_growth (a tie
goes to the lower row) and is absent without growth.
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


def test_breakeven_multipliers_through_the_ledger(syn_cfg, worlds):
    cfg = syn_cfg
    s = cfg["risk"]["common_shock_sd"]
    rho = cfg["risk"]["shock_corr_above_below"]
    for seed, cells, base, sc in _cases(cfg, worlds):
        ps = strip.pool_strip(cells, cfg, sc, base)
        be = ps["pool_breakeven_m"]
        assert ps["pool_breakeven_label"] == labels.POOL_BREAKEVEN_LABEL
        lc = L.evaluate(cells, cfg, replace(sc, pool_multiplier=be["class"]), base, "middle")
        assert lc.mu.sum() == pytest.approx(sc.class_target, abs=1e-9), seed
        for q, t in risk.pct_targets(cfg):
            m = be[(q, t)]
            assert m is not None and np.isfinite(m)
            lc = L.evaluate(cells, cfg, replace(sc, pool_multiplier=m), base, "middle")
            g = risk.median_signs(cells, cfg, "score", t)
            assert risk.cf_pct(lc.admits, lc.yld, g, q, s, rho)["margin_expected"] == pytest.approx(0.0, abs=1e-9)


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
                                        (0.151, 5), (None, None)])
def test_marker_row(syn_cfg, worlds, growth, row):
    """pool_grid 0.8 to 1.6 by 0.1: growth 0.12 marks 1.1 (row 4); 0.149 marks 1.1, 0.151 marks 1.2; beyond the grid
    the end rows; no growth, no marker."""
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
