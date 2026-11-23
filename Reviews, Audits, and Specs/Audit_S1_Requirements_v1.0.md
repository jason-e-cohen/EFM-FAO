# Audit of S1: Requirements and User Stories (v1.0)

**Auditor:** Claude Opus 5.5 (Cowork), October 23, 2026. I did not write S1.
**Audited:** `S1_Requirements_and_User_Stories.md` v1.0 (October 22; 469 lines, about 11,800 words), the Claude Code session report (two screenshots: "Did the call answers change any Richmond requirements?" and the FR count, contradictions and open questions), and commit `350da38`.
**Checked against:** `Handoff_S1_Kickoff.md` (Phase B), `02_methodology_v2.6.md`, `03_technical_roadmap_v2.6.md`, `Richmond_Call_Capture_Sheet.md`, `Audit_S4_S5_Rereview_v2.4.md`, `Verification_Report_Oct22.md`, `efa_fao/docs/data_request_v3/` (law dictionary, `GAP_LOG.md`), the pitch deck in the folder (`EFA_FAO_Pitch_Deck.md`, October 19), the EAB proposal PDF, and Richmond's public ABA 509 files (`aba-509-saas/data/`, 2021 to 2025).
**Conventions:** severity and confidence as in `CLAUDE.md`. **Shown** = read in the files or computed; **Suspected** = reasoned. Section references (§) are to methodology v2.6 unless stated.

---

## 1. Verdict

**Not ready for sign-off. Revise before S2 to S5 build on it.**

The generic layer (FR groups 4.1 to 4.10, NFRs, section 7) mostly restates methodology v2.6 faithfully. It is usable after targeted fixes: about a dozen wrong acceptance pointers and several missing FRs. The Richmond layer (sections 3, 5, 8 and 10) and the traceability matrix need material revision. The problems have three root causes:

1. **The call answers were taken at face value.** They were not reconciled with each other or with Richmond's public 509 record. The "hard seat cap" sits against classes of 121 to 146 over five years. "9 full rides and 9 full-pay" sits against about 40 students per class at or above full tuition. The award redesign is dated to 2025, but it is planned for this cycle.
2. **Richmond's situation falls outside what the methodology represents, and S1 did not flag it.** Richmond is redesigning its own awards this cycle, raising tuition about 5%, holding a hard cap, and wants to target geography. The methodology has no concept of a client-led policy change, a waitlist-filled hard cap, or evaluating a client's own proposed grid. S1 wrote stories as if the methodology covered these. Story 7, for example, promises a redistribution that the 5%-of-tuition guardrail would block.
3. **The process skipped its controls.** The handoff called for the strongest model and plan mode for Phase B, the EAB proposal and the current pitch as inputs, and Jason's sign-off. The session used Sonnet 4.6, did not use the EAB proposal, did not verify the pitch, and ticked four of the five "done" boxes itself. Two of the four ticks are false.

S1 does several things right. It flags that no final screen verdict can be stated before the production run (CONTR-01). It keeps the consumer ZIP layer gated and out of the Richmond MVP. It carries the audit edits E1, E3 to E13 into FRs correctly. It applies the blinding answer to the estimator choice (FR-43).

## 2. Process audit

| Handoff requirement (§4 to §5 of the handoff) | What happened | Assessment |
|---|---|---|
| Phase B on the strongest model, in plan mode, outline approved first | Sonnet 4.6 (commit `350da38` co-author line). No record of an approved outline in the repo or in S1 | Deviation (Shown for the model; plan mode not verifiable, ask) |
| Phase A checkpoint, then Phase B | One commit bundles Phase A, the v2.6 adoption, the S2b data request draft and S1. Phase A cannot be reviewed or reverted on its own | Medium. Future steps: one commit per step |
| Inputs include the current pitch copy and the EAB proposal | EAB proposal not referenced anywhere in S1. Pitch not checked (left as OD-03) | Deviation (Shown) |
| About 5,000 to 7,000 words | About 11,800 words. Requirement text is repeated across the FR table, stories and matrix | Low. Length hides the Richmond issues |
| "S1 is done when … Jason signs off" | Four boxes ticked by Claude. "Every Critical and High finding maps" is false: F11 is unmapped, and F6 and F8 map only to tangential FRs (S1A-16). "Evidence-state table matches the pitch" is false (S1A-24) | Medium. A self-certified gate is not a gate |
| Flag contradictions, do not resolve them | Five CONTR items were flagged. CONTR-02's reasoning is wrong, and the four largest contradictions are missing (S1A-01 to S1A-04) | High |

