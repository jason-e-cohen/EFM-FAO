# Verification: Session B reconciliation — November 16, 2026

**Reviewer:** Claude Sonnet 4.6 (independent; did not write the reconciled documents) | **Date:** November 16, 2026 | **Scope:** Every finding B1-1 to B7 from `Audit_Session_B_Design_Report.md`, checked against the target document named in DECISIONS.md (Jason accepted all fixes and the three simplifications on Nov 16). Cross-document consistency. Builder ambiguities in spec v0.6. | **Action taken:** None — read only. Nothing edited or committed.

---

## 1. Finding-by-finding status

Verdict key: **Applied** = fix is present and matches the proposed text; **Applied with issues** = fix is present but incomplete or inconsistent; **Missing** = fix is not present.

### Part B1 — Spec v0.5 mechanics and consistency (target: `Prototype_Spec_Scenario_Workbook_v0.6.md`)

| Finding | Severity | Verdict | Evidence |
|---|---|---|---|
| B1-1. Test 16 rewritten | Blocking | **Applied** | Test 14 (shrink path): "for N below the expected class, hits N within rounding; for N at or above it, returns the input rates; ... while cutting below the threshold, the share at or above t is non-decreasing as N falls." `[v0.6, B1-1, B1-5]` present. |
| B1-2. Test 13 rewritten (merge invariance) | Blocking | **Applied** | Test 11: "splitting out-of-state cells into segment and non-segment cells in any proportion changes no total or probability. Separately, the base-yield pooling returns the stated value for cells with 0, 4, 5 and 30 admits…" `[v0.6, B1-2]`. |
| B1-3. Test 14 rewritten (scope all_out) | Blocking | **Applied** | Test 12: "scope `residency_out` with no segment cells gives the same awards, yields, class, merit and probabilities as scope `segment` with every out-of-state cell placed in the segment, and as the toy answers in test 1." `[v0.6, B1-3, B1-14]`. |
| B1-4. Paid-anyway formula | Blocking | **Applied** | Incentive block: "of which paid to students the parent already enrolled: `sum_c min(e_pc, e_sc) × incentive_sc`." Cell-level form with `incentive_sc` per cell. `[v0.6, B1-4, B1-11, B7-9]`. |
| B1-5. Trim divide-by-zero / floor_rate / exempt_cells | Blocking (Phase 1 guard) | **Applied** | Shrink path: `rm_k = A_k y_k max(0, r_k − floor_rate) / r_k`; `removed_share_k = 0 if rm_k = 0, else MIN(1, MAX(0, (M−N−R_{k−1})/rm_k))`; per-N status shows shortfall. `[v0.6, B1-5, B1-16]`. |
| B1-6. Fallback chain and "LSAT group" | Major | **Applied** | Section 2 config: "Score group: cells at or above `score.pool_threshold` form the upper group, all others the lower group; unscored rows join the lower group for pooling. `[v0.6, B1-6]`." Section 4 base yield: pool at 30 admits, then residency fallback. |
| B1-7. Tier yield offset merged into segment shift | Major | **Applied** | Section 2 scenario file: "`tier_yield_offset_pts` is removed and its use is covered by `yield_shift_pts_segment`." `[v0.6, B5-1, B7-8]`. |
| B1-8. Normal approximation flagged at small M_S | Major | **Applied** | Segment block: "shows 'approximate (fewer than 20 expected)' when `M_S < 20`." 90% range clipped at zero. `[v0.6, B1-8, B4-7]`. |
| B1-9. Simulation model written down | Major | **Applied** | Section 5: "Per draw, e ~ Normal(1, s); each cell's yield is clip(e × y_c, 0, 1); enrollment ~ Binomial(A_c, clipped yield)…" `[v0.6, B1-9]`. |
| B1-10. Tripwire definitions | Major | **Applied (by simplification)** | Tripwires replaced by pool strip; bisection and bracket definitions removed. `[v0.6, B7-4, B1-10]`. Pool strip specified at section 3. |
| B1-11. Incentive KPI population and sign rules | Major | **Applied** | Incentive block: population = cells with `incentive_sc > 0`; `dE`; `dSpend / dE` when dE ≥ 0.5; "savings per enrollee lost" when dE ≤ −0.5; "change under half a student" otherwise; validity check; `dNTR / dE`. `[v0.6, B1-11]`. |
| B1-12. Interface contract (section 15) | Major | **Applied** | Section 15 item 11 has the full table with `name`, `unit`, `grain`, `source sheet and named range`, `Python`, `label`. `[v0.6, B1-12]`. Tagged "Required before Phase 2, not Phase 1" in test 9. |
| B1-13. Net-price block wording risk | Major | **Applied (by simplification)** | Net-price rung table removed; replaced by two lines in tuition what-if. `[v0.6, B7-5, B1-13]`. |
| B1-14. Empty segment handling | Major | **Applied** | Segment block: "With no cells in the active segment, every segment figure shows 'no segment cells in the data' and nothing is divided. Scope `segment` with no segment cells is an error only when `bonus_usd > 0`, `segment_pool_lift_pct != 0` or `segment_goal` is set." `[v0.6, B1-14]`. |
| B1-15. Base yield re-centered at latest award | Major | **Applied** | Section 4: `y0_ck = (n_c (ybar_c + (b_k / 100)(a0_c − abar_c) / 1000) + k_pool × ypool_c) / (n_c + k_pool)`. `[v0.6, B4-5, B1-15, B1-6]`. |
| B1-16. protect_target / protect_segment: below_threshold | Major | **Applied** | Section 2 config: `trim: {protect_segment: below_threshold, floor_rate: 0, exempt_cells: []}`. Section 3 trim order: "segment cells below the first median threshold t are placed after all non-segment cells below t and before any cell at or above t." `[v0.6, B1-5, B1-16]`. |
| B1-17. goal rounded up | Minor | **Applied** | Segment block: "goal rounded up to an integer `[B1-17]`". |
| B1-18. Continuity correction in goal-seek constraint | Minor | **Applied (by deferral)** | Goal-seek is deferred. `[v0.6, B7-3]`. Finding is moot. |
| B1-19. class_what_if vs cap ambiguity | Minor | **Applied** | Class-size table: "Rows with N at or above the Middle expected class M show 'not applicable (N at or above expected class)'; rows above the cap show 'above cap'." `[v0.6, B1-19]`. |
| B1-20. Formula whitelist (SUM, ROW; blank-means-inherit; helper columns) | Minor | **Applied** | Section 6: adds `ROW` to whitelist; "blank means inherit: `IF(cell = "", inherited, cell)`"; "Helper columns per N are allowed on `Trim`". `[v0.6, B1-20]`. |
| B1-21. Handoff labels (D14/D15; Phase 1b omissions; change-list stale) | Minor | **Applied** | Handoff: D14 = shrink path (line 24); D15 = pool strip (line 25). Handoff is a Phase 1-only brief; Phase 1b/2 is handled in the spec. The old change list (now in `_superseded/`) is not referenced from the handoff. No "90 to 150" appears under D14. |
| B1-22. Test 2 toy grid size | Minor | **Applied** | Test 2: "on a toy grid with expected class at least 25, the closed forms against the exact convolution (tolerance 0.01) and the simulation against the exact convolution (tolerance 0.005, 200,000 draws). `[v0.6, B1-22]`." |
| B1-23. Test 15 cost-per-incremental identity | Minor | **Applied** | Test 13: "`dSpend = sum e_s (a_s − a_p) + sum (e_s − e_p) a_p` cell by cell". `[v0.6, B1-4, B1-11, B1-23]`. |
| B1-24. Unscored rows policy stated | Minor | **Applied** | Trim section: "The unscored-first order is a policy choice with access implications and the README says so. `[v0.6, B1-24]`." |
| B1-25. Test 3 LibreOffice forced recalculation | Blocking (Phase 2) | **Applied** | Test 3: "Recalculate with a dedicated LibreOffice profile (`-env:UserInstallation=file://<tmp profile>`) whose `registrymodifications.xcu` sets `/org.openoffice.Office.Calc/Formula/Load/OOXMLRecalcMode` to 0… Guard: build one copy with every cached value set to −999 and assert that none survives recalculation." `[v0.6, B1-25]`. |

