# EFA + FAO v2.4: Roadmap to the Technical Spec

This is preparation for the spec phase, not the spec. It lists what the spec must decide, what is built, what v2.1 changes, and what remains. The methodology is in `02_methodology_v2.md`; the v2 version of this roadmap is archived in `_archive_pre_review_2026-10-15/`.

**Guiding rule:** a feature is added only if it changes a recommendation or a client decision, and the lean Monte Carlo study shows it does so reliably. Deferred features and their triggers are listed in methodology section 11.

**Labels [v2.2].** S = spec step (S1 to S11). R = review finding (R1 to R12, labeled F1 to F12 in earlier versions). FR = functional requirement. S4-n and S5-n are numbered review edits within those steps.

**Spec steps and where they stand.** Each step is one document, written and reviewed in order.

| Step | Document | Source today | Status | Review |
|------|----------|--------------|--------|--------|
| S1 | Requirements and user stories | None | Not started | Jason signs off |
| S2 | Data contract and synthetic data specification | Data request, data dictionary | Partial; world library to define; add geography script and market fields; add external-data contract for ABA 509 and a law world calibrated to it | Jason signs off |
| S3 | Pipeline architecture and interfaces | Section 1 below | Needs typed interfaces | Opus review |
| S4 | Statistical methods | Methodology sections 2, 4 (including evidence audit, sample-size guide, and timing by wave), 6, 7, 10 | Drafted (v2.2); open issues O1 to O3, O5, O7, O10 | **Opus re-review pending** |
| S5 | Optimization | Methodology section 5 (market tier, targeted objectives, policy lookup, program-length horizon, conditional-award persistence), Appendix C | Drafted (v2.2); open issues O4, O8 | **Opus re-review pending** |
| S6 | Database | `sql/schema.sql` (drafted, not applied) | Needs new tables (including `market_reference` for 509 data) | Security review |
| S7 | Dashboard | Section 4 below | Requirements only; no wireframes | Walkthrough with an enrollment user |
| S8 | Privacy, equity, and alignment controls | Methodology section 9 | Drafted; equity audit and funnel outputs not yet reviewed | Opus review, then client alignment review |
| S9 | QA and Monte Carlo release gate | Methodology section 10 | Thresholds are proposals; open issues O6, O16, O19; law world calibrated to 509 | Opus review of thresholds |
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
| `funnel_cells.csv` | `funnel_cells` | Funnel and pacing view |
| `efa_drivers.csv` | `efa_drivers` | Funnel and pacing view (drivers panel) |
| `pacing.csv` [new] | `pacing` | Same date last year, plan, projected census |
| `melt_segments.csv` [new] | `melt_segments` | Melt risk by segment |
| `scenarios.csv` | `scenarios` | Scenario planner, each scenario at low, middle, and high sensitivity |
| `policy_grid.csv` [new] | `policy_grid` | Current versus recommended award by cell, projected yield |
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
2. **Scenario planner:** budget scenarios with class, revenue, spend, and discount rate, each at low, middle, and high sensitivity; leadership sees this view only at headline level.
3. **Policy grid:** current versus recommended award by cell, with projected yield and the guardrail applied; exportable as the scholarship policy document.
4. **Market context:** loan-cap exposure by program, lost-to institutions and net-cost gaps, peer pricing (for law schools, from public ABA 509 data), survey findings.
5. **Equity audit:** allocation and yield by group, flagged audit-only.

Methodology, data quality, and lineage are a linked panel on every view, not a separate view.

**Roles:** enrollment team sees all views; leadership sees headline scenarios, the policy grid summary, and the equity audit; analyst (internal) also sees draft runs and publishes.

**Design constraints:** never show a number without its sensitivity range, interval, or a stated reason it has none; every chart links to its definition; export only aggregates.

## 5. Build phases

| Phase | Deliverable | Acceptance test |
|-------|-------------|-----------------|
| 0. Repo hardening | CI, lint, tests in the pipeline, pinned dependencies, `uv` lock | Tests pass in CI from a clean checkout |
| 1. Lean model refactor | Single anchored slope, `rdrobust` discontinuity, academic index, excluded groups, policy-grid optimizer, three-scenario evaluation, spend-matched baselines, forecast recalibration | Estimator regression check: the per-student one-slope optimizer reproduces the v2 backtest result (+2.7% realized, one seed) within tolerance. The policy-grid result is judged in the Monte Carlo gate against the spend-matched baselines, not against +2.7%. Anchor conversion test passes; runtime under the v2 run's 141 seconds |
| 2. Monte Carlo gate | Eight worlds x 50 seeds | All baseline-world thresholds in methodology section 10 met; failures in the other worlds documented and flagged by diagnostics |
| 3. Database | Apply schema, migration tests, loader | Loader round-trips every CSV; RLS tests for all roles |
| 4. Dashboard v1 | Views 2, 3, 5 and the lineage panel on the synthetic run | Walkthrough with an enrollment-team user; no student-level fields anywhere |
| 5. Monitoring and market context | Views 1 and 4; weekly in-cycle export and refresh | Pacing matches a hand calculation on synthetic data; refresh runs unattended |
| 6. Real-data pilot | One Tier 2 engagement (price test only if the suitability screen recommends one), with Clearinghouse match and survey | Data passes QA; backtest diagnostic reported; client alignment sign-off recorded |
| 7. Learning loop | Standing stratified price test; refit each cycle | Anchor interval narrows each cycle; deferred refinements evaluated against their triggers |

