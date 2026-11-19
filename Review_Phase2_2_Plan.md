# Review and plan: Brandon's points (BM-1 to BM-10), spec v0.6.3 amendment and Phase 2.2

**Date:** November 17, 2026 | **Reviewer:** independent review | **Owner:** Jason Cohen | **Inputs:** `Review_Points_Brandon_Nov17.md`, `CLAUDE.md`, `DECISIONS.md` (working copy, with the Nov 17 BM entry), `Prototype_Spec_Scenario_Workbook_v0.6.md` (v0.6.2), and the build in the working tree (Phase 2 accepted at `52b4554`; uncommitted Phase 3 work present) | **Client-confidential:** contains Brandon's figures; Richmond files only.

Nothing was edited except this file. The checks ran in scratch copies. No fixture value is reproduced here: the BM-2 tuition check ran on your computer and printed only ratios and true/false results.

## 1. Verdicts

| Item | Verdict | Main correction or addition |
|---|---|---|
| BM-1 percentile targets | **Confirm, with four corrections** | (a) The continuity correction is half the margin's lattice step, `1/(2n)` for `q = m/n` in lowest terms, not 0.5 (derived and tested, section 2). (b) The margin is a count of **swaps at fixed class size**, not "students the class can still absorb"; adding below-t students consumes it at `1 - q` each. (c) At `q = 0.5` the probability equals v0.6 exactly, but the margin is **half** the v0.6 margin. Keep `margin_t` and `p_median_t` as they are for continuity and reproduce mode, and add new names. (d) Label a target "approximate" when fewer than 20 are expected below t |
| BM-2 tuition in dollars | **Confirm** | Checked: $63,500 is exactly `round_to(base x 1.060, 50)` on the base the fixture implies (+6.01%) and equals the fixture's 2027 scenario tuition. 5.5% does not reproduce it. Store the implied increase unrounded, so the dollar figure round-trips exactly |
| BM-3 class target = cap | **Confirm; the readout is new** | The class-size table has no P(class > cap) column today (`sw/trim.py` `class_table`; Summary columns in `sw_class_table`). Add one, computed at each N's trimmed admits |
| BM-4 revenue goal | **Confirm, with one rule** | One effective entering target, `ntr_target - continuing_ntr_usd` under `all_jd`, read by all three places that use `ntr_target` (the Summary probability, the yield-strip probability and the yield-strip NTR break-even). The tuition what-if holds continuing revenue fixed and says so |
| BM-5 `above_floor` (decided) | **Confirm, with two specifications** | Unscored segment cells are not protected under `above_floor` (no score, so not "at or above the floor"). The Trim order now depends on `score.floor`, which Inputs marks "live", so `score.floor` must join the "rebuild needed" check. Also flag: if Brandon's 10th-percentile t ends up above 154, `above_floor` still cuts non-segment cells at or above that t before segment cells between 154 and t |
| BM-6 growth to date | **Correct: half built** | `pool_ytd_growth` is already an editable Inputs cell shown on the pool strip (`sw/workbook.py` lines 524 and 1915). What is missing is the as-of date, the row marker, and a definition: growth must be in **applications at or above `score.pool_threshold`**, because that is what the pool multiplier scales. **Add a break-even pool multiplier** (closed form) as the "bottom drops out" trigger Brandon asked for |
| BM-7 Scenario 4 first | **Confirm; sequence with the Phase 3 work in progress** | Phase 3 code is uncommitted in files Phase 2.2 also changes, and `sw/reproduce.py` reads `score.median_thresholds` and `tuition_increase_by_year`. See section 5 |
| BM-8 full-tuition calibration | **Correct the comparison** | Compare Brandon's 9 with the History sheet's **actual** base-cohort enrolled in full-tuition cells first (a data check), then with the ledger's expected Baseline (a model check). Report both; assert neither. Confirm that "full ride" means full tuition with no stipend |
| BM-10 bookkeeping | **Confirm, plus three places** | Also update `CLAUDE.md` working rule (7) (5.5%), the spec's section 2 tuition line and the D4 row, and mark the `DECISIONS.md` Nov 13 line "Richmond planning tuition 5.5%" as superseded |

## 2. BM-1 continuity correction: derivation and test

