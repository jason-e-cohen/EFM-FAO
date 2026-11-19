# Review points: Brandon Metheny's reply (Nov 17, 2026) for the build

**Owner:** Jason Cohen | **Date:** November 17, 2026 | **For:** the reviewer or evaluator session that writes the next spec amendment (proposed tag **[v0.6.3, BM-n]**) | **Base:** `Prototype_Spec_Scenario_Workbook_v0.6.md` at v0.6.2, Phase 2 accepted, Phase 2.1 reviewed

**Source.** Brandon Metheny (Associate Dean of Admissions) replied on Nov 17 to Jason's email of the same day; Dean Rooksby was copied. Client-confidential: keep it to Richmond's files, and copy no fixture values into code, config or tests.

**What he said that matters for the build:**
- 2027-28 tuition is proposed at **$63,500** (the Board approves it in February and rarely changes proposals). The class is **"roughly 140"**. The path beyond 2027 waits for Brandon and Dean Rooksby.
- Richmond is **operating under YA Scenario 4** because early high-LSAT applications are on track. He wants a defined trigger for "the bottom drops out".
- He doesn't know how YA's yield and admit guidelines are built ("historical data").
- **Main campus approves tuition and sets a revenue goal**; otherwise the law school runs itself.
- **Tight class:** keep the 75th to 25th percentile spread small and watch the 10th percentile (bar-passage risk). This matters more as the class shrinks. They also minimize full-tuition scholarships and full-pay students (9 full rides last year, against roughly 27 in earlier years).
- He wants to act between weekly calls: a planner his team can update themselves.
- State counts (by LSAT band) and weekly pacing arrive by the end of this week.

**Recommendation on timing.** BM-1 to BM-5 and BM-7 are schema or config changes that Phase 3 and the live Richmond build sit on. Apply them in a short **Phase 2.2** pass before Phase 3. BM-6 and BM-10 can go in the same pass. BM-8 is for the live build. BM-9 is deferred.

---

## BM-1. Percentile targets (generalize the median). Must; Phase 2.2

**Gap.** v0.6 has margins and P(median holds) at `score.median_thresholds` only. Richmond also needs the 25th, 75th and 10th percentiles.

**Proposal.** Replace `median_thresholds` with `percentile_targets`, a list of `{q, t}`. The median becomes `q = 0.5`, and existing configs load unchanged, mapped one-to-one.
- The q-th percentile is at or above t when at most a share q of the scored class is below t.
- Margin in students: `margin_q(t) = q x N_scored - G_-`, which equals `q G_+ - (1 - q) G_-`. It reads as "students below t that the class can still absorb".
- It is linear in cell counts with weights `g_c = +q` (at or above t), `-(1 - q)` (below), and 0 (unscored, under `excluded`). So the closed form, the pool-strip linear split and the shrink path all carry over.
- Variance: `V_q = q^2 sum_{above} v_c + (1-q)^2 sum_{below} v_c + s^2 (q^2 G_+^2 + (1-q)^2 G_-^2 - 2 rho q (1-q) G_+ G_-)`. At `q = 0.5` this is a quarter of the v0.6 `V_m` (same probability, because the margin is halved too).
- **The reviewer must derive the continuity correction for the weighted margin** and confirm it against simulation within 0.02 (extend test 4). The v0.6 `-0.5` applies to the plus-or-minus-one margin and does not carry over unchanged.

**Readouts.**
- Summary: margin and P(holds) for each target, in the Middle case, with Low and High as for the median.
- Class-size table: the same, at each N.
- Pool strip: the median and P(class > cap) as now; add `q = 0.25` only if it costs no new sheet.
- Spread: no point estimate. Show the **score band containing the expected 25th and 75th percentiles** (from expected cumulative counts), labeled "band, not a score".

**Constraints.**
- Each `t` must be a lower bound in `score.bands`; the loader enforces this, as it does for GPA.
- GPA percentiles are not supported (one GPA boundary). Say so in the README.

**Methodology.** Add the percentile convention, the tie rule and the 10th percentile (not an ABA 509 figure; a client measure) to Appendix F of `02_methodology_v2.8.md`.

**Tests:**
- unit: hand-computed margins at `q = 0.10, 0.25, 0.5, 0.75` on the toy grid;
- `q = 0.5` reproduces every v0.6 median figure;
- test 4 extended;
- shrink-path monotonicity holds for every `t` while the walk is below `t`;
- Excel parity for the new cells.

