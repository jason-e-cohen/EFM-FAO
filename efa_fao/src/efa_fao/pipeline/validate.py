"""Synthetic-only validation against the ground truth (never runs on real client data).

Real engagements validate with the randomized price-test holdout and out-of-time backtests instead.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, brier_score_loss
from ..synth import world
from .models import PriceResponseModel, legacy_replica, legacy_predict
from .optimize import build_curves, solve, evaluate


def truth_fn_factory(truth: pd.DataFrame, pool: pd.DataFrame, b0: float):
    T = truth.loc[pool.student_key].copy(); T["loans_offered"] = pool.loans_offered.to_numpy()
    nd = T.nondisc_gift_known.to_numpy()
    return lambda p_, dk: world.p_enroll(T, b0, nd + np.asarray(dk) * 1000.0)


def match_true_spend(fn_model, fn_truth, pool, persist, cap, target_spend, base_budget, objective="ntr", floor=False):
    cur = build_curves(fn_model, pool, persist, cap, floor)
    lo, hi = 0.2 * base_budget, 3.0 * base_budget
    best = None
    for _ in range(14):
        mid = 0.5 * (lo + hi)
        d, _ = solve(cur, budget=mid, objective=objective)
        sp = evaluate(fn_truth, pool, d, persist)["discretionary_spend"]
        best = (d, mid, sp)
        if abs(sp - target_spend) / target_spend < 0.01: break
        lo, hi = (mid, hi) if sp < target_spend else (lo, mid)
    return best[0], best[1]


def strategy_comparison(models: dict, pool, truth, b0, persist, cap, legacy_rep=None):
    fn_t = truth_fn_factory(truth, pool, b0)
    sq = pool.disc_k.to_numpy(float)
    sq_eval = evaluate(fn_t, pool, sq, persist); target = sq_eval["discretionary_spend"]
    out = {"status_quo": {**sq_eval, "alloc": sq}}
    for name, m in models.items():
        fn = lambda p_, dk, m=m: m.predict_p(p_, dk)
        base_b = evaluate(fn, pool, sq, persist)["discretionary_spend"]
        d, _ = match_true_spend(fn, fn_t, pool, persist, cap, target, base_b)
        pred = evaluate(fn, pool, d, persist)["ntr_multi_year"] - evaluate(fn, pool, sq, persist)["ntr_multi_year"]
        out[name] = {**evaluate(fn_t, pool, d, persist), "alloc": d, "pred_ntr_vs_sq": pred}
    # oracle: knows the truth
    d, _ = match_true_spend(fn_t, fn_t, pool, persist, cap, target, target)
    out["oracle_upper_bound"] = {**evaluate(fn_t, pool, d, persist), "alloc": d}
    # legacy conclusion applied literally: aid effect is ~0, so discretionary aid is not justified
    z = np.where(pool.athlete.to_numpy() == 1, sq, 0.0)
    out["legacy_literal_zero_discretionary"] = {**evaluate(fn_t, pool, z, persist), "alloc": z}
    return out


def recovery_table(truth_slice: pd.DataFrame, tr: pd.DataFrame, est: dict) -> pd.DataFrame:
    rows = []
    te = tr.in_price_test.to_numpy() == 1
    true_all = 100 * truth_slice.true_ame_per_1k.mean(); true_te = 100 * truth_slice.true_ame_per_1k[te].mean()
    rows.append({"method": "Ground truth (synthetic)", "ame_pp_per_1k": true_te, "ci_low": np.nan, "ci_high": np.nan})
    for k, (v, se) in est.items():
        rows.append({"method": k, "ame_pp_per_1k": 100 * v, "ci_low": 100 * (v - 1.96 * se) if se else np.nan,
                     "ci_high": 100 * (v + 1.96 * se) if se else np.nan})
    r = pd.DataFrame(rows); r["truth_in_ci"] = [np.nan] + [bool(a <= true_te <= b) if pd.notna(a) else np.nan for a, b in zip(r.ci_low[1:], r.ci_high[1:])]
    return r


def holdout_accuracy(models: dict, ho: pd.DataFrame, legacy_rep) -> pd.DataFrame:
    y = ho.enrolled.to_numpy(float); rows = []
    for name, m in models.items():
        p = m.predict_p(ho); rows.append({"model": name, "auc": roc_auc_score(y, p), "brier": brier_score_loss(y, p), "mean_pred": p.mean(), "mean_actual": y.mean(), "decision_time_valid": True})
    ftf = ho[ho.student_type == "First-time freshman"]
    pl = legacy_predict(legacy_rep, ftf)
    rows.append({"model": "legacy_replica (uses post-enrollment disbursed aid)", "auc": roc_auc_score(ftf.enrolled, pl), "brier": brier_score_loss(ftf.enrolled, pl),
                 "mean_pred": pl.mean(), "mean_actual": ftf.enrolled.mean(), "decision_time_valid": False})
    return pd.DataFrame(rows)
