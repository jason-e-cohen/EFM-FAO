# EFA + FAO v2.8: Roadmap to the Technical Spec

This is preparation for the spec phase, not the spec. It lists what the spec must decide, what is built, what v2.1 changes, and what remains. The methodology is in `02_methodology_v2.8.md` (earlier versions are in `_superseded/`; v2.8 edits are tagged **[v2.8, Bn-m]** by Session B finding; decisions are logged in `DECISIONS.md`); the v2 version of this roadmap is archived in `_archive_pre_review_2026-10-15/`.

**[v2.7] What changed.** The Richmond scenario workbook review (November 4 and 5, 2026) led to: no per-cell guardrail; the client's fine matrix as the policy of record; a scenario evaluator and an Excel scenario workbook computed by one ledger; small cells shown to named client roles; the aid office and leadership seeing all views. Items below tagged **[v2.7]** carry these changes.

**[v2.7, V27A] Addendum (November 13, 2026).** The evaluator gains a combined target-state market tier (NY and PA by default) with its own incentive scope and an optional application lift, class sizes from 100 to 140 under a hard cap of 140 this cycle with a shrink-path rule, pool tripwires and net-price readouts (V27A-01 to V27A-07; `_superseded/CHANGELOG_v2.7.md`). The prototype spec is v0.5; the market tier is part of the Phase 1 data model.

**[v2.8] Session B reconciliation (November 16, 2026).** Jason accepted the Session B design audit (`Audit_Session_B_Design_Report.md`) in full. For this roadmap: the **Excel workbook ships first** and dashboard views 2 and 3 become an add-on after the workbook's core computation is accepted; the target-state tier becomes a general **priority segment**; the tripwires become a **pool strip**; the net-price readouts become two lines; goal-seek, the schedule layer, the simulation sheet and the multi-year stubs are deferred; the prototype spec is **v0.6**. Richmond's first award decisions are for the class entering in fall 2027, so the workbook's must-have list lands by February 2027 (section 5A). Richmond data handling is Jason's and outside the spec.

**Guiding rule:** a feature is added only if it changes a recommendation or a client decision, and the lean Monte Carlo study shows it does so reliably. Deferred features and their triggers are listed in methodology section 11.

**Labels [v2.2].** S = spec step (S1 to S11). R = review finding (R1 to R12, labeled F1 to F12 in earlier versions). FR = functional requirement. S4-n and S5-n are numbered review edits within those steps. **[v2.5]** F1 to F20 are the re-review findings (methodology Appendix B). A1 to A33 are the audit's findings, E1 to E14 its required edits. Methodology section 13 also uses A1 to A5 for the audit's five tasks; cite audit findings as "audit A<n>".

**Spec steps and where they stand.** Each step is one document, written and reviewed in order.

