# Audit Session A report: tactical audit and cleanup

**Reviewer:** Claude Sonnet 5.5 (independent) | **Date:** November 16, 2026 | **Scope:** Parts A1 to A3 of `Handoff_Session_A_Tactical_Audit_Cleanup.md`. No email sent, changed or deleted. Nothing committed. Client-facing items still need Jason's review and a confidentiality check before anything leaves Frankel.

## 1. Verdict

1. **Email: not ready.** There is no unsent draft. The Nov 13 revision (Gmail message 1a1d649a373b9ca9, "Re: Fwd: FAO at Richmond Law") was already sent to Ryan; Gmail shows no drafts. Fix A1-5 (Blocking), then A1-1, A1-2, A1-6, A1-7, A1-8, A1-10 and A1-12 (Major), then the house-style items.
2. **Small-cell rule: clear for the authenticated dashboard (default and Richmond), unclear for the Excel workbook, policy document, pitch claims and anything public**, and three documents conflict (A2-1 to A2-3).
3. **Cleanup: all four items done** (data request additions, small-cell wording in three files, four small text fixes, sweep with no in-place edits needed). Extra small-cell wording found outside the edit list is proposed, not edited.
4. **Decisions made (Nov 16):** counts are deposits and the two prior cycles; the five-year plan and undergraduate gap promise is deferred; generator bug fixed; extra pitch deck wording applied (section 6). Still open: the email edits in section 6.

## 2. Part A1: Richmond email figures

Source for the figures: `ya_workbook_support/analysis_output.txt` (AO), rerun by me on the fixture with Python 3.10, numpy and openpyxl. **The rerun matches the saved output exactly.** My own arithmetic is in `review_support_v0.5/a1_checks.py`. The Nov 13 body has 866 words. Brandon's Oct 30 note and Dean Rooksby's Nov 13 note were read in Gmail.

