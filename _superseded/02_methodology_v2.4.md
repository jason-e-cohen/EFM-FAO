# EFA + FAO v2.4: Methodology (lean model, decisions merged)

**Status:** Specification. v2.1 replaces the v2 estimator and optimizer with a simpler design after an independent review (October 2026). Results quoted here come from the v2 build on synthetic data unless marked otherwise; items marked **[to build]** are not yet implemented. The v2 text is archived in `_archive_pre_review_2026-10-15/`. **v2.2** merges the October 15 decisions (horizon, history, price-test policy, client alignment gate, segment floors, labels) and flags open design issues for the S4 and S5 re-review (section 13). Additions are tagged **[v2.2]**. **v2.3** adds batch scoring and the policy lookup, geography and targeted objectives, the evidence audit, the price-test sample-size guide, and the decisions confirmed on October 20 (tagged **[v2.3]**). **v2.4** adds the ABA 509 market layer, program-length horizons, conditional-award persistence, timing by wave, and the boosted-model challenger rule (tagged **[v2.4]**).

**Design principle:** be rigorous at the one point where simplicity loses the answer (the level of price sensitivity) and simple everywhere else.

## 1. Scope

Two linked products and one monitoring layer share one data model.

- **EFA (enrollment funnel analysis):** where do prospects drop out, and what predicts movement through inquiry, application, admit, deposit, and enrollment at census?
- **FAO (financial aid optimization):** given the projected admitted pool, a budget, and goals, what award policy should the institution use for discretionary aid?
- **Monitoring [to build]:** during the cycle, how is the class pacing against last year and the plan, and where is melt risk?
- **Scoring and targeting add-ons [v2.3]:** batch enrollment-probability scores, a policy lookup, and targeted objectives by segment or market.

Undergraduate first-time and transfer cohorts are in scope now. Graduate and professional programs are in scope for the descriptive layers (funnel, pacing, loan-cap exposure) and enter the price model only once a program has its own price evidence.

## 2. Funnel analysis

**Stages:** inquiry, application, admit, deposit, enrolled at census. Stealth applicants (application is the first touch) skip the inquiry stage and are flagged, not dropped. Deposit to census is reported as its own stage so melt is visible.

**Descriptive layer:** a fixed, published set of tables: each dimension by cohort, and a short list of approved two-way tables pooled across cohorts. Tables are designed not to overlap in ways that allow suppressed cells to be recovered by subtraction. Cells with fewer than 10 students are suppressed. [Simplified from v2, which published all one-way and all two-way tables with complementary suppression.]

**Driver layer:**
- Inquiry to application: logit with clustered standard errors on non-stealth inquiries, reported as average marginal effects in percentage points with confidence intervals.
- Admit to enroll: effects of non-price attributes from the forecast model, with intervals, labeled **associational**.

**Academic index [to build]:** one composite of GPA and test scores (test-optional handled inside the index), reported in quintiles. It replaces separate GPA, test, and missing-test terms in the forecast model and defines grid rows in the optimizer.

**Geography [v2.3].** Home address enters as a derived **market**, never as an address. Before removing addresses, the client runs a script that returns the metropolitan or micropolitan area (CBSA code), state, ZIP3, and a distance-to-campus band; ZIP3 alone does not map cleanly to a metro area. The funnel is reported by market, with markets under 10 students pooled into an "other" tier. Optional descriptive layers: market penetration (enrolled students relative to public counts of high school graduates or population by market) and source effectiveness by market. Consumer segmentation (for example PRIZM) is an add-on the client appends at the same step. It is descriptive and used to target outreach. It enters the forecast only if the client elects it and the proxy audit allows it, and it never enters the aid grid by default.

