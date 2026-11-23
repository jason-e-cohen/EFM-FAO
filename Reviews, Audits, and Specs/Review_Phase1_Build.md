# Review: Phase 1 build of the scenario-workbook prototype

**Date:** November 17, 2026 | **Reviewer:** independent review (did not write the build) | **Owner:** Jason Cohen | **Scope:** `prototypes/scenario_workbook/` against `Prototype_Spec_Scenario_Workbook_v0.6.md` (sections 2 to 5, 10 to 12), `DECISIONS.md` and `CLAUDE.md` | **Build reviewed:** files dated Nov 16, 21:42 to 22:03 UTC, after the spec's last commit (`12984a9`, 16:06 EST), so the build saw the final spec.

Nothing was edited except this file. Mutation tests ran in a scratch copy. Nothing was committed.

## 1. Re-run from a clean state

A copy with no `output/`, `__pycache__` or `.pytest_cache` was run with `python -m pytest tests -q -p no:cacheprovider`.

| Item | Builder reported | Re-run |
|---|---|---|
| Tests | 64 pass, none skipped, about 50 s | 64 pass, none skipped, 49 s |
| Test 2: closed form vs exact, asserted points | 0.0083 (tol 0.01) | 0.0083 |
| Test 2: off-center band at class about 31 (recorded, not asserted) | 0.0113 | 0.0113 (target 25 on a grid with expected class 30.6) |
| Test 2: band on the doubled grid (class about 61) | 0.0063 | 0.0061 worst |
| Test 2: median, closed form vs exact, rho 1.0 and 0.5 | 0.0012 to 0.0022 | 0.0012 to 0.0021 |
| Test 2: simulation vs exact (200,000 draws) | 0.0020 (tol 0.005) | 0.0020 |
| Test 4: closed form vs simulation, 20 worlds | worst 0.011 (tol 0.02) | worst 0.011 (`p_ntr_ge_mean+0sd`) |
| Test 13: segment exact vs simulation | 0.0014 (tol 0.01) | 0.0014 |
| Test 13: Excel normal form vs exact (E_S 26 to 30) | 0.011, reported | 0.011 |
| Test 5 shares, asserted rows (residency, yield by group, class range, confounding) | 100% | 100% |
| Test 5 shares, reported rows (admit rates by score group, awards, sparsity, class mix, pool, GPA admit rates) | 100, 95, 50, 40, 5, 0% | 100, 95, 50, 40, 5, 0% |

Environment: Linux, Python 3.13.18, numpy 2.5.3, scipy 1.18.1, pandas 3.0.5. This is not the locked environment (macOS, Python 3.12.15, numpy 2.5.4, pandas 3.0.6). Every figure matched anyway. **Not verified:** a run in `.venv` on your Mac.

## 2. Formulas checked against the spec

Each check compares the code with the spec text and with a small case computed independently, outside the package's own tests.

| Formula (spec section) | Check | Result |
|---|---|---|
| Ledger steps 1 to 8 (section 3) | Hand recomputation of the toy scenario S: apps, admits, awards, caps, incentive, yield with shift and segment override, enrolled, merit, need, gross, aid, `ntr_y1`, margin at 166, full-tuition count | All match (for example class 40.874, merit $1,225,752, `ntr_y1` $894,696) |
| Incentive cap and decomposition (section 3) | Hand case: child = parent + $10,000 bonus to out-of-state, cap binding in the segment cell | C $183,800; C_any $121,000; dE 6.6; dSpend $375,800; dNTR -$32,600; aid per additional $56,939. All match |
| Base-yield pooling and re-centering (section 4) | Test 11(b) hand values re-derived (0, 4, 5, 30 admits; segment pool 22 and 42 admits) | Match. Pool keys are (residency, segment, score group), then (residency, score group) |
| Exact segment probability with the shock (section 3) | 20-node Gauss-Hermite against brute-force integration over 4,001 shock points, with fractional admits | 0.85389034 both |
| Median variance with rho (section 5) | Exact variance of the margin under the two-shock model at rho 1.0, 0.5, 0.0, against `V_m` minus the stated overstatement `s^2 sum A y^2` | Equal to 5 decimals at each rho |
| Shrink path (section 3) | Five-cell case: unscored, out-of-state and in-state below t, protected segment cell below t, one cell at 170. N = 20, 15, 10, 8, 5 | Order u, out, in, segment, upper as specified; rates match by hand (for example 0.4167 at N = 15); with `floor_rate` 0.1 and the upper cell exempt, shortfall 5.6 by hand and in code |
| Pool strip with below-threshold cells in the upper group (section 3) | 165 cell (below t = 166, scales with m), m = 1.0 and 1.5 | Margin, P(median) and class equal hand values; `G_-` carries the 165 cell's scaled part |
| Yield strip, tuition what-if (section 3) | Read against spec; test 15 compares both with the ledger | Formulas match the spec; coverage gaps in finding R-03 |

