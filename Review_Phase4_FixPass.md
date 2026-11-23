# Review: Phase 4 fix pass (scenario-workbook prototype)

Independent review of the uncommitted changes in `prototypes/scenario_workbook/` since `4d59750`, against `Reviews, Audits, and Specs/Review_Phase4_Build.md` (R4-01 to R4-18) and the Nov 19 entries in `DECISIONS.md`. Reviewer: Claude Code on Jason's Mac, Nov 20, 2026. No code, spec or config was edited and nothing was committed. Every figure below comes from synthetic data. No Yellow Arrows cell value appears in this file.

## 1. Verdict

The fix pass closes 13 of the 17 R4 items. It partly closes 3 (R4-03, R4-06, R4-08). R4-07 is closed in code but not yet in the method documents. The full suite passes with and without the fixture. Every Python mutant is caught. Excel mutation: 131 of 131 caught.

Desktop Excel for Mac parity on the final build `6d46dbd8b55c` passed on Nov 20, with 0 mismatches in 61,830 formula cells (section 8).

One item stands between this build and acceptance:

- **R4-06 leak (Medium).** On a held build, the Summary's "Working values" block still prints the parts of every held median and percentile figure. It sits outside the print area, so the PDF is clean, but the block ships in the workbook. Fix it before a held workbook goes to Richmond.

Windows Excel parity is still pending. Per R4-15 it is due before Richmond, not before acceptance. The other findings are Low and do not block acceptance.

## 2. Environment

| Item | Value | Source |
|---|---|---|
| Python | 3.12.15, project `.venv` (`../../.venv`) | `python --version` |
| xlsxwriter | 3.3.1 | `requirements.lock` |
| LibreOffice | 26.8.3.1, the version pinned for acceptance | `config/tools.yaml`; RunLog of `6d46dbd8b55c` |
| Fixture | Set by absolute path on the Mac for the second suite run and the Excel mutation run; the file was not copied | shell environment |

This review ran in the project `.venv` on the Mac. That closes R4-18.

## 3. Test runs (step 1)

| Run | Passed | Skipped | Failed | Time |
|---|---|---|---|---|
| Without `YA_FIXTURE_PATH` | 260 | 72 | 0 | 346 s |
| With `YA_FIXTURE_PATH` | 329 | 3 | 0 | 385 s |

Notes on the skips:

- **Without the fixture:** all 72 skips are the fixture-gated tests in `tests/test_06_reproduce.py`.
- **With the fixture:** the 3 skips are the Baseline criteria `ntr`, `margin_score` and `margin_gpa`, reported as "not derivable from the file" (`tests/test_06_reproduce.py:557`). This matches DECISIONS Nov 18: 57 of 57 derivable criteria, with 3 Baseline criteria not derivable.

Both runs exited 0, and no test failed.

## 4. Mutation checks (step 2)

| Mode | Mutants | Caught | Survived | Time | Report |
|---|---|---|---|---|---|
| Python (`--jobs 6`) | 165 | 165 | 0 | 3,270 s | `output/mutation/report.json` (rewritten by this run, Nov 20 14:33) |
| Excel (`--excel --jobs 2`) | 131 | 131 | 0 | 4,327 s | `output/mutation/report_excel.json` |

Excel mode:

- 16 distinct tests catch at least one mutant.
- The script warns that one test, `test_03::test_excel_equals_python`, accounts for 66 of the 131 catches, as on Nov 19. Test 3 is the Excel-equals-Python parity test, so most Excel mutants fail there by design.
- I checked the catching test for every R4 and P4.1 mutant (table below). I did not check that each of the other test 3 catches fails on the mutated cell rather than for an unrelated reason.

Python mode:

- 90 distinct tests catch at least one mutant.
- The test with the most catches is `tests/test_02_risk.py::test_closed_vs_exact_vs_sim`, with 9 of 165.

The mutants that bear on the R4 items:

