# Handoff: review, tactical audit and cleanup after spec v0.5 (fresh session)

**Requested by:** Jason Cohen | **Date:** November 16, 2026 | **Recommended model:** Opus 5.5, high effort
**Time budget:** about 6 to 8 focused hours across four parts. Do them in order and stop when each part's stop condition is met.
**Output:** one report, `Audit_v0.5_and_Cleanup_Report.md`, in this folder, plus the cleanup edits listed in Part 4. Nothing else changes.

## Starting prompt (paste into the new session)

> You are an independent reviewer for the EFA + FAO project in this folder. You did not write the material you are reviewing. Read `CLAUDE.md`, then `Handoff_Review_Audit_Cleanup_v0.5.md` in full; it is your brief. Do Parts 1 to 4 in order, using a task list. Parts 1 to 3 are review only: report findings, do not edit the files under review. Part 4 is a bounded cleanup with an explicit edit list. Write everything to `Audit_v0.5_and_Cleanup_Report.md`. Do not send, update or delete any email, do not commit, and stop when Part 4 is done.

## Role and finding format

Be adversarial and specific, and don't praise. Your job is to confirm, correct or overturn, not to redesign. If something holds, say so in one line and move on.

For every finding give:
- **ID** (A-n for Part 1, B-n for Part 2, M-n for Part 3);
- **Severity:** Blocking (wrong output, or a contradiction the build would hit), Major (misleading or ambiguous, likely to cause rework), Minor (wording or polish);
- **Evidence:** Shown (reproduced, computed or read directly, with file and line) or Suspected (reasoned), and your confidence (low, medium, high);
- **Location** (file, section, line);
- **Proposed fix** as replacement text or a formula, short enough for Jason to apply.

## Ground rules

