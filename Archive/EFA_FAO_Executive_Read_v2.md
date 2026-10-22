# EFA + FAO v2: Executive Read (revised after independent review)

**Prepared for:** Jason Cohen, Director of Research + Insights
**Status:** Methodology reviewed independently (Opus, four phases). Review edits accepted. Spec phase next. No further code until the spec steps in the companion roadmap are complete.
**Supersedes:** `EFA_FAO_Executive_Read.md`.

## Bottom line

Build the product. The foundation is sound and worth keeping: the data model, the leakage controls, the aggregates-only privacy architecture, the optimizer formulation, and the principle of anchoring price sensitivity in design-based evidence.

The recommendation layer was not ready to ship, and my first executive read overstated what the prototype had shown. The reviewer found three critical problems:

1. **The segment pattern of price sensitivity is wrong, and it drives who gets more and who gets cut.** In the backtest, ignoring segment differences beat the recommended setting on revenue.
2. **The uncertainty does not hang together.** One correction ratio was applied to every scenario, the bands and the headline were on different scales, and the budget held only on average.
3. **All validation came from one synthetic draw.** No claim has a distribution behind it.

**Interim position:** until these are fixed and a multi-seed validation study passes, the product uses a uniform price-sensitivity slope set by the design-based anchor, raises awards only within the range the price test has actually tested, and shows no probability-of-gain headline. Segment differences are learned by stratifying the price test, not borrowed from observational data.

## Corrections to my first executive read

These are statements I made that the review showed to be wrong or unsupported. They are withdrawn.

| What I said | What is correct |
|-------------|-----------------|
| International students are price-insensitive, so cutting their aid is an economic result and a policy choice | The true sensitivity for international students is about 1.34 points per $1,000, close to the 1.49 overall. The large cut was an **estimation error**, not a fact about those students |
| Every strategy was tuned to the same actual spend | False for two rows: the observational optimizer spent $0.48M and the legacy strategy spent $0, against $0.88M |
| Holdout accuracy (AUC 0.833) shows the hybrid model keeps forecast accuracy | The hybrid and the observational model are identical at current awards, so the holdout cannot validate the hybrid. Counterfactual accuracy must be checked on the randomized arm |
| Highest-need students gain most, and this matches the economics | Their estimated sensitivity (4.68) is about 85% above the truth (2.53). Part of the shift is an artifact |
| The legacy conclusion costs 65 students and 5.6% | True in this one world. "Cut all discretionary aid" is a strawman baseline: the prior output said aid did not move enrollment, not that it should be eliminated. Fair baselines are in the roadmap |
| A "planning estimate" (model gain times 0.17) is a sound headline | The realized-to-predicted ratio ranged from 0.14 to 0.62 across tuning settings and was negative for the observational optimizer. One scalar cannot correct all scenarios. Retired |
| The recommended allocation gains 7.5 students and 1.8% | One seed and one cohort. It is an illustration, not a result |
| There is a 100% probability of beating the status quo | Uncalibrated (1.0 at every budget from 1x to 2x, from 40 bootstrap draws). Withdrawn |
| The budget constraint holds | Only in expectation. At 1x the 95th percentile of realized spend was about 2.8 times the budget |
| Bands describe the uncertainty | Bands were right-skewed (at 1x, 416 to 673 enrolled) and on the raw model scale while the headline was scaled |

## What the review found sound

- Excluding accepted and disbursed fields from price and forecast models
- Keeping missing as missing, with "No FAFSA" as its own category
- Aggregates-only privacy architecture (sound in design; disclosure itself is still untested)
- The optimization formulation and solver
- Anchoring the price level in design-based evidence, as a principle
- The power arithmetic: about 0.56 points of standard error from four cohorts of price-test data

## What changes in the product

1. **Uniform slope by default.** The anchor sets one price sensitivity. Segment differences enter only through a hierarchical model fit on the randomized arm, with observational slopes used as weak prior means that carry an explicit bias variance. A hierarchical model replaces the uniform slope only if a multi-seed study shows it beating the uniform slope in at least 60% of seeds on cross-fitted value.
2. **A stratified price test.** Randomize the bonus within each policy segment (for example need tier, residency, academic tier) so heterogeneity can be learned. Check whether staff quietly lower other aid for bonus recipients.
3. **Increases only within the tested range.** Award increases are bounded by the range the price test covered. Revisions and renewals can only go up. Reductions are allowed only on first offers that have not yet been released, because no student has seen the counterfactual award. Cuts to communicated offers are not recommended, because the price test never observed cuts and the validation world could not detect asymmetric reactions.
4. **Budget as a tail risk.** Spend is limited with a tail-risk (CVaR) constraint across posterior draws, calibrated so that realized spend exceeds the budget by more than 5% in at most 5% of draws. The budget horizon (year one or four years) must match the revenue horizon.
5. **Honest numbers.** Each scenario shows a cross-fitted estimate of gain with a coverage-tested range. No probability-of-gain headline until calibration is demonstrated by a coverage study. Every recommendation is compared with fair baselines matched to the same spend.
6. **Release gate.** A Monte Carlo study over 200 or more synthetic worlds must pass numeric thresholds before the recommendation layer is published to any client.

