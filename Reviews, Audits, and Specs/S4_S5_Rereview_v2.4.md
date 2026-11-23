# EFA + FAO v2.4: S4 and S5 Re-review

> **Errata (added October 22, 2026, after the audit).** The audit (`Audit_S4_S5_Rereview_v2.4.md`, Claude Fable 5.1) held this review with minor revisions. Both Critical conclusions stand. The review text below is unchanged. The following claims are superseded; read them as corrected here.
>
> | Claim in this review | Corrected | Audit finding |
> |---|---|---|
> | Test-only estimators carry a "+6% estimand bias" that the all-eligible analysis removes | No bias once the AME is evaluated at status-quo awards (1.29 to 1.34 against 1.31). The +6% to +11% is the received-dose evaluation point | A20 |
> | The all-eligible analysis cuts the SE from 0.44 to 0.29 (34%); simulation ratio 0.66 | About 20% in logit units (0.0345 to 0.0275, analytic 0.76). The 0.66 compared two different estimands. The all-eligible estimate is primary only if staff are blind to test membership | A21, A22 |
> | A median-position target could turn the test verdict positive | Not supported. At the 5%-of-tuition guardrail a raise-the-median target is infeasible for aid; a target makes the test less valuable | A4 |
> | A ±10% class band still gives Not recommended | Corrected. At N = 650 with a five-band pool and ±10%, the verdict is Recommend or Optional. The verdict is decided by the capacity band | A3 |
> | Conditional-scholarship counts lag two years | One year. Report year Y lists classes Y − 1 to Y − 3; the count is final after year one. The 2021 and 2022 files carry stale headers | A16 |
> | Rank-matching illustration: Wake Forest 66th quantile, $43,000 against $51,800 | Position 0.71, $47,100 against $55,550 | A18 |
> | Buffer of "about 12%"; spend SD 7.6%; P(overrun) about 25% | About 15% (award-weighted); spend SD 9.4%; about 30%. 7.6% is the count SD | A29 |
> | The §8 median constraint with the 1.645σ margin | Cannot be implemented: the status quo violates it. Constrain the expectation; report P(median holds) separately | A30 |
> | "Perfect knowledge of the slope is worth less than one cycle of the cheapest test" | True only at the base prior ($0.31M against $0.34M). False at N(0.6, 0.5²) ($0.68M) and N(1.0, 1.0²) ($0.41M) | A32 |
>
> Also from the audit, not claims of this review but relevant to it: EVSI under the production rule can be negative (A5); the cost of a capped test is understated by about 19% (A6); the uncapped-contrast numbers used the zero-effect cost (A7); the two-band Richmond pool has no admissible reallocation, so its status-quo verdicts overstate the rule's inertness (A9).

**Reviewer:** independent (Claude Opus 5.5), October 21, 2026. I did not design this method.
**Read:** `02_methodology_v2.4.md`, `01_executive_read_v2.4.md`, `03_technical_roadmap_v2.4.md`, `CHANGELOG_v2.4.md`; the v2 build (`efa_fao/src`, `config`, `outputs`, synthetic data); ABA 509 files in `aba-509-saas/data` (2021 to 2025 reports). Synthetic and public data only.
**Computed for this review** (scripts and results in `review_support_v2.4/`):
1. I re-ran the v2 backtest for the uniform-slope policy and evaluated the same allocation at the three sensitivity scenarios.
2. I simulated four price-test designs, 300 replications each, on the synthetic eligible pool.
3. I ran Richmond sample-size and value-of-information calculations.
4. I computed binomial false-fail rates for the Monte Carlo thresholds.

The sandbox had no scipy, so I used a Lagrangian knapsack solver. It reproduces the repo's backtest within 0.1% (predicted +$0.977M, realized +$0.605M).

**Conventions**
- **Severity:**
  - **Critical:** produces a wrong or unusable recommendation for the pilot.
  - **High:** biases a client-facing number or blocks a vertical.
  - **Medium** and **Low** as usual.
- **Confidence** (Critical and High only): low, medium or high.
- **Shown** means read in the materials or reproduced by computation. **Suspected** means reasoned but not yet tested.
- **MVP tier:**
  - **M0:** fix in the spec before Claude Code starts.
  - **M1:** fix before the Richmond pilot produces client numbers.
  - **M2:** defer, with a trigger.

## Richmond baselines (ABA 509)

| Item | Value | Source |
|---|---|---|
| Offers and matriculants | 689 offers and 146 matriculants in 2025. Offers ranged 631 to 691 and matriculants 117 to 146 over 2021 to 2025 | 509 First-Year Class |
| Yield (matriculants per offer) | 21.2% in 2025; 18.5% to 21.2% over 2021 to 2025, mean 20.0% | Same |
| Tuition, full-time | $57,700 in 2025-26, up from $55,550 (2024-25) and $53,440 (2023-24), about +3.9% a year. No fees. Same for residents and nonresidents | 509 tuition |
| Class profile (25th / 50th / 75th) | LSAT 159 / 164 / 167; UGPA 3.66 / 3.81 / 3.92 | 509 |
| Grants (2024-25 academic year, all 392 JD students) | 81% receive a grant. Recipient percentiles are $20,000 / $40,000 / $55,550, and the 75th equals full 2024-25 tuition. 108 students (28%) are at or above full tuition | 509 Grants |
| Average grant and net tuition (my estimate) | About $30,700 per student from band midpoints, a discount of about 55%. Net tuition is about $26,000 per enrollee at 2025-26 tuition | Derived; assumption |
| Conditional scholarships | None reported in the 2021 to 2024 reports | 509 tuition and conditional scholarships |
| Persistence | 2025: one non-academic 1L attrition, no academic attrition, 4 transfers out. Annual persistence is about 0.97 in year one and 0.99 after. The three-year revenue multiplier M is about 2.92 | 509 Attrition |
| Break-even slope (derived) | β\* = 100 × p × 1,000 / (net tuition − mean bonus) ≈ **0.9 to 1.0 percentage points per $1,000** for a $2,000 to $4,000 bonus | Derived |
| Enrollment count noise (derived) | Binomial SD ≈ 10.4 enrollees, which is **7.6% of the class** and about $0.33M of first-year scholarship spend | Derived |

Peers in the 509 file run higher on yield than Richmond: Washington and Lee 24%, Wake Forest 28%, Villanova 31%, Maryland 31%, George Mason 36%, William & Mary 38%. Two of them are public, with in-state tuition of $38,734 (William & Mary) and $24,864 (George Mason). Because of that, Virginia residency changes Richmond's applicants' outside options even though Richmond itself charges one price.

---

## Phase 1: Cold review

### 1.1 Strongest objections, ranked

