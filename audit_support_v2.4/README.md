# Audit support scripts (S4/S5 re-review audit, October 2026)

Analysis scripts only; synthetic and public data only. All ran without scipy, using the review's `review_support_v2.4/stub/` and `lagr.py`.

| Script | What it does | Used in |
|---|---|---|
| `voi5.py` | Generalized value-of-information engine: K position bands, one-logit-slope or one-pp-slope response, class bands, median targets, priors, one-year bonus, capped vs uncapped cost. Reproduces `voi2.py`/`evpi.py`/`table.py` exactly with the 2-band pool. | Task 1, Task 2 |
| `run_task1.py` → `task1_rows.json` | Verdict grid at N = 650 across pools, class bands, priors, targets, bonus types, rules | Task 1 |
| `t2_lakeshore.py` | Lakeshore (v2 backtest) two-sided vs one-sided rule at anchor SE 0.30/0.46/0.70/1.0, budgets 1x and 0.75x, anchors 1.14/0.8/0.6 (env vars MID, SES, BF). Paths point at a scratch copy at /tmp/work as in the review's scripts. | Task 2 |
| `desim2.py` | Re-runs the four price-test designs, 300 replications, reporting the AME at received doses and at status-quo awards, the logit slope, and a test-status (staff behaviour) effect of ±0.10 logit | Task 4 |
| `*_rerun.out` | Outputs from re-running the review's own scripts unchanged | Task 1, 4, 5 |
