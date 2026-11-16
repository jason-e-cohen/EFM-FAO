# Prototype spec v0.1: formula-driven scenario workbook (for Claude Code)

**Date:** November 4, 2026 | **Owner:** Jason Cohen | **Status:** draft for Jason's review | **Reads with:** `CLAUDE.md`, `Richmond_YA_Scenario_Workbook_Assessment.md` (sections 3, 4, 11), `02_methodology_v2.6.md` section 5

## 0. Purpose, scope, rules

**Purpose.** Build a Python program that generates an Excel scenario workbook with live formulas: it reproduces the panels of the Yellow Arrows (YA) Richmond workbook, then adds risk probabilities, evidence labels, distribution metrics and checks. The prototype proves the ledger and the risk formulas on synthetic data and on the YA file as a validation fixture. It does not estimate price response; a placeholder response table stands in for the pipeline.

**In scope (this spec):** reference ledger and risk functions in Python; workbook generator; reproduce mode; synthetic cell-level data generator; tests. **Out of scope:** the estimation pipeline, optimizer, Supabase, dashboard, pacing import, the Market sheet (509 gap), the Frontier sheet, admit-rate optimization, any USNWR link. Hooks for these are listed in section 12.

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
  sw/synth_cells.py              cell-level synthetic generator
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
- `evidence_tolerance_usd` (2500).

**Cell data (`cells.csv`, long format).** One row per cell x cohort: `cell_id, residency, lsat_lo, gpa_class, cohort, apps, admits, award_usd, enrolled`. Cohorts: three actuals (2024 to 2026). Cell order is fixed by (residency, lsat_lo descending, gpa_class); the workbook uses the same order.

**Scenario file (`scenarios.yaml`).** Per scenario: `name`, `parent`, `description`, `pool_multiplier`, `specialty_usd`, `need_total` (optional override), and per-cell `admit_rate` and `award_usd` overrides relative to the parent (the generator materializes full columns). Baseline is scenario 0: admit rate and award from the latest cohort, tuition at `tuition_2027`, yield from the response base.

## 3. Reference ledger (Python is the definition; Excel mirrors it)

For scenario s, cell c, case k in {low, middle, high}:

1. `apps_sc = apps_c,2026 x (pool_multiplier_s if lsat_lo_c >= pool_threshold_lsat else 1)`
2. `admits_sc = apps_sc x rate_sc`, rounded to an integer when `integer_admits`
3. `yield_sck = response(c, award_sc, k)` (section 4)
4. `enrolled_sck = admits_sc x yield_sck`, rounded when `integer_enrolled`
5. `merit_sk = sum_c enrolled_sck x award_sc`; `need_sk = need_total_s / need_denominator x class_sk`; `class_sk = sum_c enrolled_sck`
6. `gross_sk = class_sk x tuition_2027`; `aid_sk = merit + need + specialty_s`; `NTR_sk = gross - aid`; `discount_sk = aid / gross`; `avg_aid = aid / class`

**KPIs per scenario and case:** class; applications and admits (total, by residency); enrolled at or above each LSAT threshold, below `floor_lsat`; enrolled with GPA class `hi`; **margin** (YA definition) = count at or above the threshold minus count below; full-tuition enrolled (award at or above tuition) and full-pay enrolled (award of zero); barbell index = (full-tuition + full-pay) / class; Baseline NTR minus scenario NTR ("price of the target").

## 4. Response (placeholder in the prototype; the pipeline replaces it later)

