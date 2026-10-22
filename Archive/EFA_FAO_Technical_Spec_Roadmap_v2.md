# EFA + FAO v2: Technical Spec Roadmap (revised after independent review)

**Purpose:** Define what the technical spec must contain, in what order it is written, and how it is handed to Claude Code.
**This document is not the spec.** Each spec step becomes its own document, written and reviewed on its own.
**Supersedes:** `EFA_FAO_Technical_Spec_Roadmap.md`. **Companion:** `EFA_FAO_Executive_Read_v2.md`.
**Review status:** Methodology reviewed by Opus in four phases. All numbered edits below are accepted. Items marked PENDING depend on material the reviewer has not yet seen.

## 1. Product definition

**EFA:** where prospective students leave the funnel (inquiry, application, admit, deposit, enrolled at census), what predicts movement, and how that differs by segment.

**FAO:** given the admitted pool, a discretionary budget, and goals, how should discretionary institutional aid be allocated, and what will the class, net tuition revenue (NTR), and discount rate look like under each choice, with honest uncertainty?

**Delivery:** a Python build pipeline in a secure compute environment that publishes aggregates to Supabase, plus a Vercel dashboard for enrollment teams and leadership.

**Success criteria (numeric thresholds are set in S9 before any run)**
1. A real engagement runs from data request to published dashboard in under ten weeks.
2. Every number on screen traces to a run, a data hash, and a code version.
3. Across 200 or more synthetic worlds, price-effect intervals achieve their stated coverage, the realized-spend tail meets the budget constraint, and the recommended allocation beats matched-spend baselines by more than one standard error.
4. No student-level field reaches the database or dashboard, verified by automated tests.
5. No client-facing recommendation is published until the release gate (section 6) passes.

## 2. Non-negotiable principles

1. **Synthetic data only for testing and demonstration.** No client or prior-engagement files in the repository, tests, demos, or prompts.
2. **Aggregates only outside the compute environment.** Minimum cell size 10, complementary suppression, enforced in code and in the database.
3. **No leakage.** Only information known at the decision date may enter a price or forecast model. The decision date is defined precisely in S2 and tested.
4. **Protected attributes are audit-only.** Never in an allocation model. Enforced by test. Proxy effects are examined in the equity audit.
5. **Missing is never zero.**
6. **No unvalidated headline numbers.** A gain, a probability, or a band is shown only if its coverage has been demonstrated by the multi-seed study. Until then, show cross-fitted estimates with ranges and a stated status.
7. **Recommendations stay inside the evidence.** Increases are bounded by the range the price test covered. Reductions are allowed only on first offers not yet released. Revisions and renewals go up only.
8. **Reproducible runs.** Code version, config hash, data hash, seeds, and rules applied with row counts, recorded for every run.
9. **Publishing is a deliberate human act.** The pipeline never publishes.
10. **Counsel gate** before any client publication of allocation logic or the equity audit.

## 3. The reference prototype and what the review found

A working prototype exists as a zip. Treat it as a reference implementation and a source of lessons, not production code.

**Keep as concepts:** the data model (students, aid offers in long form, FAFSA, price test, pricing, aid policy); leakage controls; missing-as-missing; aggregates-only architecture; the MILP formulation; disclosure-control rules; guardrail tests; a synthetic world with known truth.

**Replace or fix:** the segment-pattern machinery, the scaling step, the bootstrap, the realization ratio, the budget constraint, the baselines, and the validation design.

### Review findings and dispositions

