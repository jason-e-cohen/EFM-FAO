# Prototype spec v0.2: formula-driven scenario workbook (for Claude Code)

**Date:** November 4, 2026 (v0.2 adds Jason's decisions of the same day and supersedes v0.1) | **Owner:** Jason Cohen | **Status:** draft for Jason's review | **Reads with:** `CLAUDE.md`, `Richmond_YA_Scenario_Workbook_Assessment.md` (sections 3, 4, 11), `02_methodology_v2.6.md` section 5

## 0. Purpose, scope, rules

**Purpose.** Build a Python program that generates an Excel scenario workbook with live formulas: it reproduces the panels of the Yellow Arrows (YA) Richmond workbook, then adds risk probabilities, evidence labels, distribution metrics and checks. The prototype proves the ledger and the risk formulas on synthetic data and on the YA file as a validation fixture. It does not estimate price response; a placeholder response table stands in for the pipeline.

**In scope (this spec):** reference ledger and risk functions in Python; a geography overlay; a schedule layer that expands a few award parameters into the fine matrix; an admit-rate goal-seek helper; workbook generator; reproduce mode; synthetic cell-level data generator; tests. **Out of scope:** the estimation pipeline, the award optimizer, an admit-rate dimension in the optimizer (evaluator inputs and goal-seek only for now), Supabase, dashboard, pacing import (pool growth is a manual input; Slate pacing is a later addition), the Market sheet (509 gap), the Frontier sheet, any USNWR link (a possible future law-product feature). Hooks are listed in section 12.

**Decisions in force (Jason, Nov 4, 2026).** (1) Admit-rate levers are scenario inputs that map onto the YA approach and report YA-style margins and uncertainty. (2) The fixed 5% guardrail is removed as a constraint and as a flag: the prototype never labels an award exceptional, anomalous or out of bounds. (3) Policy is expressed at the client's fine matrix; geography is a dimension. (4) No small-cell suppression: the workbook and the hosted dashboard show small cells to authenticated client staff, enrollment team and leadership included. (5) The Excel workbook, the dashboard and the policy document must agree everywhere (section 15).

**Rules for the build**
1. Code lives under `prototypes/scenario_workbook/`. Do not modify `efa_fao/src/`, `efa_fao/config/`, or any existing spec document.
2. Use the project environment (`.venv`, Python 3.12). Add `xlsxwriter`, `openpyxl` (read only), `pyyaml` and `pytest` if missing. Report each dependency you add.
3. The YA workbook (`Richmond Law - 2027 Scenarios for Client.xlsx`) is a validation fixture only. Never copy its cell values into code, config, test data or documentation. Read it at test time from the path in env var `YA_FIXTURE_PATH`; tests that need it skip when the variable is unset. `fixtures/` and `output/` are git-ignored; keep them that way.
4. Shape refinements to the synthetic generator use ranges and parameters only (section 10). Record each in `docs/shape_targets.md` with its source and range.
5. No protected attributes anywhere (race, ethnicity, gender). No student-level data: the prototype works on cell-level and market-level counts.
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
  sw/reproduce.py                YA fixture loader and comparison
  tests/                         section 11
  docs/shape_targets.md          provenance of each shape parameter
  fixtures/, output/             git-ignored
```
CLI: `python -m sw.build --config config/richmond_like.yaml --data <cells.csv|synthetic> --out output/scenario_workbook.xlsx` and `python -m sw.reproduce --out output/reproduce.xlsx` (uses `YA_FIXTURE_PATH`).

## 2. Inputs

**Config (`richmond_like.yaml`).**
- `tuition_by_cohort`, `tuition_2027`, `tuition_migration` (default: derived from the two values).
- `lsat_bands`: ordered list with lower bound (170, 167, 166, 165, 161, 158, 154, 152, 0). `gpa_classes`: `hi` (3.83 and above), `lo`, `blank`. Unscored rows (GRE, JD-Next, no score) are supported but default to zero.
- `median_thresholds`: LSAT [166, 165], GPA 3.83. `floor_lsat`: 154. `pool_threshold_lsat`: 165.
- `class_cap`, `class_target`, `class_band` (defaults: cap 140, target 140, band 4; D2 in section 13), `ntr_target`.
- `need_total` (200000), `need_denominator` (140): need = need_total / need_denominator x enrolled class. `specialty_usd` per scenario.
- `common_shock_sd` (default 0.10, illustrative), `sensitivity_slopes` (placeholder low, middle, high: 0.5, 1.0, 1.5 yield points per $1,000), `yield_floor` and `yield_cap` per LSAT group.
- `integer_admits`, `integer_enrolled` (true in reproduce mode, false otherwise).
- `evidence_tolerance_usd` (2500): sets the observed range for the evidence label, which is information only (section 4).
- `markets`: list of `{id, type: state|msa, residency: in|out, label}`; default placeholder: three in-state metro markets and six out-of-state states, plus an implicit `other` per residency. Nothing finer than a state or an MSA appears in outputs.
- `market_targets`: optional per market, a minimum expected enrolled or a change from 2026.
- `goalseek`: `{p_star: 0.80, admit_rate_bounds: [0, 1] per cell, class_floor_from_band: true, objective: min_disruption | max_ntr, max_iterations: 3}`.
- `schedule`: `{award_rounding: 500, default_tiers: derived from the admits-per-group merge in section 6A}`.
- `small_cell_suppression: none`.

**Cell data (`cells.csv`, long format).** One row per cell x cohort: `cell_id, residency, lsat_lo, gpa_class, cohort, apps, admits, award_usd, enrolled`. Cohorts: three actuals (2024 to 2026). Cell order is fixed by (residency, lsat_lo descending, gpa_class); the workbook uses the same order.

**Markets file (`markets.csv`).** One row per market x cohort: `market_id, cohort, apps, admits, enrolled`. The generator derives `share_{m|r,g}`, the market's share of admits within residency r and LSAT group g (165 and above, below 165); shares sum to 1 within each (r, g). Where the file has no LSAT split, shares are by residency only. Independence of market and the LSAT x GPA cell within (r, g) is an assumption that the README states.

**Scenario file (`scenarios.yaml`).** Per scenario: `name`, `parent`, `description`, `pool_multiplier`, `specialty_usd`, `need_total` (optional override), `market_bonus_usd` per market, `award_mode` (`manual` or `schedule`), schedule parameters when in `schedule` mode (section 6A), and per-cell `admit_rate` and `award_usd` overrides relative to the parent (the generator materializes full columns). Baseline is scenario 0: admit rate and award from the latest cohort, tuition at `tuition_2027`, yield from the response base.

## 3. Reference ledger (Python is the definition; Excel mirrors it)

Units are (cell c, market m); with `markets` empty there is one unit per cell. For scenario s and case k in {low, middle, high}:

1. `apps_sc = apps_c,2026 x (pool_multiplier_s if lsat_lo_c >= pool_threshold_lsat else 1)`
2. `admits_sc = apps_sc x rate_sc`, rounded to an integer when `integer_admits`; `admits_scm = admits_sc x share_{m | r(c), g(c)}`
3. `award_scm = min(award_sc + bonus_sm, tuition_2027)`; `yield_scmk = response(c, award_scm, k)` (section 4)
4. `enrolled_scmk = admits_scm x yield_scmk`; `enrolled_sck = sum_m enrolled_scmk`, rounded when `integer_enrolled`; `class_sk = sum_c enrolled_sck`
5. `merit_sk = sum_c,m enrolled_scmk x award_sc`; `market_cost_sk = sum_c,m enrolled_scmk x (award_scm - award_sc)`; `need_sk = need_total_s / need_denominator x class_sk`
6. `gross_sk = class_sk x tuition_2027`; `aid_sk = merit + market_cost + need + specialty_s`; `NTR_sk = gross - aid`; `discount_sk = aid / gross`; `avg_aid = aid / class`

With every `bonus_sm` equal to zero, the market ledger must equal the cell ledger exactly (shares sum to 1); this is a test. Reproduce mode has no market layer and `specialty_s` is the YA lump sum. Yield is constant when admit rates change (D1).

**KPIs per scenario and case:** class; applications and admits (total, by residency); enrolled at or above each LSAT threshold, below `floor_lsat`; enrolled with GPA class `hi`; **margin** (YA definition) = count at or above the threshold minus count below; full-tuition enrolled (award at or above tuition) and full-pay enrolled (award of zero); barbell index = (full-tuition + full-pay) / class; Baseline NTR minus scenario NTR ("price of the target"); enrolled by market, change from 2026 and against `market_targets`.

## 4. Response (placeholder in the prototype; the pipeline replaces it later)

Per cell, base award `a0_c` = latest cohort award and base yield `y0_c` = admits-weighted yield over the last 3 cohorts (fallback: the cell's LSAT-group pooled yield when admits are under 5). For a candidate award `a` and slope `b_k` (points per $1,000):

`yield = clip(y0_c + (b_k / 100) x (a - a0_c) / 1000, yield_floor_g, yield_cap_g)`

The Response sheet tabulates yield at award rungs (0, 5,000, ... up to tuition; plus a "full tuition" rung that follows tuition) for each cell and case; the Ledger interpolates linearly between rungs with `MATCH`/`INDEX` and clamps outside the rung range. Each cell carries an **evidence label**: `observed` if `a` lies within the cell's historical award range plus `evidence_tolerance_usd`, otherwise `extrapolated`; the prototype labels every response source `placeholder (client-assumed)`. The label describes how well the yield is known, never the award: it carries no warning color, threshold or message. The Ledger records it per scenario cell, and the Summary reports the share of enrolled in `extrapolated` cells as a plain figure. Awards may differ from any prior value by any amount; the prototype applies no cap on award moves. Linear extrapolation is bounded only by `yield_floor` and `yield_cap` per LSAT group (placeholders 0.03 and 0.60).

Marginal-admit yield (yield changing with admit rate) is not modeled: yield is constant when admit rates change, in live and reproduce mode (the YA file does the same in 24 of 24 cases; Jason, Nov 4). Expose `marginal_admit_yield_slope` (default 0) that the ledger reads and ignores with a note when non-zero; implementing it waits for a marginal-admit yield estimate.

## 5. Risk functions (closed form, validated against simulation)

Independent binomial enrollment by unit (a cell, or a cell x market pair when the market layer is on; the formulas are written with c indexing units) given `admits_sc` and `yield_sc`. With `mu_c = A_c y_c` and `v_c = A_c y_c (1 - y_c)`, `Phi` the standard normal CDF, `s` = `common_shock_sd`:

- **Class:** `M = sum mu_c`; `V = sum v_c + s^2 M^2`. `P(class > cap) = 1 - Phi((cap + 0.5 - M)/sqrt(V))`. `P(|class - target| <= band) = Phi((target + band + 0.5 - M)/sqrt(V)) - Phi((target - band - 0.5 - M)/sqrt(V))`. 90% interval: `M +/- 1.645 sqrt(V)`.
- **Median holds at threshold t:** sign `g_c = +1` if `lsat_lo_c >= t` else `-1` (unscored rows count as -1). `m = sum g_c mu_c`; `V_m = sum v_c`. `P(median >= t) = 1 - Phi((-0.5 - m)/sqrt(V_m))`. The common shock is **not** added here: it scales `m` and leaves its sign unchanged. Same form for GPA with `g_c = +1` for class `hi`. Tie rule: the median holds when at least half the class is at or above t.
- **NTR:** `w_c = tuition - award_c - need_total/need_denominator`; `mean = sum w_c mu_c - specialty`; `V_n = sum w_c^2 v_c + s^2 (sum w_c mu_c)^2`. `P(NTR >= target) = 1 - Phi((target - mean)/sqrt(V_n))`.
- **Market m (market layer on):** `M_m = sum_c mu_cm`; `V'_m = sum_c v_cm + s^2 M_m^2`; `P(enrolled_m >= target_m) = 1 - Phi((target_m - 0.5 - M_m)/sqrt(V'_m))`. Markets share the common shock, so market outcomes are correlated; the prototype reports each market's probability separately and does not claim a joint probability.

**Validation already run on the YA fixture (Scenarios 1, 2, 4, from `ya_workbook_support/analysis.py`):** normal vs simulation within 0.01 for P(median at 166) 0.66, 0.61, 0.68; P(class above 140) 0.42, 0.22, 0.41 vs 0.42, 0.22, 0.40; P(NTR at least $4.5M) 0.32, 0.23, 0.43 vs 0.31, 0.23, 0.43; with s = 0.10: class SD 17.07 (formula) vs 17.0 and NTR SD $0.558M vs $0.56M (Scenario 1). Test 11.4 repeats this on synthetic worlds with tolerance 0.02.

## 6. Workbook sheets (XlsxWriter)

General: no hidden rows or columns; no conditional format or message that characterizes an award as unusual (a neutral highlight of cells changed from the parent is allowed); inputs unlocked and blue; formula cells locked; sheet protection with no password (D8); named ranges for every Inputs cell; freeze panes; print setup; consistent number formats. Formulas use `ROUND`, `SUMPRODUCT`, `INDEX`, `MATCH`, `MIN`, `MAX`, `IF`, `SQRT`, `NORMSDIST`, `TEXT` and `&`; no dynamic arrays, no `LET`/`LAMBDA`, no macros, no volatile functions. Write each formula with its cached value (from the Python ledger) so previews show numbers.

| Sheet | Content |
|---|---|
| `README` | Purpose, how to use, color key, the labels (observed, extrapolated, placeholder), what is static and what is live, build id |
| `Inputs` | Section 2 config values as named inputs; sensitivity case selector (Low, Middle, High) for display; mode switch (Live, Reproduce) |
| `History` | Cell x cohort panels: applications, admits, admit rate, award $, award % of tuition, yield, enrolled; totals by residency and overall; tuition row |
| `Response` | Per cell: `a0`, `y0`, observed award range, rung grid, yield at each rung for Low, Middle, High, evidence label |
| `Markets` | Market x cohort history (apps, admits, enrolled), shares `share_{m|r,g}`, 2026 base, optional targets. Omitted when `markets` is empty |
| `Schedule` | Optional authoring layer per scenario: award by LSAT tier x residency, a GPA step, tier edges (lower bounds), all inputs; expands by formula into a fine award per cell (section 6A). Used when the scenario's `award_mode` is `schedule` |
| `Levers` | Header rows per scenario: name, parent, description, pool multiplier, specialty, need override, `award_mode`, market bonus per market. Body: per cell `admit_rate` (input, with lower and upper bounds that `GoalSeek` reads) and `award_usd` (input in `manual` mode, the `Schedule` result in `schedule` mode). A neutral highlight marks cells that differ from the parent (parent fixed at build time). A "cells changed from parent" count per scenario |
| `Ledger_Low`, `Ledger_Middle`, `Ledger_High` | Per cell, per scenario block of columns: apps, admit rate, admits, award; then per market the yield, enrolled and evidence label; then enrolled total and spend. Totals row. Formulas per section 3 and 4; the mode switch selects live yield or the `Reproduce` override |
| `Summary` | Section 3 KPIs and section 5 probabilities for Baseline and each scenario, Middle case in the main block and Low and High for class, NTR, P(median). Price-of-target row. Evidence row (share of enrolled in `extrapolated` cells, plain figure). Market block: enrolled by market, change from 2026, P(target met). Narrative rows (section 8) |
| `Distribution` | Full-tuition and full-pay counts, barbell index, share of merit dollars going to the top quartile of enrolled by academic position (cells ordered by `lsat_lo`, then GPA class; weighted by expected enrolled). **Step sizes:** award difference between adjacent LSAT bands within each residency x GPA class, per scenario, as a plain table with no threshold, color or message |
| `GoalSeek` | Static output of `goalseek.py` for named scenarios (proposed admit rates per cell, change from the parent, status, binding constraints) with the lever checksum guard, plus live cells showing the Ledger's gap to each target. Staff copy proposed rates into `Levers` by hand |
| `Static_MC` | Monte Carlo results for named scenarios (class, NTR, P(median) at 20,000 draws, seed fixed), the build date, and a checksum over the lever cells with a live flag: `RE-RUN NEEDED` when the lever checksum differs. Checksum: `ROUND(SUM(lever range) + SUMPRODUCT(lever range, ROW(lever range)), 6)` |
| `Checks` | Section 7 |
| `Reproduce` | Present only in reproduce mode: YA yields, admit rates, awards and pool settings as loaded values |
| `RunLog` | Build id, git commit, config hash, data hash, timestamp, dependencies, response source label |

Later sheets (stubs allowed): `MultiYear` (award rule toggle fixed dollars or percent of tuition, tuition migration, retention by year, three-year spend and NTR). Not in this prototype: `Market`, `Frontier`.

## 6A. Schedule and goal-seek helpers

**Schedule (`schedule.py`, mirrored by the `Schedule` sheet).** Parameters per scenario: tier edges (LSAT lower bounds, descending), a base award for each (tier, residency), and a GPA step in dollars applied to class `hi`. Expansion: `award_c = clip(round_to(base[tier(lsat_lo_c), r_c] + gpa_step x [gpa_c = hi], award_rounding), 0, tuition)`. The default tiering comes from the sizing in section 15 (about 13 award-tier parameters). The same function renders the policy document's fine matrix. Schedule is an authoring convenience: the policy of record is the fine matrix it produces, and a client may overwrite any cell in `manual` mode.

**Goal-seek (`goalseek.py`).** Given a scenario with awards and yields fixed, find admit rates `r_c` in `[lo_c, hi_c]` that meet class and median targets with minimal change. With `A_c` applications, `y_c` yield, `mu_c = A_c y_c r_c`:
- Class: `M = sum A_c y_c r_c`, linear in `r`. Constraint `M <= cap + 0.5 - z sqrt(V)` with `z = Phi^-1(p*)`, and optionally `M >= target - band`.
- Median at t: `m = sum g_c A_c y_c r_c`. Constraint `m >= -0.5 + z sqrt(V_m)`.
- `V` and `V_m` depend on `r`; fix them at the current rates, solve, recompute at the solution, repeat up to `max_iterations`.
- Objective `min_disruption`: minimize `sum A_c |r_c - r0_c|` (split into positive and negative parts); alternative `max_ntr`: maximize `sum w_c A_c y_c r_c`.
- Solve with `scipy.optimize.linprog` (HiGHS). Round admits to integers, re-evaluate in the ledger, and report the ledger's probabilities, never the LP's. If infeasible, report which constraint binds.
This is a planning helper, not the S5 optimizer. It is deliberately linear so staff can reproduce its reasoning.

## 7. Checks sheet (each returns OK or a message)

Integrity only; nothing here comments on an award. Totals of cell rows equal totals rows; admits at most applications; enrolled at most admits; award at least zero and at most tuition after the bonus clamp; yield between 0 and 1; shares sum to 1 within each (residency, LSAT group); market enrolled sums to class; `Schedule` expansion equals the `Levers` awards when `award_mode` is `schedule`; class against cap and band (reported as a result, not a warning); spend against `budget_total` when set (D7); history reconciliation (grid-implied merit against reported actual merit, when provided; show the percent gap); Summary class equals Ledger total; lever checksum guard.

## 8. Narratives

Python and Excel versions of two templates per scenario, populated from live cells:
- **Changes from parent:** "Pool multiplier {x}. Awards changed in {n} cells; admit rates changed in {m} cells." (Counts by formula; named bands listed only in the Python version written to `Static_MC`.)
- **Projected outcome:** "Class {N} (90% range {lo} to {hi}). LSAT median {t}: {count at or above} of {N}, margin {margin}, probability {p}. GPA median {3.83}: margin {g}, probability {pg}. {k} enrolled below {floor}. Full-tuition {ft}, full-pay {fp}. NTR {x}M (90% range), discount {d}%. Markets: {market sentence}. Evidence: {share}% of enrolled in cells where the yield is extrapolated." The market sentence lists each market's expected enrolled, change from 2026 and probability of meeting its target.

## 9. Reproduce mode (acceptance test against the YA fixture)

`reproduce.py` reads the YA workbook (read only) and builds a workbook in which the Ledger runs with YA's admit rates, awards, yields and pool settings as client-assumed values.

**Fixture layout (verified October 30 file).** Sheet `Client Strategy Comparison`: six panels, each 12 columns wide starting at columns B (admit rate), O (admits), AB (award %), AO (award $), BB (yield), BO (enrolled); within a panel the columns are 2024, 2025, 2026, Baseline, Scenarios 1 to 8. Rows 7 to 40 are in-state cells and rows 59 to 92 are out-of-state; column A holds the cell label. Ignore rows 41 to 56, 93 onward (`#N/A` filler). Applications are not in the file: use `admits / admit rate` for 2026 where the rate is above zero. Tuition by cohort: award $ / award % (55,550; 57,600; 59,900; 63,500). Sheet `Client Scenarios`: scenario columns AH (S1), AP (S2), AX (S3), BF (S4); rows 179 to 183 hold gross, merit, need, specialty and total aid; row 186 holds NTR; row 189 holds the narrative text. Pool multipliers: 1.30 for Scenarios 1 to 3, 1.50 for Scenario 4, applied at LSAT 165 and above; need $200,000 over 140 enrolled (Scenario 4: need $190,000 and specialty $10,000). Scenarios 5 to 8 are empty; skip them.

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
| Geography | **No source in the fixture** (residency only). Placeholder generator parameters: three in-state metro markets and six out-of-state states with a declining share profile; a market with under 30 admits across history is pooled into its residency's other tier. Replace from Richmond's state and ZIP3 extract when available | The overlay and market targets need a market structure to test |
| **Confounding** | Cross-sectional, admit-weighted slope of cell yield on award share: raw about -0.04 to -0.17 points per $1,000; adjusted for LSAT group, GPA class and residency from -0.9 to +0.1 | Aid is targeted at high-credential, lower-yield admits, so the observed slope is near zero or negative while the true slope is positive. The synthetic world must reproduce this so that the pipeline is tested on the same trap |

