"""Headline probabilities at several values of s, on synthetic builds only (O37).

Uses the prototype's own code (prototypes/scenario_workbook/sw/, imported read only) on the
synthetic config and scenario file, changing only risk.common_shock_sd in memory. No client
data, no fixture.

  .venv/bin/python -I analysis/o37_shock_calibration/sensitivity_synthetic.py --s 0.05 0.10 0.15 --seeds 101

Writes results/synthetic_sensitivity.csv (Middle case, every synthetic scenario), or --out.

--s-base B (Nov 23, 2026): treat each --s as s_year and run the prototype at the total
s = sqrt(s_year^2 + B^2) (methodology section 6, two-part form; the prototype's risk code still
reads one total value from risk.common_shock_sd until Phase 5.1).
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import pandas as pd
import yaml

HERE = Path(__file__).resolve().parent
PROTO = HERE.parents[1] / "prototypes" / "scenario_workbook"
sys.path.insert(0, str(PROTO))
from sw import build, risk, synth_cells  # noqa: E402
from sw.config import load as load_config  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--s", type=float, nargs="+", default=[0.05, 0.10, 0.15])
    ap.add_argument("--seeds", type=int, nargs="+", default=[101])
    ap.add_argument("--s-base", type=float, default=0.0)
    ap.add_argument("--out", default="synthetic_sensitivity.csv")
    a = ap.parse_args()
    cfg0 = load_config(str(PROTO / "config" / "synthetic.yaml"))
    specs = yaml.safe_load((PROTO / "config" / "scenarios_synthetic.yaml").read_text())["scenarios"]
    rows = []
    for seed in a.seeds:
        cells = synth_cells.generate(cfg0, seed)
        for s in a.s:
            cfg = copy.deepcopy(cfg0)
            s_tot = (s**2 + a.s_base**2) ** 0.5
            cfg["risk"]["common_shock_sd"] = s_tot
            scen = build.scenarios_from_specs(specs, cells, cfg)
            run = build.make_run(cfg, cells, scen)
            for sc in run.scenarios:
                lc = run.lcs[sc.name]["middle"]
                cd, cp, nt = risk.class_dist(lc), risk.class_probs(lc), risk.ntr(lc)
                row = {"seed": seed, "s": s, "s_base": a.s_base, "s_total": s_tot, "scenario": sc.name, "class_mean": cd["class_mean"],
                       "class_lo90": cd["class_lo90"], "class_hi90": cd["class_hi90"], "class_sd": cd["class_sd"],
                       "p_class_over_cap": cp["p_class_over_cap"], "p_class_in_band": cp["p_class_in_band"],
                       "p_ntr_ge_target": nt.get("p_ntr_y1_ge_target"), "ntr_sd": nt["ntr_sd"]}
                for meas, t in risk.median_targets(cfg):
                    m = risk.median(lc, meas, t)
                    row[f"p_median_{meas}_{t:g}"] = m["p_median_t"]
                    row[f"p_median_{meas}_{t:g}_rho05"] = m["p_median_t_rho05"]
                rows.append(row)
    out = pd.DataFrame(rows)
    (HERE / "results").mkdir(exist_ok=True)
    out.to_csv(HERE / "results" / a.out, index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 30):
        print(out.round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