**Richmond config.** `t` values for 25 and 10 are pending Brandon (Jason's email asked which scores they watch). Until then, use Richmond's public ABA 509 25th percentile from Jason's 509 dashboard as a placeholder, label it, and leave 10 unset.

## BM-2. Tuition as a dollar plan figure. Must; Phase 2.2

**Change.** Allow `tuition_by_year_usd` (for example `{2027: 63500}`), which takes precedence over `tuition_increase_by_year`. The Inputs sheet shows the implied increase. Clients state tuition in dollars, so this is the general form.

**Richmond config:**
- set `tuition_by_year_usd: {2027: 63500}`, with the comment "Brandon, Nov 17: proposed; Board approval February 2027";
- `tuition_base` and `tuition_by_cohort` stay pending Richmond's published figures (OP-8), which Jason enters;
- `tuition_grid` stays as a what-if.

**Note for Jason.** $63,500 is about 6.0% over the base the fixture implies, which matches reproduce mode. Dean Rooksby's "just over 5.5%" doesn't. Confirm the base year's tuition when entering the published figure; it may reconcile the two.

**DECISIONS.md:**
- OD-09: the 2027 figure is now proposed at $63,500 (final in February); the path after 2027 stays open.
- Remove "Richmond planning 5.5%" from the Nov 13 entry, or mark it superseded.

## BM-3. Class target equals the cap in 2027. Must; Phase 2.2 (config and one readout)

**Facts.**
- `class.target` and `class.cap` both stay 140; the glide path toward 100 to 115 is not this cycle. This updates the Nov 13 assumption that it starts now.
- OD-08 stays open for the path.
- New open item **OD-11: is 140 a hard ceiling or a target with room?** Brandon's "roughly 140" leaves this open.

**Readout.** Make sure the class-size table shows **P(class > cap)** at each N, so the target that keeps overshoot risk at an acceptable level can be read off without goal-seek (deferred). Scenario 4 runs at about a 0.41 chance of exceeding 140 on the fixture, per spec section 5 validation. Add a test if the column is new.

## BM-4. Revenue goal from main campus. Must; Phase 2.2

**Gap.** `ntr_target` tests the entering class's first-year NTR (`ntr_y1`). Main campus's goal is likely total JD net tuition, and `ntr_horizon` is deferred.

**Proposal.** Add these optional inputs:
- `ntr_goal_basis`: `entering_y1` (default) or `all_jd`;
- `continuing_ntr_usd`: client-supplied net tuition from returning students in the plan year, fixed.

Under `all_jd`: `P(continuing + ntr_y1 >= goal) = 1 - Phi((goal - continuing - mean)/sqrt(V_n))`. Label it "continuing-student revenue as supplied by the client; attrition and renewals not modeled".

This keeps `ntr_horizon` deferred and stays a client-generic input. The same pattern could later serve `discount_all` (OD-05) with `continuing_aid_usd` and continuing gross tuition; don't build that now.

**Open items.**
- **OD-12:** the revenue goal's value and basis (Jason's email asked).
- Add "continuing-student net tuition for the plan year" to the Richmond data needs (spec section 15 item 10).

**Tests:**
- `entering_y1` equals v0.6;
- `all_jd` with continuing 0 equals `entering_y1`;
- the shift identity;
- Excel parity.

## BM-5. Segment protection against the 10th percentile. **Decided (Jason, Nov 17): adopt; 154 is the NY/PA floor.** Must; Phase 2.2

**Tension.** `trim.protect_segment: below_threshold` places NY/PA cells below the median threshold after all other cells below it. A 152 from New York is cut after a 163 from Virginia, which works against the 10th percentile.

**Proposal.** Add the value `above_floor`: segment cells at or above `score.floor` are protected as now; segment cells below the floor are cut in normal order. **Set `trim.protect_segment: above_floor` in Richmond's config, with `score.floor` 154.** Keep `below_threshold` as an option for clients without a floor concern.

**Test.** With `above_floor`, no segment cell below the floor is cut after a non-segment cell at or above the floor. Every other ordering is unchanged.

## BM-6. Editable growth to date on the pool strip. Should; Phase 2.2

**Change.** Move `pool_ytd_growth` from a config annotation to an **editable Inputs cell with an as-of date**. Mark the nearest `pool_grid` row on the pool strip with a formula ("growth to date is about here"). Keep the existing caution label.

Display only: no logic reads it, and the check that no output comments on an award still holds. This is what lets Brandon's team update the trigger weekly without a rebuild. Pacing import from Slate stays deferred.

**Test.** Changing the cell moves the marker after recalculation in LibreOffice, and nothing else changes.

## BM-7. Scenario 4 first. Must; Phase 3

- In Phase 3, run reproduce acceptance on Scenario 4 first.
- If mismatches remain, resolve Scenario 4's before Scenarios 1 and 2.
- Check that S4's 1.50 pool multiplier and its $10,000 NY/PA specialty sum load exactly.

The first Richmond deliverable is S4's pool strip with growth to date marked (BM-6), and S4's class-size table with percentile rows (BM-1).

## BM-8. Full-tuition and no-award counts as a calibration check. Should; live build

v0.6 already reports full-tuition enrolled, no-merit-award enrolled and the barbell index (KPIs, B3-7), which cover the "minimize full rides and full pay" goal.

For the live build: the base-cycle ledger's expected full-tuition enrolled should land near Brandon's figure of 9. Report the gap; don't assert it.

Confirm with Brandon that "full ride" means full tuition (the KPI's definition).

## BM-9. State counts arriving this week. **Deferred (Jason, Nov 17): handle as the data arrives; not part of this pass.**

The segment needs `share_source: client_counts`. Brandon's counts will be aggregates by state (by LSAT band, if he can). Write down the transform from state counts to a segment share per cell before the data arrives:
- the mapping to the cell schema;
- what happens when the LSAT band is missing (fall back to the residency-level share);
- how small counts are handled (the small-cell policy is none for Richmond's named roles).

Keep it out of `sw/` if it reads client files. Record it where Jason keeps Richmond data handling.

## BM-10. Data request and decisions bookkeeping. Should

**Spec section 15 item 10 and `efa_fao/docs/data_request_v3/spec/`:** add
- continuing-student net tuition (BM-4);
- the LSAT scores they track at the 25th and 10th percentiles (BM-1);
- whether 140 is a ceiling (OD-11).

**`DECISIONS.md`:**
- a Nov 17 entry for Brandon's facts;
- OD-09 updated;
- OD-08 noted (2027 at about 140);
- new OD-11 (cap firmness), OD-12 (revenue goal value and basis) and OD-13 (percentile thresholds), all for Brandon;
- Jason's decisions: BM-5 adopted (154 is the NY/PA floor for trimming); BM-9 deferred.

**Not changed:**
- the segment design;
- "Response based on client-input" (Brandon confirms YA's responses are undocumented);
- the request for deposits and two prior cycles of pacing (already in place, A1-12);
- deferred items (Slate pacing, goal-seek, `ntr_horizon`, the dashboard).