**Event.** With `G+` and `G-` the scored enrolled at or above and below t, the q-th percentile is at or above t when `G- <= q N`, where `N = G+ + G-`. This is the inclusive tie rule; at `q = 0.5` it is v0.6's "at least half at or above t". Equivalently `M_q = q G+ - (1 - q) G- >= 0`.

**Lattice.** Write `q = m/n` in lowest terms. Then `n M_q = m G+ - (n - m) G-` is an integer, and because `gcd(m, n - m) = 1` it takes every integer value. So `M_q` lives on a lattice of step `1/n`. The (G+, G-) distribution is smooth over many students (the SD of M_q is 2 to 9 here), so neighbouring lattice points carry nearly equal mass, and the half-step correction applies:

`P(percentile q at or above t) = 1 - Phi((-1/(2n) - E[M_q]) / sqrt(V_q))`

| q | n | Correction | Equivalent |
|---|---|---|---|
| 0.10 | 10 | 0.05 | |
| 0.25, 0.75 | 4 | 0.125 | |
| 0.50 | 2 | 0.25 | v0.6's 0.5 on the doubled margin `G+ - G-` |

`V_q` as Brandon wrote it is confirmed.

**Test.** Exact: given the two shocks, G+ and G- are independent sums of cell binomials, so `P(m G+ >= (n - m) G-)` comes from two one-dimensional distributions, mixed over 20-node Gauss-Hermite (20 x 20 nodes at rho 0.5). The setup was 20 synthetic worlds with 6 scenarios each (pool 0.6 to 1.8, bonus 0 to $10,000, shift -4 to +4 points), q in {0.10, 0.25, 0.50, 0.75}, every scored band bound as t, kept where P lay roughly between 0.01 and 0.99.

| Comparison | Cases | Max error, derived `1/(2n)` | Max error, v0.6's 0.5 reused | Max error, no correction |
|---|---|---|---|---|
| Exact, rho 1.0: q = 0.10 / 0.25 / 0.50 / 0.75 | 181 / 139 / 220 / 141 | 0.0124 / 0.0046 / 0.0016 / 0.0047 | 0.062 / 0.036 / 0.020 / 0.040 | 0.020 / 0.019 / 0.020 / 0.008 |
| Exact, rho 0.5 (8 worlds) | 92 / 60 / 113 / 68 | 0.0104 / 0.0034 / 0.0014 / 0.0040 | 0.059 / 0.029 / 0.017 / 0.034 | 0.018 / 0.013 / 0.017 / 0.007 |
| Simulation, 200,000 draws, rho 1.0 and 0.5 | 123 | **0.0108** (all q) | 0.058 | 0.019 |
| q = 0.5 against the v0.6 median closed form | 333 | 2e-16 | | |

The derived correction is best at every q and passes test 4's 0.02 everywhere. Reusing 0.5 fails 0.02 at q = 0.10.

**Where it is weakest.** At q = 0.10 every error above 0.01 occurs when fewer than 20 students are expected below t (max 0.0124; 0.0053 between 20 and 30; 0.0034 above 30). That count is small and skewed. Hence the label "approximate (fewer than 20 expected below t)", and test tolerances of 0.01 where at least 20 are expected below t, 0.02 otherwise. At a class of 140, the 10th percentile always carries the label: about 14 students decide it, which is the honest reading.

**Margin unit.** One swap of a below-t student for one at or above t (N fixed) changes `M_q` by exactly 1. So `M_q` is "swaps to spare (or needed) at the same class size". Adding k below-t students without removing anyone uses `k(1 - q)`, so the class absorbs `M_q / (1 - q)` additions. For example, at q = 0.10 a margin of -1 needs 1 swap, or 10 more students at or above t if no one leaves.

## 3. Draft amendment text, spec v0.6.3 (tag **[v0.6.3, BM-n]**)

**Header.** Status: v0.6.3 (Nov 17, 2026): Brandon Metheny's reply applied (`Review_Points_Brandon_Nov17.md`, `Review_Phase2_2_Plan.md`); ready for Phase 2.2.