## 6. Open technical decisions

1. **Grid dimensions:** default 75 cells (academic index quintile x need band x residency); whether program is added for some clients.
2. **Retention priors** for multi-year scenarios when client history is short. (Horizon is decided: year one is the default, up to four years if the client elects, and budget and revenue horizons must match.)
3. **Anchor pooling rule:** inverse-variance pooling with a 1.5 standard error disagreement flag, versus experiment-only once the test is mature.
4. **Excluded groups:** default list and client overrides.
5. **Refresh cadence** during yield season: weekly or biweekly.
6. **Student-level returns:** whether melt lists are offered at all, and the secure channel used.
7. **Tier 1 scope:** exactly which outputs a Tier 1 client receives without a price test.
8. **Graduate programs:** which programs enter the descriptive layers first.
9. **Scale:** shift to DuckDB and Parquet once any client exceeds about 1M student-term rows.
10. **Segment floors:** decided (confirmed October 20; first-generation is a client option).
11. **Price-test screen thresholds:** the numeric rule is accepted as a starting point (smallest detectable effect after planned cycles at most about 2.3 points per $1,000) and goes to the reviewer for re-evaluation; confirm the plausible-effect range and the yield and adjustment assumptions in S4.
12. **Alignment packet contents:** the sign-off is a one-page approval (decided); the scope of the legal-considerations note is open.
13. **Verticals and moderators:** per-vertical grid profiles (law and professional programs by relative position within the program) and the moderator discovery protocol (methodology section 4).
14. **Open design issues O1 to O15** (methodology section 13), resolved through the S4 and S5 re-review.
15. **Market tiers and targets:** tier definitions, the cap on cells, floors for target markets, and infeasibility behavior.
16. **Scoring governance:** recipients, retention, and prohibited uses.
17. **Consumer-segment add-on:** license terms for sharing codes, level of geography, and proxy audit before any model use.
18. **509 definitions and rank-matching** (O16): confirm field definitions and validate in a law world.
19. **Program-length horizon and conditional awards** (O17).
20. **Boosted-model challenger margin** (O19).

## 7. Risks

| Risk | Mitigation |
|------|-----------|
| Complexity creeps back in | Features added only through the triggers in methodology section 11 and the Monte Carlo gate |
| One slope leaves value on the table where segment differences are real | Stratified test builds segment evidence; revisit after three cycles |
| Clients cannot supply offer dates or merit grids | Tier 1 request; discontinuity-only or experiment-only anchor with wider ranges |
| Price test not offered or not approved | Discontinuity-only anchor, flagged as local, with an explicit "evidence too weak" outcome; the product must work without a test |
| Small institutions: tests underpowered | Report the smallest detectable effect up front; pool cycles |
| Legal exposure from recommendations | Policy attributes only; audit; no credit data; client alignment gate with a legal-considerations note; legal review at the client's option |
| Overreading 509 data | School-level, lagged, and ecological: reference and descriptive only; never the price anchor |
| Boosted model overfits small yield samples | Logit default; challenger only with calibration and a pre-set margin |
| Geographic proxies for race and income | Equity audit by market; consumer segments never in the aid grid by default; whitelisted target attributes |
| Thin history in target markets | Flag and widen ranges; no optimized claims for markets under about 30 historical admits |
| Short client history (three cohorts) | Year-one scenarios lead; multi-year results use stated retention priors and are labeled; wider ranges |
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
| Coding in this phase | None; advisory and specification only | Jason |
| Budget horizon | Year one required and default; client may extend up to four years | Jason |
| Data history | Three to five cohorts requested (minimum three, ideal five) | Jason |
| Standing price test | Optional per engagement, only where it yields actionable insight; decided by the client's VP or Director of Enrollment, or a Dean | Jason |
| Gate before client publication | Client alignment and approval gate; legal review is the client's choice | Jason |
| Pilot | Assumed to proceed on the v2.1 data request; client approval pending | Jason |
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
