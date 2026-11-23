# Verification Report, October 22, 2026

**Scope:** Phase A2 of `Handoff_S1_Kickoff.md`. Nothing under `efa_fao/src/` was modified. Synthetic and public data only. Failures are reported, not fixed (there were none).
**Environment:** Python 3.12.15 in `.venv/` (conda, git-ignored): numpy, scipy 1.18.1, pandas, statsmodels, scikit-learn, pyyaml, pytest 9.1.1. The repo's MILP calls scipy's HiGHS.

## 1. Guardrail tests

`efa_fao/tests/test_guardrails.py`, run from `efa_fao/` with `PYTHONPATH=src`. Run twice: once against the existing `outputs/`, once after the pipeline regenerated them. Both runs: 7 passed.

| # | Test | Result |
|---|---|---|
| 1 | `test_no_student_level_columns_in_published_outputs` | Pass |
| 2 | `test_small_cells_are_suppressed` | Pass |
| 3 | `test_protected_attributes_never_enter_allocation_models` | Pass |
| 4 | `test_post_decision_aid_never_enters_price_models` | Pass |
| 5 | `test_optimizer_respects_budget_cap_and_athletes` | Pass |
| 6 | `test_missing_aid_is_not_silently_zero` | Pass |
| 7 | `test_run_metadata_present` | Pass |

The tests read the files in `outputs/`, so they check the pipeline's published artifacts, not only the code. The roadmap's "7 passing" claim is now verified. The tests do not cover the lean-model changes in v2.5 (anchor conversion, spend matching, support rule), which do not exist yet.

## 2. Pipeline reproduction

Commands from `efa_fao/README.md`: synthetic data generation (about 5 seconds) and `run_pipeline --boot 40` (87 seconds). The previous `outputs/` were saved first and compared.

| Quantity (quoted in the executive read) | Quoted | Regenerated |
|---|---|---|
| Ground truth AME (points per $1,000) | 1.49 | 1.488 |
| Legacy replica | about 0 | -0.014 |
| Controlled observational logit | +0.19 | +0.190 |
| Price test alone | +0.63 (-0.46 to 1.72) | +0.630 (-0.462 to 1.722) |
| Merit-grid discontinuity | +2.22 (0.63 to 3.81) | +2.217 (0.626 to 3.808) |
| Pooled anchor | +1.14 (0.24 to 2.04) | +1.138 (0.238 to 2.039) |
| v2 recommended: four-year revenue vs status quo | +$0.42M (+1.8%) | +$0.419M (+1.84%) |
| One anchored slope (kappa 0.0) | +$0.60M (+2.7%) | +$0.605M (+2.66%) |
| Perfect-information bound | +$1.37M (+6.0%) | +$1.369M (+6.01%) |
| Legacy applied literally | -$1.26M (-5.6%) | -$1.265M (-5.55%) |
| Observational optimizer | -$0.34M (-1.5%) | -$0.340M (-1.49%) |

All quoted numbers reproduce. Against the earlier saved outputs, every CSV except `scenarios.csv` and `validation_strategy_backtest.csv` matches to 1e-12; those two differ by at most 0.055% and 0.031% (MILP solver tolerance). Not checked here: the quoted forecast AUC (0.833) and the 4% yield overprediction.

## 3. Stubbed scripts re-run with the real solver

The review's and audit's scripts were copied to the session scratch folder with paths changed to this repository and the stub and `lagr.py` removed. The originals in `review_support_v2.4/` and `audit_support_v2.4/` are unchanged. Differences above 1%: **none**.

| Script | Solver path | Comparison | Largest difference |
|---|---|---|---|
| `bt.py` (backtest, p10/p50/p90/truth-level slopes, realized gain) | Real HiGHS MILP replaces the Lagrangian solver | Against `audit_support_v2.4/bt_rerun.out` | 0.58% on realized enrollment change (-1.514 vs -1.522 enrollees). Dollar quantities: 0.06% or less |
| `voi5.py`, `run_task1.py` (37 verdict runs) | None. These scripts use numpy only and never called the stub or the solver | Against `task1_rows.json` | 0 on all verdicts and dollar fields (identical output) |
| `table.py`, `evpi.py` (Richmond worked-example table) | None (numpy only) | Against `*_rerun.out` | Identical |
| `chk.py` | scipy replaces the stub | Against `chk_rerun.out` | Identical |
| `desim.py` | scipy replaces the stub | Against `desim_rerun.out` | Last-digit floating-point only |
| `t2_lakeshore.py` (extra, not requested) | Real MILP replaces `lagr.solve` | Against the audit's Task 2 table | Gain at mid $857k / $834k / $805k, realized $469k / $449k / $422k, as in the audit |
| `desim2.py` (extra) | scipy | No stored baseline | Ran; not compared |