| Step | Document | Source today | Status | Review |
|------|----------|--------------|--------|--------|
| S1 | Requirements and user stories | None | Not started | Jason signs off |
| S2 | Data contract and synthetic data specification | Data request, data dictionary | Partial; world library to define; add geography script and market fields; add external-data contract for ABA 509 and a law world calibrated to it. **[v2.6]** Add the `zip_key` contract, consumer fields, and the consumer synthetic worlds (W21, W21L). **[v2.7, V27-35]** The law world (W0L) takes its shape parameters from the Richmond scenario-workbook fixture check (admit-rate and yield trends, sparsity, the confounding trap); the prototype's cell generator is a stopgap until W0L exists | Jason signs off **[V27A-01]** Add `market_tier` to the cell aggregate and a target-share parameter to the law world; the data request adds aggregate counts by state, weekly pacing and the tuition and class-size paths (V27A-07). |
| S2b | **Data request v3 and data dictionary** (client-facing, with an Excel field template) | `efa_fao/docs/04_data_request_v2.md` (v2.1 text, undergraduate-shaped), reference request from Jason, CDS 2025-26 template | **[v2.6] Draft built October 22 in `efa_fao/docs/data_request_v3/` (law and undergraduate documents, Excel templates, dictionaries, gap log).** Reconcile to the S2 data contract on sign-off, then promote over 04. Derived from the S2 data contract so request and contract cannot drift. Contents: Tier 1 and Tier 2 by program (law, undergraduate); law fields (LSAT, UGPA, JD-Next, position reference classes, commitment length, renewal rule, award mode, stipend flag); offer dates, versions and reason codes; capacity band; blinding question; price-test section by program; optional `zip_key` file (Appendix E.3); institutional reference (CDS or ABA 509) for reconciliation; secure transfer; checklist. A law Tier 1 version goes first | Jason signs off; then client review |
| S3 | Pipeline architecture and interfaces | Section 1 below | Needs typed interfaces. **[v2.6]** Add `load_zip_table`, `zip_index`, `fit_tiers`, `assign_tier`, `match_report`, `proxy_audit` | Opus review |
| S4 | Statistical methods | Methodology sections 2, 4 (including evidence audit, sample-size guide, and timing by wave), 6, 7, 10 | **[v2.5]** Re-reviewed (Opus 5.5) and audited (Fable 5.1); edits S4-1 to S4-14 and E1 to E14 merged; O1 to O3, O5, O7, O10 ruled. Awaiting Jason's sign-off | Review and audit complete |
| S5 | Optimization | Methodology section 5 (market tier, targeted objectives, policy lookup, program-length horizon, conditional-award persistence), Appendix C | **[v2.5]** Re-reviewed and audited; edits S5-1 to S5-10 and E3, E8, E9 merged; O4, O8 ruled. Awaiting Jason's sign-off | Review and audit complete |
| S6 | Database | `sql/schema.sql` (drafted, not applied) | Needs new tables (including `market_reference` for 509 data). **[v2.6]** Add `zip_key`, `student_consumer`, `consumer_gate_status` after the S4 and S5 consumer review. **[v2.7, V27-35]** Add `award_usd` to cells; an unsuppressed cell export for named roles; `small_cell_policy` on engagements (the `suppressed` check follows it); `aid_office` in the role enum and RLS; tables for scenario levers, runs and results | Security review |
| S7 | Dashboard | Section 4 below | Requirements only; no wireframes. **[v2.7, V27-35]** View 2 becomes the scenario evaluator, view 3 shows the fine matrix with step sizes, roles gain the aid office; views 2 and 3 ship in the first delivery with the Excel workbook | Walkthrough with an enrollment user |
| S8 | Privacy, equity, and alignment controls | Methodology section 9 | Drafted; equity audit and funnel outputs not yet reviewed. **[v2.6]** Add the consumer purpose statement, construction rule, P1 gate, P2 to P4 reports, and the license posture. **[v2.7, V27-35]** Replace blanket suppression by the small-cell disclosure policy (methodology section 9), the role map, and the sign-off record in the alignment-gate packet | Opus review, then client alignment review |
| S9 | QA and Monte Carlo release gate | Methodology section 10 | **[v2.5]** Thresholds revised in the re-review (21 worlds; 200 and 100 seeds) and audit-checked arithmetic; O6, O16, O19 ruled; law world calibrated to 509; W12 variant added (E1). **[v2.6]** Consumer worlds W21 and W21L; G2 power at law size (O35). **[v2.7, V27-35]** Add ledger-versus-simulation and Excel-versus-Python reconciliation tests; drop the maximum-cut assertion from guardrail test 5; add a step-size test (test 8) | Opus review of thresholds |
| S10 | DevOps and runbook | None | Not started | Jason signs off |
| S11 | Implementation plan for Claude Code | None | Not started | Final readiness check |

## 1. Architecture

```
Client secure transfer (de-identified)            Compute environment (never Supabase)
  students / aid_offers / fafsa / price_test  -> validate -> prepare -> estimate -> backtest -> optimize grid -> aggregate
  weekly in-cycle export (yield season)       -> validate -> pacing / melt lookups -------------------------> aggregate
                                                                       |                                         |
                                                             model_run.json (lineage)             aggregate CSV / JSON artifacts
                                                                                                                 |
                                                                                        Supabase (Postgres + RLS) <- service role writes
                                                                                                                 |
                                                                                       Vercel (Next.js) <- user JWT reads under RLS
Student-level returns to the client (for example a melt list, batch scores, or the policy lookup) go back through the client's secure channel, never Supabase.
```

**Recommended stack**
- **Compute:** Python 3.12, numpy, scipy (HiGHS MILP), pandas, statsmodels, and `rdrobust` for the discontinuity. Standard, well-tested packages replace hand-built estimators where one exists, which lowers maintenance and makes review easier.
- **Orchestration:** a plain CLI plus a Makefile and GitHub Actions. Move to Prefect or Dagster only when many institutions run on schedules.
- **Database:** Supabase Postgres with row-level security, aggregates only (schema in `sql/schema.sql`).
- **Dashboard:** Next.js on Vercel, Supabase client, one chart library. Static JSON snapshots per published run.
- **Auth:** Supabase Auth; two client roles (`enrollment_team`, `leadership`) plus internal `analyst`.

## 2. What is built, and what v2.1 changes

