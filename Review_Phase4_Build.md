# Review: Phase 2.2 and Phase 4 build (scenario-workbook prototype)

**Reviewer:** independent session (did not write the build) | **Date:** November 19, 2026 | **Range:** `phase3-accepted` (d633fc4) to `phase4-built` (4d59750), 44 files | **Read:** `CLAUDE.md`, `DECISIONS.md` (Nov 17 to 19), spec v0.6.3 section 0A, `Review_Phase2_2_Plan.md` sections 2 to 4 | **Edited:** this file only; nothing committed.

Severity: Critical, High, Medium, Low. "Shown" means reproduced in this review; "suspected" means read from code or inferred, not run. No Yellow Arrows figure appears in this file.

## 0. Environment (read first)

The project `.venv` could not be used. It is a macOS arm64 environment, and the shell on the linked Mac is a Linux VM that cannot execute it (`Exec format error`) and has no package network. The suite ran instead in this session's Linux workspace from a staged copy of the working tree at `phase4-built` (tree clean, HEAD = tag):

| Item | Project `.venv` (lock) | This run |
|---|---|---|
| Python | 3.12.15 | 3.13.18 |
| numpy / scipy / pandas | 2.5.4 / 1.18.1 / 3.0.6 | 2.5.3 / 1.18.1 / 3.0.5 |
| xlsxwriter | 3.3.1 | 3.2.9 |
| LibreOffice | 26.8.3.1 | 24.2.7.2 |

The build id (which hashes `requirements.lock`, not installed versions) came out the same as on the Mac (`631be71b4843`), so the inputs are identical. The fixture was copied into this session's private workspace for the fixture run and deleted afterwards; nothing derived from it was written to the Mac. **Re-run the suite in the project `.venv` on the Mac before acceptance**; the results below are evidence, not the acceptance run.

## 1. Test runs

| Run | Result | Failures |
|---|---|---|
| Without `YA_FIXTURE_PATH` | 234 passed, 72 skipped, 1 failed (307 collected; 276 s) | `test_03::test_integer_reproduce_workbook_equals_python`: one cell, `Checks!C15` (the R3-3 rounding probe), Python 3, LibreOffice 2 |
| With `YA_FIXTURE_PATH` | 302 passed, 3 skipped, 2 failed (307 collected; 279 s) | the same probe cell in the synthetic reproduce workbook and in the fixture reproduce workbook (`test_06::test_reproduce_workbook_equals_python`) |

The 3 skips are the documented Baseline criteria not derivable from the file. Reproduce criteria: 60 rows, 0 failures, 2 cells not reproducible (as accepted in Phase 3); `ntr` ours minus file is exactly 0 for Scenarios 1 to 4.

**Reading of the failures:** environment, not this change. `ROUND(0.35/0.14,0)` is 2 in LibreOffice 24.2.7 and 3 in Python, LibreOffice 26.8 and Excel for Mac (Phase 3). The probe is doing its job: it is the only cell that differs across about 3 x 10,000+ formula cells, so no ledger figure in these builds lands on a rounding knife-edge. It does mean results depend on the spreadsheet engine version, which is a further reason for the pending Windows Excel check (R4-16).

## 2. Hand checks