**Section 2, config.**
- `score.percentile_targets`: list of `{q, t}`; `q` in (0, 1) with at most two decimals; each `t` a lower bound in `score.bands` (the loader enforces both). The legacy `score.median_thresholds: [t, ...]` loads as `{q: 0.5, t}` for each value, and the loader keeps `median_thresholds` available as the derived list of q = 0.5 thresholds (reproduce mode reads it). The Trim order's threshold is the first target with q = 0.5. GPA percentiles are not supported (one GPA boundary); the README says so. **[v0.6.3, BM-1]**
- `tuition_by_year_usd` (optional, by plan year): when set for a year it takes precedence over `tuition_increase_by_year`. Baseline's `tuition_increase_pct` is the implied increase `100 x (tuition_by_year_usd / tuition_base - 1)`, stored unrounded, so `round_to(tuition_base x (1 + p), tuition_rounding_usd)` returns the dollar figure exactly. Inputs shows the implied increase. Children inherit it as before. **[v0.6.3, BM-2]**
- `ntr_goal_basis`: `entering_y1` (default) or `all_jd`; `continuing_ntr_usd` (required under `all_jd`): net tuition from continuing students in the plan year, supplied by the client and held fixed. Under `all_jd`, `ntr_target` is the total JD goal, and every figure that reads it uses the effective entering target `ntr_target - continuing_ntr_usd`. **[v0.6.3, BM-4]**
- `trim.protect_segment`: `below_threshold`, `above_floor` or `none`. `above_floor`: segment cells with a score at or above `score.floor` and below the trim threshold go after all non-segment cells below that threshold; segment cells below the floor, and unscored segment cells, are trimmed in normal order. **[v0.6.3, BM-5]**
- `pool_ytd_growth` and `pool_ytd_as_of` (date): editable Inputs cells. Growth to date is the change in complete applications at or above `score.pool_threshold` against the same week of the prior cycle. Display only. **[v0.6.3, BM-6]**

**Section 3, readouts.**
- Percentile block (Summary, Middle case; Low and High as for the median), per target: `margin_q_t = q x N_scored - G-` (swaps at the same class size), `P(percentile q at or above t)`, and the rho 0.5 line. The v0.6 median rows and names (`margin_t`, `p_median_t`) stay unchanged. **[v0.6.3, BM-1]**
- Spread: for q = 0.25 and 0.75, the score band whose lower bound is the largest t with expected share below t at most q (ratio of expected counts), labeled "band, not a score". **[v0.6.3, BM-1]**
- Class-size table: add P(class > cap) at each N, from the trimmed admits; and margin and P for each percentile target. **[v0.6.3, BM-3, BM-1]**
- Pool strip: P(holds) for each percentile target (from the same linear split); the row nearest `1 + pool_ytd_growth` is marked "growth to date ({as of}) is about here". **Break-even pool multipliers:** `m_class = (class.target - M_lo) / M_hi`; `m_q = -E[M_q]_lo / E[M_q]_hi` for each target. Both are expectations, labeled "pool multiplier at which the expected class meets the target / the expected margin is zero; not a probability". **[v0.6.3, BM-6]**
- NTR goal under `all_jd`: the Summary shows "projected JD net tuition = continuing (client-supplied) + `ntr_y1`" and `P(continuing + ntr_y1 >= ntr_target)`. The tuition what-if shows `ntr_y1` only, with "continuing revenue held at the supplied figure". **[v0.6.3, BM-4]**

**Section 4, labels.**
- `PCT_APPROX_LABEL` = "approximate (fewer than 20 expected below t)".
- `BAND_NOT_SCORE_LABEL` = "band, not a score".
- `CONTINUING_LABEL` = "continuing-student revenue as supplied by the client; attrition and renewals not modeled".
- `POOL_BREAKEVEN_LABEL` as above.

**Section 5, closed form.** Add: `M_q = sum_c g_c mu_c` with `g = +q` at or above t, `-(1 - q)` below, 0 for unscored under `excluded` (`-(1 - q)` under `below`). `V_q = q^2 sum_{above} v + (1-q)^2 sum_{below} v + s^2 (q^2 G+^2 + (1-q)^2 G-^2 - 2 rho q (1-q) G+ G-)`. `P = 1 - Phi((-1/(2n) - E[M_q]) / sqrt(V_q))`, with `q = m/n` in lowest terms (half the lattice step of `M_q`). At q = 0.5 this equals the v0.6 median probability exactly. Validated against exact distributions and simulation (`Review_Phase2_2_Plan.md` section 2).

**Section 7, Checks.** Add `score.floor` to the "rebuild needed" rows when `protect_segment` is `above_floor`. Add a row "each percentile t is a band bound" (static).

**Section 11, tests.** Add tests 21 to 26 (section 4 below); extend tests 2, 3, 4, 14 and 20.