## 3. Findings

### 3.1 Call interpretation and Richmond facts

| ID | Sev | Conf | Evidence | Finding | Direction |
|---|---|---|---|---|---|
| S1A-01 | **Critical** | Medium | Shown: Q2; S1 OD-01, §8, Story 2. Suspected: whether fall 2027 offers already use the new model | **The barbell-to-even change is misdated, and its consequence is missed.** Q2 says the barbell held "last year (2025 admit cycle)" and that Richmond "wants to move away" from it. The change is prospective, possibly already live in offers released since September. S1 calls it "the 2025 … policy change" and treats it as a historical evidence source. If it is live, three things follow. (a) The empirical status-quo grid (§5, FR-02) is the old barbell, which no longer "matches practice," so the client confirmation in FR-02 cannot be given as specified. (b) The policy change has no post-period. It can serve as evidence for the 2028 cycle at the earliest, after the fall 2027 census. (c) It is confounded with the +5% tuition move and the Grad PLUS closure of July 1, 2026 (§8). The Grad PLUS closure hits hardest the bottom-quartile, full-pay students, the same band that gains most under the redesign | Ask Richmond: are this cycle's offers already on the new model, and from what date? Define two references in S1: the *historical* grid (evidence and equity baseline) and the *client's planned* grid (this cycle). Raise the definition as a methodology decision (D1). Rewrite OD-01: earliest usable post-period, the confounds, and the design that could survive them (band-level difference-in-differences with dose varying by band, controlling for prior PLUS reliance). Require the new policy to be logged in `policy_changes` with effective dates and awards by cell, so it becomes evidence next cycle |
| S1A-02 | High | High | Shown: Q2 "Yes, but I don't have it now"; S1 §3, §10.1 | **The existing scholarship grid is not chased, and the strongest anchor route is underweighted.** Richmond said a published or index-based grid exists. The barbell itself sets full tuition above one position cut and $0 below another, so jumps far exceed the 3%-of-tuition minimum (§4, evidence audit). Those cuts are the best candidate discontinuities. They qualify only if they sit on a fixed running variable, not on each year's quartiles, and pass density and placebo checks. S1's §3 "Anchor available" row names only the policy change, and no open question asks for the grid | Add an OQ: obtain the grid, its running variable, cut points, award amounts and effective dates for five cycles. Name the barbell cut points as a candidate threshold source in §3 and FR-22's Richmond note. Note the limit: an estimate at a $0-to-full-tuition jump is local and far outside the guardrail-sized moves the grid would make |
| S1A-03 | High | High | Shown: 509 first-year class 145, 121, 134, 133, 146 (2021 to 2025); Q6 | **"Hard seat cap, fill to 100%" contradicts the record and is not representable.** Richmond's class ranged −11% to +7% around its five-year mean of 136. "Hard cap" likely means a hard ceiling with the target met by the waitlist. That differs from the symmetric expected band in §5 (law default ±3%). It also changes the objective: under waitlist backfill, an induced enrollee displaces a waitlist admit, so the marginal revenue is the difference between the two students' net tuition, not the full net tuition. S1 maps "hard cap" to "±3% or tighter" (Story 3, §8) and asks only for a number (OQ-01) | Reframe OQ-01: ceiling and floor separately; whether the waitlist fills the class; how far below target they have accepted (history says about 11%). Add CONTR-06: §5 and the screen have no hard-cap-with-backfill representation (methodology decision D3). Keep "Not recommended" as the working assumption, but mark it **Suspected** for an asymmetric band: the audit showed the verdict turns on the band (audit A3) |
| S1A-04 | Medium | High | Shown: 509 grant data (2024-25: 101 full plus 7 above full of 392 students; 73 without a grant); Q2 | **"9 full rides and 9 full-pay" contradicts both the 509 data and the call's own "quartile" description.** The 509 implies about 40 students per entering class at or above full tuition and about 27 with no grant. Top and bottom quartiles of a class of 146 are about 36 each. Unless "9" means something else (full tuition plus living costs, or a sub-group), the status-quo grid and the size of the redesign are misstated | Add an OQ to reconcile; do not size any change from "9 and 9" |
| S1A-05 | Medium | Medium | Shown: Q12 ("wouldn't likely approve less than state-level targeting; I suggested perhaps MSA level") | **The dean's geographic position is overstated.** S1 says Richmond "confirmed state and MSA level" (§8, Story 6, alignment-gate item 3). The dean signalled state level. MSA was Jason's suggestion | Record state as confirmed and MSA as proposed, pending the dean |
| S1A-06 | Low | High | Shown: Q7 "Enrollment would own this"; S1 §2 note | S1 says the aid office owns the extract. Q7 says Enrollment does. Q12 (counsel reviews aid policy) is not carried into the Richmond alignment-gate steps | Correct the owner. Add counsel review to Richmond's gate sequence (FR-49 note, §8) |
| S1A-07 | Medium | High | Shown: Q13 "Yes, and it's fixed"; Q2 "discount rate static" | **CONTR-02's reasoning is wrong.** S1 says adding geographic bonus aid "requires cutting aid elsewhere." At a static discount rate with tuition up about 5%, the aid pool grows about 5%. That is roughly $0.2M for an entering class and about $0.6M across all classes (estimate from audit A25's average grant). It funds targeted bonuses without cuts, unless fixed-dollar renewals or a fixed-dollar budget absorb it. The real question is which of two binding rules applies: a discount *rate* (scales with tuition) or a dollar *budget* (Q13 says fixed). They conflict | Rewrite CONTR-02 as: discount-rate target versus fixed-dollar budget, with the entering-class versus all-class definition and the horizon (Q13). One of them is the constraint; the other is reported |

