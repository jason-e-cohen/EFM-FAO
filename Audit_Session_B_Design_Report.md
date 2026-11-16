# Audit Session B report: design audit

**Reviewer:** Claude Opus 5.5 (independent; did not write the material) | **Date:** November 16, 2026 | **Brief:** `Handoff_Session_B_Design_Audit.md` | **Status:** complete (Parts B1 to B7). Review only: nothing edited except this report and scripts in `review_support_v0.5/`. Nothing committed. Nothing here goes to a client without Jason's review.

**Environment.** The repo `.venv` is a macOS build and does not run on the Linux device. Checks use the device's Python 3.10.12 with numpy 2.2.6 (scipy is not installed and could not be installed; the normal CDF is computed with `math.erf`). All checks use synthetic toy numbers; no fixture value is copied.

**Jason's answer to the Part B6 question (Nov 16):** "workbook this spring 2027, decisions in summer / fall 2027; we have 6 mos to build."

## 1. Verdict

1. **Spec v0.5 is build-ready for Phase 1 after five Blocking text fixes:** tests 13, 14 and 16 cannot pass as written (B1-1 to B1-3); the paid-anyway share is wrong when the score floor is set or the tuition cap binds (B1-4); the Trim formula divides by zero on empty cells and ignores its floor and exemptions (B1-5). Before Phase 2, test 3 must force LibreOffice to recalculate, or it compares Python with Python (B1-25, shown).
2. **Metrics:** one Blocking for the later S5 integration (NTR means year-1 tuition in the ledger and three-year tuition-and-fees with persistence in the optimizer, yet the documents require them to be equal, B3-1). Major: discount rate basis and the Dean's meaning (B3-2), median basis for unscored students (B3-3), pacing and pool-growth populations (B3-4), unlabeled ratios of expectations (B3-5), deferrals in yield (B3-6), class population (B3-9), "net price" naming (B3-13).
3. **Statistics:** the methods suit the data. The uncalibrated common shock (s = 0.10) drives P(class > cap) and the goal-seek ceiling, cannot be estimated from one client's cycles, and is untested by any synthetic world (B4-1); a single common shock hides segment-level shocks from the median (B4-2); law-size forecast thresholds misfire 16% to 29% of the time (B4-3).
4. **Generality:** Richmond is built into names (LSAT, 2026, out-of-state target) and defaults; there is no single client schema, no annual cycle, no pinned environment, and the design set has not been committed since October 23. Renames before Phase 1 fix most of it cheaply (B5-1).
5. **Feasibility:** the Must list is 15 to 24 build days and 28 to 42 review hours, which fits six months only if the production data path (rule change, SOW data terms, Richmond's extract and state counts) is settled this month.
6. **Top three simplifications:** defer dashboard views 2 and 3, goal-seek and the schedule; replace tripwires, the net-price block and `Static_MC` with closed-form strips and lines; generalize the target tier to a priority segment with score- and year-generic names.
7. **Decisions for Jason (section 9):** the production data path; which entering class the summer and fall decisions are for; reopening A5 (dashboard in the first delivery); the shrink-path protection rule; the median basis; the discount basis.

## 2. Part B1: spec v0.5 mechanics and consistency

**Method.** Diffed v0.5 against v0.4 (every removed line reviewed); checked C1 to C29 against sections 0 to 15; toy checks in `review_support_v0.5/b1_toy_checks.py`. Line numbers are from the spec as of Nov 16.

**Change-list coverage.** C1 to C29 are all present in v0.5 and say what the change list says, with three differences: C17 gained the upside tripwire (from C29; fine), C24's target-enrollee goal-seek constraint lost the continuity correction (B1-18), and the change list's B10 calls D17 "planning tuition placeholder" while the spec's D17 is the target-tier application lift (Jason's answer F3; the spec is right, the change list is stale; B1-21).

### Answers to the 13 questions

| Q | Answer (finding IDs below) |
|---|---|
| 1 Target-enrolled probability | Continuity correction is in the right direction for an integer goal (P(E_T >= g) = P(E_T > g - 0.5)). V_T includes s^2 M_T^2, built the same way as the class variance (holds). The normal form is not flagged at small M_T, and its error reaches 0.016 to 0.025 at M_T of 4 to 8 (B1-8). Empty tier divides by zero (B1-14) |
| 2 Cost per incremental | dSpend_T = merit_T(s) - merit_T(p) counts all award dollars in target cells, including the incentive to students who would have enrolled anyway, plus base awards to new enrollees: right for this KPI. Under scope `all_out` it misses out_other incentive spend; negative dE gets a wrong message; validity is not enforced (B1-11). The 0.5 threshold is a display guard on a difference of expectations, not a sampling-noise rule, so it need not scale with M_T (holds) |
| 3 Paid-anyway share | Computed over all target cells, not the cells that receive the incentive, and as an aggregate ratio that ignores the tuition cap: wrong output (B1-4, Blocking). Validity condition is a label only (B1-11) |
| 4 Incentive scope | `all_out` reduces to the v0.4 formula on merged data, but test 14 has no v0.4 implementation to compare against (B1-3). `target` with an empty tier is an error as required, but the rule is broader than it should be (B1-14). The tuition cap follows the incentive in ledger step 4 and in the Checks sheet; the net-price block ignores the incentive and does not clamp scaled awards (B1-13) |
| 5 Tier mechanics | Fallback chain stated two different ways in section 4 and missing pool thresholds; "LSAT group" undefined (B1-6). Offset applies to out_target only (holds) but its meaning depends on the fallback level and duplicates the target shift (B1-7). Precedence is unambiguous: section 2 says the overrides "override" (replace), and the strip adds on top (holds; Excel blank handling, B1-20). Lift multiplies after the pool multiplier at all scores; spec section 2, step 2 and test 15 agree (holds); the tripwires do not say whether the lift is in (B1-10) |
| 6 Class size and cap | Every live use is correct: P(class > cap) uses `class_cap` (section 5, strip, test 18); band, break-even, m_class and narratives use `class_size`; goal-seek uses the cap with an optional floor at target - band. `need_denominator` stays 140 and test 9 and 18 assert `need_rate` invariance (holds). Range rules agree across section 2 line 54, D5 and test 18 (holds). The what-if list is global while the cap is per scenario (B1-19) |
| 7 Shrink path | E_{k-1} is the cumulative expected enrollment of the cells before k, which equals what was removed before k because earlier cells are fully removed first; the walk stops exactly at M - N (holds). mu_k = 0 gives #DIV/0!, which SUMPRODUCT propagates; floor_rate and exempt_cells are not in the Excel formula (B1-5, Blocking). N >= M returns the original rates by construction of MAX(0, ...) (holds), but test 16 asks it to "hit N" (B1-1). With default floor 0 and no exempt cells the walk always reaches target cells last; with exemptions or a floor it can fall short silently (B1-5). Tie-break orders match between section 3 and test 16; the Trim sheet takes its order from Python at build time (holds). Buildable in XlsxWriter with no macros; needs one helper column per N for "lowest band still admitted" (B1-20) |
| 8 Pool tripwires | Decomposition matches where the multiplier applies (cells at or above `pool_threshold_lsat`, including the 165 band, which carries g = -1 at t = 166); G_hi can be zero or negative and the spec shows "none" rather than dividing (holds, wording B1-10). Under G_hi > 0 and G_lo <= -0.5, P(median holds) is increasing in m, and P(class > cap) is increasing over the practical range (toy check: both monotone on m in [0.3, 3]). Brackets are not stated, and lift inclusion is not stated (B1-10) |
| 9 Net-price readouts | Fixed-award change Ts - T26 and scaled change p(T26 - A) (within the $50 tuition rounding) both hold; the full-tuition rung is zero under both only because the spec special-cases it (holds). No path feeds the equivalent yield shift into the ledger (holds), but the line restates the deferred net-price response as a number and lacks the response label (B1-13) |
| 10 Decisions | D1 holds: trim writes ordinary rates the analyst can overwrite, and goal-seek is the CLAUDE.md-sanctioned helper (note: `max_ntr` mode is an admit-rate optimizer in all but name; keep it labeled a helper). D10 holds in the ledger. No new output labels an award. Small cells are shown; spec decision (4) still omits the aid office (Session A A2-2, not yet fixed) |
| 11 Tests 13 to 20 | Tests 13, 14, 16 cannot pass as written (B1-1 to B1-3). Test 15's 0.02 tolerance is marginal for small target tiers (B1-8) and its "identity" is a definition (B1-23). Untested: tier offset, fallback chain, `oos_min_lsat` under scope `target`, paid-anyway share, empty-tier display, trim floor and exemptions, `pair_award_rule`, upside tripwire bracket failure. Tests 1, 2, 4, 5 never run with an empty target tier (test 1's toy grid now has a target cell; tests 4 and 5 use synthetic worlds with a 0.25 target share), so they do not exercise the empty case at all (B1-14) |
| 12 Interface contract | There is no contract: section 15 has no list of outputs with names, units and source sheets, though test 11 and decision (5) depend on one (B1-12) |
| 13 Phase table and handoff | Phase 1 scope and tests match. Phase 1b differs (handoff omits the discount and UG-gap rows and paired scenarios). The handoff labels the shrink path D15 (spec: D14) and attributes "90 to 150" to D14 (spec: section 2 only) (B1-21) |

### Toy-check output (from `review_support_v0.5/b1_toy_checks.py`)