| Mutant | Item | Caught by |
|---|---|---|
| R01 | R4-13 | `test_24_pool_breakeven.py::test_marker_row[0.05-4]` |
| R02 | R4-08, R4-13 | `test_22_percentile.py::test_spread_band_tie_is_inclusive` |
| N83 | R4-16 | `test_19_output_coverage.py::test_top_quartile_share_value_with_mixed_residency_at_the_line` (a value test, no longer a crash) |
| N86 to N89, N94 | R4-03, R4-06 | `test_27_fix_pass.py::test_hold_in_python` |
| N90, N91 | R4-04 | `test_24` break-even tests |
| N92 | R4-14 | `test_21_loader.py::test_tuition_by_year_usd_later_year_needs_no_earlier_increase` |
| N93 | R4-07 | `test_19_output_coverage.py::test_need_departure_is_a_fixed_amount` |
| RX01, RX02 | R4-09 | `test_03::test_edge_below_workbook_equals_python` |
| RX05, RX07 | R4-10 | `test_26::test_live_inputs_median_tuition_and_goal_basis` |
| RX06 | R4-10 | `test_03::test_edge_workbook_equals_python` |
| RX03, RX04, E119, E120 | R4-12, R4-04 | `test_03::test_excel_equals_python` |
| E117, E122, E123 | R4-06 | `test_27::test_hold_contract_ranges_equal_the_dump` |
| E118 | R4-05 | `test_09::test_every_contract_name_matches_the_python_dump` |
| E121 | R4-11 | `test_26::test_live_inputs_median_tuition_and_goal_basis` |
| E124 | R4-13 | `test_26::test_growth_tie_marks_the_upper_row_in_excel` |

## 5. R4 items (step 3)