### 3.2 Methodology gaps S1 should have flagged

| ID | Sev | Conf | Evidence | Finding | Direction |
|---|---|---|---|---|---|
| S1A-08 | **High** | High | Shown: Q1, Q2; EAB proposal, "Live Simulation" and "2026-2027 Deliverables" slides ("Live Simulation … quantify the impact of pricing & award changes"; "Fall 2027 Scholarship Simulation Modeling"); §1 law profile, §5 weak-evidence state | **Nothing in S1 evaluates the client's own proposed policy.** Richmond's real needs this cycle are its own redesign, geographic bonuses and a +5% tuition move. In the no-anchor state S1 can only return the old status-quo grid (FR-27, Story 7). The competing EAB proposal sells exactly this what-if simulation. The methodology forbids Frankel *recommending* level changes without evidence. It is silent on *scoring a client-proposed policy* under honest bounds | Add as a methodology decision (D2), not a silent FR. If adopted: a scenario mode that scores a client grid at b = 0 and at the prior's 90th percentile, never at a point estimate. Output class, net tuition revenue, discount rate, position mix, the equity audit and the proxy screen. Label it "prior-based, not evidence-based; not a recommendation" |
| S1A-09 | **High** | High | Shown: §5 guardrail (5% of tuition ≈ $2,885 per cell per cycle); Story 7; FR-33 | **Story 7 promises a redistribution the methodology blocks.** Moving a full-tuition top cell toward the middle takes years at $2,885 per cycle. Floors (Appendix C) add further limits. Story 7 says the optimizer "reallocates within the floors and guardrails" as though that delivers Richmond's goal | Raise D4: the guardrail binds Frankel-recommended cuts, not client-directed changes. Client changes are logged and acknowledged at the alignment gate. Rewrite Story 7 accordingly |
| S1A-10 | High | High | Shown: §5 increases-only (0 ≤ Δ ≤ tested dose; revenue at b_L); §4 support ("with no anchor, no level changes are allowed"); Story 4 | **Story 4 (mid-cycle increases-only) cannot run for Richmond.** With no anchor there is no b_L or b_H and no tested dose. The handoff's risk note also listed this analysis as a likely this-cycle item; both were wrong | Make Story 4 conditional on an anchor. Add a no-anchor story instead: a mid-cycle budget and class tracker for client-initiated revisions and appeals, at status-quo response (b = 0) with reason codes. It is descriptive, uses the §5 three-group accounting, and contains no price response |
| S1A-11 | Medium | High | Shown: §5 cells (law: position 5 × market 2, optionally × need 2; market tier up to 5 levels); S1 CONTR-04, FR-29 | **Geography and need cannot both fit Richmond's 21-cell cap.** S1 confirms 20 cells (position 5 × need 2 × market 2). Market 2 (home state or other) cannot express state or MSA targets. Three market tiers with need give 30 cells. Even 20 cells average about 32 admits each, so uneven bands push cells under 30 and trigger merges (Suspected) | Raise D5 (grid shape for Richmond). Options: position 5 × market 3 = 15; or position 3 × need 2 × market 3 = 18. Choose on how much need actually drives Richmond's awards (Q3 says only "yes") |
| S1A-12 | Medium | High | Shown: §5 tuition scenarios ("within the evidence only if the change is no larger than the tested dose"); Q2 tuition +5% | The +5% tuition move is not modeled anywhere in S1 (no FR covers tuition scenarios). With no anchor and no tested dose it is outside the evidence. Richmond's revenue goals depend on it | Add an FR for tuition scenarios with the evidence limit. State in §8 that the revenue effect of the tuition move cannot be estimated this cycle |