| Check | Result |
|---|---|
| Target-tier P(E_T >= goal), normal vs exact Poisson-binomial (s = 0) and vs 200,000-draw simulation (s = 0.10) | Worst error over all goals: M_T 4.2: 0.022 (s 0), 0.025 (s 0.10); M_T 8.1: 0.016, 0.020; M_T 20.7: 0.011, 0.013 |
| Six-cell class (M = 27), normal vs exact | Worst error 0.0075 over all caps |
| Median: closed form without shock vs simulation with multiplicative N(1, 0.10) shock | Differences 0.000 to 0.002 at margins -15 to -6 (supports the spec's claim that the shock can be left out of the median) |
| Paid-anyway, four target cells, `oos_min_lsat` 165, $10,000 incentive, cap binding in the top cell | Spec formula 0.834 ($66,281); eligible cells only 0.637 ($50,666); cell-level 0.623 ($49,500) of $79,500 incentive cost |
| Shrink path with `protect_target` (11 cells, M = 120, three target cells) | Share at or above 166 rises from 0.367 to 0.662 down to N = 65, then falls once the walk cuts non-target cells above 166 while target cells below 166 remain |
| Tier split vs the admits >= 5 fallback | An 8-admit out-of-state cell split 25/75 gives a 2-admit part that falls back to the pool yield; expected enrolled 2.0 unsplit vs 1.8 split |
| Tripwire monotonicity (synthetic split, s = 0.10) | Both probabilities monotone in m on [0.3, 3] |

### Findings

**Blocking**

**B1-1. Test 16 cannot pass as written.** Blocking. Shown (reading plus toy), high.
Location: spec line 236 (test 16); section 10 class range (line 213, "133 to 146 per cohort"); section 3 shrink path (line 108); section 2 `trim` (line 64).
(a) "Hits N within rounding for N = 100 to 140": the shrink path only removes admits, so for N >= M it returns the original rates and cannot hit N. Synthetic worlds are generated with classes of 133 to 146, so N = 135 and 140 will often sit above M. (b) "The share at or above the threshold is non-decreasing as N falls" conflicts with `protect_target: true`: once the walk has cut every non-target cell below the threshold it cuts non-target cells above it while target cells below it remain, and the share falls (toy: 0.662 at N = 65, 0.633 at N = 60). It bites whenever M - N exceeds expected enrollment in non-target cells below t.
Fix: replace test 16's first and last clauses with "for each N in `class_what_if` with N < M, the trimmed expected class equals N within 1e-9 (1 when `integer_admits`); for N >= M the rates equal the input rates" and "while the walk is in cells below t (all cells cut so far have `lsat_lo` < t), the share at or above t is non-decreasing as N falls". See B1-16 for the design question underneath.

**B1-2. Test 13 (tier merge invariance) contradicts the base-yield fallback.** Blocking. Shown, high.
Location: line 233 (test 13); line 130 (fallback chain); line 122.
A split part that drops below 5 admits switches from its own history to a pooled yield, so totals change even with "equal parameters" (toy: 2.0 vs 1.8 expected enrolled).
Fix: "13. Tier merge invariance: with `y0` and `a0` inherited from the unsplit cell (the fallback chain bypassed), splitting out-of-state cells into two tiers in any proportion changes no total or probability. A separate assertion checks that the fallback chain picks the level stated in section 4 for a cell with 4, 5 and 0 admits."

**B1-3. Test 14 compares against a v0.4 implementation that does not exist.** Blocking. Shown, high.
Location: line 234; Handoff "the Phase 1 build has not started"; line 122 vs line 130.
v0.4 was never built, and its fallback ("the cell's LSAT-group pooled yield") differs from v0.5's even on merged data.
Fix: "scope `all_out` with every out-of-state cell in `out_other` gives the same awards, yields, class, merit and probabilities as scope `target` with every out-of-state cell relabeled `out_target`, and as the hand-computed toy answers in test 1."

**B1-4. Paid-anyway share is wrong when `oos_min_lsat` is set or the tuition cap binds.** Blocking (wrong output). Shown (toy), high.
Location: line 106 (section 3, paid-anyway); C14.
The ratio runs over all target cells, so cells below `oos_min_lsat` (no incentive, same enrollment in both terms) pull it toward 1; and multiplying it by total cost assumes a uniform incentive, which the tuition cap breaks in the top rungs. Toy: 0.834 against the correct 0.623.
Fix (cell level, in Python and Excel): `incentive_c = award_sc - award_base_sc`; `paid_anyway_usd = sum_c min(e_pc, e_sc) x incentive_c` over cells with `incentive_c > 0`; `paid_anyway_share = paid_anyway_usd / oos_cost`. Same population for the cost per incremental enrollee (B1-11).

**B1-5. The Trim formula divides by zero on empty cells and ignores `floor_rate` and `exempt_cells`.** Blocking for Phase 2 (Python must guard in Phase 1). Shown (reading), high.
Location: line 157 (`Trim` sheet); line 110 (rule step 2); line 64.
Sparse cells have mu_k = 0, so the formula returns #DIV/0!, which every per-N SUMPRODUCT propagates. It also cuts to rate 0, not `floor_rate`, trims exempt cells, and reports no shortfall when M - N is unreachable.
Fix: define removable enrollment `rm_k = A_k y_k max(0, r_k - floor_rate) x [cell k not exempt]` and `R_k` its cumulative sum in trim order; `removed_share_k = IF(rm_k = 0, 0, MIN(1, MAX(0, (M - N - R_{k-1}) / rm_k)))`; `rate_k(N) = r_k - (r_k - floor_rate) x removed_share_k` for non-exempt cells; and a per-N status `IF(M - N > R_K, "N not reachable: shortfall " & TEXT(M - N - R_K, "0.0"), "OK")`. State that `floor_rate` is an absolute admit rate and that trim uses the Middle case.

**B1-25. Test 3 (and test 7) pass vacuously: LibreOffice headless does not recalculate an XLSX file on load by default.** Blocking for Phase 2. Shown, high.
Location: spec line 223 (test 3), line 227 (test 7), line 145 ("Write each formula with its cached value").
The spec writes Python's cached value into every formula, and LibreOffice does not recalculate XLSX on load by default. On the device (LibreOffice 26.2), `=1+1` cached as 5 reads back 5 after headless conversion, and 2 with `OOXMLRecalcMode` set to 0 (`b6_lo_recalc_check.py`, `b6_lo_recalc_fix.py`). Test 3 as written compares Python with Python.
Fix (test 3): "Recalculate with a dedicated LibreOffice profile (`-env:UserInstallation=file://<tmp profile>`) whose `registrymodifications.xcu` sets `/org.openoffice.Office.Calc/Formula/Load/OOXMLRecalcMode` to 0 (always). As a guard, build one copy with every cached value set to a sentinel (for example -999) and assert that no sentinel survives recalculation." Same for test 7.

**Major**

**B1-6. The base-yield fallback is stated two ways, with no thresholds for the pool levels, and "LSAT group" is not defined.** Major. Shown, high.
Location: line 122 ("fallback: the cell's LSAT-group pooled yield when admits are under 5") vs line 130 ("the cell's three cohorts when admits are at least 5, else the (market tier, LSAT group) pool, else the (residency, LSAT group) pool"); "LSAT group" also at line 56 (floor and cap) and line 217 (generator).
Whether "at least 5" is per cohort or summed, and when the tier pool is too thin, is not said.
Fix: delete the parenthesis on line 122 and replace line 130's first sentence with: "Base-yield fallback per cell: the cell's own three-cohort admits-weighted yield when its three-cohort admits total at least 5; else the (market tier, LSAT group) pool when that pool's three-cohort admits total at least 30; else the (residency, LSAT group) pool. An LSAT group is the cells at or above `pool_threshold_lsat` or below it (two groups; unscored rows join the lower group)." Add the fallback assertion to test 13 (B1-2).

**B1-7. `tier_yield_offset_pts` means different things at different fallback levels and duplicates `yield_shift_pts_target`.** Major. Suspected (reasoned), medium.
Location: line 59, line 130, C9, C21.
When y0 comes from the residency pool the offset stands in for the missing tier difference; when it comes from the cell's own history or the tier pool, the offset double counts it. With a linear response it differs from the target shift only at the yield bounds. No test exercises it.
Fix (judgment call): either (a) apply the offset only when y0 comes from the residency pool, with the text "Assumed yield difference of target-tier admits over other out-of-state admits, used only where the tier's own history is too thin", or (b) drop it and use `yield_shift_pts_target` (B7 candidate). Add a test either way.

**B1-8. The target-tier normal approximation is not flagged at small M_T, and test 15's tolerance can fail on it.** Major. Shown (toy), high.
Location: line 104 (target KPIs); line 235 (test 15, tolerance 0.02).
Worst error against the exact distribution: 0.022 to 0.025 at M_T = 4.2, 0.016 to 0.020 at 8.1, 0.011 to 0.013 at 20.7. Richmond's NY and PA tier could hold 10 to 20 expected enrollees.
Fix: Python computes P(E_T >= goal) exactly (convolution of the cell binomials, which is cheap at these sizes, mixed over the shock by Gauss-Hermite quadrature with 20 nodes); Excel keeps the normal form and shows "approximate (fewer than 20 expected)" when M_T < 20; test 15 compares Python's exact value with simulation (tolerance 0.01) and reports the Excel normal's gap without asserting it.

**B1-9. The simulation model of the common shock is not written down, yet tests 2, 4 and 15 depend on it.** Major. Shown, high.
Location: line 56 (`common_shock_sd`); section 5; section 1 (`sw/mc.py`); `ya_workbook_support/analysis.py` lines 143 to 148 (multiplier drawn from N(1, 0.10) on every cell's yield, clipped to [0, 1]).
Fix (section 5, new last paragraph): "Simulation (`mc.py`): per draw, e ~ Normal(1, s); each cell's yield is clip(e x y_c, 0, 1); enrollment ~ Binomial(A_c, clipped yield), independent across cells given e. The closed-form variance s^2 M^2 is the matching approximation (it overstates the variance by s^2 sum A_c y_c^2, which is small)."

**B1-10. Tripwire definitions leave four things open.** Major. Shown, high.
Location: line 114; C17; test 17.
(a) Whether `target_pool_lift_pct` and other scenario levers are applied when M_lo, M_hi, G_lo, G_hi are computed. (b) Whether m replaces the scenario's `pool_multiplier` or multiplies it ("growth over 2026, m - 1" implies it replaces it). (c) The bisection bracket and what is shown when the probability target is not reached inside it. (d) There are two LSAT median thresholds, so there are up to six tripwire numbers, not four; and "none" covers both "holds at any pool" (G_lo >= 0, G_hi >= 0) and "never holds" (G_lo < 0, G_hi <= 0).
Fix: "M_lo, M_hi, G_lo and G_hi are computed with every scenario lever applied except the pool multiplier, which is set to 1; m replaces `pool_multiplier`; the target-tier lift stays applied. Bisection searches m in [0.5, 3.0]; if the target probability is not crossed in that bracket, show 'not reached between -50% and +200%'. Linear forms: if G_hi <= 0, show 'holds at any pool' when G_lo >= 0 and 'not reachable by pool growth' otherwise. Tripwires are reported for the first LSAT median threshold only (166 by default); the second is in the Python output."

**B1-11. The two incentive KPIs need a defined population, a sign rule and an enforced validity check.** Major. Shown, high.
Location: lines 105 to 106; C14.
(a) Under scope `all_out`, the incentive also goes to `out_other`, but dE and dSpend run over target cells only. (b) A negative dE (an incentive cut) shows "increment under half a student". (c) "Valid only when s differs from p by the incentive alone" is a label; the workbook can check it. (d) dSpend is aid dollars; a CFO will ask for the NTR effect too (each incremental enrollee also pays tuition).
Fix: "Population: cells that receive the incentive in s (in scope and at or above `oos_min_lsat`). Show dE and dSpend always; show dSpend / dE when dE >= 0.5, 'savings per enrollee lost' (dSpend / dE) when dE <= -0.5, and 'change under half a student' otherwise. Show 'not valid: parent differs in more than the incentive' unless every lever other than `oos_bonus_usd`, `oos_bonus_scope` and `oos_min_lsat` equals the parent's (checked by formula over the lever columns). Add the row 'NTR change per incremental enrollee' = dNTR / dE."

**B1-12. Section 15 has no interface contract.** Major. Shown, high.
Location: lines 282 to 293; test 11 (line 231, "the interface contract in section 15"); decision (5) line 11.
Test 11 has nothing to enumerate, and the v0.5 blocks are not bound to names.
Fix: add section 15 item 11, a table with columns `name`, `unit`, `scenario/case grain`, `source sheet and named range`, `Python function`, `label required` (for example `target_enrolled_mean | students | scenario x case | Summary!TGT_E | ledger.target_kpis | Response based on client-input`). Required before Phase 2, not Phase 1.

**B1-13. The net-price block's "equivalent yield shift" restates the deferred net-price response as a number; the block ignores the incentive.** Major. Suspected (reasoned), medium.
Location: line 116; D10, D16; CLAUDE.md deferred features ("we have no evidence").
The line reads as an estimate of sticker-price response, which CLAUDE.md says has no evidence, and lacks the response label though it uses b_M. Rungs also ignore the incentive, and `A (1 + p)` is not clamped at `Ts` (it can exceed it by up to $25 after rounding).
Fix: replace the line with "If admits responded to a tuition rise as they respond to an equal cut in aid (not assumed anywhere in this workbook), the change would equal x yield points at the placeholder slope. Response based on client-input." or delete it (B7). Add "net price for target-tier cells includes the incentive" and use `min(A (1 + p), Ts)`.

**B1-14. An empty target tier is not handled, and the error rule would stop Richmond planning runs before state-level counts arrive.** Major. Shown, high.
Location: line 60 ("`target` with no target cells is an error"); line 104 (`V_T`); section 9 (reproduce: tier empty); section 15 item 10 (state counts requested, not received).
With no target cells, P(E_T >= goal) divides by zero; and since Richmond's cells carry no state yet, every planning scenario with scope `target` errors, even at a zero incentive.
Fix: "Scope `target` with no target cells is an error only when `oos_bonus_usd` > 0, `target_pool_lift_pct` != 0 or `target_enrolled_goal` is set. With no target cells, every target KPI shows 'no target-tier cells in the data' and no probability is computed." Add a test that builds an empty-tier run and finds no NaN or error cells.

**B1-15. Base yield pairs a three-cohort average yield with the latest award.** Major. Suspected, medium (cross-reference to B4).
Location: line 122 (`a0_c` = latest cohort award; `y0_c` = three-cohort admits-weighted yield).
Section 10 records 165-and-above awards falling from about 0.98 to 0.79 of tuition over the three cohorts, so under the spec's own slope the Baseline yield at a0 is overstated there (and understated where awards rose), moving every scenario built on Baseline.
Fix (judgment call): "y0_c is the three-cohort admits-weighted yield re-centered at the latest award: y0_c,k = ybar_c + (b_k / 100) x (a0_c - abar_c) / 1000, where abar_c is the admits-weighted three-cohort award." This makes y0 depend on the case k; if that is unwanted, use the latest cohort's yield where its admits are at least 5.

**B1-16. `protect_target` can cut high-LSAT non-target cells before low-LSAT target cells.** Major (judgment call). Shown (toy), medium.
Location: line 110 (rule step 1: "every `out_target` cell is placed after all other cells"); D14; CLAUDE.md working rule 3.
Read literally, the walk removes a 170-and-above in-state cell before a 152 NY cell, lowering the median. At Richmond's current mix it rarely gets that far for N >= 100.
Options: (a) keep as is and state the consequence; (b) protect target cells only below the median threshold: "target cells below t are trimmed after all non-target cells below t and before any cell at or above t". Recommend (b); it changes nothing at Richmond's current mix and removes the conflict in B1-1.

**Minor**

- **B1-17.** Line 104: the continuity correction assumes an integer goal; `target_enrolled_goal` is free text. Fix: "goal is rounded up to an integer."
- **B1-18.** Line 174 (goal-seek target constraint): `M_T >= goal + z sqrt(V_T)` lacks the continuity correction used in the probability. Fix: `M_T >= goal - 0.5 + z sqrt(V_T)` (consistent with the class and median constraints).
- **B1-19.** Line 54: `class_what_if` is global but `class_cap` is per scenario; "values above `class_cap` are rejected" is ambiguous. Fix: "rows above a scenario's cap show 'above cap' for that scenario; the shrink-path group shows 'not applicable (N at or above expected class)' when N >= M."
- **B1-20.** Line 145 (formula whitelist): omits `SUM` and `ROW`, which the checksum on line 160 uses. The residency and target overrides need "blank means inherit"; write it as `IF(cell = "", inherited, cell)`. "Lowest LSAT band still admitted" needs one helper column per N (`IF(removed < 1, lsat_lo, 999)`), which the "no per-shift helper columns" rule (written for the yield strip) should not be read to forbid.
- **B1-21.** Labels: `Handoff_Prototype_Phase1.md` calls the shrink path D15 (spec D14) and puts "rejects values outside 90 to 150" under D14 (spec: section 2 only); the handoff's Phase 1b omits the discount and UG-gap rows and paired award-rule scenarios that spec section 12 lists; `Spec_v0.5_Change_List_draft.md` B10 lists D17 as the tuition placeholder (spec D17 is the lift). Fix the handoff and annotate the change list as superseded by section F.
- **B1-22.** Test 2's 0.01 tolerance holds only if the toy grid is large enough: at M = 27 the normal's worst error is 0.0075, and smaller grids fail. Fix: "toy grid with expected class at least 25; compare the closed form with the exact convolution (tolerance 0.01) and the simulation with the exact convolution (tolerance 0.005)."
- **B1-23.** Test 15's "cost-per-incremental identity" is a definition. Fix: assert `dSpend = sum_T e_s (a_s - a_p) + sum_T (e_s - e_p) a_p` cell by cell.
- **B1-24.** Line 52 and 110: unscored rows (GRE, JD-Next) sit in band 0 and are trimmed first. State it as a policy choice in the README, since it bears on access.

**Held (one line each).** Continuity-correction direction (Q1); V_T built like the class variance (Q1); median form without the shock (toy differences at most 0.002); tripwire bisection monotonicity under G_hi > 0, G_lo <= -0.5 (toy); tuition cap after the incentive in the ledger and schedule; `need_rate` fixed at 200,000 / 140; range rules consistent across section 2, D5 and test 18; shift precedence is replacement; lift at all scores, after the pool multiplier; D1, D2, D3 and D10 hold in the ledger; no new output labels an award; tie-break orders agree between section 3 and test 16.

### B1 verdict

Spec v0.5 is fit to build Phase 1 from after five Blocking fixes, all text edits of a few lines: rewrite tests 13, 14 and 16 (B1-1 to B1-3), replace the paid-anyway formula with the cell-level form (B1-4), and guard the shrink-path division and implement `floor_rate` and `exempt_cells` (B1-5). B1-6 (fallback chain), B1-9 (shock model), B1-10 (tripwire definitions) and B1-14 (empty tier) should be fixed in the same pass, because the Phase 1 build would otherwise have to guess. B1-12 (interface contract) and B1-25 (forced recalculation in test 3) are needed before Phase 2, not Phase 1. B1-7, B1-15 and B1-16 are judgment calls for Jason; none blocks Phase 1.

## 3. Part B2: methodology v2.7 edits and the V27A addendum

**Method.** Diffed `02_methodology_v2.7.md` against `02_methodology_v2.6.md` by tag; checked each V27 item in `Change_List_v2.7_draft.md` and each V27A item in `CHANGELOG_v2.7.md` against the methodology, S1 v1.2, the roadmap v2.7, the executive read v2.7, CLAUDE.md and spec v0.5. Guardrail, screen and disclosure edits first.

### Status of every item

| Items | Status | Finding |
|---|---|---|
| V27-01 guardrail removed, step-size table (methodology line 450) | Applied as listed | Residual "guardrails" in the alignment-gate packet line (B2-6) |
| V27-02 support rule (line 321) | Applied as listed | |
| V27-03 median statement withdrawn (line 496) | Applied as listed | |
| V27-04 screen verdicts marked (lines 262 to 272) | Applied with issues | B2-2 |
| V27-05 O36 (lines 272, 1068) | Applied as listed | |
| V27-06 thresholds (line 413) | Applied as listed | |
| V27-07 count rule, decision layer (line 358) | Applied as listed | B2-5 (count under the class range) |
| V27-08 law profile (line 360) | Applied, then contradicted by V27A-01 | B2-1 |
| V27-09 ladder (line 395) | Applied as listed | |
| V27-10 scenario evaluator (lines 540 to 562) | Applied as listed | Tier offset missing (B2-4) |
| V27-11 tuition scenarios (line 529) | Applied as listed | |
| V27-12 outputs (line 536) | Applied as listed | |
| V27-13 descriptive layer and markets (lines 38, 55) | Applied as listed | |
| V27-14 small-cell disclosure (lines 617 to 622) | Applied as listed | Files, policy document and public material not covered (B2-3) |
| V27-15 evaluator views and O37 (line 576) | Applied as listed | |
| V27-16 section 11 rows (lines 773, 787 to 792) | Applied as listed | |
| V27-17 limitations (lines 825 to 830) | Applied as listed | |
| V27-18 section 14 and F20 (lines 889, 1091 to 1099) | Applied as listed | |
| V27-19 Appendix C (line 914) | Applied as listed | |
| V27-20 scope and O36 to O40 (lines 28, 1068 to 1072) | Applied as listed | |
| V27-21 to V27-23 FR-29 to FR-31 | Applied as listed | |
| V27-24 FR-33 retired, FR-33a | Applied as listed | |
| V27-25, V27-26 FR-34, FR-36 | Applied as listed | |
| V27-27 FR-40 | Applied as listed | |
| V27-28 FR-52, NFR-01, FR-61 | Applied with issues | FR-52 says "seven" tests and "All 7 existing tests pass" while adding test 8 (B2-7) |
| V27-29 FR-55, FR-56 | Applied as listed | |
| V27-30 FR-71 to FR-76 | Applied as listed | FR-06 acceptance still contradicts FR-76 (Session A A2-1; unfixed, B2-3) |
| V27-31 roles | Applied as listed | |
| V27-32 evidence-state note (S1 line 59) | Applied as listed | |
| V27-33 stories 6, 7, 8; sections 7, 8 | Applied as listed | |
| V27-34 OD-07, CONTR-02, CONTR-05 | Applied as listed | |
| V27-35 to V27-39 roadmap | Applied as listed | |
| V27-40 to V27-43 CLAUDE.md | Applied as listed | |
| V27A-01 target tier, incentive scope, lift, offset, target KPIs | Applied with issues | Section 5 lacks the target KPIs and the offset; line 360 contradicts it; executive read not updated (B2-1, B2-4, B2-8) |
| V27A-02 class target under a hard cap | Applied in methodology, S1, roadmap; not in the executive read | B2-8 |
| V27A-03 shrink path | Applied with issues | FR-78 acceptance inherits the test 16 contradiction (B1-1) |
| V27A-04 tripwires | Applied with issues | FR-79 inherits B1-10 |
| V27A-05 net-price readouts | Applied as listed | Wording risk in the spec (B1-13) |
| V27A-06 tuition 5.5% placeholder | Applied with issues | FR-74 calls 6.0% "default" without "reproduce mode" (B2-9) |
| V27A-07 data request additions | Applied (Session A, Nov 16) | |

### Specific checks

| Check | Result |
|---|---|
| Guardrail language; client-declared policy envelope | No live text flags a client award. "Client-declared policy envelope" appears only in the spec's hook list (line 254) and is defined nowhere. Residues: B2-2, B2-6, B2-11 |
| Price-test screen | Status paragraph (line 272) correct; four untagged statements of the ±3% verdict remain (B2-2). "±4 on 140 is ±2.9%" no longer fixes the row when the target can be 110 (±3.6%) |
| Small-cell disclosure | Session A's rule confirmed for the authenticated dashboard, and its wording edits match it; files, policy document and public material not covered (B2-3) |
| Decision layer and count rule | 13 groups plus one incentive = 14 against a limit of 21. V27A does not change the count (the tier is not a schedule dimension; lift and offset are assumptions, not policy parameters). Tighter at a smaller class (B2-5) |
| Tuition defaults | 5.5% is labeled unconfirmed everywhere (M lines 529, 558; FR-74, OD-09, CONTR-05; D4; CLAUDE.md). 6.0% lacks "reproduce mode" in FR-74 and D4 (B2-9) |
| Open items | O36 to O40, OD-05, OD-08, OD-09 open; OD-07 resolved and recorded; OD-06 stale (B2-10). Nothing closed silently |
| Traceability | All 81 FR rows cite a section that exists; section 5 defines none of the FR-77 KPIs (B2-4) |

### Findings

**B2-1. Methodology line 360 contradicts V27A-01.** Major. Shown, high. (Passed on by Session A.)
Location: `02_methodology_v2.7.md` line 360: "Geography enters as one out-of-state incentive (additional dollars per out-of-state student, optional score floor); market-level geography (states, MSAs) is deferred (section 11)."
Fix: "Geography enters as a market tier on each cell (in-state, out-of-state target, out-of-state other; one combined target tier of client-defined states) and one out-of-state incentive aimed at the target tier or at all out-of-state, with an optional score floor **[v2.7, V27A-01]**. Per-state tiers, MSAs and ZIP3 are deferred (section 11)."

**B2-2. Price-test verdicts are still stated as current in four places.** Major. Shown, high.
Location: executive read line 114 ("For Richmond's economics the verdict is Not recommended at a ±3% class band"); methodology lines 266, 268 and 1075.
The executive read is the document most likely to be paraphrased to a client. Its status line (line 6) says the verdicts are pending, but the sentence itself is untagged.
Fix: append to each of the four: " **[v2.7, V27-04: computed under the 5% guardrail; pending re-run (O36); do not quote]**". Replace "Richmond's class band (±4 on 140) is about ±2.9%, so the ±3% row is the relevant one" with "Richmond's band of ±4 is ±2.9% at 140 and ±3.6% at 110, so the re-run should report ±3% and ±4% at the target class in use."

**B2-3. The small-cell rule does not cover delivered files, the policy document or public material, and FR-06 still contradicts it.** Major. Shown, high. (Confirms Session A A2-1 to A2-3.)
Location: methodology section 9 (lines 617 to 622) and section 2 (line 38); S1 FR-06 acceptance (line 87, "No cell under 10 in any output"); spec decision (4), D3.
The rule is written for the dashboard's authenticated roles. The Excel workbook goes through a secure channel to named people but cannot authenticate each viewer; the policy document carries awards by cell; marketing and public material are not addressed.
Fix (methodology section 9, new bullets; proposed rule for Jason to confirm with Cat):
- "**Files.** The Excel workbook and the policy lookup file follow the engagement's `small_cell_policy` and go only to the named roles through the secure channel; the cover note names the roles. Under the default policy, the workbook's count columns are suppressed as on the dashboard."
- "**Policy document.** The scholarship policy document carries award amounts by cell, which describe policy, not students. Projected counts by cell appear in it only under the engagement's policy."
- "**Public and marketing material.** Always the default rule (no cell under 10, complementary suppression), whatever the client elects. Client-specific material is not public."
And S1 FR-06 acceptance: "Small-cell policy applied as configured (FR-76); structure matches approved table set; stealth flag present."

**B2-4. Methodology section 5 does not define the target-tier KPIs or the tier yield offset.** Major. Shown, high.
Location: methodology lines 545 to 562; V27A-01 says "target KPIs ... Methodology 5"; S1 FR-77; spec section 3 lines 104 to 106; methodology line 828 mentions "a client-input offset".
The methodology is the declared source of truth, but the target enrolled range, P(goal), cost per incremental target enrollee and paid-anyway share are defined only in the spec. The offset appears only in the limitations.
Fix: add to the evaluator's Ledger list "yield for target-tier cells adds a client-input offset where the tier's own history is too thin (spec section 4)", and add a "Target-tier measures" paragraph that cites the metric definitions appendix proposed in Part B3 (section 4 below), using the corrected formulas from B1-4 and B1-11.

**B2-5. The count rule is tighter at the low end of the class range.** Minor. Suspected (arithmetic on the methodology's own figures), medium.
Location: methodology line 358.
The limit of 21 implies about 630 to 659 projected admits. A shrink to a class of 100 removes about 40 expected enrollees from cells yielding around 0.22, about 180 admits, leaving about 470 and a limit of 15 against 14 parameters. The merge rule rebuilds groups on projected admits, so it adapts, but the "about 13 groups" figure holds at the current class only.
Fix: append "At a class of 100 the limit is about 15; the merge rule is re-run on the projected admits of the scenario in use."

**B2-6.** Minor. Methodology line 612: "reviews the allocation logic, guardrails and floors" reads as the removed per-cell guardrail. Fix: "reviews the allocation logic, the segment floors, the equity audit and the data use".

**B2-7.** Minor. S1 FR-52 (line 164) and its traceability row (line 429): "Enforce the seven existing guardrail tests" and "All 7 existing tests pass" while test 8 is added. Fix: "Enforce the eight guardrail tests (seven existing, test 2 and test 5 as amended, plus test 8, the step-size report)" and "All 8 tests pass". State also that the consumer-module rule "ZIP-level outputs aggregate at least 10 students" is independent of `small_cell_policy`.

**B2-8. The executive read has none of the V27A addendum.** Major. Shown, high.
Location: `01_executive_read_v2.7.md` (no mention of the target tier, the class range or cap, the shrink path, tripwires, net-price readouts or the 5.5% placeholder; `CHANGELOG_v2.7.md` lists it under "Files touched").
Fix: add after line 6: "**[v2.7, V27A] What changed (November 13, 2026).** For Richmond the evaluator gains one combined target-state tier (NY and PA by default) with an incentive aimed at it and an optional application lift; class size becomes a target under a hard cap (140 this cycle; supported 100 to 140) with a shrink path that trims the lowest LSAT bands first; pool tripwires; and display-only net-price readouts. Planning scenarios use a 5.5% tuition increase, unconfirmed until Brandon supplies the figure."

**B2-9.** Minor. S1 FR-74 (line 203) and spec D4 (line 263): "default 6.0% for 2027". Fix: "6.0% for 2027 in reproduce mode".

**B2-10.** Minor. S1 OD-06 (line 491): resolution text predates V27A-01. Fix: append "**[V27A-01]** Partly answered: the evaluator uses one combined target tier (NY, PA); whether the optimizer needs a state or MSA targeted-objective constraint stays open."

**B2-11.** Minor. Shown, high. The data request still asks for the removed guardrail: `efa_fao/docs/data_request_v3/spec/fields.csv` line 139, `aid_policy,guardrail_max_cut_pct` ("Largest cut any group's award may take ... Default 5% if blank", M section 5). Fix: delete the row, or rename it `client_max_cut_pct` with the description "Any limit your policy places on year-over-year award cuts, if you have one. We report against it; we do not impose one." and rebuild the request.

**Stop condition met:** every V27 and V27A item is marked above.

## 4. Part B3: metric definitions

**Sources read.** Methodology v2.7 sections 2, 3, 5, 7 and Appendix D; spec v0.5 sections 2 to 5; S1 v1.2; data request v3 `spec/definitions.csv` and `spec/fields.csv`; `efa_fao/src/efa_fao/pipeline/optimize.py` and `aggregate.py`. "M" = methodology v2.7, "S" = spec v0.5, "DR" = data request v3 spec files. "Not defined" means no document defines it.

### Metric register

| Metric | Definition as written (source) | Numerator | Denominator | Time basis | Dollar basis | External standard | Where defined | Where computed | Consistent? |
|---|---|---|---|---|---|---|---|---|---|
| Applications | "complete and actionable (fee paid or waived) and notified of a decision, or withdrew" (DR definitions, Applicant) | Complete applications | n/a | Cycle total; pacing: "received" to date | n/a | CDS C1; ABA 509 applications | DR definitions; DR fields line 177 | S §9 (reproduce: admits ÷ admit rate); `sw/ledger.py` | **No.** Pacing counts applications "received" (DR line 177), not complete. Reproduce mode cannot recover cells with no admits (S §10). B3-4 |
| Admit rate | admits ÷ applications by cell (S §3 step 3) | Admits incl. waitlist admits (DR Admitted) | Applications | Cohort | n/a | CDS C1; 509 offers ÷ applications | DR; S §3 | `sw/ledger.py`; `aggregate.py` line 25 | Yes |
| Yield | M §2 509 rule: "matriculants from the applicant pool ÷ offers"; S §4: enrolled ÷ admits by cell; `aggregate.py`: enrolled ÷ admits | Enrolled at census | Admits (incl. waitlist admits) | Cohort; census | n/a | ABA 509 | M line 89; S §3, §4 | `sw/response.py`, `ledger.py`; `aggregate.py` | **Partly.** Deferrals undefined: DR asks `actual_entry_cohort`, but no document says whether a deferred admit counts in the application year's denominator or a later year's numerator. B3-6 |
| Melt | "deposit to census is reported as its own stage" (M §2 line 36); "historical deposit-to-census rates" (M §7) | Deposits not enrolled at census | Deposits | Census | n/a | none | M §2, §7 | pipeline (to build) | Yes, but the evaluator has no deposit stage (yield is admit to census, melt included). State it (appendix) |
| Class size | "class = sum enrolled" (S §3 step 6); "Enrolled at the official census date ... reconcile to the matriculants you report to the ABA" (DR) | Enrolled first-year JD at census | n/a | Census | n/a | ABA 509 matriculants (full-time and part-time) | DR; S §3 | `ledger.py` | **Not fully defined.** Whether `class_cap` 140 counts full-time first-years only, part-time, or transfers is not stated. B3-9 |
| Funnel stage conversions (EFA) | "stage-to-stage conversion rates (inquiry → application → admit → deposit → enrolled at census) by cohort and pooled" (S1 FR-06) | Count at next stage | Count at prior stage; stealth applicants excluded from inquiry → application | Cohort | n/a | none | M §2; FR-06, FR-12 | `aggregate.py` lines 20 to 30 | Yes |
| Projected census (pacing) | "current counts by stage × historical stage-to-census conversion rates by days to deadline" (M §7) | Projected enrolled | n/a | "same date last year" (M §7) vs "same week of the cycle" (DR line 175) | n/a | none | M §7; FR-14 | to build | **No** (two time bases). B3-4 |
| LSAT and UGPA medians, percentiles | 509: "describe matriculants, not admits" (M line 88); S §5: median holds when at least half the class is at or above t; unscored rows count as below | Enrolled at or above t | Class (S) vs matriculants with that test score (509, suspected) | Census | n/a | ABA 509 | M §2; S §5 | `risk.py` | **Suspected departure.** B3-3 |
| Median margin and P(median holds) | margin = count at or above t minus count below (S §3, "YA definition") | Signed count | n/a | Census, expected | n/a | none (client's own) | S §3, §5 | `risk.py` | Yes, given B3-3 |
| Share at or above threshold | count at or above t ÷ class (S test 16; Summary) | Expected count at or above t | Expected class | Expected | n/a | none | S §11 test 16 only | `ledger.py`, `trim.py` | **Ratio of expectations, unlabeled.** B3-5 |
| Gross tuition | `class x tuition_s` (S §3 step 8) | Expected class × tuition | n/a | Entering class, year 1 | Tuition only, no fees | NACUBO uses tuition and fees | S §3 | `ledger.py` | **Departure unstated.** B3-2 |
| Merit, need, specialty spend | merit = sum enrolled × award; need = `need_rate` × class, `need_rate` = 200,000 ÷ 140; specialty lump sum (S §3, §2) | Dollars | n/a (need: fixed 140) | Entering class, year 1 | Institutional gift aid | CDS H institutional grants | S §2, §3; M §5 | `ledger.py` | Yes. The fixed 140 is stated (S line 55). The need total is a rate, not a pool: a smaller class spends less need aid; say so (appendix) |
| Discount rate | `aid / gross`, aid = merit + need + specialty (S §3 step 8); `optimize.py` line 69: institutional aid ÷ tuition; M §5: "optional cap on the class-wide discount rate" | Institutional gift aid | Gross tuition | Entering class, year 1 | Tuition only | NACUBO TDS: institutional grant aid ÷ gross tuition **and fee** revenue, first-time full-time and all students | S §3; M line 449 | `ledger.py`; `optimize.py` | **No.** "Class-wide" is undefined; fees excluded; the Dean's "maintain the discount rate" basis is unknown. B3-2 |
| NTR (evaluator) | `gross - aid` (S §3 step 8); "NTR = class × tuition − merit − need − specialty" (M §5 line 550) | | | Entering class, year 1 | Tuition only | none | S §3; M §5 | `ledger.py` | **No: conflicts with the optimizer NTR.** B3-1 |
| NTR (optimizer) | "Expected multi-year institutional net tuition revenue: Σ P(enroll) × (tuition − institutional aid) × persistence" over the commitment horizon (M §5 lines 421 to 440); "Institutional net tuition = tuition and fees minus institutional gift aid" (M line 116) | | | Entering class, three years (law) | Tuition (and fees, line 116) | none | M §3, §5 | `optimize.py` lines 28 to 29 (tuition only, multi-year) | **No.** B3-1 |
| Net price (readout) | "net price at 2026 tuition T26 − A; at scenario tuition Ts − A" (S §3) | Tuition − merit award | n/a | Rung, year 1 | Tuition only; merit only | IPEDS net price is COA minus all grant aid, for first-time full-time undergraduates; M line 115 "net cost = COA minus gift aid" | S §3 | `netprice.py` | **Name collides with IPEDS and M's "net cost".** B3-13 |
| Average aid | `aid / class` (S §3) | Aid | Class | Expected | Institutional | none | S §3 | `ledger.py` | Ratio of expectations (B3-5) |
| Full-tuition, full-pay, barbell | full-tuition = award ≥ tuition; full-pay = award of zero; barbell = (full-tuition + full-pay) ÷ class (S §3) | | Class | Expected | Merit only | none | S §3 | `ledger.py` | **"Full-pay" ignores need aid**, which is not assigned to cells. B3-7 |
| Price of the target | Baseline NTR minus scenario NTR (S §3) | | n/a | Year 1 | Year-1 NTR | none | S §3 | `ledger.py` | Yes (inherits B3-1) |
| Out-of-state share | Residency "at application, from the known physical address" (DR definitions); target state "State of the permanent address at application" (DR line 169) | Out-of-state enrolled | Class | Application | n/a | none (509 has no residency) | DR | `ledger.py` | **Two address bases.** B3-10 |
| Target-tier enrolled and share | `E_T`; target share of class (S §3) | Expected target enrolled | Expected class (share) | Expected | n/a | none | S §3 only | `ledger.py` | Defined only in spec (B2-4); share is a ratio of expectations |
| P(E_T ≥ goal) | `1 - Phi((goal - 0.5 - M_T)/sqrt(V_T))` (S §3) | | | Expected | n/a | none | S §3 | `risk.py` | Approximation flag missing (B1-8); empty tier (B1-14) |
| Cost per incremental target enrollee | `dSpend / dE` vs parent (S §3) | Change in merit dollars in target cells | Change in expected target enrolled | Year 1 | Merit (base and incentive) | none | S §3 only | `ledger.py` | **Population and sign rules incomplete** (B1-11) |
| Paid-anyway share | `min(1, E_T(p)/E_T(s))` (S §3) | | | Year 1 | Incentive dollars | none | S §3 only | `ledger.py` | **Wrong** (B1-4) |
| P(class > cap), P(class within band) | S §5 closed forms | | | Census, expected | n/a | none | S §5; M §5 | `risk.py` | Yes |
| P(NTR ≥ target) | S §5 | | | Year 1 | Year-1 NTR | none | S §5 | `risk.py` | Inherits B3-1 |
| Pool multiplier and pool growth to date | multiplier on 2026 applications at LSAT ≥ 165 (S §3 step 2); `pool_ytd_growth_pct`: "annotation ... the current high-LSAT application growth Richmond reports" (S line 66) | Applications (165+) | 2026 applications (165+) | Final pool (multiplier) vs to date (annotation) | n/a | none | S §2, §3 | `tripwire.py` (annotation only) | **No.** Population (score basis, received or complete), comparison week and baseline are undefined; to-date growth is not final growth. B3-4 |
| Award gap against the market | Appendix D rank-matching on 509 grant percentiles (all full-time students, prior academic year, recipients only) | Peer share of tuition − own share | n/a | 509 report year − 1, normalized to current tuition | Institutional grants | ABA 509 | M Appendix D, §2 | to build (`Market` sheet out of scope) | **Yes on the field reading** (B3-11 minor) |
| Evidence share | share of enrolled in `extrapolated` cells (S §4) | Expected enrolled in extrapolated cells | Expected class | Expected | n/a | none | S §4 | `ledger.py` | Yes |
| Incentive cost | `sum enrolled × (award - award_base)` (S §3 step 7) | Dollars | n/a | Year 1 | Incentive after cap | none | S §3 | `ledger.py` | Yes |
| Step sizes | award difference between adjacent LSAT bands within residency × GPA class (S §6 Distribution) | Dollars | n/a | Scenario | Award | none | S §6; M §5 | `workbook.py` | Yes |

### Findings

**B3-1. NTR is defined two ways, and the documents claim the optimizer and ledger give the same NTR.** Blocking for the S5 integration (not for Phase 1). Shown, high.
Location: M §5 Objective (lines 419 to 440: multi-year with persistence over the commitment horizon); M line 116 ("tuition and fees minus institutional gift aid"); M §5 evaluator (line 550: one year, tuition only); M line 554 and spec §15 item 1 ("The optimizer's projected class, spend and NTR for any grid equal the ledger's"); S1 FR-31 acceptance (V27-23: "optimizer and ledger give identical class, spend and NTR"); `optimize.py` lines 66 to 67 (both `ntr_year1` and `ntr_multi_year`).
The equality cannot hold as written, and fees are in one definition only.
Fix: name them `ntr_y1` (entering class, first year, tuition only, after institutional gift aid) and `ntr_horizon` (entering class over the award commitment, with persistence and the renewal rule), state both in the metric appendix, and restate the equality as "the optimizer's `ntr_y1`, class and year-1 spend for a grid equal the ledger's; `ntr_horizon` equals the `MultiYear` sheet's when it is built." Fees: exclude them everywhere (mandatory fees are not discounted at Richmond as far as the documents show) and edit M line 116 to "tuition minus institutional gift aid; required fees are reported separately".

**B3-2. The discount rate departs from NACUBO without saying so, and "maintain the discount rate" has no stated basis.** Major. Shown (documents), high; the Dean's meaning is Suspected, medium.
Location: S §3 step 8; `optimize.py` line 69; M line 449 ("class-wide discount rate"); S1 OD-05 (Dean, Nov 13: "the five-year plan is to maintain the discount rate").
The documents compute entering-class, first-year aid over tuition without fees; NACUBO divides institutional grant aid by tuition and fee revenue, for first-time and for all students. A dean speaking of a five-year plan most likely means the all-JD budget rate (judgment; ask Brandon). The two diverge: with fixed-dollar renewals and 5.5% increases, the 2L and 3L discount falls each year on its own.
Fix: define `discount_entering_y1` (what the ledger computes, labeled "entering class, first year, tuition only, institutional aid") and, when `MultiYear` exists, `discount_all_jd`. Add to OD-05: "Which discount rate: entering class or all JD students, with or without fees?" Until answered, the Summary label reads "Discount rate (entering class, first year)".

**B3-3. The median and percentile basis may depart from ABA 509 for students without an LSAT or UGPA.** Major. Suspected, medium (I did not read the ABA 509 instructions; Jason or counsel should check).
Location: S §5 ("unscored rows count as -1"); S §2 line 52 (GRE, JD-Next and no-score rows supported); GPA `g_c = +1` for class `hi` only, so blank GPA counts as below; M line 88.
If 509 percentiles are computed among matriculants with that test (my understanding; GRE-only matriculants are counted separately), counting unscored enrollees as below makes P(median holds) conservative. The tie rule may also differ for an even-sized class.
Fix: "Medians are computed as the ABA 509 does: LSAT percentiles over matriculants with an LSAT (highest score), UGPA percentiles over matriculants with an LSAC UGPA. Unscored rows are excluded from both terms of the margin and reported as a count." Keep the current conservative rule as an option (`unscored_in_median: below | excluded`, default `excluded`) if Jason prefers it, and say which is in use on the Summary.

**B3-4. Pacing, pool growth and the data request use different populations and time bases.** Major. Shown, high.
Location: DR fields line 173 (`early_funnel_by_state.deposits`: net of withdrawals by census) vs line 179 (`early_pacing.deposits_cumulative`: gross deposits received); line 177 (`applications_cumulative`: "received") vs the Applicant definition (complete and actionable); M §7 ("against the same date last year") vs DR line 175 (same week of the cycle); S line 66 (`pool_ytd_growth_pct`) vs S §3 step 2 (multiplier on final 2026 applications at LSAT 165 and above); Session A A1-9 (the baseline of Richmond's "up 60%" is unknown).
The tripwires set a final-pool multiplier beside to-date growth of undefined basis, which overstates final growth when applicants file earlier.
Fix: in the DR, rename `deposits` in `early_funnel_by_state` to `deposits_net_of_withdrawals` and state that the pacing count is gross; ask for `applications_cumulative` as complete applications, with an LSAT band column so 165-and-above growth can be computed. In the spec, define `pool_ytd_growth_pct` as "growth in complete applications at LSAT ≥ `pool_threshold_lsat`, this cycle against the mean of the prior two cycles at the same week of the cycle", shown with the label "growth to date; final growth may differ if applicants file earlier or later than last year". In M §7, change "same date last year" to "same week of the cycle (week counted from the application open date)".

**B3-5. Ratios of expectations are presented without saying so.** Major. Shown, high.
Location: S §3 (discount = aid ÷ gross; average aid; barbell index; target share; paid-anyway share); S test 16 (share at or above); S §6 `Static_MC` (simulated class, NTR, P(median) at 20,000 draws).
If `Static_MC` or the dashboard reports a mean of simulated ratios, it will differ slightly from the Summary.
Fix (spec §3, after the KPI list): "Ratios (discount rate, average aid, shares, barbell index, paid-anyway share) are ratios of expected values, E[X] ÷ E[Y], everywhere, including `Static_MC`, which reports the ratio of simulated means. Each is labeled 'ratio of expected values' in the README."

**B3-6. Yield does not say how deferrals and waitlist admits are counted.** Major. Suspected, medium.
Location: S §4 (yield = enrolled ÷ admits); M line 89 (509 yield); DR definitions (Admitted includes waitlist admits; Deferral: send the actual entry cohort).
Fix: "Yield for cohort Y = enrolled at census in Y among admits of cohort Y ÷ admits of cohort Y (waitlist admits included). An admit who defers counts as a non-enrollee in Y and is not added to Y + 1's numerator; deferred entrants are reported separately so the class reconciles to 509 matriculants." Jason to confirm against how Richmond's 509 yield is computed.

**B3-7.** Minor. "Full-pay" (S §3) counts enrollees with no merit award, but need aid is a flat rate on every enrollee and is not assigned to cells. Fix: rename "no merit award" (and the barbell index's text accordingly).

**B3-8.** Target-tier KPIs: see B1-4, B1-11 and B2-4.

**B3-9. Class size has no population definition.** Major. Shown, high.
Location: S §2 (`class_cap`, `class_size`); DR Enrolled definition; DR `enrollment_load`, `Entrant type`.
Fix: "Class: first-year JD entrants enrolled at the census date, full-time and part-time (as on the 509), excluding transfers and visiting students; `class_cap` and `class_size` use the same population. Richmond to confirm whether the cap of 140 counts part-time entrants."

**B3-10.** Minor. Residency ("known physical address at application") and the target-state field ("permanent address at application") use different words for what should be one address. Fix: use "permanent address at application" in both and say the residency and state come from the same field.

**B3-11.** Minor. Appendix D reads the 509 fields correctly (all full-time students, prior academic year, recipients-only percentiles; the v2.5 field rules hold). Two gaps: the illustration compares dollar grants before the step 4 normalization (Wake Forest's and Richmond's grant years carry different tuition), and for public peers the tuition used to normalize (resident or nonresident) is not stated. Fix: show the illustration in shares of tuition; add "public peers: normalize by nonresident tuition for out-of-state positions and resident tuition otherwise; flag the peer".

**B3-12.** Minor. The need total is a per-enrollee rate (S line 55), so a smaller class spends less need aid. A CFO may read "$200,000" as a fixed pool. Fix: label the Inputs cell "Need aid: $200,000 at a class of 140 ($1,429 per enrollee; scales with class)".

**B3-13.** Major. Shown, high. "Net price" in the spec (tuition minus merit award) collides with IPEDS net price (cost of attendance minus all grant aid, undergraduates) and with the methodology's own "net cost" (M line 115). Fix: rename the readout "net tuition after merit award" throughout spec §3, FR-80 and the Summary.

### Proposed "Metric definitions" appendix (proposed only; not applied)

One line per metric. Every client-facing figure cites this list by name.

1. **Application:** complete and actionable application to the JD program (CDS and 509 basis); pacing counts the same, cumulative to the week of the cycle.
2. **Admit:** offer of admission, including from the waiting list, counted in the cohort applied to.
3. **Admit rate:** admits ÷ applications, by cell and cohort.
4. **Enrolled (class):** first-year JD entrants at the census date, full-time and part-time as on the 509, excluding transfers; equals 509 matriculants.
5. **Yield:** enrolled at census in the cohort ÷ admits of the cohort; deferrals count as non-enrollees in the year applied and are reported separately.
6. **Deposit (gross):** first enrollment deposits received; **deposit (net):** deposits not withdrawn by census; **melt:** 1 − enrolled ÷ gross deposits.
7. **Class cap / class target:** a hard upper bound / the planned class, both on the enrolled population above.
8. **LSAT and UGPA percentiles:** as on the 509 (highest LSAT; LSAC UGPA; over matriculants with that measure); unscored matriculants are counted separately.
9. **Median margin at t:** enrolled with a score at or above t minus enrolled with a score below t; P(median holds) = P(margin ≥ 0).
10. **Share at or above t:** expected enrolled at or above t ÷ expected enrolled with a score (ratio of expected values).
11. **Gross tuition (year 1):** enrolled × published first-year tuition; fees excluded and reported separately.
12. **Merit, need, specialty spend (year 1):** institutional gift aid to the entering class in its first year; need is a fixed rate per enrollee.
13. **Discount rate (entering class, year 1):** (merit + need + specialty) ÷ gross tuition (year 1), ratio of expected values; differs from NACUBO (which includes fees) and from an all-JD rate.
14. **NTR (year 1):** gross tuition − merit − need − specialty, entering class, first year.
15. **NTR (horizon):** entering-class NTR over the award commitment (three years for JD), with persistence and the recorded renewal rule.
16. **Net tuition after merit award:** published tuition − merit award, by award rung; not IPEDS net price.
17. **Out-of-state share / target tier:** by the permanent address at application; target tier = client-listed states.
18. **Target-tier enrolled (E_T):** expected enrolled in target-tier cells; P(E_T ≥ goal) with the goal rounded up.
19. **Incentive cost:** Σ enrolled × (award after incentive and cap − award before incentive).
20. **Cost per incremental incentive enrollee:** change in merit dollars ÷ change in expected enrolled, over cells receiving the incentive, against a parent that differs only by the incentive.
21. **Paid-anyway share:** Σ min(parent enrolled, scenario enrolled) × incentive per enrollee ÷ incentive cost, over cells receiving the incentive.
22. **Pool multiplier:** final complete applications at LSAT ≥ the pool threshold ÷ the same in the base cycle; **pool growth to date:** the same ratio at the same week of the cycle against the mean of the prior two cycles.
23. **Market award gap:** Appendix D rank-matched peer grant share minus own share, median across the approved peer set, in shares of current tuition.
24. **Evidence share:** expected enrolled in cells whose award is outside the observed range ÷ expected class.
25. **Step size:** award difference between adjacent LSAT bands within residency × GPA class.

**Stop condition met:** every metric the brief lists is in the register with every column filled or marked.

## 5. Part B4: statistical and methodological fitness

**Scale assumed.** Up to 10 clients; three to five cycles each; law about 650 admits and 140 enrollees a cycle (M §10 W0L), undergraduate a few thousand admits; fine cells mostly under 10 admits (S §10). Checks in `review_support_v0.5/b4_checks.py` (synthetic numbers).

### Verdict by method

| Method | Verdict | One line |
|---|---|---|
| EFA funnel projection (pacing lookup by days to deadline, M §7, FR-14) | Fit with conditions | Right tool; the "interval from prior-year spread" rests on two prior cycles and cannot be estimated; use the shock term instead (B4-4) |
| Yield forecast (regularized logit, about 10 to 12 features) | Fit | About 2,000 admits and 400 enrollees over three law cohorts supports 10 to 12 terms; the stability and release thresholds are too tight for law size (B4-3) |
| Boosted-tree challenger (M §11, FR-64) | Simpler alternative recommended (law) | With about 400 events per client there is little room for a tree to beat a regularized logit; keep for undergraduate, drop for law |
| One logit slope | Fit | Defensible given the v2 backtest; the evaluator uses it only as a client-input placeholder until an anchor exists |
| Design-based anchors (randomized bonus test, merit-grid discontinuity, qualifying policy change) | Fit; not available to Richmond in 2027 | Richmond has no published merit grid (M §10 W0L) and no test, so year 1 runs with no anchor; the 2025 barbell change (OD-01) is the only candidate |
| Value-of-information screen | Fit with conditions; simpler alternative for year 1 | Verdicts pending O36. At law size a power and break-even table leads to the same "not now" decision far more cheaply; defer O36 until a client contemplates a test (B7) |
| Position bands as the main moderator | Fit with conditions | Sound for the optimizer; the evaluator uses the client's LSAT × GPA cells instead, so the product carries two academic schemas (B5, B7) |
| Class and median risk (closed form vs simulation) | Fit with conditions | Validated within 0.01; rests on an uncalibrated common shock that also hides segment-level shocks from the median (B4-1, B4-2) |
| Small cells and pooling (base-yield fallback at 5 admits) | Simpler alternative recommended | Replace the hard threshold with partial pooling: one formula, no discontinuity, fixes B1-2 (B4-5) |
| Optimizer (LP on the decision layer, two-sided choice rule, weak-evidence state) | Fit; not used by Richmond in 2027 | With no anchor the output is the documented status-quo grid by rule; the evaluator is the 2027 deliverable |
| Monte Carlo gates and seeds | Fit with conditions | No world has a year-level shock, so the W0L class-coverage gate cannot detect understated class variance (B4-1); runtime about 4,300 seeds per release (B7) |
| Synthetic worlds and recovery tests | Fit | The confounding trap is planted and recovered against; W0L is calibrated to one client (B5) |
| Backtesting across cycles | Fit with conditions | One out-of-time cohort is a single draw; the evaluator needs its own forecast-against-actual record each cycle (B5) |

### Answers to the six questions

| Question | Answer |
|---|---|
| 1. Year-level shocks | Included in the evaluator (s = 0.10, common to every cell; O37 open), so the class is not treated as independent. s cannot be calibrated from one client: with true s = 0.10, three cycles give an estimate between 0.000 and 0.175 (10th to 90th percentile) and zero 30% of the time; five cycles 0.000 to 0.157 (`b4_checks.py` item 2). Segment-level shocks are assumed away (B4-1, B4-2) |
| 2. Thin data | Fallbacks written for the anchor, forecast, cells and position bands; none for s, the pacing interval or the target-tier share before state counts (B4-1, B4-4, B6) |
| 3. Placeholders | Consistent for award-driven outputs; nothing labels outputs that depend on s, and the label would drop off shifted scenarios once an anchor exists (B4-6) |
| 4. Normal approximation | Adequate for class and NTR (0.01 on the fixture; 0.0075 on a toy class of 27); not for small target tiers (B1-8). In the tails the uncalibrated shock, not the approximation, dominates (B4-7) |
| 5. Causal claims | Confounding is handled well in the methodology (observational model not a price source; driver layer labeled associational; trap planted in the worlds). The evaluator's incentive KPIs and the lift's "accountable for" framing read as causal (B4-8) |
| 6. Interval consistency | Not consistent: 90% outcome ranges, placeholder Low and High cases, 10th to 90th slope percentiles and 95% CIs all appear as "ranges" (B4-9) |

### Findings

**B4-1. The common-shock SD drives the headline risk figures, cannot be calibrated per client, and no synthetic world tests it.** Major. Shown (simulation and arithmetic), high.
Location: S §2 line 56 (s = 0.10, illustrative); S §5; M §5 line 556, §6 line 576; O37; M §10 (no world with a year-level shock; W0L class gate "realized class inside the projected 90% interval in ≥ 85% of seeds").
With s = 0.10 the class SD at an expected class of 140 is about 17.5 rather than about 10.5 from enrollment noise alone, so s sets P(class > cap), the upside tripwire and the goal-seek ceiling (at p* = 0.80 goal-seek holds the expected class near 127 rather than 132 under a cap of 140). Because the synthetic worlds have no year shock, the W0L coverage gate passes whether s is right or not.
Fix (methodology §6 and O37): "s is calibrated from public data, not from one client: for law, the year-over-year change in each school's 509 yield (matriculants ÷ offers), detrended, with binomial noise removed, among schools of similar size; for undergraduate, the same from IPEDS admissions data. A client's own out-of-time forecast errors replace it only after five cycles, combined by inverse variance. Add world W22: a year-level multiplicative yield shock with SD 0.05, 0.10 and 0.15, under which the W0L class-coverage gate must hold." This uses public data only and mixes no client's data.

**B4-2. Segment-specific year shocks would widen the median probability; the single common shock assumes them away.** Major. Shown (arithmetic), medium.
Location: S §5 ("The common shock is not added here"); M §5 line 556.
If the shock to admits at or above the threshold has correlation ρ with the shock below it, the margin's variance gains 2 s^2 G^2 (1 − ρ) near the median. At s = 0.10, margin +4: P(median holds) is 0.666 at ρ = 1, 0.653 at 0.8, 0.639 at 0.5 and 0.622 at 0; at margin +10: 0.840, 0.820, 0.797, 0.766 (`b4_checks.py`, item 1). High-LSAT admits face the most competitive market, so ρ < 1 is plausible.
Fix: add `shock_corr_above_below` (default 1.0, which reproduces today's figures) to the config and the median variance `V_m = sum v_c + s^2 (G_+^2 + G_-^2 - 2 rho G_+ G_-)`, with G_+ the expected count at or above t and G_- the count below; show P(median holds) at ρ = 0.5 as a sensitivity line labeled "if high-score and other admits' yields move differently year to year".

**B4-3. Forecast stability and release thresholds will fail a correct model often at law size.** Major. Shown (simulation), medium.
Location: M §4 Response model ("unstable if γ is outside [0.8, 1.2]"); M §7 batch scoring release criterion 1 (slope in [0.85, 1.15]).
At 650 admits and 21% yield the sampling SD of the calibration slope is about 0.14. A correctly specified model falls outside [0.8, 1.2] in 16% of cohorts and outside [0.85, 1.15] in 29% (`b4_checks.py`, item 3).
Fix: "Unstable (or fail) when the 90% confidence interval of γ excludes the band [0.8, 1.2] (release: [0.85, 1.15]); report γ with its interval. At fewer than 1,500 admits per cohort, pool two cohorts for the check."

**B4-4. The pacing interval cannot be estimated from two prior cycles.** Major. Suspected, medium.
Location: M §7 Projected census ("an interval from prior-year spread and binomial noise"); DR `early_pacing` (current and prior two cycles).
A spread from two values is not an interval. Timing shifts (applicants filing earlier) also bias same-week comparisons, which is what Richmond's in-cycle "up 60%" may reflect (Session A A1-9).
Fix: "Projected-census interval: binomial noise plus the year-level shock s (B4-1); prior-cycle spread is shown as a check, not used, until five cycles exist. Pacing ratios are reported beside the share of the prior cycles' final applications that had arrived by the same week, so a timing shift is visible."

**B4-5. Replace the hard base-yield fallback with partial pooling.** Major (simplification with better statistics). Suspected (reasoned), medium.
Location: S §4 lines 122 and 130; S §10 (about 45% to 55% of active cells under 10 admits).
A cell with 5 admits over three cohorts has a yield SE near 0.18 yet uses its own history in full, while a cell with 4 uses none of it. The threshold also breaks tier invariance (B1-2).
Fix: "y0_c = (n_c ybar_c + k ybar_pool) / (n_c + k), with n_c the cell's three-cohort admits, ybar_pool the (market tier, LSAT group) pool yield (or the residency pool when the tier pool has fewer than 30 admits), and k = 20 by default (set from the between-cell variance when it can be estimated)." One formula in Python and Excel. Tier invariance then holds approximately rather than exactly; test 13 bypasses y0 as B1-2 proposes.

**B4-6. Two placeholder kinds are not labeled apart.** Major. Shown, high.
Location: S §4 (`RESPONSE_LABEL`, one constant); M §5 Labels ("after which the label names the evidence status"); S §2 (shift, lift, offset "labeled Response based on client-input"); S §2 line 56 (s illustrative; no output label).
Once an anchor exists, scenarios with a yield shift, lift or offset still rest on client input, and every probability and interval rests on s.
Fix: keep `RESPONSE_LABEL` for the slope, and add `ASSUMPTION_LABEL` = "Includes client-input assumptions (yield shift, application lift, tier offset)" for any scenario where one is non-zero, whatever the evidence state; and `SHOCK_LABEL` = "Year-to-year variation assumed (s = 0.10), not yet calibrated" beside every probability and interval until O37 closes.

**B4-7.** Minor. Show probabilities below 5% or above 95% as "under 5%" or "over 95%" while s is uncalibrated; clip target-tier 90% ranges at zero and flag them when M_T < 20.

**B4-8. The lift is framed as marketing accountability without a comparison.** Major. Suspected, medium.
Location: S line 62; D17; FR-74.
Growth in NY and PA applications includes national trends and Richmond's general pool growth, which the pool multiplier already carries. Crediting the lift to marketing is a causal claim the workbook cannot support.
Fix: replace the sentence with "`target_pool_lift_pct` is target-tier application growth beyond the pool multiplier. When state-level pacing arrives, the reported figure is target-tier growth minus other out-of-state growth at the same week, which removes the shared trend; it is still not a causal estimate of marketing." Also check the public national applicant volume trend (LSAC) before attributing Richmond's high-LSAT growth to anything Richmond did.

**B4-9. Interval types are not named consistently.** Major. Shown, high.
Location: S §3 and §5 (90% outcome intervals; L, M, H placeholder slopes); M §6 (L, M, H = 10th, 50th, 90th slope percentiles); M §6 forecast interval (calibration error plus binomial); M §10 (95% anchor coverage); roadmap §4 design constraint.
Fix (metric appendix and README): "Every range is one of three kinds and says which: (1) 90% outcome range (enrollment noise and year-level variation, at the Middle case); (2) the Low and High price-response cases (placeholder slopes 0.5 and 1.5 until an anchor exists; then the 10th and 90th percentiles of the slope); (3) a 95% confidence interval for an estimated parameter. Kinds 1 and 2 are never combined into one range. The pipeline's class interval and the evaluator's use the same method once O37 closes."

**Stop condition met:** every method has a verdict; findings cover each one not plainly fit.

## 6. Part B5: generality, multiple years, reproducibility

### 6.1 Hard-coding sweep

Searched spec v0.5, methodology v2.7, S1 v1.2, roadmap v2.7, `efa_fao/config/institution.yaml`, `efa_fao/sql/schema.sql` and `efa_fao/src/`. Mentions of Richmond figures as worked examples or records of decisions are not counted.

| Item | Where | Class | Note and fix |
|---|---|---|---|
| 140 (class cap, need denominator) | S §2 defaults (lines 54, 55), D5 | Client config, but a Richmond value set as the product default | Move to `config/richmond.yaml`; the product schema has no default (required input) |
| Class range 100 to 140; reject outside 90 to 150 | S §2 line 54, test 18, handoff | **Hard-coded** | A law school of 300 or a college of 1,500 is rejected. Fix: `supported_range` and `reject_range` in client config, default `[0.7, 1.0] x class_cap` and `[0.6, 1.1] x class_cap` |
| 165 (pool threshold), 166 and 165 (median thresholds), 154 (floor), 3.83 (GPA) | S §2 lines 52, 53 | Client config (Richmond values as defaults) | Same: required inputs, no product default |
| NY, PA | S §2 line 61, D9, D13; M line 361 | Client config (default in product) | Remove the product default |
| $59,900, $63,500 | S §9 (fixture layout), S §2 tuition example | Fixture text, fine | |
| $200,000 need pool | S §2 line 55 | Client config | |
| 6.0% reproduce, 5.5% planning | S §2, D4; M §5 | Client config (Richmond) | Fine as labeled |
| Pool multipliers 1.30, 1.50; $10,000 NY/PA lump sum | S §9 only | Fixture text, fine | |
| Three-year renewals | M §5 Horizon | Vertical config (law), declared | Fine |
| LSAT in names: `lsat_lo`, `lsat_bands`, `floor_lsat`, `pool_threshold_lsat`, `order: lsat_then_gpa`, "LSAT group", median "LSAT" | S §2, §3, §4, §5; cell file | **Hard-coded (vertical)** | An undergraduate client has SAT, ACT, an academic index or no test. Fix: `score_lo`, `score_bands`, `score_measure: LSAT` in config; GPA likewise `gpa_measure` |
| Base year in names: `tuition_2026`, `apps_c,2026`, `T26`, "growth over 2026", `year` default 2027, `tuition_increase_by_year` 2027 to 2031 | S §2, §3 | **Hard-coded (cycle)** | Year 2 breaks every name. Fix: `base_cycle`, `plan_cycle`, `tuition_base`, `apps_base`, `T_base`, growth "over the base cycle" |
| `out_target`, `oos_bonus_*`, "target states" | S §2, §3, §6 | **Hard-coded (use case)** | Geography-specific; see 6.3 |
| `need_rate` flat per enrollee | S §2, §3 | **Hard-coded (vertical)** | Fits law (Richmond's need is small); not undergraduate, where need aid varies by need band |
| Single `tuition_s` | S §3 | **Hard-coded** | Publics charge by residency. Fix: `tuition_by_residency` (optional) |
| `richmond_like.yaml` | S §1 | Client config name, fine | |
| `LEVELS_K = 0..12` ($1,000 to $12,000 ladder) | `optimize.py` line 16 | **Hard-coded** | Law ladder is $2,500 steps to tuition (M §5); move to config |
| Merit grid duplicated as `GRID` | `models.py` line 159 | **Hard-coded** | Read from config |
| EFC categories at $14,000 | `prepare.py` line 94 | Hard-coded (undergraduate) | Config |
| `max_cut_per_student_k: 3` guardrail | `institution.yaml` line 25; `optimize.py` lines 17, 33 | **Removed decision still in code** | Delete with the S6 work (change list F) |
| `min_cell_size >= 10` check | `schema.sql` line 16; suppressed-row check line 78 | **Hard-coded rule** | Conflicts with Richmond's policy (Session A A2-4); replace with `small_cell_policy` |
| Scenario IDs in `leadership_scenarios` view | `schema.sql` (view) | **Hard-coded** | Use a `is_headline` flag on scenarios |
| `app_role` enum lacks `aid_office` | `schema.sql` line 7 | Known (V27-31) | |

**The mockup in `efa_fao/src/`.** It survives in part:

| Component | Survives? | What must change |
|---|---|---|
| `run_pipeline.py` orchestration and run manifest (config and data SHA-256 in `model_run.json`) | Yes | Add environment lock hash and git commit |
| `models.py` logit fitting with clustered SEs | Yes (forecast model) | Remove the hard-coded grid |
| `prepare.py`, `validate.py` (leakage and timing checks) | Mostly | Vertical-specific need categories to config |
| `aggregate.py` funnel tables | Yes | Suppression from `small_cell_policy`; complementary suppression only under the default |
| `optimize.py` | **No.** It chooses an award per student by MILP, which the closed decision "no per-student optimization (the policy grid and lookup replace it)" rules out, and it carries the removed guardrail | Rewrite as the decision-layer LP; its `evaluate()` must call the ledger |
| `synth/` (undergraduate "Lakeshore" world) | As W0 only | W0L is still to build |
| `config/institution.yaml` | **Cannot carry a law client**: no score scale, bands, residency tiers, class cap or target, need rate, renewal rule or market tier; `tuition_fees` merges tuition and fees | Replace with the schema in 6.2 |

### 6.2 Configuration model

Today client-specific items live in five places: `richmond_like.yaml` (spec, not built), `scenarios.yaml` (spec), `institution.yaml` (mockup, undergraduate only), the `institutions` and `engagements` tables (privacy and phase), and CLAUDE.md (Richmond policies: small cells, 5.5%, target states). There is no single schema.

**Proposed minimal schema (proposed only).** One file per client per cycle, versioned and hashed into every run.

```yaml
client:      {id, name, vertical: law | ug, small_cell_policy: default | none, roles: [...]}
cycle:       {base_cycle: 2026, plan_cycle: 2027, history: [2024, 2025, 2026]}
academic:
  score:     {measure: LSAT | SAT | ACT | index, bands: [...], unscored: excluded | below}
  gpa:       {measure: UGPA | HSGPA, classes: {hi: 3.83}}
  thresholds: {median: [166, 165], floor: 154, pool: 165}
cells:       {dimensions: [residency, segment, score_band, gpa_class]}   # ug adds need_band
segments:    [{name: target_states, within: {residency: out}, members: [NY, PA]}]
price:       {tuition_by_year: {...}, by_residency: false, fees: {...}, rounding: 50,
              award_renewal: fixed | percent, commitment_years: 3,
              need: {mode: flat_rate | by_cell, total: 200000, reference_class: 140}}
class:       {target: 140, cap: 140, band: 4, supported: [100, 140]}
objectives:  [{kpi: class, cap: 140}, {kpi: median_margin, measure: score, t: 166, p_star: 0.8},
              {kpi: segment_enrolled, segment: target_states, goal: null},
              {kpi: discount_entering_y1, max: null}, {kpi: ntr_y1, min: null}]
risk:        {common_shock_sd: 0.10, shock_source: illustrative | public | client, shock_corr: 1.0}
data_flags:  {state_counts: false, pacing: false, need: false, price_test: false, anchor: none}
```

Scenario files stay as in spec §2, with `oos_*` and `*_target` fields renamed to segment terms.

### 6.3 Priorities without new code (three-client walkthrough, on paper)

| | Richmond (law: geography, smaller class, LSAT) | Private undergraduate (NTR under a discount cap) | Public undergraduate (yield among in-state admits) |
|---|---|---|---|
| Levers | Admit rates, awards (schedule), pool multiplier, tuition, class target and cap, incentive to target tier, lift, shift | Awards by academic band × need band × residency, admit rates, tuition, shift | Awards by band × residency, admit rates, in-state incentive, shift |
| KPIs | Class, P(class > cap), median margin and P(median holds), target-tier enrolled and P(goal), incentive KPIs, NTR (year 1), discount | NTR over four years with renewals, discount (NACUBO, with fees, first-time and all), P(discount ≤ cap), class | In-state enrolled, in-state yield, P(in-state ≥ goal), class, NTR |
| Sheets and views | All of spec §6; dashboard views 2 and 3 | Inputs, Levers, Ledger, Summary, MultiYear, Distribution | Inputs, Levers, Ledger, Summary |
| Works as specified | Yes | Ledger, class risk, tuition what-if | Ledger, class risk |
| New code needed | None beyond the B1 fixes | Score-generic names; need aid by cell (not a flat rate); fees in the discount; P(discount ≤ cap) closed form (discount ≤ c is linear: Σ (award + need − c × T) × enrolled ≤ 0, so it takes the NTR form); `MultiYear` with four-year renewals | Score-generic names; tuition by residency; an **in-state** priority segment, which `out_target` and `oos_bonus_scope` cannot express |

**The priority-segment question.** The target-state tier is one instance of a client-defined priority segment: a set of cells with an optional goal, incentive, application lift and yield offset. Naming it generally (`segment` column; `segments:` in config; `bonus_scope: segment | residency_out | none`; `segment_pool_lift_pct`) costs nothing before Phase 1 starts, keeps D13 exactly (one combined segment for Richmond, part of the foundational cell schema), and lets the public client's in-state priority and a program or region priority run without new code. Limits: a segment must be a union of cells. Student attributes that cut across cells (first-generation, Pell) need a cell dimension, which raises the cell count and triggers the proxy screen and equity audit (M §9). **Recommendation: rename before the Phase 1 build; one segment per scenario for now.** What would change this: a client asking for two overlapping priority segments at once.

### 6.4 Multiple years

| Check | Status | Where |
|---|---|---|
| Data stored by cycle, with snapshots and versions | Partly: `model_runs` are immutable, versioned by `live_cohort` with config and data hashes (`schema.sql` lines 48 to 66); the scenario workbook has no store | schema; S §6 RunLog |
| Re-estimation when a new cycle arrives | Stated once: roadmap phase 7 "refit each cycle" (line 130) | roadmap |
| Prior-year estimates as priors | Anchor: pooled over cycles with disagreement rules (M §4); moderators need two cycles; no rule for the forecast or for s | M §4 |
| Forecast-against-actual reconciliation each cycle | Partly: one out-of-time backtest per engagement (M §6); **nothing compares last year's adopted scenario with what happened** | — |
| Policy changes as evidence | Yes: `policy_changes` log, qualifying policy change criteria (M §4), O39 | M §4, §5 |
| Multi-year renewals in NTR | Optimizer yes (commitment horizon, persistence, renewal rule); evaluator no (year 1; `MultiYear` stub) | M §5; S §6 |
| MultiYear and Trajectory | Stubs (Phase 4), Trajectory in Phase 5 | S §12 |
| Written annual cycle | **None** | — |

**Proposed minimum annual cycle (proposed only).**
1. **After census (October):** load census actuals; run the calibration report: last cycle's adopted scenario (class, medians, NTR, discount, segment enrolled) against actuals, with each miss shown against its 90% range; add the client's forecast error to the s record; log any policy change as a candidate qualifying change.
2. **Before the cycle (November to December):** roll `base_cycle` forward; refresh 509 or IPEDS reference data; refit the forecast; re-run the evidence audit; freeze and hash the cycle config; build the first workbook.
3. **In cycle (January to May):** weekly pacing loads; tripwire check against pool growth to date; every scenario revision saved as a new versioned run.
4. **Award decisions:** the adopted scenario is marked and frozen; it is what step 1 compares next year.

### 6.5 Reproducibility

| Check | Status |
|---|---|
| Seeds | Fixed in spec (generator, `Static_MC`, tests) and in `run_pipeline.py` (seed 11) |
| Pinned environment | **None.** No `requirements.txt`, lock file or `environment.yml` in the repo; `.venv` is macOS-only. Fix: `requirements.lock` (exact versions) hashed into `RunLog` and `model_run.json` |
| Config and data hashes | Yes: `model_run.json` and `model_runs` (SHA-256); `RunLog` sheet in spec |
| Versioned outputs | Supabase runs are immutable; local `outputs/` and the workbook `output/` are git-ignored and overwritten. Fix: write to `output/<client>/<cycle>/<build_id>/` |
| Deterministic Excel builds | Not specified. XlsxWriter stamps creation time in document properties, so files differ byte for byte. Fix: set a fixed `created` property from the build id and test equality on cell values and formulas, not bytes |
| Design set under version control | **The last commit is October 23** (`git log`); v2.7, spec v0.5, both change lists, the handoffs and Session A's edits are untracked or uncommitted. Last year's design cannot be recovered from git today |

### 6.6 Client isolation

- **Supabase:** one project, separation by RLS on `institution_id` through `memberships` (`schema.sql` lines 147 to 186). Explicit and adequate for 10 clients. The pipeline writes with the service role, which bypasses RLS, so isolation on write depends on the pipeline.
- **Pipeline runs:** `run_pipeline.py` reads whatever `--data` points at; nothing checks that the data's institution matches the config's. Fix: each data batch carries `institution_id` and the run refuses a mismatch; one client per run.
- **Working folders:** this project folder holds Richmond-confidential files beside the product code. With a second client, Claude Code sessions in this folder could read both. Fix: product code in one repository; each client's data, fixtures and workbooks in a separate folder or repository outside it.
- **Pooling across clients (decision for Jason):** M §11 line 779 lists "Empirical prior pooled across clients: design-based estimates from at least three clients; replaces the vertical default prior in the screen". Even a pooled slope is derived from each client's confidential data. Frankel policy is not to mix one client's confidential information into another's work, so this needs either written consent in each SOW or removal. B4-1's shock calibration uses public 509 and IPEDS data only and needs no such decision.

### 6.7 Right-sizing

| Built or specified for a larger scale | Evidence | Suggestion |
|---|---|---|
| Monte Carlo release study: about 4,300 seeds a release (W0 and W0L at 200; W1 to W20 at 100 each; 9 cells × 100 for each consumer world), up to 30 s a seed | M §10 | About 36 hours a release at the 30 s target; keep W0, W0L and the worlds tied to live decisions (B7) |
| Consumer ZIP module: license gate, gates G1 to G4, P1 to P4, five-variant bake-off | M §2, §9, App. E | G2 may be unreachable at law size (O35); defer for law |
| Moderator discovery with pre-registration and Holm correction | M §4 | Needs randomized tests most clients will not run |
| Boosted-tree challenger | M §11, FR-64 | Law: drop (B4) |
| Dashboard with five views and RLS for at most 10 clients | roadmap §4 | Fine if the workbook stays the primary deliverable; see B6 |
| Grids up to 125 cells | M §5 | Count rule caps law at about 21 anyway |

### 6.8 Findings

**B5-1.** Major. Score scale, base year, geography-specific segment names and the class range are hard-coded in spec v0.5 (table 6.1). Fix: rename before the Phase 1 build (`score_*`, `base_cycle`, `segment`), and move every Richmond value out of product defaults into `config/richmond.yaml`. Cost now is a few hours of spec edits; cost after Phase 1 is a refactor of every module and test.

**B5-2.** Major. There is no written annual cycle and no comparison of last year's adopted scenario with actuals (6.4). Fix: adopt the four-step cycle above as a short section in the roadmap; add a `Calibration` sheet to the workbook in year 2.

**B5-3.** Major. No pinned environment, non-deterministic workbook builds, and a design set three weeks out of git (6.5). Fix as listed; the git item is Jason's call (this session does not commit).

**B5-4.** Major. Isolation depends on the pipeline and on folder discipline (6.6). Fix as listed.

**B5-5.** Decision for Jason. Cross-client empirical prior (M §11 line 779): remove, or require SOW consent.

**B5-6.** Major. The mockup optimizer is per-student and carries the removed guardrail; its config cannot carry a law client (6.1). Fix: treat `efa_fao/src/` as a parts bin; plan the S5 build around the ledger and the decision layer.

**Stop condition met:** seven items answered; hard-coding table, three-client walkthrough, minimal schema and annual cycle given.

## 7. Part B6: feasibility against Richmond's 2027 cycle

**Dates (Jason, Nov 16):** first scenario workbook in spring 2027; aid decisions in summer and fall 2027; six months to build (to about mid-May 2027). **Reading I took, to confirm:** awards for the class entering in fall 2027 are made from now through spring 2027, so decisions in summer and fall 2027 most likely set award policy for the class entering in 2028. The spring workbook can still serve the 2027 class in late-cycle shaping (cap, waitlist, the January pool check Brandon described), but it is too late to set that class's first offers. If Jason means the fall 2027 class, the Must list below has to land by about February, not May.

**Assumptions.** Claude Code builds; Jason is the only reviewer. "Build days" are supervised Claude Code session days; review hours are Jason's.

### What Richmond has sent and not sent

| Sent | Not sent (requested or to request) |
|---|---|
| Yellow Arrows workbook (fixture and shape use only; CLAUDE.md bars it from deliverables) | Any cell- or student-level extract usable in a deliverable (law Tier 1 request is drafted, not sent) |
| Brandon's Oct 30 note (Scenario 4 needs +50% high-LSAT applications; currently up about 60%) | State-level counts for three cycles (V27A-07); weekly pacing for the current and two prior cycles |
| Dean Rooksby's Nov 13 priorities | Exact 2027 tuition (OD-09); class-size path (OD-08); which discount rate (B3-2) |

**Consequence for the target tier.** Without state counts, the target-tier share of out-of-state applications is the synthetic placeholder 0.25 (S §10). Every target KPI (E_T, P(goal), cost per incremental, paid-anyway share) is then an assumption on top of an assumption and must carry "Target-tier share assumed (0.25), not from Richmond's data" until the counts arrive.

**A dependency the documents do not list.** CLAUDE.md allows synthetic and public data only and keeps the YA file out of deliverables. A workbook on Richmond's own data needs a decision to move from spec phase to production for this client, a data agreement in the SOW, Cat's sign-off on handling, and a secure place to process the extract. None of this is on the roadmap's critical path.

### Cut line

| Item | Group | Build days | Jason review (h) | Reasoning |
|---|---|---|---|---|
| Spec v0.6: B1 Blocking fixes, B1-6, B1-9, B1-10, B1-14, B5-1 renames | Must | 0.5 to 1 | 2 to 3 | Cheapest before code exists |
| Phase 1: ledger, risk, response, synthetic cells, trim, linear tripwires, target tier; tests 1, 2, 4, 5, 13 to 18 | Must | 3 to 5 | 4 to 6 | Foundation |
| Phase 2: workbook with README, Inputs, History, Response, Levers, Ledger x3, Summary, Trim, Checks, RunLog; tests 3 (forced recalculation), 9, 20 | Must | 5 to 8 | 8 to 12 | The deliverable; largest review load (open in desktop Excel here, not only at Phase 4) |
| Phase 3: reproduce mode against the YA fixture (test 6) | Must | 2 to 3 | 2 to 3 | The only real-data acceptance test available before Richmond's extract |
| Production data path: rule change, SOW data terms, cell-level extract and state counts, intake QA | Must | 2 to 4 | 6 to 10 | Plus Richmond's lead time (4 to 8 weeks); critical path |
| Live Richmond build, QA, labels, confidentiality check, client-ready review | Must | 2 to 3 | 6 to 8 | |
| **Must subtotal** | | **15 to 24** | **28 to 42** | About 3 to 5 hours a week over six months |
| Probability tripwires (bisection) | Should | 0.5 to 1 | 1 | Linear forms suffice for the January-style check |
| Phase 3b: schedule sheet and goal-seek (uniform and trim) | Should | 3 to 4 | 3 to 4 | Useful if Richmond authors by tiers; the Levers sheet works without it |
| Phase 1b: net-price block (reworded, B1-13) | Should | 1 | 1 to 2 | Answers the Dean's tuition question; display only |
| Phase 4 (part): Distribution, narratives, PDF render | Should | 2 to 3 | 3 to 4 | |
| Pinned environment, versioned outputs, deterministic build (B5-3) | Should | 0.5 to 1 | 1 | Needed before year 2 |
| Dashboard views 2 and 3 (OD-07, A5) | Later | 8 to 15 | 10 to 15 | Recommend reopening A5: workbook and PDF first; the dashboard repeats every figure and adds the reconciliation burden of FR-73 |
| `Static_MC` and stale guard | Later | 1 to 2 | 1 | Closed forms are validated; keep simulation in tests |
| `MultiYear`, `Trajectory`, five-year path and UG gap | Later | 3 to 5 | 4 | Deferred by Jason (Session A); year 2 |
| Per-state tiers, pipeline response table, S5 optimizer, screen re-run (O36), consumer ZIP, Monte Carlo expansion | Later | — | — | No anchor exists for Richmond; the optimizer would return the status-quo grid by rule |

**Test burden.** Computationally light: the 200,000-draw and 20-seed tests run in seconds on toy grids and cell-level worlds. The real cost is authoring tests that cannot pass as written (B1-1 to B1-3, B1-25) and test 5: tuning a generator to meet every shape range in 90% of 20 seeds can take longer than the ledger. Make the shape rows that do not touch ledger mechanics (GPA admit-rate ranges, pool-share trend, sparsity) report-only for Phase 1 acceptance, and keep the residency, yield and confounding rows asserted.

**Technical risks checked.**
- Excel and LibreOffice parity: Shown risk (B1-25); fix is a profile setting. Functions in the whitelist recalculate in LibreOffice 26.2 (`NORMSDIST` checked).
- Environment: the repo `.venv` is macOS-only. The linked Linux device has Python 3.10, numpy, pandas, xlsxwriter, openpyxl, pyyaml and LibreOffice, but no scipy or pytest, and pip could not reach a package index. Phase 1 can run without scipy; goal-seek (`linprog`) cannot. Decide the build machine (Jason's Mac with the 3.12 `.venv`) before Phase 1, and add a lock file.
- Wiring the pipeline's Response table later: low risk if the sheet layout is fixed now (S §15 item 3) and the interface contract exists (B1-12).

### Three biggest execution risks

| Risk | Why | Reduce it by |
|---|---|---|
| 1. No production data path | Rules allow synthetic data only; no extract, state counts or SOW data terms; Richmond's lead time | Decide the production rule with Cat this month; send the law request with the V27A-07 additions by mid-December with a February due date; build the target tier to show its placeholder status until counts arrive |
| 2. Reviewer bandwidth and scope growth | One reviewer for 28 to 42 hours on the Must list alone; the spec went from v0.1 (Nov 4) to v0.5 (Nov 13) in nine days, growing from 185 to 293 lines, alongside 43 V27, 7 V27A and 29 C change items | Freeze scope at the Must list (spec v0.6 = fixes and renames only); review by acceptance tests and a one-page checklist per phase; batch reviews every two weeks |
| 3. Vacuous parity testing and environment drift | Test 3 passes without recalculation (Shown); the build environment is undecided | Fix test 3 now; build on one machine with a lock file; open the Phase 2 workbook in desktop Excel |

## 8. Part B7: simplification

### Baseline count (spec v0.5 and the design set)

| Item | Count now | Source |
|---|---|---|
| Scenario-level scalar levers | 18 (pool multiplier, specialty, need override, tuition increase, award scaling, class target, class cap, incentive dollars, scope, score floor, application lift, target goal, yield shift global, in, out, target, discount target, award mode) plus schedule parameters (about 15) and per-cell admit rate and award (2 × about 68 cells) | S §2 scenario file |
| Config parameters | About 45 top-level | S §2 |
| KPIs per scenario and case | About 50 headline figures, plus about 200 what-if cells (tuition 4 rows, yield strip 7, class mix-held 9, shrink path 9, net-price rungs, tripwires up to 6) | S §3, §5, §6 Summary |
| Sheets | 17, plus 2 stubs | S §6 |
| Modules | 14 in `sw/` | S §1 |
| Tests | 20 | S §11 |
| Live design documents | 12 (executive read, methodology, roadmap, S1, spec, two change lists, three changelogs, Phase 1 handoff, CLAUDE.md), plus 9 older versions of the first three kept beside them, and two review handoffs | file map |

### Ranked proposals (largest complexity removed per unit of value lost first)

| Rank | Proposal | Complexity removed | Value lost; who asked | Risk | Recommendation |
|---|---|---|---|---|---|
| 1 | Drop `Static_MC` from the workbook; keep simulation in tests | 1 sheet, the checksum and stale-state guard, test 7 | A simulation figure beside the closed forms (spec v0.1 design); the closed forms are validated within 0.01 | Low; the README cites the validation | **Cut** |
| 2 | Defer dashboard views 2 and 3; ship the workbook and a PDF Summary first | Supabase scenario tables, two views, FR-73 three-way reconciliation for year 1, 8 to 15 build days | A5 / OD-07 (Jason, Nov 5) | Richmond sees no hosted view until year 2 | **Defer to after the spring delivery** (decision for Jason) |
| 3 | Defer goal-seek and the schedule layer | 2 modules, 2 sheets, the LP and its iteration, tests 10 and 11 (part); the `trim` goal-seek mode duplicates the shrink path, and `uniform` duplicates the mix-held factor | D1 helper (Jason, Nov 4); FR-75 | Analysts aim at targets by hand with the break-evens and the shrink path | **Defer to year 2** |
| 4 | Replace the pool tripwires with a pool strip: P(class > cap), P(median holds), expected class and margin at multipliers 0.8 to 1.6 in steps of 0.1 | 1 module, bisection, up to 6 numbers, the bracket and "none" rules (B1-10), test 17 | Single tripwire numbers (D15, Jason Nov 13); readers read the crossing off the strip | Low; same closed forms, live in Excel, so Excel and Python agree by construction | **Merge** |
| 5 | Cut the net-price block to two lines in the tuition what-if ("awards fixed: +$X for every student below full tuition; awards scaled: + p × net price"); drop automatic paired scenarios and the "equivalent yield shift" line | 1 module, a rung table × 3 rules, `pair_award_rule`, test 19, the B1-13 wording risk | D16 rung detail (Jason, Nov 13); the Dean's tuition question is still answered | Low | **Cut to two lines** |
| 6 | Remove the `MultiYear` and `Trajectory` stubs from Phase 4 | 2 stub sheets | Nothing until built; the five-year plan is deferred (Session A) | None | **Cut stubs; build in year 2** |
| 7 | Merge the two class-size tables: keep the shrink path; show the proportional factor f as one column in it | 1 Summary block, the f-scaled formulas, a test 9 clause | Mix-held view (D5, Nov 5) | Low | **Merge** |
| 8 | Merge `tier_yield_offset_pts` into the target (segment) shift; treat the application lift as a segment pool multiplier | 1 parameter, its fallback interaction (B1-7), an untested mechanic | None distinct (D17 keeps the lift) | Low | **Merge** |
| 9 | Merge the two incentive KPIs into one decomposition row: incentive cost, of which paid to students the parent already enrolled, additional enrollees, aid per additional enrollee | One validity rule, one population, one formula (fixes B1-4 and B1-11 together) | None; both figures remain | Low | **Merge** |
| 10 | Generalize the target tier to a priority segment and use score-generic names (B5-1) | Geography-specific names in schema, levers and tests; new code for other clients | None (D13 kept) | Renaming cost now is a few hours; after Phase 1 it is a refactor | **Do before Phase 1** |
| 11 | Consolidate the design set: one decision log (merging the two change lists and three changelogs), methodology §5 evaluator text replaced by a pointer to the spec plus the metric appendix, older versions moved to `_superseded/` | About 5 documents; the drift found in B2-1, B2-4 and B2-8 | History (kept in git once committed) | Low | **Merge** |
| 12 | Freeze methodology sections year 1 will not use (consumer ZIP module, price-test design and screen re-run O36, moderator discovery, increases-only re-optimization, batch scoring, boosted challenger, worlds W19 to W21L): mark "not maintained until triggered" | Every future change list stops touching them; about 40% of the methodology | None in year 1 | Stale text when revived; the trigger restarts review | **Defer** |
| 13 | Reduce the Monte Carlo release study to W0, W0L, W22 (year shock, B4-1) and the worlds tied to live decisions (W5, W6, W8, W9, W10, W11) | About 3,000 of 4,300 seeds a release | Coverage of deferred features | Re-add worlds when features return | **Defer** |
| 14 | Keep reproduce mode | — | — | — | **Keep** (the only real-data acceptance test before Richmond's extract) |
| 15 | Keep three Ledger sheets | — | — | Merging them into one sheet saves little and complicates formulas | **Keep** |

**After ranks 1 to 10:** sheets 17 + 2 stubs → 13 (README, Inputs, History, Response, Levers, Ledger x3, Summary, Trim, Distribution, Checks, RunLog, with Reproduce in reproduce mode); modules 14 → 9; tests 20 → about 14; scenario scalar levers 18 → 15; tripwire numbers up to 6 → one strip; Must-list build days fall by about 15 to 25 (B6).

### If we did only three

Ship the spring workbook on the closed-form core and nothing else: (1) **defer dashboard views 2 and 3, goal-seek and the schedule** to after the spring delivery, which removes the largest build and review items without touching what Richmond asked for; (2) **replace the tripwires, the net-price block and `Static_MC` with strips and lines computed by the closed forms already in the ledger**, which removes three modules and the definitions that B1 found ambiguous while keeping every question Dean Rooksby and Brandon raised answerable; (3) **rename the target tier to a general priority segment and make score and year names generic before Phase 1 starts**, which keeps D13 and is the one change that is cheap now and expensive later.

## 9. Consolidated decision list for Jason

| # | Decision | Options | Recommendation | What it changes | Source |
|---|---|---|---|---|---|
| 1 | Production data path for Richmond | (a) keep synthetic-only until S3 to S9 sign-off; (b) authorize a cell-level Richmond extract for the evaluator now, with SOW data terms and Cat's sign-off | (b), cell-level aggregates only, no student-level data | CLAUDE.md rule 1; a secure working folder; the data request goes out | B6 risk 1 |
| 2 | Which entering class the summer and fall 2027 decisions are for | 2027 or 2028 | Confirm; if 2027, the Must list must land by February | Schedule | B6 |
| 3 | Apply the B1 Blocking fixes and B5-1 renames as spec v0.6 before Phase 1 | Now, or build v0.5 and patch | Now | About a day of edits; avoids a refactor | B1, B5-1 |
| 4 | Shrink-path protection of target cells | (a) all target cells last; (b) target cells below the median threshold last among cells below it | (b) | Trim order; test 16 | B1-16 |
| 5 | Base-yield estimate | Hard fallback at 5 admits; partial pooling; also re-center at the latest award | Partial pooling (k = 20), re-centered | Response; tests 13, 5 | B1-15, B4-5 |
| 6 | Tier yield offset | Restrict to the pooled fallback, or merge into the segment shift | Merge | One parameter fewer | B1-7, B7 rank 8 |
| 7 | Median basis for unscored students | Count as below (now); exclude as the 509 does (to verify) | Exclude, after checking the 509 instructions | Median margin, P(median holds) | B3-3 |
| 8 | Discount-rate definition | Entering class year 1 (now); all JD; with or without fees | Label the current one; ask Brandon which the Dean means | Summary labels; OD-05 | B3-2 |
| 9 | NTR names and the optimizer-ledger equality | One NTR; two named NTRs | `ntr_y1` and `ntr_horizon`; fees excluded | FR-31, spec §15 item 1, M line 116 | B3-1 |
| 10 | Calibrate s from public 509 and IPEDS yield histories; add world W22 | Keep 0.10 illustrative; calibrate | Calibrate | O37; P(class > cap); W0L gate | B4-1 |
| 11 | Small-cell rule for files, the policy document and public material | As proposed in B2-3, with Cat | Adopt | Methodology §9; FR-06 | B2-3 |
| 12 | Dashboard views 2 and 3 in the first delivery (A5, OD-07) | Keep; defer to after the spring workbook | Defer | 8 to 15 build days | B6, B7 rank 2 |
| 13 | Defer goal-seek and schedule; replace tripwires, net-price block and `Static_MC` with strips and lines | Keep; cut | Cut or defer as ranked | Modules 14 → 9, tests 20 → about 14 | B7 ranks 1, 3 to 5 |
| 14 | Priority segment in place of the target-state tier names | Keep geography names; generalize | Generalize now (D13 unchanged) | Schema, levers, tests | B5 6.3 |
| 15 | Cross-client empirical prior (M §11 line 779) | Remove; keep with SOW consent | Remove from the plan, or add consent language to every SOW | Frankel confidentiality policy | B5-5 |
| 16 | Commit the design set and choose the build machine | Commit now; later | Commit after review (this session does not commit); build on the Mac `.venv` with a lock file | Reproducibility | B5-3, B6 |

## 10. What I could not check, and why

- **ABA 509 instructions** were not read; B3-3 (unscored students in percentiles) and B3-6 (deferrals in yield) rest on my understanding of the form and need checking.
- **NACUBO and IPEDS definitions** are stated from general knowledge; I ran no web search.
- **The pipeline and guardrail tests** were not run: the repo `.venv` is macOS-only, and the device has Python 3.10 without scipy or pytest, which could not be installed.
- **The Yellow Arrows fixture** was not opened; no Richmond figure was re-derived. Figures quoted from the methodology and spec (for example the 0.01 validation and the 21-group limit) are taken as written.
- **Normal-approximation and shrink-path checks** used toy grids, not the synthetic generator (not yet built).
- **LibreOffice recalculation** was checked on LibreOffice 26.2 on Linux; desktop Excel's behavior on open was not checked.
- **Effort estimates** in B6 are judgment, not measurement.
- **National law applicant trends** (for B4-8) were not looked up.
- **The optional Fable 5.2 second opinion** on B4 and B7 was not run.
- **Pitch and pricing decks** were not reviewed beyond what Session A changed.

Nothing here goes to a client without Jason's review. Before any part of this report or its figures leaves Frankel, check it for Richmond-confidential content (Dean Rooksby's priorities, Brandon's figures, the fixture-derived ranges).