Source for each row: fixture sheets 1 and 2 and the computation in this session (October to November 2026 analysis; rerun `ya_workbook_support/analysis.py` for the base figures). Adopting these in the main S2 world definitions (W0L) is a separate change for Jason's review.

## 11. Tests (`pytest`)

1. **Ledger unit tests:** each identity in section 3 on a 6-cell toy grid with hand-computed answers.
2. **Risk unit tests:** closed forms against a 200,000-draw simulation on the toy grid; tolerance 0.01.
3. **Excel equals Python:** build the workbook from the synthetic world, recalculate with LibreOffice headless (`soffice --headless --convert-to xlsx --outdir <tmp>`), read recalculated values with `openpyxl(data_only=True)` and compare every Ledger and Summary numeric cell to the Python result: exact for integers, 1e-6 relative for floats. If `soffice` is missing, report it, skip, and list the cells that need a manual Excel open.
4. **Closed form vs simulation on synthetic worlds:** class, median and NTR probabilities within 0.02 for 20 random scenarios.
5. **Shape targets:** the synthetic generator meets every range in section 10 across 20 seeds (report the share of seeds passing; require at least 90%).
6. **Reproduce:** section 9 pass criteria (skipped without `YA_FIXTURE_PATH`).
7. **Stale guard:** editing one lever value in a copy of the workbook flips the `RE-RUN NEEDED` flag (checked after LibreOffice recalculation).
8. **Guardrails:** no column named race, ethnicity or gender in any input or output; no student-level fields; workbook contains no formulas referencing external files; no hidden sheets, rows or columns; no conditional format or cell text that labels an award exceptional, anomalous, out of bounds or beyond a limit.
9. **Market and schedule:** with all bonuses zero the market ledger equals the cell ledger; schedule expansion is constant within tiers and equals the manual matrix when copied; market probabilities within 0.02 of simulation.
10. **Goal-seek:** on 20 synthetic scenarios the LP either meets class and median targets in the ledger (within rounding) or reports infeasibility with the binding constraint; total admit change is no larger than a greedy baseline.
11. **Reconciliation:** Summary and Ledger agree with a Python dump of the same run for every figure that the dashboard and policy document will read (the interface contract in section 15).
12. **Rendering:** convert `Summary` to PDF with LibreOffice and save to `output/` for visual review (not asserted).