### 3.3 Missing or incomplete requirements

| ID | Sev | Conf | Evidence | Finding | Direction |
|---|---|---|---|---|---|
| S1A-13 | High | High | Shown: grep of S1; §4 response model; §5 policy grid scope; §10 | **Core methods have no FR.** Missing items: forecast recalibration (logit p\* = α + γ logit f; "unstable" label if γ is outside [0.8, 1.2]); the cell reference award r_c and the response model; holdout acceptance; cell yield shrinkage (cells under 30 admits, prior weight 30); pool projection and the three refresh dates; excluded groups and stipends above tuition; confound diagnostics (§10); fair baselines and "if the grid fails, the winning heuristic becomes the recommendation" (§10); the Monte Carlo release gate (the S9 link) | Add FRs in 4.5 and 4.6. Map them to F6, F8, F9, F11, R7, R8 and R9 |
| S1A-14 | Medium | High | Shown: pitch ("Federal loan-limit exposure (Tier 1)"); §8; data request v3 PLUS fields; S1 FR-57 (M1), §8 table | **Loan-cap exposure is missing from Richmond's MVP.** Grad PLUS closed to new borrowers on July 1, 2026 (§8). It is the largest change in law financing this cycle, and the pitch promises it at Tier 1 | Add it as a Richmond MVP deliverable (descriptive), with PLUS fields required in FR-05 |
| S1A-15 | Medium | High | Shown: §11 deferred items (mechanism tests; one-year bonus); FR-27 | The evidence plan for a no-anchor client has no required content. For Richmond (hard cap; randomization appetite "perhaps") it should name the cheaper routes: a deposit-deadline or award-timing test, and a one-year bonus | Specify the evidence plan's contents in FR-27: sources examined, why each failed, the next-cycle routes with cost, and the logging needed now (`policy_changes`, reason codes) |
| S1A-16 | Medium | High | Shown: FR-05; data dictionary v3 (`capacity_type`, `discount_rate_target`, `discretionary_budget`, waitlist dates, need fields, PLUS fields, `grid_effective_dates`); roadmap S2b status | FR-05 mixes scoping answers (capacity band, blinding) with data fields. It omits need, PLUS, waitlist, grid history and capacity type, all of which the v3 dictionary already has. It is also marked executable "before any analysis," while v3 is a draft pending S2 and S2b sign-off and the engagement may be unsigned (OD-02) | Point FR-05 at the v3 dictionary as the field source of truth and list only the law-critical fields. Move scoping answers to FR-01, which also needs capacity type and the discount and budget definitions. State the sequencing: S2b sign-off and engagement signed, then the request is sent |
| S1A-17 | Medium | High | Shown: FR-16 (MVP; "reason code present on every revision row"); Q9 ("I will need to find out") | Historical revisions will not carry reason codes, so FR-16's acceptance fails on Tier 1 history | Split FR-16: prospective logging (required) and historical revisions flagged "uncoded" and excluded from price estimation |

