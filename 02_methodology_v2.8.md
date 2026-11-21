# EFA + FAO v2.8: Methodology (lean model, consumer ZIP layer adopted, scenario evaluator and fine-matrix policy, metric definitions)

**Status:** Specification. v2.6 adopts the consumer ZIP data amendment (`_superseded/Amendment_Consumer_ZIP_Data_v2.6_draft.md`; decisions D1 to D5 of October 22, 2026). **The amendment was adopted without a separate audit. Its gate thresholds (G1 to G4) are proposals, and a scoped audit of the consumer layer is still advised before S4 and S5 are signed off.** Counsel reviews the license and the proxy note before the first use in an aid grid at any client. The v2.5 audit result is unchanged (`Audit_S4_S5_Rereview_v2.4.md`, Claude Fable 5.1, October 21, 2026: held with minor revisions; edits E1 to E14 merged and tagged **[v2.5, E<n>]**). Pending sign-off.

**Version history**
- **v2.1** replaced the v2 estimator and optimizer with a simpler design after the first independent review (October 2026).
- **v2.2** merged the October 15 decisions. Additions are tagged **[v2.2]**.
- **v2.3** added batch scoring, the policy lookup, geography and targeted objectives, the evidence audit, and the price-test sample-size guide. Tagged **[v2.3]**.
- **v2.4** added the ABA 509 market layer, program-length horizons, timing by wave, and the boosted-model challenger rule. Tagged **[v2.4]**.
- **v2.5** merges the required-before-build edits from the S4 and S5 re-review (`S4_S5_Rereview_v2.4.md`; edits S4-1 to S4-14 and S5-1 to S5-10). Changes are tagged **[v2.5]**, with the edit number where one applies. The v2.4 text is kept as `_superseded/02_methodology_v2.4.md`.
- **v2.5 audit addendum** merges the audit's required edits E1 to E14 (`_superseded/CHANGELOG_v2.5.md`, addendum). Tagged **[v2.5, E<n>]**.
- **v2.6** adopts the consumer ZIP data amendment and resolves five points raised on reading it: P4 report-only everywhere, P1 as the only blocking proxy gate, the G2 power question at law size, the credit-data rule narrowed, and the tier count under the law cell cap. Tagged **[v2.6]**. The v2.5 text is kept as `_superseded/02_methodology_v2.5.md`.
- **v2.7** (November 5, 2026) records Jason's decisions of November 4 and 5 after the Richmond scenario workbook review: the per-cell guardrail is removed; the threshold freeze is dropped for client-declared bands; the policy of record is the client's fine matrix, with an optimizer decision layer of at most floor(admits ÷ 30) parameters; a scenario evaluator with tuition, class-size, out-of-state and yield levers is added; small-cell suppression becomes a per-client setting; the screen's price-test verdicts are marked pending a re-run. Tagged **[v2.7, V27-n]** (`_superseded/Change_List_v2.7_draft.md`). The v2.6 text is kept as `_superseded/02_methodology_v2.6.md`. **The v2.7 edits have not been separately audited; the guardrail, screen and disclosure edits are the ones to review first.** **[v2.7, V27A] Addendum (November 13, 2026):** the evaluator gains a combined target-state market tier with its own incentive scope, a class range of 100 to 140 under a hard cap with a shrink-path rule, pool tripwires and net-price readouts (V27A-01 to V27A-07; see `_superseded/CHANGELOG_v2.7.md`).
- **v2.8** (November 16, 2026) applies the Session B design audit (`Audit_Session_B_Design_Report.md`), accepted by Jason on November 16: metric definitions (Appendix F), two named NTRs, the discount-rate and median bases, shock calibration from public data and a year-shock world (W22), law-size stability rules, the small-cell rule for files and public material, a general priority segment in place of the target-state tier names, the workbook-first sequence, and three simplifications (tripwires replaced by a pool strip, net-price readouts reduced to two lines, goal-seek and the schedule deferred). Tagged **[v2.8, Bn-m]** by audit finding. The v2.7 text is kept in `_superseded/02_methodology_v2.7.md`. Decisions are logged in `DECISIONS.md`.

**Maintenance status [v2.8, B7-12].** Year 1 (Richmond 2027) uses sections 1 to 3, section 5 (scenario evaluator), sections 6, 9 and 12, and Appendices D and F. The following are **frozen**: kept as written, not updated by later change sets until a client triggers them: the price-test design, sample size and screen (section 4, from "Evidence sources" item 1 through "Timing and sensitivity by date"), moderator discovery, increases-only evaluation, batch scoring (section 7), the consumer ZIP module (section 2 consumer layer, section 9 consumer subsection, Appendix E), the boosted challenger (section 11), and worlds W12 to W15 and W19 to W21L (section 10).

Results quoted here come from the v2 build on synthetic data unless marked otherwise. Items marked **[to build]** are not yet implemented.

**Design principle:** be rigorous at the one point where simplicity loses the answer (the level of price sensitivity) and simple everywhere else. **[v2.5]** Rigor at that point includes not acting on the level when the evidence cannot tell which side of break-even it falls.

## 1. Scope

Two linked products and one monitoring layer share one data model.

- **EFA (enrollment funnel analysis):** where do prospects drop out, and what predicts movement through inquiry, application, admit, deposit, and enrollment at census?
- **FAO (financial aid optimization):** given the projected admitted pool, a budget, and goals, what award policy should the institution use for flexible aid?
- **Monitoring [to build]:** during the cycle, how is the class pacing against the same week of the prior two cycles and the plan **[v2.8, B3-4]**, and where is melt risk?
- **Scoring and targeting add-ons [v2.3]:** batch enrollment-probability scores, a policy lookup, and targeted objectives by segment or market.
- **Consumer ZIP layer [v2.6]:** an optional add-on that appends neighborhood-level capacity indicators from ZIP5 for targeting, the forecast baseline, and, only under gates, a derived capacity tier in the aid grid (sections 2, 5 and 9; Appendix E).
- **Scenario evaluator [v2.7, V27-10, V27-20]:** scores award and admit-rate scenarios the client writes, with a response based on client-input until an anchor exists. It evaluates and does not recommend (section 5).

Undergraduate first-time and transfer cohorts are in scope now. Graduate and professional programs are in scope for the descriptive layers (funnel, pacing, loan-cap exposure). They enter the price model only once a program has its own design-based price evidence.

**[v2.5] Law profile.** JD programs use the law profile in section 5: total-award mode, a ladder to tuition, a horizon equal to the award commitment, and position bands. A law school with no usable design-based evidence (section 4, evidence audit) receives EFA, monitoring, the 509 market view, the evidence audit, and a written status-quo grid. It does not receive an optimized grid.

## 2. Funnel analysis

**Stages:** inquiry, application, admit, deposit, enrolled at census. Stealth applicants (the application is the first touch) skip the inquiry stage and are flagged, not dropped. Deposit to census is reported as its own stage so melt is visible.

**Descriptive layer:** a fixed, published set of tables: each dimension by cohort, plus a short list of approved two-way tables pooled across cohorts. Tables are designed so that suppressed cells cannot be recovered by subtraction. **[v2.7, V27-13]** Small-cell handling follows the engagement's `small_cell_policy`: the default suppresses cells with fewer than 10 students and applies complementary suppression; a client may elect no suppression for named, authenticated client roles (Richmond has; section 9, Small-cell disclosure).

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
- **Derivation:** before removing addresses, the client runs a script that returns the metropolitan or micropolitan area (CBSA code), state, ZIP3, and a distance-to-campus band. ZIP3 alone does not map cleanly to a metro area. **[v2.6]** ZIP5 is requested only in the separate `zip_key` file (Appendix E), and only when the consumer add-on is elected.
- **Reporting:** the funnel is reported by market. **[v2.7, V27-13]** Under the default `small_cell_policy`, markets under 10 students are pooled into an "other" tier; under a no-suppression policy they are shown.
- **Optional descriptive layers:** market penetration (enrolled students relative to public counts of high school graduates or population by market) and source effectiveness by market.
- **Consumer ZIP layer [v2.6].** See the next subsection. It replaces the v2.3 rule that consumer segmentation is descriptive only and never enters the aid grid.


**ZIP consumer index and capacity tier [v2.6].** An optional add-on. The client supplies ZIP5 in a separate file (Appendix E); Frankel appends neighborhood-level indicators from a licensed or free source and derives a capacity tier.

*Purpose.* The tier measures neighborhood-level capacity to pay and expected response to price. It is not a measure of, or a substitute for, race, ethnicity or any protected trait, and it is not constructed, adjusted or selected using race data (section 9).