| ID | Severity | Finding | Disposition | Spec |
|----|----------|---------|-------------|------|
| F1 | Critical | Segment price pattern wrong in size and ranking; it drives the allocation | Uniform slope by default; segment differences only from a hierarchical model on the randomized arm, observational slopes as weak prior means with explicit bias variance | S4 |
| F2 | Critical | Recommended setting underperformed uniform slope on realized revenue while the model's predicted gain rose with kappa | Choose tuning settings by cross-fitted doubly robust value, never by predicted gain | S4, S5 |
| F3 | High | One realization ratio applied to all scenarios; ratio varies 0.14 to 0.62 and is negative for one optimizer | Retire the scalar. Cross-fitted policy evaluation per scenario, applied to enrollment, discount rate, and revenue | S4, S5 |
| F4 | High | Budget holds only in expectation; 95th percentile spend about 2.8 times budget at 1x | CVaR constraint across posterior draws; reserve | S5 |
| F5 | High | Bands and probability of gain uncalibrated; bands unscaled while headline scaled | 500 or more draws, allocation selected inside folds, bands on the same scale as the headline, coverage study | S4, S9 |
| F6 | High | Hybrid average effect (1.40) does not equal the anchor (1.14) | Calibrate scaling on the hybrid itself; unit test within 1% | S4 |
| F7 | High | All validation from one seed | Monte Carlo over 200 or more seeds; release gate | S9 |
| F8 | High | Forecast overpredicts yield (0.211 vs 0.202); holdout cannot validate the hybrid | Out-of-time recalibration; counterfactual check on the randomized arm | S4, S9 |
| F9 | Medium | "Same actual spend" false for some rows | Match spend within 1%, or report gain per dollar | S9 |
| F10 | Medium | Pooled anchor mixes two different estimates; z-test cannot flag it | Report both; random-effects pooling; bias-corrected discontinuity inference | S4 |
| F11 | Low | Class-floor scenario never binds | Ship floor scenarios only where they bind; report shadow prices | S5 |
| F12 | High | Validation cannot detect asymmetric reaction to cuts | Policy: no cuts to communicated offers; add loss-aversion and appeals worlds | S1, S5, S9 |

**Still open (reviewer did not see the files):** proxy fairness, disclosure control, guardrail test logs, and leakage beyond the planted leak. PENDING review.

## 4. The spec set, in order

Each step produces one document. Gates are marked. "Review" means an independent Opus pass on that document.

| Step | Document | Gate | Model tier |
|------|----------|------|-----------|
| S1 | Requirements and user stories | Jason signs off | Sonnet |
| S2 | Data contract and synthetic data specification | Jason signs off | Sonnet |
| S3 | Pipeline architecture and module interfaces | Architecture review | Opus review |
| S4 | Statistical methods specification (incorporates section 5 edits) | **Opus re-review of the rewritten spec** | Sonnet or Opus author, Opus review |
| S5 | Optimization specification (incorporates section 5 edits) | Opus re-review with S4 | Opus review |
| S6 | Database specification | Security review | Sonnet, Opus review |
| S7 | Dashboard specification | Walkthrough with an enrollment user | Sonnet |
| S8 | Privacy, equity, and legal controls | **Opus review, then counsel** | Opus review |
| S9 | QA, validation protocol, and Monte Carlo release gate | Review with S4 | Sonnet, Opus review of thresholds |
| S10 | DevOps, environments, and runbook | Jason signs off | Sonnet |
| S11 | Implementation plan for Claude Code | Final readiness check | Sonnet |

### S1 Requirements and user stories
Personas, jobs to be done, numbered functional and non-functional requirements, explicit non-goals. Must include the evidence-bounded recommendation policy (increases within tested range; no cuts to communicated offers) as a requirement, not a setting.

### S2 Data contract and synthetic data specification
Client data contract (tables, fields, types, definitions). Definitions must include: enrolled at census; offered, accepted, disbursed; **decision date** (precisely defined per institution, with how package revisions and appeals are handled); need index type (EFC versus SAI); stealth applicant; bonus-arm eligibility and its overlap with the discontinuity sample. Synthetic specification: generator requirements, parameter provenance table, truth model, world library (section 8), seeds, versioning, and labeling.

### S3 Pipeline architecture and module interfaces
Module boundaries (validate, prepare, estimate, backtest, optimize, aggregate, export), typed contracts, configuration, lineage, error handling, runtime budgets, storage, orchestration.

