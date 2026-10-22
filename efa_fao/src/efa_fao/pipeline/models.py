"""Estimators for the improved EFA + FAO methodology.

  legacy_replica   : what the prior engagements did (logit, aid in $K, bundled aid, MEMs). Kept as a baseline.
  PriceResponseModel("observational") : controlled logit with heterogeneous price terms.
  experiment_estimate : randomized bonus-aid arm (unbiased, noisy).
  rd_estimate      : regression discontinuity at merit-grid thresholds (unbiased locally, noisy).
  PriceResponseModel("anchored")  : observational shape, experiment-calibrated level (recommended).

Pure numpy/scipy so the pipeline has no heavy dependencies and every number is auditable.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.special import expit

CAT_BASE = ["student_type", "residency", "source_category", "program_area", "gpa_band", "act_band", "need_band", "lead_band"]
NUM_BASE = ["first_gen", "athlete", "campus_visit", "engagement_cap", "loans_k"]
PRICE_SEGMENTS = [("need_band", "Highest need"), ("need_band", "High need"), ("need_band", "Moderate need"),
                  ("need_band", "No FAFSA"), ("residency", "Out-of-state"), ("residency", "International"),
                  ("student_type", "Transfer"), ("first_gen", 1), ("athlete", 1), ("gpa_hi", 1)]


def fit_logit(X, y, offset=None, l2=1e-3, cluster=None, max_iter=100):
    n, k = X.shape
    off = np.zeros(n) if offset is None else np.asarray(offset, float)
    pen = np.full(k, l2); pen[0] = 0.0
    beta = np.zeros(k); ybar = np.clip(y.mean(), 1e-4, 1 - 1e-4)
    beta[0] = np.log(ybar / (1 - ybar)) - off.mean()

    def ll(bt):
        e = X @ bt + off
        return float(np.sum(y * e - np.logaddexp(0, e)) - 0.5 * np.sum(pen * bt ** 2))
    cur = ll(beta)
    for _ in range(max_iter):
        p = expit(X @ beta + off); w = p * (1 - p) + 1e-9
        g = X.T @ (y - p) - pen * beta
        H = (X * w[:, None]).T @ X + np.diag(pen)
        step = np.linalg.solve(H, g); t = 1.0
        while t > 1e-6:
            cand = beta + t * step; val = ll(cand)
            if val >= cur - 1e-10: break
            t *= 0.5
        beta, cur = cand, val
        if np.max(np.abs(t * step)) < 1e-9: break
    p = expit(X @ beta + off); w = p * (1 - p) + 1e-9
    Hinv = np.linalg.inv((X * w[:, None]).T @ X + np.diag(pen))
    sc = X * (y - p)[:, None]
    if cluster is None:
        meat = sc.T @ sc; G = n
    else:
        cs = pd.DataFrame(sc).groupby(np.asarray(cluster)).sum().to_numpy(); meat = cs.T @ cs; G = len(cs)
    cov = Hinv @ meat @ Hinv * (G / max(G - 1, 1))
    return {"beta": beta, "cov": cov, "se": np.sqrt(np.diag(cov)), "n": n}


class Design:
    """Deterministic design matrix: fixed levels, fixed reference, optional price block."""

    def __init__(self, cats, nums, segments=(), price_var="net_cost_k"):
        self.cats, self.nums, self.segments, self.price_var = list(cats), list(nums), list(segments), price_var

    def fit(self, df):
        self.levels = {c: list(df[c].value_counts().index) for c in self.cats}   # first = reference (most common)
        self.names = ["intercept"] + self.nums
        for c in self.cats: self.names += [f"{c}={l}" for l in self.levels[c][1:]]
        self.n_base = len(self.names)
        self.price_names = [self.price_var] + [f"{self.price_var}:{c}={v}" for c, v in self.segments]
        return self

    def base(self, df):
        cols = [np.ones(len(df))] + [df[c].to_numpy(float) for c in self.nums]
        for c in self.cats:
            v = df[c].to_numpy()
            cols += [(v == l).astype(float) for l in self.levels[c][1:]]
        return np.column_stack(cols)

    def seg(self, df):
        return np.column_stack([np.ones(len(df))] + [(df[c].to_numpy() == v).astype(float) for c, v in self.segments])

    def full(self, df):
        return np.column_stack([self.base(df), self.seg(df) * df[self.price_var].to_numpy(float)[:, None]])


class PriceResponseModel:
    """p(enroll | student, discretionary aid).

    mode='observational': controlled logit with heterogeneous price terms (biased by unobserved fit).
    mode='anchored'     : level set by design-based evidence (experiment + RD, inverse-variance pooled);
                          relative sensitivity pattern borrowed from the observational model, shrunk toward
                          uniform by its estimated reliability (kappa).
    """

    def __init__(self, mode="anchored"):
        self.mode = mode; self.lam = 1.0; self.kappa = 1.0; self.sbar = 0.0; self.anchor = None

    def init_design(self, train):
        self.d = Design(CAT_BASE, NUM_BASE, PRICE_SEGMENTS).fit(train)
        return self

    # --- helpers -------------------------------------------------------------------------
    def _s_obs(self, df):
        return -(self.d.seg(df) @ self.price_beta)          # logit change per +$1K aid, observational

    def _s_eff(self, df):
        s = self._s_obs(df)
        return self.lam * np.clip((1 - self.kappa) * self.sbar + self.kappa * s, 0.0, None)

    def _refit_base(self, train, lam):
        self.lam = lam
        off = -self._s_eff(train) * train.net_cost_k.to_numpy(float)
        return fit_logit(self.d.base(train), train.enrolled.to_numpy(float), offset=off, cluster=train.student_key.to_numpy())

    def fit(self, train, anchor_ame=None, kappa=None):
        from scipy.optimize import brentq
        y = train.enrolled.to_numpy(float); cl = train.student_key.to_numpy()
        Xf = self.d.full(train); f = fit_logit(Xf, y, cluster=cl)
        self.obs_fit = f; self.obs_beta = f["beta"]; self.price_beta = f["beta"][self.d.n_base:]
        if self.mode == "observational": return self
        te = (train.in_price_test == 1).to_numpy()
        if anchor_ame is None: anchor_ame = design_anchor(train, GRID)["ame"]
        self.anchor = anchor_ame
        S = self.d.seg(train); Vp = f["cov"][self.d.n_base:, self.d.n_base:]
        s_all = self._s_obs(train); var_i = np.einsum("ij,jk,ik->i", S, Vp, S)
        self.sbar = float(np.mean(s_all[te])) if te.any() else float(np.mean(s_all))
        spread = float(np.var(s_all)); self.kappa_est = float(np.clip(1 - var_i.mean() / max(spread, 1e-12), 0.1, 0.9))
        self.kappa = self.kappa_est if kappa is None else float(kappa)
        pop = te if te.any() else np.ones(len(train), bool)

        def gap(lam):
            g = self._refit_base(train, lam); self.base_beta = g["beta"]
            p0 = self.predict_p(train[pop]); p1 = self.predict_p(train[pop], train.disc_k[pop].to_numpy() + 1.0)
            return float((p1 - p0).mean() - anchor_ame)
        lo, hi = 0.05, 60.0
        glo, ghi = gap(lo), gap(hi)
        self.lam = lo if glo > 0 else (hi if ghi < 0 else brentq(gap, lo, hi, xtol=1e-3))
        g = self._refit_base(train, self.lam); self.base_beta = g["beta"]; self.base_fit = g
        return self

    def _eta(self, df, net_cost_k):
        if self.mode == "observational":
            return self.d.base(df) @ self.obs_beta[:self.d.n_base] + (self.d.seg(df) @ self.price_beta) * net_cost_k
        return self.d.base(df) @ self.base_beta - self._s_eff(df) * net_cost_k

    def predict_p(self, df, disc_k=None):
        nc = df.net_cost_k.to_numpy(float)
        if disc_k is not None: nc = nc - (np.asarray(disc_k, float) - df.disc_k.to_numpy(float))
        return expit(self._eta(df, nc))

    def aid_effect_per_1k(self, df):
        d0 = df.disc_k.to_numpy(float)
        return self.predict_p(df, d0 + 1.0) - self.predict_p(df, d0)

    def coef_table(self):
        if self.mode == "observational":
            return pd.DataFrame({"term": self.d.names + self.d.price_names, "coef": self.obs_fit["beta"], "se": self.obs_fit["se"]})
        return pd.DataFrame({"term": self.d.names, "coef": self.base_beta, "se": self.base_fit["se"]})


GRID = [[3.90, 16000], [3.70, 14000], [3.50, 12000], [3.20, 9000], [0.00, 5000]]


def design_anchor(train, grid=GRID):
    """Inverse-variance pool of the randomized experiment and the pooled RD estimate."""
    E = experiment_estimate(train); R = rd_estimate(train, grid)
    w1, w2 = 1 / E["ame_se"] ** 2, 1 / R["pooled_se"] ** 2
    ame = (w1 * E["ame_per_1k"] + w2 * R["pooled_per_1k"]) / (w1 + w2)
    return {"ame": float(ame), "se": float(1 / np.sqrt(w1 + w2)), "experiment": E, "rd": R,
            "heterogeneity_z": float((E["ame_per_1k"] - R["pooled_per_1k"]) / np.sqrt(E["ame_se"] ** 2 + R["pooled_se"] ** 2))}


def experiment_estimate(train, exp_d=None):
    ex = train[train.in_price_test == 1]
    if exp_d is None:
        exp_d = Design(["need_band", "residency", "gpa_band"], ["first_gen", "campus_visit", "engagement_cap"], [], price_var="offset_k").fit(ex)
    X = exp_d.full(ex); y = ex.enrolled.to_numpy(float)
    f = fit_logit(X, y, cluster=ex.student_key.to_numpy())
    j = exp_d.n_base; b, se = f["beta"][j], f["se"][j]
    eta = X @ f["beta"]
    ame = float((expit(eta) - expit(eta - b)).mean())            # effect of +$1K bonus aid vs none
    ame_se = float(se * (expit(eta) * (1 - expit(eta))).mean())
    # model-free check: difference in means, highest vs lowest offsets
    lo, hi = ex[ex.test_offset == ex.test_offset.min()], ex[ex.test_offset == ex.test_offset.max()]
    slope_lpm = np.polyfit(ex.offset_k, y, 1)[0]
    return {"n": int(len(ex)), "logit_coef": float(b), "logit_se": float(se), "ame_per_1k": ame, "ame_se": ame_se,
            "lpm_slope_per_1k": float(slope_lpm), "enroll_rate_lowest_offset": float(lo.enrolled.mean()),
            "enroll_rate_highest_offset": float(hi.enrolled.mean())}


def rd_estimate(df, grid, bw=0.12):
    sub = df[(df.student_type == "First-time freshman") & (df.athlete == 0) & df.hs_gpa.notna()]
    tiers = sorted(grid, key=lambda r: r[0])
    out = []
    for i in range(1, len(tiers)):
        c, amt = tiers[i]; jump_k = (amt - tiers[i - 1][1]) / 1000.0
        w = sub[(sub.hs_gpa - c).abs() <= bw]
        x = (w.hs_gpa - c).to_numpy(); D = (x >= 0).astype(float); y = w.enrolled.to_numpy(float)
        k = np.clip(1 - np.abs(x) / bw, 0.05, 1)
        X = np.column_stack([np.ones(len(w)), D, x, D * x]); W = k
        A = np.linalg.inv((X * W[:, None]).T @ X); b = A @ (X * W[:, None]).T @ y
        r = y - X @ b; meat = (X * (W * r)[:, None]).T @ (X * (W * r)[:, None]); V = A @ meat @ A
        out.append({"cutoff": c, "award_jump_k": jump_k, "n": int(len(w)), "jump_enroll": float(b[1]),
                    "effect_per_1k": float(b[1] / jump_k), "se_per_1k": float(np.sqrt(V[1, 1]) / jump_k)})
    wts = np.array([1 / o["se_per_1k"] ** 2 for o in out])
    est = float(sum(w * o["effect_per_1k"] for w, o in zip(wts, out)) / wts.sum()); se = float(1 / np.sqrt(wts.sum()))
    return {"by_cutoff": out, "pooled_per_1k": est, "pooled_se": se}


def legacy_replica(train):
    """Faithful-in-spirit rebuild of the prior spec: bundled aid, disbursed non-institutional flag,
    missing EFC recoded to $0, race and gender as predictors, marginal effects at the means."""
    d = train[train.student_type == "First-time freshman"].copy()
    d["race_group"] = np.select([d.race_ethnicity == "White", d.race_ethnicity == "Black or African American",
                                 d.race_ethnicity == "Unknown"], ["White", "Black", "Unknown"], default="Two+/Other")
    cats = ["residency", "race_group", "gender", "gpa_band", "legacy_efc_cat", "lead_band"]
    des = Design(cats, ["athlete", "fafsa_filed", "legacy_inst_k", "legacy_noninst_any"], [], "legacy_inst_k").fit(d)
    d2 = d.copy(); d2["fafsa_filed"] = d2.fafsa_filed.fillna(0)
    des.nums = ["athlete", "fafsa_filed", "legacy_inst_k", "legacy_noninst_any"]
    X = des.base(d2); y = d2.enrolled.to_numpy(float)
    f = fit_logit(X, y, cluster=d2.student_key.to_numpy())
    names = des.names; j_aid = names.index("legacy_inst_k"); j_non = names.index("legacy_noninst_any")
    xbar = X.mean(axis=0); pbar = expit(xbar @ f["beta"])
    mem = lambda j: float(pbar * (1 - pbar) * f["beta"][j])
    return {"design": des, "fit": f, "names": names, "aid_logit": float(f["beta"][j_aid]), "aid_se": float(f["se"][j_aid]),
            "aid_mem_per_1k": mem(j_aid), "noninst_mem": mem(j_non), "noninst_logit": float(f["beta"][j_non]),
            "n": int(len(d2))}


def legacy_predict(rep, df):
    d = df.copy(); d["fafsa_filed"] = d.fafsa_filed.fillna(0)
    d["race_group"] = np.select([d.race_ethnicity == "White", d.race_ethnicity == "Black or African American",
                                 d.race_ethnicity == "Unknown"], ["White", "Black", "Unknown"], default="Two+/Other")
    return expit(rep["design"].base(d) @ rep["fit"]["beta"])


def fit_retention(enrolled_hist):
    d = enrolled_hist[enrolled_hist.retained_y2.notna()]
    des = Design(["residency", "gpa_band", "need_band", "program_area"], ["campus_visit", "first_gen", "athlete"], [], "net_cost_k").fit(d)
    f = fit_logit(des.base(d), d.retained_y2.to_numpy(float), cluster=d.student_key.to_numpy())
    return {"design": des, "beta": f["beta"]}


def predict_retention(ret, df):
    return expit(ret["design"].base(df) @ ret["beta"])


class HybridModel:
    """Predict with the observational model; intervene with the anchored price slopes.

    p(d) = expit( logit p_obs(status-quo award) + s_eff_i * (d - d_status_quo) )
    The forecast keeps the observational model's accuracy at the status quo; counterfactual aid changes
    use only the design-anchored sensitivity, so confounding in the observational price terms never
    leaks into what-if answers.
    """

    def __init__(self, obs: PriceResponseModel, anchored: PriceResponseModel):
        self.obs, self.anc = obs, anchored

    @property
    def d(self): return self.anc.d

    def predict_p(self, df, disc_k=None):
        p0 = np.clip(self.obs.predict_p(df), 1e-6, 1 - 1e-6)
        if disc_k is None: return p0
        delta = np.asarray(disc_k, float) - df.disc_k.to_numpy(float)
        return expit(np.log(p0 / (1 - p0)) + self.anc._s_eff(df) * delta)

    def aid_effect_per_1k(self, df):
        d0 = df.disc_k.to_numpy(float)
        return self.predict_p(df, d0 + 1.0) - self.predict_p(df, d0)
