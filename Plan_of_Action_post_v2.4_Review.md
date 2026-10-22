# EFA + FAO: Plan of Action After the v2.4 Re-review

**Owner:** Jason Cohen
**First published:** October 21, 2026 | **Updated:** October 22, 2026 (status refresh; consumer ZIP data amendment added)
**First client:** University of Richmond School of Law.

## Status as of October 22

| Item | State |
|---|---|
| Re-review (`S4_S5_Rereview_v2.4.md`) | Done; errata block added |
| Scoped audit (`Audit_S4_S5_Rereview_v2.4.md`) | Done: holds with minor revisions. Edits E1 to E14 merged |
| Methodology v2.5, executive read v2.5, roadmap v2.5, changelog | Done (Phase A of `Handoff_S1_Kickoff.md`) |
| Verification (`Verification_Report_Oct22.md`) | Done: 7 of 7 guardrail tests pass; pipeline reproduces; real-solver re-runs differ by under 1% |
| Richmond discovery call | Held October 22. Answers go in `Richmond_Call_Capture_Sheet.md` |
| Git, `CLAUDE.md` | In place |
| S1 (requirements and user stories) | Next, once the capture sheet is filled in |
| **Consumer ZIP data amendment** | **Adopted October 22 as `02_methodology_v2.6.md`** (C1, C3 done; no separate audit). Companion documents and `CHANGELOG_v2.6.md` done. Track C below |
| Law Tier 1 data request | Not written. Gaps listed in the verification report, section 5 |
| Pitch materials | Confirm which copy is current. Add the ZIP privacy-claim check (track C) |

## Guiding principles

1. **Richmond's answers, not the build, are the critical path.** The class-size band decides the price-test verdict; the existing price evidence decides whether an optimized grid is possible at all.
2. **Licensing and counsel review are the critical path for consumer data.** The module can be built and tested on synthetic data now. Licensed data stays switched off until the Claritas agreement (gate L1) is signed.

## Sequence at a glance

| Step | What | Depends on | Status / timing |
|---|---|---|---|
| 1 | Audit, Richmond discovery, reset of promises | — | Audit and call done; promise reset and pitch check open |
| 2 | Methodology v2.5 and companion documents | Step 1 audit | Done |
| **2b (track C)** | **Consumer ZIP amendment: scoped audit, adoption decision, v2.6 reconciliation** | Jason's go-ahead; Step 2 | **New. Runs beside Step 3** |
| 3 | Spec documents S1 to S5 and S9 (plus consumer additions) | Step 2; Richmond answers | Next; about 3 to 5 weeks |
| 4 | Build: CI, screen, lean refactor, Monte Carlo gate, database and dashboard (plus the consumer module on the free-data source) | Step 3 signed off | Incremental |
| 5 | Richmond pilot | Discovery; Step 4 screen | 2027 cycle |
| 6 | Learning loop; per-engagement consumer bake-off | Step 5 | Ongoing |

Timings are planning estimates, not commitments. Richmond's offer season is the hard external clock, and offers are already rolling.

## Step 1. Audit, discovery, and promises

**1a. Scoped audit.** Done. Result: holds with minor revisions; both Critical findings stand; the Richmond price-test verdict is Not recommended at a ±3% class band and not robust above it.

**1b. Richmond discovery call.** Held. Record answers in `Richmond_Call_Capture_Sheet.md`. The priority questions are Q6 (capacity band), Q2 (existing price evidence), Q8 (blinding) and Q1 (objective). **Add one follow-up (not on the sheet):** does Richmond hold or want a Claritas license, and is the permanent address at application available in its records? Both feed track C.

**1c. Reset what we promise Richmond.**
- **Offer for the coming cycle:**
  - funnel analysis;
  - in-cycle pacing and melt monitoring;
  - the ABA 509 market view;
  - the evidence audit;
  - a written version of the current award grid.
- **Conditional:** an optimized grid, only if the evidence audit finds usable price evidence or Richmond accepts a test the screen supports.
- **Check the pitch materials** (still open):
  - one slope, no segment-level sensitivity claim;
  - no promise that test results arrive within a 4 to 6 week phase;
  - **[new]** make no privacy or fairness claim about ZIP data until L1 clears. The deck's privacy paragraph says "no full ZIP codes"; the amendment will change that. "No consumer credit data" stays true only if Claritas confirms its inputs (O28).