**Market reference data (ABA 509) [v2.4].** For law schools, the public ABA 509 disclosures are an external reference dataset: class profile (LSAT and UGPA 25th, 50th, and 75th percentiles), applications, offers, matriculants, tuition and cost of attendance, grant percentiles and the share of students receiving grants, and conditional-scholarship counts. Confirm field definitions before use (recipients versus all students, full-time versus part-time, resident versus nonresident). Uses: (a) peer pricing and approximate net-price distributions in the market view; (b) a **market award gap**, approximated by **rank-matching**, so a student at the program's 75th percentile on LSAT and UGPA is compared with each peer's 75th-percentile grant (a strong assumption, so the gap is a candidate moderator and descriptive layer, never a slope); (c) prevalence and loss rates of conditional scholarships as a candidate mechanism; (d) a yield prior (matriculants per offer) where client history is thin; (e) public parameters for the law synthetic world. Limits: school-level only and one year behind, and cross-school regressions on these data are ecological and confounded, so they never set the price anchor. Each annual release is stored with its source, retrieval date, and definitions, and carries no student-level data.

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
- **Tier 2 (full):** four to five cohorts, every package version with dates, merit grid with effective dates, and, where the price-test screen recommends one, a price test (section 4). Supports the full FAO.
- **History [v2.2]:** request three to five cohorts. Three is the minimum and five is ideal. Include retention to the next fall, and to later falls where available.

## 4. Price response

### The problem

Aid is not random. Staff give more discretionary aid where they see weaker interest, so a regression on historical awards can show that more aid goes with lower yield. In the synthetic world the correlation between discretionary aid and unobserved interest is -0.41. The legacy-style model recovers -0.01 points per $1,000 and a controlled observational logit recovers +0.19, against a true effect of +1.49.

### Evidence sources

1. **Randomized bonus-aid test (primary when run; an add-on, not a core feature) [v2.3].** A random share of eligible admits receive extra discretionary aid. Positive-only: nobody receives less than they otherwise would.
   - **Arms [changed]:** $0, $2,000, and $4,000, assigned 40% / 20% / 40%. Average cost per test student is unchanged from v2 ($2,000), but spreading doses to the ends lowers the standard error of the slope. At v2's sample (1,917 test students over four cohorts) the approximate standard error falls from 0.56 to 0.44 points per $1,000, and the smallest effect detectable with 80% power falls from about 1.6 to about 1.2. A $0 / $4,000 two-arm design would reach about 0.39 but gives up the check on linearity. These figures assume the slope's standard error scales with the spread of doses; confirm in the Monte Carlo study.
   - **Stratified assignment:** randomize within need band and residency so later cycles can estimate segment differences (section 11).
   - **Compliance check:** compare other discretionary aid between arms to detect staff offsetting the bonus.
   - **Offered only where it pays off [v2.2]:** a suitability screen runs in scoping. It checks decision value (could learning price sensitivity change the allocation by more than the test costs), power (does the expected sample give a minimum detectable effect within about 1.5 times a plausible effect), alternative evidence (does the merit grid already give adequate precision), operations (can the aid office run it), and time to value (will results be used across at least two cycles, or can history be pooled). Outcomes are Recommend, Optional, or Not recommended, each with a stated reason. The client's VP or Director of Enrollment, or a Dean, decides per engagement. Without a test the anchor is the discontinuity alone, labeled local, with wider ranges (see also open issue O2).
2. **Merit-grid regression discontinuity (secondary, optional).** Used only where a published threshold has a meaningful award jump and passes diagnostics.
   - Use a standard package (`rdrobust` or equivalent) with data-driven bandwidth and bias-corrected intervals, not a hand-built fixed window.
   - Run a density (manipulation) test and placebo thresholds. Drop the discontinuity if either fails.
   - Divide the enrollment jump by the **net-cost** jump, not the award jump, so merit awards that displace need aid are handled.
   - In the synthetic run the 3.2 GPA threshold carries almost all the information (standard error 1.1 points per $1,000 versus 1.5 to 3.5 at the other three).

The controlled observational model is **no longer a price source**. It is used only as the forecast model (below).

### Evidence audit and price-test sample size [v2.3]

**Evidence audit (scoping).** Before proposing a test, audit the client's history for usable price variation: merit-grid thresholds with award jumps and enough admits near them; policy changes between cohorts (award schedules, tuition, new scholarships) with a comparison group; and natural experiments (competitions or cutoffs). Report the precision a history-only anchor would achieve. The one-page result feeds the suitability screen.

**What history can and cannot do.** A past cycle cannot be randomized. It can supply design-based evidence (thresholds, policy changes, natural experiments). It cannot set the price level from historical awards alone, because aid was targeted.

