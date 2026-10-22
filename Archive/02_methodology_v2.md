# EFA + FAO v2.1: Methodology (lean model)

**Status:** Specification. v2.1 replaces the v2 estimator and optimizer with a simpler design after an independent review (October 2026). Results quoted here come from the v2 build on synthetic data unless marked otherwise; items marked **[to build]** are not yet implemented. The v2 text is archived in `_archive_pre_review_2026-10-15/`.

**Design principle:** be rigorous at the one point where simplicity loses the answer (the level of price sensitivity) and simple everywhere else.

## 1. Scope

Two linked products and one monitoring layer share one data model.

- **EFA (enrollment funnel analysis):** where do prospects drop out, and what predicts movement through inquiry, application, admit, deposit, and enrollment at census?
- **FAO (financial aid optimization):** given the projected admitted pool, a budget, and goals, what award policy should the institution use for discretionary aid?
- **Monitoring [to build]:** during the cycle, how is the class pacing against last year and the plan, and where is melt risk?

Undergraduate first-time and transfer cohorts are in scope now. Graduate and professional programs are in scope for the descriptive layers (funnel, pacing, loan-cap exposure) and enter the price model only once a program has its own price evidence.

## 2. Funnel analysis

**Stages:** inquiry, application, admit, deposit, enrolled at census. Stealth applicants (application is the first touch) skip the inquiry stage and are flagged, not dropped. Deposit to census is reported as its own stage so melt is visible.

**Descriptive layer:** a fixed, published set of tables: each dimension by cohort, and a short list of approved two-way tables pooled across cohorts. Tables are designed not to overlap in ways that allow suppressed cells to be recovered by subtraction. Cells with fewer than 10 students are suppressed. [Simplified from v2, which published all one-way and all two-way tables with complementary suppression.]

**Driver layer:**
- Inquiry to application: logit with clustered standard errors on non-stealth inquiries, reported as average marginal effects in percentage points with confidence intervals.
- Admit to enroll: effects of non-price attributes from the forecast model, with intervals, labeled **associational**.

**Academic index [to build]:** one composite of GPA and test scores (test-optional handled inside the index), reported in quintiles. It replaces separate GPA, test, and missing-test terms in the forecast model and defines grid rows in the optimizer.

## 3. Data model

Aid arrives in long form: one row per student, fund, and package version, with offered, accepted, and disbursed amounts and dates.

| Class | Components | Used in price models |
|-------|-----------|----------------------|
| Institutional gift | merit, need, athletic, discretionary, other | Yes, if offered by the decision date |
| Other gift | state, Pell, SEOG, external | Yes, if known at the decision date |
| Self-help | subsidized, unsubsidized, Parent PLUS, Grad PLUS, private or institutional loan, work-study | Never as price reduction; used in the loan-cap exposure layer (section 8) |
| Post-decision fields | accepted, disbursed | **Never** (leakage) |

**Net cost** = cost of attendance minus gift aid known at the decision date. **Institutional net tuition** = tuition and fees minus institutional gift aid. Need index is EFC through 2023-24 and SAI from 2024-25, labeled by type; "No FAFSA" is a separate category. Institutional-methodology need (CSS Profile) is accepted where the client uses it.

**Decision date** means the student's deposit deadline or the date the student deposited, whichever is earlier. Any award or revision dated after it is excluded from price models. Revisions before it are kept with their dates and logged as revisions.

**Excluded groups [to build]:** a configurable table (athletes, tuition waivers and exchanges, special scholarships, others the client names). Excluded students keep current packages, are left out of price estimation, and are reported separately so class totals reconcile.

**Data tiers [to build]:**
- **Tier 1 (minimum):** three cohorts, final packages by component, offer dates where available, merit grid. Supports EFA, the forecast, monitoring, and a discontinuity-only price anchor with wider bands.
- **Tier 2 (full):** four to five cohorts, every package version with dates, merit grid with effective dates, and a price test. Supports the full FAO.

## 4. Price response

### The problem

Aid is not random. Staff give more discretionary aid where they see weaker interest, so a regression on historical awards can show that more aid goes with lower yield. In the synthetic world the correlation between discretionary aid and unobserved interest is -0.41. The legacy-style model recovers -0.01 points per $1,000 and a controlled observational logit recovers +0.19, against a true effect of +1.49.

### Evidence sources