No formula error was found.

## 3. Mutation testing

70 single-formula mutants, each run against the full suite in its own scratch copy. **46 caught, 24 survived.** One survivor (L13, C_any without `min`) cannot change any result on valid input: with a valid parent and a positive slope, the child enrolls at least as many as the parent in every incentive cell. The other 23 are coverage gaps (findings R-02 to R-04). Appendix A lists the survivors.

## 4. Findings

| ID | Severity | Finding | Evidence (shown or suspected) | Location | Fix |
|---|---|---|---|---|---|
| R-01 | Major | Python computes yield from the formula. The spec has Excel interpolate between award rungs. The two disagree wherever a floor or cap kink falls between rungs, so Phase 2 test 3 (Excel equals Python at 1e-6) will fail as specified (open point 2) | **Shown:** 10 worlds, 3 scenarios, 3 cases: 35 of 6,003 cell evaluations differ, by up to 1.46 yield points (High), 1.10 (Middle) and 0.38 (Low) | Spec section 4; `sw/response.py` `yield_at` | Decide in the spec before Phase 2: both sides use one method. Recommended: the Ledger computes the formula directly, `MIN(MAX(y0 + b*(a - a0)/100000, floor), cap)`, and the Response sheet keeps the rung table for display. When the pipeline's tabular response arrives (section 15 item 3), both switch to interpolation together. Alternative: add each cell's kink points as extra rungs |
| R-02 | Major | Some interface-contract outputs have no test. Phase 2 test 3 shows only that Excel matches Python, so an error here would carry into the workbook | **Shown (mutants survive):** dNTR and `ntr_per_additional` (parent priced with the child's weights, L15); 90% ranges for class, NTR and segment (1.96 for 1.645, K10); `p_median_t_rho05` (configured rho used instead of 0.5, K13); segment `V_S`, `segment_lo90/hi90` and the Excel normal form (shock term dropped, L17); evidence label tolerance and `evidence_extrapolated_share` (R6) | `sw/ledger.py` `incentive`, `segment`; `sw/risk.py` `median`, `cf_*`; `sw/response.py` `evidence_labels` | Add toy hand-value asserts: dNTR and `ntr_per_additional` (the section 2 hand case gives -$32,600 and -$4,939); lo90 and hi90 for class and segment; the rho 0.5 line on a config with rho 1; `V_S`; one observed and one extrapolated cell at the tolerance edge |
| R-03 | Major | The strips and the tuition what-if are tested only at points where they cannot fail | **Shown:** survivors P3 (pool strip ignores rho; tests use rho 1), P4 (pool NTR SD), P6 (NTR break-even denominator), P7 (clip count always 0), P8 (what-if discount column), P9 (scaled net-tuition line), P10 (what-if awards not recomputed at T(p); only the scenario's own p is tested), P12 (yield-strip medians ignore the shift) | `sw/strip.py` | Pool strip at rho 0.5 against the ledger; NTR SD against `risk.cf_ntr`; NTR break-even reaching `ntr_target`; a scenario where the clip count is positive; the tuition what-if at every grid p against a ledger run with that `tuition_increase_pct` (full-tuition cells follow T(p)); the discount column; hand values for both net-tuition lines; yield-strip medians against the ledger |
| R-04 | Minor | Several branches of the ledger, trim, response and config have no test | **Shown (mutants survive):** residency yield-shift override adds instead of replacing (L8; Phase 2 test 8 covers it later); no clip after the shift (L9); trimmed rates ignore `floor_rate` (T2; only the shortfall text is tested); integer settling removed or idle (T6, T6b; the within-1 check passes without it); lowest band admitted (T8); full-tuition count tolerance (L19); pooling at exactly 30 admits (R3); multi-year compounding (C3). Test 2's toy grid has no 165 or 166 cells, so both score medians are identical and sit in the tail (p about 0.02); the exact rho < 1 path is not separated from independence (K9) | `tests/test_01`, `test_02`, `test_11`, `test_14` | Toy cases for: a residency override with a non-zero global shift; a capped cell with a negative shift; trimmed rates equal to `floor_rate` for fully cut cells; integer settling with `floor_rate` > 0 (where settling matters), with a tolerance tied to the last cell's yield; a segment pool of exactly 30; `plan_year` two years out. Add 165 and 166 cells to the test 2 toy grid so the medians sit near p = 0.3 to 0.7 |
| R-05 | Minor | With `integer_admits`, the shrink path rewrites the admit rate of cells it does not cut | **Shown:** seed 101, pool 1.15, N = 130: 27 of 81 uncut cells get new rates (largest change 0.13); their admits are unchanged. The Levers "cells changed from parent" count would include them | `sw/trim.py` `_settle_integer`, last line | Return the input rate for cells with `removed_share` 0; write new rates only for cut cells |
| R-06 | Minor | Test 5's asserted rows pass by construction, and the confounding row does not detect confounding (open point 6) | **Shown:** overall yield is 0.2108 to 0.2122 across 60 seed-cohorts, the band around the configured 0.2115. Setting the config target to 0.23 moves it to 0.2293 to 0.2307 and fails three rows. With the planted decay and the true slope both 0, the confounding row still passes 20 of 20 (adjusted slope -0.07 to +0.06, raw slope from the raked group targets) | `sw/synth_cells.py` `_enroll`; `config/shape_targets.yaml` | Decide in the spec: record test 5 as a calibration check of the stopgap generator. It is evidence about the generator, not the evaluator. If the confounding row is meant to show that a confound is present, require the adjusted slope to exclude zero, or move the row to W0L. No evaluator change |
| R-07 | Minor | The example award in the scaled net-tuition line uses `award_base`, which is plan-year dollars when awards scale. It also excludes zero awards, which the build report does not mention | **Shown** by reading. The line is `p x (base-cycle tuition minus award)`, so it needs the base-cycle award | `sw/strip.py` `tuition`, lines 171 to 172 | Use `scen.award_usd` (base-cycle lever dollars). State the rule in spec section 3 (enrolled-weighted mean over 0 < award < full tuition, rounded to $1,000) |
| R-08 | Minor | The code makes four choices the spec does not state, and the Excel mirror must copy each one | **Shown** by reading: (a) yield is clipped twice: the response is clipped, then the shift is added and clipped again (consistent with Excel adding the shift to clipped rung values); (b) `class_lo90` is clipped at zero, but the spec clips only the segment range; (c) pooling falls back further: (residency, score group), then score group, then all cells; (d) fractional admits use Binomial(floor) + Bernoulli(fraction) | `sw/ledger.py` line 238; `sw/risk.py` lines 32, 143 to 156; `sw/response.py` lines 223 to 229 | Record each in spec sections 3 to 5 before Phase 2 |

## 5. The builder's open points

| # | Point | Verdict | Reason |
|---|---|---|---|
| 1 | Full-tuition flag per cell | **Accept; decide in spec** | Read literally, the spec fails: a baseline full-tuition award holds base-cycle tuition, which is below the plan-year tuition, so the "at or above the parent's tuition" rule would drop it from the rung. The flag fixes this. The spec should make the flag a Levers column (baseline: award at or above base-cycle tuition; override: at or above the parent's tuition) and list it under validity. The code already compares it |
| 2 | Rung interpolation vs direct formula | **Decide in spec** | See R-01. Both sides must use one method. The direct formula is simpler now; rungs are the interface the pipeline will supply later |
| 3 | Test 2 band check run at class 61, not 31 | **Accept; decide in spec** | The 0.0113 miss is normal-approximation skew at a class of about 30; the doubled grid stays within 0.0061. Spec: assert the band probability at expected class 50 or more, and report it below that. Related judgment call: the Excel segment normal misses by 0.011 at E_S 26 to 30, above the "approximate" threshold of 20. Raising that threshold to 30 would label those cases |
| 4 | Rho in test 4 for the median only | **Accept; decide in spec** | Rho is defined between the above-t and below-t groups (section 5); class and NTR have one common shock. Spec text: "at rho 1.0 and 0.5 for the median probabilities" |
| 5 | Added `segment` scenario field | **Accept; decide in spec** | Section 2 allows at most one active segment but names no field. Add `segment` to the scenario-file fields and to the validity list (the code includes it) |
| 6 | Generator forces group yields | **Accept as a stopgap; decide in spec** | See R-06. This is acceptable for Phase 1 because the evaluator does not depend on the generator's realism, but test 5 should be described as a calibration check |
| 7a | Fractional admits as Binomial(floor) + Bernoulli(fraction) | **Accept** | The mean is exact; per-cell variance differs from `A y (1 - y)` by `frac x y^2 (1 - frac)`, which is small. Record it in section 5 |
| 7b | Pool fallback when a pool has no admits | **Accept** | It occurs only when the (residency, score group) pool has no admits; otherwise the result is undefined. Record it in section 4 |
| 7c | Example award in the scaled line | **Change** | See R-07 |
| 7d | GPA median threshold equals the GPA class boundary | **Accept** | The cell schema has one GPA boundary, so a different threshold could not be evaluated. The loader enforces it. Record it in section 2 |
| 8 | Richmond tuition left null | **Accept** | Correct under rules 3 and 7: the only source on hand was the fixture. Phase 2 runs on synthetic data, so this does not block it. Richmond's published tuition by cohort, and the 2027 figure (OD-09, Brandon), are needed before Phase 3 and the live build |

## 6. Rules and hygiene

| Check | Result |
|---|---|
| No Yellow Arrows fixture value in code, config, tests or docs | **Pass.** Method: the fixture was read on your computer (it was not copied to the cloud workspace). From it, 1,563 distinctive numeric tokens were taken (integers of 1,000 or more that are not multiples of 5,000; decimals with four or more places; dollar values with cents) plus every text string of 25 characters or more. These were searched for in the 31 files under `prototypes/scenario_workbook/` (excluding `output/` and caches): 0 hits. The synthetic and toy tuition levels match none of the three fixture-implied tuition values within $100. **Limit:** a value with three decimals or fewer (such as 0.94) cannot be told apart from the spec's ranges, which rule 4 allows. The build reports that it never opened the fixture, and `YA_FIXTURE_PATH` is unset |
| `efa_fao/` untouched | **Pass.** `git status` and `git diff HEAD -- efa_fao` show no tracked changes; no file under `efa_fao/` was modified after Nov 16, 21:00 UTC. Spec documents are unchanged against HEAD |
| `requirements.lock` exact versions | **Pass.** 28 lines, all `name==version`, covering every dependency the spec requires. Written with `pip list --format=freeze` (the build explained why); the Python version appears only in a comment |
| Git hygiene | The fixture and `output/` are git-ignored (`git check-ignore` confirms); `fixtures/` does not exist; `prototypes/` is untracked; nothing is committed |
| Protected attributes, student-level data | `cells.py` rejects any column outside the 10-column schema. Phase 1 has no outputs to scan; test 7 is Phase 4 |

## 7. Verdict

**Ready for Phase 2 after named fixes.** No formula error was found, and every reported figure reproduces. Before Phase 2 code starts:

1. Decide R-01 in the spec, so test 3 can pass by design.
2. Add the tests in R-02 and R-03. Phase 2 makes Excel match Python, so Python has to be checked first.
3. Fix R-05 and R-07 (each is a few lines).
4. Record the spec decisions for open points 1, 3, 4, 5 and 7, and for R-08.

R-04 and R-06 can follow during Phase 2.

**Not verified:** a run in `.venv` on your Mac; anything from Phases 2 to 4 (workbook, Excel parity, reproduce mode, guardrail test 7); any Richmond figure.

## Appendix A. Surviving mutants

| ID | Mutation | Covered by |
|---|---|---|
| L8 | Residency yield-shift override adds instead of replacing | R-04 |
| L9 | No clip after the shift | R-04 |
| L13 | C_any without `min` (cannot change results on valid input) | none needed |
| L15 | dNTR prices the parent with the child's weights | R-02 |
| L17 | Segment `V_S` without the shock term | R-02 |
| L19 | Full-tuition count tolerance of $10,000 | R-04 |
| R3 | Segment pool needs more than 30 admits | R-04 |
| R6 | Evidence tolerance ignored | R-02 |
| K9 | Exact two-group shocks independent | R-04 |
| K10 | 90% ranges use 1.96 | R-02 |
| K13 | rho 0.5 sensitivity uses the configured rho | R-02 |
| T2 | Trimmed rate ignores `floor_rate` | R-04 |
| T6, T6b | Integer settling removed, or the settling step idle | R-04 |
| T8 | Lowest band admitted ignores admits | R-04 |
| P3 | Pool strip median ignores rho | R-03 |
| P4 | Pool strip NTR SD without the shock | R-03 |
| P6 | NTR break-even uses the wrong denominator | R-03 |
| P7 | Clip count always 0 | R-03 |
| P8 | Tuition what-if discount column wrong | R-03 |
| P9 | Scaled net-tuition line ignores the award | R-03 |
| P10 | Tuition what-if awards not recomputed at T(p) | R-03 |
| P12 | Yield-strip medians ignore the shift | R-03 |
| C3 | Multi-year tuition increase added instead of compounded | R-04 |

Caught (46): pool multiplier and segment lift scope; both award caps; full-tuition rung (baseline and override); scaled awards; segment override replacing; need scaling; discount; `bonus_min_score`; aid-per-additional threshold; validity fields; segment lo90 clip; share denominator; integer admit rounding; pooling denominator, re-centering sign, segment pool use, zero-admit cells, `ybar` weighting; class variance shock, cap continuity, band edge, median rho, median tie rule, NTR variance shock, unscored sign, Gauss-Hermite scaling, fractional Bernoulli, segment `>=`; removable enrollment with floor, segment protection, residency tie order, shortfall, protection threshold, above-cap rows; pool strip `G_-` scaling, class variance and segment lift; tuition what-if specialty; class break-even; simulation shock; cap check; tuition rounding.