### 3.4 FR accuracy and acceptance pointers

| ID | Sev | Conf | Evidence | Finding | Direction |
|---|---|---|---|---|---|
| S1A-18 | Medium | High | Shown: §3 data tiers ("Tier 1 … supports … a discontinuity-only price anchor"); §5 weak-evidence trigger; S1 §3 table | Two contradictions with the methodology, both unflagged. (a) "Anchor available" is mapped to Tier 2, but Tier 1 supports a discontinuity anchor. (b) The weak-evidence state adds "or the anchor straddles β\*" as a trigger. The methodology triggers it only on q10 ≤ 0 or no anchor; straddling β\* is a W8 pass check | Correct both. If straddling β\* should be a trigger, raise it as a methodology question |
| S1A-19 | Medium | High | Shown: Verification Report §1 (test 5 = budget cap and athletes); §10 world list | Wrong or nonexistent acceptance pointers. FR-33 cites "guardrail test 5," which tests budget and athletes, not the 5% guardrail. FR-38 cites "planted-proxy seeds," but no such world exists. FR-23's acceptance (matches the stylized worked example) conflicts with its own text (must run on the production optimizer with a 509-calibrated pool). FR-32 uses a Richmond estimate ("about 15%") as an acceptance test | FR-33: a new guardrail unit test. FR-38: add a proxy world to S9, or use a fixture. FR-23: two checks, (i) the production code reproduces the worked example on the stylized fixture, (ii) the verdict is reported for the 509-calibrated pool. FR-32: buffer equals the formula on a fixture |
| S1A-20 | Low | High | Shown: FR-34, Story 7; Appendix C | The "Pell-eligible" floor is copied into the law profile, but JD students are not Pell-eligible | Law floor: highest-need band only |
| S1A-21 | Medium | High | Shown: roadmap §1 (roles `enrollment_team`, `leadership`, `analyst`) and §5 (dashboard v1 = views 2, 3, 5); S1 §2, FR-57, FR-61, OD-07 | The new `aid_office` role has view 3 access, but FR-61's row-level security covers three roles only. OD-07 recommends views 1, 4 and 5 first for Richmond, yet FR-57 (view 4) is M1 while views 2 and 3 are MVP | Either add `aid_office` to row-level security or deliver its access by export. Align priorities with OD-07: views 1, 4 and 5 are MVP for a no-anchor client; views 2 and 3 follow an anchor |
| S1A-22 | Low | High | Shown: FR-35; Q6 | The headcount-maximizing scenario is meaningless under a hard cap | Suppress it when capacity type is "hard cap"; report why |

### 3.5 Traceability matrix