**Sample size.** For first-time admits outside excluded groups, with arms at $0, $2,000, and $4,000 (40/20/40) and covariate adjustment, the standard error of the slope is about `0.85 x sqrt(p(1 - p)) / (1.79 x sqrt(n))` in probability per $1,000, where n is the number of test students and p is the baseline yield. The smallest effect detectable with 80% power is about 2.8 times that. At 21% yield this is about `54 / sqrt(n)` points per $1,000. The formula reproduces the v2 prototype (1,917 test students, standard error 0.44, smallest detectable effect 1.2).

| Eligible admits per year | One cycle, 40% in test | Three cycles, 40% in test | One cycle, everyone in test |
|--------------------------|-----------------------:|--------------------------:|----------------------------:|
| 600 | 3.5 | 2.0 | 2.2 |
| 1,000 | 2.7 | 1.6 | 1.7 |
| 2,000 | 1.9 | 1.1 | 1.2 |
| 4,000 | 1.4 | 0.8 | 0.9 |

Values are the smallest detectable effect in points per $1,000. Assumptions to confirm in S4: 21% yield, a 0.85 covariate-adjustment factor, and a plausible true effect of 1 to 3 points per $1,000. At 10% yield the figures fall by about a quarter; at 40% yield they rise by about a fifth. About 1,300 test students are needed to detect 1.5 points.

**Screen rule (starting point; reviewer to re-evaluate).** Recommend a test when the smallest detectable effect after the planned cycles is at most about 2.3 points per $1,000 (1.5 times a plausible 1.5-point effect). Otherwise the outcome is Optional or Not recommended, with the reason stated.

**Cost.** Expected bonus cost per test student is about the mean bonus times the yield ($2,000 x 21%, about $420), less the revenue from any extra enrollment if aid works. At zero effect, 1,300 test students cost about $0.55M. At a 1.5-point effect (and about $20,000 of year-one net tuition per student) the test is roughly break-even. The cost is real but bounded, and it buys the price level that protects the whole discretionary budget.

### Timing and sensitivity by date [v2.4]

Whether price response changes through the cycle (early versus late offers, before and after deposit deadlines or negotiation windows) is learned from the client's own data, not from outside timing data.

- **Within the client's test:** stratify randomization by offer wave and estimate a slope per wave. Each wave has fewer students, so the smallest detectable effect per wave is larger. Use two or three waves at most and report each wave's range. The treatment log (section 7) records every revision with date and reason. In law, negotiation and reconsideration requests drive many revisions; treat them as an endogenous channel, never as randomized variation.
- **Market timing context:** public applicant-volume reports can describe how the market is pacing. They are descriptive and never feed price estimates. Applicant-reported timing sites are not used (closed decision, section 14).
- **Use of results:** a wave-specific slope changes a recommendation only if it passes the moderator tests (section 4) and beats a single slope in held-out revenue (section 11).

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
- **Support:** for communicated offers (revisions and renewals) awards may only rise, and by no more than the largest tested bonus. For first offers, cuts relative to the current grid are allowed only within the guardrail in section 5. **[v2.2]** For first offers, increases relative to the current grid are also limited to the largest tested bonus (with no test, the largest award jump the discontinuity observed), so recommendations stay inside the range the evidence covers.

**Why one slope:** in the v2 backtest the uniform slope (kappa = 0) produced the highest realized revenue gain of any setting: +$0.60M (+2.7%) versus +$0.42M (+1.8%) for the v2 recommended setting. The v2 segment pattern was precise but wrong in size (for example, international students estimated at 0.18 against a true 1.34). One synthetic seed; to be confirmed in section 10.

### Moderator discovery [v2.2, proposed]

Historical data may be used to **propose** candidate moderators of price sensitivity. They do not set slopes. A moderator enters the price model only through the deferred refinement in section 11, after stratified test evidence supports it.

