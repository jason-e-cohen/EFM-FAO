# Review: Phase 2 build of the scenario-workbook prototype

**Date:** November 17, 2026 | **Reviewer:** independent review (did not write the build) | **Owner:** Jason Cohen | **Scope:** Phase 2 (`sw/workbook.py`, `sw/narrative.py`, `sw/build.py`, `sw/contract.py`, `sw/lo.py`; tests 3, 8, 9, 10, 18) and the Phase 1.1 Python changes it carries, against `Prototype_Spec_Scenario_Workbook_v0.6.md` v0.6.1 and `DECISIONS.md` | **Build reviewed:** uncommitted working tree on Nov 17 (after commit `adc22e3`); deliverable `output/synthetic/2027/d2fbfbc29bc4/workbook.xlsx`

Nothing was edited except this file. Mutation tests ran in scratch copies. Nothing was committed.

## 1. Re-run

| Item | Builder reported | Re-run |
|---|---|---|
| Full suite | 123 passed, 0 skipped | 123 passed, 0 skipped, 74 s (Linux, Python 3.13, LibreOffice 24.2; you used LibreOffice 26.8 on the Mac) |
| Test 3 | 56,997 formula cells match; sentinel guard holds; two builds differ only in the RunLog timestamp | Pass. The delivered workbook has 56,997 formula cells |
| Tests 8, 9, 18 | Pass | Pass |
| Test 20 (mutation check) | 86 of 86 caught | **The recorded run is void (finding P2-02).** Corrected re-run: baseline 100 passed and 23 skipped; 86 of 86 caught, each by a test that checks the mutated formula |

## 2. What test 3 actually proves

**Shown:** the "Python value" each workbook formula is compared with comes from the reference functions (`sw/contract.py` `compute`, which calls `ledger`, `risk`, `strip`, `trim`, `response`). It is not a second implementation inside the generator, so test 3 compares the workbook with the reference.

To see whether the workbook tests catch a wrong Excel formula, 47 mutants were applied one at a time to the formula strings in `sw/workbook.py`. Each mutant workbook was rebuilt, recalculated in LibreOffice and run against tests 3, 8, 9 and 18. **34 caught, 13 survived.** Every survivor is a branch that neither test workbook (the five-scenario `scenarios_synthetic.yaml` and the test 8 workbook) ever reaches:

| Mutant | Branch the test workbooks never reach |
|---|---|
| X05, X06 | Yield at the floor or cap: the outer clip (after the shift) and the inner clip (response) can each be deleted. Test 8 deliberately avoids clipping. R-01 chose a single formula column so that Excel and Python "agree exactly, including where the floor or cap binds", and no workbook test shows that |
| X42 | Yield-strip clip count (it is 0 in every test workbook) |
| X01 | Award base capped at tuition for an unflagged cell whose lever award is above tuition |
| X09 | In-state yield-shift override (test 8 sets out-of-state and segment only) |
| X10 | `need_total` override on Levers |
| X23 | Segment goal rounded up (every goal is an integer) |
| X28 | Validity check when a child differs from its parent only in a `full_tuition` flag |
| X32, X34, X47 | Shrink path with `floor_rate` above 0 (removable enrollment, trimmed rate) and the "N not reachable" shortfall status |
| X36 | Segment pool at exactly 30 admits |
| X38 | Pool-strip median at rho below 1 (config rho is 1) |

The Python side of each branch is tested (test 19, and the mutation check). What is missing is a workbook built so that the Excel formulas take these branches.

## 3. Findings