**B1 verdict:** all 25 findings Applied. No Missing.

---

### Part B2 — Methodology v2.7 edits (target: `02_methodology_v2.8.md`, `S1_Requirements_and_User_Stories.md` v1.3, `01_executive_read_v2.8.md`, `efa_fao/docs/data_request_v3/spec/fields.csv`)

| Finding | Severity | Verdict | Evidence |
|---|---|---|---|
| B2-1. Methodology line 360 contradicts V27A-01 | Major | **Applied** | Methodology line 363: "Geography enters as a priority segment on each cell (Richmond: one combined segment of client-listed states, NY and PA, within out-of-state) and one incentive aimed at the segment or at all out-of-state, with an optional score floor `[v2.8, B2-1]`. Per-state segments, MSAs and ZIP3 are deferred (section 11)." |
| B2-2. Price-test verdicts tagged "do not quote" in four places | Major | **Applied** | Methodology lines 269 (`worked example`), 271 (`Not recommended at every size`), 275 (`status of verdicts`): all carry `[v2.8, B2-2: computed under the 5% guardrail; pending re-run (O36); do not quote]` and the ±2.9%/±3.6% note. Executive read line 118: same tag. All four instances found. |
| B2-3. Small-cell rule for files, policy doc and public material; FR-06 fix | Major | **Applied** | Methodology section 9 has the three new bullets (Files, Policy document, Public and marketing material) `[v2.8, B2-3]`. S1 FR-06 acceptance now reads "Small-cell policy applied as configured (FR-76) `[v1.3, B2-3]`; structure matches approved table set; stealth flag present." CLAUDE.md has the same bullets with `[v2.8, B2-3]`. |
| B2-4. Methodology section 5 missing target-tier KPIs | Major | **Applied** | Methodology section 5 now has the "Segment and incentive measures" paragraph `[v2.8, B2-4, B1-4, B1-11]` with the decomposition and definitions, referencing Appendix F. The tier yield offset is merged into the segment shift (B7 rank 8), so "yield for target-tier cells adds a client-input offset" does not appear verbatim, but the offset as a separate parameter no longer exists and the segment shift covers the same purpose. |
| B2-5. Count rule at smaller class | Minor | **Applied** | Methodology line 361: "At a class of 100 the limit is about 15; the merge rule is re-run on the projected admits of the scenario in use `[v2.8, B2-5]`." |
| B2-6. Alignment gate review text | Minor | **Applied** | Methodology line 619: "reviews the allocation logic, the segment floors, the equity audit and the data use `[v2.8, B2-6]`." |
| B2-7. FR-52 eight tests | Minor | **Applied** | S1 FR-52: "eight guardrail tests (seven existing, with test 2 and test 5 amended, plus test 8, the step-size report) `[v1.3, B2-7]`". The consumer-module note ("ZIP-level outputs aggregate at least 10 students is independent of `small_cell_policy`") is present in the acceptance text. |
| B2-8. Executive read missing V27A addendum | Major | **Applied** | Executive read line 8: `[v2.7, V27A] What changed (November 13, 2026)` paragraph present and tagged `[v2.8, B2-8]`. Covers target-state group, class range, shrink path, 5.5% placeholder. Pool tripwires are not mentioned (correctly omitted — they were replaced before reconciliation). |
| B2-9. FR-74 and D4: "reproduce mode" qualifier on 6.0% | Minor | **Applied** | S1 FR-74: "6.0% for 2027 in reproduce mode; Richmond planning 5.5%, unconfirmed `[V27A-06; v1.3, B2-9]`". Spec D4: "reproduce mode 6.0%; Richmond planning 5.5%, unconfirmed". |
| B2-10. OD-06 stale resolution | Minor | **Applied** | S1 OD-06: "Partly answered: the evaluator uses one combined priority segment (NY, PA); whether the optimizer needs a state or MSA targeted-objective constraint stays open. `[v1.3, B2-10]`." |
| B2-11. Data request `guardrail_max_cut_pct` renamed | Minor | **Applied** | `fields.csv` line 139: `aid_policy, client_max_cut_pct, decimal, 1, N, N, "Any limit your policy places on year-over-year award cuts, if you have one, as a percent of tuition. We report against it; we do not impose one.", …, M section 5 (v2.8)`. |