**Backtest detail (kappa 0, 2026 holdout).** Predicted gain at p10 / p50 / p90: $0.503M / $0.977M / $1.648M (stub: $0.502M / $0.978M / $1.649M). Realized gain $604,873 (stub $605,224). Model-set-budget realized gain $523k against a predicted $909k (stub: $523k and $909k). The pipeline's own `validation_strategy_backtest.csv` gives the same predicted $977,118 for kappa 0, so the stub, the real solver and the repo agree.

**What this closes.** The audit's "could not run HiGHS" item (its section 5) is closed for the backtest and the Lakeshore two-sided comparison: the Lagrangian solver reproduces the real solver within 0.1%. The value-of-information results (`voi5.py`, `table.py`) never depended on the solver. They still rest on stylized pools, which this run does not change.

**Scratch outputs** are in `/private/tmp/claude-502/-Users-jasoncohen-projects-EFA-FAO/94997506-1a3a-4b8e-aecc-884fc5ee9f73/scratchpad/rerun/` (`bt_real.out`, `task1_rows.json`, `t2_real.out`, and others). They are not in the repository. Say if you want them copied into `audit_support_v2.4/` as `*_real.out`.

## 4. Observations that are not test failures

1. **Regenerating overwrote `efa_fao/outputs/` and `efa_fao/data/synthetic/*.csv`.** Both are git-ignored (as the handoff specifies). The pre-run outputs were saved to the scratch folder first. Contents are identical to the earlier run except the two files noted above.
2. **Tests depend on `outputs/` existing.** On a fresh clone (outputs ignored), tests 2 and 7 fail until the pipeline has run, and test 1 passes vacuously (it loops over files that do not exist). Tests 3 to 6 read code and, where needed, the synthetic data (also ignored, regenerable); I did not run them from a clean clone. This affects the planned CI (roadmap phase 0), and the `CLAUDE.md` command order reflects it.
3. **`Amendment_Consumer_ZIP_Data_v2.6_draft.md` appeared in the folder during this session** (not created by Phase A, not audited). It proposes unblocking ZIP5 consumer data and a capacity tier in the aid grid, which contradicts methodology section 9 as it stands in v2.5. It was left out of the baseline commit and not edited. `CLAUDE.md` states that v2.5 rules govern until it is adopted.

## 5. Data request: law gaps

`efa_fao/docs/04_data_request_v2.md` (v2.1 text, referred to as v2.3 in the handoff) was not rewritten, as instructed. It has one law mention (LSAT among graduate test scores). A law Tier 1 request cannot be sent against it. Gaps against methodology v2.5:

| # | Gap | Where methodology v2.5 requires it | Current request |
|---|---|---|---|
| 1 | **LSAT, UGPA and position fields.** UGPA, GRE or JD-Next with concordance, the prior three entering classes' distributions (the reference for relative position), and band assignment | Section 2, relative position | "Test scores (... LSAT for graduate programs)" and "GPA", nothing on position, reference classes or JD-Next |
| 2 | **Offer dates and package versions.** Offer release date and batch (for waves), every version for Tier 2, award mode (total institutional scholarship versus supplement), stipends above tuition flagged | Sections 3, 4 (waves), 5 (award mode) | Offer dates "where available" for Tier 1; versions only for Tier 2; no release batch; no stipend flag |
| 3 | **Reason codes on revisions.** Student request, documented competing offer, staff-initiated, appeal | Section 3, decision date and revisions | Only "date and reason for any award revision" under the optional in-cycle export, no code list |
| 4 | **Renewal rule.** Fixed dollars or percentage of tuition at renewal; renewal conditions (GPA, rank, credits); planned tuition increases | Section 3, renewal rule; section 5, persistence | Absent |
| 5 | **Capacity band.** Hard seat cap or soft target; accepted band (±3%, ±5%, ±10%) | Section 4, screen inputs (mandatory per E7) | "Discount and class-size targets" only, no band |
| 6 | **Blinding question.** Can staff deliver a test bonus as a formula line with no test flag in the CRM; who sees award details | Section 4, analysis population (E1) | Absent. The test section says only "please do not adjust other discretionary aid" |

Further gaps seen while reading (not in the handoff's list; judgment calls on whether to add them):
- The price-test section is undergraduate-shaped: arms $0 / $2,000 / $4,000 and strata of need band by residency. Methodology sets law arms at 10% to 15% of tuition, stratified by position band by wave.
- Law-specific fields: JD program and full-time or part-time status, deferral, per-student scholarship commitment length, and the client's own ABA 509 yield history (used to check the forecast intercept).
- The peer set asks for 8 to 15 schools; the 509 procedure uses 5 to 10 (approved by the client).
- The timeline and Tier 1 description promise "a first estimate of price sensitivity from the merit grid." Many law schools have no published threshold, and Tier 1 then supports no anchor and no optimized grid (section 3, Tier 1).
- "Recommendations are delivered as ... award levels by academic, need, and residency group" does not describe the law grid (position band by market, optional need).
- "Aid policy recommendation delivered (Tier 2)" at 10 weeks and "several cycles" for precision need restating against the screen's verdict.