**Section 12, phases.** Add the row: "2.2 | BM-1 to BM-6, tests 21 to 26 | all tests pass; Excel parity on the main and edge workbooks; mutation check clean".

**Section 15, item 10 (Richmond data needs).** Add: continuing-student net tuition for the plan year (BM-4); the LSAT scores Richmond tracks at the 25th and 10th percentiles (BM-1); whether 140 is a ceiling (OD-11).

**Section 15, item 11 (contract).** Add `margin_q_t`, `p_pct_q_t`, `p_pct_q_t_rho05` (s x k x target), `pct_band_q` (s), `p_class_over_cap` in `CT_CLASS_TABLE`, `pool_breakeven_m`, `p_jd_ntr_ge_goal`.

**Section 2, `tuition_increase_by_year` line, and the D4 row.** Replace "Richmond planning [5.5%, unconfirmed]" with "Richmond 2027: $63,500 proposed (Brandon, Nov 17; Board approval February 2027), entered as `tuition_by_year_usd`".

**Methodology Appendix F (text for `02_methodology_v2.8.md`).** "Score percentile at or above t: at most a share q of scored enrollees (excluding unscored, as for the median; O41) score below t; the median is q = 0.5. Margin: `q x N_scored - G-`, the number of below-t enrollees that could replace enrollees at or above t at the same class size. The 10th percentile is a client measure, not an ABA 509 figure. The ABA's own percentile convention is to confirm against the 509 instructions (O41)."

**Richmond config (until Brandon answers OD-13):**
- `percentile_targets`: the two median targets as today; a q = 0.25 target at the band bound at or below Richmond's public ABA 509 25th percentile LSAT (from your 509 dashboard), commented "placeholder, nearest band bound at or below the 509 figure; OD-13"; q = 0.10 unset.
- Note: t must be a band bound, and Richmond's bands below 165 are 161, 158, 154 and 152, so a 25th percentile of, say, 160 can only be tested at 158 or 161.
- `tuition_by_year_usd: {2027: 63500}` with the comment from BM-2.
- `trim.protect_segment: above_floor`.

## 4. Phase 2.2 task list

Order matters: config and loader first, then Python, then Excel, then tests 3 and 20.

| # | Task | Files | Tests |
|---|---|---|---|
| 1 | Loader: `percentile_targets` (validation of q and t, legacy mapping, derived `median_thresholds`); `tuition_by_year_usd` precedence and unrounded implied increase; `ntr_goal_basis` and `continuing_ntr_usd`; `protect_segment: above_floor`; `pool_ytd_as_of` | `sw/config.py`, configs | **21** (loader): t outside the bands rejected; q outside (0, 1) or with three or more decimals rejected; legacy `median_thresholds` loads to `{0.5, t}`; `all_jd` without `continuing_ntr_usd` rejected; for 200 random bases, `round_to(base x (1 + implied), 50)` equals the dollar figure exactly |
| 2 | Percentile closed form with the `1/(2n)` correction; margins in swaps; the "approximate" flag; band readout | `sw/risk.py`, `sw/ledger.py`, `sw/labels.py` | **22**: hand-computed margins and probabilities at q = 0.10, 0.25, 0.5 and 0.75 on the toy grid; q = 0.5 gives P equal to `p_median_t` to 1e-12 and margin equal to `margin_t / 2`; band readout on a hand case. **Test 2 extended:** closed form against the exact two-pmf convolution (section 2 method), tolerance 0.01 where 20 or more are expected below t and 0.02 otherwise, at rho 1.0 and 0.5. **Test 4 extended:** against simulation within 0.02 on 20 worlds, both rho |
| 3 | Trim order `above_floor`; class-size table gains P(class > cap) and percentile rows | `sw/trim.py` | **23**: with `above_floor`, no segment cell below the floor (or unscored) is cut after a non-segment cell at or above the floor; segment cells from the floor up to t go after non-segment cells below t; `below_threshold` ordering unchanged (test 14 passes). **Test 14 extended:** for every target t, the share at or above t is non-decreasing while the walk cuts cells below t. P(class > cap) at each N equals `risk.cf_class` on a ledger evaluated at that N's trimmed rates |
| 4 | Pool strip: percentile columns, marker, as-of date, break-even multipliers | `sw/strip.py` | **24**: `m_class` evaluated through the ledger gives expected class equal to the target within 1e-9; `m_q` gives expected `M_q` of 0 within 1e-9; percentile P at each m equals a ledger evaluation at that pool multiplier |
| 5 | NTR goal basis | `sw/risk.py`, `sw/strip.py` | **25**: `entering_y1` reproduces v0.6 everywhere; `all_jd` with continuing 0 equals `entering_y1`; for any goal G and continuing C, each of the three figures under `all_jd` at G equals the `entering_y1` figure at G - C |
| 6 | Excel: Inputs (percentile table, implied increase, basis, continuing, as-of date); Summary percentile block and spread; class-table columns; pool-strip columns, marker and break-evens; Checks (floor in the rebuild check, band-bound row); README (GPA percentiles not supported, margin unit, labels) | `sw/workbook.py`, `sw/narrative.py`, `sw/contract.py` | **Test 3:** main and edge workbooks cover at least three targets, including one with fewer than 20 expected below t; the edge config adds `all_jd`, `above_floor` and a `tuition_by_year_usd` year. **26:** after editing `pool_ytd_growth` and recalculating in LibreOffice, only the marker cells change (every other formula cell identical) |
| 7 | Mutation check: new Python and Excel mutants | `tests/mutation_check.py` | **Test 20:** at least the correction (0.5 in place of `1/(2n)`; must fail test 2 at q = 0.10), the percentile weights, `above_floor` tiers, the class-table P(cap), the break-even formulas, the effective NTR target in each of its three uses, and the tuition precedence. No survivors |
| 8 | Reproduce mode unaffected | none | **Test 6** passes unchanged on the fixture |
| 9 | Bookkeeping (BM-10) | `DECISIONS.md`, `CLAUDE.md` rule (7), spec, `efa_fao/docs/data_request_v3/spec/` | none; the reviewer checks the text |