- **Confidentiality.** Richmond material (the Yellow Arrows workbook `Richmond Law - 2027 Scenarios for Client.xlsx`, the assessment, Dean Rooksby's priorities) is client-confidential. Keep it local. Never put client names, figures or campaign details into a web search; search with general terms if you search at all. Never copy fixture values into code, config, tests or documentation.
- **Read-only areas:** `efa_fao/src/`, `efa_fao/config/`, `efa_fao/sql/`, everything in `Archive/` and `_superseded/`. The design documents under review (spec v0.5, methodology v2.7, S1 v1.2, roadmap v2.7, executive read v2.7) are read-only except for the Part 4 list.
- **Do not move, rename or delete files.** Do not commit.
- **Environment.** If the repo `.venv` won't run on your platform, use any Python 3.12 with numpy, scipy and pandas for checks, and report what you used. Put scratch scripts in a `review_support_v0.5/` folder in this project (git-ignored like `review_support_v2.4/`).

## Material

| File | What it is |
|---|---|
| `Prototype_Spec_Scenario_Workbook_v0.5.md` | Scenario-workbook build spec (the main object of Part 2) |
| `Spec_v0.5_Change_List_draft.md` | Why each v0.5 change was made (C1 to C29, decisions D13 to D17, Jason's Nov 13 answers in section F) |
| `_superseded/Prototype_Spec_Scenario_Workbook_v0.4.md` | Prior spec, for diffing |
| `02_methodology_v2.7.md`, `S1_Requirements_and_User_Stories.md` (v1.2), `03_technical_roadmap_v2.7.md`, `01_executive_read_v2.7.md` | Design set; v2.7 edits tagged [v2.7, V27-n], Nov 13 addendum tagged [v2.7, V27A-n] |
| `Change_List_v2.7_draft.md`, `CHANGELOG_v2.7.md` | The v2.7 change list and its record, including the V27A addendum |
| `02_methodology_v2.6.md` and siblings | Prior versions, for diffing |
| `Handoff_Prototype_Phase1.md` | The Phase 1 build brief that depends on spec v0.5 |
| `ya_workbook_support/analysis.py`, `analysis_output.txt` | Reference computations on the Yellow Arrows workbook (source of most email figures) |
| `Richmond_YA_Scenario_Workbook_Assessment.md` | Background on the client workbook (git-ignored) |

---

## Part 1. Tactical audit: the Richmond email figures (do first; about 45 minutes)

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

## Part 2. Review: spec v0.5 mechanics and consistency (main part; about 3 to 4 hours)

**Why:** the Phase 1 build follows this spec, and v0.5 added mechanics that nobody has checked independently. All 56 edits applied cleanly, which proves the text landed, not that the formulas, tables and tests agree.

**Method:**
1. Diff v0.5 against v0.4.
2. For each change in the change list (C1 to C29), confirm that it is present, that it says what the change list says, and that it agrees with every other section that touches it (sections 2, 3, 5, 6, 6A, 9, 10, 11, 12, 13, 15).
3. Where a formula can be checked numerically, check it on a small toy grid in `review_support_v0.5/` (say six cells, one in the target tier).

**Specific questions (answer each, then add anything else you find):**

1. **Target-enrolled probability.** P(E_T >= goal) = 1 - Phi((goal - 0.5 - M_T) / sqrt(V_T)).
   - Is the continuity correction applied in the right direction?
   - Is V_T built the same way as the class variance in section 5? In particular, if the class risk includes a common yield shock, does V_T include it too, or does the target tier get a smaller variance than it should?
   - Does the closed form behave sensibly when M_T is small (for example, under 10)? Is the normal approximation flagged there?
2. **Cost per incremental target enrollee.** dSpend_T / dE_T, reported when dE_T >= 0.5.
   - Is dSpend_T all incentive dollars in target cells, including those paid to students who would have enrolled anyway? It should be, for this KPI.
   - What is shown when dE_T < 0.5 or negative?
   - Is the 0.5 threshold justified, or should it scale with M_T?
3. **Paid-anyway share.** min(1, E_T(parent) / E_T(scenario)).
   - Check that it is computed over the cells that receive the incentive only. With `oos_min_lsat` set, target cells below the floor receive nothing and must be excluded from both terms.
   - Check the stated validity condition (the scenario differs from its parent by the incentive alone) is enforced or labeled when it fails.
4. **Incentive scope.**
   - `all_out` must reproduce v0.4 exactly on merged data.
   - `target` with an empty target tier must raise an error.
   - Check that the award cap at tuition is applied after the incentive, in every place awards are computed (ledger, Excel formulas, net-price block).
5. **Tier mechanics.**
   - Check the fallback chain (cell, then tier by LSAT group, then residency by LSAT group).
   - Check that `tier_yield_offset_pts` applies to `out_target` only, and how it interacts with clipping at 0 and 1.
   - Check that the shift precedence (target, then out, then global) is unambiguous: does a target shift replace the out-of-state shift or add to it? The spec must say one.
   - `target_pool_lift_pct`: does it multiply before or after the pool multiplier, and only at LSAT 165 and above or at all scores? Check that the spec, test 15 and the tripwires all assume the same thing.
6. **Class size and cap (C29).**
   - `class_cap` is hard; `class_size` is the target and must be at most the cap.
   - Check every place that previously used "class size 140" now uses the right one of the two: P(class > cap), the band probability, the what-if tables, the shrink path, goal-seek, Summary, Checks and narratives.
   - Check that `need_denominator` stays 140 and that `need_rate` is unchanged when the class shrinks.
   - Check that the range rules agree everywhere: supported and tested at 100 to 140, rejected outside 90 to 150, what-if list 100 to 140 in steps of 5.
7. **Shrink path.**
   - Excel: removed_share_k = MIN(1, MAX(0, (M - N - E_{k-1}) / mu_k)). Is E_{k-1} the cumulative expected enrollment removed before cell k? Does the walk stop exactly at M - N? What happens when mu_k = 0?
   - What happens when N >= M (the spec should return the original rates, never add admits)?
   - What happens when protecting the target tier makes the target unreachable without cutting target cells? Check that the order then reaches target cells last rather than failing silently.
   - Are tie-break orders (blank, lo, hi GPA; out_other, in, out_target) consistent between Python, the Excel `Trim` sheet and test 16?
   - Can the Excel formulas be built with XlsxWriter, with no macros, and recalculate in LibreOffice?
8. **Pool tripwires.**
   - Linear forms: m_class = (class_size - M_lo) / M_hi and m_median = -G_lo / G_hi. Check the decomposition (which cells sit in the "lo" part and which in the "hi" part) matches where the pool multiplier applies.
   - The multiplier applies at LSAT 165 and above but the median threshold may be 166, so the 165 band adds to the class without adding to the share above the median. Confirm G_hi can be zero or negative, and that "undefined" is handled and shown, not divided through.
   - Bisection: are the brackets stated, and are P(median holds) and P(class > cap) monotone in the multiplier under the spec's own assumptions? Where they might not be, what does the spec do?
   - Is `target_pool_lift_pct` included in or excluded from the tripwire multiplier? The spec must say which.
9. **Net-price readouts.**
   - Fixed-award change = Ts - T26; scaled-award change = p x (T26 - A). Check both identities, the full-tuition rung (zero under both), and the enrolled-weighted average.
   - The equivalent yield shift at placeholder slope b_M must be display-only: confirm no path feeds it into the ledger, and that it carries the "Arithmetic at constant award. Sticker-price demand effect not modeled." label and "Response based on client-input" where required.
10. **Decisions and guardrails.**
    - D1 (admit rates are not an optimizer dimension) still holds with the shrink path and goal-seek `mode: trim`.
    - D10 (net-price yield response deferred) still holds.
    - No new output labels an award exceptional or anomalous.
    - Small cells are shown, not suppressed.
11. **Tests 13 to 20.** Does each test check what it claims, and is it achievable as written (tolerances, number of worlds, seeds)? Is any v0.5 mechanic left untested? Do tests 1, 2, 4 and 5 (as edited) still pass by construction when the target tier is empty?
12. **Interface contract (section 15).** Every new output the dashboard or policy document will read (target block, both class-size tables, tripwires, net-price block) is in the contract with a name, unit and source sheet.
13. **Phase table and handoff.** Check that section 12 and `Handoff_Prototype_Phase1.md` list the same Phase 1 and 1b scope and tests, and that the handoff's "decisions already made" matches D13 to D17.

**Stop condition:** all 13 questions answered, with findings in the format above, and a one-paragraph verdict: whether the spec is fit to build Phase 1 from as is, after named Blocking fixes, or not yet.

---

## Part 3. Review: methodology v2.7 edits and the V27A addendum (bounded; about 2 hours)

**Why:** the v2.7 edits were never audited separately, and the Nov 13 addendum now sits on top of them. This is a consistency and accuracy pass, not a redesign.

**Method:**
1. Diff `02_methodology_v2.7.md` against `02_methodology_v2.6.md`.
2. For each change in `Change_List_v2.7_draft.md` (V27-01 onward) and each V27A item in `CHANGELOG_v2.7.md`, check it was applied as listed, is internally consistent, and does not contradict spec v0.5, S1 v1.2, the roadmap or the executive read.
3. Review the **guardrail, screen and disclosure edits first.** These were flagged in the methodology itself as the ones to review first.

**Specifically check:**
- The guardrail removal and the client-declared policy envelope: is any guardrail language left that would flag client awards as exceptional?
- The price-test screen as it now reads.
- Small-cell disclosure (methodology section 9 and FR-76): what exactly is the current rule, by audience? Record it plainly in the report, because Part 4 depends on it.
- The decision layer versus policy of record (count rule, at most floor(admits / 30) parameters; Richmond about 13 groups plus one incentive), and whether the V27A target tier changes that count.
- Tuition defaults: 6.0% in reproduce mode, and 5.5% as an unconfirmed Richmond planning placeholder. Check they are never stated as confirmed.
- Open items (O36 to O40 and OD-01 to OD-09): still open where they should be, with nothing silently closed.
- Traceability: every FR in S1 v1.2 (including FR-77 to FR-80) maps to a methodology section that actually contains it.

**Stop condition:** every V27 and V27A item is marked Applied as listed, Applied with issues (findings), or Not applied.

---

## Part 4. Cleanup (bounded edits; about 1 hour; do after Parts 1 to 3)

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
2. **Small-cell and privacy wording.** These say small groups are suppressed, which may no longer match the policy recorded in Part 3:
   - `efa_fao/docs/data_request_v3/spec/request_spec.yaml` (about line 203, "groups smaller than ten");
   - `Pitch and pricing decks/EFA_FAO_Pitch_Slides.html` (about line 247);
   - `Pitch and pricing decks/EFA_FAO_Pitch_Deck.md` (about line 113).

   If Part 3 recorded a clear rule:
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

   Fix plain wording mismatches in place. Report anything that touches substance as a finding instead.
5. **Spec fixes from Part 2 are not cleanup.** Do not apply Blocking or Major spec findings yourself; Jason decides which to apply.

**Stop condition:** every item is marked Done (with log) or Proposed (with text). Then stop.

---

## Report layout (`Audit_v0.5_and_Cleanup_Report.md`)

1. Verdict in five lines:
   - the email (ready, or which sentences to fix);
   - the spec (build-ready or not, and the Blocking items);
   - the methodology (count of issues by severity);
   - cleanup done;
   - anything Jason must decide.
2. Part 1 table (figure, status, replacement sentence, source).
3. Part 2 findings, Blocking first.
4. Part 3 findings, with the small-cell rule recorded plainly.
5. Part 4 log and proposals.
6. What you could not check and why (for example, no Gmail access, fixture missing, LibreOffice missing).

Keep the report under about 4,000 words. Mark every statistic and claim with its source so Jason can check it. Client-facing items (the email, the data request, the pitch deck) still need Jason's own review and a confidentiality check before anything leaves Frankel.
