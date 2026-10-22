# EFA + FAO v2: Executive Read (revision 3)

**Prepared for:** Jason Cohen, Director of Research + Insights
**Status:** Methodology reviewed independently (Opus, four phases). Review edits accepted. Spec phase next. No further code until the spec steps in the companion roadmap are complete.
**Supersedes:** `EFA_FAO_Executive_Read_v2.md`. Revision 3 incorporates Jason's decisions (October 2026) on budget horizon, data history, the price test, the client alignment gate, the pilot, and segment floors.

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
2. **A price test, only where it pays off.** Where a screen shows a test would yield real, actionable insight, randomize the bonus within each policy segment (for example need tier, residency, academic tier) so heterogeneity can be learned, and check whether staff quietly lower other aid for bonus recipients. Where it would not, the product runs without a test, anchored on the merit-grid discontinuity with wider ranges and a plain label saying so. The client's VP or Director of Enrollment, or a Dean, decides per engagement.
3. **Increases only within the tested range.** Award increases are bounded by the range the price test covered. Revisions and renewals can only go up. Reductions are allowed only on first offers that have not yet been released, because no student has seen the counterfactual award. Cuts to communicated offers are not recommended, because the price test never observed cuts and the validation world could not detect asymmetric reactions.
4. **Budget as a tail risk.** Spend is limited with a tail-risk (CVaR) constraint across posterior draws, calibrated so that realized spend exceeds the budget by more than 5% in at most 5% of draws. Year one is required and is the default horizon. The client may extend to a multi-year horizon (up to four years), and the budget and revenue horizons must match. Multi-year results are labeled assumption-dependent when retention beyond year two cannot be estimated from the client's history.
5. **Honest numbers.** Each scenario shows a cross-fitted estimate of gain with a coverage-tested range. No probability-of-gain headline until calibration is demonstrated by a coverage study. Every recommendation is compared with fair baselines matched to the same spend.
6. **Segment floors.** The optimizer cannot cut a policy-defined segment below a floor (see the recommendation below), and every run shows which floors bind and what they cost.
7. **Release gate.** A Monte Carlo study over 200 or more synthetic worlds must pass numeric thresholds before the recommendation layer is published to any client.

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

All testing and demonstration use pure synthetic data. The prior engagement files are not used as test data, although you have permission. The prototype's synthetic parameters were calibrated to aggregates printed in prior decks, so the spec must re-base every parameter on public benchmarks or document it as illustrative. For real engagements, we request three to five cohorts of client history (minimum three, ideal five).

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

**Decided (your answers)**

| Topic | Decision |
|-------|----------|
| Budget horizon | Client's choice. Year one is required and the default; the client may extend to a multi-year horizon (up to four years) |
| Data history requested | Three to five cohorts: minimum three, ideal five |
| Standing price test | An option per engagement, offered only where it yields real, actionable insight, never as a complication without payoff. Decided by the client's VP or Director of Enrollment, or a Dean |
| Gate before client publication | Kept, as a **client alignment and approval gate**. It is about buy-in and agreement on logic, guardrails, floors, and the equity audit. Legal review is the client's choice |
| Pilot | We will pilot. For now, proceed on the assumption that the v2 data request model is approved |
| Segment floors | Required. Recommended defaults below, pending your confirmation |

**Recommended segment floors (pending your confirmation)**

A floor is a minimum on a segment's average discretionary award, as a share of that segment's trailing three-cohort average. It applies to first offers not yet released, and every run reports which floors bind and what each costs in net tuition revenue.

| Segment | Floor | Why |
|---------|-------|-----|
| Highest-need and Pell-eligible | 100% of trailing average | Access mission; should rarely bind |
| Other need tiers, including no-FAFSA | 75% | Limits reallocation to 25% per cycle where evidence is weakest |
| In-state, out-of-state, international | 75% each | Guards against the estimation-error cut seen in the review |
| Transfer | 75% | Small samples |
| First-generation | Client option; 100% if mission-driven | Correlates with protected attributes, so the client decides |

Not used: academic tier (the merit grid already protects it), region, source channel, and race, ethnicity, or gender (never). A floor can relax to 50% only where the price test shows that segment is materially less sensitive and the client approves. With the uniform-slope default these floors will rarely bind; they are a safeguard for the future, when segment-specific estimates are used.

**Still open**

1. Confirm the floor percentages and the first-generation treatment.
2. Retention assumptions for years three and four when a client's history is short.
3. What the client signs at the alignment gate, and what the legal-considerations note covers.

## Risks

| Risk | Mitigation |
|------|-----------|
| Recommendation layer shipped before validation | Release gate based on the multi-seed study; uniform-slope fallback |
| Price test not offered or not approved | Discontinuity-only anchor with wider ranges and a plain label; the product must work without a test |
| Underpowered tests at small institutions | Suitability screen; report minimum detectable effect before starting; pool cycles |
| Short client history (three cohorts) | Year-one scenarios lead; multi-year results use stated retention priors and are labeled; wider ranges |
| Over-trust in projections | Cross-fitted ranges, coverage-tested; fair baselines; no probability headline until calibrated |
| Legal and equity exposure | Protected attributes excluded and tested; audit view; client alignment gate with a legal-considerations note, and legal review at the client's option |
| Synthetic world flatters the method | World library that includes failure cases (see roadmap) |
| Scope creep into a general analytics platform | Two products, one objective, one dashboard |

## Next steps

1. Confirm the segment floor defaults and answer the remaining open items above.
2. Provide the Phase 3 output from the review so the Monte Carlo study specification can be folded into S9 (S = spec step; see the roadmap).
3. Give the reviewer the aggregate files it did not see (equity audit, funnel cells, segment projections, the guardrail test file) so the fairness and disclosure items can be closed.
4. Update the client data request (history of three to five cohorts) and draft S1, the requirements spec.
5. Work through the spec steps in the companion roadmap, in order.
