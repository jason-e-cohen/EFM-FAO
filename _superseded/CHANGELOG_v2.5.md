# v2.5 Change Log

**Base:** `02_methodology_v2.4.md`. Changes are tagged **[v2.5]** in `02_methodology_v2.5.md`.
**Source:** `S4_S5_Rereview_v2.4.md`, required-before-build edits S4-1 to S4-14 and S5-1 to S5-10.
**Status:** audit completed (`Audit_S4_S5_Rereview_v2.4.md`); its edits E1 to E14 are in the addendum below. Pending sign-off.

The executive read and technical roadmap were brought to v2.5 after the audit (Oct 22, 2026). The data request (v2.3) and pitch materials are not yet updated.

## Edits applied

| Edit | Change | Section |
|---|---|---|
| S4-1 | Analyse every randomized eligible (intent to treat), not test students only | 4, Evidence sources |
| S4-2 | Estimand θ defined at status-quo awards; pool logit slopes; flag in logit units; widen scenarios on a flag; experiment-only after two consecutive flags | 4, Estimand and Anchor |
| S4-3 | Conversion test replaced: status-quo-point AME on recalibrated p, within 5% | 4, Response model |
| S4-4 | Baseline centered on recalibrated p\* and the cell reference award r_c; forecast has no aid fields | 4, Response model |
| S4-5 | Sample-size formula: k = 0.92 or √(1 − R²); eligible yield; dose scaled by vertical; MDE for information only | 4, Sample size |
| S4-6 | Test cost × award-commitment multiplier M; no revenue offset when capacity is capped | 4, Sample size and cost |
| S4-7 | Power-based screen retired; value-of-information screen with Richmond worked example | 4, Screen rule |
| S4-8 | Wave slopes descriptive; four conditions before one can change a recommendation | 4, Timing |
| S4-9 | Evidence audit minimum-evidence criteria and μ0/σ0 output | 4, Evidence audit |
| S4-10 | Scenarios are quantiles of the logit-slope posterior, with b_L floored at 0 | 6 |
| S4-11 | Monte Carlo realized ÷ predicted distribution published; low scenario shown beside every headline | 6 |
| S4-12 | Count-noise buffer (1.645 × spend SD at b_H) | 5, Constraints; 6 |
| S4-13 | Monte Carlo study: 21 worlds, including law and confound strength; 200 and 100 seeds; model-set budgets; outcome draws; fair-baseline margin | 10 |
| S4-14 | "Four cohorts" corrected to three (2023 to 2025) | Appendix B |
| S5-1 | Two-sided choice rule; automatic weak-evidence state | 5, Choice rule |
| S5-2 | Award mode (supplement or total); ladder to tuition; cap = max(configured cap, current award); law cap 100% | 5 |
| S5-3 | Budget and revenue horizon equal the award commitment length | 5, Horizon |
| S5-4 | Cells ≤ admits per cohort ÷ 30; UG and law profiles | 5, Cells |
| S5-5 | Guardrail is 5% of tuition | 5, Constraints |
| S5-6 | Whitelist adds position band; median constraint; feasibility pass; shadow price; runtime proxy screen | 5, Targeted objectives |
| S5-7 | Increases-only evaluation for mid-cycle re-optimization | 5 |
| S5-8 | Policy grid scope: reserve, pool projection, frozen thresholds, `policy_changes` log | 5 |
| S5-9 | Floors apply to all market tiers, including targets | Appendix C |
| S5-10 | Spend counted over the commitment horizon | 5, Horizon |

## Other additions

- Law profile in scope (section 1).
- Relative position definition (section 2).
- ABA 509 field rules (section 2), and the rank-matching procedure (new Appendix D).
- Renewal rule and revision reason codes in the data model (section 3).
- Policy changes as a third evidence source (section 4).
- Moderator discovery protocol with three adoption gates (section 4).
- Batch-scoring and consumer-segment release criteria (sections 7 and 9).
- Boosted-challenger margin and Monte Carlo tests (section 11).
- New deferred refinements: mechanism tests, a one-year bonus test, and an empirical prior pooled across clients (section 11).
- Re-review findings F1 to F20 with their status (Appendix B).
- Open issues O1 to O19 ruled, with new audit items A1 to A5 (section 13).

## Pending the audit (all closed; see the addendum)

| Item | Question |
|---|---|
| A1 | Does the Not recommended verdict for Richmond hold under a richer pool, other class bands, other priors, a median target, and a one-year bonus? |
| A2 | Is the two-sided rule so conservative that it nearly always returns the status quo? |
| A3 | Are the ABA 509 field definitions correct as inferred? |
| A4 | Do the estimand and logit-pooling argument hold? |
| A5 | Arithmetic in the Richmond baselines |

## Addendum: audit edits E1 to E14 (October 22, 2026)

**Source:** `Audit_S4_S5_Rereview_v2.4.md`, section 4 (verdict: holds with minor revisions). All edits are in `02_methodology_v2.5.md`, tagged **[v2.5, E<n>]**. "Acceptance" is the test the audit attached; none is implemented yet (coding has not started).