**Exit criteria:** capture sheet filled in; revised scope agreed internally; pitch copy confirmed.

## Step 2. Methodology v2.5 (done)

All items complete: audit edits applied, companion documents brought to v2.5, errata added to the review.

## Step 2b (track C). Consumer ZIP data amendment

**What it proposes.** ZIP5-derived consumer data (P$YCLE Premier as the primary source for a capacity tier, PRIZM optional for outreach), licensed and appended by Frankel. A derived three-band capacity tier may become a gated aid-grid dimension. Raw segment codes, ZIP5 as a feature, and household-level fields stay blocked. Racial and demographic guardrails are unchanged. Law follows the same rules as undergraduate.

**Status [October 22].** Adopted as v2.6. Why it needed its own track: it reverses v2.5 section 9 ("consumer segments never enter the aid grid"; "no geography finer than CBSA"), and it has not been audited. Its own text says the thresholds are "proposed; audit to confirm," and its license section is a blocker, not a detail.

| # | Action | Owner | Gate or dependency |
|---|---|---|---|
| C1 | **Decide how to proceed.** Done: adopted October 22 without a prior audit. Five issues resolved: P4 report-only everywhere; P1 the only blocking gate; G2 power test kept; credit-data rule narrowed to individual-level data; ZIP5 transient, ZIP3 stored; two tiers for law (three for undergraduate), fixed per program | Jason | Done |
| C2 | **Scoped audit of the consumer layer** (now optional but advised, before S4 and S5 sign-off; brief to be written; items below) | Auditor | Before S4/S5 sign-off |
| C3 | **Reconcile into v2.6.** Done: `02_methodology_v2.6.md` (sections 2 to 5, 7, 9 to 14, Appendices C and E; O13, O20 to O35), executive read, roadmap, `CHANGELOG_v2.6.md`, `CLAUDE.md`. **Not done:** data request (`zip_key` file), pitch privacy paragraph | Claude Code | Done |
| C4 | **License and counsel (Gate L1):** a written Claritas agreement covering client enrollment and aid analytics, appending by Frankel, return of derived tiers to clients, use in aid-allocation policy, retention. **Deferred until a firm client contract exists** (Oct 22 decision). Fallbacks: F1 client-licensed with a third-party processor agreement; F2 free ACS/IRS data; F3 another vendor. Also request Claritas documentation of inputs, including any use of race or ethnicity (O28) | Jason, counsel | Firm contract |
| C5 | **Counsel review** of the license and proxy note before first grid use at any client (approved Oct 22) | Counsel | Before any grid use |
| C6 | **Spec additions in Step 3:** the `zip_key` contract and consumer fields in S2; tier formula and gates in S4; grid mechanics under the cell cap in S5; proxy tests in S8; synthetic-world additions in S9 | Claude Code | C3 |
| C7 | **Build the consumer module** (`pipeline/consumer.py`) on the free ACS/IRS source first. It validates the architecture and sets the baseline paid data must beat. Licensed ingestion stays off | Claude Code | Step 4; spec signed off |
| C8 | **Per-engagement bake-off** (variants A to E), gates G1 to G4 and proxy gate P1 | Analyst | Three or more cohorts; license cleared |

**Scope of the C2 audit.** Points the amendment leaves open or that I could see on reading it. These are my observations, not audited findings.

