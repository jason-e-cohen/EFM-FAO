# Opus Re-review Instructions: EFA + FAO v2.4 (S4 statistical methods, S5 optimization)

Paste this as the first message in a new chat. Attach files only when a phase says to. Stop at the end of each phase and wait for "continue."

---

**Role.** You are an independent reviewer with expertise in causal inference, enrollment analytics, and constrained optimization. You did not design this method. Be specific and adversarial, and don't praise. Don't write production code or review UI. Use synthetic data only; never ask for real client data. State your confidence (low, medium, high) for every Critical or High finding, and separate what the materials show from what you suspect. If an area is sound, say so in one line. If you find nothing Critical, say so plainly.

**Context.** The product has two parts. EFA is the funnel analysis from inquiry through enrollment at census. FAO recommends a scholarship policy grid (default 75 cells: academic index quintile x need band x residency) that maximizes expected net tuition revenue under budget, class-size, discount, and guardrail constraints. Price sensitivity is anchored in design-based evidence (a randomized bonus-aid test and merit-grid discontinuity); everything else is simple.

You reviewed an earlier version and found twelve issues (R1 to R12). The author has since replaced the segment pattern with one anchored slope, replaced the bootstrap with three sensitivity scenarios, dropped the realization multiplier, deferred CVaR budget constraints, and moved from per-student awards to a policy grid. **This is a re-review of that response, not of the old design.** You have no memory of the earlier review, so use the findings below.

| ID | Earlier finding | v2.4 response |
|----|-----------------|---------------|
| R1, R2 | Segment price pattern wrong; recommended setting beaten by uniform slope | Pattern removed; one slope |
| R3, R5 | Realization ratio does not carry over; bands and probability uncalibrated | Multiplier and probability dropped; three scenarios |
| R4 | Budget holds only on average | Checked at all three scenarios |
| R6 | Hybrid average did not equal the anchor | Conversion rule plus a 1% test |
| R7 | One seed | Lean Monte Carlo: 8 worlds x 50 seeds |
| R8 | Forecast overpredicts yield | Out-of-time recalibration |
| R9 | Comparisons not spend-matched | Baselines matched within 1% |
| R10 | Pooled estimates differ | Inverse-variance pooling, flag at 1.5 SE |
| R11, R12 | Class floor never binds; asymmetric response to cuts untested | Shipped only if binding; support rule and a loss-averse world |

**Project direction to respect.** Historical data may *propose* candidate moderators and mechanisms of price sensitivity, but slopes are set only by design-based evidence. For graduate and professional programs, the preferred primary moderator is relative position within the program's own score distribution (for example LSAT and undergraduate GPA against the 25th, 50th, 75th, and possibly 85th percentiles), refined by engagement signals and award gap versus the market. The observational aid-versus-applicant-quality confound must be tracked and planted in the synthetic worlds so tests check that the pipeline recovers the truth.

**Scope added in v2.3.** Batch enrollment-probability scoring (optional, secure-channel delivery); a policy lookup in place of per-student optimal packages; targeted objectives on whitelisted policy attributes including geography (MSA or similar), with race and ethnicity blocked as targets; a market tier option for the grid; a scoping evidence audit; a price-test sample-size guide and numeric screen rule; and the price test as an add-on. **Out of scope, do not design:** the grid-tier price estimator (all admits, smooth controls on GPA) is deferred to a future phase, and per-student optimization is not planned.

**Scope added in v2.4.** An ABA 509 reference layer for law schools (peer pricing, a rank-matched market award gap, conditional scholarships, a yield prior, synthetic-world parameters); horizons that follow program length, with conditional-award persistence; sensitivity by date learned from wave-stratified tests within the client's own data; and a rule keeping a regularized logit as the forecast default with a boosted-tree challenger for scoring only. **Closed, do not revisit:** collecting applicant-reported timing data from third-party sites (license and data quality).

---

## Phase 1: Cold review (about 700 words)

**Attach:** `02_methodology_v2.4.md`, `01_executive_read_v2.4.md`, `03_technical_roadmap_v2.4.md`, `CHANGELOG_v2.4.md`. No results yet.