| ID | Severity | Finding | Evidence (shown or suspected) | Location | Fix |
|---|---|---|---|---|---|
| P2-01 | Major | Excel-equals-Python holds only on the branches the two test workbooks reach. Thirteen Excel formula paths can be wrong without any test failing (section 2), including the clip behavior R-01 was adopted to guarantee | **Shown:** 13 of 47 Excel-formula mutants survive tests 3, 8, 9 and 18 | `tests/test_03_excel_equals_python.py`, `tests/conftest.py` | Add a third "edge" workbook to test 3, compared cell by cell like the main one. Config: `floor_rate` 0.2 with exempt cells, rho 0.5, `pooling_min_admits` set equal to one segment pool's admits. Scenarios: a shift large enough that some cells hit the cap and others the floor; an in-state override; a `need_total` override; a goal of 24.3; an unflagged award above tuition; a child that differs only in one `full_tuition` flag; class sizes in `what_if` low enough to produce a shortfall. Re-run the Excel mutants afterwards (the list is in section 2) |
| P2-02 | Minor | The mutation check's Phase 2 report is void. Its scratch copy omits `requirements.lock`, so `test_two_builds_differ_only_in_runlog` fails in every mutant run. The baseline (99 passed) was taken before that test was added during the run | **Shown:** in `output/mutation/report.json`, 61 of 86 mutants are "caught" only by that test. With the same harness here, the unmutated baseline fails. After copying the lock file, the baseline passes and 86 of 86 are caught by substantive tests, so the conclusion stands | `tests/mutation_check.py` `_copy_tree` | Copy `requirements.lock` (or everything except `output/`). Have the run fail if the baseline's test count differs from the mutant runs'. Warn when one test accounts for most catches |
| P2-03 | Minor | An award typed into a full-tuition cell is ignored (P1.1-1), but it is still counted and shown as a change | **Shown:** in "Smaller class, scaled awards", `in-170-hi` holds 40,000 with the flag set. Levers counts 3 awards changed from the parent and grey-fills the cell, and the narrative says "Awards changed in 3 cells". Only 2 take effect; the cell stays at $57,150 tuition. Only Checks shows the conflict | `sw/workbook.py` `w_levers` change counts; `sw/narrative.py` | Exclude conflict cells from "awards changed", and report them separately ("1 award entry ignored: full-tuition flag set"). Show a neutral marker beside the conflicting cell on Levers, where the analyst types |
| P2-04 | Minor | The shock label template prints literally as "Year-to-year variation assumed (s = {s})" | **Shown:** README B7 (your screenshot) and Summary B318 (labels block) | `sw/workbook.py` `w_readme`, `sw_labels` | Fill in `s` from the config, or write "s = the year-to-year SD on Inputs" |
| P2-05 | Minor | Data cells show a trailing decimal point in desktop Excel ("11.", "50,000.", "170.") | **Shown:** your History screenshot. The cause is the format `#,##0.##########` (format key `data`) on History, Response, Levers and the Ledger static columns | `sw/workbook.py` `_formats` | Use `#,##0` for counts, `$#,##0` for dollars, `0` for scores and flags, `0.0000` for rates |
| P2-06 | Minor | Values fixed at build go stale without notice when an input changes. The Trim order depends on the first median threshold, `protect_segment`, exempt cells and each scenario's active segment; the exact segment probability is static. Inputs labels the first two "build-time", but nothing flags a change. The builder's item 7 says Excel cannot re-sort with the allowed functions; it can, with a rank computed by `SUMPRODUCT` on a composite key, then `MATCH` on the rank | **Shown** by reading. The live rank is **suspected** feasible (not built here) | `sw/workbook.py` `w_trim`, `sw_segment`, `w_checks` | Prototype: add a Checks row comparing each build-time input, and each scenario's active segment, with its value at build ("rebuild needed"). Label the static exact probability as stale when the segment's expected enrollment differs from its build value. A live Trim order is optional |
| P2-07 | Minor | Two segment rules differ between Excel and the spec. A blank `segment` on Levers means "no active segment" in Excel, but spec OP-5 says it defaults to the only configured segment. And `bonus_scope: segment` with no segment cells plus a positive bonus, lift or goal is an error in Python but produces no Check in Excel | **Shown** by reading: Ledger header `IF(seg="","",seg)`, `in_seg` = 0 when blank; the Checks list has no such row | `sw/workbook.py` `_ledger_block`, `w_checks` | When exactly one segment is configured, the Excel default should be that segment. Add a Checks row for the scope error |

**Cosmetic, for the Phase 4 render review:** in the Summary PDF the "parent" row truncates "Out-of-state incentive", and "under 5%" is left-aligned among right-aligned percentages.

## 4. The builder's spec problems