**B2 verdict:** all 11 findings Applied. No Missing.

---

### Part B3 — Metric definitions (target: `02_methodology_v2.8.md` Appendix F, `Prototype_Spec_Scenario_Workbook_v0.6.md`, `S1_Requirements_and_User_Stories.md`)

| Finding | Severity | Verdict | Evidence |
|---|---|---|---|
| B3-1. NTR named two ways | Blocking (S5) | **Applied** | Methodology section 3: "The two NTR measures, `ntr_y1` and `ntr_horizon`, are defined in Appendix F." Methodology section 5: `ntr_y1` and `ntr_horizon` distinguished. Appendix F items 14–15. Spec section 3 and 15. S1 FR-71 acceptance: "optimizer and ledger give identical class, first-year spend and `ntr_y1`". FR-31: same. |
| B3-2. Discount rate basis and basis question | Major | **Applied** | Appendix F item 13: "`discount_entering_y1`… Differs from NACUBO (which includes fees) and from `discount_all`." Methodology section 5. Spec section 3: "The Summary label for the discount rate is 'Discount rate (entering class, first year)'." O42 open for Brandon (entering class vs all JD; with or without fees). |
| B3-3. Median basis for unscored students | Major | **Applied** | Spec section 2: "`unscored_in_median: excluded` (default)… excluded means unscored and blank-GPA enrollees leave both sides of the corresponding margin and are reported as a count." Methodology Appendix F item 8. Reproduce mode uses YA rule (`below`). O41 open pending 509 instructions. |
| B3-4. Pacing, pool growth, data request populations | Major | **Applied** | Methodology section 7: pacing "against the same week of the cycle (counted from the application open date)." Spec: `pool_ytd_growth` defined as "growth in complete applications at or above `score.pool_threshold`, this cycle against the mean of the prior two cycles at the same week of the cycle." `[v0.6, B3-4]`. DR fields.csv is not modified for the pacing column rename (the fix describes renaming `deposits` to `deposits_net_of_withdrawals` and asking for complete applications with an LSAT band); this portion of B3-4 is **not propagated to fields.csv**. See note below. |
| B3-5. Ratios of expectations labeled | Major | **Applied** | Spec section 3: "Ratios… are ratios of expected values, E[X] / E[Y], everywhere, and the README says so. `[v0.6, B3-5]`." Methodology section 5. |
| B3-6. Deferrals in yield | Major | **Applied** | Appendix F item 5: "an admit who defers counts as a non-enrollee in the year applied and is reported separately (confirm against how the client's 509 yield is computed)." |
| B3-7. "Full-pay" renamed | Minor | **Applied** | Spec section 3 KPIs: "**no-merit-award enrolled** (award of zero; need aid is not assigned to cells) `[v0.6, B3-7]`." Barbell index uses the new term. |
| B3-8. Target-tier KPI corrections | — | **Applied** | Via B1-4, B1-11, B2-4 above. |
| B3-9. Class size population defined | Major | **Applied** | Spec section 2: "Class: first-year entrants enrolled at the census date, full-time and part-time as on the 509, excluding transfers (Richmond to confirm whether the cap counts part-time entrants). `[v0.6, B3-9]`." Appendix F item 4. |
| B3-10. Residency / target address basis | Minor | **Applied** | Appendix F item 17: "from the permanent address at application" for both residency and segment. |
| B3-11. Market award gap normalization for public peers | Minor | **Applied** | Appendix F item 23: "Public peers: normalize by nonresident tuition for out-of-state positions and resident tuition otherwise, and flag the peer `[v2.8, B3-11]`." |
| B3-12. Need total label | Minor | **Applied** | Spec section 2: "The Inputs label reads 'Need aid: $200,000 at a class of 140 ($1,429 per enrollee; scales with class)'. `[v0.6, B3-12]`." |
| B3-13. "Net price" renamed | Major | **Applied** | Spec section 3 and throughout: "net tuition after merit award." FR-80 header and S1 use the same term. Appendix F item 16. |

