# EFA + FAO

Enrollment funnel analysis (EFA) and financial aid optimization (FAO) for higher-ed clients, built by Frankel (owner and sign-off: Jason Cohen). Current phase: advisory and specification. First client: University of Richmond School of Law (discovery call held October 22, 2026).

## File map

| Path | What |
|---|---|
| `02_methodology_v2.7.md` | The method (S4 statistics, S5 optimization and scenario evaluator, consumer ZIP layer, small-cell disclosure in section 9). Source of truth. v2.6, v2.5 and v2.4 kept beside it |
| `S1_Requirements_and_User_Stories.md` | S1 functional requirements v1.1 (v2.7 edits in place, tagged) |
| `Change_List_v2.7_draft.md` | The 43 v2.7 changes (V27-01 to V27-43) and the A1 to A6 decisions, with Jason's answers |
| `Spec_v0.5_Change_List_draft.md` | The v0.5 prototype-spec changes (C1 to C29) and Jason's Nov 13 answers; applied in the v0.5 spec |
| `Handoff_Session_A_Tactical_Audit_Cleanup.md`, `Handoff_Session_B_Design_Audit.md` | Review briefs for fresh sessions. A (run first): email-figure audit, small-cell rule, bounded cleanup; output `Audit_Session_A_Report.md`. B: spec v0.5 review, metric definitions, statistical fitness, generality (clients, years, priorities), feasibility, simplification; output `Audit_Session_B_Design_Report.md` |
| `01_executive_read_v2.7.md`, `03_technical_roadmap_v2.7.md` | Executive read; spec steps S1 to S11, architecture, decision log (v2.6 copies kept beside them) |
| `CHANGELOG_v2.5.md`, `CHANGELOG_v2.6.md`, `CHANGELOG_v2.7.md` | v2.5: edits S4-1 to S5-10 and audit edits E1 to E14. v2.6: consumer ZIP adoption, O20 to O35. v2.7: Richmond scenario-workbook decisions, V27-01 to V27-43, O36 to O40 |
| `S4_S5_Rereview_v2.4.md` | Opus 5.5 re-review (errata block at top) |
| `Audit_S4_S5_Rereview_v2.4.md` | Fable 5.1 audit of the re-review. Edits E1 to E14 in its section 4 |
| `review_support_v2.4/`, `audit_support_v2.4/` | Analysis scripts. Paths point at `/tmp/work`; edit to rerun |
| `Verification_Report_Oct22.md` | Test and re-run results with the real solver; data-request law gaps |
| `Handoff_S1_Kickoff.md`, `Richmond_Call_Capture_Sheet.md` | S1 inputs |
| `Richmond_YA_Scenario_Workbook_Assessment.md`, `ya_workbook_support/` | Reverse-engineering of the Yellow Arrows scenario workbook (git-ignored; confidential) |
| `Prototype_Spec_Scenario_Workbook_v0.5.md`, `Handoff_Prototype_Phase1.md` | Spec for Claude Code: Python-generated, formula-driven scenario workbook prototype; handoff note for the Phase 1 build session. Earlier spec versions are in `_superseded/` |
| `efa_fao/` | The v2 build: `src/`, `config/`, `sql/`, `tests/`, `docs/` (v2 docs, data request), `outputs/` |
| `efa_fao/docs/data_request_v3/` | Data request v3 (draft): `spec/` is the source, `build_request.py` generates the law and undergraduate documents, Excel templates and dictionaries into `output/`; `GAP_LOG.md` has sources and judgment calls. The v2.1 request stays in `docs/04_data_request_v2.md` until S2 signs off |
| `Pitch and pricing decks/`, `*.pdf` | Client-facing materials; confirm which pitch copy is current |

## Tags and conventions

- Version tags: **[v2.5]** marks a change in a document; add the edit number where one applies, for example **[v2.5, E7]**. **[v2.6]** marks the consumer ZIP adoption. **[v2.7]** marks the Richmond scenario-workbook decisions (tags and file map: V27-43); add the change ID where one applies, for example **[v2.7, V27-01]**. The Nov 13 addendum (target-state tier, class range and cap, shrink path, pool tripwires, net-price readouts, tuition placeholder, data-request additions) is **[v2.7, V27A-01]** to **[v2.7, V27A-07]**, listed in `CHANGELOG_v2.7.md`.
- IDs: **R1 to R12** first review; **S4-n, S5-n** re-review edits; **F1 to F20** re-review findings; **A1 to A33** audit findings; **E1 to E14** audit edits; **O1 to O19** open issues; **W0 to W20** Monte Carlo worlds; **FR-n** functional requirements (S1); **S1 to S11** spec steps.
- Collision: methodology section 13 calls the audit's five tasks A1 to A5. Write "audit Task n" or "audit A<n>".
- Severity: Critical, High, Medium, Low. Confidence: low, medium, high. Separate what is shown from what is suspected.
- Where two designs are both defensible, label it a judgment call and say what would change the choice.

## Rules

- Synthetic and public data only. Never ask for or use real client data. Prior-engagement files are off limits until rights are confirmed.
  - **Exception (Jason, Nov 4, 2026):** the Richmond-provided Yellow Arrows workbook (`Richmond Law - 2027 Scenarios for Client.xlsx`; Richmond gave it to Jason with permission to hold and work with it) may be used (a) as a validation fixture for the scenario ledger and (b) to refine the shape and definitions of synthetic worlds. For (b), carry over parameters and ranges only (rates, mixes, correlations, sparsity), never cell values or counts, and record each in `prototypes/scenario_workbook/docs/shape_targets.md`. The file and anything that reproduces its cell values stay out of git (see `.gitignore`), out of Supabase, and out of client deliverables.
