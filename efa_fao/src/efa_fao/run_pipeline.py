"""End-to-end pipeline: validate -> prepare -> estimate -> backtest -> optimize -> aggregate -> export.

Usage:  PYTHONPATH=src python -m efa_fao.run_pipeline --data data/synthetic --out outputs --boot 40
"""
from __future__ import annotations
import argparse, hashlib, json, time, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import yaml
from scipy.special import expit

from .pipeline import prepare as prep, models as M, optimize as O, aggregate as AG
warnings.filterwarnings("ignore")
SEG_DIMS = ["All", "need_band", "residency", "student_type", "gpa_band", "first_gen", "program_area"]


def jsonable(o):
    if isinstance(o, dict): return {k: jsonable(v) for k, v in o.items() if k != "alloc"}
    if isinstance(o, (list, tuple)): return [jsonable(v) for v in o]
    if isinstance(o, (np.floating, float)): return None if not np.isfinite(o) else float(o)
    if isinstance(o, (np.integer,)): return int(o)
    if isinstance(o, np.ndarray): return jsonable(o.tolist())
    return o


def fit_models(train, base=None, anchor=None, kappa=None):
    mo = M.PriceResponseModel("observational"); ma = M.PriceResponseModel("anchored")
    if base is None: mo.init_design(train); ma.d = mo.d
    else: mo.d = base["mo"].d; ma.d = base["mo"].d
    mo.fit(train)
    A = anchor or M.design_anchor(train)
    ma.fit(train, anchor_ame=A["ame"], kappa=kappa)
    return {"mo": mo, "ma": ma, "hy": M.HybridModel(mo, ma), "anchor": A}


def boot_models(train, base, B, seed=11):
    rng = np.random.default_rng(seed); out = []
    for _ in range(B):
        tb = train.iloc[rng.integers(0, len(train), len(train))].reset_index(drop=True)
        try: out.append(fit_models(tb, base)["hy"])
        except Exception: continue
    return out


def band(vals, lo=5, hi=95): return float(np.percentile(vals, lo)), float(np.percentile(vals, hi))


def eval_with_bands(pool, d, persist, point, boots, sq_d):
    base = O.evaluate(point.predict_p, pool, d, persist)
    draws = [O.evaluate(m.predict_p, pool, d, persist) for m in boots]
    sq_draws = [O.evaluate(m.predict_p, pool, sq_d, persist) for m in boots]
    r = dict(base)
    for k in ["expected_enrolled", "ntr_multi_year", "discretionary_spend", "discount_rate"]:
        lo, hi = band([x[k] for x in draws]); r[f"{k}_p05"], r[f"{k}_p95"] = lo, hi
    r["prob_ntr_gain_vs_status_quo"] = float(np.mean([a["ntr_multi_year"] > b["ntr_multi_year"] for a, b in zip(draws, sq_draws)]))
    return r


def logit_ame_table(df, y, cats, nums, label):
    d = M.Design(cats, nums, [], "none").fit(df); X = d.base(df)
    f = M.fit_logit(X, y.to_numpy(float), cluster=df.student_key.to_numpy()); b = f["beta"]; rows = []
    p = expit(X @ b); w = (p * (1 - p)).mean()
    for j, nm in enumerate(d.names):
        if nm == "intercept": continue
        Xs = X.copy(); Xs[:, j] = 1.0; X0 = X.copy(); X0[:, j] = 0.0
        if "=" in nm:                                    # categorical level vs reference
            c = nm.split("=")[0]; cols = [i for i, n in enumerate(d.names) if n.startswith(c + "=")]
            Xs[:, cols] = 0; Xs[:, j] = 1; X0[:, cols] = 0
        ame = float((expit(Xs @ b) - expit(X0 @ b)).mean()); se = float(f["se"][j] * w)
        rows.append({"stage": label, "term": nm, "ame_pp": 100 * ame, "ci_low_pp": 100 * (ame - 1.96 * se), "ci_high_pp": 100 * (ame + 1.96 * se)})
    return pd.DataFrame(rows)


