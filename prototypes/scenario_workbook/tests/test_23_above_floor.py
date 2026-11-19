"""Test 23 [v0.6.3, BM-5] (Review_Phase2_2_Plan.md section 4, task 3): segment protection above the floor.

With trim.protect_segment above_floor, on 20 synthetic worlds: no segment cell below score.floor (or unscored) is cut
after a non-segment cell at or above the floor; segment cells from the floor up to the first median threshold t go after
every non-segment cell below t and before any cell at or above t; the walk still reaches each N. below_threshold keeps
the v0.6 order (test 14 passes; checked here against the v0.6 rule written out). In the edge workbook (above_floor),
editing score.floor makes Checks show "rebuild needed".
"""
import copy
import os

import numpy as np
import pytest

from sw import labels, ledger as L, response, trim
from sw.config import validate

GPA_TRIM = {"blank": 0, "lo": 1, "hi": 2}


def _cfg(syn_cfg, mode):
    raw = copy.deepcopy({k: v for k, v in syn_cfg.items() if not k.startswith("_")})
    raw["trim"]["protect_segment"] = mode
    return validate(raw)


def _v06_order(lc):
    """The v0.6 rule (below_threshold), written out independently of sw/trim.py."""
    cells, cfg = lc.cells, lc.cfg
    t = cfg["score"]["median_thresholds"][0]
    keys = []
    for i in range(cells.n):
        s = cells.score_lo[i]
        below = np.isnan(s) or s < t
        tier = (1 if lc.in_segment[i] else 0) if below else 2
        tie = 2 if lc.in_segment[i] else (0 if cells.residency[i] == "out" else 1)
        keys.append((tier, -np.inf if np.isnan(s) else s, GPA_TRIM[cells.gpa_class[i]], tie, i))
    return np.array([k[-1] for k in sorted(keys)])


def _scen(cells, cfg):
    return L.derive(L.baseline(cells, cfg), "S", cfg, cells, pool_multiplier=1.15)


def test_above_floor_order_and_walk(syn_cfg, worlds):
    cfg = _cfg(syn_cfg, "above_floor")
    t = cfg["score"]["median_thresholds"][0]
    fl = cfg["score"]["floor"]
    for seed, cells in worlds.items():
        base = response.base_yield(cells, cfg)
        sc = _scen(cells, cfg)
        lc = L.evaluate(cells, cfg, sc, base, "middle")
        order = trim.trim_order(lc)
        pos = np.empty(cells.n, int)
        pos[order] = np.arange(cells.n)
        s = cells.score_lo
        seg = lc.in_segment
        unscored = np.isnan(s)
        sv = np.nan_to_num(s, nan=-1.0)
        seg_low = seg & (unscored | (sv < fl))                     # trimmed in normal order
        seg_mid = seg & ~unscored & (sv >= fl) & (sv < t)          # protected
        non_ge_floor = ~seg & ~unscored & (sv >= fl)
        non_below_t = ~seg & (unscored | (sv < t))
        at_or_above_t = ~unscored & (sv >= t)
        assert seg_low.any() and seg_mid.any(), seed
        assert pos[seg_low].max() < pos[non_ge_floor].min(), seed
        assert pos[seg_mid].min() > pos[non_below_t].max(), seed
        assert pos[seg_mid].max() < pos[at_or_above_t].min(), seed
        # within the normal tier: ascending score (unscored first), then GPA, then out, in, segment
        tier0 = order[np.isin(order, np.flatnonzero(non_below_t | seg_low))]
        key = [(-np.inf if unscored[i] else s[i], GPA_TRIM[cells.gpa_class[i]],
                2 if seg[i] else (0 if cells.residency[i] == "out" else 1)) for i in tier0]
        assert key == sorted(key)
        M = float(lc.mu.sum())
        for N in cfg["class"]["what_if"]:
            if N >= M:
                continue
            tr = trim.trim_rates(lc, N)
            assert tr["status"] == labels.CT_OK
            lcN = L.evaluate(cells, cfg, L.with_rates(sc, tr["rates"]), base, "middle")
            assert abs(lcN.mu.sum() - N) <= 1e-9