| # | Objection | Severity | Confidence | Evidence |
|---|---|---|---|---|
| 1 | **The choice rule is one-sided, so weak evidence tilts the grid toward cuts.** §5 requires the gain to stay at or above zero at the low scenario only. A cut always gains when students are less price-sensitive, so any cut the middle scenario favors passes, and none is checked against the high scenario. O2's fix (floor the low slope at zero) makes this worse, because every cut "gains" at zero. The plausible range of 1 to 3 points per $1,000 straddles break-even (about 1.0 at Richmond, about 1.1 in Lakeshore), so whenever the point estimate falls below break-even the rule recommends cutting, and it never asks the evidence to rule out the opposite. That is the legacy failure ("aid doesn't matter, so cut it") the product exists to prevent | Critical | High | Shown (rule text); harm Suspected until the grid optimizer exists |
| 2 | **S5 cannot represent a law school's status quo.** (a) The per-student cap of 75% of tuition fails for the 28% of Richmond students at or above full tuition. (b) The $0 to $12,000 ladder sits against awards up to $57,700. (c) The default horizon is year one, but Richmond's awards renew automatically for three years, so a year-one budget understates the commitment by about 2.9 times. (d) 75 cells over about 650 admits leaves about 9 admits per cell per cohort, and 125 cells leaves about 5. (e) Need band may not be an operative policy attribute in law. O8 names the problem; the spec does not solve it | Critical (pilot) | High | Shown (509 and §5) |
| 3 | **The screen rule measures detectability, not decision value.** It asks whether a fixed 1.5-point effect could be detected. It should ask whether learning the slope would change the grid by more than the test costs. The threshold also shifts with price level ($1,000 is 2.7% of Lakeshore tuition and 1.7% of Richmond's), and it ignores break-even, class caps and renewal costs. At Richmond scale the current rule says Recommend: the smallest detectable effect after three cycles is about 1.9 to 2.1. Yet even perfect knowledge of the slope is worth only $0.10M to $0.68M over three cohorts within a ±3% class band, less than one cycle of the cheapest test ($0.32M plus operating cost) | High | High | Shown (computation, §10) |
| 4 | **Test cost is understated about threefold for multi-year programs.** The $420 per test student counts year one only. A renewable bonus costs about M times that (M is 2.92 at Richmond), which comes to $1,226 per test student at a $4,000 top arm and $2,453 at $8,000. Where seats are capped, the extra enrollees a bonus buys displace other admits, so the revenue offset behind "roughly break-even at 1.5 points" disappears | High | High | Shown |
| 5 | **The anchor's estimand is undefined, and pooling AMEs mixes populations.** In the code, the experiment's AME is measured at each student's received dose. The discontinuity is local to its threshold. The "truth" of 1.49 is measured at awards that include the bonus; at status-quo awards the true effect is **1.31**. Test-only estimators averaged 1.38 to 1.45 against 1.31 (+6% to +11%). The 10% bias gate depends entirely on which estimand is used | High | High | Shown (simulation) |
| 6 | **The forecast baseline (O1) is undefined for a policy grid.** The response is centered on each student's "current award," but at grid-design time no live admit has one. The generator hands live-cohort students their staff awards in advance, which hides the problem | High | Medium | Shown (generator code) |
| 7 | **Free precision is left unused.** Eligible admits randomized out of the test (60%) are a valid $0 arm. Analysing every randomized eligible cuts the SE from 0.44 to 0.29 at the same bonus cost, which is worth more than the arm redesign, and removes the +6% estimand bias in this world | High | High | Shown (simulation) |
| 8 | **The budget and class checks use expectations only.** At Richmond, binomial noise alone moves the class by ±10 students and spend by ±7.6%. An expected-spend constraint holds the budget about half the time, and the chance of a 5% overrun is about 25%. Varying the slope scenario does not touch this | High | High | Shown (calculation) |
| 9 | **The Monte Carlo gate is miscalibrated.** With 50 seeds, the 90% to 98% coverage band fails a correct method 11.5% of the time, not about 5%. The gate compares against the retired v2 optimizer, uses an ambiguous "truth," and there is no law world | High | High | Shown (binomial; code) |
| 10 | **509 rank-matching misreads the fields.** Grant fields cover the prior academic year, among recipients only, across all three classes. LSAT and UGPA percentiles describe matriculants, not admits. The scraped table stores 0 as nonresident tuition at private schools | Medium | — | Shown (Richmond rows) |

**Sound:**
- The decision-date leakage rule.
- `rdrobust` with a net-cost denominator and density and placebo checks.
- Excluding protected attributes and credit data.
- Descriptive layers that never feed price.
- Keeping the closed timing-data decision closed.

### 1.2 Rulings on departures from the first review

| Departure | Ruling | Reason |
|---|---|---|
| Three scenarios instead of posterior draws | **Confirm, with changes** | With one parameter, three quantiles carry what draws would. Two changes: take quantiles of the **logit-slope** posterior, and evaluate the choice rule at both ends (§3 of Phase 3) |
| No realization correction | **Confirm per engagement; change the disclosure** | A one-seed ratio that ranged from 0.14 to 0.62 is not a correction. But the shortfall comes from forecast and allocation error that slope scenarios cannot represent (Phase 2). Publish the Monte Carlo distribution of realized ÷ predicted (median and 10th percentile) in the methodology and show the low scenario beside every headline |
| CVaR deferred | **Confirm** | Two caveats. Add a closed-form count-noise buffer, which covers sampling variance rather than model uncertainty; it is not CVaR, and it matters at 146 seats. CVaR returns only with segment slopes, as planned |
| Inverse-variance pooling, flag at 1.5 SE | **Change** | Pool **logit slopes**, each converted on its own sample at status-quo awards; flag when \|z\| > 1.5 in those units. On a flag, the scenarios span both estimates; after two consecutive flags, use the experiment only. *Judgment call:* I would switch to experiment-only by default if the prestige-bump world shows pooling failing coverage while experiment-only passes |
| Policy grid instead of per-student awards | **Confirm** | Add three things: a cell-count rule (cells ≤ admits per cohort ÷ 30), an award mode (supplement or total), and a grid-constrained fence-sitter as the fair comparator |

### 1.3 Open issues O1 to O19

| ID | Real? | Severity | Ruling on the proposed resolution | Tier |
|---|---|---|---|---|
| O1 Forecast baseline | Yes | High | **Change.** Center on the *cell-level expected status-quo award*, with the forecast excluding the award (Phase 3 §3). Option (a), adding net cost to the forecast, pulls the confounded aid coefficient into the baseline and needs per-student status-quo awards that do not exist at design time | M0 |
| O2 Weak evidence | Yes | Critical with the one-sided rule | **Change.** Use a two-sided rule with low = max(0, q10). "Evidence too weak" then follows automatically; label it whenever q10 ≤ 0. Report the posterior SD and the screen's value of information, not only the MDE | M0 |
| O3 Uncorrected gains | Yes | High | **Change.** Do not add forecast and retention dimensions to the headline. Fix the causes: recalibrate intercept and slope out of time, and pool cell yields partially. In the Monte Carlo, realized gain must reach the low-scenario prediction in ≥ 80% of seeds, and the realized ÷ predicted distribution is published | M0 spec, M1 test |
| O4 Grid scope | Yes | High | **Confirm, with additions** (Phase 3 §4): award mode, reserve for appeals, pool projection, frozen cut points | M0 |
| O5 Anchor population | Yes | High | **Change.** Convert each source on its own sample, pool in logit units, and define the estimand at status-quo awards on the eligible population. On a flag, widen the scenarios (as proposed) | M0 |
| O6 Monte Carlo design | Yes | High | **Confirm the direction, change the numbers.** 200 seeds in the two baseline worlds and 100 elsewhere; beat the best fair heuristic (Phase 3 §2); add the listed worlds plus a law world and confound-strength worlds | M1 |
| O7 Bonus timing | Yes | Medium | **Confirm.** Also evaluate revisions at the low scenario for revenue and the high scenario for spend | M1 |
| O8 Verticals | Yes | Critical for Richmond | **Confirm, and specify the law profile** (Phase 3 §4 and §5) | M0 |
| O9 Interference | Yes | High in law | **Confirm, plus more.** Law applicants compare scholarships openly and negotiate, so a control admit who learns of a peer's bonus asks for reconsideration. Add the negotiation-interference world, report reconsideration rates by arm, and disclose the design at the alignment gate | M1 |
| O10 Pooling method | Yes | Low | **Change** to logit-unit pooling (1.2) | M0 |
| O11 Departures | — | — | Ruled in 1.2 | — |
| O12 Thin-history markets | Yes | Medium | **Confirm, plus more.** Shrink market intercepts toward their tier, and let flagged markets inherit the parent tier's award | M1 |
| O13 Consumer segments | Yes | Medium | **Confirm.** Release criteria in Phase 3 §9 | M2 |
| O14 Market tier and targets | Yes | Medium | **Change.** Cap cells at min(125, admits ÷ 30). **Reject** exempting target markets from floors: floors guard against estimation error, which is worst in thin target markets | M0 |
| O15 Scoring governance | Yes | Medium | **Confirm.** Additions in Phase 3 §9 | M1 |
| O16 509 definitions | Yes | Medium | **Confirm.** The field problems are already shown (1.8); procedure and validation in Phase 3 §11 | M1 |
| O17 Horizon and conditional awards | Partly | High (horizon); Low for Richmond (conditional) | **Change.** The binding point is that the budget horizon must equal the award's commitment length. Richmond reports no conditional scholarships, so conditional modeling stays in configuration until a client offers them | M0 horizon, M2 conditional |
| O18 Timing by wave | Yes | Medium | **Change.** Per-wave slopes are descriptive only at any realistic size. Richmond's per-wave MDE is about 5 points per $1,000, and the MDE for a difference between waves is about 7 | M2 for decisions |
| O19 Boosted challenger | Yes | Low for MVP | **Set the margin** in Phase 3 §13. At Richmond size the challenger cannot pass | M2 |

### 1.4 Internal consistency of S4 and S5

- **The response formula and the forecast disagree (O1).** The formula centers on `p_forecast(current award)`, but the forecast has no award term.
- **The anchor conversion test is near-tautological.** "Average effect equals the anchor within 1%" checks a first-order identity that holds by construction (the second-order term is under 1% at these slopes). It cannot catch the real error: p values taken from an uncalibrated forecast. That forecast overpredicts status-quo enrollment by 6.6% on the holdout, which moves β by about 5%.
- **The three scenarios can break the choice rule** (q10 below zero, O2), and the rule checks only one side.
- **The support rule leaves Tier 1 law with nothing.** Increases are capped at the largest tested bonus or the largest observed discontinuity jump. A law school with no published grid and no test therefore has no anchor and no allowed increases. The spec should say plainly that Tier 1 law means no FAO optimization; it is not "discontinuity-only."
- **The v2 build mixes horizons.** It optimizes four-year revenue against a **one-year** spend budget (`optimize.py`: spend = P × d), while §5 says the horizons must match. The headline +2.7% (four-year) comes from that mismatch.
- **Floors and the guardrail operate at different scales.** In undergraduate programs (average discretionary award about $3,000), the 75% floor binds before the $3,000 guardrail. In law (average award about $31,000), the guardrail binds first. "Floors will rarely bind with one slope" is untested.
- **The targeting whitelist omits academic position,** which a law median target needs.
- **The academic index replaces GPA in the forecast,** but the discontinuity still needs the raw running variable and the fixed merit thresholds. Keep both.
- **Tuition scenarios apply β to changes in net cost.** They are within the evidence only if the change is no larger than the tested dose.
- **Sound:** shipping the class-floor scenario only when it binds; the four shipped budget scenarios.

### 1.5 Sample-size guide and cost

- **The 0.85 covariate factor is compensating for the wrong yield.** It reproduces the prototype's SE (0.557) only because the formula uses p = 0.21, while the test population's yield was **0.17**. Eligibles exclude athletes, whose high yield lifts the overall 20.5%. At 0.17 the implied factor is 0.92. The oracle bound is 0.86, since the true probabilities explain 26% of outcome variance among eligibles, and a real forecast with AUC 0.83 does worse than the oracle. **Use 0.92**, or √(1 − R²) from the client's out-of-time forecast.
- **The 21% yield is right for Richmond but wrong for the prototype's test population.** Always use the eligible population's yield.
- **The 1.5-point plausible effect (range 1 to 3) has no stated source and does not transfer across price levels.** Set the prior per vertical, or per 1% of tuition, and always show it beside the break-even slope. Both verticals straddle break-even, which is exactly why power to detect "not zero" is the wrong target.
- **The dose is too small for law.** $0 / $2,000 / $4,000 is 0% to 7% of Richmond's tuition, smaller than the moves a law grid makes, and the support rule then caps grid increases at $4,000. Scale the top arm to the policy moves under consideration (law default: 10% to 15% of tuition).
- **The SE gain claimed for the arm redesign holds,** and analysing every randomized eligible is a second, larger gain (§1.1 #7).
- **The cost figure needs two corrections:** multiply by M, and for capped programs drop the induced-enrollment offset.

Richmond (650 eligible admits, 40% in the test, p = 0.21, factor 0.92). Each cell shows SE / MDE in points per $1,000:

| Top arm | Analysis | 1 cycle | 2 cycles | 3 cycles |
|---|---|---|---|---|
| $4,000 | Test arm only | 1.30 / 3.64 | 0.92 / 2.57 | 0.75 / 2.10 |
| $4,000 | All randomized eligibles | 0.98 / 2.75 | 0.69 / 1.94 | 0.57 / 1.59 |
| $8,000 | Test arm only | 0.65 / 1.82 | 0.46 / 1.29 | 0.38 / 1.05 |
| $8,000 | All randomized eligibles | 0.49 / 1.38 | 0.35 / 0.97 | 0.28 / 0.79 |

At zero effect, one cycle costs $0.32M with a $4,000 top arm and $0.64M with $8,000 (260 test students, three-year renewal).

### 1.6 Price-test screen rule

The threshold (MDE ≤ 2.3) is not defensible as a decision rule. 80% power and the 1-to-3 range work as reporting conventions, but they should not decide anything. The basis should be **value of information**: the expected gain in revenue (or in the cost of meeting a target) from choosing the grid with the test's result, set against the test's cost and the cycles lost while it runs, all computed on the client's actual decision space (class band, support rule, floors, targets). At Richmond's scale the replacement returns **Not recommended** for a revenue objective, at every size from 600 to 4,000 admits under a ±3% class band. It can turn positive only if Richmond names a target, such as a median-LSAT position, whose cost depends on the slope. Full specification and worked examples are in Phase 3 §10.

### 1.7 Targeted objectives, market tier and geography

- **Infeasibility.** Aid works only at the admit stage. Within Richmond's ±3% seat band, most enrollment targets cannot be reached through aid alone. The spec needs a soft-constraint feasibility pass that reports the shortfall and the budget that would close it (Phase 3 §8).
- **Thin-history markets (O12).** The flag at under 30 historical admits is right. Forecasts for those markets should borrow strength from the market's tier and distance band, and the markets should inherit the parent tier's award with no cells of their own.
- **Proxy risk.** A metro area is a strong proxy for race and income. Add a runtime composition screen to the static whitelist test (Phase 3 §8).
- **Cell cap (O14).** 125 cells is too many for most clients; tie the count to admits. Floors must cover target markets.
- **Law.** For a private law school, residency is a market, not a price attribute. It still matters through competitors' in-state pricing (William & Mary and George Mason).

### 1.8 509 layer, horizon and persistence, timing

- **The field definitions break rank-matching as specified.**
  - **Year.** Richmond's 75th-percentile grant equals the *prior* year's tuition in two consecutive reports ($53,440 in 2024 and $55,550 in 2025), so the grant fields describe the prior academic year.
  - **Population.** Grant percentiles are among recipients only (81% at Richmond) and pool all three classes.
  - **Scores.** LSAT and UGPA percentiles describe matriculants, not admits.
  - **Tuition field.** Nonresident tuition is stored as 0 for private schools.

  Rank-matching must convert recipient percentiles to all-student quantiles, normalize grants by the grant year's tuition, and treat matriculant percentiles as the reference. The procedure is in Phase 3 §11.
- **Yield prior.** For the client itself, the 509 yields are its own history: a calibration check on the forecast intercept, not a prior. Peer yields are never a prior for the client.
- **Horizon.** Following program length is right. The binding change is that the **budget horizon must equal the award's commitment length**. For renewable law awards the default is three years, not year one.
- **Conditional awards (O17).** Richmond reports none, so persistence is retention alone (about 0.97 in year one and 0.99 after). Build the conditional pathway as configuration only (M2).
- **Timing (O18).** At Richmond, the per-wave MDE for one cycle is about 5.1 points per $1,000 with a $4,000 top arm, and the MDE for a difference between waves is about 7.3. Stratify the randomization by wave, which costs nothing, but report pooled results; a wave-specific slope cannot change a recommendation within the MVP.

---

## Phase 2: Test against results

The outputs in `efa_fao/outputs/` come from the v2 build: a per-student optimizer, bootstrap bands, the old arms, and the v2 equity audit. None of the v2.4 features (grid, three scenarios, conversion rule, 40/20/40) has been built. So I tested the claims by re-running the v2 code paths and simulating the new design.

### 2.1 Phase 1 concerns, revised

| Phase 1 # | Status | What the outputs add |
|---|---|---|
| 1 One-sided choice rule | **Confirmed** (logic) | Not visible in the outputs, because the scenarios were never built |
| 2 Law not representable | **Confirmed** | The 509 data alone show it |
| 3 Screen rule | **Confirmed** | The value-of-information calculation shows it (Phase 3 §10) |
| 4 Test cost | **Confirmed** | — |
| 5 Estimand | **Confirmed and quantified** | The true AME at status-quo awards is 1.31; at bonus-inclusive awards it is 1.49 |
| 6 O1 baseline | **Confirmed** | `generate.py` gives the live cohort its staff awards in advance |
| 7 All-eligible analysis | **Confirmed** | SE 0.287 against 0.438 (300 replications) |
| 8 Count noise | **Confirmed** | The backtest scores expectations only, so it cannot show this |
| 9 Monte Carlo gate | **Confirmed, plus new** | The backtest matches spend using the *true* response (`validate.match_true_spend`) |
| 10 509 fields | **Confirmed** | — |
| — | **New N1** | The three-scenario range covered the realized gain by coincidence (2.2 below) |
| — | **New N2** | Forecast bias against the true expectation is +6.6%. The documents report 4%, measured against one realized draw |
| — | **New N3** | The backtest headline mixes a four-year revenue objective with a one-year budget |
| — | **New N4** | The price test in the backtest spans three cohorts (2023 to 2025; 1,917 students), not four as §4 states |
| — | **New N5** | The equity audit is still v2 (international students' average discretionary award down 62%, only 1% with an increase); it has not been re-run, as the executive read concedes |
| — | **Dissolved** | My doubt about the 40/20/40 SE claim: simulation confirms it (2.2) |

### 2.2 Claims tested

**(a) "One slope beats the segment pattern."** The backtest shows that realized gain rises monotonically as kappa falls: +$0.39M at 0.9, +$0.42M at 0.72, +$0.46M at 0.5, +$0.60M at 0. Segment recovery shows the pattern wrong in size and order (international 0.18 against a truth of 1.34; lower-need 0.04 against 1.22). This **supports** a narrow claim: *in this world, an observational segment pattern does worse than none.* It **cannot** support the claims that heterogeneity is unimportant (true slopes run 0.85 to 2.53 across need bands, and the uniform slope captures only 44% of the oracle gain), that the result generalizes beyond one seed and one cohort, or that a grid would match the per-student result. Evaluation uses true expectations, so outcome noise is absent, but estimation noise across seeds is untested.

**(b) "40/20/40 cuts the SE from 0.56 to about 0.44."** **Supported.** Simulated SDs on the synthetic eligible pool (n = 4,843, 40% in the test, logit with covariates, 300 replications): uniform five-arm 0.548, 40/20/40 0.438, two-arm 0.391. What it **cannot** support: that the middle arm gives a useful check on linearity, since the power to detect the saturation world is untested. And the claim misses the larger gain: analysing every randomized eligible gives **0.287** at the same cost. Test-only estimators are also biased upward against the status-quo estimand (1.38 for 40/20/40, 1.45 for two-arm, against 1.31). The all-eligible analysis is unbiased (1.31).

**(c) "The three-scenario range would have covered the realized gain."** For the uniform-slope allocation, I evaluated the same allocation at the 10th, 50th and 90th percentile slopes (0.55, 1.14 and 1.73 points per $1,000):

| | Low | Middle | High | At the true slope (1.49) | Realized (truth) |
|---|---|---|---|---|---|
| Predicted gain | $0.50M | $0.98M | $1.65M | $1.35M | **$0.61M** |
| Predicted change in enrollees | +2.2 | +7.5 | +16.1 | +12.2 | **−1.5** |

The range covered the realized gain, near its low end, but **for the wrong reason**. The anchor was too low, and a lower slope happens to mimic errors that come from elsewhere:
- The forecast overpredicts status-quo enrollment by 6.6% (413.9 against 388.1 expected).
- The allocation exploits forecast error: it predicted +7.5 enrollees and got −1.5.

Had the anchor been right, the range would have sat around $0.8M to $2.0M and missed. With a budget set on *model-predicted* spend (as in production) rather than matched to true spend, realized gain was $0.52M against a predicted $0.91M (ratio 0.58), and true spend came in 4% under status quo. The claim is **not established** as a property of the method. The fix is O3 (recalibration plus cell shrinkage) and a Monte Carlo coverage test.

**(d) "The anchor conversion rule (plus the 1% test) closes the 1.40 versus 1.14 gap."** The rule is **not built**. The 1.40 came from mixing the observational base with anchored slopes, and any rule that defines β from the anchor removes that particular gap by construction. What the outputs show is that the remaining risks are elsewhere: which p values are used (+6.6% level bias), and which estimand applies (1.31 against 1.49, a 12% gap). The 1% test detects neither (1.4).

### 2.3 Findings

| ID | Severity | Conf. | Status | Finding | Why it matters | Evidence | Proposed fix | How to test it | Tier |
|---|---|---|---|---|---|---|---|---|---|
| F1 | Critical | High | Confirmed | Choice rule checks only the low scenario | Approves cuts whenever the point estimate is below break-even, regardless of uncertainty | Shown: §5 text. Suspected: frequency | Two-sided rule; low = max(0, q10) (Phase 3 §3) | Unit test: a cut whose gain is negative at the high scenario is rejected. Monte Carlo W6/W8: no level change when q10 ≤ 0 or the interval straddles β\* | M0 |
| F2 | Critical | High | Confirmed | Law status quo not representable: 75% cap, $12k ladder, year-one horizon, 75 to 125 cells | Richmond cannot even be baselined; cuts would be forced | Shown: 509 (28% ≥ full tuition; awards renew; 650 admits) | Award mode "total"; cap = max(configured cap, current award); ladder to tuition; horizon = commitment; cells ≤ admits ÷ 30; law profile | Load a Richmond-calibrated status quo; the optimizer returns it unchanged when β = 0 and the budget equals status-quo spend | M0 |
| F3 | High | High | Confirmed | Screen rule is power-based and not invariant to price level | Recommends tests that cannot pay back; Richmond would be told Recommend | Shown: EVPI $0.10M to $0.68M against a minimum test cost of $0.32M | Value-of-information screen (Phase 3 §10) | Worked examples reproduce; property test: the verdict is unchanged when all dollar inputs are scaled by a constant | M0 |
| F4 | High | High | Confirmed | Test cost is year-one only and assumes induced enrollment adds revenue | Understates cost about 2.9× for law and ignores capacity | Shown: calculation | Cost = M × E[enrolled test students' bonus]; no offset when capped | Hand calculation in the screen output | M0 |
| F5 | High | High | Confirmed | Estimand undefined; AMEs pooled across populations | The bias gate and the conversion are ambiguous by 12% | Shown: 1.31 against 1.49; test-only +6% to +11% | Estimand = AME at status-quo awards for eligibles; pool logit slopes | Monte Carlo anchor bias against the defined estimand | M0 |
| F6 | High | Med | Confirmed | Baseline for a grid undefined (O1) | Response centered on awards that do not exist at design time | Shown: generator code | Center on the cell-level expected status-quo award | Holdout: predicted status-quo class within its forecast interval | M0 |
| F7 | High | High | New | Randomized-out eligibles unused | Gives up a 34% SE reduction at zero cost; biased estimand | Shown: simulation 0.287 against 0.438 | Analyse every randomized eligible (intent to treat) | Monte Carlo W0: SE ratio ≤ 0.8 against test-only | M0 |
| F8 | High | High | New | Scenario coverage of realized gain was coincidental | The headline range will miss when the anchor is right | Shown: re-run (true-slope prediction 2.2× realized) | Recalibrate (intercept and slope); shrink cell yields; disclose the Monte Carlo ratio | Monte Carlo: realized ≥ low-scenario prediction in ≥ 80% of seeds; median ratio in [0.7, 1.15] | M1 |
| F9 | High | High | New | Backtest matches spend with true probabilities | Budget compliance and model-budget gains are untested | Shown: `match_true_spend`; model-budget ratio 0.58 | Report both versions; gate on the model-budget version | Monte Carlo metric as specified | M1 |
| F10 | High | High | Confirmed | Budget and class checks ignore count noise | P(> 5% overrun) ≈ 25% at Richmond | Shown: binomial SD 7.6% | Buffer = 1.645 × spend SD at the high scenario | Monte Carlo with outcome draws: overrun ≤ 5% of seeds | M0 |
| F11 | High | High | Confirmed | Monte Carlo gate: false-fail 11.5% at 50 seeds; compares against the retired optimizer; no law world | Gate is unreliable and partly irrelevant | Shown: binomial; §10 | Phase 3 §1 and §2 | False-fail ≤ 3% family-wise by calculation | M1 |
| F12 | Medium | — | Confirmed | Sample-size assumptions: 0.85 factor, 21% yield, scale-dependent effect, small dose | MDEs about 8% optimistic; law dose too small for the decision space | Shown | Factor 0.92 or √(1 − R²); eligible yield; prior per vertical; scaled dose | Monte Carlo SE against formula within 10% | M0 |
| F13 | Medium | — | Confirmed | 509 field misreads (prior year, recipients only, all classes, matriculants, nonresident = 0) | Market gap biased; tuition could read as $0 | Shown: Richmond rows | Phase 3 §11 procedure | Synthetic law world, ρ = 0.9 and 0.7 | M1 |
| F14 | Medium | — | New | v2 headline mixes a four-year revenue objective with a one-year budget | Overstates the spend the budget allows | Shown: `optimize.py` | Horizon match enforced in config validation | Config test rejects mismatched horizons | M0 |
| F15 | Medium | — | Confirmed | The conversion rule's 1% test is near-tautological | Gives false comfort | Shown: math | Replace with a status-quo-point check against the experiment's own AME | Unit test with a miscalibrated forecast fails | M0 |
| F16 | Medium | — | Confirmed | Wave slopes not estimable at realistic sizes | Promised analysis cannot deliver | Shown: MDE 5 to 7 at Richmond | Descriptive only; pooled contrast after ≥ 2 cycles | — | M2 |
| F17 | Medium | — | New | Equity audit not re-run; the v2 international cut still in outputs | Risk that stale numbers reach a client | Shown: `equity_audit.csv` | Block publishing of v2 equity tables | Release checklist | M1 |
| F18 | High | Med | Confirmed | Negotiation interference in law (O9) | Attenuates the slope; control admits request matches | Suspected | Interference world W14; report reconsideration rates by arm; alignment-gate disclosure | W14 pass criterion | M1 |
| F19 | Low | — | New | "Four cohorts" in §4 should read "three" | Documentation | Shown | Edit | — | M0 |
| F20 | Low | — | Confirmed | Guardrail in dollars; scales differently from floors | Floors and guardrail bind in different order by vertical | Shown | Guardrail as a percentage of tuition (default 5%) | Monte Carlo reports binding frequency | M0 |

### 2.4 Claims in the documents these outputs do not establish

| Claim | What would establish it |
|---|---|
| +$0.60M (+2.7%) for one slope, as a property of the method | Monte Carlo W0, 200 seeds, at model-set budgets |
| The policy grid performs like the per-student optimizer, and overfits less | Grid built; Monte Carlo against per-student and fair baselines |
| 40/20/40 gives SE 0.44 (supported by my simulation, not by the outputs) and an MDE of about 1.2 | Monte Carlo W0 with the new arms; analyse all eligibles |
| The sample-size table and the 2.3 screen threshold | Replaced by the value-of-information screen; validate the SE formula against Monte Carlo SEs |
| The cost of about $420 per test student and "roughly break-even at 1.5 points" | Cost formula with M and capacity |
| Anchor conversion within 1% closes the hybrid gap | Built rule; the status-quo-point check in F15 |
| Budget holds at all three scenarios | Monte Carlo with outcome draws and model-set budgets |
| The three-scenario range covers the realized gain | Monte Carlo coverage test (F8) |
| The forecast overpredicts by about 4% | Holdout against the true expectation (6.6%); recalibration test |
| International cut retracted; need shift partly an artifact | Equity audit re-run under the lean model |
| Floors "rarely bind" with one slope | Binding frequency in the Monte Carlo |
| Class floor does not bind (shown only in v2: 473 projected against a 427 floor at 1.5× budget) | Re-check under the grid |
| Rank-matched market award gap is meaningful | Synthetic law world (Phase 3 §11) |
| Conditional-award persistence, program-length horizon results | Law world; not needed for Richmond |
| Wave-specific sensitivity | Not achievable at pilot scale |
| Boosted challenger value | W20 worlds; two pilot backtests |
| Seven guardrail tests pass | Run in CI; I did not run them (no scipy in my sandbox) |
| Forecast accuracy "identical either way" | True but uninformative: the hybrid reuses the observational predictions at the status quo by construction |

---

## Phase 3: Design work

The design target is an MVP. Each item is marked with what ships first and what is deferred.

**Notation used throughout**

| Symbol | Meaning |
|---|---|
| b | Logit slope per $1,000 |
| θ | AME in percentage points per $1,000 at status-quo awards |
| b = θ / (100 · mean p(1 − p)) | Conversion between the two |
| c | Grid cells |
| n_c | Projected admits in cell c |
| a_c | Grid award in cell c |
| r_c | Reference (status-quo) award in cell c |
| L, M, H | Slope scenarios |

### 1. Monte Carlo study

**Protocol (per seed).**
1. Generate five historical cohorts, one holdout cohort and one live cohort.
2. Run the full pipeline (evidence audit, anchor, forecast, grid, scenarios) with no access to truth.
3. Score on the holdout two ways:
   - with **true expectations** (allocation value);
   - with **one Bernoulli outcome draw** (spend and class noise).
4. Set budgets on **model-predicted** spend, as production does. The truth-matched comparison is kept only for strategy ranking.

**Estimand.**
- θ = the mean over eligible holdout admits of [p_true(d_SQ + $1,000) − p_true(d_SQ)].
- Coverage is judged on b.

**Runtime.** Drop the bootstrap, target ≤ 30 seconds per seed, and run seeds in parallel. About 20 worlds × 100 to 200 seeds is roughly 30 CPU-hours per release.

| World | Mechanism and parameters | What it should break | Seeds | Pass |
|---|---|---|---|---|
| W0 UG baseline | Current generator; aid versus unobserved-interest correlation ≈ −0.4 | — | 200 | All baseline thresholds below |
| W0L Law baseline | Calibrated to Richmond 509: 650 admits, yield 21%, tuition $57,700, grant distribution matching the 509 percentiles (28% at or above full tuition), no merit grid, position bands, three-year renewable awards, persistence 0.97/0.99, true θ = 1.0. Run with and without a test | Representability, horizon, cap, count noise | 200 | Law thresholds below |
| W1 | Staff targeting differs by need band (fit coefficient −0.3 to −1.5) | Segment patterns from history | 100 | Baseline anchor thresholds |
| W2 | Unobserved slope heterogeneity, SD 0.6 on b | Value of one slope | 100 | Gain > 0 in ≥ 80% of seeds; document the shortfall against the oracle |
| W3 | Slope halves beyond +$6,000 | Linearity | 100 | Middle-arm linearity check flags in ≥ 50% (power-limited, document it); support rule holds the loss to < 0.5% |
| W4 | Cuts hurt 2× (loss aversion) | First-offer cuts | 100 | Gain ≥ 0 in ≥ 85% |
| W5 | +0.3 logit prestige bump at merit thresholds | Discontinuity inflation | 100 | Disagreement flag fires in ≥ 70%; coverage ≥ 85% after the flag action |
| W6 | 600 admits, 15% test share | Power | 100 | When q10 ≤ 0, no level change in 100% of seeds; realized loss < 0.5% in ≥ 95% |
| W7 | Slope drifts 25% between cohorts | Pooling across cohorts | 100 | Coverage ≥ 85%; drift diagnostic reported |
| W8 Tier 1 | No test; one usable threshold | Local anchor | 100 | Coverage ≥ 85% with "local" widening; two-sided rule blocks level changes when the interval straddles β\* |
| W9 | No grid, no test | — | 100 | Status "no anchor" and no optimized grid in 100% |
| W10 | Data quality: 10% missing offer dates, 5% of awards dated after the decision, 3% duplicate packages | Cleaning | 100 | QA catches ≥ 95% of planted rows; anchor bias ≤ W0 limit + 5 points |
| W11 | Planted post-decision field correlated with enrollment | Leakage | 100 | Blocked in 100% |
| W12 | Staff offsetting: 30% of controls get +$1,000, or treated students lose 50% of the bonus in other aid | Experiment | 100 | Compliance check flags in ≥ 80% when the offset is ≥ 25% of the bonus |
| W13 | Merit thresholds move 0.1 GPA in cohort 3 | Discontinuity regime | 100 | Estimated per regime; bias within the W0 limit |
| W14 | Negotiation interference: 20% of control admits in a treated stratum obtain the median bonus by reconsideration | Experiment attenuation | 100 | Reconsideration-rate diagnostic flags in ≥ 70%; intent-to-treat bias reported |
| W15 | Retention depends on net cost (−0.02 logit per $1,000); non-constant hazard | Multi-year revenue | 100 | Year-one results unaffected; multi-year error documented and labeled |
| W16 to W18 | Confound strength −0.2 / −0.6 / +0.2 (W0 is −0.4) | Confound robustness | 100 each | Anchor thresholds hold; the naive-minus-anchor gap is monotone in strength and reported |
| W19 | Law with conditional awards (25% lose by 2L) | Persistence | 100 | M2: only when a client needs it |
| W20a/b | Additive / interaction worlds | Boosted challenger | 100 each | §13 |

**Baseline thresholds (W0 and W0L).** False-fail rates are binomial at 200 seeds.

| Check | Threshold | False-fail if the method is correct | Notes |
|---|---|---|---|
| Anchor bias | \|mean bias\| ≤ 10% of b | — | Against the estimand defined above |
| 95% interval coverage | 90% to 98% of seeds | **1.0%** if true coverage is 95% | A method at 85% coverage passes only 2.5% of the time |
| Scenario calibration | Realized ≥ low-scenario prediction in ≥ 80% of seeds; median realized ÷ middle prediction in [0.70, 1.15] | — | — |
| Realized gain | > 0 in ≥ 90% of seeds that reallocate | 0.1% if the true rate is 95% | — |
| Fair baselines | Beat the best fair baseline (§2) | — | — |
| Spend overrun | Realized spend (outcome draw) > 105% of budget in ≤ 5% of seeds | 0.3% if the true rate is 2% | — |
| Class projection | UG: within 2% in ≥ 90% of seeds (expectation). W0L: realized class inside the projected 90% interval in ≥ 85% of seeds | — | The W0L test checks the interval, not the point |
| Two-sided rule | No level change whenever q10 ≤ 0 | — | 100% of seeds |

Family-wise false-fail is about 2% to 3%.

**Other worlds.** A world either meets the baseline thresholds, or its designated diagnostic fires in ≥ 70% of its seeds while false-alarming in ≤ 10% of W0 seeds. This replaces "flag 80% of failing worlds," which is too coarse with about 20 worlds.

### 2. Fair baselines and margin

**Spend matching.** Each policy is compared twice:
- at a budget set on its own model-predicted spend (the production condition);
- at true spend matched within 1% (as now, for ranking only).

**Baselines.**
- **Status quo:** historical policy reproduced.
- **Proportional rescale:** a_i = s × d_i^SQ, with s solved to hit spend.
- **Need-first fill:** add $1,000 steps to admits in the highest need band, then the next band, until spend is reached. Cuts remove from the lowest need band first. In law without need data, use position bands from lowest yield upward.
- **Grid-constrained fence-sitter:** cells whose mean forecast p at the status quo lies in [0.30, 0.60] get a uniform increment, solved to hit spend; other cells stay at status quo. The per-student fence-sitter is reported for reference only, because it is individualized pricing, which the product prohibits.
- **Legacy zero-discretionary and oracle:** context only.

**Margin.** Across paired seeds, the grid must beat the best of {status quo, proportional, need-first, grid fence-sitter} on mean realized gain by at least **max(0.25% of status-quo multi-year net tuition revenue, 1.645 × SE of the paired difference)**, and must win in ≥ 60% of seeds. That is about $57,000 in Lakeshore and $28,000 per Richmond cohort. **If the grid fails, ship the winning heuristic as the recommendation.** It is simpler and has the same evidence behind it.

### 3. O1 and O2 as exact rules

**O1: baseline.**
1. **Forecast.** f(x) is a regularized logit on decision-date features. All aid fields are excluded.
2. **Recalibration.** Recalibrate out of time on the latest complete cohort: logit p\* = α + γ · logit f. Report γ. If γ is outside [0.8, 1.2], label the forecast "unstable."
3. **Reference award.** r_c = the mean status-quo flexible award among admits in cell c in that cohort, adjusted for known rule changes (tuition, merit grid) to the live year.
   - Supplement mode: the discretionary component.
   - Total mode: total institutional scholarship.
4. **Response.** p_i(a_c) = expit(logit p\*_i + b · (a_c − r_c)), with formula awards fixed.
5. **Rationale.** p\* estimates yield under the status-quo *policy* for students like x, so r_c is the matching award. Replacing staff targeting within a cell with a flat award changes how award and interest co-vary inside the cell. The first-order model ignores that; W1 and W16 to W18 measure the error.
6. **Acceptance.** On the holdout, Σ_c n_c · mean_i∈c p_i(r_c) falls inside the forecast interval. In W0, status-quo class error is ≤ 2%.

**O2 and the choice rule.**
1. **Posterior.** b ~ N(b̂, s²), from the pooled logit slope.
2. **Scenarios.** b_L = max(0, b̂ − 1.2816 s); b_M = b̂; b_H = b̂ + 1.2816 s.
3. **Feasibility.** A grid a is feasible if the budget (with buffer, §6), class band, floors and targets hold at b_L, b_M **and** b_H.
4. **Choice.** a\* = argmax NTR_M(a) subject to Gain_L(a) ≥ 0 **and** Gain_H(a) ≥ 0, where each gain is measured against the status-quo grid under the same scenario.
5. **Weak evidence.** If b̂ − 1.2816 s ≤ 0, every view carries "Evidence too weak to change aid levels." In that state:
   - any change of more than 1% in expected spend at b_M is blocked;
   - only reallocations non-negative at b = 0 and at b_H pass.
6. **No admissible grid.** If nothing beats status quo, ship the documented status-quo grid, the reasons, and the screen's evidence plan.
7. **Acceptance.** Unit tests on synthetic gain curves:
   - a cut that is positive at L and M but negative at H is rejected;
   - an all-below-break-even cut is accepted;
   - with q10 ≤ 0, no level change is made.

### 4. Policy grid specification (O4)

**Award mode.** Set per program.
- `supplement` (UG default): the grid award is added after formula awards (merit grid, need grant, athletic awards). Formula awards and excluded groups are untouched.
- `total` (law and professional default): the grid award is the total institutional scholarship.

**Cells.**
- Policy attributes only.
- Count ≤ floor(projected admits per cohort ÷ 30). Richmond's limit is 21.
- Profiles:
  - **UG:** academic-index quintile × need band (5) × residency (3). Collapse in this order until the count rule holds: need to 3 bands, then index to tertiles.
  - **Law:** position band (5; see §5) × market (Virginia / other) × optional need (2) = 10 to 20 cells.

**Ladder and cap.**
- Steps of $1,000 (UG) or $2,500 (law), up to tuition.
- Per-student cap = **max(configured cap, current award)**, so the status quo is always representable. The law default cap is 100% of tuition. Awards above tuition stay as an excluded "stipend" component.

**Guardrail.** The per-cell cut on first offers is ≤ 5% of tuition: about $1,900 at Lakeshore and $2,900 at Richmond. Floors follow Appendix C.

**Merit grid and need formula.** Unchanged in the MVP. Need bands are harmonized SAI/EFC bands, and "No FAFSA" is its own band. CSS Profile is accepted where the client uses it.

**Appeals and negotiation.**
- Reserve R = the trailing three-cohort mean of post-first-offer increases, by cell. Deduct it from the budget before optimizing.
- Appeals follow the increases-only rules (§6), are logged, and are excluded from estimation.

**Pool projection.**
- Projected admits by cell = admits to date + (last cohort's final admits by cell − its admits by cell at the same day of the cycle) × (live applications to date ÷ last year's applications at the same date).
- Refresh on three fixed dates: first release, mid-cycle, final wave. The grid is frozen between refreshes.

**Thresholds.**
- Index or position cut points are computed from the trailing three cohorts at cycle start and frozen for at least two cycles.
- Changes take effect only at cycle boundaries and go in a `policy_changes` table (effective date; old and new cut points and awards).
- Award differences between adjacent cells at a cut point are logged as candidate discontinuities for the evidence audit.

**Status-quo grid.** Derived empirically (mean award by cell in the latest cohort) and confirmed by the client as matching practice before any optimization.

### 5. Moderator discovery protocol (graduate and professional)

**Relative position.**
- **Reference distribution:** the program's enrolled first-years over the prior three entering classes, from client data. As a fallback, use the 509 25th/50th/75th percentiles, linearly interpolated, with tails extrapolated at the 50-to-75 spacing and capped at 0 and 100.
- **Per measure:** position = empirical CDF (LSAT; UGPA). GRE and JD-Next are converted through a published concordance where one exists; otherwise flagged, with UGPA used alone.
- **Combined position:** the mean of the available measures. Equal weights by default; configurable.
- **Bands:** < 25, 25 to 50, 50 to 75, 75 to 85, ≥ 85. Keep the ≥ 85 band only if it has ≥ 30 admits per cohort; otherwise merge it.
- **Freezing:** bands are frozen at cycle start.
- **Admits versus matriculants:** admits sit above matriculants, so report the admit distribution by band.

**Candidate generation (history, at least three cohorts).**
- **Fixed list:** position band, engagement index (pre-decision events, visit), market award-gap band (§11), market tier, need (if collected), and application timing.
- **History is used descriptively only:** yield curves by candidate and award quantile, plus confound diagnostics, all labeled associational.
- **Ranking:** by revenue at stake (Σ admits × net tuition in the segment) and plausibility, never by significance.
- **Limit:** at most three candidates carried into a cycle, pre-registered.

**Testing on the randomized arm.**
- Randomization is stratified by the candidate's strata, with ≤ 5 strata per cycle in total.
- **Model:** logit(enroll) = covariates + b · dose + Σ_k b_k · dose × 1[stratum k].
- **Hypothesis test:** H0: b_k = 0, one-sided at α = 0.10 in the pre-registered direction, with Holm correction across candidates.
- **Power:** print the SE of each interaction. At Richmond scale it exceeds the main effect, which makes the limit explicit.

**Gates before any moderator influences allocation.**
1. The interaction passes on pooled data from at least two cycles.
2. The segment-slope policy beats one slope in held-out policy value by more than 1 SE, using inverse-probability evaluation on the latest randomized cycle.
3. Monte Carlo W2-type worlds show a gain over the lean model.

**What may influence allocation, and when.**
- **Always:** position band as a grid dimension, with one slope.
- **Never:** slopes taken from history, or the 509 gap as a slope modifier.
- **After the three gates:** stratum slopes with hierarchical shrinkage (deferred refinement).
- **MVP for Richmond:** descriptive position-band yield curves plus the 509 gap. No moderator will clear the gates at this size.

### 6. Increases-only evaluation

**State at date t.**
- **D:** deposited, with committed awards.
- **R:** released offers, undecided, with committed awards d_i^c.
- **U:** unreleased (actual and projected).

**Budget**, evaluated at b_H, because spend rises with sensitivity:

> Σ_D (1 − melt_i) d_i^c + Σ_R π_i(t) · p_i(d_i^c + Δ_i) · (d_i^c + Δ_i) + Σ_U p_j(a_c) · a_c + R + buffer ≤ B

- π_i(t) is the historical conversion of admits still undecided at the same number of days to the deadline, from the pacing lookup, scaled by the forecast's relative risk.
- Δ_i ≥ 0 and Δ_i ≤ the tested dose. Increases apply cell-wide or to logged appeals.

**Revenue.** Evaluate increases on released offers at b_L, because the response to revisions is unestimated (O7).

**Class.** Projected class = deposits × (1 − melt) + undecided conversion + unreleased. Check the upper capacity at b_H and the floor at b_L.

**Rules.**
- A new grid applies to unreleased offers only.
- Released offers keep their committed awards even if their cell's new award is lower, and the remaining budget is computed on those committed awards.

**Buffer.** Buffer = 1.645 × √(Σ p(1 − p) · award²) over all committed and planned awards, for ≤ 5% overrun probability. At Richmond that is about 1.645 × 7.6% ≈ 12% of first-year scholarship spend.

**Acceptance.**
- A synthetic mid-cycle snapshot matches a hand calculation to the dollar.
- Monte Carlo W0 and W0L overrun ≤ 5% of seeds.

### 7. Evidence audit

**Checks (output is one page).**
1. **Published thresholds.** Dates in force; net-cost jump; admits within the `rdrobust` bandwidth on each side; density test; four placebo cut points; SE converted to logit units.
2. **Policy changes.** Award schedule, tuition, new scholarships. For each: affected and comparison groups, pre-period cohorts, pre-trend, change in net cost, n per cohort, difference-in-differences estimate and SE.
3. **Natural experiments.** Same criteria as item 1.
4. **Data sufficiency.** Share of awards with offer dates; package versions; decision dates.

**Minimum evidence to call a source usable.**
- **Threshold:**
  - unchanged for ≥ 2 cohorts;
  - net-cost jump ≥ 3% of tuition;
  - ≥ 150 admits within the bandwidth on each side (pooled);
  - density test p ≥ 0.05;
  - ≤ 1 of 4 placebos significant at 5%;
  - implied logit-slope SE ≤ the vertical prior SD (otherwise the source is "uninformative").
- **Policy change:**
  - ≥ 2 pre-period cohorts;
  - pre-trend difference not significant at 10% and ≤ 2 points;
  - change in net cost ≥ 3% of tuition for ≥ 100 admits per cohort;
  - comparison group unaffected;
  - SE ≤ the prior SD.

**Feed to the screen.** μ0 and σ0 are the inverse-variance combination of the usable sources and the vertical default prior. The audit also states yes or no to "anchor available without a test."

**Richmond.** The audit decides whether any index threshold or policy change exists. If none does: the vertical prior applies, the answer is "no anchor without test," and FAO runs in the weak-evidence state.

### 8. Targeted objectives and market tiers

**Constraint forms (all linear).** Each holds at k ∈ {L, M, H}.

| Objective | Form |
|---|---|
| Minimum enrollment, segment S | Σ_c∈S n_c p_c^k(a_c) ≥ T_S |
| Year-over-year gain | T_S = (1 + g_S) · E_S^SQ,k |
| Weights | maximize NTR_M + Σ_S w_S Σ_c∈S n_c p_c^M ($ per enrollee, client-stated) |
| Law median position ≥ m | Σ_c: band ≥ m n_c p_c^k ≥ 0.5 Σ_c n_c p_c^k + 1.645 σ_k, with σ_k = √(Σ n_c p_c(1 − p_c)) computed at status quo and updated once |

**Market tiers.** At most 5: home MSA, priority MSAs, other in-state, other out-of-state, international.

**Feasibility.**
1. At b_L, minimize Σ s_S with slack s_S ≥ 0.
2. If the minimum is > 0, report for each target:
   - the shortfall in enrollees at L, M and H;
   - the budget that would close it (re-solve with the budget free up to 2×);
   - the funnel stage where the segment leaks (from EFA).
3. **Shadow price:** re-solve with T_S relaxed by one enrollee and report the revenue per enrollee. Flag it when it exceeds the segment's net tuition, because that means buying enrollees at a loss.

**Thin history.**
- Markets with < 30 admits across history merge into their parent tier for cells and targets.
- Market intercepts in the forecast are shrunk toward the tier mean (ridge, λ chosen out of time).
- Targets on flagged markets are reported as "descriptive goal, not optimized."

**Floors.** Apply to every market tier, including targets.

**Whitelist test.**
- **Allowed:** market tier, CBSA, state, distance band, program, first-generation status, Pell eligibility, residency, student type, position or index band, need band.
- **Blocked:** race, ethnicity, gender, consumer-segment codes, credit data, and any geography finer than CBSA.
- **Static test:** config schema validation rejects each blocked attribute (one unit test per attribute).
- **Runtime proxy screen:** using audit-only data, compare each target segment's composition with the admit pool. If any group's share differs by > 20 points, or Cramér's V ≥ 0.3:
  - the segment needs explicit acknowledgment at the alignment gate;
  - the equity audit reports allocation changes by group.

  This is not an automatic block, because geography is legitimately whitelisted.

### 9. Release criteria: batch scoring (O15) and consumer segments (O13)

**Batch scoring may ship when:**
1. **Out-of-time calibration on ≥ 1 cohort:**
   - slope in [0.85, 1.15];
   - \|intercept\| ≤ 0.1 logit;
   - deciles within ±3 points (UG), or inside the 90% binomial band (small programs).
2. **Leakage and protected-attribute tests pass on the scoring feature set.**
3. **The file contains only** the client's key, the score, its band, the model version and the score date. The policy-lookup award appears only if elected, and it is the cell award.
4. **The SOW** names recipient roles and prohibits individualized pricing, use in admission decisions, use in individual scholarship negotiation (law), and onward sharing. Frankel deletes the files within 30 days of engagement close and keeps a deletion log.
5. **Monitoring:** decile calibration at each refresh; an alarm if the score-distribution PSI exceeds 0.2.
6. **The documentation sheet** states what a score does not mean.
7. **The alignment gate** signs off.

**Consumer segments may move beyond descriptive use only when:** (M2)
1. The client confirms in writing that its license allows sharing derived codes with a consultant for this purpose.
2. Codes are at block-group or ZIP level, never household.
3. The proxy audit shows Cramér's V with race and ethnicity < 0.3.
4. The codes add ≥ 0.01 out-of-time AUC.
5. The alignment gate approves.
6. They never enter the aid grid (closed).

### 10. Screen rule specification (value of information)

**Inputs from the client at scoping.**

| Input | Notes |
|---|---|
| N | Eligible admits per cohort |
| p | Eligible yield |
| Tuition and mean institutional award per enrollee | Or the discount rate |
| Award commitment H and annual persistence s | M = Σ_t<H s^t |
| Renewal rule | Fixed $ or % of tuition |
| Capacity | Class band ± %, or "uncapped" |
| Floors and targets | With $ weights, or as constraints |
| Planned top dose D | Law default 10% to 15% of tuition; UG $4,000 |
| Test share | Default 40% |
| Test cycles K | 1 or 2 |
| Cycles of use U | Default 3 |
| Operating cost F per cycle | — |
| Evidence-audit μ0, σ0 | Or the vertical default |

**Computation.**
1. **Projected pool.** Build it with cells per §4, from Tier 1 data if available; otherwise from a synthetic pool calibrated to public data (509 or IPEDS).
2. **Prior.** b ~ N(μ0, σ0²), truncated at 0; 21-point quadrature.
3. **Value matrix.** For each node b_i, solve the production optimizer for a\*(b_i) under the client's constraints. V[i, j] = the gain against status quo under b_i of a\*(b_j), with feasibility checked at b_i.
4. **EVPI** = U · (Σ_i w_i max_j V[i, j] − Σ_i w_i V[i, j0]), where j0 is the grid the two-sided rule picks under the prior.
   - **Gate 1:** if EVPI ≤ the cost of the cheapest admissible design, the verdict is **Not recommended** and the computation stops.
5. **Design SE**, in logit units: SE_b = 0.92 · √(p(1 − p)) · 0.76 / (0.447 · D · √(0.4 · N · K) · p(1 − p)). The factor 0.76 is the all-eligible analysis, analytic and conservative; simulation gave 0.66.
6. **EVSI.** For 21 values of b_i × 21 z-nodes: compute b̂ = b_i + z · SE_b, update the posterior, choose the grid with the production two-sided rule at the posterior quantiles, and score it at b_i. EVSI = U · (EV_test − EV_no test).
7. **Cost.**
   - Capped programs: C = M · 0.4 · N · K · p · E[bonus], with no revenue offset.
   - Uncapped programs: the prior-expected net cost, with the zero-effect cost also reported.
8. **Net value** = EVSI − C − F · K.

**Verdicts.**
- **Recommend:** all of the following hold.
  - Net value ≥ max($50,000; 0.5% of one cohort's multi-year net tuition).
  - EVSI ÷ (C + F · K) ≥ 1.5.
  - Zero-effect cost ≤ 5% of one cohort's multi-year net tuition.
  - Operating gates pass: the office can randomize and log; U ≥ 2; the alignment gate accepts disclosure.
- **Optional:** net value > 0, but a threshold or gate above is missed.
- **Not recommended:** net value ≤ 0, or Gate 1 stops the computation.

**Reported every time:** EVPI, EVSI, cost, the MDE (kept for familiarity), β\*, and the grid change the test would most likely trigger.

**Worked examples.** Richmond economics throughout:
- p = 0.21; tuition $57,700; net tuition $26,000 per enrollee; M = 2.92.
- Class band ±3%, plus a floor on enrollees above the median position.
- Prior θ ~ N(1.0, 0.5²); U = 3; F = $25,000 per cycle.
- Designs D ∈ {$4,000, $8,000} × K ∈ {1, 2}; the best design is shown.
- Step 1 uses a stylized two-band pool: above and below the median position, yields 15% and 27%, net tuition $15,700 and $30,700.

| Eligible admits | Status-quo class | EVPI (3 cohorts) | Best design | EVSI | Test cost + operating | Net value | Verdict | Current rule (3-cycle MDE) |
|---|---|---|---|---|---|---|---|---|
| 600 | 126 | $0.29M | $4,000 top arm, 1 cycle | ≈ $0 | $0.32M | −$0.32M | **Not recommended** | 2.0 → Recommend |
| 1,000 | 210 | $0.48M | $4,000, 1 cycle | $0.003M | $0.52M | −$0.51M | **Not recommended** | 1.6 → Recommend |
| 2,000 | 420 | $0.96M | $4,000, 1 cycle | $0.05M | $1.01M | −$0.96M | **Not recommended** | 1.1 → Recommend |
| 4,000 | 840 | $1.92M | $4,000, 1 cycle | $0.30M | $1.99M | −$1.69M | **Not recommended** | 0.8 → Recommend |

**Sensitivity.**
- **Prior.** At Richmond's actual N of 650, EVPI ranges from $0.10M to $0.68M across priors (μ0 0.6 to 1.4; σ0 0.5 to 1.0).
- **Class band ±10%.** At 4,000 admits, EVSI is $1.71M against a cost of $1.99M (ratio 0.86), still Not recommended.
- **Uncapped scale decision** (the UG pattern, where class can grow): with an $8,000 top arm and one cycle, net value is +$0.28M, +$1.13M, +$3.8M and +$9.7M for the four sizes, all **Recommend**. That shows the **decision space, not N, drives the verdict.**

**Interpretation for Richmond.** On a revenue objective, a price test cannot pay for itself: even perfect knowledge of the slope is worth less than one cycle of the cheapest test. Rerun the screen if Richmond names a slope-sensitive target, such as a median position. Two cheaper randomized options exist (M2):
- **Mechanism tests** (deposit-deadline or award-timing randomization), which cost almost nothing in dollars.
- **A one-year bonus** in place of a renewable one. It costs one-third as much but measures response to a different treatment. *Judgment call.*

### 11. ABA 509 layer

**Field rules** (confirm against the ABA definitions before release):
- Grant counts and percentiles cover all full-time JD students in the academic year *before* the report year; percentiles are among recipients.
- LSAT and UGPA percentiles describe matriculants.
- Yield = matriculants from the applicant pool ÷ offers.
- For a private school, nonresident tuition of 0 means "same as resident": normalize it and flag it.
- Conditional-scholarship counts lag two years. Prevalence = entering conditional awards ÷ class; loss rate = reduced or eliminated ÷ entering, for the same cohort.
- Use the full-time fields only.

**Rank-matching**, for each peer j and own position q:
1. **Applicant values.** Take the applicant's LSAT_q and UGPA_q from the client's own position distribution.
2. **Peer position.** π_j = mean of CDF_j(LSAT_q) and CDF_j(UGPA_q), using the interpolated 25th/50th/75th percentiles.
3. **All-student quantile and grant.** u = π_j. With recipient share r_j and share at or above full tuition f_j:
   - if u < 1 − r_j, the grant is 0;
   - if u ≥ 1 − f_j, the grant is the grant year's tuition;
   - otherwise v = (u − (1 − r_j)) / r_j, and the grant is interpolated on the recipient 25th/50th/75th percentiles (linear to the 25th below; capped at tuition above).
4. **Normalize** to a share of the grant year's tuition, then apply it to current tuition.
5. **Gap:** Gap_j(q) = peer share − own share at q. Compute the own share the same way from the client's own 509 data for symmetry, or from client data.
6. **Market gap:** the median of Gap_j(q) over the client-approved peer set (5 to 10 schools), reported with its interquartile range.
7. **Assumptions, stated on every output:**
   - grant rank equals academic rank (comonotone);
   - the all-class award distribution stands in for entering awards;
   - positions are relative to matriculants.

*Illustration (2025 reports):* an applicant at Richmond's 75th position (LSAT 167, UGPA 3.92) sits at about Wake Forest's 66th all-student quantile. That maps to about $43,000 there, against about $51,800 at Richmond, so Richmond is the more generous by about $9,000 at that position.

**Validation in a synthetic law world.**
- Generate 12 peer schools from 509-calibrated parameters.
- Student grants: g = F⁻¹(Φ(ρ · z_index + √(1 − ρ²) · ε)), with ρ ∈ {0.9, 0.7, 0.5}.
- Matriculation increases with grant and decreases with position, so matriculant selection is real.
- Publish the aggregates exactly as the 509 does (recipients only, all classes, prior year).
- **Truth:** the mean grant offered to an *admit* at position q at each peer.
- **Pass:** per-band \|bias\| ≤ 5% of tuition and Spearman ≥ 0.8 across bands at ρ = 0.9 and 0.7. Document the failure at 0.5, and report the matriculant-selection bias, which is expected to be positive.

**Allowed uses.**
- **Descriptive:** tuition and cost of attendance, grant distribution, class profile, applications, offers and yield, attrition and transfers, bar passage and employment, conditional-scholarship prevalence.
- **Candidate moderator:** market award-gap band and peer conditional prevalence, only through the §5 gates.
- **Forecast input:** none. The gap is a fixed function of position for a given peer set, and it lags a year.
- **Yield:** the client's own 509 yields check the recalibrated intercept. The status-quo yield must fall inside the five-year 509 range ± the binomial band. Cells with < 30 admits shrink toward the program yield with prior weight 30. Peer yields are never a prior for the client.
- **Synthetic parameters:** W0L.

### 12. Timing and sensitivity by date

**Waves.**
- Two by default. Three only if offers go out in at least three batches at least three weeks apart.
- A wave is a release batch.

**Randomization.**
- Stratified by wave × position band (law) or need band × residency (UG).
- Blocked within each stratum, so arm shares are exactly 40 / 20 / 40 of the test.
- **Analyse every randomized eligible.**

**Precision.**

| Setting | Per-wave MDE (points per $1,000) | MDE for a wave difference |
|---|---|---|
| Richmond, one cycle, $4,000 top arm | 5.1 | 7.3 |
| Richmond, one cycle, $8,000 top arm | 2.6 | 3.6 |
| UG, 2,000 admits, three cycles, $4,000 top arm | 1.7 | 2.4 |

**Revisions.**
- Every post-offer change is logged with its reason: student request, documented competing offer, staff-initiated, or appeal.
- The bonus is always delivered in the first offer, never as a revision.
- Estimation uses the first-offer randomized dose only (intent to treat).
- Reconsideration and increase rates by arm are reported as compliance diagnostics, and revision amounts are never used as price variation.

**A wave slope may change a recommendation only if all of the following hold.**
1. A single early-versus-late contrast was pre-registered with its direction.
2. Pooled over at least two cycles, the contrast is significant one-sided at 5% and is ≥ 50% of the pooled slope.
3. It beats one slope in held-out policy value by more than 1 SE.
4. A Monte Carlo timing world confirms it.

Until then, wave results are descriptive.

### 13. Boosted-model challenger

**Inputs.** The forecast's decision-date features: no aid fields, no protected attributes.

**Monotone constraints.**
- Increasing in: campus visit, engagement count, admitted-student event attendance, days applied before the deadline.
- Decreasing in: position band (law).
- Unconstrained: need band and market.

**Calibration.** Isotonic or Platt, fit on an out-of-time cohort.
- Calibration slope in [0.9, 1.1].
- Expected calibration error ≤ 0.02 (UG), or inside the binomial band (small programs).

**Margin.** The challenger is adopted for scoring only if, on each of at least two out-of-time cohorts:
- AUC improves by ≥ 0.02, with the paired-bootstrap 90% lower bound above 0;
- Brier improves by ≥ 3% relative;
- no decile is worse calibrated than the logit's worst decile.

The pilot backtest must show the same.

**Reason codes.** TreeSHAP top 3 positive and negative contributors from the frozen model, restricted to whitelisted names, stored with each score.

**Synthetic worlds.**
- **W20a, additive:** the challenger must fail in ≥ 90% of seeds.
- **W20b, interactions:** engagement × position (+0.6 logit for high engagement at top positions), visit × distance (visit matters only beyond 250 miles), and a step at deposit-deadline proximity. The challenger must pass in ≥ 70% of seeds at UG size (2,000 admits, three cohorts). Report the pass rate at law size (650), which I expect to be low.

**Optimizer baseline: No.** The grid baseline stays the recalibrated logit: smooth, monotone, aggregable by cell, and the model the β conversion is defined on. *Judgment call; what would change my mind:* W20b showing grid revenue loss above 0.5% from the logit's cell-level miscalibration, confirmed in two client backtests.

---

## Phase 4: Verdict and edits

### 4.1 Verdict

**Not fit to build as written. Fit to build once the M0 edits below are made.** I found two Critical issues.

1. The one-sided choice rule approves aid cuts whenever the estimate falls below break-even, however uncertain it is.
2. S5 cannot represent Richmond's status quo: the per-student cap, the ladder, the year-one horizon against renewable awards, and the cell count.

The third issue that matters most is the evidence economics. The screen should run on value of information, the experiment should analyse every randomized eligible, and the anchor needs a defined estimand pooled in logit units.

For Richmond, expect funnel analysis, monitoring, the 509 market view, and a codified status-quo grid. An optimized grid is possible only if the evidence audit finds design-based variation.

### 4.2 Numbered edits

| Edit | Section | Old | New | Acceptance test |
|---|---|---|---|---|
| S4-1 | §4 Evidence sources | Estimate from test students only | Analyse every randomized eligible, with non-selected eligibles as the $0 arm (intent to treat) | Monte Carlo W0: SE ≤ 0.8 × test-only; bias ≤ 3% |
| S4-2 | §4 Anchor | Pool AMEs by inverse variance; flag at 1.5 SE | Estimand θ = AME at status-quo awards for eligibles. Convert each source to b on its own sample, pool b, and flag at \|z\| > 1.5 in b units. Flag action: scenarios span both. After two consecutive flags: experiment only | W5 flag rate ≥ 70%; W0 false flags ≤ 10% |
| S4-3 | §4 Response model | β = anchor ÷ mean p(1 − p); 1% test | b from S4-2. The test compares the model's AME at status-quo awards on the experiment's eligibles, using **recalibrated** p, with the experiment's own status-quo AME (within 5%) | A deliberately miscalibrated forecast fails the test |
| S4-4 | §4 Response model | Center on `p_forecast(current award)` | Center on recalibrated p\* and the cell reference award r_c (Phase 3 §3) | Holdout status-quo class inside the forecast interval |
| S4-5 | §4 Sample size | 0.85 factor; 21% yield; MDE table; plausible 1 to 3 | Factor 0.92 or √(1 − R²); eligible yield; dose scaled to the vertical; all-eligible analysis; MDE reported for information only | Formula SE within 10% of Monte Carlo SE |
| S4-6 | §4 Cost | ~$420 per test student (year one) | M × E[enrolled bonus]; no induced-revenue offset when capped | Screen output matches a hand calculation |
| S4-7 | §4 Screen rule | Recommend if MDE ≤ 2.3 | Value-of-information screen (Phase 3 §10) | Worked examples reproduce; the verdict is unchanged under scaling of all dollar inputs |
| S4-8 | §4 Timing | Slope per wave | Stratify by wave; pooled estimate; wave contrast descriptive until the Phase 3 §12 gates are met | — |
| S4-9 | §4 Evidence audit | Checks listed | Add the minimum-evidence criteria and the μ0/σ0 output (Phase 3 §7) | One-page output on W8 and W9 |
| S4-10 | §6 Scenarios | 10th/50th/90th of the anchor AME | Quantiles of the logit-slope posterior; b_L = max(0, q10) | — |
| S4-11 | §6 Honesty | No realization multiplier | Also publish the Monte Carlo realized ÷ predicted distribution; show the low scenario beside every headline | Monte Carlo F8 criteria |
| S4-12 | §6 / §5 Budget | Checked at three scenarios | Plus a count-noise buffer of 1.645 × spend SD at b_H | Overrun ≤ 5% of seeds (outcome draws) |
| S4-13 | §10 Validation | 8 worlds × 50 seeds; beat the v2 optimizer in 60% | Phase 3 §1 and §2: 200/100 seeds, law world, confound worlds, model-set budgets, outcome draws, fair-baseline margin | Family-wise false-fail ≤ 3% by calculation |
| S4-14 | §4 text | "1,917 test students over four cohorts" | "…over three cohorts (2023 to 2025)" | — |
| S5-1 | §5 Choice rule | Gain ≥ 0 at the low scenario | Gain ≥ 0 at **both** L and H; constraints hold at L, M and H; automatic weak-evidence label | Unit tests in Phase 3 §3 |
| S5-2 | §5 Decision | Award from $0 to $12,000 on a $1,000 ladder; cap 75% of tuition | `award_mode` supplement or total; ladder to tuition; cap = max(configured cap, current award); law cap 100% | The Richmond-calibrated status quo is returned unchanged at β = 0 |
| S5-3 | §5 Horizon | Year one is the default | Budget and revenue horizon = the award's commitment length (law: 3; UG: as the client elects, ≥ 1); config rejects mismatches | Config test |
| S5-4 | §5 Grid | 75 cells (125 with market tier) | Cells ≤ admits per cohort ÷ 30; UG and law profiles (Phase 3 §4) | Config test; W0L |
| S5-5 | §5 Guardrail | No cell cut > $3,000 | ≤ 5% of tuition (configurable) | Monte Carlo reports binding frequency of guardrail and floors |
| S5-6 | §5 Targets | Whitelist without position; feasibility undefined | Add position band; median constraint; feasibility pass; shadow price; proxy screen (Phase 3 §8) | Whitelist unit tests; infeasible-target fixture |
| S5-7 | §5 Support | Revisions only rise | Increases-only evaluation (Phase 3 §6) | Mid-cycle snapshot matches a hand calculation |
| S5-8 | §5 Policy grid | Scope undefined (O4) | Phase 3 §4: reserve, projection, frozen thresholds, `policy_changes` log | Pool-projection backtest within 5% by cell group |
| S5-9 | App. C | Floors exempt for target markets (O14 proposal) | Floors apply to all tiers, including targets; segments under 30 admits pooled | Monte Carlo binding report |
| S5-10 | §5 Objective | Discretionary spend counts year one | Spend counted over the commitment horizon, with persistence | F14 config test |

### 4.3 Release readiness: true before Claude Code starts

1. Edits S4-1 to S4-14 and S5-1 to S5-10 merged into a v2.5 methodology. Section 13 updated with these rulings.
2. Estimand, choice rule and grid-baseline definitions written as functions with signatures (S3 interfaces).
3. A law profile in config: award mode, ladder, cap, horizon, position bands, cell rule.
4. The W0L world specified from the 509 parameters above, and the Monte Carlo study signed off (worlds, seeds, metrics, thresholds).
5. The screen's inputs added to the data request and scoping template. The Richmond screen run on its scoping inputs: expected verdict Not recommended unless a target is named.
6. The pitch and Phase 2 slide wording (changelog items 1 and 5) aligned with one slope, and with "no optimized grid without design-based evidence."
7. v2 equity and scenario tables blocked from any client-facing output.
8. The guardrail tests run in CI from a clean checkout; I could not verify the "7 passing."

### 4.4 Open questions for the author

1. **Is Richmond's real objective revenue, class size, or median position?** The screen's verdict turns on it.
2. **Does Richmond publish an index-based scholarship grid,** or has it changed award schedules in the last five cycles? This decides whether any anchor exists without a test.
3. **Does Richmond use need (FAFSA or institutional) in scholarships at all?** If not, drop need from the law grid.
4. **Are Richmond's awards fixed-dollar or a percentage of tuition at renewal?** At +3.9% tuition growth, this changes three-year net tuition by roughly 5%.
5. **Would Richmond accept a one-year bonus test,** or a mechanism test (deadline or timing), instead of a renewable bonus?
6. **What capacity band does Richmond hold its class to?** I assumed ±3%.
7. **Should a grid that fails to beat the best simple heuristic be replaced by that heuristic?** I recommend yes.

**What I could not verify**
- That the ABA defines the grant fields as I infer (prior year, recipients only); this is inferred from Richmond's rows.
- Richmond's actual average grant: my $30,700 is a band-midpoint estimate.
- The seven guardrail tests.
- The SAI/EFC harmonization and the data dictionary.
- The `funnel_cells` disclosure set (not opened).
- Any grid-optimizer behavior: none is built. The one-sided cut risk is shown by logic, not by a run.
- The value-of-information worked examples, which rest on a stylized two-band pool and a stated prior. The production screen should use the real optimizer on a 509-calibrated pool.
