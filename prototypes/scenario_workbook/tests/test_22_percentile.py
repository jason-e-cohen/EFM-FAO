"""Test 22 [v0.6.3, BM-1] (Review_Phase2_2_Plan.md section 4, task 2): percentile targets on the toy grid.

Hand-computed margins and probabilities at q = 0.10, 0.25, 0.5 and 0.75; at q = 0.5 the probability equals p_median_t
to 1e-12 and the margin is margin_t / 2; the spread band on a hand case; the "approximate" flag; the margin unit (one
swap at the same class size moves the margin by 1; adding k enrollees below t uses k(1 - q)).

Toy Baseline, Middle case (tests/toy.py; tuition 53,000, c1 on the full-tuition rung):
cell  score  admits  award   yield  enrolled  v = A y (1 - y)
c1    170    20      53,000  0.23   4.6       3.542
c2    161    30      10,000  0.40   12.0      7.2
c3    170    20      30,000  0.15   3.0       2.55
c4    161    30      20,000  0.25   7.5       5.625
c5    170    20      45,000  0.10   2.0       1.8
c6    unsc.  5       0       0.30   1.5       (excluded)
At t = 166: G+ = 9.6, G- = 19.5, sum v above = 7.892, below = 12.825; s = 0.10, rho = 1.
"""
import math
from dataclasses import replace

import numpy as np
import pytest

from sw import labels, ledger as L, response, risk
from toy import idx, toy_cells, toy_cfg, toy_override

S_SD = 0.10
GP, GM, VA, VB = 9.6, 19.5, 7.892, 12.825
HAND = {  # q: (n, margin q G+ - (1 - q) G-)
    0.10: (10, 0.10 * GP - 0.90 * GM),          # -16.59
    0.25: (4, 0.25 * GP - 0.75 * GM),           # -12.225
    0.50: (2, 0.50 * GP - 0.50 * GM),           # -4.95
    0.75: (4, 0.75 * GP - 0.25 * GM),           # 2.325
}