- **Tests for a candidate:** determined before the aid decision; observable at packaging time; explains variation in the aid effect (checked on the randomized arm, not on historical awards); stable across cycles and populated enough to estimate a slope.
- **Ranking:** by expected net tuition revenue gain for the segment, not by statistical significance.
- **Primary candidate for graduate and professional programs:** the applicant's position relative to the program's own score distribution (for example, LSAT and undergraduate GPA against the school's 25th, 50th, 75th, and possibly 85th percentiles). Other candidates: engagement signals, and the applicant's award gap against the market where market award data are available.
- **Mechanisms:** levers the client can pull other than the dollar amount (award timing, award structure and renewability, matching windows, engagement touchpoints, deposit deadlines) are tracked as candidates for future randomized tests. They need causal evidence before any claim that they shift sensitivity.

## 5. Optimization: policy grid

**Decision [changed]:** an award level for each cell of a policy grid, not for each student. Default grid: academic index quintile (5) x need band (5, including No FAFSA) x residency (3) = 75 cells, on a $1,000 ladder from $0 to $12,000 (about 1,000 binary choices instead of about 25,000). Cells are configurable but must use policy attributes only. **[v2.3]** A client that targets markets may replace residency with a **market tier** (home market, priority or target MSAs, other in-state, other out-of-state, international: up to 5 tiers, 125 cells).

Why: offers go out on a rolling basis, so a policy staff can apply at packaging time is more usable than a list of awards for a pool that is not yet known. A grid is also documentable for counsel, and fewer free choices leave the optimizer less room to exploit model error.

**Objective:** expected multi-year institutional net tuition revenue, the sum over students of `P(enroll | cell award) x (tuition - institutional aid) x persistence factor`. The persistence factor is 1 for a year-one horizon. **[v2.2]** For a longer horizon it is a lookup of historical retention by segment where the client's history supports it, and a stated prior (published benchmarks or the client's published rates; decided October 20) otherwise. Multi-year results are labeled assumption-dependent when retention beyond year two cannot be estimated. **[v2.4]** Where awards are conditional on GPA or credits (common in law), persistence includes the expected loss of award: the expected renewed award, not only retention, enters multi-year revenue, using the client's renewal history or, failing that, conditional-scholarship loss rates from the 509 data as a stated prior.

**Constraints**
- Discretionary spend at most the budget, checked at all three sensitivity scenarios (section 6). **[v2.2]** Horizon: year one is required and is the default. The client may extend to a multi-year horizon (up to four years). The budget and revenue horizons must match. **[v2.4]** The maximum horizon is the program length set in configuration (three years for a full-time JD, four for most undergraduate degrees).
- Optional expected class-size floor, checked at all three sensitivity scenarios.
- Institutional aid at most 75% of tuition per student; optional cap on the class-wide discount rate.
- No cell's award falls more than $3,000 below its current-grid level (configurable).
- **Segment floors [v2.2]:** the average award across the cells of a policy segment may not fall below a set share of that segment's trailing three-cohort average (Appendix C). Each run reports which floors bind and their shadow prices.
- Excluded groups keep current packages.

**Choice rule:** maximize revenue at the middle sensitivity scenario, subject to the revenue gain over the status quo staying at or above zero at the low scenario.

**Targeted objectives [v2.3].** Beyond revenue and headcount, the client may choose a minimum expected enrollment for named segments or markets, a year-over-year gain target for them, or segment and market weights on enrollment. Targets use whitelisted policy attributes only: market tier or named MSAs, program, first-generation status, Pell eligibility, residency, and student type. Race, ethnicity, and gender are blocked as targets by a test. Each target is a linear constraint or weight, evaluated at all three sensitivity scenarios. Each run reports whether the target is feasible within the budget and its shadow price (the revenue given up to reach it). The aid lever works at the admit stage only: where a target market is short of applicants, the funnel analysis shows where it leaks, and aid cannot fix it. Markets with thin history get wider ranges and are flagged (open issue O12).

**Policy lookup [v2.3].** The recommended award for a given student is the grid award for that student's cell. It is the policy applied, not a separate per-student optimization.

**Solver:** multiple-choice knapsack as a mixed-integer program (HiGHS).

**Scenarios shipped:** budget at 0.75x, 1x, and 1.25x; headcount-maximizing at 1x; a class-floor scenario only where the floor binds (report its shadow price). **Tuition scenarios [to build]:** a change in sticker price, applied as a change in net cost for the admitted pool. Labeled "admit stage only" because the model does not capture effects on who applies. No sticker-price optimization.

