# Review: Phase 3 build (reproduce mode)

**Date:** November 18, 2026 | **Reviewer:** independent review | **Owner:** Jason Cohen | **Scope:** the builder's Phase 3 report (uncommitted working tree: `sw/reproduce.py`, test 6, Ledger reproduce branches), checked against spec v0.6.2 section 9, `CLAUDE.md` rules, and Richmond's public ABA 509 data | **Fixture:** read only, on your computer; nothing from it is reproduced here.

## 1. What I could check

| Builder's claim | Check | Result |
|---|---|---|
| The fixture counts unscored and blank-GPA enrollees on neither side of the margins (`excluded`), not `below` as spec section 9 says | `output/phase3/reproduce_report.json` and `detect_counting_rule` in `sw/reproduce.py` | **Confirmed:** all 18 count groups that contain unscored or blank-GPA students satisfy at + below + others = total. None fits `below`. The ABA 509 uses the same basis (LSAT percentiles over students with an LSAT) |
| With applications rounded after the pool multiplier, admits match in every cell except the unrecoverable ones | Report diagnostics | **Confirmed:** 67 of 68 cells for Baseline and Scenario 3; 66 of 68 for Scenarios 1, 2 and 4. Under the spec ledger it is 60 to 66 of 68. Every cell's enrolled equals round(admits x yield) |
| The 34 failures trace to three causes | Report failures and cell differences | **Consistent:** cell differences per scenario (1, 5, 5, 8 and 2 cells) line up with the rounding and unrecoverable-cell diagnostics |
| The fixture's data are real Richmond counts | Compared with the public 509 (2024, 2025) | Class size, unscored count, blank-GPA count and GPA quartiles agree; **LSAT bands below 161 do not** (finding R3-4) |
| Test results (184 passed, 34 failed, 3 skipped; mutants 108 of 108 and 71 of 71) | Not re-run | **Not verified.** The shell on your computer cannot install scipy (network allow list), and I kept the fixture off the cloud workspace |

## 2. Decisions the builder asked for

| Decision | Recommendation | Reason |
|---|---|---|
| Counting rule | **Switch reproduce mode to `excluded`.** Correct spec section 9 and D19 ("YA rule") | 18 of 18 groups show it, and it is also the ABA 509 basis, so live and reproduce modes then share one rule and O41's basis question closes |
| Application rounding | **Adopt for reproduce mode only** (a `reproduce.round_apps_after_pool: true` setting; spec section 3 unchanged for live) | Reproduce mode exists to match YA's arithmetic; live mode is ours. The Ledger needs the matching `ROUND` behind the mode switch, covered by test 3's reproduce workbook |
| The two unrecoverable cells | **Recover base applications from the scenario columns, or report them; never invent.** Where a scenario gives the cell a non-zero rate, `apps_base = admits_s / (rate_s x pool x lift)`. Load it only if every scenario that uses the cell implies the same value (after the file's rounding). Otherwise mark the cell "not reproducible from the file" and exclude it from the criteria, with the count shown | The file must hold these applications implicitly, because YA admits students there. The History sheet should show unknown applications as blank ("not in file"), not 0; the 38 history cell-cohorts loaded as 0 read as zero applicants |
| Ledger rounding at 15 significant digits | **Keep provisionally; verify in desktop Excel** | It makes Python match LibreOffice, but desktop Excel is the target. Add a reproduce sentinel build to `compare_excel_saved.py` and one deliberate test cell at x.4999999999999996. If Excel differs from LibreOffice, follow Excel. Accept the `labels.xl` text fix (round half away from zero, as `TEXT` does) |

The spec corrections the builder listed (section 9 narrative columns; Baseline taken from the fixture; pool multiplier from scenario descriptions; need rounded per enrollee in reproduce mode; no class-size table in reproduce builds) are all **accepted as spec text**.

## 3. Findings

| ID | Severity | Finding | Evidence | Fix |
|---|---|---|---|---|
| R3-1 | Major (process) | Phase 3 acceptance can be met now under "mismatches reported with causes" (spec section 12), but the three causes are fixable and the evidence says the scenarios will then match | Diagnostics above | Apply the three decisions, re-run, and accept on the criteria themselves. Scenario 4 first (BM-7) |
| R3-2 | Major (rule) | BM-7's "first Richmond deliverable is S4's class-size table and pool strip" collides with `CLAUDE.md`: the fixture and anything reproducing its cell values stay out of client deliverables. A reproduce build has no class-size table, and a live build carrying S4's award matrix reproduces fixture cell values | `CLAUDE.md` rules; builder's spec point 7 | **Decided (Jason, Nov 18):** exception recorded in `DECISIONS.md` and `CLAUDE.md`. S4's levers may go into a live build on Richmond's cell data, returned to Richmond's named roles only. The S4 scenario file is generated at run time into a git-ignored path. Scenarios 1 to 3 are not covered |
| R3-3 | Minor | `compare_excel_saved.py` handles live builds only, so the reproduce workbook's Excel behavior, including the 15-digit rounding call, is unmeasured | Builder's "not verified" | Extend the script to reproduce sentinel builds |
| R3-4 | High (for BM-1; reproduce unaffected) | The fixture's LSAT bands below 161 disagree with the published 509 in both history years. More than a quarter of LSAT-holding enrollees sit below 158 against the 509's 25th percentile of 158 (2024) and 159 (2025), and the 2024 counts put the median below 161 against 164. Class size, unscored and blank-GPA counts, GPA quartiles, the LSAT 75th percentile and the 2025 median all agree | Public 509 compilations (`aba-509-saas/data`) against fixture cohort counts, computed on your computer | Reproduce mode is unaffected: it matches YA's own count rows. But percentile and median figures computed on cell data with this basis will not match what Richmond reports to the ABA. See `Review_Phase2_2_Plan.md`, addendum (task 10: 509 reconciliation block; data request: highest LSAT; OD-14) |
| R3-5 | Minor | The mutation runs use `--deselect` for the pass-criterion tests. That is fine while those tests fail, but it should not become the default | Builder's report | Remove the deselect once the scenarios match |

## 4. Sequencing

Finish Phase 3 with the three decisions, re-run, and commit. Then run Phase 2.2 from that commit, as recommended in `Review_Phase2_2_Plan.md` section 5. Phase 2.2 should keep the `median_thresholds` alias, which `sw/reproduce.py` reads.

**Not verified:** the builder's test and mutation counts (not re-run, as above); desktop Excel on a reproduce workbook; the YA grid's LSAT basis.