| # | Check | Method | Result |
|---|---|---|---|
| 1 | Percentile probability and the `1/(2n)` correction | Own brute-force exact distribution (fine shock grid, binomial pmfs, explicit double sum over G+ and G-), 8 small grids, q in {0.10, 0.25, 0.5, 0.75}, rho 1.0 and 0.5, kept where 0.01 < P < 0.99 (17 cases) | Closed form within **0.008** of exact (max at q 0.10 with 12 expected below t, a case that carries the "approximate" label); `1/(2n)` beats the 0.5 correction in every case (0.5 errs up to 0.057) and beats no correction in 15 of 17. `risk.exact_pct` equals my brute force to 4 decimals in all 17 cases. Shown |
| 2 | Margin in swaps | Toy Baseline at t = 166 (G+ 9.6, G- 19.5): margins by hand at four q; move one enrollee from c2 (161) to c1 (170); add 3 enrollees at 161 | Margins equal the hand values (-16.59, -12.225, -4.95, 2.325); one swap moves each by exactly 1.0; adding 3 below moves by -3(1 - q). Shown |
| 3 | `above_floor` trim order | Own 10-cell grid with segment cells at 152, 154 (the floor), 158, 166 and unscored; order written out by hand | `above_floor`, `below_threshold` and `none` all match the hand order. Segment cell at exactly the floor is protected. Shown |
| 4 | `all_jd` basis, three places | Synthetic world, goal G = $9.0M, continuing C = $5.2M, against `entering_y1` at G - C, and by hand `1 - Phi((G - C - mean) / sd)` | Summary probability, every yield-strip probability and the NTR break-even shift identical (difference 0); hand value identical. Excel uses `in_ntr_target_eff` in all three formulas (read). Shown |
| 5 | Break-even pool multipliers | Evaluate the ledger at `m_class` and each `m_q` | Expected class 140.0 at `m_class`; expected `M_q` 0 (to 2e-15) at each `m_q`. Shown. See R4-04 for values that are negative or outside the grid |
| 6 | `tuition_by_year_usd` round trip | 2,000 random bases (including cents) and dollar figures on the $50 unit | 0 failures; an increase given for the same year is ignored (precedence holds). Shown. See R4-15 for a two-year gap |
| 7 | Reproduce need rounding and Scenario 4 fixed amount | Fixture run, per scenario and case; pool and yield strips | NTR ours minus file = 0 for Scenarios 1 to 4; only Scenario 4 carries a departure; need stays positive in every case and at every pool-strip and yield-strip point. Shown. See R4-07 for what the file cannot tell us |
| 8 | Distribution and top-quartile share | Toy Baseline by hand: class 30.6, quartile 7.65; (170, hi) 6.6 enrolled fully in, (170, lo) 1.05 of 3.0 in | Top-quartile merit $365,300 of $693,800, share 0.52652; `ledger.top_quartile_merit` identical. LibreOffice values of the Distribution sheet equal Python (test 3 passes on main, edge and reproduce builds). Shown |

## 3. Reviewer mutants

Each mutant applied alone to a scratch copy, chosen where the builder's 154 Python and 116 Excel mutants do not reach. Python mutants ran the Python suite with `SW_SKIP_EXCEL=1` and without test 4 (simulation; none of these mutants touches a probability formula); baseline 186 passed. Excel mutants ran tests 3, 6, 7, 8, 9, 18, 23 and 26 with LibreOffice, leaving out the one probe-affected test from section 1.

| ID | Mutant (one change) | Result | Caught by |
|---|---|---|---|
| R01 | Growth-to-date marker: a tie goes to the upper row (`<` to `<=`) | **Survived** | none (R4-13) |
| R02 | Spread band: share below t strictly less than q (`<=` to `<`) | **Survived** | none; differs only at an exact tie (R4-13) |
| R03 | `tuition_by_year_usd` not a multiple of the rounding unit accepted | caught | test 21 |
| R04 | Duplicate percentile target accepted | caught | test 21 |
| R05 | Config with no q = 0.5 target accepted | caught | test 21 |
| R06 | Legacy `median_thresholds` disagreeing with the targets accepted | caught | test 21 |
| R07 | Unsorted pool grid accepted | caught | test 21 |
| R08 | Segment cell exactly at `score.floor` not protected (`>=` to `>`) | caught | test 23 |
| R09 | `p_jd_ntr_ge_goal` filled under `entering_y1` | caught | test 25 |
| R10 | JD projection is continuing minus `ntr_y1` | caught | test 25 |
| R11 | Need departure sign reversed in `ntr_const` | caught | test 6 (no fixture) |
| R12 | `tuition_by_year_usd` for a year at or before `base_cycle` accepted | caught | test 21 |
| R13 | Straddling position dropped from the top quartile | caught | test 19 |
| R14 | `m_q` denominator with median weights (q ignored) | caught | test 24 |
| R15 | Pool-strip percentile binomial variance scaled by m squared | caught | test 24 |
| RX01 | Excel percentile sign: unscored always 0 (ignores `unscored_in_median: below`) | **Survived** | none (R4-09) |
| RX02 | Excel spread band: unscored term dropped under `below` | **Survived** | none (R4-09) |
| RX03 | Continuing-revenue row shown under `entering_y1` | caught | test 3 |
| RX04 | P(JD goal) shown under `entering_y1` | caught | test 3 |
| RX05 | Inputs: a q = 0.5 target's t written as a static value (no longer follows `median_thresholds`) | **Survived** | none (R4-10) |
| RX06 | Spread text for the lowest band (bound 0) shown as "0 to below ..." | **Survived** | none; no build reaches the lowest band (R4-10) |
| RX07 | Inputs implied tuition increase written as a static value | **Survived** | none (R4-10) |
| RX08 | Pool-strip Vm part without (1 - y) | caught | test 3 |

