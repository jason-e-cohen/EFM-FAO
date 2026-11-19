"""Test 4: closed form against simulation on synthetic worlds. One Baseline-derived scenario on each of the 20 worlds
(seeds in config/synthetic.yaml), each with a pool multiplier, a bonus and a yield shift drawn from that file's
ranges. Class, median and NTR probabilities within 0.02; medians at rho 1.0 and 0.5. [v0.6.3, BM-1] Percentile
targets (the config's, plus q = 0.75 at 167) within 0.02 at rho 1.0 and 0.5.

Class and NTR are compared at rho 1 only: their closed forms have one common shock (section 5); rho applies to the
two groups of a median threshold."""
import json
import os

import numpy as np

from sw import ledger as L, mc, response, risk, synth_cells


def test_closed_form_vs_simulation(syn_cfg, worlds, report_dir):
    cfg = syn_cfg
    t4 = cfg["test4"]
    tol = t4["tolerance"]
    draws = t4["draws"]
    s = cfg["risk"]["common_shock_sd"]
    band = cfg["class"]["band"]
    rows = []
    worst = {}
    for seed, cells in worlds.items():
        base = response.base_yield(cells, cfg)
        d = synth_cells.scenario_draws(cfg, seed)
        sc = L.derive(L.baseline(cells, cfg), f"t4-{seed}", cfg, cells, bonus_scope=t4["bonus_scope"], **d)
        lc = L.evaluate(cells, cfg, sc, base, "middle")
        A, y = lc.admits, lc.yld
        M = float(lc.mu.sum())
        n = risk.cf_ntr(A, y, lc.w, s, lc.specialty, None)
        weights = {"class": np.ones(cells.n), "ntr": lc.w}
        sim = mc.simulate(A, y, s, weights, draws, seed=seed)
        cls, ntr = sim["class"], sim["ntr"] - lc.specialty
        checks = []
        for cap in (cfg["class"]["cap"], round(M) - 10, round(M), round(M) + 10):
            cf = risk.cf_class(A, y, s, cap, cap, band)
            checks.append((f"p_class_over_{cap}", cf["p_class_over_cap"], float((cls > cap).mean())))
            checks.append((f"p_class_within_{band}_of_{cap}", cf["p_class_in_band"],
                           float((np.abs(cls - cap) <= band).mean())))
        for z in (-1.0, 0.0, 1.0):
            tgt = n["ntr_mean"] + z * n["ntr_sd"]
            cf = risk.cf_ntr(A, y, lc.w, s, lc.specialty, tgt)["p_ntr_y1_ge_target"]
            checks.append((f"p_ntr_ge_mean{z:+.0f}sd", cf, float((ntr >= tgt).mean())))
        tgt = cfg["ntr_target"]
        checks.append(("p_ntr_ge_config_target", risk.cf_ntr(A, y, lc.w, s, lc.specialty, tgt)["p_ntr_y1_ge_target"],
                       float((ntr >= tgt).mean())))
        for meas, t in risk.median_targets(cfg):
            g = risk.median_signs(cells, cfg, meas, t)
            for rho in (1.0, 0.5):
                groups = None if rho >= 1 else (g > 0)
                sm = mc.simulate(A, y, s, {"m": g}, draws, seed=seed + 7, groups=groups, rho=rho)["m"]
                checks.append((f"p_median_{meas}_{t}_rho{rho}", risk.cf_median(A, y, g, s, rho)["p"],
                               float((sm >= 0).mean())))
        # [v0.6.3, BM-1] percentile targets: integer weights m and -(n - m), so the event m G+ >= (n - m) G- is exact
        from sw import config as C
        for q, t in risk.pct_targets(cfg) + [(0.75, 167)]:
            g = risk.median_signs(cells, cfg, "score", t)
            n_ = C.pct_lattice_n(q)
            m_ = int(round(q * n_))
            wq = np.where(g > 0, m_, np.where(g < 0, -(n_ - m_), 0))
            for rho in (1.0, 0.5):
                groups = None if rho >= 1 else (g > 0)
                sm = mc.simulate(A, y, s, {"m": wq}, draws, seed=seed + 11, groups=groups, rho=rho)["m"]
                checks.append((f"p_pct_q{q:g}_{t}_rho{rho}", risk.cf_pct(A, y, g, q, s, rho)["p"],
                               float((sm >= 0).mean())))
        for name, cf, sm in checks:
            gap = abs(cf - sm)
            key = name.split("_of_")[0].split("_over_")[0] if "class" in name else name
            worst[key] = max(worst.get(key, 0.0), gap)
            rows.append({"seed": seed, "check": name, "closed": cf, "sim": sm, "gap": gap, **d})
    with open(os.path.join(report_dir, "test04_cf_vs_sim.json"), "w") as f:
        json.dump({"worst_gap_by_check": worst, "rows": rows}, f, indent=1)
    bad = [r for r in rows if r["gap"] > tol]
    assert not bad, bad[:5]
