# Scenario-workbook prototype

Spec: `../../Prototype_Spec_Scenario_Workbook_v0.6.md` (v0.6.1). Status: Phase 1 and the Phase 1.1 fix pass (reference ledger, risk, response, shrink path, strips, synthetic cells, tests 1, 2, 4, 5, 11 to 17, 19 and the on-demand mutation check, test 20). The workbook generator, narratives and reproduce mode are Phases 2 and 3 and are not built.

The evaluator scores scenarios the client writes and recommends nothing. Every figure that depends on the placeholder response slopes carries "Response based on client-input".

## Run

From this folder, with the project environment:

```bash
../../.venv/bin/python -m pytest tests -q
```

About 50 seconds; test 4 takes most of it. Reports land in `output/phase1/` (git-ignored). Tests that need the Yellow Arrows fixture read `YA_FIXTURE_PATH` and skip without it; no Phase 1 test needs it.

Mutation check (test 20; on demand, not collected by pytest; about 2.5 minutes with 6 jobs, including one unmutated run):

```bash
../../.venv/bin/python tests/mutation_check.py --jobs 6
```

It applies each mutant in `tests/mutation_check.py` to a scratch copy, runs the suite there and exits non-zero if any mutant survives that is not listed in `EQUIVALENT` with its reason. Report: `output/mutation/report.json`.

LibreOffice (Phases 2 and 4): `config/tools.yaml` holds `soffice_path`; env var `SOFFICE_PATH` overrides it.

## Modules

| Module | Role |
|---|---|
| `sw/config.py` | Loads and validates `config/<client>.yaml`; a missing required value is an error (spec rule 7) |
| `sw/cells.py` | Cell schema (`cell_id, residency, segment, score_lo, gpa_class, cohort, apps, admits, award_usd, enrolled`), order, validation |
| `sw/response.py` | Base yield by partial pooling (k = 20) re-centered at the latest award; placeholder response; evidence label |
| `sw/ledger.py` | Scenarios and the section 3 ledger; KPIs, money, segment block, incentive block, award matrix and step sizes |
| `sw/risk.py` | Closed forms (class, median, NTR, segment) and exact distributions (cell binomials mixed over the year shock) |
| `sw/strip.py` | Tuition what-if with the two net-tuition lines, yield strip with linear break-evens, pool strip |
| `sw/trim.py` | Shrink path and class-size table |
| `sw/mc.py` | Simulation (tests only) |
| `sw/synth_cells.py` | Cell-level synthetic generator (stopgap until W0L) and shape metrics |
| `sw/labels.py` | Fixed label text |

## What each Phase 1 test proves

| Test | File | Proves |
|---|---|---|
| 1 | `test_01_ledger.py` | Each section 3 identity on a six-cell toy grid against hand-computed answers, including the caps on `award_base` and on the incentive |
| 2 | `test_02_risk.py` | Closed forms within 0.01 of the exact convolution, and simulation (200,000 draws) within 0.005, on a toy grid with expected class about 31 (class-band probability asserted only at expected class 50 or more, on the doubled grid) and on a balanced median grid where rho 0.5 matters |
| 4 | `test_04_cf_vs_sim.py` | Closed-form class, median (rho 1.0 and 0.5) and NTR probabilities within 0.02 of simulation on 20 synthetic worlds |
| 5 | `test_05_shape.py` | Calibration check of the stopgap generator: asserted shape rows hold in at least 90% of 20 seeds; other rows, including confounding, reported (R-06) |
| 11 | `test_11_segment_invariance.py` | Splitting out-of-state cells into segment and non-segment cells changes no total or probability; pooled base-yield values |
| 12 | `test_12_incentive_scope.py` | Incentive scope rules |
| 13 | `test_13_segment_incentive.py` | Segment lift, exact segment probability against simulation, incentive decomposition identities, validity flag |
| 14 | `test_14_shrink_path.py` | Shrink path: hits N, order, monotone share, shortfall, integer settling |
| 15 | `test_15_pool_strip.py` | Pool strip equals the ledger at each multiplier (also: yield strip and tuition what-if against the ledger) |
| 16 | `test_16_class_range.py` | Class targets 100 to 140 under the cap; rejections and the supported-range notice |
| 17 | `test_17_empty_segment.py` | No segment cells: no NaN, no division error, the "no segment cells in the data" text |
| 19 | `test_19_output_coverage.py` | Every interface-contract figure against a hand-computed value or an exact ledger identity at a point where its formula can fail: 90% ranges, segment variance and flag, rho 0.5 median, evidence label, incentive block, tuition what-if at every grid value, net-tuition lines, yield strip, pool strip at rho 0.5, overrides, clipping, trimmed rates, integer settling, pooling edges |
| 20 | `mutation_check.py` | Each mutant (Review Appendix A survivors and caught list, plus Phase 1.1 changes) is caught by the suite |
| (support) | `test_00_config_labels.py` | Rule 7 on `richmond.yaml`; exact label text |

## Metric names (methodology Appendix F)

`ntr_y1` (entering class, first year: `gross_y1` minus merit, need and specialty); `discount_entering_y1` (aid over `gross_y1`; Summary label "Discount rate (entering class, first year)"); `gross_y1` (enrolled times published first-year tuition; fees excluded); median margin at t (enrolled with a score at or above t minus enrolled with a score below t); share at or above t (over expected enrolled with a score); `E_S` (segment enrolled); incentive cost, paid-anyway share, aid per additional enrollee (Appendix F items 19 to 21); evidence share (item 24); step size (item 25). Ratios are ratios of expected values, E[X] / E[Y], everywhere.

## Policy choices stated here

- The shrink path trims unscored applicants first. This is a policy choice with access implications.
- Unscored enrollees are excluded from both sides of the median margins and reported as a count (`unscored_in_median: excluded`, pending the 509 instructions, O41).
- Range kinds are never combined: "90% outcome range" (enrollment noise and year-level variation, Middle case) and "Low and High price-response cases" (placeholder slopes now).
- While `shock_source` is `illustrative`, probabilities show as "under 5%" or "over 95%" beyond those bounds, beside "Year-to-year variation assumed (s = ...), not yet calibrated".
