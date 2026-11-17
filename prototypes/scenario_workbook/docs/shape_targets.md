# Shape targets: provenance of the synthetic generator's parameters

**Date:** November 16, 2026 | **Spec:** `Prototype_Spec_Scenario_Workbook_v0.6.md` section 10 and rule 4 | **Files:** `config/shape_targets.yaml` (target ranges), `config/synthetic.yaml` (`generator:`, the parameters), `sw/synth_cells.py`

Rule: ranges and parameters only. No cell value or count from the Yellow Arrows fixture appears here, in config, in code or in tests. The ranges below are the ones written in spec section 10, which records them from the fixture (sheets 1 and 2) and the October to November 2026 analysis (`ya_workbook_support/analysis.py`, git-ignored). This build did not open the fixture; the ranges were taken from the spec as written.

## 1. Target ranges (`config/shape_targets.yaml`)

Metrics are computed per history cohort on the residency-only view (segment cells merged back into their out-of-state cells, the basis on which the fixture ranges were measured), except the confounding slopes, which pool the three cohorts.

| Row | Range (spec section 10) | Source | Asserted | How it is checked; judgment calls |
|---|---|---|---|---|
| Residency | Out-of-state 67% to 72% of applications and admits; 49% to 53% of enrolled and falling; yield about 0.15 out-of-state, 0.33 to 0.35 in-state | Fixture sheets 1 and 2; analysis | Yes | Each cohort in range; "falling" = last cohort below first. "About 0.15" checked as 0.14 to 0.16 (tolerance 0.01 is a judgment call) |
| Admit rates by score group | 165+: 0.94, 0.85, 0.79 (falling); below 165: 0.33, 0.30, 0.25 | Fixture; analysis | No | Within 0.03 of each cohort value; 165+ falling |
| Admit rates by GPA | 3.83+: 0.79 to 0.85; below 3.83: 0.22 to 0.31 | Fixture; analysis | No | Each cohort in range; "below 3.83" = GPA class `lo` (blank GPA excluded) |
| Yield by group | 165+ 0.18 to 0.21; below 165 0.22 to 0.23; GPA 3.83+ 0.12 to 0.20; below 3.83 0.23 to 0.29; overall 0.209 to 0.214 | Fixture; analysis | Yes | Each cohort in range |
| Applicant pool | About 1,450 to 1,630 applications; 165+ share rises from about 0.18 to 0.27 | Fixture (applications implied as admits / admit rate); analysis | No | Each cohort in range; 165+ share within 0.02 of 0.18, 0.225 (interpolated), 0.27 |
| Awards | Admit-weighted award share of tuition: 165+ 0.98, 0.87, 0.79; below 165 0.32, 0.26, 0.25; fixed-dollar rungs; top rung equals tuition; tuition grows about 3.7%, 4.0%, 6.0% | Fixture; analysis | No | Within 0.03 per cohort; top rung equals tuition in each cohort; history steps within 0.2 points of 3.7 and 4.0 (6.0 is the plan step in `tuition_increase_by_year`) |
| Class | 133 to 146 per cohort | Fixture; analysis | Yes (range only) | Each cohort in range |
| Class mix | 165+ share of enrolled rises from about 0.35 to 0.53 | Fixture; analysis | No | Within 0.03 of 0.35, 0.44 (interpolated), 0.53 |
| Cell sparsity | Median 8 to 12 admits per active cell; about 45% to 55% of active cells under 10 admits; about 90% or more under 10 enrolled | Fixture; analysis section 8 | No | Each cohort; active cell = admits > 0 |
| Confounding | Admit-weighted cross-sectional slope of cell yield on award: raw about -0.04 to -0.17 points per $1,000; adjusted for score group, GPA class and residency -0.9 to +0.1 | Analysis | Yes | Weighted least squares of cell yield (points) on award ($1,000), weights = admits, active cell-cohorts pooled over three cohorts; adjusted adds indicators for score group, GPA class (lo, blank) and residency. The spec does not define the regression; this definition is a judgment call |

**Pass rule.** Asserted rows must hold in at least 90% of the 20 seeds in `config/synthetic.yaml` (`generator.seeds`); reported rows are listed with their pass shares in `output/phase1/test05_shape.json`.

## 2. Synthetic assumptions with no fixture source

| Parameter | Value | Source | Note |
|---|---|---|---|
| `segment_share_of_out` | 0.25 in each score group | Synthetic placeholder (spec section 10) | Share of each out-of-state cell's applications assigned to the segment. Richmond's real share waits for state-level counts (`share_source: assumed`; every segment figure carries "Segment share assumed, not from client data") |
| `segment_yield_offset_pts` | 0 | Synthetic placeholder (spec section 10) | Segment cells have the same yield as their out-of-state twins |
| `segment_apps_trend` | 0 | Synthetic placeholder (spec section 10) | Segment share constant across cohorts |
| `true_slope_pts_per_1000` | 1.2 | Spec section 10 default | Hidden response slope used only to make enrolled counts |

