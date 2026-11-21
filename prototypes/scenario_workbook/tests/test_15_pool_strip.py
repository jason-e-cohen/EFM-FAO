"""Test 15: pool strip. At each m, every strip figure equals the ledger run with pool_multiplier = m (no clip, no
rounding); probabilities stay in [0, 1].

Also checked here (Phase 1 functions; the Excel side is test 8 in Phase 2): the yield strip at shift d equals the
ledger with the shift entered when no cell clips, and the tuition what-if row at the scenario's own p equals the
ledger ntr_y1.
"""
import math
from dataclasses import replace

import numpy as np
import pytest

from sw import ledger as L, response, risk, strip


def _scenario(cells, cfg):
    return L.derive(L.baseline(cells, cfg), "S", cfg, cells, pool_multiplier=1.3, bonus_usd=5000.0,
                    segment_pool_lift_pct=10.0, yield_shift_pts=0.5, specialty_usd=20000.0)


def test_pool_strip_equals_ledger(syn_cfg, worlds):
    cfg = syn_cfg
    s = cfg["risk"]["common_shock_sd"]
    rho = cfg["risk"]["shock_corr_above_below"]
    for seed in cfg["generator"]["seeds"][:5]:
        cells = worlds[seed]
        base = response.base_yield(cells, cfg)
        sc = _scenario(cells, cfg)
        ps = strip.pool_strip(cells, cfg, sc, base)
        assert ps["label"] == "yield held constant as the pool changes"
        for row in ps["pool_strip"]:
            m = row["pool_multiplier"]
            lc = L.evaluate(cells, cfg, replace(sc, pool_multiplier=m), base, "middle")
            cf = risk.cf_class(lc.admits, lc.yld, s, sc.class_cap, sc.class_target, cfg["class"]["band"])
            assert row["class_mean"] == pytest.approx(float(lc.mu.sum()), rel=1e-12)
            assert row["p_class_over_cap"] == pytest.approx(cf["p_class_over_cap"], abs=1e-12)
            # F-4: the median at every score median threshold
            assert sorted(row["median"]) == sorted(cfg["score"]["median_thresholds"])
            for t in cfg["score"]["median_thresholds"]:
                g = risk.median_signs(cells, cfg, "score", t)
                md = risk.cf_median(lc.admits, lc.yld, g, s, rho)
                assert row["median"][t]["margin"] == pytest.approx(md["margin_expected"], abs=1e-9)
                assert row["median"][t]["p"] == pytest.approx(md["p"], abs=1e-12)
                assert 0.0 <= row["median"][t]["p"] <= 1.0
            assert row["ntr_mean"] == pytest.approx(L.money(lc)["ntr_y1"], rel=1e-12)
            assert row["growth"] == pytest.approx(m - 1)
            assert 0.0 <= row["p_class_over_cap"] <= 1.0


def test_yield_strip_equals_ledger_when_no_clip(syn_cfg, worlds):
    cfg = syn_cfg
    cells = worlds[cfg["generator"]["seeds"][0]]
    base = response.base_yield(cells, cfg)
    sc = _scenario(cells, cfg)
    lc = L.evaluate(cells, cfg, sc, base, "middle")
    ys = strip.yield_strip(lc)
    assert ys["clip_count"] == 0
    for row in ys["yield_strip"]:
        d = row["shift_pts"]
        lcd = L.evaluate(cells, cfg, replace(sc, yield_shift_pts=sc.yield_shift_pts + d), base, "middle")
        assert row["class_mean"] == pytest.approx(float(lcd.mu.sum()), rel=1e-12)
        assert row["ntr_mean"] == pytest.approx(L.money(lcd)["ntr_y1"], rel=1e-12)
        cp = risk.class_probs(lcd)
        assert row["p_class_over_cap"] == pytest.approx(cp["p_class_over_cap"], abs=1e-12)
    be = ys["breakeven_shift_class"]
    lcb = L.evaluate(cells, cfg, replace(sc, yield_shift_pts=sc.yield_shift_pts + be), base, "middle")
    assert float(lcb.mu.sum()) == pytest.approx(sc.class_target, abs=1e-9)


def test_tuition_whatif_own_p(syn_cfg, worlds):
    cfg = syn_cfg
    cells = worlds[cfg["generator"]["seeds"][0]]
    base = response.base_yield(cells, cfg)
    sc = _scenario(cells, cfg)
    lc = L.evaluate(cells, cfg, sc, base, "middle")
    tw = strip.tuition(lc, grid=[sc.tuition_increase_pct])
    assert tw["tuition_whatif"][0]["ntr_y1"] == pytest.approx(L.money(lc)["ntr_y1"], rel=1e-12)
    assert tw["net_tuition_line_fixed"] == lc.tuition - cfg["tuition_base"]
    assert tw["labels"] == ["Sticker-price demand effect not modeled."]
