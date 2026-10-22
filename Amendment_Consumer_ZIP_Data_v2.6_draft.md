# Amendment: ZIP-Level Consumer Data (P$YCLE / PRIZM) for Targeting and Aid Allocation

**Status:** **Adopted into `02_methodology_v2.6.md` on October 22, 2026; superseded by it. Kept for history; edit the methodology, not this file.** Five issues were resolved on adoption (see `CHANGELOG_v2.6.md`). Not separately audited.
**Owner:** Jason Cohen. **Date:** October 22, 2026.
**Supersedes:** O13 (consumer segments), the consumer-segment lines in methodology sections 2, 5, 7 and 9, and the "ZIP3 only" rule in the data request.

## 1. Decisions taken

| # | Decision | Effect |
|---|---|---|
| D1 | Consumer data is unblocked at **ZIP5** (never street address, never household). | Replaces "never above CBSA" for derived consumer fields only. ZIP5 itself is still never a grid dimension, target or dashboard field. |
| D2 | **Frankel licenses the data and runs the append** from client-supplied ZIP5. | Needs a license that allows it. See section 2, which is a build blocker. |
| D3 | The aid grid may use a **derived capacity tier**, gated. Raw segment codes stay blocked. | New allowed grid dimension; tests in section 5. |
| D4 | **Law follows the same rules as undergraduate**, with its own gates and evidence. | Law gets no exemption and no extra restriction. Cell-cap arithmetic in section 4.4 shows what this costs. |
| D5 | Racial and demographic guardrails are unchanged: race, ethnicity and gender are audit-only and never inputs, including to the construction of the tier. | Section 5. |

Product choice (ruled, not asked): **P$YCLE Premier is the primary source for the capacity tier**; PRIZM Premier is optional for outreach targeting. P$YCLE Premier is Claritas's financial-behavior segmentation: 60 segments in 12 lifestage groups, built partly on estimated household income-producing (liquid) assets, with property-value and technology enhancements. That is closer to capacity to pay than PRIZM's lifestyle and socioeconomic segmentation. A pre-registered bake-off (section 6) confirms the choice per engagement, against a free ACS/IRS baseline.

## 2. Blocking finding: the Claritas license as posted

I read Claritas's posted Information Services Agreement (July 23, 2024). Your contract may supersede it, and I have not seen your contract. As posted, the terms conflict with D2:

| Clause (posted terms) | What it says | Implication |
|---|---|---|
| 4 License grant | Internal use "in support of Licensee's marketing and promotional purposes." A third-party processor needs a Third Party Processor Agreement (TPPA). The consultant exemption excludes a consultant "acting on behalf of multiple clients." | Aid allocation is not marketing. Frankel serves multiple clients, so the exemption does not apply to us. |
| 6(c) | No use "to develop any application or service for list enhancement or data appending." | Appending ZIP data to client records as a service may be barred. |
| 6(b) | No distributing or sublicensing Licensed Materials "or derivatives" to third parties without written consent. | Returning tiers, scored files or policy grids that embed derived values needs consent. |
| 5 Output | Aggregated output may be shared only to market the licensee's own business. | Client deliverables are not covered. |
| 6(d) | No use for eligibility for employment, credit, healthcare, charity care or insurance; no use that "could result in disparate impact or treatment against any group"; no use "to assess consumer financial risk." | Not a clean fit for scholarships, but the disparate-impact language is broad and P$YCLE is a financial product. Needs explicit written carve-out. |
| Segmentation terms | No one-for-one ZIP-to-segment cross-reference or disclosure "unless aggregated to include not less than 3 segments." Exports only as appended to consumer records under a Directory license. | Use ZIP **distributions** (at least 3 segments), never a ZIP's single dominant segment. Never output ZIP-to-segment pairs. A Directory license may be needed. |

**Gate L1 (before any build that ingests licensed data):** a written agreement with Claritas that expressly permits (a) use for client enrollment and aid analytics, (b) appending to client student records by Frankel, (c) return of derived capacity tiers and scores to clients, (d) use in aid-allocation policy, with the disparate-impact and financial-risk language addressed, (e) retention for the engagement plus archival.

**Fallbacks if L1 fails or is slow:**
- **F1. Client-licensed.** The client licenses Claritas and runs the append; Frankel signs a TPPA. We receive derived fields and never ZIP5.
- **F2. Free-data tier.** ACS, IRS SOI and Scorecard indicators at ZIP/ZCTA level, which the spec already allows. The consumer module is license-agnostic (section 7), so the same gates and grid logic apply.
- **F3. Another vendor.** Experian Mosaic or similar, subject to its own terms. Not reviewed.