1. **Randomized bonus-aid test (primary).** A random share of eligible admits receive extra discretionary aid. Positive-only: nobody receives less than they otherwise would.
   - **Arms [changed]:** $0, $2,000, and $4,000, assigned 40% / 20% / 40%. Average cost per test student is unchanged from v2 ($2,000), but spreading doses to the ends lowers the standard error of the slope. At v2's sample (1,917 test students over four cohorts) the approximate standard error falls from 0.56 to 0.44 points per $1,000, and the smallest effect detectable with 80% power falls from about 1.6 to about 1.2. A $0 / $4,000 two-arm design would reach about 0.39 but gives up the check on linearity. These figures assume the slope's standard error scales with the spread of doses; confirm in the Monte Carlo study.
   - **Stratified assignment:** randomize within need band and residency so later cycles can estimate segment differences (section 11).
   - **Compliance check:** compare other discretionary aid between arms to detect staff offsetting the bonus.
2. **Merit-grid regression discontinuity (secondary, optional).** Used only where a published threshold has a meaningful award jump and passes diagnostics.
   - Use a standard package (`rdrobust` or equivalent) with data-driven bandwidth and bias-corrected intervals, not a hand-built fixed window.
   - Run a density (manipulation) test and placebo thresholds. Drop the discontinuity if either fails.
   - Divide the enrollment jump by the **net-cost** jump, not the award jump, so merit awards that displace need aid are handled.
   - In the synthetic run the 3.2 GPA threshold carries almost all the information (standard error 1.1 points per $1,000 versus 1.5 to 3.5 at the other three).

The controlled observational model is **no longer a price source**. It is used only as the forecast model (below).

### Anchor

Report the experiment and the discontinuity separately. Pool them by inverse variance into one **anchor** (average effect, percentage points per $1,000), and flag the result when the two disagree by more than 1.5 standard errors. With a Tier 1 client and no test, the anchor is the discontinuity alone and is labeled local.

Synthetic results (v2 build): experiment +0.63 (95% interval -0.46 to 1.72), discontinuity +2.22 (0.63 to 3.81), pooled anchor +1.14 (0.24 to 2.04), truth +1.49.

*Judgment call:* pooling versus experiment-only. Pooling is defensible while the two estimates are statistically compatible and the discontinuity passes diagnostics. What would change this: placebo or density failures, or repeated disagreement across cycles.

### Response model

One slope for everyone, on the logit scale:

`p(d) = expit( logit p_forecast(current award) + beta * (d - current award) )`