## What the prototype did and did not establish

**Established, within one synthetic world:** the experiment's standard error (0.56 points), the pooled-anchor arithmetic, and that a model using aid recorded after enrollment looks extremely accurate (AUC 0.99) and is caught by the leakage tests.

**Not established:** the claims in the table above, the guardrail tests (not independently verified), disclosure control (the aggregate files were not reviewed), proxy fairness (the equity audit was not reviewed), and anything about real institutions.

The prototype remains useful as a reference implementation and as a source of lessons. It is not production code, and its numbers should not appear in client or sales material.

## Audiences and views

| Audience | Needs | Views |
|----------|-------|-------|
| Enrollment team | Where do we lose students? How much aid, for whom? | Funnel explorer, drivers, price response, scenario planner, allocation by segment, probability calculator |
| Leadership | What will the class and discount rate look like? What is the risk? | Headline scenarios with ranges, class projection, equity audit, lineage |
| Analyst | Is it right? Can I defend every number? | Everything, plus draft runs, diagnostics, and publish |

## Data stance (decided)

All testing and demonstration use pure synthetic data. The prior engagement files are not used as test data, although you have permission. The prototype's synthetic parameters were calibrated to aggregates printed in prior decks, so the spec must re-base every parameter on public benchmarks or document it as illustrative.

## Decisions

**Made (accepted with the reviewer's defaults)**

| Decision | Choice |
|----------|--------|
| Default slope structure | Uniform, with hierarchical segments only if they win the multi-seed study |
| Switching rule | Hierarchical wins in at least 60% of seeds on cross-fitted value |
| Discontinuity in the anchor | Keep, and drop if the density or placebo tests fail |
| Cuts | First offers not yet released only; revisions and renewals up only |
| Budget constraint | CVaR across posterior draws |
| Planning-estimate scalar | Retired |
| Probability-of-gain headline | Withheld until calibrated |

**Still needed from you**

1. **Budget horizon:** year one or four years? - Answer: the client will decide, so it needs to be flexible. we'd likely ask for a minimum of 3 yrs of data, with 5yrs as ideal. probably budget horizons at 1 and 3+ yrs
2. **Standing price test:** offer in every engagement, with segment stratification? Who approves on the client side? - Answer: let's leave this as an option only where it would yield real and actionable outcomes / insight. It can't be a stretch or an obfuscation or uneeded complication without payoff
3. **Counsel gate:** legal review of allocation logic and the equity audit before any client publication. - Answer: yes, we want this in place for client review and approval.
4. **Pilot client** and the data request (v2) agreement with them. - Answer: agree; we'll pilot this.
5. **Segment floors:** whether any policy-defined segment gets a minimum award (never defined on protected attributes). - Answer: make a recommendation for what a reasonable floor should be. Yes, we need one.

## Risks

| Risk | Mitigation |
|------|-----------|
| Recommendation layer shipped before validation | Release gate based on the multi-seed study; uniform-slope fallback |
| Client price test not approved | Discontinuity-only anchor with wider ranges; recommend starting a test |
| Underpowered tests at small institutions | Report minimum detectable effect before starting; pool cycles |
| Over-trust in projections | Cross-fitted ranges, coverage-tested; fair baselines; no probability headline until calibrated |
| Legal and equity exposure | Protected attributes excluded and tested; audit view; counsel gate |
| Synthetic world flatters the method | World library that includes failure cases (see roadmap) |
| Scope creep into a general analytics platform | Two products, one objective, one dashboard |

## Next steps

1. Provide the Phase 3 output from the review so the Monte Carlo study specification can be folded into S9.
2. Give the reviewer the aggregate files it did not see (equity audit, funnel cells, segment projections, the guardrail test file) so the fairness and disclosure items can be closed.
3. Work through the spec steps in the companion roadmap, in order.