| Module | Status | v2.1 action |
|--------|--------|-------------|
| Synthetic institution generator with ground truth | Built | Extend with the 21 Monte Carlo worlds **[v2.5]** |
| Validation, cleaning rules, QA log | Built | Keep |
| Feature layer with leakage and protected-attribute controls | Built | Add decision-date rule, academic index, excluded-groups table |
| Estimators: legacy replica, observational, experiment, discontinuity, anchored, hybrid | Built | Remove segment pattern, kappa, and scaling; replace discontinuity with `rdrobust` plus diagnostics; add anchor-to-logit conversion and its test |
| Forecast model | Built | Reduce to a fixed 10 to 12 feature regularized logit; add out-of-time recalibration |
| Retention model and multi-year revenue | Built | Replace with a retention lookup by segment |
| Optimizer (MILP) | Built (per student) | Rebuild as a policy grid (default 75 cells) with the three-scenario choice rule |
| Bootstrap uncertainty and realization ratio | Built | Retire; replace with three sensitivity scenarios and a backtest diagnostic |
| Baselines | Partial | Add proportional rescale, need-first fill, fence-sitter rule; match spend within 1% |
| Aggregation with disclosure control | Built | Replace with a fixed, non-overlapping table set |
| Equity audit | Built | Keep; re-run under v2.1 |
| Pacing, melt, loan-cap exposure, Clearinghouse, survey, peer pricing | Not started | New, descriptive only |
| Supabase schema with RLS | Drafted, not applied | Update for new tables; migration test |
| Data dictionary, source taxonomy, data request | Drafted | **[v2.6]** Data request moves to S2b (full rewrite). Add Tier 1 / Tier 2, Grad PLUS and PLUS denial fields, CSS Profile fields, program, graduate test scores, new test arms |
| Guardrail tests | 7 passing (verified October 22, 2026 under Python 3.12 with scipy and HiGHS) | Add: anchor conversion, spend matching, support rule. **[v2.6]** Add the consumer tests: no ZIP5 or segment codes in any analysis or output table; tier construction takes no race, ethnicity or gender argument; tier rejected as a grid dimension unless every required gate passed; raw segment codes rejected as features; no ZIP-to-segment pairs and ZIP outputs of at least 3 segments and 10 students; P4 never a pass or fail field |
| Batch scoring and policy lookup [v2.3] | Not started | New optional add-on; secure-channel delivery only |
| Geography derivation script and market layers [v2.3] | Not started | New; client-side script for CBSA and distance band; market funnel and penetration |
| Evidence audit [v2.3] | Not started | New scoping module feeding the price-test screen |
| Targeted objectives [v2.3] | Not started | New constraints and weights on whitelisted policy attributes |
| External reference data ingestion (ABA 509) [v2.4] | Not started | New; versioned annual loads from the existing 509 dashboard or the public files; aggregates only |
| Wave-stratified timing analysis [v2.4] | Not started | New; per-wave slopes within the price test |
| Dashboard | Not started | Five views (section 4) |
| Loader, CI, scheduling | Not started | Small |

## 3. Pipeline outputs and their tables

| Output file | Table | Dashboard use |
|-------------|-------|---------------|
| `funnel_cells.csv` | `funnel_cells` | Funnel and pacing view. **[v2.7]** Gains `award_usd` and `market_tier` by cell and cohort, and an unsuppressed export for named roles under `small_cell_policy` |
| `efa_drivers.csv` | `efa_drivers` | Funnel and pacing view (drivers panel) |
| `pacing.csv` [new] | `pacing` | Same date last year, plan, projected census |
| `melt_segments.csv` [new] | `melt_segments` | Melt risk by segment |
| `scenarios.csv` | `scenarios` | Scenario planner, each scenario at low, middle, and high sensitivity |
| `policy_grid.csv` [new] | `policy_grid` | Current versus recommended award by cell, projected yield. **[v2.7, V27-36]** Fine-matrix cells; loses the guardrail column; gains step-size columns |
| `scenario_levers.csv`, `scenario_results.csv` [new, v2.7] | `scenario_levers`, `scenario_results` | Scenario evaluator: levers per scenario and ledger results at the L, M, H cases, with what-if strips; one ledger feeds the dashboard, the Excel workbook and the policy document |
| `price_response_curves.csv` | `price_response_curves` | One curve per segment from the single slope, three sensitivity lines |
| `market_context.csv` [new] | `market_context` | Loan-cap exposure, lost-to institutions, peer net price, survey summaries |
| `market_reference.csv` [new, v2.4] | `market_reference` | Market context view: peers, tuition, grants, conditional scholarships |
| `market_funnel.csv` [new, v2.3] | `market_funnel` | Funnel and pacing view, by market |
| `evidence_audit.csv` [new, v2.3] | `evidence_audit` | Analyst view: price evidence available and test power |
| `batch_scores` [new, v2.3] | None | Student-level; never loaded to Supabase; delivered through the client's secure channel |
| `equity_audit.csv` | `equity_audit` | Equity audit |
| `model_run.json` | `model_runs` | Lineage, anchor evidence, diagnostics, backtest result |
| `validation_*.csv` | `validation_*` | Synthetic demo only |