Build the module and the synthetic-world tests now; do not load licensed data until L1 is signed.

## 3. Open issues: rulings

| ID | Issue | Ruling | Status |
|---|---|---|---|
| O13 | Consumer segments | **Rewritten.** ZIP5-derived fields allowed for targeting, forecast baseline and gated grid use. Raw codes blocked. Gates in section 5. | Ruled |
| O20 | License scope for Frankel as licensee | Gate L1 and fallbacks F1 to F3. | **Needs Claritas** |
| O21 | P$YCLE vs PRIZM | P$YCLE for capacity, PRIZM optional for outreach. Per-engagement bake-off including the free baseline. One licensed product per engagement. | Ruled |
| O22 | ZIP5 re-identification risk | ZIP5 travels in a separate `zip_key` file, is used only by the append job, and is never in analysis tables. Deleted after append QA or at close. No street address, no names. | Ruled |
| O23 | Tier construction | A **deterministic published formula** on the ZIP distribution. No trained model, no segment codes. Section 4.1. | Ruled |
| O24 | Grid cell cap (cells at most admits per cohort ÷ 30) | Tier enters by **substitution**, not addition. Section 4.4. | Ruled |
| O25 | Law applicability | Same rules; own lift and proxy tests; address-definition rule; cell-cap consequences. Section 4.5. | Ruled |
| O26 | Proxy-test thresholds | **Minimal:** P1 (V below 0.3, already in v2.5) is the only gate. P2 to P4 are report-only. | Ruled (Oct 22) |
| O27 | FAFSA data use (HEA 483(a)(3)(E)) and FERPA | The tier uses no FAFSA data, so prospect-stage use does not touch FAFSA data. SAI is used only to validate the tier on admitted students inside the aid-administration engagement. | Ruled; counsel note |
| O28 | Claritas inputs | Request documentation of the asset-indicator inputs, including whether race or ethnicity is used, plus vintage and refresh cadence. | **Needs Claritas** |
| O29 | ZIP vs ZCTA | Claritas ZIP5 and Census ZCTA differ. Use the HUD USPS crosswalk for the free baseline and the race-composition audit. | Ruled |
| O30 | Vintage drift | Freeze one vintage per cycle. Score all historical cohorts with that same vintage. Test sensitivity to two vintages. | Ruled |
| O31 | Cost vs lift | Licensed data must beat the free baseline (gate G2), or it is not used. | Ruled |

## 4. Methodology text [v2.6]

### 4.1 The ZIP consumer index (section 2, Geography)

- **Input:** for each ZIP5, the household distribution across P$YCLE Premier segments (at least 3 segments; ZIPs with fewer are pooled to the parent ZIP3 for the index).
- **Segment score:** Claritas's own affluence ordering of segments (or its asset index if licensed). We do not substitute our judgment.
- **ZIP index:** household-weighted mean segment score, plus the share of households in the top affluence quintile.
- **Capacity tier:** three bands cut on the prior-three-cohort admit pool, frozen at cycle start, same rule as position bands. A tier needs at least 30 admits per cohort or it merges. Unmatched or non-ZIP addresses (PO box, military, international) get **Unknown**, never an imputed tier.
- **Address:** permanent address at application, ZIP5 only.
- **Never used:** segment codes, lifestage groups, ZIP5 as a feature, household identifiers.
- **Reported:** national percentile of the ZIP index alongside the tier.

### 4.2 Roles and gates by use (replaces section 9 consumer-segment criteria)

| Use | Allowed when |
|---|---|
| **Targeting and outreach** | L1 (or F1/F2); G1, P1, P4; alignment gate. Outputs are tier-level or ZIP lists without segment labels. |
| **Forecast baseline** (expected yield p\*, reference award r_c) | Above, plus G2 (lift) and G3 (calibration). One price slope is unchanged. |
| **Aid grid dimension** | Above, plus backtest gate G4, floors, the P2 to P4 reports at the alignment gate, and a counsel review of the license and proxy note before first use at any client. |
| **Price-sensitivity moderator** | Only through the section 4 discovery protocol and its three adoption gates. Not part of this amendment. |

### 4.3 Whitelist [v2.6] (section 5)

- **Allowed:** all v2.5 items, plus **consumer capacity tier** (derived from ZIP5).
- **Blocked:** race, ethnicity, gender, consumer-segment codes, lifestage codes, credit data, ZIP5 as a dimension or target, any household-level field.
- **Targeted objectives:** an enrollment target on the capacity tier requires alignment-gate acknowledgment and the proxy screen.

