# EFA + FAO scenario evaluator: methods reference

**For:** a statistician, econometrician or data scientist who needs to understand, audit or defend what the scenario workbook computes. It assumes probability, regression and some causal inference; it assumes nothing about admissions.
**State described:** November 19, 2026: spec `Prototype_Spec_Scenario_Workbook_v0.6.md` v0.6.3 (section 0A governs), methodology `02_methodology_v2.8.md`, decisions to Nov 19 in `DECISIONS.md`. Items the Phase 4 fix pass will change are marked **[fix pass]**.
**Companion:** `guides/Guide_Quickstart_and_HowTo.md` (how to run it). This document says what is computed, under what assumptions, and how we know the code computes it.

**Authority.** This reference explains; it does not define. Where it and the spec or methodology differ, the spec (section 0A first) and methodology Appendix F win, and this reference has a bug.

---

## Contents and reading paths

| Part | Section | Question it answers |
|---|---|---|
| I. Frame | 1. The problem and the estimand gap | What decision is this for, and why can we not just regress yield on aid? |
| | 2. Architecture: evaluator now, estimator later | What is built, what is specified, and how they connect |
| II. Model | 3. Notation and data | What a cell is; every symbol used below |
| | 4. The deterministic ledger | How a scenario becomes expected counts and dollars |
| | 5. The response placeholder | Where yield comes from when there is no causal estimate |
| | 6. The stochastic model and closed forms | How expected counts become probabilities and ranges |
| | 7. Strips, tables and decompositions | The what-if readouts and why each is exact or approximate |
| III. Outputs | 8. Metric register: primary, derived, display | Which numbers carry the analysis and which follow from them |
| IV. Assurance | 9. Verification: how we know the code is right | Tests 1 to 26, mutation checks, Excel parity, reproduce mode |
| | 10. Assumption register | Every assumption, where it bites, how it could be checked |
| | 11. Known limitations and open questions | What we do not claim |
| V. Beyond the evaluator | 12. The estimation pipeline and optimizer (specified, not built) | How the placeholder gets replaced |
| Appendices | A. Symbol index; B. Formula cross-reference; C. Auditor's checklist | Lookup |

**Reading paths.**
- *Auditing the probabilities:* 3, then 6, then 9 (tests 2, 4, 22), then 10 (A6 to A10).
- *Auditing the revenue figures:* 3, then 4, then 8, then 9 (tests 1, 8, 19, 25).
- *Challenging the causal claims:* 1, then 5, then 10 (A1 to A5), then 12.
- *Reviewing a build:* Appendix C.

---

# Part I. Frame

## 1. The problem and the estimand gap

A school chooses, for each cell of its applicant pool, an **admit rate** and a **merit award**. These jointly determine the entering class size, its score distribution and first-year net tuition revenue. The decision is made once a year under uncertainty about how many admits will enroll.

Two kinds of uncertainty matter, and the design keeps them separate throughout:

1. **Outcome uncertainty given the response.** Even if each admit's enrollment probability were known, enrollment is random (binomial noise) and years differ (a common shock to all yields). This is what the workbook's **probabilities and 90% ranges** describe.
2. **Uncertainty about the response itself.** How much does yield move per $1,000 of award? This is a causal quantity. Historical cell data do not identify it: staff give more aid where they expect weaker interest, so the cross-sectional association between award and yield is biased toward zero or negative. In the project's synthetic world the legacy-style regression recovers about 0 points per $1,000 against a true effect of about +1.3 (methodology section 4, "The problem"). On the client fixture the raw cross-sectional slope is slightly negative (spec section 10, confounding row). This is what the **Low, Middle and High cases** describe.

The workbook never combines the two (spec section 4, "Range kinds"). A 90% range is always within one response case.

**Consequence for design.** Until a school has design-based evidence on the response (a randomized aid test or a qualifying discontinuity; section 12), the workbook evaluates scenarios the client writes, using a response slope the client chooses, and recommends nothing. Every output that depends on that slope carries the label "Response based on client-input" (rule in `CLAUDE.md`, V27-41).

*Transition.* Section 2 shows where the evaluator sits in the larger design; Part II then builds it up from data to probabilities.

## 2. Architecture: evaluator now, estimator later

| Component | Status | What it does | Defined in |
|---|---|---|---|
| Scenario evaluator (the workbook) | **Built** (Phases 1 to 4) | Client-written scenario to expected outcomes, probabilities, what-ifs | Spec v0.6.3; methodology 5, "Scenario evaluator" |
| Reproduce mode | Built, accepted | Runs the client consultant's own scenarios through our ledger to prove arithmetic equivalence | Spec 0A-B, 9 |
| Response estimation (S4) | Specified | Randomized bonus test and discontinuity designs to estimate the slope θ | Methodology 4 |
| Policy-grid optimizer (S5) | Specified | Chooses award grids under a two-sided robustness rule | Methodology 5 |
| Monitoring, dashboard | Specified / deferred | In-cycle tracking; hosted aggregates | Methodology 7; roadmap |

