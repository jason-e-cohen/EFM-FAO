"""Ground-truth behavioral model for the synthetic institution.

This module is the *data-generating process*. The analytic pipeline must never import it.
It is used only (a) to generate synthetic outcomes and (b) to validate that the pipeline
recovers the truth. Real engagements have no equivalent, which is why the experiment-anchored
estimator exists.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.special import expit

BASE_PRICE_SLOPE = -0.12   # change in log-odds of deposit per +$1,000 net cost, before heterogeneity
PROGRAM_FX = {"Health": 0.30, "STEM": 0.10, "Business": 0.0, "Education": -0.05,
              "Arts & Humanities": -0.10, "Social Sciences": 0.0, "Undecided": -0.35}


def price_multiplier(df: pd.DataFrame) -> np.ndarray:
    m = np.ones(len(df))
    n = df["need_latent"].to_numpy()
    m *= np.where(n > 0.6, 1.55, np.where(n < -0.6, 0.65, 1.0))
    res = df["residency"].to_numpy()
    m *= np.where(res == "Out-of-state", 1.30, np.where(res == "International", 0.70, 1.0))
    m *= np.where(df["first_gen"].to_numpy() == 1, 1.20, 1.0)
    m *= np.where(df["student_type"].to_numpy() == "Transfer", 1.40, 1.0)
    m *= np.where(df["athlete"].to_numpy() == 1, 0.55, 1.0)
    m *= np.where(df["gpa_true"].to_numpy() >= 3.7, 1.10, 1.0)
    return m


def melt_prob(df: pd.DataFrame) -> np.ndarray:
    return (0.05 + 0.04 * (df["residency"].to_numpy() == "Out-of-state")
            + 0.03 * (df["campus_visit"].to_numpy() == 0))


def utility_nonprice(df: pd.DataFrame, b0: float) -> np.ndarray:
    res = df["residency"].to_numpy()
    x = (b0 + 0.85 * df["u"].to_numpy() + 0.45 * df["campus_visit"].to_numpy()
         + 0.12 * np.minimum(df["engagement_touches"].to_numpy(), 8)
         + 0.35 * df["fafsa_filed"].to_numpy())
    x = x + np.where(res == "Out-of-state", -0.55, np.where(res == "International", 0.40, 0.0))
    x = x + 1.4 * df["athlete"].to_numpy() - 0.35 * df["ability"].to_numpy()
    x = x + 0.25 * (df["app_lead_days"].to_numpy() > 150)
    x = x + 2.6 * (df["student_type"].to_numpy() == "Transfer")
    x = x + df["program_area"].map(PROGRAM_FX).to_numpy()
    x = x - 0.015 * df["loans_offered"].to_numpy() / 1000.0
    return x


def p_deposit(df: pd.DataFrame, b0: float, gift_total) -> np.ndarray:
    net_cost_k = (df["coa"].to_numpy() - np.asarray(gift_total)) / 1000.0
    beta = BASE_PRICE_SLOPE * price_multiplier(df)
    return expit(utility_nonprice(df, b0) + beta * net_cost_k)


def p_enroll(df: pd.DataFrame, b0: float, gift_total) -> np.ndarray:
    return p_deposit(df, b0, gift_total) * (1.0 - melt_prob(df))


def true_ame_per_1k(df: pd.DataFrame, b0: float, gift_total) -> np.ndarray:
    """Per-student change in enrollment probability from +$1,000 of gift aid (finite difference)."""
    g = np.asarray(gift_total, dtype=float)
    return p_enroll(df, b0, g + 1000.0) - p_enroll(df, b0, g)


def calibrate_b0(df: pd.DataFrame, gift_total, target: float) -> float:
    from scipy.optimize import brentq
    f = lambda b: p_enroll(df, b, gift_total).mean() - target
    return brentq(f, -30, 30)