### 4.4 Grid mechanics under the cell cap

The default undergraduate grid is about 75 cells. A full extra dimension of three tiers would exceed the cap (admits per cohort ÷ 30). So tier enters by one of two pre-registered routes:

1. **Split the No-FAFSA need band** into three tiered cells (default; adds 2 cells).
2. **Substitute** for a weaker dimension (for example collapse residency to two levels) when backtest shows a gain and the cap allows.

The route is chosen by out-of-time backtest before the cycle, then frozen. Floors apply to every tier cell (Appendix C): highest-need and Pell-eligible at 100%, others at 75%.

### 4.5 Law profile

- Same gates; evidence assessed on the program's own cohorts, pooled across cohorts when below 300 admits per cohort.
- The tier cannot add a dimension to the law grid beyond the cap: with about 600 admits the cap is 20 cells, and five position bands times three tiers is 15. Substitution applies as in 4.4.
- Document the address: for JD applicants the permanent address may not be a family address. The bake-off reports lift by address type where the client supplies both.
- Expect weaker signal than undergraduate. The gates decide, not the expectation.

## 5. Guardrails and gates

**Purpose statement** (recorded at the alignment gate): the tier measures neighborhood-level capacity to pay and expected response to price. It is not a measure of, or substitute for, race, ethnicity or any protected trait. It is not constructed, adjusted or selected using race data.

**Construction rule:** the tier is never residualized, reweighted or tuned against race composition. Candidate definitions are pre-registered (P$YCLE index, PRIZM rank, free ACS income). If one fails P1, we merge tiers or drop to the free baseline; we do not "correct" it with race data.

**Posture:** these tests are a record, not a legal safe harbor. Passing P1 does not establish compliance, and the reports are not thresholds. Legal responsibility stays with the client and counsel review.

| Gate | Test | Threshold (proposed; audit to confirm) |
|---|---|---|
| G1 | Match rate on ZIP5 | At least 95% of students; unmatched are Unknown |
| G2 | Out-of-time AUC lift over the free ACS/IRS baseline, with bootstrap 90% lower bound | At least +0.01; lower bound above 0 |
| G3 | Calibration and drift | v2.5 calibration criteria; tier-distribution PSI at most 0.2 |
| G4 | Grid backtest | Tier grid beats the no-tier grid and the best fair heuristic (S4-13 margin) |
| P1 | Cramér's V, tier vs race and ethnicity (audit-only data), per cohort and pooled | Below 0.3. **The only proxy gate.** Carried over unchanged from v2.5 |

**Report-only (no pass or fail) [revised Oct 22]:** the following are computed by the equity audit and shown at the alignment gate. They never block a release; the client decides.

| Report | What it shows |
|---|---|
| P2 | Whether adding the tier raises how well race group can be predicted from the allowed attributes |
| P3 | Mean expected award and share of discretionary dollars by race group, tier policy vs no-tier policy |
| P4 | Correlation of the ZIP index with ACS race composition |

Audit-only data: student-level race from the client, and ZIP-level race composition from the ACS. Neither enters any feature set. A static test enforces it.

## 6. Pre-registered bake-off (per engagement)

Variants, all scored out of time on at least three cohorts: (A) baseline without geography; (B) A plus free ACS/IRS ZIP indicators; (C) B plus P$YCLE index; (D) B plus PRIZM index; (E) C and D. Outcomes: enrollment AUC and calibration; agreement with SAI on admitted students who filed (validation only); P1 as the gate, P2 to P4 as reports. The winner needs G2. If no licensed variant passes, use B and report that the licensed data did not earn its cost.

## 7. Technical build

**New module `pipeline/consumer.py`:**
- `load_zip_table(source, vintage)`: license-agnostic interface. A source is Claritas direct, client-supplied derived fields, or the free ACS/IRS table.
- `zip_index(distribution)`: section 4.1 formula; refuses a ZIP with fewer than 3 segments.
- `fit_tiers(admit_pool)` and `assign_tier(zip_index, cut_points)`: cut points frozen and versioned.
- `match_report()`: match rate, Unknown share, row counts, as an explicit QA rule.
- `proxy_audit()`: P1 to P4, writing to the equity audit.

**Config:** `config/consumer_zip.yaml` (product, vintage, tier count, thresholds G1 to G4, P1 to P4, merge rules).

**Schema:**
- `zip_key(student_key, zip5, address_type)`: restricted access, append job only, deletion log.
- `student_consumer(student_key, zip_index, zip_top_quintile_share, tier, match_flag, vintage)`: no ZIP5.
- `consumer_gate_status(engagement, use, gate, value, passed, date)`.

