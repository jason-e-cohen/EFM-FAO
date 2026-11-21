# O37: calibrating the year-to-year variation s from public data

**Date:** November 21, 2026 | **For:** Jason Cohen | **Status:** analysis for review. Nothing in `sw/`, the configs, the spec, the methodology or `DECISIONS.md` has changed, and nothing is committed. **Basis:** methodology `02_methodology_v2.8.md` section 6 ([v2.8, B4-1]) and O37; spec v0.6 sections 2, 4 and 5 (`risk.common_shock_sd`, `shock_source`, `SHOCK_LABEL`). **Code and tables:** `analysis/o37_shock_calibration/` (README there). Public data only; no client data; the Yellow Arrows file was not an input; no school is named.

## 1. Summary

| | Law (ABA 509, fall 2021 to 2025) | Undergraduate (IPEDS, fall 2014 to 2023) |
|---|---|---|
| Shock around a known level: section 6's method (detrended year-over-year change, binomial removed) | 0.063 to 0.070 (95% CI about 0.053 to 0.079) | 0.102 to 0.116 |
| Same, controlling for the change in admit rate | 0.056 to 0.060 | 0.101 to 0.114 |
| Do shocks revert? | No. The independent-each-year part is about 0; changes persist | Partly: an independent part of 0.070 and a persistent part of 0.103 |
| What a school faces: one-year-ahead forecast error beyond binomial noise, base yield = mean of the last three cohorts (as the workbook builds it) | 0.110 (0.097 to 0.121); peer band 0.121 (0.101 to 0.138) | 0.148 (0.144 to 0.152) |
| **Recommended s** | **0.10** (plausible range 0.09 to 0.12), `shock_source: public` | **0.14, provisional** (by size band 0.10 to 0.17); rerun in the client's own band |
| Spread scales with yield (multiplicative)? | Yes (slope 2.3; 2 = multiplicative, 0 = additive) | Yes (slope 1.8) |

The recommendation keeps the law value at 0.10, but on a different footing. The specified method gives about 0.065. That figure assumes the base yield equals this year's true level, so that each year's shock is independent and reverts. In the law panel, shocks do not revert. A base yield averaged over past cohorts is therefore stale by the planning year, and the error a planner actually faces is 0.09 (forecasting from last year) to 0.11 (from a three-cohort mean). In the workbook, s is the only source of variation beyond binomial noise in a kind-1 outcome range (section 6, [v2.8, B4-9]), and no other term carries base-yield error. Calibrating s to the forecast error is the honest choice. **Judgment call**; section 7 says what would change it.

## 2. Data and years

**Law.** Inputs, read only from the 509 dashboard repo:
- `data/First_Year_Class_2021.xlsx` to `2024.xlsx` (ABA compilations);
- `data/aba509_all_schools_2025.csv`;
- for the column changes between years, `scraper/ingest_historical_backfill.py`, `scraper/build_school_crosswalk.py` and `data/crosswalk_review_needed.csv`.

No other file in that repo, no `.env` file and no Supabase table was opened, and no script there was run.

- **Cohort definition.** SchoolYear is the fall entering class.
  - The 2023 and 2024 files carry a `SchoolYear` column equal to the file year. The 2021 and 2022 files have no such column; their year is taken from the file name.
  - A published 2025 509 report labels its first-year class "2025 First Year Class (Oct 6, 2024 to Oct 5, 2025)", and the 509 counts are taken as of October 5. These come from third-party and school pages and were not checked against the ABA's instructions, which I did not open.
  - National application totals follow the known pattern of the cycles: 475,658 (2021), 426,983 (2022), 413,064 (2023), 423,349 (2024), 517,353 (2025). This matches a fall 2021 surge, a fall 2022 decline and a fall 2025 surge.