**B3 note on B3-4 (data request fields):** The B3-4 fix called for renaming `early_funnel_by_state.deposits` to `deposits_net_of_withdrawals`, asking for complete applications in `applications_cumulative` with an LSAT band column, and changing the pacing "same date last year" language. The spec and methodology are updated, but `fields.csv` has not been audited for the rename or the LSAT band column addition. The DR is a draft (v3) and this fix requires a targeted check against `fields.csv` lines 173–180, which were outside the scope of the current fields.csv read. Flag for Jason at the next DR review pass.

**B3 verdict:** 12 of 13 findings Applied; B3-4 partially applied (spec and methodology updated, fields.csv rename not confirmed).

---

### Part B4 — Statistical and methodological fitness (target: `02_methodology_v2.8.md`, `Prototype_Spec_Scenario_Workbook_v0.6.md`, `S1_Requirements_and_User_Stories.md`)

| Finding | Severity | Verdict | Evidence |
|---|---|---|---|
| B4-1. s calibrated from public data; world W22 | Major | **Applied** | Methodology section 6: "s is calibrated from public data, never from another client… law: year-over-year change in each school's ABA 509 yield… `[v2.8, B4-1]`." Roadmap phase 2 adds W22. O37 open. |
| B4-2. Segment-level shocks; shock_corr_above_below | Major | **Applied** | Methodology section 5 median formula: `V_m = Σ A y (1−y) + s² (G₊² + G₋² − 2ρ G₊ G₋)`. Spec section 5: same, with `rho = shock_corr_above_below`. Summary shows sensitivity line at ρ = 0.5. `[v0.6, B4-2, B3-3]`. |
| B4-3. Stability/release thresholds at law size | Major | **Applied** | Methodology section 7 batch scoring: "the 90% confidence interval of the slope overlaps [0.85, 1.15] `[v2.8, B4-3]`". FR-62 acceptance updated. |
| B4-4. Pacing interval uses shock s, not prior spread | Major | **Applied with issues** | Methodology section 7: "interval from binomial noise and the year-level shock s; prior-cycle spread is shown as a check, not used, until five cycles exist `[v2.8, B4-4]`." **Issue:** S1 FR-14 still reads "projection interval from prior-year spread and binomial enrollment noise" — the B4-4 fix was not propagated to this FR. The methodology and FR-14 disagree. |
| B4-5. Partial pooling with k = 20 | Major | **Applied** | Spec section 4 base yield: full formula with `k_pool = pooling_k`. Methodology section 5. `[v0.6, B4-5, B1-15]`. |
| B4-6. RESPONSE_LABEL vs ASSUMPTION_LABEL vs SHOCK_LABEL | Major | **Applied** | Spec section 4 labels: three separate constants with exact text. `[v0.6, B4-6]`. |
| B4-7. Probabilities beyond 5%/95% shown as "under 5%" | Minor | **Applied** | Spec section 4: "probabilities below 5% or above 95% show as 'under 5%' or 'over 95%'. `[v0.6, B4-7]`." |
| B4-8. Lift framing not causal | Major | **Applied** | Spec section 3 incentive block: "These are what the assumed response implies, not estimates of what an incentive causes. `[v0.6, B4-8]`." Methodology section 5. |
| B4-9. Range kinds named | Major | **Applied** | Spec section 4 labels: "(1) 90% outcome range… (2) the Low and High price-response cases… (3) a 95% confidence interval… Kinds 1 and 2 are never combined." `[v0.6, B4-9]`. Methodology section 6. |