13 of 15 Python and 3 of 8 Excel mutants caught. The surviving Python mutants are tie rules; the surviving Excel mutants sit on branches no built workbook reaches (`unscored_in_median: below`, the lowest band) or on cells whose liveness no test edits. The builder's own report (`output/mutation/`, fixture present) shows 154 of 154 Python and 116 of 116 Excel mutants caught, with the warning that test 3 accounts for 61 of the 116 Excel catches.

## 4. Fixture rule

| Scope | Method | Result |
|---|---|---|
| Code, configs, tests, docs under `prototypes/` | Every distinctive numeric value in the fixture (691 tokens: non-integers with 4+ significant digits; integers of 1,000 or more that are not round thousands; with and without thousands separators) searched as a token | 3 files: `63500` in `richmond.yaml` and `test_21_loader.py`; `12,500` in `test_19` (a toy award) |
| `DECISIONS.md`, `CLAUDE.md`, spec, methodology, `Review_Phase2_2_Plan.md`, `Review_Phase3_Build.md`, `Review_Points_Brandon_Nov17.md`, `efa_fao/` (incl. data request v3 spec and outputs) | Same | `63,500` and `55,550` only |
| Data request outputs changed in the range (law template `.xlsx`, Richmond law `.docx`) | Text extracted, same scan | No match |
| Summary PDF (`output/phase4/Summary_render.pdf`) | Text extracted, same scan | No match (synthetic build) |
| Values the Phase 2.2 tests use for the need rule (`200000`, `190000`, `1429`) | Exact search of the fixture | Not in the fixture |
| git | `git ls-files`; `.gitignore` | Fixture, `ya_workbook_support/`, the assessment and `prototypes/scenario_workbook/output/` are ignored; no tracked workbook from the prototype |

**Verdict: the rule holds.** The two matches are coincident client facts with independent sources: $63,500 is Brandon's 2027 figure (Nov 17, confirmed Nov 18) and $55,550 is the public 2024 ABA 509 tuition (DECISIONS Nov 18). $12,500 is a toy award. No delivered workbook exists yet; the reproduce workbooks in `output/richmond_law/` hold fixture values by design and are git-ignored. Not checked: the Scenario 4 live scenario file (not generated yet; R4-06).

## 5. Summary PDF as a client page

Reviewed all 18 pages of `output/phase4/Summary_render.pdf` (synthetic build `631be71b4843`, rendered by LibreOffice 26.8.3.1 on the Mac). Findings R4-01 to R4-03, R4-10 and R4-11 below. What reads well: the section notes now carry the response and shock labels on every section; the clamp text is right-aligned; the parent names wrap; the percentile block explains the margin unit; the break-even table carries "not a probability".

## 6. Findings