1. **Internal inconsistency.** Section 4.2 lists P4 as a requirement for targeting use, but section 5 makes P4 report-only. Decide which.
2. **Proxy gating is thin by design.** Only P1 (Cramér's V below 0.3) is a gate; P2 to P4 are reported. A neighborhood capacity tier is a known proxy for race. This was Jason's ruling, so the audit should test whether P1 alone catches the synthetic worlds with high ZIP-race correlation (the amendment's c = 0.4 and 0.7), and counsel should see the proxy note before first grid use.
3. **G2 power (suspected, untested).** Gate G2 asks for at least +0.01 out-of-time AUC with a bootstrap lower bound above 0. At a law school's size (roughly 650 admits a year over three cohorts) that may be unreachable even for a real signal. Test it in W0L.
4. **License terms.** The posted Claritas terms conflict with D2 on five clauses (the amendment's section 2). The audit should check the gate L1 wording and the fallbacks, not just accept the list.
5. **"No credit data" claim.** P$YCLE is built partly on estimated liquid assets. Whether it counts as consumer credit data under our rule depends on O28.
6. **Cell-cap arithmetic for law.** A law grid with position band (5) and a market dimension (2) already has 10 cells; three tiers would make 30, above the cap of 20 at about 600 admits. The amendment's "substitution" route needs a concrete default for law.
7. **Address validity for JD applicants.** The permanent address at application may be a family address. Check the bake-off's treatment.
8. **Tier construction.** The formula depends on Claritas's own affluence ordering of segments; confirm that ordering is available under the license and is stable across vintages (O30).
9. **FAFSA and FERPA note (O27).** Counsel item, not an audit item.

**Effect on Richmond.** Targeting use is plausible this cycle only if L1 clears quickly and the free-data baseline is ready. Grid use is unlikely this cycle: G2 and G4 need at least three cohorts of backtest, L1 must clear, and counsel review comes first. Do not mention ZIP-based aid allocation to Richmond as a deliverable.

## Step 3. Spec documents

| Spec | Focus for this round | Review |
|---|---|---|
| S1 Requirements and user stories | Richmond as the first user. **Consumer ZIP requirements are listed as gated and conditional on C1**, not as MVP | Jason signs off |
| S2 Data contract and synthetic data | W0L law world calibrated to 509; 509 field rules; screen scoping inputs. **[C6]** `zip_key` and consumer fields; ZIP latent-capacity and ZIP-race synthetic additions | Jason signs off |
| S3 Pipeline interfaces | Estimand, choice rule, grid baseline, screen, evidence audit as typed functions. **[C6]** `load_zip_table`, `zip_index`, `fit_tiers`, `assign_tier`, `match_report`, `proxy_audit` | Opus review |
| S4 Statistical methods | Rewritten from v2.5. **[C6]** tier formula, gates G1 to G4, bake-off | Opus review |
| S5 Optimization | Rewritten from v2.5, law profile included. **[C6]** tier-by-substitution under the cell cap | Opus review |
| S8 Privacy, equity, alignment | **[C6]** proxy tests P1 to P4, purpose statement, construction rule, license posture | Opus review, then client alignment |
| S9 QA and Monte Carlo gate | Worlds, seeds, thresholds. **[C6]** consumer worlds (signal strength ρ, race correlation c) | Opus review of thresholds |

Hold S6 (database) and S7 (dashboard) until S4 and S5 are stable. The consumer tables (`zip_key`, `student_consumer`, `consumer_gate_status`) go into S6 once C1 is decided.

## Step 3b. Data request v3 (new spec step S2b)

No earlier step built the data request in full. S2 covers the data contract; the request was only a parallel item. It is now its own spec step, S2b. **Status [October 22]: draft built** in `efa_fao/docs/data_request_v3/` (single spec, law and undergraduate documents, Excel templates, dictionaries, gap log, spec tests). `efa_fao/docs/04_data_request_v2.md` is unchanged.

| # | Action | Owner | Status |
|---|---|---|---|
| D1 | Law Tier 1 request first (client-facing document and Excel template), using the six law gaps and further gaps in `Verification_Report_Oct22.md` section 5, and the optional `zip_key` add-on (methodology Appendix E.3) | Claude Code (Cowork drafted) | Draft done: `Data_Request_v3_law_*.docx`. Needs Richmond call answers to tune (conditional scholarships, need use, offer batches, hard or soft cap) |
| D2 | Reconcile definitions to the Common Data Set (undergraduate) and the ABA 509 report (law) | Claude Code | Done in `spec/definitions.csv` and `GAP_LOG.md` section 2 |
| D3 | Institutional reference check (CDS or ABA 509) for QA reconciliation | Claude Code | Done: `Institutional_Reference` worksheet and section 9 of the document |
| D4 | Full v3 request for law and undergraduate, Tier 1 and Tier 2, reconciled to the S2 data contract | Claude Code | Draft done for both programs. **Reconcile to S2 when S2 is signed off**, then promote over 04 |
| D5 | Jason reviews the generated documents against his reference request and `GAP_LOG.md` (judgment calls J1 to J10) | Jason | Open |
| D6 | Counsel review of privacy, ZIP5 add-on and data-use language; confirm loan-limit statements with Federal Student Aid; revise the pitch deck's privacy and Tier 1 text to match | Jason, counsel | Open |

**Judgment call.** D1 ships before S2 is final so Richmond can start; D4 follows S2 so the request and the contract cannot drift. If Richmond's data is not due before S2 signs off, merge D1 into D4.

## Step 4. Build order

Lead with what Richmond needs first.

1. **Repo hardening.** CI, pinned dependencies, the guardrail tests from a clean checkout. Note from verification: tests 2 and 7 fail on a fresh clone until the pipeline has run, and test 1 passes vacuously. Fix the ordering in CI.
2. **Evidence audit and value-of-information screen,** as a standalone tool. Run it on the real optimizer with a 509-calibrated pool. Acceptance: reproduces the audit's worked examples, and the verdict is unchanged when all dollar inputs are scaled.
3. **Lean-model refactor with the law profile:** all-eligible analysis (conditional on blinding), logit-unit pooling, cell-level baseline, two-sided choice rule, award modes, commitment-length horizon, count-noise buffer, policy grid.
4. **Monte Carlo gate,** including W0L and the confound worlds. If the grid does not beat the best fair heuristic, ship the heuristic.
5. **Consumer module on the free source [C7],** if the amendment is adopted. Add its guardrail tests to `test_guardrails.py`: no ZIP5 or segment codes in any analysis or output table; tier construction takes no race, ethnicity or gender argument; tier rejected as a grid dimension unless every required gate passed; no output pairs a ZIP with a segment.
6. **Database, dashboard, and monitoring.**

## Step 5. Richmond pilot

1. Send the law Tier 1 data request; receive data through the secure channel.
2. Run QA; run the evidence audit; run the screen on Richmond's real inputs, objective, and capacity band.
3. Deliver the descriptive layers: funnel, pacing and melt, 509 market view, written status-quo grid.
4. Only if the audit and screen support it: FAO optimization, then the alignment gate (one-page approval, with the equity audit).
5. **Consumer data:** targeting use only, and only once L1 has cleared. Otherwise the free ACS/IRS indicators serve as the descriptive geography layer.
6. Record the backtest diagnostic and the treatment log for the next cycle.

**Exit criteria:**
- the data pass QA;
- the evidence-audit and screen verdicts are documented;
- the descriptive deliverables are accepted;
- the alignment sign-off is recorded if optimization ran;
- if consumer data were used, gate status is recorded in `consumer_gate_status`.

## Step 6. Learning loop

- Re-run the screen each cycle as Richmond's evidence accumulates.
- Pool design-based price evidence across clients into an empirical prior.
- Run the consumer bake-off at each new engagement. If no licensed variant beats the free baseline (G2), do not use the licensed data.
- Revisit deferred refinements (methodology section 11) only when their triggers are met.

## Risks to the plan

| Risk | Mitigation |
|---|---|
| Richmond's class-size band is wider than ±3% | The screen verdict can move to Optional or Recommend. Rerun on the real optimizer before promising anything |
| No usable price evidence at Richmond | Deliver the descriptive scope; propose a mechanism test or one-year bonus next cycle |
| Offer season starts before the build is ready | Descriptive layers and the evidence audit need no optimizer; sequence them first |
| Staff cannot be blind to test membership | Primary estimator becomes test-only; record the call answer (Q8) |
| **Claritas license does not permit our use (L1 fails or is slow)** | Fall back to client-licensed (F1) or free data (F2). The module is license-agnostic, so the build is unaffected |
| **Amendment adopted without audit** | Adopted on Jason's decision. Mitigation: scoped audit (C2) before S4/S5 sign-off, counsel review before first grid use, tier default off in the law grid, G1 to G4 thresholds treated as untested proposals (O35 open) |
| **Neighborhood capacity tier acts as a proxy for race** | P1 gate, P2 to P4 reports, purpose statement, construction rule, counsel review before first grid use; high-correlation synthetic worlds must show the tier stays out of the grid |
| **Privacy or fairness claims in client materials get ahead of the license** | Pitch check in Step 1c; no ZIP-based claims until L1 clears |
| **Scope creep: consumer data pulls effort from the Richmond critical path** | Track C runs beside Step 3. The free-data module is built after Step 4 items 1 to 4, not before |
| Competitive pressure to promise an optimized grid now | Keep the claim honest; the evidence audit and screen are the differentiator |
