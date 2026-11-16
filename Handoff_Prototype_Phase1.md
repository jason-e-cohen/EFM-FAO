# Handoff: scenario-workbook prototype, Phase 1 (fresh session)

**Date:** November 16, 2026 (replaces the November 13 version, which pointed to spec v0.5) | **From:** Jason Cohen | **Build brief:** `Prototype_Spec_Scenario_Workbook_v0.6.md` (self-contained; sections 0 to 15)

**Status:** the Phase 1 build has not started. Richmond's first award decisions are for the class entering in fall 2027, so Phase 1 should finish in early December (roadmap v2.8, section 5A).

## Starting prompt (paste into a new Claude Code session on Jason's Mac)

> You are building Phase 1 of the scenario-workbook prototype for the EFA + FAO project in this folder. Read `CLAUDE.md` first, then `Prototype_Spec_Scenario_Workbook_v0.6.md` in full. The spec is your brief; follow its rules in section 0. Build only Phase 1 (section 12): `sw/ledger.py`, `sw/risk.py`, `sw/response.py`, `sw/trim.py`, `sw/strip.py`, `sw/mc.py`, `sw/synth_cells.py`, `sw/labels.py`, `config/richmond.yaml`, `config/synthetic.yaml`, `config/shape_targets.yaml`, `requirements.lock`, `docs/shape_targets.md`, and tests 1, 2, 4, 5 and 11 to 17. Do not build the workbook generator or reproduce mode yet, and do not build anything the spec lists as deferred. Use a task list, work in `prototypes/scenario_workbook/`, and stop when Phase 1 acceptance is met. Then report back as section 14 of the spec describes, and wait for review.

## Read, in this order
1. `CLAUDE.md` (rules, the Nov 4 exceptions, the evaluator working rules, deferred features).
2. `Prototype_Spec_Scenario_Workbook_v0.6.md`: sections 2 to 5 and 10 to 12 matter most for Phase 1.
3. `02_methodology_v2.8.md` Appendix F (metric definitions) and section 5, Scenario evaluator.
4. `DECISIONS.md` (decisions not to reopen) and, only if a rule is unclear, `Audit_Session_B_Design_Report.md` (the finding IDs tagged in the spec).
5. `Richmond_YA_Scenario_Workbook_Assessment.md` sections 3, 4, 11 and 12 and `ya_workbook_support/analysis.py` (git-ignored; background only; never copy values).

## Decisions already made (do not reopen)
- Admit-rate levers are scenario inputs; yield is constant when admit rates move; the shrink path writes rates and is not an optimizer (D1, D14).
- **No guardrail, no "exceptional" or "anomalous" labels anywhere** (D2).
- Small cells are shown to Richmond's named roles, never suppressed (D3).
- **One priority segment per scenario** (Richmond: NY and PA within out-of-state, combined), part of the cell schema; one incentive scoped to the segment or all out-of-state; an optional segment application lift, default 0 (D9, D13, D17). The cell file carries no state.
- **Class target under a hard cap** (Richmond 140 this cycle), supported 100 to 140; ranges come from config, not code (D5).
- **Shrink path:** lowest score band first, then GPA; segment cells below the median threshold are trimmed after other cells below it (D14).
- **Pool strip** in place of tripwires; **two net-tuition lines** in place of the net-price block (D15, D16).
- **Base yield** by partial pooling (k = 20), re-centered at the latest award (D18). **Unscored students** are excluded from the median margins by default (D19).
- Labels are constants in `sw/labels.py`, exact text as spec section 4: "Response based on client-input" and the assumption, shock and segment-share labels.
- Names are generic (`score_*`, `segment`, `base_cycle`); no client value is a product default (spec rule 7).
- Deferred, no stubs: goal-seek, schedule, `Static_MC`, `MultiYear`, `Trajectory`, net-price yield response, dashboard.

## Environment
- Build on Jason's Mac with the repo `.venv` (Python 3.12). Install what is missing (`numpy`, `scipy`, `pandas`, `xlsxwriter`, `openpyxl`, `pyyaml`, `pytest`) and write `prototypes/scenario_workbook/requirements.lock` with `pip freeze`. Report what you added.
- LibreOffice (`soffice`) is needed from Phase 2; check it now and note the result. Phase 2 must use the forced-recalculation profile in spec test 3.
- Set `YA_FIXTURE_PATH` to `Richmond Law - 2027 Scenarios for Client.xlsx` in this folder; Phase 1 tests do not need it.
- `fixtures/` and `output/` are git-ignored. Do not commit; Jason commits.
- Do not modify `efa_fao/src/`, `efa_fao/config/` or any specification document. If the spec is wrong or ambiguous, say so in the report.

## Definition of done
- Tests 1, 2, 4, 5 and 11 to 17 pass (test 5: the asserted shape rows in at least 90% of 20 seeds; the reported rows listed with their pass shares).
- `docs/shape_targets.md` records the source and range of every shape parameter, including the segment share of out-of-state applications (a synthetic placeholder).
- Report: what was built, test results with skips and reasons, dependencies added, tolerances achieved (closed form against exact and simulation, including the segment probability and the median at rho 0.5), and anything ambiguous or wrong in the spec.
- Stop. Phase 2 starts after Jason reviews. Open items for Brandon do not block the build: the class target path, the exact tuition increase, and which discount rate the Dean means.

## Handling
Frankel-confidential and client-confidential material: keep the fixture and anything derived from it local; nothing goes outside Frankel without Jason's review.
