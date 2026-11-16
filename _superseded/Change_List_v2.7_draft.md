# EFA + FAO v2.7: change list (draft for Jason's approval)

**Date:** November 5, 2026 | **Owner:** Jason Cohen | **Status:** A1 to A6 answered Nov 5 (section A); **edits applied Nov 5** (see `CHANGELOG_v2.7.md`: methodology, roadmap and executive read v2.7, S1 v1.1, CLAUDE.md); code, schema and tests (section F) untouched | **Reads with:** `02_methodology_v2.6.md`, `S1_Requirements_and_User_Stories.md`, `03_technical_roadmap_v2.6.md`, `CLAUDE.md`, `Prototype_Spec_Scenario_Workbook_v0.4.md`, `Richmond_YA_Scenario_Workbook_Assessment.md` (git-ignored; section 12 holds the fixture evidence)

**What v2.7 is.** The Richmond Yellow Arrows (YA) workbook showed that the client plans in a fine LSAT x GPA x residency matrix, moves admit rates and awards together, and does not use a per-cell cap on award changes. Jason's decisions of Nov 4 and 5 follow from that. v2.7 makes the specification say so, without opening any closed decision. Tag edits **[v2.7, V27-n]**. Nothing here changes the statistics of sections 4 and 6 except where stated.

**Decisions this list implements** (Jason, Nov 4 and 5)
1. Admit-rate levers are scenario inputs that follow the YA approach; goal-seek helper; admit-rate optimization later.
2. The 5% per-cell guardrail is removed (constraint, flag and reporting). The two-cycle threshold freeze is dropped for client-authored thresholds.
3. Policy of record is the client's fine matrix. The optimizer works on a low-dimensional decision layer; the fine matrix is rendered by rule.
4. Small cells are shown to authenticated client staff (enrollment team, leadership, aid office). Cleared with Cat.
5. The Excel workbook, the dashboard and the policy document agree everywhere, because one ledger computes all three.
6. Tuition migration, class size, out-of-state incentive and yield shift are scenario levers. Geography is one out-of-state incentive parameter. A net-price yield response is deferred.
7. The YA workbook is a validation fixture and a source of synthetic shape parameters; it stays out of git.

---

## A. Decisions (answered by Jason, Nov 5)

| # | Question | Decision |
|---|---|---|
| A1 | Where the scenario evaluator sits in the evidence states | **Accepted.** The evaluator is a fifth deliverable in every evidence state. Every output carries the fixed label **"Response based on client-input"**. "Evidence too weak to change aid levels" (FR-26) stays on Frankel-recommended grids only. One sentence is added to the CLAUDE.md price-change rule: evaluation is not recommendation. |
| A2 | Segment floors with the guardrail gone | **Keep floors** (Appendix C, FR-34). Fixture check: they do not bind in any YA scenario. |
| A3 | Dropping the freeze versus discontinuity evidence | **Accepted.** Freeze dropped; changes logged in `policy_changes`; the trade-off is stated in the evidence-audit narrative. |
| A4 | Small-cell scope and roles | **Accepted.** `small_cell_policy` is per client (default k = 10; Richmond none). `leadership` and `aid_office` both see all views including small cells; `enrollment_team` unchanged. Cat and Richmond staff have signed off; the written record (date, scope, names of roles) goes in the SOW and the alignment-gate packet. |
| A5 | Dashboard order (OD-07) | **Accepted.** Scenario evaluator (view 2) and policy grid (view 3) ship in the first delivery with the Excel workbook. |
| A6 | "Tuition scenarios [to build]" | **Accepted.** Replaced by the lever design (V27-11); net-price response moves to section 11. |

---

## B. Methodology (`02_methodology_v2.7.md`, written from v2.6; v2.6 stays beside it)

