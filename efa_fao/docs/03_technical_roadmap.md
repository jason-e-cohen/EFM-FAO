# EFA + FAO v2.1: Roadmap to the Technical Spec

This is preparation for the spec phase, not the spec. It lists what the spec must decide, what is built, what v2.1 changes, and what remains. The methodology is in `02_methodology_v2.md`; the v2 version of this roadmap is archived in `_archive_pre_review_2026-10-15/`.

**Guiding rule:** a feature is added only if it changes a recommendation or a client decision, and the lean Monte Carlo study shows it does so reliably. Deferred features and their triggers are listed in methodology section 11.

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
Student-level returns to the client (for example a melt list) go back through the client's secure channel, never Supabase.
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
| Synthetic institution generator with ground truth | Built | Extend with the eight Monte Carlo worlds |
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
| Data dictionary, source taxonomy, data request | Drafted | Add Tier 1 / Tier 2, Grad PLUS and PLUS denial fields, CSS Profile fields, program, graduate test scores, new test arms |
| Guardrail tests | 7 passing | Add: anchor conversion, spend matching, support rule, no credit data |
| Dashboard | Not started | Five views (section 4) |
| Loader, CI, scheduling | Not started | Small |

## 3. Pipeline outputs and their tables

| Output file | Table | Dashboard use |
|-------------|-------|---------------|
| `funnel_cells.csv` | `funnel_cells` | Funnel and pacing view |
| `efa_drivers.csv` | `efa_drivers` | Funnel and pacing view (drivers panel) |
| `pacing.csv` [new] | `pacing` | Same date last year, plan, projected census |
| `melt_segments.csv` [new] | `melt_segments` | Melt risk by segment |
| `scenarios.csv` | `scenarios` | Scenario planner, each scenario at low, middle, and high sensitivity |
| `policy_grid.csv` [new] | `policy_grid` | Current versus recommended award by cell, projected yield |
| `price_response_curves.csv` | `price_response_curves` | One curve per segment from the single slope, three sensitivity lines |
| `market_context.csv` [new] | `market_context` | Loan-cap exposure, lost-to institutions, peer net price, survey summaries |
| `equity_audit.csv` | `equity_audit` | Equity audit |
| `model_run.json` | `model_runs` | Lineage, anchor evidence, diagnostics, backtest result |
| `validation_*.csv` | `validation_*` | Synthetic demo only |

Retired: `projection_segments.csv` (folded into `policy_grid`) and `model_coefficients.csv` (the browser probability calculator is dropped).

## 4. Dashboard requirements to specify

**Views**
1. **Funnel and pacing** (enrollment team): conversion by stage with one or two dimensions from the approved table set, pacing against last year and plan, projected census, melt by segment, drivers panel labeled associational.
2. **Scenario planner:** budget scenarios with class, revenue, spend, and discount rate, each at low, middle, and high sensitivity; leadership sees this view only at headline level.
3. **Policy grid:** current versus recommended award by cell, with projected yield and the guardrail applied; exportable as the scholarship policy document.
4. **Market context:** loan-cap exposure by program, lost-to institutions and net-cost gaps, peer pricing, survey findings.
5. **Equity audit:** allocation and yield by group, flagged audit-only.

Methodology, data quality, and lineage are a linked panel on every view, not a separate view.

**Roles:** enrollment team sees all views; leadership sees headline scenarios, the policy grid summary, and the equity audit; analyst (internal) also sees draft runs and publishes.

**Design constraints:** never show a number without its sensitivity range, interval, or a stated reason it has none; every chart links to its definition; export only aggregates.

## 5. Build phases

| Phase | Deliverable | Acceptance test |
|-------|-------------|-----------------|
| 0. Repo hardening | CI, lint, tests in the pipeline, pinned dependencies, `uv` lock | Tests pass in CI from a clean checkout |
| 1. Lean model refactor | Single anchored slope, `rdrobust` discontinuity, academic index, excluded groups, policy-grid optimizer, three-scenario evaluation, spend-matched baselines, forecast recalibration | Backtest reproduces the one-slope result (+2.7% realized) within tolerance; anchor conversion test passes; runtime under the v2 run's 141 seconds |
| 2. Monte Carlo gate | Eight worlds x 50 seeds | All baseline-world thresholds in methodology section 10 met; failures in the other worlds documented and flagged by diagnostics |
| 3. Database | Apply schema, migration tests, loader | Loader round-trips every CSV; RLS tests for all roles |
| 4. Dashboard v1 | Views 2, 3, 5 and the lineage panel on the synthetic run | Walkthrough with an enrollment-team user; no student-level fields anywhere |
| 5. Monitoring and market context | Views 1 and 4; weekly in-cycle export and refresh | Pacing matches a hand calculation on synthetic data; refresh runs unattended |
| 6. Real-data pilot | One Tier 2 engagement with price test, Clearinghouse match, and survey | Data passes QA; backtest diagnostic reported; counsel review recorded |
| 7. Learning loop | Standing stratified price test; refit each cycle | Anchor interval narrows each cycle; deferred refinements evaluated against their triggers |

## 6. Open technical decisions

1. **Grid dimensions:** default 75 cells (academic index quintile x need band x residency); whether program is added for some clients.
2. **Budget horizon:** year one or four years for renewable awards; must match the revenue horizon.
3. **Anchor pooling rule:** inverse-variance pooling with a 1.5 standard error disagreement flag, versus experiment-only once the test is mature.
4. **Excluded groups:** default list and client overrides.
5. **Refresh cadence** during yield season: weekly or biweekly.
6. **Student-level returns:** whether melt lists are offered at all, and the secure channel used.
7. **Tier 1 scope:** exactly which outputs a Tier 1 client receives without a price test.
8. **Graduate programs:** which programs enter the descriptive layers first.
9. **Scale:** shift to DuckDB and Parquet once any client exceeds about 1M student-term rows.

## 7. Risks

| Risk | Mitigation |
|------|-----------|
| Complexity creeps back in | Features added only through the triggers in methodology section 11 and the Monte Carlo gate |
| One slope leaves value on the table where segment differences are real | Stratified test builds segment evidence; revisit after three cycles |
| Clients cannot supply offer dates or merit grids | Tier 1 request; discontinuity-only or experiment-only anchor with wider ranges |
| Price test not approved | Discontinuity-only anchor, flagged as local; recommend starting a test |
| Small institutions: tests underpowered | Report the smallest detectable effect up front; pool cycles |
| Legal exposure from recommendations | Policy attributes only; audit; no credit data; counsel review before publish |
| Over-trusting the model | Three sensitivity scenarios on every number; backtest diagnostic |
| Federal loan rules change again | Cap values held in configuration with an effective date |
| Clearinghouse cost or survey nonresponse | Client orders the match; survey results weighted and reported with response rates |
| Rights to prior engagement data | Do not reuse until confirmed; synthetic demo meanwhile |
| FAFSA changes (SAI replaces EFC) | Need-index type column; analyses use a harmonized need band |

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

Not yet verified by the reviewer: the code and generator, the `equity_audit` and `funnel_cells` outputs (proxy fairness and disclosure), and the test logs behind "7 passing."
