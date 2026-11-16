# Prototype spec v0.5: change list (draft for Jason's review)

**Date:** November 13, 2026 | **Base:** `Prototype_Spec_Scenario_Workbook_v0.4.md` | **Status:** applied on Nov 13 in `Prototype_Spec_Scenario_Workbook_v0.5.md` (v0.4 moved to `_superseded/`) | **Source of changes:** Jason's answers on Nov 13 and Dean Rooksby's priorities (note to Ryan, Nov 13)

## A. Inputs behind this change list

1. **Target-state flag is foundational (Jason, Nov 13).** It belongs in Phase 1, or at minimum in the data model, ledger and generator so nothing is retrofitted. This reopens D9 ("nothing finer than one out-of-state incentive until about two cycles of data") by exactly one step: a market tier flag on each cell and an incentive that can be aimed at it. Per-state structure, MSAs and ZIP3 stay deferred.
2. **Class size runs from 100 (low end) to 140 (top end) (Jason, Nov 13).** Jason will confirm the target with Brandon. Every function, table and test must work across that range.
3. **What drives the rest (Dean's note, Nov 13; confidential to Richmond).** Tuition up just over 5.5% with the discount rate held; a five-year path to 100 to 115 students; stronger out-of-state pipelines from key markets (NY, PA); a narrower gap to undergraduate tuition (law is $11K below UG today); LSAT quality rising; early applicant interest strong and hoped to continue. Brandon's Oct 30 note adds that Scenario 4 needs at least +50% in high-LSAT applications and that high-LSAT applications are up about 60% now, with a January adjustment if the pool softens.
4. **What the YA file cannot tell us.** It carries residency only (in-state, out-of-state), no state. Scenario 4's NY and PA item is a $10K specialty lump sum with no modeled response. The target tier therefore starts empty in reproduce mode and is populated by synthetic parameters and, later, Richmond's state-level counts.

## B. Changes by section

### B1. Section 0 (purpose, scope, decisions)

- **C1. In scope.** Replace "a single out-of-state incentive lever" with "a market tier flag (in-state, out-of-state target, out-of-state other; target states set by the client, default NY and PA) and a single out-of-state incentive whose scope is the target tier or all out-of-state". Add to the in-scope list: "class sizes from 100 to 140, a shrink-path rule, pool tripwires, net-price readouts (display only)".
- **C2. Out of scope.** Replace "market-level geography (states, MSAs, ZIP3; revisit after about two cycles of data)" with "geography below the single target tier (one tier per state, MSAs, ZIP3; revisit after about two cycles of data and receipt of state-level counts)".
- **C3. Decisions in force.** Rewrite (3): "Policy is expressed at the client's fine matrix. Geography enters as a market tier on each cell and one incentive parameter in additional dollars; anything finer waits for data." Rewrite (6): "...class size is a scenario lever, supported and tested from 100 to 140 (Jason, Nov 13; target to be confirmed with Richmond)". Add (8): "Net-price readouts are display-only arithmetic; no demand response (D10 stands)."

### B2. Section 1 (layout)

- **C4.** Add `sw/trim.py` (shrink-path rule), `sw/tripwire.py` (pool tripwires), `sw/netprice.py` (net-price readouts). `config/richmond_like.yaml` keeps its name.

### B3. Section 2 (inputs)

- **C5. Cell data.** Add required column `market_tier` with values `in`, `out_target`, `out_other`. `residency` stays (`in` or `out`) and is derived: `in` for `in`, `out` for both out tiers. Mapping from state to tier happens in data preparation, using `target_states`; the cell file carries no state. Cell order becomes (market_tier in the order in, out_target, out_other; lsat_lo descending; gpa_class). The fixture loader assigns every out-of-state cell to `out_other`.
- **C6. Config.** Add `target_states` (default [NY, PA]; label only), `market_tiers`, `ug_tuition_by_year` (optional), `class_size_by_year` (optional), `discount_target` (optional, per scenario), `pool_ytd_growth_pct` (annotation only; no logic; shown beside the pool tripwire), `pair_award_rule` (list of scenario names that get an automatic sibling with `award_scale_with_tuition` flipped; default: Baseline only), and `trim`: `{order: lsat_then_gpa, protect_target: true, floor_rate: 0, exempt_cells: []}`.
- **C7. Class size.** Replace "class_size (default 140...)" text with: default 140; supported and tested from 100 to 140; values outside 90 to 150 are rejected, and values outside 100 to 140 carry a plain notice. `class_what_if` default becomes 100, 105, 110, 115, 120, 125, 130, 135, 140 (editable). `class_band` stays 4 (input). `need_denominator` stays 140, so `need_rate` is unchanged at any class size.
- **C8. Tuition.** `tuition_increase_by_year` extends to 2031. Planning scenarios for Richmond set `tuition_increase_pct` explicitly to 5.5% and mark it "unconfirmed" until Brandon supplies the exact figure (Dean: "just over 5.5%"). Reproduce mode and the history-reproduction test stay at 6.0% and $63,500. `tuition_grid` default stays 5.0, 5.5, 6.0, 6.5.
- **C9. Incentive and yield shift.** Replace the `oos_incentive` paragraph: per scenario `oos_bonus_usd` (default 0), `oos_bonus_scope` (`all_out` or `target`; default `all_out` so v0.4 behavior is unchanged; the Richmond planning config sets `target`; `target` with no target cells is an error, never a silent no-op), and `oos_min_lsat`. Add `target_pool_lift_pct` (default 0): a multiplicative lift on applications in `out_target` cells (the lever that geo-targeted marketing is accountable for; its marketing cost is outside NTR and the Summary says so). Add `target_enrolled_goal` (optional). Add `tier_yield_offset_pts` (default 0, applies to `out_target`) and `yield_shift_pts_target`. Precedence for the shift in a target cell: `yield_shift_pts_target`, else `yield_shift_pts_out`, else `yield_shift_pts`. All labeled "Response based on client-input".
- **C10. Scenario file.** Add the new fields to the per-scenario list: `oos_bonus_scope`, `target_pool_lift_pct`, `target_enrolled_goal`, `yield_shift_pts_target`, `discount_target`, `year` (default 2027).

### B4. Section 3 (ledger)

- **C11. Step 2.** `apps_sc = apps_c,2026 x pool_mult_sc x (1 + target_pool_lift_s x [tier_c = out_target])`, where `pool_mult_sc` is `pool_multiplier_s` if `lsat_lo_c >= pool_threshold_lsat`, else 1.
- **C12. Step 4.** The bonus applies where `[tier_c = out_target]` when scope is `target`, or `[residency_c = out]` when scope is `all_out`, in both cases with `lsat_lo_c >= oos_min_lsat_s`. The tuition clamp is unchanged.
- **C13. Step 5.** The shift follows the precedence in C9; the tier offset applies to `y0` for `out_target` cells (section 4).
- **C14. Target KPIs (new).** Per scenario and case: target applications, admits and enrolled (`E_T`), target share of class, target merit dollars, incentive cost (target cells only when scope is `target`). Closed forms: `M_T = sum_T mu_c`, `V_T = sum_T v_c + s^2 M_T^2`, `P(E_T >= goal) = 1 - Phi((goal - 0.5 - M_T)/sqrt(V_T))`, 90% interval `M_T +/- 1.645 sqrt(V_T)`.
  - **Cost per incremental target enrollee**, scenario s against parent p: `dE = E_T(s) - E_T(p)`, `dSpend = merit_T(s) - merit_T(p)`, shown as `dSpend / dE` when `dE >= 0.5`, otherwise "increment under half a student".
  - **Paid-anyway share**: `min(1, E_T(p) / E_T(s))` times the incentive cost gives the incentive dollars paid to students the parent already had. Both figures are valid when s differs from p only by the incentive and are labeled so. Both depend on the placeholder slope and carry "Response based on client-input".
- **C15. Class-size what-if.** Keep the v0.4 mix-held rows and add a second group, **shrink path**: for each N in `class_what_if`, apply the shrink rule (C16) and evaluate in the ledger: expected class, LSAT and GPA margins and P(median holds), NTR, discount, target enrolled, lowest LSAT band still admitted, admits cut by LSAT band. The two groups answer different questions: mix-held scales everything; shrink path removes admits from the bottom, which is what raises the median.
- **C16. Shrink-path rule (new, `trim.py`).** Given scenario rates and a target N below the expected class M:
  1. Order cells ascending by `lsat_lo`, then by GPA class (blank, lo, hi). Ties among tiers break in the order `out_other`, `in`, `out_target`. With `protect_target`, every `out_target` cell is placed after all other cells; `exempt_cells` are never trimmed.
  2. Walk the order, removing admits cell by cell until the removed expected enrollment `sum mu_c` equals `M - N`. A cell is cut to `floor_rate` before the walk moves on; the last cell is cut partially.
  3. Return trimmed admit rates, the lowest LSAT band still admitted, and cuts by band. Round admits when `integer_admits`, then settle the residual in the last cell.
  The rule is deterministic and evaluator-only: it writes admit rates into a scenario the analyst may overwrite, so D1 holds (admit rates are never an optimizer dimension). It is not an optimizer.
- **C17. Pool tripwires (new, `tripwire.py`).** With multiplier `m` on cells at or above `pool_threshold_lsat`, let `M_lo` and `M_hi` be expected enrolled below and at or above the threshold at `m = 1`. Then `M(m) = M_lo + m M_hi`, and the expected LSAT margin at threshold t is `G(m) = G_lo + m G_hi`, with `g_c` as in section 5. Linear break-evens (Excel and Python): `m_class = (class_size - M_lo) / M_hi`; `m_median = -G_lo / G_hi`, defined when `M_hi > 0` and `G_hi > 0`; otherwise the Summary shows "none". Python also solves for the multiplier at which `P(median holds) = p*` (default 0.80) by bisection on the section 5 form. Output as growth over 2026, `m - 1`, beside the `pool_ytd_growth_pct` annotation. Labeled "linear approximation; yield held constant". This turns Brandon's January check into a trigger the team can agree on in advance.
- **C18. Net-price readouts (new, `netprice.py`; display only).** For each scenario and each distinct award rung among cells with admits: net price at 2026 tuition `T26 - A`; at scenario tuition with fixed awards `Ts - A`; with scaled awards `Ts - A (1 + p)` (full-tuition rung is zero either way). Show dollars and percent change, plus the enrolled-weighted average over enrollees with award below tuition. Add one line: "At the placeholder slope b_M, this net price change equals a yield shift of x points (not applied; compare the yield strip)". Label: "Arithmetic at constant award. Sticker-price demand effect not modeled." Scaled awards raise yield in the ledger only because award dollars rise; the readout says so.
- **C19. Discount and gap rows.** If `discount_target` is set, the Summary shows the discount rate and its margin to target. If `ug_tuition_by_year` is set, the Summary shows the law-to-UG gap for the year.
- **C20. Year.** The ledger accepts `year` and takes tuition from `tuition_increase_by_year`; no other multi-year logic in this prototype. This is the foundation for a later trajectory view (B9).

### B5. Section 4 (response)

- **C21.** Base-yield fallback chain per cell: cell (3 cohorts) when admits are at least 5, else (market_tier, LSAT group), else (residency, LSAT group). `y0` for `out_target` cells adds `tier_yield_offset_pts`. Evidence labels are unchanged. The Summary reports the share of target-tier enrolled in cells with fewer than 10 admits as a plain figure. No suppression anywhere (D3).

### B6. Section 5 (risk)

- **C22.** No change to the closed forms. Add: cells are independent, so splitting a residency into tiers with equal parameters leaves class, median and NTR probabilities unchanged (a test). The target block uses the class form of section 5 on target cells.

### B7. Sections 6, 6A, 9, 10

- **C23. Sheets (Phase 2).** `Levers`: tier column per cell and the new header fields. `Ledger_*`: tier column. `Summary`: target block (enrolled with range, P(goal), incentive cost, cost per incremental, paid-anyway share), class-size table with both groups, pool tripwire rows, net-price block, paired award-rule scenarios. New helper sheet `Trim`: cells in trim order with `mu_c`, cumulative expected enrollment `E_k`, then per N: `removed_share_k = MIN(1, MAX(0, (M - N - E_{k-1}) / mu_k))`, `rate_k(N) = r_k x (1 - removed_share_k)`, and per-N summaries by `SUMPRODUCT` (`m(N) = sum g_c mu_c (1 - removed_c)`, `V_m(N) = sum v_c (1 - removed_c)`). Live mode only; reproduce mode has no `Trim` outputs.
- **C24. Schedule and goal-seek (6A).** Tier is not a schedule dimension: `out_target` and `out_other` share the out-of-state schedule, and the incentive carries the difference. The decision layer stays about 13 award-tier parameters plus one incentive. Goal-seek gains `mode: uniform | trim` (default `trim` when the target class is below the expected class) and an optional linear constraint `sum_T A_c y_c r_c >= goal + z sqrt(V_T)` (iterated like the class constraint), so a target-enrollee goal can sit beside the class and median targets.
- **C25. Reproduce (9).** Unchanged. The loader maps every out-of-state cell to `out_other`; the target tier is empty; Scenario 4's $10K specialty stays a lump sum in `specialty_usd` and is not decomposed by state.
- **C26. Synthetic generator (10).** Add parameters: `target_share_of_out` by LSAT group (placeholder 0.25, a synthetic assumption to be replaced from Richmond's state-level counts), `target_yield_offset_pts` (0), `target_apps_trend` (0). Add no new fixture-derived range: the existing out-of-state ranges must hold on the merged tiers (test 5). Add generator scenarios at class sizes 100, 110, 120, 130, 140 for tests of the shrink path.

### B8. Section 11 (tests)

- **C27. Edits.** Test 1: add a target-tier cell to the toy grid. Test 5: assert the shape ranges on merged tiers. Test 9: class-size default list and need-rate invariance across 100 to 140.
- **C28. New tests.**
  13. **Tier merge invariance:** splitting out-of-state cells into two tiers with equal parameters changes no total or probability.
  14. **Incentive scope:** scope `target` changes award, merit and incentive cost only in target cells; scope `all_out` equals v0.4 on merged data; scope `target` with no target cells raises an error.
  15. **Target levers:** `target_pool_lift_pct` changes applications in target cells only, and 0 equals the parent; shift precedence follows C9; target-enrolled closed form against simulation within 0.02; the cost-per-incremental identity `dSpend / dE` on a scenario that differs from its parent only by the incentive.
  16. **Shrink path:** hits N within rounding for N = 100 to 140 on 20 synthetic worlds; admits never rise; order respected; with `protect_target`, target cells are untouched until every other cell is at its floor; at N = M it returns the original rates; expected count at or above a threshold is unchanged while only cells below the threshold are trimmed; the share at or above the threshold is non-decreasing as N falls.
  17. **Pool tripwire:** at `m_class` the expected class equals `class_size` and at `m_median` the expected margin is zero (no clip, no rounding); the bisection result returns `P = p*` within 0.005.
  18. **Class range:** ledger, risk, trim and generator run at N = 100, 110, 120, 130, 140; `need_rate` is unchanged; no probability leaves [0, 1].
  19. **Net price:** the fixed-dollar change equals `Ts - T26` for every rung; the scaled change equals `p x (T26 - A)` within rounding; the full-tuition rung is zero under both.
  20. **Excel equals Python (with test 3, Phase 2):** target block, both class-size groups, tripwire and net-price cells.

### B9. Section 12 (phases) and later work

| Phase | Adds from v0.5 |
|---|---|
| 1 (foundation, must) | `market_tier` in the cell schema and generator; tier logic in ledger and response; target KPIs; scope, lift and shift levers; `trim.py`; `tripwire.py`; class range 100 to 140; tests 1, 2, 4, 5 as edited, and 13 to 18 |
| 1 (follows if time allows, otherwise Phase 2) | `netprice.py` (C18), discount and gap rows (C19), auto-paired award-rule scenarios, test 19 |
| 2 | Excel: sheets in C23, test 20, tests 3 and 9 as edited |
| 3, 3b | Reproduce unchanged; schedule tier rule and goal-seek `trim` mode and target constraint (C24) |
| 4 | Unchanged, plus the `Trajectory` stub reading `year`, `class_size_by_year`, `tuition_increase_by_year`, `ug_tuition_by_year` |
| 5 (next build) | `Trajectory` sheet for 2027 to 2031 (class, tuition, discount, medians, target-tier enrollment); per-state tiers after Richmond's state-level counts |

### B10. Section 13 (decisions)

- **D4:** add "planning scenarios use 5.5% (unconfirmed) until Brandon supplies the figure; reproduce mode stays 6.0%".
- **D5:** replace the what-if list with "100 to 140 in steps of 5"; add "supported range 100 to 140".
- **D9:** replace with "Decided (Nov 13): a three-value market tier on each cell (in, out_target, out_other), target states set by the client (default NY, PA), one incentive whose scope is the target tier or all out-of-state, an optional target-tier application lift and yield offset; per-state tiers, MSAs and ZIP3 wait for data".
- **D10:** add "Net-price readouts are arithmetic at constant award (C18); they are not applied".
- **New D13** target-state tier (above). **D14** class size 100 to 140 with a shrink-path rule (evaluator-only). **D15** pool tripwires. **D16** net-price readouts, display only. **D17** planning tuition placeholder.

### B11. Section 15 (integration)

- Item 2: the pipeline's cell aggregate needs `market_tier`. Request from Richmond: aggregate applicant, admit and enrolled counts by state for the last three cycles (no student-level data), weekly application pacing against last year by LSAT band, the exact 2027 tuition and the planned path, UG tuition, and the planned class size path.
- Item 4: the decision layer stays about 13 plus one incentive; the policy document carries the target-state definition and the incentive's scope.
- Item 9: add the target-state tier, the incentive scope and the class range to the levers shared by all three deliverables.

## C. Other documents that change after approval

- `CLAUDE.md`: deferred-features list (market-level geography stays deferred; the single target tier moves into scope), class-size range, tuition placeholder.
- `Handoff_Prototype_Phase1.md`: scope, reading order (v0.5), "decisions not to reopen" (D13 to D17), the Phase 1 test list.
- `S1_Requirements_and_User_Stories.md`: new requirements for the target-state tier and incentive scope, the class range and shrink path, and pool tripwires; OD-07 note unchanged.
- `02_methodology_v2.7.md`: the geography section reads "market tier" already; add the single-tier prototype and the target-enrollee objective; confirm wording against D13.
- Data-request text and pitch decks: add the state-level counts, pacing and tuition items; the "cells under 10 suppressed" wording still conflicts for Richmond.

## D. What v0.5 does not do

No state-level estimation; no marketing cost in NTR; no yield response to tuition or net price; no multi-year logic beyond `year`; no change to the guardrail decisions (D2) or small-cell visibility (D3).

## E. Questions for Jason

1. One combined target tier, or one per state? Recommendation: combined now (NY and PA cells are too thin to split), reported by state later from the data request.
2. Shrink order: LSAT first, then GPA, target tier protected. Confirm, or name a different order.
3. Include `target_pool_lift_pct`? Recommendation: yes. It is one number, defaults to zero, and it is the lever geo-targeted marketing is accountable for.
4. Is 140 the 2027 cap with the glide path starting this cycle, or the starting point for a later path? Brandon's answer sets `class_size` for the Richmond baseline.
5. Has the Phase 1 build started? If yes, this list goes in as an addendum; if not, apply it to a v0.5 spec before the build begins.

## F. Answers (Jason, Nov 13) and additions made when applying

1. One combined target tier: agreed.
2. Shrink order (LSAT first, then GPA, target tier protected): agreed.
3. `target_pool_lift_pct`: included, default 0 (D17).
4. 140 is a hard cap this cycle and the glide path toward 100 to 115 starts this cycle; this may shift, and Brandon will confirm. **C29 (added at apply):** because the cap is hard and the path may start below it, `class_cap` (default 140) is separate from `class_size` (the target, at most the cap). P(class > cap) uses the cap; the band probability uses the target; the shrink path and what-if tables accept N up to the cap; the pool tripwires gain an upside tripwire (P(class > cap) = 1 - p*), since a stronger pool is also a risk under a hard cap.
5. The Phase 1 build has not started; the handoff note is rewritten for v0.5.