**The interface.** The evaluator consumes a response as a function `yield(cell, award, case)`. Today it is the placeholder of section 5. When the pipeline supplies an estimated response, it arrives as a rung table per cell and case, and one Ledger column switches from formula to interpolation (spec section 4, "Yield method"; section 15 item 3). Nothing else in the evaluator changes; the label changes from "client-input" to the evidence status.

**Python is the definition; Excel mirrors it.** Every figure is computed in Python (`sw/`) and written to Excel as a live formula. Tests require the two to agree on every formula cell (section 9). This lets the client change levers in Excel while we keep a tested reference implementation.

---

# Part II. Model

*Where you are:* the next four sections build the model in the order data flows: cells (3), deterministic expectations (4), the yield input (5), randomness (6), then the derived what-if readouts (7).

## 3. Notation and data

### 3.1 Cells
A **cell** c is a group of admits sharing:
- residency r_c in {in, out};
- segment membership (optional; a client-listed subset of one residency, e.g. Richmond's NY and PA applicants within out-of-state);
- score band with lower bound `score_lo_c` (blank for unscored applicants);
- GPA class in {hi, lo, blank}.

Per cell and historical cohort the data are applications, admits, award (dollars) and enrolled. The schema admits no other column, and the loader refuses student identifiers; protected attributes cannot enter (test 7). All modeling is on cells; there is no student-level data in the workbook.

### 3.2 Indices and symbols

| Symbol | Meaning |
|---|---|
| s | Scenario (Baseline, or a child that names a parent and changes some levers) |
| c | Cell |
| k | Response case: L, M, H (Low, Middle, High slope) |
| T_s | First-year tuition in scenario s |
| A_c | Admits in cell c (scenario implied) |
| a_c | Award in cell c, after incentive and cap |
| y_c | Yield in cell c (case implicit) |
| μ_c = A_c y_c | Expected enrolled |
| v_c = A_c y_c (1 − y_c) | Binomial variance of enrolled |
| s (in risk formulas) | SD of the common year shock, `common_shock_sd` (0.10 illustrative) |
| ρ | Correlation of shocks between cells at/above and below a threshold |
| Φ | Standard normal CDF |
| t, q | Score threshold; percentile share (median q = 0.5) |
| G₊, G₋ | Expected scored enrolled at or above / below t |

Full index: Appendix A.

### 3.3 Inputs at three levels
| Level | Examples | Where |
|---|---|---|
| Client constants | Score bands, pool threshold, floor, class cap and target, need total and reference class, percentile targets, risk settings | `config/<client>.yaml` (build-time) |
| Scenario levers | Admit rates and awards per cell, pool multiplier, tuition change, bonus and scope, yield shifts, segment lift, specialty aid, class target | `config/scenarios_<client>.yaml`; editable on the Levers sheet |
| History | Cell counts by cohort | Data file |

Build-time constants that a user edits in Excel trigger a "rebuild needed" check rather than silently recomputing (spec section 7).

## 4. The deterministic ledger

*Purpose:* map a scenario to expected counts and dollars per cell and case. Everything here is an expectation; randomness enters in section 6. Source: spec section 3, items 1 to 8.

### 4.1 Tuition
T_s = round_to(T_base × (1 + p_s), $50), where p_s is the tuition increase. If the client gives a plan-year dollar figure (`tuition_by_year_usd`), p_s is the implied increase, stored unrounded so rounding returns the dollar figure exactly (0A-A2; test 21 checks 200 random bases).

### 4.2 Applications and admits
apps_sc = apps_c,base × m_sc × (1 + λ_s · 1[c ∈ segment]), with m_sc = pool multiplier if score_lo_c ≥ pool threshold, else 1. The segment lift λ applies at all scores, after the pool multiplier.
A_sc = apps_sc × rate_sc (rounded only when integer admits are configured, as in reproduce mode).

### 4.3 Awards and the incentive
- award_base: if the cell is flagged full tuition, T_s; else the lever award, scaled by (1 + p_s) if awards scale with tuition; capped at T_s.
- award a_sc = min(award_base + bonus_s × eligible_sc, T_s), with eligibility by scope (out-of-state, segment or none) and an optional minimum score.
- incentive_sc = a_sc − award_base_sc ≥ 0; less than the bonus where the tuition cap binds.

### 4.4 Yield
y_sck = clip( clip(response(c, a_sc, k)) + shift_sc/100 , floor, cap ) with floor 0.03 and cap 0.60 (Richmond config). The response is clipped, the shift added, and the result clipped again. Shift precedence: segment override, else residency override, else global; overrides replace rather than add.

**Two structural assumptions sit here** (register A2, A3):
- **D1: yield does not depend on the admit rate.** Admitting more of a cell admits more students with the same enrollment probability (no marginal-admit decline).
- **D10: sticker price does not move applications or yield.** Yield responds to the award in dollars; tuition changes affect revenue only, unless the analyst adds a shift.

### 4.5 Enrollment and money
- e_sck = A_sc × y_sck; class_sk = Σ_c e_sck.
- merit = Σ e × a; incentive cost = Σ e × incentive (included in merit).
- need = need_rate × class, with need_rate = need.total / reference_class. A scenario's departure from the client's need total is a fixed dollar amount (R4-07, Nov 19), not a rate change.
- gross_y1 = class × T; aid = merit + need + specialty; **ntr_y1 = gross_y1 − aid**; **discount_entering_y1 = aid / gross_y1**.

**Ratios of expectations.** Discount rate, average aid, shares and the barbell index are E[X]/E[Y], not E[X/Y] (spec section 3, "Ratios"). This is a definitional choice: it makes every ratio a closed-form function of the Ledger and keeps Excel and Python identical. The difference from E[X/Y] is second order in the coefficient of variation of the denominator (small at class sizes above 100).

### 4.6 Score-distribution quantities
For threshold t:
- **Margin at t:** expected enrolled with score ≥ t minus expected enrolled with score < t. Unscored enrollees are in neither term (the ABA 509 rule; O41 closed) and are reported as a count.
- **Share at or above t:** expected at or above t ÷ expected enrolled with a score.
- **Percentile target {q, t}:** "at most a share q of scored enrollees score below t". Margin in swaps: margin_q_t = q × N_scored − G₋ (the number of below-t enrollees that could replace at-or-above-t enrollees at the same class size; one swap moves it by 1). For q = 0.5 the Summary shows the at-or-above-minus-below margin instead, so each event has one margin on the page (R4-03) **[fix pass]**.

*Transition.* Every quantity above is linear in e_c, which is linear in y_c. Section 5 says where y_c comes from; section 6 uses the linearity to get closed-form probabilities.

## 5. The response placeholder

*Purpose:* supply yield as a function of award, per cell and case, without a causal estimate. Source: spec section 4.

### 5.1 Base yield by partial pooling
For each cell, history gives ȳ_c (admits-weighted yield), ā_c (admits-weighted award) and n_c (total admits). The cell's latest award is a0_c. With slope b_k in points per $1,000:

y0_ck = [ n_c ( ȳ_c + (b_k/100)(a0_c − ā_c)/1000 ) + κ · ypool_c ] / (n_c + κ),  κ = 20

The cell mean is first moved from its historical average award to the current award along the assumed slope, then shrunk toward a pool mean. Pools fall back in order: (residency, segment, score group) if it has at least 30 admits; else (residency, score group); else score group; else all cells. A cell with no admits takes the pool value.

*Why shrink.* Cells are small (median about 8 to 12 admits per active cell in the fixture shape; spec section 10). Raw cell yields would put most of their variance into noise. κ = 20 means a cell with 20 admits gets half its own mean. This is an empirical-Bayes-style choice with a fixed, not estimated, κ (register A5).

### 5.2 Yield at a candidate award
yield(a) = clip( y0_ck + (b_k/100)(a − a0_c)/1000, 0.03, 0.60 ).
Slopes b_L, b_M, b_H = 0.5, 1.0, 1.5 points per $1,000 (Richmond config). These are client-input placeholders, chosen to bracket plausible values; they are not estimates (register A1).

**Linear, not logit.** The placeholder is linear in dollars with clipping. The pipeline's response model is a logit with one slope (section 12); the linear form is a deliberate simplification for a placeholder that is labeled as such, so that every downstream formula stays a `SUMPRODUCT`.

### 5.3 Evidence label
A cell's yield is **observed** if its award lies within the cell's historical award range ± $2,500, else **extrapolated**. The Summary reports the share of expected enrolled in extrapolated cells. The label describes how well yield is known at that award; it never limits the award (no per-cell guardrail; V27-01).

### 5.4 What the slope does and does not touch
| Depends on b_k | Does not |
|---|---|
| Yield wherever the award differs from a0_c (incentives, award changes, tuition scaling) | Baseline yield at current awards (b enters y0 only through the history-to-current adjustment) |
| Everything downstream of those yields | Pool multiplier, shift, admit-rate changes (D1) |

So the Low/Middle/High spread is near zero for a scenario that changes only admit rates and pool size, and large for incentive scenarios. Readers should not read a narrow case spread as low risk; it may mean the scenario does not touch awards.

## 6. The stochastic model and closed forms

*Purpose:* turn expected counts into probabilities and ranges. Source: spec section 5 and 0A-A1.

### 6.1 The model
Given admits A_c and yields y_c:
- each cell's enrolled count is binomial, independent across cells given a common year shock;
- the shock is multiplicative on yield: e ~ N(1, s²), cell yield = clip(e · y_c, 0, 1);
- for score-threshold events, cells at or above t and below t may receive shocks with correlation ρ (default 1, sensitivity at 0.5).

s = 0.10 is **illustrative** (register A6). It is the single most influential uncalibrated number in the workbook: at a class of 140, the shock contributes about s·M = 14 students of SD against about √Σv ≈ 10 from binomial noise. Calibration from public ABA 509 and IPEDS yield series is open issue O37; until then every probability carries SHOCK_LABEL and values beyond 5% / 95% display as "under 5%" / "over 95%".

### 6.2 Class
M = Σ μ_c, V = Σ v_c + s² M².
- P(class > cap) = 1 − Φ((cap + 0.5 − M)/√V)
- P(|class − target| ≤ band) = Φ((target + band + 0.5 − M)/√V) − Φ((target − band − 0.5 − M)/√V)
- 90% range M ± 1.645 √V, lower end clipped at 0.

The s²M² term is the variance of a mean-one multiplicative shock applied to M, by the law of total variance. Relative to the simulation model it overstates by s² Σ A_c y_c² (the binomial variance given the shock is slightly smaller when yields scale up), which is small.

### 6.3 Median
g_c = +1 if score_lo ≥ t, −1 if below, 0 if unscored. m = Σ g_c μ_c (the margin).
V_m = Σ_{g≠0} v_c + s² (G₊² + G₋² − 2ρ G₊ G₋).
P(median ≥ t) = 1 − Φ((−0.5 − m)/√V_m).

At ρ = 1 the shock term is s² m²: a common shock scales both groups, so the margin moves in proportion. At ρ < 1 the groups move differently and variance rises, which is the Summary's ρ = 0.5 sensitivity line ("if high-score and other admits' yields move differently year to year").

**Tie rule.** The median holds when at least half of the scored class is at or above t (inclusive). The ABA averages the two middle scores, so at an exact tie the published median can fall between bands. Near a tie, our probability can read a few points high (up to about 4 points on synthetic data). Kept deliberately and stated on the Summary, README and methodology (R4-08) **[fix pass for the wording]**.

### 6.4 Percentiles (generalizes 6.3)
For target {q, t}, with g = +q at or above t, −(1 − q) below, 0 unscored:
- E[M_q] = Σ g_c μ_c
- V_q = q² Σ_above v + (1 − q)² Σ_below v + s² (q² G₊² + (1 − q)² G₋² − 2ρ q(1 − q) G₊ G₋)
- P(percentile q at or above t) = 1 − Φ( (−1/(2n) − E[M_q]) / √V_q ), with q = m/n in lowest terms.

The −1/(2n) is the continuity correction for a lattice of step 1/n. At q = 0.5 (n = 2) the expression equals the median probability exactly (test 22, to 1e-12). Where fewer than 20 enrollees are expected below t the normal is weak and the figure carries PCT_APPROX_LABEL. For q = 0.25 and 0.75 the Summary shows a "band, not a score": the band the percentile most likely falls in.

### 6.5 Net tuition revenue
w_c = T − a_c − need_rate (net dollars per enrollee in cell c).
mean = Σ w_c μ_c − specialty; V_n = Σ w_c² v_c + s² (Σ w_c μ_c)².
P(ntr_y1 ≥ target) = 1 − Φ((target − mean)/√V_n).
Under `ntr_goal_basis: all_jd`, the target is reduced by client-supplied continuing-student revenue, held fixed (0A-A4; register A11).

### 6.6 Segment enrolled
Python computes P(E_S ≥ goal) exactly: the convolution of the segment cells' binomials, mixed over the shock with 20-node Gauss-Hermite quadrature. Excel uses the normal form with a continuity correction, and flags it "approximate (fewer than 30 expected)" when M_S < 30. The Summary shows Python's exact value as a static copy with a status row that turns stale if inputs change.

### 6.7 Why closed forms, and how good they are
Closed forms keep every probability a live Excel formula over Ledger columns, so a client's lever change updates the risk figures without code. The cost is a normal approximation. Section 9 gives the evidence: closed forms within 0.01 of exact convolutions on toy grids (test 2), and within 0.02 of 200,000-draw simulation on 20 synthetic worlds for class, median at ρ 1 and 0.5, percentiles and NTR (test 4).

*Transition.* Section 7 reuses these formulas across grids of one lever at a time. Because every figure is linear (means) or quadratic (variances) in quantities the Ledger already holds, the strips are exact functions of the lever, not re-runs.

## 7. Strips, tables and decompositions

| Readout | Varies | Holds fixed | Exact or approximate | Source |
|---|---|---|---|---|
| Tuition what-if | Tuition increase p over a grid | Class and mix; awards recomputed with the cap | Exact arithmetic; no demand effect ("Sticker-price demand effect not modeled") | Spec 3 |
| Yield strip | Uniform shift d on top of scenario shift | Admits | Exact in d while no cell clips; clip count shown; break-evens labeled "linear approximation" | Spec 3 |
| Pool strip | Pool multiplier m (replaces scenario value) | Yields | Exact: every quantity splits into a below-threshold part and an above-threshold part linear in m | Spec 3; 0A-A6 |
| Class-size table | Class target N | Response | Exact given the deterministic shrink path | Spec 3 (shrink path) |
| Incentive block | Scenario vs its parent | Everything except the bonus | Exact identities; validity flag if anything else differs | Spec 3 |

**Yield strip algebra.** With A_c admits and y_c yields: M(d) = Σ A_c (y_c + d); Σ A_c (y_c + d)(1 − y_c − d) = Σ A_c y_c(1 − y_c) + d Σ A_c(1 − 2y_c) − d² Σ A_c. So each row is three `SUMPRODUCT`s. Break-even shifts: (target − M)/Σ A_c for class; (NTR target − mean)/Σ w_c A_c for revenue.

**Pool strip algebra.** Split the Ledger at m = 1 into lo (cells below the pool threshold) and hi (at or above). Then M(m) = M_lo + m M_hi, V(m) = V_lo + m V_hi + s² M(m)², and for score events both G₊ and G₋ split, because cells below t can sit above the pool threshold (at Richmond the 165 band is below t = 166 but scales with the pool). Break-evens: m_class = (target − M_lo)/M_hi and m_q = −E[M_q]_lo / E[M_q]_hi, labeled "not a probability". A marker row shows where client-reported growth to date falls.

**Shrink path.** To reach a smaller class N < M, cut admits in a fixed order: ascending score (unscored first), then GPA class (blank, lo, hi), with segment cells at or above the floor protected until non-segment cells below the threshold are exhausted (Richmond: `above_floor`). Removable enrollment per cell rm_k = A_k y_k (r_k − floor_rate)/r_k; the walk removes rm_k in order until M − N is reached; a shortfall is reported if it cannot. Cells not cut keep their rates exactly. This is a **policy rule, not an optimizer**: it writes admit rates the analyst may overwrite. The unscored-first order has access implications, and the README says so (register A13).

**Incentive decomposition.** Over cells receiving an incentive, against a parent identical except for the bonus:
- cost C = Σ e_s × incentive;
- paid-anyway C_any = Σ min(e_p, e_s) × incentive, share C_any / C;
- additional enrollees dE = Σ (e_s − e_p); dSpend = Σ (e_s a_s − e_p a_p); aid per additional enrollee dSpend/dE when |dE| ≥ 0.5.
Identity checked in test 13: dSpend = Σ e_s(a_s − a_p) + Σ (e_s − e_p) a_p. All of it is what the assumed slope implies; none of it is an estimate of what an incentive causes.

---

# Part III. Outputs

## 8. Metric register: primary, derived, display

*How to read this.* **Primary** figures carry the analysis: they come directly from the ledger and risk model and are the ones to audit first. **Derived** figures are deterministic functions of primaries; if the primaries are right they are right, and tests check the identities. **Display** figures are presentation (labels, flags, held rows). Definitions: methodology Appendix F (item numbers in brackets).

| Metric | Class | Formula (section) | Depends on slope? | Depends on s, ρ? |
|---|---|---|---|---|
| Expected class M [F4] | Primary | Σ μ_c (4.5) | Where awards change | No |
| P(class > cap), class 90% range | Primary | 6.2 | Yes | Yes |
| Margin at t [F9]; P(median holds) | Primary | 4.6, 6.3 | Yes | Yes |
| Percentile margin (swaps), P(percentile holds) [F26] | Primary | 4.6, 6.4 | Yes | Yes |
| ntr_y1 [F14]; P(ntr_y1 ≥ target); NTR range | Primary | 4.5, 6.5 | Yes | Yes |
| Segment enrolled E_S [F18]; P(E_S ≥ goal) | Primary | 4.5, 6.6 | Yes | Yes |
| Applications, admits | Primary | 4.2 | No | No |
| gross_y1 [F11], merit, need, specialty [F12] | Derived | 4.5 | Merit: yes | No |
| discount_entering_y1 [F13], average aid | Derived (ratio of expectations) | 4.5 | Yes | No |
| Share at or above t [F10] | Derived | 4.6 | Yes | No |
| Full-tuition, no-merit-award counts; barbell index | Derived | Spec 3 | Yes | No |
| Price of the target (Baseline ntr_y1 − scenario ntr_y1) | Derived | Spec 3 | Yes | No |
| Incentive cost, paid-anyway share, aid per additional enrollee [F19 to F21] | Derived | 7 | Yes | No |
| Top-quartile merit share; step sizes [F25] | Derived (Distribution sheet) | Spec Phase 4 | Yes | No |
| Strips, class-size table, break-evens | Derived (exact functions of primaries) | 7 | Yes | Probabilities: yes |
| Evidence share [F24] | Derived | 5.3 | No | No |
| History 509 reconciliation | Data check (report only) | Spec 0A-B7 | No | No |
| Labels, held rows, "under 5%" | Display | Spec 4; R4-06 | — | — |

**Held figures.** For Richmond, `hold_position_rows: true` replaces every median and percentile figure with "held pending confirmation of the LSAT basis (OD-14)" **[fix pass]**, because the History 509 reconciliation found the client workbook's lower LSAT bands disagree with the published 509 percentiles.

---

# Part IV. Assurance

## 9. Verification: how we know the code is right

*Logic of the evidence.* Four independent layers, each answering a different question:

| Layer | Question | Evidence |
|---|---|---|
| Unit identities | Does each formula equal its definition at hand-checkable points? | Tests 1, 19, 22 |
| Statistical approximation | Are the closed forms close enough to the model they approximate? | Tests 2, 4, 13 |
| Implementation parity | Does Excel compute what Python computes, cell by cell? | Tests 3, 18, 26; desktop Excel check |
| Test strength | Would the tests notice a wrong formula? | Mutation check (test 20) |
| External equivalence | Does the ledger reproduce an independent client workbook? | Reproduce mode (test 6) |

### 9.1 Test catalogue
Full one-line descriptions: `prototypes/scenario_workbook/README.md`, "What each test proves". Grouped:

| Group | Tests | What they establish |
|---|---|---|
| Ledger identities | 1, 8, 12, 19, 25 | Every section 4 identity on a hand-computed toy grid; lever semantics (zero bonus equals parent; shift 0 equals parent; overrides replace); incentive scope; every interface-contract figure at a point where its formula can fail; the revenue-goal basis |
| Risk approximations | 2, 4, 13, 22 | Closed forms vs exact convolution (≤ 0.01) and simulation (≤ 0.005 on toy; ≤ 0.02 on 20 synthetic worlds); percentile closed form at q 0.10 to 0.75, ρ 1 and 0.5; exact segment probability vs simulation |
| Readouts | 14, 15, 16, 23, 24 | Shrink path hits N, keeps order, monotone share; pool strip equals the ledger at each m; class targets 100 to 140; segment protection order; pool break-evens zero the margin to 1e-9 |
| Robustness | 11, 17, 21 | Splitting cells into segment / non-segment changes no total; empty segment produces no division error; loader rejects malformed configs |
| Parity | 3, 9, 18, 26 | Every formula cell, every sheet, after forced LibreOffice recalculation (integers exact, floats 1e-6 relative), on main, edge and reproduce workbooks; every contract range equals the Python dump |
| Guardrails | 7 | No protected-attribute or student-level fields; no hidden content or external links; required labels present |
| Calibration of synthetic data | 5 | The generator meets its asserted shape targets in ≥ 90% of 20 seeds (calibration, not realism) |
| Reproduce | 6 | 57 of 57 derivable criteria against the client workbook (Phase 3, Nov 18) |
| Rendering | 10 | Summary to PDF for human review (not asserted) |

Current count (Phase 4 review, Nov 19): 307 collected; 234 passed and 72 skipped without the fixture.

### 9.2 Excel parity, and why the sentinel matters
A workbook written by Python stores cached values. A naïve test that opens it and reads values would read Python's own numbers back. So:
1. LibreOffice is run headless with a profile forcing full recalculation on load (`OOXMLRecalcMode = 0`);
2. a **sentinel** build sets every cached value to −999, so any cell not recalculated is detectable;
3. for desktop Excel, the analyst opens the sentinel in Excel, saves a copy, and `compare_excel_saved.py` compares every formula cell to Python and every formula string to the rebuild, refusing files that are not a recalculated sentinel of the current build id.

Last desktop result: reproduce sentinel build `08c50a6fabaf`, Excel for Mac 16: 29,063 formula cells, 0 mismatches (DECISIONS, Nov 18). A Windows Excel check precedes the first client delivery. One deliberate rounding probe (`ROUND(0.35/0.14, 0)`) shows engine dependence: 3 in Python, Excel for Mac and LibreOffice 26.8; 2 in LibreOffice 24.2 (R4-17).

### 9.3 Mutation checking
`tests/mutation_check.py` applies each listed mutant (a deliberate formula error) to a scratch copy and runs the suite. Acceptance: every mutant caught, except those recorded as unable to change any result on valid input. Phase 3: 115 of 115 Python mutants and 75 of 75 Excel-formula mutants caught. This is the main evidence that the tests in 9.1 have power, not just coverage.

### 9.4 Reproduce mode as external validation
The client's consultant built an independent scenario workbook. Loading its admit rates, awards and yields into our ledger, with its counting conventions, reproduces its class, merit, NTR (to the dollar after need rounding), threshold counts, full-tuition and no-award counts, and margins: 57 of 57 derivable criteria; 2 cells not reproducible from the file, excluded and counted (Phase 3). Reproduce mode validates **arithmetic and conventions**, not the response or the risk model; the client workbook has no probabilities.

## 10. Assumption register

Each assumption, where it enters, how much it matters, and what would test it. "Bites" means which outputs move if it is wrong.

| ID | Assumption | Enters | Bites | How it could be checked or relaxed |
|---|---|---|---|---|
| A1 | Yield responds linearly to award at slopes 0.5 / 1.0 / 1.5 pts per $1,000 (client-input) | 5.2 | Every scenario that changes awards | Randomized bonus test or discontinuity (12); labeled "Response based on client-input" |
| A2 | Yield is independent of admit rate (D1; no marginal-admit decline) | 4.4 | Pool and admit-rate scenarios overstate yield of added admits | Deferred until an estimate exists (`CLAUDE.md`, deferred features) |
| A3 | Sticker price does not move applications or yield (D10) | 4.4 | Tuition what-if overstates revenue gain from increases | Net-price response deferred; analyst can add a shift (ASSUMPTION_LABEL) |
| A4 | One slope for all cells | 5.2 | Heterogeneous response by score or residency is averaged | Moderator discovery in the pipeline (methodology 4) |
| A5 | Base yield shrinks toward pool with fixed κ = 20; pools need ≥ 30 admits | 5.1 | Small cells' base yields | Cross-validate κ on more cohorts; test 11 checks the pooling arithmetic |
| A6 | Common year shock, SD s = 0.10, multiplicative, normal | 6.1 | Every probability and range | Calibrate from public 509/IPEDS yield series (O37); synthetic world W22 |
| A7 | ρ = 1 between high- and low-score shocks | 6.3 | Median and percentile probabilities | ρ = 0.5 sensitivity line shown |
| A8 | Cell enrollments independent given the shock | 6.1 | Variance (understated if peer effects or cross-admit correlation) | Compare predicted vs realized ranges over cycles (annual cycle, roadmap 5B) |
| A9 | Normal approximation with continuity correction | 6.2 to 6.5 | Small expected counts | Tests 2, 4, 22; approximation flags below 20 or 30 expected |
| A10 | Inclusive tie rule for medians and percentiles | 6.3 | Can read a few points high near a tie | Stated on Summary (R4-08) |
| A11 | Need aid is a fixed rate per enrollee; departures fixed in dollars; continuing NTR held fixed | 4.5, 6.5 | NTR when class or mix changes | Client need model; OD-16 to confirm |
| A12 | Unscored enrollees excluded from score events (ABA 509 rule) | 4.6 | Margins and percentiles | O41 closed; 509 reconciliation |
| A13 | Shrink order: lowest score first, unscored first, segment protected above floor | 7 | Class-size table composition | Client policy; overwrite rates by hand |
| A14 | Score bands reflect each student's highest LSAT (509 basis) | Data | All score events | Held for Richmond (OD-14); data request asks for highest-LSAT bands |
| A15 | Ratios are ratios of expectations | 4.5 | Discount, shares | Definitional; second-order difference |
| A16 | Fractional admits treated as Binomial(floor) + Bernoulli(frac) | 6.1 | Negligible variance difference | Stated in spec 5 |

## 11. Known limitations and open questions

**What the workbook does not claim.**
- It does not estimate the effect of aid on enrollment. Scenario differences that involve awards are consequences of A1.
- Probabilities are model-based under A6 to A9 with an uncalibrated shock. They are comparative (scenario vs scenario) more than absolute until O37 closes.
- It does not optimize. The shrink path is a rule; the incentive block is accounting.
- It models one entering class for one year. Multi-year revenue (`ntr_horizon`, persistence, renewals) is a year-2 build.

**Open items that change numbers** (`DECISIONS.md`, open table): OD-14 LSAT basis (holds Richmond's score rows); OD-13 percentile target; OD-16 need departure rule; OD-09 base-year tuition (blocks the live Richmond build); O37 shock calibration; continuing-student NTR for `all_jd`.

---

# Part V. Beyond the evaluator

## 12. The estimation pipeline and optimizer (specified, not built)

This is how the placeholder in section 5 is meant to be replaced. Source: methodology sections 4 and 5. Brief, because none of it runs yet.

**Estimand.** θ: the average over eligible admits of the change in enrollment probability from +$1,000 of gift aid at status-quo awards, in points per $1,000 (methodology 4, "Estimand"). Under a one-slope logit, b = θ / (100 × mean p(1 − p)).

**Identification.**
1. A randomized, positive-only bonus-aid test (arms $0, D/2, D at 40/20/40, stratified), analyzed intent-to-treat with the effect evaluated at dose 0.
2. A regression discontinuity at an award threshold, or a qualifying policy change.
Each is converted to a logit slope at status-quo awards; they are pooled by inverse variance with the discontinuity's weight capped at 30%, and a disagreement flag at |z| > 1.5.

**Response model.** p_i(a) = expit( logit p*_i + b (a − r_c) ), with p* from a recalibrated forecast model that contains no aid fields and no protected attributes, and r_c the cell's status-quo reference award.

**Optimizer and choice rule.** Cases b_L = max(0, b̂ − 1.2816 s), b_M, b_H = b̂ + 1.2816 s. A grid is feasible only if every constraint holds in all three; the choice maximizes NTR at b_M subject to a non-negative gain over the status quo at both b_L and b_H. With weak or no evidence, the output is the documented status-quo grid. No price-level change without design-based evidence.

**Connection back.** When this runs, the evaluator's yield column reads the estimated response and the Low/Middle/High cases become the estimate's interval rather than placeholders.

---

# Appendices

## A. Symbol index

| Symbol | Meaning | Section |
|---|---|---|
| a_c, a0_c, ā_c | Award; current award; historical admits-weighted award | 4.3, 5.1 |
| A_c | Admits | 4.2 |
| b_k | Placeholder slope (pts per $1,000) for case k | 5.2 |
| e_c, μ_c | Expected enrolled | 4.5, 6 |
| v_c | Binomial variance A y (1 − y) | 6 |
| M, V | Expected class; its variance | 6.2 |
| m, V_m | Median margin; its variance | 6.3 |
| E[M_q], V_q | Percentile margin; its variance | 6.4 |
| G₊, G₋ | Expected scored enrolled at or above / below t | 6.3 |
| w_c | Net dollars per enrollee | 6.5 |
| s | Year-shock SD | 6.1 |
| ρ | Shock correlation across a threshold | 6.3 |
| κ | Pooling strength (20) | 5.1 |
| m (pool) | Pool multiplier | 4.2, 7 |
| d | Uniform yield shift (strip) | 7 |
| rm_k, R_k | Removable enrollment; cumulative | 7 |
| θ | Causal estimand, pts per $1,000 | 12 |

## B. Formula cross-reference

| Figure | This guide | Spec | Methodology | Code | Test |
|---|---|---|---|---|---|
| Ledger identities | 4 | 3 | F11 to F14 | `sw/ledger.py` | 1, 19 |
| Base yield, response | 5 | 4 | 4 (pipeline form) | `sw/response.py` | 11, 19 |
| Class, median, NTR risk | 6.2, 6.3, 6.5 | 5 | 6 | `sw/risk.py` | 2, 4 |
| Percentiles | 6.4 | 0A-A1 | F26 | `sw/risk.py` | 2, 22 |
| Segment exact | 6.6 | 3 | F18 | `sw/risk.py` | 13 |
| Strips | 7 | 3 | — | `sw/strip.py` | 15, 24, 8 |
| Shrink path | 7 | 3 | — | `sw/trim.py` | 14, 23 |
| Excel mirror | 2, 9.2 | 6 | — | `sw/workbook.py` | 3, 18 |
| Simulation | 6.7 | 5 | — | `sw/mc.py` | 2, 4 |

## C. Auditor's checklist

1. Read section 0A of the spec and the open-decisions table in `DECISIONS.md`.
2. Run the suite; confirm counts against 9.1. Run the mutation check (Python and Excel).
3. Pick one scenario. Recompute class, ntr_y1 and P(class > cap) by hand from the Ledger columns using sections 4 and 6.2.
4. Check one median probability at ρ = 1 and ρ = 0.5 against 6.3.
5. Open the sentinel build in desktop Excel; run `compare_excel_saved.py`.
6. Vary s from 0.05 to 0.15 in a copy and note how the probabilities move (A6 is the largest lever on them).
7. Confirm every response-dependent figure carries "Response based on client-input" and every probability carries the shock label.
8. Read the History 509 reconciliation; confirm held rows are held where the score basis is unconfirmed.
9. Record findings with severity and confidence, separating what is shown from what is suspected.
