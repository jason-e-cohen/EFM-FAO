# Handoff, Session A: tactical audit and cleanup (fresh session)

**Requested by:** Jason Cohen | **Date:** November 16, 2026 | **Recommended model:** Opus 5.5 or Sonnet 5.5 (mostly tracing and bounded edits)
**Time budget:** about 2 hours. Run this **before** Session B (`Handoff_Session_B_Design_Audit.md`), because Session B reviews the documents this session edits.
**Output:** `Audit_Session_A_Report.md` in this folder, plus the cleanup edits listed in Part A3. Nothing else changes.

## Starting prompt (paste into the new session)

> You are an independent reviewer for the EFA + FAO project in this folder. You did not write the material you are reviewing. Read `CLAUDE.md`, then `Handoff_Session_A_Tactical_Audit_Cleanup.md` in full; it is your brief. Do Parts A1 to A3 in order, using a task list. Parts A1 and A2 are review only. Part A3 is a bounded cleanup with an explicit edit list. Write everything to `Audit_Session_A_Report.md`. Do not send, update or delete any email, do not commit, and stop when Part A3 is done.

## Role and finding format

Be adversarial and specific, and don't praise. Your job is to confirm, correct or overturn, not to redesign. If something holds, say so in one line and move on.

For every finding give:
- **ID** (A1-n for Part A1, A2-n for Part A2, A3-n for Part A3);
- **Severity:** Blocking (wrong output, or a contradiction the build would hit), Major (misleading or ambiguous, likely to cause rework), Minor (wording or polish);
- **Evidence:** Shown (reproduced, computed or read directly, with file and line) or Suspected (reasoned), and your confidence (low, medium, high);
- **Location** (file, section, line);
- **Proposed fix** as replacement text or a formula, short enough for Jason to apply.

## Ground rules

