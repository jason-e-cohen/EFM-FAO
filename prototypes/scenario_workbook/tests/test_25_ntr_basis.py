"""Test 25 [v0.6.3, BM-4] (Review_Phase2_2_Plan.md section 4, task 5): the revenue goal basis.

entering_y1 reproduces v0.6 everywhere (the three figures that read ntr_target: the Summary probability, the yield-strip
probability and the yield-strip NTR break-even); all_jd with continuing 0 equals entering_y1; for any goal G and
continuing C, each of the three figures under all_jd at G equals the entering_y1 figure at G - C. Under all_jd the dump
carries P(continuing + ntr_y1 >= goal) and the projected JD net tuition; the tuition what-if says continuing revenue is
held at the supplied figure.
"""
import copy

import numpy as np
import pytest

from sw import labels, ledger as L, response, risk, strip
from sw.config import validate


def _cfg(syn_cfg, **over):
    raw = copy.deepcopy({k: v for k, v in syn_cfg.items() if not k.startswith("_")})
    raw.update(over)
    return validate(raw)


def _three(cells, cfg, sc, base):
    lc = L.evaluate(cells, cfg, sc, base, "middle")
    ys = strip.yield_strip(lc)
    return ([risk.ntr(lc)["p_ntr_y1_ge_target"]] + [r["p_ntr_y1_ge_target"] for r in ys["yield_strip"]]
            + [ys["breakeven_shift_ntr"]])


@pytest.fixture(scope="module")
def world(syn_cfg, worlds):
    cells = worlds[syn_cfg["generator"]["seeds"][3]]
    base = response.base_yield(cells, syn_cfg)
    sc = L.derive(L.baseline(cells, syn_cfg), "s", syn_cfg, cells, bonus_usd=5000.0, specialty_usd=20000.0)
    return cells, base, sc


def test_entering_y1_is_v06(syn_cfg, world):
    cells, base, sc = world
    cfg = syn_cfg
    lc = L.evaluate(cells, cfg, sc, base, "middle")
    s = cfg["risk"]["common_shock_sd"]
    G = cfg["ntr_target"]
    # v0.6: target read as given; constant = specialty (live mode has no need departure)
    assert lc.need_lump == 0.0 and lc.ntr_const == lc.specialty
    v06 = risk.cf_ntr(lc.admits, lc.yld, lc.w, s, lc.specialty, G)["p_ntr_y1_ge_target"]
    assert risk.ntr(lc)["p_ntr_y1_ge_target"] == v06
    ys = strip.yield_strip(lc)
    for r in ys["yield_strip"]:
        yd = lc.yld + r["shift_pts"] / 100.0
        assert r["p_ntr_y1_ge_target"] == risk.cf_ntr(lc.admits, yd, lc.w, s, lc.specialty, G)["p_ntr_y1_ge_target"]
    mean = float((lc.w * lc.admits * lc.yld).sum()) - lc.specialty
    assert ys["breakeven_shift_ntr"] == pytest.approx((G - mean) / float((lc.w * lc.admits).sum()) * 100, rel=1e-12)
    assert strip.tuition(lc)["continuing_note"] == ""


def test_all_jd_with_zero_continuing_equals_entering(syn_cfg, world):
    cells, base, sc = world
    a = _three(cells, syn_cfg, sc, base)
    b = _three(cells, _cfg(syn_cfg, ntr_goal_basis="all_jd", continuing_ntr_usd=0), sc, base)
    assert a == b


@pytest.mark.parametrize("G,C", [(4_300_000, 1_000_000), (12_000_000, 8_500_000), (9_000_000, 3_250_000.5),
                                 (5_000_000, -250_000)])
def test_all_jd_at_G_equals_entering_at_G_minus_C(syn_cfg, world, G, C):
    cells, base, sc = world
    jd = _cfg(syn_cfg, ntr_goal_basis="all_jd", continuing_ntr_usd=C, ntr_target=G)
    en = _cfg(syn_cfg, ntr_target=G - C)
    assert _three(cells, jd, sc, base) == _three(cells, en, sc, base)
    lc = L.evaluate(cells, jd, sc, base, "middle")
    assert strip.tuition(lc)["continuing_note"] == labels.CONTINUING_HELD


def test_dump_carries_the_jd_figures(syn_cfg, world):
    from sw import build, contract as K
    cells, base, sc = world
    for cfg, jd in ((syn_cfg, False), (_cfg(syn_cfg, ntr_goal_basis="all_jd", continuing_ntr_usd=7_000_000,
                                            ntr_target=11_000_000), True)):
        run = build.make_run(cfg, cells, [L.baseline(cells, cfg)], {"build_id": "t25"})
        vals = K.compute(run)
        d = vals["sk"][("Baseline", "middle")]
        if jd:
            assert d["p_jd_ntr_ge_goal"] == d["p_ntr_y1_ge_target"] is not None
            assert d["jd_ntr"] == pytest.approx(7_000_000 + d["ntr_y1"], abs=1e-6)
        else:
            assert d["p_jd_ntr_ge_goal"] is None and d["jd_ntr"] is None
        assert K.dump(run, vals)["SUM_P_JD_NTR_GE_GOAL"][1][0] == d["p_jd_ntr_ge_goal"]
