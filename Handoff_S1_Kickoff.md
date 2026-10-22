# Handoff: S1 Kickoff (Requirements and User Stories)

**Prepared:** October 22, 2026, from a Cowork session
**Recommended executor:** Claude Code, opened in `/Users/jasoncohen/projects/EFA_FAO`
**Owner and sign-off:** Jason Cohen
**First client:** University of Richmond School of Law (discovery call held October 22; answers in `Richmond_Call_Capture_Sheet.md`)

## 1. Where things stand

| Item | State |
|---|---|
| Methodology | `02_methodology_v2.5.md`: draft that merges the 24 review edits (S4-1 to S4-14, S5-1 to S5-10). **It predates the audit, so audit edits E1 to E14 are not yet applied** |
| Re-review | `S4_S5_Rereview_v2.4.md` (Opus 5.5). Several claims are superseded by the audit; see the errata list in Phase A |
| Audit | `Audit_S4_S5_Rereview_v2.4.md` (Fable 5.1): **holds with minor revisions**. Both Critical findings stand. 14 required edits in its section 4; support scripts in `audit_support_v2.4/` |
| Support scripts | `review_support_v2.4/` and `audit_support_v2.4/`. They ran in a sandbox without scipy, using `stub/` and a Lagrangian knapsack solver in place of HiGHS. **Never run against the repo's real solver** |
| Executive read, roadmap | Still v2.4 (stale; see Phase A, step 4) |
| Data request | Still v2.3 and undergraduate-shaped (`efa_fao/docs/04_data_request_v2.md`; one law mention). No law Tier 1 request exists |
| Pitch materials | `Pitch and pricing decks/` files show last-modified dates of October 19 to 21 and `EFA_FAO_Pitch_Deck.md` still says "Phase 2: 4–6 weeks". Jason says they were updated; **confirm which copy is current** |
| Code | `efa_fao/`: the v2 build (per-student optimizer, bootstrap). Not a git repository. The "7 guardrail tests passing" claim has never been verified by a reviewer |
| Decision log | "Coding in this phase: none; advisory and specification only" (Jason). Build starts after S3, S4, S5 and S9 are signed off |

## 2. Why Claude Code for this step

- **Same folder, no translation layer.** It reads and writes the spec files and the repo directly, and runs the tests on Jason's machine with the real scientific stack. The Cowork sandbox lacked scipy and scikit-learn, which forced the stubs.
- **Continuity into S2, S3 and S6.** The data contract, typed interfaces and schema are code-adjacent. A repo with git history and a `CLAUDE.md` lets later steps check specs against code.
- **Leaner context.** Cowork carries a very large tool surface in every turn. I cannot see Jason's billing, so this is a structural judgment, not a measured saving.
- **Keep Cowork for** client-facing and business work: the Richmond follow-up email, pitch and pricing decks, any docx or pptx deliverables, and connector tasks (mail, Slack, Drive).

**Suggested model use.** Phase A is mechanical (applying listed edits): a mid-tier model is enough. Phase B (S1 requirements and traceability) needs judgment: use the strongest model, and use plan mode so the outline is approved before the full draft is written.

## 3. Phase A: housekeeping (stop at the checkpoint)

Do not modify anything under `efa_fao/src/`. This phase is repo setup, verification and document edits.

**A1. Repo baseline**
1. `git init` in the EFA_FAO folder. Add a `.gitignore` for `.DS_Store`, `__pycache__/`, `efa_fao/data/synthetic/*.csv` (regenerable) and `efa_fao/outputs/`.
2. Commit the current state as the baseline, with a message stating that the audit edits are not yet applied.

**A2. Verify what was never verified**
1. Create a Python 3.12 environment (per the roadmap stack). Install numpy, scipy, pandas, statsmodels, scikit-learn, pyyaml and pytest.
2. Run `efa_fao/tests/test_guardrails.py`. Report pass or fail for each of the seven tests.
3. Regenerate the synthetic data and run the v2 pipeline (`README.md` in `efa_fao/` has the commands; about 2 minutes). Confirm the outputs reproduce the quoted numbers (anchor, backtest, recovery table).
4. Re-run `review_support_v2.4/bt.py` and the audit's `voi5.py` and `run_task1.py` with the **real** scipy and HiGHS in place of `stub/` and `lagr.py`. The scripts' paths point at a scratch copy under `/tmp/work`; adjust them. Report any difference above 1% in: the backtest gain, the Richmond worked-example table, and the task 1 verdict grid. This closes the audit's "could not run HiGHS" item.
5. Write the results to `Verification_Report_Oct22.md`. Do not fix failures here; report them.