## 12. Phases, acceptance and hooks

| Phase | Deliverable | Accept when |
|---|---|---|
| 1 | `ledger.py`, `risk.py`, `response.py`, `mc.py`, `synth_cells.py`, tests 1, 2, 4, 5 | Tests pass; shape targets met |
| 2 | `workbook.py` with README, Inputs, History, Markets, Response, Levers, Ledger x3, Summary, Checks, RunLog; tests 3 and 9 | Excel equals Python on synthetic worlds |
| 3 | `reproduce.py`, Reproduce sheet, test 6 | Section 9 criteria met, or mismatches reported with causes |
| 3b | `schedule.py` and `Schedule` sheet; `goalseek.py` and `GoalSeek` sheet; tests 10 and 11 | Schedule expands as specified; goal-seek meets targets in the ledger |
| 4 | Distribution, Static_MC with guard, narratives, MultiYear stub; tests 7, 8 and 12 | Tests pass; Jason reviews the PDF render and opens the file in desktop Excel |

Hooks for later work (leave stubs and TODO notes, no logic): pipeline-supplied Response table (same sheet layout, evidence labels `estimated` or `extrapolated`); marginal-admit yield; pacing-based pool path with interval (Slate, later addition); `Market` (509 rank-matched award gap); `Frontier`; an admit-rate dimension in the optimizer; the proxy screen on market targets (pipeline); a client-declared policy envelope; USNWR planner link (possible future law-product feature).

