# EFA + FAO v2.5: Methodology (lean model, re-review edits merged)

**Status:** Specification. **Draft pending the scoped audit** (`Auditor_Brief_S4_S5_Rereview_v2.4.md`). The audit's corrections will be folded in before sign-off.

**Version history**
- **v2.1** replaced the v2 estimator and optimizer with a simpler design after the first independent review (October 2026).
- **v2.2** merged the October 15 decisions. Additions are tagged **[v2.2]**.
- **v2.3** added batch scoring, the policy lookup, geography and targeted objectives, the evidence audit, and the price-test sample-size guide. Tagged **[v2.3]**.
- **v2.4** added the ABA 509 market layer, program-length horizons, timing by wave, and the boosted-model challenger rule. Tagged **[v2.4]**.
- **v2.5** merges the required-before-build edits from the S4 and S5 re-review (`S4_S5_Rereview_v2.4.md`; edits S4-1 to S4-14 and S5-1 to S5-10). Changes are tagged **[v2.5]**, with the edit number where one applies. The v2.4 text is kept as `02_methodology_v2.4.md`.

Results quoted here come from the v2 build on synthetic data unless marked otherwise. Items marked **[to build]** are not yet implemented.

**Design principle:** be rigorous at the one point where simplicity loses the answer (the level of price sensitivity) and simple everywhere else. **[v2.5]** Rigor at that point includes not acting on the level when the evidence cannot tell which side of break-even it falls.

## 1. Scope

Two linked products and one monitoring layer share one data model.

- **EFA (enrollment funnel analysis):** where do prospects drop out, and what predicts movement through inquiry, application, admit, deposit, and enrollment at census?
- **FAO (financial aid optimization):** given the projected admitted pool, a budget, and goals, what award policy should the institution use for flexible aid?
- **Monitoring [to build]:** during the cycle, how is the class pacing against last year and the plan, and where is melt risk?
- **Scoring and targeting add-ons [v2.3]:** batch enrollment-probability scores, a policy lookup, and targeted objectives by segment or market.

Undergraduate first-time and transfer cohorts are in scope now. Graduate and professional programs are in scope for the descriptive layers (funnel, pacing, loan-cap exposure). They enter the price model only once a program has its own design-based price evidence.

**[v2.5] Law profile.** JD programs use the law profile in section 5: total-award mode, a ladder to tuition, a horizon equal to the award commitment, and position bands. A law school with no usable design-based evidence (section 4, evidence audit) receives EFA, monitoring, the 509 market view, the evidence audit, and a written status-quo grid. It does not receive an optimized grid.

## 2. Funnel analysis

**Stages:** inquiry, application, admit, deposit, enrolled at census. Stealth applicants (the application is the first touch) skip the inquiry stage and are flagged, not dropped. Deposit to census is reported as its own stage so melt is visible.

**Descriptive layer:** a fixed, published set of tables: each dimension by cohort, plus a short list of approved two-way tables pooled across cohorts. Tables are designed so that suppressed cells cannot be recovered by subtraction. Cells with fewer than 10 students are suppressed.

**Driver layer:**
- **Inquiry to application:** logit with clustered standard errors on non-stealth inquiries, reported as average marginal effects in percentage points with confidence intervals.
- **Admit to enroll:** effects of non-price attributes from the forecast model, with intervals, labeled **associational**.

**Academic index [to build]:** one composite of GPA and test scores (test-optional handled inside the index), reported in quintiles. It replaces separate GPA, test, and missing-test terms in the forecast model and defines grid rows in the optimizer. **[v2.5]** The raw running variables (GPA, LSAT) and the published merit thresholds are kept alongside the index, for the discontinuity.

**Relative position (graduate and professional) [v2.5].** This is the applicant's position within the program's own enrolled distribution.
- **Reference distribution:** the prior three entering classes from client data. As a fallback, the 509 25th, 50th and 75th percentiles, linearly interpolated, with tails extrapolated at the 50-to-75 spacing and capped at 0 and 100.
- **Per measure:** position = empirical CDF (LSAT; UGPA). GRE and JD-Next are converted through a published concordance where one exists; otherwise they are flagged and UGPA is used alone.
- **Combined position:** the mean of available measures. Equal weights by default; configurable.
- **Bands:** under 25, 25 to 50, 50 to 75, 75 to 85, and 85 or above. The top band is kept only if it has at least 30 admits per cohort; otherwise it is merged.
- **Freezing:** bands are frozen at cycle start. The admit distribution by band is reported, because admits sit above matriculants.

**Geography [v2.3].** Home address enters as a derived **market**, never as an address.
- **Derivation:** before removing addresses, the client runs a script that returns the metropolitan or micropolitan area (CBSA code), state, ZIP3, and a distance-to-campus band. ZIP3 alone does not map cleanly to a metro area.
- **Reporting:** the funnel is reported by market, with markets under 10 students pooled into an "other" tier.
- **Optional descriptive layers:** market penetration (enrolled students relative to public counts of high school graduates or population by market) and source effectiveness by market.
- **Consumer segmentation** (for example PRIZM) is an add-on the client appends at the same step. It is descriptive and used to target outreach. It enters the forecast only under the release criteria in section 7, and never enters the aid grid.

**Market reference data (ABA 509) [v2.4; field rules v2.5].** For law schools, the public ABA 509 disclosures are an external reference dataset.

*Field rules [v2.5].* These are inferred from the data and **to be confirmed against the ABA's definitions in the audit**:
- Grant counts and percentiles cover all full-time JD students in the academic year *before* the report year, and the percentiles are among recipients only. Evidence: Richmond's 75th-percentile grant equals the prior year's tuition in both the 2024 and 2025 reports.
- LSAT and UGPA percentiles describe matriculants, not admits.
- Yield = matriculants from the applicant pool ÷ offers.
- A nonresident tuition of 0 at a private school means "same as resident" and is normalized and flagged.
- Conditional-scholarship counts lag two years.
- Full-time fields only.

*Uses:*
- **(a) Descriptive:** peer pricing and approximate net-price distributions.
- **(b) Market award gap:** estimated by the rank-matching procedure in Appendix D. It is descriptive, and a candidate moderator only through the gates in section 4. It is never a slope and never a forecast input.
- **(c) Conditional scholarships:** prevalence and loss rates as a candidate mechanism.
- **(d) Yield:** the client's own 509 yield history checks the recalibrated forecast intercept. Peer yields are never a prior for the client.
- **(e) Synthetic worlds:** public parameters for the law synthetic world (W0L, section 10).

*Limits:* school-level only and one year behind. Cross-school regressions on these data are ecological and confounded, so they never set the price anchor. Each annual release is stored with its source, retrieval date, and definitions, and carries no student-level data.

## 3. Data model

Aid arrives in long form: one row per student, fund, and package version, with offered, accepted, and disbursed amounts and dates.

| Class | Components | Used in price models |
|-------|-----------|----------------------|
| Institutional gift | merit, need, athletic, discretionary, other | Yes, if offered by the decision date |
| Other gift | state, Pell, SEOG, external | Yes, if known at the decision date |
| Self-help | subsidized, unsubsidized, Parent PLUS, Grad PLUS, private or institutional loan, work-study | Never as a price reduction; used in the loan-cap exposure layer (section 8) |
| Post-decision fields | accepted, disbursed | **Never** (leakage) |

**Definitions**
- **Net cost** = cost of attendance minus gift aid known at the decision date.
- **Institutional net tuition** = tuition and fees minus institutional gift aid.
- **Need index:** EFC through 2023-24 and SAI from 2024-25, labeled by type. "No FAFSA" is a separate category. Institutional-methodology need (CSS Profile) is accepted where the client uses it.
- **Decision date:** the student's deposit deadline or the date the student deposited, whichever is earlier. Any award or revision dated after it is excluded from price models. Revisions before it are kept with their dates and logged as revisions. **[v2.5]** Every revision carries a reason code: student request, documented competing offer, staff-initiated, or appeal.
- **[v2.5] Renewal rule:** each institutional award records whether it renews as fixed dollars or as a percentage of tuition, and any renewal conditions (GPA, credits).

