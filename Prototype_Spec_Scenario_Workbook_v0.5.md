# Prototype spec v0.5: formula-driven scenario workbook (for Claude Code)

**Date:** November 13, 2026 (v0.5 adds the target-state market tier, class sizes 100 to 140 under a hard cap, a shrink-path rule, pool tripwires and net-price readouts, and supersedes v0.4; v0.4 added the independent yield lever) | **Owner:** Jason Cohen | **Status:** draft for Jason's review | **Reads with:** `CLAUDE.md`, `Richmond_YA_Scenario_Workbook_Assessment.md` (sections 3, 4, 11), `02_methodology_v2.7.md` section 5

## 0. Purpose, scope, rules

**Purpose.** Build a Python program that generates an Excel scenario workbook with live formulas: it reproduces the panels of the Yellow Arrows (YA) Richmond workbook, then adds risk probabilities, evidence labels, distribution metrics and checks. The prototype proves the ledger and the risk formulas on synthetic data and on the YA file as a validation fixture. It does not estimate price response; a placeholder response table stands in for the pipeline.

**In scope (this spec):** reference ledger and risk functions in Python; a market tier on each cell (in-state, out-of-state target, out-of-state other) with a single out-of-state incentive aimed at the target tier or at all out-of-state and an optional target-tier application lift; class sizes from 100 to 140 under a hard cap, with a shrink-path rule; pool tripwires; net-price readouts (display only); tuition-migration, class-size and yield-shift what-if levers; a schedule layer that expands a few award parameters into the fine matrix; an admit-rate goal-seek helper; workbook generator; reproduce mode; synthetic cell-level data generator; tests. **Out of scope:** the estimation pipeline, the award optimizer, an admit-rate dimension in the optimizer (evaluator inputs and goal-seek only for now), Supabase, dashboard, pacing import (pool growth is a manual input; Slate pacing is a later addition), geography below the single target tier (one tier per state, MSAs, ZIP3; revisit after about two cycles of data and receipt of Richmond's state-level counts), the 509 Market sheet, the Frontier sheet, any USNWR link (a possible future law-product feature). Hooks are listed in section 12. **Principle (Jason, Nov 5): keep it simple and low-dimensional; do not overbuild.**

**Decisions in force (Jason, Nov 4 and 5, 2026).** (1) Admit-rate levers are scenario inputs that map onto the YA approach and report YA-style margins and uncertainty. (2) The fixed 5% guardrail is removed as a constraint and as a flag: the prototype never labels an award exceptional, anomalous or out of bounds. (3) Policy is expressed at the client's fine matrix. Geography enters as a market tier on each cell (in-state, out-of-state target, out-of-state other; target states set by the client, default NY and PA) and one incentive parameter in additional dollars; anything finer waits for data. (4) No small-cell suppression: the workbook and the hosted dashboard show small cells to authenticated client staff, enrollment team and leadership included. (5) The Excel workbook, the dashboard and the policy document must agree everywhere (section 15). (6) Tuition migration (this year and future years) and class size are scenario levers with visible outputs in Excel and the dashboard. Class size is supported and tested from 100 to 140. 140 is a hard cap in the current cycle, with a glide path toward 100 to 115 over five years (Jason, Nov 13; Brandon to confirm). (7) Yield has an independent scenario lever (a shift in points) with its own what-if strip; yield otherwise responds to award dollars only. A net-price yield response is deferred (CLAUDE.md, deferred features). (8) The target-state tier is one combined tier (NY and PA by default) and is part of the foundational data model, not a later add-on (Jason, Nov 13). (9) Net-price readouts are display-only arithmetic; no demand response (D10 stands).

**Rules for the build**
1. Code lives under `prototypes/scenario_workbook/`. Do not modify `efa_fao/src/`, `efa_fao/config/`, or any existing spec document.
2. Use the project environment (`.venv`, Python 3.12). Add `xlsxwriter`, `openpyxl` (read only), `pyyaml` and `pytest` if missing. Report each dependency you add.
3. The YA workbook (`Richmond Law - 2027 Scenarios for Client.xlsx`) is a validation fixture only. Never copy its cell values into code, config, test data or documentation. Read it at test time from the path in env var `YA_FIXTURE_PATH`; tests that need it skip when the variable is unset. `fixtures/` and `output/` are git-ignored; keep them that way.
4. Shape refinements to the synthetic generator use ranges and parameters only (section 10). Record each in `docs/shape_targets.md` with its source and range.
5. No protected attributes anywhere (race, ethnicity, gender). No student-level data: the prototype works on cell-level counts.
6. Fix failures in your own prototype tests. Do not fix failures in `efa_fao/tests/`; report them.
7. Style for prose and docstrings: concise, no emojis, no "genuinely", "honestly" or "straightforward".

## 1. Layout

```
prototypes/scenario_workbook/
  README.md                      how to run; what each test proves
  config/richmond_like.yaml      bands, thresholds, defaults (section 2)
  config/shape_targets.yaml      synthetic-world targets (section 10)
  sw/ledger.py                   reference ledger
  sw/risk.py                     closed-form probabilities
  sw/response.py                 placeholder response, interpolation, evidence flags
  sw/workbook.py                 XlsxWriter generator
  sw/narrative.py                text templates (Python and Excel forms)
  sw/mc.py                       Monte Carlo for static panels and tests
  sw/synth_cells.py              cell-level synthetic generator (stopgap, section 15)
  sw/schedule.py                 expands schedule parameters into the fine award matrix
  sw/goalseek.py                 admit-rate goal-seek (linear program)
  sw/trim.py                     shrink-path rule (admit rates for a smaller class)
  sw/tripwire.py                 pool tripwires (linear and bisection)
  sw/netprice.py                 net-price readouts (display only)
  sw/reproduce.py                YA fixture loader and comparison
  tests/                         section 11
  docs/shape_targets.md          provenance of each shape parameter
  fixtures/, output/             git-ignored
```
CLI: `python -m sw.build --config config/richmond_like.yaml --data <cells.csv|synthetic> --out output/scenario_workbook.xlsx` and `python -m sw.reproduce --out output/reproduce.xlsx` (uses `YA_FIXTURE_PATH`).

## 2. Inputs

**Config (`richmond_like.yaml`).**
- `tuition_by_cohort` (history), `tuition_2026`, `tuition_increase_by_year` (inputs by year, 2027 to 2031; default 6.0% each in reproduce mode, placeholders beyond 2027), `tuition_rounding_usd` (50). Scenario value `tuition_2027 = round_to(tuition_2026 x (1 + p_s), tuition_rounding_usd)`, where `p_s` is the scenario's `tuition_increase_pct` (default: the 2027 input). With 6.0% and $50 rounding the formula reproduces the fixture's 2027 tuition and every earlier step; a test checks this. Reproduce mode uses the fixture's tuition dollars as loaded values. Planning scenarios for Richmond set `tuition_increase_pct` explicitly to 5.5% (Dean Rooksby: "just over 5.5%"), marked unconfirmed until Brandon supplies the figure; the reproduce config and the history-reproduction test stay at 6.0%.
- `lsat_bands`: ordered list with lower bound (170, 167, 166, 165, 161, 158, 154, 152, 0). `gpa_classes`: `hi` (3.83 and above), `lo`, `blank`. Unscored rows (GRE, JD-Next, no score) are supported but default to zero.
- `median_thresholds`: LSAT [166, 165], GPA 3.83. `floor_lsat`: 154. `pool_threshold_lsat`: 165.
- `class_cap` (default 140; a hard cap in the current cycle), `class_size` (the target; default equal to `class_cap`; must not exceed it), `class_band` (default 4), `class_what_if` (default 100 to 140 in steps of 5; editable; values above `class_cap` are rejected), `ntr_target`. Supported and tested range: 100 to 140. Values outside 90 to 150 are rejected, and values outside 100 to 140 carry a plain notice. Optional inputs: `class_size_by_year`, `ug_tuition_by_year`, and `discount_target` (per scenario).
- `need_total` (200000) and `need_denominator` (140, a fixed reference class): `need_rate = need_total / need_denominator` per enrolled student (about $1,429), so need aid = `need_rate` x enrolled class and scales with class size. Changing `class_size` does not change `need_rate`. `specialty_usd` per scenario.
- `common_shock_sd` (default 0.10, illustrative), `sensitivity_slopes` (placeholder low, middle, high: 0.5, 1.0, 1.5 yield points per $1,000), `yield_floor` and `yield_cap` per LSAT group, `yield_shift_grid` (default -3, -2, -1, 0, +1, +2, +3 percentage points; editable).
- `integer_admits`, `integer_enrolled` (true in reproduce mode, false otherwise).
- `evidence_tolerance_usd` (2500): sets the observed range for the evidence label, which is information only (section 4).
- `yield_shift`: per scenario `yield_shift_pts` (default 0, percentage points added to every cell's yield), with optional `yield_shift_pts_in`, `yield_shift_pts_out` and `yield_shift_pts_target` that override it by residency and tier (precedence for a target-tier cell: target, then out, then global). `tier_yield_offset_pts` (default 0) adds to the base yield of target-tier cells (section 4). Independent of the award response and the same in the Low, Middle and High cases. Always labeled "Response based on client-input".
- `oos_incentive`: per scenario `oos_bonus_usd` (default 0), `oos_bonus_scope` (`all_out` or `target`; default `all_out`, which reproduces v0.4; the Richmond planning config sets `target`; `target` with no target cells is an error, never a silent no-op) and `oos_min_lsat` (default none) to limit eligibility. The bonus is applied per enrolled student in scope. The Summary shows its total expected cost and the helper "bonus implied by a dollar pool" = pool / baseline expected enrolled in scope (informational; not circular).
- `target_states` (default NY, PA; a label only, because the cell file carries no state) and `market_tiers` (`in`, `out_target`, `out_other`).
- `target_pool_lift_pct` (per scenario, default 0): multiplicative lift on applications in `out_target` cells, applied after the pool multiplier. It is the lever that geo-targeted recruiting or marketing is accountable for; the cost of that effort is outside NTR and the Summary says so. Labeled "Response based on client-input".
- `target_enrolled_goal` (per scenario, optional): expected target-tier enrollees the scenario aims at.
- `trim`: `{order: lsat_then_gpa, protect_target: true, floor_rate: 0, exempt_cells: []}` (section 3, shrink path).
- `pair_award_rule`: scenario names that get an automatic sibling with `award_scale_with_tuition` flipped (default: Baseline only).
- `pool_ytd_growth_pct`: an annotation shown beside the pool tripwires (for example, the current high-LSAT application growth Richmond reports); no logic reads it.
- `goalseek`: `{p_star: 0.80, admit_rate_bounds: [0, 1] per cell, class_floor_from_band: true, objective: min_disruption | max_ntr, mode: uniform | trim (default trim when the target class is below the expected class), max_iterations: 3}`.
- `schedule`: `{award_rounding: 500, default_tiers: derived from the admits-per-group merge in section 6A}`.
- `small_cell_suppression: none`.

**Cell data (`cells.csv`, long format).** One row per cell x cohort: `cell_id, residency, market_tier, lsat_lo, gpa_class, cohort, apps, admits, award_usd, enrolled`. `market_tier` is `in`, `out_target` or `out_other`; `residency` is `in` for `in` and `out` for both out tiers. The cell file carries no state: the mapping from state to tier happens in data preparation using `target_states`. The fixture loader assigns every out-of-state cell to `out_other`. Cohorts: three actuals (2024 to 2026). Cell order is fixed by (market_tier in the order in, out_target, out_other; lsat_lo descending; gpa_class); the workbook uses the same order.

**Scenario file (`scenarios.yaml`).** Per scenario: `name`, `parent`, `description`, `pool_multiplier`, `specialty_usd`, `need_total` (optional override), `tuition_increase_pct`, `award_scale_with_tuition` (default false: awards stay fixed dollars, the YA convention; true: base awards scale by 1 + p, with the full-tuition rung following tuition either way), `class_size`, `class_cap`, `oos_bonus_usd`, `oos_bonus_scope`, `oos_min_lsat`, `target_pool_lift_pct`, `target_enrolled_goal`, `yield_shift_pts` (and the optional residency and target overrides), `discount_target`, `year` (default 2027), `award_mode` (`manual` or `schedule`), schedule parameters when in `schedule` mode (section 6A), and per-cell `admit_rate` and `award_usd` overrides relative to the parent (the generator materializes full columns). Baseline is scenario 0: admit rate and award from the latest cohort, tuition at `tuition_2027`, yield from the response base.

## 3. Reference ledger (Python is the definition; Excel mirrors it)

For scenario s, cell c and case k in {low, middle, high}:

1. `tuition_s = round_to(tuition_2026 x (1 + p_s), tuition_rounding_usd)`
2. `apps_sc = apps_c,2026 x pool_mult_sc x (1 + target_pool_lift_s x [market_tier_c = out_target])`, where `pool_mult_sc` is `pool_multiplier_s` if `lsat_lo_c >= pool_threshold_lsat` and 1 otherwise
3. `admits_sc = apps_sc x rate_sc`, rounded to an integer when `integer_admits`
4. `award_base_sc`: the lever award; if it is at or above the parent's tuition (the full-tuition rung) it equals `tuition_s`; otherwise it is `award x (1 + p_s)` when `award_scale_with_tuition` and `award` otherwise. `award_sc = min(award_base_sc + oos_bonus_s x [in_scope_c and lsat_lo_c >= oos_min_lsat_s], tuition_s)`, where `in_scope_c` is `[market_tier_c = out_target]` when `oos_bonus_scope` is `target` and `[residency_c = out]` when it is `all_out`
5. `yield_sck = clip(response(c, award_sc, k) + shift_s,r(c) / 100, yield_floor_g, yield_cap_g)` (section 4), where `shift_s,r(c)` is the scenario's yield shift in points for the cell's residency and tier (precedence in section 2; 0 by default). Apart from the shift, yield responds to the award in dollars only; the effect of sticker price on applications or yield is not modeled (D10)
6. `enrolled_sck = admits_sc x yield_sck`, rounded when `integer_enrolled`; `class_sk = sum_c enrolled_sck`
7. `merit_sk = sum_c enrolled_sck x award_sc`; `oos_cost_sk = sum_c enrolled_sck x (award_sc - award_base_sc)` (reported separately and included in merit); `need_sk = need_rate_s x class_sk`
8. `gross_sk = class_sk x tuition_s`; `aid_sk = merit + need + specialty_s`; `NTR_sk = gross - aid`; `discount_sk = aid / gross`; `avg_aid = aid / class`

Yield is constant when admit rates change (D1). Reproduce mode has no OOS bonus and takes `specialty_s` as the YA lump sum.

**KPIs per scenario and case:** class; applications and admits (total, by residency); enrolled at or above each LSAT threshold, below `floor_lsat`; enrolled with GPA class `hi`; **margin** (YA definition) = count at or above the threshold minus count below; full-tuition enrolled (award at or above tuition) and full-pay enrolled (award of zero); barbell index = (full-tuition + full-pay) / class; Baseline NTR minus scenario NTR ("price of the target"); incentive cost; target-tier KPIs (below).

**Tuition what-if (live).** For each `p` in `tuition_grid` (default 5.0%, 5.5%, 6.0%, 6.5%; editable): NTR, net tuition per student and discount rate in the Middle case, with the scenario's class and mix held fixed and the awards rule above. Formula form: `NTR(p) = sum_c e_c x (T(p) - award_c(p)) - need - specialty`, where `e_c` is Ledger enrolled; one `SUMPRODUCT` per grid value. Each row carries the label "sticker-price demand effect not modeled".

**Yield what-if strip (live).** For each shift `d` in `yield_shift_grid`, applied on top of the scenario's own shift, in the Middle case: expected class, P(class > cap), P(class within band), NTR (mean), P(NTR at or above target), LSAT-median margin and P(median holds) at each threshold. Every figure is a closed form in `d` over Ledger columns, with `y_c` the scenario yield and `A_c` admits:
- `M(d) = sum A_c (y_c + d)`; `V(d) = sum A_c (y_c + d)(1 - y_c - d) + s^2 M(d)^2`, where `sum A_c (y_c + d)(1 - y_c - d) = sum A_c y_c (1 - y_c) + d sum A_c (1 - 2 y_c) - d^2 sum A_c`.
- `NTR mean(d) = sum w_c A_c (y_c + d) - specialty`, with `w_c` as in section 5; the NTR variance and the median quantities follow the same expansion.
- All of it is `SUMPRODUCT` over existing columns: no array `IF`, no per-shift helper columns.
The strip ignores the yield floor and cap. A count of cells where a bound would bind at the largest shift appears beside it as a plain figure, and a test shows the strip equals the Ledger with the shift entered whenever the count is zero.
**Break-evens (linear, unclipped, informational):** the uniform shift that moves the expected class to `class_size`, `(class_size - M) / sum A_c`; and the shift that moves expected NTR to `ntr_target`, `(ntr_target - mean) / sum w_c A_c`. Labeled "linear approximation".
A scenario's shift is an assumption the analyst enters, such as a view on a tuition effect, a competitor's offers or a softer yield season; the workbook does not estimate it.

**Class-size what-if (live), mix held.** For each N in `class_what_if` (default 100 to 140 in steps of 5), conditional on the class ending at N with the mix held constant: scale factor `f = N / M` (M = Middle expected class); NTR(N) = `f x (gross - merit - need) - specialty`; discount; LSAT and GPA margins scaled by `f`; and the uniform admit-rate multiplier `f` that would approximately deliver N. This reads outcomes at a class size; the probability of landing there comes from section 5, and `GoalSeek` finds rates that aim at `class_size`.

**Target-tier KPIs.** Per scenario and case: target applications, admits and enrolled (`E_T`), target share of class, target merit dollars, and incentive cost (target cells only when the scope is `target`). Closed forms on target cells: `M_T = sum_T mu_c`, `V_T = sum_T v_c + s^2 M_T^2`, `P(E_T >= goal) = 1 - Phi((goal - 0.5 - M_T)/sqrt(V_T))`, 90% interval `M_T +/- 1.645 sqrt(V_T)`.
- **Cost per incremental target enrollee,** scenario s against parent p: `dE = E_T(s) - E_T(p)` and `dSpend = merit_T(s) - merit_T(p)`; shown as `dSpend / dE` when `dE >= 0.5`, otherwise "increment under half a student".
- **Paid-anyway share:** `min(1, E_T(p) / E_T(s))`; times the incentive cost, it gives the incentive dollars paid to students the parent already had. Both figures are valid only when s differs from p by the incentive alone, and the Summary says so. Both depend on the placeholder slope and carry "Response based on client-input".

**Shrink path (`trim.py`).** The class-size what-if has a second group beside the mix-held rows. For each N in `class_what_if` (N at most `class_cap` and below the Middle expected class M) the rule writes admit rates and the ledger evaluates them. Outputs: expected class, LSAT and GPA margins and P(median holds), NTR, discount, target enrolled, the lowest LSAT band still admitted, and admits cut by LSAT band. Rule:
1. Order cells ascending by `lsat_lo`, then GPA class (blank, lo, hi). Ties among tiers break in the order `out_other`, `in`, `out_target`. With `protect_target`, every `out_target` cell is placed after all other cells. `exempt_cells` are never trimmed.
2. Walk the order, removing admits cell by cell until the removed expected enrollment equals `M - N`. A cell is cut to `floor_rate` before the walk moves on; the last cell is cut partially.
3. Round admits when `integer_admits` and settle the residual in the last cell.
The rule is deterministic and evaluator-only: it writes admit rates into a scenario the analyst may overwrite, so D1 holds (admit rates are never an optimizer dimension). The mix-held rows scale everything proportionally; the shrink path removes admits from the bottom, which is what raises the median.

**Pool tripwires (`tripwire.py`).** With multiplier `m` on cells at or above `pool_threshold_lsat`, let `M_lo` and `M_hi` be expected enrolled below and at or above the threshold at `m = 1`, and `G_lo`, `G_hi` the same split of the expected LSAT margin at threshold t (`g_c` as in section 5). Then `M(m) = M_lo + m M_hi` and `G(m) = G_lo + m G_hi`. Linear break-evens (Excel and Python): `m_class = (class_size - M_lo) / M_hi`; `m_median = -G_lo / G_hi`, defined when `M_hi > 0` and `G_hi > 0`, otherwise the Summary shows "none". Python also solves by bisection on the section 5 forms for the multiplier at which `P(median holds) = p*` (the downside tripwire) and at which `P(class > class_cap) = 1 - p*` (the upside tripwire: with a hard cap, a stronger pool is also a risk); `p*` defaults to 0.80. Each is shown as growth over 2026 (`m - 1`) beside `pool_ytd_growth_pct`. The linear forms are labeled "linear approximation; yield held constant". The tripwires let the team agree in advance on what to do if the pool softens or overshoots.

**Net-price readouts (`netprice.py`; display only).** For each scenario and each distinct award rung among cells with admits: net price at 2026 tuition `T26 - A`; at scenario tuition with fixed awards `Ts - A`; with scaled awards `Ts - A (1 + p)` (the full-tuition rung is zero either way). Show dollars and percent change, and the enrolled-weighted average over enrollees with an award below tuition. One line adds: "At the placeholder slope b_M, this net price change equals a yield shift of x points (not applied; compare the yield strip)." Label: "Arithmetic at constant award. Sticker-price demand effect not modeled." Scaled awards raise yield in the ledger only because award dollars rise, and the readout says so. Baseline gets an automatic sibling with the award rule flipped (`pair_award_rule`).

**Discount, gap and year.** If `discount_target` is set, the Summary shows the discount rate and its margin to target. If `ug_tuition_by_year` is set, the Summary shows the law-to-undergraduate tuition gap for the scenario's year. The ledger accepts `year` (default 2027) and takes tuition from `tuition_increase_by_year`; there is no other multi-year logic in this prototype (the `Trajectory` sheet is a later build).

## 4. Response (placeholder in the prototype; the pipeline replaces it later)

Per cell, base award `a0_c` = latest cohort award and base yield `y0_c` = admits-weighted yield over the last 3 cohorts (fallback: the cell's LSAT-group pooled yield when admits are under 5). For a candidate award `a` and slope `b_k` (points per $1,000):

`yield = clip(y0_c + (b_k / 100) x (a - a0_c) / 1000, yield_floor_g, yield_cap_g)`

The Response sheet tabulates yield at award rungs (0, 5,000, ... up to tuition; plus a "full tuition" rung that follows tuition) for each cell and case; the Ledger interpolates linearly between rungs with `MATCH`/`INDEX` and clamps outside the rung range. Each cell carries an **evidence label**: `observed` if `a` lies within the cell's historical award range plus `evidence_tolerance_usd`, otherwise `extrapolated`; the prototype labels every response source with the fixed text **"Response based on client-input"** (one constant, `RESPONSE_LABEL`, shown on Summary, Response, narratives and exported views). The label describes how well the yield is known, never the award: it carries no warning color, threshold or message. The Ledger records it per scenario cell, and the Summary reports the share of enrolled in `extrapolated` cells as a plain figure. Awards may differ from any prior value by any amount; the prototype applies no cap on award moves. Linear extrapolation is bounded only by `yield_floor` and `yield_cap` per LSAT group (placeholders 0.03 and 0.60).

Marginal-admit yield (yield changing with admit rate) is not modeled: yield is constant when admit rates change, in live and reproduce mode (the YA file does the same in 24 of 24 cases; Jason, Nov 4). Expose `marginal_admit_yield_slope` (default 0) that the ledger reads and ignores with a note when non-zero; implementing it waits for a marginal-admit yield estimate.

**Tiers.** Base-yield fallback chain per cell: the cell's three cohorts when admits are at least 5, else the (market tier, LSAT group) pool, else the (residency, LSAT group) pool. `y0` for `out_target` cells then adds `tier_yield_offset_pts`. Evidence labels are unchanged. The Summary reports the share of target-tier enrolled in cells with fewer than 10 admits as a plain figure; nothing is suppressed (D3).

## 5. Risk functions (closed form, validated against simulation)

Independent binomial enrollment by cell given `admits_sc` and `yield_sc`. With `mu_c = A_c y_c` and `v_c = A_c y_c (1 - y_c)`, `Phi` the standard normal CDF, `s` = `common_shock_sd`:

- **Class** (the cap is `class_cap`; the target is `class_size`, at most the cap): `M = sum mu_c`; `V = sum v_c + s^2 M^2`. `P(class > cap) = 1 - Phi((cap + 0.5 - M)/sqrt(V))`. `P(|class - target| <= band) = Phi((target + band + 0.5 - M)/sqrt(V)) - Phi((target - band - 0.5 - M)/sqrt(V))`. 90% interval: `M +/- 1.645 sqrt(V)`.
- **Target enrolled:** the class form on target cells (section 3). Cells are independent, so splitting a residency into tiers with equal parameters leaves the class, median and NTR probabilities unchanged (a test).
- **Median holds at threshold t:** sign `g_c = +1` if `lsat_lo_c >= t` else `-1` (unscored rows count as -1). `m = sum g_c mu_c`; `V_m = sum v_c`. `P(median >= t) = 1 - Phi((-0.5 - m)/sqrt(V_m))`. The common shock is **not** added here: it scales `m` and leaves its sign unchanged. Same form for GPA with `g_c = +1` for class `hi`. Tie rule: the median holds when at least half the class is at or above t.
- **NTR:** `w_c = tuition - award_c - need_rate`; `mean = sum w_c mu_c - specialty`; `V_n = sum w_c^2 v_c + s^2 (sum w_c mu_c)^2`. `P(NTR >= target) = 1 - Phi((target - mean)/sqrt(V_n))`.

**Validation already run on the YA fixture (Scenarios 1, 2, 4, from `ya_workbook_support/analysis.py`):** normal vs simulation within 0.01 for P(median at 166) 0.66, 0.61, 0.68; P(class above 140) 0.42, 0.22, 0.41 vs 0.42, 0.22, 0.40; P(NTR at least $4.5M) 0.32, 0.23, 0.43 vs 0.31, 0.23, 0.43; with s = 0.10: class SD 17.07 (formula) vs 17.0 and NTR SD $0.558M vs $0.56M (Scenario 1). Test 11.4 repeats this on synthetic worlds with tolerance 0.02.

## 6. Workbook sheets (XlsxWriter)

General: no hidden rows or columns; no conditional format or message that characterizes an award as unusual (a neutral highlight of cells changed from the parent is allowed); inputs unlocked and blue; formula cells locked; sheet protection with no password (D8); named ranges for every Inputs cell; freeze panes; print setup; consistent number formats. Formulas use `ROUND`, `SUMPRODUCT`, `INDEX`, `MATCH`, `MIN`, `MAX`, `IF`, `SQRT`, `NORMSDIST`, `TEXT` and `&`; no dynamic arrays, no `LET`/`LAMBDA`, no macros, no volatile functions. Write each formula with its cached value (from the Python ledger) so previews show numbers.

| Sheet | Content |
|---|---|
| `README` | Purpose, how to use, color key, the labels (observed, extrapolated, placeholder), what is static and what is live, build id |
| `Inputs` | Section 2 config values as named inputs; sensitivity case selector (Low, Middle, High) for display; mode switch (Live, Reproduce) |
| `History` | Cell x cohort panels: applications, admits, admit rate, award $, award % of tuition, yield, enrolled; totals by residency and overall; tuition row |
| `Response` | Per cell: `a0`, `y0`, observed award range, rung grid, yield at each rung for Low, Middle, High, evidence label |
| `Schedule` | Optional authoring layer per scenario: award by LSAT tier x residency, a GPA step, tier edges (lower bounds), all inputs; expands by formula into a fine award per cell (section 6A). Used when the scenario's `award_mode` is `schedule` |
| `Levers` | Header rows per scenario: name, parent, description, pool multiplier, specialty, need override, `award_mode`, `class_size`, `class_cap`, `tuition_increase_pct`, `award_scale_with_tuition`, `oos_bonus_usd`, `oos_bonus_scope`, `oos_min_lsat`, `target_pool_lift_pct`, `target_enrolled_goal`, `discount_target`, `yield_shift_pts` (with the residency and target overrides). Body: per cell (market tier in its own column) `admit_rate` (input, with lower and upper bounds that `GoalSeek` reads) and `award_usd` (input in `manual` mode, the `Schedule` result in `schedule` mode). A neutral highlight marks cells that differ from the parent (parent fixed at build time). A "cells changed from parent" count per scenario |
| `Ledger_Low`, `Ledger_Middle`, `Ledger_High` | Per cell (market tier in its own column), per scenario block of columns: apps, admit rate, admits, award (after tuition scaling and out-of-state incentive (per scope)), yield, evidence label, enrolled, spend. Totals row. Formulas per section 3 and 4; the mode switch selects live yield or the `Reproduce` override |
| `Summary` | Section 3 KPIs and section 5 probabilities for Baseline and each scenario, Middle case in the main block and Low and High for class, NTR, P(median). Price-of-target row. Evidence row (share of enrolled in `extrapolated` cells, plain figure). Tuition, yield-shift and class-size what-if blocks (mix held and shrink path) and the break-evens (section 3), the target block (enrolled with range, P(goal), incentive cost, cost per incremental target enrollee, paid-anyway share), pool tripwires, the net-price block, discount and UG-gap rows. Narrative rows (section 8) |
| `Trim` | Helper for the shrink path (live mode only): cells in trim order with expected enrollment `mu_c` and cumulative `E_k`; per N, `removed_share_k = MIN(1, MAX(0, (M - N - E_{k-1}) / mu_k))`, `rate_k(N) = r_k x (1 - removed_share_k)`, and per-N summaries by `SUMPRODUCT` (`m(N) = sum g_c mu_c (1 - removed_c)`, `V_m(N) = sum v_c (1 - removed_c)`) |
| `Distribution` | Full-tuition and full-pay counts, barbell index, share of merit dollars going to the top quartile of enrolled by academic position (cells ordered by `lsat_lo`, then GPA class; weighted by expected enrolled). **Step sizes:** award difference between adjacent LSAT bands within each residency x GPA class, per scenario, as a plain table with no threshold, color or message |
| `GoalSeek` | Static output of `goalseek.py` for named scenarios (proposed admit rates per cell, change from the parent, status, binding constraints) with the lever checksum guard, plus live cells showing the Ledger's gap to each target. Staff copy proposed rates into `Levers` by hand |
| `Static_MC` | Monte Carlo results for named scenarios (class, NTR, P(median) at 20,000 draws, seed fixed), the build date, and a checksum over the lever cells with a live flag: `RE-RUN NEEDED` when the lever checksum differs. Checksum: `ROUND(SUM(lever range) + SUMPRODUCT(lever range, ROW(lever range)), 6)` |
| `Checks` | Section 7 |
| `Reproduce` | Present only in reproduce mode: YA yields, admit rates, awards and pool settings as loaded values |
| `RunLog` | Build id, git commit, config hash, data hash, timestamp, dependencies, response source label |

Later sheets (stubs allowed): `MultiYear` (award rule toggle fixed dollars or percent of tuition, tuition migration read from `tuition_increase_by_year`, retention by year, three-year spend and NTR) and `Trajectory` (2027 to 2031: class, tuition, discount, medians and target-tier enrollment by year, from `year`, `class_size_by_year`, `tuition_increase_by_year` and `ug_tuition_by_year`). Not in this prototype: `Market`, `Frontier`.

## 6A. Schedule and goal-seek helpers

**Schedule (`schedule.py`, mirrored by the `Schedule` sheet).** Parameters per scenario: tier edges (LSAT lower bounds, descending), a base award for each (tier, residency), and a GPA step in dollars applied to class `hi`. Expansion: `award_c = clip(round_to(base[tier(lsat_lo_c), r_c] + gpa_step x [gpa_c = hi], award_rounding), 0, tuition)`. The default tiering comes from the sizing in section 15 (about 13 award-tier parameters). The same function renders the policy document's fine matrix. Schedule is an authoring convenience: the policy of record is the fine matrix it produces, and a client may overwrite any cell in `manual` mode. The market tier is not a schedule dimension: `out_target` and `out_other` cells share the out-of-state schedule, and the incentive carries the difference.

**Goal-seek (`goalseek.py`).** Given a scenario with awards and yields fixed, find admit rates `r_c` in `[lo_c, hi_c]` that meet class and median targets with minimal change. With `A_c` applications, `y_c` yield, `mu_c = A_c y_c r_c`:
- Class: `M = sum A_c y_c r_c`, linear in `r`. Constraint `M <= class_cap + 0.5 - z sqrt(V)` with `z = Phi^-1(p*)`, and optionally `M >= target - band`.
- Median at t: `m = sum g_c A_c y_c r_c`. Constraint `m >= -0.5 + z sqrt(V_m)`.
- Target enrolled (optional): `M_T = sum_T A_c y_c r_c`, linear in `r`. Constraint `M_T >= goal + z sqrt(V_T)`, iterated like the class constraint.
- Modes: `uniform` scales all rates; `trim` applies the shrink-path rule (section 3) to reach the target class; both write ordinary admit rates the analyst can overwrite.
- `V` and `V_m` depend on `r`; fix them at the current rates, solve, recompute at the solution, repeat up to `max_iterations`.
- Objective `min_disruption`: minimize `sum A_c |r_c - r0_c|` (split into positive and negative parts); alternative `max_ntr`: maximize `sum w_c A_c y_c r_c`.
- Solve with `scipy.optimize.linprog` (HiGHS). Round admits to integers, re-evaluate in the ledger, and report the ledger's probabilities, never the LP's. If infeasible, report which constraint binds.
This is a planning helper, not the S5 optimizer. It is deliberately linear so staff can reproduce its reasoning.

## 7. Checks sheet (each returns OK or a message)

Integrity only; nothing here comments on an award. Totals of cell rows equal totals rows; admits at most applications; enrolled at most admits; award at least zero and at most tuition after the bonus clamp; yield between 0 and 1; tuition formula reproduces the history steps; `Schedule` expansion equals the `Levers` awards when `award_mode` is `schedule`; class against cap and band (reported as a result, not a warning); spend against `budget_total` when set (D7); history reconciliation (grid-implied merit against reported actual merit, when provided; show the percent gap); Summary class equals Ledger total; lever checksum guard.

## 8. Narratives

Python and Excel versions of two templates per scenario, populated from live cells:
- **Changes from parent:** "Pool multiplier {x}. Awards changed in {n} cells; admit rates changed in {m} cells." (Counts by formula; named bands listed only in the Python version written to `Static_MC`.)
- **Projected outcome:** "Class {N} (90% range {lo} to {hi}). LSAT median {t}: {count at or above} of {N}, margin {margin}, probability {p}. GPA median {3.83}: margin {g}, probability {pg}. {k} enrolled below {floor}. Full-tuition {ft}, full-pay {fp}. NTR {x}M (90% range), discount {d}%. Tuition {T} (+{p}%); class size {class_size} (cap {class_cap}); incentive {b} ({scope}); target-state enrolled {E_T}. Evidence: {share}% of enrolled in cells where the yield is extrapolated."

## 9. Reproduce mode (acceptance test against the YA fixture)

`reproduce.py` reads the YA workbook (read only) and builds a workbook in which the Ledger runs with YA's admit rates, awards, yields and pool settings as client-input values.

**Fixture layout (verified October 30 file).** Sheet `Client Strategy Comparison`: six panels, each 12 columns wide starting at columns B (admit rate), O (admits), AB (award %), AO (award $), BB (yield), BO (enrolled); within a panel the columns are 2024, 2025, 2026, Baseline, Scenarios 1 to 8. Rows 7 to 40 are in-state cells and rows 59 to 92 are out-of-state; column A holds the cell label. Ignore rows 41 to 56, 93 onward (`#N/A` filler). Applications are not in the file: use `admits / admit rate` for 2026 where the rate is above zero. Tuition by cohort: award $ / award % (55,550; 57,600; 59,900; 63,500). Sheet `Client Scenarios`: scenario columns AH (S1), AP (S2), AX (S3), BF (S4); rows 179 to 183 hold gross, merit, need, specialty and total aid; row 186 holds NTR; row 189 holds the narrative text. Pool multipliers: 1.30 for Scenarios 1 to 3, 1.50 for Scenario 4, applied at LSAT 165 and above; need $200,000 over 140 enrolled (Scenario 4: need $190,000 and specialty $10,000). Scenarios 5 to 8 are empty; skip them. The file has residency only, no state: every out-of-state cell loads as `out_other`, the target tier is empty, and Scenario 4's $10K specialty stays a lump sum in `specialty_usd` (it is not decomposed by state).

**Pass criteria (Scenarios 1 to 4 and Baseline where derivable):** class equal; merit spend equal; NTR within $100 (observed gap $60); enrolled at or above 166, 165, 154, 3.83 and below 154 equal to the file's counts and narrative; full-tuition and full-pay counts equal to the narrative (21 and 14; 15 and 11; 10 and 11; 9 and 13); LSAT and GPA margins equal to the narrative. Report every mismatch; do not tune to force a match.

## 10. Synthetic cell-level generator and shape targets

Generate three cohorts of cell-level counts for the Richmond-like band grid (section 2), plus a hidden true response slope (default 1.2 points per $1,000, configurable) used only to make enrolled counts. Seeds fixed. Do not use `efa_fao/src/synth`. These **ranges** come from the fixture and set the generator's targets (`config/shape_targets.yaml`; record provenance in `docs/shape_targets.md`; test them in 11.5). They are directional: three cohorts, small cells.

| Feature | Target range | Why it matters |
|---|---|---|
| Residency | Out-of-state is 67% to 72% of applications and admits; its share of enrolled is 49% to 53% and falling; yield about 0.15 out-of-state and 0.33 to 0.35 in-state | Two markets with different yield |
| Admit rates by LSAT group | 165 and above: 0.94, 0.85, 0.79 across the three cohorts (falling); below 165: 0.33, 0.30, 0.25 | The selectivity lever is real and moving |
| Admit rates by GPA | 3.83 and above 0.79 to 0.85; below 3.83 0.22 to 0.31 | |
| Yield by group | LSAT 165+ 0.18 to 0.21; below 165 0.22 to 0.23; GPA 3.83+ 0.12 to 0.20; below 3.83 0.23 to 0.29; overall 0.209 to 0.214 | High-credential admits yield lower; overall yield stable |
| Applicant pool | About 1,450 to 1,630 applications; 165+ share rises from about 0.18 to 0.27; 165+ applications grew about 50% then about 7% (approximate: cells with no admits cannot be recovered) | Pool composition is non-stationary |
| Awards | Admit-weighted award as a share of tuition: 165+ 0.98, 0.87, 0.79; below 165 0.32, 0.26, 0.25; fixed-dollar rungs; top rung equals tuition; tuition grows about 3.7%, 4.0%, 6.0% | Barbell easing; sticker price moving |
| Class | 133 to 146 per cohort; share of enrolled at 165+ rises from about 0.35 to 0.53 | |
| Cell sparsity | Median 8 to 12 admits per active cell; about 45% to 55% of active cells under 10 admits; about 90% or more under 10 enrolled | Forces pooled estimation and tests small-cell handling |
| **Confounding** | Cross-sectional, admit-weighted slope of cell yield on award share: raw about -0.04 to -0.17 points per $1,000; adjusted for LSAT group, GPA class and residency from -0.9 to +0.1 | Aid is targeted at high-credential, lower-yield admits, so the observed slope is near zero or negative while the true slope is positive. The synthetic world must reproduce this so that the pipeline is tested on the same trap |

Source for each row: fixture sheets 1 and 2 and the computation in this session (October to November 2026 analysis; rerun `ya_workbook_support/analysis.py` for the base figures). Adopting these in the main S2 world definitions (W0L) is a separate change for Jason's review.

**Target tier.** The generator assigns each out-of-state cell's applications to `out_target` or `out_other` with `target_share_of_out` by LSAT group (placeholder 0.25, a synthetic assumption to be replaced from Richmond's state-level counts), `target_yield_offset_pts` (0) and `target_apps_trend` (0). No new range comes from the fixture, which has no state; the out-of-state ranges above must hold on the merged tiers (test 5). Generate scenarios at class sizes 100, 110, 120, 130 and 140 under `class_cap` 140 for the shrink-path and tripwire tests.

## 11. Tests (`pytest`)

1. **Ledger unit tests:** each identity in section 3 on a 6-cell toy grid (one cell in the target tier) with hand-computed answers.
2. **Risk unit tests:** closed forms against a 200,000-draw simulation on the toy grid; tolerance 0.01.
3. **Excel equals Python:** build the workbook from the synthetic world, recalculate with LibreOffice headless (`soffice --headless --convert-to xlsx --outdir <tmp>`), read recalculated values with `openpyxl(data_only=True)` and compare every Ledger and Summary numeric cell to the Python result: exact for integers, 1e-6 relative for floats. If `soffice` is missing, report it, skip, and list the cells that need a manual Excel open.
4. **Closed form vs simulation on synthetic worlds:** class, median and NTR probabilities within 0.02 for 20 random scenarios.
5. **Shape targets:** the synthetic generator meets every range in section 10 across 20 seeds, on merged tiers (report the share of seeds passing; require at least 90%).
6. **Reproduce:** section 9 pass criteria (skipped without `YA_FIXTURE_PATH`).
7. **Stale guard:** editing one lever value in a copy of the workbook flips the `RE-RUN NEEDED` flag (checked after LibreOffice recalculation).
8. **Guardrails:** no column named race, ethnicity or gender in any input or output; no student-level fields; workbook contains no formulas referencing external files; no hidden sheets, rows or columns; no conditional format or cell text that labels an award exceptional, anomalous, out of bounds or beyond a limit.
9. **Levers and schedule:** with `oos_bonus_usd` zero and the parent's tuition increase, a child scenario equals its parent; the tuition what-if row at the scenario's own `p` equals the Ledger NTR; the class-size what-if at N = M equals the Ledger NTR; `need_rate` is unchanged when `class_size` changes; schedule expansion is constant within tiers and equals the manual matrix when copied. **Yield shift:** a scenario with shift `d` equals the same scenario's yield-strip column at `d` when no cell clips; shift 0 equals the parent; the class break-even shift applied to the scenario returns an expected class equal to `class_size` when no cell clips; the residency overrides apply only to their residency.
10. **Goal-seek:** on 20 synthetic scenarios the LP either meets class and median targets in the ledger (within rounding) or reports infeasibility with the binding constraint; total admit change is no larger than a greedy baseline.
11. **Reconciliation:** Summary and Ledger agree with a Python dump of the same run for every figure that the dashboard and policy document will read (the interface contract in section 15).
12. **Rendering:** convert `Summary` to PDF with LibreOffice and save to `output/` for visual review (not asserted).
13. **Tier merge invariance:** splitting out-of-state cells into two tiers with equal parameters changes no total or probability.
14. **Incentive scope:** scope `target` changes award, merit and incentive cost only in target cells; scope `all_out` equals v0.4 on merged data; scope `target` with no target cells raises an error.
15. **Target levers:** `target_pool_lift_pct` changes applications in target cells only, and 0 equals the parent; shift precedence follows section 2; the target-enrolled closed form matches simulation within 0.02; the cost-per-incremental identity `dSpend / dE` holds on a scenario that differs from its parent only by the incentive.
16. **Shrink path:** hits N within rounding for N = 100 to 140 on 20 synthetic worlds; admits never rise; the order is respected; with `protect_target`, target cells are untouched until every other cell is at its floor; at N = M it returns the original rates; the expected count at or above a threshold is unchanged while only cells below the threshold are trimmed; the share at or above the threshold is non-decreasing as N falls.
17. **Pool tripwires:** at `m_class` the expected class equals `class_size` and at `m_median` the expected margin is zero (no clip, no rounding); the bisection results return `P(median holds) = p*` and `P(class > class_cap) = 1 - p*` within 0.005.
18. **Class range and cap:** ledger, risk, trim and generator run at N = 100, 110, 120, 130, 140; `need_rate` is unchanged; no probability leaves [0, 1]; `P(class > cap)` uses `class_cap`; `class_size` above `class_cap` and a what-if N above it are rejected.
19. **Net price:** the fixed-dollar change equals `Ts - T26` for every rung; the scaled change equals `p x (T26 - A)` within rounding; the full-tuition rung is zero under both.
20. **Excel equals Python for the v0.5 cells (Phase 2, with test 3):** target block, both class-size groups, tripwires, net-price block.

## 12. Phases, acceptance and hooks

| Phase | Deliverable | Accept when |
|---|---|---|
| 1 | `ledger.py`, `risk.py`, `response.py`, `mc.py`, `synth_cells.py`, `trim.py`, `tripwire.py`; market tier in the cell schema, ledger, response and generator; target KPIs and levers; class range 100 to 140 under `class_cap`; tests 1, 2, 4, 5 (as edited) and 13 to 18 | Tests pass; shape targets met |
| 1b | `netprice.py`, discount and UG-gap rows, paired award-rule scenarios, test 19 (Phase 1 if time allows, otherwise Phase 2) | Test 19 passes |
| 2 | `workbook.py` with README, Inputs, History, Response, Levers, Ledger x3, Summary, Trim, Checks, RunLog; tests 3, 9 and 20 | Excel equals Python on synthetic worlds |
| 3 | `reproduce.py`, Reproduce sheet, test 6 | Section 9 criteria met, or mismatches reported with causes |
| 3b | `schedule.py` and `Schedule` sheet; `goalseek.py` (modes `uniform` and `trim`, target-enrolled constraint) and `GoalSeek` sheet; tests 10 and 11 | Schedule expands as specified; goal-seek meets targets in the ledger |
| 4 | Distribution, Static_MC with guard, narratives, MultiYear and Trajectory stubs; tests 7, 8 and 12 | Tests pass; Jason reviews the PDF render and opens the file in desktop Excel |
| 5 (next build) | `Trajectory` sheet for 2027 to 2031 (class, tuition, discount, medians, target-tier enrollment); per-state tiers once Richmond's state-level counts arrive | Reviewed by Jason |

Hooks for later work (leave stubs and TODO notes, no logic; the full list is in CLAUDE.md under deferred features): pipeline-supplied Response table (same sheet layout, evidence labels `estimated` or `extrapolated`); marginal-admit yield; net-price yield response (yield moves with tuition minus award; see CLAUDE.md); geography below the single target tier (one tier per state, MSAs; after about two cycles of data and Richmond's state-level counts); pacing-based pool path with interval (Slate, later addition); `Market` (509 rank-matched award gap); `Frontier`; an admit-rate dimension in the optimizer; the proxy screen on market targets (pipeline); a client-declared policy envelope; USNWR planner link (possible future law-product feature).

## 13. Decisions

| ID | Question | Status |
|---|---|---|
| D1 | Admissions levers | Decided (Nov 4): evaluator inputs plus goal-seek helper; constant yield when admit rates move; an admit-rate dimension for the optimizer may come later |
| D2 | Guardrail | Decided (Nov 4): fixed 5% rule removed as constraint and flag; evidence label kept as information; band-edge step sizes shown as a plain table |
| D3 | Small cells | Decided (Nov 4 and 5): shown to authenticated client staff, enrollment team, leadership and the aid office, in every view; cleared by Cat and Richmond staff |
| D4 | Tuition migration | Decided (Nov 5): a scenario lever plus a by-year input for future years (default 6.0% for 2027, which reproduces the fixture's tuition with $50 rounding); what-if grid 5.0% to 6.5% in Excel and the dashboard. Nov 13: Richmond planning scenarios use 5.5% (unconfirmed, from Dean Rooksby's "just over 5.5%") until Brandon supplies the figure; reproduce mode stays at 6.0% |
| D5 | Class size | Decided (Nov 5, revised Nov 13): `class_size` is the target and `class_cap` the hard cap (140 in the current cycle); supported range 100 to 140; what-if table 100 to 140 in steps of 5; glide path toward 100 to 115 over five years, to be confirmed with Brandon. Need aid scales per enrolled student at a fixed rate |
| D6 | Sensitivity slopes 0.5, 1.0, 1.5; shock SD 0.10; yield floor and cap | Placeholders, not evidence |
| D7 | Budget figure | Unknown; `budget_total` optional |
| D8 | Sheet protection | On, no password |
| D9 | Geography | Decided (Nov 5, revised Nov 13): a market tier on each cell (in, out_target, out_other), one combined target tier with states set by the client (default NY, PA), one incentive whose scope is the target tier or all out-of-state, an optional target-tier application lift and yield offset; per-state tiers, MSAs and ZIP3 wait for data |
| D10 | Sticker-price demand effect | Not modeled: tuition changes alter NTR arithmetic, not applications or yield, unless the analyst enters a yield shift (D12) or a pool multiplier. Every tuition output says so. A net-price response (yield moving with tuition minus award) is deferred to a future feature (CLAUDE.md, deferred features). Net-price readouts (section 3) are arithmetic at constant award and are not applied |
| D11 | Awards when tuition moves | Default fixed dollars (YA convention); a per-scenario toggle scales awards with tuition; the full-tuition rung always follows tuition |
| D12 | Independent yield lever | Decided (Nov 5): per-scenario yield shift in percentage points (optional by residency), strip of -3 to +3 points, two linear break-evens. Labeled "Response based on client-input". No net-price switch |
| D13 | Target-state tier | Decided (Nov 13): one combined tier, part of the foundational data model (Phase 1); see D9 |
| D14 | Class range and shrink path | Decided (Nov 13): 100 to 140 supported; 140 is a hard cap this cycle; shrink order LSAT then GPA with target-tier cells protected; evaluator-only rule (D1 holds) |
| D15 | Pool tripwires | Added (Nov 13): downside and upside tripwires on the pool multiplier, linear forms in Excel, bisection forms in Python |
| D16 | Net-price readouts | Added (Nov 13): display-only arithmetic; D10 stands |
| D17 | Target-tier application lift | Decided (Nov 13): include `target_pool_lift_pct`, default 0 |

## 14. Handling and report-back

The YA file is Richmond-provided with permission, but it is YA's work product: use our own layout and wording; do not reproduce their text or branding. Anything that reproduces its cell values stays out of git (Jason confirmed Nov 4); the file may calibrate synthetic data through ranges and parameters (section 10). When done, report: what was built per phase, test results (including skips and why), dependencies added, mismatches in reproduce mode with the likeliest cause, and anything in this spec that proved ambiguous or wrong. Workbooks that go to a client need Jason's review first.

## 15. Integration with the pipeline and the other deliverables

1. **One evaluator.** The ledger is the single reference evaluator of any award grid. The optimizer's projected class, spend and NTR for a solved grid must equal the ledger's for the same grid (a later test). The Excel workbook, the dashboard scenario view and the policy document read ledger outputs; none recomputes them. Test 11 is the reconciliation.
2. **Cell data.** The pipeline's cell aggregate (today `funnel_cells.csv`) needs `award_usd` and `market_tier` by cell and cohort, and an unsuppressed variant for authenticated client staff. Suppression is removed for this client (D3); the CLAUDE.md rule and schema enforcement change in v2.7, not in this prototype.
3. **Response.** The pipeline supplies a table per cell x award rung x case with an evidence label, plus the anchored slope and its uncertainty from `model_run.json` (`b_L`, `b_M`, `b_H` replace the placeholder slopes).
4. **Policy of record at the fine matrix.** The optimizer works on a low-dimensional decision layer and the fine matrix is rendered by `schedule.py`, the function the `Schedule` sheet mirrors. Sizing on the YA fixture (7 of 68 fine cells have 30 or more admits): merging adjacent LSAT bands within residency x GPA (3.83 and above, other) until each group has 30 admits gives about 13 groups (16 to 17 at 20 admits), on both 2026 admits and the three-cohort mean. The decision layer is therefore about 13 award-tier parameters plus one out-of-state incentive (scope: the target tier or all out-of-state; the market tier is not a decision dimension), 14 in total, which fits the methodology's count rule (cells at most admits / 30 = 21) if that rule is kept.
5. **Policy document and admissions.** The aid policy carries the award matrix, the out-of-state incentive with its scope, and the target-state list. Admit rates and pool multipliers appear in a separate planning-assumptions block, not as aid policy.
6. **Band-edge step sizes** appear as a plain table (Distribution sheet and policy document); no flag, no threshold.
7. **Synthetic data.** `synth_cells.py` is a stopgap. When the law world (W0L) generates student-level data, aggregate it with the pipeline's aggregator and retire `synth_cells.py`; the shape targets move into W0L.
8. **Sequencing.** Scenario outputs may reach Richmond before a price anchor exists (S1 OD-07), so every figure carries "Response based on client-input" until the pipeline's response table replaces the placeholder. The workbook evaluates scenarios and does not recommend prices.
9. **Levers shared by all three deliverables.** Tuition migration (this year and future years), class size and cap, the out-of-state incentive and its scope, the target-tier application lift and the yield shift are scenario inputs in Excel, the dashboard scenario view and the policy document's assumptions block, each computed by the ledger. The dashboard shows the tuition what-if grid, the yield-shift strip and the class-size what-if table with the same labels.
10. **Data request additions (Richmond).** Aggregate application, admit and deposit counts by state (by LSAT band if available) for the last three cycles (no student-level data), weekly pacing against the prior two cycles at the same week of the cycle, the exact 2027 tuition and the planned path, undergraduate tuition by year, and the planned class size path.