| Edit | Change | Section | Audit finding | Acceptance |
|---|---|---|---|---|
| E1 | Bias sentence deleted. Precision gain restated as about 20% in logit units (analytic 0.76). All-eligible estimate is primary only if staff are blind to test membership; otherwise test-only at dose 0 is primary and all-eligible is secondary. Yield-contrast compliance check noted as unable to detect the effect; W12 variant added | 4, Evidence sources; 10 | A20, A21, A22 | W12 variant (0.10-logit test-status effect): primary bias ≤ 10% in ≥ 90% of seeds |
| E2 | "simulation: 0.66" replaced by "simulation in logit units gives 0.80" | 4, Sample size | A21 | Formula SE within 10% of Monte Carlo SE in logit units |
| E3 | Choice rule keeps "maximize at b_M"; screen's preposterior analysis uses the same objective. Open-for-audit note replaced by the audit result | 4, Screen rule; 5, Choice rule | A10 | Screen and optimizer pick the same grid on a shared fixture |
| E4 | EVSI scored with the same function as the no-test value; may be negative; reported with sign; negative gives Not recommended and a review of the quantile margins | 4, Screen rule | A5 | Five-band Richmond fixture: EVSI −$0.12M; unconstrained Bayes rule gives ≥ 0 |
| E5 | EVPI formula unchanged; j0 may be a reallocation and V[i, j0] is never dropped | 4, Screen rule | Task 1.4 | Fixture with j0 ≠ status quo matches a hand calculation |
| E6 | Capped or banded cost includes induced enrollees' bonuses ($375k vs $315k at zero effect); ratio gate and 5% gate use the zero-effect cost in both regimes | 4, Cost; Screen rule | A6, A7 | Richmond fixture: $375k and $315k (D = $4,000, K = 1); ratio gate defined when expected net cost < 0 |
| E7 | Worked example rewritten: verdict conditional on capacity band; position target does not help; capacity band is a mandatory scoping input; verdicts reported at the client's band, ±5% and ±10%. Stylized-pool caveat replaced by a requirement to run the screen on the production optimizer | 4, Screen rule | A2, A3, A4 | Screen shows three-band verdicts; verdict unchanged under scaling of all dollar inputs |
| E8 | Median constraint is on the expectation; the 1.645σ margin is dropped from feasibility; probability the median holds is reported separately | 5, Targeted objectives | A30 | Richmond-calibrated status quo is feasible under the constraint, infeasible with the margin |
| E9 | Buffer "about 12%" replaced by "about 15% (award-weighted)" | 5, Constraints | A29 | Buffer on the five-band fixture 15.5% ± 0.5 |
| E10 | Conditional-scholarship lag is one year (report year Y lists Y − 1 to Y − 3; count final after year one); cohort labels from report year; flag peers above 10% prevalence; nonresident-zero rule narrowed to a few private schools. Field-rules caveat updated | 2, Field rules; Appendix D | A16, A17, A13 | Loader test: Brooklyn 2021-22 cohort reads 390 / 73 from the 2022, 2023 and 2024 files |
| E11 | Rank-matching illustration replaced (position 0.71, $47,100 vs $55,550) | Appendix D | A18 | Unit test for the full-tuition branch and tail extrapolation |
| E12 | Conversion-test tolerance is 1.645 × SE of the difference; fixture with a 10% level bias must fail | 4, Response model | A24 | Biased fixture fails; unbiased passes |
| E13 | Discontinuity weight reported beside the anchor and capped at 30% | 4, Anchor | A23 | Anchor output shows the weight |
| E14 | Per-wave MDE basis stated (test-only; 3.9 and 5.5 all-eligible) | 4, Timing | A31 | None |

**Also changed in the same pass**
- Status line: "draft pending the audit" removed. Version history has an audit-addendum line.
- Section 13: open items A1 to A5 closed with the audit's result for each. O2 and O16 rulings annotated.
- Appendix B: rows F1, F3, F7, F13 and F18 updated to the audit's findings (F1 was not in the handoff list; its text said "audit to test conservatism").
- Section 4, sample size: a note that the 0.76 factor applies only when the all-eligible estimate is primary (follows from E1).
- Section 5, Choice rule: the "Open for the audit" paragraph replaced by the audit result (A8 to A10).
- Section 10, W12 row: variant added (E1 acceptance).

**Not changed, flagged for Jason** (see `Verification_Report_Oct22.md`)
- Appendix A still cites the simulated SD 0.287 for the all-eligible design; the audit (A21) says that figure compares two different estimands.
- The audit's E4 and E6 name screen steps 6 and 7; the methodology's steps are 5 (EVSI) and 6 (net value), and the cost text sits above the steps. Edits were placed by content, not by step number.
- E13 says "cap it at 30%" without a mechanism; the text states the cap and leaves the mechanism to S3.