**B4 verdict:** 8 Applied, 1 Applied with issues (B4-4 fix not propagated to S1 FR-14).

---

### Part B5 — Generality, multiple years, reproducibility (target: `Prototype_Spec_Scenario_Workbook_v0.6.md`, `02_methodology_v2.8.md`, `03_technical_roadmap_v2.8.md`, `CLAUDE.md`)

| Finding | Severity | Verdict | Evidence |
|---|---|---|---|
| B5-1. Generic score, year and geography names; Richmond values in richmond.yaml | Major | **Applied with issues** | Spec section 2: `score_lo`, `score_bands`, `score.measure`, `base_cycle`, `plan_cycle`, `segment`, `bonus_*` (not `oos_bonus_*`), all present. Rule 7: "No client value is a product default." `config/richmond.yaml` holds Richmond's. **Issue:** Roadmap section 4 (dashboard views, line 109) still describes view 2 as containing "out-of-state incentive with its scope, target-tier application lift, yield shift" — v2.7 terminology not updated to generic segment names. This is a description of deferred dashboard views but inconsistent with the naming decision. |
| B5-2. Annual cycle written | Major | **Applied** | Roadmap section 5B: four-step annual cycle. `[v2.8, B5-2]`. |
| B5-3. Pinned environment; deterministic builds; commit design set | Major | **Applied** | Spec rule 2: `requirements.lock` with pip freeze. Roadmap section 5C: `requirements.lock` hashed into RunLog; `output/<client>/<cycle>/<build_id>/`; workbook properties from build id. `[v2.8, B5-3, B5-4]`. The design set commit is Jason's call and is noted as such. |
| B5-4. Pipeline isolation (one client per run; folder discipline) | Major | **Applied** | Roadmap section 5C: "One client per pipeline run; each data batch carries `institution_id` and a run refuses a mismatch. Client data, fixtures and workbooks live outside the product code folder." `[v2.8, B5-3, B5-4]`. |
| B5-5. Cross-client empirical prior removed | Decision | **Applied** | Methodology section 11: "~~Empirical prior pooled across clients~~ **Removed `[v2.8, B5-5]`**". CLAUDE.md: "Never mix one client's confidential information into another client's work, including pooled estimates or priors built from several clients. `[v2.8, B5-5]`." DECISIONS.md closed decision. |
| B5-6. Mockup noted as parts bin | Major | **Applied** | CLAUDE.md: "The mockup in `efa_fao/src/` is a parts bin: its optimizer is per-student and carries the removed guardrail, and its config cannot carry a law client (Session B, B5-6)." |

