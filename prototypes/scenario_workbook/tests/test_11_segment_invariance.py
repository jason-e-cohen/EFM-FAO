"""Test 11: segment merge invariance, and the base-yield pooling values of section 4.

(a) With y0 and a0 inherited from the unsplit cell (response.base_yield's test-only base_override), splitting
out-of-state cells into segment and non-segment cells in any proportion changes no total or probability.
(b) Pooling returns the stated value for cells with 0, 4, 5 and 30 admits, and for a segment pool below and above
30 admits.
"""
import numpy as np
import pandas as pd
import pytest

from sw import CASES, cells as C, ledger as L, response, risk, strip, synth_cells
from toy import toy_cells, toy_cfg, toy_override


def _outputs(cells, cfg, scen, base):
    lc = L.evaluate(cells, cfg, scen, base, "middle")
    out = dict(L.money(lc))
    out.pop("labels")
    k = L.kpis(lc)
    for key in ("apps_total", "admits_total", "admits_out", "full_tuition_n", "no_merit_award_n", "barbell",
                "unscored_count", "enrolled_gpa_hi", "enrolled_below_floor"):
        out[key] = k[key]
    for t, v in k["share_at_or_above_t"].items():
        out[f"share_{t}"] = v
    for key, v in risk.class_dist(lc).items():
        if key != "labels":
            out[key] = v
    for key, v in risk.class_probs(lc).items():
        if key != "labels":
            out[key] = v
    for meas, t in risk.median_targets(cfg):
        md = risk.median(lc, meas, t)
        out[f"margin_{meas}_{t}"] = md["margin_t"]
        out[f"p_{meas}_{t}"] = md["p_median_t"]
        out[f"p05_{meas}_{t}"] = md["p_median_t_rho05"]
    n = risk.ntr(lc, target=out["ntr_y1"] * 0.95)
    out["ntr_sd"] = n["ntr_sd"]
    out["p_ntr"] = n["p_ntr_y1_ge_target"]
    ps = strip.pool_strip(cells, cfg, scen, base)
    for r in ps["pool_strip"]:
        out[f"pool_{r['pool_multiplier']}"] = (r["class_mean"], r["p_median"], r["ntr_mean"])
    return out


def _compare(a, b):
    for k in a:
        va, vb = a[k], b[k]
        np.testing.assert_allclose(np.asarray(va, float), np.asarray(vb, float), rtol=1e-9, atol=1e-7, err_msg=k)


@pytest.mark.parametrize("shares", [(0.3, 0.7, 0.5), (0.05, 0.95, 0.0), (1.0, 0.25, 0.6)])
def test_toy_split_invariance(shares):
    cfg = toy_cfg()
    whole = toy_cells(cfg, segment_mode="none")
    ov = toy_override()
    base_w = response.base_yield(whole, cfg, base_override=ov)
    splits = {cid: (sh, "priority") for cid, sh in zip(("c3", "c4", "c5"), shares)}
    split = C.split_cells(whole, splits, cfg)
    ov_split = {}
    for cid in split.cell_id:
        parent = cid.split("|")[0]
        ov_split[cid] = ov[parent]
    base_s = response.base_yield(split, cfg, base_override=ov_split)
    kw = dict(pool_multiplier=1.3, bonus_usd=8000.0, bonus_scope="residency_out", yield_shift_pts=0.5,
              yield_shift_pts_out=1.0, specialty_usd=2000.0)
    sw_ = L.derive(L.baseline(whole, cfg), "S", cfg, whole, **kw)
    ss_ = L.derive(L.baseline(split, cfg), "S", cfg, split, **kw)
    _compare(_outputs(whole, cfg, sw_, base_w), _outputs(split, cfg, ss_, base_s))


def test_synthetic_world_merge_invariance(syn_cfg, worlds):
    """A generated world (segment cells present) against the same world with segment cells merged back."""
    cfg = syn_cfg
    seed = cfg["generator"]["seeds"][0]
    split = worlds[seed]
    df = split.to_long()
    seg = cfg["segments"][0]["name"]
    df["cell_id"] = df["cell_id"].str.replace(f"-{seg}-", "-", regex=False)
    df["segment"] = ""
    merged_df = df.groupby(["cell_id", "cohort"], as_index=False).agg(
        residency=("residency", "first"), segment=("segment", "first"), score_lo=("score_lo", "first"),
        gpa_class=("gpa_class", "first"), apps=("apps", "sum"), admits=("admits", "sum"),
        award_usd=("award_usd", "first"), enrolled=("enrolled", "sum"))
    merged = C.from_long(merged_df[C.COLUMNS], cfg)
    assert merged.n < split.n
    base_m = response.base_yield(merged, cfg)
    ov = {}
    for cid in split.cell_id:
        i = merged.index(cid.replace(f"-{seg}-", "-"))
        ov[cid] = ({k: base_m.y0[k][i] for k in CASES}, base_m.a0[i])
    base_s = response.base_yield(split, cfg, base_override=ov)
    kw = dict(pool_multiplier=1.25, bonus_usd=6000.0, bonus_scope="residency_out", yield_shift_pts=-0.5)
    sm = L.derive(L.baseline(merged, cfg), "S", cfg, merged, **kw)
    ss = L.derive(L.baseline(split, cfg), "S", cfg, split, **kw)
    _compare(_outputs(merged, cfg, sm, base_m), _outputs(split, cfg, ss, base_s))