Retired: `projection_segments.csv` (folded into `policy_grid`) and `model_coefficients.csv` (the browser probability calculator is dropped).

## 4. Dashboard requirements to specify

**Views**
1. **Funnel and pacing** (enrollment team): conversion by stage with one or two dimensions from the approved table set, pacing against last year and plan, projected census, melt by segment, drivers panel labeled associational.
2. **Scenario evaluator [v2.7, V27-37]:** client-authored and recommended scenarios with levers (admit rate, pool multiplier, award, tuition migration, class size under a cap, out-of-state incentive with its scope, target-tier application lift, yield shift), class, revenue, spend and discount rate at low, middle and high, what-if strips, and the label "Response based on client-input" where it applies.
3. **Policy grid [v2.7, V27-37]:** current versus recommended or client-authored award by fine-matrix cell, with projected yield and the step-size table (no guardrail); exportable as the scholarship policy document.
4. **Market context:** loan-cap exposure by program, lost-to institutions and net-cost gaps, peer pricing (for law schools, from public ABA 509 data), survey findings.
5. **Equity audit:** allocation and yield by group, flagged audit-only.

Methodology, data quality, and lineage are a linked panel on every view, not a separate view.

**Roles [v2.7, V27-31]:** enrollment team, leadership and the aid office see all views; small cells follow the engagement's `small_cell_policy` (Richmond: shown to these roles); analyst (internal) also sees draft runs and publishes.

**Design constraints:** never show a number without its sensitivity range, interval, or a stated reason it has none; every chart links to its definition; export only aggregates.

## 5. Build phases

| Phase | Deliverable | Acceptance test |
|-------|-------------|-----------------|
| 0. Repo hardening | CI, lint, tests in the pipeline, pinned dependencies, `uv` lock | Tests pass in CI from a clean checkout |
| 1. Lean model refactor | Single anchored slope, `rdrobust` discontinuity, academic index, excluded groups, policy-grid optimizer, three-scenario evaluation, spend-matched baselines, forecast recalibration | Estimator regression check: the per-student one-slope optimizer reproduces the v2 backtest result (+2.7% realized, one seed) within tolerance. The policy-grid result is judged in the Monte Carlo gate against the spend-matched baselines, not against +2.7%. Anchor conversion test passes; runtime under the v2 run's 141 seconds |
| 1b. Scenario ledger and Excel workbook **[v2.7, V27-38; v2.8]** | Reference ledger, closed-form risk, shrink path, strips, formula-driven workbook (goal-seek deferred); built first in `prototypes/scenario_workbook/` (spec `Prototype_Spec_Scenario_Workbook_v0.6.md`), promoted into the pipeline after Jason reviews the render | Excel equals Python on synthetic worlds; reproduce mode matches the client's reference workbook; optimizer and ledger agree on any grid |
| 2. Monte Carlo gate | **[v2.5]** 21 worlds; 200 seeds for W0 and W0L, 100 for the others. **[v2.8, B7-13]** Each release runs W0, W0L, W22 (year shock) and W5, W6, W8 to W11; the others run when their feature is in use | All baseline-world thresholds in methodology section 10 met; failures in the other worlds documented and flagged by diagnostics |
| 3. Database | Apply schema, migration tests, loader | Loader round-trips every CSV; RLS tests for all roles |
| 4. Dashboard v1 | Views 2, 3, 5 and the lineage panel on the synthetic run (**[v2.8]** an add-on after the Richmond workbook is accepted; it reads the same ledger outputs through the interface contract, spec v0.6 §15 item 11) | Walkthrough with an enrollment-team user; no student-level fields anywhere |
| 5. Monitoring and market context | Views 1 and 4; weekly in-cycle export and refresh | Pacing matches a hand calculation on synthetic data; refresh runs unattended |
| 6. Real-data pilot | One Tier 2 engagement (price test only if the suitability screen recommends one), with Clearinghouse match and survey | Data passes QA; backtest diagnostic reported; client alignment sign-off recorded |
| 7. Learning loop | Standing stratified price test; refit each cycle | Anchor interval narrows each cycle; deferred refinements evaluated against their triggers |

### 5A. Richmond 2027 workbook: critical path [v2.8, B6]

Award decisions for the 2027 entering class: the Must items land by February 2027. Build days are supervised Claude Code days; review hours are Jason's.

