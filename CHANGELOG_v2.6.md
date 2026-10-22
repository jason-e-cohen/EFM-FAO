# v2.6 Change Log

**Base:** `02_methodology_v2.5.md` (kept unchanged beside v2.6). Changes are tagged **[v2.6]** in `02_methodology_v2.6.md`.
**Source:** `Amendment_Consumer_ZIP_Data_v2.6_draft.md`, adopted by Jason on October 22, 2026, with five issues resolved.
**Status:** Not separately audited. Thresholds G1 to G4 are untested proposals. Counsel review and Claritas license gate L1 precede first grid use. Pending sign-off.

## Decisions on adoption (Jason, October 22, 2026)

| # | Issue | Resolution | Where |
|---|---|---|---|
| 1 | P4 inconsistency (amendment section 4.2 vs section 5) | P4 is report-only everywhere; no test treats it as pass or fail | 9; E.2 (O32) |
| 2 | Which proxy checks block | P1 (Cramer's V below 0.3) is the only blocking proxy gate. P2 to P4 are reports, assessed with counsel | 9 (O32) |
| 3 | G2 power at law size | Test kept; failing to power it is not a pass; default is no tier in the law grid; measured in W21L | 5, 9, 10 (O35, open) |
| 4 | "No consumer credit data of any kind" | Narrowed to individual-level credit data (scores, bureau matches), which stays out of scope and is not planned. ZIP-level derived indexes, including P$YCLE, are not blocked | 9, 11 (O33) |
| 5 | ZIP granularity | ZIP5 append, ZIP3 stored. ZIP5 is transient (append job only, deleted within 30 days of append QA). Retained: state, ZIP3, ZIP index, tier, match flag, vintage | 2, 3, 9, E.2 |
| 6 | Tiers per admit | Two tiers fixed per program (law default 2, undergraduate default 3), with a 30-admit-per-cohort merge rule. Per-admit tier choice is rejected; Unknown is never imputed | 2, 5 (O34) |

## Edits applied

| Section | Change |
|---|---|
| Status, version history, 1 | v2.6 status line; consumer ZIP layer in scope |
| 2 | New "ZIP consumer index and capacity tier": deterministic ZIP index, tier count and cut points, Unknown handling, retention, vintage freeze, law notes |
| 3 | Consumer fields; `zip_key` as optional Tier 1 add-on |
| 4 | Forecast baseline and moderator candidates may use the tier |
| 5 | New "Consumer capacity tier in the grid": three routes, cell arithmetic, why fixed tiers, whitelist update (tier allowed; segment and lifestage codes, individual credit, ZIP5/ZIP3 dimensions, household fields blocked) |
| 7 | Batch-scoring files carry the score, not the tier, unless L1 permits |
| 9 | Credit-data bullet narrowed; new "Consumer data: purpose, gates and guardrails" (purpose statement, construction rule, gates by use, G1 to G4, P1, report-only P2 to P4, FAFSA/FERPA, alignment-gate packet) |
| 10 | New "Consumer bake-off" (variants A to E); worlds W21 and W21L |
| 11 | Consumer rows replaced |
| 12 | Four new limitations |
| Appendix C | Floor row covers capacity-tier cells |
| Appendix E (new) | E.1 Claritas clause table, gate L1, fallbacks F1 to F3; E.2 technical build and guardrail tests; E.3 data-request language for `zip_key` |
| 13 | O13 rewritten; O20 to O35 added |
| 14 | Five closed-decision rows |

## Companion documents

- `01_executive_read_v2.6.md`: status line, credit-data line, geography row, four decision rows, open item 6.
- `03_technical_roadmap_v2.6.md`: S2, S3, S4, S5, S8 and S9 rows; guardrail-test row; open item 17; risk rows; review log entry.
- `CLAUDE.md`: file map and the consumer-data rule.
- `Amendment_Consumer_ZIP_Data_v2.6_draft.md`: marked adopted and superseded.
- `Handoff_S1_Kickoff.md`, `Plan_of_Action_post_v2.4_Review.md`: brought to v2.6.

## Added after adoption

- New spec step **S2b, data request v3** (roadmap table; Plan of Action Step 3b, D1 to D6). Draft built in `efa_fao/docs/data_request_v3/`: one spec, law and undergraduate documents, Excel templates, dictionaries, `GAP_LOG.md`, spec tests. Sources: v2.1 request, Jason's reference request, the CDS 2025-26 template, methodology v2.6. 04 is unchanged; promote v3 after S2 sign-off.

## Not done, flagged for Jason

- **No audit of the consumer layer.** A scoped audit (Plan of Action, C2) is advised before S4 and S5 sign-off.
- **Pitch deck:** the privacy paragraph ("No full ZIP codes"; "No consumer credit data") conflicts with v2.6 and needs revising. The folder copy may be stale; confirm the current copy.
- **Data request** (`efa_fao/docs/04_data_request_v2.md`): not updated; the `zip_key` language is in Appendix E.3. The law Tier 1 request is not written.
- **Open:** O35 (G2 power at law size), O28 (Claritas input documentation), L1 (Claritas agreement, deferred to a firm client contract).
- `efa_fao/src/` untouched.