# ---------------------------------------------------------------------------------------------------------------
# (b) pooling values

def _pool_cells(cfg, seg_above):
    # id, segment, score, gpa, admits by cohort, enrolled by cohort, award by cohort
    spec = [
        ("A", "", 170.0, "lo", [0, 0, 0], [0, 0, 0], [20000, 20000, 20000]),
        ("B", "", 170.0, "hi", [1, 1, 2], [0, 1, 1], [20000, 22000, 24000]),
        ("C", "", 167.0, "lo", [2, 2, 1], [1, 0, 1], [30000, 30000, 30000]),
        ("D", "", 167.0, "hi", [10, 10, 10], [3, 2, 4], [25000, 30000, 35000]),
        ("S1", "priority", 170.0, "lo", [10, 10, 10] if seg_above else [3, 3, 4],
         [3, 3, 3] if seg_above else [1, 1, 1], [40000, 40000, 40000]),
        ("S2", "priority", 167.0, "hi", [4, 4, 4], [1, 2, 1], [45000, 45000, 45000]),
        # an in-state cell so the residency pools are distinct
        ("I", "", 170.0, "hi", [20, 20, 20], [10, 10, 10], [50000, 50000, 50000]),
    ]
    rows = []
    for cid, seg, sc, gpa, adm, enr, aw in spec:
        res = "in" if cid == "I" else "out"
        for j, coh in enumerate((2024, 2025, 2026)):
            rows.append({"cell_id": cid, "residency": res, "segment": seg, "score_lo": sc, "gpa_class": gpa,
                         "cohort": coh, "apps": 2 * adm[j] + 1, "admits": adm[j], "award_usd": aw[j],
                         "enrolled": enr[j]})
    return C.from_long(pd.DataFrame(rows, columns=C.COLUMNS), cfg)


@pytest.mark.parametrize("seg_above", [False, True])
def test_pooling_values(seg_above):
    cfg = toy_cfg()
    cells = _pool_cells(cfg, seg_above)
    base = response.base_yield(cells, cfg)
    k = 20.0
    slopes = {"low": 0.5, "middle": 1.0, "high": 1.5}
    # non-segment out-of-state upper pool: A, B, C, D -> 39 admits (>= 30), 13 enrolled
    yp_non = 13 / 39
    if seg_above:
        yp_seg = (9 + 4) / (30 + 12)                    # segment pool: 42 admits >= 30
    else:
        yp_seg = (0 + 2 + 2 + 9 + 3 + 4) / (0 + 4 + 5 + 30 + 10 + 12)   # 22 < 30: residency x group pool
    for case, b in slopes.items():
        y0 = dict(zip(cells.cell_id, base.y0[case]))
        assert y0["A"] == pytest.approx(yp_non)                                                  # 0 admits
        cB = 2 / 4 + b / 100 * (24000 - (20000 + 22000 + 2 * 24000) / 4) / 1000
        assert y0["B"] == pytest.approx((4 * cB + k * yp_non) / (4 + k))                         # 4 admits
        assert y0["C"] == pytest.approx((5 * (2 / 5) + k * yp_non) / (5 + k))                     # 5 admits
        cD = 9 / 30 + b / 100 * (35000 - 30000) / 1000
        assert y0["D"] == pytest.approx((30 * cD + k * yp_non) / (30 + k))                        # 30 admits
        nS1 = 30 if seg_above else 10
        eS1 = 9 if seg_above else 3
        assert y0["S1"] == pytest.approx((nS1 * (eS1 / nS1) + k * yp_seg) / (nS1 + k))
        assert y0["S2"] == pytest.approx((12 * (4 / 12) + k * yp_seg) / (12 + k))
    lvl = dict(zip(cells.cell_id, base.pool_level))
    assert lvl["S1"] == ("segment" if seg_above else "residency")
    assert lvl["A"] == "segment"      # (out, blank segment, upper) pool has 39 admits