**Excluded groups [to build]:** a configurable table (athletes, tuition waivers and exchanges, special scholarships, others the client names). Excluded students keep their current packages, are left out of price estimation, and are reported separately so class totals reconcile. **[v2.5]** Awards above full tuition (stipends) are an excluded component in total-award mode.

**Data tiers [to build]:**
- **Tier 1 (minimum):** three cohorts, final packages by component, offer dates where available, and the merit grid. Supports EFA, the forecast, monitoring, and a discontinuity-only price anchor with wider bands. **[v2.5]** Where the client has no published threshold (common in law), Tier 1 supports no anchor, and FAO runs in the weak-evidence state (section 5).
- **Tier 2 (full):** four to five cohorts, every package version with dates, the merit grid with effective dates, and, where the price-test screen recommends one, a price test (section 4). Supports the full FAO.
- **History [v2.2]:** request three to five cohorts. Three is the minimum and five is ideal. Include retention to the next fall, and to later falls where available.

## 4. Price response

### The problem

Aid is not random. Staff give more discretionary aid where they see weaker interest, so a regression on historical awards can show that more aid goes with lower yield. In the synthetic world the correlation between discretionary aid and unobserved interest is −0.41. Against a true effect of +1.49 (+1.31 measured at status-quo awards; see the estimand below):
- the legacy-style model recovers −0.01 points per $1,000;
- a controlled observational logit recovers +0.19.

### Estimand [v2.5, S4-2]

The anchor estimates **θ**: the average, over eligible admits, of the change in enrollment probability from +$1,000 of gift aid **at status-quo awards** (excluding any test bonus), in percentage points per $1,000.

Under the one-slope model, θ corresponds to a logit slope **b**: b = θ / (100 × mean p(1 − p)), with p evaluated at status-quo awards on the same population.

In the synthetic world, θ = 1.31. The 1.49 quoted in earlier versions is the effect at bonus-inclusive awards, a different evaluation point (12% higher).

### Evidence sources

1. **Randomized bonus-aid test (primary when run; an add-on, not a core feature) [v2.3].** A random share of eligible admits receive extra discretionary aid. It is positive-only: nobody receives less than they otherwise would.
   - **Arms:** $0, D/2, and D, assigned 40% / 20% / 40% within the test. **[v2.5, S4-5]** The top arm D is set per vertical so the test covers the award moves the grid will consider:
     - UG default: D = $4,000;
     - law and professional default: D = 10% to 15% of tuition, rounded to $1,000.

     The middle arm gives a weak check on linearity.
   - **Analysis population [v2.5, S4-1]:** **every randomized eligible admit**, with eligibles randomized out of the test serving as additional $0 observations (intent to treat). In the synthetic world this cuts the slope's standard error from 0.44 (test students only) to 0.29 at no extra cost. It also removes an upward bias of about 6% that test-only estimators show against θ.
   - **Estimation:** logit of enrollment on the dose and pre-specified covariates. The effect is computed at dose 0 (status-quo awards), not at the received dose.
   - **Stratified assignment:** randomize within strata (need band × residency for UG; position band × wave for law), using blocked randomization so the arm shares are exact.
   - **Compliance check:** compare other discretionary aid, reconsideration requests, and revisions between arms and between test and non-test eligibles. The aim is to detect staff offsetting or negotiation spillover.
   - **Delivery:** the bonus is always part of the first offer, never a revision.
   - **Offered only where it pays off [v2.2; rule replaced in v2.5]:** see the screen rule below.
2. **Merit-grid regression discontinuity (secondary, optional).** Used only where a published threshold has a meaningful award jump and passes diagnostics.
   - Use a standard package (`rdrobust` or equivalent) with a data-driven bandwidth and bias-corrected intervals.
   - Run a density (manipulation) test and placebo thresholds. Drop the discontinuity if either fails.
   - Divide the enrollment jump by the **net-cost** jump, not the award jump, so merit awards that displace need aid are handled.
   - In the synthetic run the 3.2 GPA threshold carries almost all the information (SE 1.1 points per $1,000, against 1.5 to 3.5 at the other three).
3. **Policy changes and natural experiments [v2.5].** A change in award schedule or tuition with an unaffected comparison group, estimated by difference-in-differences, when it meets the evidence-audit criteria below.

The controlled observational model is **not a price source**. It is used only as the forecast model (below).

### Evidence audit [v2.3; criteria v2.5, S4-9]

Before proposing a test, audit the client's history for usable price variation. The result is one page.

**Checks**
1. **Published thresholds:** dates in force, net-cost jump, admits within the bandwidth on each side, density test, four placebo cut points, and the SE converted to logit units.
2. **Policy changes:** affected and comparison groups, pre-period cohorts, pre-trend, change in net cost, n per cohort, and the difference-in-differences estimate and SE.
3. **Natural experiments** (competitions, cutoffs): same criteria as thresholds.
4. **Data sufficiency:** share of awards with offer dates; package versions; decision dates.

**Minimum evidence for a usable source**
- **Threshold:**
  - unchanged for at least 2 cohorts;
  - net-cost jump of at least 3% of tuition;
  - at least 150 admits within the bandwidth on each side (pooled across cohorts);
  - density test p ≥ 0.05;
  - at most 1 of 4 placebos significant at 5%;
  - implied logit-slope SE no larger than the vertical prior SD (otherwise "uninformative").
- **Policy change:**
  - at least 2 pre-period cohorts;
  - a pre-trend difference that is not significant at 10% and is at most 2 points;
  - a change in net cost of at least 3% of tuition, for at least 100 admits per cohort;
  - an unaffected comparison group;
  - SE no larger than the prior SD.

**Output to the screen:** μ0 and σ0, the inverse-variance combination of usable sources with the vertical default prior, and a yes or no for "anchor available without a test."

**What history can and cannot do.** A past cycle cannot be randomized. It can supply design-based evidence (thresholds, policy changes, natural experiments). It cannot set the price level from historical awards alone, because aid was targeted.

### Sample size and cost [v2.3; revised v2.5, S4-5 and S4-6]

**Standard error of the slope**, in percentage points per $1,000, for the 40/20/40 design:

`SE ≈ 100 × k × √(p(1 − p)) / (0.447 × D × √n_test) × 0.76`

- p is the **eligible population's** baseline yield.
- D is the top arm in thousands of dollars.
- n_test is the number of test students over the planned cycles.
- 0.76 is the analytic gain from the all-eligible analysis (simulation: 0.66).
- k is the covariate-adjustment factor. **Use k = 0.92 by default, or √(1 − R²) from the client's out-of-time forecast.** The v2.3 value of 0.85 reproduced the prototype only because it used 21% yield where the test population's yield was 17%. The oracle bound in the synthetic world is 0.86.

The smallest detectable effect at 80% power (two-sided, 5%) is about 2.8 × SE. It is reported **for information only**; it does not decide whether to run a test.

*Richmond example (650 eligible admits, 40% in the test, p = 0.21, all-eligible analysis). SE / MDE in points per $1,000:*

| Top arm | 1 cycle | 2 cycles | 3 cycles |
|---|---|---|---|
| $4,000 | 0.98 / 2.75 | 0.69 / 1.94 | 0.57 / 1.59 |
| $8,000 | 0.49 / 1.38 | 0.35 / 0.97 | 0.28 / 0.79 |

**Break-even slope.** β\* = 100 × p × 1,000 / (net tuition per enrollee − mean bonus). It is about 1.1 in the synthetic UG world and about 0.9 to 1.0 at Richmond. Plausible effects sit near break-even in both verticals. The decision therefore turns on which side of break-even the slope falls, not on whether it differs from zero.

**Cost.** Expected cost of the test = M × (test students) × E[p × bonus], where M = Σ_t<H s^t is the award-commitment multiplier (H years, persistence s).
- For a **capacity-capped** program, induced enrollees displace other admits, so there is no revenue offset.
- For an **uncapped** program, report the prior-expected net cost and the zero-effect cost.

At Richmond (M ≈ 2.92, renewable awards), cost per test student at zero effect is about **$1,226 with D = $4,000 and $2,453 with D = $8,000**, against the year-one-only $420 quoted in v2.3.

### Price-test screen rule [v2.5, S4-7; replaces the v2.3 rule]