**B5 verdict:** 5 Applied, 1 Applied with issues (B5-1: roadmap view 2 description retains v2.7 names).

---

### Part B6 — Feasibility (target: `03_technical_roadmap_v2.8.md`, `CLAUDE.md`, `Handoff_Prototype_Phase1.md`)

| Item | Verdict | Evidence |
|---|---|---|
| Must-list schedule; February 2027 deadline | **Applied** | Roadmap section 5A: "Award decisions for the 2027 entering class: the Must items land by February 2027." CLAUDE.md: "Richmond's first award decisions are for the class entering fall 2027; the workbook's Must list lands by February 2027 (roadmap v2.8 section 5A)." Handoff: "Richmond's first award decisions are for the class entering in fall 2027, so Phase 1 should finish in early December." |
| Excel parity risk (test 3 / LibreOffice) | **Applied** | Roadmap section 7 risks table: "Excel parity tests pass without recalculating (LibreOffice does not recalculate XLSX on load by default) → Forced-recalculation profile and a sentinel check (spec v0.6 test 3)." |
| Scope freeze at Must list | **Applied** | Roadmap section 7: "Scope frozen at the section 5A Must list." |
| Richmond data handling outside the spec | **Applied** | DECISIONS.md: "Richmond data handling is Jason's and outside the spec." Handoff section: "Live Richmond build on Richmond's cell data (outside this spec; data handling by Jason)." |

**B6 verdict:** Applied.

---

### Part B7 — Simplification (target: `Prototype_Spec_Scenario_Workbook_v0.6.md`, `02_methodology_v2.8.md`, `03_technical_roadmap_v2.8.md`, `DECISIONS.md`, `CLAUDE.md`)

| Rank | Proposal | Verdict | Evidence |
|---|---|---|---|
| 1 | Drop `Static_MC` from workbook; keep simulation in tests | **Applied** | Spec section 0 "Out of scope": "`Static_MC` (simulation stays in tests)". `[v0.6, B7]`. DECISIONS.md deferred list. |
| 2 | Defer dashboard views 2 and 3; workbook first | **Applied** | Spec section 0: "dashboard (add-on after the workbook)". Roadmap phase 4: "add-on after the Richmond workbook is accepted". Executive read line 10. DECISIONS.md. S1 FR-55/56 marked "Add-on, after the workbook `[v1.3]`". |
| 3 | Defer goal-seek and schedule | **Applied** | Spec section 0 and section 12 deferred list: "`Schedule` and `schedule.py`; goal-seek (`goalseek.py`, `GoalSeek` sheet)". DECISIONS.md deferred list. FR-75 "Deferred `[v1.3, B7-3]`". |
| 4 | Pool strip replaces tripwires | **Applied** | Spec section 3: pool strip defined. D15: "Pool tripwires → Replaced by the pool strip (Nov 16, B7-4)." FR-79. |
| 5 | Net-price block reduced to two lines | **Applied** | Spec section 3: "two lines replace the v0.5 net-price block `[v0.6, B7-5, B1-13]`." D16. FR-80. |
| 6 | Remove `MultiYear` and `Trajectory` stubs | **Applied** | Spec section 12 deferred: "`MultiYear` and `Trajectory` (year 2)". DECISIONS.md deferred list. |
| 7 | Merge two class-size tables (shrink path and proportional factor) | **Applied** | Spec section 3: class-size table shows both the shrink-path rates and "the proportional factor `f = N / M` as a reference column." `[v0.6, B7-7]`. |
| 8 | Merge `tier_yield_offset_pts` into segment shift | **Applied** | Spec section 2 scenario file: "`tier_yield_offset_pts` is removed and its use is covered by `yield_shift_pts_segment`." `[v0.6, B5-1, B7-8]`. |
| 9 | Merge two incentive KPIs into one decomposition | **Applied** | Spec section 3 incentive block: unified decomposition with C, C_any, dE, dSpend, dNTR. `[v0.6, B7-9]`. |
| 10 | Generic priority segment and score/year names before Phase 1 | **Applied** | Spec section 2: all names generic. See B5-1 above for roadmap view 2 caveat. |

**B7 verdict:** Applied (with the roadmap view 2 caveat inherited from B5-1).

---

## 2. Summary table

