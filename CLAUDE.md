# EFA + FAO

Enrollment funnel analysis (EFA) and financial aid optimization (FAO) for higher-ed clients, built by Frankel (owner and sign-off: Jason Cohen). Current phase: advisory and specification. First client: University of Richmond School of Law (discovery call held October 22, 2026).

## File map

| Path | What |
|---|---|
| `02_methodology_v2.6.md` | The method (S4 statistics, S5 optimization, consumer ZIP layer in section 9 and Appendix E). Source of truth. v2.5 and v2.4 kept beside it |
| `01_executive_read_v2.6.md`, `03_technical_roadmap_v2.6.md` | Executive read; spec steps S1 to S11, architecture, decision log |
| `CHANGELOG_v2.5.md`, `CHANGELOG_v2.6.md` | v2.5: edits S4-1 to S5-10 and audit edits E1 to E14. v2.6: consumer ZIP adoption, O20 to O35 |
| `S4_S5_Rereview_v2.4.md` | Opus 5.5 re-review (errata block at top) |
| `Audit_S4_S5_Rereview_v2.4.md` | Fable 5.1 audit of the re-review. Edits E1 to E14 in its section 4 |
| `review_support_v2.4/`, `audit_support_v2.4/` | Analysis scripts. Paths point at `/tmp/work`; edit to rerun |
| `Verification_Report_Oct22.md` | Test and re-run results with the real solver; data-request law gaps |
| `Handoff_S1_Kickoff.md`, `Richmond_Call_Capture_Sheet.md` | S1 inputs |
| `efa_fao/` | The v2 build: `src/`, `config/`, `sql/`, `tests/`, `docs/` (v2 docs, data request), `outputs/` |
| `efa_fao/docs/data_request_v3/` | Data request v3 (draft): `spec/` is the source, `build_request.py` generates the law and undergraduate documents, Excel templates and dictionaries into `output/`; `GAP_LOG.md` has sources and judgment calls. The v2.1 request stays in `docs/04_data_request_v2.md` until S2 signs off |
| `Pitch and pricing decks/`, `*.pdf` | Client-facing materials; confirm which pitch copy is current |

## Tags and conventions

- Version tags: **[v2.5]** marks a change in a document; add the edit number where one applies, for example **[v2.5, E7]**. **[v2.6]** marks the consumer ZIP adoption.
- IDs: **R1 to R12** first review; **S4-n, S5-n** re-review edits; **F1 to F20** re-review findings; **A1 to A33** audit findings; **E1 to E14** audit edits; **O1 to O19** open issues; **W0 to W20** Monte Carlo worlds; **FR-n** functional requirements (S1); **S1 to S11** spec steps.
- Collision: methodology section 13 calls the audit's five tasks A1 to A5. Write "audit Task n" or "audit A<n>".
- Severity: Critical, High, Medium, Low. Confidence: low, medium, high. Separate what is shown from what is suspected.
- Where two designs are both defensible, label it a judgment call and say what would change the choice.

## Rules

- Synthetic and public data only. Never ask for or use real client data. Prior-engagement files are off limits until rights are confirmed.
- Closed decisions stay closed unless Jason reopens them: no third-party applicant-reported timing data; no per-student optimization (the policy grid and lookup replace it); no grid-tier price estimation (deferred, not specified).
- Protected attributes (race, ethnicity, gender) never enter a model, grid, or target. A test enforces it.
- No individual-level consumer credit data (scores, bureau matches); not planned. ZIP-level derived indexes, including P$YCLE, are not blocked by this rule. v2.6 (adopted October 22, 2026, not separately audited) governs the consumer ZIP layer: ZIP5 is used only by the append job and deleted within 30 days of append QA; ZIP3, state, the ZIP index and the capacity tier are retained; raw segment codes never enter a model, grid or output; the capacity tier enters the grid only through gates G1 to G4 and P1 (P1 is the only blocking proxy gate; P2 to P4 are report-only). Claritas license gate L1 and counsel review precede first grid use. The amendment file is superseded by `02_methodology_v2.6.md`.
- Student-level data never goes to Supabase or the hosted dashboard. Aggregates only, cells under 10 suppressed.
- No price level change without design-based evidence. A client with no anchor gets the documented status-quo grid, not an optimized grid.
- Do not modify `efa_fao/src/` while the spec phase runs.
- Report test failures; do not fix them unless asked.

## Commands

Run from `efa_fao/` with the project environment (`../.venv`, Python 3.12; create it with conda if missing).

```bash
PYTHONPATH=src ../.venv/bin/python -m efa_fao.synth.generate --out data/synthetic   # about 5 s
PYTHONPATH=src ../.venv/bin/python -m efa_fao.run_pipeline --boot 40       # about 90 s; writes outputs/
PYTHONPATH=src ../.venv/bin/python -m pytest tests/test_guardrails.py -q   # 7 tests; run after the pipeline
```

`data/synthetic/*.csv` and `outputs/` are git-ignored and regenerable. The guardrail tests read `outputs/`, so run the pipeline first.

## Decision log (coding)

Coding in this phase: none; advisory and specification only (Jason). The build starts after S3, S4, S5 and S9 are signed off. Until then, do not start implementing v2.6 in `efa_fao/src/`.

## Writing

Concise. No emojis. Avoid "genuinely", "honestly" and "straightforward". Tables for comparisons, short paragraphs otherwise. Cite the methodology section, finding ID or file for every number. Report what was not verified.