## 13. Decisions

| ID | Question | Status |
|---|---|---|
| D1 | Admissions levers | Decided (Nov 4): evaluator inputs plus goal-seek helper; constant yield when admit rates move; an admit-rate dimension for the optimizer may come later |
| D2 | Guardrail | Decided (Nov 4): fixed 5% rule removed as constraint and flag; evidence label kept as information; band-edge step sizes shown as a plain table |
| D3 | Small cells | Decided (Nov 4): shown to authenticated client staff, enrollment team and leadership; cleared with Cat. Confirm the aid office has the same access |
| D4 | Tuition migration | Open: fixture implies +6.0%; the capture sheet says "just above 5%". Default: fixture |
| D5 | Class cap 140 and band +/-4 | Open: inferred from the YA need denominator; confirm with Richmond |
| D6 | Sensitivity slopes 0.5, 1.0, 1.5; shock SD 0.10; yield floor and cap | Placeholders, not evidence |
| D7 | Budget figure | Unknown; `budget_total` optional |
| D8 | Sheet protection | On, no password |
| D9 | Geography | Interpreted as an additive bonus by market (state or MSA) on top of the matrix award, with shares by residency and LSAT group; nothing finer than a state or MSA. Pending Jason's confirmation |

## 14. Handling and report-back

The YA file is Richmond-provided with permission, but it is YA's work product: use our own layout and wording; do not reproduce their text or branding. Anything that reproduces its cell values stays out of git (Jason confirmed Nov 4); the file may calibrate synthetic data through ranges and parameters (section 10). When done, report: what was built per phase, test results (including skips and why), dependencies added, mismatches in reproduce mode with the likeliest cause, and anything in this spec that proved ambiguous or wrong. Workbooks that go to a client need Jason's review first.