The v2.3 rule (recommend a test when the smallest detectable effect is at most about 2.3 points per $1,000) is retired. It measured detectability rather than decision value, shifted with price level, and ignored break-even, class caps, and renewal costs.

**Inputs from the client at scoping:**
- N, eligible admits per cohort;
- p, eligible yield;
- tuition, and the mean institutional award per enrollee;
- award commitment H, persistence s, and the renewal rule;
- capacity: class band ± %, or "uncapped";
- floors and targets;
- the planned top arm D and the test share (default 40%);
- test cycles K (1 or 2);
- cycles of use U (default 3);
- operating cost F per cycle;
- the evidence-audit μ0 and σ0, or the vertical default prior.

**Computation**
1. **Pool.** Build a projected pool, with cells per section 5, from Tier 1 data where available. Otherwise use a synthetic pool calibrated to public data (509 or IPEDS).
2. **Prior.** b ~ N(μ0, σ0²), truncated at 0; 21-point quadrature.
3. **Value matrix.** For each prior node b_i, solve the production optimizer for the best grid a\*(b_i) under the client's constraints. V[i, j] = gain against status quo under b_i of a\*(b_j), with feasibility checked at b_i.
4. **EVPI** = U × (Σ_i w_i max_j V[i, j] − Σ_i w_i V[i, j0]), where j0 is the grid the two-sided choice rule picks under the prior. **Gate 1:** if EVPI ≤ the cost of the cheapest admissible design, the verdict is **Not recommended**.
5. **EVSI.** For each design (D, K), compute SE_b in logit units. For 21 b-nodes × 21 z-nodes: b̂ = b_i + z × SE_b; update the posterior; choose the grid with the production two-sided rule at the posterior quantiles; score it at b_i. EVSI = U × (EV_test − EV_no test).
6. **Net value** = EVSI − cost − F × K.

**Verdicts**
- **Recommend:** all of the following hold.
  - Net value ≥ max($50,000; 0.5% of one cohort's multi-year net tuition revenue).
  - EVSI ÷ (cost + F × K) ≥ 1.5.
  - Zero-effect cost ≤ 5% of one cohort's multi-year net tuition revenue.
  - The office can randomize and log; U ≥ 2; the client alignment gate accepts the disclosure.
- **Optional:** net value > 0, but a threshold or gate above is missed.
- **Not recommended:** net value ≤ 0, or Gate 1 stops the computation.

**Reported every time:** EVPI, EVSI, cost, the MDE, β\*, and the grid change the test would most likely trigger.

The client's VP or Director of Enrollment, or a Dean, decides per engagement.

*Worked example (Richmond economics, revenue objective, ±3% class band, median-position floor, prior θ ~ N(1.0, 0.5²), U = 3).* The verdict is **Not recommended** at 600, 1,000, 2,000, and 4,000 eligible admits: EVPI is $0.29M to $1.92M, against test costs of $0.32M to $1.99M. At Richmond's own size, EVPI is $0.10M to $0.68M across priors.
- Under an uncapped scale decision, the same economics give Recommend at every size. The decision space, not N, drives the verdict.
- Rerun the screen if the client names a slope-sensitive target (for example, a median position).

These examples use a stylized two-band pool; **to be confirmed in the audit.**

**Cheaper randomized options (deferred, section 11):**
- mechanism tests (deposit deadline or award timing), which cost almost nothing in dollars;
- a one-year (non-renewable) bonus, at about one-third the cost, though it measures response to a different treatment.

### Timing and sensitivity by date [v2.4; revised v2.5, S4-8]

Whether price response changes through the cycle is learned from the client's own data, not from outside timing data.

- **Waves:** two by default. Three only if offers are released in at least three batches at least three weeks apart. Randomization is stratified by wave.
- **Estimation:** pooled across waves. Per-wave slopes are reported as descriptive ranges. At Richmond with one cycle and D = $4,000, the per-wave MDE is about 5.1 points per $1,000, and the MDE for a wave difference is about 7.3.
- **Negotiation and reconsideration:** in law, these drive many revisions. They are post-treatment outcomes, logged with reason codes, and never used as price variation. Reconsideration and increase rates by arm are reported as compliance diagnostics.
- **When a wave slope may change a recommendation:** only if all four hold.
  1. A single early-versus-late contrast was pre-registered with its direction.
  2. Pooled over at least two cycles, the contrast is significant one-sided at 5% and at least 50% of the pooled slope.
  3. It beats one slope in held-out policy value by more than 1 SE.
  4. A Monte Carlo timing world confirms it.
- **Market timing context:** public applicant-volume reports describe how the market is pacing. They are descriptive and never feed price estimates. Applicant-reported timing sites are not used (closed decision, section 14).

### Anchor [revised v2.5, S4-2]

- **Separate estimates.** The experiment and the discontinuity are reported separately, each converted to a **logit slope on its own sample at status-quo awards**.
- **Pooling.** The two logit slopes are pooled by inverse variance into the anchor b̂ with SE s. Under the one-slope model both sources estimate the same b, and their AMEs differ only through p(1 − p).
- **Disagreement flag:** raised when |z| > 1.5 in logit units. On a flag, the sensitivity scenarios widen to span both estimates. After flags in two consecutive cycles, the anchor becomes experiment-only.
- **Tier 1 without a test:** the anchor is the discontinuity (or qualifying policy change) alone, labeled local. A Tier 1 client with no usable source has **no anchor**.

Synthetic results (v2 build, AME scale, older pooling): experiment +0.63 (95% interval −0.46 to 1.72); discontinuity +2.22 (0.63 to 3.81); pooled anchor +1.14 (0.24 to 2.04); θ = 1.31.

*Judgment call:* pooling versus experiment-only. Pooling is defensible while the two estimates are compatible and the discontinuity passes diagnostics. What would change this: placebo or density failures, repeated disagreement, or the prestige-bump Monte Carlo world showing that pooling fails coverage while experiment-only passes.

### Response model [revised v2.5, S4-3 and S4-4]

One slope for everyone, on the logit scale:

`p_i(a_c) = expit( logit p*_i + b × (a_c − r_c) )`

- **Forecast model:** a regularized logit with a fixed set of about 10 to 12 decision-date features: academic index or position band, need band, residency or market, program, decision type, application timing, campus visit, engagement, first-generation status, and stealth flag. **It contains no aid fields.** Protected attributes are excluded.
- **Recalibration:** out of time, on the latest complete cohort: logit p\* = α + γ × logit f. The forecast is labeled "unstable" if γ is outside [0.8, 1.2].
- **Reference award r_c** for the student's cell c: the mean status-quo flexible award among admits in that cell in the recalibration cohort (supplement mode: the discretionary component; total mode: the total institutional scholarship). It is adjusted for known rule changes (tuition, merit grid) to the live year. p\* estimates yield under the status-quo *policy* for students like this one, so r_c is the matching award. Formula awards stay fixed.
- **Known limitation:** replacing staff targeting within a cell with a flat cell award changes how award and interest move together inside the cell. The first-order model ignores this. Monte Carlo worlds W1 and W16 to W18 measure the error.
- **b** comes from the anchor.
- **Conversion test:** the model's AME at status-quo awards on the experiment's eligibles, computed with **recalibrated** p, must match the experiment's own status-quo AME within 5%. The v2.4 "within 1%" check is retired: it tested an identity that holds by construction.
- **Holdout test:** on the holdout, Σ_c n_c × mean p_i(r_c) falls inside the forecast interval.
- A single logit slope is not a single percentage-point effect. Students near 50% yield respond most in points, so the model still targets undecided students without estimating segment differences.
- **Support:**
  - Communicated offers (revisions and renewals) may only rise, and by no more than the largest tested bonus.
  - First offers may be cut relative to the status-quo grid only within the guardrail in section 5.
  - **[v2.2]** First-offer increases are also limited to the largest tested bonus (with no test, the largest award jump the qualifying discontinuity observed). With no anchor, no level changes are allowed.

**Why one slope:** in the v2 backtest the uniform slope produced the highest realized gain of any setting: +$0.60M (+2.7%), against +$0.42M (+1.8%) for the v2 recommended setting. The v2 segment pattern was precise but wrong in size (for example, international students estimated at 0.18 against a true 1.34). This is one synthetic seed and one cohort. The uniform slope captured 44% of the oracle's gain. It remains to be confirmed in section 10.

### Moderator discovery [v2.2; protocol v2.5]

Historical data may be used to **propose** candidate moderators of price sensitivity. They do not set slopes.

- **Candidate list (fixed):** relative position band (primary for graduate and professional programs; section 2), engagement index, market award-gap band (section 2 and Appendix D), market tier, need (if collected), and application timing.
- **Use of history:** descriptive yield curves by candidate and award quantile, with confound diagnostics, labeled associational. Candidates are ranked by revenue at stake and plausibility, never by statistical significance.
- **Pre-registration:** at most three candidates are carried into a cycle.
- **Test on the randomized arm:**
  - Randomization is stratified by the candidate's strata, with at most 5 strata per cycle in total.
  - Model: logit(enroll) = covariates + b × dose + Σ_k b_k × dose × 1[stratum k].
  - H0: b_k = 0, tested one-sided at α = 0.10 in the pre-registered direction, with Holm correction across candidates.
  - The SE of each interaction is always reported.
- **Gates before any moderator affects allocation:** all three must hold.
  1. The interaction passes on pooled data from at least two cycles.
  2. The segment-slope policy beats one slope in held-out policy value by more than 1 SE (inverse-probability evaluation on the latest randomized cycle).
  3. Monte Carlo worlds with heterogeneity show a gain over the lean model.
- **Always allowed:** position band as a grid dimension, with one slope. **Never allowed:** slopes taken from history, or the 509 gap as a slope modifier.
- **Mechanisms** the client can pull other than the dollar amount (award timing, award structure and renewability, matching windows, engagement touchpoints, deposit deadlines) are tracked as candidates for future randomized tests. They need causal evidence before any claim that they shift sensitivity.

## 5. Optimization: policy grid

**Decision:** an award level for each cell of a policy grid, not for each student. Cells must use policy attributes only. The offers go out on a rolling basis, so staff need a policy they can apply at packaging time; a list of awards for a pool that is not yet known would not work. A grid is also documentable for counsel, and fewer free choices leave the optimizer less room to exploit model error.

### Award mode [v2.5, S5-2]

The award mode is set per program in configuration.

- **`supplement`** (UG default): the grid award is a discretionary supplement added after formula awards (merit grid, need grant, athletic awards). Formula awards and excluded groups are unchanged.
- **`total`** (law and professional default): the grid award is the total institutional scholarship.

### Cells [v2.5, S5-4]

- **Count rule:** cells ≤ floor(projected admits per cohort ÷ 30). Richmond's limit is 21.
- **UG profile:** academic-index quintile (5) × need band (5, including No FAFSA) × residency (3), giving 75 cells. When the count rule fails, collapse need to 3 bands first, then the index to tertiles.
- **Law profile:** position band (5) × market (home state / other), optionally × need (2), giving 10 to 20 cells.
- **Market tier [v2.3]:** a client that targets markets may replace residency with a market tier (home market, priority or target MSAs, other in-state, other out-of-state, international). At most 5 tiers, with the total still within the count rule and at most 125 cells.

### Ladder and cap [v2.5, S5-2]

- **Ladder:** $1,000 steps (UG) or $2,500 steps (law), up to tuition.
- **Per-student institutional aid cap:** max(configured cap, current award), so the status quo is always representable.
  - UG default cap: 75% of tuition.
  - Law default cap: 100% of tuition.
- Awards above tuition stay as an excluded stipend component.

### Policy grid scope [v2.5, S5-8; resolves O4]

- **Relation to formula awards:** the merit grid and the need formula are unchanged in the MVP.
  - Need bands are harmonized SAI/EFC bands, with "No FAFSA" as its own band; CSS Profile is accepted.
  - In law, need is a grid dimension only if the school uses need in scholarships.
- **Appeals and negotiation:** a reserve R, equal to the trailing three-cohort mean of post-first-offer increases by cell, is deducted from the budget before optimizing. Appeals follow the increases-only rules below, are logged with reason codes, and are excluded from estimation.
- **Pool projection:**

  projected admits by cell = admits to date + (last cohort's final admits by cell − its admits by cell at the same day of the cycle) × (live applications to date ÷ last year's applications at the same date)

  The projection is refreshed on three fixed dates (first release, mid-cycle, final wave). The grid is frozen between refreshes.
- **Fixed thresholds:**
  - Index or position cut points are computed from the trailing three cohorts at cycle start and frozen for at least two cycles.
  - Changes take effect only at cycle boundaries and are recorded in a `policy_changes` table: effective date, old and new cut points, and old and new awards.
  - Award differences between adjacent cells at a cut point are logged as candidate discontinuities for the evidence audit.
- **Status-quo grid:** derived empirically (mean award by cell in the latest cohort) and confirmed by the client as matching practice before any optimization.
- **Policy lookup [v2.3]:** the recommended award for a student is the grid award for that student's cell. It is the policy applied, not a separate per-student optimization.

### Objective

Expected multi-year institutional net tuition revenue:

Σ over students of `P(enroll | cell award) × (tuition − institutional aid) × persistence factor`

The persistence factor follows the horizon (below).
- Retention is a lookup by segment where the client's history supports it, and a stated prior otherwise (published benchmarks or the client's published rates; decided October 20).
- Multi-year results are labeled assumption-dependent when retention beyond year two cannot be estimated.
- **[v2.4]** Where awards are conditional on GPA or credits, persistence uses the expected renewed award, not only retention. The source is the client's renewal history, or failing that, 509 conditional-scholarship loss rates as a stated prior.
- **[v2.5]** Renewal follows the recorded rule (fixed dollars or percentage of tuition). Richmond reports no conditional scholarships, so its persistence is retention alone (about 0.97 in year one and 0.99 after).

