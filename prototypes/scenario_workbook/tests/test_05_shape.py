"""Test 5: the asserted shape rows of section 10 hold in at least 90% of 20 seeds; the other rows are reported
(pass share per row written to output/phase1/test05_shape.json)."""
import json
import os

from sw import synth_cells


def test_shape_targets(syn_cfg, worlds, shape_targets, report_dir):
    rows = shape_targets["rows"]
    passes = {r["name"]: 0 for r in rows}
    per_seed = {}
    for seed, cells in worlds.items():
        m = synth_cells.shape_metrics(cells, syn_cfg)
        res = synth_cells.evaluate_targets(m, shape_targets, syn_cfg)
        per_seed[seed] = {k: v[0] for k, v in res.items()}
        for k, (ok, _) in res.items():
            passes[k] += ok
    n = len(worlds)
    summary = {r["name"]: {"asserted": r["asserted"], "pass_share": passes[r["name"]] / n} for r in rows}
    with open(os.path.join(report_dir, "test05_shape.json"), "w") as f:
        json.dump({"summary": summary, "per_seed": per_seed}, f, indent=1)
    need = shape_targets["min_pass_share"]
    failed = {k: v for k, v in summary.items() if v["asserted"] and v["pass_share"] < need}
    assert not failed, failed
