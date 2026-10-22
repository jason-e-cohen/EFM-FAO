# EFA + FAO v2.1: Executive Read

**Status:** v2 foundation built and validated on synthetic data. After an independent review (October 2026), v2.1 simplifies the model; the simplifications are specified and not yet built. Dashboard follows.
**Audience:** Research + Insights leadership, then client enrollment teams and executives.

## Bottom line

The prior EFA + FAO deliverables answered a useful question (what predicts enrollment?) but could not answer the question clients pay to have answered (where should the next aid dollar go?). The aid result was effectively "no effect," and applying that conclusion literally would have cost the college about 65 students and 5.6% of four-year net tuition revenue in our test world.

v2 fixed the cause by anchoring price sensitivity in a randomized price test and the merit grid. The review then found that much of v2's added sophistication was not helping. In the backtest, the simplest setting (one price-sensitivity slope for every student) produced a larger realized gain, **+$0.60M (+2.7%) in four-year revenue**, than the v2 recommended setting (+$0.42M, +1.8%), at roughly the same spend. v2's estimates of how sensitivity differs across segments were precise but wrong in size.

**v2.1 is rigorous at one point and simple everywhere else.** The level of price sensitivity still comes from design-based evidence, which is what the legacy work and competing logistic-regression approaches cannot recover when aid is targeted. Around it, v2.1 uses one slope, recommends a scholarship policy grid instead of per-student awards, and reports uncertainty as three plain sensitivity scenarios.

All figures come from one synthetic institution and one random seed. A Monte Carlo study across eight synthetic worlds is the acceptance test for v2.1.

## What the prior work did

- **Pipeline:** Excel uploads, then Stata do-files (import, cleaning, analysis), then regression tables exported to Excel, then a Tableau workbook with hard-coded coefficients behind a "Matriculation Probability Calculator."
- **Models:** logistic regressions for inquiry-to-application and admit-to-enroll, reported as marginal effects at the means. The "FAO" was one extra term (institutional aid in $1,000s) in the admit-to-enroll model for the two terms that had aid data.
- **Delivery:** a deck plus an interactive dashboard that showed student-level rows to Tableau.

## Gaps we found, and what v2.1 does about each

Evidence levels: **Verified** means read directly in code or output. **Hypothesis** means plausible but needs a data check.

| # | Gap | Evidence | v2.1 response |
|---|-----|----------|---------------|
| 1 | No optimization: no objective, budget, or allocation output | Verified (analysis do-file, decks) | Revenue objective with budget, class-size, and discount constraints; output is a scholarship policy grid |
| 2 | Aid effect flipped between April and May deliverables (+0.74 points per $1,000, then about zero) | Verified (both decks) | Design-based anchor, sensitivity scenarios, versioned runs with lineage |
| 3 | Missing aid and EFC recoded to $0, so "$0 EFC" mixes true zero with no FAFSA | Verified (cleaning do-file) | Missing stays missing; "No FAFSA" is its own category |
| 4 | "Non-institutional aid" bundles grants, loans, and work-study | Verified | Aid disaggregated by component (institutional, federal, state, external, and each loan type, including Grad PLUS) with offered, accepted, and disbursed amounts and dates |
| 5 | Non-institutional aid effect (+25 to +42 points) may reflect aid recorded after enrollment | Hypothesis | Only amounts known by the defined decision date enter price models |
| 6 | Aid is targeted, so a plain logit cannot give a price effect | Verified (UToledo deck found a negative aid coefficient) | Randomized bonus-aid test plus merit-grid discontinuity |
| 7 | Aid awards cluster in a few bands, leaving no data to learn a dose-response curve | Verified (predictor distributions) | Price test with arms at $0, $2,000, and $4,000 |
| 8 | Transfer aid model had 125 observations | Verified | Minimum-sample rule; small segments are pooled or suppressed |
| 9 | No out-of-sample validation, no calibration check, no student-level clustering | Verified | Out-of-time backtest, recalibration, clustered standard errors |
| 10 | Fragile code: absolute paths, hard-coded dates and concordances, a one-student patch by ID, three upload versions | Verified | Config-driven pipeline, hashed inputs, explicit rule log with row counts |
| 11 | Race and gender used as predictors in an aid context | Verified | Protected attributes are audit-only and blocked from models by a test |
| 12 | Student-level data shipped inside the dashboard | Verified (35 MB student-level feed) | Aggregates only, cells under 10 suppressed, enforced in the database |

Not opened: the Tableau workbooks, the `.dta` files, and the Analysis-phase do-files (inferred from decks and file sizes).

## What v2.1 changes from v2

1. **One price slope, anchored.** The randomized test and the merit grid set the level. The segment pattern from historical data, its shrinkage weight, and the rescaling step are removed.
2. **A policy, not a list.** The optimizer sets award levels for about 75 grid cells (academic index x need band x residency) that staff can apply as offers roll out and counsel can review.
3. **Plain uncertainty.** Each scenario shows results if students are less, about as, or more price-sensitive than estimated. The bootstrap, the probability-of-improvement figure, and the scaled "planning estimate" are retired.
4. **A stronger, same-cost price test.** Arms at $0, $2,000, and $4,000 (40% / 20% / 40%) cut the standard error by about a fifth at the same average cost.
5. **Lighter onboarding.** A Tier 1 data request (three cohorts, final packages) supports the funnel, forecast, and monitoring work; the full request is needed for the aid optimization.
6. **New descriptive layers.** In-cycle pacing and melt monitoring, loan-cap exposure, where non-enrolling admits went (Clearinghouse match), an admitted-student survey, and peer pricing.

