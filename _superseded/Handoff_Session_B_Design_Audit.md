# Handoff, Session B: design audit (spec, metrics, methods, generality, feasibility, simplification)

**Requested by:** Jason Cohen | **Date:** November 16, 2026 | **Recommended model:** Opus 5.5, high effort (Fable 5.2 is an optional second opinion on Parts B4 and B7)
**Time budget:** about 15 hours, over more than one sitting if needed. Run it **after** Session A (`Handoff_Session_A_Tactical_Audit_Cleanup.md`) and read Session A's report first.
**Output:** `Audit_Session_B_Design_Report.md` in this folder. This session is review only and edits nothing else.

## Starting prompt (paste into the new session)

> You are an independent reviewer for the EFA + FAO project in this folder. You did not write the material you are reviewing. Read `CLAUDE.md`, then `Handoff_Session_B_Design_Audit.md` in full (it is your brief), then `Audit_Session_A_Report.md`. Start by asking Jason the one question in Part B6. Then do Parts B1 to B7 in order, using a task list, and save each part's findings to `Audit_Session_B_Design_Report.md` as you finish it. This session is review only: edit nothing but the report and scratch scripts. Do not commit. Stop when Part B7 is done.

## Role and finding format

Be adversarial and specific, and don't praise. In Parts B1 to B6 your job is to confirm, correct or overturn, not to redesign. Part B7 (simplification) is the one place you may propose design changes, including to closed decisions. If something holds, say so in one line and move on.

The standard throughout: **a skeptical analyst at a client (an enrollment VP, a CFO, an institutional researcher) should not be able to ask "why did you calculate it that way?" without finding the answer written down.**

For every finding give:
- **ID** (B1-n, B2-n and so on, by part);
- **Severity:** Blocking (wrong output, or a contradiction the build would hit), Major (misleading or ambiguous, likely to cause rework), Minor (wording or polish);
- **Evidence:** Shown (reproduced, computed or read directly, with file and line) or Suspected (reasoned), and your confidence (low, medium, high);
- **Location** (file, section, line);
- **Proposed fix** as replacement text or a formula, short enough for Jason to apply.

## Ground rules

