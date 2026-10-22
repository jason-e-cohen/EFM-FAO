# Auditor Brief: Scoped Audit of the S4 and S5 Re-review (v2.4)

**Requested by:** Jason Cohen, Frankel Agency
**Date:** October 21, 2026
**Material under audit:** `S4_S5_Rereview_v2.4.md` (the "review"), with the scripts in `review_support_v2.4/`
**Design under review:** `02_methodology_v2.4.md`, `01_executive_read_v2.4.md`, `03_technical_roadmap_v2.4.md`, `CHANGELOG_v2.4.md`
**Time budget:** about 4 to 6 focused hours. Stop when the five tasks below are done.

## Role

You are an independent auditor with expertise in causal inference, enrollment analytics, decision analysis, and constrained optimization. You did not write the review or design the method. Your job is to **confirm, correct, or overturn specific conclusions**, not to re-review the whole design. Be adversarial and specific, and don't praise. Use synthetic and public data only; never ask for real client data.

For every finding, state:
- your confidence (low, medium, or high);
- whether it is **Shown** (reproduced or read directly) or **Suspected** (reasoned).

If a conclusion holds, say so in one line and move on.

## Context in brief

The product has two parts. **EFA** analyses the funnel from inquiry to census enrollment. **FAO** recommends a scholarship policy grid that maximizes expected net tuition revenue under budget, class-size, and guardrail constraints. Price sensitivity is one logit slope, anchored in design-based evidence: a randomized bonus-aid test and/or a merit-grid discontinuity.

The first pilot is a law school, the University of Richmond School of Law. The review uses Richmond's public ABA 509 data as baselines:
- about 650 to 690 offers a year and about 146 matriculants;
- yield about 21%;
- tuition $57,700;
- about 28% of students at or above full-tuition grants;
- no conditional scholarships.

The review reached these conclusions:

1. **Critical:** the v2.4 choice rule checks only the low-sensitivity scenario, which tilts weak-evidence recommendations toward aid cuts. The proposed fix is a two-sided rule.
2. **Critical:** the S5 optimization spec cannot represent a law school's status quo (75% per-student cap, $0 to $12,000 ladder, year-one horizon versus three-year renewable awards, cell count).
3. **High:** the price-test screen (recommend if the minimum detectable effect is at most about 2.3 points per $1,000) should be replaced by a value-of-information screen. Under that screen, Richmond is **Not recommended** for a revenue objective at every size from 600 to 4,000 admits with a ±3% class band.
4. **High:** analysing all randomized eligibles, including those randomized out of the test, cuts the slope's standard error from about 0.44 to 0.29 at no extra cost.
5. **High:** the backtest's three-scenario range covered the realized gain by coincidence.
6. **High:** the Monte Carlo gate's 50 seeds give an 11.5% false-fail rate on the coverage band.
7. **Medium:** several ABA 509 fields are misread for rank-matching (prior year, recipients only, all classes, matriculants).

The review's author rated its own confidence as follows. Focus your time accordingly.
- **High:** conclusions 1 (as logic), 2, 4, 6, and the cost multiplier.
- **Medium:** conclusion 3 (it rests on a stylized model), the two-sided rule's practical behavior, the 509 field definitions, and the logit-unit pooling argument.
- **Lower by nature:** the Phase 3 thresholds, which are judgment calls.

## Tasks

### Task 1. Stress-test the value-of-information verdict (highest priority)

**Inputs:** `voi2.py`, `evpi.py`, `table.py` (law, capped), `voi.py` (uncapped contrast), and review Phase 3 §10.

1. **Reproduce** the worked-example table (EVPI, EVSI, cost, net value at 600, 1,000, 2,000, and 4,000 admits) within rounding.
2. **Break it.** Test whether the **Not recommended** verdict for Richmond (about 650 admits) survives each of the following:
   - **a richer pool:** at least 5 position bands with realistic yield and net-tuition gradients (yield falls with position; grants rise with position);
   - **class bands** of ±3%, ±5%, and ±10%;
   - **priors** on the AME at status-quo awards of N(0.6, 0.5²), N(1.0, 0.5²), N(1.4, 0.5²), and N(1.0, 1.0²);
   - **a median-position target** (enrolled students above the target position at least half the class) in place of the revenue-only objective;
   - **a one-year (non-renewable) bonus** in place of a renewable one.
3. **Check the cost model.** Is cost at zero effect, with no induced-revenue offset, the right cost for a capacity-capped program? Is the opposite treatment right for an uncapped one?
4. **Check the logic of the decision model.** Is EVPI computed correctly relative to the no-test choice under the two-sided rule? Is EVSI bounded by EVPI in every case?

**Deliverable:** a table of verdicts across the variations, and a one-paragraph answer to: *under what conditions, if any, would a price test be Recommend or Optional for Richmond?*

### Task 2. Test whether the two-sided choice rule makes the product inert

**Inputs:** review Phase 3 §3; the backtest code `bt.py` with `lagr.py` and `stub/`.

The rule chooses the grid that maximizes revenue at the middle slope, subject to gain ≥ 0 at **both** the low slope (max(0, q10)) and the high slope (q90), with all constraints holding at all three.

