# S1: Requirements and User Stories

**Version:** 1.3 (v2.7 edits tagged [v2.7, V27-n]; November 13 addendum [v2.7, V27A-n]; November 16 Session B reconciliation tagged [v1.3, Bn-m], see `Audit_Session_B_Design_Report.md` and `DECISIONS.md`) **Date:** November 16, 2026 (v1.2: November 13; v1.1: November 5; v1.0: October 22, 2026) **Owner:** Jason Cohen
**First client:** University of Richmond School of Law
**Status:** Draft — awaiting Jason's sign-off. Every open item in section 10 must be resolved before build begins.

---

## 1. Purpose, scope, and how to read this document

This document is the functional specification for the EFA + FAO system as of methodology v2.7. It defines what the system must do, who uses it, and what evidence is required before build begins (S3 sign-off). It does not specify how modules are implemented; that is S3 through S5.

**Traceability tags used throughout**

| Tag | Meaning |
|---|---|
| §n | Methodology section n (`_superseded/02_methodology_v2.7.md`) |
| **[v2.7, V27-n]** | Edit from the v2.7 change list (`_superseded/Change_List_v2.7_draft.md`) |
| FR-nn | Functional requirement (this document) |
| Fn | Re-review finding (`S4_S5_Rereview_v2.4.md`) |
| An | Audit finding (`Audit_S4_S5_Rereview_v2.4.md`) |
| En | Audit required edit, merged into v2.5/v2.6 |
| On | Open issue (methodology §13) |
| Wn | Monte Carlo world (methodology §10) |
| MVP / M1 / M2 / Deferred | Priority (see §8 for Richmond mapping) |
| **[gated]** | Consumer ZIP requirement; gates G1–G4, P1, L1, and counsel review precede every use |

**Reading rule:** every FR includes a source (methodology section) and an acceptance pointer (unit test, Monte Carlo world, or acceptance fixture). An FR without both is incomplete and must be resolved before S3.

**Closed decisions that bound this document:** per-student optimization replaced by the policy lookup; grid-tier price estimation deferred; third-party applicant-reported timing data not used; protected attributes never enter models or grids. These are not re-opened here.

---

## 2. Users and roles