- **Forecast model:** a regularized logit with a fixed feature set of about 10 to 12 terms (academic index, need band, residency, program, decision type, application timing, campus visit, engagement, first-generation status, stealth flag). Protected attributes are excluded. Recalibrate on an out-of-time cohort before use.
- **beta** converts the anchor to the logit scale: beta = anchor / mean of p(1 - p) over the anchor's sample. A test asserts that the model's average effect on that sample equals the anchor within 1%. (In v2 the hybrid's average was 1.40 against an anchor of 1.14; this test closes that gap.)
- A single logit slope is not a single percentage-point effect. Students near 50% yield respond most in points, so the model still targets undecided students without estimating segment differences.
- **Support:** for communicated offers (revisions and renewals) awards may only rise, and by no more than the largest tested bonus. For first offers, cuts relative to the current grid are allowed only within the guardrail in section 5.

**Why one slope:** in the v2 backtest the uniform slope (kappa = 0) produced the highest realized revenue gain of any setting: +$0.60M (+2.7%) versus +$0.42M (+1.8%) for the v2 recommended setting. The v2 segment pattern was precise but wrong in size (for example, international students estimated at 0.18 against a true 1.34). One synthetic seed; to be confirmed in section 10.

## 5. Optimization: policy grid

**Decision [changed]:** an award level for each cell of a policy grid, not for each student. Default grid: academic index quintile (5) x need band (5, including No FAFSA) x residency (3) = 75 cells, on a $1,000 ladder from $0 to $12,000 (about 1,000 binary choices instead of about 25,000). Cells are configurable but must use policy attributes only.

Why: offers go out on a rolling basis, so a policy staff can apply at packaging time is more usable than a list of awards for a pool that is not yet known. A grid is also documentable for counsel, and fewer free choices leave the optimizer less room to exploit model error.

**Objective:** expected multi-year institutional net tuition revenue, the sum over students of `P(enroll | cell award) x (tuition - institutional aid) x persistence factor`. The persistence factor is a lookup of historical retention by segment summed over four years.

**Constraints**
- Discretionary spend at most the budget, checked at all three sensitivity scenarios (section 6). The budget horizon is set in the configuration and must match the revenue horizon (year one, or four years for renewable awards).
- Optional expected class-size floor, checked at all three sensitivity scenarios.
- Institutional aid at most 75% of tuition per student; optional cap on the class-wide discount rate.
- No cell's award falls more than $3,000 below its current-grid level (configurable).
- Excluded groups keep current packages.

**Choice rule:** maximize revenue at the middle sensitivity scenario, subject to the revenue gain over the status quo staying at or above zero at the low scenario.

**Solver:** multiple-choice knapsack as a mixed-integer program (HiGHS).

**Scenarios shipped:** budget at 0.75x, 1x, and 1.25x; headcount-maximizing at 1x; a class-floor scenario only where the floor binds (report its shadow price). **Tuition scenarios [to build]:** a change in sticker price, applied as a change in net cost for the admitted pool. Labeled "admit stage only" because the model does not capture effects on who applies. No sticker-price optimization.

**Outputs:** the recommended grid, a scholarship policy document, and projected class, revenue, spend, and discount rate under each scenario.

## 6. Uncertainty and honesty [changed]

- **Three sensitivity scenarios:** with one price parameter, uncertainty is one-dimensional. Every scenario is evaluated at beta low, middle, and high (10th, 50th, and 90th percentiles of the anchor's interval) and shown as "gain if students are less, about as, or more price-sensitive than estimated." This replaces the v2 40-draw bootstrap, the probability-of-improvement figure, and the scaled planning estimate.
- **Forecast uncertainty:** class projections carry an interval from the out-of-time calibration error.
- **Backtest diagnostic:** each engagement runs one out-of-time backtest and reports realized versus predicted gain. It is a check on the model, not a multiplier applied to the headline. In v2 this ratio was 0.62 for the uniform slope and 0.17 for the v2 recommended setting, which is why the multiplier is dropped together with the segment pattern that drove it.

## 7. Monitoring layer [to build]

- **Pacing:** admits, deposits, revenue, and discretionary spend against the same date last year and against plan.
- **Projected census:** current counts by stage times historical stage-to-census conversion rates by days to deadline (a lookup table, not a new model), with an interval from prior-year spread.
- **Melt:** historical deposit-to-census rates by a few flags known at deposit (housing application, verification selected, unmet need above a threshold, FAFSA not received). Segment-level in the dashboard. Any student-level list goes back to the client through their secure channel, never the hosted dashboard.
- **Refresh:** weekly or biweekly client export during yield season.
- **Treatment log:** every mid-cycle award revision is recorded with date and reason, so it can be separated from the price estimate the following year.

## 8. Descriptive differentiators [to build]

Descriptive only. None of these enters the price model or the decision-time forecast.

- **Loan-cap exposure.** Grad PLUS closed to new borrowers on July 1, 2026, and new annual and aggregate caps apply to graduate and professional borrowing and to Parent PLUS (per public summaries; confirm current limits with Federal Student Aid). Report, by program and segment, how many admits relied on PLUS in prior cohorts and how many dollars now sit above the caps. Translate the uncovered amount into a revenue range using the three sensitivity scenarios, with the caveat that our price evidence comes from gift aid, not loan access. Once fall 2026 outcomes arrive, compare 2025 to 2026 changes for high-reliance versus low-reliance segments.
- **Where non-enrolling admits went.** A National Student Clearinghouse match ordered by the client, joined to IPEDS and College Scorecard net price by income band, gives "lost to" institutions and net-cost gaps by segment.
- **Admitted-student survey.** Enrolling and non-enrolling admits report competing offers and reasons. This gives measured competitor offers for a sample.
- **Peer pricing comparison.** Sticker price and net price by income band against a client-approved peer set, from IPEDS.

## 9. Equity and legal guardrails

- Race, ethnicity, and gender are **never** model inputs. A test enforces it.
- No consumer credit data (credit scores or bureau matches). They would require identified records, their permissible use for aid decisions is unclear, and they are strong proxies for race. Ability to pay comes from FAFSA, CSS Profile, observed borrowing, and optional public Census tract indicators appended by the client before de-identification.
- Grid cells use policy attributes only. Need band, geography, and residency can still act as proxies, so the audit table compares status quo and recommended policies by group (average award, expected yield, expected discount rate, share receiving an increase) and is reviewed with every recommendation.
- Counsel review is required before using any recommendation.

## 10. Validation plan

| Layer | Synthetic (truth known) | Real clients |
|-------|-------------------------|--------------|
| Price anchor | Bias and interval coverage across seeds | Experiment versus discontinuity; diagnostics |
| Forecast | Holdout AUC, Brier, calibration | Out-of-time holdout by cohort |
| Policy value | Realized gain at matched spend against baselines | Backtest; policy evaluation on the test arm |
| Leakage | Planted-leak detection | Field-timing checks on every dated field |
| Disclosure | Tests on all published tables | Same, plus manual review before publish |

**Baselines** (spend matched within 1%): status quo; proportional rescale of current awards; need-first fill; a "fence-sitter" rule (top up admits with forecast yield between 0.3 and 0.6); v2 per-student optimizer; perfect-information oracle.

**Lean Monte Carlo study [to build]**, run at each release, not per engagement. Eight synthetic worlds: baseline; targeting that differs by segment; large heterogeneity on unobserved traits; response that flattens above $6,000; cuts that hurt twice as much as increases help; a prestige bump at merit thresholds; a small college (600 admits per cohort, 15% test share); sensitivity drifting 25% between cohorts. Fifty seeds each.

Pass thresholds in the baseline world:
- Anchor bias at most 10% of truth; 95% intervals cover truth in 90% to 98% of seeds.
- Realized revenue gain positive in at least 90% of seeds.
- Lean model matches or beats the v2 optimizer in at least 60% of seeds, with an average shortfall of no more than 0.5 percentage points of revenue gain.
- Realized spend above 105% of budget in no more than 5% of seeds.
- Projected class within 2% of realized in at least 90% of seeds.

In the other seven worlds, failures are documented, and a diagnostic (anchor disagreement flag, discontinuity tests, backtest diagnostic) must flag at least 80% of the worlds where the method fails.

## 11. Future refinements (deferred)

Added only when the data support them and the Monte Carlo study shows a gain over the lean model.

| Refinement | Trigger to add it |
|-----------|-------------------|
| Segment price differences from stratified randomization, pooled hierarchically | Three or more test cycles; segment estimates beat a single slope in held-out revenue |
| Adaptive price tests across admit waves | A client with several admit waves and a standing test |
| Worst-case-average (CVaR) budget constraints and posterior-draw optimization | Segment differences adopted, so uncertainty is no longer one-dimensional |
| Settings chosen by cross-fitted realized value | More than one tuning setting remains |
| Loan-access response estimated from the 2026 cap change | Fall 2026 census data available |
| Sticker-price optimization | Evidence on applicant-pool response |
| Year-specific retention | Three or more years of retention per cohort |
| Time-varying treatment (revisions and appeals) | Treatment log in place for at least one cycle |

## 12. Known limitations

- Price response is logistic in net cost, with one slope; real behavior may show kinks or saturation.
- Positive-only tests do not show how students react to communicated cuts; the support rule in section 4 limits exposure.
- Retention is a historical lookup that does not respond to aid.
- No cost-to-serve model; the objective is net tuition revenue, not contribution margin.
- Competitor offers are observed only for survey respondents.

## Appendix A. What changed from v2 and why

| v2 feature | v2.1 | Evidence |
|-----------|------|----------|
| Observational segment pattern, shrinkage (kappa), scaling and refit | Cut; one anchored slope | Uniform slope +2.7% versus +1.8% realized in the backtest |
| Hybrid forecast-plus-intervene model | Kept in the simpler form above | Forecast accuracy identical either way (AUC 0.833) |
| Discontinuity with fixed 0.12 window | Standard package, diagnostics, net-cost denominator; optional | One threshold carries most information |
| Test arms $0 to $4,000 in $1,000 steps | 40/20/40 at $0, $2,000, $4,000; stratified | Same cost, about 0.44 versus 0.56 standard error |
| Per-student optimizer | 75-cell policy grid | Usable at packaging time; less overfitting |
| 40-draw bootstrap, probability of beating status quo, realization multiplier | Three sensitivity scenarios; backtest as a diagnostic | Probability read 100% at every budget from 1x to 2x; ratio ranged 0.14 to 0.62 |
| Expected-value budget | Budget checked at all three scenarios | Bootstrap 95th-percentile spend was 2.8x the budget at 1x |
| Nine scenarios | Four, plus class floor only if it binds | The v2 class-floor scenario did not bind |
| All one-way and two-way tables | Fixed non-overlapping set | Differencing risk |

## Appendix B. Review findings and their status

| ID | Finding | Status in v2.1 |
|----|---------|----------------|
| F1 | Segment pattern wrong in size and order | Removed with the segment pattern |
| F2 | Recommended setting beaten by uniform slope | Uniform slope is now the default |
| F3 | Realization ratio does not carry over | Dropped as a multiplier |
| F4 | Budget holds only on average | Checked at all three scenarios; Monte Carlo threshold |
| F5 | Bands and probability uncalibrated | Replaced by three scenarios |
| F6 | Hybrid average does not equal the anchor | Conversion rule and test in section 4 |
| F7 | Validation from one seed | Lean Monte Carlo study, section 10 |
| F8 | Forecast overpredicts yield by about 4% | Out-of-time recalibration required |
| F9 | Comparisons not spend-matched | Baselines matched within 1% |
| F10 | Pooled estimates differ | Report both; flag at 1.5 standard errors; discontinuity diagnostics |
| F11 | Class-floor scenario does not bind | Shipped only when binding |
| F12 | Validation cannot see asymmetric response to cuts | Support rule; loss-averse Monte Carlo world |
| — | Leakage definition, proxy fairness, disclosure | Decision date defined; audit kept; table set simplified. Still to verify on real outputs |
