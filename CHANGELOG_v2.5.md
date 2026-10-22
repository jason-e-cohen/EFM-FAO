# v2.5 Change Log

**Base:** `02_methodology_v2.4.md`. Changes are tagged **[v2.5]** in `02_methodology_v2.5.md`.
**Source:** `S4_S5_Rereview_v2.4.md`, required-before-build edits S4-1 to S4-14 and S5-1 to S5-10.
**Status:** draft pending the scoped audit (`Auditor_Brief_S4_S5_Rereview_v2.4.md`).

The executive read, technical roadmap, data request, and pitch materials are still at v2.4 or v2.3. Bring them to v2.5 after the audit (Plan of Action, Step 2).

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

## Pending the audit

| Item | Question |
|---|---|
| A1 | Does the Not recommended verdict for Richmond hold under a richer pool, other class bands, other priors, a median target, and a one-year bonus? |
| A2 | Is the two-sided rule so conservative that it nearly always returns the status quo? |
| A3 | Are the ABA 509 field definitions correct as inferred? |
| A4 | Do the estimand and logit-pooling argument hold? |
| A5 | Arithmetic in the Richmond baselines |
