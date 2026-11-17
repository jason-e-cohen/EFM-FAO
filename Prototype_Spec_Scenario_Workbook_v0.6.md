# Prototype spec v0.6: formula-driven scenario workbook (for Claude Code)

**Date:** November 16, 2026 (v0.6 applies the Session B design audit, `Audit_Session_B_Design_Report.md`, accepted by Jason on Nov 16: Blocking and other fixes, generic names, the metric definitions, and three simplifications; supersedes v0.5) | **Owner:** Jason Cohen | **Status:** v0.6.1 (Nov 17, 2026): Phase 1 built and reviewed (`Review_Phase1_Build.md`); amendments tagged **[v0.6.1, R-n]** or **[v0.6.1, OP-n]** (the builder's open points); ready for the Phase 1.1 fix pass and Phase 2. Phase 2 review follow-ups (Nov 17) are tagged **[v0.6.2, P2-n]** and **[v0.6.2, Q-n]** (the Phase 2 builder's questions, `Review_Phase2_Build.md` section 4) | **Reads with:** `CLAUDE.md`, `02_methodology_v2.8.md` (section 5 and Appendix F, metric definitions), `DECISIONS.md`, `Richmond_YA_Scenario_Workbook_Assessment.md` (sections 3, 4, 11; git-ignored)

Change tags: **[v0.6, Bn-m]** cites the Session B finding that caused a change. Untagged text is carried from v0.5.

## 0. Purpose, scope, rules

**Purpose.** Build a Python program that generates an Excel scenario workbook with live formulas: it reproduces the panels of the Yellow Arrows (YA) Richmond workbook, then adds risk probabilities, evidence labels, distribution metrics and checks. The prototype proves the ledger and the risk formulas on synthetic data and on the YA file as a validation fixture. It does not estimate price response; a placeholder response table stands in for the pipeline. The workbook is the first deliverable; a dashboard is a later add-on that reads the same ledger outputs (section 15). **[v0.6]**

**In scope.** Reference ledger and risk functions in Python; a priority segment on each cell (Richmond: one combined target-state segment, NY and PA) with one incentive aimed at the segment or at all out-of-state, and an optional segment application lift; class sizes as a target under a hard cap, with a shrink-path table; a pool strip; tuition, class-size and yield-shift what-if levers; workbook generator; reproduce mode; synthetic cell-level generator; tests.

**Out of scope (deferred; do not build or stub).** **[v0.6, B7]** The `Schedule` sheet and `schedule.py`; goal-seek (`goalseek.py`, `GoalSeek` sheet); `Static_MC` (simulation stays in tests); `MultiYear` and `Trajectory` (year 2); the net-price rung table and paired award-rule scenarios (replaced by two lines, section 3); bisection tripwires (replaced by the pool strip); the dashboard (add-on after the workbook); the estimation pipeline; the award optimizer; an admit-rate dimension in the optimizer; Supabase; pacing import; geography below the single segment; the 509 `Market` sheet; `Frontier`; any USNWR link. **Principle (Jason, Nov 5): keep it simple and low-dimensional; do not overbuild.**

**Decisions in force.** (1) Admit-rate levers are scenario inputs that map onto the YA approach and report YA-style margins and uncertainty. (2) No guardrail: the prototype never labels an award exceptional, anomalous or out of bounds. (3) Policy is expressed at the client's fine matrix. Geography enters as a priority segment on each cell and one incentive parameter in additional dollars; anything finer waits for data. (4) No small-cell suppression at Richmond: the workbook and any later dashboard show small cells to the named, authenticated client roles (enrollment team, leadership, aid office); the workbook goes only to those roles through the secure channel (methodology section 9). **[v0.6, B2-3]** (5) The Excel workbook, the policy document and any later dashboard agree everywhere (section 15). (6) Tuition migration and class size are scenario levers; class size is a target under a hard cap (Richmond: 140 this cycle; glide path toward 100 to 115 over five years, Brandon to confirm). (7) Yield has an independent scenario lever (a shift in points); yield otherwise responds to award dollars only; a net-price yield response is deferred. (8) The priority segment is part of the foundational cell schema, not an add-on (D13). (9) Nothing in this workbook recommends a price; every response-dependent output carries its label (section 4).

**Rules for the build**
1. Code lives under `prototypes/scenario_workbook/`. Do not modify `efa_fao/src/`, `efa_fao/config/`, or any specification document.
2. **[v0.6, B5-3]** Build on Jason's Mac with the project environment (`.venv`, Python 3.12). Add `xlsxwriter`, `openpyxl` (read only), `pyyaml`, `scipy` and `pytest` if missing, then write `prototypes/scenario_workbook/requirements.lock` with exact versions (`pip freeze`). Report each dependency added. LibreOffice is needed from Phase 2.
3. The YA workbook (`Richmond Law - 2027 Scenarios for Client.xlsx`) is a validation fixture only. Never copy its cell values into code, config, test data or documentation. Read it at test time from env var `YA_FIXTURE_PATH`; tests that need it skip when unset. `fixtures/` and `output/` are git-ignored.
4. Shape refinements to the synthetic generator use ranges and parameters only (section 10), recorded in `docs/shape_targets.md` with source and range.
5. No protected attributes anywhere (race, ethnicity, gender). No student-level data: the prototype works on cell-level counts.
6. Fix failures in your own prototype tests. Do not fix failures in `efa_fao/tests/`; report them.
7. **[v0.6, B5-1]** No client value is a product default. Product code reads every client value from `config/<client>.yaml`; `config/richmond.yaml` holds Richmond's. A required value that is missing is an error, not a silent default.
8. Style for prose and docstrings: concise, no emojis, no "genuinely", "honestly" or "straightforward".

## 1. Layout

```
prototypes/scenario_workbook/
  README.md                 how to run; what each test proves; metric names (methodology Appendix F)
  requirements.lock         exact versions
  config/richmond.yaml      Richmond client config (section 2)
  config/synthetic.yaml     synthetic-world config for tests
  config/shape_targets.yaml synthetic-world targets (section 10)
  sw/ledger.py              reference ledger and KPIs (section 3)
  sw/risk.py                closed-form and exact probabilities (section 5)
  sw/response.py            placeholder response, base yield, evidence labels (section 4)
  sw/trim.py                shrink-path rule (section 3)
  sw/strip.py               yield, pool and tuition what-if strips (section 3)
  sw/mc.py                  simulation, used by tests only
  sw/synth_cells.py         cell-level synthetic generator (stopgap; section 15)
  sw/workbook.py            XlsxWriter generator
  sw/narrative.py           text templates (Python and Excel forms)
  sw/reproduce.py           YA fixture loader and comparison
  sw/labels.py              RESPONSE_LABEL, ASSUMPTION_LABEL, SHOCK_LABEL and other fixed text
  tests/                    section 11
  docs/shape_targets.md     provenance of each shape parameter
  fixtures/, output/        git-ignored; output/<client>/<cycle>/<build_id>/
```
CLI: `python -m sw.build --config config/richmond.yaml --data <cells.csv|synthetic> --out output/` and `python -m sw.reproduce --out output/` (uses `YA_FIXTURE_PATH`).

## 2. Inputs

