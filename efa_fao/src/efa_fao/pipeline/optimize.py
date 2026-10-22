"""Financial aid optimization: choose a discretionary award level for each admitted student.

Objective  : expected multi-year net tuition revenue (NTR), or expected enrolled headcount.
Constraints: expected discretionary spend <= budget; optional minimum expected class size;
             optional cap on institutional discount rate; per-student cap on total institutional aid;
             athletes keep their current packages; optional "no reductions" floor for offers already out.
Method     : multiple-choice knapsack solved exactly as a MILP (HiGHS via scipy.optimize.milp).
Only non-protected features reach the response model, so the allocation cannot use race or gender.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import csr_matrix

LEVELS_K = np.arange(0, 13)          # discretionary award in $K, step $1,000
DEFAULT_MAX_CUT_K = None            # guardrail: max reduction ($K) versus the current award; set from config


def persistence_factor(r: np.ndarray, years: int) -> np.ndarray:
    return sum(np.power(r, t) for t in range(years))


def build_curves(prob_fn, pool: pd.DataFrame, persist: np.ndarray, cap: float, floor_current=False, max_cut_k=None):
    n, K = len(pool), len(LEVELS_K)
    P = np.column_stack([prob_fn(pool, np.full(n, float(k))) for k in LEVELS_K])
    d = LEVELS_K * 1000.0
    net_tuition = pool.tuition.to_numpy()[:, None] - pool.inst_fixed.to_numpy()[:, None] - d[None, :]
    ntr = P * net_tuition * persist[:, None]
    spend = P * d[None, :]                                  # aid is paid only if the student enrolls
    allowed = (pool.inst_fixed.to_numpy()[:, None] + d[None, :]) <= cap * pool.tuition.to_numpy()[:, None]
    cur = np.clip(np.round(pool.disc_k.to_numpy()).astype(int), 0, LEVELS_K[-1])
    mc = DEFAULT_MAX_CUT_K if max_cut_k is None else max_cut_k
    if floor_current:
        allowed &= LEVELS_K[None, :] >= cur[:, None]
    elif mc is not None:
        allowed &= LEVELS_K[None, :] >= (cur - mc)[:, None]
    ath = (pool.athlete == 1).to_numpy()
    allowed[ath] = False; allowed[ath, cur[ath]] = True      # athletic packages are set elsewhere
    allowed[np.arange(n), cur] |= ~allowed.any(axis=1)       # never leave a student without an option
    return {"P": P, "ntr": ntr, "spend": spend, "allowed": allowed, "ntr1": P * net_tuition}


def solve(curves, budget=None, objective="ntr", min_enroll=None, time_limit=60):
    P, spend, allowed = curves["P"], curves["spend"], curves["allowed"]
    n, K = P.shape
    val = curves["ntr"] if objective == "ntr" else P
    A = csr_matrix((np.ones(n * K), (np.repeat(np.arange(n), K), np.arange(n * K))), shape=(n, n * K))
    cons = [LinearConstraint(A, 1, 1)]
    if budget is not None: cons.append(LinearConstraint(csr_matrix(spend.reshape(1, -1)), -np.inf, budget))
    if min_enroll is not None: cons.append(LinearConstraint(csr_matrix(P.reshape(1, -1)), min_enroll, np.inf))
    res = milp(-val.ravel(), constraints=cons, integrality=np.ones(n * K),
               bounds=Bounds(0, allowed.ravel().astype(float)), options={"time_limit": time_limit, "mip_rel_gap": 1e-4})
    if res.x is None: raise RuntimeError(f"allocation infeasible or failed: {res.message}")
    x = res.x.reshape(n, K)
    return LEVELS_K[x.argmax(axis=1)].astype(float), {"status": int(res.status), "message": res.message}


def evaluate(prob_fn, pool, d_k, persist):
    """Expected outcomes of an allocation d_k (in $K, one per student) under a response function."""
    p = prob_fn(pool, d_k)
    inst = pool.inst_fixed.to_numpy() + d_k * 1000.0
    net_t = pool.tuition.to_numpy() - inst
    enrolled = float(p.sum())
    return {"expected_enrolled": enrolled,
            "ntr_year1": float((p * net_t).sum()),
            "ntr_multi_year": float((p * net_t * persist).sum()),
            "discretionary_spend": float((p * d_k * 1000.0).sum()),
            "discount_rate": float((p * inst).sum() / (p * pool.tuition.to_numpy()).sum())}
