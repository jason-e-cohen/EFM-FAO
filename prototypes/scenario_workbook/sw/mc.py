"""Simulation (tests only; spec section 5, [v0.6, B1-9]).

Per draw, e ~ Normal(1, s); each cell's yield is clip(e x y_c, 0, 1); enrollment ~ Binomial(A_c, clipped yield),
independent across cells given e. With groups and rho < 1, cells in the two groups take shocks e1 and e2 with
correlation rho. Non-integer admits: Binomial(floor(A), p) + Bernoulli(frac(A) x p), as in risk.exact_pmf.
"""
import numpy as np


def simulate(A, y, s, weights, n_draws, seed, groups=None, rho=1.0, chunk=20000):
    """Return {name: array of per-draw sums sum_c weights[name]_c X_c}."""
    rng = np.random.default_rng(seed)
    A = np.asarray(A, float)
    y = np.asarray(y, float)
    n = np.floor(A + 1e-9).astype(np.int64)
    f = A - n
    f[f < 1e-9] = 0.0
    W = {k: np.asarray(v, float) for k, v in weights.items()}
    grp = None if groups is None else np.asarray(groups, bool)
    out = {k: [] for k in W}
    done = 0
    while done < n_draws:
        m = min(chunk, n_draws - done)
        z1 = rng.standard_normal(m)
        if grp is None or rho >= 1.0:
            e = (1 + s * z1)[:, None] * np.ones(len(A))[None, :]
        else:
            z2 = rho * z1 + np.sqrt(1 - rho * rho) * rng.standard_normal(m)
            e = np.where(grp[None, :], (1 + s * z1)[:, None], (1 + s * z2)[:, None])
        p = np.clip(e * y[None, :], 0.0, 1.0)
        x = rng.binomial(n[None, :], p).astype(float)
        if (f > 0).any():
            x += rng.random(p.shape) < f[None, :] * p
        for k, w in W.items():
            out[k].append(x @ w)
        done += m
    return {k: np.concatenate(v) for k, v in out.items()}
