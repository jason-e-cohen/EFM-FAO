"""Guardrail tests: privacy, protected attributes, leakage, and optimizer constraints."""
import json
from pathlib import Path
import numpy as np, pandas as pd, yaml
from efa_fao.pipeline import models as M, optimize as O, prepare as P

OUT = Path("outputs"); CFG = yaml.safe_load(open("config/institution.yaml"))


def test_no_student_level_columns_in_published_outputs():
    for f in OUT.glob("*.csv"):
        if f.name.startswith("validation_"): continue
        cols = set(pd.read_csv(f, nrows=1).columns)
        assert not ({"student_key", "hs_gpa", "act", "need_index"} & cols), f.name


def test_small_cells_are_suppressed():
    k = CFG["privacy"]["min_cell_size"]
    fc = pd.read_csv(OUT / "funnel_cells.csv")
    assert (fc[fc.suppressed == 0].inquiries >= k).all()
    assert fc[fc.suppressed == 1][["inquiries", "enrolled"]].isna().all().all()
    for f, c in [("price_response_curves.csv", "students"), ("projection_segments.csv", "admits"), ("equity_audit.csv", "admits")]:
        assert (pd.read_csv(OUT / f)[c] >= k).all(), f


def test_protected_attributes_never_enter_allocation_models():
    feats = set(M.CAT_BASE) | set(M.NUM_BASE) | {c for c, _ in M.PRICE_SEGMENTS}
    assert not (set(CFG["privacy"]["protected_attributes"]) & feats)


def test_post_decision_aid_never_enters_price_models():
    feats = set(M.CAT_BASE) | set(M.NUM_BASE) | {c for c, _ in M.PRICE_SEGMENTS} | {"net_cost_k"}
    assert not any("disbursed" in f or "accepted" in f or f.startswith("legacy_") for f in feats)


def test_optimizer_respects_budget_cap_and_athletes():
    rng = np.random.default_rng(0); n = 300
    pool = pd.DataFrame({"tuition": 36000.0, "inst_fixed": rng.choice([8000, 14000, 20000], n).astype(float),
                         "disc_k": rng.choice([0, 1, 2, 3], n).astype(float), "athlete": (rng.random(n) < 0.1).astype(int)})
    slope = rng.uniform(0.02, 0.2, n)
    fn = lambda p, d: 1 / (1 + np.exp(-(-1.2 + slope * (np.asarray(d) - p.disc_k.to_numpy()))))
    persist = np.full(n, 3.0)
    cur = O.build_curves(fn, pool, persist, cap=0.75, max_cut_k=3)
    B = 0.8 * (cur["spend"][np.arange(n), pool.disc_k.astype(int)]).sum()
    d, info = O.solve(cur, budget=B)
    ev = O.evaluate(fn, pool, d, persist)
    assert ev["discretionary_spend"] <= B * 1.0001
    assert ((pool.inst_fixed + d * 1000) <= 0.75 * pool.tuition + 1e-6)[pool.athlete == 0].all()
    assert (d[pool.athlete == 1] == pool.disc_k[pool.athlete == 1]).all()
    assert (d >= pool.disc_k - 3 - 1e-9)[pool.athlete == 0].all()


def test_missing_aid_is_not_silently_zero():
    cov = P.pivot_aid(pd.DataFrame({"student_key": ["a"], "component": ["pell"], "known_at_decision": [1],
                                    "offered_amount": [100.0], "disbursed_amount": [np.nan]}), {2025})
    assert "pell" in cov.columns and cov.loc["a", "pell__disbursed"] == 0.0 and cov.loc["a", "pell"] == 100.0


def test_run_metadata_present():
    m = json.load(open(OUT / "model_run.json"))
    assert m["is_synthetic"] is True and len(m["data_sha256"]) == 64 and 0 <= m["live"]["realization_ratio"] <= 1