| ID | Severity | Finding | Evidence | Location | Fix |
|---|---|---|---|---|---|
| R4-01 | High | Two Summary sections print too small to read. The pool strip page is fit to one page width while its "split at m = 1" parts table now has 7 + 16 columns (G+, G-, V+, V- for each of four percentile targets), with unformatted values up to 16 digits; the page prints at about a third of size. The class-size table (3 + 8 new columns) prints at about a fifth. The pool strip is part of the Scenario 4 deliverable | Shown: PDF pp. 10 and 11 | `sw/workbook.py` `sw_pool` (parts table), `sw_class_table`; `sw/lo.py` `_section_copy` (fit to width) | Move the parts table (working values) to a helper sheet or leave it out of the render; format any that stay; split the class table into two blocks (class and money; median and percentile); have test 10 fail when a section exceeds a column limit or a minimum scale |
| R4-02 | Medium | The three cosmetics decided Nov 19 are still present, and the same cause cuts more text: (a) no header row on continued pages (pp. 3 and 4: scenario columns unidentified); (b) column-A labels cut (pp. 2 to 4, e.g. "P(median holds), score 166, rho 0.5: if high-score and other adm"); (c) net-tuition line text cut (p. 8, "Awards fixed in dolla"). Also cut: the label legend (p. 13 shows about 15 characters of each label, including the four v0.6.3 labels); the approximation flags (pp. 3 and 6, "approximate (fewer"); the incentive "Validity" and "reading" rows (p. 7) | Shown: PDF | `sw/lo.py` `_section_copy` (no print title rows, no wrap); label column widths in `sw/workbook.py` | Set print title rows to each section's header row; wrap long labels and text cells with row heights; widen or wrap the legend text column; extend test 10 to flag text longer than its rendered cell |
| R4-03 | Medium | Two different "margins" for the same event on one page. "Median margin, score 166: -26.7 students" (at or above minus below) and "50th percentile (q 0.5) at or above score 166: margin (swaps) -13.4 students", same probability. A client reading both sees conflicting numbers in the same unit | Shown: PDF pp. 2 and 3 | `sw/workbook.py` `sw_percentiles` | Judgment call: leave q = 0.5 targets out of the percentile block (the median rows already carry them), or relabel the median margin "difference, at or above minus below (2 per swap)". Removing the rows changes nothing computed |
| R4-04 | Medium | Break-even pool multipliers are printed when they have no meaning. With a low target the expected margin is positive with no top-pool applicants at all, and `m_q` comes out negative: q 0.25 at 154 gives -0.33 to -0.60 and q 0.10 at 152 gives -0.07 to -0.28 on synthetic worlds 101 to 105. In the shipped build, 1.667 (median at 166) and 0.588 (10th at 154) lie outside the 0.8 to 1.6 grid without a note. Richmond's 25th-at-158 placeholder is the kind of target that can go negative | Shown: `strip.pool_strip` on worlds 101 to 105 with edited targets; PDF p. 10 | `sw/strip.py` `pool_strip`; `sw/workbook.py` `sw_pool` break-even formulas | Show "holds at any pool size" when both parts are at or above zero, "not reached by growth" when the sign is wrong, and mark values outside the grid; add a test case with a low target |
| R4-05 | Medium | `top_quartile_merit_share` is not in the interface contract. Spec 0A item 8 and DECISIONS Nov 19 (Phase 4 call 3) give it a named range with prefix `DIST`; the build has none, `contract.SK` and the dump leave it out, and test 9 does not look for it | Shown: defined names of build `631be71b4843`; `sw/contract.py` | `sw/contract.py`, `sw/workbook.py` `w_distribution`, test 9 | Add `DIST_TOP_QUARTILE_MERIT_SHARE` (s x k) over the Distribution share rows, add it to `SK`, the dump and the README contract list; extend test 9 |
| R4-06 | Medium | The build cannot yet produce the first Richmond deliverable as scoped (DECISIONS Nov 18): there is no way to hold the median and percentile rows until OD-14 is answered. Phase 2.2 also added percentile P columns and `m_q` break-evens to the pool strip, which the deliverable carries | Shown: no hold setting in `sw/` or the configs | `sw/workbook.py`, config | A build setting that leaves out (or marks "held until OD-14") the median, percentile and spread rows, the pool-strip median and percentile columns and `m_q`, in the workbook and the PDF; a test |
| R4-07 | Medium | The Scenario 4 need rule (the departure from `need.total` taken as a fixed amount) reproduces the file exactly, but it is a reading the file cannot confirm. The file gives one need figure per scenario at that scenario's own class, so a fixed amount and a changed need rate fit it equally well. DECISIONS and spec 0A item B5 record only the whole-dollar rounding; the fixed amount appears only in `reproduce.py`, `ledger.py` and the README. In a live build the same `need_total` override scales with class, so the live Scenario 4 deliverable will apply a different rule from the reproduce build | Shown: ours minus file NTR = 0 for Scenarios 1 to 4; only Scenario 4 departs; need positive at every case and strip point. The equivalence is shown by inspection of the file layout (one value per scenario) | `sw/ledger.py` `evaluate`; `sw/reproduce.py` `_need_total` | Record the rule and its reason in DECISIONS; decide which rule the live Scenario 4 build uses and label it; if it matters, ask Brandon how the Scenario 4 need figure was set |
| R4-08 | Medium | The tie convention changes P(percentile held) by a few points, but it is described as immaterial. The build uses the inclusive event (held when exactly a share q is below t). Exact distributions on synthetic world 101 Baseline: median at 165, 0.325 inclusive against 0.289 strict (0.036); 25th at 161, 0.021; 10th at 154, 0.009. Methodology F26 and O41 call the 509's convention "immaterial at band resolution", which is true for the band readout, not for the probability | Shown: `risk.exact_pmf` on world 101 | Methodology Appendix F item 26; README; Summary note | Judgment call, no code change needed: state the inclusive rule beside the percentile block and in F26, and reword O41 so it does not call the convention immaterial for P. What would change it: the 509 instructions giving a nearest-rank or interpolated rule |
| R4-09 | Medium | No workbook is built under `unscored_in_median: below`, which is a live Inputs choice, so the Excel percentile sign and spread-band branches for it are untested (RX01, RX02 survive). A user who switches the input gets formulas no test has compared with Python | Shown: mutants RX01 and RX02 | `tests/edge.py`, test 3 | Build a workbook under `below` (a second edge config, or switch the edge config) and compare it in test 3 |
| R4-10 | Low | Live-ness not tested for two new Inputs links. A q = 0.5 target's t should follow the median threshold, and the implied tuition increase should follow `tuition_by_year_usd`; both survive being made static (RX05, RX07). The lowest-band spread text is never reached (RX06) | Shown: mutants | test 26 pattern | Extend the test 26 edit-and-recalculate pattern to `median_thresholds` and `tuition_by_year_usd`; add a toy case whose 25th percentile falls in the lowest band |
| R4-11 | Low | In Excel, `all_jd` with a blank `continuing_ntr_usd` computes silently: the blank counts as 0, so the JD goal is compared with entering revenue only. Python rejects the config, but `ntr_goal_basis` is a live drop-down and no Checks row covers it | Suspected (code read; not recalculated) | `sw/workbook.py` Inputs `ntr_target_eff`; `w_checks` | Checks row: "ntr_goal_basis all_jd needs continuing_ntr_usd" |
| R4-12 | Low | The Summary gives P(... at or above ntr_target) but not the target itself (or the effective target under `all_jd`). Under `all_jd` the two probability rows are identical. Under `entering_y1` three labeled `all_jd` rows print empty | Shown: PDF p. 4; edge workbook | `sw/workbook.py` `sw_main` | Add rows for `ntr_target` and the effective entering target; show "not used (entering_y1)" in the `all_jd` rows |
| R4-13 | Low | Tie rules are untested and undocumented. The growth marker goes to the lower row on a tie (R01 survives), and ties are reachable with ordinary inputs: in floating point, 1 + 0.05, 1 + 0.15 and 1 + 0.25 equal the grid midpoints exactly, so 15% growth marks the 1.1 row, not 1.2. The spread-band tie (R02) is the same convention as R4-08 | Shown: mutant R01; float check | `sw/strip.py`, `sw/workbook.py` `sw_pool` | Pick the rule (lower, upper or round half up), say it in the marker note, and test it at 15% |
| R4-14 | Low | `tuition_by_year_usd` for a later year still needs `tuition_increase_by_year` for every earlier year, although the dollar figure resets the factor: `{2028: 60000}` with plan 2028 and no 2027 value raises "no value for 2027"; the Excel builder would fail on `tyears.index`. Not reachable while plan = base + 1 | Shown: Python | `sw/config.py` `plan_increase_pct`; `sw/workbook.py` `tuition_factor_x` | Skip years before the last dollar year, or say in the loader message that each year needs a figure |
| R4-15 | Low | The desktop Excel evidence is thin for this build. `output/phase2/excel_compare_report.json`, which DECISIONS Nov 17 cites for the Phase 2 desktop-Excel parity, now holds a pytest temporary file's LibreOffice result (build `631be71b4843`, Nov 19 17:18). The Nov 19 decision to write hand-run reports to a build-specific file is not implemented (`compare_excel_saved.py` is unchanged in the range). The newest Excel-saved copy is of `0614216cf543`, not the final build | Shown: file contents and dates on the Mac | `tests/compare_excel_saved.py`; the test that calls it | As decided Nov 19; re-run desktop Excel parity on the final build before acceptance, and Windows Excel before Richmond |
| R4-16 | Low | N83 is still caught only by a crash (test 1, "too many values to unpack", 2.5 s), as noted Nov 19 | Shown: `output/mutation/report.json` | `tests/test_19_output_coverage.py` | As decided: a value test in which residency order within a position would change the share |
| R4-17 | Info | The rounding probe gives 2 in LibreOffice 24.2.7 (3 in Python, LibreOffice 26.8 and Excel for Mac). It is the only mismatching cell in three compared workbooks. Results depend on the engine version | Shown: section 1 | Checks probe row | None in code. Pin the LibreOffice version used for acceptance in `config/tools.yaml` notes; keep the Windows Excel check |
| R4-18 | Info | This review did not run in the project `.venv` (section 0) | Shown | none | Re-run the full suite with and without the fixture on the Mac |

