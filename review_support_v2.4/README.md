# Support scripts for the v2.4 S4/S5 re-review

Analysis scripts only (not production code). Synthetic data and public ABA 509 data only.

| Script | What it computes | Result used in the review |
|---|---|---|
| `bt.py` (+ `lagr.py`) | Re-runs the v2 backtest for the uniform-slope (kappa 0) policy on the 2026 holdout and evaluates the same allocation at the 10th/50th/90th percentile slope, at the true slope, and with a model-set budget | Predicted gain $0.50M / $0.98M / $1.65M; realized $0.61M; SQ enrollment overpredicted 413.9 vs 388.1; model-budget ratio 0.58 |
| `desim.py`, `chk.py` | 300 replications of four price-test designs on the synthetic eligible pool (2023-2025) | SD of AME: uniform 0.548, 40/20/40 0.438, two-arm 0.391, 40/20/40 analysed on all randomized eligibles 0.287; estimand at status-quo awards 1.31 vs 1.49 at bonus-inclusive awards |
| `voi.py` | Value of information, uncapped scale decision (template A) | Contrast case in Phase 3 section 10 |
| `voi2.py`, `evpi.py`, `table.py` | Value of information with Richmond economics, two position bands, +/-3% class band, median floor, two-sided choice rule | Worked examples in Phase 3 section 10 |

The sandbox had no scipy, so `stub/` supplies `expit`, `brentq`, and a placeholder `milp`; `lagr.py` replaces the MILP with a Lagrangian solver for the single-budget multiple-choice knapsack. It reproduces the repo's backtest (predicted +$0.977M, realized +$0.605M) within 0.1%. Paths in the scripts point to a scratch copy of `efa_fao/`; edit them to rerun.