| Item | Sev. (Nov 19) | Status | Evidence |
|---|---|---|---|
| R4-01 | High | Closed | Summary PDF: the pool strip is readable (pp. 13 and 14). The class table splits across pp. 16 to 19 and reads at about 75%. The parts table moved below the print area under "Working values ... (not printed)" (`sw/workbook.py:52`, `sw_pool_parts` at line 2432). Render limits (`MIN_SCALE` 0.75, `MAX_PAGES_ACROSS` 3) are in `sw/lo.py` and tested in test 10. |
| R4-02 | Medium | Closed | Header rows repeat on continued pages (p. 3). Column-A labels wrap. The net-tuition sentences print in full (p. 9), and so do the label legend (p. 21), the approximation flags and the Validity rows. Some text still spills past the last column; see section 6, F-5. |
| R4-03 | Medium | Partly closed | The main block shows one margin per event. q = 0.5 targets are left out of the percentile block, and the percentile rows say "margin (swaps)" (p. 3; `test_27::test_one_margin_per_event`). Still present: the pool strip prints both "P(median) 166" and "P(50th percentile at or above 166/165)" with identical values (e.g. 9% and 9%), and the break-even table keeps the q = 0.5 columns. Cause: `contract.strip_columns` lists `p_pct_q{q}_{t}` for every target, q = 0.5 included (`sw/contract.py:137`), while `ct_ptargets` drops q = 0.5 only from the main block. Low as it stands, since the strip shows probabilities only and no conflicting margin. |
| R4-04 | Medium | Closed | `strip.breakeven_m` returns "holds at any pool size", "not reached by growth", "above the pool grid" or "below the pool grid". Each case is checked through the ledger at the unclipped multiplier (`test_24::test_breakeven_multipliers_through_the_ledger`, `test_low_targets_hold_at_any_pool_size`), and Excel mirrors it (`be_x`). PDF p. 15 shows the notes. Residuals: F-2 and F-3. |
| R4-05 | Medium | Closed | `DIST_TOP_QUARTILE_MERIT_SHARE` is defined over `Distribution!$C$22:$G$24`. It is in `SK` and the dump and is checked by test 9. |
| R4-06 | Medium | Partly closed | See the note below the table. |
| R4-07 | Medium | Closed in code; open in the documents | See the note below the table. |
| R4-08 | Medium | Partly closed | The Summary states the inclusive rule beside the percentile block (`labels.PCT_TIE_RULE`; `test_27::test_tie_rule_stated`), and so does the README. The "immaterial" wording is withdrawn in DECISIONS Nov 19. Methodology Appendix F item 26 (`02_methodology_v2.8.md:1156`) gives the inclusive definition, but it does not carry the caveat that the convention moves P by a few points (0.036 at median 165 on world 101, per R4-08). The methodology is unchanged in the working tree. |
| R4-09 | Medium | Closed | `tests/edge.py:100` builds the edge workbook a second time under `unscored_in_median: below`. Test 3 compares it with Python. The fixture case moves the 25th percentile band from 158 to 154 (`edge.py:153`). RX01 and RX02, which survived on Nov 19, are now caught by `test_edge_below_workbook_equals_python`. |
| R4-10 | Low | Closed | `test_26::test_live_inputs_median_tuition_and_goal_basis` edits the median threshold and `tuition_by_year_usd` in a copy and recalculates. The edge workbook reaches the lowest-band spread text (`edge.py:144`). RX05, RX06 and RX07 are now caught. |
| R4-11 | Low | Closed | Checks row "Revenue goal: ntr_goal_basis all_jd needs continuing_ntr_usd" (`sw/workbook.py:3031`); recalculated in test 26 with `all_jd` and a blank continuing figure. |
| R4-12 | Low | Closed | PDF p. 4 shows rows for `ntr_target` ($4,300,000, synthetic) and the effective target. The `all_jd` rows read "not used (entering_y1)" (`labels.NOT_USED_ENTERING`; `test_27::test_entering_rows_and_targets`). |
| R4-13 | Low | Closed | Ties go to the upper row in Python (`sw/strip.py`, within 1e-9) and in Excel (`<=0.000000001`). Tested at 0.05, 0.15, 0.25 and -0.05 (`test_24::test_marker_row`) and in Excel at 0.15 (`test_26::test_growth_tie_marks_the_upper_row_in_excel`). The rule is stated in the marker note (`labels.POOL_YTD_TIE`). R01 is caught. |
| R4-14 | Low | Closed | `plan_increase_pct` starts at the last dollar year (`sw/config.py`); Excel uses `tuition_factor_x`. Test 21 covers Python and Excel; N92 is caught. |
| R4-15 | Low | Closed (Windows Excel pending) | `compare_excel_saved.py` now writes `output/excel_check/<build_id>.json`, and the tests write to temporary paths. `output/phase2/excel_compare_report.json` is still dated Nov 19 12:18 after today's two suite runs and after the hand-run comparison, so it was not overwritten. Desktop Excel for Mac parity on `6d46dbd8b55c` passed on Nov 20 (section 8; `output/excel_check/6d46dbd8b55c.json`). Windows Excel is pending. |
| R4-16 | Low | Closed | N83 is caught by a value test (section 4). |
| R4-17 | Info | Closed | `config/tools.yaml` pins `libreoffice_acceptance_version: 26.8.3.1`. Test 10 checks the installed version, and the RunLog records it. |
| R4-18 | Info | Closed | Section 2. |

**R4-06.** On a held build, every printed median and percentile figure reads "held pending confirmation of the LSAT basis (OD-14)" and nothing else changes, but the "Working values" block still carries the held parts (F-1).

- **What was checked:** I built `config/synthetic.yaml` with `hold_position_rows: true` in the scratchpad (build `22abbb67bb0d`) and compared it cell by cell with `6d46dbd8b55c`.
- **What changed:**
  - 1,358 cells now hold the text, and 148 merged blanks sit beside them.
  - The 5 outcome narratives changed.
  - Otherwise only the build ids, RunLog lines and the README's build and held lines differ.
- **What stayed the same:** every other figure on every sheet. Shown.
- **Tests:** `test_27` checks the same in LibreOffice (`test_hold_replaces_every_median_and_percentile_figure`) and in Python (`test_hold_in_python`, which catches N86 to N88 and N94).
- **Gap:** the "Working values" block (F-1).

