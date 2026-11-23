# EFA + FAO

Enrollment funnel analysis (EFA) and financial aid optimization (FAO) for higher-ed clients, built by Frankel (owner and sign-off: Jason Cohen). Current phase: specification complete for the scenario-workbook prototype (spec v0.6, Nov 16, 2026); Phase 1 build next. Richmond's first award decisions are for the class entering fall 2027; the workbook's Must list lands by February 2027 (roadmap v2.8 section 5A). First client: University of Richmond School of Law (discovery call held October 22, 2026).

## File map

| Path | What |
|---|---|
| `02_methodology_v2.8.md` | The method (S4 statistics, S5 optimization and scenario evaluator, consumer ZIP layer, small-cell disclosure in section 9, metric definitions in Appendix F). Source of truth. Earlier versions are in `_superseded/` |
| `Prototype_Spec_Scenario_Workbook_v0.6.md`, `Handoff_Prototype_Phase1.md` | Spec for Claude Code: Python-generated, formula-driven scenario workbook prototype; handoff for the Phase 1 build session. Earlier spec versions are in `_superseded/` |
| `DECISIONS.md` | Decision log: every decision by date with its IDs, closed decisions, deferred features, open decisions. Replaces the change lists and changelogs (now in `_superseded/`) |
| `Reviews, Audits, and Specs/S1_Requirements_and_User_Stories.md` | S1 functional requirements v1.3 (edits in place, tagged [v2.7], [v1.3, Bn-m]) |
| `01_executive_read_v2.8.md`, `03_technical_roadmap_v2.8.md` | Executive read; spec steps S1 to S11, architecture, Richmond critical path (5A), annual cycle (5B), reproducibility (5C), decision log |
| `Reviews, Audits, and Specs/Audit_Session_B_Design_Report.md`, `Reviews, Audits, and Specs/Audit_Session_A_Report.md` | Nov 16 audits. Session B finding IDs (B1-n to B7) are the change IDs for v2.8 and spec v0.6. Session A holds the Richmond email-figure audit (contains client-confidential figures) |
| `Reviews, Audits, and Specs/S4_S5_Rereview_v2.4.md`, `Reviews, Audits, and Specs/Audit_S4_S5_Rereview_v2.4.md`, `Reviews, Audits, and Specs/Audit_S1_Requirements_v1.0.md` | Earlier reviews (E1 to E14 are in the S4/S5 audit, section 4) |
| `review_support_v2.4/`, `audit_support_v2.4/`, `review_support_v0.5/` | Analysis and check scripts. v2.4 paths point at `/tmp/work`; edit to rerun |
| `Reviews, Audits, and Specs/Verification_Report_Oct22.md` | Test and re-run results with the real solver; data-request law gaps |
| `Reviews, Audits, and Specs/Handoff_S1_Kickoff.md`, `Reviews, Audits, and Specs/Richmond_Call_Capture_Sheet.md` | S1 inputs |
| `Reviews, Audits, and Specs/Richmond_YA_Scenario_Workbook_Assessment.md`, `ya_workbook_support/` | Reverse-engineering of the Yellow Arrows scenario workbook (git-ignored; confidential) |
| `guides/` | `Guide_Quickstart_and_HowTo.md` (setup, first build, new client, next cycle, delivery checklist) and `Methods_Reference.md` (equations, primary and derived metrics, tests, assumption register) for a new analyst or an auditor. Refresh at each accepted phase |
| `efa_fao/` | The v2 build: `src/`, `config/`, `sql/`, `tests/`, `docs/` (v2 docs, data request), `outputs/` |
| `efa_fao/docs/data_request_v3/` | Data request v3 (draft): `spec/` is the source, `build_request.py` generates the law and undergraduate documents, Excel templates and dictionaries into `output/`; `GAP_LOG.md` has sources and judgment calls. The v2.1 request stays in `docs/04_data_request_v2.md` until S2 signs off |
| `Pitch and pricing decks/`, `*.pdf` | Client-facing materials; confirm which pitch copy is current |

## Tags and conventions