Out of scope: BM-7 (Phase 3), BM-8 (live build: a report row comparing History's actual base-cohort full-tuition enrolled, and the Baseline expected, with Brandon's 9), BM-9 (deferred).

## 5. Sequencing judgment call

The Brandon note recommends Phase 2.2 before Phase 3. The working tree, however, already holds uncommitted Phase 3 work (`sw/reproduce.py`, test 6, edits to `config.py`, `ledger.py`, `workbook.py` and `labels.py`), and Phase 2.2 changes the same files. Reproduce mode needs none of BM-1 to BM-6: YA has only the median, and tuition is loaded from the fixture.

**Recommended:** let the Phase 3 session finish S4's reproduce acceptance (BM-7) and commit, then run Phase 2.2 from that commit, with test 6 as a regression guard.

**Alternative:** pause Phase 3 and commit its work in progress on a branch first. Choose this if Richmond needs percentile rows before S4's reproduce result.

Either way, do not run the two passes on the same uncommitted tree.

**Not verified:** the ABA 509 percentile convention (O41); Richmond's 509 25th-percentile figure (not looked up, to keep the client name out of searches); desktop Excel for the Phase 2.2 cells (the Phase 2.2 acceptance should repeat the sentinel-copy comparison).

## Addendum, November 18: checked against Richmond's ABA 509 data

**Source:** the 509 dashboard repository (`aba-509-saas/data`): the ABA's annual compilations for 2021 to 2024 and the dashboard's 2025 scrape. The 509 figures below are public. The comparisons with the fixture ran on your computer and are reported here only as agree or disagree.

**Richmond, 509 by report year (report year = fall entering class):**

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| First-year class (all full-time; part-time 0) | 145 | 121 | 134 | 133 | 146 |
| LSAT 25th / 50th / 75th | 157 / 162 / 163 | 158 / 163 / 165 | 157 / 164 / 165 | 158 / 164 / 165 | 159 / 164 / 167 |
| UGPA 25th / 50th / 75th | 3.46 / 3.70 / 3.79 | 3.33 / 3.75 / 3.87 | 3.50 / 3.75 / 3.86 | 3.50 / 3.75 / 3.83 | 3.66 / 3.81 / 3.92 |
| Without an LSAT (GRE etc.) | 0 | 0 | 0 | 0 | 2 |
| Full-time tuition (no fees) | $50,500 | $51,510 | $53,440 | $55,550 | $57,700 |
| Students at full tuition / more than full, all JD | 101 / 5 | 91 / 4 | 92 / 4 | 80 / 3 | see note |