- **Confidentiality.** Richmond material (the Yellow Arrows workbook `Richmond Law - 2027 Scenarios for Client.xlsx`, the assessment, Dean Rooksby's priorities) is client-confidential. Keep it local. Never put client names, figures or campaign details into a web search; search with general terms if you search at all. Never copy fixture values into code, config, tests or documentation.
- **This session is review only.** Edit nothing except your report and scratch scripts. `efa_fao/src/`, `efa_fao/config/` and `efa_fao/sql/` are read for Part B5 only.
- **Never mix client data.** If you propose any use of one client's data (even aggregates) in another client's work, flag it as a decision for Jason; do not assume it is allowed.
- **Do not move, rename or delete files.** Do not commit.
- **Environment.** If the repo `.venv` won't run on your platform, use any Python 3.12 with numpy, scipy and pandas for checks, and report what you used. Put scratch scripts in a `review_support_v0.5/` folder in this project (git-ignored like `review_support_v2.4/`).
- **Save as you go.** Write each part's findings to the report when the part is done. If the session gets long, start a fresh one with this brief and the report, and continue from the next part.

## Material

| File | What it is |
|---|---|
| `Prototype_Spec_Scenario_Workbook_v0.5.md` | Scenario-workbook build spec (the main object of Part B1) |
| `Spec_v0.5_Change_List_draft.md` | Why each v0.5 change was made (C1 to C29, decisions D13 to D17, Jason's Nov 13 answers in section F) |
| `_superseded/Prototype_Spec_Scenario_Workbook_v0.4.md` | Prior spec, for diffing |
| `02_methodology_v2.7.md`, `S1_Requirements_and_User_Stories.md` (v1.2), `03_technical_roadmap_v2.7.md`, `01_executive_read_v2.7.md` | Design set; v2.7 edits tagged [v2.7, V27-n], Nov 13 addendum tagged [v2.7, V27A-n] |
| `Change_List_v2.7_draft.md`, `CHANGELOG_v2.7.md` | The v2.7 change list and its record, including the V27A addendum |
| `02_methodology_v2.6.md` and siblings | Prior versions, for diffing |
| `Handoff_Prototype_Phase1.md` | The Phase 1 build brief that depends on spec v0.5 |
| `ya_workbook_support/analysis.py`, `analysis_output.txt` | Reference computations on the Yellow Arrows workbook (source of most email figures) |
| `Richmond_YA_Scenario_Workbook_Assessment.md` | Background on the client workbook (git-ignored) |
| `Audit_Session_A_Report.md` | Session A's findings, the small-cell rule and anything it passed on (read first) |
| `efa_fao/src/`, `efa_fao/config/institution.yaml`, `efa_fao/sql/schema.sql`, `efa_fao/outputs/` | The earlier pipeline mockup, built on a synthetic undergraduate setup ("Lakeshore College"); read-only, for Part B5 |
| `efa_fao/docs/data_request_v3/` | Data request v3 (law and undergraduate), for definitions in Part B3 |
| `Opus_Methodology_Review_Instructions.md`, `Audit_S4_S5_Rereview_v2.4.md`, `Verification_Report_Oct22.md` | Earlier reviews, so you don't repeat settled findings |


---

## Part B1. Spec v0.5 mechanics and consistency (about 3 hours)

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

## Part B2. Methodology v2.7 edits and the V27A addendum (about 1.5 hours)

**Why:** the v2.7 edits were never audited separately, and the Nov 13 addendum now sits on top of them. This is a consistency and accuracy pass, not a redesign.

**Method:**
1. Diff `02_methodology_v2.7.md` against `02_methodology_v2.6.md`.
2. For each change in `Change_List_v2.7_draft.md` (V27-01 onward) and each V27A item in `CHANGELOG_v2.7.md`, check it was applied as listed, is internally consistent, and does not contradict spec v0.5, S1 v1.2, the roadmap or the executive read.
3. Review the **guardrail, screen and disclosure edits first.** These were flagged in the methodology itself as the ones to review first.

**Specifically check:**
- The guardrail removal and the client-declared policy envelope: is any guardrail language left that would flag client awards as exceptional?
- The price-test screen as it now reads.
- Small-cell disclosure: confirm or correct the rule Session A recorded, and check that Session A's wording edits match it.
- The decision layer versus policy of record (count rule, at most floor(admits / 30) parameters; Richmond about 13 groups plus one incentive), and whether the V27A target tier changes that count.
- Tuition defaults: 6.0% in reproduce mode, and 5.5% as an unconfirmed Richmond planning placeholder. Check they are never stated as confirmed.
- Open items (O36 to O40 and OD-01 to OD-09): still open where they should be, with nothing silently closed.
- Traceability: every FR in S1 v1.2 (including FR-77 to FR-80) maps to a methodology section that actually contains it.

**Stop condition:** every V27 and V27A item is marked Applied as listed, Applied with issues (findings), or Not applied.

---

## Part B3. Metric definitions: numerators, denominators and audiences (about 2.5 hours)

**Why:** every figure a client sees must say which population, which date and which dollars it uses, and it must match the recognized published definition or say plainly where it departs.

**Build a metric register** as a table in the report, with these columns:

| Column | What goes in it |
|---|---|
| Metric | The metric's name |
| Definition as written | Quoted, with its source |
| Numerator | What is counted on top |
| Denominator | The population: who exactly is counted |
| Time basis | Cycle and as-of date (application, deposit, census, fall snapshot) |
| Dollar basis | Tuition only or tuition and fees; institutional grants only or all gift aid; year 1 or multi-year with renewals |
| External standard | ABA 509, Common Data Set, IPEDS or NACUBO Tuition Discounting Study; and whether we match it or state our departure |
| Where defined | Document and section |
| Where computed | Spec section and code file |
| Consistent? | Yes, or the conflict |

**Cover at least these:**
- **Funnel:** applications (complete only? withdrawn?), admit rate, yield (enrolled over admits, or deposits over admits; which admits, including waitlist admits and deferrals), melt, class size (census headcount; law full-time and part-time), and funnel stage conversions in the EFA.
- **Academic profile:** LSAT and UGPA medians and percentiles (the ABA 509 basis), and the share at or above a threshold.
- **Revenue and price:**
  - Discount rate: entering class or all students, and which aid counts. Dean Rooksby wants to "maintain the discount rate", so say which definition he most likely means and what the documents assume.
  - NTR: entering class or all classes, year 1 or with renewals, and fees.
  - Net price: tuition minus institutional grant, versus the IPEDS net price.
  - Need spend and `need_rate`: the fixed 140 denominator is correct only if it is stated.
- **Geography:** out-of-state share (residency at application, at matriculation, or domicile).
- **Scenario-workbook KPIs:**
  - target-tier enrolled;
  - cost per incremental target enrollee;
  - paid-anyway share;
  - P(class > cap) and P(median holds);
  - pool growth year to date (same week of the prior cycle? complete applications? which LSAT score);
  - award gap against the market (ABA 509 rank-matched; earlier reviews found 509 fields misread, so check this one).

**Flag:**
1. Any metric defined two ways in different documents.
2. Any denominator that changes silently between scenarios or years.
3. Any ratio of expectations presented as an expected ratio (E[X]/E[Y] against E[X/Y]), for example the discount rate, share-above-threshold or paid-anyway share in simulation.
4. Any departure from a published standard that is not stated.
5. Any metric a client would see that has no written definition.

**Deliverable:**
- the register;
- findings;
- a proposed "Metric definitions" appendix (one line per metric) that the methodology, workbook README and dashboard could all cite. Proposed only; do not apply it.

**Stop condition:** every metric above is in the register with every column filled, or marked "not defined anywhere".

---

## Part B4. Statistical and methodological fitness (about 2.5 hours)

**Why:** the methods must suit the data this product will actually see: up to 10 clients; three to five cycles each; a few hundred to a few thousand admits per cycle; and small cells.

For each core method, answer four questions:
- Is it the right tool for that data?
- Would a simpler method lead to the same decision?
- Would it survive a skeptical client analyst?
- What are its failure modes, and what validation exists?

The methods:
- EFA funnel projection (stage-conversion pacing, FR-14);
- the yield model (regularized logit by default; boosted tree as a later challenger);
- price sensitivity (one logit slope; design-based anchors from a randomized bonus test or a merit-grid discontinuity; the value-of-information screen for the price test);
- position bands relative to the school's 25th, 50th and 75th percentiles as the main moderator;
- the class and median risk (closed-form normal against simulation);
- small cells and any pooling;
- the optimizer (linear program, decision layer under the count rule, the two-sided choice rule and the weak-evidence state);
- the Monte Carlo gates and seeds;
- the synthetic worlds and recovery tests;
- backtesting across cycles.

**Specific questions:**
1. **Year-level shocks.** Does the class and median uncertainty include a shared year-level yield shock (O37 is open)? If students are treated as independent, class-size variance is understated. Can a common shock be calibrated from three to five cycles, and what is the fallback when it can't?
2. **Thin data.** With one client and few cycles, what does each method fall back to, and is that written down?
3. **Placeholders.** Is "Response based on client-input" kept clearly apart from estimated responses everywhere, including in KPIs derived from it?
4. **Normal approximation.** Is it adequate at tail probabilities and for small target-tier counts? Where it isn't, what replaces it?
5. **Causal claims.** Does any output imply a causal effect of aid on yield drawn from observational data, where aid goes to stronger admits who have more options? Where is the confounding handled, and is the claim worded to match?
6. **Interval consistency.** Are intervals consistently 90%, labeled, and computed the same way across the workbook, dashboard and policy document?

**Stop condition:** every method has a one-line verdict (fit, fit with conditions, simpler alternative recommended, or not fit) and findings for any that are not plainly fit.

---

## Part B5. Generality: multiple clients, multiple years, different priorities, reproducibility (about 3 hours)

**Context:**
- There will never be more than 10 clients, in two verticals (law and undergraduate).
- Clients prioritize differently: geography (Richmond), NTR, yield, academic profile, class size, discount rate, access.
- Year 2 and year 3 must build on year 1's data and process, and improve on it.
- Nothing should be hard-coded to one institution or one use case.

1. **Hard-coding sweep.** Search the spec, methodology, S1, roadmap, config and code for client-specific constants and assumptions, including:
   - 140, 165, 166, NY, PA, $59,900, $63,500, the $200,000 need pool, 6.0%, 5.5%;
   - the 1.30 and 1.50 pool multipliers, the $10,000 NY/PA lump sum, three-year renewals;
   - LSAT-only logic, and "Richmond".

   Classify each one:
   - client config (fine);
   - vertical config, law or undergraduate (fine if declared);
   - hard-coded (finding).

   The code in `efa_fao/src/` is an earlier mockup built on a synthetic undergraduate setup, and it still carries a per-student aid-cut guardrail (`max_cut_per_student_k`) that the design has since removed. Say what in it survives into the product, what must change, and whether its config schema could carry a law client.
2. **Configuration model.** Is there one schema, per client and per cycle, that carries all of the following?
   - institution and vertical;
   - score scale (LSAT, GRE, SAT, ACT, test-optional);
   - segments and tiers;
   - levers, objectives and constraints;
   - data-availability flags.

   Map where each client-specific item lives today, and propose the smallest schema that covers law and undergraduate.
3. **Priorities without new code.** Can the evaluator and optimizer express each of these as configuration?
   - maximize NTR;
   - hit a class size;
   - raise yield;
   - raise a median or the share above a threshold;
   - hold a discount rate;
   - hit enrollment in a priority segment (geography, program, first-generation, in-state).

   Test on paper with three clients:
   - Richmond: geography, a smaller class, and LSAT;
   - a private undergraduate client focused on NTR under a discount-rate cap;
   - a public undergraduate client focused on yield among in-state admits.

   For each, list the levers, KPIs, sheets and dashboard views that apply, and what would need new code. **Question to answer:** the target-state tier is one instance of a "priority segment" (any client-defined grouping with a goal, an incentive, a lift and an offset). Would naming and building it generally be simpler and more general than geography-specific naming? Weigh this against D13.
4. **Multi-year.** How does year 2 use year 1? Check each of these:
   - data stored by cycle, with snapshots and versions;
   - re-estimation when a new cycle arrives;
   - use of prior-year estimates as priors;
   - a forecast-against-actual reconciliation each cycle (a calibration report);
   - policy changes between years treated as evidence (the v2.7 "qualifying policy change");
   - multi-year award renewals in NTR (law three years, undergraduate four);
   - the MultiYear and Trajectory stubs.

   Is there a written annual cycle (what runs when, what is refreshed, what is carried forward)? If not, outline the minimum one.
5. **Reproducibility.** Can last year's run be recreated exactly? Check:
   - seeds;
   - pinned environment;
   - config and data hashes in a run manifest (the `RunLog` sheet, `model_run.json`);
   - versioned outputs;
   - deterministic Excel builds.
6. **Client isolation.** With up to 10 clients on one Supabase and Vercel setup, is separation explicit (separate projects or row-level security), and can any pipeline run read another client's data? If any document proposes pooling across clients (for example, a shared law yield prior), flag it as a decision for Jason. Frankel policy is not to mix one client's confidential information into another client's work.
7. **Right-sizing.** Flag anything built for a scale this product won't reach.

**Stop condition:** all seven items answered; a hard-coding table; the three-client walkthrough; a proposed minimal schema and annual cycle (proposed only).

---

## Part B6. Feasibility against Richmond's 2027 cycle (about 1.5 hours)

**Assumption:** Claude Code does the building and Jason reviews; there is no other engineering staff. The documents don't state Richmond's delivery dates, so at the start of the session ask Jason one question: when Richmond needs the first scenario workbook, and when its first aid decisions for the 2027 entering class happen. If he isn't available, assume award decisions run from winter through spring 2027 and the workbook is needed within weeks, and say so.

**Check:**
- effort by phase (spec v0.5 section 12 and the roadmap) and the critical path;
- Jason's review time per phase, since he is the likely bottleneck;
- data dependencies: what Richmond has sent and what it hasn't. Without state-level counts the target tier runs on placeholders; say what that means for the 2027 deliverable;
- the minimum Richmond needs for 2027;
- what can wait for year 2;
- technical risks (Excel and LibreOffice parity, the macOS `.venv`, wiring the pipeline's Response table in later);
- whether the Phase 1 test burden is proportionate (20 tests, 20 seeds, 200,000-draw simulations).

**Deliverable:**
- a cut line in three groups (Must for Richmond 2027, Should, Later), with an effort range for each item and the reasoning;
- the three biggest execution risks and how to reduce each one.

---

## Part B7. Simplification (synthesis; about 1.5 hours; do last)

**You may challenge closed decisions** (D1 to D17 and the Nov 4, 5 and 13 decisions). Jason decides. Every proposal must state:
- what is cut, merged or deferred;
- the complexity removed (modules, parameters, levers, sheets, KPIs, tests, documents);
- what decision or client need is lost, and who asked for it (Dean Rooksby, Jason, a decision ID);
- the risk;
- your recommendation (cut, merge, defer to year 2, or keep).

**Start with a baseline count:**
- levers and parameters per scenario;
- KPIs per scenario;
- sheets;
- modules;
- tests;
- documents in the design set.

**Examine at least these** (they are candidates, not conclusions):
- the two class-size tables (mix held, and the shrink path);
- the four tripwire numbers (linear and probability, downside and upside);
- the four yield-shift levers (global, out-of-state, target, tier offset) plus the pool lift;
- the two incentive KPIs (cost per incremental enrollee, and paid-anyway share);
- the net-price block and the paired award-rule scenarios;
- `Static_MC` alongside the closed forms;
- the two goal-seek modes plus the schedule;
- the MultiYear and Trajectory stubs;
- reproduce mode;
- the number of documents in the design set (executive read, methodology, roadmap, S1, spec, change lists, changelogs, handoffs) and whether some could merge;
- anything in the methodology that year 1 won't use;
- simplifications that come from generality in Part B5 (for example, a general priority segment in place of geography-specific fields).

**Deliverable:**
- a ranked table, with the largest complexity reduction per unit of lost value first;
- a one-paragraph "if we did only three" recommendation.

---

## Report layout (`Audit_Session_B_Design_Report.md`)

1. **Verdict, at most 10 lines:**
   - is spec v0.5 build-ready (and the Blocking items);
   - metric-definition issues by severity;
   - statistical concerns;
   - the generality verdict (multiple clients, years and priorities);
   - the feasibility cut line for Richmond 2027;
   - the top three simplifications;
   - the decisions Jason must make.
2. Parts B1 to B7, each with its findings (Blocking first) and its deliverables.
3. A consolidated decision list for Jason: each decision, the options, your recommendation, and what it changes.
4. What you could not check, and why.

Keep the prose under about 9,000 words, plus tables. Mark every statistic and claim with its source so Jason can check it. Nothing here goes to a client without Jason's review.
