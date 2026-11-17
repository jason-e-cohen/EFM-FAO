# Scenario-workbook prototype

Spec: `../../Prototype_Spec_Scenario_Workbook_v0.6.md` (v0.6.1). Status: Phase 1, the Phase 1.1 fix pass (with P1.1-1 and P1.1-4 applied in Python) and Phase 2 (workbook generator and narratives; tests 3, 8, 9, 10 and 18). Reproduce mode (Phase 3) and the Distribution sheet (Phase 4) are not built.

The evaluator scores scenarios the client writes and recommends nothing. Every figure that depends on the placeholder response slopes carries "Response based on client-input".

## Run

From this folder, with the project environment:

```bash
../../.venv/bin/python -m pytest tests -q
```

About 80 seconds; test 4 and the LibreOffice recalculations take most of it. Reports land in `output/phase1/` and `output/phase2/` (git-ignored). Tests that need the Yellow Arrows fixture read `YA_FIXTURE_PATH` and skip without it; no Phase 1 or Phase 2 test needs it. The workbook tests (3, 8, 9, 10, 18) need LibreOffice and skip, with the reason, without it.

Build a workbook (synthetic data only until the live Richmond build; Richmond tuition stays null in `config/richmond.yaml`):

```bash
../../.venv/bin/python -m sw.build --config config/synthetic.yaml --data synthetic --seed 101 --scenarios config/scenarios_synthetic.yaml --out output/ --pdf
```

It writes `output/<client>/<plan_cycle>/<build_id>/workbook.xlsx` and, with `--pdf`, `workbook_Summary.pdf`. The build id is a hash of the config, cell data, scenario file and `requirements.lock`; two builds of the same inputs differ only in RunLog.

Mutation check (test 20; on demand, not collected by pytest; about 2.5 minutes with 6 jobs, including one unmutated run):

```bash
../../.venv/bin/python tests/mutation_check.py --jobs 6
```

It applies each mutant in `tests/mutation_check.py` to a scratch copy, runs the Python suite there (with `SW_SKIP_EXCEL=1`: the workbook tests compare Excel with Python and would fail for any Python mutant, so they are left out) and exits non-zero if any mutant survives that is not listed in `EQUIVALENT` with its reason. Report: `output/mutation/report.json`.

LibreOffice: `config/tools.yaml` holds `soffice_path`; env var `SOFFICE_PATH` overrides it. Every call uses a fresh profile whose `registrymodifications.xcu` sets `OOXMLRecalcMode` to 0, so LibreOffice recalculates every formula on load.

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
| `sw/build.py` | CLI; scenario file loading (`scenarios.yaml`: Baseline first, then children with fields and per-cell overrides); the run; build id and hashes |
| `sw/workbook.py` | XlsxWriter generator: README, Inputs, History, Response, Levers, Ledger_Low/Middle/High, Summary, Trim, Checks, RunLog. Every computed cell is a live formula written with its cached Python value |
| `sw/narrative.py` | The two narratives per scenario, in a Python form and an Excel form built from the same template parts |
| `sw/contract.py` | Interface contract (spec section 15 item 11): the Python dump keyed by the Summary range names, and the range layouts |
| `sw/lo.py` | LibreOffice: forced-recalculation profile, recalculation, Summary PDF render |

## Workbook (Phase 2)

| Sheet | Content |
|---|---|
| README | Purpose, how to use, color key, labels and range kinds, metric names, what is static and what is live, policy choices, contract range names |
| Inputs | Config values as named inputs (`in_<key>`; lists as one named row). Notes say which inputs are live and which need a rebuild. Case selector. No mode switch (Phase 3) |
| History | Cell x cohort panels (applications, admits, admit rate, award $, award % of tuition, yield, enrolled); totals by residency, segment and overall; tuition row |
| Response | Base yield by partial pooling as live formulas from History and Inputs; observed award range; rung grid for display only (R-01) |
| Levers | Header fields and per-cell `admit_rate`, `award_usd`, `full_tuition` per scenario. A child inherits each lever from its parent by formula (italic blue) until overwritten; grey fill marks cells that differ from the parent; change counts. `AWARD_MATRIX`: the resolved award |
| Ledger_Low/Middle/High | Per cell and scenario: section 3 of the spec, yield as one formula column (R-01). Ledger_Middle adds the award at T(p) for the tuition what-if and admits at pool multiplier 1 for the pool strip |
| Summary | Selected case; main block (Middle); Low and High; segment block; incentive block; tuition what-if with the two net-tuition lines; yield strip and break-evens; pool strip and its lo/hi parts; class-size table; narratives; labels; the interface-contract ranges for every case |
| Trim | Shrink path per scenario: the walk in trim order (fixed at build), then rates, admits and a lowest-band helper per N in Ledger order |
| Checks | Section 7 integrity checks and the full-tuition award conflicts (P1.1-1), with each conflicting cell listed |
| RunLog | Build id, git commit, hashes, timestamp, response source, shock source |