**A3. Apply the audit edits**
1. Apply E1 to E14 from section 4 of `Audit_S4_S5_Rereview_v2.4.md` to `02_methodology_v2.5.md`. Judgment points: E1 (primary estimator conditional on blinding), E4 to E7 (screen logic and wording), E8 (median constraint).
2. Remove "draft pending the audit" from the status line. Mark the open items A1 to A5 in section 13 as closed, with the audit's result for each.
3. Update Appendix B rows for F3, F7, F13 and F18 to match the audit.
4. Append an addendum to `CHANGELOG_v2.5.md` listing E1 to E14.
5. Add an **errata block** at the top of `S4_S5_Rereview_v2.4.md` (do not rewrite the review). Superseded claims, each pointing to its audit finding:
   - the "+6% estimand bias" and "SE 0.44 to 0.29 (34%)" claims (A20, A21);
   - "a median target could turn the test verdict positive" (A4);
   - the ±10% class-band statement (A3);
   - "conditional-scholarship counts lag two years" (A16);
   - the rank-matching illustration values (A18);
   - the buffer of "about 12%" (A29);
   - the §8 median constraint with the 1.645σ margin (A30);
   - "perfect knowledge is worth less than one cycle" without the prior qualifier (A32).

**A4. Bring the other documents to v2.5**
Edit surgically; do not rewrite the narrative.
- **`01_executive_read_v2.4.md` → v2.5.** Update: the price-test section (cost with the commitment multiplier; the value-of-information screen replaces the 2.3-point rule); the proof-of-value caveats; the decisions table (screen rule decided; two-sided rule; award mode and horizon); "What this does not prove" (add the audit's fragilities); the closing "Still open" list.
- **`03_technical_roadmap_v2.4.md` → v2.5.** Update: the S4 and S5 status rows; section 6 items 11, 14 and 18 to 20; section 9 (open questions); the decision log (screen replaced, two-sided rule, award mode, horizon equals commitment, audit completed). Record the audit in a short review log. Replace "Opus re-review pending" with the completed state.
- **Data request.** Do not rewrite it now. List its law gaps in `Verification_Report_Oct22.md`: LSAT/UGPA and position fields, offer dates and package versions, reason codes on revisions, renewal rule, capacity band, and a blinding question.

**A5. `CLAUDE.md`**
Create `CLAUDE.md` in the folder. Keep it under 80 lines. Contents:
- what the project is and the file map (methodology, review, audit, support scripts, `efa_fao/`);
- the version and tag conventions ([v2.x], S4-n, F-n, A-n);
- the rules: synthetic and public data only; no real client data; closed decisions stay closed (third-party timing data, per-student optimization, grid-tier price estimation); protected attributes never enter models; no consumer credit data;
- commands to run the tests and the pipeline;
- the decision log entry that coding starts after S3, S4, S5 and S9 are signed off;
- the writing conventions: concise, no emojis.

**Checkpoint.** Stop and report to Jason: test results, any divergence from the stubbed numbers, the edits applied, anything in the audit edits that did not fit the text. Phase B starts when Jason confirms and `Richmond_Call_Capture_Sheet.md` is filled in. If Jason chooses to proceed without the call answers, record every dependent item as a labeled assumption in S1 section 10.

## 4. Phase B: S1, Requirements and user stories

**Inputs:** `02_methodology_v2.5.md` (merged), `01_executive_read` and `03_technical_roadmap` (v2.5), `Audit_S4_S5_Rereview_v2.4.md`, `S4_S5_Rereview_v2.4.md` (with errata), `Richmond_Call_Capture_Sheet.md`, the Pitch deck (current copy), the EAB proposal PDF (for what the client is comparing against).

**Output:** `S1_Requirements_and_User_Stories.md`. About 5,000 to 7,000 words. Plan mode first: produce the outline and the list of open decisions, get Jason's approval, then write.

**Required structure**

1. **Purpose, scope, and how to read it.** One page. Defines the traceability tags.
2. **Users and roles.** Enrollment team, leadership, aid office, alignment-gate approver, and the internal Frankel analyst. Map to the planned roles (`enrollment_team`, `leadership`, `analyst`) and say what each can see.
3. **Evidence states and deliverables.** The backbone of the document. A table of states and what the client receives in each:
   - **No anchor:** EFA, monitoring, the 509 market view, the evidence audit, and the documented status-quo grid. No optimized grid.
   - **Weak evidence** (q10 ≤ 0): the same, plus the evidence-too-weak state and the screen's plan.
   - **Anchor available:** the optimized grid under the two-sided rule.
   - **Test running:** the above, plus test operations and compliance reporting.

   Also map each state to Tier 1 and Tier 2 data, and to the Richmond MVP.
4. **Functional requirements.** Restore the FR table (see the open decision). Groups:
   - intake and scoping inputs;
   - EFA funnel;
   - monitoring;
   - ABA 509 market layer;
   - evidence audit and value-of-information screen;
   - FAO grid and scenarios;
   - price-test operations;
   - governance (alignment gate, equity audit);
   - delivery (dashboard views, secure-channel exports);
   - add-ons (batch scoring).

   Each row: ID (FR-n), requirement (at most two lines), priority (MVP, M1, M2, deferred), source (methodology section), and acceptance pointer.
5. **User stories for Richmond.** Concrete stories with Given/When/Then acceptance for the enrollment dean, aid office director and Frankel analyst. Include the weak-evidence and no-anchor stories, the mid-cycle increases-only story, and the story where the client's capacity band changes the screen verdict.
6. **Non-functional requirements.**
   - privacy: suppression below 10, aggregates only to Supabase, student-level data only through the secure channel;
   - lineage and reproducibility;
   - explainability (every number carries a range or a stated reason it has none);
   - runtime budgets;
   - the equity audit before any publication.
7. **Out of scope, closed and deferred.** From methodology sections 11 and 14, plus any Richmond-specific exclusions.
8. **Richmond MVP and timeline.** What can be delivered this cycle given where offers stand (Capture Sheet Q10), what waits for the next cycle, and what the alignment gate requires.
9. **Traceability matrix.** Each FR maps to its methodology section, the review or audit finding it answers, and the test (a unit test, a Monte Carlo world, or an acceptance fixture) that will check it.
10. **Open decisions and assumptions log.** Everything that depends on an unanswered question, labeled as an assumption with the question that would resolve it.

**S1 is done when**
- every FR traces to a methodology section;
- every Critical and High finding from the review and audit maps to at least one FR or acceptance criterion;
- no FR contradicts the methodology (flag any contradiction found, and do not silently resolve it);
- the evidence-state table matches the pitch promises;
- Jason signs off.

## 5. Open decisions for Jason

| # | Decision | Recommendation |
|---|---|---|
| 1 | Restore the FR table dropped in v2.1 (changelog item 3) | Yes: it is the traceability backbone for S3 and S9 |
| 2 | Is the Richmond pilot confirmed? | The decision log says "assumed to proceed." S1 will frame Richmond as the first user either way; say if the engagement is not yet signed |
| 3 | Which pitch copy is current? | Confirm before S1 checks the evidence-state table against it |
| 4 | Produce a law Tier 1 data request now, or after S2? | Now, in parallel with S1: Richmond cannot send data against the v2.3 request |
| 5 | Dashboard scope for the Richmond MVP | S1 proposes views 1, 4 and 5 first; confirm |
| 6 | Capacity band (from the call) | Decides the Richmond screen verdict; record it as a fixed S1 input |

## 6. Known risks for this step

- **The value-of-information verdict rests on stylized pools.** Both the review and the audit used simplified Richmond pools. The production screen must run on the real optimizer with a 509-calibrated pool. S1 must state this as a requirement, not as a finished result.
- **Schedule.** S1 to S5 and S9 take weeks, and Richmond's offers are already rolling. S1 must say plainly what the client can expect to influence this cycle (likely the descriptive layers, the evidence audit, a written grid, and mid-cycle increases-only analysis) and what waits.
- **The all-eligible analysis depends on staff blindness** (audit A22). If Richmond answers Q8 with "no," the primary estimator changes. Record the answer.

## 7. Conventions

- Synthetic and public data only. Never ask for real client data.
- Tag every change [v2.5] with the edit number where one applies.
- Severity: Critical, High, Medium, Low. Confidence: low, medium, high. Separate what is shown from what is suspected.
- Keep it concise: no emojis; avoid "genuinely", "honestly" and "straightforward".
- Where two designs are both defensible, label it a judgment call and say what would change the choice.

## 8. Starter prompt (paste into Claude Code, opened in the EFA_FAO folder)

```
Read Handoff_S1_Kickoff.md in full, then do Phase A (sections 3.A1 to 3.A5) and stop at the checkpoint.
Do not modify anything under efa_fao/src/. Report test results, divergences from the stubbed
numbers, the edits applied, and anything that did not fit. Wait for my confirmation and for
Richmond_Call_Capture_Sheet.md to be filled in before starting Phase B. For Phase B, use plan mode
first: give me the S1 outline and the open decisions, then write the document after I approve.
```