## 15. Integration with the pipeline and the other deliverables

1. **One evaluator.** The ledger is the single reference evaluator of any award grid. The optimizer's projected class, spend and NTR for a solved grid must equal the ledger's for the same grid (a later test). The Excel workbook, the dashboard scenario view and the policy document read ledger outputs; none recomputes them. Test 11 is the reconciliation.
2. **Cell data.** The pipeline's cell aggregate (today `funnel_cells.csv`) needs `award_usd` by cell and cohort, and an unsuppressed variant for authenticated client staff. Suppression is removed for this client (D3); the CLAUDE.md rule and schema enforcement change in v2.7, not in this prototype.
3. **Response.** The pipeline supplies a table per cell x award rung x case with an evidence label, plus the anchored slope and its uncertainty from `model_run.json` (`b_L`, `b_M`, `b_H` replace the placeholder slopes).
4. **Policy of record at the fine matrix.** The optimizer works on a low-dimensional decision layer and the fine matrix is rendered by `schedule.py`, the function the `Schedule` sheet mirrors. Sizing on the YA fixture (7 of 68 fine cells have 30 or more admits): merging adjacent LSAT bands within residency x GPA (3.83 and above, other) until each group has 30 admits gives about 13 groups (16 to 17 at 20 admits), on both 2026 admits and the three-cohort mean. The decision layer is therefore about 13 award-tier parameters plus one bonus per target market (up to about six), roughly 19 in total, which fits the methodology's count rule (cells at most admits / 30 = 21) if that rule is kept. Markets with under 30 admits across history are pooled.
5. **Policy document and admissions.** The aid policy carries the award matrix and market bonuses. Admit rates and pool multipliers appear in a separate planning-assumptions block, not as aid policy.
6. **Band-edge step sizes** appear as a plain table (Distribution sheet and policy document); no flag, no threshold.
7. **Synthetic data.** `synth_cells.py` is a stopgap. When the law world (W0L) generates student-level data, aggregate it with the pipeline's aggregator and retire `synth_cells.py`; the shape targets move into W0L.
8. **Sequencing.** Scenario outputs may reach Richmond before a price anchor exists (S1 OD-07), so every figure is labeled client-assumed until the pipeline's response table replaces the placeholder. The workbook evaluates scenarios and does not recommend prices.
