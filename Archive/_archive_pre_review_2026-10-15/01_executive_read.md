# EFA + FAO v2: Executive Read

**Status:** Foundation built and validated on synthetic data. Dashboard is the next build phase.
**Audience:** Research + Insights leadership, then client enrollment teams and executives.

## Bottom line

The prior EFA + FAO deliverables answered a useful question (what predicts enrollment?) but could not answer the question clients pay to have answered (where should the next aid dollar go?). The aid result was effectively "no effect," and applying that conclusion literally would have cost the college about 65 students and 5.6% of four-year net tuition revenue in our test world.

Version 2 fixes the cause. It treats aid as a causal question, uses a randomized price test and the merit grid to anchor the answer, optimizes net tuition revenue under a budget, and reports honest uncertainty. In a synthetic institution where we know the truth, the recommended allocation beats the status quo by about **7 enrolled students and 1.8% of four-year NTR (about $0.42M for one cohort) at the same actual spend**. A perfectly informed allocator would gain 6.0%. We also found that the model's own predicted gain is about six times larger than the gain that materializes, so every projection now ships with a backtested "planning" figure next to the raw model figure.

## What the prior work did

- **Pipeline:** Excel uploads, then Stata do-files (import, cleaning, analysis), then regression tables exported to Excel, then a Tableau workbook with hard-coded coefficients behind a "Matriculation Probability Calculator."
- **Models:** logistic regressions for inquiry-to-application and admit-to-enroll, reported as marginal effects at the means. The "FAO" was one extra term (institutional aid in $1,000s) in the admit-to-enroll model for the two terms that had aid data.
- **Delivery:** a deck plus an interactive dashboard that showed student-level rows to Tableau.

## Gaps we found, and what v2 does about each

Evidence levels: **Verified** means read directly in code or output. **Hypothesis** means plausible but needs a data check.

| # | Gap | Evidence | v2 response |
|---|-----|----------|-------------|
| 1 | No optimization: no objective, budget, or allocation output | Verified (analysis do-file, decks) | NTR objective, budget and class-size constraints, discount cap, allocation by segment |
| 2 | Aid effect flipped between April and May deliverables (+0.74 points per $1,000, then about zero) | Verified (both decks) | Design-based anchor, bootstrap bands, versioned runs with lineage |
| 3 | Missing aid and EFC recoded to $0, so "$0 EFC" mixes true zero with no FAFSA | Verified (cleaning do-file) | Missing stays missing; "No FAFSA" is its own category; aid is zero only where the cohort has aid coverage |
| 4 | "Non-institutional aid" bundles grants, loans, and work-study | Verified | Twelve disaggregated components with offered, accepted, and disbursed amounts and dates |
| 5 | Non-institutional aid effect (+25 to +42 points) may reflect aid recorded after enrollment | Hypothesis | Only amounts known at the decision date enter price models; disbursed and accepted amounts are excluded by test |
| 6 | Aid is targeted, so a plain logit cannot give a price effect | Verified (UToledo deck found a negative aid coefficient) | Randomized bonus-aid arm plus regression discontinuity at merit-grid thresholds |
| 7 | Aid awards cluster in a few bands, leaving no data to learn a dose-response curve | Verified (predictor distributions) | Positive-only price test spreads awards; data request asks for the merit grid |
| 8 | Transfer aid model had 125 observations | Verified | Minimum-sample rule; small segments are pooled or suppressed rather than modeled |
| 9 | No out-of-sample validation, no calibration check, no student-level clustering | Verified | Time-split backtest, calibration, clustered standard errors |
| 10 | Fragile code: absolute paths, hard-coded dates and concordances, a one-student patch by ID, three upload versions | Verified | Config-driven pipeline, hashed inputs, explicit rule log with row counts |
| 11 | Race and gender used as predictors in an aid context | Verified | Protected attributes are audit-only and are blocked from models by a test |
| 12 | Student-level data shipped inside the dashboard | Verified (35 MB student-level feed) | Aggregates only, minimum cell size 10, complementary suppression, enforced in the database |