| ID | Sev | Conf | Evidence | Finding | Direction |
|---|---|---|---|---|---|
| S1A-23 | **High** | High | Shown: Appendix B (R1 to R12, F1 to F20); S1 §9 | **The matrix is unreliable as a backbone for S3 and S9.** 16 of the 22 R-code citations do not match Appendix B (only FR-28/R10, FR-32/R4, FR-34/R1, FR-35/R11, FR-48/R3 and FR-55/R5 do). Examples: R12 (asymmetric response to cuts) cited for suppression, the dashboard and the secure channel; R11 (class floor) cited for protected attributes; R2 cited for pacing; R9 cited for the inquiry logit. F19 (a "four cohorts" typo) is cited for the randomization log (FR-42). F17 (stale equity audit) is cited for the proxy screen (FR-38). O3 (uncorrected gains) is cited for the evidence audit (FR-22). F11 (Monte Carlo gate, High) maps to nothing. F6 maps only to FR-02 (client confirmation) and F8 only to FR-48 (backtest diagnostic), neither of which implements the fix | Rebuild the matrix from Appendix B and the audit table. Add a mechanical check: a short script that parses every F, A, R, O and E code in S1 and confirms it exists and that its finding text matches the FR's topic. Re-test the "every Critical and High finding maps" criterion against the corrected matrix |

### 3.6 Stories, MVP, timeline and pitch

| ID | Sev | Conf | Evidence | Finding | Direction |
|---|---|---|---|---|---|
| S1A-24 | Medium | High | Shown: pitch §§3 to 7 (Tier 1 price estimate "from your award rules"; 75-cell grid; $3,000 guardrail; arms $0/$2,000/$4,000; "Phase 2: 4–6 weeks"; "no full ZIP codes"; "no consumer credit data"); S1 "done" box 4 | **The evidence-state table does not match the pitch, and S1 ticked the box anyway.** The pitch promises an optimized grid on a fixed timeline. S1 (correctly) says no anchor means no grid | List each mismatch as a pitch edit, not an S1 caveat. Untick the box until the pitch is revised |
| S1A-25 | High | High | Shown: S1 §8 (no dates); `CLAUDE.md` (no coding until S3, S4, S5 and S9 sign-off); §7 monitoring "[to build]"; Q10 (offers from about September) | **The Richmond timeline has no dates and no production path.** Every "this cycle: Yes" deliverable needs code the decision log says cannot be written yet. Monitoring is "[to build]" and yield season runs roughly January to May. S1 does not say how the funnel, pacing, the 509 view and the evidence audit get produced in time. Existing assets could cover part of it: the v2 build's EFA tables, and the `aba-509-saas` dashboard for the 509 view | Add a dated timeline (data request sent, data received, interim deliverables, census). Raise D6: an interim analyst-run path for this cycle's descriptive deliverables, labeled interim, or an explicit exception to the coding freeze. Confirm the law timeline offsets from `GAP_LOG.md` ("S1 should confirm"; S1 deferred them as OD-04) |
| S1A-26 | Medium | High | Shown: handoff §4 item 5; S1 §5 | Story coverage is thin where Richmond's work actually is. There is no weak-evidence story distinct from no-anchor: Story 2 is no-anchor, titled "evidence too weak." The analyst has no story for intake QA, the evidence audit or publication. The aid director's only story (Story 4) is infeasible. Stories 5 and 6 assume a test or an optimizer that Richmond will not have this cycle, without saying so | Add stories: weak evidence (anchor with q10 ≤ 0); analyst intake to evidence audit to alignment gate; aid director applying the documented grid and logging revisions; scoring of the client's own proposal (if D2 is adopted). Label stories 5 and 6 conditional |

## 4. Check of the session report (screenshots)

**"Five substantive changes"**