- Version tags: **[v2.5]** marks a change in a document; add the edit number where one applies, for example **[v2.5, E7]**. **[v2.6]** marks the consumer ZIP adoption. **[v2.7]** marks the Richmond scenario-workbook decisions (tags and file map: V27-43); add the change ID where one applies, for example **[v2.7, V27-01]**. The Nov 13 addendum (target-state tier, class range and cap, shrink path, pool tripwires, net-price readouts, tuition placeholder, data-request additions) is **[v2.7, V27A-01]** to **[v2.7, V27A-07]**, listed in `_superseded/CHANGELOG_v2.7.md`. **[v2.8]** (methodology, roadmap, executive read), **[v1.3]** (S1) and **[v0.6]** (spec) mark the Nov 16 Session B reconciliation; add the finding ID, for example **[v2.8, B3-1]**. Record new decisions in `DECISIONS.md`.
- IDs: **R1 to R12** first review; **S4-n, S5-n** re-review edits; **F1 to F20** re-review findings; **A1 to A33** audit findings; **E1 to E14** audit edits; **O1 to O19** open issues; **W0 to W20** Monte Carlo worlds; **FR-n** functional requirements (S1); **S1 to S11** spec steps.
- Collision: methodology section 13 calls the audit's five tasks A1 to A5. Write "audit Task n" or "audit A<n>".
- Severity: Critical, High, Medium, Low. Confidence: low, medium, high. Separate what is shown from what is suspected.
- Where two designs are both defensible, label it a judgment call and say what would change the choice.

## Rules

- Synthetic and public data only. Never ask for or use real client data. Prior-engagement files are off limits until rights are confirmed.
  - **Exception (Jason, Nov 4, 2026):** the Richmond-provided Yellow Arrows workbook (`Richmond Law - 2027 Scenarios for Client.xlsx`; Richmond gave it to Jason with permission to hold and work with it) may be used (a) as a validation fixture for the scenario ledger and (b) to refine the shape and definitions of synthetic worlds. For (b), carry over parameters and ranges only (rates, mixes, correlations, sparsity), never cell values or counts, and record each in `prototypes/scenario_workbook/docs/shape_targets.md`. The file and anything that reproduces its cell values stay out of git (see `.gitignore`), out of Supabase, and out of client deliverables.
  - **Exception (Jason, Nov 18, 2026; BM-7, R3-2):** Scenario 4's levers from that workbook (admit rates, awards, full-tuition flags, pool multiplier, specialty, need and tuition) may be entered in a live build on Richmond's own cell data, and that workbook may go to Richmond's named roles through the secure channel, because it is Richmond's own scenario returned to Richmond. The Scenario 4 scenario file is generated at run time into a git-ignored path and is never committed. The other limits stand: nothing from the fixture goes to git, Supabase, the dashboard, public or marketing material, or any other client's work, and Scenarios 1 to 3 are not covered unless Jason extends this.
- Closed decisions stay closed unless Jason reopens them: no third-party applicant-reported timing data; no per-student optimization (the policy grid and lookup replace it); no grid-tier price estimation (deferred, not specified).
- Protected attributes (race, ethnicity, gender) never enter a model, grid, or target. A test enforces it.
- No individual-level consumer credit data (scores, bureau matches); not planned. ZIP-level derived indexes, including P$YCLE, are not blocked by this rule. v2.6 (adopted October 22, 2026, not separately audited) governs the consumer ZIP layer: ZIP5 is used only by the append job and deleted within 30 days of append QA; ZIP3, state, the ZIP index and the capacity tier are retained; raw segment codes never enter a model, grid or output; the capacity tier enters the grid only through gates G1 to G4 and P1 (P1 is the only blocking proxy gate; P2 to P4 are report-only). Claritas license gate L1 and counsel review precede first grid use. The amendment file is superseded by `_superseded/02_methodology_v2.6.md`.
- Student-level data never goes to Supabase or the hosted dashboard. Aggregates only. Small-cell suppression is the per-client `small_cell_policy` (default: suppress cells under 10, with complementary suppression). Richmond: no suppression, for its named, authenticated roles (enrollment team, leadership, aid office); Cat and Richmond staff signed off (Jason, Nov 5, 2026). Record the sign-off in the SOW and the alignment-gate packet. **[v2.7, V27-40]** Files (the workbook, the policy lookup) follow the same policy and go only to the named roles through the secure channel; public and marketing material always uses the default rule (methodology section 9; Cat to confirm, O43). **[v2.8, B2-3]**
- The Yellow Arrows workbook never leaves Jason's Mac: not to a cloud workspace, a reviewer's environment or any other machine. A review that needs the fixture runs its tests through Claude Code on the Mac (Jason, Nov 19, 2026).
- Never mix one client's confidential information into another client's work, including pooled estimates or priors built from several clients. Calibrate from public data (ABA 509, IPEDS) instead. **[v2.8, B5-5]**
- No price level change without design-based evidence. A client with no anchor gets the documented status-quo grid, not an optimized grid. The scenario evaluator scores scenarios the client writes with a response based on client-input and recommends nothing; every output that depends on the response carries the label "Response based on client-input". **[v2.7, V27-41]**
- Do not modify `efa_fao/src/` while the spec phase runs.
  - **Exception (Jason, Nov 4, 2026):** the scenario-workbook prototype is built under `prototypes/scenario_workbook/`, which is outside `efa_fao/src/`. Spec: `Prototype_Spec_Scenario_Workbook_v0.6.md`.