## 3. Generator parameters (`config/synthetic.yaml`, `generator:`): synthetic choices tuned to the ranges

None of these comes from a fixture cell. Each is a choice made so the generated worlds meet section 1; the row it serves is named.

| Parameter | Value | Serves |
|---|---|---|
| `apps_total` | 1,500, 1,560, 1,645 (SD 1%) | Class range (asserted); applicant pool (reported). The third cohort sits above 1,630 so the class stays at or above 133 with that cohort's lower admit rates |
| `upper_share_of_apps` | 0.18, 0.225, 0.27 (SD 0.006) | Applicant pool; class mix |
| `out_share_of_apps` | 0.695 (SD 0.002) | Residency |
| `band_weights`, `band_dirichlet_conc` | Upper 0.35, 0.33, 0.15, 0.17; lower 0.22, 0.18, 0.20, 0.08, 0.28, unscored 0.04; concentration 300 | Cell sparsity; seed-to-seed variation in cell composition |
| `gpa_mix` | Upper 0.40 hi, 0.57 lo, 0.03 blank; lower 0.18, 0.79, 0.03 | Admit rates and yields by GPA |
| `admit_rate_group` | 165+ 0.94, 0.85, 0.79; below 0.33, 0.30, 0.255 | Admit rates by score group; the third lower-group value is 0.255 (not 0.25) to keep the class at or above 133 |
| `admit_logit_band`, `admit_logit_gpa` | Band effects -2.0 to +1.2; GPA hi +2.8, blank -0.5 | Admit rates by GPA (reported; see section 4) |
| `award_share_band`, `award_share_gpa`, `award_share_res`, `award_share_noise_sd` | Band levels 0 to 1.0; GPA +0.08, -0.04, -0.10; in-state +0.04; cell noise SD 0.03 | Awards; confounding raw slope (the in-state lift moves the raw slope toward the middle of its range) |
| `award_share_target`, `award_rung_usd`, `full_tuition_share` | Targets as in section 1; $5,000 rungs; share at or above 0.97 takes full tuition | Awards |
| `yield_award_decay_per_1000` | 0.02 | Confounding: a cell's intrinsic yield falls with its typical award |
| `yield_targets` | Overall 0.2115; out-of-state share of enrolled 0.513, 0.509, 0.505; lower group 0.225; GPA hi 0.150, 0.155, 0.160 | Residency; yield by group |
| Tuition by cohort | 50,000; 51,850; 53,900 (steps 3.7% and 4.0%, rounded to $50) | Awards (tuition growth); invented dollar levels |
| Need, NTR target | $175,000 at a class of 140; $4.3M | Synthetic values for the tests; not Richmond's |

## 4. How the generator meets the narrow ranges, and what that means

Group-level yields (residency, score group, GPA, overall) are raked to the targets and integer counts are produced by controlled rounding that keeps block totals. Independent binomial enrollment could not meet these rows: at about 650 admits the binomial SD of overall yield is about 0.016, against an asserted range 0.005 wide (0.209 to 0.214). The ranges describe one realized file; the generator reproduces that file's shape with cell-level variation (applications by multinomial draw, awards by persistent cell noise, enrolled by randomized rounding) but without year-level sampling noise in the group yields. Test 5 therefore checks the calibration and the rounding, not an emergent property, for the residency, yield and class rows. The confounding row is not raked and is the substantive check.

The hidden true slope moves yields within a cell across cohorts; because group factors are re-raked each cohort, the slope does not move group-level yields over time. The prototype estimates no response, so this does not affect Phase 1; the pipeline's recovery tests should use the W0L world, not this stopgap.

Reported sub-checks that miss (seeds failing out of 20, Nov 16 run; pass shares by row in `output/phase1/test05_shape.json`):

| Sub-check | Seeds failing | Why |
|---|---|---|
| GPA-lo admit rate 0.22 to 0.31 | 20 | First cohort about 0.32 to 0.35: the 165+ group is admitted at 0.94, which lifts GPA-lo; a stronger GPA effect pushes GPA-hi above 0.85 instead |
| GPA-hi admit rate 0.79 to 0.85 | 10 | Third cohort 0.76 to 0.82 |
| Applications 1,450 to 1,630 | 19 | Third cohort set above 1,630 to keep the class at or above 133 |
| 165+ share of enrolled near 0.35, 0.44, 0.53 | 12 | Third cohort about 0.50 |
| Share of active cells under 10 admits, 45% to 55% | 9 | Some cohorts at 0.41 to 0.57 |
| Median admits per active cell, 8 to 12 | 4 | Some cohorts at 6.5 to 7 |
| Top rung equals tuition | 1 | One seed's cohort has no full-tuition cell with the generated noise |
