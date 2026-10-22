# EFA + FAO v2: Roadmap to the Technical Spec

This is preparation for the spec phase, not the spec. It lists what the spec must decide, what is already built, and what remains.

## 1. Architecture

```
Client secure transfer (de-identified)         Compute environment (never Supabase)
  students / aid_offers / fafsa / price_test -> validate -> prepare -> estimate -> backtest -> optimize -> aggregate
                                                                     |                                   |
                                                           model_run.json (lineage)        aggregate CSV / JSON artifacts
                                                                                                         |
                                                                                    Supabase (Postgres + RLS) <- service role writes
                                                                                                         |
                                                                                   Vercel (Next.js) <- user JWT reads under RLS
```

**Recommended stack**
- **Compute:** Python 3.12, numpy, scipy (HiGHS MILP), pandas. No heavy dependencies; every estimator is in the repo and auditable. Add DuckDB and Parquet for intermediate storage at real data scale.
- **Orchestration:** a plain CLI plus a Makefile and GitHub Actions for the first version. Move to Prefect or Dagster only when there are many institutions on schedules.
- **Database:** Supabase Postgres with row-level security, aggregates only (schema in `sql/schema.sql`).
- **Dashboard:** Next.js on Vercel, Supabase client, chart library of your choice (Recharts or visx). Static JSON snapshots per published run for fast loads.
- **Auth:** Supabase Auth; roles `admin`, `analyst`, `enrollment_team`, `leadership` per institution.

## 2. What is built (this repository)

| Module | Status | Notes |
|--------|--------|-------|
| Synthetic institution generator with ground truth | Built | 143,200 student-term rows, about 56,000 aid rows, 2,609 price-test rows |
| Validation, cleaning rules, QA log | Built | Row counts for every rule |
| Feature layer with leakage and protected-attribute controls | Built | Test-enforced |
| Estimators: legacy replica, observational, experiment, discontinuity, anchored, hybrid | Built | Pure numpy and scipy |
| Retention model and multi-year NTR | Built | Constant-hazard approximation |
| Optimizer (MILP) with budget, class floor, cap, guardrail | Built | Under one second per solve |
| Bootstrap uncertainty and realization ratio | Built | Bands right-skewed; see section 6 |
| Aggregation with disclosure control | Built | Minimum cell 10, complementary suppression |
| Equity audit | Built | Audit-only |
| Supabase schema with RLS | Drafted, not yet applied | Needs a migration test |
| Data dictionary, source taxonomy, data request | Drafted | Client review pending |
| Guardrail tests | 7 passing | Privacy, leakage, protected attributes, optimizer |
| **Dashboard (Next.js on Vercel)** | **Not started** | Next phase |
| Loader (CSV to Supabase) | Not started | Small |
| CI and scheduling | Not started | |

## 3. Pipeline outputs and their tables

| Output file | Table | Dashboard use |
|-------------|-------|---------------|
| `funnel_cells.csv` | `funnel_cells` | Funnel explorer: pick any two dimensions, see conversion by stage |
| `efa_drivers.csv` | `efa_drivers` | Drivers view with intervals |
| `price_response_curves.csv` | `price_response_curves` | Curves by segment with bands |
| `scenarios.csv` | `scenarios` | Budget slider, frontier chart, planning vs model estimate |
| `projection_segments.csv` | `projection_segments` | Class projection and allocation by segment |
| `equity_audit.csv` | `equity_audit` | Audit view |
| `model_coefficients.csv` | `model_coefficients` | Probability calculator (browser-side) |
| `model_run.json` | `model_runs` | Lineage, anchor evidence, realization ratio |
| `validation_*.csv` | `validation_*` | Synthetic demo only: "how we know it works" |

## 4. Dashboard requirements to specify

**Views**
1. **Funnel explorer** (enrollment team): two-dimension filters, cohort selector, stage conversion bars, suppressed cells shown as "n < 10".
2. **Drivers:** forest plot of average marginal effects with intervals; labels distinguishing causal from associational.
3. **Price response:** curves by segment, bands, a marker at the current average award.
4. **Scenario planner:** budget slider over precomputed scenarios, frontier chart, expected class, NTR, discount rate, **planning estimate headline with the raw model figure as an upper bound**, probability of beating the status quo.
5. **Allocation by segment:** current versus recommended award, expected yield, price sensitivity.
6. **Equity audit:** allocation and yield by group, flagged as audit-only.
7. **Probability calculator:** browser-side logistic calculator from published coefficients; no student records.
8. **Data quality and lineage:** rules applied, row counts, run hash, anchor evidence, realization ratio.
9. **Methodology:** short, plain-language explanation of every number.

**Roles**
- Enrollment team: all views.
- Leadership: headline scenarios (the `leadership_scenarios` view), class projection, equity audit, lineage.
- Analyst: everything, plus draft (unpublished) runs and the publish action.

**Design constraints:** never display a number without its interval or a stated reason it has none; every chart links to its definition; export only aggregates.

## 5. Build phases

| Phase | Deliverable | Acceptance test |
|-------|-------------|-----------------|
| 0. Repo hardening | CI, lint, tests in the pipeline, pinned dependencies, `uv` lock | Tests pass in CI from a clean checkout |
| 1. Database | Apply schema, migration tests, loader | Loader round-trips every CSV; RLS tests for all four roles |
| 2. Dashboard v1 | Views 1, 4, 5, 8 on synthetic run | Walkthrough with an enrollment-team user; no student-level fields anywhere |
| 3. Dashboard v2 | Views 2, 3, 6, 7, 9; leadership view | Accessibility pass; leadership sees only headline views |
| 4. Real-data pilot | One client engagement using data request v2 | Data passes QA; backtest and realization ratio reported; counsel review recorded |
| 5. Learning loop | Standing price test; refit each cycle | Interval on price sensitivity narrows each cycle |

## 6. Open technical decisions

1. **Bound the scaling factor** and add an informative prior so bootstrap bands are not right-skewed when the experiment is weak.
2. **Persistence model:** replace the constant-hazard approximation with year-specific retention once three or more years of retention exist.
3. **Segment floors:** configurable per-segment minimum awards defined on policy attributes (never on protected attributes).
4. **Multi-year awards:** modeling renewable awards and their conditions.
5. **Contribution margin:** optional cost-to-serve input.
6. **Time-varying treatment:** package revisions and appeals after the first offer.
7. **Scale:** shift to DuckDB and Parquet once any client exceeds about 1M student-term rows.
8. **Refresh cadence:** per cycle (offline) versus weekly during yield season.

## 7. Risks

| Risk | Mitigation |
|------|-----------|
| Clients cannot supply offer dates or merit grids | Data request v2 makes them required; fall back to experiment-only anchor and wider bands |
| Price test not approved | Discontinuity-only anchor, flagged as local; recommend starting a test |
| Small institutions: tests underpowered | Report minimum detectable effect up front; pool cycles; extend duration |
| Legal exposure from allocation recommendations | Protected attributes excluded; audit; counsel review gate before publish |
| Over-trusting the model | Planning estimate headline; realization ratio; probability of improvement |
| Rights to prior engagement data | Do not reuse until confirmed; synthetic demo meanwhile |
| FAFSA changes (SAI replaces EFC) | Need-index type column; analyses use harmonized gap, not raw index |

## 8. Definition of done for the spec phase

- Every table, column, and index in `sql/schema.sql` justified and migration-tested.
- Every dashboard view has a wireframe, data contract, empty and error states, and a disclosure review.
- Every pipeline module has an interface, test plan, and runtime budget.
- A written validation protocol for the first real pilot, signed off before data arrive.