**Guardrail tests (extend `test_guardrails.py`):**
- ZIP5 and segment codes absent from every analysis and output table.
- The tier-construction function takes no race, ethnicity or gender argument.
- Tier is rejected as a grid dimension unless `consumer_gate_status` shows every required gate passed.
- Raw segment codes rejected as model features.
- No output pairs a ZIP with a segment; ZIP-level outputs aggregate at least 3 segments and at least 10 students.

**Synthetic world (W0, W0L):** add latent household resources by ZIP; a noisy ZIP index with signal strength ρ in {0.2, 0.5, 0.8}; ZIP race composition correlated with the latent at strength c in {0, 0.4, 0.7}. Monte Carlo additions: the pipeline recovers capacity at the expected rate; P1 fires when c is high; with c = 0.7 the tier does not enter the grid; a tier-grid never underperforms the best fair heuristic beyond the margin.

**Dashboard and delivery:** tier-level aggregates only; no ZIP5 maps; no segment labels. Batch-scoring files carry the score, not the tier, unless L1 permits.

**Sequencing against the plan of action:**
1. Now: build the pipeline first (Oct 22 decision). Claritas agreement (L1) and the documentation request (O28) wait for a firm client contract; licensed-data ingestion stays switched off until then. Counsel review of the license and proxy note is approved and runs before first grid use.
2. Step 3: add the ZIP contract to S2, the tier and gates to S4, grid mechanics to S5, proxy tests to S8, worlds to S9.
3. Step 4: build the module with the free ACS/IRS source first. It validates the architecture and sets the baseline the paid data must beat.
4. Richmond 2027 cycle: targeting use is plausible; grid use is unlikely this cycle, because G2 and G4 need at least three cohorts of backtest and L1 must clear first.

## 8. Data request amendment (replace in `04_data_request`)

**New file (Tier 1 optional add-on):**

| File | One row per | Fields |
|---|---|---|
| `zip_key` | Person | Hashed student key (same as other files); `zip5` (permanent address at application); `address_type` (permanent or current); blank if unknown |

**Replace in "How to send data safely":**
- "No full ZIP codes" becomes: "No street addresses. ZIP5 is sent only in the separate `zip_key` file."
- "Send ZIP3 and state, not full ZIP" becomes: "`students` keeps state and ZIP3. ZIP5 goes in `zip_key`, through your secure channel."

**Add to "What we do with the data":**
- ZIP5 is used only to attach neighborhood-level indices from a licensed third-party dataset. We then replace it with derived fields and delete `zip_key` within 30 days of append QA, or at engagement close.
- Indices are neighborhood-level. We do not receive or use household-level data, credit data or street addresses.
- Race, ethnicity and gender are never used to build or adjust these indices.
- A match report is returned to you.

**Add to the checklist:**
- [ ] Optional: `zip_key` (ZIP5), with written approval of the transfer under your data-use agreement
- [ ] Confirm which address field is the permanent address at application
- [ ] Signed acknowledgment of the consumer-data purpose statement (alignment gate)

**Add to `data_dictionary_v2.csv`:** `zip_key.student_key`, `zip_key.zip5`, `zip_key.address_type` (all text; zip5 required only when the add-on is elected). Update `students.region_code` note: "ZIP3 retained; ZIP5 only in zip_key."

## 9. Documents to bring in line

| Document | Change |
|---|---|
| `02_methodology_v2.5.md` | Sections 2, 5, 7, 9, 10 and the not-planned table ("Consumer-segment codes in the aid grid") per this amendment; O13 row |
| `01_executive_read_v2.4.md` | Geography decision row; equity flags; open item 6 |
| `03_technical_roadmap_v2.4.md` | Open item 17; guardrail-test list; risk rows on geographic proxies |
| `04_data_request_v2.md` | Section 8 above |
| `EFA_FAO_Pitch_Deck.md` (privacy paragraph, line 113) | "No full ZIP codes" and the fairness claim need revision once L1 clears. "No consumer credit data" remains true |
| `CHANGELOG_v2.6.md` | New file |

## 10. Resolved and still open

**Resolved (Oct 22):**
1. Build the pipeline first; obtain the Claritas agreement when a firm client contract is in hand.
2. Counsel review of the license and proxy note before first grid use: yes.
3. Proxy tests minimal: P1 only as a gate; P2 to P4 report-only.

**Still open:** whether you hold any existing Claritas contract (L1 scope depends on it); Claritas documentation on inputs and race (O28), deferred with L1.