**Task**
1. List your strongest objections to the design, ranked, with confidence.
2. Rule on the departures from your earlier review, each as **confirm, change, or reject**: three scenarios instead of posterior draws; no realization correction; CVaR deferred; inverse-variance pooling with a 1.5 SE flag; policy grid instead of per-student awards.
3. Review open issues O1 to O11 in methodology section 13. For each: is it real, how severe, and is the proposed resolution right?
4. Check internal consistency of S4 and S5 (for example, whether the response formula and the forecast's feature list agree, and whether the three scenarios can break the choice rule).
5. Review the sample-size guide and cost estimate in methodology section 4 (the 0.85 covariate adjustment, the 21% yield and 1.5-point plausible-effect assumptions).
6. **Re-evaluate the price-test screen rule.** The rule: recommend a test when the smallest detectable effect after the planned cycles is at most about 2.3 points per $1,000 (1.5 times a plausible 1.5-point effect). The author accepts it as a starting point only. Is the threshold defensible? Are 80% power and the 1 to 3 point plausible range right? Is a power-based rule the right basis, or should the rule come from the value of information (the expected gain from a better allocation against the test's cost and delay)? Propose a replacement if it is wrong.
7. Review targeted objectives, the market tier, and geography: infeasibility, thin-history markets (O12), proxy risk, and the cell cap (O14).
8. Review the 509 reference layer (the rank-matching assumption, field definitions, and limits; O16), the program-length horizon and conditional-award persistence (O17), and the wave-stratified timing approach (O18).

## Phase 2: Test against results (about 800 words plus table)

**Attach:** the v2-build validation outputs (recovery table, strategy backtest, holdout accuracy, segment recovery, scenarios).

**Task**
1. Revise Phase 1: mark each concern confirmed, dissolved, or new.
2. Test these claims against the outputs and say what each can and cannot support: the one slope beats the segment pattern (one seed, one cohort); the 40/20/40 test design cuts the slope's standard error from 0.56 to about 0.44; the three-scenario range would have covered the realized gain in the backtest (the uniform slope predicted about 60% more than it realized); the anchor conversion rule.
3. Return a findings table:

| ID | Severity | Finding | Why it matters | Evidence | Proposed fix | How to test it |
|----|----------|---------|----------------|----------|--------------|----------------|

4. List every claim in the documents that these outputs do not establish, and what would establish it.

## Phase 3: Design work (about 1,000 words)

No attachments. Produce specifications precise enough for an engineer to implement.

1. **Monte Carlo study:** worlds (mechanism, parameters, what each should break), seeds per world, metrics, numeric pass thresholds, and false-fail rates. Include the missing worlds named in O6, a Tier 1 discontinuity-only world, and worlds that plant the aid-versus-applicant-quality confound at several strengths.
2. **Fair baselines** (proportional rescale, need-first fill, fence-sitter rule) and the margin by which the policy grid must beat the best of them.
3. **O1 and O2 as exact rules:** how the forecast baseline is defined, and the behavior when the anchor's low scenario is at or below zero.
4. **Policy grid spec (O4):** total versus discretionary awards, relation to the merit grid, need formula, and appeals, pool projection while offers roll out, and fixed thresholds that preserve discontinuity evidence.
5. **Moderator discovery protocol for graduate and professional programs:** how candidates are generated from history, how they are tested on the randomized arm, what may influence allocation and when, and how relative position within the program is defined.
6. **Increases-only evaluation:** what changes in the budget and class-size checks when communicated offers can only rise.
7. **Evidence audit:** the checks, the minimum evidence for a usable threshold or policy-change comparison, and how the one-page result feeds the screen.
8. **Targeted objectives and market tiers:** exact constraint forms, feasibility and shadow-price reporting, behavior in thin-history markets, and the whitelist test that blocks protected attributes.
9. **Batch scoring governance (O15) and the consumer-segment add-on (O13):** what must be true before either is released.
10. **Screen rule specification:** if you change the rule, specify it exactly: the inputs the client supplies, how decision value is computed, the thresholds for Recommend, Optional, and Not recommended, and worked examples for colleges with 600, 1,000, 2,000, and 4,000 eligible admits a year.
11. **ABA 509 layer:** the exact rank-matching procedure, how to validate it in a synthetic law world with known truth, which 509 fields are allowed where (descriptive only versus candidate moderator), and the yield-prior use for thin history.
12. **Timing and sensitivity by date:** the wave design (number of waves, stratification, sample size per wave and the smallest detectable effect), how to treat negotiation and reconsideration revisions, and what a wave-specific slope must show before it changes a recommendation.
13. **Boosted-model challenger:** set the margin (out-of-time AUC and Brier), the calibration, monotone-constraint, and reason-code requirements, the synthetic worlds with interactions needed to test it, and whether it should ever feed the optimizer baseline.

## Phase 4: Verdict and edits (about 600 words)

1. **Verdict** (under 150 words): is the design fit to build on, and what are the two or three issues that matter most?
2. **Numbered edits** to the S4 and S5 text (methodology sections 4, 5, 6, 10, and Appendix C), each stated as old behavior, new behavior, and acceptance test.
3. **Release readiness:** what must be true before Claude Code starts building.
4. **Open questions** for the author, and what you could not verify.

---

**Rules for all phases.** Where two designs are both defensible, label it a judgment call and say what would change your mind. Do not propose methods that need data a typical small private college lacks without saying what to do instead. Do not pad.
