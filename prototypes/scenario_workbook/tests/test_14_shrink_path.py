"""Test 14: shrink path on 20 synthetic worlds.

For each N in class.what_if with N < M: trimmed expected class equals N within 1e-9 (within 1 with integer admits);
for N >= M the rates equal the input rates; admits never rise; the order of section 3 is respected; while the walk
is in cells below t, the share at or above t is non-decreasing as N falls; with floor_rate > 0 or exempt_cells a
shortfall is reported when M - N exceeds R_K; no cell with zero admits produces an error.
"""
import copy

import numpy as np
import pytest

from sw import labels, ledger as L, response, trim
from sw.config import validate

GPA_TRIM = {"blank": 0, "lo": 1, "hi": 2}


def _scen(cells, cfg, pool=1.15):
    # a pool multiplier puts M above the cap so every what-if N is a cut
    return L.derive(L.baseline(cells, cfg), "S", cfg, cells, pool_multiplier=pool)


def _check_order(lc, order):
    cfg = lc.cfg
    t = cfg["score"]["median_thresholds"][0]
    s = lc.cells.score_lo
    below = np.isnan(s) | (np.nan_to_num(s, nan=-1) < t)
    seg = lc.in_segment
    # protected segment cells below t: after all non-segment cells below t, before any cell at or above t
    pos = np.empty(len(order), int)
    pos[order] = np.arange(len(order))
    if seg[below].any() and (~seg & below).any():
        assert pos[seg & below].min() > pos[~seg & below].max()
    if (seg & below).any() and (~below).any():
        assert pos[seg & below].max() < pos[~below].min()
    # within a tier: ascending score (unscored first), then GPA blank, lo, hi, then out, in, segment
    tier = np.where(~below, 2, np.where(seg, 1, 0))
    key = [(tier[i], -np.inf if np.isnan(s[i]) else s[i], GPA_TRIM[lc.cells.gpa_class[i]],
            2 if seg[i] else (0 if lc.cells.residency[i] == "out" else 1)) for i in order]
    assert key == sorted(key)


def test_shrink_path_worlds(syn_cfg, worlds):
    cfg = syn_cfg
    t = cfg["score"]["median_thresholds"][0]
    for seed, cells in worlds.items():
        base = response.base_yield(cells, cfg)
        sc = _scen(cells, cfg)
        lc = L.evaluate(cells, cfg, sc, base, "middle")
        M = float(lc.mu.sum())
        order = trim.trim_order(lc)
        _check_order(lc, order)
        prev_share = None
        walk_below = True
        for N in sorted(cfg["class"]["what_if"], reverse=True):
            tr = trim.trim_rates(lc, N)
            if N >= M:
                np.testing.assert_array_equal(tr["rates"], lc.rate)
                continue
            assert tr["status"] == labels.CT_OK
            lcN = L.evaluate(cells, cfg, L.with_rates(sc, tr["rates"]), base, "middle")
            assert abs(lcN.mu.sum() - N) <= 1e-9, (seed, N)
            assert (lcN.admits <= lc.admits + 1e-12).all()
            sh = tr["removed_share"][order][tr["rm"][order] > 0]
            assert (np.diff(sh) <= 1e-12).all()                      # 1, ..., 1, partial, 0, ..., 0
            cut = order[tr["removed_share"][order] > 0]
            last = cut[-1]
            last_below = np.isnan(cells.score_lo[last]) or cells.score_lo[last] < t
            share = L.kpis(lcN)["share_at_or_above_t"][t]
            if walk_below and last_below:
                if prev_share is not None:
                    assert share >= prev_share - 1e-12
                prev_share = share
            else:
                walk_below = False