### S4 Statistical methods specification
Must implement the edits in section 5. Also covers funnel models, retention and multi-year value (with the constant-hazard assumption either validated or replaced), diagnostics, and failure modes (weak experiment, no experiment, no discontinuity, tiny samples).

### S5 Optimization specification
Must implement the edits in section 5. Also covers decision variables, objective options, scenario set, allocation outputs, stability checks, and degenerate cases.

### S6 Database specification
Tables, keys, indexes, row-level security by role, leadership views, publishing workflow, audit log, loader contract, migrations, backup, retention. Role-by-role access matrix with automated tests. No table can hold a student-level field.

### S7 Dashboard specification
Views: funnel explorer, drivers, price response, scenario planner, allocation by segment, equity audit, probability calculator, data quality and lineage, methodology. Per view: purpose, data contract, interactions, empty, loading, and error states, suppressed-cell treatment, export rules, accessibility. The scenario planner shows cross-fitted gain ranges and the matched-spend baselines, with no probability-of-gain headline until the coverage study passes.

### S8 Privacy, equity, and legal controls
Threat model, disclosure control including differencing across scenarios, filters, and cohorts, de-identification for client transfer, equity audit design including proxy effects, guardrail policy, counsel packet. PENDING: reviewer to examine the equity audit, funnel cells, and segment projection outputs.

### S9 QA, validation protocol, and release gate
Unit, integration, property, and regression tests; the Monte Carlo study (section 6); leakage, privacy, and performance tests; matched-spend backtests; pilot protocol with pre-registered criteria.

### S10 DevOps and runbook
Repository layout, dependency pinning, CI, environments, secrets, scheduling, run and publish procedures, incident response, deletion at engagement close.

### S11 Implementation plan for Claude Code
Small, testable increments; order of work; repository instruction file; stop-and-ask checkpoints.

## 5. Accepted review edits (binding for S4 and S5)

### Statistical methods (S4)

| ID | Edit |
|----|------|
| S4-1 | Default to a uniform slope set by the anchor. Allow segment differences only from a hierarchical model fit on the randomized arm. Observational slopes enter as prior means with an explicit bias variance |
| S4-2 | Define the population and scale (percentage points or logit) to which the anchor applies. Test that the hybrid's average effect equals the anchor within 1% |
| S4-3 | Report the experiment and the discontinuity separately. Pool with random effects |
| S4-4 | Discontinuity: data-driven bandwidth; bias-corrected intervals; density (manipulation) test; placebo thresholds; use the jump in net price as the denominator, not the jump in award |
| S4-5 | Randomize the bonus within each policy segment. Check whether staff lower other aid for bonus recipients |
| S4-6 | Replace the 40-draw bootstrap with 500 or more posterior draws. Choose the allocation inside cross-fitting folds |
| S4-7 | Cross-fit the realization correction separately for each scenario. Apply it to enrollment and discount rate as well as revenue. Scale bands the same way as the headline |
| S4-8 | Recalibrate the forecast on out-of-time data. Report calibration across cohorts with intervals |
| S4-9 | Define the decision date. Add timing tests for package revisions and appeals |
| S4-10 | The Monte Carlo study is a release gate |

### Optimization (S5)

| ID | Edit |
|----|------|
| S5-1 | Objective is the average across posterior draws |
| S5-2 | Replace the expected-spend budget with a CVaR constraint, calibrated so realized spend exceeds the budget by more than 5% in at most 5% of draws |
| S5-3 | Keep increases within the range the experiment tested. Revisions and renewals can only go up. Reductions only on first offers not yet released |
| S5-4 | State whether the budget covers year one or four years and match it to the revenue horizon (open decision) |
| S5-5 | Optional cap on the class-wide discount rate |
| S5-6 | Ship baselines matched to the same spend within 1%. Recommend over the uniform-slope baseline only if the cross-fitted gain beats it by more than one standard error |
| S5-7 | Choose tuning settings by cross-fitted doubly robust value, not predicted gain |
| S5-8 | Ship class-floor scenarios only where the floor binds, and report shadow prices |

