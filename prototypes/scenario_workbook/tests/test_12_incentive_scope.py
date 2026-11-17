"""Test 12: incentive scope.

- Scope `segment` changes award, merit and incentive cost only in segment cells.
- Scope `residency_out` with no segment cells gives the same awards, yields, class, merit and probabilities as scope
  `segment` with every out-of-state cell placed in the segment, and as the toy answers of test 1 (scenario P).
- Scope `segment` with no segment cells and a positive bonus raises an error; with a zero bonus it does not.
"""
import numpy as np
import pytest

from sw import ledger as L, response, risk
from sw.config import ConfigError
from toy import P, idx, toy_cells, toy_cfg, toy_override


def _setup(mode):
    cfg = toy_cfg()
    cells = toy_cells(cfg, segment_mode=mode)
    base = response.base_yield(cells, cfg, base_override=toy_override())
    return cfg, cells, base


def test_segment_scope_touches_segment_cells_only():
    cfg, cells, base = _setup("one")
    b = L.baseline(cells, cfg)
    s = L.derive(b, "seg", cfg, cells, bonus_usd=6000.0, bonus_scope="segment")
    lb = L.evaluate(cells, cfg, b, base, "middle")
    ls = L.evaluate(cells, cfg, s, base, "middle")
    seg = ls.in_segment
    assert seg.sum() == 1
    changed_award = ls.award != lb.award
    changed_merit = ~np.isclose(ls.enrolled * ls.award, lb.enrolled * lb.award)
    changed_inc = ls.incentive != lb.incentive
    assert not (changed_award & ~seg).any() and changed_award[seg].all()
    assert not (changed_merit & ~seg).any() and changed_merit[seg].all()
    assert not (changed_inc & ~seg).any() and changed_inc[seg].all()


def _scope_outputs(cfg, cells, base, scope):
    s = L.derive(L.baseline(cells, cfg), "P", cfg, cells, pool_multiplier=1.2, bonus_usd=10000.0, bonus_scope=scope)
    lc = L.evaluate(cells, cfg, s, base, "middle")
    out = {"award": lc.award[idx(cells)], "yld": lc.yld[idx(cells)]}
    m = L.money(lc)
    out.update(class_n=m["class_n"], merit=m["merit"], ntr=m["ntr_y1"], incentive_cost=m["incentive_cost"])
    out.update({k: v for k, v in risk.class_probs(lc).items() if k != "labels"})
    for meas, t in risk.median_targets(cfg):
        out[f"p_{meas}_{t}"] = risk.median(lc, meas, t)["p_median_t"]
    out["p_ntr"] = risk.ntr(lc, target=800000)["p_ntr_y1_ge_target"]
    return out


def test_residency_out_equals_segment_all_out_equals_toy():
    cfg_n, cells_n, base_n = _setup("none")
    cfg_a, cells_a, base_a = _setup("all_out")
    a = _scope_outputs(cfg_n, cells_n, base_n, "residency_out")
    b = _scope_outputs(cfg_a, cells_a, base_a, "segment")
    for k in a:
        np.testing.assert_allclose(a[k], b[k], rtol=1e-12, atol=1e-9, err_msg=k)
    np.testing.assert_allclose(a["award"], P["award"])
    np.testing.assert_allclose(a["yld"], P["yld"], atol=1e-12)
    assert a["class_n"] == pytest.approx(P["class_n"])
    assert a["merit"] == pytest.approx(P["merit"])
    assert a["ntr"] == pytest.approx(P["ntr_y1"])
    assert a["incentive_cost"] == pytest.approx(P["incentive_cost"])


def test_segment_scope_without_segment_cells():
    cfg, cells, base = _setup("none")
    b = L.baseline(cells, cfg)
    with pytest.raises(ConfigError):
        L.derive(b, "bad", cfg, cells, bonus_usd=5000.0, bonus_scope="segment")
    s = L.derive(b, "ok", cfg, cells, bonus_usd=0.0, bonus_scope="segment")
    lc = L.evaluate(cells, cfg, s, base, "middle")
    assert (lc.incentive == 0).all()