**R4-07.** Live mode:

- `sw/ledger.py` `evaluate` sets `need_lump = need_total - cfg["need"]["total"]` and keeps `need_rate` from the config, so need = `need_rate × class + need_lump`.
- The Ledger writes `IF(nt="",0,nt-in_need_total)` and `need = NR*cls + NL` in every build.
- Tests: `test_19::test_need_departure_is_a_fixed_amount` in Python, the edge "Need override" in test 3 for Excel, and N93 for the mutant.

Reproduce mode:

- `need_rate` is rounded to whole dollars (spec item 5) with the same lump.
- Covered by test 6 with the fixture (passed).

Still open:

- The method still says "need = need rate × class" (`02_methodology_v2.8.md:553`).
- The spec mentions only the reproduce rounding (`Prototype_Spec_Scenario_Workbook_v0.6.md:49`).
- OD-16 (how the Scenario 4 need figure was set) is open with Brandon.

## 6. New findings

| ID | Sev. | Finding | Evidence | Shown / suspected | Suggested fix |
|---|---|---|---|---|---|
| F-1 | Medium | On a held build, the Summary's "Working values: pool strip split at m = 1 (not printed)" block (row 544 and below on the synthetic build) still shows Gp and Gm for the first median threshold and for each percentile target. The held median margin follows: Baseline Gp 0 + 50.90 and Gm 66.74 + 10.86 give -26.7, the figure the hold replaces. The block is outside the print area, so the PDF is clean, but it ships in the workbook. `test_27` skips the block: its labels do not match the test's `median|percentile` pattern. | Held build `22abbb67bb0d` (synthetic, scratchpad); `sw/workbook.py` `sw_pool_parts` (line 2432); `tests/test_27_fix_pass.py:48` | Shown | Apply `_held` to the held thresholds' Gp, Gm, Vp and Vm in `sw_pool_parts`, or leave those columns out under the hold; extend `test_27` to the block. Judgment call: the Ledger's "median sign" and "percentile sign" columns (`sw/workbook.py:1158`) let a user rebuild the margin with a SUMPRODUCT. That is a calculation, not a printed figure, so I would leave them. |
| F-2 | Low | When growth lowers a target's margin (e_hi < 0 with m > 0), the break-even is a ceiling, but it prints as a plain number in the same column as floors, and the note does not say so. | `sw/strip.py` `breakeven_m`; `test_24:112` (2.4, -2.0 gives 1.2) | Shown in code. Not seen on the synthetic build's PDF. For Richmond's targets the hi part sits at or above every percentile t, so e_hi > 0 is expected; and `m_q` is held for Richmond anyway. | Label a ceiling "at most m" or add a line to the note. |
| F-3 | Low | The break-even table's column B heading, "break-even pool multiplier", sits over an empty column. | PDF p. 15 | Shown | Drop the empty column or move the heading. |
| F-4 | Low | The pool strip and the contract ranges keep q = 0.5 percentile columns that repeat the median columns (R4-03 residual). The contract section prints about 6 pages. | PDF pp. 13, 14 and 22 to 27; `sw/contract.py:137` | Shown | Drop q = 0.5 from the strip as from the main block, or say why it stays. |
| F-5 | Low | Render cosmetics. See section 7. | PDFs | Shown | None needed for acceptance. |
| F-6 | Low | Documentation gaps: the R4-07 rule is missing from the methodology (line 553) and the spec; the R4-08 caveat is missing from F26. | Section 5 | Shown | Add the R4-07 rule and the R4-08 caveat to the methodology and spec, tagged with their R4 IDs. |

## 7. Rendered Summary PDFs (step 4)

Both files were reviewed page by page: `output/phase4/Summary_render.pdf` (27 pages) and `Summary_render_hold.pdf` (29 pages).

- **Regenerated by the suite:** the suite rewrote both today (Nov 20 13:28), and the new files are pixel-identical to the Nov 19 copies.
- **Headers:** no section is missing its header.
- **Readability:** every section reads at 75% or larger, except the narratives page (p. 20), which reads small but legible.

