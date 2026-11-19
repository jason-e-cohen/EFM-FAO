# EFA + FAO: decision log

**Owner:** Jason Cohen | **Started:** November 16, 2026 | Replaces, as the place to look up decisions, `Change_List_v2.7_draft.md`, `Spec_v0.5_Change_List_draft.md` and `CHANGELOG_v2.4.md` to `CHANGELOG_v2.7.md` (all in `_superseded/`, unchanged, for history). Add new decisions at the top of section 1 with a date, the decider and the documents changed. IDs: V27-n, V27A-n (v2.7 change lists), C-n and D-n (prototype spec), Bn-m (Session B audit findings), A1-n to A3-n (Session A).

## 1. Decisions by date

### November 19, 2026 (Jason): Phase 4 build

| Decision | IDs |
|---|---|
| Top-quartile merit share: unscored enrollees rank last (below every score band); the position straddling the quartile line counts in proportion; cells sharing a score band and GPA class are taken together | Phase 4 calls 1, 2 |
| `top_quartile_merit_share` joins the interface contract with its own named range (prefix `DIST`); the other Distribution figures keep their existing Summary ranges (one range per figure, Q-1) | Phase 4 call 3 |
| Summary PDF: fix the three remaining cosmetics (net-tuition line columns cut short, long column-A labels cut off, scenario headers not repeated on continued pages), since the Summary is the client-facing render | Phase 4 |
| Mutant N83 needs a test that checks a value, not only a crash; hand-run Excel comparison reports go to a build-specific file that tests never overwrite | Phase 4 |
| An independent reviewer pass covers Phase 2.2 and Phase 4 before the fix pass; a pre-delivery review and the Windows Excel check precede the first Richmond workbook | Process |

### November 18, 2026 (Jason): spec v0.6.3

Applied as section 0A of `Prototype_Spec_Scenario_Workbook_v0.6.md`: Brandon's points BM-1 to BM-6 as designed in `Review_Phase2_2_Plan.md` section 3 (for Phase 2.2), the Phase 3 reproduce rules (R3), and the Scenario 4 deliverable scope. Methodology Appendix F gains item 26 (score percentiles). Phase 2.2 runs from the `phase3-accepted` commit; reproduce-mode need-aid rounding per enrollee is added to it.

### November 18, 2026 (Jason): Phase 3 accepted

Reproduce mode meets its criteria: 57 of 57 derivable criteria pass (3 Baseline criteria not derivable from the file; 2 cells not reproducible from the file, excluded and counted). Desktop Excel parity measured on the reproduce sentinel build `08c50a6fabaf` (Excel for Mac 16): 29,063 formula cells, 0 value mismatches, 0 cells still at -999, 0 formula-text differences; the rounding probe gives 3 in Excel, Python and LibreOffice, so the 15-significant-digit rounding stands (`output/phase3/excel_compare_report.json`). Mutation checks: Python 115 of 115, Excel 75 of 75 (before the sentinel file-name fix, which changed no formula). The History sheet's 509 check confirms the lower-band mismatch (LSAT 25th percentile in 2024 and 2025, median in 2024); OD-14 holds Scenario 4's median and percentile rows.

### November 18, 2026 (Jason): 509 findings and Scenario 4 deliverable scope

