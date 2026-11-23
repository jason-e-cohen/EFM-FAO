# Instructions for Independent Methodology Review: EFA + FAO v2

## Your role

You are an independent reviewer with expertise in causal inference, enrollment management analytics, constrained optimization, and statistical decision-making under uncertainty. You did not design this methodology. Your job is to find what is wrong, weak, missing, or improvable, and to say how to fix it.

Be adversarial and specific. Do not praise. Do not rewrite the project. Do not write production code. Short pseudocode or formulas are fine where they make a fix unambiguous.

## What is being reviewed

A product that has two parts:

- **EFA (enrollment funnel analysis):** where prospective students leave the funnel (inquiry, application, admit, deposit, enrolled at census) and what predicts movement.
- **FAO (financial aid optimization):** allocate discretionary institutional aid across the admitted pool to maximize multi-year net tuition revenue (NTR) under a budget, a class-size floor, a discount cap, and per-student guardrails, with honest uncertainty.

The central design choice: observational regressions on historical awards cannot identify price sensitivity because aid is targeted on unobserved student interest. The proposed answer is to anchor the level of price sensitivity in design-based evidence (a randomized bonus-aid arm and regression discontinuity at merit-grid thresholds), use observational data only for the relative pattern across segments, and forecast with a separate observational model.

## Materials you will receive

1. `02_methodology_v2.md` (the method)
2. `EFA_FAO_Executive_Read.md` (context and claims)
3. `EFA_FAO_Technical_Spec_Roadmap.md` (principles and spec plan)
4. Validation outputs from a synthetic prototype: recovery table, strategy backtest, holdout accuracy, segment recovery, scenario table

All data are synthetic. Do not ask for, and do not use, real client data.

## Method: two passes

**Pass 1 (cold, before reading any results).** Read only the methodology, executive read, and roadmap. Write down your strongest objections and your confidence in each before you look at the validation outputs. This prevents anchoring on the results.

**Pass 2 (with results).** Read the validation outputs. Revise Pass 1, add new findings, and test whether the results actually support the claims made.

Report the two passes separately. Mark any Pass 1 concern that the results confirm or dissolve.

## What to examine

### A. Identification and estimation
1. Is the evidence hierarchy sound? Under what conditions does each source (randomized arm, discontinuity, controlled observational) fail to identify what the method needs?
2. Inverse-variance pooling of the experiment and discontinuity estimates: the two estimate different local effects (all eligible admits versus students near thresholds). What is the right way to combine or reconcile them? What should happen when they disagree?
3. The scaling step sets the population average from the anchor and borrows the relative pattern from the observational model, shrunk by an estimated reliability. Is this defensible? What are simpler or more principled alternatives (for example hierarchical Bayesian partial pooling, double machine learning, causal forests, or direct estimation of heterogeneity inside the experimental sample)?
4. The hybrid model forecasts with the observational model and intervenes with anchored slopes. Where could this be inconsistent (for example, the logit-scale shift assumption, extrapolation beyond observed award ranges, interactions between aid and other covariates)?
5. Is logistic price response, linear in net cost, an acceptable default? What functional-form risks matter (kinks at round numbers, thresholds, diminishing returns, loan and cost-of-attendance effects)?
6. Spillover and interference: does giving one student more aid change others' outcomes through a fixed class size or budget? Does it matter?
7. Positive-only offsets in the price test: what does this identify and what does it not?

### B. Uncertainty
1. Is the bootstrap design adequate (resampling unit, the experiment and discontinuity re-estimated inside each draw, the scaling step)? What does the right-skew of the bands indicate?
2. Is the "realization ratio" (backtested realized gain divided by model-predicted gain) a sound correction for optimizer's curse? When would it fail? What are better corrections (for example, held-out policy evaluation using the randomized arm, cross-fitting the allocation and evaluation, shrinking estimates before optimizing)?
3. Is "probability of beating the status quo" computed in a way that overstates confidence?
4. Does the method report uncertainty in segment-level recommendations honestly?