## 7. Verdict

**Computation: sound.** The Phase 2.2 formulas hold up under independent checks. The percentile closed form and its `1/(2n)` correction agree with my own exact distribution within 0.008. The margin counts swaps exactly, and the `above_floor` order matches a hand order. The `all_jd` basis is consistent in all three places, and the break-evens hit their targets through the ledger. Tuition round trips 2,000 of 2,000 times, reproduce NTR matches the file exactly, and the top-quartile share matches a hand case. The suite passes apart from one engine-dependent probe cell, and the fixture rule holds. No Critical finding.

**Phase 4: not ready to accept as the client-facing render.** Jason's acceptance criterion for Phase 4 is the PDF. Two pages are unreadable (R4-01), and the three cosmetics decided Nov 19 plus more cut text remain (R4-02). The Distribution figure decided for the contract is missing (R4-05).

**Before the first Richmond workbook:**
- Fix R4-01, R4-02, R4-05 and R4-06 in the fix pass, plus R4-04 and R4-09.
- Jason decides R4-03, R4-07 and R4-08. Each is a judgment call, and none changes a computed figure except the need rule in the live Scenario 4 build.
- Re-run the suite in the project `.venv` and desktop Excel parity on the final build (R4-15, R4-18), then Windows Excel as already decided.

The Low items can ride along with the fix pass.