- **Confidentiality.** Richmond material (the Yellow Arrows workbook `Richmond Law - 2027 Scenarios for Client.xlsx`, the assessment, Dean Rooksby's priorities) is client-confidential. Keep it local. Never put client names, figures or campaign details into a web search; search with general terms if you search at all. Never copy fixture values into code, config, tests or documentation.
- **Read-only areas:** `efa_fao/src/`, `efa_fao/config/`, `efa_fao/sql/`, everything in `Archive/` and `_superseded/`. The design documents under review (spec v0.5, methodology v2.7, S1 v1.2, roadmap v2.7, executive read v2.7) are read-only except for the Part A3 list.
- **Do not move, rename or delete files.** Do not commit.
- **Environment.** If the repo `.venv` won't run on your platform, use any Python 3.12 with numpy, scipy and pandas for checks, and report what you used. Put scratch scripts in a `review_support_v0.5/` folder in this project (git-ignored like `review_support_v2.4/`).

## Material

| File | What it is |
|---|---|
| `ya_workbook_support/analysis.py`, `analysis_output.txt` | Reference computations on the Yellow Arrows workbook (source of most email figures) |
| `Richmond_YA_Scenario_Workbook_Assessment.md` | Background on the client workbook (git-ignored) |
| `CLAUDE.md`, `02_methodology_v2.7.md`, `S1_Requirements_and_User_Stories.md` (v1.2), `Prototype_Spec_Scenario_Workbook_v0.5.md` | Design set, for the small-cell rule and the cleanup edits |
| `efa_fao/docs/data_request_v3/` | Data request source (`spec/`), builder (`build_request.py`), tests (`test_spec.py`), `GAP_LOG.md` |
| `Pitch and pricing decks/` | Pitch deck (`.md`, `.html`) and pricing slides (`.pptx`) |

---

## Part A1. Tactical audit: the Richmond email figures (do first; about 45 minutes)

**Why first:** Ryan Frankel asked for a final run of the email and analysis, and the draft goes from Ryan to Dean Rooksby. The Dean will read every number as Frankel's.

**Where the draft is:** Jason's Gmail, draft to ryan@frankelagency.com, subject "Re: Fwd: FAO at Richmond Law", thread labeled "To Send to Jacob Rooksby". If a Gmail tool is connected, read it there (and say whether it is still an unsent draft). If not, ask Jason to paste the body. **Do not modify, send or delete the draft.**

**Recompute or trace each figure independently** (don't trust the draft's own lead-in note):

| Figure in the draft | Claimed source | What to check |
|---|---|---|
| 60% | Brandon's Oct 30 note (Gmail) | Find the note and confirm the figure and what it measures. If you can't reach Gmail, flag it for Jason |
| 114 to 122 students | `analysis_output.txt` section 10, flat 165+ pool, Scenarios 1, 2 and 4 | Rerun `analysis.py` if the fixture is present; confirm the range and that the email describes it as "pool held flat, everything else unchanged" |
| 44.9% | Same section, Scenario 1 share at or above 166 | It is Scenario 1 only (S2 is 44.4%, S4 is 41.7%). Check that the sentence does not imply it holds for every scenario |
| "two in three", "40%" | Class-risk lines in `analysis_output.txt` (P(class > 140) about 0.41 to 0.42; P(within 4 of 140) about 0.34) | Confirm which probability each phrase states and that the wording matches it exactly (for example, "misses 140 by more than four" versus "lands above 140") |
| about $3,300 and 17% | Our arithmetic: 5.5% on $59,900 is about $3,295; on a $40,000 award, net price rises from $19,900 by about 16.6%; on $50,000 by about 33% | Recompute; confirm the email says the award is held fixed in dollars, and that "17%" is labeled as an example award level |
| about 107 | Our arithmetic: 140 / 1.055^5 = 140 / 1.30696 = 107.1, holding the discount rate constant | Recompute; state the assumption it rests on (per-student net revenue grows with tuition at a constant discount rate, entering class only) and check the email states it too |
| "just over 5.5%" | Dean Rooksby's own words | Confirm it is presented as the Dean's figure, pending Brandon's specifics |

**Also check:**
- No figure appears that isn't in this table. Trace any extra figure the same way.
- No content from any other Frankel client.
- The commitment Jason asked for ("excited to support their geo-targeting strategy" and "confident in our ability to deliver on that goal") is present. Check that it promises capability, not a specific enrollment number.
- **Jason's house style:**
  - no em dashes or en dashes anywhere;
  - no sentence without a subject ("Wanted to..." is wrong, "I wanted to..." is right);
  - salutation "Dean Rooksby,";
  - "Frankel", never "Frankel Agency";
  - prose only, no bullets in the client-facing body.

**Stop condition:** every figure is marked Confirmed, Corrected (with replacement sentence) or Unverifiable (with what Jason needs to check).

---

## Part A2. Record the current small-cell rule (about 20 minutes)

Part A3 rewrites client-facing privacy wording, so first pin down the rule it must match. Read `CLAUDE.md`, methodology v2.7 section 9 (small-cell disclosure), FR-76 in S1 v1.2, and the spec v0.5 guardrail test (test 8). Write the rule in the report as a short table by audience:
- the Excel workbook sent through the client's secure channel;
- the authenticated client dashboard;
- the aid office;
- the policy document;
- pitch and marketing claims;
- anything public.

Where the documents disagree, record the disagreement as a finding and do not resolve it yourself.

**Stop condition:** a rule is recorded for every audience, or marked "unclear" with the conflicting sources.

---

## Part A3. Cleanup (bounded edits; about 1 hour)

Make **only** the edits below. For each edit, log the file, line, old text and new text in the report's cleanup section. If a fix needs judgment beyond what is written here, don't make it; list it as a proposal.

1. **Data request additions (V27A-07).**
   - In `efa_fao/docs/data_request_v3/spec/`, add a law early-delivery item for Richmond:
     - aggregate application, admit and deposit counts by state (by LSAT band if available) for the last three cycles;
     - weekly pacing for the current cycle against the prior two cycles at the same week;
     - the exact 2027 tuition increase and the planned tuition path;
     - undergraduate tuition by year;
     - the class-size target path.
   - Use the spec's existing structure (`request_spec.yaml` and the CSVs). Do not duplicate the student-level state and ZIP3 fields already there; these are aggregates for use before student-level data arrive.
   - Rebuild with `build_request.py`, run `test_spec.py`, and add an entry to `GAP_LOG.md`.
   - Report the regenerated files. Do not send anything to the client.
2. **Small-cell and privacy wording.** These say small groups are suppressed, which may no longer match the rule recorded in Part A2:
   - `efa_fao/docs/data_request_v3/spec/request_spec.yaml` (about line 203, "groups smaller than ten");
   - `Pitch and pricing decks/EFA_FAO_Pitch_Slides.html` (about line 247);
   - `Pitch and pricing decks/EFA_FAO_Pitch_Deck.md` (about line 113).

   If Part A2 recorded a clear rule:
   - rewrite these three to match it exactly, keeping the claim no stronger than the rule;
   - rebuild the data request;
   - leave the `.pptx` pricing slides alone (they were checked and carry no such wording).

   If the rule is unclear or differs by audience in a way the wording can't carry, don't edit; propose text instead. These are client-facing privacy statements: flag them for Jason's review either way. Also list, without editing, any suppression logic in `efa_fao/src/` or `efa_fao/config/institution.yaml` that conflicts with the rule.
3. **Small text fixes in the design set:**
   - Spec v0.5, section 6, Ledger sheet row: "OOS incentive" becomes "out-of-state incentive (per scope)".
   - `CHANGELOG_v2.7.md` table rows 4 and 7: append "(superseded in part by V27A-01)" where they say geography is one out-of-state incentive.
   - S1 CONTR-05 ("Tuition increase (~5%)"): append "**[V27A-06]** Richmond planning uses 5.5%, unconfirmed (OD-09)."
4. **Stale-reference sweep.** Search the current documents (top-level `.md` files at v2.7, S1, spec v0.5, both handoffs, `CLAUDE.md`; not `Archive/`, `_superseded/` or the v2.4 to v2.6 files) for:
   - "v0.4" (other than historical or "reproduces v0.4 behavior" references);
   - "130, 135" and "130 to 145";
   - "one out-of-state incentive" or "single out-of-state incentive" stated as the current design;
   - "default 140" where it implies the target and cap are the same thing;
   - "6.0%" stated as Richmond's 2027 plan.

   Fix plain wording mismatches in place. Report anything that touches substance as a finding for Session B instead.

**Stop condition:** every item is marked Done (with log) or Proposed (with text). Then stop.

---

## Report layout (`Audit_Session_A_Report.md`)

1. Verdict in four lines:
   - the email (ready, or which sentences to fix);
   - the small-cell rule (clear or not);
   - cleanup done;
   - anything Jason must decide.
2. Part A1 table (figure, status, replacement sentence, source).
3. Part A2 rule table and any conflicts.
4. Part A3 log and proposals, including anything passed to Session B.
5. What you could not check and why (for example, no Gmail access or the fixture missing).

Keep the report under about 2,000 words. Mark every statistic and claim with its source so Jason can check it. Client-facing items (the email, the data request, the pitch deck) still need Jason's own review and a confidentiality check before anything leaves Frankel.