def test_below_threshold_order_unchanged(syn_cfg, worlds):
    for mode in ("below_threshold",):
        cfg = _cfg(syn_cfg, mode)
        for seed, cells in worlds.items():
            base = response.base_yield(cells, cfg)
            lc = L.evaluate(cells, cfg, _scen(cells, cfg), base, "middle")
            np.testing.assert_array_equal(trim.trim_order(lc), _v06_order(lc))


def test_modes_differ_only_in_the_segment_cells_below_the_floor(syn_cfg, worlds):
    """above_floor moves exactly the segment cells below the floor (and unscored ones) out of the protected tier."""
    cells = worlds[syn_cfg["generator"]["seeds"][0]]
    out = {}
    for mode in ("below_threshold", "above_floor", "none"):
        cfg = _cfg(syn_cfg, mode)
        base = response.base_yield(cells, cfg)
        lc = L.evaluate(cells, cfg, _scen(cells, cfg), base, "middle")
        out[mode] = (list(trim.trim_order(lc)), lc)
    lc = out["above_floor"][1]
    s = np.nan_to_num(cells.score_lo, nan=-1.0)
    low = set(np.flatnonzero(lc.in_segment & (s < syn_cfg["score"]["floor"])))
    assert low
    assert out["above_floor"][0] != out["below_threshold"][0] and out["above_floor"][0] != out["none"][0]
    # the protected cells under above_floor are the below_threshold protected cells minus the low ones
    t = syn_cfg["score"]["median_thresholds"][0]
    prot_bt = set(np.flatnonzero(lc.in_segment & (s < t)))
    assert prot_bt - low == set(np.flatnonzero(lc.in_segment & (s >= syn_cfg["score"]["floor"]) & (s < t)))


def test_floor_joins_the_rebuild_check(edge_wb, lo_profile):
    """Edge workbook (above_floor): Checks has the floor row (OK at build); after editing score.floor and
    recalculating it shows 'rebuild needed'. The same edited copy moves percentile target 3's t off the band bounds and
    changes target 4's q: Checks lists the t [v0.6.3, section 0A item A7] and flags the q as 'rebuild needed'."""
    import openpyxl
    from conftest import PHASE2
    from sw import lo
    assert edge_wb["info"]["run"].cfg["trim"]["protect_segment"] == "above_floor"
    chk = "Trim order: score.floor equals its value at build (protect_segment above_floor)"

    def rows(ws):
        return {ws.cell(r, 1).value: ws.cell(r, 3).value for r in range(1, ws.max_row + 1)}
    assert rows(edge_wb["values"]["Checks"])[chk] == "OK"
    wb = openpyxl.load_workbook(edge_wb["path"])
    (sheet, coord), = list(wb.defined_names["in_score_floor"].destinations)
    wb[sheet][coord.replace("$", "")].value = 152
    for name, k, v in (("in_pct_t", 2, 163), ("in_pct_q", 3, 0.2)):
        (sheet, coord), = list(wb.defined_names[name].destinations)
        wb[sheet][coord.replace("$", "")][0][k].value = v
    r0 = rows(edge_wb["values"]["Checks"])
    assert r0["Percentile target 3: t is a band bound (score.bands)"] == "OK"
    assert r0["Percentile target 4: q equals its value at build"] == "OK"
    out = os.path.join(PHASE2, "edge_floor_edit")
    os.makedirs(out, exist_ok=True)
    src = os.path.join(out, "edited.xlsx")
    wb.save(src)
    vals = openpyxl.load_workbook(lo.recalc(src, os.path.join(out, "recalculated"), profile=lo_profile),
                                  data_only=True)
    r1 = rows(vals["Checks"])
    assert r1[chk] == labels.REBUILD_NEEDED.format(build="154")
    assert r1["Percentile target 3: t is a band bound (score.bands)"] == "t 163 is not a band lower bound"
    assert r1["Percentile target 4: q equals its value at build"] == labels.REBUILD_NEEDED.format(build="0.1")
    assert r1["Percentile target 1: t is a band bound (score.bands)"] == "OK"