## 6. Monte Carlo release gate (skeleton)

**PENDING:** the reviewer's Phase 3 specification of this study. Fold it into S9 when received. Until then, this is the minimum.

**Scale:** 200 or more synthetic worlds, seeds recorded, factors varied across a grid.

**Factors to vary:** strength and shape of targeting; heterogeneity in price sensitivity; sample size and price-test share; presence or absence of a price test and a merit grid; threshold effect differences; asymmetric reaction to cuts; cohort drift.

**Metrics:** bias and error of each estimator (experiment, discontinuity, pooled anchor, hybrid); coverage of stated intervals; forecast calibration by cohort; rank correlation between predicted and realized gain across tuning settings; realized gain distribution against matched-spend baselines; frequency of realized spend exceeding 1.05 times budget; stability of allocations to small perturbations.

**Starting thresholds (proposals, to be fixed in S9 before any run):** 90% intervals cover the truth between 85% and 95% of the time; realized spend exceeds 1.05 times budget in at most 5% of worlds; recommended allocation beats the uniform-slope baseline by more than one standard error in the worlds where it is meant to; failure worlds are correctly flagged by diagnostics rather than producing confident recommendations.

**Decision rules**

| Question | Rule |
|----------|------|
| Hierarchical segments versus uniform slope | Hierarchical only if it wins in at least 60% of seeds on cross-fitted value |
| Discontinuity in the anchor | Keep unless the density or placebo tests fail |
| Recommendation layer published | Only if every threshold passes |
| Any threshold fails | Fall back to the uniform-slope optimizer with ranges, and document the failure |

## 7. Functional requirements (seed list for S1)

| ID | Requirement |
|----|-------------|
| F1 | Validate client files against the data contract and report every rule applied with row counts |
| F2 | Map raw source labels with a versioned taxonomy and queue unmapped labels for review |
| F3 | Compute funnel stage counts and rates by cohort and by one or two dimensions, with disclosure control |
| F4 | Estimate funnel drivers with intervals and label each causal or associational |
| F5 | Estimate price sensitivity from the randomized arm, discontinuity, and observational data, report each with its interval, and test their agreement |
| F6 | Report minimum detectable effect and required sample for a planned price test |
| F7 | Forecast the admitted pool's enrollment at current awards with out-of-time calibration diagnostics |
| F8 | Produce price-response curves with bands on a stated scale |
| F9 | Optimize discretionary awards under a tail-risk budget, class floor, discount cap, and evidence-bounded changes |
| F10 | Produce a scenario set and a frontier, including only floor scenarios that bind |
| F11 | Show cross-fitted gain ranges and matched-spend baselines for every scenario |
| F12 | Produce an equity audit including proxy checks, with no protected attribute in any allocation model |
| F13 | Record lineage and block publication until an analyst publishes |
| F14 | Enforce role-based access: enrollment team, leadership, analyst, admin |
| F15 | Provide a browser-side probability calculator from published coefficients |
| F16 | Generate synthetic worlds with known truth and score estimators and allocations against it |
| F17 | Label all synthetic runs and dashboards clearly |
| F18 | Delete client raw data at engagement close and log it |
| F19 | Check bonus-arm integrity: randomization balance within segments and no offsetting reductions in other aid |
| F20 | Run the release-gate study and refuse to enable recommendations if any threshold fails |

## 8. Synthetic world library

Every parameter has a documented source: a public benchmark, a stated assumption, or a stated illustration. No parameter derives from client files or prior-engagement decks. Each world stores its truth apart from client-visible tables.