Defects found:

| Page(s) | Item |
|---|---|
| 17 | On the class-table continuation page, the section title and note are cut at the edge of column B. |
| 3, 16 to 19 | The lowest score band shows as "0" ("admits cut, 0"; the "lowest band admitted" column shows 0). |
| 21 | The client legend carries internal IDs (R4-06, R4-07, R4-08) and config key names. |
| 13, 14 | The pool growth-to-date row prints a bare "4" for the nearest grid row. |
| 4, 6, 7 | Text runs past the last column: "not used (entering_y1)", "approximate (fewer than 30 expected)", "change under half a student". |
| 10, 13, 14 | Adjacent headers collide: "mean ntr_y1 target)", "mean ntr_y1 ntr_y1 SD". |
| all | The grey fill on section titles covers column A only. |
| 22 to 27 | Contract rows are double-spaced unevenly. |

Held render (`Summary_render_hold.pdf`):

- Pages 2 and 3 (main block), 13 to 16 (pool strip), 17 (break-even: class column kept, `m_q` held) and 18 (class table, merged hold cells) read correctly.
- The hold text sits against neighbouring numbers with no padding.
- The held pool strip runs to 4 pages, against 2 unheld.

R4-03, R4-04 and R4-12 on the PDFs: see section 5.

## 8. Synthetic sentinel (step 5)

```
../../.venv/bin/python -m sw.build --config config/synthetic.yaml --data synthetic --seed 101 --scenarios config/scenarios_synthetic.yaml --out output/ --pdf --sentinel
```

- **Build id:** `6d46dbd8b55c`.
- **Files** (both in `prototypes/scenario_workbook/output/synthetic/2027/6d46dbd8b55c/`):
  - `workbook_sentinel.xlsx`
  - `workbook_sentinel_Summary.pdf`
- **RunLog:**
  - "sentinel: every formula cell holds -999"
  - LibreOffice acceptance version 26.8.3.1
  - not held
  - lists the uncommitted files
- **Matches Nov 19:** the build id equals the Nov 19 `workbook.xlsx` build, so the code has not changed since then.

**Desktop Excel parity (R4-15), Nov 20.** Jason opened the sentinel in Excel, recalculated it and saved it as `workbook_sentinel_excel_copy.xlsx` in the same folder. The comparison was run at Jason's request:

```
../../.venv/bin/python tests/compare_excel_saved.py output/synthetic/2027/6d46dbd8b55c/workbook_sentinel_excel_copy.xlsx
```

| Item | Result |
|---|---|
| Saved by | Microsoft Macintosh Excel 16.0300 |
| Formula cells compared | 61,830 over 11 sheets |
| Value mismatches | 0 |
| Cells still at -999 | 0 |
| Formula-text differences | 0 |
| Exit code | 0 |
| Report | `output/excel_check/6d46dbd8b55c.json` |

The report's `rounding_probe` is null. That is expected for a live build: the probe row is written only in reproduce builds (`sw/workbook.py:2920` to 2924). The probe result for desktop Excel stands from the Nov 18 reproduce sentinel `08c50a6fabaf`. openpyxl warned that it does not support the Conditional Formatting extension. The comparison reads values and formulas, so the warning does not affect it.

## 9. Not verified

- Windows Excel parity (R4-15). Desktop Excel for Mac passed (section 8).
- Desktop Excel on a held build or a reproduce build of this code. Only the live synthetic sentinel was compared.
- Excel recalculation of a held build by me. `test_27::test_hold_workbook_equals_python` covers it in LibreOffice.
- The e_hi < 0 break-even case (F-2) on Richmond data. I reasoned from Richmond's configured targets and did not run it.
- Whether the Ledger sign columns should count as part of the hold (F-1, judgment call).
- Richmond's live Scenario 4 build. I did not build it.

Client-facing work, including any Richmond workbook or Summary PDF from this build, needs human review before it is sent.