| Decision | IDs |
|---|---|
| Scenario 4's first deliverable to Richmond carries class size, NTR, the pool strip and P(class > cap). Its median and percentile rows are held until Brandon says which LSAT the Yellow Arrows grid bands by (OD-14), because the fixture's lower LSAT bands disagree with the 509 and band-level results depend on the basis | R3-4, BM-7 |
| Tuition: the 509 figures stand for 2024 ($55,550) and 2025 ($57,700); 2027 is $63,500 (Brandon, confirmed by Jason Nov 18; Board approval February 2027) | BM-2, OD-09 |
| Percentile placeholder: 25th percentile at LSAT 158 (the nearest band to Richmond's published 158 and 159) until Brandon confirms the target | BM-1, OD-13 |
| The three R3-4 additions are adopted: a 509 reconciliation check on the History sheet (report only), a data-request line asking for bands by highest LSAT, and the LSAT-basis question to Brandon | R3-4 |

### November 18, 2026 (Jason): Phase 3 reproduce mode (`Review_Phase3_Build.md`)

| Decision | IDs |
|---|---|
| Reproduce mode counts unscored and blank-GPA enrollees the "excluded" way, as the fixture does (18 of 18 groups) and as the ABA 509 does; one rule in live and reproduce modes. O41's basis question is closed; only the 509's interpolation convention is unknown, which does not matter at band resolution | R3 decision 1, O41 |
| Applications are rounded after the pool multiplier in reproduce mode only (`reproduce.round_apps_after_pool`) | R3 decision 2 |
| Cells whose base applications cannot be recovered consistently from the file are marked "not reproducible from the file", excluded from the criteria on both sides and counted; never invented. History shows unknown applications as blank | R3 decision 3 |
| Ledger rounding at 15 significant digits kept; confirmed in LibreOffice, to be confirmed in desktop Excel on the reproduce sentinel copy | R3 decision 4, R3-3 |
| Richmond's public ABA 509 figures for 2024 and 2025 entered in `config/richmond.yaml` for the History sheet's 509 reconciliation (report only) | R3-4 |

### November 18, 2026 (Jason): Scenario 4 in a Richmond deliverable (`Review_Phase3_Build.md` R3-2)

| Decision | IDs |
|---|---|
| Exception to the fixture rule: Scenario 4's levers from the Yellow Arrows workbook may be entered in a live build on Richmond's own cell data, and that workbook may go to Richmond's named roles through the secure channel, because it is Richmond's own scenario returned to Richmond. The Scenario 4 scenario file is generated at run time into a git-ignored path, never committed. All other fixture limits stand (no git, Supabase, dashboard, public or marketing use, or other clients' work); Scenarios 1 to 3 are not covered. Recorded in `CLAUDE.md` (rules). | BM-7, R3-2 |

### November 17, 2026 (Jason): Brandon Metheny's reply (`Review_Points_Brandon_Nov17.md`)

| Decision | IDs |
|---|---|
| Shrink path: NY/PA (segment) cells are protected only at or above `score.floor` (154); segment cells below 154 are trimmed in normal order (`trim.protect_segment: above_floor`) | BM-5 |
| The transform from Brandon's state counts to segment shares per cell is handled as the data arrives, outside this pass | BM-9 |
| BM-1 to BM-4, BM-6 to BM-8 and BM-10 go to a reviewer session for the v0.6.3 amendment and a Phase 2.2 plan | BM-1 to BM-10 |

### November 17, 2026 (Jason): Phase 2 accepted

Desktop Excel parity measured: the sentinel build (every cached value -999), recalculated and saved by desktop Excel, matched Python on every formula cell of every sheet with 0 mismatches (`tests/compare_excel_saved.py`). Phase 2 is accepted. Re-run after the P21 follow-up on build `a5d46aca1735` (synthetic world 101), saved by Microsoft Excel 16 for Mac: all 57,483 formula cells match Python, none still holds -999, and no formula differs from the build (`output/phase2/excel_compare_report.json`). Windows Excel is not yet checked; check it before the first workbook goes to Richmond.

### November 17, 2026 (Jason): Phase 2 review (`Review_Phase2_Build.md`)

Applied as spec v0.6.2 (tags **[v0.6.2, P2-n]** and **[v0.6.2, Q-n]**). Fixes P2-01 to P2-07 go to the Phase 2.1 fix pass.

| Decision | IDs |
|---|---|
| Test 3 adds an edge workbook that reaches every branch; desktop Excel parity is measured by comparing an Excel-saved copy with Python | P2-01 |
| Canonical range names are prefix + name in upper case, no aliases; `p_segment_goal_exact` added to the contract from Python; `award_matrix` is the resolved award on Levers | Q-1, Q-2, Q-3 |
| An "entered" award on a full-tuition cell is one that differs from the inherited award; it is counted and marked separately, not as a change | Q-4, P2-03 |
| Scaled net-tuition example: base-cycle lever award below base-cycle tuition, cells without the full-tuition flag | Q-5 |
| Narrative NTR range slot; Baseline line "no parent scenario" | Q-6 |
| Trim order stays fixed at build; Checks flags "rebuild needed" and a stale exact segment probability | Q-7, P2-06 |
| Budget check compares total aid by default, merit only by setting; Brandon to say which (OD-10) | Q-8e |
| Optional inputs `bonus_pool_usd` and `merit_actual_by_cohort` | Q-8d, Q-8f |
| Blank segment on Levers defaults to the only configured segment; the empty-segment scope error is a Check | P2-07 |
| Phase 2.1 review (`Review_Phase2_1_Fix_Pass.md`): the Excel comparison runs on the sentinel build and refuses anything else; the build id includes a hash of the generator code; one edge scenario sets a non-zero global shift with an in-state override; builder calls 1 to 4 and 6 accepted, call 5 changed | P21-01 to P21-03 |

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
| Phase 1.1 follow-ups: the full-tuition flag wins over an award typed into the cell, and Checks lists the conflict; `plan_year` is a label (tuition comes from the scenario's increase, inherited by children); the scaled-line example uses cells without the full-tuition flag; step sizes group by residency x segment x GPA; the band check runs on a second toy grid at class 50 or more | P1.1-1 to P1.1-5 |

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
- Richmond planning tuition 5.5%, unconfirmed; reproduce mode 6.0%. **Superseded Nov 18:** 2027 tuition is $63,500 in dollars (BM-2).
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
| OD-09 | 2027 settled at $63,500 (Nov 18); the 2026-27 base-cycle tuition for `tuition_base` and the path after 2027 remain open | Brandon / Jason |
| OD-10 | Whether Richmond's budget figure covers total aid (merit, need, specialty) or merit only | Brandon |
| OD-11 | Whether 140 was a hard cap in 2025 (the 509 first-year class was 146) | Brandon |
| OD-13 | The percentile target Brandon wants (placeholder 25th percentile at 158) | Brandon |
| OD-14 | Which LSAT the Yellow Arrows grid bands students by (highest, most recent or average); holds Scenario 4's median and percentile rows | Brandon |
| OD-15 | Whether "full ride" means full tuition with no stipend (BM-8) | Brandon |
| O41 | Basis closed Nov 18 (509 excludes unscored students, as the fixture does). Still open: the 509's exact percentile interpolation convention (immaterial at band level) and how deferrals enter 509 yield | Jason (509 instructions) |
| O43 | Small-cell rule for files, the policy document and public material (methodology section 9) | Cat |
| O36 | Screen re-run without the guardrail (frozen until a client considers a price test) | Later |
| O37 | Year-shock calibration from public data | Phase 2 or before the live build |
| O40 | Record of the small-cell sign-off in the SOW and the alignment-gate packet | Jason |
