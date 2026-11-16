# v2.7 Change Log

**Base:** `02_methodology_v2.6.md`, `S1_Requirements_and_User_Stories.md` v1.0, `03_technical_roadmap_v2.6.md`, `01_executive_read_v2.6.md` (all kept unchanged beside the v2.7 copies, except S1, which is edited in place as v1.1). Changes are tagged **[v2.7, V27-n]**.
**Source:** Jason Cohen's decisions of November 4 and 5, 2026, after reviewing the Richmond scenario workbook; the change list is `Change_List_v2.7_draft.md` (decisions A1 to A6 answered November 5).
**Status:** Not separately audited. The guardrail, screen and small-cell disclosure edits are the ones to review first. Pending sign-off.

## Decisions (Jason, November 4 and 5, 2026)

| # | Decision | Where |
|---|---|---|
| 1 | Admit-rate levers are scenario inputs plus a goal-seek helper; admit-rate optimization later | Methodology 5 (evaluator), 11 |
| 2 | The 5% per-cell guardrail is removed (constraint, flag, report); a step-size table replaces it. Segment floors stay | Methodology 4, 5, Appendix C; FR-33, FR-33a, FR-34 |
| 3 | The threshold freeze is dropped for client-declared bands; changes logged at cycle boundaries | Methodology 5; FR-30; O39 |
| 4 | The policy of record is the client's fine matrix; the optimizer works on a decision layer of at most floor(admits ÷ 30) parameters (about 13 groups plus one out-of-state incentive at Richmond) (superseded in part by V27A-01) | Methodology 5; FR-29 |
| 5 | Small-cell handling is a per-client policy; Richmond's named roles (enrollment team, leadership, aid office) see small cells. Cat and Richmond staff signed off | Methodology 2, 9; NFR-01; FR-61, FR-76; O40 |
| 6 | A scenario evaluator is a deliverable in every evidence state; label "Response based on client-input"; one ledger feeds Excel, dashboard and policy document | Methodology 5; FR-71 to FR-75; roadmap 3, 4, 5 |
| 7 | Levers: tuition migration by year (default 6.0% for 2027), class size (default 140), out-of-state incentive, yield shift. Geography is one out-of-state incentive (superseded in part by V27A-01) | Methodology 5, 6; FR-74 |
| 8 | Net-price yield response, market-level geography, admit-rate optimizer dimension, marginal-admit yield, Slate pacing and the USNWR planner feed are deferred | Methodology 11; CLAUDE.md |
| 9 | Dashboard order: scenario evaluator and policy grid ship in the first delivery with the Excel workbook | S1 OD-07; roadmap 5 |
| 10 | The price-test verdicts were computed under the guardrail and are pending a re-run; not to be quoted | Methodology 4; O36; S1 section 8 |

## Edits applied

| File | Change |
|---|---|
| `02_methodology_v2.7.md` | V27-01 to V27-20: guardrail removed; support rule; median statement withdrawn; screen verdicts marked pending; cells split into decision layer and fine matrix; thresholds; ladder note; scenario evaluator subsection; tuition scenarios replaced; outputs; small-cell policy in 2 and 9; section 6 evaluator views; validation table; section 11 rows; section 12 limitations; Appendix B (F20 superseded); Appendix C; section 13 (O36 to O40); section 14 decisions |
| `S1_Requirements_and_User_Stories.md` (v1.1) | V27-21 to V27-34: FR-29, FR-30, FR-31, FR-33 retired, FR-33a, FR-34, FR-36, FR-40, FR-52, FR-55, FR-56, FR-61, NFR-01; new section 4.11 (FR-71 to FR-76); roles; evidence-state note; stories 6, 7 and new Story 8; sections 7 and 8; traceability; OD-07, CONTR-02, CONTR-05 |
| `03_technical_roadmap_v2.7.md` | V27-35 to V27-39: steps S2, S6, S7, S8, S9; outputs; dashboard views and roles; Phase 1b; open decision 1; risks; decision log |
| `01_executive_read_v2.7.md` | Status paragraph; item 12; the screen verdict statements; decisions 3 and 5; new decision 10 |
| `CLAUDE.md` | V27-40 to V27-43: small-cell rule; evaluator label under the price-change rule; tags; file map; test count note |

## Open issues opened

O36 screen re-run without the guardrail; O37 common-shock calibration; O38 evaluator slopes versus the anchor; O39 discontinuity evidence after the freeze is dropped; O40 small-cell disclosure record.

## Not changed

Statistics of sections 4 and 6 (apart from the screen's status), the choice rule, the weak-evidence state, increases-only evaluation, the whitelist, consumer ZIP rules, closed decisions. Code, schema and tests under `efa_fao/` are untouched; the implementation list is section F of the change list.

## Addendum, November 13, 2026 (V27A-01 to V27A-07)

**Source:** Dean Rooksby's priorities (note to Ryan Frankel, Nov 13) and Jason Cohen's answers the same day; the change list is `Spec_v0.5_Change_List_draft.md`. Tagged **[v2.7, V27A-n]**. Not separately audited.

| ID | Change | Where |
|---|---|---|
| V27A-01 | Combined target-state market tier (client-defined states; Richmond NY, PA) on every cell; one incentive whose scope is the target tier or all out-of-state; optional target-tier application lift and yield offset; target KPIs (enrolled with range, probability of a goal, cost per incremental enrollee, paid-anyway share) | Methodology 5, 11, 14; FR-74, FR-77; Story 6; roadmap S2 and decision log; spec v0.5 |
| V27A-02 | Class size as the target under a hard cap (140 this cycle); supported 100 to 140; five-year path toward 100 to 115 to be confirmed | Methodology 5, 14; FR-74, FR-78; Story 8; OD-05, new OD rows |
| V27A-03 | Shrink-path rule: lowest LSAT band first, then GPA, target tier last; evaluator-only | Methodology 5, 12; FR-78 |
| V27A-04 | Pool tripwires: linear and probability forms, downside (median) and upside (hard cap) | Methodology 5; FR-79 |
| V27A-05 | Net-price readouts: display only; the yield response stays deferred | Methodology 5, 14; FR-80; CONTR-05 |
| V27A-06 | Richmond planning scenarios use 5.5% tuition (unconfirmed); reproduce mode stays 6.0% | Methodology 5; FR-74; spec D4 |
| V27A-07 | Data request additions: aggregate counts by state for three cycles, weekly pacing, exact tuition and path, undergraduate tuition, class size path | Spec v0.5 section 15; roadmap S2 |

**Files touched:** `Prototype_Spec_Scenario_Workbook_v0.5.md` (v0.4 moved to `_superseded/`), `Handoff_Prototype_Phase1.md`, `CLAUDE.md`, `02_methodology_v2.7.md`, `S1_Requirements_and_User_Stories.md` (v1.2), `03_technical_roadmap_v2.7.md`, `01_executive_read_v2.7.md`. Code under `efa_fao/` is untouched. Still to do: the data-request source under `efa_fao/docs/data_request_v3/spec/` (V27A-07) and the pitch and pricing decks.
