"""Test 16: class range and cap. Ledger, risk, trim and generator run at class targets of 100, 110, 120, 130 and 140
(including a world whose expected class is below 140); need_rate is unchanged; P(class > cap) uses the cap; a target
above the cap and a target outside reject_range are rejected; a target outside supported_range carries the notice.
"""
import copy

import numpy as np
import pytest

from sw import labels, ledger as L, response, risk, synth_cells, trim
from sw.config import ConfigError, validate

TARGETS = (100, 110, 120, 130, 140)


@pytest.mark.parametrize("scale", [1.0, 0.85])
def test_targets_under_cap(syn_cfg, scale):
    cfg = syn_cfg
    cells = synth_cells.generate(cfg, cfg["generator"]["seeds"][3], scale=scale)
    base = response.base_yield(cells, cfg)
    b = L.baseline(cells, cfg)
    lb = L.evaluate(cells, cfg, b, base, "middle")
    M = float(lb.mu.sum())
    if scale < 1:
        assert M < 140 - 10                                    # a world whose expected class is well below 140
    for T in TARGETS:
        s = L.derive(b, f"T{T}", cfg, cells, class_target=float(T))
        assert not s.notices
        lc = L.evaluate(cells, cfg, s, base, "middle")
        assert lc.need_rate == lb.need_rate
        cp = risk.class_probs(lc)
        cf = risk.cf_class(lc.admits, lc.yld, cfg["risk"]["common_shock_sd"], s.class_cap, T, cfg["class"]["band"])
        assert cp["p_class_over_cap"] == pytest.approx(cf["p_class_over_cap"])
        assert cp["p_class_in_band"] == pytest.approx(cf["p_class_in_band"])
        if T < M:
            tr = trim.trim_rates(lc, T)
            lcT = L.evaluate(cells, cfg, L.with_rates(s, tr["rates"]), base, "middle")
            assert float(lcT.mu.sum()) == pytest.approx(T, abs=1e-9)
            assert lcT.need_rate == lb.need_rate
            assert L.money(lcT)["need"] == pytest.approx(lb.need_rate * T)
        else:
            assert np.array_equal(trim.trim_rates(lc, T)["rates"], lc.rate)
    ct = trim.class_table(cells, cfg, b, base)
    assert [r["N"] for r in ct["class_table"]] == cfg["class"]["what_if"]


def test_cap_used_for_probability(syn_cfg, worlds):
    cfg = syn_cfg
    cells = worlds[cfg["generator"]["seeds"][0]]
    base = response.base_yield(cells, cfg)
    b = L.baseline(cells, cfg)
    p_lo = risk.class_probs(L.evaluate(cells, cfg, L.derive(b, "a", cfg, cells, class_cap=140.0), base, "middle"))
    p_hi = risk.class_probs(L.evaluate(cells, cfg, L.derive(b, "b", cfg, cells, class_cap=150.0, class_target=140.0),
                                       base, "middle"))
    assert p_hi["p_class_over_cap"] < p_lo["p_class_over_cap"]


def test_target_rejections_and_notice(syn_cfg, worlds):
    cfg = syn_cfg
    cells = worlds[cfg["generator"]["seeds"][0]]
    b = L.baseline(cells, cfg)
    with pytest.raises(ConfigError):
        L.derive(b, "over", cfg, cells, class_target=141.0)                 # above the cap
    with pytest.raises(ConfigError):
        L.derive(b, "reject", cfg, cells, class_target=80.0)                # below reject_range (84 to 154)
    s = L.derive(b, "notice", cfg, cells, class_target=95.0)                # inside reject, outside supported
    assert s.notices == [labels.CLASS_TARGET_NOTICE.format(target="95", lo="100", hi="140")]
    raw = copy.deepcopy({k: v for k, v in cfg.items() if not k.startswith("_")})
    raw["class"]["target"] = 150
    with pytest.raises(ConfigError):
        validate(raw)


def test_default_ranges_from_cap(syn_cfg):
    raw = copy.deepcopy({k: v for k, v in syn_cfg.items() if not k.startswith("_")})
    del raw["class"]["supported_range"]
    del raw["class"]["reject_range"]
    cfg = validate(raw)
    assert cfg["class"]["supported_range"] == pytest.approx([98.0, 140.0])
    assert cfg["class"]["reject_range"] == pytest.approx([84.0, 154.0])