| Claim | Audit | Note |
|---|---|---|
| 1. Primary estimator test-only | Right direction, overstated | Q8 was tentative ("I don't think…"). Keep it as an assumption pending OQ-12. It is moot unless a test runs, and the screen points to Not recommended |
| 2. Geography at state/MSA; ZIP3 sufficient | Partly wrong | The dean signalled state; MSA was proposed (S1A-05). ZIP3 is blocked as a grid dimension or target (§5 whitelist). State and CBSA come from the client-side derivation script (§2) |
| 3. Need is a grid dimension; 20 cells within the cap | Arithmetic right, conclusion incomplete | Leaves no room for the geographic objective (S1A-11). How need enters awards is unconfirmed |
| 4. Galaxkey confirmed; FR-05 can proceed immediately | Half right | The channel is fine. The request itself is a draft pending S2 and S2b sign-off, and the engagement may be unsigned (S1A-16) |
| 5. Barbell-to-even as the 2025 policy change | Wrong | Prospective, confounded, and it reshapes the status-quo definition (S1A-01). The barbell's cut points are the better anchor candidate (S1A-02) |

**Contradictions CONTR-01 to CONTR-05**

| Item | Audit |
|---|---|
| CONTR-01 Screen verdict before production run | Correct. Add the asymmetric-band caveat (S1A-03) |
| CONTR-02 Discount rate versus redistribution | Reasoning wrong (S1A-07) |
| CONTR-03 ZIP3 versus consumer ZIP add-on | Correct |
| CONTR-04 Need as a grid dimension | Incomplete (S1A-11) |
| CONTR-05 Tuition +5% and renewal rule | Correct as far as it goes. Add that the tuition move is itself a price change, outside the evidence (S1A-12), and a confound for the policy-change source (S1A-01) |
| **Missing** | CONTR-06 hard cap with waitlist (S1A-03); CONTR-07 guardrail versus client-directed redesign (S1A-09); CONTR-08 status-quo grid during a client-led change (S1A-01); CONTR-09 no evaluation of client proposals in the no-anchor state (S1A-08); CONTR-10 Tier 1 can anchor (S1A-18) |