### Horizon [v2.5, S5-3 and S5-10]

- The budget horizon and the revenue horizon **equal the award's commitment length**:
  - three years for a renewable full-time JD award;
  - for UG, as the client elects, from one year up to program length.
- Configuration validation rejects mismatched horizons.
- Discretionary spend is counted over the commitment horizon, with persistence.

The v2 build optimized four-year revenue against a one-year budget. That is no longer allowed.

### Constraints

- **Budget:** expected flexible spend plus the appeals reserve plus the count-noise buffer must not exceed the budget, at all three sensitivity scenarios (section 6). **[v2.5, S4-12]**

  buffer = 1.645 × √(Σ p(1 − p) × award²), evaluated at the high scenario

  This targets at most a 5% chance of overrun from enrollment noise alone. At Richmond the buffer is about 12% of first-year scholarship spend.
- **Class size:** an optional expected class band (floor and ceiling), checked at all three scenarios. The law default is ±3% of the status quo.
- **Per-student aid cap** as above, and an optional cap on the class-wide discount rate.
- **Guardrail [v2.5, S5-5]:** no cell's first-offer award falls more than **5% of tuition** below its status-quo level (configurable). That is about $1,900 at Lakeshore and $2,900 at Richmond.
- **Segment floors [v2.2]:** the average award across a policy segment's cells may not fall below a set share of that segment's trailing three-cohort average (Appendix C). Each run reports which floors bind and their shadow prices.
- **Excluded groups** keep their current packages.

### Choice rule [v2.5, S5-1; replaces the v2.4 rule]

1. **Scenarios:** b_L = max(0, b̂ − 1.2816 s), b_M = b̂, b_H = b̂ + 1.2816 s.
2. **Feasibility:** a grid is feasible only if every constraint holds at b_L, b_M **and** b_H.
3. **Choice:** maximize net tuition revenue at b_M, subject to the gain over the status-quo grid being ≥ 0 at **both** b_L and b_H.

The v2.4 rule checked only the low scenario. That approves any cut the middle scenario favors, because a cut always gains when students are less sensitive, and the rule never checked the case where they are more sensitive.

**Weak-evidence state.** Triggered when b̂ − 1.2816 s ≤ 0, or when no anchor exists. Every view carries "Evidence too weak to change aid levels." In this state:
- any change of more than 1% in expected spend at b_M is blocked;
- only reallocations that are non-negative at b = 0 and at b_H pass;
- with no anchor, the output is the documented status-quo grid.