**Outputs:** the recommended grid, a scholarship policy document, and projected class, revenue, spend, and discount rate under each scenario. **[v2.3]** Optional: the policy lookup file, delivered through the client's secure channel.

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
- **Batch scoring [v2.3]:** an optional add-on. Each batch returns, per student, the forecast probability of enrolling with its calibration band, and optionally the policy lookup award. Inputs are decision-date information only; race, ethnicity, and gender are excluded. Files go to the client through its secure channel with the score date and model version, never through the hosted dashboard. A score says who is likely to enroll, not who will respond to outreach or to an extra dollar, and the documentation says so. Calibration by decile is reported at every refresh. Scores are not used for individualized pricing. **[v2.4]** The forecast default is a regularized logit; section 11 sets the rule for a boosted-tree challenger.

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
- **Client alignment gate [v2.2]:** before any client publication, the client's decision maker (VP or Director of Enrollment, or a Dean, plus others the client designates) reviews the allocation logic, guardrails and floors, the equity audit, and the data use, and signs off. Legal review is the client's choice. The packet includes a short legal-considerations note so the client can decide. **[v2.3]** The sign-off is a one-page approval.
- **Targeting and geography [v2.3]:** geography is a policy attribute, but it is also a strong proxy for race and income. Every geographic target or grid dimension is covered by the equity audit (allocation and yield by group, including by market). Consumer-segment codes are never used in the aid grid by default. Credit data of any kind remains excluded.

## 10. Validation plan

| Layer | Synthetic (truth known) | Real clients |
|-------|-------------------------|--------------|
| Price anchor | Bias and interval coverage across seeds | Experiment versus discontinuity; diagnostics |
| Forecast | Holdout AUC, Brier, calibration | Out-of-time holdout by cohort |
| Policy value | Realized gain at matched spend against baselines | Backtest; policy evaluation on the test arm |
| Leakage | Planted-leak detection | Field-timing checks on every dated field |
| Disclosure | Tests on all published tables | Same, plus manual review before publish |

**Baselines** (spend matched within 1%): status quo; proportional rescale of current awards; need-first fill; a "fence-sitter" rule (top up admits with forecast yield between 0.3 and 0.6); v2 per-student optimizer; perfect-information oracle.

**Confound tracking [v2.2].** Every run reports the aid-versus-applicant-quality diagnostics from the historical data: how strongly awards track academic position and engagement, and the gap between the naive aid coefficient and the anchor. The synthetic worlds plant known confounds so the study checks that the pipeline recovers the true effect despite them.

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
| Moderator-based segments (relative position, engagement, award gap versus market) [v2.2] | Candidate passes the four tests on stratified test evidence and beats a single slope in held-out revenue |
| Mechanism tests: award timing, structure, deposit deadlines [v2.2] | A client with a standing test and a lever it can randomize |
| Grid-tier price estimation (all admits, smooth controls on GPA) [v2.3] | **Deferred to a future phase and not specified now.** Revisit if the Monte Carlo study shows the lean model leaves value and a client has a clean tiered grid |
| Per-student optimization [v2.3] | Not planned; the policy lookup replaces it |
| Boosted-tree forecast challenger [v2.4] | The default stays a regularized logit. A boosted-tree model is allowed only as a challenger for the batch scoring add-on, with calibration, monotone constraints on key features, and reason codes. Adopt only if it beats the logit out of time by a pre-set margin (set by the reviewer) in synthetic worlds with interactions and in the pilot backtest |
| Consumer-segment codes in the aid grid [v2.3] | Not planned; would need an alignment-gate decision and a clean proxy audit |

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

R1 to R12 are the review findings (labeled F1 to F12 in earlier versions).