- **The 2024 compilation and the 2025 CSV are different cohorts.** 195 schools appear in both. None has the same applications or offers in both, and the application totals differ by 22%. (The 2021 and 2024 national offer totals are both 135,539. That is a coincidence: only one school has the same offer count in both years.)
- **Column schemas.** For 2021 and 2022: `CompletedApplications`, `OffersAdmission`, `EnrolleesFromApplicantPool`, `OtherFirstYearEnrolles`, `TotalFYClassAll`. For 2023 and 2024: `Applications`, `Offers`, `Enrollees`, `OtherFirstYearEnrollees`, `TotalEnrollees`. This is per `ingest_historical_backfill.py`, and it was checked against the file headers.
- **Name match.** The repo's crosswalk lives in Supabase, so I rebuilt it locally (`build_law_panel.py`): the repo's `normalize()` rules, then exact match, then token coverage, then the review file's resolutions, then a manual table.
  - All 395 raw names are matched: 229 exact, 104 by token, 9 through the review file, 53 manual.
  - No school has two rows in a year.
  - 18 school-years show a size jump over 0.5 in log. I checked each by hand. They are the 2025 application surge, a closure, a consolidation and one likely data error (offers well below the next year's level, with a yield near 0.62). The data error is removed by the implausible-jump rule.
- **Yield.** Enrollees from the applicant pool ÷ offers (Appendix F item 5). For 2021 to 2024 this equals the ABA's published `EnrollOfferRate` to within 0.005 points.
  - In 2025 the scraped `enrollees_from_pool` exceeds the count implied by the ABA's own rates at 45 schools, by 2 to 16. Both published rates (from offers and from applications) imply the same smaller count.
  - I used the ABA-implied count for 2025, which keeps 2025 consistent with earlier years. With the scraped count instead, the estimates move by at most 0.002.
  - The cause is not verified; a change in the 2025 509 definition is suspected.
- **Deferrals.** Given for 2025 only (`enrollees_deferred`): 753 in all, a median of 2 per school, 148 schools with any, 0.55% of offers. They do not enter the yield.
- **Older compilations.** The ABA disclosure site lists First Year Class compilations back to 2011. Downloading them goes through the site's backend service, and that request was blocked in this session, so 2011 to 2020 are not in this panel. The README explains how to add them by hand; the builder reads them from `data/aba_extra/`.

**Undergraduate.** IPEDS ADM2014 to ADM2023 (revised files where NCES published them) and HD files, downloaded from NCES. ADM2024 returned "not found" (not yet published).
- Kept: four-year, public or private nonprofit, degree-granting institutions where all three counts are reported by the institution (IPEDS flag R).
- Yield = ENRLT ÷ ADMSSN.

**Panel sizes after the rules (section 3).**

| | Units | Unit-years | First differences | Units in (b) (3 or more years) | Median offers | Median yield | Median class |
|---|---|---|---|---|---|---|---|
| Law, all | 198 | 974 | 773 | 195 | 601 | 0.304 | 175 |
| Law, peer band (first-year class 100 to 200) | 101 | 502 | | | 463 | 0.312 | 146 |
| Undergraduate, all | 1,612 | 13,963 | 12,086 | 1,541 | 2,294 | 0.253 | 523 |

The panel is in `analysis/o37_shock_calibration/data/` (git-ignored).

## 3. Data-quality and outlier rules

| Rule | Law school-years removed | Undergraduate |
|---|---|---|
| Closure: a school that stopped reporting after a teach-out (class fell from about 120 to 25), and one with a single year and zero offers | 4 | none applied |
| Consolidation: a school whose 2025 class absorbed a campus that stopped reporting in 2025 (class up 0.70 in log); its 2025 row only | 1 | none applied |
| Too small: offers under 50 or enrollees under 10 (law); offers under 100 or enrolled under 50 (undergraduate) | 1 (zero offers) | 1,913 |
| Implausible: log yield more than 0.5 from the unit's own median (about 65% above or 40% below its usual yield); units with 3 or more years | 3 | 701 (4.8%) |

**Size bands** use the unit's median first-year class over the years present (characteristics only; no school list). Law: under 100; 100 to 200 (peer band); 201 to 299; 300 and over. Undergraduate: under 300; 300 to 999; 1,000 to 2,999; 3,000 and over (first-time enrolled).

**Rule sensitivity.**
- Law: turning the implausible rule off raises (a) from 0.063 to 0.072, and the three-cohort forecast error from 0.110 to 0.120.
- Undergraduate: turning it off raises (a) from 0.102 to 0.132. The undergraduate figure depends on this rule much more than the law figure does. IPEDS step changes (for example, a new application platform) look like yield shocks and are not.

## 4. Estimates

All values are SDs on the log-yield scale (≈ s in e ~ N(1, s)), with binomial enrollment noise removed. Intervals are percentile 95% intervals from resampling schools: 2,000 draws for law, 500 for undergraduate, seed 37. Full tables are in `results/estimates.csv` (every configuration). Estimator code is in `estimators.py`.

**Estimator check** (`validate_estimators.py`; 200 simulated law-shaped panels per world; `results/validation.csv`):
- With independent shocks (school 0.06, national 0.03), (a) and (b) return 0.061 and 0.060 for the school part and 0.067 for the total (true 0.067). The persistence split returns 0.060 for the independent part.
- With random-walk shocks of 0.06, (a) and (b) understate (0.043), and the persistence split recovers 0.062 for the persistent part.
- The forecast-error estimates match theory: s√2 from last year's yield, and s√(4/3) from a three-year mean.

### 4.1 Law, all schools, 2021 to 2025

| Estimator | Total | School-specific | National |
|---|---|---|---|
| (a) first differences | 0.063 (0.053 to 0.072) | 0.058 (0.048 to 0.067) | 0.024 |
| (b) level and trend | 0.070 (0.060 to 0.079) | 0.061 (0.050 to 0.070) | 0.034 (3-df interval 0.019 to 0.127) |
| (c) first differences + admit rate | 0.056 (0.046 to 0.065) | 0.055 (0.044 to 0.063) | |
| (c) level and trend + admit rate | 0.060 (0.050 to 0.069) | 0.058 (0.047 to 0.066) | |
| Persistence: independent part | | 0.000 (0.000 to 0.025) | |
| Persistence: random-walk part | | 0.091 (0.080 to 0.101) | |
| Forecast error, last year's yield | 0.089 (0.076 to 0.102) | 0.082 (0.067 to 0.095) | |
| Forecast error, 2-cohort mean | 0.096 (0.084 to 0.107) | 0.088 (0.076 to 0.099) | |
| Forecast error, 3-cohort mean (targets 2024, 2025) | 0.110 (0.097 to 0.121) | 0.104 (0.090 to 0.117) | |

- **Admit-rate slope** (c): −0.20 (−0.29 to −0.10). A 10% rise in the admit rate goes with a 2% lower yield.
- **Binomial noise** is 51% of the variance of yield changes.
- **Year effects on log yield** (detrended): 2021 +0.031, 2022 −0.015, 2023 −0.030, 2024 −0.020, 2025 +0.034.
- **Autocorrelation of yield changes**: −0.23 (−0.30 to −0.16). Shocks that revert each year would give −0.5 (simulation: −0.49); a pure random walk with this binomial share would give about −0.25.

### 4.2 Law, by band, window and type

| Configuration | Schools | (a) total | (b) total | (c) FD total | Forecast, last year | Forecast, 3-cohort mean |
|---|---|---|---|---|---|---|
| Peer band 100 to 200, 2021-2025 | 101 | 0.062 (0.047 to 0.077) | 0.067 (0.052 to 0.081) | 0.060 | 0.088 (0.066 to 0.110) | 0.121 (0.101 to 0.138) |
| Under 100 | 12 | 0.079 (0.032 to 0.108) | 0.086 | 0.057 | 0.111 | 0.090 |
| 201 to 299 | 57 | 0.065 | 0.075 | 0.054 | 0.092 | 0.107 |
| 300 and over | 26 | 0.052 | 0.058 | 0.044 | 0.073 | 0.077 |
| All, 2023-2025 (without 2021, 2022) | 194 | 0.066 (0.052 to 0.080) | 0.055 (0.032 to 0.074) | 0.058 | 0.094 | n/a (2-cohort: 0.106) |
| Peer band, 2023-2025 | 100 | 0.073 (0.050 to 0.096) | 0.066 (0.029 to 0.096) | 0.069 | 0.104 | n/a (2-cohort: 0.112) |
| All, 2022-2025 (without 2021) | 196 | 0.057 | 0.052 | 0.049 | 0.080 | 0.114 |
| Private | 109 | 0.055 | 0.064 | 0.049 | 0.078 | 0.094 |
| Public | 86 | 0.071 | 0.076 | 0.065 | 0.101 | 0.127 |

Dropping the 2021 and 2022 entering classes leaves the school-specific figures about where they were (0.052 to 0.066). The national component falls to 0.014 to 0.017, because the 2021 swing leaves the window. The excess falls as schools get larger, from about 0.08 below 100 to about 0.05 at 300 and over. The peer band sits at the all-school level.

### 4.3 Undergraduate

| Configuration | Units | (a) total | (b) total | (c) FD total | Persistence: independent / random-walk | Forecast, last year | Forecast, 3-cohort mean |
|---|---|---|---|---|---|---|---|
| All, 2014-2023 | 1,570 | 0.102 (0.100 to 0.105) | 0.116 | 0.101 | 0.070 / 0.103 | 0.145 | 0.148 (0.144 to 0.152) |
| Private nonprofit | 1,001 | 0.109 | 0.122 | 0.107 | 0.075 / 0.109 | 0.153 | 0.155 |
| Public | 570 | 0.090 | 0.104 | 0.089 | 0.062 / 0.090 | 0.128 | 0.134 |
| Under 300 entering | 491 | 0.128 | 0.142 | 0.126 | 0.095 / 0.120 | 0.181 | 0.174 |
| 300 to 999 | 646 | 0.100 | 0.114 | 0.099 | 0.068 / 0.100 | 0.141 | 0.146 |
| 1,000 to 2,999 | 299 | 0.084 | 0.097 | 0.083 | 0.046 / 0.094 | 0.119 | 0.136 |
| 3,000 and over | 134 | 0.061 | 0.071 | 0.057 | 0.027 / 0.071 | 0.086 | 0.103 |
| Private nonprofit, 300 to 999 | 468 | 0.098 | 0.112 | 0.098 | 0.067 / 0.099 | 0.139 | 0.145 (0.138 to 0.152) |
| Without fall 2020 and 2021 | 1,562 | 0.097 | 0.111 | 0.097 | 0.070 / 0.095 | 0.138 | 0.137 |
| 2019-2023 only (five years, as law) | 1,443 | 0.109 | 0.108 | 0.107 | 0.073 / 0.109 | 0.154 | 0.143 |

- **National component:** 0.016 to 0.020 (10-year interval 0.013 to 0.038). The largest year effect is fall 2020 (−0.041).
- **Admit-rate slope:** −0.14.
- **Binomial share** of the variance of changes: 15%. Undergraduate cells are large, so nearly all of the spread is excess.

### 4.4 Multiplicative or additive

Unit-specific excess spread of yield changes, by fifths of the unit's mean yield (`results/multiplicative.csv`):

| Law, mean yield | 0.21 | 0.27 | 0.30 | 0.35 | 0.47 |
|---|---|---|---|---|---|
| Excess SD of log yield | 0.061 | 0.048 | 0.048 | 0.058 | 0.070 |
| Excess SD of yield, points | 1.3 | 1.3 | 1.4 | 2.0 | 3.0 |

| Undergraduate, mean yield | 0.14 | 0.20 | 0.26 | 0.35 | 0.58 |
|---|---|---|---|---|---|
| Excess SD of log yield | 0.111 | 0.100 | 0.094 | 0.094 | 0.106 |
| Excess SD of yield, points | 1.6 | 2.0 | 2.4 | 3.3 | 5.7 |

Measured in points, the spread more than doubles across the yield range; on the log scale it stays roughly flat. Fitting log of the level variance against log of mean yield gives a slope of 2.35 for law (2.07 in the peer band) and 1.83 for undergraduate. Under a multiplicative shock the slope is 2; under an additive one it is 0. The workbook's multiplicative form (e times y) fits. The slopes were not bootstrapped.

## 5. National versus school-specific: which a planning school faces

**Both, in our reading.**

- **The national component cannot be known when the decisions are made.** Awards, admit targets and the budget for the fall 2027 class are set in the winter and spring of the 2026-27 cycle. The national yield climate of that cycle shows up only as admitted students decide. LSAC volume reports show applicant counts during the cycle, not yields.
  - Panel evidence: the detrended national log yield moved by +0.031 in 2021, and from −0.020 in 2024 to +0.034 in 2025. A school that set its awards on its own history would have missed both swings.
- **The school-specific component is the larger part.** It is about 0.058 against a national 0.024 to 0.034, so national is 15% to 25% of the variance. A school can watch its own deposits as they come in, but its plan is set first.
- **The workbook's shock fits a combined total.** One common e multiplies every cell. It is meant to capture whatever moves all of a school's cells together in a year, whether the cause is national or local, so the total (national plus school-specific) is the matching quantity.
- **What would change this reading:** a client that sets awards after watching yields mid-cycle and can still re-price. Then only the part not yet revealed belongs in s. There is no public data on that timing.

## 6. What a four-difference panel can and cannot support

**It can support:**
- A pooled cross-school estimate of the excess spread with useful precision (±0.01 at 195 schools) under the assumption that every school shares one s.
- A test of whether shocks revert, and a check of the multiplicative form.
- Size-band contrasts at the 100-school level.

**It cannot support:**
- **The national component**, from three effective degrees of freedom: 95% interval 0.019 to 0.127.
- **Separating persistent shocks from school-specific trends.** With four differences per school, a random walk and trends of about 6% a year look the same. Both mean that an average of past cohorts is a stale forecast; neither can be told apart from the other, or projected forward.
- **Whether s varies over time** (one five-year window, which includes the 2021 and 2025 surges). Without 2021 and 2022, two differences remain: point estimates are similar, intervals 1.5 to 2 times as wide.
- **Any single school's own s.**
- **The three-cohort forecast error** rests on two target years (2024, 2025), and one of them, 2025, is a surge year.

The 2011 to 2020 compilations would add about ten differences per school and test whether 2021 to 2025 is typical. They are the most useful addition. The ten-year undergraduate panel gives the same qualitative picture (persistent shocks, multiplicative form), and its five-year 2019-2023 subset matches the full ten years within 0.01.

## 7. Recommendation

**Law: s = 0.10, `shock_source: public`.** Reasoning:

1. **Basis.** The workbook's kind-1 range is binomial noise plus s, around a base yield that pools all history cohorts re-centered at the latest award (`sw/response.py`, `base_yield`). The matching target is therefore the one-year-ahead error of a forecast built that way, beyond binomial noise:
   - 0.110 from a three-cohort mean (peer band 0.121);
   - 0.096 from a two-cohort mean;
   - 0.089 from last year's yield.
2. **Admit-rate changes.** Controlling for them lowers the excess by 10% to 15% (section 4.1). The workbook takes admits as levers, so planned admit and mix changes should not sit in s. Within-cycle waitlist offers, however, respond to the yield shock itself, so this control overstates the planned part. Taking 0.10 rather than 0.11 allows for both.
3. **Why not 0.065.** The specified detrended first-difference value assumes shocks revert each year. The panel says they do not (independent part 0.000, interval up to 0.025). At 0.065, the year-level part of a range built around a three-cohort base yield would be about a third too small.
4. **Uncertainty.** The plausible range is 0.09 to 0.12. Section 8 shows what this moves.

**Judgment call. What would change it:**
- A base yield built from the latest cohort only: s = 0.09.
- A base yield that tracks the current level (for example, the pipeline's out-of-time-calibrated forecast, whose own error then enters the range): s ≈ 0.06 to 0.065, the shock-only value, so the error is not counted twice.
- The 2011 to 2020 compilations showing that 2021 to 2025 was unusually volatile.
- Five cycles of a client's own out-of-time errors, combined by inverse variance (section 6).

The methodology text in section 6 would need to say "one-year-ahead forecast error of a mean of recent cohorts" rather than "year-over-year change, detrended". Under the methodology's own range rule (B4-9), the pipeline's class interval and the evaluator's should then use the same basis.

**Undergraduate: s = 0.14, provisional.** This is private nonprofit, 300 to 999 entering (0.139 to 0.145), and all institutions (0.137 to 0.148 by forecast window). It is larger for small classes (0.17 under 300) and smaller for large ones (0.10 at 3,000 and over). It depends on the implausible-jump rule (section 3). Rerun in the client's own size band and control at engagement; IPEDS fall 2024 is not yet published.

**Proposed label text** (spec section 4; `sw/labels.py`). Today `SHOCK_LABEL` appears only while `shock_source` is `illustrative`, and the workbook then shows nothing about s. I propose a second constant shown beside every probability and range when the source is `public`, so the reader still knows what range kind 1 includes:
- `SHOCK_LABEL_PUBLIC` = "Year-to-year variation s = {s}, calibrated from public {source} yield histories ({years})", with `{source}` = "ABA 509" or "IPEDS" and `{years}` = "fall 2021 to 2025 entering classes" or "fall 2014 to 2023".
- Law instance: "Year-to-year variation s = 0.1, calibrated from public ABA 509 yield histories (fall 2021 to 2025 entering classes)".
- `shock_source` value: `public`.

**Recommendation on the "under 5%" and "over 95%" display.** Keep it after the switch. Tail probabilities move most with s: the synthetic Baseline P(NTR ≥ target) reads 4% at s = 0.065, 8% at 0.10 and 10% at 0.12 (section 8). The normal approximation is also weakest in the tails.

These are proposals; the config, label and spec change after your review (DECISIONS Nov 21, O37).

## 8. Effect on headline probabilities (synthetic builds only)

Synthetic config and scenarios (`config/synthetic.yaml`, `scenarios_synthetic.yaml`, seed 101), Middle case, computed with the prototype's own `sw/risk.py`; only `risk.common_shock_sd` was changed, in memory (`sensitivity_synthetic.py`, `results/synthetic_sensitivity.csv`). Cap 140, band ±4, median thresholds 166 and 165 at ρ = 1. All figures are synthetic and carry "Response based on client-input".

| Scenario (expected class) | s | 90% class range | P(class > cap) | P(class in band) | P(median 165 holds) | P(NTR ≥ target) |
|---|---|---|---|---|---|---|
| Baseline (129.1) | 0.05 | 110 to 149 | 0.17 | 0.20 | 0.325 | 0.03 |
| | 0.065 | 108 to 150 | 0.19 | 0.19 | 0.325 | 0.04 |
| | **0.10** | **102 to 156** | **0.24** | **0.18** | **0.325** | **0.08** |
| | 0.12 | 99 to 159 | 0.27 | 0.16 | 0.325 | 0.10 |
| | 0.15 | 93 to 165 | 0.30 | 0.15 | 0.325 | 0.14 |
| Out-of-state incentive (144.6) | 0.05 / 0.10 / 0.15 | 124-165 / 115-174 / 105-184 | 0.63 / 0.59 / 0.57 | 0.26 / 0.19 / 0.15 | 0.478 (all) | 0.05 / 0.10 / 0.17 |
| Segment incentive (137.3) | 0.05 / 0.10 / 0.15 | 117-157 / 109-165 / 100-175 | 0.40 / 0.43 / 0.44 | 0.28 / 0.21 / 0.15 | 0.32 (all) | 0.04 / 0.10 / 0.16 |
| Larger pool, softer yield (148.6) | 0.05 / 0.10 / 0.15 | 127-170 / 119-179 / 108-189 | 0.74 / 0.67 / 0.63 | 0.22 / 0.17 / 0.14 | 0.878 / 0.877 / 0.875 | 0.03 / 0.07 / 0.13 |
| Smaller class, scaled awards (141.9) | 0.05 / 0.10 / 0.15 | 121-162 / 113-171 / 103-181 | 0.54 / 0.53 / 0.52 | 0.06 / 0.10 / 0.10 | 0.312 (all) | 0.02 / 0.05 / 0.11 |

**Readout.**
- **Class range.** Going from s = 0.065 to 0.10 widens the 90% class range by 11 to 13 students. P(class > cap) moves toward 0.5, by 1 to 5 points.
- **P(class in band)** changes by 2 to 5 points. It falls in four scenarios and rises in the one whose mean sits outside the band.
- **P(NTR ≥ target)** roughly doubles in these tail cases.
- **P(median holds) at ρ = 1 barely moves.** The shock term is s² × margin², and the margin is near zero. At ρ = 0.5 it moves more: Baseline at 165 reads 0.333, 0.352 and 0.373 at s = 0.05, 0.10 and 0.15.
- **Recommended value.** It equals the current illustrative value, so with s = 0.10 the computed figures do not change. Only the source and the label change.

## 9. What public data cannot calibrate

- **ρ (`shock_corr_above_below`)**, the correlation between the year shocks of high-score and other admits. The 509 reports offers and enrollees for the whole school, not by score band. ρ stays at 1 with the 0.5 sensitivity line.
- **Cell-level structure:** whether a common shock is the right form, segment- or residency-specific shocks, and idiosyncratic cell shocks beyond binomial noise (school totals average these away).
- **How much of a school's yield change is planned mix** (admits moved between bands) versus shock. The admit-rate control is a partial proxy, and it is endogenous to within-cycle waitlist decisions.
- **The persistence form** (random walk versus trend), whether s varies over time, and which part a client sees before it re-prices.
- **Price response, marginal-admit yield and pool variation.** Application-volume variation could be calibrated from the same files, but it was not part of this task.
- **A client's own s**, until five cycles of its own out-of-time errors exist (methodology section 6).

## 10. Not verified

- The ABA 509 definitions were not read. This covers the meaning of SchoolYear and the 2025 enrollee discrepancy. The fall-cohort reading rests on the 2023-2024 `SchoolYear` column, application totals and third-party pages.
- The 2011 to 2020 compilations were not obtained (backend download blocked).
- The local crosswalk was not checked against the 509 repo's Supabase crosswalk, which was not opened. Mismatches would show as size jumps, and the 18 found were explained.
- The closure and consolidation readings are inferred from the data (stopped reporting, class changes), not from ABA notices.
- IPEDS X-flags: only reported values (R) were kept. Imputation rules were not reviewed further, and ADM2024 is unpublished.
- The multiplicative slopes have no bootstrap interval. The national component's interval is a chi-square approximation that ignores sampling noise.
- World W22 (methodology section 10, O37: "test in W22") was not built or run.
- The synthetic sensitivity used seed 101 only and the closed forms, not the exact distributions.
- The prototype test suite was not run (no prototype code changed).
- Searches used general terms only; no client name was searched.

Before any of this leaves Frankel, check that it holds no client confidential information. It was built from public data only, and it needs human review before it goes to a client.