**Client config (`config/<client>.yaml`).** **[v0.6, B5-1]** Names are generic; Richmond's values are shown in brackets and live only in `richmond.yaml`.
- `client`: `id`, `name`, `vertical` (law or ug), `small_cell_policy` (none at Richmond).
- `cycle`: `base_cycle` [2026], `plan_cycle` [2027], `history` [2024, 2025, 2026]. Every "base" quantity below is for `base_cycle`; nothing in code names a year.
- `tuition_by_cohort` (history), `tuition_base` (tuition in `base_cycle`), `tuition_increase_by_year` (by plan year; reproduce mode [6.0%]; Richmond planning [5.5%, unconfirmed until Brandon supplies the figure]), `tuition_rounding_usd` [50]. Scenario tuition `tuition_s = round_to(tuition_base x (1 + p_s), tuition_rounding_usd)`. With 6.0% and $50 rounding the formula reproduces the fixture's next-cycle tuition and every earlier step; a test checks this. Reproduce mode uses the fixture's tuition dollars as loaded values. Fees are excluded from tuition everywhere and reported separately when supplied **[v0.6, B3-1]**.
- `score`: `measure` [LSAT], `bands` (ordered lower bounds) [170, 167, 166, 165, 161, 158, 154, 152, 0], `pool_threshold` [165], `floor` [154], `median_thresholds` [166, 165]. `gpa`: `measure` [UGPA], `classes` (`hi` at or above [3.83], `lo`, `blank`), `median_threshold` [3.83]; the median threshold must equal the `hi` boundary, because the cell schema has one GPA boundary (the loader enforces it) **[v0.6.1, OP-7d]**. **Score group:** cells at or above `score.pool_threshold` form the upper group, all others the lower group; unscored rows (GRE, JD-Next, none; `score_lo` blank) join the lower group for pooling. **[v0.6, B1-6]**
- `unscored_in_median`: `excluded` (default) or `below`. Excluded means unscored and blank-GPA enrollees leave both sides of the corresponding margin and are reported as a count (the ABA 509 basis, to confirm against the 509 instructions); `below` is the v0.5 rule. **[v0.6, B3-3]**
- `class`: `cap` [140; hard this cycle], `target` [140; must not exceed `cap`], `band` [4], `what_if` [100 to 140 in steps of 5], `supported_range` (default 0.7 x cap to cap) and `reject_range` (default 0.6 x cap to 1.1 x cap). A target outside the supported range carries a plain notice; outside the reject range it is an error. **[v0.6, B5-1, B1-19]** Class: first-year entrants enrolled at the census date, full-time and part-time as on the 509, excluding transfers (Richmond to confirm whether the cap counts part-time entrants). **[v0.6, B3-9]**
- `need`: `total` [200,000], `reference_class` [140]. `need_rate = total / reference_class` per enrolled student [about $1,429]; need aid = `need_rate` x enrolled class, so a smaller class spends less need aid. Changing the class target does not change `need_rate`. The Inputs label reads "Need aid: $200,000 at a class of 140 ($1,429 per enrollee; scales with class)". **[v0.6, B3-12]**
- `ntr_target` (optional), `discount_target` (optional, per scenario).
- `risk`: `common_shock_sd` [0.10; illustrative until calibrated, methodology O37], `shock_source` (`illustrative`, `public` or `client`), `shock_corr_above_below` [1.0], `sensitivity_slopes` (placeholder low, middle, high: 0.5, 1.0, 1.5 yield points per $1,000), `yield_floor` and `yield_cap` per score group (placeholders 0.03 and 0.60), `yield_shift_grid` [-3 to +3 points], `pool_grid` [0.8 to 1.6 in steps of 0.1] **[v0.6, B7-4]**, `tuition_grid` [5.0%, 5.5%, 6.0%, 6.5%].
- `pooling_k` [20]: prior weight in admits for base-yield pooling (section 4). **[v0.6, B4-5]**
- `integer_admits`, `integer_enrolled` (true in reproduce mode, false otherwise).
- `evidence_tolerance_usd` [2,500]: sets the observed range for the evidence label (information only).
- `segments`: list, at most one active per scenario. Each: `name` [target_states], `within` (`residency: out` at Richmond; `in` is allowed, for example a public's in-state priority), `members_label` [NY, PA] (a label only; the cell file carries the segment, not the state), `share_source` (`client_counts` or `assumed`; Richmond `assumed` until state-level counts arrive). **[v0.6, B5-1, D13]**
- `trim`: `{protect_segment: below_threshold, floor_rate: 0, exempt_cells: []}`. `floor_rate` is an absolute admit rate. **[v0.6, B1-5, B1-16]**
- `pool_ytd_growth`: annotation shown beside the pool strip, defined as growth in complete applications at or above `score.pool_threshold`, this cycle against the mean of the prior two cycles at the same week of the cycle, with the label "growth to date; final growth may differ if applicants file earlier or later than last year". No logic reads it. **[v0.6, B3-4]**
- `small_cell_suppression: none` (Richmond).

**Cell data (`cells.csv`, long format).** One row per cell x cohort: `cell_id, residency, segment, score_lo, gpa_class, cohort, apps, admits, award_usd, enrolled`. `residency` is `in` or `out`; `segment` is blank or the name of a configured segment and must lie within its `within` residency. Applications are complete applications; admits include waitlist admits, counted in the cohort applied to; enrolled is census enrollment (methodology Appendix F). Cohorts: three actuals. Cell order: residency (in, out), segment (blank first), `score_lo` descending, GPA class (hi, lo, blank); the workbook uses the same order. The fixture loader leaves `segment` blank on every cell.

**Scenario file (`scenarios.yaml`).** Per scenario: `name`, `parent`, `description`, `pool_multiplier`, `specialty_usd`, `need_total` (optional override), `tuition_increase_pct`, `award_scale_with_tuition` (default false: fixed dollars, the YA convention; true: base awards scale by 1 + p; the full-tuition rung follows tuition either way), `class_target`, `class_cap`, `bonus_usd`, `bonus_scope` (`residency_out`, `segment` or `none`; default `residency_out`), `bonus_min_score`, `segment` (the active segment's name; defaults to the only configured segment and is an error when several are configured and none is named; a blank cell on Levers means the same default in Excel **[v0.6.2, P2-07]**) **[v0.6.1, OP-5]**, `segment_pool_lift_pct`, `segment_goal`, `yield_shift_pts` with optional `yield_shift_pts_in`, `yield_shift_pts_out` and `yield_shift_pts_segment`, `discount_target`, `plan_year` (default `plan_cycle`; a label in this prototype: tuition comes only from the scenario's `tuition_increase_pct`, which Baseline takes from `tuition_increase_by_year` for its plan year and a child inherits from its parent unless set **[v0.6.1, P1.1-2]**), and per-cell `admit_rate`, `award_usd` and `full_tuition` overrides relative to the parent (the generator materializes full columns). **[v0.6.1, OP-1]** `full_tuition` is a per-cell flag: on Baseline it is true where the latest-cohort award is at or above base-cycle tuition; a child inherits its parent's flags unless it overrides them; the Levers sheet shows it as an editable column beside `award_usd`. While the flag is set the cell's award is tuition and any `award_usd` entered there is ignored, in Python and Excel alike; the Checks sheet lists each such cell ("award entered on a full-tuition cell is ignored; clear the flag to use it"). An award override does not change the flag **[v0.6.1, P1.1-1]**. Baseline is scenario 0: admit rate and award from the latest cohort, tuition at the plan year, yield from the response base. **[v0.6, B5-1, B7-8]** (v0.5 names: `oos_bonus_*` became `bonus_*`; `target_*` became `segment_*`; `tier_yield_offset_pts` is removed and its use is covered by `yield_shift_pts_segment`.)

## 3. Reference ledger (Python is the definition; Excel mirrors it)

For scenario s, cell c and case k in {low, middle, high}:

1. `tuition_s = round_to(tuition_base x (1 + p_s), tuition_rounding_usd)`
2. `apps_sc = apps_c,base x pool_mult_sc x (1 + segment_lift_s x [cell c in the active segment])`, where `pool_mult_sc` is `pool_multiplier_s` if `score_lo_c >= score.pool_threshold` and 1 otherwise. The lift applies at all scores, after the pool multiplier.
3. `admits_sc = apps_sc x rate_sc`, rounded when `integer_admits`
4. `award_base_sc`: the lever award; if the cell's `full_tuition` flag is set it equals `tuition_s` **[v0.6.1, OP-1]**; otherwise `award x (1 + p_s)` when `award_scale_with_tuition` and `award` otherwise, then `min(., tuition_s)`. `award_sc = min(award_base_sc + bonus_s x [eligible_sc], tuition_s)`, where `eligible_sc` = in scope (`[residency_c = out]` for `residency_out`; `[c in segment]` for `segment`; never for `none`) and `score_lo_c >= bonus_min_score_s` when set. `incentive_sc = award_sc - award_base_sc` (zero or positive; less than the bonus where the cap binds).
5. `yield_sck = clip(response(c, award_sc, k) + shift_sc / 100, yield_floor_g, yield_cap_g)` (section 4), where `shift_sc` is `yield_shift_pts_segment` for a segment cell when set, else the residency override when set, else `yield_shift_pts`. Overrides replace, not add; a blank override inherits (Excel: `IF(cell = "", inherited, cell)`). The response is clipped first and the shifted value is clipped again, in Python and Excel alike **[v0.6.1, R-08a]**. Apart from the shift, yield responds to the award in dollars only; sticker price does not move applications or yield (D10).
6. `enrolled_sck = admits_sc x yield_sck`, rounded when `integer_enrolled`; `class_sk = sum_c enrolled_sck`
7. `merit_sk = sum_c enrolled_sck x award_sc`; `incentive_cost_sk = sum_c enrolled_sck x incentive_sc` (reported separately and included in merit); `need_sk = need_rate_s x class_sk`
8. `gross_y1_sk = class_sk x tuition_s`; `aid_sk = merit + need + specialty_s`; `ntr_y1_sk = gross_y1 - aid`; `discount_entering_y1_sk = aid / gross_y1`; `avg_aid = aid / class`. **[v0.6, B3-1, B3-2]** Names follow methodology Appendix F. The Summary label for the discount rate is "Discount rate (entering class, first year)". `ntr_horizon` (multi-year, with persistence and the renewal rule) is a year-2 build.

Yield is constant when admit rates change (D1). Reproduce mode has no bonus and takes `specialty_s` as the YA lump sum.

**Ratios.** Discount rate, average aid, shares, the barbell index and the incentive shares are ratios of expected values, E[X] / E[Y], everywhere, and the README says so. **[v0.6, B3-5]**

**KPIs per scenario and case.** Class; applications and admits (total, by residency); enrolled at or above each score threshold and below `score.floor`; enrolled with GPA class `hi`; **margin** at each threshold (enrolled with a score at or above t minus enrolled with a score below t; under `unscored_in_median: excluded`, unscored enrollees are in neither term and are shown as a count); share at or above t (expected count at or above t over expected enrolled with a score); full-tuition enrolled (award at or above tuition), **no-merit-award enrolled** (award of zero; need aid is not assigned to cells) **[v0.6, B3-7]**; barbell index = (full-tuition + no-merit-award) / class; Baseline `ntr_y1` minus scenario `ntr_y1` ("price of the target"); incentive block; segment block.

**Tuition what-if (live).** For each `p` in `tuition_grid`: `ntr_y1`, net tuition per student and the discount rate in the Middle case, with the scenario's class and mix held fixed and the award rule above (awards recomputed with `min(., T(p))`). `NTR(p) = sum_c e_c x (T(p) - award_c(p)) - need - specialty`; one `SUMPRODUCT` per grid value. Each row carries "Sticker-price demand effect not modeled." Below the grid, two lines replace the v0.5 net-price block **[v0.6, B7-5, B1-13]**:
- "Awards fixed in dollars: every student below full tuition pays {Ts - T_base} more than at base-cycle tuition."
- "Awards scaled with tuition: a student pays {p} x (base-cycle tuition minus award) more, for example {x} at an award of {A}." The example award `A` is the enrolled-weighted mean **base-cycle** lever award (`award_usd`, not `award_base`) over enrollees whose base-cycle lever award, before any incentive, is below base-cycle tuition and whose cell has no `full_tuition` flag (an unflagged award typed at or above tuition is a full-tuition student, and the comparison must be in base-cycle dollars or the line's `T_base - A` turns negative) **[v0.6.2, Q-5; P1.1-4]**, zero awards included, rounded to $1,000 **[v0.6.1, R-07, OP-7c]**.
Both are arithmetic at constant award; neither changes yield.

**Yield what-if strip (live).** For each shift `d` in `yield_shift_grid`, applied on top of the scenario's own shift, in the Middle case: expected class, P(class > cap), P(class within band of target), mean `ntr_y1`, P(`ntr_y1` at or above target), margin and P(median holds) at each threshold. Closed forms in `d` over Ledger columns, with `y_c` the scenario yield and `A_c` admits:
- `M(d) = sum A_c (y_c + d)`; `V(d) = sum A_c (y_c + d)(1 - y_c - d) + s^2 M(d)^2`, where `sum A_c (y_c + d)(1 - y_c - d) = sum A_c y_c (1 - y_c) + d sum A_c (1 - 2 y_c) - d^2 sum A_c`.
- `NTR mean(d) = sum w_c A_c (y_c + d) - specialty`, `w_c` as in section 5; the NTR variance and median quantities follow the same expansion.
- All `SUMPRODUCT` over existing columns: no array `IF`, no per-shift helper columns.
The strip ignores the yield floor and cap; a count of cells where a bound would bind at the largest shift appears beside it, and a test shows the strip equals the Ledger with the shift entered when the count is zero. **Break-evens (linear, unclipped, labeled "linear approximation"):** the uniform shift that moves the expected class to `class_target`, `(class_target - M) / sum A_c`; and the shift that moves mean NTR to `ntr_target`, `(ntr_target - mean) / sum w_c A_c`.

**Pool strip (live; replaces the v0.5 tripwires).** **[v0.6, B7-4, B1-10]** For each `m` in `pool_grid`, with every scenario lever applied except the pool multiplier, which `m` replaces (the segment lift stays applied): expected class `M(m) = M_lo + m M_hi`, P(class > cap), expected margin `G(m) = G_lo + m G_hi` and P(median holds) at the first score threshold, and mean `ntr_y1`. Every quantity splits the Ledger at `m = 1` into a `lo` part (cells below `score.pool_threshold`) and a `hi` part (cells at or above it), and the `hi` part scales with `m`: `M(m) = M_lo + m M_hi`; `V(m) = V_lo + m V_hi + s^2 M(m)^2` with `V = sum v_c`. For the median at threshold t, split both counts the same way: `G_+(m) = G_+lo + m G_+hi` and `G_-(m) = G_-lo + m G_-hi`, where `G_+` and `G_-` are the expected scored counts at or above and below t. Cells below t can sit in the `hi` part (at Richmond the 165 band is below t = 166 but scales with the pool), so `G_-hi` is not zero in general. Then `G(m) = G_+(m) - G_-(m)` and `V_m(m) = V_m,lo + m V_m,hi + s^2 (G_+(m)^2 + G_-(m)^2 - 2 rho G_+(m) G_-(m))`, with `V_m` the binomial part over scored cells (section 5). **[v0.6, verification Nov 16]** Every figure is a `SUMPRODUCT` on the split columns. Show growth as `m - 1` beside `pool_ytd_growth`. Label: "yield held constant as the pool changes". Readers find where the median or cap stops holding by reading down the strip; no bisection.

**Class-size table (live; shrink path).** **[v0.6, B7-7]** For each N in `class.what_if` up to the scenario's cap: the shrink path (below) writes admit rates and the table shows expected class, margins and P(median holds), `ntr_y1`, discount, segment enrolled, the lowest score band still admitted, admits cut by band, and the proportional factor `f = N / M` as a reference column (what a uniform cut would scale everything by). Rows with N at or above the Middle expected class M show "not applicable (N at or above expected class)"; rows above the cap show "above cap". **[v0.6, B1-19]**

**Shrink path (`trim.py`).** **[v0.6, B1-5, B1-16]** Uses the Middle case.
1. Order: ascending `score_lo` (unscored first), then GPA class (blank, lo, hi); ties among residency and segment break in the order out of state outside the segment, in-state outside the segment, segment. With `protect_segment: below_threshold`, segment cells below the first median threshold t are placed after all non-segment cells below t and before any cell at or above t. `exempt_cells` are never trimmed.
2. Removable enrollment per cell: `rm_k = A_k y_k max(0, r_k - floor_rate) / r_k` for non-exempt cells with `r_k > 0`, else 0 (equivalently `admits_k x y_k x (r_k - floor_rate) / r_k`); `R_k` is its cumulative sum in trim order. `removed_share_k = 0` if `rm_k = 0`, else `MIN(1, MAX(0, (M - N - R_{k-1}) / rm_k))`; `rate_k(N) = r_k - (r_k - floor_rate) x removed_share_k`.
3. Status per N: "OK", or "N not reachable: shortfall {M - N - R_K}" when `M - N > R_K`.
4. Round admits when `integer_admits` and settle the residual in the last cell cut. Cells the walk does not cut keep their input admit rates exactly; rounding never changes a rate the walk did not touch **[v0.6.1, R-05]**.
The rule is deterministic and evaluator-only: it writes admit rates the analyst may overwrite, so D1 holds. The unscored-first order is a policy choice with access implications and the README says so. **[v0.6, B1-24]**

**Segment block.** **[v0.6, B1-8, B1-14, B4-7]** Per scenario and case: segment applications, admits and enrolled `E_S`, segment share of class, segment merit dollars, and `P(E_S >= goal)` with `goal` rounded up to an integer **[B1-17]**. Python computes the probability exactly (convolution of the cell binomials, mixed over the shock by 20-node Gauss-Hermite quadrature). Excel uses the normal form `1 - Phi((goal - 0.5 - M_S)/sqrt(V_S))`, `M_S = sum_S mu_c`, `V_S = sum_S v_c + s^2 M_S^2`, and shows "approximate (fewer than 30 expected)" when `M_S < 30` **[v0.6.1, OP-3]**. 90% range `M_S +/- 1.645 sqrt(V_S)`. Every 90% range's lower end (class, NTR excepted, segment) is clipped at zero **[v0.6.1, R-08b]**. With no cells in the active segment, every segment figure shows "no segment cells in the data" and nothing is divided. Scope `segment` with no segment cells is an error only when `bonus_usd > 0`, `segment_pool_lift_pct != 0` or `segment_goal` is set. When `share_source: assumed`, every segment figure carries "Segment share assumed, not from client data". **[v0.6, B6]**

**Incentive block (one decomposition).** **[v0.6, B1-4, B1-11, B7-9]** Population: cells with `incentive_sc > 0` in scenario s. Against the parent p:
- incentive cost `C = sum_c e_sc x incentive_sc`;
- of which paid to students the parent already enrolled: `C_any = sum_c min(e_pc, e_sc) x incentive_sc`, and its share `C_any / C`;
- additional enrollees `dE = sum_c (e_sc - e_pc)`, change in merit dollars `dSpend = sum_c (e_sc a_sc - e_pc a_pc)`, change in `ntr_y1` over the same cells `dNTR`;
- aid per additional enrollee `dSpend / dE` when `dE >= 0.5`; "savings per enrollee lost" `dSpend / dE` when `dE <= -0.5`; otherwise "change under half a student"; and `dNTR / dE` on the same rule.
- Validity: computed by formula; shows "not valid: parent differs in more than the incentive" unless these equal the parent's: `pool_multiplier`, `specialty_usd`, `need_total`, `tuition_increase_pct`, `award_scale_with_tuition`, `class_target`, `class_cap`, `segment_pool_lift_pct`, `yield_shift_pts`, `yield_shift_pts_in`, `yield_shift_pts_out`, `yield_shift_pts_segment`, `plan_year`, `segment`, and every cell's `admit_rate`, `award_usd` and `full_tuition`. Only `bonus_usd`, `bonus_scope` and `bonus_min_score` may differ (`segment_goal` and `discount_target` are targets, not levers, and are ignored).
- "Bonus implied by a dollar pool" = pool / baseline expected enrolled in scope (informational), shown when the optional scenario input `bonus_pool_usd` is set **[v0.6.2, Q-8d]**.
All of it depends on the placeholder slope and carries `RESPONSE_LABEL`. The figures are what the assumed response implies, not estimates of what an incentive causes. **[v0.6, B4-8]**

**Discount and gap rows.** If `discount_target` is set, the Summary shows the entering-class discount rate and its margin to target. A law-to-undergraduate tuition gap row is not built in v0.6 (deferred with `MultiYear`).

## 4. Response (placeholder in the prototype; the pipeline replaces it later)

**Base yield.** **[v0.6, B4-5, B1-15, B1-6]** Per cell, base award `a0_c` = latest cohort award, and base yield by partial pooling, re-centered at `a0_c` for each case k:

`ybar_c` = the cell's admits-weighted yield over the history cohorts; `abar_c` = its admits-weighted award; `n_c` = its total admits.
`ypool_c` = the admits-weighted yield of the (residency, segment, score group) pool when that pool has at least 30 admits over the history, else the (residency, score group) pool; if that pool has no admits, the score group across residencies; if that has none, all cells **[v0.6.1, R-08c, OP-7b]**.
`y0_ck = (n_c (ybar_c + (b_k / 100)(a0_c - abar_c) / 1000) + k_pool x ypool_c) / (n_c + k_pool)`, with `k_pool = pooling_k` (20). A cell with no admits takes `ypool_c`.

For a candidate award `a`: `yield = clip(y0_ck + (b_k / 100) x (a - a0_c) / 1000, yield_floor_g, yield_cap_g)`.

**Yield method [v0.6.1, R-01].** Python and Excel both compute yield from the formula above, in one Ledger column per case (`yield`), so they agree exactly, including where the floor or cap binds. The Response sheet tabulates yield at award rungs (0, 5,000, ... up to tuition, plus a "full tuition" rung) for each cell and case **for display only**; no Ledger formula reads it. When the pipeline supplies an estimated response as a rung table (section 15 item 3), Python and Excel switch together to linear interpolation between rungs, by changing that one column, and test 3 is re-baselined. **Evidence label:** `observed` if `a` lies within the cell's historical award range plus `evidence_tolerance_usd`, otherwise `extrapolated`; it describes how well the yield is known, never the award, and carries no color, threshold or message. The Summary reports the share of enrolled in `extrapolated` cells (expected enrolled in extrapolated cells over expected class).

**Labels (`sw/labels.py`; each one constant, exact text).** **[v0.6, B4-6]**
- `RESPONSE_LABEL` = "Response based on client-input": every output that depends on the placeholder slope; replaced by the evidence status once the pipeline supplies an anchored response.
- `ASSUMPTION_LABEL` = "Includes client-input assumptions (yield shift, application lift)": any scenario with a non-zero shift or lift, in every evidence state.
- `SHOCK_LABEL` = "Year-to-year variation assumed (s = {s}), not yet calibrated": beside every probability and range while `shock_source` is `illustrative`. While it applies, probabilities below 5% or above 95% show as "under 5%" or "over 95%". **[v0.6, B4-7]**
- `SEGMENT_SHARE_LABEL` = "Segment share assumed, not from client data".
- Range kinds (README and every range label): "90% outcome range" (enrollment noise and year-level variation, Middle case); "Low and High price-response cases" (placeholder slopes now); kinds are never combined. **[v0.6, B4-9]**

Awards may differ from any prior value by any amount; there is no cap on award moves. Marginal-admit yield is not modeled: yield is constant when admit rates change. Expose `marginal_admit_yield_slope` (default 0), read and ignored with a note when non-zero.

## 5. Risk functions (closed form, validated against simulation)

Independent binomial enrollment by cell given admits and yield, plus a common multiplicative year shock. With `mu_c = A_c y_c`, `v_c = A_c y_c (1 - y_c)`, `Phi` the standard normal CDF, `s` = `common_shock_sd`:

- **Class:** `M = sum mu_c`; `V = sum v_c + s^2 M^2`. `P(class > cap) = 1 - Phi((cap + 0.5 - M)/sqrt(V))`. `P(|class - target| <= band) = Phi((target + band + 0.5 - M)/sqrt(V)) - Phi((target - band - 0.5 - M)/sqrt(V))`. 90% range `M +/- 1.645 sqrt(V)`.
- **Median holds at threshold t:** `g_c = +1` if `score_lo_c >= t`, `-1` if below, and 0 for unscored cells under `unscored_in_median: excluded` (`-1` under `below`). `m = sum g_c mu_c`; `G_+` and `G_-` the expected counts at or above and below t. `V_m = sum_{g != 0} v_c + s^2 (G_+^2 + G_-^2 - 2 rho G_+ G_-)`, with `rho = shock_corr_above_below`; at `rho = 1` this is `sum v_c + s^2 m^2`, which v0.5 approximated by `sum v_c`. `P(median >= t) = 1 - Phi((-0.5 - m)/sqrt(V_m))`. The Summary adds one sensitivity line at `rho = 0.5`: "if high-score and other admits' yields move differently year to year". Same form for GPA with `g_c = +1` for class `hi`. Tie rule: holds when at least half of the scored class is at or above t. **[v0.6, B4-2, B3-3]**
- **NTR (`ntr_y1`):** `w_c = tuition - award_c - need_rate`; `mean = sum w_c mu_c - specialty`; `V_n = sum w_c^2 v_c + s^2 (sum w_c mu_c)^2`. `P(NTR >= target) = 1 - Phi((target - mean)/sqrt(V_n))`.
- **Segment enrolled:** section 3.

**Simulation (`mc.py`, tests only).** **[v0.6, B1-9]** Per draw, `e ~ Normal(1, s)`; each cell's yield is `clip(e x y_c, 0, 1)`; enrollment `~ Binomial(A_c, clipped yield)`, independent across cells given `e`. For `rho < 1`, draw `e_+` and `e_-` for cells at or above and below t with correlation `rho`. The closed-form `s^2 M^2` matches this model up to a small overstatement (`s^2 sum A_c y_c^2`). Fractional admits (live mode) enter the exact and simulated models as `Binomial(floor(A_c), y) + Bernoulli(frac(A_c) x y)`; the mean is exact and the variance differs from `A_c y (1 - y)` by `frac x y^2 (1 - frac)`, which is small **[v0.6.1, R-08d, OP-7a]**.

**Validation already run on the YA fixture (Scenarios 1, 2, 4, from `ya_workbook_support/analysis.py`):** normal vs simulation within 0.01 for P(median at 166) 0.66, 0.61, 0.68; P(class above 140) 0.42, 0.22, 0.41 vs 0.42, 0.22, 0.40; P(NTR at least $4.5M) 0.32, 0.23, 0.43 vs 0.31, 0.23, 0.43; with s = 0.10, class SD 17.07 (formula) vs 17.0 and NTR SD $0.558M vs $0.56M (Scenario 1). These used the v0.5 median rule (unscored below, no shock term).

## 6. Workbook sheets (XlsxWriter)

General: no hidden rows or columns; no conditional format or message that characterizes an award as unusual (a neutral highlight of cells changed from the parent is allowed); inputs unlocked and blue; formula cells locked; sheet protection with no password; named ranges for every Inputs cell; freeze panes; print setup; consistent number formats. Formulas use `ROUND`, `SUM`, `SUMPRODUCT`, `INDEX`, `MATCH`, `MIN`, `MAX`, `IF`, `SQRT`, `NORMSDIST`, `TEXT`, `ROW` and `&`; no dynamic arrays, no `LET`/`LAMBDA`, no macros, no volatile functions. Helper columns per N are allowed on `Trim`. Write each formula with its cached value from the Python ledger so previews show numbers. **[v0.6, B1-20]** Workbook document properties use a fixed creation time derived from the build id, so two builds of the same inputs differ only in `RunLog`. **[v0.6, B5-3]**

| Sheet | Content |
|---|---|
| `README` | Purpose, how to use, color key, every label and range kind (section 4), metric names and definitions (methodology Appendix F), what is static and what is live, policy choices (unscored trimmed first; unscored excluded from medians), build id |
| `Inputs` | Section 2 config values as named inputs; case selector (Low, Middle, High) for display; mode switch (Live, Reproduce) |
| `History` | Cell x cohort panels: applications, admits, admit rate, award $, award % of tuition, yield, enrolled; totals by residency, segment and overall; tuition row |
| `Response` | Per cell: `a0`, `ybar`, `abar`, `n`, pool yield, `y0` by case, observed award range, evidence label; rung grid with yield at each rung for Low, Middle, High, for display only (R-01) |
| `Levers` | Header rows per scenario (section 2 scenario fields). Body per cell (residency and segment in their own columns): `admit_rate`, `award_usd` and `full_tuition` inputs. Neutral highlight of cells that differ from the parent; a "cells changed from parent" count that excludes award entries ignored under a full-tuition flag, which are counted and marked separately ("award entry ignored: full-tuition flag set") **[v0.6.2, P2-03]** |
| `Ledger_Low`, `Ledger_Middle`, `Ledger_High` | Per cell, per scenario block: apps, admit rate, admits, award base, incentive, award, yield (formula, one column; R-01), evidence label, enrolled, spend, score-group flag. Totals row. Formulas per sections 3 and 4; the mode switch selects live yield or the `Reproduce` override |
| `Summary` | KPIs and probabilities for Baseline and each scenario (Middle case in the main block; Low and High for class, `ntr_y1`, P(median)); price-of-target row; evidence row; tuition what-if with the two net-tuition lines; yield strip and break-evens; pool strip; class-size table (shrink path); segment block; incentive block; discount row; labels; narrative rows |
| `Trim` | Live mode only: cells in trim order with `rm_k` and `R_k`; per N, `removed_share_k`, `rate_k(N)`, helper columns and per-N summaries by `SUMPRODUCT` |
| `Distribution` | Full-tuition and no-merit-award counts, barbell index, share of merit dollars to the top quartile of enrolled by academic position (cells ordered by `score_lo`, then GPA class; weighted by expected enrolled). **Step sizes:** award difference between adjacent score bands within each residency x segment x GPA class (segment and non-segment cells at the same band can carry different awards in the fine matrix; P1.1-3), per scenario, as a plain table with no threshold, color or message |
| `Checks` | Section 7 |
| `Reproduce` | Reproduce mode only: YA yields, admit rates, awards and pool settings as loaded values |
| `RunLog` | Build id, git commit (and the list of uncommitted files, if any), config hash, data hash, `requirements.lock` hash, code hash, timestamp, response source label, shock source. The build id hashes the config, data, `requirements.lock` and `sw/*.py`, so two workbooks share an id only if they are the same apart from the timestamp **[v0.6.2, P21-03]** |

## 7. Checks sheet (each returns OK or a message)

Integrity only; nothing comments on an award. Totals of cell rows equal totals rows; admits at most applications; enrolled at most admits; award at least zero and at most tuition after the incentive; yield between 0 and 1; tuition formula reproduces the history steps; class against cap and band (reported as a result, not a warning); spend against `budget_total` when set, comparing total aid (merit + need + specialty) by default (`budget_basis: total_aid`, the default) or merit only (`budget_basis: merit`) (Brandon to say which Richmond's figure covers; OD-10) **[v0.6.2, Q-8e]**; history reconciliation (grid-implied merit against `merit_actual_by_cohort`, an optional config input, when provided; percent gap) **[v0.6.2, Q-8f]**; the full-tuition award conflict (P1.1-1); `bonus_scope: segment` with no segment cells and a positive bonus, lift or goal (the Python error, shown as a Check) **[v0.6.2, P2-07]**; "rebuild needed" when any build-time input (first median threshold, `protect_segment`, exempt cells, each scenario's active segment) differs from its value at build, and a stale flag on the static exact segment probability when the segment's expected enrollment, its goal or its set of cells differs from its build value **[v0.6.2, P2-06, P21 call 1]**; Summary class equals Ledger total; segment cells lie within their `within` residency; class target at most the cap.

## 8. Narratives

Python and Excel versions of two templates per scenario, populated from live cells:
- **Changes from parent:** "Pool multiplier {x}. Awards changed in {n} cells; admit rates changed in {m} cells." Baseline reads "Baseline: no parent scenario." Ignored award entries on full-tuition cells are reported as "{k} award entries ignored: full-tuition flag set." (singular when k is 1) **[v0.6.2, Q-6, P2-03]**
- **Projected outcome:** "Class {N} (90% outcome range {lo} to {hi}). {score measure} median {t}: margin {margin}, probability {p}. GPA median {g_t}: margin {g}, probability {pg}. {k} enrolled below {floor}. Full-tuition {ft}, no merit award {nm}. First-year NTR {x}M (90% outcome range {lo}M to {hi}M) **[v0.6.2, Q-6]**, discount rate (entering class, first year) {d}%. Tuition {T} (+{p}%); class target {target} (cap {cap}); incentive {b} ({scope}); {segment name} enrolled {E_S}. Evidence: {share}% of enrolled in cells where the yield is extrapolated." followed by the labels that apply.

## 9. Reproduce mode (acceptance test against the YA fixture)

`reproduce.py` reads the YA workbook (read only) and builds a workbook in which the Ledger runs with YA's admit rates, awards, yields and pool settings as client-input values.

**Fixture layout (verified October 30 file).** Sheet `Client Strategy Comparison`: six panels, each 12 columns wide starting at columns B (admit rate), O (admits), AB (award %), AO (award $), BB (yield), BO (enrolled); within a panel the columns are 2024, 2025, 2026, Baseline, Scenarios 1 to 8. Rows 7 to 40 are in-state cells and rows 59 to 92 are out-of-state; column A holds the cell label. Ignore rows 41 to 56, 93 onward (`#N/A` filler). Applications are not in the file: use `admits / admit rate` for 2026 where the rate is above zero (cells with no admits cannot be recovered). Tuition by cohort: award $ / award %. Sheet `Client Scenarios`: scenario columns AH (S1), AP (S2), AX (S3), BF (S4); rows 179 to 183 hold gross, merit, need, specialty and total aid; row 186 NTR; row 189 the narrative text. Pool multipliers apply at LSAT 165 and above; need over a reference class of 140; Scenario 4's NY and PA item is a specialty lump sum. Scenarios 5 to 8 are empty; skip them. The file has residency only: every cell loads with a blank segment, and Scenario 4's specialty stays a lump sum.

**Reproduce settings.** `unscored_in_median: below` (the YA counting rule; confirm on load and report), integer admits and enrolled, YA yields as loaded values.

**Pass criteria (Scenarios 1 to 4 and Baseline where derivable):** class equal; merit spend equal; NTR within $100 (observed gap $60); enrolled at or above 166, 165, 154, 3.83 and below 154 equal to the file's counts and narrative; full-tuition and no-merit-award counts equal to the narrative (21 and 14; 15 and 11; 10 and 11; 9 and 13); LSAT and GPA margins equal to the narrative. Report every mismatch; do not tune to force a match.

## 10. Synthetic cell-level generator and shape targets

Generate three cohorts of cell-level counts for the Richmond-like band grid, plus a hidden true response slope (default 1.2 points per $1,000, configurable) used only to make enrolled counts. Seeds fixed. Do not use `efa_fao/src/synth`. These **ranges** come from the fixture and set the generator's targets (`config/shape_targets.yaml`; provenance in `docs/shape_targets.md`). Rows marked **asserted** must hold in at least 90% of 20 seeds for Phase 1 acceptance; the others are reported, not asserted. **[v0.6, B6]**

| Feature | Target range | Asserted? |
|---|---|---|
| Residency | Out-of-state is 67% to 72% of applications and admits; its share of enrolled is 49% to 53% and falling; yield about 0.15 out-of-state and 0.33 to 0.35 in-state | **Asserted** |
| Admit rates by score group | 165 and above: 0.94, 0.85, 0.79 across the three cohorts (falling); below 165: 0.33, 0.30, 0.25 | Reported |
| Admit rates by GPA | 3.83 and above 0.79 to 0.85; below 3.83 0.22 to 0.31 | Reported |
| Yield by group | 165+ 0.18 to 0.21; below 165 0.22 to 0.23; GPA 3.83+ 0.12 to 0.20; below 3.83 0.23 to 0.29; overall 0.209 to 0.214 | **Asserted** |
| Applicant pool | About 1,450 to 1,630 applications; 165+ share rises from about 0.18 to 0.27 | Reported |
| Awards | Admit-weighted award as a share of tuition: 165+ 0.98, 0.87, 0.79; below 165 0.32, 0.26, 0.25; fixed-dollar rungs; top rung equals tuition; tuition grows about 3.7%, 4.0%, 6.0% | Reported |
| Class | 133 to 146 per cohort; share of enrolled at 165+ rises from about 0.35 to 0.53 | **Asserted** (class range only) |
| Cell sparsity | Median 8 to 12 admits per active cell; about 45% to 55% of active cells under 10 admits; about 90% or more under 10 enrolled | Reported |
| **Confounding** | Cross-sectional admit-weighted slope of cell yield on award share: raw about -0.04 to -0.17 points per $1,000; adjusted for score group, GPA class and residency from -0.9 to +0.1 | Reported (R-06) |

Source for each row: fixture sheets 1 and 2 and the October to November 2026 analysis (`ya_workbook_support/analysis.py`). Adopting these in the main S2 world definitions (W0L) is a separate change.

**Segment.** The generator assigns each out-of-state cell's applications to the segment with `segment_share_of_out` by score group (placeholder 0.25, a synthetic assumption), `segment_yield_offset_pts` (0) and `segment_apps_trend` (0). No new range comes from the fixture. Generate scenarios at class targets of 100, 110, 120, 130 and 140 under a cap of 140, including worlds whose expected class is below 140.

## 11. Tests (`pytest`)

1. **Ledger unit tests:** each identity in section 3 on a 6-cell toy grid (one segment cell) with hand-computed answers, including the cap on `award_base` and on the incentive.
2. **Risk unit tests:** on a toy grid with expected class at least 25, the closed forms against the exact convolution (tolerance 0.01; the class-band probability is asserted only where the expected class is at least 50, on a second toy grid built for that purpose, and reported on the small grid **[v0.6.1, OP-3, P1.1-5]**) and the simulation against the exact convolution (tolerance 0.005, 200,000 draws). **[v0.6, B1-22]**
3. **Excel equals Python:** build from a synthetic world; recalculate with a dedicated LibreOffice profile (`-env:UserInstallation=file://<tmp profile>`) whose `registrymodifications.xcu` sets `/org.openoffice.Office.Calc/Formula/Load/OOXMLRecalcMode` to 0; read with `openpyxl(data_only=True)`; compare every Ledger and Summary numeric cell to Python (exact for integers, 1e-6 relative for floats). Guard: build one copy with every cached value set to -999 and assert that none survives recalculation. **Edge workbook [v0.6.2, P2-01]:** test 3 also compares, cell by cell, a third workbook built to reach every branch: `floor_rate` 0.2 with exempt cells, `rho` 0.5, a segment pool at exactly the pooling threshold, a shift large enough that some cells hit the yield cap and others the floor, an in-state override, a `need_total` override, a non-integer segment goal, an unflagged award above tuition, a child differing from its parent only in one `full_tuition` flag, and `what_if` sizes low enough to produce a shortfall. **Desktop Excel:** `tests/compare_excel_saved.py <path>` compares a copy saved by desktop Excel after recalculation with Python at the same tolerances (run by hand; Phase 2 acceptance). The copy must start from the sentinel build (every cached value -999), so any cell Excel did not recalculate shows as a mismatch; the script refuses a file that is not a recalculated sentinel build of the current build id **[v0.6.2, P21-01]**. If `soffice` is missing, report and skip. **[v0.6, B1-25]**
4. **Closed form vs simulation on synthetic worlds:** class, median and NTR probabilities within 0.02 for 20 scenarios: one Baseline scenario on each of 20 worlds from `synth_cells.py` with a fixed seed set listed in `config/synthetic.yaml`, each with a pool multiplier, a bonus and a yield shift drawn from that file's stated ranges; median probabilities at `rho` 1.0 and 0.5 (class and NTR have one common shock) **[v0.6.1, OP-4]**.
5. **Shape calibration:** the asserted rows of section 10 hold in at least 90% of 20 seeds; the other rows are reported. This checks that the stopgap generator is calibrated to its targets; it does not test realism, because the generator steers group yields onto them. The confounding row is reported, not asserted, until the law world W0L provides a real check **[v0.6.1, R-06, OP-6]**.
6. **Reproduce:** section 9 pass criteria (skipped without `YA_FIXTURE_PATH`).
7. **Guardrails:** no column named race, ethnicity or gender in any input or output; no student-level fields; no formulas referencing external files; no hidden sheets, rows or columns; no conditional format or cell text that labels an award exceptional, anomalous, out of bounds or beyond a limit; every label in `sw/labels.py` appears where section 4 requires it.
8. **Levers:** with `bonus_usd` zero and the parent's tuition increase, a child equals its parent; the tuition what-if row at the scenario's own `p` equals the Ledger `ntr_y1`; `need_rate` is unchanged when the class target changes; a scenario with shift `d` equals the yield-strip column at `d` when no cell clips; shift 0 equals the parent; the class break-even shift returns an expected class equal to the target when no cell clips; residency and segment overrides apply only to their cells and replace rather than add.
9. **Reconciliation:** every output in the interface contract (section 15, item 11) agrees between Summary, Ledger and a Python dump of the same run.
10. **Rendering:** convert `Summary` to PDF with LibreOffice and save to `output/` for visual review (not asserted).
11. **Segment merge invariance:** with `y0` and `a0` inherited from the unsplit cell (passed through a test-only `base_override` argument of `response.base_yield`, a mapping of cell id to `(y0 by case, a0)` that skips pooling; production code never sets it), splitting out-of-state cells into segment and non-segment cells in any proportion changes no total or probability. Separately, the base-yield pooling of section 4 returns the stated value for cells with 0, 4, 5 and 30 admits and for a segment pool below and above 30 admits. **[v0.6, B1-2]**
12. **Incentive scope:** scope `segment` changes award, merit and incentive cost only in segment cells; scope `residency_out` with no segment cells gives the same awards, yields, class, merit and probabilities as scope `segment` with every out-of-state cell placed in the segment, and as the toy answers in test 1; scope `segment` with no segment cells and a positive bonus raises an error; with a zero bonus it does not. **[v0.6, B1-3, B1-14]**
13. **Segment and incentive:** `segment_pool_lift_pct` changes applications in segment cells only, and 0 equals the parent; Python's exact `P(E_S >= goal)` matches simulation within 0.01; the Excel normal's gap is reported, not asserted; on a scenario that differs from its parent only by the incentive, `dSpend = sum e_s (a_s - a_p) + sum (e_s - e_p) a_p` cell by cell, `C_any <= C`, and `C_any` equals the cell-level sum (including cells where the cap binds and cells below `bonus_min_score`); the validity flag turns "not valid" when any other lever differs. **[v0.6, B1-4, B1-11, B1-23]**
14. **Shrink path:** on 20 synthetic worlds, for each N in `class.what_if` with N < M, the trimmed expected class equals N within 1e-9 (within 1 when `integer_admits`); for N >= M the rates equal the input rates; admits never rise; the order of section 3 is respected; while the walk is in cells below t, the share at or above t is non-decreasing as N falls; with `floor_rate` > 0 or `exempt_cells`, a shortfall is reported when M - N exceeds `R_K`; no cell with zero admits produces an error. **[v0.6, B1-1, B1-5]**
15. **Pool strip:** at each `m`, every strip figure equals the ledger run with `pool_multiplier = m` (no clip, no rounding); probabilities stay in [0, 1]. **[v0.6, B7-4]**
16. **Class range and cap:** ledger, risk, trim and generator run at class targets of 100, 110, 120, 130 and 140; `need_rate` is unchanged; `P(class > cap)` uses the cap; a target above the cap and a target outside `reject_range` are rejected; a target outside `supported_range` carries the notice.
17. **Empty segment:** a run with no segment cells (as in reproduce mode) produces no NaN, no division error and the "no segment cells in the data" text in every segment figure. **[v0.6, B1-14]**
18. **Excel equals Python for the v0.6 blocks (Phase 2, with test 3):** segment block, incentive block, class-size table, pool strip, the two net-tuition lines.
19. **Output coverage [v0.6.1, R-02, R-03, R-04]:** every figure in the interface contract (section 15 item 11) has a Python test with a hand-computed or exact value that fails if its formula changes, at points where the formula can fail: the 90% ranges (class, NTR, segment); segment variance; `p_median_t_rho05`; the evidence label; the incentive `dNTR` and `ntr_per_additional`; the tuition what-if at every grid value, not only the scenario's own (awards recomputed at `T(p)`, discount column); the scaled net-tuition line; the yield strip's medians, clip count and both break-evens; the pool strip at `rho` below 1 and its NTR spread; the residency override replacing (not adding); the clip after the shift; trimmed rates at a positive `floor_rate`; integer settling, including that uncut cells keep their rates (R-05).
20. **Mutation check [v0.6.1]:** `tests/mutation_check.py` (run on demand, not in the default `pytest` run) applies the mutants listed in `Review_Phase1_Build.md` Appendix A one at a time to a scratch copy and reports which survive. Acceptance: no survivor except those recorded as unable to change any result on valid input.

## 12. Phases, acceptance and hooks

| Phase | Deliverable | Accept when |
|---|---|---|
| 1 | `ledger.py`, `risk.py`, `response.py`, `trim.py`, `strip.py`, `mc.py`, `synth_cells.py`, `labels.py`, configs, `requirements.lock`; the segment in the cell schema, ledger, response and generator; segment and incentive blocks; class range under the cap; tests 1, 2, 4, 5, 11 to 17 | Tests pass; asserted shape targets met |
| 1.1 | Fix pass from `Review_Phase1_Build.md`: R-01 (no Python change), R-02 to R-05, R-07; tests 19 and 20 **[v0.6.1]** | All tests pass in the project `.venv`; the mutation check shows no surviving mutant except those listed as unable to change a result |
| 2 | `workbook.py` and `narrative.py` with README, Inputs, History, Response, Levers, Ledger x3, Summary, Trim, Checks, RunLog; tests 3, 8, 9, 18 | Excel equals Python on synthetic worlds; Jason opens the file in desktop Excel |
| 3 | `reproduce.py`, Reproduce sheet, test 6 | Section 9 criteria met, or mismatches reported with causes |
| 4 | Distribution sheet, tests 7 and 10 | Tests pass; Jason reviews the PDF render |
| Then | Live Richmond build on Richmond's cell data (outside this spec; data handling by Jason). Needs Richmond's published tuition by cohort and the 2027 figure (OD-09) in `config/richmond.yaml`, which stay null until then **[v0.6.1, OP-8]** | Jason's review |

Deferred (no stubs): `Schedule` and `schedule.py`; goal-seek; `Static_MC`; `MultiYear` and `Trajectory`; `ntr_horizon`; per-state segments; the pipeline Response table (same sheet layout, evidence labels `estimated` or `extrapolated`); marginal-admit yield; net-price yield response; pacing import; `Market`; `Frontier`; an admit-rate dimension in the optimizer; the dashboard add-on; USNWR planner link. See `DECISIONS.md`.

## 13. Decisions

| ID | Question | Status |
|---|---|---|
| D1 | Admissions levers | Decided (Nov 4): evaluator inputs; constant yield when admit rates move; the shrink path writes rates and is not an optimizer. Goal-seek deferred (Nov 16) |
| D2 | Guardrail | Removed (Nov 4); evidence label kept as information; step sizes as a plain table |
| D3 | Small cells | Shown to Richmond's named roles in every view (Nov 4 and 5); files go only to those roles (Nov 16, B2-3; Cat to confirm) |
| D4 | Tuition migration | A scenario lever plus a by-year input; reproduce mode 6.0%; Richmond planning 5.5%, unconfirmed (Nov 13) |
| D5 | Class size | Target under a hard cap (140 this cycle); supported range and table 100 to 140; need aid scales per enrollee (Nov 5, revised Nov 13) |
| D6 | Slopes 0.5, 1.0, 1.5; shock SD 0.10; yield floor and cap | Placeholders, labeled (Nov 16) |
| D7 | Budget figure | Unknown; `budget_total` optional |
| D8 | Sheet protection | On, no password |
| D9 | Geography | One priority segment per scenario (Richmond: NY and PA combined), one incentive aimed at the segment or all out-of-state, optional segment lift; finer geography waits for data (Nov 13; generalized Nov 16) |
| D10 | Sticker-price demand effect | Not modeled; tuition changes NTR arithmetic only; net-price response deferred |
| D11 | Awards when tuition moves | Fixed dollars by default; per-scenario toggle to scale |
| D12 | Independent yield lever | Shift in points, global with residency and segment overrides; strip -3 to +3; two linear break-evens |
| D13 | Segment in the foundation | Decided (Nov 13); generalized from "target-state tier" to "priority segment" (Nov 16) |
| D14 | Class range and shrink path | Decided (Nov 13); segment cells protected below the median threshold only (Nov 16, B1-16) |
| D15 | Pool tripwires | Replaced by the pool strip (Nov 16, B7-4) |
| D16 | Net-price readouts | Replaced by two lines in the tuition what-if (Nov 16, B7-5) |
| D17 | Segment application lift | Included, default 0 (Nov 13) |
| D18 | Base yield | Partial pooling (k = 20), re-centered at the latest award (Nov 16, B4-5, B1-15) |
| D19 | Median basis | Unscored excluded by default, pending the 509 instructions; reproduce mode uses the YA rule (Nov 16, B3-3) |
| D20 | Deliverable order | Workbook first; dashboard as an add-on after the core computation (Nov 16) |

## 14. Handling and report-back

The YA file is Richmond-provided with permission, but it is YA's work product: use our own layout and wording; do not reproduce their text or branding. Anything that reproduces its cell values stays out of git. When done, report what was built per phase, test results (including skips and why), dependencies added, the closed-form-versus-exact tolerances achieved, mismatches in reproduce mode with the likeliest cause, and anything in this spec that proved ambiguous or wrong. Workbooks that go to a client need Jason's review first.

## 15. Integration with the pipeline and the other deliverables

1. **One evaluator.** The ledger is the single reference evaluator of any award grid. The optimizer's `ntr_y1`, class and first-year spend for a grid equal the ledger's; `ntr_horizon` will equal the multi-year sheet's when built. **[v0.6, B3-1]** The workbook, the policy document and any later dashboard read ledger outputs; none recomputes them.
2. **Cell data.** The pipeline's cell aggregate needs `award_usd` and `segment` by cell and cohort, and an unsuppressed variant for Richmond's named roles.
3. **Response.** The pipeline supplies a table per cell x award rung x case with an evidence label, plus the anchored slope and its uncertainty (`b_L`, `b_M`, `b_H` replace the placeholders).
4. **Policy of record at the fine matrix.** The optimizer works on a decision layer of about 13 award groups plus one incentive (at most floor(admits / 30) parameters; about 15 at a class of 100). The segment is not a decision dimension; the incentive carries it.
5. **Policy document.** Carries the award matrix, the incentive with its scope, and the segment definition. Admit rates and pool multipliers appear in a separate planning-assumptions block.
6. **Step sizes** appear as a plain table (Distribution sheet and policy document); no flag, no threshold.
7. **Synthetic data.** `synth_cells.py` is a stopgap until the law world (W0L) exists.
8. **Sequencing.** Every response-dependent figure carries `RESPONSE_LABEL` until the pipeline's response replaces the placeholder. The workbook evaluates scenarios and recommends nothing.
9. **Levers shared by the deliverables.** Tuition migration, class target and cap, the incentive and its scope, the segment lift and the yield shift, each computed by the ledger.
10. **Richmond data needs.** Aggregate application, admit and deposit counts by state (by LSAT band if available) for the last three cycles; weekly pacing of complete applications (by LSAT band), admits and deposits against the prior two cycles at the same week of the cycle; the exact 2027 tuition and the planned path; the planned class size path. (Data handling: Jason.)
11. **Interface contract.** **[v0.6, B1-12]** Every figure the policy document or a later dashboard reads. Test 9 enumerates this table. Grain "s x k" means per scenario and case. **Named ranges (canonical) [v0.6.2, Q-1]:** each name's range is the prefix in the Source column plus the name in upper case; where the Source column shows a short form (for example `SUM_PCAP`), read it as the prefix only (`SUM_P_CLASS_OVER_CAP`). There are no aliases. Each name's Summary range is the prefix in the Source column plus the name in upper case (for example `class_lo90` → `SUM_CLASS_LO90`, `incentive_paid_anyway` → `INC_INCENTIVE_PAID_ANYWAY`, `pool_strip[m]` → `PS_POOL_STRIP`); scenario, case and grid value are the range's columns and rows, not part of the name. The Python function returns a dict keyed by the same names.

| Name | Unit | Grain | Source (Summary named range) | Python | Label |
|---|---|---|---|---|---|
| `class_mean`, `class_lo90`, `class_hi90` | students | s x k | `SUM_CLASS_MEAN`, `SUM_CLASS_LO90`, `SUM_CLASS_HI90` | `risk.class_dist` | SHOCK_LABEL |
| `p_class_over_cap`, `p_class_in_band` | probability | s x k | `SUM_PCAP`, `SUM_PBAND` | `risk.class_probs` | SHOCK_LABEL |
| `margin_t`, `p_median_t`, `p_median_t_rho05` | students; probability | s x k x t | `SUM_MARGIN_*`, `SUM_PMED_*` | `risk.median` | SHOCK_LABEL |
| `share_at_or_above_t`, `unscored_count` | ratio; students | s x k x t | `SUM_SHARE_*` | `ledger.kpis` | ratio of expected values |
| `gross_y1`, `merit`, `need`, `specialty`, `aid`, `ntr_y1`, `discount_entering_y1`, `avg_aid` | USD; ratio | s x k | `SUM_*` | `ledger.money` | RESPONSE_LABEL where award-dependent |
| `p_ntr_y1_ge_target` | probability | s x k | `SUM_PNTR` | `risk.ntr` | SHOCK_LABEL |
| `full_tuition_n`, `no_merit_award_n`, `barbell` | students; ratio | s x k | `SUM_FT`, `SUM_NM`, `SUM_BB` | `ledger.kpis` | |
| `segment_enrolled`, `segment_lo90`, `segment_hi90`, `p_segment_goal`, `segment_share` | students; probability; ratio | s x k | `SEG_*` | `ledger.segment`, `risk.segment_exact` | RESPONSE_LABEL, SEGMENT_SHARE_LABEL |
| `incentive_cost`, `incentive_paid_anyway`, `incentive_paid_anyway_share`, `additional_enrollees`, `aid_per_additional`, `ntr_per_additional`, `incentive_valid` | USD; students; ratio; flag | s x k | `INC_*` | `ledger.incentive` | RESPONSE_LABEL |
| `tuition_whatif[p]` (`ntr_y1`, net tuition per student, discount), `net_tuition_line_fixed`, `net_tuition_line_scaled` | USD; ratio | s x p | `TW_*` | `strip.tuition` | "Sticker-price demand effect not modeled." |
| `yield_strip[d]`, `breakeven_shift_class`, `breakeven_shift_ntr` | mixed | s x d | `YS_*` | `strip.yield_strip` | ASSUMPTION_LABEL, SHOCK_LABEL |
| `pool_strip[m]` | mixed | s x m | `PS_*` | `strip.pool_strip` | "yield held constant as the pool changes" |
| `class_table[N]` | mixed | s x N | `CT_*` | `trim.class_table` | |
| `evidence_extrapolated_share` | ratio | s x k | `SUM_EVID` | `response.evidence` | |
| `p_segment_goal_exact` | probability | s x k | Python only (`risk.segment_exact`); the workbook shows a static copy with the stale flag (P2-06) | `risk.segment_exact` | RESPONSE_LABEL **[v0.6.2, Q-2]** |
| `award_matrix` (resolved award, after the full-tuition flag and incentive), `step_sizes` | USD | s x cell | `Levers` `AWARD_MATRIX` block **[v0.6.2, Q-3]**, `Distribution` | `ledger.awards` | |