Not opened: the Tableau workbooks, the `.dta` files, and the Analysis-phase do-files (inferred from decks and file sizes).

## What v2 changes

1. **One model forecasts, another intervenes.** The forecast model keeps predictive accuracy (AUC 0.83). The price-response model answers "what if we change aid," using only design-based evidence.
2. **Evidence hierarchy.** Randomized price test and merit-grid discontinuity set the level of price sensitivity. Observational data supply only the relative pattern across segments, shrunk toward uniform by its estimated reliability.
3. **Real objective.** Maximize multi-year net tuition revenue subject to a discretionary budget, an optional class-size floor, and a discount cap.
4. **Guardrails.** No student's discretionary award falls by more than $3,000 (configurable). Athletes keep current packages. Protected attributes never enter allocation.
5. **Honest numbers.** Every scenario shows a raw model estimate, a backtested planning estimate, and a bootstrap band.
6. **Privacy by construction.** Student-level data never reaches Supabase.

## Proof of value (synthetic world, truth known)

Backtest on the 2026 cohort (1,966 admits), models fit on 2022 to 2025. Every strategy is tuned to the **same actual discretionary spend ($0.88M)** and scored against the true behavior.

| Strategy | Enrolled vs status quo | Four-year NTR vs status quo |
|----------|-----------------------:|----------------------------:|
| Legacy conclusion applied literally (cut discretionary aid) | -64.7 | -$1.26M (-5.6%) |
| Observational model alone, optimized | -24.2 | -$0.34M (-1.5%) |
| **v2 hybrid model, optimized (recommended)** | **+7.5** | **+$0.42M (+1.8%)** |
| Perfect-information upper bound | +13.3 | +$1.37M (+6.0%) |

Sensitivity: across shrinkage settings from 0 to 0.9 the recommended gain stays between +1.7% and +2.7%.

**Where the aid effect comes from.** True effect: +1.49 points of yield per $1,000. Legacy spec: about zero. Controlled observational logit: +0.19. Price test alone: +0.63 (95% interval -0.46 to 1.72). Merit-grid discontinuity: +2.22 (0.63 to 3.81). Pooled anchor: +1.14 (0.24 to 2.04).

**Leakage check.** The legacy-style model reaches AUC 0.99 because it uses aid disbursed after enrollment. That number is impressive and useless at decision time. The decision-time model reaches AUC 0.83.

## What this does not prove

- All numbers come from a synthetic institution built to have recoverable structure. They validate behavior of the method, not results for any real college.
- At this college size a single price test is underpowered: four cohorts and 1,917 students give a standard error of 0.56 points. Smallest effect it could reliably detect is about 1.6 points per $1,000. Plan on three to four cycles, or a larger test share.
- Reallocation gains are modest. The headline benefit is avoiding wrong conclusions and learning faster, with real but smaller reallocation gains.
- The model's predicted gain overstates the realized gain (realization ratio 0.17 in the backtest). On real data the ratio must be estimated from the price-test arm and historical backtests.

## Equity and policy flags to review

- The unconstrained optimizer cut discretionary aid for international students by about 93%, because they are price-insensitive. With the $3,000 guardrail the cut is about 62% (from $2,176 to $830 on average). Leadership should decide whether to add a floor.
- Highest-need students gain the most (average discretionary award from $3,666 to $4,996), lower-need students lose the most ($1,384 to $332). That matches the economics but needs a policy conversation.
- Black or African American admits see slightly higher average awards and expected yield under the recommendation, but race is audit-only and never used in allocation.

## Data and IP note

The synthetic data were built from aggregate shapes (funnel rates, mix, award bands) printed in prior deliverables. No student records were copied. The prior engagements' student-level files should not be used as test data until rights are confirmed with the original clients and former employer.

## Decisions needed

1. Approve the synthetic world as the demo dataset and the "planning estimate" convention (raw model figure shown only as an upper bound).
2. Choose a policy stance on guardrails (maximum cut, any segment floors).
3. Decide whether a price test is offered as part of every engagement (recommended) and who approves it on the client side.
4. Confirm dashboard audiences: enrollment team (full), leadership (headline scenarios only).