- Report test failures; do not fix them unless asked.

## Commands

Run from `efa_fao/` with the project environment (`../.venv`, Python 3.12; create it with conda if missing).

```bash
PYTHONPATH=src ../.venv/bin/python -m efa_fao.synth.generate --out data/synthetic   # about 5 s
PYTHONPATH=src ../.venv/bin/python -m efa_fao.run_pipeline --boot 40       # about 90 s; writes outputs/
PYTHONPATH=src ../.venv/bin/python -m pytest tests/test_guardrails.py -q   # 7 tests today; becomes 8 when the v2.7 guardrail edits are implemented **[v2.7, V27-42]** (test 2 checks the small-cell policy, test 5 drops its maximum-cut assertion, a step-size test is added); run after the pipeline
```

`data/synthetic/*.csv` and `outputs/` are git-ignored and regenerable. The guardrail tests read `outputs/`, so run the pipeline first.

The scenario-workbook prototype builds on Jason's Mac with the same `.venv` (macOS only) and pins its dependencies in `prototypes/scenario_workbook/requirements.lock`. Its Excel parity test forces LibreOffice to recalculate (spec v0.6 test 3). Do not put comments after `#` in command blocks meant for pasting into zsh.

## Deferred features (decided not now; do not build or spec as active scope)

- **Net-price yield response (Jason, Nov 5, 2026).** An optional switch so yield responds to net price (tuition minus award) instead of award dollars alone: `yield = y0 + (b/100) x (a - a0 - (T - T0)) / 1000`. With fixed-dollar awards, a tuition increase would act like an equal cut in aid. It assumes applicants react to sticker price as they do to aid, for which we have no evidence, so it would be offered only as a labeled bound. Today the independent yield shift (prototype spec D12) covers tuition effects the analyst wants to assume.
- USNWR planner feed (possible future law-product feature).
- Slate-based pool-growth pacing (later addition; pool growth is a manual input now).
- Goal-seek helper and schedule authoring layer; `Static_MC`; `MultiYear`, `Trajectory` and `ntr_horizon` in the evaluator (year 2) (Jason, Nov 16, 2026).
- Dashboard scenario and policy views: an add-on after the workbook's core computation is accepted (Jason, Nov 16, 2026).
- Geography below the single priority segment (per-state segments, MSAs, ZIP3); revisit after Richmond's state-level counts and about two cycles of data. In scope now: one combined target tier (default NY and PA) with one incentive aimed at it (Jason, Nov 13, 2026).
- Admit-rate dimension in the S5 optimizer (evaluator inputs and the shrink path only for now).
- Marginal-admit yield (yield changing with admit rate); waits for an estimate.

## Decision log (coding)

Coding in this phase: none in `efa_fao/src/`; advisory and specification only (Jason). **Exception (Nov 4, 2026):** the scenario-workbook prototype under `prototypes/scenario_workbook/`. The pipeline build starts after S3, S4, S5 and S9 are signed off; until then, do not start implementing v2.6 or v2.8 in `efa_fao/src/`. The mockup in `efa_fao/src/` is a parts bin: its optimizer is per-student and carries the removed guardrail, and its config cannot carry a law client (Session B, B5-6).

**Scenario evaluator working rules (Jason, Nov 13, revised Nov 16, 2026).** (1) The priority segment is part of the cell schema from the start, never an add-on; one segment per scenario, a client-defined set of cells within one residency (Richmond: NY and PA within out-of-state, combined). Names are generic (`segment`, `score_*`, `base_cycle`); no client value is a product default. (2) `class.cap` is a hard cap (Richmond 140 this cycle) and `class.target` is the target; the evaluator is supported and tested from 100 to 140, with a five-year path toward 100 to 115 to be confirmed with Brandon. (3) Shrink order: lowest score band first, then GPA; segment cells below the median threshold are trimmed after other cells below it; it writes admit rates and is not an optimizer dimension. (4) A pool strip replaces the tripwires; two net-tuition lines replace the net-price block; the net-price yield response stays deferred. (5) The Excel workbook ships first; the dashboard is an add-on reading the same ledger outputs. (6) Metric names and definitions follow methodology Appendix F (for example `ntr_y1`, `discount_entering_y1`). (7) Richmond 2027 tuition is $63,500, entered in dollars (`tuition_by_year_usd`; Brandon, Nov 17; Board approval February 2027); reproduce mode loads the fixture's tuition. The 5.5% placeholder is retired (Nov 18). (8) Client facts from Dean Rooksby's Nov 13 note stay confidential to Richmond.

## Writing

Concise. No emojis. Avoid "genuinely", "honestly" and "straightforward". Tables for comparisons, short paragraphs otherwise. Cite the methodology section, finding ID or file for every number. Report what was not verified.