**No admissible grid.** If no grid beats the status quo under the rule, the output is the documented status-quo grid, the reasons, and the screen's evidence plan.

*Open for the audit:* whether the two-sided rule is so conservative that it nearly always returns the status quo, and whether a minimax-regret or posterior-expected-value rule should replace it.

### Increases-only evaluation [v2.5, S5-7]

Mid-cycle re-optimization works on three groups of students: deposited (D), released but undecided (R), and unreleased (U).

- **Budget** (at b_H):

  Σ_D (1 − melt) × committed award + Σ_R π_i(t) × p_i(committed + Δ_i) × (committed + Δ_i) + Σ_U p_j(a_c) × a_c + reserve + buffer ≤ budget

  - π_i(t) is the historical conversion of admits still undecided at the same number of days to the deadline (pacing lookup), scaled by the forecast's relative risk.
  - Increases must be non-negative and no larger than the tested dose: 0 ≤ Δ_i ≤ D.
- **Revenue from increases on released offers** is evaluated at b_L, because the response to revisions is unestimated (O7).
- **Class:** projected class = deposits × (1 − melt) + undecided conversion + unreleased. The capacity ceiling is checked at b_H and the floor at b_L.
- **Released offers:** a new grid applies only to unreleased offers. Released offers keep their committed awards even if the cell's new award is lower, and the remaining budget is computed on those committed amounts.

### Targeted objectives [v2.3; revised v2.5, S5-6]

Each targeted objective is linear and must hold at all three scenarios (k ∈ {L, M, H}).

| Objective | Form |
|---|---|
| Minimum expected enrollment, segment S | Σ_c∈S n_c p_c^k(a_c) ≥ T_S |
| Year-over-year gain | T_S = (1 + g_S) × status-quo expected enrollment of S at scenario k |
| Enrollment weights | maximize NTR_M + Σ_S w_S × expected enrollment of S at b_M, with w_S in dollars per enrollee, stated by the client |
| Median position (law) | Σ over cells at or above band m of n_c p_c^k ≥ 0.5 × Σ_c n_c p_c^k + 1.645 σ_k, with σ_k = √(Σ n_c p_c(1 − p_c)) |

**Whitelist [v2.5].**
- **Allowed:** market tier or CBSA, state, distance band, program, first-generation status, Pell eligibility, residency, student type, academic index or **position band**, and need band.
- **Blocked:** race, ethnicity, gender, consumer-segment codes, credit data, and any geography finer than CBSA.
- **Enforcement:**
  - a static schema test, with one unit test per blocked attribute;
  - a runtime proxy screen. If a target segment's composition by race or ethnicity (audit-only data) differs from the admit pool by more than 20 points for any group, or Cramér's V ≥ 0.3, the target needs explicit acknowledgment at the alignment gate, and the equity audit reports allocation changes by group.

**Feasibility.**
1. Minimize total slack at b_L.
2. If the slack is positive, report:
   - each target's shortfall in enrollees at L, M and H;
   - the budget that would close it (re-solve with the budget free up to 2×);
   - the funnel stage where the segment leaks.
3. **Shadow price:** re-solve with the target relaxed by one enrollee and report the revenue per enrollee. Flag it when it exceeds the segment's net tuition.

The aid lever works at the admit stage only. Where a target market is short of applicants, the funnel analysis shows where it leaks, and aid cannot fix it.

**Thin history (O12).**
- Markets with fewer than 30 admits across history merge into their parent tier for cells and targets.
- Market intercepts in the forecast are shrunk toward the tier mean.
- Targets on flagged markets are reported as "descriptive goal, not optimized."

### Solver, scenarios, and outputs

**Solver:** multiple-choice knapsack as a mixed-integer program (HiGHS).

**Scenarios shipped:**
- budget at 0.75×, 1×, and 1.25×;
- headcount-maximizing at 1×;
- a class-floor scenario only where the floor binds (report its shadow price).

**Tuition scenarios [to build]:** a change in sticker price, applied as a change in net cost for the admitted pool. These are within the evidence only if the change is no larger than the tested dose. They are labeled "admit stage only," because the model does not capture effects on who applies. There is no sticker-price optimization.

**Outputs:**
- the recommended grid (or the documented status-quo grid in the weak-evidence state);
- a scholarship policy document;
- projected class, revenue, spend, and discount rate under each scenario;
- the evidence status.

**[v2.3]** Optional: the policy lookup file, delivered through the client's secure channel.

## 6. Uncertainty and honesty

- **Three sensitivity scenarios [revised v2.5, S4-10]:** b_L, b_M, b_H are the 10th, 50th, and 90th percentiles of the **logit-slope** posterior, with b_L floored at 0. They are shown as "gain if students are less, about as, or more price-sensitive than estimated." This replaces the v2 40-draw bootstrap, the probability-of-improvement figure, and the scaled planning estimate.
- **Forecast uncertainty:** class projections carry an interval from the out-of-time calibration error, combined with binomial enrollment noise. **[v2.5]** At Richmond, binomial noise alone is about ±10 enrollees (7.6% of the class) at one SD.
- **Count noise [v2.5, S4-12]:** budget and class checks include the buffer in section 5.
- **Model-to-realized disclosure [v2.5, S4-11]:**
  - The methodology publishes the Monte Carlo distribution of realized ÷ predicted gain (median and 10th percentile) for each release.
  - The low scenario is shown beside every headline gain.
  - No multiplier is applied per engagement.

  In the v2 backtest, the three-scenario range covered the realized gain only because the anchor was too low. The shortfall came from forecast overprediction (+6.6% against the true expectation) and allocation error (predicted +7.5 enrollees, realized −1.5). Out-of-time recalibration and cell-level pooling address these.
- **Backtest diagnostic:** each engagement runs one out-of-time backtest and reports realized versus predicted gain. Budgets are set on model-predicted spend, as in production. The diagnostic is a check, not a multiplier.

## 7. Monitoring layer [to build]

- **Pacing:** admits, deposits, revenue, and flexible spend against the same date last year and against plan.
- **Projected census:** current counts by stage × historical stage-to-census conversion rates by days to deadline (a lookup table, not a new model), with an interval from prior-year spread and binomial noise.
- **Melt:** historical deposit-to-census rates by a few flags known at deposit (housing application, verification selected, unmet need above a threshold, FAFSA not received). Segment-level in the dashboard. Any student-level list goes back to the client through its secure channel, never the hosted dashboard.
- **Refresh:** weekly or biweekly client export during yield season.
- **Treatment log:** every mid-cycle award revision is recorded with date and reason code, so it can be separated from the price estimate the following year.
- **Batch scoring [v2.3; release criteria v2.5].** An optional add-on. Each batch returns, per student, the forecast probability of enrolling with its calibration band, and optionally the policy lookup award (the cell award). Inputs are decision-date information only; race, ethnicity, and gender are excluded. A score says who is likely to enroll, not who will respond to outreach or to an extra dollar. It may ship only when all of these hold:
  1. **Out-of-time calibration on at least one cohort:** slope in [0.85, 1.15]; |intercept| ≤ 0.1 logit; deciles within ±3 points (UG) or inside the 90% binomial band (small programs).
  2. **Feature tests:** leakage and protected-attribute tests pass on the scoring feature set.
  3. **File contents:** only the client's key, score, band, model version, and score date.
  4. **SOW terms:** the SOW names recipient roles and prohibits individualized pricing, use in admission decisions, use in individual scholarship negotiation, and onward sharing. Frankel deletes the files within 30 days of engagement close and keeps a deletion log.
  5. **Monitoring:** decile calibration at every refresh, with an alarm if the score-distribution PSI exceeds 0.2.
  6. **Alignment gate:** sign-off recorded.

  The forecast default is a regularized logit; section 11 sets the rule for a boosted-tree challenger.

## 8. Descriptive differentiators [to build]

Descriptive only. None of these enters the price model or the decision-time forecast.