Per cell, base award `a0_c` = latest cohort award and base yield `y0_c` = admits-weighted yield over the last 3 cohorts (fallback: the cell's LSAT-group pooled yield when admits are under 5). For a candidate award `a` and slope `b_k` (points per $1,000):

`yield = clip(y0_c + (b_k / 100) x (a - a0_c) / 1000, yield_floor_g, yield_cap_g)`

The Response sheet tabulates yield at award rungs (0, 5,000, ... up to tuition; plus a "full tuition" rung that follows tuition) for each cell and case; the Ledger interpolates linearly between rungs with `MATCH`/`INDEX` and clamps outside the rung range. Each cell carries an **evidence label**: `observed` if `a` lies within the cell's historical award range plus `evidence_tolerance_usd`, otherwise `extrapolated`; the prototype labels every response source `placeholder (client-assumed)`. In the Ledger, an `extrapolated` flag per scenario cell, and the share of enrolled in flagged cells, feed the Summary.

Marginal-admit yield (yield changing with admit rate) is not modeled; the YA file holds it constant (24 of 24 cases) and reproduce mode needs that. Expose a config key `marginal_admit_yield_slope` (default 0) that the ledger reads and ignores with a warning when non-zero; Phase C implements it.

## 5. Risk functions (closed form, validated against simulation)

Independent binomial enrollment by cell given `admits_sc` and `yield_sc`. With `mu_c = A_c y_c` and `v_c = A_c y_c (1 - y_c)`, `Phi` the standard normal CDF, `s` = `common_shock_sd`:

- **Class:** `M = sum mu_c`; `V = sum v_c + s^2 M^2`. `P(class > cap) = 1 - Phi((cap + 0.5 - M)/sqrt(V))`. `P(|class - target| <= band) = Phi((target + band + 0.5 - M)/sqrt(V)) - Phi((target - band - 0.5 - M)/sqrt(V))`. 90% interval: `M +/- 1.645 sqrt(V)`.
- **Median holds at threshold t:** sign `g_c = +1` if `lsat_lo_c >= t` else `-1` (unscored rows count as -1). `m = sum g_c mu_c`; `V_m = sum v_c`. `P(median >= t) = 1 - Phi((-0.5 - m)/sqrt(V_m))`. The common shock is **not** added here: it scales `m` and leaves its sign unchanged. Same form for GPA with `g_c = +1` for class `hi`. Tie rule: the median holds when at least half the class is at or above t.
- **NTR:** `w_c = tuition - award_c - need_total/need_denominator`; `mean = sum w_c mu_c - specialty`; `V_n = sum w_c^2 v_c + s^2 (sum w_c mu_c)^2`. `P(NTR >= target) = 1 - Phi((target - mean)/sqrt(V_n))`.

**Validation already run on the YA fixture (Scenarios 1, 2, 4, from `ya_workbook_support/analysis.py`):** normal vs simulation within 0.01 for P(median at 166) 0.66, 0.61, 0.68; P(class above 140) 0.42, 0.22, 0.41 vs 0.42, 0.22, 0.40; P(NTR at least $4.5M) 0.32, 0.23, 0.43 vs 0.31, 0.23, 0.43; with s = 0.10: class SD 17.07 (formula) vs 17.0 and NTR SD $0.558M vs $0.56M (Scenario 1). Test 11.4 repeats this on synthetic worlds with tolerance 0.02.

## 6. Workbook sheets (XlsxWriter)

General: no hidden rows or columns; inputs unlocked and blue; formula cells locked; sheet protection with no password (D8); named ranges for every Inputs cell; freeze panes; print setup; consistent number formats. Formulas use `ROUND`, `SUMPRODUCT`, `INDEX`, `MATCH`, `MIN`, `MAX`, `IF`, `SQRT`, `NORMSDIST`, `TEXT` and `&`; no dynamic arrays, no `LET`/`LAMBDA`, no macros, no volatile functions. Write each formula with its cached value (from the Python ledger) so previews show numbers.

| Sheet | Content |
|---|---|
| `README` | Purpose, how to use, color key, the labels (observed, extrapolated, placeholder), what is static and what is live, build id |
| `Inputs` | Section 2 config values as named inputs; sensitivity case selector (Low, Middle, High) for display; mode switch (Live, Reproduce) |
| `History` | Cell x cohort panels: applications, admits, admit rate, award $, award % of tuition, yield, enrolled; totals by residency and overall; tuition row |
| `Response` | Per cell: `a0`, `y0`, observed award range, rung grid, yield at each rung for Low, Middle, High, evidence label |
| `Levers` | Header rows per scenario: name, parent, description, pool multiplier, specialty, need override. Body: per cell `admit_rate` and `award_usd` inputs. Conditional format highlights cells that differ from the parent (parent is fixed at build time). A "cells changed from parent" count per scenario |
| `Ledger_Low`, `Ledger_Middle`, `Ledger_High` | Per cell, per scenario block of columns: apps, admit rate, admits, award, yield, extrapolated flag, enrolled, spend. Totals row. Formulas per section 3 and 4; the mode switch selects live yield or the `Reproduce` override |
| `Summary` | Section 3 KPIs and section 5 probabilities for Baseline and each scenario, Middle case in the main block and Low and High for class, NTR, P(median). Price-of-target row. Evidence row (cells flagged, share of enrolled flagged). Narrative rows (section 8) |
| `Distribution` | Full-tuition and full-pay counts, barbell index, share of merit dollars going to the top quartile of enrolled by academic position (cells ordered by `lsat_lo`, then GPA class; weighted by expected enrolled) |
| `Static_MC` | Monte Carlo results for named scenarios (class, NTR, P(median) at 20,000 draws, seed fixed), the build date, and a checksum over the lever cells with a live flag: `RE-RUN NEEDED` when the lever checksum differs. Checksum: `ROUND(SUM(lever range) + SUMPRODUCT(lever range, ROW(lever range)), 6)` |
| `Checks` | Section 7 |
| `Reproduce` | Present only in reproduce mode: YA yields, admit rates, awards and pool settings as loaded values |
| `RunLog` | Build id, git commit, config hash, data hash, timestamp, dependencies, response source label |

Phase 4 sheets (stubs allowed): `MultiYear` (award rule toggle fixed dollars or percent of tuition, tuition migration, retention by year, three-year spend and NTR). Not in this prototype: `Market`, `Frontier`.

## 7. Checks sheet (each returns OK or a message)

Totals of cell rows equal totals rows; admits at most applications; enrolled at most admits; award at most tuition and at least zero; yield between 0 and 1; award ladder monotone within a residency by `lsat_lo` and GPA class (warn, not fail); class against cap and band; spend against `budget_total` when set (D7: Richmond's budget is fixed but the figure is unknown); history reconciliation (grid-implied merit against reported actual merit, when provided; show the percent gap); sum of Summary class across residency equals Ledger total; extrapolated share above 25% of enrolled raises a warning; checksum guard.

## 8. Narratives

Python and Excel versions of two templates per scenario, populated from live cells:
- **Changes from parent:** "Pool multiplier {x}. Awards changed in {n} cells; admit rates changed in {m} cells." (Counts by formula; named bands listed only in the Python version written to `Static_MC`.)
- **Projected outcome:** "Class {N} (90% range {lo} to {hi}). LSAT median {t}: {count at or above} of {N}, margin {margin}, probability {p}. GPA median {3.83}: margin {g}, probability {pg}. {k} enrolled below {floor}. Full-tuition {ft}, full-pay {fp}. NTR {x}M (90% range), discount {d}%. Evidence: {share}% of enrolled in extrapolated cells."

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
8. **Guardrails:** no column named race, ethnicity or gender in any input or output; no student-level fields; workbook contains no formulas referencing external files; no hidden sheets, rows or columns.
9. **Rendering:** convert `Summary` to PDF with LibreOffice and save to `output/` for visual review (not asserted).

## 12. Phases, acceptance and hooks

| Phase | Deliverable | Accept when |
|---|---|---|
| 1 | `ledger.py`, `risk.py`, `response.py`, `mc.py`, `synth_cells.py`, tests 1, 2, 4, 5 | Tests pass; shape targets met |
| 2 | `workbook.py` with README, Inputs, History, Response, Levers, Ledger x3, Summary, Checks, RunLog; test 3 | Excel equals Python on synthetic worlds |
| 3 | `reproduce.py`, Reproduce sheet, test 6 | Section 9 criteria met, or mismatches reported with causes |
| 4 | Distribution, Static_MC with guard, narratives, MultiYear stub; tests 7 to 9 | Tests pass; Jason reviews the PDF render and opens the file in desktop Excel |

Hooks for later work (leave stubs and TODO notes, no logic): pipeline-supplied Response table (same sheet layout, evidence labels `estimated` or `extrapolated`); marginal-admit yield; pacing-based pool path with interval; `Market` (509 rank-matched award gap); `Frontier`; admit-rate optimization; USNWR planner link.

## 13. Decisions assumed as defaults (change by editing config; none blocks the build)

| ID | Question | Default assumed |
|---|---|---|
| D1 | Admissions levers | Inputs only; no optimization |
| D2 | Evaluating client-authored grids outside the guardrail | Allowed, labeled `extrapolated`. Class cap 140 and band +/-4 are inferred from the YA need denominator; confirm with Richmond |
| D3 | Fine matrix disclosure | Workbook goes to the client through the secure channel; no cell suppression in the workbook; never to Supabase |
| D4 | Tuition migration | Taken from the fixture (+6.0%); the capture sheet says "just above 5%": confirm |
| D5 | Sensitivity slopes 0.5, 1.0, 1.5 | Placeholders, not evidence |
| D6 | Common shock SD 0.10 | Illustrative |
| D7 | Budget figure | Unknown; `budget_total` optional |
| D8 | Sheet protection | On, no password |

## 14. Handling and report-back

The YA file is Richmond-provided with permission, but it is YA's work product: use our own layout and wording; do not reproduce their text or branding. Anything that reproduces its cell values stays out of git. When done, report: what was built per phase, test results (including skips and why), dependencies added, mismatches in reproduce mode with the likeliest cause, and anything in this spec that proved ambiguous or wrong. Workbooks that go to a client need Jason's review first.