def test_class_table_statuses(syn_cfg, worlds):
    cfg = syn_cfg
    cells = worlds[cfg["generator"]["seeds"][0]]
    base = response.base_yield(cells, cfg)
    sc = L.baseline(cells, cfg)
    ct = trim.class_table(cells, cfg, sc, base, Ns=[100, 120, 139, 140, 145])
    M = ct["M"]
    st = {r["N"]: r["status"] for r in ct["class_table"]}
    assert st[145] == labels.CT_ABOVE_CAP
    for N in (100, 120, 139, 140):
        assert st[N] == (labels.CT_NOT_APPLICABLE if N >= M else labels.CT_OK)
    row = next(r for r in ct["class_table"] if r["N"] == 100)
    assert row["f"] == pytest.approx(100 / M)
    assert row["class_mean"] == pytest.approx(100.0)
    assert row["lowest_band_admitted"] is not None and row["admits_cut_by_band"]


def _cfg_with(cfg, **trim_over):
    raw = copy.deepcopy({k: v for k, v in cfg.items() if not k.startswith("_")})
    raw["trim"].update(trim_over)
    return validate(raw)


@pytest.mark.parametrize("kind", ["floor_rate", "exempt"])
def test_shortfall(syn_cfg, worlds, kind):
    cells = worlds[syn_cfg["generator"]["seeds"][1]]
    if kind == "floor_rate":
        cfg = _cfg_with(syn_cfg, floor_rate=0.6)
    else:
        lower = [c for c, s in zip(cells.cell_id, cells.score_lo) if np.isnan(s) or s < 170]
        cfg = _cfg_with(syn_cfg, exempt_cells=lower)
    base = response.base_yield(cells, cfg)
    sc = L.baseline(cells, cfg)
    lc = L.evaluate(cells, cfg, sc, base, "middle")
    M = float(lc.mu.sum())
    for N in (100, 120):
        tr = trim.trim_rates(lc, N)
        R_K = float(tr["R"][-1])
        if M - N > R_K:
            assert tr["status"] == labels.CT_SHORTFALL.format(shortfall=f"{M - N - R_K:.1f}")
            assert tr["shortfall"] == pytest.approx(M - N - R_K)
        else:
            assert tr["status"] == labels.CT_OK
    assert trim.trim_rates(lc, 100)["shortfall"] > 0          # the parameters above leave too little to cut


def test_integer_admits_within_one(syn_cfg, worlds):
    raw = copy.deepcopy({k: v for k, v in syn_cfg.items() if not k.startswith("_")})
    raw["integer_admits"] = True
    cfg = validate(raw)
    for seed in syn_cfg["generator"]["seeds"]:
        cells = worlds[seed]
        base = response.base_yield(cells, cfg)
        sc = _scen(cells, cfg)
        lc = L.evaluate(cells, cfg, sc, base, "middle")
        for N in cfg["class"]["what_if"]:
            if N >= lc.mu.sum():
                continue
            tr = trim.trim_rates(lc, N)
            lcN = L.evaluate(cells, cfg, L.with_rates(sc, tr["rates"]), base, "middle")
            assert abs(lcN.mu.sum() - N) <= 1.0, (seed, N, lcN.mu.sum())
            assert (lcN.admits <= lc.admits).all()
            assert np.allclose(lcN.admits, np.round(lcN.admits))
            uncut = tr["removed_share"] == 0                       # [v0.6.1, R-05]
            np.testing.assert_array_equal(tr["rates"][uncut], lc.rate[uncut])


def test_zero_admit_cells(syn_cfg, worlds):
    cells = worlds[syn_cfg["generator"]["seeds"][2]]
    cfg = syn_cfg
    base = response.base_yield(cells, cfg)
    sc = L.baseline(cells, cfg)
    zero = [cells.cell_id[i] for i in range(cells.n)][:10]
    s0 = L.derive(sc, "z", cfg, cells, admit_rate={c: 0.0 for c in zero})
    lc = L.evaluate(cells, cfg, s0, base, "middle")
    assert (lc.admits == 0).sum() >= 10
    with np.errstate(all="raise"):
        tr = trim.trim_rates(lc, 110)
    assert np.isfinite(tr["rates"]).all()