| # | Point | Verdict | Reason |
|---|---|---|---|
| 1 | Range-name rule vs the table's short names | **Accept; decide in spec** | Make the rule names (`SUM_P_CLASS_OVER_CAP`, ...) canonical in the section 15 table. Drop the aliases unless something already reads them; nothing does yet, and one name per figure keeps the dashboard contract simple |
| 2 | `p_segment_goal`: the contract cites the exact value, but Excel computes the normal form | **Accept; decide in spec** | The workbook's named range is the live normal form. Add `p_segment_goal_exact` to the contract, from Python, for the policy document and dashboard (they read ledger outputs, not Excel). The static exact value in the workbook needs the staleness flag in P2-06 |
| 3 | `award_matrix` source | **Accept; decide in spec** | The resolved award (after the flag and incentive) is the right figure. Change the Source column to "Levers, `AWARD_MATRIX` block" |
| 4 | P1.1-1: what counts as "entered" | **Accept** | Flag set and award different from the inherited one. An entry equal to the inherited value changes nothing, so not listing it is harmless. See P2-03 for how the conflict is counted |
| 5 | P1.1-4: "award before incentive below plan tuition" | **Accept; change the spec text** | The spec's "cells without the flag" would include an unflagged cell whose typed award is capped at tuition, which is a full-tuition student. The builder's rule matches what the line describes |
| 6 | Narrative template: NTR range slot; Baseline changes line | **Accept; change the spec text** | Template: "First-year NTR {x}M (90% outcome range {lo}M to {hi}M)". Baseline: "Baseline: no parent scenario." |
| 7 | Trim order fixed at build | **Accept for the prototype, with P2-06** | A live order is possible with `SUMPRODUCT` and `MATCH`, so it is a choice, not a limit. A staleness check is the cheaper fix now |
| 8a | Mode switch left out | **Accept** | Phase 3 |
| 8b | Live mode refuses integer admits | **Accept** | Spec section 2 (integer in reproduce mode only). The Excel `IF(in_integer_admits=1, ROUND...)` branches are untested until Phase 3's test 6 |
| 8c | No `AND`, `OR`, `ROUNDUP` (comparison arithmetic instead) | **Accept** | Works in both programs. Adding `AND` and `OR` to the allowed list would be harmless if you prefer readability |
| 8d | New optional input for "bonus implied by a dollar pool" | **Accept; add to spec section 2** | Needed for the figure to exist |
| 8e | Budget check compares total aid | **Decide** | Judgment call (D7, budget figure unknown). Use total aid if Richmond's budget covers need and specialty, merit only if it is a scholarship budget. Ask Brandon which one the figure means |
| 8f | History reconciliation cannot run | **Accept; add before the live build** | Add an optional `merit_actual_by_cohort` to the config. Richmond's reported merit totals would feed it |

## 5. Rules and hygiene

| Check | Result |
|---|---|
| No Yellow Arrows fixture value in code, config, tests, docs or the delivered workbook | **Pass.** The same scan as in Phase 1 ran on your computer: 1,563 distinctive tokens and long strings from the fixture, searched across the 45 prototype files and every value in the delivered workbook. Two coincidental hits: 12,500 in test 19 (a toy award of 10,000 plus the $2,500 evidence tolerance) and 0.8125 in the workbook (13/16, a synthetic ratio) |
| `efa_fao/` and spec documents | Unchanged against HEAD; only `prototypes/` differs |
| Dependencies | No new packages; `requirements.lock` unchanged since Phase 1 |
| Workbook structure | No hidden sheets, rows or columns; every sheet protected without a password; `fullCalcOnLoad` set, so Excel recalculates on open; longest formula 3,359 characters (Excel's limit is 8,192); deepest nesting 9 levels (limit 64); 113 defined names |

## 6. Verdict

**Ready for your desktop Excel check after P2-01.** The workbook formulas match the Python reference on everything the test workbooks exercise, and the Phase 1.1 Python coverage holds once the mutation check runs correctly. Before acceptance:

1. Add the edge workbook (P2-01) and confirm that the 13 Excel mutants are caught.
2. **Desktop Excel parity (the spec's Phase 2 acceptance step, not verified here).** Open `workbook.xlsx` in Excel, let it recalculate, then use Save As to save a copy (Excel then stores its own computed values) and send it to me. I can compare every formula cell with Python at the test 3 tolerance, which turns "Jason opens the file" into a measured check.
3. Fix P2-02 to P2-07 and the spec decisions in section 4; none of them blocks step 2.

**Not verified:** desktop Excel on Mac or Windows; LibreOffice 26.8 (I used 24.2); the Phase 3 integer-admit branches; anything client-facing.