- **Loan-cap exposure.** Grad PLUS closed to new borrowers on July 1, 2026, and new annual and aggregate caps apply to graduate and professional borrowing and to Parent PLUS (per public summaries; confirm current limits with Federal Student Aid).
  - Report, by program and segment, how many admits relied on PLUS in prior cohorts and how many dollars now sit above the caps.
  - Translate the uncovered amount into a revenue range using the three sensitivity scenarios, with the caveat that the price evidence comes from gift aid, not loan access.
  - Once fall 2026 outcomes arrive, compare 2025 to 2026 changes for high-reliance versus low-reliance segments.
- **Where non-enrolling admits went.** A National Student Clearinghouse match ordered by the client, joined to IPEDS and College Scorecard net price by income band, gives "lost to" institutions and net-cost gaps by segment.
- **Admitted-student survey.** Enrolling and non-enrolling admits report competing offers and reasons, giving measured competitor offers for a sample.
- **Peer pricing comparison.** Sticker price and net price by income band against a client-approved peer set, from IPEDS. For law schools, from the ABA 509 layer, including the rank-matched market award gap (Appendix D).

## 9. Equity and legal guardrails

- **Protected attributes:** race, ethnicity, and gender are **never** model inputs. A test enforces it.
- **No consumer credit data** (credit scores or bureau matches). They would require identified records, their permissible use for aid decisions is unclear, and they are strong proxies for race. Ability to pay comes from FAFSA, CSS Profile, observed borrowing, and optional public Census tract indicators appended by the client before de-identification.
- **Equity audit:** grid cells use policy attributes only, but need band, geography, residency, and position can still act as proxies. The audit table compares status-quo and recommended policies by group (average award, expected yield, expected discount rate, share receiving an increase) and is reviewed with every recommendation. **[v2.5]** Equity tables from the v2 build must not be shown to clients; they are re-run under the lean model.
- **Client alignment gate [v2.2]:** before any client publication, the client's decision maker (VP or Director of Enrollment, or a Dean, plus others the client designates) reviews the allocation logic, guardrails and floors, the equity audit, and the data use, and signs off. Legal review is the client's choice. The packet includes a short legal-considerations note so the client can decide. **[v2.3]** The sign-off is a one-page approval. **[v2.5]** For a price test, the packet also discloses the design and the negotiation-interference risk.
- **Targeting and geography [v2.3; v2.5]:**
  - Geography is a policy attribute, but it is also a strong proxy for race and income. Every geographic target or grid dimension is covered by the equity audit and the runtime proxy screen (section 5).
  - **Consumer segments** may move beyond descriptive use only when all of these hold:
    1. the client confirms in writing that its license permits sharing derived codes with a consultant;
    2. the codes are at block-group or ZIP level, never household;
    3. the proxy audit shows Cramér's V with race and ethnicity below 0.3;
    4. the codes add at least 0.01 out-of-time AUC;
    5. the alignment gate approves.

    They never enter the aid grid.
  - Credit data of any kind remains excluded.

## 10. Validation plan

| Layer | Synthetic (truth known) | Real clients |
|-------|-------------------------|--------------|
| Price anchor | Bias against θ and interval coverage across seeds | Experiment versus discontinuity; diagnostics |
| Forecast | Holdout AUC, Brier, calibration | Out-of-time holdout by cohort |
| Policy value | Realized gain at model-set budgets against fair baselines | Backtest; policy evaluation on the test arm |
| Leakage | Planted-leak detection | Field-timing checks on every dated field |
| Disclosure | Tests on all published tables | Same, plus manual review before publishing |

### Fair baselines [v2.5, S4-13]

Each policy is evaluated twice: at a budget set on its own model-predicted spend (the production condition), and at true spend matched within 1% (for ranking only).

- **Status quo.**
- **Proportional rescale:** status-quo awards × s, with s solved to hit spend.
- **Need-first fill:** $1,000 steps to admits in the highest need band, then the next, until spend is reached. Cuts start at the lowest need band. In law without need data, fill by position band from lowest yield upward.
- **Grid-constrained fence-sitter:** cells whose mean forecast p at the status quo lies in [0.30, 0.60] get a uniform increment solved to hit spend. The per-student version is reported only as a reference, because it is individualized pricing.
- **Context only:** legacy zero-discretionary and the perfect-information oracle.

**Margin.** Across paired seeds, the grid must beat the best of {status quo, proportional, need-first, grid fence-sitter} on mean realized gain by at least max(0.25% of status-quo multi-year net tuition revenue, 1.645 × the SE of the paired difference), and must win in at least 60% of seeds. **If the grid fails, the winning heuristic becomes the recommendation.**

### Confound tracking [v2.2]

Every run reports the aid-versus-applicant-quality diagnostics from the historical data: how strongly awards track academic position and engagement, and the gap between the naive aid coefficient and the anchor. The synthetic worlds plant known confounds at several strengths, so the study checks that the pipeline recovers the true effect despite them.

### Monte Carlo study [to build; revised v2.5, S4-13]

The study runs at each release, not per engagement.

**Per seed:**
1. Generate five historical cohorts, a holdout, and a live cohort.
2. Run the full pipeline with no access to truth.
3. Score with true expectations (allocation value) and with one Bernoulli outcome draw (spend and class noise).

Budgets are set on model-predicted spend. The target runtime is at most 30 seconds per seed, without a bootstrap.

| World | Mechanism | Seeds | Pass |
|---|---|---|---|
| W0 UG baseline | Current generator; confound about −0.4 | 200 | Baseline thresholds |
| W0L Law baseline | Richmond-calibrated: 650 admits, 21% yield, $57,700 tuition, 509 grant distribution (28% at or above full tuition), no merit grid, position bands, three-year renewable awards, persistence 0.97/0.99, θ = 1.0; with and without a test | 200 | Baseline thresholds, with the law class test below |
| W1 | Targeting differs by need band | 100 | Anchor thresholds |
| W2 | Unobserved slope heterogeneity (SD 0.6) | 100 | Gain > 0 in ≥ 80%; shortfall against the oracle documented |
| W3 | Slope halves beyond +$6,000 | 100 | Linearity flag ≥ 50%; loss < 0.5% |
| W4 | Cuts hurt twice as much | 100 | Gain ≥ 0 in ≥ 85% |
| W5 | Prestige bump at merit thresholds | 100 | Disagreement flag ≥ 70%; coverage ≥ 85% after the flag action |
| W6 | 600 admits, 15% test share | 100 | No level change when q10 ≤ 0 (100%); loss < 0.5% in ≥ 95% |
| W7 | Slope drifts 25% between cohorts | 100 | Coverage ≥ 85% |
| W8 Tier 1 | No test; one usable threshold | 100 | Coverage ≥ 85% with the local label; no level change when the interval straddles β\* |
| W9 | No grid, no test | 100 | "No anchor," no optimized grid (100%) |
| W10 | Data-quality faults (missing dates, post-decision awards, duplicates) | 100 | QA catches ≥ 95%; bias within the W0 limit + 5 points |
| W11 | Planted leak | 100 | Blocked (100%) |
| W12 | Staff offsetting | 100 | Compliance flag ≥ 80% when the offset ≥ 25% of the bonus |
| W13 | Merit thresholds move between cohorts | 100 | Per-regime estimate; bias within the limit |
| W14 | Negotiation interference in the control arm | 100 | Reconsideration flag ≥ 70%; intent-to-treat bias reported |
| W15 | Retention depends on net cost; non-constant hazard | 100 | Year one unaffected; multi-year error documented |
| W16 to W18 | Confound strength −0.2, −0.6, +0.2 | 100 each | Anchor thresholds; confound diagnostic monotone in strength |
| W19 | Conditional awards (deferred) | 100 | When a client needs it |
| W20a/b | Additive / interaction worlds | 100 each | Section 11, boosted challenger |

**Baseline thresholds (W0 and W0L).** False-fail rates assume a correct method; binomial at 200 seeds.

| Check | Threshold | False-fail |
|---|---|---|
| Anchor bias | \|mean bias\| ≤ 10% of b | — |
| 95% interval coverage | 90% to 98% of seeds | 1.0% |
| Scenario calibration | Realized ≥ low-scenario prediction in ≥ 80% of seeds; median realized ÷ middle prediction in [0.70, 1.15] | — |
| Realized gain | > 0 in ≥ 90% of reallocating seeds | 0.1% |
| Fair baselines | Margin above | — |
| Spend overrun (outcome draws) | > 105% of budget in ≤ 5% of seeds | 0.3% |
| Class projection | UG: within 2% in ≥ 90% of seeds. W0L: realized class inside the projected 90% interval in ≥ 85% of seeds | — |
| Two-sided rule | No level change when q10 ≤ 0 (100%) | — |
| Floors and guardrail | Binding frequency reported | — |