| Step | Must items | Build days | Review (h) | Target |
|---|---|---|---|---|
| 1 | Spec v0.6 (done Nov 16) | — | 2 to 3 | Nov 2026 |
| 2 | Phase 1: ledger, risk, response, trim, strips, segment, synthetic cells; tests 1, 2, 4, 5, 11 to 17 | 3 to 5 | 4 to 6 | Early Dec 2026 |
| 3 | Phase 2: workbook, tests 3, 8, 9, 18; Jason opens it in desktop Excel | 5 to 8 | 8 to 12 | Early Jan 2027 |
| 4 | Phase 3: reproduce mode against the YA fixture (test 6) | 2 to 3 | 2 to 3 | Mid Jan 2027 |
| 5 | Live Richmond build on Richmond's cell data and state counts (data handling: Jason); QA; labels; confidentiality check | 2 to 3 | 6 to 8 | Early Feb 2027 |
| — | Should: Distribution sheet and PDF render (Phase 4); pinned environment and versioned outputs | 2 to 4 | 4 to 5 | With steps 3 to 5 |
| — | Later: dashboard views 2 and 3; goal-seek and schedule; `MultiYear` and `Trajectory`; per-state segments; optimizer; screen re-run (O36) | — | — | After February |

### 5B. Annual cycle [v2.8, B5-2]

1. **After census (October):** load census actuals; calibration report comparing last cycle's adopted scenario (class, medians, `ntr_y1`, discount, segment enrolled) with actuals, each miss shown against its 90% range; add the client's forecast error to the record for s; log any policy change as a candidate qualifying change.
2. **Before the cycle (November to December):** roll the base cycle forward; refresh 509 or IPEDS reference data; refit the forecast; re-run the evidence audit; freeze and hash the cycle config; build the first workbook.
3. **In cycle (January to May):** weekly pacing loads; read the pool strip against pool growth to date; save every scenario revision as a new versioned build.
4. **Award decisions:** the adopted scenario is marked and frozen; step 1 compares it next year.

### 5C. Reproducibility and isolation [v2.8, B5-3, B5-4]

- Pinned environment: `requirements.lock` (exact versions) per build, hashed into `RunLog` and `model_run.json`; the repo `.venv` is macOS-only, so builds run on Jason's Mac.
- Versioned outputs: `output/<client>/<cycle>/<build_id>/`; workbook document properties carry a fixed creation time so builds compare by cell values and formulas.
- Commit the design set after each reviewed change set; tag releases.
- One client per pipeline run; each data batch carries `institution_id` and a run refuses a mismatch. Client data, fixtures and workbooks live outside the product code folder.
- Supabase isolation is by RLS on `institution_id`; the service role bypasses RLS, so write isolation depends on the pipeline check above.

## 6. Open technical decisions