| Part | Findings | Applied | Applied with issues | Missing |
|---|---|---|---|---|
| B1 (spec mechanics) | 25 | 25 | 0 | 0 |
| B2 (methodology v2.7 edits) | 11 | 11 | 0 | 0 |
| B3 (metric definitions) | 13 | 12 | 1 (B3-4 partial) | 0 |
| B4 (statistical fitness) | 9 | 8 | 1 (B4-4 / FR-14) | 0 |
| B5 (generality) | 6 | 5 | 1 (B5-1 roadmap view) | 0 |
| B6 (feasibility) | 4 items | 4 | 0 | 0 |
| B7 (simplification) | 10 ranks | 10 | 0 | 0 |
| **Total** | **78** | **75** | **3** | **0** |

---

## 3. Issues requiring attention before Phase 1 or the Phase 2 workbook

### Issue 1 — B4-4: S1 FR-14 not updated (target: `S1_Requirements_and_User_Stories.md`)

**What it says:** "Compute projected census: current counts by stage multiplied by historical stage-to-census conversion rates… with a projection interval from prior-year spread and binomial enrollment noise."

**What the methodology now says (section 7):** "interval from binomial noise and the year-level shock s; prior-cycle spread is shown as a check, not used, until five cycles exist `[v2.8, B4-4]`."

**Risk:** the FR-14 acceptance pointer does not reflect the corrected interval method. A builder reading FR-14 alone would implement the old method. The methodology is the source of truth, but a discrepancy in a functional requirement is confusing.

**Recommended action:** Revise FR-14 acceptance text to read "projection interval from binomial noise and the year-level shock s; prior-cycle spread shown as a check; `[v2.8, B4-4]`."

---

### Issue 2 — B5-1: Roadmap view 2 description uses v2.7 names (target: `03_technical_roadmap_v2.8.md`)

**What it says (section 4, line 109):** "Scenario evaluator `[v2.7, V27-37]`: … levers (admit rate, pool multiplier, award, tuition migration, class size under a cap, **out-of-state incentive with its scope, target-tier application lift**, yield shift)…"

**What the naming decision requires:** `bonus_*`, `segment_pool_lift_pct`, `segment` per B5-1.

**Risk:** a builder skimming the roadmap for view 2 requirements would find v2.7 terminology not matching the spec or the config schema. This is a deferred view (add-on after the workbook), so it does not block Phase 1, but it will create confusion when the dashboard work starts.

**Recommended action:** Update the view 2 description to use generic names before dashboard work begins.

---

### Issue 3 — B3-4 (partial): `fields.csv` rename not confirmed

**Context:** B3-4 called for renaming `early_funnel_by_state.deposits` to `deposits_net_of_withdrawals` and asking for LSAT-banded complete applications in the pacing request. The spec and methodology wording changes are present. The `fields.csv` was not fully reviewed for these renamed or added rows — only the guardrail row (B2-11) was checked.

**Risk:** if the data request is sent to Richmond before the DR fields file is updated, the client may supply pacing data that doesn't match what the pipeline expects. This is a data request issue, not a spec or methodology issue.

**Recommended action:** Check `fields.csv` lines in the `early_funnel_by_state` and `early_pacing` sections before sending the law data request.

---

## 4. Cross-document consistency checks

Checked: spec v0.6, methodology v2.8, roadmap v2.8, executive read v2.8, S1 v1.3, handoff (Nov 16), DECISIONS.md. Spot-checked: fields.csv, CLAUDE.md.

| Item | Status |
|---|---|
| Test numbering: spec v0.6 has 18 tests (1–18); handoff says tests 1, 2, 4, 5 and 11–17 for Phase 1 | Consistent |
| Phase 1 scope: same list in spec section 12 and handoff | Consistent |
| NTR names (`ntr_y1`, `ntr_horizon`): spec §3, §15, methodology §3, §5, Appendix F, S1 FR-31, FR-71 | Consistent |
| `discount_entering_y1`: spec §3, §15, methodology §5, Appendix F, S1 FR-74 | Consistent |
| Deferred items: goal-seek, schedule, `MultiYear`, `ntr_horizon` in evaluator, dashboard views, `Static_MC` | Consistent across spec §0, §12, roadmap, DECISIONS.md, S1, CLAUDE.md |
| Deadline: February 2027 for Must list | Consistent in roadmap §5A, CLAUDE.md, handoff |
| s = 0.10 labeled illustrative; O37 open | Consistent in spec §2, §4, §5, methodology §6, roadmap §7 |
| Priority segment (not "target-state tier") | Consistent in spec, methodology, DECISIONS.md, CLAUDE.md, handoff; **inconsistent** in roadmap §4 view 2 description (retains v2.7 names, as noted in Issue 2) |
| Richmond planning tuition 5.5% (unconfirmed); reproduce mode 6.0% | Consistent in spec D4, §2, methodology §5, S1 FR-74, DECISIONS.md |
| Partial pooling k = 20; re-centered base yield | Consistent in spec §4, methodology §5, DECISIONS.md, CLAUDE.md |
| Shrink path protects segment cells below the median threshold only (not all segment cells) | Consistent in spec §3, methodology §5, S1 FR-78, DECISIONS.md |
| Cross-client prior removed | Consistent in methodology §11, DECISIONS.md, CLAUDE.md |
| FR-55 and FR-56 marked "Add-on, after the workbook" | Consistent with roadmap §4 and §5, DECISIONS.md, executive read |
| World W22 (year shock) added | Consistent in methodology §6, roadmap §5 phase 2, DECISIONS.md |
| OD-06 "partly answered" text | Consistent in S1 and DECISIONS.md |