**What this settles:**
- **O41 basis (BM-1):** the 509 computes LSAT percentiles over students with an LSAT and reports the others separately (2025: 144 of 146), and does the same for GPA. That is `unscored_in_median: excluded`. The fixture's count rows use the same rule (Phase 3 found 18 of 18 groups). The 509's interpolation convention cannot be read from these figures; at band resolution it does not matter.
- **BM-1 placeholder:** Richmond's 509 25th-percentile LSAT is 158 (2024) and 159 (2025). The nearest band bound at or below is **158**, so use q = 0.25, t = 158 (OD-13 placeholder). Testing 159 itself would need a 158/159 band split in Richmond's cell data. The 509 median is 164 in 2023 to 2025, below both median thresholds (166 and 165), which are goals, not the current position.
- **B3-9 / BM-3 class basis:** Richmond has had no part-time entrants since 2021, so whether the cap counts part-time entrants is moot. The fixture's enrolled totals equal the 509 first-year class for 2024 and 2025, including the 509's "other first-year enrollees". Its unscored and blank-GPA counts equal the 509's excluded counts.
- **OD-11 (cap firmness):** the 2025 class was 146, six above 140. Ask Brandon whether 140 was the cap that year.
- **OP-8 / BM-2 tuition:** published tuition is $55,550 (2024) and $57,700 (2025). The fixture's implied 2024 tuition matches exactly; its 2025 figure is $100 below the 509's. Enter the 509 figures in `tuition_by_cohort` for 2024 and 2025. The 2026-27 figure is not in the 509 yet (the 2026 report comes out later), so Jason enters Richmond's published figure. **Dean Rooksby's "just over 5.5%"** holds if the published 2026-27 tuition is between about $60,150 and $60,190 ($63,500 / 1.0559 to $63,500 / 1.0551). The fixture's implied base would then be a few hundred dollars low, as its 2025 figure is $100 low. Check this when entering the published figure.
- **BM-8 (full rides):** the all-JD full-tuition counts of 80 to 101 (2021 to 2024) are about 27 to 34 per entering class, which matches Brandon's "roughly 27 in earlier years". This supports reading "full ride" as the 509's "full tuition" category, with "more than full tuition" separate (3 to 5 a year). The fixture's cell grid does not reproduce 9 in its latest history cohort: it holds one award per cell, so full rides inside a cell with a lower policy award are invisible. The BM-8 comparison should state that limit.
- **Note on the 2025 scrape (for the 509 dashboard, not this project):** the 2025 grants row has the same count (101) for "half to full" and "full tuition", which looks like a scraper duplication. Verify it against the 2025 PDF before using it.
- **BM-4 sanity range (public data only, order of magnitude):** continuing students in 2027-28 are the fall 2025 and fall 2026 classes, about 280 after attrition and transfers (2025: 1 other attrition, 4 transfers out). About 82% receive grants, with a median grant of $30,000 to $40,000 (2021 to 2025). The 75th-percentile grant equals the prior year's tuition in 2022 to 2025, which suggests renewals are fixed in dollars. Continuing net tuition at $63,500 would be roughly $8.5M to $10M. Use this to sanity-check the client's `continuing_ntr_usd`, not in place of it.

**New finding, High for BM-1: the fixture's LSAT bands below 161 do not match the 509.** In both 2024 and 2025, more than a quarter of the fixture's LSAT-holding enrollees sit below 158, which the 509's 25th percentile (158, then 159) does not allow. The 2024 counts also put the median below 161, against the 509's 164. Everything else agrees: class size, unscored count, blank-GPA count, the share below 3.83 GPA in both years, the LSAT 75th percentile, and the 2025 median. Likeliest cause (suspected, not shown): the YA history panels place students by an LSAT other than the highest score the ABA uses, or the lower bands are labeled differently in the history panels than in the scenario panels. Consequence: percentile and median margins computed on cell data with this basis will not match the 509 figures Richmond reports. **Add to Phase 2.2 (task 10):** a report-only "509 reconciliation" block on the History sheet, per history cohort and comparing the cell data with the client's public 509: first-year class, unscored and blank-GPA counts, and whether each published LSAT and UGPA quartile is consistent with the band shares. It applies to any law client. **Add to the data request:** score bands by the highest LSAT, as reported to the ABA. **Add OD-14 (Brandon or Jason):** which LSAT the YA grid uses.
