# Review: Phase 2.1 fix pass (scenario-workbook prototype)

**Date:** November 17, 2026 | **Reviewer:** independent review (did not write the build) | **Owner:** Jason Cohen | **Scope:** the Phase 2.1 changes (uncommitted, on top of `2fd9760`) against `Review_Phase2_Build.md` P2-01 to P2-07 and spec v0.6.2 (Q-1 to Q-8f) | **Deliverable checked:** `output/phase2/workbook.xlsx` (build `d2fbfbc29bc4`)

Nothing was edited except this file; mutation and false-pass tests ran in scratch copies; nothing was committed.

## 1. Claims checked

| Builder's claim | Re-check | Result |
|---|---|---|
| Full suite 135 passed, 0 skipped | Re-run (Linux, Python 3.13, LibreOffice 24.2) | **Confirmed:** 135 passed, 100 s |
| Python mutants 91 of 91 caught; baseline and count checks fixed (P2-02) | Ran `tests/mutation_check.py` unmodified | **Confirmed:** baseline 104 passed and 31 skipped (135 collected); 91 of 91 caught by 51 different tests, at most 9 by any one |
| The review's 13 surviving Excel mutants are all caught | Re-applied the review's own 47 Excel mutants (still in my scratch copy) to the new code | **12 of 13 confirmed; 46 of 47 caught overall.** X09 still survives (P21-02). The builder rebuilt X09 as "in-state override ignored", which is caught. The review's X09 was "in-state override adds to the global shift", and the edge scenarios set the in-state override with a global shift of 0, so adding and replacing give the same result. The review table described the branch, not the mutation, so the builder's reading was reasonable |
| Edge workbook compared cell by cell | Read `tests/edge.py` and test 3 | **Confirmed:** every formula cell on every sheet, plus a test that the edge inputs still reach each branch |
| P2-03 ignored award entries | Delivered workbook | **Confirmed:** Levers shows 2 awards changed and 1 award entry ignored in "Smaller class, scaled awards"; it previously counted 3 changes |
| P2-04 shock label | Delivered workbook | **Confirmed:** no literal `{s}` anywhere |
| P2-05 number formats | Delivered workbook | **Confirmed:** History uses `0`, `#,##0` and `$#,##0`; no format left that ends in `.##` |
| P2-06 "rebuild needed" and the stale flag | Edited the workbook (first median threshold 166 to 167), recalculated in LibreOffice | **Confirmed:** Checks shows "rebuild needed: differs from its value at build (166)". The exempt-cells check is present |
| P2-07 blank segment | Same edited copy, one scenario's segment blanked | **Confirmed:** falls back to the configured segment; the trim-order and stale-probability checks stay OK, as they should |
| `compare_excel_saved.py` refuses the workbook as built | Ran it on the delivered workbook as built | **Not confirmed (P21-01)** |

## 2. Findings

| ID | Severity | Finding | Evidence (shown or suspected) | Location | Fix |
|---|---|---|---|---|---|
| P21-01 | Major | `compare_excel_saved.py` can certify values that no one recalculated. Its only guard is "the saved copy's sheets are byte-identical to a fresh build", which fails open | **Shown**, three ways, each reporting "OK: every formula cell matches Python" (exit 0): (a) **the delivered workbook as built**, because a build here differs from the Mac build in the Levers conditional-format order and in the last digit of some floats, so the byte check never fires outside the build environment; (b) the workbook resaved by LibreOffice with recalculation off; (c) the same after I replaced a Ledger tuition formula with `=0`. The script prints only a note when the saving application is not Excel, and the builder's own comment says the application name cannot be trusted | `tests/compare_excel_saved.py` | Make the Excel check run on the sentinel build: every cached value is -999 (test 3 already builds this copy), and RunLog records that the cached values are sentinels. The script then requires a sentinel-built source and fails any cell still holding -999. Also compare each cell's formula text with the rebuild's (ignoring case, spacing and Excel's `_xlfn.` prefixes) and list the differences |
| P21-02 | Minor | The in-state yield-shift override can add to the global shift instead of replacing it in Excel, and no test fails | **Shown:** review mutant X09 survives tests 3, 8, 9 and 18 | `tests/edge.py` or `tests/test_08_levers.py` | Give one scenario a non-zero global shift together with the in-state override. For example, add `yield_shift_pts_in: -1` to the test 8 "Overrides" scenario, which already has a global shift of 1 |
| P21-03 | Minor | The build id hashes the inputs and `requirements.lock` but not the generator code (the builder's judgment call 5) | **Shown:** the Phase 2 and Phase 2.1 workbooks share build id `d2fbfbc29bc4` although their layout and formulas differ. RunLog's git line says "working tree has uncommitted changes" without saying which | `sw/build.py` | Include a hash of `sw/*.py` in the build id. Two workbooks then share an id only if they are the same file apart from the timestamp, and the comparison script's layout heuristic becomes a backup |

## 3. The builder's judgment calls

| # | Point | Verdict | Reason |
|---|---|---|---|
| 1 | Stale flag also fires when the goal changes or the segment loses its cells | **Accept; widen the spec text** | Either change makes the static exact probability wrong, so it should fire |
| 2 | "1 award entry ignored" (singular) | **Accept** | Grammar; the template should allow both forms |
| 3 | `budget_basis` value `total_aid` | **Accept; name it in the spec** | The spec names only `merit`; the default needs a name. OD-10 (Brandon) still decides which basis Richmond uses |
| 4 | "Rebuild needed" compares the resolved segment | **Accept** | Blank and explicitly named resolve to the same segment, so neither changes the trim order. Confirmed in the edited copy |
| 5 | Build id ignores code | **Change** | See P21-03 |
| 6 | Trim order fixed at build | **Already decided (Q-7)** | The rebuild check makes it safe |

## 4. Hygiene

| Check | Result |
|---|---|
| Yellow Arrows fixture | Scan re-run on your computer over all prototype files, including `tests/edge.py`: no distinctive fixture value or text. Coincidences: 12,500 in test 19 (a toy award, as before) and the edge award of $55,000, a round award level chosen between synthetic base-cycle and plan-year tuition |
| `efa_fao/`, spec and decision documents | Unchanged against HEAD; only `prototypes/` differs |
| Dependencies | None added |

## 5. Verdict

**Accept the Phase 2.1 fix pass after P21-01; P21-02 and P21-03 can follow.**

**For your Excel check now, before P21-01 is fixed:** open the sentinel copy, `prototypes/scenario_workbook/output/phase2/sentinel/synthetic/2027/d2fbfbc29bc4/workbook.xlsx`, not `output/phase2/workbook.xlsx`. It has the same build id and the same formulas, but every cached value is -999. Excel recalculates it when it opens (the file asks for a full calculation on load). Save As a copy, then run `tests/compare_excel_saved.py` on that copy. Any cell Excel did not recalculate still holds -999 and shows up as a mismatch, so the guard in P21-01 is not needed for this run. If every cell matches, the result is good evidence for the Phase 2 acceptance step.

**Not verified:** desktop Excel itself; LibreOffice 26.8 (I used 24.2); the builder's Excel-mode mutation run of 59 mutants (my own 47 cover the same ground); Phase 3 and 4 items.
