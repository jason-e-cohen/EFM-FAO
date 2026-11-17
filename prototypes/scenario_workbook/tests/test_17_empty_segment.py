"""Test 17: a run with no segment cells (as in reproduce mode) produces no NaN, no division error and the
"no segment cells in the data" text in every segment figure."""
import math

import numpy as np

from sw import labels, ledger as L, response, risk, strip, trim
from toy import toy_cells, toy_cfg, toy_override


def _walk(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _walk(v)
    elif isinstance(obj, np.ndarray):
        yield from obj.ravel().tolist()
    else:
        yield obj


def _no_nan(obj):
    for v in _walk(obj):
        if isinstance(v, (float, np.floating)):
            assert not math.isnan(v)


def test_empty_segment():
    cfg = toy_cfg()
    cells = toy_cells(cfg, segment_mode="none")
    base = response.base_yield(cells, cfg, base_override=toy_override())
    b = L.baseline(cells, cfg)
    s = L.derive(b, "S", cfg, cells, pool_multiplier=1.2, bonus_usd=5000.0, bonus_scope="residency_out",
                 segment_goal=5, segment_pool_lift_pct=10.0, yield_shift_pts_segment=2.0)
    with np.errstate(all="raise"):
        for case in ("low", "middle", "high"):
            lc = L.evaluate(cells, cfg, s, base, case)
            seg = L.segment(lc)
            for k, v in seg.items():
                if k != "labels":
                    assert v == labels.NO_SEGMENT_CELLS, k
            assert risk.segment_exact(lc, 5) == labels.NO_SEGMENT_CELLS
            out = [L.money(lc), L.kpis(lc), risk.class_dist(lc), risk.class_probs(lc), risk.ntr(lc, 800000),
                   L.incentive(lc, L.evaluate(cells, cfg, b, base, case)), response.evidence(lc, base, cfg)]
            for meas, t in risk.median_targets(cfg):
                out.append(risk.median(lc, meas, t))
            _no_nan(out)
        lc = L.evaluate(cells, cfg, s, base, "middle")
        _no_nan([strip.tuition(lc), strip.yield_strip(lc), strip.pool_strip(cells, cfg, s, base)])
        ct = trim.class_table(cells, cfg, s, base)
        for row in ct["class_table"]:
            if "segment_enrolled" in row:
                assert row["segment_enrolled"] == labels.NO_SEGMENT_CELLS
        _no_nan([{k: v for k, v in r.items() if k != "median"} for r in ct["class_table"]])