The family-wise false-fail rate is about 2% to 3%.

**Other worlds:** each either meets the baseline thresholds, or its designated diagnostic fires in at least 70% of its seeds while false-alarming in at most 10% of W0 seeds.

## 11. Future refinements (deferred)

Added only when the data support them and the Monte Carlo study shows a gain over the lean model.

| Refinement | Trigger to add it |
|-----------|-------------------|
| Segment price differences from stratified randomization, pooled hierarchically | The moderator gates in section 4 |
| Adaptive price tests across admit waves | A client with several admit waves and a standing test |
| Worst-case-average (CVaR) budget constraints and posterior-draw optimization | Segment differences adopted, so uncertainty is no longer one-dimensional |
| Settings chosen by cross-fitted realized value | More than one tuning setting remains |
| Loan-access response estimated from the 2026 cap change | Fall 2026 census data available |
| Sticker-price optimization | Evidence on applicant-pool response |
| Year-specific retention | Three or more years of retention per cohort |
| Time-varying treatment (revisions and appeals) | Treatment log in place for at least one cycle |
| Wave-specific slopes [v2.5] | The four conditions in section 4, timing |
| Mechanism tests: award timing, structure, deposit deadlines [v2.2] | A client with a lever it can randomize. **[v2.5]** The preferred first randomized step where a bonus test is not recommended |
| One-year (non-renewable) bonus test [v2.5] | A client that accepts it; result labeled as response to a one-year grant |
| Empirical prior pooled across clients [v2.5] | Design-based estimates from at least three clients; replaces the vertical default prior in the screen |
| Conditional-award persistence modeling | A client that offers conditional scholarships |
| Grid-tier price estimation (all admits, smooth controls on GPA) [v2.3] | **Deferred to a future phase and not specified now** |
| Per-student optimization [v2.3] | Not planned; the policy lookup replaces it |
| Boosted-tree forecast challenger [v2.4; margin v2.5] | See below |
| Consumer-segment codes in the aid grid [v2.3] | Not planned |

**Boosted challenger [v2.5].** For the batch-scoring add-on only.
- **Features:** the same decision-date features as the forecast.
- **Monotone constraints:**
  - increasing in campus visit, engagement count, admitted-student event attendance, and days applied before the deadline;
  - decreasing in position band (law);
  - unconstrained in need and market.
- **Calibration:** isotonic or Platt on an out-of-time cohort; calibration slope in [0.9, 1.1]; expected calibration error ≤ 0.02 (UG) or inside the binomial band.
- **Margin:** adopted only if, on each of at least two out-of-time cohorts:
  - AUC improves by at least 0.02, with the paired-bootstrap 90% lower bound above 0;
  - Brier improves by at least 3% relative;
  - no decile is worse calibrated than the logit's worst decile.

  The pilot backtest must show the same.
- **Reason codes:** TreeSHAP top 3 positive and negative contributors, restricted to whitelisted names, stored with each score.
- **Monte Carlo:** in W20a (additive) the challenger must fail in at least 90% of seeds. In W20b (engagement × position, visit × distance, and a step near the deposit deadline) it must pass in at least 70% of seeds at UG size; the pass rate at law size is reported.
- **Optimizer baseline:** the challenger never feeds it. *Judgment call:* revisit only if W20b shows a grid revenue loss above 0.5% from the logit's cell-level miscalibration, confirmed in two client backtests.

## 12. Known limitations

- Price response is logistic in net cost, with one slope; real behavior may show kinks or saturation.
- Positive-only tests do not show how students react to communicated cuts; the support rule limits exposure.
- Retention is a historical lookup that does not respond to aid.
- No cost-to-serve model; the objective is net tuition revenue, not contribution margin.
- Competitor offers are observed only for survey respondents.
- **[v2.5]** The cell-level baseline ignores how award and interest move together inside a cell once staff targeting is replaced by a flat award.
- **[v2.5]** The two-sided rule may often return the status quo when evidence is weak. That is by design, but its commercial implication is that some clients will receive descriptive and policy-documentation deliverables only.
- **[v2.5]** Rank-matching assumes grant rank equals academic rank at each peer.

## Appendix A. What changed from v2 and why

| v2 feature | v2.1 | Evidence |
|-----------|------|----------|
| Observational segment pattern, shrinkage (kappa), scaling and refit | Cut; one anchored slope | Uniform slope +2.7% versus +1.8% realized in the backtest |
| Hybrid forecast-plus-intervene model | Kept in a simpler form | Forecast accuracy identical either way (AUC 0.833), by construction |
| Discontinuity with fixed 0.12 window | Standard package, diagnostics, net-cost denominator; optional | One threshold carries most information |
| Test arms $0 to $4,000 in $1,000 steps | 40/20/40 at $0, D/2, D; stratified; **[v2.5]** all-eligible analysis | Simulated SE 0.548 → 0.438 (40/20/40) → 0.287 (all eligibles) |
| Per-student optimizer | Policy grid | Usable at packaging time; less overfitting |
| 40-draw bootstrap, probability of beating status quo, realization multiplier | Three sensitivity scenarios; backtest diagnostic; **[v2.5]** Monte Carlo disclosure | Probability read 100% at every budget from 1× to 2×; ratio ranged 0.14 to 0.62 |
| Expected-value budget | Budget at all three scenarios; **[v2.5]** count-noise buffer | Bootstrap 95th-percentile spend was 2.8× the budget at 1× |
| Nine scenarios | Four, plus class floor only if it binds | The v2 class-floor scenario did not bind |
| All one-way and two-way tables | Fixed non-overlapping set | Differencing risk |
| **[v2.5]** Power-based screen | Value-of-information screen | Power rule recommends tests that cannot pay back |

## Appendix B. Review findings and their status

**First review (R1 to R12):**

| ID | Finding | Status |
|----|---------|--------|
| R1 | Segment pattern wrong in size and order | Removed with the segment pattern |
| R2 | Recommended setting beaten by uniform slope | Uniform slope is the default |
| R3 | Realization ratio does not carry over | Dropped as a multiplier; Monte Carlo disclosure added (v2.5) |
| R4 | Budget holds only on average | Three scenarios plus the count-noise buffer (v2.5) |
| R5 | Bands and probability uncalibrated | Replaced by three scenarios on the logit slope |
| R6 | Hybrid average does not equal the anchor | Status-quo-point conversion test (v2.5) |
| R7 | Validation from one seed | Monte Carlo study, section 10 |
| R8 | Forecast overpredicts yield (4% against the realized draw; 6.6% against the true expectation) | Out-of-time intercept and slope recalibration |
| R9 | Comparisons not spend-matched | Fair baselines at model-set and matched spend |
| R10 | Pooled estimates differ | Logit-unit pooling, 1.5 SE flag, scenario widening (v2.5) |
| R11 | Class-floor scenario does not bind | Shipped only when binding |
| R12 | Validation cannot see asymmetric response to cuts | Support rule; loss-averse world |

**S4 and S5 re-review (F1 to F20; October 21, 2026), status in v2.5:**