def _phi(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _hand_p(q, rho=1.0):
    n, E = HAND[q]
    V = q * q * VA + (1 - q) ** 2 * VB + S_SD ** 2 * (q * q * GP * GP + (1 - q) ** 2 * GM * GM
                                                     - 2 * rho * q * (1 - q) * GP * GM)
    return 1 - _phi((-1 / (2 * n) - E) / math.sqrt(V))


@pytest.fixture(scope="module")
def toy():
    cfg = toy_cfg()
    cells = toy_cells(cfg)
    base = response.base_yield(cells, cfg, base_override=toy_override())
    lc = L.evaluate(cells, cfg, L.baseline(cells, cfg), base, "middle")
    np.testing.assert_allclose(lc.enrolled[idx(cells)], [4.6, 12.0, 3.0, 7.5, 2.0, 1.5], atol=1e-12)
    return cfg, cells, lc


@pytest.mark.parametrize("q", sorted(HAND))
def test_hand_margins_and_probabilities(toy, q):
    cfg, cells, lc = toy
    r = risk.pct(lc, q, 166)
    assert r["margin_q_t"] == pytest.approx(HAND[q][1], abs=1e-12)
    assert r["margin_expected"] == pytest.approx(HAND[q][1], abs=1e-12)
    assert r["expected_below"] == pytest.approx(GM, abs=1e-12)
    assert r["p_pct_q_t"] == pytest.approx(_hand_p(q), abs=1e-12)
    assert r["p_pct_q_t_rho05"] == pytest.approx(_hand_p(q, 0.5), abs=1e-12)
    g = risk.median_signs(cells, cfg, "score", 166)
    assert risk.cf_pct(lc.admits, lc.yld, g, q, S_SD, 1.0)["correction"] == 1 / (2 * HAND[q][0])


def test_q_half_equals_the_median(toy, worlds, syn_cfg):
    cfg, cells, lc = toy
    for t in (170, 166, 165, 161):
        md, pc = risk.median(lc, "score", t), risk.pct(lc, 0.5, t)
        assert pc["p_pct_q_t"] == pytest.approx(md["p_median_t"], abs=1e-12)
        assert pc["p_pct_q_t_rho05"] == pytest.approx(md["p_median_t_rho05"], abs=1e-12)
        assert pc["margin_q_t"] == pytest.approx(md["margin_t"] / 2, abs=1e-12)
    for seed in list(worlds)[:5]:
        c = worlds[seed]
        base = response.base_yield(c, syn_cfg)
        lw = L.evaluate(c, syn_cfg, L.derive(L.baseline(c, syn_cfg), "s", syn_cfg, c, pool_multiplier=1.3), base,
                        "middle")
        for t in syn_cfg["score"]["bands"]:
            md, pc = risk.median(lw, "score", t), risk.pct(lw, 0.5, t)
            assert pc["p_pct_q_t"] == pytest.approx(md["p_median_t"], abs=1e-12)
            assert pc["margin_q_t"] == pytest.approx(md["margin_t"] / 2, abs=1e-9)


def test_unscored_below_rule(toy):
    """Under unscored_in_median 'below', unscored enrollees count below t with weight -(1 - q)."""
    cfg, cells, lc = toy
    cfg_b = toy_cfg(unscored_in_median="below")
    lcb = replace(lc, cfg=cfg_b)
    r = risk.pct(lcb, 0.25, 166)
    assert r["margin_q_t"] == pytest.approx(0.25 * GP - 0.75 * (GM + 1.5), abs=1e-12)
    assert r["expected_below"] == pytest.approx(GM + 1.5, abs=1e-12)


def test_approximate_flag(toy):
    cfg, cells, lc = toy
    assert risk.pct(lc, 0.25, 166)["approximate"] == labels.PCT_APPROX_LABEL          # 19.5 expected below
    big = replace(lc, admits=lc.admits * 2, mu=lc.mu * 2, enrolled=lc.enrolled * 2)  # 39 expected below
    assert risk.pct(big, 0.25, 166)["approximate"] == ""
    assert labels.PCT_APPROX_LABEL == "approximate (fewer than 20 expected below t)"


def test_spread_band_hand_case(toy):
    """Scored enrolled: 9.6 at 170, 19.5 at 161 (29.1). Share below t: 0 for t <= 161, 0.670 for 165 to 170. q = 0.25:
    the largest bound with share at most 0.25 is 161 (band 161 to below 165); q = 0.75: 170 (band 170+). Under 'below'
    the 1.5 unscored count below every t: share below 0 is 0.049, so q = 0.01 finds no band."""
    cfg, cells, lc = toy
    assert risk.pct_band(lc, 0.25) == 161.0
    assert risk.pct_band(lc, 0.75) == 170.0
    assert risk.pct_band(lc, 0.66) == 161.0                     # 19.5 / 29.1 = 0.670 > 0.66
    lcb = replace(lc, cfg=toy_cfg(unscored_in_median="below"))
    assert risk.pct_band(lcb, 0.25) == 161.0
    assert risk.pct_band(lcb, 0.75) == 170.0
    assert risk.pct_band(lcb, 0.01) is None
    assert risk.pct_band(replace(lc, enrolled=lc.enrolled * 0), 0.25) is None
    lows = sorted(float(b) for b in cfg["score"]["bands"])
    assert L._range_text(lows, lows.index(161.0), lows.index(161.0), lambda x: f"{x:g}") == "161 to below 165"
    assert labels.BAND_NOT_SCORE_LABEL == "band, not a score"


def test_spread_band_tie_is_inclusive(toy):
    """R4-08, R4-13 (mutant R02): the spread band holds a bound t when the share below t is at most q, a tie included.
    The toy's share below 165 to 170 is 19.5 / 29.1; at q equal to it exactly the band is 170 (inclusive), not 161 (a
    strict rule). The percentile probability's event is inclusive too: margin 0 holds."""
    cfg, cells, lc = toy
    e, sc = lc.enrolled, cells.score_lo
    scored = ~np.isnan(sc)
    q = float(e[scored & (sc < 170.0)].sum()) / float(e[scored].sum())
    assert risk.pct_band(lc, q) == 170.0
    assert risk.pct_band(lc, q - 1e-12) == 161.0


def test_margin_unit(toy):
    """One swap (an enrollee below t replaced by one at or above t, class size fixed) changes the margin by exactly 1;
    adding k enrollees below t without removing anyone changes it by -k(1 - q)."""
    cfg, cells, lc = toy
    i_c2, i_c1 = cells.index("c2"), cells.index("c1")
    for q in (0.10, 0.25, 0.5, 0.75):
        m0 = risk.pct(lc, q, 166)["margin_q_t"]
        e = lc.enrolled.copy()
        e[i_c2] -= 1
        e[i_c1] += 1
        assert risk.pct(replace(lc, enrolled=e), q, 166)["margin_q_t"] == pytest.approx(m0 + 1, abs=1e-12)
        e = lc.enrolled.copy()
        e[i_c2] += 3
        assert risk.pct(replace(lc, enrolled=e), q, 166)["margin_q_t"] == pytest.approx(m0 - 3 * (1 - q), abs=1e-12)