Named ranges: every contract figure is the Summary range `<prefix>_<NAME>` (rows are cases, thresholds or grid values; columns are scenarios or a strip's fields; see `sw/contract.py`). The spec table's short names (`SUM_PCAP`, `SUM_PBAND`, `SUM_FT`, `SUM_NM`, `SUM_BB`, `SUM_PNTR`, `SUM_EVID`) are aliases of the same ranges. `p_segment_goal` in the workbook is the normal form; the exact value from the build is shown beside it as a static figure.

## What each test proves

| Test | File | Proves |
|---|---|---|
| 1 | `test_01_ledger.py` | Each section 3 identity on a six-cell toy grid against hand-computed answers, including the caps on `award_base` and on the incentive |
| 2 | `test_02_risk.py` | Closed forms within 0.01 of the exact convolution, and simulation (200,000 draws) within 0.005, on a toy grid with expected class about 31 (class-band probability asserted only at expected class 50 or more, on the doubled grid) and on a balanced median grid where rho 0.5 matters |
| 3 | `test_03_excel_equals_python.py` | Excel equals Python: every formula cell on every sheet after a forced LibreOffice recalculation (integers exact, floats 1e-6 relative); the -999 sentinel guard; the profile setting; formula vocabulary; two builds differ only in RunLog |
| 4 | `test_04_cf_vs_sim.py` | Closed-form class, median (rho 1.0 and 0.5) and NTR probabilities within 0.02 of simulation on 20 synthetic worlds |
| 5 | `test_05_shape.py` | Calibration check of the stopgap generator: asserted shape rows hold in at least 90% of 20 seeds; other rows, including confounding, reported (R-06) |
| 8 | `test_08_levers.py` | Lever semantics in the recalculated workbook: a zero-bonus child and a shift-0 child equal the parent; need rate unchanged by the class target; a shift equals the yield-strip row; the class break-even hits the target; residency and segment overrides replace; the tuition what-if at a scenario's own increase equals its ntr_y1 |
| 9 | `test_09_reconciliation.py` | Every interface-contract range equals the Python dump and agrees with the Ledger columns; aliases; award matrix; strips at the scenario's own settings |
| 10 | `test_10_render.py` | Summary rendered to `output/phase2/Summary_render.pdf` (one page group per section) for review; not asserted |
| 11 | `test_11_segment_invariance.py` | Splitting out-of-state cells into segment and non-segment cells changes no total or probability; pooled base-yield values |
| 12 | `test_12_incentive_scope.py` | Incentive scope rules |
| 13 | `test_13_segment_incentive.py` | Segment lift, exact segment probability against simulation, incentive decomposition identities, validity flag |
| 14 | `test_14_shrink_path.py` | Shrink path: hits N, order, monotone share, shortfall, integer settling |
| 15 | `test_15_pool_strip.py` | Pool strip equals the ledger at each multiplier (also: yield strip and tuition what-if against the ledger) |
| 16 | `test_16_class_range.py` | Class targets 100 to 140 under the cap; rejections and the supported-range notice |
| 17 | `test_17_empty_segment.py` | No segment cells: no NaN, no division error, the "no segment cells in the data" text |
| 18 | `test_18_v06_blocks.py` | Segment block, incentive block, class-size table, pool strip and the net-tuition lines against fresh Python calls; narratives equal `sw.narrative`; the full-tuition conflict listing; segment normal-versus-exact gap reported in `output/phase2/test18_report.json` |
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