| World | Purpose |
|-------|---------|
| Baseline small private | Typical case with moderate signal |
| Weak-signal small college | Honest uncertainty when the experiment is underpowered |
| Large public, high volume | Scale and runtime |
| No price test | Discontinuity-only anchor |
| No merit grid | Experiment-only anchor |
| Strong confounding | Observational model alone fails |
| **Segment-specific targeting** | Staff target aid harder in some segments; tests the segment-pattern bias that drove F1 |
| **Heterogeneous threshold effects** | Different true effect at each merit threshold; tests pooling (F10) |
| **Loss aversion and appeals** | Cuts hurt more than equal increases help; students appeal (F12) |
| **Staff offset behavior** | Staff reduce other aid for bonus recipients; tests the randomization check |
| **Bonus contamination of the discontinuity sample** | Bonus offsets add noise near thresholds |
| **Cohort drift and regime change** | Behavior or grid changes mid-history |
| Leakage trap | Aid recorded only after enrollment |
| Data quality chaos | Duplicates, impossible stage order, missing aid coverage, mixed EFC and SAI, unmapped sources |
| Equity stress | Groups differ in need and sensitivity; proxy effects present |
| Retention beyond year two | True retention process spans years three and four, to test the persistence assumption |

PENDING: additions from the reviewer's Phase 3 list of worlds that make the method fail.

**Pilot rule:** the first real client's data never enters the repository. Only aggregates and run lineage are retained.

## 9. Non-functional requirements (seed list for S1)

- **Performance:** a full run on a 150,000-row world completes in under ten minutes on a laptop, excluding the Monte Carlo study (which runs in CI on a schedule). Each allocation solve under ten seconds.
- **Scalability:** designed to 1,000,000 student-term rows using columnar storage.
- **Reproducibility:** same inputs, config, and seeds produce identical outputs.
- **Security:** least-privilege roles, separate environments, secrets never in the repository, no student-level data in any hosted service.
- **Accessibility:** WCAG 2.2 AA.
- **Observability:** run logs, failure alerts, a data quality report for every run.

## 10. Build phases after the spec

| Phase | Deliverable | Acceptance |
|-------|-------------|-----------|
| 0 | Repository, CI, instruction file, synthetic world library | Clean checkout runs the synthetic pipeline and tests |
| 1 | Pipeline rebuilt to spec with the uniform-slope default | Unit and property tests pass; anchor equality test passes |
| 2 | Monte Carlo release gate | All thresholds pass, or the fallback is documented |
| 3 | Database and loader | Role access matrix tests pass; no student-level fields possible |
| 4 | Dashboard v1 (funnel, scenario planner, allocation, lineage) | Walkthrough with an enrollment-team user |
| 5 | Dashboard v2 (drivers, price response, equity, calculator, leadership views) | Accessibility pass; leadership sees only intended views |
| 6 | Pilot with one real client | Pre-registered criteria met; counsel gate recorded |
| 7 | Learning loop | Price sensitivity interval narrows each cycle; segment heterogeneity assessed on stratified data |

## 11. Model and tooling strategy

The review is itself evidence on the model question. A fresh Opus pass, given the documents cold, found errors that I, as the author, did not catch: a wrong economic claim about a segment, a false spend-matching statement, a validation that could not validate what it claimed, and a scaling design that performed worse than ignoring it. Independent review is where the stronger tier earns its cost.

| Work | Recommended |
|------|-------------|
| Re-review of the rewritten S4 and S5 | Opus |
| Privacy, equity, and legal controls (S8), architecture (S3), database security (S6) | Opus review |
| Review of Monte Carlo thresholds (S9) | Opus |
| Requirements, data contract, dashboard, DevOps, implementation plan (S1, S2, S7, S10, S11) | Sonnet |
| Implementation in Claude Code from tight specs, tests, migrations, front end | Sonnet |

## 12. Claude Code working agreement (goes in the repository instruction file)

1. Read the spec for the increment before writing code. Restate the acceptance criteria.
2. Write guardrail tests first (privacy, leakage, protected attributes, evidence bounds), then the code.
3. Use synthetic data only. Refuse any request to load client files.
4. Keep each pull request small, one increment, with tests and a short note on what changed.
5. Never display a gain, probability, or band whose coverage has not been demonstrated.
6. Stop and ask when a requirement is ambiguous, a spec step conflicts with a principle, a threshold cannot be met, or a new dependency is proposed.
7. Never publish, deploy to production, or change access rules without explicit approval.
8. Record decisions in a decision log; do not silently reinterpret the spec.