| ID | Figure in draft | Status, severity, confidence | Replacement sentence | Source |
|---|---|---|---|---|
| A1-1 | "114 and 122" | **Corrected**, Major, high. Numbers hold for Scenarios 1, 2, 4 only (122, 117, 114); Scenario 3 was not run. The email says "that pool", but the flat pool is the 165-and-above pool. The Nov 12 version said "165 and above"; the Nov 13 rewrite lost it | "When I kept the pool of applicants at 165 and above flat and held everything else constant, Scenarios 1, 2 and 4 landed between 114 and 122 rather than near 140." | AO section 10 (lines 78-80) |
| A1-2 | "growth of 30% to 50%" (not in the brief's table) | **Corrected**, Major, high. Growth is on 165+ cells only (about 1.30 in Scenarios 1 to 3, 1.51 in Scenario 4; below-165 cells 1.00) | "Every YA scenario assumes that growth in applicants at 165 and above, 30% in Scenarios 1 to 3 and 50% in Scenario 4, holds through the close." | AO section 4 (lines 30-34) |
| A1-3 | "45% ... at or above 166" | **Confirmed.** 0.449, Scenario 1 only (S2 0.444, S4 0.417); the sentence names Scenario 1 and does not generalize | none | AO line 78-80 |
| A1-4 | "40% chance of running over 140", "three of four" | **Confirmed**, Minor. P(class above 140): S1 0.42, S3 0.45, S4 0.41, S2 0.22. Independent-binomial simulation, seed 7. Suggest "roughly 40% to 45%" | "...in three of the four scenarios there's a 40% to 45% chance of the class running over 140." | AO lines 64-71 |
| A1-5 | "five-person margin on the LSAT median holds about two times in three" | **Unverifiable as worded**, Blocking, high. No "five-person margin" quantity exists in AO. "Two in three" matches 1 minus P(within 4 of 140) = 0.66 (S1, S3, S4; S2 0.72), or P(LSAT median at or above 166) = 0.66, 0.61, 0.68 (S1, S2, S4). The sentence ties one to the other | "By our read, the class lands within four students of 140 only about one time in three under ordinary enrollment variation, so it misses by more than four about two times in three." | AO lines 64-71 |
| A1-6 | "$3,300 (roughly 17%) under a 5.5% increase" | **Arithmetic confirmed; attribution corrected**, Major, high. 59,900 x 5.5% = 3,294.5; 3,294.5 / 19,900 = 16.56%; at a $50,000 award 33.3%. "As I read the workbook" is wrong: the workbook's own step is 59,900 to 63,500, **+6.01%** (+$3,600, 18.1% at $40,000). Award held fixed is stated; $40,000 is not labeled as an example level | "At the 5.5% increase you describe, with awards fixed in dollars, a student with a $40,000 award (an illustrative level) would see net price rise by about $3,300, roughly 17%. The YA scenarios assume about 6%, and yield is held steady." | AO lines 9-16; `a1_checks.py` |
| A1-7 | "about 107"; "5.5% each year" | **Arithmetic confirmed; assumptions incomplete**, Major, high. 1.055^5 = 1.30696; 140 / 1.30696 = 107.1. Email states entering-class revenue and held discount rate; it does not say it starts from 140 (2026 actual 138 gives 105.6) or that 5.5% every year is our assumption (Dean gave next year only) | "...a 5.5% increase each year (our assumption beyond next year) with the discount rate held keeps entering class revenue about flat, from a class of 140 today to a class near 107 after five years..." | `a1_checks.py`; AO line 12 |
| A1-8 | "just over 5.5%" | **Not present**, Major. Email states "5.5%" three times as fact. Dean's words: "just over 5.5% (Brandon can get you the specifics)" | Attribute once: "the increase you describe, just over 5.5%, which we are using as a working figure until Brandon confirms it". | Dean Rooksby, Nov 13 |
| A1-9 | "60%" | **Confirmed at source, absent from the email.** Brandon: "For reference we're currently up 60%", for high LSAT applicants; Scenario 4 needs "at least a 50% increase". Baseline of the 60% is not stated | none needed; if added, ask Brandon for the baseline | Brandon, Oct 30 |
| A1-10 | "one point per $1,000 sits almost exactly where added aid pays for itself" (not in table) | **Corrected**, Major, medium. Break-even ratio = (1 pt per $1,000) x (tuition minus award) / yield. Admit-weighted median 0.94 (2026 cells) and 1.18 (Base); cell median 0.72 and 0.85; IQR 0.34-0.98 and 0.70-1.22; only 27% and 41% of cells within 0.8-1.25. Assumes a linear slope and a one-year view | "On average across admits, one point per $1,000 sits near the break-even where added aid pays for itself, and it varies widely from cell to cell." | `a1_checks.py` |
| A1-11 | "yield rises about one point per $1,000"; "same when admit rates go up" | **Confirmed.** Median 0.99 (IQR 0.65-1.04; range 0.31-2.00); yield unchanged in 24 of 24 admit-rate changes | none; "about one point on average" is safer | AO lines 38, 84 |

**Other checks.**

- A1-12 (Major, high): the data request asks for different counts than the email. Email item 3 asks for "applicant, admit, and enrolled counts"; item 4 for pacing "against last year"; spec section 15 item 10 says the same (adds "by LSAT band"). The Session A brief, and so the new data request files, use deposits and the prior two cycles. Jason to choose; see GAP_LOG J11.
- A1-13 (Major, medium): "lay out the five-year plan year by year, including the gap with undergraduate tuition" outruns spec v0.5. The Summary shows the gap for one year, and the `MultiYear` and `Trajectory` sheets are a later build (spec lines 118, 165). "We're building a live what-if planner ... and a matching dashboard" is also present tense for a spec-phase item (CLAUDE.md decision log).
- Commitment: present ("excited to support your geo-targeting strategy ... confident in our ability to deliver on that goal"). It promises capability, not an enrollment number. Minor: "goal" could read as an outcome; "strategy" is safer.
- Other Frankel clients: none found.
- House style:
  - No em or en dashes (checked by script).
  - Salutation and "Frankel" use are correct.
  - **Bullets and a numbered list are present** (9 items), where prose only is required: Major.
  - Two sentences lack a subject ("Thank you for sharing...", "Thank you also for asking..."): Minor; use "I appreciate you sharing the 2027 scenarios with us." and "I also appreciate you asking what we might need."

## 3. Part A2: the small-cell rule

Sources: CLAUDE.md Rules; methodology v2.7 section 9 (lines 617-623) and section 2 (line 38); S1 v1.2 FR-76 (line 205), FR-06, FR-61, NFR-01; spec v0.5 decision (4), D3, test 8; roadmap v2.7 line 114.

| Audience | Rule | Status |
|---|---|---|
| Authenticated client dashboard | Per-engagement `small_cell_policy`. Default: suppress cells under 10 with complementary suppression. Richmond: no suppression for named, authenticated roles (enrollment team, leadership, aid office); analyst sees all; gate approver sees the packet only. Other clients keep the default unless they elect otherwise in writing. Cat and Richmond staff signed off Nov 5 | Clear |
| Aid office | Sees all views including small cells at Richmond | Clear |
| Excel workbook through the secure channel | Spec v0.5 decision (4) and D3 say the workbook shows small cells to authenticated client staff. Section 9 and FR-76 define the rule by dashboard role and do not mention files. A delivered file cannot be authenticated per viewer | **Unclear** |
| Policy document | Not addressed. It carries the fine award matrix (spec section 15). FR-06 acceptance says "No cell under 10 in any output" | **Unclear** (conflict) |
| Pitch and marketing claims | No rule. Only the default can be stated generally; Richmond-specific material cannot claim suppression | **Unclear** (inferred) |
| Anything public | Not addressed. Aggregates only and no student-level rows (section 9) | **Unclear** |

- **A2-1 (Major, high):** FR-06 acceptance ("No cell under 10 in any output", S1 line 87) contradicts FR-76 and the same row's text.
- **A2-2 (Minor, high):** spec decision (4) lists "authenticated client staff, enrollment team and leadership" and omits the aid office, which D3 and FR-76 include.
- **A2-3 (Major, high):** spec test 8 has no small-cell assertion. The small-cell test is guardrail test 2 in `efa_fao/tests/test_guardrails.py` (lines 17-21), which asserts suppression for every cell and conflicts with the Richmond rule.
- **A2-4 (listed, not edited; read-only areas):** code and config that enforce suppression unconditionally: `efa_fao/config/institution.yaml:34`; `efa_fao/src/efa_fao/pipeline/aggregate.py` (lines 3-4, 47-63); `run_pipeline.py:98`; `efa_fao/sql/schema.sql:16` (`min_cell_size >= 10`) and `:76-78` (suppressed rows must be null).
- **A2-5 (Minor):** the sign-off record (O40) is not yet in the SOW or alignment-gate packet.

## 4. Part A3: cleanup log and proposals

**Item 1, data request additions: Done.** Files under `efa_fao/docs/data_request_v3/`:

- `spec/files.csv` lines 13-15: three law-only rows (`early_funnel_by_state`, `early_pacing`, `early_planning_path`).
- `spec/fields.csv` lines 168-186: 19 fields. No student-level state or ZIP3 field repeated.
- `spec/request_spec.yaml` lines 80-86 (paragraph, three bullets) and line 258 (checklist line).
- `GAP_LOG.md` section 7 (J11 to J15).
- Regenerated all eight files in `output/`; the law template gains three sheets, the undergraduate dictionary is unchanged. `test_spec.py`: 8 of 8 pass (plain Python loop; `pytest` not installed).

**Item 2, small-cell wording: Done, flagged for Jason's review.** I judged the rule clear for statements about the dashboard and aggregate reporting, and wrote each claim no stronger than "default plus per-client election".

| File and line | Old | New |
|---|---|---|
| `request_spec.yaml:212` | "The dashboard shows aggregates only, with groups smaller than ten suppressed." | "The dashboard shows aggregates only. By default, groups smaller than ten are suppressed. You can elect to show small groups to named staff." |
| `Pitch and pricing decks/EFA_FAO_Pitch_Slides.html:247` | "aggregate-only reporting with small cells suppressed." | "aggregate-only reporting. Small cells are suppressed by default, and each client sets its own policy for named, authenticated staff." |
| `Pitch and pricing decks/EFA_FAO_Pitch_Deck.md:113` | "groups under 10 students are suppressed, and raw files" | "groups under 10 students are suppressed by default (each client can set its own policy for named, authenticated staff), and raw files" |

The `.pptx` slides were not touched. **Proposed, not edited (outside the list):** `Pitch_Deck.md:29` "Groups under 10 students are never shown" becomes "Small groups are suppressed by default; each client sets its own policy for named, authenticated staff."; `Pitch_Deck.html:227` and `:405` take the same "by default" qualifier; `Pitch_Deck.html:401` says "FERPA-approved environment", which I could not verify.

**Item 3, small text fixes: Done.**

| File, line | Old | New |
|---|---|---|
| `Prototype_Spec_Scenario_Workbook_v0.5.md:155` | "after tuition scaling and OOS incentive)" | "after tuition scaling and out-of-state incentive (per scope))" |
| `CHANGELOG_v2.7.md:14` (row 4) | "...plus one out-of-state incentive at Richmond) \|" | adds "(superseded in part by V27A-01)" |
| `CHANGELOG_v2.7.md:17` (row 7) | "...Geography is one out-of-state incentive \|" | adds "(superseded in part by V27A-01)" |
| `S1_Requirements_and_User_Stories.md:504` (CONTR-05) | "Tuition increase (~5%) and fixed-dollar renewal rule." | adds "**[V27A-06]** Richmond planning uses 5.5%, unconfirmed (OD-09)." |

**Item 4, stale-reference sweep: Done, no in-place edits needed.**

- "v0.4": 14 hits, all historical or "reproduces v0.4".
- "130, 135" and "130 to 145": none.
- "default 140" implying target equals cap: only `CHANGELOG_v2.7.md:17` and `Change_List_v2.7_draft.md:45`, both Nov 5 records. Spec v0.5 line 54 and FR-78 keep target and cap apart.
- "6.0%": live documents label it reproduce mode. The same two Nov 5 records state it as the default; propose extending the row 7 note to "(superseded in part by V27A-01, V27A-02 and V27A-06)".
- "one out-of-state incentive": `Change_List_v2.7_draft.md:13` is a Nov 5 record.

**Passed to Session B (substance):**

- `02_methodology_v2.7.md:360` still says "Geography enters as one out-of-state incentive ... market-level geography is deferred", while V27A-01 puts a market tier on every cell.
- The generator bug below.
- A1-12 and A1-13.

**Found, not fixed (Major, high):** in `request_spec.yaml` (lines 41-42), `p: {only: law, text: ...}` resolves to no text in `blocks_to_ir`, so "What you receive depends on the evidence..." and "We do not recommend a change in price level without design-based evidence" appear in no output. Shown: the sentence is absent from the law `.md`. Fix: `p: {law: "..."}`.

**Also noted:** `.gitignore` does not list `review_support_v0.5/` or `review_support_v2.4/`, although the brief says both are ignored. Proposed: add both.

## 5. What I could not check

- Whether Ryan has since sent anything to the Dean: only Jason's mailbox was visible.
- The A1-10 ratio assumes the workbook's linear yield rule; other forms were not tested.
- The `.docx` and `.xlsx` files were opened programmatically, not visually.
- `efa_fao/src/`, config and SQL were read, not run; guardrail tests were not run.
- The device has Python 3.10 (not 3.12) and no `pytest`; the analysis needs only numpy and openpyxl.
- Counsel has not reviewed the privacy wording. Jason: check that the email, data request and pitch carry no other client's confidential information before anything leaves Frankel.

## 6. Follow-up after Jason's decisions (November 16, 2026)

| Decision | Action taken | Still to do |
|---|---|---|
| Counts: deposits and the two prior cycles (A1-12) | Data request already matched. Spec v0.5 section 15 item 10 (line 293) rewritten to "application, admit and deposit counts by state (by LSAT band if available) for the last three cycles ... weekly pacing against the prior two cycles at the same week of the cycle". GAP_LOG J11 marked confirmed | Email. Item 3 becomes "aggregate application, admit, and deposit counts by state for the last three cycles, with New York and Pennsylvania broken out and LSAT band if you have it"; item 4 becomes "weekly pacing of applications, admits, and deposits for this cycle against the prior two cycles at the same week" |
| Defer the five-year plan and undergraduate gap (A1-13) | None in the files | Email: drop "and we'd lay out the five-year plan year by year, including the gap with undergraduate tuition" and keep "Each result would carry the probability that it holds, with the baseline beside it." The data request still asks for undergraduate tuition by year (`ug_tuition_usd`); delete that field and the matching phrase in the bullet if you do not want it asked |
| Fix the generator bug | `request_spec.yaml` lines 41-42 now `p: {law: ...}`. The sentence "We do not recommend a change in price level without design-based evidence" is back in the law request (1 match) and absent from the undergraduate one. Both requests rebuilt; 8 of 8 spec tests pass | None |
| Extra pitch deck wording | `Pitch_Deck.md:29`, `Pitch_Deck.html:227` and `:405` now carry "by default; each client sets its own policy for named, authenticated staff" | The "FERPA-approved environment" line (`Pitch_Deck.html:401`) is unchanged and unverified |