- Closed decisions stay closed unless Jason reopens them: no third-party applicant-reported timing data; no per-student optimization (the policy grid and lookup replace it); no grid-tier price estimation (deferred, not specified).
- Protected attributes (race, ethnicity, gender) never enter a model, grid, or target. A test enforces it.
- No individual-level consumer credit data (scores, bureau matches); not planned. ZIP-level derived indexes, including P$YCLE, are not blocked by this rule. v2.6 (adopted October 22, 2026, not separately audited) governs the consumer ZIP layer: ZIP5 is used only by the append job and deleted within 30 days of append QA; ZIP3, state, the ZIP index and the capacity tier are retained; raw segment codes never enter a model, grid or output; the capacity tier enters the grid only through gates G1 to G4 and P1 (P1 is the only blocking proxy gate; P2 to P4 are report-only). Claritas license gate L1 and counsel review precede first grid use. The amendment file is superseded by `02_methodology_v2.6.md`.
- Student-level data never goes to Supabase or the hosted dashboard. Aggregates only. Small-cell suppression is the per-client `small_cell_policy` (default: suppress cells under 10, with complementary suppression). Richmond: no suppression, for its named, authenticated roles (enrollment team, leadership, aid office); Cat and Richmond staff signed off (Jason, Nov 5, 2026). Record the sign-off in the SOW and the alignment-gate packet. **[v2.7, V27-40]**
- No price level change without design-based evidence. A client with no anchor gets the documented status-quo grid, not an optimized grid. The scenario evaluator scores scenarios the client writes with a response based on client-input and recommends nothing; every output that depends on the response carries the label "Response based on client-input". **[v2.7, V27-41]**
- Do not modify `efa_fao/src/` while the spec phase runs.
  - **Exception (Jason, Nov 4, 2026):** the scenario-workbook prototype is built under `prototypes/scenario_workbook/`, which is outside `efa_fao/src/`. Spec: `Prototype_Spec_Scenario_Workbook_v0.5.md`.
- Report test failures; do not fix them unless asked.

## Commands

Run from `efa_fao/` with the project environment (`../.venv`, Python 3.12; create it with conda if missing).

```bash
PYTHONPATH=src ../.venv/bin/python -m efa_fao.synth.generate --out data/synthetic   # about 5 s
PYTHONPATH=src ../.venv/bin/python -m efa_fao.run_pipeline --boot 40       # about 90 s; writes outputs/
PYTHONPATH=src ../.venv/bin/python -m pytest tests/test_guardrails.py -q   # 7 tests today; becomes 8 when the v2.7 guardrail edits are implemented **[v2.7, V27-42]** (test 2 checks the small-cell policy, test 5 drops its maximum-cut assertion, a step-size test is added); run after the pipeline
```

`data/synthetic/*.csv` and `outputs/` are git-ignored and regenerable. The guardrail tests read `outputs/`, so run the pipeline first.

## Deferred features (decided not now; do not build or spec as active scope)

- **Net-price yield response (Jason, Nov 5, 2026).** An optional switch so yield responds to net price (tuition minus award) instead of award dollars alone: `yield = y0 + (b/100) x (a - a0 - (T - T0)) / 1000`. With fixed-dollar awards, a tuition increase would act like an equal cut in aid. It assumes applicants react to sticker price as they do to aid, for which we have no evidence, so it would be offered only as a labeled bound. Today the independent yield shift (prototype spec D12) covers tuition effects the analyst wants to assume.
- USNWR planner feed (possible future law-product feature).
- Slate-based pool-growth pacing (later addition; pool growth is a manual input now).
- Geography below the single target tier (per-state tiers, MSAs, ZIP3); revisit after Richmond's state-level counts and about two cycles of data. In scope now: one combined target tier (default NY and PA) with one incentive aimed at it (Jason, Nov 13, 2026).
- Admit-rate dimension in the S5 optimizer (evaluator inputs and goal-seek only for now).
- Marginal-admit yield (yield changing with admit rate); waits for an estimate.

## Decision log (coding)

Coding in this phase: none in `efa_fao/src/`; advisory and specification only (Jason). **Exception (Nov 4, 2026):** the scenario-workbook prototype under `prototypes/scenario_workbook/`. The build starts after S3, S4, S5 and S9 are signed off. Until then, do not start implementing v2.6 in `efa_fao/src/`.

**Scenario evaluator working rules (Jason, Nov 13, 2026).** (1) The market tier (in-state, out-of-state target, out-of-state other) is part of the cell schema from the start, never an add-on; target states are client-defined (Richmond: NY, PA), one combined tier. (2) `class_cap` is a hard cap (140 this cycle) and `class_size` is the target; the evaluator is supported and tested from 100 to 140, with a five-year path toward 100 to 115 to be confirmed with Brandon. (3) Shrink order: lowest LSAT band first, then GPA, target-tier cells last; it writes admit rates and is not an optimizer dimension. (4) Net-price readouts are display-only; the net-price yield response stays deferred. (5) Richmond planning scenarios use a 5.5% tuition increase, unconfirmed, until Brandon supplies the figure; reproduce mode stays at 6.0%. (6) Client facts from Dean Rooksby's Nov 13 note stay confidential to Richmond.

## Writing

Concise. No emojis. Avoid "genuinely", "honestly" and "straightforward". Tables for comparisons, short paragraphs otherwise. Cite the methodology section, finding ID or file for every number. Report what was not verified.
