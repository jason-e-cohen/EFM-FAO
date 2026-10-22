# EFA + FAO v2: Methodology

## 1. Scope

Two linked products share one data model.

- **EFA (enrollment funnel analysis):** where do prospects drop out, and what predicts movement through inquiry, application, admit, deposit, and enrollment?
- **FAO (financial aid optimization):** given the admitted pool, a budget, and goals, how should discretionary institutional aid be allocated?

## 2. Funnel analysis

**Stages:** inquiry, application, admit, deposit, enrolled at census. Stealth applicants (application is the first touch) skip the inquiry stage and are flagged, not dropped.

**Descriptive layer:** pre-aggregated cells for every single dimension by cohort and every pair of dimensions pooled across cohorts, with rates, minimum cell size 10, and complementary suppression.

**Driver layer:**
- Inquiry to application: logit with clustered standard errors on non-stealth inquiries. Reported as average marginal effects in percentage points, each with a confidence interval.
- Admit to enroll: effects of non-price attributes from the forecasting model, bootstrap intervals, labeled **associational**.

**Changes from the legacy build:** average marginal effects instead of effects at the means; explicit unknown categories instead of zero fill; one definition of "enrolled" (census); source taxonomy applied by versioned rules with an unmapped-source queue.

## 3. Aid data model

Aid arrives in long form: one row per student, fund, and package version, with offered, accepted, and disbursed amounts and dates.

| Class | Components | Used in price models |
|-------|-----------|----------------------|
| Institutional gift | merit, need, athletic, discretionary, other | Yes, if offered by the decision date |
| Other gift | state, Pell, SEOG, external | Yes, if known at the decision date |
| Self-help | subsidized, unsubsidized, Parent PLUS, work-study | Loans enter only as a debt-burden control; never as price reduction |
| Post-decision fields | accepted, disbursed | **Never** (leakage) |

**Net cost** = cost of attendance minus gift aid known at the decision date. **Institutional net tuition** = tuition and fees minus institutional gift aid. Need index is EFC through 2023-24 and SAI from 2024-25, labeled by type; "No FAFSA" is a separate category.

## 4. The price-response problem

Aid is not random. Staff give more discretionary aid where they see weaker interest, so a plain regression can show that more aid goes with lower yield. In the synthetic world, the correlation between discretionary aid and unobserved interest is -0.41, which reproduces the legacy puzzle.

### Evidence sources

1. **Randomized bonus-aid arm.** A random share of eligible admits receive an extra $0 to $4,000 of discretionary aid. Positive-only offsets avoid taking anything away. Unbiased, but noisy at small-college sample sizes.
2. **Merit-grid regression discontinuity.** Awards jump at published GPA thresholds. Local linear fits within a 0.12 GPA window estimate the enrollment jump divided by the award jump. Unbiased locally, noisy, and limited to students near thresholds.
3. **Controlled observational model.** Rich controls, heterogeneous price terms. Precise, but biased where unobserved fit drives targeting.

### Estimator

1. Pool (1) and (2) by inverse variance into an **anchor** for the average effect per $1,000.
2. Take the relative sensitivity pattern from (3). Shrink toward uniform with weight kappa, estimated from the reliability of the segment-level price terms (0.72 in the main run).
3. Scale the pattern with a single factor so the population average equals the anchor, refitting the other coefficients each time so the model stays calibrated.
4. **Hybrid:** forecast with the observational model at the status quo award; change aid using only the anchored slopes.

   `p(d) = expit( logit p_obs(current award) + s_eff * (d - current award) )`

This keeps forecast accuracy (AUC 0.833, mean prediction 0.211 against 0.202 actual) while keeping confounded price terms out of what-if answers.

### Power

With 1,917 test students over four cohorts the standard error is 0.56 points per $1,000. Detecting an effect with 80% power needs roughly 2.8 times the standard error, about 1.6 points. Halving the standard error needs four times the sample. The data request therefore asks for a test share of at least 40% of eligible admits, an offset range of $0 to $4,000, and a commitment to repeat it.

## 5. Optimization

**Decision:** discretionary award for each admitted student, on a $1,000 grid from $0 to $12,000.

**Expected value per choice:** `P(enroll | award) x (tuition - institutional aid) x persistence`. Persistence is the sum over four years of a retention-model survival factor.

**Constraints**
- Expected discretionary spend at most the budget. Aid is paid only if the student enrolls, so spend is probability-weighted.
- Optional expected class size floor.
- Institutional aid at most 75% of tuition per student (configurable).
- No student's award falls by more than $3,000 versus the current award (configurable).
- Athletes keep current packages.

**Solver:** multiple-choice knapsack as a mixed-integer program (HiGHS). About 25,000 binary variables solve in under a second.

**Scenarios shipped:** budget at 0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x, unconstrained NTR, headcount-maximizing at 1x, and NTR with a class-size floor.

## 6. Uncertainty and honesty

- **Bootstrap:** 40 resamples of the full pipeline (observational fit, anchor, scaling). Each allocation is evaluated under every draw to produce bands and the probability of beating the status quo.
- **Realization ratio:** in the backtest the model predicted +$2.44M for the recommended allocation and the truth delivered +$0.42M (ratio 0.17). Optimization exploits model errors. Each scenario therefore shows a **planning estimate** equal to the raw model gain times the ratio. On real data the ratio is estimated from the price-test arm and out-of-time backtests.
- **Known limitation:** bands are right-skewed because some bootstrap draws imply very high price sensitivity when the experiment is weak. Fix in the technical spec: bound the scaling factor and use an informative prior.

## 7. Equity and legal guardrails

- Race, ethnicity, and gender are **never** model inputs for allocation. A test enforces it.
- The audit table compares status quo and recommended allocations by group: average award, expected yield, expected discount rate, and share receiving an increase.
- Counsel review is required before using any recommendation, especially in jurisdictions with restrictions on race-conscious practices.
- Constraints defined on protected groups would themselves use those attributes, so guardrails are defined on awards and policy segments instead.

## 8. Validation plan

| Layer | Synthetic (truth known) | Real clients |
|-------|-------------------------|--------------|
| Recovery of price effect | Compare to the true effect | Compare estimators to each other; heterogeneity z-test between experiment and discontinuity |
| Forecast accuracy | Holdout AUC, Brier, calibration | Out-of-time holdout by cohort |
| Allocation value | Score against truth at equal true spend | Policy evaluation on the randomized arm; out-of-time backtests |
| Leakage | Check disbursed-aid flag by outcome | Same, plus automated field-timing checks |
| Disclosure | Tests on all outputs | Same, plus manual review before publish |

## 9. Known limitations

- Price response is logistic in net cost by construction; real behavior may show kinks at round numbers or thresholds.
- Retention is treated as a constant hazard for the four-year factor.
- Melt between deposit and census is absorbed into the enrollment outcome.
- No cost-to-serve model; the objective is net tuition revenue, not contribution margin.
- Competitor offers and yield from admitted students who never filed a FAFSA are unobserved.
