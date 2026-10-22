# EFA + FAO: Plan of Action After the v2.4 Re-review

**Owner:** Jason Cohen
**Date:** October 21, 2026
**Assumption:** `S4_S5_Rereview_v2.4.md` holds, or holds with minor revisions, after the scoped audit (`Auditor_Brief_S4_S5_Rereview_v2.4.md`).
**First client:** University of Richmond School of Law.

## Guiding principle

The critical path runs through Richmond's answers, not through the build. Richmond's objective and its existing price evidence decide whether FAO optimization is even on the table this cycle. Get those answers before investing in the optimizer.

## Sequence at a glance

| Step | What | Depends on | Rough timing |
|---|---|---|---|
| 1 | Audit, Richmond discovery, and reset of what we promise. These run in parallel | — | Now to about 2 weeks |
| 2 | Methodology v2.5 (merge the required edits, then audit corrections) | Step 1 audit | 1 to 2 weeks |
| 3 | Spec documents S1 to S5 and S9, in roadmap order | Step 2 | 3 to 5 weeks |
| 4 | Build: CI, then evidence audit and screen, then lean refactor with the law profile, then Monte Carlo gate, then database and dashboard | Step 3 (S1 to S5, S9 signed off) | Incremental |
| 5 | Richmond pilot | Step 1 discovery; Step 4 evidence audit and screen | Richmond's 2027 cycle |
| 6 | Learning loop across cycles and clients | Step 5 | Ongoing |

Timings are planning estimates, not commitments. Richmond's offer season (roughly December through April) is the hard external clock.

## Step 1. Now: three things in parallel

### 1a. Scoped audit

- Send the auditor `Auditor_Brief_S4_S5_Rereview_v2.4.md`, the review, `review_support_v2.4/`, the four v2.4 documents, and the 509 data folder.
- Expected output: `Audit_S4_S5_Rereview_v2.4.md`.
- **Decision point.** If the audit overturns either Critical finding, or the Richmond screen verdict, pause Step 2 and resolve that first. Otherwise, fold its corrections into v2.5.

### 1b. Richmond discovery call

These answers determine the screen's verdict and the shape of the law grid:

1. **Objective:** net tuition revenue, class size, median LSAT/UGPA position, or a mix? If position matters, which target?
2. **Existing price evidence:** does Richmond use a published or index-based scholarship grid, or has it changed its award schedule in the last five cycles?
3. **Need:** are FAFSA or institutional need data used in scholarships at all?
4. **Renewal rule:** are awards fixed-dollar or a percentage of tuition at renewal?
5. **Capacity:** how tightly is the entering class held (the review assumed ±3%)?
6. **Appetite for randomization:** would Richmond accept a bonus-aid test (renewable or one-year), or a mechanism test (deposit deadline or award timing)?
7. **Data readiness:** three to five cohorts of admits with offer dates, every package version, LSAT and UGPA, engagement, deposit and census status.

Write the answers into the scoping template so they feed the screen directly.

### 1c. Reset what we promise Richmond

- **Offer for the coming cycle:**
  - funnel analysis;
  - in-cycle pacing and melt monitoring;
  - the ABA 509 market view (peer pricing, rank-matched award gap, yield context);
  - the evidence audit;
  - a written version of Richmond's current award grid.
- **Offer conditionally:** an optimized grid, only if the evidence audit finds usable design-based price variation, or Richmond accepts a test the screen supports.
- **Fix the pitch materials** before they go out:
  - one slope, not segment-level sensitivity (changelog item 5);
  - no promise that test results arrive within a 4 to 6 week phase (changelog item 1);
  - "no optimized grid without design-based price evidence."

**Exit criteria for Step 1:**
- the audit is received and triaged;
- the discovery answers are recorded;
- the revised scope is agreed internally.

## Step 2. Methodology v2.5