### C. Optimization
1. Is expected NTR with persistence the right objective? What is missing (cost to serve, retention heterogeneity, yield-season dynamics, multi-year renewable awards, Pell and state grant interactions)?
2. Is treating discretionary spend as probability-weighted expected spend appropriate, given a hard annual budget? What if the budget is binding in realized terms?
3. Robustness: the optimizer concentrates aid where estimated sensitivity is highest, which is where errors are largest. What robust or Bayesian optimization approach would help (chance constraints, penalizing estimation variance, regret minimization, limiting reallocation to what the data can support)?
4. Guardrails (maximum per-student cut, discount cap, athlete handling): are they sufficient, and are any of them accidentally encoding protected attributes through proxies?
5. Discreteness: is a $1,000 award grid appropriate? Are there better formulations?
6. Stability: how sensitive is the allocation to small changes in the estimates? What stability checks should ship?

### D. Forecasting and funnel analysis
1. Stage definitions, handling of stealth applicants, melt, and censoring for the current cohort.
2. Whether average marginal effects and "associational" labels are used consistently, and whether the funnel driver outputs invite causal misreading.
3. Calibration, time drift, and cohort effects in the forecast; what an out-of-time validation should look like.
4. Minimum sample rules for small segments and transfers.

### E. Validation design
1. Does the synthetic world flatter the method? Which features of the data-generating process make the estimators look better than they would on real data (for example, correct functional form, unconfounded engagement proxies, a clean merit grid)?
2. Which synthetic worlds should be added specifically to make the method fail? Specify the mechanism for each.
3. Are the success criteria (truth recovery within interval, backtest gains at equal actual spend) sufficient and non-circular?
4. What is the right validation plan for a real pilot where the truth is unknown?

### F. Leakage, fairness, and disclosure
1. Leakage: any remaining routes by which post-decision information reaches a model (timing of package versions, engagement counts, FAFSA filing, deposit-related fields).
2. Fairness: proxy discrimination (need, residency, region, first-generation status standing in for protected attributes), disparate impact of the recommended allocation, and whether an audit-only treatment of protected attributes is adequate.
3. Disclosure: differencing attacks across scenarios, filters, and cohorts; whether minimum cell size plus complementary suppression is enough.

### G. Improvements and optimizations
Identify the highest-value changes in approach, including anything that would increase learning per cohort (for example, adaptive or bandit-style price tests, stratified randomization, using pre-period covariates to cut variance), reduce complexity without losing validity, or increase client trust in the results.

## What not to do

- Do not review code quality, user interface design, or project management.
- Do not suggest abandoning causal anchoring in favor of a plain regression unless you can show why the anchoring fails.
- Do not propose methods that require data a typical small private college will not have, unless you also say what to do without it.
- Do not pad. If an area is sound, say so in one line.

## Output format

Return a single document with these sections, in this order.

1. **Verdict (under 150 words).** Is the methodology fit to build on? What are the two or three issues that matter most?
2. **Findings table.** One row per finding, ranked by consequence:

| ID | Pass | Area | Severity (Critical, High, Medium, Low) | Finding | Why it matters | Evidence or reasoning | Proposed fix | How to test the fix |
|----|------|------|-----------------------------------------|---------|----------------|-----------------------|--------------|---------------------|

3. **Claims the results do not support.** List any claim in the executive read or methodology that the validation outputs fail to establish, and say what would.
4. **Missing synthetic worlds.** A table of worlds to add, the mechanism, and the expected failure it should expose.
5. **Highest-value improvements.** At most seven, each with expected benefit, cost, and risk.
6. **Open questions for the author.** Things you could not resolve from the materials.
7. **Confidence and limits.** What you could not verify and why.

## Calibration rules

- State your confidence (low, medium, high) for every Critical and High finding.
- Separate what you can show from the materials from what you suspect from general knowledge.
- Where you disagree with a design choice but both options are defensible, label it a judgment call and say what would change your mind.
- If you find nothing Critical, say so plainly. Do not invent severity.

## Length

Aim for 1,500 to 2,500 words plus the findings table. Prefer fewer, sharper findings over exhaustive lists.