1. On the synthetic Lakeshore world (v2 backtest setup, uniform slope), report how much of the middle-scenario gain the two-sided rule keeps compared with the one-sided rule. Use anchor SEs of 0.30, 0.46 (v2), and 0.70.
2. On a Richmond-calibrated pool, report how often the rule returns the status quo across the priors in Task 1.
3. Does the rule bias toward the status quo more than a minimax-regret or posterior-expected-value rule would? Recommend one rule, or confirm the review's.

**Deliverable:** the share of gain retained, the frequency of status-quo outcomes, and a recommendation with reasons.

### Task 3. Verify the ABA 509 field definitions

**Inputs:** ABA Standard 509 instructions and definitions (public); `aba-509-saas/data/` (2021 to 2025 reports); review Phase 1 §1.8 and Phase 3 §11.

Confirm or correct each of the following from the ABA's own definitions:
1. The grants and scholarships section of report year Y describes the **prior** academic year (Y − 1). The review inferred this from Richmond's 75th-percentile grant equaling prior-year tuition in two reports.
2. The grant percentiles are **among recipients**, not all students.
3. The grant section covers **all JD students**, not the entering class.
4. LSAT and UGPA percentiles describe **matriculants**.
5. The lag on conditional-scholarship counts.
6. The meaning of a 0 nonresident tuition for private schools in the scraped table.

Then judge whether the rank-matching procedure in Phase 3 §11 correctly handles each confirmed definition.

**Deliverable:** a confirm-or-correct table with sources, plus any required change to the procedure.

### Task 4. Check the estimand and pooling argument

**Inputs:** `desim.py`, `chk.py`; review Phase 1 §1.1 (#5, #7), Phase 2 §2.2(b), Phase 3 §3; `efa_fao/src/efa_fao/pipeline/models.py` (`experiment_estimate`, `rd_estimate`, `design_anchor`).

1. Reproduce the simulated standard deviations (uniform 0.548, 40/20/40 0.438, two-arm 0.391, all-eligible 0.287) and the estimand values (1.31 at status-quo awards, 1.49 at bonus-inclusive awards).
2. Is pooling **logit slopes** (each converted on its own sample at status-quo awards) the right way to combine an experiment and a local discontinuity under the one-slope assumption? What breaks if the true logit slope differs between the discontinuity's local population and the eligible pool?
3. Is the all-eligible (intent-to-treat) analysis valid when staff may treat test-cohort admits differently from non-test admits? What compliance check would detect a problem?
4. Is the review's replacement for the 1% conversion test meaningful? That replacement compares the model's AME at status-quo awards (recalibrated p) with the experiment's own status-quo AME, within 5%.

**Deliverable:** confirm or correct each point, with numbers where you reproduced them.

### Task 5. Spot-check arithmetic and internal consistency

1. **Richmond baseline table:**
   - estimated average grant (about $30,700) and discount (about 55%);
   - net tuition per enrollee (about $26,000);
   - three-year multiplier (about 2.92);
   - break-even slope (about 0.9 to 1.0 points per $1,000);
   - enrollment count SD (about 10.4, 7.6% of class).
2. **Richmond sample-size table** in Phase 1 §1.5 (covariate factor 0.92, p = 0.21, 40% in the test).
3. **Monte Carlo false-fail rates** in Phase 3 §1.
4. **Cost per test student:** $1,226 at a $4,000 top arm and $2,453 at $8,000, three-year renewal.
5. Any place where two sections of the review contradict each other, or where a Phase 3 rule cannot be implemented as written.

**Deliverable:** a list of errors with corrected values. If none, say so.

## Out of scope

- Re-reviewing the methodology from scratch, the dashboard, the database schema, or UI.
- Writing production code. Analysis scripts are fine.
- Revisiting closed decisions: third-party applicant-reported timing data; per-student optimization; grid-tier price estimation.
- Proposing methods that need data a typical small private college or law school lacks, unless you say what to do instead.

## Environment notes

- The review's scripts ran without scipy. `stub/` supplies `expit`, `brentq`, and a placeholder `milp`, and `lagr.py` replaces the MILP with a Lagrangian solver for the single-budget knapsack (it reproduces the repo's backtest within 0.1%). If you have scipy and HiGHS, rerun with the repo's own solver and report any difference.
- Paths in the scripts point to a scratch copy of `efa_fao/`; adjust them.

## Output format

Return one markdown file, `Audit_S4_S5_Rereview_v2.4.md`, with these sections:

1. **Verdict on the review** (under 150 words): does it hold, hold with minor revisions, or need material revision? Name the conclusions that changed.
2. **Findings table**

| ID | Task | Review claim | Audit result (Confirmed / Corrected / Overturned) | Severity of any error | Confidence | Evidence (Shown / Suspected) | Required change to the review or to v2.5 |
|----|------|--------------|---------------------------------------------------|-----------------------|------------|-----------------------------|-------------------------------------------|

3. **Task deliverables** 1 to 5, as specified above.
4. **Edits required to `02_methodology_v2.5.md`**, each stated as old text or behavior, new text or behavior, and acceptance test.
5. **What you could not verify.**

Propose the smallest fix, not a redesign. Where two choices are both defensible, label it a judgment call and say what would change your mind. Don't pad.