## Proof of value (synthetic world, truth known; v2 build)

Backtest on the 2026 cohort (1,966 admits), models fit on 2022 to 2025, scored against the true behavior.

| Strategy | Discretionary spend | Enrolled vs status quo | Four-year revenue vs status quo |
|----------|--------------------:|-----------------------:|--------------------------------:|
| Status quo | $0.88M | — | — |
| Legacy conclusion applied literally (cut discretionary aid) | $0 | -64.7 | -$1.26M (-5.6%) |
| Historical-data model alone, optimized | $0.48M | -24.2 | -$0.34M (-1.5%) |
| v2 recommended (segment pattern, kappa 0.72) | $0.88M | +7.5 | +$0.42M (+1.8%) |
| **One anchored slope (basis for v2.1)** | **$0.89M** | **-1.5** | **+$0.60M (+2.7%)** |
| Perfect-information upper bound | $0.89M | +13.3 | +$1.37M (+6.0%) |

The first two comparison rows did not spend the same amount, so their gaps mix model error with underspending. The one-slope result buys revenue at a cost of about 1.5 students; a class-size floor can trade some revenue back for headcount. v2.1's policy grid has not yet been run; this row is the per-student optimizer with one slope.

**Where the aid effect comes from.** True effect: +1.49 points of yield per $1,000. Legacy spec: about zero. Historical-data logit: +0.19. Price test alone: +0.63 (95% interval -0.46 to 1.72). Merit-grid discontinuity: +2.22 (0.63 to 3.81). Pooled anchor: +1.14 (0.24 to 2.04).

**Leakage check.** The legacy-style model reaches AUC 0.99 because it uses aid disbursed after enrollment. The decision-time model reaches AUC 0.83.

## What this does not prove

- All numbers come from one synthetic institution and one seed. They show how the method behaves, not results for any real college. The Monte Carlo study (methodology section 10) is the test.
- At this college size the v2 price test was underpowered: standard error 0.56 points per $1,000, smallest reliably detectable effect about 1.6, below the true 1.49. The redesigned arms bring this to about 1.2. Plan on several cycles.
- Reallocation gains are modest (about 2 to 3% of four-year revenue here). The larger benefit is avoiding wrong conclusions, such as "aid doesn't matter."
- Price evidence comes from bonuses. How students react to communicated cuts is not measured, so v2.1 only lets awards rise on revisions and renewals.
- The forecast overpredicted yield by about 4% (about 16 students on 1,966 admits). Recalibration is required before projections are shown.

## Equity and policy flags to review

- **Retracted:** the v2 finding that international students are price-insensitive (and the 62 to 93% cut it drove) was an estimation artifact. The v2 estimate was 0.18 points per $1,000; the truth in the synthetic world was 1.34, close to the overall average.
- The v2 shift toward highest-need students ($3,666 to $4,996 average) and away from lower-need students ($1,384 to $332) partly reflects overstated sensitivity for the highest-need group. Both flags must be re-run under v2.1 before any policy conversation.
- Grid cells use policy attributes only, but need band and geography can act as proxies; the equity audit is reviewed with every recommendation.
- No consumer credit data is used.

## Competitive position

A competitor deck (EAB) shows a broader service: graduate programs and loan-cap risk, weekly in-cycle monitoring, melt, net-cost positioning, tuition pricing, and a documented scholarship policy. Its method is a logistic regression on prior years' awards, which is the approach that misreads price sensitivity when aid is targeted, and its simulations show point estimates without intervals. v2.1 adopts the service elements that are cheap and useful (policy grid, monitoring, melt, loan-cap exposure, pricing scenarios) and differentiates on three things: a design-based price anchor, Clearinghouse destination data joined to peer net price, and admitted-student survey evidence on competing offers. It does not adopt consumer credit matches or student-level downloads from a hosted dashboard.

## Data and IP note

The synthetic data were built from aggregate shapes (funnel rates, mix, award bands) printed in prior deliverables. No student records were copied. The prior engagements' student-level files should not be used as test data until rights are confirmed with the original clients and former employer.

## Decisions needed

1. Approve v2.1's simplifications, with the Monte Carlo study as the acceptance test.
2. Approve the policy grid (default 75 cells) as the client deliverable in place of per-student awards.
3. Choose a policy stance on guardrails: maximum cut per cell, segment floors, increases-only for revisions and renewals.
4. Decide whether a price test is offered in every Tier 2 engagement (recommended) and who approves it on the client side.
5. Approve the new descriptive layers for the first pilot: monitoring, loan-cap exposure, Clearinghouse match, admitted-student survey.
6. Confirm dashboard audiences: enrollment team (full), leadership (headline scenarios only).