| ID | Finding | Status in v2.1 |
|----|---------|----------------|
| R1 | Segment pattern wrong in size and order | Removed with the segment pattern |
| R2 | Recommended setting beaten by uniform slope | Uniform slope is now the default |
| R3 | Realization ratio does not carry over | Dropped as a multiplier |
| R4 | Budget holds only on average | Checked at all three scenarios; Monte Carlo threshold |
| R5 | Bands and probability uncalibrated | Replaced by three scenarios |
| R6 | Hybrid average does not equal the anchor | Conversion rule and test in section 4 |
| R7 | Validation from one seed | Lean Monte Carlo study, section 10 |
| R8 | Forecast overpredicts yield by about 4% | Out-of-time recalibration required |
| R9 | Comparisons not spend-matched | Baselines matched within 1% |
| R10 | Pooled estimates differ | Report both; flag at 1.5 standard errors; discontinuity diagnostics |
| R11 | Class-floor scenario does not bind | Shipped only when binding |
| R12 | Validation cannot see asymmetric response to cuts | Support rule; loss-averse Monte Carlo world |
| — | Leakage definition, proxy fairness, disclosure | Decision date defined; audit kept; table set simplified. Still to verify on real outputs |

## Appendix C. Segment floor policy [v2.2; defaults confirmed October 20]

**Purpose.** A floor stops the optimizer from cutting a policy segment on the strength of an estimate that may be wrong. The review showed the risk is real: the large cut to international students came from an estimation error, not from the students' behavior. Floors also make access commitments visible and make the cost of honoring them explicit.

**Definition.** A floor is a minimum on a segment's average award across its grid cells (weighted by projected admits), stated as a share of that segment's trailing three-cohort average. It applies to first offers not yet released and is a hard linear constraint, so each floor adds one row to the optimizer. Formula awards (the merit grid and the need-grant formula) are not changed by the optimizer and are already an implicit floor.

| Segment | Recommended floor | Rationale |
|---------|-------------------|-----------|
| Highest-need and Pell-eligible | 100% of trailing average | Access mission; should rarely bind |
| Other need bands, including No FAFSA | 75% | Limits reallocation to 25% per cycle where evidence is weakest; No FAFSA students must not be penalized for missing information |
| In-state, out-of-state, international | 75% each | Guards against the estimation-error cut seen in the review |
| Transfer (where it is its own grid) | 75% | Small samples |
| First-generation | Client option (confirmed); 100% if mission-driven | Correlates with protected attributes, so the client decides |

**Not used for floors:** academic index (the merit grid already protects it), region, source channel, and race, ethnicity, or gender (never).

**Rules.** Segments under 30 admits are pooled with the nearest segment. A floor may relax to 50% only where the randomized arm shows the segment is materially less sensitive and the client approves at the alignment gate. Every run reports which floors bind and their shadow prices. The per-cell guardrail (no cut over $3,000) stays. With one slope, floors will rarely bind; they are mainly a safeguard for later segment-specific models. Defaults are to be tuned in the Monte Carlo study.

## 13. Open issues for the S4 and S5 re-review [v2.2]

These are unresolved. Each has a proposed resolution that the reviewer should confirm, change, or reject. None is applied above except where noted.