---

## 5. Things in spec v0.6 a Phase 1 builder would have to guess

These are gaps or ambiguities that the fix did not resolve and that would require a builder to make an undocumented choice. None blocks Phase 1 from starting, but each increases the chance of a revision cycle.

| # | Location | What is ambiguous |
|---|---|---|
| 1 | Section 3, pool strip | The formula for `V_m(m)` (median variance as a function of pool multiplier m) is not stated. The class variance expansion `V(m) = V_lo + m V_hi + s² M(m)²` is given, but the analogous expansion for the median variance is not. A builder would need to derive it: admits in high-score cells scale by m, so `G₊(m) = G₊_lo + m G₊_hi` and `G₋(m) = G₋_lo` (low-score cells unaffected by pool multiplier), and `V_m(m) = Σ_{g≠0} A_c(m) y_c (1−y_c) + s² (G₊(m)² + G₋(m)² − 2ρ G₊(m) G₋(m))`. This is derivable but should be stated explicitly to avoid implementation drift. |
| 2 | Section 11, test 4 | "Closed form vs simulation on synthetic worlds: class, median and NTR probabilities within 0.02 for 20 random scenarios." The source of the 20 scenarios is not specified. A builder would need to decide whether these are 20 seeds of the synthetic generator or 20 draws from a parameter space. Recommend stating: "20 random seeds of `synth_cells.py` (fixed seed set, documented in `config/synthetic.yaml`)." |
| 3 | Section 11, test 11 | "With `y0` and `a0` inherited from the unsplit cell (the fallback chain bypassed), splitting out-of-state cells…" The mechanism for bypassing the fallback chain in test code is not specified. A builder needs to decide how to inject a fixed `y0` and `a0` into the base yield function without calling the pooling formula. A test-time parameter (e.g., `y0_override`) or a fixture with pre-set history is needed. |
| 4 | Section 15, interface contract | Named ranges are listed with patterns like `SUM_CLASS*`, `SEG_*`, `INC_*`. The exact suffixes are not given (e.g., `SUM_CLASS_MEAN`, `SUM_CLASS_LO90`, `SUM_CLASS_HI90`). Phase 1 does not build the workbook, so this does not block Phase 1. But a Phase 1 builder writing `risk.py` and `ledger.py` function signatures that test 9 will later enumerate should know the exact names. The contract should be expanded before Phase 2. |
| 5 | Section 3, incentive block | The validity check: "shows 'not valid: parent differs in more than the incentive' unless every lever other than `bonus_usd`, `bonus_scope` and `bonus_min_score` equals the parent's (checked by formula over the lever columns)." The list of levers to compare is not enumerated. A builder must derive it by exclusion from the full scenario field list in section 2 (about 15 scalar levers plus per-cell overrides). Enumerating the check list explicitly in section 3 would eliminate the need to guess. |

---

## 6. What was not checked

- `efa_fao/docs/data_request_v3/spec/fields.csv` lines in the `early_funnel_by_state` and `early_pacing` sections (B3-4 rename). The row checked (line 139, B2-11) was confirmed.
- `efa_fao/docs/data_request_v3/spec/definitions.csv` and the generated Excel templates were not read.
- The `_superseded/` documents were not opened; supersession is taken as declared.
- The pipeline source under `efa_fao/src/` was not reviewed (out of scope per CLAUDE.md spec-phase rule).
- ABA 509 instructions and NACUBO definitions were not consulted independently.

Nothing in this report goes to a client without Jason's review. Check it for Richmond-confidential content before any external distribution.