*Source.* The module is source-agnostic: Claritas direct, client-supplied derived fields, or the free ACS/IRS table (ZCTA mapped to ZIP through the HUD USPS crosswalk, O29). **P$YCLE Premier is the primary source for capacity** (Claritas's financial-behavior segmentation: 60 segments in 12 lifestage groups, built partly on estimated household liquid assets). PRIZM Premier is optional for outreach targeting. One licensed product is used per engagement, confirmed by the bake-off in section 10 against the free baseline.

*Construction (a deterministic, published formula; no trained model).*
- **Input:** for each ZIP5, the household distribution across segments. A ZIP with fewer than 3 segments is pooled to its parent ZIP3 for the index, so no output reveals a single dominant segment.
- **Segment score:** the source's own affluence ordering of segments (or its asset index if licensed). We do not substitute our own judgment.
- **ZIP index:** the household-weighted mean segment score, plus the share of households in the top affluence quintile.
- **Capacity tier:** cut on the prior-three-cohort admit pool and frozen at cycle start, by the same rule as position bands.
  - **Tier count:** configurable at 2 or 3. **Default 3 for undergraduate, 2 for law** (section 5 explains why).
  - **Cut points (2 tiers):** chosen before the cycle by out-of-time backtest from three pre-registered candidates (top third versus the rest, median, bottom third versus the rest), then frozen.
  - **Thin tiers:** a tier needs at least 30 admits per cohort or it merges with its neighbor.
- **Unknown:** unmatched or non-ZIP addresses (PO box, military, international) are **Unknown**, never imputed, and reported as their own category. In the grid, an Unknown group below 30 admits per cohort is pooled with the tier that has more admits and is labeled "Unknown/other".
- **Address:** the permanent address at application, ZIP5 only. For JD applicants it may be a family address; the bake-off reports lift by address type where the client supplies both.
- **Reported:** the national percentile of the ZIP index beside the tier.
- **Never used:** segment codes, lifestage groups, ZIP5 as a feature, household identifiers.

*What is retained.* ZIP5 is used once, by the append job, from the separate `zip_key` file, and is deleted within 30 days of append QA or at engagement close. The analysis tables keep state, **ZIP3**, the ZIP index, the top-quintile share, the tier, the match flag and the vintage. No ZIP5 appears in any analysis table, output, dashboard or score file.

*Vintage.* One vintage is frozen per cycle. All historical cohorts are scored with that same vintage, and sensitivity to two vintages is tested (O30).

*Law.* The same rules and gates as undergraduate, with the program's own evidence, pooled across cohorts when a cohort has fewer than 300 admits. Expect a weaker signal than undergraduate. The gates decide, not the expectation.
**Market reference data (ABA 509) [v2.4; field rules v2.5].** For law schools, the public ABA 509 disclosures are an external reference dataset.

*Field rules [v2.5].* The audit confirmed these against the ABA's Standard 509 report form (headers and footnotes) and the data arithmetic. The ABA's definitions document itself was not read:
- Grant counts and percentiles cover all full-time JD students in the academic year *before* the report year, and the percentiles are among recipients only. Evidence: Richmond's 75th-percentile grant equals the prior year's tuition in both the 2024 and 2025 reports.
- LSAT and UGPA percentiles describe matriculants, not admits.
- Yield = matriculants from the applicant pool ÷ offers.
- A nonresident tuition of 0 at a private school means "same as resident" and is normalized and flagged. **[v2.5, E10]** This affects a few private schools (4 of 111 in the 2025 file, Richmond among them).
- **[v2.5, E10]** Conditional-scholarship counts: report year Y lists the entering classes Y − 1, Y − 2 and Y − 3, and the reduced-or-eliminated count is final after the first year. Cohort labels come from the report year, never from spreadsheet headers (the 2021 and 2022 files carry stale labels). Peers with conditional prevalence above 10% are flagged: their all-class grant distribution understates entering awards.
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
- **Institutional net tuition** = tuition minus institutional gift aid; required fees are reported separately **[v2.8, B3-1]**. The two NTR measures, `ntr_y1` and `ntr_horizon`, are defined in Appendix F.
- **Need index:** EFC through 2023-24 and SAI from 2024-25, labeled by type. "No FAFSA" is a separate category. Institutional-methodology need (CSS Profile) is accepted where the client uses it.
- **Decision date:** the student's deposit deadline or the date the student deposited, whichever is earlier. Any award or revision dated after it is excluded from price models. Revisions before it are kept with their dates and logged as revisions. **[v2.5]** Every revision carries a reason code: student request, documented competing offer, staff-initiated, or appeal.
- **[v2.5] Renewal rule:** each institutional award records whether it renews as fixed dollars or as a percentage of tuition, and any renewal conditions (GPA, credits).

**Excluded groups [to build]:** a configurable table (athletes, tuition waivers and exchanges, special scholarships, others the client names). Excluded students keep their current packages, are left out of price estimation, and are reported separately so class totals reconcile. **[v2.5]** Awards above full tuition (stipends) are an excluded component in total-award mode.

**Consumer fields [v2.6].** Two tables carry the add-on: `zip_key` (restricted; append job only; deleted after append QA) and `student_consumer` (ZIP index, top-quintile share, tier, match flag, vintage; no ZIP5). Schema in Appendix E.

**Data tiers [to build]:**
- **Tier 1 (minimum):** three cohorts, final packages by component, offer dates where available, and the merit grid. Supports EFA, the forecast, monitoring, and a discontinuity-only price anchor with wider bands. **[v2.6]** The `zip_key` file is an optional add-on at this tier. **[v2.5]** Where the client has no published threshold (common in law), Tier 1 supports no anchor, and FAO runs in the weak-evidence state (section 5).
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
   - **Analysis population [v2.5, S4-1; revised E1]:** **every randomized eligible admit**, with eligibles randomized out of the test serving as additional $0 observations (intent to treat). This cuts the logit-slope standard error by about 20% (analytic factor 0.76) at no extra cost. **The all-eligible estimate is primary only where staff are blind to test membership** (the bonus is a formula line, with no test flag in the CRM). Otherwise the primary estimate is test-only at dose 0, and the all-eligible estimate is reported as secondary. The reason: the all-eligible estimate is exposed to any staff behavior that differs by test status (a 0.10-logit test-status effect biases it by about 20%), and the test-only estimate is not. Test-only estimators carry no bias against θ when the AME is evaluated at status-quo awards; the 6% to 11% gap seen earlier came from evaluating at received doses.
   - **Estimation:** logit of enrollment on the dose and pre-specified covariates. The effect is computed at dose 0 (status-quo awards), not at the received dose.
   - **Stratified assignment:** randomize within strata (need band × residency for UG; position band × wave for law), using blocked randomization so the arm shares are exact.
   - **Compliance check:** compare other discretionary aid, reconsideration requests, and revisions between arms and between test and non-test eligibles. The aim is to detect staff offsetting or negotiation spillover. **[v2.5, E1]** A yield contrast between the test $0 arm and non-test eligibles cannot detect a test-status effect of the size that matters (SE about 1.5 points at Richmond's size), so it is not the check. The checks that work are the process contrasts above and blinding of staff to membership.
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
- 0.76 is the analytic gain from the all-eligible analysis; simulation in logit units gives 0.80 **[v2.5, E2]**. Use 1.0 in place of 0.76 where the primary estimate is test-only (no staff blinding; see Analysis population).
- k is the covariate-adjustment factor. **Use k = 0.92 by default, or √(1 − R²) from the client's out-of-time forecast.** The v2.3 value of 0.85 reproduced the prototype only because it used 21% yield where the test population's yield was 17%. The oracle bound in the synthetic world is 0.86.

The smallest detectable effect at 80% power (two-sided, 5%) is about 2.8 × SE. It is reported **for information only**; it does not decide whether to run a test.

*Richmond example (650 eligible admits, 40% in the test, p = 0.21, all-eligible analysis). SE / MDE in points per $1,000:*

| Top arm | 1 cycle | 2 cycles | 3 cycles |
|---|---|---|---|
| $4,000 | 0.98 / 2.75 | 0.69 / 1.94 | 0.57 / 1.59 |
| $8,000 | 0.49 / 1.38 | 0.35 / 0.97 | 0.28 / 0.79 |

**Break-even slope.** β\* = 100 × p × 1,000 / (net tuition per enrollee − mean bonus). It is about 1.1 in the synthetic UG world and about 0.9 to 1.0 at Richmond. Plausible effects sit near break-even in both verticals. The decision therefore turns on which side of break-even the slope falls, not on whether it differs from zero.

**Cost.** Expected cost of the test = M × (test students) × E[p × bonus], where M = Σ_t<H s^t is the award-commitment multiplier (H years, persistence s).
- **[v2.5, E6] Capped or banded** (hard cap or class band): expected cost at the prior = M × n_test × E[(p + θ × dose ÷ 100) × bonus]. Induced enrollees carry the bonus too, and there is no revenue offset. At Richmond ($4,000, one cycle) this is about $375k at the prior mean, against $315k at zero effect.
- **Uncapped:** the prior-expected net cost (it can be negative near break-even).
- **Both regimes:** the ratio gate and the 5%-of-net-tuition-revenue gate use the **zero-effect cost**, so they stay defined when the expected net cost is negative. Net value uses the regime-appropriate expected cost.

At Richmond (M ≈ 2.92, renewable awards), cost per test student at zero effect is about **$1,226 with D = $4,000 and $2,453 with D = $8,000**, against the year-one-only $420 quoted in v2.3.

### Price-test screen rule [v2.5, S4-7; replaces the v2.3 rule]

The v2.3 rule (recommend a test when the smallest detectable effect is at most about 2.3 points per $1,000) is retired. It measured detectability rather than decision value, shifted with price level, and ignored break-even, class caps, and renewal costs.

**Inputs from the client at scoping:**
- N, eligible admits per cohort;
- p, eligible yield;
- tuition, and the mean institutional award per enrollee;
- award commitment H, persistence s, and the renewal rule;
- capacity: class band ± %, or "uncapped" **[v2.5, E7: a mandatory scoping input; the verdict depends on it]**;
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
4. **EVPI** = U × (Σ_i w_i max_j V[i, j] − Σ_i w_i V[i, j0]), where j0 is the grid the two-sided choice rule picks under the prior. **[v2.5, E5]** j0 may be a reallocation rather than the status quo; V[i, j0] is never dropped. **Gate 1:** if EVPI ≤ the cost of the cheapest admissible design, the verdict is **Not recommended**.
5. **EVSI.** For each design (D, K), compute SE_b in logit units. For 21 b-nodes × 21 z-nodes: b̂ = b_i + z × SE_b; update the posterior; choose the grid with the production two-sided rule at the posterior quantiles; score it at b_i. EVSI = U × (EV_test − EV_no test). **[v2.5, E4]** Both expectations score every grid by the same function (realized revenue at the true slope, infeasibility uncosted). The production two-sided rule is quantile-based, so EVSI may be **negative**: a narrower posterior loosens the feasibility checks and admits riskier grids. A negative EVSI is reported with its sign, yields **Not recommended**, and triggers a review of the rule's quantile margins. The same preposterior analysis uses the choice-rule objective in section 5 (maximize net tuition revenue at b_M) **[v2.5, E3]**.
6. **Net value** = EVSI − expected cost − F × K, with the expected cost for the program's regime (see Cost above).

**Verdicts**
- **Recommend:** all of the following hold.
  - Net value ≥ max($50,000; 0.5% of one cohort's multi-year net tuition revenue).
  - EVSI ÷ (zero-effect cost + F × K) ≥ 1.5.
  - Zero-effect cost ≤ 5% of one cohort's multi-year net tuition revenue.
  - The office can randomize and log; U ≥ 2; the client alignment gate accepts the disclosure.
- **Optional:** net value > 0, but a threshold or gate above is missed.
- **Not recommended:** net value ≤ 0, or Gate 1 stops the computation.

**Reported every time:** EVPI, EVSI (with its sign), cost, the MDE, β\*, the grid change the test would most likely trigger, and **[v2.5, E7]** the verdict at the client's capacity band and at ±5% and ±10%.

The client's VP or Director of Enrollment, or a Dean, decides per engagement.

*Worked example (Richmond economics, revenue objective, ±3% class band, median-position floor, prior θ ~ N(1.0, 0.5²), U = 3).* **[v2.8, B2-2: computed under the 5% guardrail; pending re-run (O36); do not quote]** The verdict is **Not recommended** at 600, 1,000, 2,000, and 4,000 eligible admits: EVPI is $0.29M to $1.92M, against test costs of $0.32M to $1.99M. At Richmond's own size, EVPI is $0.10M to $0.68M across priors.
- Under an uncapped scale decision, the same economics give Recommend at every size. The decision space, not N, drives the verdict.
- **[v2.5, E7; v2.8, B2-2: computed under the 5% guardrail; pending re-run (O36); do not quote] At a ±3% class band the verdict is Not recommended at every size and prior tested** (four pools, five priors, renewable and one-year bonus, median floor). **The verdict turns on the capacity band:** at ±10%, a five-band Richmond pool gives Optional or Recommend, and at ±5% it is Not recommended under the capped cost and Optional under the net cost (a judgment call on the cost model). The capacity band is therefore a mandatory scoping input.
- **[v2.5, E7; superseded pending re-run, v2.7, V27-04] A position target did not raise the value of a test at the 5% guardrail.** Aid cannot move Richmond's enrolled median, so a target shrinks the admissible set and the test has nothing to decide. The earlier suggestion to rerun the screen when a client names a slope-sensitive target is withdrawn.
- **[v2.5, E4] Sign of EVSI.** On the five-band Richmond pool at ±3%, EVSI is −$0.12M under the production rule; an unconstrained Bayes rule on the same pool gives EVSI ≥ 0.

**[v2.7, V27-04, V27-05] Status of the verdicts above.** Every "Not recommended" verdict and the statement about position targets were computed with the 5% per-cell guardrail in force. The guardrail is removed in v2.7, which enlarges the set of grids the optimizer may choose and can raise the value of learning the price slope. Richmond's band of ±4 is ±2.9% at a class of 140 and ±3.6% at 110, so the re-run reports ±3% and ±4% at the class target in use **[v2.8, B2-2]**. **Do not quote these verdicts to a client.** Open issue O36: re-run the screen without the guardrail, on stylized pools and on the production optimizer with a 509-calibrated pool, with the median floor, at ±3%, ±5% and ±10%; report before any statement about a price test.

The audit reproduced the worked-example table to the dollar and extended it (37 verdict runs at N = 650). These runs use **stylized pools**: a two-band pool and five-band pools calibrated to Richmond's 509 profile. They are not results from the production optimizer. **The production screen must run on the real optimizer with a 509-calibrated pool**, and the size of the negative EVSI there is untested.

**Cheaper randomized options (deferred, section 11):**
- mechanism tests (deposit deadline or award timing), which cost almost nothing in dollars;
- a one-year (non-renewable) bonus, at about one-third the cost, though it measures response to a different treatment.

### Timing and sensitivity by date [v2.4; revised v2.5, S4-8]

Whether price response changes through the cycle is learned from the client's own data, not from outside timing data.

- **Waves:** two by default. Three only if offers are released in at least three batches at least three weeks apart. Randomization is stratified by wave.
- **Estimation:** pooled across waves. Per-wave slopes are reported as descriptive ranges. At Richmond with one cycle and D = $4,000, the per-wave MDE is about 5.1 points per $1,000, and the MDE for a wave difference is about 7.3 (test-only basis; 3.9 and 5.5 with the all-eligible analysis) **[v2.5, E14]**.
- **Negotiation and reconsideration:** in law, these drive many revisions. They are post-treatment outcomes, logged with reason codes, and never used as price variation. Reconsideration and increase rates by arm are reported as compliance diagnostics.
- **When a wave slope may change a recommendation:** only if all four hold.
  1. A single early-versus-late contrast was pre-registered with its direction.
  2. Pooled over at least two cycles, the contrast is significant one-sided at 5% and at least 50% of the pooled slope.
  3. It beats one slope in held-out policy value by more than 1 SE.
  4. A Monte Carlo timing world confirms it.
- **Market timing context:** public applicant-volume reports describe how the market is pacing. They are descriptive and never feed price estimates. Applicant-reported timing sites are not used (closed decision, section 14).

### Anchor [revised v2.5, S4-2]

- **Separate estimates.** The experiment and the discontinuity are reported separately, each converted to a **logit slope on its own sample at status-quo awards**.
- **Pooling.** The two logit slopes are pooled by inverse variance into the anchor b̂ with SE s. **[v2.5, E13]** The discontinuity's weight in the pooled anchor is reported beside the anchor and capped at 30%. (If the local slope at the threshold differs from the experiment's, the pooled bias is at most the weight times the difference.) Under the one-slope model both sources estimate the same b, and their AMEs differ only through p(1 − p).
- **Disagreement flag:** raised when |z| > 1.5 in logit units. On a flag, the sensitivity scenarios widen to span both estimates. After flags in two consecutive cycles, the anchor becomes experiment-only.
- **Tier 1 without a test:** the anchor is the discontinuity (or qualifying policy change) alone, labeled local. A Tier 1 client with no usable source has **no anchor**.

Synthetic results (v2 build, AME scale, older pooling): experiment +0.63 (95% interval −0.46 to 1.72); discontinuity +2.22 (0.63 to 3.81); pooled anchor +1.14 (0.24 to 2.04); θ = 1.31.

*Judgment call:* pooling versus experiment-only. Pooling is defensible while the two estimates are compatible and the discontinuity passes diagnostics. What would change this: placebo or density failures, repeated disagreement, or the prestige-bump Monte Carlo world showing that pooling fails coverage while experiment-only passes.

### Response model [revised v2.5, S4-3 and S4-4]

One slope for everyone, on the logit scale:

`p_i(a_c) = expit( logit p*_i + b × (a_c − r_c) )`

- **Forecast model:** a regularized logit with a fixed set of about 10 to 12 decision-date features: academic index or position band, need band, residency or market, program, decision type, application timing, campus visit, engagement, first-generation status, and stealth flag. **It contains no aid fields.** Protected attributes are excluded. **[v2.6]** The consumer capacity tier may be added as one of the terms only when the forecast-baseline gates pass (section 9).
- **Recalibration:** out of time, on the latest complete cohort: logit p\* = α + γ × logit f. The forecast is labeled "unstable" when the 90% confidence interval of γ excludes the band [0.8, 1.2]; γ is reported with its interval. At fewer than 1,500 admits per cohort, two cohorts are pooled for the check **[v2.8, B4-3]** (at law size the sampling SD of γ is about 0.14, so a point rule would flag a correct model about one cohort in six).
- **Reference award r_c** for the student's cell c: the mean status-quo flexible award among admits in that cell in the recalibration cohort (supplement mode: the discretionary component; total mode: the total institutional scholarship). It is adjusted for known rule changes (tuition, merit grid) to the live year. p\* estimates yield under the status-quo *policy* for students like this one, so r_c is the matching award. Formula awards stay fixed.
- **Known limitation:** replacing staff targeting within a cell with a flat cell award changes how award and interest move together inside the cell. The first-order model ignores this. Monte Carlo worlds W1 and W16 to W18 measure the error.
- **b** comes from the anchor.
- **Conversion test:** the model's AME at status-quo awards on the experiment's eligibles, computed with **recalibrated** p, must match the experiment's own status-quo AME within 1.645 × the SE of the difference **[v2.5, E12]**. The acceptance fixture carries a 10% level bias and must fail; the unbiased fixture must pass. The v2.4 "within 1%" check is retired: it tested an identity that holds by construction.
- **Holdout test:** on the holdout, Σ_c n_c × mean p_i(r_c) falls inside the forecast interval.
- A single logit slope is not a single percentage-point effect. Students near 50% yield respond most in points, so the model still targets undecided students without estimating segment differences.
- **Support:**
  - Communicated offers (revisions and renewals) may only rise, and by no more than the largest tested bonus.
  - **[v2.7, V27-02]** First offers for a **Frankel-recommended** grid are not limited by a per-cell guardrail (removed; section 5). A cut is reported with its evidence label (`observed` or `extrapolated` against the cell's historical award range); the label states how well the response is known and never blocks a grid. Floors (Appendix C) and the choice rule still apply. Client-authored scenarios are evaluated, not constrained (section 5, Scenario evaluator).
  - **[v2.2]** First-offer increases are also limited to the largest tested bonus (with no test, the largest award jump the qualifying discontinuity observed). With no anchor, no level changes are allowed.

**Why one slope:** in the v2 backtest the uniform slope produced the highest realized gain of any setting: +$0.60M (+2.7%), against +$0.42M (+1.8%) for the v2 recommended setting. The v2 segment pattern was precise but wrong in size (for example, international students estimated at 0.18 against a true 1.34). This is one synthetic seed and one cohort. The uniform slope captured 44% of the oracle's gain. It remains to be confirmed in section 10.

### Moderator discovery [v2.2; protocol v2.5]

Historical data may be used to **propose** candidate moderators of price sensitivity. They do not set slopes.

- **Candidate list (fixed):** relative position band (primary for graduate and professional programs; section 2), engagement index, market award-gap band (section 2 and Appendix D), market tier, **[v2.6]** consumer capacity tier (section 2), need (if collected), and application timing.
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

- **Count rule:** cells ≤ floor(projected admits per cohort ÷ 30). Richmond's limit is 21. **[v2.7, V27-07]** The rule bounds the optimizer's **decision layer**, not the policy of record. The decision layer is built by merging adjacent score bands within residency × GPA class until each group has at least 30 projected admits; on the Richmond scenario workbook this gives about 13 groups (16 to 17 at 20 admits), plus one out-of-state incentive, 14 parameters in all. At a class of 100 the limit is about 15; the merge rule is re-run on the projected admits of the scenario in use **[v2.8, B2-5]**. The **policy of record** is the client's fine matrix (at Richmond, LSAT band × GPA class × residency), rendered from the decision layer by a deterministic rule; a client may also author fine cells directly for evaluation. Fine cells are fixed by definition, so the policy lookup and the equity audit are unchanged.
- **UG profile:** academic-index quintile (5) × need band (5, including No FAFSA) × residency (3), giving 75 cells. When the count rule fails, collapse need to 3 bands first, then the index to tertiles.
- **Law profile:** position band (5) × market (home state / other), optionally × need (2), giving 10 to 20 cells. **[v2.6]** With the consumer capacity tier, see the next subsection (law default: two tiers, the tier replaces market). **[v2.7, V27-08]** For a client with a fine matrix, the law profile is the merge-rule decision layer above; the five-band profile remains the default for a client without one. Geography enters as a priority segment on each cell (Richmond: one combined segment of client-listed states, NY and PA, within out-of-state) and one incentive aimed at the segment or at all out-of-state, with an optional score floor **[v2.8, B2-1]**. Per-state segments, MSAs and ZIP3 are deferred (section 11).
- **Market tier [v2.3]:** a client that targets markets may replace residency with a market tier (home market, priority or target MSAs, other in-state, other out-of-state, international). At most 5 tiers, with the total still within the count rule and at most 125 cells. **[v2.7, V27A-01; v2.8, B5-1]** The evaluator uses a lighter form: one priority segment per scenario, a client-defined set of cells within one residency (Richmond: NY and PA within out-of-state; a public client's in-state priority is the same construct). Per-state segments wait for state-level data.


### Consumer capacity tier in the grid [v2.6]

The tier may be a grid dimension only when gates G1 to G4 and P1 have passed and counsel has reviewed the license and proxy note (section 9, Appendix E). Otherwise the tier is used only where its narrower gates allow (targeting; forecast baseline), or not at all.

**Tier count.** Configurable at 2 or 3: **3 for undergraduate by default and 2 for law by default.**

**Route into the grid.** The tier enters by one of three pre-registered routes. The route is chosen by out-of-time backtest before the cycle and frozen.
1. **Split** the No-FAFSA need band into tier cells (undergraduate default; adds 1 cell for 2 tiers or 2 cells for 3 tiers).
2. **Substitute** the tier for a weaker dimension, when the backtest shows a gain and the cell cap allows. For undergraduate, collapse residency to two levels. **For law, the tier replaces market** (home state or other).
3. **Add** the tier as a full dimension, only if the cells that remain after merging thin cells stay within the count rule.

If no route passes the backtest, the tier is not a grid dimension.

**Cell arithmetic at law size (650 admits, cap 21; at about 600 admits the cap is 20).**

| Grid | Cells | Fits the cap |
|---|---|---|
| Position (5) × market (2) | 10 | Yes (v2.5 profile) |
| Position (5) × tier (2) | 10 | Yes |
| Position (5) × tier (3) | 15 | Yes |
| Position (5) × market (2) × tier (2) | 20 | At the cap; thin cells are likely, so merging applies |
| Position (5) × market (2) × tier (3) | 30 | No |
| Position (5) × tier (2) × need (2) | 20 | At the cap |

**Why two tiers for law, set per program, and not a per-admit choice of which two apply.** The idea that the third tier "is rarely relevant for any given admit" is handled by the merge rule: a tier with fewer than 30 admits per cohort merges with its neighbor, deterministically, for every student alike. Choosing which tiers apply student by student would make the grid depend on a student-level decision instead of a cell definition. That cannot be documented as a policy for counsel, it breaks the policy lookup (the award is the cell's award) and the equity audit (which assumes fixed cells), and it moves toward per-student optimization, which is a closed decision. A fixed two-tier cut keeps the grid inside the count rule with room to spare.

**Floors.** Floors apply to every capacity-tier cell under the same segment rules (Appendix C).

*Judgment call:* with fewer than three cohorts, or where G2 or G4 cannot be powered at the client's size (reported from the consumer worlds, section 10), the default is no tier in the grid. What would change this: the W21L power results showing that a real signal at law size passes G2 in at least 70% of seeds.
### Ladder and cap [v2.5, S5-2]

- **Ladder:** $1,000 steps (UG) or $2,500 steps (law), up to tuition. **[v2.7, V27-09]** The ladder is a solver setting. It does not limit client-authored awards, which the evaluator accepts at any amount up to tuition.
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
  - **[v2.7, V27-06]** Cut points are the client's declared bands, used as given. Cut points that Frankel computes (trailing three cohorts) are fixed for the cycle at cycle start. There is no minimum number of cycles for which a band is frozen.
  - Changes take effect only at cycle boundaries and are recorded in a `policy_changes` table: effective date, old and new cut points, and old and new awards.
  - Award differences between adjacent cells at a cut point are logged for the evidence audit and shown as the step-size table. The log is informational. Trade-off: a threshold that moves every cycle may not qualify as a discontinuity source (section 4, stability criterion); the barbell-to-even policy change route is unaffected (O39).
- **Status-quo grid:** derived empirically (mean award by cell in the latest cohort) and confirmed by the client as matching practice before any optimization.
- **Policy lookup [v2.3]:** the recommended award for a student is the grid award for that student's cell. It is the policy applied, not a separate per-student optimization. **[v2.7, V27-07]** The cell is a fine-matrix cell and the award is its fine-matrix award.

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

  This targets at most a 5% chance of overrun from enrollment noise alone. At Richmond the buffer is about 15% of first-year scholarship spend (award-weighted; 12% would apply only with equal awards) **[v2.5, E9]**.
- **Class size:** an optional expected class band (floor and ceiling), checked at all three scenarios. The law default is ±3% of the status quo.
- **Per-student aid cap** as above, and an optional cap on the discount rate, stated as `discount_entering_y1` or, once multi-year evaluation exists, `discount_all` (Appendix F) **[v2.8, B3-2]**.
- **No per-cell guardrail [v2.7, V27-01]:** the v2.5 rule (S5-5: no first-offer award more than 5% of tuition below its status-quo level) is removed, as a constraint, a flag and a reported item. The Richmond scenario workbook moves awards well beyond that limit as ordinary levers (a fixture check is in the git-ignored assessment memo). Instead of a flag, every run publishes a **step-size table**: award differences between adjacent cells, with no threshold and no message. Segment floors below still limit reallocation.
- **Segment floors [v2.2]:** the average award across a policy segment's cells may not fall below a set share of that segment's trailing three-cohort average (Appendix C). Each run reports which floors bind and their shadow prices. **[v2.7, V27-19]** Floors are kept, and are evaluated on the rendered fine matrix, weighted by projected admits.
- **Excluded groups** keep their current packages.

### Choice rule [v2.5, S5-1; replaces the v2.4 rule]

1. **Scenarios:** b_L = max(0, b̂ − 1.2816 s), b_M = b̂, b_H = b̂ + 1.2816 s.
2. **Feasibility:** a grid is feasible only if every constraint holds at b_L, b_M **and** b_H.
3. **Choice:** maximize net tuition revenue at b_M, subject to the gain over the status-quo grid being ≥ 0 at **both** b_L and b_H. **[v2.5, E3]** The screen's preposterior analysis uses the same objective, so the screen and the optimizer pick the same grid on a shared fixture.

The v2.4 rule checked only the low scenario. That approves any cut the middle scenario favors, because a cut always gains when students are less sensitive, and the rule never checked the case where they are more sensitive.

**Weak-evidence state.** Triggered when b̂ − 1.2816 s ≤ 0, or when no anchor exists. Every view carries "Evidence too weak to change aid levels." In this state:
- any change of more than 1% in expected spend at b_M is blocked;
- only reallocations that are non-negative at b = 0 and at b_H pass;
- with no anchor, the output is the documented status-quo grid.

**No admissible grid.** If no grid beats the status quo under the rule, the output is the documented status-quo grid, the reasons, and the screen's evidence plan.

*Audit result (Task 2):* the two-sided rule is kept. It binds for level cuts under weak evidence, which is where it should: on the two-band Richmond pool the one-sided rule picks a $1,000 cut whose downside is $0.5M to $1.0M over three cohorts, and the two-sided rule returns the status quo. It is not biased toward the status quo beyond what the pool dictates: it returns the status quo in 5 of 5 priors on the two-band pool, which has no admissible reallocation by construction, and in 0 of 5 on the five-band pool. In the Lakeshore backtest it never binds, because any reallocation gains at any slope there. What loses money in Lakeshore is forecast error, which no slope rule addresses. Posterior expected value without gain tests picks grids that lose at the 10th percentile; minimax regret picks cuts with negative expected value. *Judgment call:* the objective stays at b_M rather than a posterior expectation; what would change it is a Monte Carlo world where the two differ by more than the fair-baseline margin.

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
| Median position (law) **[v2.5, E8]** | Σ over cells at or above band m of n_c p_c^k ≥ 0.5 × Σ_c n_c p_c^k (the expectation) |

**Median constraint [v2.5, E8].** The constraint is on the expectation only. The 1.645σ margin is dropped from feasibility: when bands are defined on the school's own enrolled class, the status quo sits at exactly 0.5 and would violate the margin, forcing the optimizer to buy position or return infeasible. The probability that the realized median holds is reported separately (from the binomial variance, σ_k = √(Σ n_c p_c(1 − p_c))) and is not a feasibility constraint. **[v2.7, V27-03]** The v2.5 statement that aid alone cannot raise Richmond's median held under the 5% guardrail and is withdrawn; whether aid can move the median is now answered by the grid evaluator and the screen re-run (O36). P(median holds) has the closed form 1 − Φ((−0.5 − m)/√V_m), with m = Σ g_c n_c p_c (g_c = +1 at or above the threshold, −1 below) and V_m = Σ n_c p_c (1 − p_c), validated against simulation within 0.01 on the Richmond scenario workbook.

**Whitelist [v2.5].**
- **Allowed:** market tier or CBSA, state, distance band, program, first-generation status, Pell eligibility, residency, student type, academic index or **position band**, need band, and **[v2.6] the consumer capacity tier** (derived from ZIP5; section 2).
- **Blocked:** race, ethnicity, gender, **[v2.6]** consumer-segment and lifestage codes, individual-level credit data (credit scores, bureau matches, tradelines; not planned), ZIP5 and ZIP3 as a dimension or target, any household-level field, and any geography finer than CBSA as a dimension or target. An enrollment target on the capacity tier needs alignment-gate acknowledgment and the proxy screen below.
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

**Tuition scenarios [v2.7, V27-11; replaces the v2.6 "to build" paragraph]:** tuition migration is a scenario lever (by year; default 6.0% for 2027 in reproduce mode; Richmond planning scenarios use 5.5%, unconfirmed, until Brandon supplies the figure **[V27A-06]**) in the evaluator below. It changes the net-tuition arithmetic only. Applications and yield do not respond to sticker price unless the analyst enters a pool multiplier or a yield shift. Mapping a sticker-price change to a change in net cost for the admitted pool is deferred (section 11). There is no sticker-price optimization.

**Outputs:**
- the recommended grid (or the documented status-quo grid in the weak-evidence state);
- a scholarship policy document;
- projected class, revenue, spend, and discount rate under each scenario;
- the evidence status;
- **[v2.7, V27-12]** the fine matrix (policy of record), the step-size table, the scenario ledger results, and a planning-assumptions block (admit rates, pool multiplier, tuition migration, class size) kept apart from aid policy.

**[v2.3]** Optional: the policy lookup file, delivered through the client's secure channel.

### Scenario evaluator (client-authored grids) [v2.7, V27-10; revised v2.8]

**Purpose.** Score a grid the client writes (award and admit rate by cell, pool multiplier, specialty and need dollars) and report class, `ntr_y1`, the entering-class discount rate and position measures with their uncertainty. It evaluates; it does not recommend, and it is available in every evidence state. The Excel workbook is the first deliverable; a dashboard is a later add-on reading the same outputs **[v2.8]**. Implementation detail: `Prototype_Spec_Scenario_Workbook_v0.6.md`. Metric names and definitions: Appendix F.

**Ledger.** For scenario s, cell c and case k in {L, M, H}:
- applications = base-cycle complete applications × pool multiplier (applied at or above the pool score threshold; Richmond LSAT 165) × an optional lift on the active priority segment's applications **[V27A-01; v2.8, B5-1]**;
- admits = applications × admit rate;
- award = lever award after tuition scaling (default fixed dollars; the full-tuition rung follows tuition) plus the incentive (aimed at the segment or at all out-of-state, with an optional score floor), capped at tuition;
- yield = response(award, k) + yield shift (global, with residency and segment overrides that replace it), clipped to a configured floor and cap. The base yield of each cell is partially pooled toward its segment or residency pool and re-centered at the latest award **[v2.8, B4-5, B1-15]**. Until an anchor exists the response is a client-input slope (placeholders 0.5, 1.0 and 1.5 points per $1,000 for L, M, H);
- enrolled = admits × yield; class = Σ enrolled;
- merit = Σ enrolled × award; need = need rate × class (a fixed amount per enrollee, the rate set by the client's need total over its reference class) plus any scenario departure from that total, taken as a fixed dollar amount that does not scale with class **[spec v0.6.3, R4-07; OD-16 open]**; `ntr_y1` = class × tuition − merit − need − specialty; `discount_entering_y1` = (merit + need + specialty) ÷ (class × tuition) **[v2.8, B3-1, B3-2]**.

Yield is held constant when admit rates change. A marginal-admit effect is not modeled (section 11). Ratios are ratios of expected values **[v2.8, B3-5]**.

**Single evaluator.** For any grid, the optimizer's class, first-year spend and `ntr_y1` equal the ledger's; the optimizer's objective `ntr_horizon` will equal the multi-year evaluation when it is built **[v2.8, B3-1]**. The workbook, the policy document and any later dashboard read ledger output and recompute nothing.

**Uncertainty (closed form).** Binomial enrollment by cell plus a multiplicative common year shock with standard deviation s (O37). With A = admits, y = yield, M = Σ A y and V = Σ A y (1 − y) + s² M²: P(class > cap) = 1 − Φ((cap + 0.5 − M)/√V). For NTR, with w_c = tuition − award − need rate: mean = Σ w A y − specialty; variance = Σ w² A y (1 − y) + s² (Σ w A y)². Median at threshold t: margin m = Σ g_c A_c y_c with g = +1 at or above t, −1 below and 0 for unscored cells (Appendix F); V_m = Σ_{g≠0} A y (1 − y) + s² (G₊² + G₋² − 2ρ G₊ G₋), where G₊ and G₋ are the expected counts above and below and ρ is the correlation between the year shocks of the two groups (default 1; a sensitivity line at 0.5) **[v2.8, B4-2]**. The segment probability is computed exactly in Python and by the normal form in Excel, flagged when fewer than 30 are expected **[v2.8, B1-8; spec v0.6.1, OP-3]**. Validated against simulation within 0.01 on the Richmond scenario workbook (v2.7 median rule).

**Levers.** Admit rate by cell; pool multiplier; award by cell; specialty and need dollars; tuition increase by year (6.0% for 2027 in reproduce mode; Richmond planning 5.5%, unconfirmed **[V27A-06]**); class target under a hard cap (140 this cycle), supported from 100 to 140, with a class-size table built on the shrink path (lowest score bands first; segment cells below the median threshold protected) **[V27A-02, V27A-03; v2.8, B1-16, B7-7]**; incentive with its scope and score floor and an optional segment application lift **[V27A-01]**; yield shift in percentage points (strip of −3 to +3, with linear break-evens). A **pool strip** shows expected class, P(class > cap), the median margin and P(median holds) across pool multipliers of 0.8 to 1.6, replacing the v2.7 tripwires **[v2.8, B7-4]**. Two lines state the net-tuition change at constant award when tuition rises, with awards fixed or scaled; they are arithmetic and change no yield **[v2.8, B7-5]**. Tuition changes NTR arithmetic only.

**Segment and incentive measures [v2.8, B2-4, B1-4, B1-11].** Segment enrolled with a 90% range and the probability of a goal; one incentive decomposition over the cells that receive it: incentive cost, the part paid to students the parent scenario already enrolled (cell by cell, so the tuition cap and score floor are respected), additional enrollees, and aid and NTR change per additional enrollee, valid only against a parent that differs by the incentive alone (checked by formula). Definitions in Appendix F. These are what the assumed response implies, not estimates of what an incentive causes **[v2.8, B4-8]**. The segment lift is segment application growth beyond the pool multiplier; once state-level pacing arrives, the reported figure is segment growth minus other out-of-state growth at the same week of the cycle, which removes a shared trend but is still not a causal estimate of recruiting or marketing.

**Deferred [v2.8, B7].** The goal-seek helper and the schedule authoring layer (year 2; FR-75); multi-year and trajectory views; the simulation sheet (simulation stays in tests).

**Labels [v2.8, B4-6, B4-9].** "Response based on client-input" on every output that depends on the placeholder slope, replaced by the evidence status once an anchored response exists; "Includes client-input assumptions (yield shift, application lift)" on any scenario with a non-zero shift or lift, in every evidence state; "Year-to-year variation assumed (s = …), not yet calibrated" beside every probability and range while s is illustrative, with probabilities beyond 5% and 95% shown as "under 5%" or "over 95%"; "Segment share assumed, not from client data" while the segment share is a placeholder. "Evidence too weak to change aid levels" applies to Frankel-recommended grids only.

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
- **[v2.7, V27-15; v2.8] Evaluator views.** Scenario results are shown as the L, M, H cases with closed-form probabilities, a yield-shift strip, a pool strip, a tuition what-if with the two net-tuition lines, a class-size table on the shrink path, and the segment and incentive blocks, each labeled per section 5.
- **[v2.8, B4-1] Year-level shock calibration (O37).** s is calibrated from public data, never from another client: for law, the year-over-year change in each school's ABA 509 yield (matriculants ÷ offers), detrended, with binomial noise removed, among schools of similar size; for undergraduate, the same from IPEDS admissions data. A client's own out-of-time forecast errors replace it only after five cycles, combined by inverse variance. One client's three to five cycles cannot estimate s (from three cycles the estimate ranges from 0 to about 0.18 when the true value is 0.10). Until calibration, s = 0.10 is illustrative and labeled.
- **[v2.8, B4-9] Range kinds.** Every range says which of three kinds it is: (1) a 90% outcome range (enrollment noise and year-level variation, at the Middle case); (2) the Low and High price-response cases (placeholder slopes until an anchor exists, then the 10th and 90th percentiles of the slope); (3) a 95% confidence interval for an estimated parameter. Kinds 1 and 2 are never combined into one range. The pipeline's class interval and the evaluator's use the same method once O37 closes.

## 7. Monitoring layer [to build]

- **Pacing:** complete applications, admits, deposits (gross), revenue and flexible spend against the same week of the cycle (counted from the application open date) in the prior two cycles and against plan **[v2.8, B3-4]**. Each pacing ratio is shown beside the share of the prior cycles' final applications that had arrived by the same week, so a shift in filing timing is visible **[v2.8, B4-4]**.
- **Projected census:** current counts by stage × historical stage-to-census conversion rates by days to deadline (a lookup table, not a new model), with an interval from binomial noise and the year-level shock s; prior-cycle spread is shown as a check, not used, until five cycles exist **[v2.8, B4-4]**.
- **Melt:** historical deposit-to-census rates by a few flags known at deposit (housing application, verification selected, unmet need above a threshold, FAFSA not received). Segment-level in the dashboard. Any student-level list goes back to the client through its secure channel, never the hosted dashboard.
- **Refresh:** weekly or biweekly client export during yield season.
- **Treatment log:** every mid-cycle award revision is recorded with date and reason code, so it can be separated from the price estimate the following year.
- **Batch scoring [v2.3; release criteria v2.5].** An optional add-on. Each batch returns, per student, the forecast probability of enrolling with its calibration band, and optionally the policy lookup award (the cell award). Inputs are decision-date information only; race, ethnicity, and gender are excluded. A score says who is likely to enroll, not who will respond to outreach or to an extra dollar. It may ship only when all of these hold:
  1. **Out-of-time calibration on at least one cohort:** the 90% confidence interval of the slope overlaps [0.85, 1.15] **[v2.8, B4-3]**; |intercept| ≤ 0.1 logit; deciles within ±3 points (UG) or inside the 90% binomial band (small programs).
  2. **Feature tests:** leakage and protected-attribute tests pass on the scoring feature set.
  3. **File contents:** only the client's key, score, band, model version, and score date. **[v2.6]** The file carries the score, not the capacity tier, unless the Claritas agreement (gate L1) permits returning derived tiers.
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
- **Credit data [v2.6, narrowed].** Individual-level consumer credit data (credit scores, bureau matches, tradelines) is **out of scope (not planned)**: it would require identified records, its permissible use for aid decisions is unclear, and it is a strong proxy for race. This rule does **not** apply to ZIP-level derived indexes, including P$YCLE. Those are neighborhood-level, are treated as non-credit data for the purposes of this specification, and are not blocked by it. How a regulator or a court would characterize them is a question for counsel, and whether Claritas's own inputs include bureau data is a license question (O28). Ability to pay comes from FAFSA, CSS Profile, observed borrowing, public Census tract indicators, and, where adopted, the capacity tier.
- **Equity audit:** grid cells use policy attributes only, but need band, geography, residency, and position can still act as proxies. The audit table compares status-quo and recommended policies by group (average award, expected yield, expected discount rate, share receiving an increase) and is reviewed with every recommendation. **[v2.5]** Equity tables from the v2 build must not be shown to clients; they are re-run under the lean model.
- **Client alignment gate [v2.2]:** before any client publication, the client's decision maker (VP or Director of Enrollment, or a Dean, plus others the client designates) reviews the allocation logic, the segment floors, the equity audit and the data use, and signs off **[v2.8, B2-6]**. Legal review is the client's choice. **[v2.6]** Where consumer data is used, the packet includes the purpose statement for acknowledgment. The packet includes a short legal-considerations note so the client can decide. **[v2.3]** The sign-off is a one-page approval. **[v2.5]** For a price test, the packet also discloses the design and the negotiation-interference risk.
- **Targeting and geography [v2.3; v2.5; v2.6]:**
  - Geography is a policy attribute, but it is also a strong proxy for race and income. Every geographic target or grid dimension is covered by the equity audit and the runtime proxy screen (section 5).
  - The rules for consumer data are in the next subsection. They replace the v2.3 release criteria for consumer segments.

### Small-cell disclosure [v2.7, V27-14]

- **Policy.** `small_cell_policy` is set per engagement. Default: suppress cells under 10 students with complementary suppression. Richmond: no suppression. Named, authenticated client roles (enrollment team, leadership, aid office) see all views, small cells included. Cat and Richmond staff have signed off (Jason Cohen, November 5, 2026).
- **What does not change.** No student-level rows, no student keys, no exact dates and no ZIP5 in Supabase or the hosted dashboard. Aggregates only.
- **Residual risk.** In a class of about 140, a cell of one or two students may be recognizable to people who know the class. The risk is accepted for the named roles. It is recorded in the SOW and the alignment-gate packet, with the date and scope of the sign-off and the roles that see small cells.
- **Any other client** keeps the default unless it elects otherwise in writing.
- **Files [v2.8, B2-3].** The Excel workbook and the policy lookup file follow the engagement's `small_cell_policy` and go only to the named roles through the secure channel; the cover note names the roles. Under the default policy, the workbook's count columns are suppressed as on the dashboard. (Cat to confirm.)
- **Policy document [v2.8, B2-3].** The scholarship policy document carries award amounts by cell, which describe policy, not students. Projected counts by cell appear in it only under the engagement's policy.
- **Public and marketing material [v2.8, B2-3].** Always the default rule (no cell under 10, complementary suppression), whatever the client elects. Client-specific material is never public.

### Consumer data: purpose, gates and guardrails [v2.6]

**Purpose statement** (recorded at the alignment gate): the capacity tier measures neighborhood-level capacity to pay and expected response to price. It is not a measure of, or a substitute for, race, ethnicity or any protected trait, and it is not constructed, adjusted or selected using race data.

**Construction rule.** The tier is never residualized, reweighted or tuned against race composition. Candidate definitions are pre-registered (P$YCLE index, PRIZM rank, free ACS income). If one fails P1, tiers merge or the method drops to the free baseline. It is not "corrected" with race data.

**Posture.** These tests are a record, not a legal safe harbor. Passing P1 does not establish compliance, and the reports are not thresholds. Legal responsibility stays with the client, and counsel reviews the license and the proxy note before the first use in an aid grid at any client (decided October 22).

**Gates by use**

| Use | Allowed when |
|---|---|
| Targeting and outreach | L1 (or fallback F1 or F2); G1 and P1; alignment gate. Outputs are tier-level or ZIP lists without segment labels |
| Forecast baseline (expected yield p\*, reference award r_c) | The above, plus G2 and G3. One price slope is unchanged |
| Aid grid dimension | The above, plus G4, floors, and the P2 to P4 reports shown at the alignment gate. Counsel review first, before first use at any client |
| Price-sensitivity moderator | Only through the moderator protocol and its three adoption gates (section 4). Not part of this amendment |

**Gates**

| Gate | Test | Threshold (proposed; the audit is to confirm) |
|---|---|---|
| G1 | Match rate on ZIP5 | At least 95% of students; unmatched are Unknown |
| G2 | Out-of-time AUC lift over the free ACS/IRS baseline, with bootstrap 90% lower bound | At least +0.01, and the lower bound above 0. **[v2.6]** The achievable power at the client's size is reported from the consumer worlds; failing to power the test is not a pass |
| G3 | Calibration and drift | Section 7 calibration criteria; tier-distribution PSI at most 0.2 |
| G4 | Grid backtest | The tier grid beats the no-tier grid and the best fair heuristic (section 10 margin) |
| **P1** | Cramér's V between tier and race and ethnicity (audit-only data), per cohort and pooled | **Below 0.3. P1 is the only proxy gate, and the only test that blocks a release** |

**Report-only: P2, P3 and P4 [v2.6].** These are computed by the equity audit and shown at the alignment gate. They never block a release, in any use, and the client decides with counsel. **P4 is report-only everywhere** (the draft amendment listed it as a requirement for targeting use; that was an inconsistency and is removed).

| Report | What it shows |
|---|---|
| P2 | Whether adding the tier raises how well race group can be predicted from the allowed attributes |
| P3 | Mean expected award and share of discretionary dollars by race group, tier policy against no-tier policy |
| P4 | Correlation of the ZIP index with ACS race composition (ZIP-level) |

**Audit-only data:** student-level race from the client, and ZIP-level race composition from the ACS. Neither enters any feature set. A static test enforces it.

**Other rules**
- **FAFSA and FERPA (O27):** the tier uses no FAFSA data, so prospect-stage use does not touch FAFSA data. SAI is used only to validate the tier on admitted students inside the aid-administration engagement. A counsel note covers HEA 483(a)(3)(E) and FERPA.
- **Segment disclosure:** no output pairs a ZIP with a segment. ZIP-level outputs aggregate at least 3 segments and at least 10 students.
- **Alignment gate:** where consumer data is used, the packet includes the purpose statement for acknowledgment and the P2 to P4 reports.

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


### Consumer bake-off [v2.6]

A pre-registered comparison per engagement, scored out of time on at least three cohorts.

| Variant | Content |
|---|---|
| A | Baseline without geography |
| B | A plus free ACS/IRS ZIP indicators |
| C | B plus the P$YCLE index |
| D | B plus the PRIZM index |
| E | C and D together |

**Outcomes:** enrollment AUC and calibration; agreement with SAI among admitted students who filed (validation only); P1 as the gate; P2 to P4 as reports. The winner must pass G2 against the free baseline B. If no licensed variant passes, variant B is used and the report says the licensed data did not earn its cost (O31).

**Law-size power note [v2.6].** At about 650 admits a year over three cohorts (roughly 2,000 admits and 400 enrollees), the standard error of an AUC difference may exceed 0.01, so G2 may be unreachable for a real signal. This is suspected, not tested. The consumer worlds (W21L) measure it. If G2 cannot be powered at law size, the tier stays out of the law grid and may still serve targeting where G1 and P1 pass.
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
| W12 | Staff offsetting. **[v2.5, E1]** Variant: a 0.10-logit test-status effect (staff treat test-cohort admits differently) | 100 | Compliance flag ≥ 80% when the offset ≥ 25% of the bonus. Variant: flagged, or the primary estimate's bias ≤ 10%, in ≥ 90% of seeds |
| W13 | Merit thresholds move between cohorts | 100 | Per-regime estimate; bias within the limit |
| W14 | Negotiation interference in the control arm | 100 | Reconsideration flag ≥ 70%; intent-to-treat bias reported |
| W15 | Retention depends on net cost; non-constant hazard | 100 | Year one unaffected; multi-year error documented |
| W16 to W18 | Confound strength −0.2, −0.6, +0.2 | 100 each | Anchor thresholds; confound diagnostic monotone in strength |
| W19 | Conditional awards (deferred) | 100 | When a client needs it |
| W20a/b | Additive / interaction worlds | 100 each | Section 11, boosted challenger |
| W21 Consumer (UG) **[v2.6]** | Latent household resources by ZIP; a noisy ZIP index with signal strength ρ ∈ {0.2, 0.5, 0.8}; ZIP race composition correlated with the latent at c ∈ {0, 0.4, 0.7} | 100 per cell of the ρ × c grid (9 cells) | At ρ = 0.2, G2 fails in ≥ 90% of seeds. At ρ = 0.8, G2 passes in ≥ 80%. P1 fires in ≥ 90% of seeds at c = 0.7, and the tier then never enters the grid (100%). Where the tier enters the grid, it beats the best fair heuristic by the margin in ≥ 90% of seeds. *Proposed; the audit is to confirm* |
| W22 Year shock **[v2.8, B4-1]** | A multiplicative year-level yield shock common to all cells, SD 0.05, 0.10 and 0.15, on the W0L pool; variant with correlation 0.5 between score groups | 100 per SD | W0L class-coverage gate holds when the evaluator's s matches the world's; coverage failure is reported when s is understated |
| W21L Consumer (law) **[v2.6]** | As W21, on the W0L pool (650 admits, 3 cohorts, tier count 2) | 100 per cell | Same checks, plus the **G2 power result at law size** (share of seeds in which a true signal at ρ = 0.5 passes G2), reported whether or not it is high. Used to apply the "no tier in the law grid" default |

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
| Floors (the per-cell guardrail was removed in v2.7) | Binding frequency reported | — |

The family-wise false-fail rate is about 2% to 3%.

**Run policy [v2.8, B7-13].** Each release runs W0, W0L, W22 and the worlds tied to live decisions (W5, W6, W8, W9, W10, W11). The other worlds run when the feature they test is in use (price test, consumer tier, conditional awards, boosted challenger).

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
| ~~Empirical prior pooled across clients [v2.5]~~ | **Removed [v2.8, B5-5]:** a prior built from other clients' estimates would mix one client's confidential information into another's work. Public sources only |
| Goal-seek helper and schedule authoring layer [v2.8, B7] | A client asking to aim admit rates at targets by solver, or to author awards by tier; now the shrink path, break-evens and manual cells |
| Multi-year evaluation (`ntr_horizon`, `discount_all`) and the five-year trajectory [v2.8] | Year 2 of an engagement; the renewal rule (OQ-02) |
| Dashboard scenario and policy views [v2.8] | After the workbook's core computation is accepted; an add-on reading the same ledger outputs |
| Conditional-award persistence modeling | A client that offers conditional scholarships |
| Grid-tier price estimation (all admits, smooth controls on GPA) [v2.3] | **Deferred to a future phase and not specified now** |
| Per-student optimization [v2.3] | Not planned; the policy lookup replaces it |
| Boosted-tree forecast challenger [v2.4; margin v2.5] | See below |
| Raw consumer-segment or lifestage codes in the aid grid or as model features [v2.3; v2.6] | Never |
| Individual-level consumer credit data [v2.6] | Not planned |
| Capacity tier as a price-sensitivity moderator [v2.6] | Only through the moderator protocol and its three adoption gates (section 4) |
| Net-price yield response [v2.7, V27-16] | A switch so yield responds to net price (tuition minus award). Needs evidence that applicants react to sticker price as they do to aid; offered only as a labeled bound |
| Geography below the single priority segment (per-state segments, MSAs, ZIP3) in the evaluator and grid [v2.7, V27A-01; v2.8] | Richmond's state-level counts and about two cycles of data; now one combined segment (Richmond NY, PA) plus one incentive |
| Admit-rate dimension in the optimizer [v2.7] | A marginal-admit yield estimate and a client request; now evaluator inputs and the shrink path (goal-seek deferred, v2.8) |
| Marginal-admit yield (yield changing with admit rate) [v2.7] | An estimate from admit-stage data; now held constant |
| Slate-based pool-growth pacing [v2.7] | Slate pacing extract; now a manual pool multiplier |
| USNWR planner feed [v2.7] | A possible future law-product feature |

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
- **[v2.6]** The capacity tier is a neighborhood-level (ecological) signal: it does not describe an individual household, and it can mislabel a student whose permanent address is a family address.
- **[v2.6]** The tier is a known proxy-prone attribute. Only P1 blocks a release; P2 to P4 are reports. The tests are a record, not a legal safe harbor.
- **[v2.6]** The thresholds G1 to G4 are proposals and are untested; G2 may be unreachable at law size (O35).
- **[v2.6]** Licensed data depends on the Claritas agreement (gate L1). Until it is signed, only synthetic and free-source data are used.
- **[v2.7, V27-17]** The evaluator's response is based on client-input until an anchor exists; its outputs describe the client's assumptions, not an estimate.
- **[v2.7]** No sticker-price demand effect: tuition changes net tuition arithmetic, not applications or yield, unless the analyst enters a pool multiplier or yield shift.
- **[v2.7]** Yield is held constant when admit rates change.
- **[v2.7]** The class-size what-if scales the expected mix proportionally; it is not a forecast of which students would fill a different class. The shrink-path table trims the lowest score bands first and is likewise a planning view **[V27A-03]**. Segment yield rests on the partially pooled out-of-state response, plus any client-input segment shift, until state-level data exist **[V27A-01; v2.8, B1-7]**.
- **[v2.8]** Year-level variation (s) is illustrative until calibrated from public data (O37); probabilities near the tails are shown as "under 5%" or "over 95%" until then.
- **[v2.8]** NTR and the discount rate in the evaluator are entering-class, first-year measures; multi-year measures wait for the multi-year evaluation.
- **[v2.7]** The closed forms assume independent enrollment across cells plus one common shock; they are checked against simulation, not proven.
- **[v2.7]** A client-authored fine matrix has no equity audit until the alignment gate runs one on the rendered matrix.

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
| F1 | One-sided choice rule tilts toward cuts | Two-sided rule (section 5); audit kept it (A8 to A10): binds for level cuts under weak evidence, inert where any reallocation gains |
| F2 | Law status quo not representable | Award mode, ladder, cap, horizon, law profile (section 5) |
| F3 | Screen rule power-based | Value-of-information screen (section 4); audit reproduced the worked example and stress-tested it (A1 to A7). Not recommended at ±3% under every pool, prior, target and bonus tested; the verdict is conditional on the capacity band (±10% gives Optional or Recommend); EVSI can be negative (E4); cost for capped programs includes induced enrollees (E6) |
| F4 | Test cost year-one only | Cost × M; no offset when capped |
| F5 | Estimand undefined | θ at status-quo awards; logit-unit pooling |
| F6 | Grid baseline undefined (O1) | Cell reference award r_c |
| F7 | Randomized-out eligibles unused | All-eligible analysis, primary only if staff are blind to test membership; otherwise test-only at dose 0 is primary (E1). The "+6% estimand bias" claim is withdrawn (A20); the gain is about 20% in logit units, not 34% (A21) |
| F8 | Scenario coverage coincidental | Recalibration, cell pooling, Monte Carlo disclosure |
| F9 | Backtest matches spend with truth | Model-set budgets in validation |
| F10 | Count noise ignored | Buffer |
| F11 | Monte Carlo gate miscalibrated | Section 10 |
| F12 | Sample-size assumptions | k = 0.92, eligible yield, scaled dose |
| F13 | 509 fields misread | Field rules (section 2); Appendix D. Audit confirmed all but two: conditional-scholarship lag is one year, not two (A16), and the nonresident-zero rule affects 4 of 111 private schools (A17). The illustration was regenerated (A18). The ABA definitions document itself was not read |
| F14 | Horizon mismatch in v2 build | Horizon = commitment; config validation |
| F15 | Conversion test tautological | Replaced |
| F16 | Wave slopes not estimable | Descriptive; four conditions |
| F17 | Equity audit stale | Blocked from client use until re-run |
| F18 | Negotiation interference | W14; compliance diagnostics; disclosure. Audit: the all-eligible estimate is fragile to a test-status effect (±0.10 logit gives about ±20% bias) that the yield-contrast compliance check cannot detect (A22); remedy is blinding plus process contrasts, and the W12 variant (E1) |
| F19 | "Four cohorts" error | Corrected: 1,917 test students over three cohorts (2023 to 2025) |
| F20 | Guardrail scale | 5% of tuition. **Superseded [v2.7, V27-01]:** guardrail removed; step-size table instead |

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
| In-state, out-of-state, international, **[v2.5]** and every market tier, including target markets, **[v2.6]** and every consumer capacity-tier cell | 75% each (the highest-need and Pell-eligible segment stays at 100%) | Guards against estimation-error cuts, which are worst in thin target markets (rejects the v2.4 exemption proposed in O14) |
| Transfer (where it is its own grid) | 75% | Small samples |
| First-generation | Client option (confirmed); 100% if mission-driven | Correlates with protected attributes, so the client decides |

**Not used for floors:** academic index or position (the merit grid and the median constraint protect them), region, source channel, and race, ethnicity, or gender (never).

**Rules.**
- Segments under 30 admits are pooled with the nearest segment.
- A floor may relax to 50% only where the randomized arm shows the segment is materially less sensitive and the client approves at the alignment gate.
- Every run reports which floors bind and their shadow prices.
- **[v2.7, V27-19]** The per-cell guardrail is removed (it stayed in v2.5 and v2.6). Floors apply to segment averages of the rendered fine matrix, weighted by projected admits.
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
- **[v2.5, E10]** Peers with conditional-scholarship prevalence above 10% are flagged "entering awards understated".

**Validation (synthetic law world).** Twelve peers built from 509-calibrated parameters. Student grants follow g = F⁻¹(Φ(ρ × z_index + √(1 − ρ²) × ε)) for ρ ∈ {0.9, 0.7, 0.5}, with matriculant selection on grant and position. Aggregates are published as the 509 does.

**Pass criteria:**
- per-band |bias| ≤ 5% of tuition, and Spearman ≥ 0.8 across bands, at ρ = 0.9 and 0.7;
- document the failure at ρ = 0.5 and the matriculant-selection bias.

*Illustration (2025 reports) [v2.5, E11]:* an applicant at Richmond's 75th position (LSAT 167, UGPA 3.92) sits at position 0.71 at Wake Forest. Applying the rules above gives about $47,100 there, against $55,550 at Richmond (full tuition, since 0.75 ≥ 1 − 0.276), a gap of about $8,450. The values come from the audit's computation of this procedure. **[to build]** Regenerate them from the implemented function, with a unit test for the full-tuition branch (u ≥ 1 − f gives tuition) and for the tail extrapolation.


## Appendix E. Consumer ZIP module [v2.6]

### E.1 License gate and fallbacks

The Claritas Information Services Agreement as posted (July 23, 2024) was read by the author of the amendment. Your contract may supersede it, and the posted terms conflict with Frankel licensing and appending the data. **The conflicts below are a build blocker for licensed data, not for the module.**

| Clause (posted terms) | What it says | Implication |
|---|---|---|
| 4, License grant | Internal use "in support of Licensee's marketing and promotional purposes." A third-party processor needs a Third Party Processor Agreement (TPPA). The consultant exemption excludes a consultant "acting on behalf of multiple clients" | Aid allocation is not marketing, and Frankel serves multiple clients |
| 6(c) | No use "to develop any application or service for list enhancement or data appending" | Appending as a service may be barred |
| 6(b) | No distributing or sublicensing Licensed Materials "or derivatives" to third parties without written consent | Returning tiers, scored files or policy grids that embed derived values needs consent |
| 5, Output | Aggregated output may be shared only to market the licensee's own business | Client deliverables are not covered |
| 6(d) | No use for eligibility for employment, credit, healthcare, charity care or insurance; no use that "could result in disparate impact or treatment against any group"; no use "to assess consumer financial risk" | The disparate-impact and financial-risk language is broad, and P$YCLE is a financial product; needs an explicit written carve-out |
| Segmentation terms | No one-for-one ZIP-to-segment cross-reference or disclosure "unless aggregated to include not less than 3 segments." Exports only as appended to consumer records under a Directory license | Use ZIP distributions of at least 3 segments, never a ZIP's single dominant segment, and never output ZIP-to-segment pairs. A Directory license may be needed |

**Gate L1 (before any build that ingests licensed data):** a written agreement with Claritas that expressly permits:
- (a) use for client enrollment and aid analytics;
- (b) appending to client student records by Frankel;
- (c) return of derived capacity tiers and scores to clients;
- (d) use in aid-allocation policy, with the disparate-impact and financial-risk language addressed;
- (e) retention for the engagement plus archival.

**Fallbacks if L1 fails or is slow**
- **F1. Client-licensed.** The client licenses Claritas and runs the append. Frankel signs a TPPA. We receive derived fields and never ZIP5.
- **F2. Free-data tier.** ACS, IRS SOI and Scorecard indicators at ZIP or ZCTA level. The module is source-agnostic, so the same gates and grid logic apply.
- **F3. Another vendor.** Experian Mosaic or similar, subject to its own terms. Not reviewed.

**Sequencing (decided October 22).** Build the pipeline first, on synthetic data and the free source. The Claritas agreement (L1) and the documentation request (O28: asset-indicator inputs, whether race or ethnicity is used, vintage and refresh cadence) wait for a firm client contract. Licensed-data ingestion stays switched off until L1 is signed. Counsel review of the license and the proxy note runs before first grid use.

### E.2 Technical build

**New module `pipeline/consumer.py`**
- `load_zip_table(source, vintage)`: license-agnostic interface. A source is Claritas direct, client-supplied derived fields, or the free ACS/IRS table.
- `zip_index(distribution)`: the section 2 formula. It refuses a ZIP with fewer than 3 segments.
- `fit_tiers(admit_pool, n_tiers)` and `assign_tier(zip_index, cut_points)`: cut points frozen and versioned.
- `match_report()`: match rate, Unknown share, and row counts, as an explicit QA rule.
- `proxy_audit()`: P1 to P4, writing to the equity audit.

**Config:** `config/consumer_zip.yaml`: product, vintage, tier count (2 or 3), thresholds for G1 to G4 and P1, merge rules, the pre-registered cut-point candidates.

**Schema**
- `zip_key(student_key, zip5, address_type)`: restricted access, append job only, deletion log.
- `student_consumer(student_key, zip_index, zip_top_quintile_share, tier, match_flag, vintage)`: no ZIP5.
- `consumer_gate_status(engagement, use, gate, value, passed, date)`.

**Guardrail tests (extend `test_guardrails.py`)**
- ZIP5 and segment codes are absent from every analysis and output table.
- The tier-construction function takes no race, ethnicity or gender argument.
- The tier is rejected as a grid dimension unless `consumer_gate_status` shows every required gate passed.
- Raw segment codes are rejected as model features.
- No output pairs a ZIP with a segment; ZIP-level outputs aggregate at least 3 segments and at least 10 students.
- **[v2.6]** P4 never appears as a pass or fail field in `consumer_gate_status`; only P1 does.

**Dashboard and delivery.** Tier-level aggregates only. No ZIP5 maps and no segment labels.

### E.3 Data request language (use when the law Tier 1 request is written)

**New file (Tier 1 optional add-on):**

| File | One row per | Fields |
|---|---|---|
| `zip_key` | Person | Hashed student key (same as other files); `zip5` (permanent address at application); `address_type` (permanent or current); blank if unknown |

**Replace in "How to send data safely"**
- "No full ZIP codes" becomes: "No street addresses. ZIP5 is sent only in the separate `zip_key` file."
- "Send ZIP3 and state, not full ZIP" becomes: "`students` keeps state and ZIP3. ZIP5 goes in `zip_key`, through your secure channel."

**Add to "What we do with the data"**
- ZIP5 is used only to attach neighborhood-level indices from a third-party dataset. We then replace it with derived fields and delete `zip_key` within 30 days of append QA, or at engagement close.
- Indices are neighborhood-level. We do not receive or use household-level data or street addresses.
- Race, ethnicity and gender are never used to build or adjust these indices.
- A match report is returned to you.

**Add to the checklist**
- [ ] Optional: `zip_key` (ZIP5), with written approval of the transfer under your data-use agreement.
- [ ] Confirm which address field is the permanent address at application.
- [ ] Signed acknowledgment of the consumer-data purpose statement (alignment gate).

**Add to `data_dictionary_v2.csv`:** `zip_key.student_key`, `zip_key.zip5`, `zip_key.address_type` (all text; `zip5` required only when the add-on is elected). Update the `students.region_code` note: "ZIP3 retained; ZIP5 only in zip_key."

The credit-data statement is **not** repeated in the data request or the pitch. See section 9 (credit data, narrowed).
## 13. Open issues: status after the S4 and S5 re-review [v2.5] and the consumer amendment [v2.6]

All issues were ruled on in `S4_S5_Rereview_v2.4.md`. "Applied" means the text above reflects the ruling. The scoped audit is complete (`Audit_S4_S5_Rereview_v2.4.md`); its rulings are in the closed items below.

| ID | Issue | Ruling | Where applied |
|----|-------|--------|---------------|
| O1 | Forecast baseline | Changed: cell reference award r_c; forecast has no aid fields | Section 4, Response model |
| O2 | Weak evidence | Changed: two-sided rule; automatic weak-evidence state. Audit: rule kept | Section 5 |
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
| O13 | Consumer segments | **Rewritten [v2.6].** ZIP5-derived fields allowed for targeting, the forecast baseline and gated grid use. Raw codes blocked. Gates in section 9 | Sections 2, 5, 9; Appendix E |
| O14 | Market tier and targets | Changed: cell rule; floors apply to all tiers; infeasibility reporting | Section 5; Appendix C |
| O15 | Scoring governance | Confirmed with release criteria | Section 7 |
| O16 | 509 definitions | Confirmed, with the lag corrected to one year (audit) | Section 2; Appendix D |
| O17 | Horizon and conditional awards | Changed: horizon = commitment; conditional modeling deferred | Section 5 |
| O18 | Wave timing | Changed: descriptive; four conditions | Section 4, Timing |
| O19 | Boosted challenger margin | Set | Section 11 |
| O20 | License scope for Frankel as licensee | Gate L1 and fallbacks F1 to F3. **Needs Claritas** (deferred to a firm client contract) | Appendix E.1 |
| O21 | P$YCLE or PRIZM | P$YCLE for capacity, PRIZM optional for outreach; per-engagement bake-off including the free baseline; one licensed product per engagement | Sections 2, 10 |
| O22 | ZIP5 re-identification risk | ZIP5 travels in a separate `zip_key` file, is used only by the append job, is never in analysis tables, and is deleted after append QA or at close. ZIP3 and state are retained. No street address, no names | Section 2; Appendix E |
| O23 | Tier construction | A deterministic published formula on the ZIP distribution. No trained model, no segment codes | Section 2 |
| O24 | Grid cell cap | The tier enters by split, substitution or addition, chosen by backtest. Law default: two tiers, tier replaces market | Section 5 |
| O25 | Law applicability | Same rules, own lift and proxy tests, address-definition rule, cell-cap consequences | Sections 2, 5 |
| O26 | Proxy-test thresholds | **P1 is the only gate; P2 to P4 are report-only everywhere** (October 22) | Section 9 |
| O27 | FAFSA data use (HEA 483(a)(3)(E)) and FERPA | The tier uses no FAFSA data. SAI only validates the tier on admitted students. Counsel note | Section 9 |
| O28 | Claritas inputs documentation | Request documentation of asset-indicator inputs (including whether race or ethnicity is used), vintage and refresh cadence. **Needs Claritas** (deferred with L1) | Appendix E.1 |
| O29 | ZIP versus ZCTA | Use the HUD USPS crosswalk for the free baseline and the race-composition audit | Section 2 |
| O30 | Vintage drift | One vintage per cycle; score all cohorts with it; test sensitivity to two vintages | Section 2 |
| O31 | Cost versus lift | Licensed data must beat the free baseline (G2), or it is not used | Section 10 |
| O32 | **P4 inconsistency in the draft amendment** | **Resolved [v2.6]:** P4 is report-only in every use, and the targeting row no longer requires it | Section 9 |
| O33 | **Credit-data rule** | **Narrowed [v2.6]:** individual-level credit data (scores, bureau matches, tradelines) is out of scope (not planned); ZIP-level derived indexes, including P$YCLE, are not blocked by it. Whether Claritas's inputs include bureau data is a license and counsel question (O28) | Section 9 |
| O34 | **Tier count under the law cell cap** | **Resolved [v2.6]:** two tiers by default for law, fixed per program, with the tier replacing market. A per-admit choice of which tiers apply is rejected (not documentable; breaks the policy lookup and the equity audit; moves toward per-student optimization). Unknown pools with the larger tier | Sections 2, 5 |
| O35 | **G2 power at law size** | **Open, to be tested [v2.6]:** G2 may be unreachable at law size even for a real signal. Measured in W21L; failing to power the test is not a pass; default is no tier in the law grid until shown otherwise | Sections 9, 10 |
| O36 | **Screen re-run without the guardrail** | **Open [v2.7, V27-05]:** re-run the value-of-information screen on stylized pools and the production optimizer (509-calibrated pool), median floor, at ±3%, ±5%, ±10%. Earlier verdicts are not to be quoted | Section 4 |
| O37 | **Common-shock calibration** | **Open [v2.7; plan v2.8, B4-1]:** s = 0.10 is illustrative; calibrate from public 509 (law) and IPEDS (undergraduate) yield histories; client forecast errors after five cycles; test in W22 | Sections 5, 6, 10 |
| O38 | **Evaluator slopes versus the anchor** | **Open [v2.7]:** placeholder slopes 0.5, 1.0, 1.5 per $1,000 are client-input; replace by b_L, b_M, b_H when an anchor exists and say which is in use | Section 5 |
| O39 | **Discontinuity evidence after the freeze is dropped** | **Open [v2.7]:** a threshold that moves each cycle may not meet the two-cohort stability criterion; track in the evidence audit | Sections 4, 5 |
| O41 | **Median basis for unscored students** | **Closed Nov 18 (spec v0.6.3):** the ABA 509 excludes unscored students from LSAT percentiles, and the fixture does the same. Earlier text: **Open [v2.8, B3-3]:** default excludes unscored and blank-GPA enrollees from the margins (as the ABA 509 is understood to); confirm against the 509 instructions | Section 5; Appendix F |
| O42 | **Which discount rate the client means** | **Open [v2.8, B3-2]:** Richmond's "maintain the discount rate" may mean the entering-class or the all-JD rate, with or without fees; ask Brandon; until then the evaluator labels its rate "entering class, first year" | Section 5; Appendix F |
| O43 | **Small-cell rule for files and public material** | **Open [v2.8, B2-3]:** Cat to confirm the rule in section 9 | Section 9 |
| O40 | **Small-cell disclosure record** | **Open [v2.7]:** record the date, scope and roles of Cat's and Richmond staff's sign-off in the SOW and the alignment-gate packet | Section 9 |

**Items opened for the audit: all closed [v2.5].** These IDs are the audit's task numbers; the audit's findings are numbered A1 to A33 in its own table, so cite them as "audit Task n" or "audit A<n>" to avoid confusion.
- **A1. Closed.** **[v2.8, B2-2: verdict computed under the 5% guardrail; pending re-run (O36); do not quote]** Value-of-information verdict for Richmond: the table reproduces. Not recommended at ±3% under every pool, prior, target, rule and bonus type tested. Not robust to the class band: at ±10% a five-band pool gives Optional or Recommend. EVSI can be negative. The median-target claim is overturned. Cost for capped programs is understated by 19% unless induced enrollees are included. Edits E3 to E7.
- **A2. Closed.** Conservatism of the two-sided rule: kept. It is not inert in general and not biased toward the status quo beyond what the pool dictates. Posterior expected value and minimax regret were rejected. Edit E3.
- **A3. Closed.** ABA 509 field definitions: confirmed from the form and the data, except the conditional-scholarship lag (one year) and the scope of the nonresident-zero rule (4 of 111). The ABA definitions document itself was not read. Edits E10, E11.
- **A4. Closed, with corrections.** Estimand and pooling: logit-unit pooling holds under the one-slope model. No "+6% bias" exists once the AME is evaluated at status-quo awards, and the all-eligible precision gain is about 20%, not 34%. The all-eligible analysis is fragile to staff test-status effects. The conversion test is under-powered at 5%. Edits E1, E2, E12, E13.
- **A5. Closed, with corrections.** Richmond baselines, sample-size table, false-fail rates and cost per test student confirmed. Buffer is about 15%, not 12% (E9). The median constraint with a 1.645σ margin cannot be implemented (E8). The per-wave MDE is test-only (E14).

## 14. Closed decisions [v2.4; v2.6]

| Decision | Outcome | Rationale |
|----------|---------|-----------|
| Collecting applicant-reported decision-timing data from a third-party law admissions site | **Closed: not used** | Considered as a weekly collection of response-timing data, to track timing by date. The site's license excludes institutional and commercial use and prohibits scraping or bulk collection without written permission. The data are self-reported, skew toward engaged applicants, and are coarse (the share of applicants who heard back, by application period). They measure how fast schools respond, not how applicants respond to price, and they do not link to a client's students. Timing sensitivity is learned from the client's own offer waves, and public applicant-volume reports describe market pace. Revisit only if the owner offers a license on terms that fit. |
| Consumer ZIP data (Oct 22, D1 to D5) | **Adopted [v2.6]** | ZIP5 consumer data is unblocked for derived fields only (never street address, never household). Frankel licenses and runs the append. A derived capacity tier may enter the grid under gates; raw segment codes stay blocked. Law follows the same rules as undergraduate. Racial and demographic guardrails are unchanged. ZIP5 itself is never a grid dimension, target or dashboard field |
| Retained geography (Oct 22) | **ZIP5 append, ZIP3 stored** | ZIP5 is transient (append job only, deleted within 30 days of append QA). Retained: state, ZIP3, ZIP index, tier, match flag, vintage |
| Proxy gating (Oct 22) | **P1 only** | P1 (Cramér's V below 0.3) is the only blocking proxy gate. P2 to P4 are report-only everywhere and are assessed with counsel |
| Credit-data rule (Oct 22) | **Narrowed** | ZIP-level derived indexes are not blocked. Individual-level credit data stays out of scope (not planned) |
| Build before license (Oct 22) | **Pipeline first; L1 waits for a firm client contract** | Licensed data is not loaded until L1 is signed. Counsel review of the license and proxy note precedes first grid use |
| Per-cell guardrail (Nov 5, 2026) | **Removed [v2.7, V27-18]** | The Richmond scenario workbook moves awards past it as ordinary levers; it would have flagged 2 to 10 cells in each scenario. Segment floors stay. A step-size table replaces the flag |
| Threshold freeze (Nov 5, 2026) | **Dropped for client-declared bands [v2.7]** | The client sets its bands; changes are logged at cycle boundaries |
| Policy of record (Nov 5, 2026) | **The client's fine matrix [v2.7]** | The optimizer works on a decision layer of at most floor(admits ÷ 30) parameters; the fine matrix is rendered by rule |
| Small cells (Nov 5, 2026) | **Per-client policy; none for Richmond's named roles [v2.7]** | Cleared by Cat and Richmond staff; recorded in the SOW and the alignment-gate packet |
| Geography in the evaluator (Nov 5, revised Nov 13, 2026) | **One combined target tier plus one incentive [v2.7, V27A-01]; generalized to a priority segment (Nov 16) [v2.8, B5-1]** | Dean Rooksby's priority is NY and PA; keep it low-dimensional; per-state tiers after state-level data |
| Class size and cap (Nov 13, 2026) | **100 to 140 supported; 140 is a hard cap this cycle [V27A-02]** | Five-year path toward 100 to 115; Brandon to confirm |
| Net-price readouts (Nov 13, 2026) | **Display-only arithmetic [V27A-05]; reduced to two lines (Nov 16) [v2.8, B7-5]** | The yield response itself stays deferred |
| Session B audit (Nov 16, 2026) | **Accepted in full [v2.8]** | Fixes, definitions (Appendix F), recommendations and three simplifications; see `DECISIONS.md` |
| Deliverable order (Nov 16, 2026) | **Workbook first; dashboard as an add-on [v2.8]** | Core computation proven in Excel before a second rendering |
| Priority segment (Nov 16, 2026) | **General segment in place of target-state tier names [v2.8, B5-1]** | Same construct for Richmond; other clients' priorities need no new code |
| Cross-client prior (Nov 16, 2026) | **Removed [v2.8, B5-5]** | Frankel does not mix one client's confidential information into another's work |
| Net-price yield response (Nov 5, 2026) | **Deferred [v2.7]** | No evidence yet that sticker price moves yield as aid does |
| Scenario evaluator in every evidence state (Nov 5, 2026) | **Adopted [v2.7]** | It evaluates client scenarios with a response based on client-input and recommends nothing |


## Appendix F. Metric definitions [v2.8, B3]

One line per metric. The workbook README, the policy document and any dashboard cite these names. Ratios are ratios of expected values.

1. **Application:** a complete and actionable application (CDS and ABA 509 basis); pacing counts the same, cumulative to the week of the cycle.
2. **Admit:** an offer of admission, including from the waiting list, counted in the cohort applied to.
3. **Admit rate:** admits ÷ applications, by cell and cohort.
4. **Enrolled (class):** first-year entrants enrolled at the census date, full-time and part-time as on the 509, excluding transfers; equals 509 matriculants (law) or CDS C1 first-time first-year enrolled (undergraduate).
5. **Yield:** enrolled at census in the cohort ÷ admits of the cohort; an admit who defers counts as a non-enrollee in the year applied and is reported separately (confirm against how the client's 509 yield is computed).
6. **Deposit (gross):** first enrollment deposits received; **deposit (net):** deposits not withdrawn by census; **melt:** 1 − enrolled ÷ gross deposits.
7. **Class cap / class target:** a hard upper bound / the planned class, both on the enrolled population above.
8. **Score and GPA percentiles:** as on the 509 for law (highest LSAT; LSAC UGPA; over matriculants with that measure); unscored matriculants are counted separately (O41).
9. **Median margin at t:** enrolled with a score at or above t minus enrolled with a score below t; **P(median holds)** = P(margin ≥ 0).
10. **Share at or above t:** expected enrolled at or above t ÷ expected enrolled with a score.
11. **Gross tuition (`gross_y1`):** enrolled × published first-year tuition; fees excluded and reported separately.
12. **Merit, need, specialty spend:** institutional gift aid to the entering class in its first year; need is a fixed rate per enrollee in the evaluator.
13. **`discount_entering_y1`:** (merit + need + specialty) ÷ `gross_y1`. Differs from NACUBO (which includes fees) and from **`discount_all`** (all enrolled students, multi-year evaluation; year 2).
14. **`ntr_y1`:** `gross_y1` − merit − need − specialty, entering class, first year.
15. **`ntr_horizon`:** entering-class NTR over the award commitment (three years for JD; as elected for undergraduate), with persistence and the recorded renewal rule; the optimizer's objective.
16. **Net tuition after merit award:** published tuition − merit award, by award; not IPEDS net price and not "net cost" (section 3).
17. **Residency and segment:** from the permanent address at application; a segment is a client-listed set of cells within one residency (Richmond: NY and PA within out-of-state).
18. **Segment enrolled (`E_S`):** expected enrolled in segment cells; P(`E_S` ≥ goal) with the goal rounded up.
19. **Incentive cost:** Σ enrolled × (award after incentive and cap − award before incentive).
20. **Aid per additional enrollee:** change in merit dollars ÷ change in expected enrolled, over the cells receiving the incentive, against a parent that differs only by the incentive.
21. **Paid-anyway share:** Σ min(parent enrolled, scenario enrolled) × incentive per enrollee ÷ incentive cost, over the cells receiving the incentive.
22. **Pool multiplier:** final complete applications at or above the pool score threshold ÷ the same in the base cycle; **pool growth to date:** the same ratio at the same week of the cycle against the same week of the prior cycle (spec v0.6.3, 0A item A6; Brandon, Nov 17).
23. **Market award gap:** Appendix D rank-matched peer grant share minus own share, median across the approved peer set, in shares of current tuition. Public peers: normalize by nonresident tuition for out-of-state positions and resident tuition otherwise, and flag the peer **[v2.8, B3-11]**.
24. **Evidence share:** expected enrolled in cells whose award lies outside the observed range ÷ expected class.
25. **Step size:** award difference between adjacent score bands within residency × segment × GPA class (segment and non-segment cells can carry different awards).
26. **Score percentile at or above t [spec v0.6.3, BM-1]:** at most a share q of scored enrollees (excluding unscored, as for the median and as the ABA 509 does; O41 closed Nov 18) score below t; the median is q = 0.5. The event is inclusive: it holds when exactly a share q is below t. The ABA averages the two middle scores, so near a tie the probability can read a few points high (about 4 points at most on synthetic data) **[R4-08]**. **Margin:** `q × N_scored − G₋`, the number of below-t enrollees that could replace enrollees at or above t at the same class size. The 10th percentile is a client measure, not an ABA 509 figure.