## 13. Decision log

| Decision | Choice | Source |
|----------|--------|--------|
| Default slope structure | Uniform | Reviewer default, accepted |
| Switch to hierarchical segments | Only if it wins in at least 60% of seeds on cross-fitted value | Reviewer default, accepted |
| Discontinuity in the anchor | Keep; drop on failed density or placebo tests | Reviewer default, accepted |
| Cuts | First offers not yet released only; revisions and renewals up only | Reviewer default, accepted |
| Budget constraint | CVaR across posterior draws | Reviewer default, accepted |
| Planning-estimate scalar | Retired | Review finding F3 |
| Probability-of-gain headline | Withheld until calibrated | Review finding F5 |
| Test data | Pure synthetic | Jason |
| Coding in this phase | None; advisory and specification only | Jason |

## 14. Open decisions

1. **Budget horizon:** year one or four years (S5-4).
2. **Standing price test:** default design, sample share, segment stratification, client approval workflow.
3. **Segment floors:** any policy-defined minimum awards (never on protected attributes).
4. **Bonus eligibility and overlap** with the discontinuity sample (see appendix).
5. **Bootstrap or posterior resampling unit:** student, or cohort blocks (see appendix).
6. **Persistence model:** constant hazard versus year-specific retention.
7. **Disclosure across scenarios and filters:** differencing protections.
8. **Refresh cadence:** per cycle or weekly during yield season.
9. **Hosting boundaries** for the compute environment.
10. **Who approves publishing** on the client side.
11. **Contribution margin:** model cost to serve in version one?

## 15. Appendix: author responses to the reviewer's open questions

These describe the prototype as built, from my reading of its design. They should be verified against the code during S4 and S9.

| Reviewer question | Answer |
|-------------------|--------|
| Who is eligible for the bonus arm, and does the discontinuity sample overlap it? | Eligible: first-time freshman admits who are not athletes, in the price-test cohorts, with a random 40% selected. The discontinuity sample uses the same kind of student across all cohorts, so it **overlaps** the arm, and bonus offsets add noise to awards near thresholds. This is a contamination to handle in S4 |
| What produces the hybrid average of 1.40 versus the anchor's 1.14? | The scaling is calibrated inside the anchored model against its own base probabilities. The hybrid substitutes the observational model's base probabilities with the anchored slopes, so the average finite-difference effect differs. Edit S4-2 fixes this |
| Is the targeting correlation the same in every segment? | The structural coefficients in the generator are the same, but the observed correlation varies by segment because need enters only for FAFSA filers and ability is clipped. It is not constant by segment, and the world should include segment-specific targeting |
| Does kappa weight the observational pattern or the uniform slope? | Kappa weights the observational pattern. At the estimated 0.72 the effective slope is mostly observational, which is why the setting hurt (F1, F2) |
| What is the bootstrap resampling unit? | Student rows with replacement, not cohorts. The experiment and discontinuity are re-estimated and the scaling re-solved in each draw. Cohort-level dependence is not captured |
| Does true retention match the constant-hazard model? | The generator defines retention only to year two. The four-year value is a modeling assumption, untested in the world. The new retention-beyond-year-two world addresses this |

## 16. Outstanding review items

1. **Phase 3 output** from the reviewer: the Monte Carlo study design, fair baselines, increases-only evaluation, and method for choosing tuning settings. Fold into S4, S5, S9.
2. **Aggregate files** the reviewer did not see: `equity_audit`, `funnel_cells`, `projection_segments`, and the guardrail test file. Needed to close proxy fairness, disclosure, and test-log items.
3. **Re-review** of the rewritten S4 and S5 once drafted.