1. Produce `02_methodology_v2.5.md` with the required-before-build edits from the review (S4-1 to S4-14 and S5-1 to S5-10). The draft is done ahead of the audit and marked "pending audit."
2. Fold in the audit's corrections when they arrive.
3. Update section 13 (open issues) with the rulings, and add the review findings to Appendix B.
4. Write `CHANGELOG_v2.5.md`.
5. Bring `01_executive_read` and `03_technical_roadmap` to v2.5, so the bottom line and decision log match the methodology.

**Exit criteria:** v2.5 signed off, with no open required-before-build items.

## Step 3. Spec documents

Write and review in roadmap order. Each step is one document.

| Spec | Focus for this round | Review |
|---|---|---|
| S1 Requirements and user stories | Written around Richmond as the first user: enrollment dean, aid office, leadership | Jason signs off |
| S2 Data contract and synthetic data | Add the law world (W0L) calibrated to the 509 data; the 509 external-data contract with field rules; scoping inputs for the screen | Jason signs off |
| S3 Pipeline interfaces | Estimand, choice rule, grid baseline, screen, and evidence audit as typed functions with signatures | Opus review |
| S4 Statistical methods | Rewritten from v2.5 | Opus review (short; checks the edits landed) |
| S5 Optimization | Rewritten from v2.5, law profile included | Opus review |
| S9 QA and Monte Carlo gate | Worlds, seeds, metrics, thresholds from review Phase 3 §1 and §2 | Opus review of thresholds |

**Hold S6 (database) and S7 (dashboard)** until S4 and S5 are stable. S8 (privacy, equity, alignment) can run alongside S5.

## Step 4. Build order

Lead with what Richmond needs first.

1. **Repo hardening.** CI, pinned dependencies, and the guardrail tests running from a clean checkout. This also confirms the "7 passing" claim.
2. **Evidence audit and value-of-information screen,** as a small standalone tool. It is needed at scoping, before data arrive, and it decides what can be sold. **Acceptance:** reproduces the review's worked examples, and the verdict does not change when all dollar inputs are scaled by a constant.
3. **Lean-model refactor with the law profile:**
   - all-eligible experiment analysis;
   - logit-unit pooling;
   - cell-level baseline;
   - two-sided choice rule;
   - award modes;
   - horizon equal to the commitment length;
   - count-noise buffer;
   - policy grid.
4. **Monte Carlo gate,** including W0L and the confound worlds. This is the acceptance test for the refactor. If the grid fails to beat the best fair heuristic, ship the heuristic.
5. **Database, dashboard, and monitoring** (roadmap phases 3 to 5).

## Step 5. Richmond pilot

1. Send the Tier 1 data request; receive the data through the secure channel.
2. Run QA; run the evidence audit; run the screen on Richmond's real inputs and stated objective.
3. Deliver the descriptive layers: funnel, pacing and melt, 509 market view, written status-quo grid.
4. **Only if the audit and screen support it:** run FAO optimization, then the client alignment gate (one-page approval, with the equity audit).
5. Record the backtest diagnostic and the treatment log for the following cycle.

**Exit criteria:**
- the data pass QA;
- the evidence-audit and screen verdicts are documented;
- the descriptive deliverables are accepted;
- the alignment sign-off is recorded if optimization ran.

## Step 6. Learning loop

- Re-run the screen each cycle as Richmond's evidence accumulates.
- Pool design-based price evidence across clients and verticals into an empirical prior. That eventually replaces the assumed prior in the screen, and it is the change most likely to turn future screens positive.
- Revisit the deferred refinements (methodology section 11) only when their triggers are met.

## Risks to the plan

| Risk | Mitigation |
|---|---|
| The audit overturns a Critical finding or the screen verdict | Decision point in Step 1a; pause v2.5 on that item only |
| Richmond's objective is median position, not revenue | Rerun the screen with the target constraint; a test may then become Optional or Recommend |
| No usable price evidence at Richmond | Deliver the descriptive scope; propose a mechanism test or one-year bonus for the next cycle |
| Offer season starts before the build is ready | Descriptive layers and the evidence audit do not need the optimizer; sequence them first |
| Competitive pressure to promise an optimized grid now | Keep the claim honest; the evidence audit and screen are the differentiator |