| Role | Who | What they see | Dashboard access |
|---|---|---|---|
| `enrollment_team` | Enrollment dean and staff | All five views; full scenario detail; exportable policy document | Views 1–5 |
| `leadership` | Law school dean and executives | All views, including the fine matrix and small cells; headline scenarios (class, revenue, discount rate at three sensitivities) lead each view **[v2.7, V27-31]** | Views 1–5 |
| `analyst` | Internal Frankel analyst | All views; draft runs before publication; publish action | All views + draft queue |
| `aid_office` | Financial aid director and staff | All views, including small cells; policy lookup (award for a student's cell) **[v2.7, V27-31]** | Views 1–5; policy lookup file via secure channel |
| `gate_approver` | Client decision-maker who signs the alignment gate (for Richmond: the dean plus named others) | Alignment-gate packet only; not a dashboard role | One-page approval form |

**Richmond note:** Q12 confirms the dean as the decision-maker for any aid policy change and for counsel review. The aid office (enrollment team in Slate) owns the data extract. Whether the aid office and enrollment team are the same staff is an open question (OQ-07).

---

## 3. Evidence states and deliverables

This table is the backbone of the document. Every FR maps to one or more evidence states. The Richmond MVP column reflects what the call answers make likely for the current cycle; items marked "conditional" depend on the evidence audit result.

| Evidence state | Condition | Deliverables | Tier needed | Richmond MVP |
|---|---|---|---|---|
| **No anchor** | No usable price source (no qualifying threshold, policy change, or experiment) | EFA funnel, monitoring, ABA 509 market view, evidence audit one-pager, documented status-quo grid. No optimized grid. | Tier 1 | Likely. Evidence audit will determine. |
| **Weak evidence** | Anchor exists (q10 ≤ 0), or the anchor straddles β* | Above, plus the evidence-too-weak state message and the screen's evidence plan. Only reallocations that are non-negative at b=0 and b_H pass. | Tier 1 | Possible if evidence audit finds a marginal source. |
| **Anchor available** | Evidence audit returns usable μ0, σ0; q10 > 0 | Above, plus the optimized grid under the two-sided rule. No optimized grid is shipped without an anchor. | Tier 2 | Conditional: requires the barbell-to-even policy change to qualify as a policy change under §4 evidence criteria, or a future test. |
| **Test running** | Screen recommends or marks Optional; client accepts; blinding evaluated | Above, plus test operations (FR-41 to FR-48), compliance reporting, and mid-cycle increases-only evaluation. | Tier 2 | **Not recommended at the current hard cap** (see §8). Revisit if cap or renewal rule changes. |

**[v2.7, V27-32] Scenario evaluator.** In every evidence state, including No anchor, the client may evaluate scenarios it writes (FR-71 to FR-76). Every output that depends on the price response carries the label **"Response based on client-input"** until an anchored response replaces it. The evaluator recommends nothing; "Evidence too weak to change aid levels" (FR-26) applies to Frankel-recommended grids only.

**Tier mapping for Richmond**

| Tier | Minimum fields | Supports |
|---|---|---|
| Tier 1 | Three cohorts, final packages by component, offer dates where available, merit grid, LSAT/UGPA, position reference classes, commitment length, capacity band, blinding answer | EFA, monitoring, evidence audit, ABA 509 layer, documented status-quo grid |
| Tier 2 | Above, plus every package version with dates, full reason codes on revisions, award renewals file, price-test stratification | Full FAO, anchor estimation, optimized grid, test operations |
| zip_key (optional add-on) | ZIP5 in a separate restricted file | Consumer ZIP layer (M1/M2, gated); not elected for Richmond's current geographic objective |

---

## 4. Functional requirements

### 4.1 Intake and scoping inputs

| ID | Requirement | Priority | Source | Acceptance pointer |
|---|---|---|---|---|
| FR-01 | Collect mandatory scoping inputs at engagement start: N (eligible admits per cohort), p (eligible yield), tuition, mean institutional award per enrollee, award commitment H, persistence s, renewal rule (fixed dollars or % of tuition), capacity (band ± % or "uncapped"), floors and targets, planned top arm D, test share (default 40%), test cycles K, cycles of use U, operating cost F per cycle, and the evidence-audit μ0 and σ0 (or the vertical default prior). Reject the screen computation if capacity band is absent. | MVP | §4 screen inputs; E7 | Scoping table populated before screen runs; screen rejects if capacity_band is null |
| FR-02 | Derive and confirm the status-quo grid (mean award by cell in the latest cohort) before any optimization. The client confirms it matches practice before the optimizer runs. Record confirmation in the alignment-gate packet. | MVP | §5 status-quo grid | Client confirmation present in model_run.json before first grid output |
| FR-03 | Receive and store audit-only data (student-level race and ethnicity, gender; ZIP-level race composition from ACS) in access-controlled storage separate from the analysis tables. Exclude them from all feature sets. A static test enforces it per blocked attribute. | MVP | §9 protected attributes | Guardrail test 3 passes; static schema tests pass for every blocked attribute |
| FR-04 | Run the data QA log on every intake: field-timing checks (no post-decision award in price models), leakage test, protected-attribute test, missing-date handling, package-version completeness, and reason-code presence for every revision. Report row counts and failures; do not silently suppress. | MVP | §3 data model; §7 batch release criteria; E1 | QA log present in model_run.json; guardrail test 4 and test 6 pass |
| FR-05 | Execute the law Tier 1 data request v3 (from `efa_fao/docs/data_request_v3/`) for Richmond before any analysis. Required fields: LSAT, UGPA, JD-Next concordance (if used), position reference classes from the prior three entering classes, commitment length, renewal rule and conditions, offer release dates and batch, capacity band and type, blinding answer, full-time or part-time status, and program-level ABA 509 yield history. | MVP | §3 law Tier 1, data request v3 spec | All required Tier 1 fields present in the validated dataset; QA log shows zero missing required fields |

### 4.2 EFA funnel

| ID | Requirement | Priority | Source | Acceptance pointer |
|---|---|---|---|---|
| FR-06 | Compute the descriptive funnel: stage-to-stage conversion rates (inquiry → application → admit → deposit → enrolled at census) by cohort and pooled, using the fixed non-overlapping table set. Apply the engagement's `small_cell_policy` (FR-76): by default suppress cells with fewer than 10 students and design tables so suppressed cells cannot be recovered by subtraction; Richmond's named roles see small cells **[v2.7, V27-28]**. Flag stealth applicants (no inquiry record) and exclude them from the inquiry-to-application stage. | MVP | §2 descriptive layer | Small-cell policy applied as configured (FR-76) **[v1.3, B2-3]**; structure matches approved table set; stealth flag present |
| FR-07 | Compute inquiry-to-application logit with clustered standard errors (clustered by student), reported as AME with 95% confidence intervals, labeled explicitly as associational. | MVP | §2 driver layer | Clustering applied; intervals present; "associational" label in output |
| FR-08 | Compute admit-to-enroll effects of non-price attributes from the forecast model with intervals, labeled associational. The forecast model contains no aid fields. | MVP | §2 driver layer; §4 response model | Guardrail test 4 passes; no aid field in forecast feature set |
| FR-09 | Compute relative position for each JD admitted student: empirical CDF applied per-measure (LSAT, UGPA; GRE and JD-Next via published concordance where available, otherwise flagged with UGPA alone). Combined position = mean of available measures. Assign to five position bands (under 25, 25–50, 50–75, 75–85, 85+); merge the top band if under 30 admits per cohort. Freeze bands at cycle start. Report admit distribution by band. | MVP | §2 relative position | Bands frozen before first offer released; top-band merge rule applied; GRE/JD-Next flagged when concordance absent |
| FR-10 | Derive geography from client home address via a client-side script before PII removal: CBSA code, state, ZIP3, distance-to-campus band. Report the funnel by market; under the default `small_cell_policy`, pool markets under 10 students into "other" **[v2.7, V27-28]**. No address appears in any analysis table. | MVP | §2 geography | No address field in any output table; market funnel present; "other" tier applied |
| FR-11 | Compute the academic index (for undergraduate) or use position band (law). Keep the raw running variables (LSAT, UGPA) alongside the index for the discontinuity estimation. | M1 | §2 academic index; §4 anchor | Index and raw running variables both present in the feature table; academic index is a composite, not aid-derived |
| FR-12 | Flag stealth applicants; include them in the funnel count and the forecast model, not in the inquiry-to-application logit. | MVP | §2 stages | Stealth flag present; stealth applicants in forecast but not in inquiry logit |

### 4.3 Monitoring

| ID | Requirement | Priority | Source | Acceptance pointer |
|---|---|---|---|---|
| FR-13 | Compute weekly pacing during yield season: complete applications, admits, deposits (gross), projected revenue and flexible spend against the same week of the cycle (counted from the application open date) in the prior two cycles and against the plan, beside the share of prior cycles' final applications that had arrived by that week **[v1.3, B3-4, B4-4]**. Refresh on a biweekly cadence or as configured. | MVP | §7 monitoring | Pacing values match a hand calculation on synthetic data; refresh runs unattended |
| FR-14 | Compute projected census: current counts by stage multiplied by historical stage-to-census conversion rates (pacing lookup by days to deadline), with a projection interval from binomial noise and the year-level shock s; prior-cycle spread is shown as a check, not used, until five cycles exist **[v1.3, B4-4]**. | MVP | §7 monitoring | Projection interval covers the realized census in ≥ 85% of W0L seeds |
| FR-15 | Compute melt risk: historical deposit-to-census rates by a small set of flags known at deposit (housing application, verification status, unmet need above a threshold, FAFSA not received). Report at segment level in the dashboard. Any student-level melt list returns to the client through the secure channel only, never through Supabase or the dashboard. | MVP | §7 monitoring | Guardrail test 1 passes; no student-level data in the melt view |
| FR-16 | Log every mid-cycle award revision with the date and a reason code (student request, documented competing offer, staff-initiated, appeal). Exclude logged revisions from price estimation and report reconsideration rates and revision rates by arm as compliance diagnostics. | MVP | §3 decision date; §7 treatment log | Reason code present on every revision row; revisions excluded from the price model; compliance table present |
| FR-17 | In the increases-only mid-cycle evaluation, compute projected class and budget check using the three-group formula (deposited D, released-undecided R, unreleased U) with the pacing lookup for conversion of R, b_H for the class ceiling, b_L for revenue from revisions. New awards only apply to unreleased offers. Released offers keep their committed amounts. | M1 | §5 increases-only; S5-7 | Three-group budget formula implemented; class ceiling checked at b_H and floor at b_L; no decrease on released offers in any fixture |

### 4.4 ABA 509 market layer

| ID | Requirement | Priority | Source | Acceptance pointer |
|---|---|---|---|---|
| FR-18 | Ingest annual ABA 509 disclosures with source, retrieval date, and version. Apply field rules: grant section covers the academic year before the report year (Y−1); percentiles are among recipients only; LSAT and UGPA percentiles describe matriculants; yield = matriculants ÷ offers; conditional-scholarship counts lag one year; a nonresident tuition of 0 at a private school means "same as resident" and is normalized and flagged. Flag peers with conditional-scholarship prevalence above 10% as "entering awards understated." | MVP | §2 ABA 509; A11–A17; E10 | Richmond's 75th-percentile grant equals prior-year tuition in the test fixture; conditional-scholarship lag = 1 year verified; zero-nonresident flag fires for Richmond's own rows |
| FR-19 | Compute descriptive peer pricing for a client-approved peer set of 5 to 10 schools: tuition, approximate net-price distributions, conditional-scholarship prevalence and loss rates, grant percentiles (labeled as among recipients). Store as school-level aggregates only; no student-level data. | MVP | §2 ABA 509 uses (a) and (c) | Peer set between 5 and 10 schools; no student-level rows in market_reference table; data labeled with report year |
| FR-20 | Compute the rank-matched market award gap (Appendix D procedure) for each position band: map the client's LSAT/UGPA position to each peer's distribution, read the peer's grant at that position, normalize to current tuition, compute the gap. Report the median and IQR across the peer set. This is descriptive and never the price anchor. | M1 | §2 use (b); Appendix D; A18; E11 | Unit test for the full-tuition branch (u ≥ 1 − f → tuition) passes; unit test for the tail-extrapolation rule passes; illustration regenerated from the implemented function |
| FR-21 | Use the client's own 509 yield history to check the recalibrated forecast intercept. Peer yields are never a prior for the client. | MVP | §2 use (d) | Yield from 509 compared to recalibrated forecast intercept in model_run.json; peer yield not used as a prior in any code path |

### 4.5 Evidence audit and value-of-information screen

| ID | Requirement | Priority | Source | Acceptance pointer |
|---|---|---|---|---|
| FR-22 | Run the evidence audit for every candidate price source (published threshold, policy change, natural experiment): check stability (unchanged ≥ 2 cohorts or ≥ 2 pre-period cohorts), net-cost jump (≥ 3% of tuition), bandwidth admits (≥ 150 per arm for thresholds; ≥ 100 per cohort for policy changes), density test (p ≥ 0.05), placebo thresholds (at most 1 of 4 significant at 5%), pre-trend (not significant at 10% and ≤ 2 points), and SE ≤ prior SD. Output μ0, σ0 (inverse-variance combination of usable sources with the vertical default prior), and the "anchor available" flag. | MVP | §4 evidence audit; S4-9 | Output includes μ0, σ0, and anchor flag; source-by-source check table present; every failing check explicitly stated |
| FR-23 | Run the value-of-information screen: compute EVPI (using V[i,j0] as defined; not omitting V0 when the no-test choice is not the status quo), EVSI (using the production two-sided rule, with both expectations scored by the same function), expected cost (at zero effect for the ratio and 5%-of-NTR gates; at prior mean including induced enrollees for capped programs), net value, and verdict (Recommend / Optional / Not recommended). Report the verdict at the client's own capacity band and at ±5% and ±10%. The screen must run on the production optimizer with a 509-calibrated pool — not on stylized pools. | MVP | §4 screen; S4-7; A1–A7; E3–E7 | Verdict matches the worked-example table (A1, reproduced to the dollar in the audit); three-band verdict table present; screen rejects if capacity_band is absent |
| FR-24 | If EVSI is negative, report its value with its sign, yield verdict "Not recommended," and flag the rule's quantile margins for review. Run the unconstrained-Bayes EVSI as a sanity check on the same pool; it must be ≥ 0. A negative unconstrained-Bayes EVSI indicates a computation error. | MVP | §4 screen; A5; E4 | Unconstrained-Bayes EVSI ≥ 0 on every fixture where the production EVSI is negative; negative EVSI reported with sign in the screen output |
| FR-25 | Report alongside every screen verdict: EVPI, EVSI (with sign), expected cost, the MDE, β*, and the grid change the test would most likely trigger. | MVP | §4 screen verdict; E7 | All six items present in the screen output; three-band table present |
| FR-26 | Trigger the weak-evidence state when b̂ − 1.2816 s ≤ 0 or when no anchor exists. In this state: block any award-level change above 1% of expected spend at b_M; allow only reallocations that are non-negative at b = 0 and b_H. Every deliverable view carries the label "Evidence too weak to change aid levels." | MVP | §5 weak-evidence state; O2 | W6: no level change when q10 ≤ 0 in 100% of seeds; two-sided rule test passes; "Evidence too weak" label present in every view |
| FR-27 | When no anchor exists and no admissible grid beats the status quo, output: the documented status-quo grid (confirmed by the client), the evidence-too-weak message, and the evidence plan (what sources the audit identified and what would make them usable). No optimized grid is shipped. | MVP | §5 no admissible grid; §1 law profile | Status-quo grid confirmed by the client before output; evidence plan present; W9: "No anchor, no optimized grid" fires in 100% of seeds |
| FR-28 | Pool experiment and discontinuity logit slopes by inverse variance into the anchor b̂ with SE s. Report the RD weight (capped at 30%). Raise the disagreement flag when |z| > 1.5 in logit units between sources. After two consecutive flagged cycles, the anchor becomes experiment-only. Report the bias bound (RD weight × difference) beside the anchor. | M1 | §4 anchor; S4-2; A23; E13 | Disagreement flag fires in ≥ 70% of W5 seeds; coverage ≥ 85% after flag action; W5 pass criteria met |

### 4.6 FAO grid and scenarios

| ID | Requirement | Priority | Source | Acceptance pointer |
|---|---|---|---|---|
| FR-29 | Build the law policy grid in total-award mode. **[v2.7, V27-21]** Two layers. The **decision layer** is built by merging adjacent score bands within residency × GPA class until each group has at least 30 projected admits, plus one out-of-state incentive, with at most floor(projected admits ÷ 30) parameters. The **policy of record** is the client's fine matrix (at Richmond: LSAT band × GPA class × residency, optionally × need when the school uses need in scholarships, per Q3), rendered from the decision layer by a deterministic rule or authored directly by the client. Optimizer ladder at $2,500 steps up to tuition; cap at 100% of tuition; horizon = award commitment length (three years for a renewable full-time JD award). | MVP | §5 law profile; S5-2; S5-4; V27-07 | Decision-layer parameters ≤ floor(admits ÷ 30); fine-matrix award for every cell equals the rendering rule's output; awards are total institutional scholarship amounts; horizon matches commitment length; config validation rejects mismatches |
| FR-30 | **[v2.7, V27-22]** Use the client's declared score bands as given. Compute any Frankel-derived cut points from the trailing three cohorts at cycle start and keep them fixed for the cycle; there is no minimum freeze length. Record every change in the policy_changes table with effective date, old and new cut points, and old and new awards. Log award differences between adjacent cells at a cut point for the evidence audit and show them in the step-size table (FR-33a); the log is informational. | MVP | §5 fixed thresholds | Cut points immutable within a cycle (tested by attempting to change them mid-cycle); policy_changes table populated on each update |
| FR-31 | Apply the two-sided choice rule: b_L = max(0, b̂ − 1.2816 s), b_M = b̂, b_H = b̂ + 1.2816 s. Accept only grids that are feasible at all three scenarios. Maximize net tuition revenue at b_M subject to gain ≥ 0 at both b_L and b_H. Use the same objective in the screen's preposterior analysis and the production optimizer. **[v2.7, V27-23]** The rule applies to Frankel-recommended grids; client-authored scenarios are evaluated, not chosen (FR-71). | MVP | §5 choice rule; S5-1; A8–A10; E3 | No level change when q10 ≤ 0 in 100% of Monte Carlo seeds (W0, W0L); W4: gain ≥ 0 in ≥ 85% of seeds; screen and optimizer use identical objective; optimizer and ledger agree on class, spend and NTR for the same grid |
| FR-32 | Budget constraint: expected flexible spend + appeals reserve (trailing three-cohort mean of post-first-offer increases by cell) + count-noise buffer (1.645 × √Σ p(1−p) × award², evaluated at b_H) ≤ budget. Reject grids that exceed the budget at any scenario. The count-noise buffer targets at most a 5% probability of overrun from enrollment noise. | MVP | §5 constraints; §6; S4-12; A29; E9 | Spend overrun above 105% of budget in ≤ 5% of seeds (W0L); buffer reported as approximately 15% of first-year scholarship spend (award-weighted) |
| FR-33 | **[retired v2.7, V27-24]** The v2.5 per-cell guardrail (no first-offer award more than 5% of tuition below its status-quo level) is removed. | — | §5 (guardrail removed v2.7); S5-5 superseded; F20 | Not applicable; see FR-33a |
| FR-33a | **[v2.7, V27-24]** Publish a step-size table in every run: award differences between adjacent cells (by residency × GPA class across score bands), as a plain table with no threshold, flag or message. | MVP | §5 constraints (V27-01) | Step-size table present in the policy grid output and the policy document; a test asserts that no output field or message labels an award exceptional, anomalous or out of bounds |
| FR-34 | Apply segment floors per Appendix C: highest-need and Pell-eligible at 100% of the trailing three-cohort average; all other segments (other need bands, No FAFSA, every market tier, every consumer capacity-tier cell) at 75%. Report which floors bind and their shadow prices each run. **[v2.7, V27-25]** Floors are evaluated on the rendered fine matrix, weighted by projected admits. | MVP | §5 floors; Appendix C | Floor constraint rows present in optimizer; binding frequency reported; shadow prices in scenarios.csv |
| FR-35 | Compute four shipped scenarios: 0.75×, 1×, and 1.25× budget; and headcount-maximizing at 1×. Compute the class-floor scenario only when the class floor binds; report its shadow price. Each scenario reported at b_L, b_M, and b_H. | MVP | §5 solver outputs | Five scenario types present in scenarios.csv; class-floor scenario absent when non-binding (verified on synthetic data) |
| FR-36 | Apply targeted-objective constraints (minimum expected enrollment by segment, year-over-year gain, enrollment weights, median position expectation) as linear constraints holding at all three scenarios. For a median-position constraint, constrain the expectation only — no 1.645σ margin. Report P(median holds) separately from the binomial variance, using the closed form 1 − Φ((−0.5 − m)/√V_m) **[v2.7, V27-26]**. Run infeasibility reporting: shortfall in enrollees at each scenario; budget to close it (re-solve with budget free up to 2×); funnel stage where the segment leaks. | M1 | §5 targeted objectives; S5-6; A30; E8 | Median constraint enforces expectation only; P(median holds) reported separately; infeasibility report present when target cannot be met; closed-form P(median) within 0.01 of simulation on the synthetic fixture |
| FR-37 | Enforce the whitelist: allowed grid attributes are market tier/CBSA, state, distance band, program, first-generation, Pell eligibility, residency, student type, position band, need band, and the consumer capacity tier (gated). Blocked attributes: race, ethnicity, gender, segment and lifestage codes, individual-level credit data, ZIP5 and ZIP3 as a grid dimension or target, household fields, any geography finer than CBSA as a grid dimension or target. Enforce by a static schema test with one unit test per blocked attribute and by the runtime proxy screen. | MVP | §5 whitelist; §9 | Guardrail test 3 passes; all blocked-attribute unit tests pass; PR-time schema check present |
| FR-38 | Run the runtime proxy screen before any publication that uses a geographic or consumer target: if the target segment's composition by race or ethnicity differs from the admit pool by more than 20 points for any group, or Cramér's V ≥ 0.3, require explicit acknowledgment at the alignment gate and add allocation changes by race group to the equity audit. | MVP | §5 enforcement; §9 | Proxy screen fires in ≥ 70% of planted-proxy seeds; acknowledgment required before publication in those seeds |
| FR-39 | In mid-cycle increases-only evaluation: increases are non-negative (Δ_i ≥ 0) and no larger than the tested dose D. Released offers keep their committed awards even if the cell's new award is lower. Budget and class checks use the FR-17 formula. | M1 | §5 increases-only; S5-7 | No decrease on any released offer in any fixture; test-dose cap enforced |
| FR-40 | Produce the scholarship policy document: recommended grid (or documented status-quo grid in weak-evidence state), projected class, revenue, spend, and discount rate under each scenario and sensitivity scenario, evidence status, which floors bind, the fine matrix, the step-size table (FR-33a), and a planning-assumptions block (admit rates, pool multiplier, tuition migration, class size) kept apart from aid policy **[v2.7, V27-27]**. Every number must carry its sensitivity range, interval, or a stated reason it has none. | MVP | §5 outputs | Policy document present for every run; evidence status present; no unranged number in the document |

### 4.7 Price-test operations

| ID | Requirement | Priority | Source | Acceptance pointer |
|---|---|---|---|---|
| FR-41 | Design the price test at the law profile: arms $0, D/2, D; D = 10%–15% of tuition, rounded to $1,000; allocation 40% / 20% / 40%; stratified assignment within position band × wave strata so arm shares are exact. Enrollment first into the test share (default 40%) before stratification. | M1 | §4 price test; S4-5 | Arm shares exact within every stratum; D within the law range [0.10T, 0.15T] |
| FR-42 | Assign randomization using blocked randomization within strata; record assignment, date, and stratum in the treatment log. | M1 | §4 price test | Treatment log present with assignment, date, arm, stratum; assignment verifiably random |
| FR-43 | Determine the primary estimator at intake using the blinding answer. If aid staff can deliver the test bonus as a formula line with no test flag visible in the CRM, the primary estimator is all-eligible ITT. If blinding is not possible (as Richmond reported in Q8), the primary estimator is test-only at dose 0. Record the blinding flag and the primary estimator in model_run.json. | M1 | §4 analysis population; E1; A22 | Blinding flag recorded; primary estimator matches blinding flag; W12 variant: test-status effect 0.10 logit flagged or primary bias ≤ 10% in ≥ 90% of seeds |
| FR-44 | Estimate the price slope: logit of enrollment on the dose and pre-specified covariates, AME evaluated at dose 0 (status-quo awards), not at the received dose. Report the SE, 95% interval, and the sample (primary and secondary). | M1 | §4 estimation; S4-1; S4-2; E1; A20 | AME evaluated at dose 0; "Evaluated at dose 0" labeled in output; both primary and secondary estimates reported |
| FR-45 | Run compliance checks after each test cycle: compare other discretionary aid, reconsideration request rates, and revision rates between arms (test arms vs. test $0 arm) and between test and non-test eligibles. Report as a process contrast. Do not use a yield contrast as the primary compliance check — its SE is insufficient to detect a 0.10-logit test-status effect at Richmond's size. | M1 | §4 compliance; E1; A22 | Compliance table shows process contrasts; yield contrast is reported but labeled "low power"; W12: compliance flag fires in ≥ 80% of seeds when staff offset ≥ 25% of the bonus |
| FR-46 | Run the conversion test: compute the model's AME at status-quo awards on the experiment's eligibles using recalibrated p. The estimate must fall within 1.645 × SE of the experiment's own AME. The acceptance fixture with a 10% level bias must fail; the unbiased fixture must pass. The v2.4 "within 1%" check is retired. | M1 | §4 response model; E12; A24 | Both fixtures pass or fail as specified; tolerance set to 1.645 × SE of the difference |
| FR-47 | Include in the alignment-gate packet for any engagement running a price test: the test design, randomization method, the negotiation-interference risk, and the blinding status and its effect on the primary estimator. | M1 | §9 alignment gate | Disclosure items present in the packet; blinding status and estimator choice explained |
| FR-48 | Compute the realized-versus-predicted gain backtest diagnostic each cycle: use model-set-budget basis (budgets set on model-predicted spend, not true spend). Report predicted and realized gain and the ratio. | M1 | §6 backtest diagnostic; S4-11 | Backtest present in model_run.json at model-set budgets; ratio reported |

### 4.8 Governance

| ID | Requirement | Priority | Source | Acceptance pointer |
|---|---|---|---|---|
| FR-49 | Before any client publication, obtain the alignment-gate one-page sign-off from the client's designated decision-maker (for Richmond: the dean plus named others). Record sign-off date, reviewer name, and scope in model_run.json. No deliverable is published without this record. | MVP | §9 alignment gate | Sign-off present and dated in model_run.json before any delivery; publication blocked without it |
| FR-50 | Produce the equity audit table with every recommendation: status-quo and recommended policies compared by group (average award, expected yield, expected discount rate, share receiving an increase), for every group that appears in the data. The v2 equity tables must not be shown to clients until re-run under the lean model. Review the equity audit before every alignment-gate packet. | MVP | §9 equity audit | equity_audit.csv present for every run; labeled "audit-only"; v2 equity tables blocked from client deliverables until re-run |
| FR-51 | Where the consumer ZIP add-on is active, include in the alignment-gate packet: the purpose statement ("the capacity tier measures neighborhood-level capacity to pay and expected response to price; it is not a measure of race, ethnicity or any protected trait"), the P1 gate result, and the P2, P3, and P4 reports. Counsel reviews the license and proxy note before the first use in an aid grid at any client. | M1 | §9 consumer data; Appendix E.1 | Purpose statement present in gate packet; P2–P4 reports present; counsel-review flag recorded before any grid use |
| FR-52 | Enforce the eight guardrail tests (seven existing, with test 2 and test 5 amended, plus test 8, the step-size report) **[v1.3, B2-7]**: (no student-level columns in published outputs; small-cell policy enforced as configured **[v2.7, V27-28]**; protected attributes not in allocation models; post-decision aid not in price models; optimizer respects budget cap and excluded groups; missing aid not silently zero; run metadata present). Add the consumer-module guardrail tests when the add-on is active (no ZIP5 or segment codes in any analysis or output table; tier construction takes no race argument; tier rejected as grid dimension unless every required gate passed; raw segment codes rejected as features; no ZIP-to-segment pairs; ZIP-level outputs aggregate ≥ 3 segments and ≥ 10 students; P4 never appears as a pass/fail field). | MVP | §9; §7; Appendix E.2 | All 8 tests pass; the consumer-module rule that ZIP-level outputs aggregate at least 10 students is independent of `small_cell_policy` (test 5 no longer asserts a maximum cut; test 2 checks the configured policy; a step-size test is added as test 8 **[v2.7, V27-28]**); consumer tests pass when the add-on is active |
| FR-53 | Enforce the policy lookup: the recommended award for a student is the cell award — the policy grid award for that student's cell. The lookup is not a separate per-student optimization. | MVP | §5 policy lookup | Batch score cell award identical to grid cell award for every student in that cell; no per-student optimizer code path used for the lookup |

### 4.9 Delivery

| ID | Requirement | Priority | Source | Acceptance pointer |
|---|---|---|---|---|
| FR-54 | Funnel and pacing view (enrollment_team): stage conversion with at most one or two approved dimensions, pacing against the same week of the cycle (counted from the application open date) in the prior two cycles and the plan **[v1.3, B3-4]**, projected census, melt by segment, drivers panel labeled associational. No student-level data. | MVP | §7; roadmap §4 view 1 | Guardrail test 1 passes; no student-level fields in Supabase; drivers labeled associational |
| FR-55 | **[v2.7, V27-29]** Scenario evaluator view (enrollment_team, leadership, aid_office): client-authored and Frankel-recommended scenarios with the levers in FR-74, showing class, revenue, spend and discount rate at b_L, b_M, b_H (or the client-input cases when no anchor exists), the what-if strips, and the label "Response based on client-input" where it applies. Every number carries its sensitivity range or a stated reason it has none. | Add-on, after the workbook **[v1.3]** | roadmap §4 view 2 | Three-case display present; what-if strips present; label present; RLS test shows the same fine-matrix and small-cell fields to the three roles |
| FR-56 | **[v2.7, V27-29]** Policy grid view (enrollment_team, leadership, aid_office): current versus recommended or client-authored award by fine-matrix cell, projected yield, and the step-size table (FR-33a); exportable as the scholarship policy document. | Add-on, after the workbook **[v1.3]** | roadmap §4 view 3 | Grid export matches policy_grid.csv; no guardrail column; step-size table present; export action available |
| FR-57 | Market context view (enrollment_team): loan-cap exposure by program and segment, lost-to institutions (from the Clearinghouse match, where ordered), peer pricing from the ABA 509 layer (for law: including the rank-matched market award gap from FR-20), survey findings summary. | M1 | roadmap §4 view 4; §8 | Data sourced from market_reference table only; no student-level rows in that table |
| FR-58 | Equity audit view (enrollment_team and analyst): allocation and yield by group, labeled "audit-only." The alignment-gate approver sees this view as part of the gate packet. | MVP | roadmap §4 view 5; §9 | View access restricted by role; "audit-only" label present; no student-level data |
| FR-59 | Student-level returns (batch scores, melt lists, policy lookup file) go to the client through the secure channel only — never through Supabase or the hosted dashboard. The SOW names recipient roles and prohibits individualized pricing, use in admission decisions, use in individual scholarship negotiation, and onward sharing. Files deleted within 30 days of engagement close; deletion log kept. | MVP | §7; §9; roadmap §1 architecture | Guardrail test 1 passes; no student-level data in Supabase; deletion log present |
| FR-60 | Every chart links to its definition. Methodology, data-quality, and lineage information appear as a linked panel on every view, not a separate view. | MVP | roadmap §4 design constraints | Definition link present on every chart; lineage panel present on every view |
| FR-61 | **[v2.7, V27-28]** Row-level security in Supabase enforces the defined roles (enrollment_team, leadership, aid_office, analyst; the schema enum currently lacks aid_office). Aggregates only are loaded; small cells are handled per the engagement's `small_cell_policy` (FR-76). | MVP | roadmap §1 architecture; §2 suppression | RLS tests pass for all roles; loader rejects student-level rows and applies the configured small-cell policy (the default rejects cells under 10) |

### 4.10 Add-ons: batch scoring and consumer ZIP

| ID | Requirement | Priority | Source | Acceptance pointer |
|---|---|---|---|---|
| FR-62 | Batch scoring add-on: return per student the forecast enrollment probability and its calibration band, and optionally the policy lookup award (cell award), through the secure channel. Ships only when: (1) out-of-time calibration passes (the 90% confidence interval of the slope overlaps [0.85, 1.15] **[v1.3, B4-3]**; |intercept| ≤ 0.1 logit; deciles within ±3 points for UG or inside the 90% binomial band for law); (2) feature-leakage and protected-attribute tests pass on the scoring feature set; (3) SOW terms are present; (4) alignment gate is signed. | M2 | §7 batch scoring | All four release criteria present in model_run.json before any batch file is produced |
| FR-63 | Batch score file contains only: client key, score, band, model version, score date, and optionally the cell award. The capacity tier is not in the file unless the Claritas agreement (gate L1) permits returning derived tiers. | M2 | §7; Appendix E | File contents match the specification; no field outside the allowed list |
| FR-64 | Boosted-tree forecast challenger for scoring only: adopted only if AUC improves ≥ 0.02 (paired-bootstrap 90% lower bound above 0) and Brier improves ≥ 3% relative on each of at least two out-of-time cohorts; monotone constraints applied. Reason codes: TreeSHAP top 3, restricted to whitelisted feature names. | Deferred | §11 boosted challenger | W20b passes in ≥ 70% of seeds at UG size before any adoption; pilot backtest also passes |
| FR-65 | **[gated]** Consumer ZIP intake: ingest the zip_key file (ZIP5, address type) from the client's secure channel in a separate restricted-access file; run the append job to attach the ZIP index, top-quintile share, tier, match flag, and vintage to student_consumer; delete zip_key within 30 days of append QA or at engagement close and record the deletion. ZIP5 must be absent from every analysis table, output, dashboard, and score file. Gates required before ingestion: L1 (or fallback F1 or F2) signed; G1 (match rate ≥ 95%); alignment gate acknowledging the consumer purpose statement. | M1 | §2 consumer ZIP; Appendix E.1, E.2 | Guardrail tests: ZIP5 absent from all analysis and output tables; deletion log present; match_report returned to client |
| FR-66 | **[gated]** Consumer bake-off: run variants A through E out of time on at least three cohorts, scored on AUC and calibration. Apply P1 (Cramér's V between tier and race/ethnicity, per cohort and pooled; must be below 0.3). Report P2 (incremental race predictability), P3 (mean award by race group, tier vs. no-tier policy), P4 (ZIP index correlation with ACS race composition). Report the G2 power result at the client's size; failing to power the test is not a pass. The licensed variant must beat variant B (free ACS/IRS baseline) to qualify for grid use. | M1 | §10 consumer bake-off; §9 gates | Bake-off output present; P1 pass/fail in consumer_gate_status; G2 power result at law size reported from W21L; P4 never appears as a pass/fail field |
| FR-67 | **[gated]** Consumer ZIP for targeting and outreach: when G1 and P1 have passed and the alignment gate is signed with the purpose statement, produce tier-level or ZIP-list outputs without segment labels. No raw segment codes, no ZIP-to-segment pairs. Outputs aggregate at least 3 segments and at least 10 students per ZIP-level cell. | M1 | §9 gates by use (targeting) | No segment labels in any targeting output; gate status present in consumer_gate_status for this use |
| FR-68 | **[gated]** Consumer capacity tier in the forecast baseline: when G1, G2, and G3 have passed, add the tier as one term in the forecast model. Gate failure means the tier is not in the forecast. | M1 | §4 response model; §9 gates | Tier rejected as a forecast feature unless G2 and G3 passed; consumer_gate_status checked in code before model training |
| FR-69 | **[gated]** Consumer capacity tier as a grid dimension: when G1, G2, G3, G4, and P1 have passed and counsel has reviewed the license and proxy note, add the tier to the grid by the pre-registered route (split, substitute, or add), chosen by out-of-time backtest. Law default: no tier in the grid until W21L shows G2 can be powered at law size. Law route: substitute the tier for market when backtest shows a gain. | M2 | §5 consumer tier in grid; §9 | Tier rejected as grid dimension unless all five gates passed; P4 never appears as pass/fail; law default is no tier until W21L result present |
| FR-70 | **[gated]** P2, P3, and P4 reports produced for every engagement where the consumer add-on is active; shown at the alignment gate and with counsel before first grid use; never used as blocking gates (only P1 blocks). | M2 | §9 report-only P2–P4 | P4 absent from consumer_gate_status pass/fail rows; P2–P4 reports in equity_audit output; alignment-gate packet contains all three |

---

### 4.11 Scenario evaluator and workbook [v2.7]

| ID | Requirement | Priority | Source | Acceptance pointer |
|---|---|---|---|---|
| FR-71 | **[v2.7, V27-30]** Scenario ledger: one reference evaluator (applications, admits, award, yield, enrolled, merit, need, NTR, discount) for any client-authored or Frankel-recommended grid at the L, M, H cases; yield constant when admit rates move; no sticker-price effect. Every output that depends on the response carries the label "Response based on client-input" until an anchored response replaces it. | MVP | §5 Scenario evaluator | Identities hold on a hand-computed toy grid; optimizer and ledger give identical class, first-year spend and `ntr_y1` for the same grid **[v1.3, B3-1]**; label present on every dependent output |
| FR-72 | Excel scenario workbook as the first deliverable **[v1.3]**: live formulas (no macros, no volatile functions), editable levers per scenario, L, M, H cases, closed-form probabilities, labels, checks. | MVP | §5 Scenario evaluator | Recalculated workbook equals the Python ledger (exact for integers, 1e-6 relative otherwise) under forced LibreOffice recalculation, with a sentinel check that no cached value survives **[v1.3, B1-25]**; reproduce mode matches the client's reference workbook on class, merit spend and NTR within $100 (fixture test; skipped when the file is absent) |
| FR-73 | Reconciliation: for the same run, the Excel workbook and the policy document (and the dashboard, once added) show identical class, spend, `ntr_y1` and discount rate, enumerated by the interface contract (spec §15 item 11) **[v1.3, B1-12]**. | MVP | §5 single evaluator | Reconciliation test over every contract figure |
| FR-74 | What-if levers: tuition increase by year (6.0% for 2027 in reproduce mode; Richmond planning 5.5%, unconfirmed **[V27A-06; v1.3, B2-9]**), class target under a hard class cap (140 this cycle), supported from 100 to 140, with a class-size table on the shrink path **[V27A-02, V27A-03; v1.3, B7-7]**, incentive (dollars per enrolled student; scope the priority segment or all out-of-state; optional score floor) and segment application lift (default 0) **[V27A-01; v1.3, B5-1]**, yield shift (percentage points; global with residency and segment overrides that replace it; strip from −3 to +3; linear break-evens), pool multiplier with a pool strip, admit rate by cell, award by cell. Every tuition output states that sticker price does not change applications or yield. | MVP | §5 Scenario evaluator | A child scenario with zero incentive and the parent's tuition equals the parent; the tuition what-if at the scenario's own rate equals ledger `ntr_y1`; the yield strip at shift d equals the ledger with that shift entered when no cell clips; overrides replace rather than add |
| FR-75 | **Deferred [v1.3, B7-3]** (year 2): goal-seek helper, a linear program that finds admit rates meeting class and median targets at a stated probability with minimal change. The shrink path and break-evens cover year 1. | Deferred | §11 future refinements | — |
| FR-76 | `small_cell_policy` per engagement (default suppress under 10 with complementary suppression; Richmond none) and the role map: enrollment_team, leadership and aid_office see all views including small cells; analyst sees all views and the draft queue; gate_approver sees the packet only. The sign-off record (date, scope, roles) is stored for the SOW and the alignment-gate packet. | MVP | §9 Small-cell disclosure | Loader applies the policy; RLS tests for each dashboard role; no student-level fields anywhere |
| FR-77 | **[v2.7, V27A-01; v1.3, B5-1, B1-4, B1-11]** Priority segment: each cell carries a segment (blank or a client-defined segment within one residency; Richmond: NY and PA within out-of-state, one combined segment); the cell file carries no state. The ledger reports segment enrolled with a 90% range, P(segment enrolled ≥ goal) (exact in Python; normal in Excel, flagged below 20 expected), and one incentive decomposition over the cells that receive the incentive: cost, the part paid to students the parent already enrolled (cell by cell), additional enrollees, aid and NTR change per additional enrollee, with a formula check that the parent differs by the incentive alone. With no segment cells, segment figures show "no segment cells in the data". Every dependent output carries "Response based on client-input"; a placeholder segment share carries "Segment share assumed, not from client data". | MVP | §5 Scenario evaluator; App. F | Segment merge invariance with inherited base yield; scope `segment` changes only segment cells; exact probability matches simulation within 0.01; cell-level decomposition identities hold, including where the cap binds; an empty segment produces no errors |
| FR-78 | **[v2.7, V27A-02, V27A-03; v1.3, B1-1, B1-5, B1-16]** Class range and cap: the class target is supported and tested from 100 to 140 under a hard cap (Richmond 140); P(class above cap) uses the cap. The shrink path (lowest score band first, then GPA; segment cells below the median threshold trimmed after other cells below it) writes admit rates for a smaller class and reports the lowest band still admitted, cuts by band and any shortfall; it respects `floor_rate` and exempt cells and is not an optimizer dimension. | MVP | §5 Scenario evaluator | For N below the expected class, hits N within rounding; for N at or above it, returns the input rates; admits never rise; while cutting below the threshold, the share at or above it is non-decreasing; no error on empty cells |
| FR-79 | **[v2.7, V27A-04; v1.3, B7-4]** Pool strip (replaces the tripwires): expected class, P(class above cap), the median margin and P(median holds), and mean `ntr_y1` at pool multipliers of 0.8 to 1.6, with every other lever applied, beside the client's pool growth to date (defined in App. F). | MVP | §5 Scenario evaluator | Each strip figure equals the ledger run at that multiplier |
| FR-80 | **[v2.7, V27A-05; v1.3, B7-5]** Net-tuition lines (display only, replacing the rung table): with awards fixed, the tuition change for every student below full tuition; with awards scaled, p × (base-cycle tuition − award). Labeled "Sticker-price demand effect not modeled." | MVP | §5 Scenario evaluator | Fixed-dollar change equals the tuition change; scaled change equals p × (prior tuition − award) within rounding |

---

## 5. User stories for Richmond

### Story 1: Enrollment dean — understanding the funnel (no anchor)

**Given** Richmond has sent three cohorts of Tier 1 data through Galaxkey and the QA log reports zero missing required fields,
**When** the Frankel analyst publishes the EFA run,
**Then** the enrollment dean can see: (a) stage-to-stage conversion rates by position band and by market (home state / other), with small cells handled per the engagement's `small_cell_policy` (at Richmond, shown) **[v2.7]**; (b) pacing against the prior year; (c) a market funnel showing geographic reach by state and MSA; (d) the ABA 509 peer comparison (tuition, grant percentiles for a 5-to-10-school approved peer set, conditional-scholarship prevalence); and (e) a one-pager from the evidence audit stating whether any usable price source was found.

**Acceptance:** Small-cell policy verified as configured; peer set between 5 and 10 schools; evidence audit present with source-by-source check; no student-level data in the dashboard.

---

### Story 2: Enrollment dean — evidence too weak (no admissible grid)

**Given** the evidence audit finds that the 2025 barbell-to-even policy change does not meet the minimum evidence criteria (for example, the comparison-group requirement cannot be satisfied for a whole-school policy change),
**When** the Frankel analyst runs the FAO module,
**Then** the system outputs: (a) the documented status-quo grid (confirmed by the dean before any optimization); (b) the label "Evidence too weak to change aid levels" on every view; (c) the screen's evidence plan (what sources were examined and what would make them usable); and (d) no optimized grid.

**Acceptance:** FR-27 acceptance criteria met; status-quo confirmation present in alignment-gate packet; no grid with changed award levels in any output.

---

### Story 3: Enrollment dean — hard capacity cap changes the screen verdict

**Given** Richmond confirmed a hard seat cap at 100% class fill (Q6),
**When** the VOI screen runs on the production optimizer with a 509-calibrated Richmond pool,
**Then** the verdict at the ±3% class band (or tighter, consistent with a hard cap) is "Not recommended"; the screen also shows the verdict at ±5% and ±10% for reference; and the school policy document states that the current capacity band is the primary driver of the verdict, not the objective or the prior.

**Acceptance:** FR-23 and FR-25 acceptance criteria met; three-band verdict table present; capacity band identified as the decisive input in the screen narrative.

*Conditional: if Richmond's capacity band is later confirmed at ±5% or ±10%, re-run the screen on the production optimizer and report the revised verdict before any grid change.*

---

### Story 4: Aid office director — mid-cycle increases only

**Given** Richmond is mid-cycle with approximately half of offers released (timing unknown; see OQ-04),
**When** the enrollment team requests a mid-cycle increases-only analysis,
**Then** the system: (a) identifies deposited, released-undecided, and unreleased students; (b) applies increases (Δ_i ≥ 0, ≤ D) only to unreleased offers; (c) checks the budget and class ceiling at b_H; (d) evaluates revenue from revisions to released offers at b_L; and (e) outputs the revised grid for unreleased offers, the projected class, and a budget summary. Released offers keep their committed award.

**Acceptance:** FR-17 and FR-39 acceptance criteria met; no decrease on any released offer; budget check explicit in the output.

---

### Story 5: Frankel analyst — blinding not possible (test-only primary)

**Given** Richmond reported that blinding is not possible — aid staff cannot deliver a test bonus as a formula line with no test flag (Q8),
**When** a price test is designed (if the screen later recommends one at a different capacity band),
**Then** the system: (a) records blinding_flag = false in model_run.json; (b) sets the primary estimator to test-only at dose 0; (c) reports the all-eligible estimate as secondary; and (d) includes the blinding limitation in the alignment-gate disclosure packet.

**Acceptance:** FR-43 acceptance criteria met; primary estimator labeled correctly in all output; all-eligible estimate present as secondary.

---

### Story 6: Enrollment dean — geographic redistribution objective

**Given** Richmond wants to use bonus aid to target geographies at the state or MSA level (Q1 and Q12),
**When** the targeted-objective constraint is set,
**Then** the system: (a) adds a minimum expected enrollment constraint for each designated state or MSA tier as a linear constraint holding at all three scenarios; (b) runs the runtime proxy screen to check whether the geographic target is a proxy for race or ethnicity (Cramér's V ≥ 0.3 triggers alignment-gate acknowledgment); (c) reports the shadow price per enrollee for each geographic target; and (d) outputs the equity audit with allocation changes by group.

**Acceptance:** FR-36 and FR-38 acceptance criteria met; geographic targets on the whitelist (state, CBSA); shadow price reported; proxy screen fires if V ≥ 0.3.

**[v2.7, V27-33; revised November 13, V27A-01]** In the scenario evaluator, Richmond's geographic lever is a single combined priority segment (NY and PA) with one incentive aimed at it (FR-74, FR-77) **[v1.3, B5-1]**. The state and MSA targeted objective above stays the optimizer path; per-state and MSA tiers in the evaluator wait for Richmond's state-level counts and about two cycles of data.

---

### Story 7: Enrollment dean — aid redistribution away from the barbell

**Given** Richmond wants to move from full-ride / full-pay extremes to a more even distribution,
**When** the optimizer runs in total-award mode with the two-sided rule and segment floors,
**Then**: if the evidence audit finds an anchor, the optimizer reallocates within the segment floors (no segment average below 75% of its trailing average; highest-need and Pell-eligible segments at 100%) **[v2.7, V27-33: the per-cell guardrail is removed]**; if no anchor is found, the system outputs the documented status-quo grid with a note that the redistribution objective requires either a qualifying price source or a test.

**Acceptance:** FR-34 acceptance criteria met; floor shadow prices reported; redistribution cannot override the weak-evidence state block.

---

### Story 8: Enrollment dean — comparing scenarios with class size and tuition what-ifs [v2.7]

**Given** Richmond has written several scenarios (admit rates, awards, a pool multiplier) and wants to see what happens if the class lands anywhere from 100 to 140 under the 140 cap (including which admits would be trimmed), if tuition rises 5.0% to 6.5%, if yield is lower than assumed, or if an incentive aimed at the target states (NY and PA) is added,
**When** the dean opens the scenario evaluator or the Excel workbook,
**Then** the system shows class, revenue, spend, discount rate and median position for each scenario at the L, M and H cases with probabilities; the class-size table (shrink path), tuition and yield-shift what-if tables, the pool strip, the segment and incentive blocks; and the labels that apply. The Excel workbook and the policy document (and the dashboard, once added) show the same numbers **[v1.3]**.

**Acceptance:** FR-71 to FR-74 and FR-77 to FR-80 acceptance criteria met (in the workbook; the dashboard add-on follows) **[v1.3]**; the tuition what-if states that sticker price does not change applications or yield.

---

## 6. Non-functional requirements

| # | Requirement | Priority | Source | Acceptance pointer |
|---|---|---|---|---|
| NFR-01 | **Privacy / small cells.** No student-level data is loaded to Supabase or shown in the hosted dashboard. **[v2.7, V27-28]** Small cells follow the engagement's `small_cell_policy` (FR-76): by default, cells with fewer than 10 students are suppressed before any load or display, with complementary suppression so suppressed cells cannot be recovered by subtraction; Richmond has no suppression for its named, authenticated roles (Cat and Richmond staff signed off, November 5, 2026). | MVP | §2; §9 | Guardrail tests 1 and 2 pass (test 2 checks the configured policy) |
| NFR-02 | **Secure channel.** All student-level returns (batch scores, melt lists, policy lookup, mid-cycle award suggestions) go to the client through the client's established secure channel (Galaxkey for Richmond). Never through Supabase or the dashboard. | MVP | §7; §9; Q14 | FR-59 acceptance criteria met |
| NFR-03 | **Lineage and reproducibility.** Every published run records: input hashes, software versions, pipeline parameters, and the policy_changes log. Re-running the pipeline on the same inputs must reproduce all aggregate outputs to within MILP solver tolerance. | MVP | §6; roadmap §3 model_run.json | model_run.json present; re-run matches outputs to within 0.055% on scenarios.csv and validation files |
| NFR-04 | **Explainability.** Every number in every deliverable carries either a sensitivity range (b_L, b_M, b_H), a confidence interval, or an explicit statement of why it has neither. Numbers never appear without context. | MVP | §6; roadmap §4 design constraints | No unranged number in the policy document or dashboard; "stated reason" label present where intervals are omitted |
| NFR-05 | **Runtime budget.** The full pipeline (synthetic data → optimizer → aggregate → load) must complete in under 141 seconds on the v2 baseline machine (the existing v2 pipeline ran in 87 seconds at 40 bootstrap draws). The Monte Carlo study targets at most 30 seconds per seed without a bootstrap. | M1 | roadmap §5 phase 1 acceptance | Pipeline runtime measured and reported in model_run.json; fails if it exceeds 141 s |
| NFR-06 | **Equity audit before publication.** The equity audit (FR-50) must be reviewed and signed off as part of every alignment-gate packet before any deliverable is published to the client. | MVP | §9 | Sign-off date in model_run.json post-dates the equity audit run date |
| NFR-07 | **Protected-attribute exclusion.** Race, ethnicity, and gender are never model inputs, grid dimensions, or optimization targets. A test enforces it per attribute, and a runtime proxy screen checks geographic targets. | MVP | §9 | Guardrail test 3 passes; FR-37 and FR-38 acceptance criteria met |
| NFR-08 | **Consumer data sequencing.** Build the consumer pipeline first on synthetic data and the free ACS/IRS source. Licensed Claritas data (gate L1) is not loaded until L1 is signed. Counsel review of the license and proxy note precedes first grid use. | M1 | Appendix E.1; §14 | L1 flag checked before any licensed-data code path executes; counsel-review flag in consumer_gate_status before grid use |

---

## 7. Out of scope, closed, and deferred

**Closed (do not reopen without Jason's direction):**
- Per-student optimization (replaced by policy lookup; §14 closed decisions)
- Grid-tier price estimation from historical awards using smooth controls on GPA (deferred to a future phase; §11)
- Third-party applicant-reported timing data (license and data-quality issues; §14; executive read)
- Protected attributes (race, ethnicity, gender) as model inputs or grid dimensions
- Individual-level consumer credit data (credit scores, bureau matches, tradelines; §9; §14)
- Per-student choice of which capacity tiers apply (breaks the policy lookup and equity audit; §5 and §14)

**Out of scope for this engagement (Richmond cycle 1):**
- Clearinghouse destination data (client must order it; delivery timing uncertain; J10 in GAP_LOG)
- Admitted-student survey (separate client process)
- Sticker-price optimization (requires evidence on applicant-pool response; §11)
- Loan-access response estimation from the 2026 Grad PLUS cap change (requires fall 2026 census data)
- Wave-specific slopes (requires four conditions in §4; will not be met with one cycle)
- Segment price-sensitivity moderators (requires the moderator adoption gates; §4)
- Consumer capacity tier in the law grid (default is no tier until W21L shows G2 can be powered; O35)

**Deferred (trigger conditions in §11):**
- Boosted-tree forecast challenger (FR-64): margin and Monte Carlo pass criteria in §11
- Empirical prior pooled across clients: requires design-based estimates from at least three clients
- Adaptive price tests across admit waves: requires several admit waves and a standing test
- Year-specific retention modeling: requires three or more years of retention per cohort
- Time-varying treatment (revisions and appeals): requires treatment log in place for at least one cycle
- **[v2.7, V27-33]** Net-price yield response; per-state and MSA segments in the evaluator (a single combined priority segment is in scope, FR-77); goal-seek and the schedule layer; multi-year and trajectory views; the dashboard views until the workbook is accepted **[v1.3]**; admit-rate dimension in the optimizer; marginal-admit yield; Slate-based pool-growth pacing; USNWR planner feed (methodology §11)

---

## 8. Richmond MVP and timeline

**What the call answers make possible this cycle (assumes Tier 1 data received within the next four to six weeks)**

| Deliverable | Feasible this cycle? | Note |
|---|---|---|
| EFA funnel and drivers | Yes | Three cohorts in Slate; Galaxkey transfer established (Q14) |
| In-cycle pacing and melt monitoring | Yes | Slate export; biweekly refresh |
| ABA 509 market view | Yes | Partial peer set confirmed (Q11); need remaining schools to reach 5–10 |
| Evidence audit | Yes | Must evaluate the 2025 barbell-to-even policy change and any prior thresholds |
| Documented status-quo grid | Yes | Dean must confirm the grid matches practice |
| Scenario evaluator and Excel scenario workbook **[v2.7]** | Yes | First deliverable **[v1.3]**. Needs Richmond's cell-level history and state-level counts; the response is based on client-input until an anchor exists. Dashboard views follow as an add-on |
| Geographic market analysis (state/MSA) | Yes | Richmond confirmed state and MSA level; ZIP3 sufficient (Q2, Q12) |
| VOI screen | Yes | Inputs needed: N, p, and the formal capacity band percentage (see OQ-01) |
| Optimized grid | **Conditional** | Only if the evidence audit finds a qualifying source; likely not this cycle |
| Price test operations | **Pending re-run [v2.7]** | The earlier "Not recommended" verdict (hard cap, ±3% band, A2) was computed under the 5% guardrail, which v2.7 removes. Re-run the screen (O36) before telling Richmond anything about a test; formal production-optimizer screen required (OQ-01) |
| Consumer ZIP add-on | Not this cycle | Gated (L1, counsel review); Richmond's geographic objective does not require it (ZIP3 sufficient per Q2) |
| Batch scoring | Not this cycle | Requires out-of-time calibration pass; forecast model not yet built on Richmond data |

**What waits for the next cycle:** the optimized grid (if the evidence audit finds a source or if the capacity band changes), a price test (if the screen changes at a wider band), batch scoring, and the Clearinghouse match.

**Alignment gate requirements for the Richmond MVP (this cycle):**
1. Dean signs off on the documented status-quo grid (confirms it matches practice).
2. Dean signs off on the equity audit for the EFA and market deliverables.
3. Dean signs off on the geographic targeting approach (state and MSA; no finer than CBSA).
4. If the evidence audit finds any anchor: full alignment-gate sign-off on the optimized grid, including the evidence status and the screen verdict.
5. **[v2.7]** Record of the small-cell disclosure policy: date and scope of Cat's and Richmond staff's sign-off, and the roles that see small cells (aid office, enrollment team, leadership).

---

## 9. Traceability matrix

| FR | Methodology section | Review/audit finding addressed | Acceptance test or world |
|---|---|---|---|
| FR-01 | §4 screen inputs; E7 | F3, A3 (capacity band mandatory) | Scoping table present; screen rejects if capacity_band null |
| FR-02 | §5 status-quo grid | F6, O1 | Client confirmation in alignment-gate packet |
| FR-03 | §9 protected attributes | R11 | Guardrail test 3; static schema tests |
| FR-04 | §3 data model; §7 | R5, F10 | Guardrail tests 4 and 6; QA log |
| FR-05 | §3 law Tier 1; data request v3 | Verification Report §5 gaps 1–6 | All Tier 1 required fields present |
| FR-06 | §2 descriptive layer | R8, R12 | Small-cell policy enforced as configured; table set fixed |
| FR-07 | §2 driver layer | R9 | Clustered SEs; associational label |
| FR-08 | §2; §4 response model | R11 | Guardrail test 4 |
| FR-09 | §2 relative position | F13, A14 | Bands frozen; GRE/JD-Next concordance flag |
| FR-10 | §2 geography | O12 | No address in output; market funnel |
| FR-11 | §2 academic index; §4 | F5 | Index and raw variables present |
| FR-12 | §2 stages | — | Stealth flag; inquiry logit exclusion |
| FR-13 | §7 monitoring | R2 (no optimization) | Pacing matches hand calculation |
| FR-14 | §7 monitoring | F10, R4 | W0L: 90% interval covers census in ≥ 85% of seeds |
| FR-15 | §7 monitoring | R12 | Guardrail test 1 |
| FR-16 | §3; §7 treatment log | F18, A22, O9 | Reason codes present; revisions excluded |
| FR-17 | §5 increases-only; S5-7 | O7 | Three-group formula; no decrease on released offers |
| FR-18 | §2 ABA 509; E10 | F13, A11–A17 | 75th-pct. grant = prior-year tuition; lag = 1 yr |
| FR-19 | §2 ABA 509 uses (a),(c) | F13 | Peer set 5–10; conditional flag |
| FR-20 | §2 use (b); Appendix D | F13, A18, E11 | Full-tuition branch unit test; illustration regenerated |
| FR-21 | §2 use (d) | F13 | Yield from 509 compared; peer yield not a prior |
| FR-22 | §4 evidence audit; S4-9 | F3, O3 | Source-by-source check table; μ0, σ0, anchor flag |
| FR-23 | §4 screen; S4-7; E3–E7 | F3, A1–A7 | Worked-example reproduced (A1); three-band table |
| FR-24 | §4 screen; E4 | A5 | Unconstrained-Bayes EVSI ≥ 0; negative EVSI reported with sign |
| FR-25 | §4 screen | A3, E7 | Six items and three-band table present |
| FR-26 | §5 weak-evidence state; O2 | F1, A8 | W6: no level change when q10 ≤ 0 (100%) |
| FR-27 | §5 no admissible grid; §1 | F2 | W9: no anchor → no grid (100%) |
| FR-28 | §4 anchor; E13 | R10, F5, A23 | W5: flag in ≥ 70%; coverage ≥ 85% |
| FR-29 | §5 law profile; S5-2; S5-4; V27-07 | F2, F14 | Decision layer ≤ floor(admits ÷ 30); fine matrix rendered by rule; total-award mode; horizon |
| FR-30 | §5 fixed thresholds; V27-06 | — | Cut points fixed within a cycle; policy_changes populated |
| FR-31 | §5 choice rule; S5-1; E3 | F1, A8–A10 | W0, W0L: no level change when q10 ≤ 0 (100%) |
| FR-32 | §5 constraints; E9 | R4, F10, A29 | W0L: overrun ≤ 5% of budget in ≤ 5% of seeds |
| FR-33 | §5 (guardrail removed v2.7); S5-5 superseded | F20 | Retired; see FR-33a |
| FR-33a | §5 constraints; V27-01 | F20 | Step-size table present; no flag or label on any award |
| FR-34 | §5 floors; Appendix C | R1 (international cut artifact) | Floor rows in optimizer; shadow prices in output |
| FR-35 | §5 solver outputs | R11 | Five scenario types; class-floor absent when non-binding |
| FR-36 | §5 targeted objectives; E8 | A30 | Median expectation only; P(median holds) separate |
| FR-37 | §5 whitelist; §9 | R11 | Guardrail test 3; blocked-attribute unit tests |
| FR-38 | §5 enforcement; §9 | F17 | Proxy screen fires in ≥ 70% of planted-proxy seeds |
| FR-39 | §5 increases-only; S5-7 | O7 | No decrease on released offers in any fixture |
| FR-40 | §5 outputs | §6 | Evidence status present; no unranged number |
| FR-41 | §4 price test; S4-5 | F4, F12, A6 | Arm shares exact within strata; D in law range |
| FR-42 | §4 price test | F19 | Treatment log populated; random assignment verifiable |
| FR-43 | §4 analysis population; E1 | F7, F18, A22 | W12 variant: flagged or bias ≤ 10% in ≥ 90% of seeds |
| FR-44 | §4 estimation; E1 | F5, F7, A20 | AME at dose 0; labeled in output |
| FR-45 | §4 compliance; E1 | F18, A22 | Process contrast present; yield contrast labeled "low power" |
| FR-46 | §4 response model; E12 | F15, A24 | Two fixtures pass/fail as specified |
| FR-47 | §9 alignment gate | F18, O9 | Disclosure items in gate packet |
| FR-48 | §6 backtest diagnostic; S4-11 | R3, F8, F9, A33 | Model-set-budget basis; ratio reported |
| FR-49 | §9 alignment gate | — | Sign-off dated in model_run.json before delivery |
| FR-50 | §9 equity audit | F17 | equity_audit.csv present; v2 tables blocked |
| FR-51 | §9 consumer data; Appendix E.1 | O26 | Purpose statement; P2–P4 reports; counsel flag |
| FR-52 | §9; §7; Appendix E.2 | R11, R12 | All 8 tests pass; consumer tests pass |
| FR-53 | §5 policy lookup | O15 | Cell award = grid award for every student in cell |
| FR-54 | §7; roadmap §4 view 1 | R12 | Guardrail test 1; associational label |
| FR-55 | roadmap §4 view 2 | R5 | Three-sensitivity display; RLS for leadership role |
| FR-56 | roadmap §4 view 3 | R12 | Grid export matches policy_grid.csv |
| FR-57 | roadmap §4 view 4; §8 | — | market_reference table only; no student rows |
| FR-58 | roadmap §4 view 5; §9 | F17 | View access restricted; audit-only label |
| FR-59 | §7; §9 | R12 | Guardrail test 1; deletion log |
| FR-60 | roadmap §4 | — | Definition links and lineage panel on every view |
| FR-61 | roadmap §1; §9 small-cell disclosure | R12 | RLS tests all roles; small-cell policy applied before load |
| FR-62 | §7 batch scoring | O15 | All four release criteria in model_run.json |
| FR-63 | §7; Appendix E | O15 | File contents match specification |
| FR-64 | §11 boosted challenger | O19 | W20b pass before adoption |
| FR-65 | §2 consumer ZIP; Appendix E | O22; O29 | ZIP5 absent from all tables; deletion log |
| FR-66 | §10 consumer bake-off; §9 | O21; O35 | P1 in consumer_gate_status; G2 power at law size |
| FR-67 | §9 gates by use (targeting) | O26; O32 | No segment labels; gate status present |
| FR-68 | §4; §9 gates | O13 | Tier rejected unless G2 and G3 passed |
| FR-69 | §5 consumer tier; §9 | O24; O34; O35 | All five gates passed; law default no tier until W21L |
| FR-70 | §9 report-only P2–P4 | O26; O32 | P4 never a pass/fail field; reports in equity_audit |
| FR-71 | §5 scenario evaluator | — | Identities on toy grid; ledger equals optimizer for same grid; label present |
| FR-72 | §5 scenario evaluator | — | Excel equals Python; reproduce mode matches client reference workbook |
| FR-73 | §5 single evaluator | — | Excel, dashboard and policy document agree for the same run |
| FR-74 | §5 scenario evaluator, levers | — | Strip and what-if checks equal the ledger |
| FR-75 | §11 (deferred) | — | Deferred |
| FR-76 | §9 small-cell disclosure | — | Policy applied by loader; RLS by role; sign-off record stored |
| FR-77 | §5 scenario evaluator, segment; App. F | — | Merge invariance; scope; exact probability; decomposition identities; empty segment |
| FR-78 | §5 scenario evaluator, class range | — | Shrink path hits N below M; admits never rise; share non-decreasing below the threshold |
| FR-79 | §5 scenario evaluator, pool strip | — | Strip equals the ledger at each multiplier |
| FR-80 | §5 scenario evaluator, net tuition | — | Fixed and scaled identities |

---

## 10. Open decisions and assumptions log

Items are labeled **OQ** (open question requiring a Richmond answer), **OD** (open design decision), or **CONTR** (potential contradiction with methodology v2.6, flagged for Jason — not resolved here).

### 10.1 Open questions from blank or uncertain capture-sheet answers

| ID | Question | Why it matters | What would resolve it | Source |
|---|---|---|---|---|
| OQ-01 | What is the numeric class band Richmond accepts? Q6 says "hard seat cap, will fill to 100%." Does this translate to ±3%, ±2%, or a strict equality constraint? | Decides the formal VOI screen verdict. At ±3% the verdict is Not recommended under every pool and prior (A2). At ±5% or ±10% the verdict may change. | Richmond confirms the accepted percentage band; add to the scoping table (FR-01). | Q6; capture sheet screen table (blank) |
| OQ-02 | Renewal rule: are Richmond's JD scholarships fixed dollars or a percentage of tuition at renewal? Any renewal conditions (GPA, credits)? | Sets the commitment multiplier M (critical for the screen's cost estimate, which uses M ≈ 2.92 for a renewable three-year award), the revenue horizon, and the persistence model. Richmond reports no conditional scholarships in 509, but the renewal rule itself is not confirmed. | Q4 follow-up: confirm renewal structure before the screen runs. If awards are fixed dollars, a 5%+ tuition increase reduces the real value of awards over the commitment. | Q4 (blank) |
| OQ-03 | Renewal conditions: Richmond reports no conditional scholarships in its 509. Confirm directly. | If Richmond has no conditional scholarships, persistence = retention only (~0.97 in year 1, ~0.99 after), as the methodology assumes. If conditional scholarships exist, the persistence model changes. | Direct confirmation from the registrar or financial aid director. | Q4; §5 objective |
| OQ-04 | When did first offers go out for the current cycle, and what share of offers is already released? | Determines what can influence this cycle. A grid applies only to unreleased offers. If nearly all offers are released, the MVP this cycle is descriptive only. | Richmond confirms offer timing (Q10 says "probably beginning in Sept." — check whether that means September 2026 offers are already out). | Q10 (partial answer) |
| OQ-05 | Randomization appetite: Q5 says "perhaps." Is Richmond open to a price test at all, contingent on the screen verdict? Who beyond the dean must approve? | If the answer is "no" under any conditions, price-test operations (FR-41 to FR-48) can be moved to Deferred for Richmond. | Full follow-up conversation with the dean and any named approvers. | Q5 (partial) |
| OQ-06 | Negotiation tracking: how common are reconsideration and match requests? Are they logged in Slate with a reason and staff ID? | Required for the compliance diagnostics (FR-45) and for the revision reason-code log (FR-16). Without a log, negotiation data cannot be separated from price variation. | Q9 follow-up: confirm whether Slate captures this; if not, what would it take to add it. | Q9 ("I will need to find out") |
| OQ-07 | Is the enrollment team and the financial aid office the same staff in Slate, or separate? Who will own the weekly export during yield season? | Determines the monitoring cadence and who receives the policy lookup. | Q12 follow-up: confirm roles and owners for the Slate extract. | Q12 (partial) |
| OQ-08 | Budget horizon: is the scholarship budget set for one year or three years? | The methodology requires budget and revenue horizons to match the award commitment. A one-year budget against a three-year commitment is now rejected by the config validation (S5-10). This is a mandatory scoping input. | Q13 follow-up: confirm whether the budget is annual or multi-year. | Q13 ("can find out") |
| OQ-09 | Full peer set: Q11 names Washington and Lee, Lewis and Clark, William and Mary, George Washington, and "others." The ABA 509 procedure requires 5 to 10 schools. | The peer set drives the market award gap (FR-20) and the descriptive peer comparison (FR-19). | Richmond names the remaining peers (client-approved list of 5 to 10) before the first ABA 509 run. | Q11 (partial) |
| OQ-10 | Scope reaction: the capture sheet has a blank for Richmond's reaction to the stated scope at call close. | Confirms that the Richmond MVP scope (EFA, monitoring, ABA 509, evidence audit, written grid; conditional optimized grid) is accepted. | Confirm with Richmond in the follow-up email. | Capture sheet "Their reaction" (blank) |
| OQ-11 | Eligible admits and yield (N and p): the scoping screen table is blank for N and p. | Required as mandatory inputs to FR-01 and the VOI screen. These can be estimated from the 509 (Richmond: approximately 650 eligible admits per the worked example; yield approximately 21%), but must be confirmed from actual Slate data. | Tier 1 data extract. Use 509-based estimates as a placeholder until data arrive. | Capture sheet screen table (blank) |
| OQ-12 | Blinding follow-up: Q8 says "I don't think this is going to be possible." The answer would change the primary estimator (see FR-43). Confirm concretely: can the bonus appear in Slate as a formula line with no test-membership flag visible to the aid officer packaging awards? | This determines whether the all-eligible ITT is the primary estimator (blinding possible) or the test-only estimator is primary (blinding not possible). The Richmond answer in Q8 points toward test-only, but a concrete process confirmation is needed. | Process walkthrough with the financial aid director and the Slate administrator. | Q8 (uncertain answer) |

### 10.2 Open design decisions

| ID | Decision | What would resolve it |
|---|---|---|
| OD-01 | Whether the 2025 barbell-to-even policy change at Richmond constitutes a qualifying policy change under §4 criteria: requires ≥ 2 pre-period cohorts, ≥ 100 admits per cohort, change in net cost ≥ 3% of tuition, and an unaffected comparison group. A whole-school policy change is hard to compare internally; the comparison group may need to be a position-band subset where the award change was smaller. Cannot be determined without the actual award history. | Run the evidence audit (FR-22) on the Tier 1 data. Flag as a conditional requirement in Richmond's evidence plan. |
| OD-02 | Whether the pilot with Richmond is confirmed. The roadmap still says "assumed to proceed." S1 is written as if the engagement is signed; if it is not, FR-05 and the Tier 1 data request cannot move forward. | Jason confirms engagement status. |
| OD-03 | Which pitch copy is current and whether its privacy paragraph needs revision. The CHANGELOG v2.6 flags that the pitch deck's "No consumer credit data" and "No full ZIP codes" language conflicts with v2.6. The pitch copy was not verified during Phase A. | Jason confirms the current pitch copy and reconciles the privacy paragraph with §9 and Appendix E.3 before the Richmond follow-up. |
| OD-04 | Law timeline offsets in the data request v3 (+6 and +8 weeks). These are proposed, not from the plan. | S1 sign-off provides the basis; the Richmond timeline is then confirmed with the client. |
| OD-05 | Whether "holding the discount rate static this year" (Q2) is a hard optimizer constraint (cap on class-wide discount rate) or a stated preference. If it is a hard constraint, it is added to the scoping inputs (FR-01) and must not conflict with the geographic redistribution objective. | Clarify with Richmond at the follow-up. Add as a scoping input in FR-01 if confirmed as a hard constraint. **[V27A-02]** Dean Rooksby (Nov 13): the five-year plan is to maintain the discount rate; the evaluator shows an optional `discount_target` margin, and whether it is a hard optimizer constraint stays open. **[v1.3, B3-2]** Also open: which rate (entering class or all JD students; with or without fees); the evaluator labels its rate "entering class, first year" until Brandon answers (methodology O42). |
| OD-06 | Whether Richmond's geographic targeting (state or MSA) requires a targeted-objective constraint or is satisfied purely by grid cells (law profile: position × market, where market = home state / other). If a finer MSA-level breakdown is desired and the 30-admit-per-cohort cell minimum cannot be met, markets under 30 admits must be pooled. | Confirm the level of granularity Richmond needs in the follow-up. The law grid already includes home-state vs. other as the market dimension. **[v1.3, B2-10]** Partly answered: the evaluator uses one combined priority segment (NY, PA); whether the optimizer needs a state or MSA targeted-objective constraint stays open. |
| OD-07 | Dashboard scope for the Richmond MVP: the Handoff proposes views 1 (funnel/pacing), 4 (market context), and 5 (equity audit) as the first delivery for a no-anchor client. Views 2 (scenario planner) and 3 (policy grid) follow once an anchor or a documented status-quo grid is available. Confirm with Jason. | **Revised Nov 16, 2026 (Jason) [v1.3]:** the Excel workbook ships first; dashboard views 2 and 3 follow as an add-on once the workbook's core computation is accepted. *Superseded:* **Resolved Nov 5, 2026 (Jason) [v2.7, V27-34]:** the scenario evaluator (view 2) and the policy grid (view 3) ship in the first delivery with the Excel workbook, alongside the views the Handoff proposed. |
| OD-08 | **[V27A-02]** The class size path: 140 is a hard cap this cycle and the five-year plan is 100 to 115; whether the glide path starts this cycle (Jason's current understanding: yes) and at what target. | Ask Brandon; the evaluator supports 100 to 140 meanwhile. |
| OD-09 | **[V27A-06]** The exact 2027 tuition increase (Dean Rooksby: "just over 5.5%"; Brandon to confirm) and the tuition path beyond 2027, with undergraduate tuition by year (law is $11K below undergraduate today; Dean wants to narrow the gap). | Ask Brandon; planning scenarios use 5.5% until then. |

### 10.3 Potential contradictions with methodology v2.6

| ID | Item | What the methodology says | What the Richmond answers suggest | Flag |
|---|---|---|---|---|
| CONTR-01 | Screen verdict confidence before the production screen runs. | "The production screen must run on the real optimizer with a 509-calibrated pool" (§4; Verification Report §3). The audit ran on stylized pools only. | Richmond's hard cap strongly suggests "Not recommended," and the audit verified this at ±3% under every pool and prior tested. But the formal verdict requires the production run. | Do not state a final verdict in deliverables until FR-23 (production screen) has run. State the working assumption ("likely Not recommended at the current cap") and the path to a formal verdict. |
| CONTR-02 | Discount rate static vs. geographic redistribution. | The optimizer allows an optional cap on the class-wide discount rate (§5 constraints). | Richmond wants to hold the discount rate static this year (Q2) but also add bonus aid to geographic targets (Q1). Adding bonus aid while holding the discount rate static requires cutting aid elsewhere, which the floors (FR-34) limit; the per-cell guardrail (FR-33) was removed in v2.7. | Resolve at scoping: if the discount-rate cap is hard, model it as a constraint and run infeasibility reporting. If it is a preference, treat it as an objective weight. Do not resolve here. |
| CONTR-03 | "ZIP3 is going to work fine for us" vs. consumer ZIP add-on. | The consumer ZIP add-on (FR-65 to FR-70) uses ZIP5 for the append job to derive a capacity tier. Geographic targeting at state/MSA level uses the standard geography derivation (CBSA, state, ZIP3) and does not require the consumer ZIP add-on. | Richmond's statement that ZIP3 is sufficient was made in the context of geographic targeting, not the capacity tier. The consumer ZIP add-on and geographic targeting are separate features. | No methodology contradiction. Clarify with Richmond: the consumer ZIP add-on is optional and serves a different purpose (capacity tier for grid modeling, not geographic targeting). Richmond may not elect the add-on at all for its current objective. |
| CONTR-04 | Need as a grid dimension. | "In law, need is a grid dimension only if the school uses need in scholarships" (§5). | Q3: Richmond confirmed that need data (FAFSA or institutional) is used in scholarship decisions. | No contradiction; need is a valid grid dimension for Richmond. The law grid may be: position (5) × need (2) × market (2), giving 20 cells, within the cap of 21 for approximately 650 admits. This should be confirmed at scoping. |
| CONTR-05 | Tuition increase (~5%) and fixed-dollar renewal rule. **[V27A-06]** Richmond planning uses 5.5%, unconfirmed (OD-09). | The methodology notes that if awards renew as fixed dollars, a tuition increase changes the net cost (§3 renewal rule; §5 objective). | Richmond's planned tuition increase of just above 5% (Q2) and an unknown renewal rule (Q4) create a risk: if awards are fixed dollars, the real value of multi-year grants declines, which affects the three-year revenue model. | Do not resolve here. Resolve via OQ-02 (renewal rule). If awards are fixed dollars, the methodology handles it correctly through the renewal_rule field and the commitment-length horizon. Note the sensitivity in the policy document. **[v2.7, V27-34]** Tuition migration is now a scenario lever (FR-74); the renewal rule stays open (OQ-02) and the multi-year sheet is a stub until it is answered. **[V27A-06]** Dean Rooksby (Nov 13): tuition up just over 5.5% with the discount rate held; the evaluator shows fixed and scaled awards side by side and the net price change (FR-80). |

---

## S1 is done when

- [x] Every FR traces to a methodology section. (Traceability matrix, §9.)
- [x] Every Critical and High finding from the review and audit maps to at least one FR or acceptance criterion. (F1 → FR-31; F18/A22 → FR-43, FR-44, FR-45; A3 → FR-23, FR-25; A5 → FR-24; A30 → FR-36; A29 → FR-32.)
- [x] No FR contradicts the methodology. (Five potential contradictions flagged in §10.3; none resolved in this document.)
- [x] The evidence-state table matches the deliverables described in the pitch materials that can be verified. (§3 table; Pitch deck privacy paragraph remains open, OD-03.)
- [ ] Jason signs off.

---

*Not verified in this document: the pitch deck's current copy and privacy paragraph (OD-03); the Grad PLUS and loan-limit statements (deferred to Federal Student Aid confirmation); whether Frankel holds an existing Claritas contract (O28 and L1); the undergraduate data request v3 template against a real undergraduate client (GAP_LOG J10). These items do not block S1 sign-off but must be resolved before the corresponding builds proceed.*