| ID | Finding | Status |
|----|---------|--------|
| F1 | One-sided choice rule tilts toward cuts | Two-sided rule (section 5); audit to test conservatism |
| F2 | Law status quo not representable | Award mode, ladder, cap, horizon, law profile (section 5) |
| F3 | Screen rule power-based | Value-of-information screen (section 4); audit to stress-test |
| F4 | Test cost year-one only | Cost × M; no offset when capped |
| F5 | Estimand undefined | θ at status-quo awards; logit-unit pooling |
| F6 | Grid baseline undefined (O1) | Cell reference award r_c |
| F7 | Randomized-out eligibles unused | All-eligible analysis |
| F8 | Scenario coverage coincidental | Recalibration, cell pooling, Monte Carlo disclosure |
| F9 | Backtest matches spend with truth | Model-set budgets in validation |
| F10 | Count noise ignored | Buffer |
| F11 | Monte Carlo gate miscalibrated | Section 10 |
| F12 | Sample-size assumptions | k = 0.92, eligible yield, scaled dose |
| F13 | 509 fields misread | Field rules (section 2); Appendix D; audit to confirm |
| F14 | Horizon mismatch in v2 build | Horizon = commitment; config validation |
| F15 | Conversion test tautological | Replaced |
| F16 | Wave slopes not estimable | Descriptive; four conditions |
| F17 | Equity audit stale | Blocked from client use until re-run |
| F18 | Negotiation interference | W14; compliance diagnostics; disclosure |
| F19 | "Four cohorts" error | Corrected: 1,917 test students over three cohorts (2023 to 2025) |
| F20 | Guardrail scale | 5% of tuition |

## Appendix C. Segment floor policy [v2.2; defaults confirmed October 20; v2.5 scope]

**Purpose.** A floor stops the optimizer from cutting a policy segment on the strength of an estimate that may be wrong. The first review showed the risk is real: the large cut to international students came from an estimation error, not from the students' behavior. Floors also make access commitments visible and make the cost of honoring them explicit.

**Definition.** A floor is a minimum on a segment's average award across its grid cells (weighted by projected admits), stated as a share of that segment's trailing three-cohort average.
- It applies to first offers not yet released.
- It is a hard linear constraint, so each floor adds one row to the optimizer.
- In supplement mode, formula awards are not changed by the optimizer and act as an implicit floor.

| Segment | Recommended floor | Rationale |
|---------|-------------------|-----------|
| Highest-need and Pell-eligible | 100% of trailing average | Access mission; should rarely bind |
| Other need bands, including No FAFSA | 75% | Limits reallocation to 25% per cycle where evidence is weakest; No FAFSA students must not be penalized for missing information |
| In-state, out-of-state, international, **[v2.5]** and every market tier, including target markets | 75% each | Guards against estimation-error cuts, which are worst in thin target markets (rejects the v2.4 exemption proposed in O14) |
| Transfer (where it is its own grid) | 75% | Small samples |
| First-generation | Client option (confirmed); 100% if mission-driven | Correlates with protected attributes, so the client decides |

**Not used for floors:** academic index or position (the merit grid and the median constraint protect them), region, source channel, and race, ethnicity, or gender (never).

**Rules.**
- Segments under 30 admits are pooled with the nearest segment.
- A floor may relax to 50% only where the randomized arm shows the segment is materially less sensitive and the client approves at the alignment gate.
- Every run reports which floors bind and their shadow prices.
- The per-cell guardrail (no first-offer cut above 5% of tuition) stays.
- Binding frequency is measured in the Monte Carlo study rather than assumed rare.

## Appendix D. ABA 509 rank-matching procedure [v2.5]

For each peer j and the client's own position q:

1. **Applicant values.** Take LSAT_q and UGPA_q from the client's own position distribution.
2. **Peer position.** π_j = mean of CDF_j(LSAT_q) and CDF_j(UGPA_q), using the peer's interpolated 25th, 50th and 75th percentiles.
3. **Peer grant.** Treat π_j as the all-student quantile u. Let r_j be the peer's share receiving grants and f_j the share at or above full tuition.
   - If u < 1 − r_j, the grant is $0.
   - If u ≥ 1 − f_j, the grant is the grant year's tuition.
   - Otherwise, set v = (u − (1 − r_j)) / r_j and interpolate the recipient 25th, 50th and 75th percentiles (linear to the 25th below; capped at tuition above).
4. **Normalize.** Convert to a share of the grant year's tuition (the year before the report), then apply that share to current tuition.
5. **Gap.** Gap_j(q) = peer share − own share at q. Compute the own share the same way, or from client data.
6. **Market gap.** The median of Gap_j(q) across a client-approved peer set of 5 to 10 schools, with its interquartile range.

**Stated assumptions:**
- grant rank equals academic rank;
- the all-class award distribution stands in for entering awards;
- positions are measured against matriculants.

**Validation (synthetic law world).** Twelve peers built from 509-calibrated parameters. Student grants follow g = F⁻¹(Φ(ρ × z_index + √(1 − ρ²) × ε)) for ρ ∈ {0.9, 0.7, 0.5}, with matriculant selection on grant and position. Aggregates are published as the 509 does.

**Pass criteria:**
- per-band |bias| ≤ 5% of tuition, and Spearman ≥ 0.8 across bands, at ρ = 0.9 and 0.7;
- document the failure at ρ = 0.5 and the matriculant-selection bias.

*Illustration (2025 reports):* an applicant at Richmond's 75th position (LSAT 167, UGPA 3.92) sits at about Wake Forest's 66th all-student quantile. That maps to about $43,000 there, against about $51,800 at Richmond.

## 13. Open issues: status after the S4 and S5 re-review [v2.5]

All issues were ruled on in `S4_S5_Rereview_v2.4.md`. "Applied" means the text above reflects the ruling. Items marked "audit" are pending the scoped audit.

| ID | Issue | Ruling | Where applied |
|----|-------|--------|---------------|
| O1 | Forecast baseline | Changed: cell reference award r_c; forecast has no aid fields | Section 4, Response model |
| O2 | Weak evidence | Changed: two-sided rule; automatic weak-evidence state | Section 5 (audit: conservatism) |
| O3 | Uncorrected gains | Changed: fix causes; Monte Carlo disclosure and thresholds | Sections 4, 6, 10 |
| O4 | Grid scope | Confirmed with additions | Section 5, Policy grid scope |
| O5 | Anchor population | Changed: estimand θ; logit-unit pooling; widen on flag | Section 4, Estimand and Anchor |
| O6 | Monte Carlo design | Confirmed direction; numbers changed | Section 10 |
| O7 | Bonus timing | Confirmed; revisions evaluated at b_L for revenue and b_H for spend | Section 5, Increases-only |
| O8 | Verticals | Confirmed; law profile specified | Sections 1, 2, 5 |
| O9 | Interference | Confirmed; W14, compliance diagnostics, disclosure | Sections 4, 9, 10 |
| O10 | Pooling method | Changed: logit-unit pooling | Section 4, Anchor |
| O11 | Departures from the first review | Three scenarios: confirmed (logit slope). No realization correction: confirmed, with disclosure. CVaR: deferred, with count-noise buffer | Sections 5, 6 |
| O12 | Thin-history markets | Confirmed with shrinkage and parent-tier inheritance | Section 5, Targeted objectives |
| O13 | Consumer segments | Confirmed; release criteria | Section 9 |
| O14 | Market tier and targets | Changed: cell rule; floors apply to all tiers; infeasibility reporting | Section 5; Appendix C |
| O15 | Scoring governance | Confirmed with release criteria | Section 7 |
| O16 | 509 definitions | Confirmed; field rules and procedure | Section 2; Appendix D (audit: definitions) |
| O17 | Horizon and conditional awards | Changed: horizon = commitment; conditional modeling deferred | Section 5 |
| O18 | Wave timing | Changed: descriptive; four conditions | Section 4, Timing |
| O19 | Boosted challenger margin | Set | Section 11 |

**New open items for the audit:**
- **A1.** Robustness of the value-of-information verdict for Richmond.
- **A2.** Practical conservatism of the two-sided rule.
- **A3.** ABA 509 field definitions.
- **A4.** The estimand and pooling argument.
- **A5.** Arithmetic in the Richmond baselines.

## 14. Closed decisions [v2.4]

| Decision | Outcome | Rationale |
|----------|---------|-----------|
| Collecting applicant-reported decision-timing data from a third-party law admissions site | **Closed: not used** | Considered as a weekly collection of response-timing data, to track timing by date. The site's license excludes institutional and commercial use and prohibits scraping or bulk collection without written permission. The data are self-reported, skew toward engaged applicants, and are coarse (the share of applicants who heard back, by application period). They measure how fast schools respond, not how applicants respond to price, and they do not link to a client's students. Timing sensitivity is learned from the client's own offer waves, and public applicant-volume reports describe market pace. Revisit only if the owner offers a license on terms that fit. |
