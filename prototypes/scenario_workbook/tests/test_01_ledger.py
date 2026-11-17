"""Test 1: ledger identities of section 3 on the six-cell toy grid, against hand-computed answers."""
import numpy as np
import pytest

from sw import ledger as L, response, risk
from toy import P, S, idx, toy_cells, toy_cfg, toy_override


@pytest.fixture(scope="module")
def toy():
    cfg = toy_cfg()
    cells = toy_cells(cfg)
    base = response.base_yield(cells, cfg, base_override=toy_override())
    return cfg, cells, base


def scen_S(cfg, cells, b):
    return L.derive(b, "S", cfg, cells, pool_multiplier=1.2, segment_pool_lift_pct=10.0, bonus_usd=10000.0,
                    bonus_scope="residency_out", yield_shift_pts=1.0, yield_shift_pts_segment=-2.0,
                    specialty_usd=5000.0)


def scen_P(cfg, cells, b):
    return L.derive(b, "P", cfg, cells, pool_multiplier=1.2, bonus_usd=10000.0, bonus_scope="residency_out")


def test_tuition_and_need(toy):
    cfg, cells, base = toy
    b = L.baseline(cells, cfg)
    lc = L.evaluate(cells, cfg, b, base, "middle")
    assert lc.tuition == 53000.0
    assert lc.need_rate == 1000.0


def test_identities_scenario_S(toy):
    cfg, cells, base = toy
    lc = L.evaluate(cells, cfg, scen_S(cfg, cells, L.baseline(cells, cfg)), base, "middle")
    np.testing.assert_allclose(lc.apps[idx(cells)], S["apps"], rtol=0, atol=1e-9)
    np.testing.assert_allclose(lc.admits[idx(cells)], S["admits"], atol=1e-9)
    np.testing.assert_allclose(lc.award_base[idx(cells)], S["award_base"], atol=1e-9)
    np.testing.assert_allclose(lc.award[idx(cells)], S["award"], atol=1e-9)
    np.testing.assert_allclose(lc.incentive[idx(cells)], S["incentive"], atol=1e-9)
    np.testing.assert_allclose(lc.yld[idx(cells)], S["yld"], atol=1e-12)
    np.testing.assert_allclose(lc.enrolled[idx(cells)], S["enrolled"], atol=1e-9)
    m = L.money(lc)
    for k in ("class_n", "merit", "incentive_cost", "need", "gross_y1", "aid", "ntr_y1"):
        assert m[k] == pytest.approx(S[k], abs=1e-6), k
    assert m["discount_entering_y1"] == pytest.approx(S["aid"] / S["gross_y1"], rel=1e-12)
    assert m["avg_aid"] == pytest.approx(S["aid"] / S["class_n"], rel=1e-12)
    k = L.kpis(lc)
    assert k["full_tuition_n"] == pytest.approx(S["full_tuition_n"], abs=1e-9)
    assert k["no_merit_award_n"] == pytest.approx(S["no_merit_award_n"], abs=1e-9)
    assert k["barbell"] == pytest.approx((S["full_tuition_n"] + S["no_merit_award_n"]) / S["class_n"], rel=1e-12)
    md = risk.median(lc, "score", 166)
    assert md["margin_t"] == pytest.approx(S["margin_166"], abs=1e-9)
    assert md["unscored_count"] == pytest.approx(1.55, abs=1e-9)
    assert k["share_at_or_above_t"][166] == pytest.approx((5.76 + 6.24 + 4.224) / (S["class_n"] - 1.55), rel=1e-12)


def test_identities_scenario_P(toy):
    cfg, cells, base = toy
    lc = L.evaluate(cells, cfg, scen_P(cfg, cells, L.baseline(cells, cfg)), base, "middle")
    np.testing.assert_allclose(lc.admits[idx(cells)], P["admits"], atol=1e-9)
    np.testing.assert_allclose(lc.award[idx(cells)], P["award"], atol=1e-9)
    np.testing.assert_allclose(lc.yld[idx(cells)], P["yld"], atol=1e-12)
    m = L.money(lc)
    for k in ("class_n", "merit", "incentive_cost", "ntr_y1"):
        assert m[k] == pytest.approx(P[k], abs=1e-6), k


def test_cap_on_award_base(toy):
    """Tuition decrease of 2%: T = 49,000. A lever of 49,500 (below the parent's tuition, so not the full-tuition
    rung) is capped at 49,000; the full-tuition cell follows tuition to 49,000."""
    cfg, cells, base = toy
    b = L.baseline(cells, cfg)
    s = L.derive(b, "cap", cfg, cells, award={"c3": 49500.0}, tuition_increase_pct=-2.0)
    lc = L.evaluate(cells, cfg, s, base, "middle")
    assert lc.tuition == 49000.0
    assert lc.award_base[cells.index("c3")] == 49000.0
    assert lc.award_base[cells.index("c1")] == 49000.0
    assert not s.full_tuition[cells.index("c3")]


def test_cap_on_incentive(toy):
    cfg, cells, base = toy
    b = L.baseline(cells, cfg)
    s = L.derive(b, "inc", cfg, cells, bonus_usd=10000.0)
    lc = L.evaluate(cells, cfg, s, base, "middle")
    i = cells.index("c5")
    assert lc.award[i] == 53000.0 and lc.incentive[i] == 8000.0
    assert (lc.award <= lc.tuition).all() and (lc.incentive >= 0).all()


def test_award_scaling(toy):
    cfg, cells, base = toy
    b = L.baseline(cells, cfg)
    s = L.derive(b, "scaled", cfg, cells, award_scale_with_tuition=True)
    lc = L.evaluate(cells, cfg, s, base, "middle")
    assert lc.award_base[cells.index("c2")] == pytest.approx(10600.0)
    assert lc.award_base[cells.index("c1")] == 53000.0      # full-tuition rung follows tuition either way


def test_full_tuition_override_is_rung(toy):
    """An award override at or above the parent's tuition is the full-tuition rung."""
    cfg, cells, base = toy
    b = L.baseline(cells, cfg)
    s = L.derive(b, "ft", cfg, cells, award={"c2": 53000.0})
    s2 = L.derive(s, "ft2", cfg, cells, tuition_increase_pct=8.0)
    lc = L.evaluate(cells, cfg, s2, base, "middle")
    assert lc.award[cells.index("c2")] == lc.tuition == 54000.0


def test_yield_clip_and_case_slopes(toy):
    cfg, cells, base = toy
    b = L.baseline(cells, cfg)
    s = L.derive(b, "big", cfg, cells, award={"c2": 50000.0})
    i = cells.index("c2")
    for case, slope in (("low", 0.5), ("middle", 1.0), ("high", 1.5)):
        lc = L.evaluate(cells, cfg, s, base, case)
        expect = min(0.60, 0.40 + slope / 100 * 40)
        assert lc.yld[i] == pytest.approx(expect)


def test_integer_rounding(toy):
    cfg = toy_cfg(integer_admits=True, integer_enrolled=True)
    cells = toy_cells(cfg)
    base = response.base_yield(cells, cfg, base_override=toy_override())
    lc = L.evaluate(cells, cfg, scen_S(cfg, cells, L.baseline(cells, cfg)), base, "middle")
    np.testing.assert_allclose(lc.admits[idx(cells)], [24, 30, 24, 30, 26, 5])          # 26.4 rounds to 26
    np.testing.assert_allclose(lc.enrolled, np.floor(lc.admits * lc.yld + 0.5))