1. **Grid dimensions:** default 75 cells (academic index quintile x need band x residency); whether program is added for some clients. **[v2.7, V27-39]** For a client with a fine matrix, the optimizer's decision layer is the merge-rule groups (about 13 at Richmond) plus one out-of-state incentive, and the fine matrix is rendered by rule.
2. **Retention priors** for multi-year scenarios when client history is short. (Horizon is decided **[v2.5]**: it equals the award commitment, three years for a renewable full-time JD award and as elected for undergraduate, and budget and revenue horizons must match.)
3. **Anchor pooling rule:** inverse-variance pooling with a 1.5 standard error disagreement flag, versus experiment-only once the test is mature.
4. **Excluded groups:** default list and client overrides.
5. **Refresh cadence** during yield season: weekly or biweekly.
6. **Student-level returns:** whether melt lists are offered at all, and the secure channel used.
7. **Tier 1 scope:** exactly which outputs a Tier 1 client receives without a price test.
8. **Graduate programs:** which programs enter the descriptive layers first.
9. **Scale:** shift to DuckDB and Parquet once any client exceeds about 1M student-term rows.
10. **Segment floors:** decided (confirmed October 20; first-generation is a client option).
11. **Price-test screen [v2.5, decided]:** the 2.3-point power rule is replaced by the value-of-information screen. Open: run it on the production optimizer with a 509-calibrated pool (the audit used stylized pools), make the capacity band a mandatory scoping input, and review the quantile margins if EVSI is negative.
12. **Alignment packet contents:** the sign-off is a one-page approval (decided); the scope of the legal-considerations note is open.
13. **Verticals and moderators:** per-vertical grid profiles (law and professional programs by relative position within the program) and the moderator discovery protocol (methodology section 4).
14. **Open design issues O1 to O19** (methodology section 13): **[v2.5, closed]** ruled in the S4 and S5 re-review; the audit's five tasks are closed with corrections (E1 to E14).
15. **Market tiers and targets:** tier definitions, the cap on cells, floors for target markets, and infeasibility behavior.
16. **Scoring governance:** recipients, retention, and prohibited uses.
17. **Consumer ZIP layer [v2.6, adopted October 22]:** ZIP5 append with ZIP3 retained; capacity tier gated (G1 to G4, P1); P1 is the only blocking proxy gate. Open: Claritas agreement (L1, deferred to a firm client contract), counsel review before first grid use, documentation of Claritas inputs (O28), G2 power at law size (O35, tested in W21L), and a scoped audit of the consumer layer before S4 and S5 sign-off.
18. **509 definitions and rank-matching** (O16): **[v2.5]** definitions confirmed by the audit from the report form and the data (the ABA's definitions document was not read); conditional-scholarship lag is one year. Open: validate rank-matching in the law world; regenerate the Appendix D illustration from the implemented function.
19. **Program-length horizon and conditional awards** (O17): **[v2.5, decided]** horizon equals the award commitment; conditional-award modeling deferred.
20. **Boosted-model challenger margin** (O19): **[v2.5, set]** margin and Monte Carlo tests in methodology section 11.

## 7. Risks

| Risk | Mitigation |
|------|-----------|
| **[v2.8, B6]** Excel parity tests pass without recalculating (LibreOffice does not recalculate XLSX on load by default) | Forced-recalculation profile and a sentinel check (spec v0.6 test 3) |
| **[v2.8, B6]** Reviewer bandwidth and scope growth | Scope frozen at the section 5A Must list; review by acceptance tests and a one-page checklist per phase |
| **[v2.8, B4-1]** The illustrative year shock (s = 0.10) drives the cap and median probabilities | Calibrate from public 509 and IPEDS data (O37); label until then; world W22 |
| Complexity creeps back in | Features added only through the triggers in methodology section 11 and the Monte Carlo gate |
| One slope leaves value on the table where segment differences are real | Stratified test builds segment evidence; revisit after three cycles |
| Clients cannot supply offer dates or merit grids | Tier 1 request; discontinuity-only or experiment-only anchor with wider ranges |
| Price test not offered or not approved | Discontinuity-only anchor, flagged as local, with an explicit "evidence too weak" outcome; the product must work without a test |
| Small institutions: tests underpowered | Report the smallest detectable effect up front; pool cycles |
| Legal exposure from recommendations | Policy attributes only; audit; no individual-level credit data; client alignment gate with a legal-considerations note; legal review at the client's option |
| Overreading 509 data | School-level, lagged, and ecological: reference and descriptive only; never the price anchor |
| Boosted model overfits small yield samples | Logit default; challenger only with calibration and a pre-set margin |
| Geographic proxies for race and income | Equity audit by market; the consumer capacity tier enters the grid only through gates G1 to G4 and P1, with P2 to P4 reported and counsel review first; raw segment codes never; whitelisted target attributes |
| Thin history in target markets | Flag and widen ranges; no optimized claims for markets under about 30 historical admits |
| Short client history (three cohorts) | Year-one scenarios lead; multi-year results use stated retention priors and are labeled; wider ranges |
| Over-trusting the model | Three sensitivity scenarios on every number; backtest diagnostic |
| Federal loan rules change again | Cap values held in configuration with an effective date |
| Clearinghouse cost or survey nonresponse | Client orders the match; survey results weighted and reported with response rates |
| Rights to prior engagement data | Do not reuse until confirmed; synthetic demo meanwhile |
| FAFSA changes (SAI replaces EFC) | Need-index type column; analyses use a harmonized need band |
| **[v2.7]** A client reads an NTR labeled "Response based on client-input" as a forecast | The label on every dependent output; Low, Middle and High cases; yield-shift strip; the evaluator never recommends |
| **[v2.7]** A cell of one or two students is recognizable to people who know the class | Named, authenticated roles only; sign-off recorded in the SOW and the alignment-gate packet; no student-level rows anywhere |
| **[v2.7]** Excel, dashboard and policy document drift apart | One ledger computes all three; reconciliation test (FR-73) |

## 8. Definition of done for the spec phase

- Every table, column, and index in `sql/schema.sql` justified and migration-tested.
- Every dashboard view has a wireframe, data contract, empty and error states, and a disclosure review.
- Every pipeline module has an interface, test plan, and runtime budget.
- The Monte Carlo study is specified with its worlds, seeds, metrics, and pass thresholds, and signed off.
- A written validation protocol for the first real pilot, signed off before data arrive.

## 9. Open questions from the review

1. Who counts as "eligible" for the price test, and does the discontinuity sample overlap the test sample?
2. What produced the v2 hybrid average of 1.40 against an anchor of 1.14?
3. Is the -0.41 targeting correlation the same in every segment of the synthetic generator?
4. Does the generator's true retention match the constant-hazard model used to score it?

**[v2.5]** The "7 passing" claim was verified on October 22, 2026: all seven guardrail tests pass, and the v2 pipeline reproduces the quoted anchor, backtest, and recovery numbers (`Verification_Report_Oct22.md`). Still not verified by a reviewer: the generator code, and the `equity_audit` and `funnel_cells` outputs (proxy fairness and disclosure). The audit also left open: a run of the HiGHS-based pipeline on the production screen, Richmond's actual grant distribution by class, and whether staff can be blind to test membership at a law school.

**Review log [v2.5]**

| Date | Review | Result |
|------|--------|--------|
| Oct 15, 2026 | First independent review (R1 to R12) | v2 simplified to v2.1 |
| Oct 21, 2026 | S4 and S5 re-review, Claude Opus 5.5 (`S4_S5_Rereview_v2.4.md`) | 20 findings (F1 to F20), 24 required edits merged into v2.5. Errata added Oct 22 |
| Oct 21, 2026 | Audit of the re-review, Claude Fable 5.1 (`Audit_S4_S5_Rereview_v2.4.md`) | Holds with minor revisions. Both Critical findings stand. 14 edits (E1 to E14) merged Oct 22 |
| Oct 22, 2026 | Verification run, real scipy and HiGHS (`Verification_Report_Oct22.md`) | Seven guardrail tests pass; stub and real-solver results agree within 1% |
| Oct 22, 2026 | Consumer ZIP amendment adopted by Jason (D1 to D5); five issues resolved in `_superseded/02_methodology_v2.6.md` | **Not audited.** Scoped audit advised before S4 and S5 sign-off; counsel review before first grid use |

## 10. Author responses to the review questions [v2.2]

These describe the v2 prototype as designed, from my reading of its design. Verify against the code during S4 and S9.

| Question | Answer |
|----------|--------|
| Who is eligible for the price test, and does the discontinuity sample overlap it? | Eligible: first-time admits who are not athletes, in the test cohorts, with a random 40% selected. The discontinuity sample uses the same kind of student across all cohorts, so it overlaps the test sample, and bonus offsets add noise to awards near thresholds |
| What produced the v2 hybrid average of 1.40 against the anchor of 1.14? | The scaling was calibrated inside the anchored model against its own base probabilities. The hybrid substituted the observational model's base probabilities with the anchored slopes, so the average effect differs. The v2.1 conversion rule and test close this |
| Is the targeting correlation the same in every segment? | The structural coefficients in the generator are the same, but the observed correlation varies by segment because need enters only for FAFSA filers and ability is clipped. The world library should include segment-specific targeting |
| Does the generator's true retention match the constant-hazard model? | The generator defines retention only to year two. The four-year value was a modeling assumption, untested in the world |

## 11. Decision log [v2.2]

| Decision | Choice | Source |
|----------|--------|--------|
| Default slope structure | One anchored slope | Reviewer default, adopted in v2.1 |
| Discontinuity in the anchor | Keep; drop on failed density or placebo tests | Reviewer default, adopted in v2.1 |
| Cuts and increases | Cuts only on first offers not yet released; revisions and renewals up only; increases within the tested range | Reviewer default; first-offer increase bound added in v2.2 |
| Test data | Pure synthetic | Jason |
| Coding in this phase | None in `efa_fao/src/`; advisory and specification only. Build starts after S3, S4, S5 and S9 are signed off. **[v2.7]** Exception (Nov 4, 2026): the scenario-workbook prototype under `prototypes/scenario_workbook/` | Jason |
| Budget horizon | Year one required and default; client may extend up to four years. **[v2.5] Superseded:** horizon equals the award commitment | Jason (original); S5-3 and S5-10 (v2.5) |
| Data history | Three to five cohorts requested (minimum three, ideal five) | Jason |
| Standing price test | Optional per engagement, only where it yields actionable insight; decided by the client's VP or Director of Enrollment, or a Dean | Jason |
| Gate before client publication | Client alignment and approval gate; legal review is the client's choice | Jason |
| Pilot | **[v2.6]** The v2.1 request cannot support a law pilot; proceeds on the S2b law Tier 1 request; client approval pending | Jason |
| Segment floors | Required; defaults in methodology Appendix C confirmed October 20; first-generation is a client option | Jason |
| Retention priors | Published benchmarks or the client's published rates, stated and labeled | Jason |
| Alignment gate sign-off | One-page approval | Jason |
| Batch scoring | Kept as an optional add-on; secure-channel delivery | Jason |
| Per-student packages | Cut; replaced by the policy lookup | Jason |
| Win-optimization | Kept, narrowed to whitelisted policy attributes, including geography (MSA or similar) | Jason |
| Price test | An add-on, not core; preceded by an evidence audit | Jason |
| Synthetic testing | Build and use it; not pitched to clients | Jason |
| Grid-tier price estimation | Deferred to a future phase; not in the spec | Jason |
| ABA 509 data | External reference dataset (peers, market award gap by rank-matching, conditional scholarships, yield prior, synthetic-world parameters); never the price anchor | Jason |
| Horizon | Follows program length (for example three years for a full-time JD) | Jason, with recommendation |
| Forecast model | Regularized logit by default; boosted-tree challenger for scoring only, behind a margin | Jason, with recommendation |
| Applicant-reported timing data (third-party site) | **Closed: not used.** Considered a weekly collection of response-timing data from an applicant-reported law admissions site, to track timing by date. Decided against. The site's license excludes institutional and commercial use and prohibits scraping or bulk collection without written permission. The data are self-reported, skew toward engaged applicants, and are coarse (the share of applicants who heard back, by application period). They measure how fast schools respond, not how applicants respond to price, and they do not link to a client's students. Timing sensitivity is learned from the client's own offer waves, and public applicant-volume reports describe market pace. Revisit only if the owner offers a license on terms that fit. | Jason |
| **[v2.5]** Price-test screen | Value-of-information screen replaces the 2.3-point power rule | S4-7; audit A1 to A7, E4 to E7. Pending sign-off |
| **[v2.5]** Choice rule | Two-sided (gain at low and high scenarios); automatic weak-evidence state | S5-1; audit kept it (A8 to A10) |
| **[v2.5]** Award mode | `supplement` (UG) or `total` (law); ladder to tuition; law cap 100% | S5-2 |
| **[v2.5]** Horizon | Equals the award commitment length; mismatches rejected | S5-3, S5-10 |
| **[v2.5]** Primary estimator | All-eligible ITT only if staff are blind to test membership; otherwise test-only at dose 0 | Audit A22, E1 |
| **[v2.5]** Audit | Completed October 21 to 22, 2026; E1 to E14 merged | `Audit_S4_S5_Rereview_v2.4.md` |
| **[v2.7]** Per-cell guardrail | Removed; step-size table instead; segment floors stay | Jason, Nov 5, 2026 (V27-01) |
| **[v2.7]** Threshold freeze | Dropped for client-declared bands | Jason, Nov 5, 2026 (V27-06) |
| **[v2.7]** Policy of record | The client's fine matrix; optimizer decision layer of at most floor(admits ÷ 30) parameters | Jason, Nov 5, 2026 (V27-07) |
| **[v2.7]** Small cells | Per-client policy; none for Richmond's named roles (enrollment team, leadership, aid office); Cat and Richmond staff signed off | Jason, Nov 5, 2026 (V27-13, V27-14) |
| **[v2.7]** Scenario evaluator | Fifth deliverable in every evidence state; one ledger for Excel, dashboard and policy document; label "Response based on client-input" | Jason, Nov 5, 2026 (V27-10) |
| **[v2.7]** Geography in the evaluator | One combined target tier (NY, PA by default) plus one incentive; per-state tiers after state-level data | Jason, Nov 5 and Nov 13, 2026 (V27A-01) |
| **[v2.7]** Class size and cap | 100 to 140 supported; 140 is a hard cap this cycle; shrink path lowest LSAT band first, target tier protected; Brandon to confirm the path | Jason, Nov 13, 2026 (V27A-02, V27A-03) |
| **[v2.7]** Pool tripwires and net-price readouts | Added to the evaluator; net-price readouts are display-only | Jason, Nov 13, 2026 (V27A-04, V27A-05) |
| **[v2.7]** Net-price yield response | Deferred | Jason, Nov 5, 2026 |
| **[v2.7]** Dashboard order | Views 2 and 3 ship in the first delivery with the Excel workbook | Jason, Nov 5, 2026 (OD-07); **superseded Nov 16** |
| **[v2.8]** Session B audit | Accepted in full: fixes, metric definitions (methodology Appendix F), recommendations; three simplifications | Jason, Nov 16, 2026 (`DECISIONS.md`) |
| **[v2.8]** Deliverable order | Workbook first; dashboard as an add-on after the core computation | Jason, Nov 16, 2026 |
| **[v2.8]** Priority segment | General segment in place of the target-state tier names; Richmond unchanged | Jason, Nov 16, 2026 (B5-1) |
| **[v2.8]** Tripwires, net-price readouts, goal-seek, schedule, simulation sheet | Pool strip; two net-tuition lines; goal-seek and schedule deferred; simulation in tests only | Jason, Nov 16, 2026 (B7) |
| **[v2.8]** Cross-client empirical prior | Removed | Jason, Nov 16, 2026 (B5-5) |