def category_ame_boot(boots, df, cols):
    rows = []
    for c in cols:
        if pd.api.types.is_numeric_dtype(df[c]): ref, levels = 0, [1]
        else:
            vc = list(df[c].value_counts().index); ref, levels = vc[0], vc[1:]
        for l in levels:
            diffs = []
            for m in boots:
                a, b = df.copy(), df.copy(); a[c] = l; b[c] = ref
                diffs.append((m.obs.predict_p(a) - m.obs.predict_p(b)).mean())
            rows.append({"stage": "Admit to enroll (associational)", "term": f"{c}={l} vs {ref}", "ame_pp": 100 * np.mean(diffs),
                         "ci_low_pp": 100 * np.percentile(diffs, 2.5), "ci_high_pp": 100 * np.percentile(diffs, 97.5)})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/institution.yaml"); ap.add_argument("--data", default="data/synthetic")
    ap.add_argument("--out", default="outputs"); ap.add_argument("--boot", type=int, default=40)
    ap.add_argument("--no-validate", action="store_true")
    a_ = ap.parse_args(); t0 = time.time()
    cfg = yaml.safe_load(open(a_.config)); out = Path(a_.out); out.mkdir(parents=True, exist_ok=True)
    cap = cfg["aid_policy"]["max_total_institutional_discount"]; K = cfg["privacy"]["min_cell_size"]
    hold_y, live_y = cfg["cycle"]["holdout_cohort"], cfg["cycle"]["live_cohort"]; yrs = cfg["objective"]["persistence_years"]
    O.DEFAULT_MAX_CUT_K = cfg["aid_policy"].get("max_cut_per_student_k")
    w = lambda df, n: df.to_csv(out / n, index=False)

    tabs = prep.load_tables(a_.data); tabs, qa = prep.validate_and_clean(tabs, cfg)
    adm = prep.build_admit_frame(tabs, cfg)
    train = adm[(adm.cohort < hold_y) & adm.enrolled.notna()].reset_index(drop=True)
    ho = adm[adm.cohort == hold_y].reset_index(drop=True)
    full_train = adm[(adm.cohort <= hold_y) & adm.enrolled.notna()].reset_index(drop=True)
    live = adm[adm.cohort == live_y].reset_index(drop=True)
    realization = 0.5   # default haircut when no backtest against ground truth is possible (replace with price-test policy evaluation)
    synthetic = (Path(a_.data) / "truth_admits.csv").exists() and cfg["institution"].get("is_synthetic") and not a_.no_validate
    meta = {}

    # ---------------- 1. Backtest-era fit (train on cohorts before the holdout) -------------------------------
    print("fit (backtest era)"); fb = fit_models(train)
    legacy = M.legacy_replica(train)
    ret_bt = M.fit_retention(train[train.enrolled == 1]); persist_ho = O.persistence_factor(M.predict_retention(ret_bt, ho), yrs)
    A = fb["anchor"]; E, R = A["experiment"], A["rd"]
    meta["anchor"] = {"ame_pp_per_1k": 100 * A["ame"], "se_pp": 100 * A["se"], "experiment_pp": 100 * E["ame_per_1k"],
                      "experiment_se_pp": 100 * E["ame_se"], "experiment_n": E["n"], "rd_pp": 100 * R["pooled_per_1k"],
                      "rd_se_pp": 100 * R["pooled_se"], "heterogeneity_z": A["heterogeneity_z"], "lambda": fb["ma"].lam,
                      "kappa": fb["ma"].kappa, "rd_by_cutoff": R["by_cutoff"]}
    meta["legacy_replica"] = {k: v for k, v in legacy.items() if k in ["aid_logit", "aid_se", "aid_mem_per_1k", "noninst_mem", "n"]}
    meta["observational_ame_pp"] = float(100 * fb["mo"].aid_effect_per_1k(train).mean())

    # ---------------- 2. Synthetic validation against ground truth --------------------------------------------
    if synthetic:
        from .pipeline import validate as V
        print("validate vs truth")
        truth = pd.read_csv(Path(a_.data) / "truth_admits.csv").set_index("student_key"); b0 = json.load(open(Path(a_.data) / "world_meta.json"))["b0"]
        ts = truth.loc[train.student_key]
        est = {"Legacy replica (MEM, bundled aid)": (legacy["aid_mem_per_1k"], 1.96 * 0 + legacy["aid_se"] * 0.16),
               "Controlled observational logit": (float(fb["mo"].aid_effect_per_1k(train)[train.in_price_test == 1].mean()), 0.0),
               "Randomized price test": (E["ame_per_1k"], E["ame_se"]), "Merit-grid regression discontinuity": (R["pooled_per_1k"], R["pooled_se"]),
               "Anchor (experiment + RD pooled)": (A["ame"], A["se"]),
               "Hybrid model (recommended)": (float(fb["hy"].aid_effect_per_1k(train)[train.in_price_test == 1].mean()), 0.0)}
        rec = V.recovery_table(ts, train, est); w(rec, "validation_recovery.csv")
        acc = V.holdout_accuracy({"observational": fb["mo"], "hybrid (recommended)": fb["hy"]}, ho, legacy); w(acc, "validation_holdout_accuracy.csv")
        models = {"observational_optimizer": fb["mo"], "hybrid_optimizer (recommended)": fb["hy"]}
        for kp in [0.0, 0.5, 0.9]:
            models[f"hybrid_optimizer_kappa_{kp}"] = M.HybridModel(fb["mo"], fit_models(train, fb, A, kappa=kp)["ma"])
        S = V.strategy_comparison(models, ho, truth, b0, persist_ho, cap, legacy)
        base = S["status_quo"]; rows = []
        for k, v in S.items():
            rows.append({"strategy": k, "expected_enrolled": v["expected_enrolled"], "enrolled_vs_status_quo": v["expected_enrolled"] - base["expected_enrolled"],
                         "ntr_multi_year": v["ntr_multi_year"], "ntr_vs_status_quo": v["ntr_multi_year"] - base["ntr_multi_year"],
                         "ntr_vs_status_quo_pct": 100 * (v["ntr_multi_year"] / base["ntr_multi_year"] - 1),
                         "discretionary_spend": v["discretionary_spend"], "discount_rate": v["discount_rate"],
                         "model_predicted_ntr_vs_status_quo": v.get("pred_ntr_vs_sq", np.nan)})
        bt = pd.DataFrame(rows); w(bt, "validation_strategy_backtest.csv")
        r0 = bt[bt.strategy == "hybrid_optimizer (recommended)"].iloc[0]
        realization = float(np.clip(r0.ntr_vs_status_quo / r0.model_predicted_ntr_vs_status_quo, 0.0, 1.0))
        te = (train.in_price_test == 1).to_numpy()
        seg = train.assign(est=fb["hy"].aid_effect_per_1k(train), obs=fb["mo"].aid_effect_per_1k(train), truth=ts.true_ame_per_1k.to_numpy())
        segrows = []
        for d in ["need_band", "residency", "student_type"]:
            g = (100 * seg.groupby(d)[["est", "obs", "truth"]].mean()).reset_index().rename(columns={d: "segment"}); g.insert(0, "dimension", d); segrows.append(g)
        w(pd.concat(segrows), "validation_segment_recovery.csv")
        meta["validation"] = {"true_ame_pp_train": float(100 * ts.true_ame_per_1k.mean()), "hybrid_corr_with_truth": float(np.corrcoef(seg.est, seg.truth)[0, 1])}

    # ---------------- 3. Final fit on all history; live-cycle projections & optimization ----------------------
    print("final fit + bootstrap"); ff = fit_models(full_train); hy = ff["hy"]
    boots = boot_models(full_train, ff, a_.boot); print("boots:", len(boots))
    ret = M.fit_retention(full_train[full_train.enrolled == 1]); persist = O.persistence_factor(M.predict_retention(ret, live), yrs)
    sq = live.disc_k.to_numpy(float); sq_eval = O.evaluate(hy.predict_p, live, sq, persist)
    curves = O.build_curves(hy.predict_p, live, persist, cap)
    scen, allocs = [], {}
    def add(sid, label, obj, d, bud=None, minenr=None):
        r = eval_with_bands(live, d, persist, hy, boots, sq); r.update({"scenario_id": sid, "label": label, "objective": obj, "budget": bud, "min_enrollment": minenr})
        scen.append(r); allocs[sid] = d
    add("status_quo", "Status quo awards", "n/a", sq)
    for mult in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
        d, _ = O.solve(curves, budget=mult * sq_eval["discretionary_spend"], objective="ntr"); add(f"ntr_budget_{mult:g}x", f"Max NTR at {mult:g}x budget", "ntr", d, mult * sq_eval["discretionary_spend"])
    d, _ = O.solve(curves, budget=None, objective="ntr"); add("ntr_unconstrained", "Max NTR, no budget limit", "ntr", d)
    d, _ = O.solve(curves, budget=sq_eval["discretionary_spend"], objective="headcount"); add("headcount_budget_1x", "Max enrollment at 1x budget", "headcount", d, sq_eval["discretionary_spend"])
    me = 1.03 * sq_eval["expected_enrolled"]
    d, _ = O.solve(curves, budget=1.5 * sq_eval["discretionary_spend"], objective="ntr", min_enroll=me); add("ntr_min_class_1p03", "Max NTR, class at least 3% above status quo, 1.5x budget", "ntr", d, 1.5 * sq_eval["discretionary_spend"], me)
    sc = pd.DataFrame(scen)
    sq_ntr = sq_eval["ntr_multi_year"]; sc["ntr_gain_model_pred"] = sc.ntr_multi_year - sq_ntr
    sc["realization_ratio"] = realization; sc["ntr_gain_planning"] = sc.ntr_gain_model_pred * realization
    sc["institution_id"] = cfg["institution"]["id"]; sc["cohort"] = live_y; w(sc, "scenarios.csv")
    rec = allocs["ntr_budget_1x"]
    meta["live"] = {"status_quo": sq_eval, "recommended_id": "ntr_budget_1x", "realization_ratio": realization}

    # response curves and segment projections (with bootstrap bands)
    n = len(live); Pm = np.stack([np.column_stack([m.predict_p(live, np.full(n, float(k))) for k in O.LEVELS_K]) for m in boots])
    Pp = np.column_stack([hy.predict_p(live, np.full(n, float(k))) for k in O.LEVELS_K]); crow = []
    live = live.assign(All="All students"); live["first_gen_lbl"] = live.first_gen.map({1: "First-generation", 0: "Not first-generation"})
    col = lambda dim: {"first_gen": "first_gen_lbl"}.get(dim, dim)
    for dim in SEG_DIMS:
        for val, idx in live.groupby(col(dim)).groups.items():
            ii = live.index.get_indexer(idx)
            if len(ii) < K: continue
            for j, k in enumerate(O.LEVELS_K):
                bd = Pm[:, ii, j].mean(axis=1)
                crow.append({"dimension": dim, "segment": val, "discretionary_award_usd": int(k * 1000), "students": len(ii),
                             "p_enroll": Pp[ii, j].mean(), "p05": np.percentile(bd, 5), "p95": np.percentile(bd, 95)})
    w(pd.DataFrame(crow), "price_response_curves.csv")
    prow, arow = [], []
    for dim in SEG_DIMS:
        for val, idx in live.groupby(col(dim)).groups.items():
            ii = live.index.get_indexer(idx)
            if len(ii) < K: continue
            p_sq, p_rec = hy.predict_p(live.iloc[ii], sq[ii]), hy.predict_p(live.iloc[ii], rec[ii])
            bsq = [m.predict_p(live.iloc[ii], sq[ii]).sum() for m in boots]; brec = [m.predict_p(live.iloc[ii], rec[ii]).sum() for m in boots]
            prow.append({"dimension": dim, "segment": val, "admits": len(ii), "expected_enrolled_status_quo": p_sq.sum(), "sq_p05": np.percentile(bsq, 5), "sq_p95": np.percentile(bsq, 95),
                         "expected_enrolled_recommended": p_rec.sum(), "rec_p05": np.percentile(brec, 5), "rec_p95": np.percentile(brec, 95),
                         "avg_discretionary_status_quo": sq[ii].mean() * 1000, "avg_discretionary_recommended": rec[ii].mean() * 1000,
                         "yield_status_quo": p_sq.mean(), "yield_recommended": p_rec.mean(),
                         "avg_price_sensitivity_pp_per_1k": 100 * hy.aid_effect_per_1k(live.iloc[ii]).mean()})
    w(pd.DataFrame(prow), "projection_segments.csv")
    # equity audit (protected attributes are audit-only; they never enter the models)
    eq = []
    for dim in AG.PROTECTED_DIMS:
        for val, idx in live.groupby(dim).groups.items():
            ii = live.index.get_indexer(idx); sub = live.iloc[ii]
            if len(ii) < K: continue
            for nm, d in [("status_quo", sq), ("recommended", rec)]:
                p = hy.predict_p(sub, d[ii]); inst = sub.inst_fixed.to_numpy() + d[ii] * 1000
                eq.append({"dimension": dim, "group": val, "allocation": nm, "admits": len(ii), "avg_discretionary": d[ii].mean() * 1000,
                           "expected_yield": p.mean(), "expected_discount_rate": float((p * inst).sum() / (p * sub.tuition.to_numpy()).sum()),
                           "share_with_increase": float((d[ii] > sq[ii]).mean()) if nm == "recommended" else np.nan})
    w(pd.DataFrame(eq), "equity_audit.csv")

    # ---------------- 4. EFA (funnel) outputs ------------------------------------------------------------------
    print("funnel outputs")
    students = tabs["students"]; hist_c = cfg["cycle"]["historical_cohorts"]
    w(AG.funnel_cells(students, adm, K, hist_c), "funnel_cells.csv")
    inq = students[(students.first_touch_is_application == 0) & students.cohort.isin(hist_c)].copy()
    g = inq.hs_gpa; inq["gpa_band"] = pd.cut(g, [0, 3.2, 3.5, 3.7, 3.9, 4.01], right=False, labels=["<3.2", "3.2-3.49", "3.5-3.69", "3.7-3.89", "3.9+"]).astype(object).fillna("Unknown")
    inq["lead_band"] = pd.cut(inq.inquiry_lead_days, [0, 240, 365, 540, 100000], right=False, labels=["<240d", "240-364d", "365-539d", "540d+"]).astype(object)
    inq["engagement_cap"] = np.minimum(inq.engagement_touches, 8); inq["act_known"] = inq.act.notna().astype(int)
    d1 = logit_ame_table(inq, inq.applied, ["source_category", "residency", "lead_band", "gpa_band", "program_area"], ["campus_visit", "engagement_cap", "athlete", "first_gen", "act_known"], "Inquiry to application")
    d2 = category_ame_boot(boots[:25], full_train, ["source_category", "residency", "need_band", "gpa_band", "lead_band", "student_type", "campus_visit", "first_gen"])
    drivers = pd.concat([d1, d2], ignore_index=True); drivers["institution_id"] = cfg["institution"]["id"]; w(drivers, "efa_drivers.csv")
    w(hy.anc.coef_table().assign(model="price_response_anchored"), "model_coefficients.csv")
    w(pd.DataFrame(qa["rules"]), "qa_rules.csv")

    # ---------------- 5. Run metadata (lineage) ---------------------------------------------------------------
    h = hashlib.sha256()
    for f in sorted(Path(a_.data).glob("*.csv")):
        if f.name != "truth_admits.csv": h.update(f.read_bytes())
    meta.update({"institution_id": cfg["institution"]["id"], "is_synthetic": bool(cfg["institution"].get("is_synthetic")),
                 "data_sha256": h.hexdigest(), "config_sha256": hashlib.sha256(open(a_.config, "rb").read()).hexdigest(),
                 "bootstrap_draws": len(boots), "train_cohorts": sorted(full_train.cohort.unique().tolist()), "live_cohort": live_y,
                 "qa": qa, "runtime_seconds": round(time.time() - t0, 1),
                 "live_summary": {s["scenario_id"]: {k: s[k] for k in ["expected_enrolled", "ntr_multi_year", "discretionary_spend", "discount_rate", "prob_ntr_gain_vs_status_quo"]} for s in scen}})
    json.dump(jsonable(meta), open(out / "model_run.json", "w"), indent=2)
    print("done in", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