| ID | Where | Change | Reason |
|---|---|---|---|
| V27-01 | Section 5, Constraints, **Guardrail [S5-5]** | Delete the guardrail. Add a step-size report: award differences between adjacent cells, shown as a plain table with no threshold and no flag. | Decision 2. Fixture check: the guardrail would flag 2 to 10 cells in each YA scenario (up to 26% of admits). |
| V27-02 | Section 4, Response model, **Support** bullet 3 | Delete "First offers may be cut ... only within the guardrail". Replace with: first-offer cuts are allowed; the evidence label (`observed` or `extrapolated` against the cell's historical award range) reports how well the response is known and never blocks a grid. The first-offer increase limit (largest tested bonus; with no test, the largest discontinuity jump) and the no-anchor rule stay for **Frankel-recommended** grids. | Decisions 1 and 2; A1. |
| V27-03 | Section 5, Targeted objectives, **Median constraint [E8]** | Strike "At the 5%-of-tuition guardrail, aid alone cannot raise Richmond's median." Say instead that whether aid can move the median is answered by the grid evaluator and the screen re-run (V27-05). Keep the expectation-only constraint and the separate P(median holds), with the closed form `P = 1 - Phi((-0.5 - m)/sqrt(V_m))`, validated against simulation within 0.01 on the YA scenarios. | Guardrail removal; prototype spec section 5. |
| V27-04 | Section 4, Price-test screen, worked example and **[E7]** bullets | Mark the "Not recommended" verdicts at +/-3% and the statement "a position target does not raise the value of a test at the 5% guardrail" as **computed under the guardrail; superseded pending re-run**. Richmond's band (+/-4 on 140) is about +/-2.9%, so the +/-3% row is the relevant one. | The admissible set is larger without the guardrail, so EVPI may rise. Do not quote the old verdicts to the client. |
| V27-05 | Section 4 and section 13 | New open issue **O36**: re-run the screen (stylized pools and the production optimizer on a 509-calibrated pool) without the guardrail, with the median floor, at +/-3%, +/-5%, +/-10%. Report before any client statement about a price test. | Section 4 already says the production screen is untested; this makes the dependency explicit. |
| V27-06 | Section 5, Policy grid scope, **Fixed thresholds** | Replace "frozen for at least two cycles" with: cut points are the client's declared bands, used as given; changes take effect at cycle boundaries and are logged in `policy_changes`; Frankel-computed cut points (trailing three cohorts) are frozen for the cycle only. Keep the discontinuity log, now described as informational. | Decision 2; A3. |
| V27-07 | Section 5, **Cells** count rule and law profile | Split "cells" in two. **Decision layer:** parameters at most floor(projected admits / 30) (21 at Richmond), built by merging adjacent LSAT bands within residency x GPA class (3.83 and above, other) until each group has 30 admits. On the YA fixture this gives about 13 groups (16 to 17 at 20 admits), plus one out-of-state incentive, 14 in total. **Policy of record:** the fine matrix rendered from the decision layer by a deterministic rule; a client may also author fine cells directly. The policy lookup (FR-53) returns the fine-matrix award of the student's cell. | Decision 3; fixture sizing (7 of 68 fine cells have 30 or more admits). |
| V27-08 | Section 5, Cells (law profile), and Consumer capacity tier subsection | Replace "position band (5) x market (home state / other)" by the merge-rule profile above for Richmond; keep the generic profile as the default for clients without a fine matrix. Leave the capacity-tier rules unchanged (no tier in the law grid by default). | Decision 3. |
| V27-09 | Section 5, **Ladder and cap** | Note that the optimizer's ladder (law: $2,500 steps) is a solver setting and does not limit client-authored awards, which the evaluator accepts at any amount up to tuition (the prototype renders schedules at $500). | Decision 1. |
| V27-10 | Section 5, new subsection **Scenario evaluator (client-authored grids)** | Define the ledger: apps (pool multiplier at LSAT 165 and above), admits (rate), award (after tuition scaling and out-of-state incentive), yield (response plus yield shift, clipped), enrolled, merit, need (fixed rate per enrolled student), NTR, discount. State: single reference evaluator (the optimizer's projected class, spend and NTR for a grid equal the ledger's); yield held constant when admit rates change; Low, Middle, High cases; closed-form class, median and NTR probabilities with a common-shock term; labels per A1; goal-seek as a linear planning helper, not the optimizer. Reference: prototype spec sections 3, 5, 6A. | Decisions 1, 5, 6. |
| V27-11 | Section 5, Solver, scenarios, and outputs: **Tuition scenarios [to build]** | Replace by the lever set: tuition migration by year (default 6.0% for 2027), class size (default 140), out-of-state incentive, yield shift, with what-if strips. Say plainly that tuition changes NTR arithmetic only; applications and yield do not respond unless the analyst enters a pool multiplier or a yield shift. Net-price response moves to section 11. | A6; decision 6. |
| V27-12 | Section 5, Outputs | Add: scenario ledger results, the fine matrix, the step-size table, a planning-assumptions block (admit rates, pool multiplier, tuition migration, class size) kept apart from aid policy. | Decision 5. |
| V27-13 | Section 2 (descriptive layer, line 36) and market reporting (line 53) | Make "pool markets under 10" and complementary suppression a `small_cell_policy` setting (default k = 10). State that Richmond's setting is none, with the named roles. | Decision 4; A4. |
| V27-14 | Section 9, new subsection **Small-cell disclosure [v2.7]** | Define the policy, who sees small cells, why it is acceptable here (authenticated named client roles; Cat's clearance; counsel), what stays true (no student-level rows, no ZIP5, no exact dates, no student keys), and the residual risk: a cell of one or two students in a small class can be recognizable to people who know the class. Add the item to the alignment-gate packet, with the record of Cat's and Richmond staff's sign-off. | Decision 4. |
| V27-15 | Section 6, Uncertainty | Add the yield-shift strip and the class-size and tuition what-ifs as shown-with-range views. State that the common-shock SD (0.10) is illustrative until calibrated to the out-of-time forecast error (new open issue **O37**). | Prototype spec D6; NFR-04. |
| V27-16 | Section 11, Future refinements | Add rows: net-price yield response; USNWR planner feed; Slate-based pool-growth pacing; market-level geography (states, MSAs, ZIP3) after about two cycles; admit-rate dimension in the optimizer; marginal-admit yield. Section 11 already lists "Sticker-price optimization": keep it, distinct from net-price response. | CLAUDE.md deferred list. |
| V27-17 | Section 12, Known limitations | Add: (a) the evaluator's response is based on client-input until an anchor exists; (b) no sticker-price demand effect; (c) yield constant when admit rates move; (d) class-size what-if scales the mix proportionally; (e) independence across cells in the closed form, checked against simulation; (f) client-authored and fine-matrix evaluation has no equity audit until the alignment gate runs it on the rendered matrix. | Honesty section. |
| V27-18 | Section 14, Closed decisions; Appendix B | Record decisions 1 to 7. Mark F20 (guardrail scale) **superseded v2.7**. | Traceability. |
| V27-19 | Appendix C, Rules | Delete "The per-cell guardrail ... stays." Keep floors and shadow prices. Add that floors apply to segment averages of the rendered fine matrix, weighted by projected admits. | Decision 2; A2. |
| V27-20 | Section 1, Scope; Section 13 | Add the scenario evaluator to scope. New open issues: **O36** screen re-run, **O37** shock calibration, **O38** evaluator placeholder slopes (0.5, 1.0, 1.5) versus the anchor when one exists, **O39** discontinuity evidence after the freeze is dropped, **O40** small-cell disclosure record. | Housekeeping. |

---

## C. S1 requirements (`S1_Requirements_and_User_Stories.md`, edited in place with [v2.7] tags)

| ID | Item | Change |
|---|---|---|
| V27-21 | FR-29 (law grid) | Cells become the decision layer (count rule applies to it); the fine matrix is the policy of record and is rendered by rule. Acceptance: decision-layer parameters at most floor(admits / 30); fine-matrix award for every cell equals the rule's output. |
| V27-22 | FR-30 | Remove "freeze for at least two cycles"; keep immutability within a cycle and the `policy_changes` log. Discontinuity log stays, informational. |
| V27-23 | FR-31 | Add: the choice rule applies to Frankel-recommended grids; client-authored scenarios are evaluated, not chosen. Add: optimizer and ledger give identical class, spend and NTR for the same grid (test). |
| V27-24 | **FR-33** | Retire the 5% guardrail. Replace with FR-33a: publish the step-size table; no flag. Keep the ID in the traceability table as "retired v2.7". |
| V27-25 | FR-34 | Unchanged except that floors are evaluated on the rendered fine matrix (A2). |
| V27-26 | FR-36 | Add the closed-form P(median holds) and its validation tolerance. |
| V27-27 | FR-40 | Remove "which floors and guardrail cells bind" (floors only). Add the fine matrix, the step-size table, the planning-assumptions block and the scenario results with their labels. |
| V27-28 | FR-52, **NFR-01**, FR-61 | NFR-01 becomes: no student-level data in Supabase or the dashboard; small-cell suppression follows `small_cell_policy` (default k = 10; Richmond none). FR-52's seven tests become: test 2 checks the configured policy; test 5 keeps its budget-cap and excluded-group checks and drops its maximum-cut assertion (the line that enforces the guardrail); a step-size-report test is added as test 8. FR-61 adds the `aid_office` role (the database enum lacks it) and gives `leadership` and `aid_office` all views with small cells. |
| V27-29 | FR-55, FR-56 | FR-55 becomes the **scenario evaluator** view: levers (admit rate, pool multiplier, award, specialty, need, tuition migration, class size, out-of-state incentive, yield shift), Low, Middle and High, what-if strips, labels per A1; leadership sees headline scenarios and the fine matrix. FR-56 shows the fine matrix, projected yield and step sizes, with no guardrail flag. |
| V27-30 | **New FR-71 to FR-76** | **71** scenario ledger (single evaluator). **72** formula-driven Excel scenario workbook as a deliverable, live formulas, no macros. **73** reconciliation: Excel, dashboard and policy document agree to the dollar for the same run. **74** what-if levers and strips. **75** goal-seek helper (linear, planning only). **76** `small_cell_policy` configuration and the role map. |
| V27-31 | Section 2 roles | `leadership`: all views, with the fine matrix and small cells. `aid_office`: all views, with small cells (A4). `enrollment_team` unchanged. Add `aid_office` to the database role enum and RLS. |
| V27-32 | Section 3 evidence states | Add the evaluator as a deliverable in all four states with the "Response based on client-input" label. |
| V27-33 | Section 5 stories; section 7; section 8 | Story 6 and Story 7 acceptance text mentions guardrails: remove. Add **Story 8**: dean compares four scenarios with class size and tuition what-ifs. Section 7: keep sticker-price optimization out of scope, add the deferred list. Section 8: add the workbook milestone. |
| V27-34 | OD-07, CONTR-02, CONTR-05 | OD-07: apply A5. CONTR-02: the guardrail no longer limits redistribution; the discount rate is an evaluator output and an optional constraint. CONTR-05: tuition migration is now a lever; the renewal rule (OQ-02) stays open and the multi-year sheet is a stub until it is answered. |

---

## D. Roadmap (`03_technical_roadmap_v2.7.md`)

| ID | Where | Change |
|---|---|---|
| V27-35 | Step table: S2, S6, S7, S8, S9 | **S2:** the law world (W0L) takes its shape parameters from the fixture check (prototype spec section 10) including the confounding trap; synthetic cell generator is a stopgap until W0L exists. **S6:** add `award_usd` to cells; unsuppressed cell export for named roles; `small_cell_policy` on engagements; `aid_office` in the role enum and RLS; tables for scenario levers, runs and results; the `suppressed` check constraint follows the policy. **S7:** requirements in V27-29 and V27-37. **S8:** replace the suppression control with the disclosure policy, roles and packet item (V27-14). **S9:** add ledger-versus-simulation and Excel-versus-Python reconciliation tests; drop the maximum-cut assertion from test 5. |
| V27-36 | Section 3 pipeline outputs | Add `scenario_levers`, `scenario_results`, and the fine-matrix policy file; `policy_grid.csv` loses the guardrail column and gains the step-size columns. |
| V27-37 | Section 4 dashboard | View 2 becomes the scenario evaluator; view 3 shows the fine matrix with step sizes and no guardrail; roles per V27-31; design constraint "never show a number without its range" is met by the Low, Middle, High cases and the strips. |
| V27-38 | Section 5 build phases | Insert **Phase 1b: scenario ledger and Excel workbook**, built first in `prototypes/scenario_workbook/` and promoted into the pipeline after Jason's review of the render. Move dashboard views 2 and 3 earlier (A5). |
| V27-39 | Sections 6 and 7 | Section 6 item 1 (grid dimensions) restated as the decision layer. Add risks: a client reads an NTR labeled "Response based on client-input" as a forecast; small-cell recognizability; the dashboard and Excel drifting apart (mitigated by one ledger and test 73). |

---

## E. `CLAUDE.md`

| ID | Rule | Change |
|---|---|---|
| V27-40 | "Student-level data never goes to Supabase ... cells under 10 suppressed." | "Aggregates only. Small-cell suppression is the per-client `small_cell_policy` (default k = 10). Richmond: no suppression, for authenticated named client roles (Jason, with Cat's clearance, Nov 5, 2026)." Enforcement text for `schema.sql` follows. |
| V27-41 | "No price level change without design-based evidence." | Add: "The scenario evaluator scores client-authored scenarios with a response based on client-input and recommends nothing; its outputs carry the label "Response based on client-input"." |
| V27-42 | Commands block ("7 tests") and "guardrail" wording | Update the test count and names after test 2 changes, test 5 loses its maximum-cut assertion and test 8 is added. |
| V27-43 | Tags | Add **[v2.7]** and IDs **V27-n**; keep the collision note. File map: add this change list, `CHANGELOG_v2.7.md`, and the v2.7 documents. |

## F. Code and tests affected (implementation phase; listed so nothing is missed)

`efa_fao/src/efa_fao/pipeline/optimize.py` (`max_cut_k` guardrail path), `aggregate.py` (suppression k and complementary suppression), `efa_fao/sql/schema.sql` (the `suppressed` check, role enum, RLS), `efa_fao/tests/test_guardrails.py` (tests 2 and 5, and a new test 8), `run_pipeline.py` (`award_usd`, scenario outputs), `config/` (small-cell policy, ledger parameters). **None of these is touched while the spec phase runs.**

## G. Client-facing consistency (check before the Richmond follow-up)

`01_executive_read_v2.6.md` item 12 ("cells under 10 suppressed, enforced in the database") and line 67; pitch and pricing decks (OD-03 already flags the privacy paragraph); the data request v3 text on small cells; any statement to Richmond that a price test is not recommended (depends on O36).

## H. Order of work and approvals

1. A1 to A6: answered Nov 5 (section A). Done.
2. I write `02_methodology_v2.7.md`, `03_technical_roadmap_v2.7.md`, `01_executive_read_v2.7.md`, `CHANGELOG_v2.7.md` and the in-place S1 edits, each change carrying its V27 tag.
3. A separate review pass on the changed sections only (v2.6 was not separately audited; the guardrail and screen edits are the risky ones).
4. Then S6 and S7 detail and the pipeline changes in section F.
The prototype (Phase 1 to 4) does not wait for steps 2 to 4; A1 (label) and A4 (roles) are settled, so it can start now.
