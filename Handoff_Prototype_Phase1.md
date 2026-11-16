# Handoff: scenario-workbook prototype, Phase 1 (fresh session)

**Date:** November 13, 2026 (replaces the November 5 version, which pointed to spec v0.4) | **From:** Jason Cohen's planning session | **Build brief:** `Prototype_Spec_Scenario_Workbook_v0.5.md` (self-contained; sections 0 to 15)

**Status:** the Phase 1 build has not started. The build is for this year; the market tier is part of the foundational model, not an add-on.

## Starting prompt (paste into the new session)

> You are building Phase 1 of the scenario-workbook prototype for the EFA + FAO project in this folder. Read `CLAUDE.md` first, then `Prototype_Spec_Scenario_Workbook_v0.5.md` in full. The spec is your brief; follow its rules in section 0. Build only Phase 1 (section 12): `sw/ledger.py`, `sw/risk.py`, `sw/response.py`, `sw/mc.py`, `sw/synth_cells.py`, `sw/trim.py`, `sw/tripwire.py`, the config files, the market tier (in, out_target, out_other) in the cell schema, ledger, response and generator, the target KPIs and levers, the class range 100 to 140 under `class_cap`, and tests 1, 2, 4, 5 (as edited) and 13 to 18. `netprice.py` and test 19 are Phase 1b: build them only if Phase 1 is accepted with time left, and say so in the report. Do not build the workbook generator, reproduce mode, schedule or goal-seek yet. Use a task list, work in `prototypes/scenario_workbook/`, and stop when Phase 1 acceptance is met. Then report back as the spec's section 14 and handoff note describe, and wait for review.

## Read, in this order
1. `CLAUDE.md` (rules, the two Nov 4 exceptions, the Nov 13 evaluator working rules, deferred features).
2. `Prototype_Spec_Scenario_Workbook_v0.5.md` (the brief). Sections 2 to 5 and 10 to 12 matter most for Phase 1, including the target-tier KPIs, the shrink path and the pool tripwires before section 4. `Spec_v0.5_Change_List_draft.md` explains why each change was made (read it only if a rule is unclear).
3. `Richmond_YA_Scenario_Workbook_Assessment.md` sections 3, 4, 11 and 12 (git-ignored; for background only; do not copy values from it).
4. `ya_workbook_support/analysis.py` (reference computations; do not copy fixture values into code).

## Decisions already made (do not reopen)
Admit-rate levers are inputs plus a goal-seek helper (later phase); yield is constant when admit rates move; **no guardrail, no "exceptional" or "anomalous" labels anywhere**; small cells are shown, never suppressed; **geography is one combined target-state tier (client-defined states, Richmond NY and PA; the cell file carries no state) with one incentive whose scope is the target tier or all out-of-state, plus an optional target-tier application lift that defaults to 0 (D13, D17)**; **class size is the target and `class_cap` is a hard cap (140 this cycle); the model supports 100 to 140 and rejects values outside 90 to 150 (D14)**; **the shrink path removes admits from the lowest LSAT band first, then GPA, with target-tier cells last, and is evaluator-only (D15)**; **pool tripwires are linear forms plus a bisection for the probability forms, and the year-to-date pool growth is an annotation only (D15)**; **net-price readouts are display-only arithmetic and never change yield (D16)**; tuition migration and yield shift are scenario levers; net-price yield response is deferred; every response-based output carries the exact text **"Response based on client-input"** (one constant).

## Environment notes
- The repo's `.venv` was built on macOS; a Linux session cannot execute it. Check `uname` and `.venv/bin/python --version` first. If it fails, create a separate environment (Python 3.12) outside the repo, install `numpy`, `scipy`, `pandas`, `xlsxwriter`, `openpyxl`, `pyyaml`, `pytest`, and report what you added.
- LibreOffice (`soffice`) is needed for test 3 in Phase 2, not for Phase 1. Check it now and note the result.
- The Yellow Arrows workbook is a git-ignored validation fixture. Set `YA_FIXTURE_PATH` to `Richmond Law - 2027 Scenarios for Client.xlsx` in this folder. Phase 1 tests do not need it except where the spec says so; never copy its values into code, config, tests or documentation.
- `fixtures/` and `output/` under the prototype are git-ignored. Do not commit anything; leave commits to Jason.
- Do not modify `efa_fao/src/`, `efa_fao/config/` or any specification document. If the spec is wrong or ambiguous, say so in the report; do not edit it.

## Definition of done for this handoff
- Tests 1, 2, 4, 5 and 13 to 18 pass (test 5 reports the share of 20 seeds meeting the shape targets on merged tiers; at least 90% required). Test 19 (Phase 1b) is reported separately.
- `docs/shape_targets.md` records the source and range of every shape parameter, including the target-tier share of out-of-state applications and the tier yield offset (client-input placeholders; Richmond's state-level counts are a data request, spec section 15 item 10).
- Report: what was built, test results (with any skip and the reason), dependencies added, anything ambiguous or wrong in the spec, and the closed-form-versus-simulation tolerances achieved (including the target-enrolled closed form and the pool-tripwire bisection).
- Stop. Phases 2 to 5 start after Jason reviews. Open items for Brandon (do not block the build): the 2027 class target and the glide path toward 100 to 115, and the exact tuition increase (5.5% is a planning placeholder; reproduce mode stays at 6.0%).

## Handling
Frankel-confidential and client-confidential material: keep the fixture and any output derived from it local; nothing goes outside Frankel without Jason's review.