| ID | Issue | Proposed resolution |
|----|-------|---------------------|
| O1 | **Forecast baseline.** Section 4 centers the response on `p_forecast(current award)`, but the forecast's 10 to 12 features exclude the award. It then predicts yield under historical average awards, not the student's own award, so centering on each student's current award is inconsistent | Include current net cost as a control in the forecast, used only for prediction at the status quo; or center on the expected historical award given the features. Decide and test |
| O2 | **Weak evidence.** A test-only anchor (+0.63, SE 0.56 in the v2 run) has a 10th percentile below zero, which breaks the choice rule (gain at or above zero at the low scenario) | Floor the low slope at zero; add an explicit outcome "evidence too weak: no reallocation recommended"; report the minimum detectable effect |
| O3 | **Uncorrected gains and one-dimensional uncertainty.** Scenarios vary only the price slope. Forecast error by cell, retention, and functional form are not varied. The v2 uniform slope predicted about 60% more gain than it realized (ratio 0.62) | Add forecast-error and retention scenarios; add a Monte Carlo threshold that realized gain falls inside the low-to-high range in at least 90% of seeds; consider cell-level forecast shrinkage |
| O4 | **Grid scope.** Unclear whether grid awards are total or discretionary, how they relate to the merit grid, need formula, and appeals, and how the admitted pool is projected as offers roll out. Quintile cutoffs shift each cohort and can remove the threshold variation the discontinuity uses | Define grid awards as discretionary supplements to formula awards unless a client replaces its formulas; project the pool from current admits plus the last cohort's pattern, refreshed on set dates; use fixed index thresholds; log every policy change |
| O5 | **Anchor population and disagreement.** "The anchor's sample" is undefined when a test sample and a local discontinuity sample are pooled. The action on a disagreement flag is undefined | Define the conversion on the test population; on a flag, widen the scenarios to span both estimates |
| O6 | **Monte Carlo design.** 50 seeds per world gives about a 5% false-fail chance on the 90% to 98% coverage band. The gate compares to the retired v2 optimizer. Several worlds are missing | 200 or more seeds in the baseline world; require beating the best simple heuristic by more than one standard error; add Tier 1 (discontinuity-only), no-merit-grid, data-quality, leakage, staff-offsetting, grid regime-change, peer-interference, and retention-beyond-year-two worlds |
| O7 | **Bonus timing.** The slope comes from first-offer bonuses but is applied to revisions, which may respond differently | Keep the support rule; treat revision effects as unestimated; test timing in a later cycle |
| O8 | **Verticals.** The 75-cell grid is undergraduate-shaped | Per-vertical profiles; for law and professional programs, score and GPA by relative position within the program, with need optional |
| O9 | **Test optics and interference.** Randomized aid in a small community can leak through peer comparison | Disclose the design to client leadership; monitor; add an interference world |
| O10 | **Pooling method.** Random-effects pooling is not estimable with two estimates | Keep inverse-variance pooling with the 1.5 SE flag; record as a judgment call |
| O11 | **Departures from the first review to confirm.** Three scenarios instead of posterior draws; no realization correction; CVaR deferred | Reviewer to confirm, change, or reject each |
| O12 | **Thin history in target markets.** Expansion markets have few past students, so forecast probabilities there rest on regional and distance terms | Flag markets under about 30 historical admits; widen their scenario ranges; do not report optimized results for them |
| O13 | **Consumer-segment add-on.** License terms for sharing derived codes, proxy risk, and the level of geography (ZIP or finer) are unresolved | Keep descriptive only; confirm the license permits sharing codes with a consultant; run the proxy audit before any model use |
| O14 | **Market tier and targets.** Up to 125 cells gives the optimizer more room to exploit error; unclear whether floors apply to market tiers; infeasible targets need defined behavior | Cap cells at 125; apply floors to market tiers except client-designated target markets; report infeasibility with the shortfall |
| O15 | **Scoring governance.** Who receives scores, how long files are kept, and what uses are prohibited | Secure-channel delivery only; prohibit individualized pricing from scores; deletion at engagement close |
| O16 | **509 reference data.** Field definitions (recipients versus all students, full-time versus part-time, resident versus nonresident) and the rank-matching assumption are unvalidated | Confirm definitions; test rank-matching in a synthetic law world where the truth is known; keep it a candidate moderator until it passes |
| O17 | **Program-length horizon and conditional awards.** A three-year JD with GPA-conditional awards needs expected award renewal, not only retention | Model expected renewed award from client history; fall back to 509 loss rates as a stated prior; label as assumption-dependent |
| O18 | **Wave-stratified timing.** Per-wave samples are small, and negotiation-driven revisions are endogenous | Two or three waves at most; report per-wave ranges; keep negotiation revisions out of the randomized comparison |
| O19 | **Boosted-model challenger margin.** The margin and the calibration, monotonicity, and reason-code requirements are unset | Reviewer to set the margin (for example out-of-time AUC and Brier) and test it in synthetic worlds with interactions |

Applied in this version: first-offer increases are now bounded by the tested range (section 4, Support).

## 14. Closed decisions [v2.4]

| Decision | Outcome | Rationale |
|----------|---------|-----------|
| Collecting applicant-reported decision-timing data from a third-party law admissions site | **Closed: not used** | Considered a weekly collection of response-timing data from an applicant-reported law admissions site, to track timing by date. Decided against. The site's license excludes institutional and commercial use and prohibits scraping or bulk collection without written permission. The data are self-reported, skew toward engaged applicants, and are coarse (the share of applicants who heard back, by application period). They measure how fast schools respond, not how applicants respond to price, and they do not link to a client's students. Timing sensitivity is learned from the client's own offer waves, and public applicant-volume reports describe market pace. Revisit only if the owner offers a license on terms that fit. |