**Open questions.** OQ-01 to OQ-12 are reasonable, but several are mis-framed and six are missing. Reframe OQ-01 (S1A-03). Add:
- Are this cycle's offers already on the new model, and since when?
- Obtain the existing grid with effective dates.
- Reconcile "9 and 9" with the 509 data.
- State or MSA: the dean's actual limit.
- Discount rate versus fixed budget: definition and horizon.
- What Richmond means by "bonus aid" (to keep it distinct from the price test's bonus arm).

## 5. Decisions needed from Jason before the re-draft

S1 should record these as open decisions. It should not resolve them. Each needs a methodology edit (v2.7 or S5) and a short audit.

| # | Decision | Recommendation | Judgment call: what would change it |
|---|---|---|---|
| D1 | Status-quo grid while a client changes its own policy | Two references: the *historical* empirical grid (evidence, equity baseline, backtest) and the *client planned* grid (this cycle's guardrail, floors and budget), the second once logged in `policy_changes` and acknowledged at the gate | If Richmond's fall 2027 offers are still on the barbell, one reference suffices this cycle |
| D2 | Scoring a client-proposed policy in the no-anchor state | Allow it as a labeled scenario mode, scored at b = 0 and at the prior's 90th percentile, with the equity audit and proxy screen; never a recommendation. It answers the EAB simulation offer without breaking "no level change without evidence" | Counsel or Jason judging that any prior-based number will be read as a recommendation |
| D3 | Hard cap with waitlist backfill | Asymmetric band (hard ceiling, soft floor). Marginal value of an induced enrollee = net tuition minus that of the displaced waitlist admit. Add a W0L variant to S9 | Richmond confirming a symmetric tolerance band |
| D4 | Guardrail versus client-directed change | The guardrail and floors bind Frankel's recommended cuts. Client-directed changes are logged and acknowledged at the alignment gate | None expected; this restates the guardrail's purpose (§5) |
| D5 | Richmond grid shape | Position 5 × market 3 (Virginia, target states, other) = 15 cells. Need added only if the status-quo grid shows need moves awards | Need-based awards being material in Richmond's data |
| D6 | Production path for this cycle's descriptive deliverables | Analyst-run interim deliverables from the v2 EFA code paths and `aba-509-saas`, labeled interim; or a scoped exception to the coding freeze | Richmond's timeline slipping to the 2028 cycle |

## 6. Revision directions for S1 (v1.1)

Order matters: Richmond follow-up first, then D1 to D6, then the re-draft. Use Opus in plan mode, with the outline of changes approved before editing.

| Section | Edit |
|---|---|
| Header | Status "Draft v1.1, pending Jason". Remove the self-ticked boxes. Change "awaiting sign-off" to name the open decisions |
| §2 Roles | Fix the extract owner (Q7). Resolve the `aid_office` access path (S1A-21). Add counsel to Richmond's gate (Q12) |
| §3 Evidence states | Correct the Tier mapping and the weak-evidence trigger (S1A-18). Richmond column: name the barbell cut points as the first anchor candidate (S1A-02); the redesign as next-cycle evidence only (S1A-01); add a row or note for client-proposal scoring if D2 is adopted |
| §4.1 | FR-01: add capacity type, ceiling and floor separately, the discount-rate versus budget definition, and the tuition plan. FR-05: point at the v3 dictionary; law-critical fields (need, PLUS, waitlist, grid history); sequencing (S1A-16) |
| §4.3 | Split FR-16 (S1A-17). FR-17 stays M1 and is conditional on an anchor. Add the no-anchor revision tracker (S1A-10) |
| §4.5 | Add FRs: recalibration, r_c and the response model, cell shrinkage, confound diagnostics. FR-23: two-part acceptance. FR-27: evidence-plan contents (S1A-15). FR-22: Richmond note on threshold candidates |
| §4.6 | Add FRs: pool projection, excluded groups and stipends, tuition scenarios with the evidence limit (S1A-12), fair baselines with heuristic fallback. FR-29: shape per D5. FR-33 and FR-38: fix pointers. FR-34: law floor. FR-35: suppress headcount-max under a hard cap |
| §4.9 | Align view priorities with OD-07 (S1A-21). Make loan-cap exposure MVP for law (S1A-14) |
| §5 Stories | Rewrite 2 (status quo per D1), 3 (asymmetric band), 4 (conditional), 6 (conditional; state confirmed, MSA proposed) and 7 (per D4). Add the four stories in S1A-26 |
| §8 MVP | Dated timeline. Production path per D6. Add loan-cap exposure. Remove "assumes Tier 1 in four to six weeks" unless tied to S2b sign-off and a signed engagement |
| §9 Matrix | Rebuild and machine-check (S1A-23) |
| §10 | Reframe OQ-01. Add the six missing OQs (section 4 above), CONTR-06 to CONTR-10, and D1 to D6 as open decisions. Rewrite CONTR-02 |
| Length | Target 7,000 to 8,000 words. Cut repetition between the FR rows, the stories and the matrix; the stories should cite FR IDs rather than restate them |

**Acceptance for v1.1:**
- the matrix check script passes;
- every Critical and High finding from the review, the audit and this document maps to an FR whose text implements the fix;
- every Richmond statement cites the capture-sheet question or 509 field it rests on;
- every story that needs an anchor, a test or D2 is labeled conditional;
- Jason ticks the boxes.

## 7. What I could not verify

- Whether plan mode was used and an outline approved (no record in the repo).
- Which pitch copy is current. I checked the folder copy (October 19), which may be stale.
- Whether Richmond's fall 2027 offers already reflect the new award model. This decides how severe S1A-01 is.
- What "9 full rides and 9 full-pay" refers to.
- Whether the barbell cut points sit on a fixed running variable (needed for S1A-02).
- The thin-cell effect at 20 cells (S1A-11) and the waitlist displacement effect (S1A-03). Both are reasoned, not computed; a W0L variant would show them.
- The aid-pool growth figure in S1A-07 is an estimate from 509 averages, not Richmond's budget.
