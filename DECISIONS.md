# EFA + FAO: decision log

**Owner:** Jason Cohen | **Started:** November 16, 2026 | Replaces, as the place to look up decisions, `Change_List_v2.7_draft.md`, `Spec_v0.5_Change_List_draft.md` and `CHANGELOG_v2.4.md` to `CHANGELOG_v2.7.md` (all in `_superseded/`, unchanged, for history). Add new decisions at the top of section 1 with a date, the decider and the documents changed. IDs: V27-n, V27A-n (v2.7 change lists), C-n and D-n (prototype spec), Bn-m (Session B audit findings), A1-n to A3-n (Session A).

## 1. Decisions by date

### November 17, 2026 (Jason): Phase 1 review (`Review_Phase1_Build.md`)

Applied as spec v0.6.1 (tags **[v0.6.1, R-n]** and **[v0.6.1, OP-n]** for the builder's open points).

| Decision | IDs |
|---|---|
| Excel computes yield from the same formula as Python, in one Ledger column; the Response rung table is display only; both switch to rung interpolation together when the pipeline supplies a rung table (option A) | R-01, OP-2 |
| Phase 1.1 fix pass before Phase 2: Python tests for every interface-contract output (test 19) and an on-demand mutation check (test 20); shrink path leaves uncut cells' rates unchanged; scaled net-tuition example uses base-cycle awards | R-02 to R-05, R-07 |
| Spec records the code's unstated choices: double clip, 90% ranges clipped at zero, pooling fallback chain, fractional admits | R-08, OP-7a, OP-7b |
| Full-tuition flag per cell (Levers column, inherited from the parent); `segment` scenario field; GPA median threshold equals the class boundary | OP-1, OP-5, OP-7d |
| Class-band probability asserted at expected class 50 or more; segment "approximate" flag below 30 expected; rho applies to the median in test 4 | OP-3, OP-4 |
| Test 5 is a calibration check of the stopgap generator; its confounding row is reported, not asserted, until W0L | R-06, OP-6 |
| Richmond tuition stays null in config until Richmond's published figures and OD-09 arrive; needed before Phase 3 | OP-8 |

### November 16, 2026 (Jason): Session B design audit accepted in full

Source: `Audit_Session_B_Design_Report.md`. Applied in `Prototype_Spec_Scenario_Workbook_v0.6.md`, `02_methodology_v2.8.md`, `S1_Requirements_and_User_Stories.md` v1.3, `03_technical_roadmap_v2.8.md`, `01_executive_read_v2.8.md`, `Handoff_Prototype_Phase1.md`, `CLAUDE.md` and the data request v3 source. Tags: **[v0.6, Bn-m]**, **[v2.8, Bn-m]**, **[v1.3, Bn-m]**.

| Decision | Finding IDs |
|---|---|
| All fixes in Parts B1 to B5 adopted as proposed | B1-1 to B1-25, B2-1 to B2-11, B3-1 to B3-13, B4-1 to B4-9, B5-1 to B5-6 |
| Metric definitions adopted (methodology Appendix F), including two named NTRs (`ntr_y1`, `ntr_horizon`) and `discount_entering_y1` | B3, B3-1, B3-2 |
| Three simplifications: (1) workbook first, dashboard views 2 and 3 as an add-on after the core computation; goal-seek and the schedule deferred; (2) pool strip in place of tripwires, two net-tuition lines in place of the net-price block, simulation sheet removed (tests keep simulation); (3) general priority segment and generic score and year names before Phase 1 | B7 ranks 1 to 10 |
| Base yield: partial pooling (k = 20), re-centered at the latest award | B4-5, B1-15 |
| Shrink path protects segment cells below the median threshold only | B1-16 |
| Median basis: unscored excluded by default, pending the 509 instructions (O41) | B3-3 |
| Year shock calibrated from public 509 and IPEDS data; world W22 | B4-1 |
| Cross-client empirical prior removed | B5-5 |
| Richmond's first award decisions are for the class entering fall 2027; Must list by February 2027 | B6 |
| Richmond data handling is Jason's and outside the spec | B6 |

### November 16, 2026 (Jason): Session A follow-ups
- Richmond counts are application, admit and **deposit** counts for the last three cycles; pacing against the prior two cycles at the same week (A1-12).
- The five-year plan and undergraduate tuition gap are deferred (A1-13).
- Data request generator bug fixed; pitch-deck small-cell wording "by default; each client sets its own policy for named, authenticated staff".

### November 13, 2026 (Jason): Dean Rooksby's priorities (V27A-01 to V27A-07; spec v0.5 C1 to C29, D13 to D17)
- One combined target-state group (NY, PA), part of the foundational cell schema (generalized to a priority segment on Nov 16).
- Class target under a hard cap (140 this cycle), supported 100 to 140; glide path toward 100 to 115 over five years, Brandon to confirm.
- Shrink order: lowest LSAT band first, then GPA, target cells last (refined Nov 16, B1-16).
- Application lift for the target group included, default 0.
- Richmond planning tuition 5.5%, unconfirmed; reproduce mode 6.0%.
- Data request additions: state-level counts, pacing, tuition path, class path.
- Client facts from Dean Rooksby's note stay confidential to Richmond.

### November 4 and 5, 2026 (Jason): Richmond scenario workbook review (V27-01 to V27-43; A1 to A6)
- The 5% per-cell guardrail is removed (constraint, flag, report); a step-size table replaces it; segment floors stay.
- The threshold freeze is dropped for client-declared bands; changes logged at cycle boundaries.
- Policy of record is the client's fine matrix; the optimizer works on a decision layer of at most floor(admits / 30) parameters.
- Small cells: per-client `small_cell_policy`; Richmond's named roles (enrollment team, leadership, aid office) see small cells; Cat and Richmond staff signed off.
- A scenario evaluator is a deliverable in every evidence state, labeled "Response based on client-input"; one ledger feeds every rendering.
- Levers: tuition migration by year, class size, out-of-state incentive, yield shift.
- The YA workbook may be used as a validation fixture and for shape parameters (ranges only); it stays out of git, Supabase and deliverables.
- The scenario-workbook prototype may be built under `prototypes/scenario_workbook/`.
- Dashboard views 2 and 3 in the first delivery (A5): **superseded Nov 16** (workbook first).

## 2. Closed decisions (stay closed unless Jason reopens them)
- No third-party applicant-reported timing data.
- No per-student optimization; the policy grid and lookup replace it.
- No grid-tier price estimation (deferred, not specified).
- Protected attributes (race, ethnicity, gender) never enter a model, grid or target.
- No individual-level consumer credit data. The consumer ZIP layer follows methodology v2.6 rules (G1 to G4, P1 blocking, L1 and counsel before first grid use).
- Student-level data never goes to Supabase or a hosted dashboard.
- No price level change without design-based evidence; the evaluator recommends nothing.
- No mixing of one client's confidential information into another client's work, including pooled priors.

## 3. Deferred (decided not now; do not build or spec as active scope)
Net-price yield response; goal-seek helper and schedule authoring layer; dashboard views (add-on after the workbook); `MultiYear`, `Trajectory`, `ntr_horizon` in the evaluator, `discount_all`; the simulation sheet; per-state segments, MSAs and ZIP3 below the single segment; USNWR planner feed; Slate-based pool pacing; admit-rate dimension in the optimizer; marginal-admit yield; methodology sections frozen in v2.8 (price-test design and screen re-run, moderator discovery, increases-only evaluation, batch scoring, consumer ZIP module, boosted challenger, worlds W12 to W15 and W19 to W21L).

## 4. Open decisions and questions
| ID | Question | Who |
|---|---|---|
| OD-05 / O42 | Which discount rate Dean Rooksby means (entering class or all JD; fees); whether it is a hard constraint | Brandon |
| OD-08 | The class target path toward 100 to 115 | Brandon |
| OD-09 | The exact 2027 tuition increase and the path after it | Brandon |
| O41 | ABA 509 basis for unscored students in percentiles; how deferrals enter 509 yield | Jason (509 instructions) |
| O43 | Small-cell rule for files, the policy document and public material (methodology section 9) | Cat |
| O36 | Screen re-run without the guardrail (frozen until a client considers a price test) | Later |
| O37 | Year-shock calibration from public data | Phase 2 or before the live build |
| O40 | Record of the small-cell sign-off in the SOW and the alignment-gate packet | Jason |
