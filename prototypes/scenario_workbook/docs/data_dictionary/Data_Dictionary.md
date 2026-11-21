# Scenario-workbook data dictionary

Generated from `dictionary.csv` by `build_dictionary.py`; do not edit by hand. One entry per variable, grouped by layer. Client labels with `{braces}` are templates: the workbook fills in the score measure, a threshold t, a share q, a case or a year from the config. A label marked *proposed* is not shown in the workbook. Test 28 checks this file against the code, the configs and a fresh synthetic build.

Columns: `role` follows Methods_Reference section 8 (primary, derived, display; plus input and internal). `response` and `shock` say whether the figure depends on the placeholder response slopes and on the year-shock settings (s, rho). `client-safe` Y means the label, name and description carry no review IDs, config key names or internals. Client-facing work still needs human review before it is sent.

## Contents

| Layer | Rows | Core | Supporting | Internal |
|---|---:|---:|---:|---:|
| [Inputs: client config](#layer-input-config) | 88 | 53 | 33 | 2 |
| [Inputs: scenario levers](#layer-input-scenario) | 26 | 22 | 4 | 0 |
| [Inputs: cell data](#layer-input-data) | 10 | 10 | 0 | 0 |
| [Inputs: other workbook cells](#layer-input-workbook) | 10 | 0 | 10 | 0 |
| [Ledger columns](#layer-ledger) | 40 | 18 | 20 | 2 |
| [Outputs](#layer-output) | 247 | 113 | 114 | 20 |
| [Checks](#layer-check) | 47 | 0 | 47 | 0 |
| [Internals](#layer-internal) | 63 | 0 | 0 | 63 |
| Total | 531 | 216 | 228 | 87 |

- [Index by analyst name](#index-by-analyst-name)

<a id="layer-input-config"></a>

## Inputs: client config

Keys of config/<client>.yaml that the loader names or the configs carry.

<a id="IN-001"></a>

#### IN-001 `client.id`: Client identifier

Short identifier of the client. Names the output folder and appears on RunLog; no figure reads it.

- Client label: "client.id"
- Excel: Inputs!B6 (in_client_id)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 2; sw/config.py REQUIRED; sw/build.py build; tests: 0; 21

<a id="IN-002"></a>

#### IN-002 `client.name`: Client name

Client name shown on Inputs for reference. No figure reads it.

- Client label: "client.name"
- Excel: Inputs!B7 (in_client_name)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: display only
- References: spec 2; sw/config.py REQUIRED; tests: 0; 21

<a id="IN-003"></a>

#### IN-003 `client.vertical`: Vertical

Law or undergraduate. Shown on Inputs; no figure reads it in the prototype.

- Client label: "client.vertical"
- Excel: Inputs!B8 (in_vertical)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: display only
- References: spec 2; sw/config.py REQUIRED; tests: 0; 21

<a id="IN-004"></a>

#### IN-004 `client.small_cell_policy`: Small-cell policy

Disclosure rule for small cells (none for a client with named, authenticated roles). Shown on Inputs and in the README handling note; the prototype suppresses nothing.

- Client label: "client.small_cell_policy"
- Excel: Inputs!B9 (in_small_cell_policy)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: display only
- References: spec 2; methodology section 9; sw/workbook.py w_readme; tests: 0; 21

<a id="IN-005"></a>

#### IN-005 `cycle.base_cycle`: Base cycle

The latest history cohort. Every base quantity (base applications, latest award, base-cycle tuition) is read at this cohort. Build-time.

- Client label: "cycle.base_cycle"
- Excel: Inputs!B15 (in_base_cycle)
- Unit: year; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-022](#LG-022), [INT-004](#INT-004)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; sw/config.py validate; tests: 0; 21

<a id="IN-006"></a>

#### IN-006 `cycle.plan_cycle`: Plan cycle

The entering class the scenarios plan for. Sets Baseline's plan year and which tuition increase applies. Build-time.

- Client label: "cycle.plan_cycle"
- Excel: Inputs!B16 (in_plan_cycle)
- Unit: year; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [IN-092](#IN-092), [INT-021](#INT-021)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; sw/config.py plan_increase_pct; tests: 21

<a id="IN-007"></a>

#### IN-007 `cycle.history`: History cohorts

Cohorts in the cell data. Base yield pools over them; History shows one panel column per cohort. Build-time.

- Client label: "cycle.history"
- Excel: Inputs!B17:D17 (in_history)
- Unit: year; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: [INT-002](#INT-002)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; sw/response.py base_yield; tests: 21

<a id="IN-008"></a>

#### IN-008 `tuition_by_cohort`: Tuition by cohort

Published first-year tuition for each history cohort, fees excluded. Feeds base-cycle tuition, the History award-percent panel and the Checks test that the tuition formula reproduces each history step.

- Client label: "tuition_by_cohort (published first-year tuition; fees excluded)"
- Excel: Inputs!B18:D18 (in_tuition_by_cohort)
- Unit: USD; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: [OUT-138](#OUT-138), [OUT-141](#OUT-141), [CK-025](#CK-025)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; App F 11; sw/config.py validate; tests: 0; 3; 21

<a id="IN-009"></a>

#### IN-009 `tuition_base`: Base-cycle tuition

Tuition in the base cycle; the loader requires it to equal tuition by cohort at the base cycle, and Inputs computes it from that list. Every scenario tuition starts from it.

- Client label: "tuition_base (tuition at base_cycle)"
- Excel: Inputs!B19 (in_tuition_base; a formula on Inputs)
- Unit: USD; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-002](#LG-002), [LG-038](#LG-038), [OUT-083](#OUT-083), [OUT-084](#OUT-084), [OUT-085](#OUT-085), [INT-021](#INT-021)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 3 item 1; sw/config.py scenario_tuition; tests: 0; 1; 21

<a id="IN-010"></a>

#### IN-010 `tuition_increase_by_year`: Planned tuition increase by year

Percent increase over the prior year for each plan year. Baseline's tuition increase reads it unless a dollar tuition is given for that year.

- Client label: "tuition_increase_by_year: increase (%; blank = not given)"
- Excel: Inputs!B21 (in_tuition_increase_pct); years in Inputs!B20 (in_tuition_increase_years, label 'tuition plan year')
- Unit: percent; dimensions: plan year
- Formula: input
- Fed by: none
- Feeds: [INT-021](#INT-021)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 0A A2; sw/config.py plan_increase_pct; tests: 21

<a id="IN-011"></a>

#### IN-011 `tuition_by_year_usd`: Planned tuition in dollars by year

Tuition in dollars for a plan year. Takes precedence over the percent increase; Baseline's increase becomes the implied percent, stored unrounded so rounding returns the dollar figure exactly.

- Client label: "tuition_by_year_usd (tuition in dollars; takes precedence; blank = use the increase)"
- Excel: Inputs!B22 (in_tuition_by_year_usd)
- Unit: USD; dimensions: plan year
- Formula: input
- Fed by: none
- Feeds: [INT-021](#INT-021)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 0A A2; sw/config.py plan_increase_pct; tests: 21; 26

<a id="IN-012"></a>

#### IN-012 `tuition_rounding_usd`: Tuition rounding unit

Scenario tuition is rounded to a multiple of this amount. Feeds every scenario tuition, the tuition what-if grid and the history-step check.

- Client label: "tuition_rounding_usd"
- Excel: Inputs!B23 (in_tuition_rounding_usd)
- Unit: USD; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-002](#LG-002), [LG-038](#LG-038), [CK-025](#CK-025)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; sw/config.py round_to; tests: 0; 1; 21

<a id="IN-013"></a>

#### IN-013 `score.measure`: Score measure name

Name of the test score (for example LSAT). Text only: it appears in Summary labels and the narratives.

- Client label: "score.measure"
- Excel: Inputs!B27 (in_score_measure)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-131](#OUT-131)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 2; tests: 3; 18

<a id="IN-014"></a>

#### IN-014 `score.bands`: Score band lower bounds

Lower bounds of the score bands, highest first. Defines the cell grid's score dimension; every threshold must be one of them; the spread band and admits-cut columns read them. Build-time.

- Client label: "score.bands (lower bounds)"
- Excel: Inputs!B28:J28 (in_score_bands)
- Unit: score; dimensions: band
- Formula: input
- Fed by: none
- Feeds: [OUT-027](#OUT-027), [CK-042](#CK-042)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; sw/config.py validate; tests: 21; 22

<a id="IN-015"></a>

#### IN-015 `score.pool_threshold`: Pool score threshold

Cells at or above this band form the upper score group: the pool multiplier scales their applications, they pool base yield separately and take the upper yield floor and cap. Also splits the pool strip.

- Client label: "score.pool_threshold"
- Excel: Inputs!B29 (in_pool_threshold)
- Unit: score; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [INT-001](#INT-001), [INT-023](#INT-023)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; App F 22; sw/response.py score_group_upper; tests: 1; 15; 19

<a id="IN-016"></a>

#### IN-016 `score.floor`: Score floor

Score below which enrolled students are counted on the Summary and in the narrative. Under above_floor segment protection it also bounds the protected segment cells in the trim order (Checks flags a change).

- Client label: "score.floor"
- Excel: Inputs!B30 (in_score_floor)
- Unit: score; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-015](#OUT-015), [INT-023](#INT-023), [INT-024](#INT-024), [INT-052](#INT-052), [CK-040](#CK-040)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 0A A5; sw/trim.py trim_order; tests: 1; 23

<a id="IN-017"></a>

#### IN-017 `score.percentile_targets`: Percentile targets

List of targets {q, t}: at most a share q of scored enrollees below band bound t. q = 0.5 targets are the medians; the others feed the percentile rows, strips, class-size table and break-evens. q is build-time; t is live.

- Client label: "score.percentile_targets: q (share below t at most q) / t (a band lower bound)"
- Excel: q: Inputs!B32:E32 (in_pct_q); t: Inputs!B33:E33 (in_pct_t)
- Unit: list; dimensions: target
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 0A A1; App F 26; sw/config.py _percentile_targets; tests: 2; 4; 21; 22

<a id="IN-018"></a>

#### IN-018 `score.percentile_targets.q`: Percentile share q

The share of scored enrollees allowed below t, strictly between 0 and 1 with at most two decimals. Sets the margin weights and the continuity correction. Build-time (Checks flags a change).

- Client label: "score.percentile_targets: q (share below t at most q)"
- Excel: Inputs!B32:E32 (in_pct_q)
- Unit: rate; dimensions: target
- Formula: input
- Fed by: none
- Feeds: [OUT-022](#OUT-022), [OUT-023](#OUT-023), [OUT-024](#OUT-024), [INT-022](#INT-022), [INT-032](#INT-032), [INT-033](#INT-033), [CK-043](#CK-043)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 0A A1; sw/config.py _percentile_targets; tests: 21; 22; 23

<a id="IN-019"></a>

#### IN-019 `score.percentile_targets.t`: Percentile threshold t

The score threshold of a percentile target; must be a band lower bound. A q = 0.5 target reads its median threshold on Inputs. Feeds the percentile sign columns.

- Client label: "score.percentile_targets: t (a band lower bound)"
- Excel: Inputs!B33:E33 (in_pct_t)
- Unit: score; dimensions: target
- Formula: input
- Fed by: none
- Feeds: [LG-015](#LG-015), [INT-024](#INT-024), [CK-042](#CK-042)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 0A A1; sw/config.py _percentile_targets; tests: 21; 22; 23

<a id="IN-020"></a>

#### IN-020 `score.median_thresholds`: Median thresholds

The q = 0.5 percentile thresholds, derived by the loader (a legacy config may give this list instead). Feed the median rows, the median sign columns and the pool strip; the first one sets the trim order.

- Client label: "score.median_thresholds (the q = 0.5 percentile targets)"
- Excel: Inputs!B31:C31 (in_median_thresholds)
- Unit: score; dimensions: threshold
- Formula: input
- Fed by: none
- Feeds: [LG-014](#LG-014), [INT-023](#INT-023), [INT-024](#INT-024), [INT-052](#INT-052), [CK-037](#CK-037)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 0A A1; sw/config.py _percentile_targets; tests: 2; 14; 21

<a id="IN-021"></a>

#### IN-021 `gpa.measure`: GPA measure name

Name of the GPA measure. Text only.

- Client label: "gpa.measure"
- Excel: Inputs!B35 (in_gpa_measure)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 2; tests: 21

<a id="IN-022"></a>

#### IN-022 `gpa.hi_at_or_above`: GPA class boundary

GPA at or above which a cell's GPA class is hi. The cell data carry the class; this value labels it. Build-time.

- Client label: "gpa.hi_at_or_above (class boundary)"
- Excel: Inputs!B36 (in_gpa_hi_at_or_above)
- Unit: GPA; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [INT-024](#INT-024)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; sw/config.py validate; tests: 21

<a id="IN-023"></a>

#### IN-023 `gpa.classes`: GPA classes

The three GPA classes of the cell schema; the loader requires exactly hi, lo, blank. Sets cell order and the GPA sign of each cell.

- Client label: "GPA classes (hi, lo, blank)" (proposed)
- Excel: Python only
- Unit: list; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-014](#LG-014)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 2; sw/config.py validate; tests: 21

<a id="IN-024"></a>

#### IN-024 `gpa.median_threshold`: GPA median threshold

Threshold of the GPA median row; must equal the GPA class boundary because the cell schema has one GPA boundary.

- Client label: "gpa.median_threshold (equals the class boundary)"
- Excel: Inputs!B37 (in_gpa_median_threshold)
- Unit: GPA; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-014](#LG-014)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; sw/config.py validate; tests: 21

<a id="IN-025"></a>

#### IN-025 `unscored_in_median`: Unscored in median rule

excluded (default; the ABA 509 basis): unscored and blank-GPA enrollees leave both sides of the margins and are reported as a count. below: they count below t. Feeds every sign column.

- Client label: "unscored_in_median (excluded or below)"
- Excel: Inputs!B38 (in_unscored_in_median)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-014](#LG-014), [LG-015](#LG-015), [OUT-027](#OUT-027)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 0A B1; App F 8; sw/risk.py median_signs; tests: 2; 3; 22

<a id="IN-026"></a>

#### IN-026 `class.cap`: Class cap

Hard upper bound on the entering class. Baseline's class cap reads it; feeds P(class above cap).

- Client label: "class.cap (hard this cycle)"
- Excel: Inputs!B41 (in_class_cap)
- Unit: count; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [IN-099](#IN-099)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; App F 7; tests: 16; 19

<a id="IN-027"></a>

#### IN-027 `class.target`: Class target

The planned class, at most the cap. Baseline's class target reads it; feeds the target band probability, the class break-evens and the shrink path.

- Client label: "class.target"
- Excel: Inputs!B42 (in_class_target)
- Unit: count; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [IN-098](#IN-098)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; App F 7; tests: 8; 16; 24

<a id="IN-028"></a>

#### IN-028 `class.band`: Class target band

Half-width of the band around the target used by P(class within target band) and the class Checks row.

- Client label: "class.band"
- Excel: Inputs!B43 (in_class_band)
- Unit: count; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-012](#OUT-012), [CK-026](#CK-026)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 5; tests: 2; 19

<a id="IN-029"></a>

#### IN-029 `class.what_if`: Class sizes for the class-size table

Class sizes N for which the shrink path writes admit rates; one class-size table row and one Trim block per N.

- Client label: "class.what_if (class-size table)"
- Excel: Inputs!B44:J44 (in_class_what_if)
- Unit: count; dimensions: N
- Formula: input
- Fed by: none
- Feeds: [OUT-115](#OUT-115), [OUT-129](#OUT-129), [INT-056](#INT-056)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 3 class-size table; tests: 14; 16

<a id="IN-030"></a>

#### IN-030 `class.supported_range`: Supported class range

Class targets inside this range are tested; outside it a target carries the class-target notice. Default 0.7 x cap to cap.

- Client label: "class.supported_range (low, high)"
- Excel: Inputs!B45:C45 (in_supported_range)
- Unit: count; dimensions: pair
- Formula: input
- Fed by: none
- Feeds: [CK-028](#CK-028)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 2; sw/config.py check_class_target; tests: 16

<a id="IN-031"></a>

#### IN-031 `class.reject_range`: Rejected class range

A class target outside this range is an error when scenarios are built. Default 0.6 x cap to 1.1 x cap.

- Client label: "class.reject_range (low, high)"
- Excel: Inputs!B46:C46 (in_reject_range)
- Unit: count; dimensions: pair
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 2; sw/config.py check_class_target; tests: 16

<a id="IN-032"></a>

#### IN-032 `need.total`: Need aid total

Need aid at the reference class. Sets the need rate per enrollee; Baseline's need total reads it; a scenario's departure from it is a fixed amount.

- Client label: "need.total"
- Excel: Inputs!B49 (in_need_total)
- Unit: USD; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [IN-097](#IN-097), [LG-004](#LG-004), [LG-005](#LG-005), [INT-019](#INT-019)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 3 item 7; App F 12; tests: 1; 8; 19

<a id="IN-033"></a>

#### IN-033 `need.reference_class`: Need reference class

Class size at which need aid equals the need total; divides it to give the need rate.

- Client label: "need.reference_class"
- Excel: Inputs!B50 (in_need_reference_class)
- Unit: count; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-004](#LG-004), [INT-019](#INT-019)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; tests: 1; 8

<a id="IN-034"></a>

#### IN-034 `ntr_target`: Net tuition revenue target

Revenue goal. Under entering_y1 it is the entering-class first-year goal; under all_jd the total JD goal, from which continuing revenue is subtracted. Feeds the effective target.

- Client label: "ntr_target (blank = none; under all_jd the total JD goal)"
- Excel: Inputs!B55 (in_ntr_target)
- Unit: USD; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-041](#OUT-041), [INT-020](#INT-020)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 0A A4; sw/config.py ntr_target_effective; tests: 19; 25

<a id="IN-035"></a>

#### IN-035 `ntr_goal_basis`: Revenue goal basis

entering_y1 (default) or all_jd. Chooses whether the effective target subtracts continuing-student revenue and whether the JD rows show figures.

- Client label: "ntr_goal_basis (entering_y1 or all_jd)"
- Excel: Inputs!B56 (in_ntr_goal_basis)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-044](#OUT-044), [OUT-045](#OUT-045), [OUT-046](#OUT-046), [OUT-082](#OUT-082), [INT-020](#INT-020), [CK-030](#CK-030)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 0A A4; tests: 21; 25; 26

<a id="IN-036"></a>

#### IN-036 `continuing_ntr_usd`: Continuing-student net tuition

Client-supplied net tuition from continuing students in the plan year, held fixed. Required under all_jd; subtracted from the target and added to ntr_y1 for the JD total.

- Client label: "continuing_ntr_usd (continuing-student net tuition, plan year)"
- Excel: Inputs!B57 (in_continuing_ntr_usd)
- Unit: USD; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-044](#OUT-044), [OUT-045](#OUT-045), [INT-020](#INT-020), [CK-030](#CK-030)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 0A A4; tests: 21; 25; 26

<a id="IN-037"></a>

#### IN-037 `discount_target`: Discount rate target

Optional discount-rate target. Baseline's discount target reads it; feeds the margin to discount target row.

- Client label: "discount_target (blank = none)"
- Excel: Inputs!B59 (in_discount_target)
- Unit: ratio; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [IN-111](#IN-111)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 2; spec 3 discount row; tests: 3; 19

<a id="IN-038"></a>

#### IN-038 `budget_total`: Aid budget

Optional aid budget. Checks compares Middle-case spend with it.

- Client label: "budget_total (blank = none)"
- Excel: Inputs!B60 (in_budget_total)
- Unit: USD; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [CK-029](#CK-029)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 7; tests: 19

<a id="IN-039"></a>

#### IN-039 `budget_basis`: Budget basis

total_aid (merit + need + specialty, default) or merit: what the budget check compares.

- Client label: "budget_basis (total_aid or merit)"
- Excel: Inputs!B61 (in_budget_basis)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [CK-029](#CK-029)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 7; tests: 19

<a id="IN-040"></a>

#### IN-040 `merit_actual_by_cohort`: Reported merit by cohort

Optional reported merit dollars per history cohort. Checks compares the grid-implied merit with it (percent gap).

- Client label: "merit_actual_by_cohort (reported merit; blank = not given)"
- Excel: Inputs!B62:D62 (in_merit_actual_by_cohort)
- Unit: USD; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: [CK-031](#CK-031)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 7; sw/ledger.py history_reconciliation; tests: 19

<a id="IN-041"></a>

#### IN-041 `risk.common_shock_sd`: Year-shock standard deviation

SD s of the common multiplicative year shock on yield. Enters every variance (s^2 terms), so every probability and range. Illustrative until calibrated.

- Client label: "risk.common_shock_sd (s)"
- Excel: Inputs!B65 (in_common_shock_sd)
- Unit: rate; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-009](#OUT-009), [OUT-010](#OUT-010), [OUT-020](#OUT-020), [OUT-021](#OUT-021), [OUT-023](#OUT-023), [OUT-024](#OUT-024), [OUT-087](#OUT-087), [INT-026](#INT-026), [INT-031](#INT-031), [INT-033](#INT-033), [INT-035](#INT-035), [INT-036](#INT-036), [INT-037](#INT-037)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 5; MR 6.1; tests: 2; 4

<a id="IN-042"></a>

#### IN-042 `risk.shock_source`: Shock source

illustrative, public or client. While illustrative, probabilities beyond 5% and 95% display as text and the year-to-year label applies.

- Client label: "risk.shock_source"
- Excel: Inputs!B66 (in_shock_source)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-011](#OUT-011), [OUT-012](#OUT-012), [OUT-020](#OUT-020), [OUT-021](#OUT-021), [OUT-023](#OUT-023), [OUT-024](#OUT-024), [OUT-043](#OUT-043), [OUT-046](#OUT-046), [OUT-061](#OUT-061)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 4; sw/labels.py fmt_prob; tests: 7; 19

<a id="IN-043"></a>

#### IN-043 `risk.shock_corr_above_below`: Shock correlation across a threshold

Correlation rho of the shocks of cells at or above and below a threshold. Enters the median and percentile variances; the rho 0.5 rows are a fixed sensitivity.

- Client label: "risk.shock_corr_above_below (rho)"
- Excel: Inputs!B67 (in_shock_corr)
- Unit: rate; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-020](#OUT-020), [OUT-023](#OUT-023), [INT-031](#INT-031), [INT-033](#INT-033)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 5; MR 6.3; tests: 2; 4

<a id="IN-044"></a>

#### IN-044 `risk.sensitivity_slopes.low`: Placeholder slope, Low case

Client-input yield response in points per $1,000 of award for the Low case. Enters base yield re-centering and the Ledger_Low yield column.

- Client label: "risk.sensitivity_slopes.low (yield points per $1,000)"
- Excel: Inputs!B68 (in_slope_low)
- Unit: points per $1,000; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-032](#LG-032), [INT-013](#INT-013)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 4; MR 5.2; tests: 1; 11; 19

<a id="IN-045"></a>

#### IN-045 `risk.sensitivity_slopes.middle`: Placeholder slope, Middle case

Client-input yield response in points per $1,000 of award for the Middle case. Enters base yield re-centering and the Ledger_Middle yield column.

- Client label: "risk.sensitivity_slopes.middle (yield points per $1,000)"
- Excel: Inputs!B69 (in_slope_middle)
- Unit: points per $1,000; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-032](#LG-032), [INT-013](#INT-013)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 4; MR 5.2; tests: 1; 11; 19

<a id="IN-046"></a>

#### IN-046 `risk.sensitivity_slopes.high`: Placeholder slope, High case

Client-input yield response in points per $1,000 of award for the High case. Enters base yield re-centering and the Ledger_High yield column.

- Client label: "risk.sensitivity_slopes.high (yield points per $1,000)"
- Excel: Inputs!B70 (in_slope_high)
- Unit: points per $1,000; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-032](#LG-032), [INT-013](#INT-013)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 4; MR 5.2; tests: 1; 11; 19

<a id="IN-047"></a>

#### IN-047 `risk.yield_floor.upper`: Yield floor, upper score group

Lowest yield allowed for upper-group cells; the yield formula clips at it twice.

- Client label: "risk.yield_floor.upper"
- Excel: Inputs!B71 (in_yield_floor_upper)
- Unit: rate; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [INT-014](#INT-014)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 5; spec 4; tests: 1; 19

<a id="IN-048"></a>

#### IN-048 `risk.yield_cap.upper`: Yield cap, upper score group

Highest yield allowed for upper-group cells; the yield formula clips at it twice.

- Client label: "risk.yield_cap.upper"
- Excel: Inputs!B72 (in_yield_cap_upper)
- Unit: rate; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [INT-015](#INT-015)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 5; spec 4; tests: 1; 19

<a id="IN-049"></a>

#### IN-049 `risk.yield_floor.lower`: Yield floor, lower score group

Lowest yield allowed for lower-group cells; the yield formula clips at it twice.

- Client label: "risk.yield_floor.lower"
- Excel: Inputs!B73 (in_yield_floor_lower)
- Unit: rate; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [INT-014](#INT-014)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 5; spec 4; tests: 1; 19

<a id="IN-050"></a>

#### IN-050 `risk.yield_cap.lower`: Yield cap, lower score group

Highest yield allowed for lower-group cells; the yield formula clips at it twice.

- Client label: "risk.yield_cap.lower"
- Excel: Inputs!B74 (in_yield_cap_lower)
- Unit: rate; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [INT-015](#INT-015)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 5; spec 4; tests: 1; 19

<a id="IN-051"></a>

#### IN-051 `risk.yield_shift_grid`: Yield shift grid

Shifts d (points) for the yield what-if strip rows; the largest and smallest set the clip count.

- Client label: "risk.yield_shift_grid (points)"
- Excel: Inputs!B75:H75 (in_yield_shift_grid)
- Unit: points; dimensions: grid value
- Formula: input
- Fed by: none
- Feeds: [OUT-087](#OUT-087), [OUT-095](#OUT-095), [OUT-096](#OUT-096)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 yield strip; tests: 15; 19

<a id="IN-052"></a>

#### IN-052 `risk.pool_grid`: Pool multiplier grid

Pool multipliers m for the pool strip rows; strictly ascending. Bounds the break-even notes and places the growth-to-date marker.

- Client label: "risk.pool_grid (pool multiplier)"
- Excel: Inputs!B76:J76 (in_pool_grid)
- Unit: multiplier; dimensions: grid value
- Formula: input
- Fed by: none
- Feeds: [OUT-099](#OUT-099), [OUT-109](#OUT-109), [OUT-111](#OUT-111), [INT-050](#INT-050), [INT-051](#INT-051)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 pool strip; spec 0A A6; tests: 15; 24; 26

<a id="IN-053"></a>

#### IN-053 `risk.tuition_grid`: Tuition what-if grid

Tuition increases p for the tuition what-if rows and the award-at-T(p) Ledger columns.

- Client label: "risk.tuition_grid (increase %)"
- Excel: Inputs!B77:E77 (in_tuition_grid)
- Unit: percent; dimensions: grid value
- Formula: input
- Fed by: none
- Feeds: [LG-038](#LG-038), [OUT-076](#OUT-076), [OUT-081](#OUT-081)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 tuition what-if; tests: 8; 15; 19

<a id="IN-054"></a>

#### IN-054 `pooling_k`: Pooling weight

Prior weight, in admits, of the pool yield in each cell's base yield (k in the partial pooling formula).

- Client label: "pooling_k (prior weight, admits)"
- Excel: Inputs!B78 (in_pooling_k)
- Unit: count; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [INT-013](#INT-013)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 4; MR 5.1; tests: 11; 19

<a id="IN-055"></a>

#### IN-055 `pooling_min_admits`: Minimum admits for the segment pool

Product rule (default 30): the (residency, segment, score group) pool is used only with at least this many history admits; otherwise base yield falls back to a wider pool.

- Client label: "pool size for the segment pool (admits)"
- Excel: Inputs!B79 (in_pooling_min_admits)
- Unit: count; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [INT-011](#INT-011)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 4; sw/config.py DEFAULTS; tests: 11; 19

<a id="IN-056"></a>

#### IN-056 `integer_admits`: Round admits

Rounds admits to whole numbers when set. True in reproduce builds only; a live build refuses it.

- Client label: "integer_admits (1 = round)"
- Excel: Inputs!B82 (in_integer_admits)
- Unit: flag; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-027](#LG-027), [LG-039](#LG-039), [INT-059](#INT-059)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 3 item 3; tests: 3; 6; 14

<a id="IN-057"></a>

#### IN-057 `integer_enrolled`: Round enrolled

Rounds enrolled to whole numbers when set. True in reproduce builds only.

- Client label: "integer_enrolled (1 = round)"
- Excel: Inputs!B83 (in_integer_enrolled)
- Unit: flag; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-035](#LG-035)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 3 item 6; tests: 3; 6

<a id="IN-058"></a>

#### IN-058 `evidence_tolerance_usd`: Evidence tolerance

Dollars added on each side of a cell's observed award range when labeling a yield observed or extrapolated.

- Client label: "evidence_tolerance_usd"
- Excel: Inputs!B80 (in_evidence_tolerance_usd)
- Unit: USD; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-033](#LG-033)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 4; App F 24; tests: 19

<a id="IN-059"></a>

#### IN-059 `marginal_admit_yield_slope`: Marginal-admit yield slope

Read and ignored: marginal-admit yield is not modeled. A non-zero value adds a notice.

- Client label: "marginal_admit_yield_slope"
- Excel: Inputs!B81 (in_marginal_admit_yield_slope)
- Unit: points; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-240](#OUT-240)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: display only
- References: spec 4; CLAUDE.md deferred features; tests: 21

<a id="IN-060"></a>

#### IN-060 `segments`: Configured segments

List of priority segments (at most one active per scenario); each names the cells within one residency that form it. An empty list is allowed.

- Client label: "segment"
- Excel: Inputs!A86:E87
- Unit: list; dimensions: segment
- Formula: input
- Fed by: none
- Feeds: [CK-036](#CK-036)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; App F 17; tests: 11; 17; 21

<a id="IN-061"></a>

#### IN-061 `segments.name`: Segment name

Name of a segment; cells carry it in the segment column. The scenario's active segment resolves to it.

- Client label: "name"
- Excel: Inputs!B87 (in_seg_names)
- Unit: text; dimensions: segment
- Formula: input
- Fed by: none
- Feeds: [LG-006](#LG-006)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; tests: 11; 13; 17

<a id="IN-062"></a>

#### IN-062 `segments.within.residency`: Segment residency

The residency (in or out) the segment lies within. Checks confirms every segment cell has it.

- Client label: "within residency"
- Excel: Inputs!C87 (in_seg_within)
- Unit: text; dimensions: segment
- Formula: input
- Fed by: none
- Feeds: [CK-034](#CK-034)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; tests: 11; 21

<a id="IN-063"></a>

#### IN-063 `segments.members_label`: Segment members label

Text naming the segment's members (for example states). A label only; the cell data carry membership.

- Client label: "members label"
- Excel: Inputs!D87 (in_seg_members)
- Unit: text; dimensions: segment
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: display only
- References: spec 2; tests: 21

<a id="IN-064"></a>

#### IN-064 `segments.share_source`: Segment share source

client_counts or assumed. When assumed, every segment figure carries the segment-share label.

- Client label: "share source"
- Excel: Inputs!E87 (in_seg_share_source)
- Unit: text; dimensions: segment
- Formula: input
- Fed by: none
- Feeds: [OUT-055](#OUT-055)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 3 segment block; tests: 7; 21

<a id="IN-065"></a>

#### IN-065 `trim.protect_segment`: Segment protection in the shrink path

Where segment cells go in the trim order: below_threshold, above_floor or none. Build-time (sets the Trim order; Checks flags a change).

- Client label: "trim.protect_segment (below_threshold, above_floor or none)"
- Excel: Inputs!B90 (in_protect_segment)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [INT-052](#INT-052), [CK-038](#CK-038), [CK-040](#CK-040)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 shrink path; spec 0A A5; tests: 14; 23

<a id="IN-066"></a>

#### IN-066 `trim.floor_rate`: Trim floor rate

Lowest admit rate the shrink path may cut a cell to. Feeds removable enrollment and trimmed rates.

- Client label: "trim.floor_rate (absolute admit rate)"
- Excel: Inputs!B91 (in_trim_floor_rate)
- Unit: rate; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [INT-053](#INT-053), [INT-057](#INT-057)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 shrink path; tests: 14

<a id="IN-067"></a>

#### IN-067 `trim.exempt_cells`: Cells exempt from trimming

Cell ids the shrink path never cuts. Build-time (Checks flags a change).

- Client label: "trim.exempt_cells"
- Excel: Inputs!B92 (in_exempt_cells)
- Unit: list; dimensions: cell
- Formula: input
- Fed by: none
- Feeds: [INT-053](#INT-053), [CK-039](#CK-039)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3 shrink path; tests: 14

<a id="IN-068"></a>

#### IN-068 `pool_ytd_growth`: Pool growth to date

Client-reported growth in complete applications at or above the pool threshold against the same week of the prior cycle. Display only: it marks the nearest pool-strip row; no other figure reads it.

- Client label: "pool_ytd_growth (display only: marks the pool-strip row)"
- Excel: Inputs!B95 (in_pool_ytd_growth)
- Unit: rate; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-108](#OUT-108), [OUT-110](#OUT-110), [INT-051](#INT-051)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: display only
- References: spec 0A A6; App F 22; tests: 24; 26

<a id="IN-069"></a>

#### IN-069 `pool_ytd_as_of`: Growth to date as-of date

Date of the growth figure; text in the marker.

- Client label: "pool_ytd_as_of (date of the growth figure)"
- Excel: Inputs!B96 (in_pool_ytd_as_of)
- Unit: date; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-108](#OUT-108), [OUT-110](#OUT-110)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: display only
- References: spec 0A A6; tests: 21

<a id="IN-070"></a>

#### IN-070 `mode`: Mode

live or reproduce; set by the reproduce build, not by hand. On Inputs it is a switch: in a reproduce build Reproduce makes the Ledgers read the loaded yields and tuition.

- Client label: "mode (Live or Reproduce)"
- Excel: Inputs!B12 (in_mode)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-002](#LG-002), [LG-004](#LG-004), [LG-032](#LG-032), [OUT-170](#OUT-170), [CK-015](#CK-015), [CK-016](#CK-016)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 9; spec 0A B; tests: 3; 6; 21

<a id="IN-071"></a>

#### IN-071 `reproduce`: Reproduce settings block

Settings used only by reproduce builds: the fixture's tuition increase, counting rule and application rounding.

- Client label: "reproduce settings" (proposed)
- Excel: Python only
- Unit: list; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: spec 0A B; DECISIONS Nov 18; tests: 6; 21

<a id="IN-072"></a>

#### IN-072 `reproduce.tuition_increase_pct`: Reproduce tuition increase

Tuition increase used in reproduce mode, where the dollar figure is dropped.

- Client label: "reproduce tuition increase" (proposed)
- Excel: Python only
- Unit: percent; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [IN-093](#IN-093)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: spec 0A B; sw/reproduce.py reproduce_config; tests: 6; 21

<a id="IN-073"></a>

#### IN-073 `reproduce.unscored_in_median`: Reproduce counting rule

Counting rule for unscored enrollees in reproduce mode (excluded, as the fixture counts them).

- Client label: "reproduce counting rule" (proposed)
- Excel: Python only
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-014](#LG-014)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: spec 0A B1; sw/reproduce.py reproduce_config; tests: 6

<a id="IN-074"></a>

#### IN-074 `reproduce.round_apps_after_pool`: Round applications after the pool multiplier

In reproduce mode only, rounds applications to whole numbers after the pool multiplier, as the fixture does. Live mode never rounds them.

- Client label: "reproduce.round_apps_after_pool (1 = whole applications after the pool multiplier)"
- Excel: Inputs (reproduce builds): in_round_apps_after_pool
- Unit: flag; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [LG-025](#LG-025)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: reproduce only
- References: spec 0A B2; sw/config.py round_apps_after_pool; tests: 3; 6

<a id="IN-075"></a>

#### IN-075 `aba_509_by_cohort`: Public ABA 509 figures

Optional public ABA 509 figures per history cohort. Feed the report-only History 509 check.

- Client label: "ABA 509 figures by cohort" (proposed)
- Excel: Python only
- Unit: list; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A B7; sw/ledger.py aba509_reconciliation; tests: 3; 9

<a id="IN-076"></a>

#### IN-076 `aba_509_by_cohort.first_year_class`: ABA 509 first-year class

Published ABA 509 count (first-year class) for one history cohort; compared with the cell data.

- Client label: "first-year class" (proposed)
- Excel: History 509 block, column '<year> 509'
- Unit: count; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: [OUT-142](#OUT-142)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A B7; sw/config.py ABA_509_KEYS; tests: 3; 9

<a id="IN-077"></a>

#### IN-077 `aba_509_by_cohort.without_score`: ABA 509 matriculants without a score

Published ABA 509 count (matriculants without a score) for one history cohort; compared with the cell data.

- Client label: "matriculants without a score" (proposed)
- Excel: History 509 block, column '<year> 509'
- Unit: count; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: [OUT-143](#OUT-143)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A B7; sw/config.py ABA_509_KEYS; tests: 3; 9

<a id="IN-078"></a>

#### IN-078 `aba_509_by_cohort.without_gpa`: ABA 509 matriculants without a GPA

Published ABA 509 count (matriculants without a GPA) for one history cohort; compared with the cell data.

- Client label: "matriculants without a GPA" (proposed)
- Excel: History 509 block, column '<year> 509'
- Unit: count; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: [OUT-144](#OUT-144)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A B7; sw/config.py ABA_509_KEYS; tests: 3; 9

<a id="IN-079"></a>

#### IN-079 `aba_509_by_cohort.score_p25`: ABA 509 score 25th percentile

Published 25th percentile of the score for one history cohort; the check asks whether it lies in the range the band shares allow.

- Client label: "score 25th percentile" (proposed)
- Excel: History 509 block, column '<year> 509'
- Unit: score; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: [OUT-145](#OUT-145)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A B7; sw/config.py ABA_509_KEYS; tests: 3; 9

<a id="IN-080"></a>

#### IN-080 `aba_509_by_cohort.score_p50`: ABA 509 score 50th percentile

Published 50th percentile of the score for one history cohort; the check asks whether it lies in the range the band shares allow.

- Client label: "score 50th percentile" (proposed)
- Excel: History 509 block, column '<year> 509'
- Unit: score; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: [OUT-146](#OUT-146)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A B7; sw/config.py ABA_509_KEYS; tests: 3; 9

<a id="IN-081"></a>

#### IN-081 `aba_509_by_cohort.score_p75`: ABA 509 score 75th percentile

Published 75th percentile of the score for one history cohort; the check asks whether it lies in the range the band shares allow.

- Client label: "score 75th percentile" (proposed)
- Excel: History 509 block, column '<year> 509'
- Unit: score; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: [OUT-147](#OUT-147)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A B7; sw/config.py ABA_509_KEYS; tests: 3; 9

<a id="IN-082"></a>

#### IN-082 `aba_509_by_cohort.gpa_p25`: ABA 509 GPA 25th percentile

Published 25th percentile of the GPA for one history cohort; the check asks whether it lies in the range the band shares allow.

- Client label: "gpa 25th percentile" (proposed)
- Excel: History 509 block, column '<year> 509'
- Unit: GPA; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: [OUT-148](#OUT-148)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A B7; sw/config.py ABA_509_KEYS; tests: 3; 9

<a id="IN-083"></a>

#### IN-083 `aba_509_by_cohort.gpa_p50`: ABA 509 GPA 50th percentile

Published 50th percentile of the GPA for one history cohort; the check asks whether it lies in the range the band shares allow.

- Client label: "gpa 50th percentile" (proposed)
- Excel: History 509 block, column '<year> 509'
- Unit: GPA; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: [OUT-149](#OUT-149)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A B7; sw/config.py ABA_509_KEYS; tests: 3; 9

<a id="IN-084"></a>

#### IN-084 `aba_509_by_cohort.gpa_p75`: ABA 509 GPA 75th percentile

Published 75th percentile of the GPA for one history cohort; the check asks whether it lies in the range the band shares allow.

- Client label: "gpa 75th percentile" (proposed)
- Excel: History 509 block, column '<year> 509'
- Unit: GPA; dimensions: cohort
- Formula: input
- Fed by: none
- Feeds: [OUT-150](#OUT-150)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A B7; sw/config.py ABA_509_KEYS; tests: 3; 9

<a id="IN-085"></a>

#### IN-085 `hold_position_rows`: Hold median and percentile figures

Build setting. When true, every median and percentile figure on the Summary reads the hold text until the score basis is confirmed. Reproduce builds are never held.

- Client label: "hold_position_rows"
- Excel: RunLog 'hold_position_rows'; not an Inputs cell
- Unit: flag; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-174](#OUT-174), [INT-024](#INT-024)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: R4-06; F-1; sw/contract.py is_held; tests: 10; 21; 27

<a id="IN-086"></a>

#### IN-086 `small_cell_suppression`: Small-cell suppression (unused key)

Present in one client config and in spec section 2, but no code reads it; client.small_cell_policy is the key the loader requires.

- Client label: "small cell suppression" (proposed)
- Excel: Python only
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: display only
- References: spec 2; one client config under config/; tests: 28

<a id="IN-087"></a>

#### IN-087 `generator`: Synthetic generator parameters

Block in the synthetic config only: parameters of the stopgap cell-level generator (seeds, shares, logits, award shares, yield targets). Feeds synthetic cell data; provenance in docs/shape_targets.md.

- Client label: "synthetic generator parameters" (proposed)
- Excel: Python only
- Unit: list; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 10; sw/synth_cells.py generate; docs/shape_targets.md; tests: 5

<a id="IN-088"></a>

#### IN-088 `test4`: Test 4 scenario ranges

Block in the synthetic config only: ranges from which test 4 draws one scenario per world, the draw count and the tolerance.

- Client label: "test 4 draw ranges" (proposed)
- Excel: Python only
- Unit: list; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 11; sw/synth_cells.py scenario_draws; tests: 4

<a id="layer-input-scenario"></a>

## Inputs: scenario levers

Fields of the scenario file and the Levers sheet.

<a id="IN-089"></a>

#### IN-089 `name`: Scenario name

Name of the scenario; Baseline is first. Heads every Ledger block and Summary column.

- Client label: "Scenario"
- Excel: Levers!A4 row, one column per scenario
- Unit: text; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [LG-001](#LG-001)
- Role: input; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 2 scenario file; tests: 3; 9

<a id="IN-090"></a>

#### IN-090 `parent`: Parent scenario

Scenario a child inherits its levers from; Baseline has none. The incentive block and change counts compare with it. Echoed on Summary row 'parent'.

- Client label: "parent"
- Excel: Levers!A5 row, one column per scenario; echoed on Summary main block row 'parent'
- Unit: text; dimensions: scenario
- Formula: input
- Fed by: [IN-134](#IN-134)
- Feeds: [OUT-065](#OUT-065), [OUT-067](#OUT-067), [OUT-068](#OUT-068), [OUT-069](#OUT-069), [OUT-074](#OUT-074), [OUT-132](#OUT-132), [OUT-133](#OUT-133), [OUT-134](#OUT-134)
- Role: input; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 2 scenario file; tests: 8; 13

<a id="IN-091"></a>

#### IN-091 `description`: Scenario description

Free text describing the scenario. Text only.

- Client label: "description"
- Excel: Levers!A6 row, one column per scenario
- Unit: text; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: Y; status: display only
- References: spec 2 scenario file; tests: 8; 19

<a id="IN-092"></a>

#### IN-092 `plan_year`: Plan year

Label only in the prototype: tuition comes from the scenario's tuition increase. Part of the incentive validity comparison.

- Client label: "plan_year (label)"
- Excel: Levers!A7 row, one column per scenario
- Unit: year; dimensions: scenario
- Formula: input
- Fed by: [IN-006](#IN-006)
- Feeds: [OUT-074](#OUT-074)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: display only
- References: spec 2 scenario file; tests: 8; 19

<a id="IN-093"></a>

#### IN-093 `tuition_increase_pct`: Tuition increase

Percent increase from base-cycle tuition to the scenario's tuition. Baseline reads it from Inputs; a child inherits it. Echoed on Summary row 'Tuition increase'.

- Client label: "tuition_increase_pct"
- Excel: Levers!A8 row, one column per scenario; echoed on Summary main block row 'Tuition increase'
- Unit: percent; dimensions: scenario
- Formula: input
- Fed by: [INT-021](#INT-021), [IN-072](#IN-072)
- Feeds: [LG-002](#LG-002), [LG-003](#LG-003), [OUT-074](#OUT-074), [CK-047](#CK-047)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 3 item 1; tests: 1; 8; 19

<a id="IN-094"></a>

#### IN-094 `award_scale_with_tuition`: Awards scale with tuition

When set, lever awards scale by 1 + p; otherwise they stay fixed in dollars (the full-tuition rung follows tuition either way).

- Client label: "award_scale_with_tuition (1 = scale)"
- Excel: Levers!A9 row, one column per scenario
- Unit: flag; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [LG-028](#LG-028), [LG-038](#LG-038), [OUT-074](#OUT-074)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 3 item 4; tests: 1; 19

<a id="IN-095"></a>

#### IN-095 `pool_multiplier`: Pool multiplier

Final complete applications at or above the pool threshold over the base cycle's. Scales upper-group applications; the pool strip replaces it with m.

- Client label: "pool_multiplier"
- Excel: Levers!A10 row, one column per scenario
- Unit: multiplier; dimensions: scenario
- Formula: input
- Fed by: [IN-130](#IN-130)
- Feeds: [LG-025](#LG-025), [OUT-074](#OUT-074), [OUT-130](#OUT-130), [CK-046](#CK-046)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 2; App F 22; tests: 1; 15; 19

<a id="IN-096"></a>

#### IN-096 `specialty_usd`: Specialty aid

Lump-sum specialty aid for the scenario. Enters aid and ntr_y1.

- Client label: "specialty_usd"
- Excel: Levers!A11 row, one column per scenario
- Unit: USD; dimensions: scenario
- Formula: input
- Fed by: [IN-131](#IN-131)
- Feeds: [OUT-036](#OUT-036), [OUT-074](#OUT-074), [INT-034](#INT-034)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 8; App F 12; tests: 1; 19

<a id="IN-097"></a>

#### IN-097 `need_total`: Scenario need total

Scenario's need total; Baseline reads Inputs. A departure from the configured need total is a fixed dollar amount added to need aid.

- Client label: "need_total"
- Excel: Levers!A12 row, one column per scenario
- Unit: USD; dimensions: scenario
- Formula: input
- Fed by: [IN-032](#IN-032), [IN-132](#IN-132)
- Feeds: [LG-005](#LG-005), [OUT-074](#OUT-074)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 7; R4-07; tests: 1; 19

<a id="IN-098"></a>

#### IN-098 `class_target`: Scenario class target

Class target for the scenario; Baseline reads Inputs. Feeds the band probability, break-evens and the class Checks rows. Echoed on Summary row 'Class target'.

- Client label: "class_target"
- Excel: Levers!A13 row, one column per scenario; echoed on Summary main block row 'Class target'
- Unit: count; dimensions: scenario
- Formula: input
- Fed by: [IN-027](#IN-027)
- Feeds: [OUT-012](#OUT-012), [OUT-074](#OUT-074), [OUT-097](#OUT-097), [OUT-111](#OUT-111), [CK-026](#CK-026), [CK-027](#CK-027), [CK-028](#CK-028)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; tests: 8; 16; 24

<a id="IN-099"></a>

#### IN-099 `class_cap`: Scenario class cap

Hard cap for the scenario; Baseline reads Inputs. Feeds P(class above cap) and the class-size table rows above the cap. Echoed on Summary row 'Class cap'.

- Client label: "class_cap"
- Excel: Levers!A14 row, one column per scenario; echoed on Summary main block row 'Class cap'
- Unit: count; dimensions: scenario
- Formula: input
- Fed by: [IN-026](#IN-026)
- Feeds: [OUT-011](#OUT-011), [OUT-074](#OUT-074), [CK-026](#CK-026), [CK-027](#CK-027)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; tests: 16; 19

<a id="IN-100"></a>

#### IN-100 `bonus_usd`: Incentive amount

Additional award dollars for eligible cells, capped at tuition. Creates the incentive column.

- Client label: "bonus_usd"
- Excel: Levers!A15 row, one column per scenario
- Unit: USD; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [LG-030](#LG-030), [LG-038](#LG-038), [CK-035](#CK-035)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 4; tests: 1; 12; 13

<a id="IN-101"></a>

#### IN-101 `bonus_scope`: Incentive scope

residency_out, segment or none: which cells are eligible for the incentive.

- Client label: "bonus_scope"
- Excel: Levers!A16 row, one column per scenario
- Unit: text; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [LG-024](#LG-024), [CK-035](#CK-035)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 4; tests: 12

<a id="IN-102"></a>

#### IN-102 `bonus_min_score`: Incentive minimum score

Optional score below which cells are not eligible; unscored cells are not eligible when it is set.

- Client label: "bonus_min_score (blank = none)"
- Excel: Levers!A17 row, one column per scenario
- Unit: score; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [LG-024](#LG-024)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 4; tests: 12

<a id="IN-103"></a>

#### IN-103 `bonus_pool_usd`: Incentive dollar pool

Optional dollar pool. Only the informational 'bonus implied by a dollar pool' row reads it.

- Client label: "bonus_pool_usd (dollar pool, informational; blank = none)"
- Excel: Levers!A18 row, one column per scenario
- Unit: USD; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [OUT-075](#OUT-075)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: display only
- References: spec 3 incentive block; tests: 19

<a id="IN-104"></a>

#### IN-104 `segment`: Active segment

Segment active in the scenario; blank means the only configured segment. Sets which cells are in segment.

- Client label: "segment (active; blank = the only configured segment)"
- Excel: Levers!A19 row, one column per scenario
- Unit: text; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [LG-006](#LG-006), [OUT-074](#OUT-074), [CK-036](#CK-036), [CK-041](#CK-041)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; tests: 13; 17

<a id="IN-105"></a>

#### IN-105 `segment_pool_lift_pct`: Segment application lift

Percent lift in segment applications at all scores, after the pool multiplier.

- Client label: "segment_pool_lift_pct"
- Excel: Levers!A20 row, one column per scenario
- Unit: percent; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [LG-025](#LG-025), [LG-039](#LG-039), [OUT-074](#OUT-074), [CK-035](#CK-035)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 2; tests: 1; 19

<a id="IN-106"></a>

#### IN-106 `segment_goal`: Segment goal

Optional goal for segment enrolled, rounded up; feeds P(segment enrolled at or above goal).

- Client label: "segment_goal (blank = none)"
- Excel: Levers!A21 row, one column per scenario
- Unit: count; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [OUT-060](#OUT-060), [OUT-063](#OUT-063), [CK-035](#CK-035)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 segment block; tests: 13

<a id="IN-107"></a>

#### IN-107 `yield_shift_pts`: Yield shift

Independent yield shift in points for every cell, unless an override applies.

- Client label: "yield_shift_pts"
- Excel: Levers!A22 row, one column per scenario
- Unit: points; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [LG-031](#LG-031), [OUT-074](#OUT-074)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 5; tests: 1; 8

<a id="IN-108"></a>

#### IN-108 `yield_shift_pts_in`: Yield shift, in-state

Replaces the global shift for in-state cells when set.

- Client label: "yield_shift_pts_in (blank inherits)"
- Excel: Levers!A23 row, one column per scenario
- Unit: points; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [LG-031](#LG-031), [OUT-074](#OUT-074)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 5; tests: 3; 8

<a id="IN-109"></a>

#### IN-109 `yield_shift_pts_out`: Yield shift, out-of-state

Replaces the global shift for out-of-state cells when set.

- Client label: "yield_shift_pts_out (blank inherits)"
- Excel: Levers!A24 row, one column per scenario
- Unit: points; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [LG-031](#LG-031), [OUT-074](#OUT-074)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 5; tests: 3; 8

<a id="IN-110"></a>

#### IN-110 `yield_shift_pts_segment`: Yield shift, segment

Replaces any other shift for segment cells when set.

- Client label: "yield_shift_pts_segment (blank inherits)"
- Excel: Levers!A25 row, one column per scenario
- Unit: points; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [LG-031](#LG-031), [OUT-074](#OUT-074)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 item 5; tests: 8; 19

<a id="IN-111"></a>

#### IN-111 `discount_target`: Scenario discount target

Optional discount-rate target for the scenario; Baseline reads Inputs. Echoed on Summary row 'Discount target'.

- Client label: "discount_target (blank = none)"
- Excel: Levers!A26 row, one column per scenario; echoed on Summary main block row 'Discount target'
- Unit: ratio; dimensions: scenario
- Formula: input
- Fed by: [IN-037](#IN-037)
- Feeds: [OUT-050](#OUT-050)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3 discount row; tests: 19

<a id="IN-112"></a>

#### IN-112 `admit_rate`: Admit rate (lever)

Per-cell admit rate. Baseline takes the latest cohort's; a child inherits by formula unless overridden (scenario file: overrides.admit_rate). Multiplies applications into admits.

- Client label: "admit_rate"
- Excel: Levers column 'admit_rate' (G, K, O, ...) from row 33
- Unit: rate; dimensions: scenario x cell
- Formula: input
- Fed by: none
- Feeds: [LG-026](#LG-026), [OUT-074](#OUT-074), [OUT-133](#OUT-133), [OUT-134](#OUT-134), [CK-046](#CK-046)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 3 item 3; App F 3; tests: 1; 8; 14

<a id="IN-113"></a>

#### IN-113 `award_usd`: Award (lever)

Per-cell lever award in dollars. Baseline takes the latest cohort's; a child inherits unless overridden (overrides.award_usd). Ignored while the full-tuition flag is set.

- Client label: "award_usd"
- Excel: Levers column 'award_usd' (H, L, P, ...) from row 33
- Unit: USD; dimensions: scenario x cell
- Formula: input
- Fed by: none
- Feeds: [LG-028](#LG-028), [LG-038](#LG-038), [OUT-074](#OUT-074), [OUT-084](#OUT-084), [OUT-132](#OUT-132), [OUT-134](#OUT-134), [OUT-135](#OUT-135), [CK-045](#CK-045)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 3 item 4; tests: 1; 18; 19

<a id="IN-114"></a>

#### IN-114 `full_tuition`: Full-tuition flag

Per-cell flag: while set the award equals the scenario tuition. Baseline sets it where the latest award is at or above base-cycle tuition; overrides.full_tuition changes it.

- Client label: "full_tuition (1/0)"
- Excel: Levers column 'full_tuition (1/0)' (I, M, Q, ...) from row 33
- Unit: flag; dimensions: scenario x cell
- Formula: input
- Fed by: none
- Feeds: [LG-028](#LG-028), [LG-038](#LG-038), [OUT-074](#OUT-074), [OUT-084](#OUT-084), [OUT-132](#OUT-132), [OUT-134](#OUT-134), [OUT-135](#OUT-135), [CK-045](#CK-045)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2; spec 3 item 4; tests: 1; 18; 19

<a id="layer-input-data"></a>

## Inputs: cell data

Columns of the cell data (cells.csv).

<a id="IN-115"></a>

#### IN-115 `cell_id`: Cell identifier

Unique id of a cell (residency, segment, score band, GPA class). Keys every per-cell row and the scenario overrides.

- Client label: "cell_id"
- Excel: History!A (and every per-cell sheet, column A)
- Unit: text; dimensions: cell
- Formula: input
- Fed by: none
- Feeds: [LG-007](#LG-007)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2 cell data; App F 1 to 5; MR 3.1; sw/cells.py COLUMNS; tests: 1; 3; 11

<a id="IN-116"></a>

#### IN-116 `residency`: Residency

in or out, from the permanent address at application. Sets incentive scope, the residency totals and shift overrides.

- Client label: "residency"
- Excel: History!B
- Unit: text; dimensions: cell
- Formula: input
- Fed by: none
- Feeds: [LG-008](#LG-008), [INT-007](#INT-007), [INT-008](#INT-008), [INT-009](#INT-009), [INT-010](#INT-010), [OUT-140](#OUT-140), [INT-052](#INT-052), [CK-034](#CK-034)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2 cell data; App F 1 to 5; MR 3.1; sw/cells.py COLUMNS; tests: 1; 3; 11

<a id="IN-117"></a>

#### IN-117 `segment`: Cell segment

Blank or the name of a configured segment within its residency. Marks segment membership.

- Client label: "segment"
- Excel: History!C
- Unit: text; dimensions: cell
- Formula: input
- Fed by: none
- Feeds: [LG-009](#LG-009), [INT-007](#INT-007), [INT-008](#INT-008), [INT-009](#INT-009), [INT-010](#INT-010), [OUT-140](#OUT-140), [CK-034](#CK-034)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2 cell data; App F 1 to 5; MR 3.1; sw/cells.py COLUMNS; tests: 1; 3; 11

<a id="IN-118"></a>

#### IN-118 `score_lo`: Score band lower bound

Lower bound of the cell's score band; blank for unscored applicants. Sets score group, signs, trim order and positions.

- Client label: "score_lo (blank = unscored)"
- Excel: History!D
- Unit: score; dimensions: cell
- Formula: input
- Fed by: none
- Feeds: [LG-010](#LG-010), [LG-012](#LG-012), [LG-014](#LG-014), [LG-015](#LG-015), [INT-001](#INT-001), [OUT-142](#OUT-142), [OUT-143](#OUT-143), [OUT-144](#OUT-144), [OUT-145](#OUT-145), [OUT-146](#OUT-146), [OUT-147](#OUT-147), [INT-052](#INT-052), [INT-060](#INT-060)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2 cell data; App F 1 to 5; MR 3.1; sw/cells.py COLUMNS; tests: 1; 3; 11

<a id="IN-119"></a>

#### IN-119 `gpa_class`: GPA class

hi, lo or blank. Sets the GPA sign, cell order and trim order.

- Client label: "gpa_class"
- Excel: History!F
- Unit: text; dimensions: cell
- Formula: input
- Fed by: none
- Feeds: [LG-011](#LG-011), [LG-014](#LG-014), [OUT-142](#OUT-142), [OUT-143](#OUT-143), [OUT-144](#OUT-144), [OUT-148](#OUT-148), [OUT-149](#OUT-149), [OUT-150](#OUT-150), [INT-052](#INT-052), [INT-060](#INT-060)
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2 cell data; App F 1 to 5; MR 3.1; sw/cells.py COLUMNS; tests: 1; 3; 11

<a id="IN-120"></a>

#### IN-120 `cohort`: Cohort

Entering cohort of the row's counts; one of the history cohorts.

- Client label: "cohort (year)"
- Excel: History panel column headers (one per history cohort)
- Unit: year; dimensions: cell x cohort
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 2 cell data; App F 1 to 5; MR 3.1; sw/cells.py COLUMNS; tests: 1; 3; 11

<a id="IN-121"></a>

#### IN-121 `apps`: Applications

Complete applications in the cell and cohort. Base-cycle applications start the ledger.

- Client label: "Applications"
- Excel: History panel 'Applications' (H:J)
- Unit: count; dimensions: cell x cohort
- Formula: input
- Fed by: none
- Feeds: [LG-022](#LG-022), [OUT-137](#OUT-137), [OUT-140](#OUT-140)
- Role: input; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 2 cell data; App F 1 to 5; MR 3.1; sw/cells.py COLUMNS; tests: 1; 3; 11

<a id="IN-122"></a>

#### IN-122 `admits`: Admits

Offers of admission, waitlist admits included, counted in the cohort applied to. Give the latest admit rate and the pooling weights.

- Client label: "Admits"
- Excel: History panel 'Admits' (L:N)
- Unit: count; dimensions: cell x cohort
- Formula: input
- Fed by: none
- Feeds: [INT-002](#INT-002), [INT-006](#INT-006), [INT-007](#INT-007), [INT-008](#INT-008), [INT-009](#INT-009), [INT-010](#INT-010), [INT-016](#INT-016), [INT-017](#INT-017), [OUT-137](#OUT-137), [OUT-139](#OUT-139), [OUT-140](#OUT-140)
- Role: input; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 2 cell data; App F 1 to 5; MR 3.1; sw/cells.py COLUMNS; tests: 1; 3; 11

<a id="IN-123"></a>

#### IN-123 `award_usd`: Award (history)

Average award in dollars in the cell and cohort. The latest is Baseline's award and a0; history awards give the observed range and the admits-weighted award.

- Client label: "Award $"
- Excel: History panel 'Award $' (T:V)
- Unit: USD; dimensions: cell x cohort
- Formula: input
- Fed by: none
- Feeds: [INT-004](#INT-004), [INT-006](#INT-006), [INT-016](#INT-016), [INT-017](#INT-017), [OUT-138](#OUT-138), [OUT-140](#OUT-140), [CK-031](#CK-031)
- Role: input; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 2 cell data; App F 1 to 5; MR 3.1; sw/cells.py COLUMNS; tests: 1; 3; 11

<a id="IN-124"></a>

#### IN-124 `enrolled`: Enrolled (history)

Census enrollment in the cell and cohort. Gives the history yields that base yield pools.

- Client label: "Enrolled"
- Excel: History panel 'Enrolled' (AF:AH)
- Unit: count; dimensions: cell x cohort
- Formula: input
- Fed by: none
- Feeds: [INT-003](#INT-003), [INT-007](#INT-007), [INT-008](#INT-008), [INT-009](#INT-009), [INT-010](#INT-010), [OUT-139](#OUT-139), [OUT-140](#OUT-140), [OUT-142](#OUT-142), [OUT-143](#OUT-143), [OUT-144](#OUT-144), [OUT-145](#OUT-145), [OUT-146](#OUT-146), [OUT-147](#OUT-147), [OUT-148](#OUT-148), [OUT-149](#OUT-149), [OUT-150](#OUT-150), [CK-031](#CK-031)
- Role: input; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 2 cell data; App F 1 to 5; MR 3.1; sw/cells.py COLUMNS; tests: 1; 3; 11

<a id="layer-input-workbook"></a>

## Inputs: other workbook cells

Editable workbook cells that are not config keys or levers (the case selector and the Reproduce sheet).

<a id="IN-125"></a>

#### IN-125 `in_case_selector`: Case selector

Chooses which price-response case the Summary's 'Selected case' block shows. Display only.

- Client label: "case selector (Low, Middle, High)"
- Excel: Inputs!B99 (in_case_selector)
- Unit: text; dimensions: scalar
- Formula: input
- Fed by: none
- Feeds: [OUT-001](#OUT-001)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: display only
- References: spec 6 Inputs; tests: 3

<a id="IN-126"></a>

#### IN-126 `loaded.yield`: Loaded yield

Yield loaded from the validation file for each cell and scenario. With the mode at Reproduce every Ledger's yield reads it (no response, shift, floor or cap).

- Client label: "yield"
- Excel: Reproduce column 'yield' from row 13
- Unit: rate; dimensions: scenario x cell
- Formula: input
- Fed by: none
- Feeds: [LG-032](#LG-032)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: spec 9; spec 0A B; sw/reproduce.py loaded_specs, synthetic_loaded; tests: 3; 6

<a id="IN-127"></a>

#### IN-127 `loaded.tuition`: Loaded tuition

Plan-year tuition loaded from the validation file. With the mode at Reproduce the Ledger tuition reads it.

- Client label: "tuition (loaded, plan year)"
- Excel: Reproduce row 'tuition (loaded, plan year)'
- Unit: USD; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [LG-002](#LG-002), [CK-047](#CK-047)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: spec 9; spec 0A B; sw/reproduce.py loaded_specs, synthetic_loaded; tests: 3; 6

<a id="IN-128"></a>

#### IN-128 `loaded.admit_rate`: Loaded admit rate

Admit rate loaded from the validation file; Checks compares the Levers admit rates with it.

- Client label: "admit_rate"
- Excel: Reproduce column 'admit_rate' from row 13
- Unit: rate; dimensions: scenario x cell
- Formula: input
- Fed by: none
- Feeds: [CK-046](#CK-046)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: spec 9; spec 0A B; sw/reproduce.py loaded_specs, synthetic_loaded; tests: 3; 6

<a id="IN-129"></a>

#### IN-129 `loaded.award_usd`: Loaded award

Award loaded from the validation file; Checks compares the resolved Middle awards with it.

- Client label: "award_usd"
- Excel: Reproduce column 'award_usd' from row 13
- Unit: USD; dimensions: scenario x cell
- Formula: input
- Fed by: none
- Feeds: [CK-046](#CK-046)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: spec 9; spec 0A B; sw/reproduce.py loaded_specs, synthetic_loaded; tests: 3; 6

<a id="IN-130"></a>

#### IN-130 `loaded.pool_multiplier`: Loaded pool multiplier

Pool multiplier read from the scenario description; Checks compares the Levers value with it.

- Client label: "pool multiplier"
- Excel: Reproduce row 'pool multiplier'
- Unit: multiplier; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [IN-095](#IN-095), [CK-046](#CK-046)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: spec 9; spec 0A B; sw/reproduce.py loaded_specs, synthetic_loaded; tests: 3; 6

<a id="IN-131"></a>

#### IN-131 `loaded.specialty_usd`: Loaded specialty aid

Specialty lump sum read from the validation file; becomes the scenario's specialty aid.

- Client label: "specialty_usd"
- Excel: Reproduce row 'specialty_usd'
- Unit: USD; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [IN-096](#IN-096)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: spec 9; spec 0A B; sw/reproduce.py loaded_specs, synthetic_loaded; tests: 3; 6

<a id="IN-132"></a>

#### IN-132 `loaded.need_total`: Loaded need total

Need total from config less any departure the file's need row shows; becomes the scenario's need total.

- Client label: "need_total"
- Excel: Reproduce row 'need_total'
- Unit: USD; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [IN-097](#IN-097)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: spec 9; spec 0A B; sw/reproduce.py loaded_specs, synthetic_loaded; tests: 3; 6

<a id="IN-133"></a>

#### IN-133 `loaded.sources`: Loaded-value source notes

Where each loaded scenario value came from (description, inheritance, need rule).

- Client label: "source notes"
- Excel: Reproduce row 'source notes'
- Unit: text; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: spec 9; spec 0A B; sw/reproduce.py loaded_specs, synthetic_loaded; tests: 3; 6

<a id="IN-134"></a>

#### IN-134 `loaded.parent`: Loaded lineage

Parent scenario read from the description, or the previous scenario when none is named.

- Client label: "parent (loaded lineage)"
- Excel: Reproduce row 'parent (loaded lineage)'
- Unit: text; dimensions: scenario
- Formula: input
- Fed by: none
- Feeds: [IN-090](#IN-090)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: spec 9; spec 0A B; sw/reproduce.py loaded_specs, synthetic_loaded; tests: 3; 6

<a id="layer-ledger"></a>

## Ledger columns

Columns of Ledger_Low, Ledger_Middle and Ledger_High (one row per header; the three sheets share them).

<a id="LG-001"></a>

#### LG-001 `Scenario`: Scenario name (block header)

Name of the scenario whose columns follow, read from Levers.

- Client label: "Scenario"
- Excel: Ledger_Low/Middle/High row 3, first column of each scenario block
- Unit: text; dimensions: scenario x case
- Formula: = Levers scenario name
- Fed by: [IN-089](#IN-089)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3

<a id="LG-002"></a>

#### LG-002 `tuition`: Scenario tuition

First-year tuition T_s in the plan year. Caps every award, sets the full-tuition award and gross tuition, and enters the net tuition weight. Echoed on Summary row 'Tuition (plan year)'.

- Client label: "tuition"
- Excel: Ledger_Low/Middle/High row 4 of each scenario block; echoed on Summary main block row 'Tuition (plan year)'
- Unit: USD; dimensions: scenario
- Formula: round_to(tuition_base x (1 + p_s / 100), tuition_rounding_usd); reproduce mode: loaded tuition
- Fed by: [IN-009](#IN-009), [IN-093](#IN-093), [IN-012](#IN-012), [IN-127](#IN-127), [IN-070](#IN-070)
- Feeds: [LG-028](#LG-028), [LG-030](#LG-030), [LG-037](#LG-037), [INT-018](#INT-018), [OUT-029](#OUT-029), [OUT-032](#OUT-032), [OUT-083](#OUT-083), [OUT-131](#OUT-131), [CK-023](#CK-023)
- Role: primary; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 0; 1; 3; 21

<a id="LG-003"></a>

#### LG-003 `increase %`: Tuition increase (block copy)

The scenario's tuition increase, copied for the award scaling and the tuition formula.

- Client label: "increase %"
- Excel: Ledger_Low/Middle/High row 5 of each scenario block
- Unit: percent; dimensions: scenario
- Formula: = Levers tuition_increase_pct
- Fed by: [IN-093](#IN-093)
- Feeds: [LG-028](#LG-028), [OUT-085](#OUT-085)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3

<a id="LG-004"></a>

#### LG-004 `need rate`: Need rate per enrollee

Need aid per enrolled student; need aid scales with the class at this rate. Enters need aid and the net tuition weight.

- Client label: "need rate"
- Excel: Ledger_Low/Middle/High row 6 of each scenario block
- Unit: USD; dimensions: scenario
- Formula: need.total / need.reference_class (reproduce mode: rounded to whole dollars)
- Fed by: [IN-032](#IN-032), [IN-033](#IN-033), [IN-070](#IN-070)
- Feeds: [LG-037](#LG-037), [OUT-035](#OUT-035), [OUT-076](#OUT-076)
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3; 19

<a id="LG-005"></a>

#### LG-005 `need departure`: Need departure (fixed amount)

The scenario's need total minus the configured need total: a fixed dollar amount added to need aid, which does not scale with the class.

- Client label: "need departure"
- Excel: Ledger_Low/Middle/High row 6, third column of each scenario block
- Unit: USD; dimensions: scenario
- Formula: need_total_s - need.total (0 when blank)
- Fed by: [IN-097](#IN-097), [IN-032](#IN-032)
- Feeds: [OUT-035](#OUT-035), [INT-034](#INT-034)
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3; 19

<a id="LG-006"></a>

#### LG-006 `segment`: Active segment (block)

The scenario's active segment name; a blank lever means the only configured segment. The in-segment column compares each cell with it.

- Client label: "segment"
- Excel: Ledger_Low/Middle/High row 7 of each scenario block
- Unit: text; dimensions: scenario
- Formula: IF(Levers segment blank, first configured segment, lever)
- Fed by: [IN-104](#IN-104), [IN-061](#IN-061)
- Feeds: [LG-023](#LG-023), [OUT-052](#OUT-052)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3

<a id="LG-007"></a>

#### LG-007 `cell_id`: Cell identifier

Cell id, in cell order. Copied from the cell data; the per-cell formulas read it.

- Client label: "cell_id"
- Excel: Ledger_Low/Middle/High column A
- Unit: text; dimensions: cell
- Formula: copy of cell data
- Fed by: [IN-115](#IN-115)
- Feeds: none
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 3

<a id="LG-008"></a>

#### LG-008 `residency`: Residency

Cell residency. Copied from the cell data; the per-cell formulas read it.

- Client label: "residency"
- Excel: Ledger_Low/Middle/High column B
- Unit: text; dimensions: cell
- Formula: copy of cell data
- Fed by: [IN-116](#IN-116)
- Feeds: [LG-024](#LG-024), [LG-031](#LG-031), [OUT-003](#OUT-003), [OUT-004](#OUT-004), [OUT-006](#OUT-006), [OUT-007](#OUT-007)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 3

<a id="LG-009"></a>

#### LG-009 `segment`: Cell segment

Cell segment ('(none)' outside every segment). Copied from the cell data; the per-cell formulas read it.

- Client label: "segment"
- Excel: Ledger_Low/Middle/High column C
- Unit: text; dimensions: cell
- Formula: copy of cell data
- Fed by: [IN-117](#IN-117)
- Feeds: [LG-023](#LG-023)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 3

<a id="LG-010"></a>

#### LG-010 `score_lo (blank = unscored)`: Score band lower bound

Score band lower bound; blank when unscored. Copied from the cell data; the per-cell formulas read it.

- Client label: "score_lo (blank = unscored)"
- Excel: Ledger_Low/Middle/High column D
- Unit: score; dimensions: cell
- Formula: copy of cell data
- Fed by: [IN-118](#IN-118)
- Feeds: [LG-024](#LG-024), [OUT-013](#OUT-013), [OUT-015](#OUT-015), [OUT-027](#OUT-027)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 3

<a id="LG-011"></a>

#### LG-011 `gpa_class`: GPA class

GPA class (hi, lo, blank). Copied from the cell data; the per-cell formulas read it.

- Client label: "gpa_class"
- Excel: Ledger_Low/Middle/High column F
- Unit: text; dimensions: cell
- Formula: copy of cell data
- Fed by: [IN-119](#IN-119)
- Feeds: [OUT-016](#OUT-016), [OUT-018](#OUT-018)
- Role: input; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 3

<a id="LG-012"></a>

#### LG-012 `scored (1/0)`: Scored flag

1 when the cell has a score band, 0 when unscored. Unscored cells take sign 0 or -1 by the counting rule and are counted separately.

- Client label: "scored (1/0)"
- Excel: Ledger_Low/Middle/High column E
- Unit: flag; dimensions: cell
- Formula: 1 if score_lo given, else 0
- Fed by: [IN-118](#IN-118)
- Feeds: [OUT-013](#OUT-013), [OUT-014](#OUT-014), [OUT-017](#OUT-017), [OUT-027](#OUT-027)
- Role: internal; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 3; 22

<a id="LG-013"></a>

#### LG-013 `upper group (1/0)`: Upper score group flag

1 when the cell is at or above the pool threshold. Applies the pool multiplier and splits the pool strip.

- Client label: "upper group (1/0)"
- Excel: Ledger_Low/Middle/High column G
- Unit: flag; dimensions: cell
- Formula: score_lo >= score.pool_threshold (unscored: 0)
- Fed by: [INT-001](#INT-001)
- Feeds: [LG-025](#LG-025), [INT-042](#INT-042), [INT-043](#INT-043), [INT-044](#INT-044), [INT-045](#INT-045), [INT-046](#INT-046), [INT-047](#INT-047), [INT-048](#INT-048), [INT-049](#INT-049)
- Role: internal; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3; 15

<a id="LG-014"></a>

#### LG-014 `median sign {measure} {t}`: Median sign

Sign g of the cell for one median target: +1 at or above t, -1 below, 0 (or -1 under 'below') for unscored or blank-GPA cells. Every median margin and probability is a SUMPRODUCT over it.

- Client label: "median sign {measure} {t}"
- Excel: Ledger_Low/Middle/High columns H onward, one per median target (score thresholds, then the GPA median)
- Unit: flag; dimensions: cell x target
- Formula: score: +1 if score_lo >= t, -1 if below; GPA: +1 hi, -1 lo; unscored or blank: 0 (excluded) or -1 (below)
- Fed by: [IN-118](#IN-118), [IN-119](#IN-119), [IN-020](#IN-020), [IN-024](#IN-024), [IN-025](#IN-025), [IN-023](#IN-023), [IN-073](#IN-073)
- Feeds: [OUT-019](#OUT-019), [OUT-020](#OUT-020), [OUT-021](#OUT-021), [INT-028](#INT-028), [INT-029](#INT-029), [INT-046](#INT-046), [INT-047](#INT-047), [INT-048](#INT-048)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 5; sw/risk.py median_signs; tests: 2; 3; 22

<a id="LG-015"></a>

#### LG-015 `percentile sign q {q}, t {t}`: Percentile sign

Sign of the cell for one percentile target, as for the median at that target's t. Weighted q and -(1 - q) in the percentile margin and probability.

- Client label: "percentile sign q {q}, t {t}"
- Excel: Ledger_Low/Middle/High columns after the median signs, one per percentile target
- Unit: flag; dimensions: cell x target
- Formula: +1 if score_lo >= t, -1 if below, unscored 0
- Fed by: [IN-118](#IN-118), [IN-019](#IN-019), [IN-025](#IN-025)
- Feeds: [OUT-022](#OUT-022), [OUT-023](#OUT-023), [OUT-024](#OUT-024), [INT-028](#INT-028), [INT-029](#INT-029), [INT-046](#INT-046), [INT-047](#INT-047), [INT-048](#INT-048), [INT-049](#INT-049)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 0A A1; sw/risk.py median_signs; tests: 3; 22

<a id="LG-016"></a>

#### LG-016 `yield floor`: Yield floor (cell)

The cell's yield floor (upper or lower group value). The yield column clips at it.

- Client label: "yield floor"
- Excel: Ledger_Low/Middle/High column after the signs
- Unit: rate; dimensions: cell
- Formula: = Response yield floor
- Fed by: [INT-014](#INT-014)
- Feeds: [LG-032](#LG-032), [OUT-096](#OUT-096)
- Role: internal; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3

<a id="LG-017"></a>

#### LG-017 `yield cap`: Yield cap (cell)

The cell's yield cap (upper or lower group value). The yield column clips at it; the yield strip counts cells where it would bind.

- Client label: "yield cap"
- Excel: Ledger_Low/Middle/High column after yield floor
- Unit: rate; dimensions: cell
- Formula: = Response yield cap
- Fed by: [INT-015](#INT-015)
- Feeds: [LG-032](#LG-032), [OUT-096](#OUT-096)
- Role: internal; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3

<a id="LG-018"></a>

#### LG-018 `a0`: Base award (a0)

The cell's latest-cohort award, the point at which base yield is centered. The yield formula measures award changes from it.

- Client label: "a0"
- Excel: Ledger_Low/Middle/High column after yield cap
- Unit: USD; dimensions: cell
- Formula: = Response a0
- Fed by: [INT-004](#INT-004)
- Feeds: [LG-032](#LG-032)
- Role: internal; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3

<a id="LG-019"></a>

#### LG-019 `y0 {case}`: Base yield (case)

The cell's base yield for the sheet's case, from partial pooling. Starting point of the yield formula.

- Client label: "y0 {case}"
- Excel: Ledger_Low/Middle/High column after a0
- Unit: rate; dimensions: cell x case
- Formula: = Response y0 for the case
- Fed by: [INT-013](#INT-013)
- Feeds: [LG-032](#LG-032)
- Role: internal; response: Y; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3

<a id="LG-020"></a>

#### LG-020 `award low (observed)`: Observed award low

Lowest history award in the cell (cohorts with admits). Lower end of the observed range for the evidence label.

- Client label: "award low (observed)"
- Excel: Ledger_Low/Middle/High column after y0
- Unit: USD; dimensions: cell
- Formula: = Response observed award low
- Fed by: [INT-016](#INT-016)
- Feeds: [LG-033](#LG-033)
- Role: internal; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3

<a id="LG-021"></a>

#### LG-021 `award high (observed)`: Observed award high

Highest history award in the cell. Upper end of the observed range for the evidence label.

- Client label: "award high (observed)"
- Excel: Ledger_Low/Middle/High column after award low
- Unit: USD; dimensions: cell
- Formula: = Response observed award high
- Fed by: [INT-017](#INT-017)
- Feeds: [LG-033](#LG-033)
- Role: internal; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3

<a id="LG-022"></a>

#### LG-022 `applications (base cycle)`: Base-cycle applications

The cell's applications in the base cycle; the start of every scenario's applications.

- Client label: "applications (base cycle)"
- Excel: Ledger_Low/Middle/High column U
- Unit: count; dimensions: cell
- Formula: = History applications at base_cycle
- Fed by: [IN-121](#IN-121), [IN-005](#IN-005)
- Feeds: [LG-025](#LG-025), [LG-039](#LG-039)
- Role: input; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3

<a id="LG-023"></a>

#### LG-023 `in segment`: In active segment

1 when the cell belongs to the scenario's active segment. Applies the segment lift, segment incentive scope and segment shift, and selects the segment block's cells.

- Client label: "in segment"
- Excel: Ledger_Low/Middle/High block column 1
- Unit: flag; dimensions: scenario x cell
- Formula: 1 if cell segment = active segment
- Fed by: [LG-009](#LG-009), [LG-006](#LG-006)
- Feeds: [LG-024](#LG-024), [LG-025](#LG-025), [LG-031](#LG-031), [LG-039](#LG-039), [OUT-053](#OUT-053), [OUT-054](#OUT-054), [OUT-055](#OUT-055), [OUT-057](#OUT-057), [OUT-058](#OUT-058), [OUT-059](#OUT-059), [OUT-061](#OUT-061), [OUT-062](#OUT-062), [OUT-063](#OUT-063), [INT-036](#INT-036), [INT-052](#INT-052), [CK-035](#CK-035)
- Role: internal; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3; 11; 17

<a id="LG-024"></a>

#### LG-024 `incentive eligible`: Incentive eligible

1 when the cell is in the incentive's scope and meets the minimum score. Only eligible cells receive the incentive.

- Client label: "incentive eligible"
- Excel: Ledger_Low/Middle/High block column 2
- Unit: flag; dimensions: scenario x cell
- Formula: in scope (out-of-state, segment or none) x (score_lo >= bonus_min_score when set)
- Fed by: [IN-101](#IN-101), [IN-102](#IN-102), [LG-008](#LG-008), [LG-023](#LG-023), [LG-010](#LG-010)
- Feeds: [LG-030](#LG-030), [LG-038](#LG-038), [OUT-075](#OUT-075)
- Role: internal; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3; 12

<a id="LG-025"></a>

#### LG-025 `applications`: Applications (scenario)

Scenario applications: base applications times the pool multiplier for upper-group cells, times the segment lift for segment cells. Multiplied by the admit rate to give admits.

- Client label: "applications"
- Excel: Ledger_Low/Middle/High block column 3
- Unit: count; dimensions: scenario x cell
- Formula: apps_base x (pool_multiplier if upper) x (1 + segment_pool_lift_pct / 100 x in_seg); reproduce: rounded when round_apps_after_pool
- Fed by: [LG-022](#LG-022), [LG-013](#LG-013), [IN-095](#IN-095), [IN-105](#IN-105), [LG-023](#LG-023), [IN-074](#IN-074)
- Feeds: [LG-027](#LG-027), [LG-040](#LG-040), [OUT-002](#OUT-002), [OUT-003](#OUT-003), [OUT-004](#OUT-004), [OUT-053](#OUT-053), [INT-057](#INT-057), [CK-021](#CK-021)
- Role: primary; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3; 6; 19

<a id="LG-026"></a>

#### LG-026 `admit rate`: Admit rate (scenario)

The scenario's admit rate for the cell, read from Levers.

- Client label: "admit rate"
- Excel: Ledger_Low/Middle/High block column 4
- Unit: rate; dimensions: scenario x cell
- Formula: = Levers admit_rate
- Fed by: [IN-112](#IN-112)
- Feeds: [LG-027](#LG-027), [LG-039](#LG-039), [INT-053](#INT-053), [INT-057](#INT-057)
- Role: input; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3

<a id="LG-027"></a>

#### LG-027 `admits`: Admits (scenario)

Applications times admit rate (rounded when integer admits are set). Multiplied by yield to give expected enrolled; the yield strip and shrink path work on it.

- Client label: "admits"
- Excel: Ledger_Low/Middle/High block column 5
- Unit: count; dimensions: scenario x cell
- Formula: applications x admit rate (ROUND when integer_admits)
- Fed by: [LG-025](#LG-025), [LG-026](#LG-026), [IN-056](#IN-056)
- Feeds: [LG-034](#LG-034), [LG-040](#LG-040), [OUT-005](#OUT-005), [OUT-006](#OUT-006), [OUT-007](#OUT-007), [OUT-009](#OUT-009), [OUT-010](#OUT-010), [OUT-020](#OUT-020), [OUT-021](#OUT-021), [OUT-023](#OUT-023), [OUT-024](#OUT-024), [OUT-054](#OUT-054), [OUT-087](#OUT-087), [OUT-096](#OUT-096), [OUT-097](#OUT-097), [OUT-098](#OUT-098), [INT-025](#INT-025), [INT-037](#INT-037), [INT-053](#INT-053), [CK-021](#CK-021), [CK-022](#CK-022)
- Role: primary; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3; 6

<a id="LG-028"></a>

#### LG-028 `award base`: Award before incentive

Award before any incentive: tuition on a full-tuition cell, otherwise the lever award (scaled by 1 + p when awards scale), capped at tuition.

- Client label: "award base"
- Excel: Ledger_Low/Middle/High block column 6
- Unit: USD; dimensions: scenario x cell
- Formula: IF(full_tuition, T_s, MIN(award_usd x (1 + p if scaled), T_s))
- Fed by: [IN-113](#IN-113), [IN-114](#IN-114), [IN-094](#IN-094), [LG-002](#LG-002), [LG-003](#LG-003)
- Feeds: [LG-029](#LG-029), [LG-030](#LG-030)
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3; 19

<a id="LG-029"></a>

#### LG-029 `incentive`: Incentive (per enrollee)

Award after incentive minus award before it: the incentive actually paid per enrollee, less than the bonus where the tuition cap binds. Feeds incentive cost and the incentive block.

- Client label: "incentive"
- Excel: Ledger_Low/Middle/High block column 7
- Unit: USD; dimensions: scenario x cell
- Formula: award - award base
- Fed by: [LG-030](#LG-030), [LG-028](#LG-028)
- Feeds: [LG-040](#LG-040), [OUT-034](#OUT-034), [OUT-065](#OUT-065), [OUT-067](#OUT-067), [OUT-068](#OUT-068), [OUT-069](#OUT-069), [OUT-073](#OUT-073)
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3; 13; 19

<a id="LG-030"></a>

#### LG-030 `award`: Award (resolved)

The award the cell's students receive: award before incentive plus the bonus where eligible, capped at tuition. Feeds yield, merit, the net tuition weight and the award matrix.

- Client label: "award"
- Excel: Ledger_Low/Middle/High block column 8
- Unit: USD; dimensions: scenario x cell
- Formula: MIN(award base + bonus_usd x eligible, T_s)
- Fed by: [LG-028](#LG-028), [IN-100](#IN-100), [LG-024](#LG-024), [LG-002](#LG-002)
- Feeds: [LG-029](#LG-029), [LG-032](#LG-032), [LG-033](#LG-033), [LG-036](#LG-036), [LG-037](#LG-037), [OUT-029](#OUT-029), [OUT-030](#OUT-030), [OUT-057](#OUT-057), [OUT-065](#OUT-065), [OUT-067](#OUT-067), [OUT-068](#OUT-068), [OUT-069](#OUT-069), [OUT-136](#OUT-136), [OUT-154](#OUT-154), [CK-023](#CK-023), [CK-046](#CK-046)
- Role: primary; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3; 9; 19

<a id="LG-031"></a>

#### LG-031 `yield shift (pts)`: Yield shift applied

The yield shift that applies to the cell: segment override, else residency override, else the global shift. Overrides replace, not add.

- Client label: "yield shift (pts)"
- Excel: Ledger_Low/Middle/High block column 9
- Unit: points; dimensions: scenario x cell
- Formula: IF(in_seg and segment override set, segment, IF(residency override set, residency, global))
- Fed by: [IN-107](#IN-107), [IN-108](#IN-108), [IN-109](#IN-109), [IN-110](#IN-110), [LG-023](#LG-023), [LG-008](#LG-008)
- Feeds: [LG-032](#LG-032)
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3; 8

<a id="LG-032"></a>

#### LG-032 `yield`: Yield

Enrollment probability per admit: base yield moved along the placeholder slope by the award change, clipped, shifted, clipped again. In reproduce mode, the loaded yield. Feeds expected enrolled and every variance.

- Client label: "yield"
- Excel: Ledger_Low/Middle/High block column 10
- Unit: rate; dimensions: scenario x case x cell
- Formula: clip(clip(y0 + b/100 x (award - a0)/1000, floor, cap) + shift/100, floor, cap)
- Fed by: [LG-019](#LG-019), [IN-044](#IN-044), [IN-045](#IN-045), [IN-046](#IN-046), [LG-030](#LG-030), [LG-018](#LG-018), [LG-031](#LG-031), [LG-016](#LG-016), [LG-017](#LG-017), [IN-126](#IN-126), [IN-070](#IN-070)
- Feeds: [LG-034](#LG-034), [OUT-009](#OUT-009), [OUT-010](#OUT-010), [OUT-020](#OUT-020), [OUT-021](#OUT-021), [OUT-023](#OUT-023), [OUT-024](#OUT-024), [OUT-087](#OUT-087), [OUT-096](#OUT-096), [OUT-097](#OUT-097), [OUT-098](#OUT-098), [INT-025](#INT-025), [INT-037](#INT-037), [INT-042](#INT-042), [INT-043](#INT-043), [INT-044](#INT-044), [INT-045](#INT-045), [INT-046](#INT-046), [INT-047](#INT-047), [INT-048](#INT-048), [INT-049](#INT-049), [INT-053](#INT-053), [CK-024](#CK-024)
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 item 5; spec 4; MR 4.4, 5.2; sw/response.py yield_at; tests: 1; 3; 6; 19

<a id="LG-033"></a>

#### LG-033 `evidence`: Evidence label (cell)

observed when the award lies within the cell's observed award range plus the tolerance, else extrapolated. Describes how well the yield is known, never the award. Feeds the extrapolated share.

- Client label: "evidence"
- Excel: Ledger_Low/Middle/High block column 11
- Unit: text; dimensions: scenario x cell
- Formula: observed if award_lo - tol <= award <= award_hi + tol, else extrapolated
- Fed by: [LG-030](#LG-030), [LG-020](#LG-020), [LG-021](#LG-021), [IN-058](#IN-058)
- Feeds: [OUT-051](#OUT-051)
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 4; App F 24; sw/response.py evidence_labels; tests: 3; 19

<a id="LG-034"></a>

#### LG-034 `expected enrolled`: Expected enrolled (mu)

Admits times yield, unrounded: mu_c. Sums to the expected class; every closed-form mean and variance reads it.

- Client label: "expected enrolled"
- Excel: Ledger_Low/Middle/High block column 12
- Unit: count; dimensions: scenario x case x cell
- Formula: mu = admits x yield
- Fed by: [LG-027](#LG-027), [LG-032](#LG-032)
- Feeds: [LG-035](#LG-035), [LG-040](#LG-040), [OUT-008](#OUT-008), [OUT-009](#OUT-009), [OUT-010](#OUT-010), [OUT-020](#OUT-020), [OUT-021](#OUT-021), [OUT-023](#OUT-023), [OUT-024](#OUT-024), [OUT-039](#OUT-039), [OUT-040](#OUT-040), [OUT-043](#OUT-043), [OUT-051](#OUT-051), [OUT-058](#OUT-058), [OUT-059](#OUT-059), [OUT-061](#OUT-061), [OUT-063](#OUT-063), [OUT-115](#OUT-115), [INT-026](#INT-026), [INT-028](#INT-028), [INT-029](#INT-029), [INT-035](#INT-035), [INT-036](#INT-036), [INT-055](#INT-055)
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 item 6; spec 5; MR 3.2; tests: 1; 2; 3

<a id="LG-035"></a>

#### LG-035 `enrolled`: Enrolled

Expected enrolled, rounded when integer enrolled is set. Counts, money, margins and shares read it.

- Client label: "enrolled"
- Excel: Ledger_Low/Middle/High block column 13
- Unit: count; dimensions: scenario x case x cell
- Formula: mu (ROUND when integer_enrolled)
- Fed by: [LG-034](#LG-034), [IN-057](#IN-057)
- Feeds: [LG-036](#LG-036), [LG-040](#LG-040), [OUT-013](#OUT-013), [OUT-014](#OUT-014), [OUT-015](#OUT-015), [OUT-016](#OUT-016), [OUT-017](#OUT-017), [OUT-018](#OUT-018), [OUT-019](#OUT-019), [OUT-022](#OUT-022), [OUT-027](#OUT-027), [OUT-029](#OUT-029), [OUT-030](#OUT-030), [OUT-031](#OUT-031), [OUT-032](#OUT-032), [OUT-034](#OUT-034), [OUT-035](#OUT-035), [OUT-048](#OUT-048), [OUT-055](#OUT-055), [OUT-056](#OUT-056), [OUT-057](#OUT-057), [OUT-065](#OUT-065), [OUT-067](#OUT-067), [OUT-068](#OUT-068), [OUT-069](#OUT-069), [OUT-075](#OUT-075), [OUT-076](#OUT-076), [OUT-084](#OUT-084), [INT-060](#INT-060), [INT-062](#INT-062), [CK-020](#CK-020), [CK-022](#CK-022)
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3; 6

<a id="LG-036"></a>

#### LG-036 `merit $`: Merit dollars (cell)

Enrolled times award: merit dollars in the cell. Sums to merit.

- Client label: "merit $"
- Excel: Ledger_Low/Middle/High block column 14
- Unit: USD; dimensions: scenario x case x cell
- Formula: enrolled x award
- Fed by: [LG-035](#LG-035), [LG-030](#LG-030)
- Feeds: [LG-040](#LG-040), [OUT-033](#OUT-033), [OUT-152](#OUT-152), [INT-060](#INT-060)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 1; 3

<a id="LG-037"></a>

#### LG-037 `net tuition weight`: Net tuition weight (w)

Net dollars per enrollee in the cell: tuition minus award minus the need rate. The NTR mean and variance, the incentive's NTR change and the pool strip's NTR read it.

- Client label: "net tuition weight"
- Excel: Ledger_Low/Middle/High block column 15
- Unit: USD; dimensions: scenario x cell
- Formula: w_c = T_s - award - need_rate
- Fed by: [LG-002](#LG-002), [LG-030](#LG-030), [LG-004](#LG-004)
- Feeds: [OUT-039](#OUT-039), [OUT-040](#OUT-040), [OUT-043](#OUT-043), [OUT-065](#OUT-065), [OUT-067](#OUT-067), [OUT-068](#OUT-068), [OUT-069](#OUT-069), [OUT-087](#OUT-087), [OUT-098](#OUT-098), [INT-035](#INT-035), [INT-044](#INT-044), [INT-045](#INT-045)
- Role: internal; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 5 NTR; MR 6.5; tests: 1; 3; 19

<a id="LG-038"></a>

#### LG-038 `award at T(p)`: Award at what-if tuition

The award recomputed at tuition T(p) for each tuition grid value under the scenario's award rule. Feeds the tuition what-if.

- Client label: "award at T(p)"
- Excel: Ledger_Middle block columns after net tuition weight, one per tuition grid value (rows 4 and 5 hold T(p) and p)
- Unit: USD; dimensions: scenario x cell x grid value
- Formula: MIN(IF(full_tuition, T(p), MIN(award_usd x (1 + p if scaled), T(p))) + bonus x eligible, T(p))
- Fed by: [IN-113](#IN-113), [IN-114](#IN-114), [IN-094](#IN-094), [IN-053](#IN-053), [IN-100](#IN-100), [LG-024](#LG-024), [IN-009](#IN-009), [IN-012](#IN-012)
- Feeds: [OUT-076](#OUT-076)
- Role: internal; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 tuition what-if; sw/strip.py tuition; tests: 3; 15; 19

<a id="LG-039"></a>

#### LG-039 `admits at pool multiplier 1`: Admits at pool multiplier 1

Admits with every lever applied except the pool multiplier, which is set to 1. The pool strip splits these into below- and above-threshold parts.

- Client label: "admits at pool multiplier 1"
- Excel: Ledger_Middle block, last column
- Unit: count; dimensions: scenario x cell
- Formula: apps_base x (1 + lift x in_seg) x admit rate
- Fed by: [LG-022](#LG-022), [IN-105](#IN-105), [LG-023](#LG-023), [LG-026](#LG-026), [IN-056](#IN-056)
- Feeds: [INT-042](#INT-042), [INT-043](#INT-043), [INT-044](#INT-044), [INT-045](#INT-045), [INT-046](#INT-046), [INT-047](#INT-047), [INT-048](#INT-048), [INT-049](#INT-049)
- Role: internal; response: N; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 pool strip; sw/strip.py pool_strip; tests: 3; 15

<a id="LG-040"></a>

#### LG-040 `Total`: Ledger totals row

Sums of applications, admits, expected enrolled, enrolled and merit dollars, and the incentive cost, per scenario block. Checks compares it with the cell rows and the Summary.

- Client label: "Total"
- Excel: Ledger_Low/Middle/High totals row below the cells
- Unit: count; dimensions: scenario x case
- Formula: SUM over cells (incentive: SUMPRODUCT(enrolled, incentive))
- Fed by: [LG-025](#LG-025), [LG-027](#LG-027), [LG-034](#LG-034), [LG-035](#LG-035), [LG-036](#LG-036), [LG-029](#LG-029)
- Feeds: [CK-020](#CK-020), [CK-033](#CK-033)
- Role: derived; response: Y; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3; MR 4; sw/ledger.py evaluate; sw/workbook.py _ledger_block; tests: 3

<a id="layer-output"></a>

## Outputs

Summary figures and contract ranges, strips, class-size table, segment and incentive blocks, narratives, History, Levers counts, Distribution, RunLog and the label constants.

<a id="OUT-001"></a>

#### OUT-001 `sw_selected`: Selected-case block

Expected class, ntr_y1 and P(median holds) at the first score threshold for the case chosen on Inputs, so a reader can flip between Low, Middle and High.

- Client label: "Selected case (Inputs case selector)"
- Excel: Summary rows 5 to 10 ('Selected case (Inputs case selector)'); figures 'Expected class', 'ntr_y1', 'P(median holds) {measure} {t}'
- Unit: count; dimensions: scenario
- Formula: INDEX of the class, ntr_y1 and median ranges by the case selector
- Fed by: [IN-125](#IN-125), [OUT-008](#OUT-008), [OUT-038](#OUT-038), [OUT-020](#OUT-020)
- Feeds: none
- Role: display; response: Y; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 6 Inputs; sw/workbook.py sw_selected; tests: 3; 10

<a id="OUT-002"></a>

#### OUT-002 `apps_total`: Applications (total)

Scenario applications summed over cells. Shown on the Summary; nothing reads it.

- Client label: "Applications"
- Excel: Summary main block (Middle case) row 'Applications'
- Unit: count; dimensions: scenario x case
- Formula: SUM (or SUMPRODUCT by residency) of the Ledger column
- Fed by: [LG-025](#LG-025)
- Feeds: none
- Role: primary; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 KPIs; MR 8; sw/ledger.py kpis; tests: 3; 19

<a id="OUT-003"></a>

#### OUT-003 `apps_in`: Applications, in-state

Scenario applications from in-state cells. Shown on the Summary; nothing reads it.

- Client label: "Applications, in-state"
- Excel: Summary main block (Middle case) row 'Applications, in-state'
- Unit: count; dimensions: scenario x case
- Formula: SUM (or SUMPRODUCT by residency) of the Ledger column
- Fed by: [LG-025](#LG-025), [LG-008](#LG-008)
- Feeds: none
- Role: primary; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 KPIs; MR 8; sw/ledger.py kpis; tests: 3; 19

<a id="OUT-004"></a>

#### OUT-004 `apps_out`: Applications, out-of-state

Scenario applications from out-of-state cells. Shown on the Summary; nothing reads it.

- Client label: "Applications, out-of-state"
- Excel: Summary main block (Middle case) row 'Applications, out-of-state'
- Unit: count; dimensions: scenario x case
- Formula: SUM (or SUMPRODUCT by residency) of the Ledger column
- Fed by: [LG-025](#LG-025), [LG-008](#LG-008)
- Feeds: none
- Role: primary; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 KPIs; MR 8; sw/ledger.py kpis; tests: 3; 19

<a id="OUT-005"></a>

#### OUT-005 `admits_total`: Admits (total)

Scenario admits summed over cells. Shown on the Summary; nothing reads it.

- Client label: "Admits"
- Excel: Summary main block (Middle case) row 'Admits'
- Unit: count; dimensions: scenario x case
- Formula: SUM (or SUMPRODUCT by residency) of the Ledger column
- Fed by: [LG-027](#LG-027)
- Feeds: none
- Role: primary; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 KPIs; MR 8; sw/ledger.py kpis; tests: 3; 19

<a id="OUT-006"></a>

#### OUT-006 `admits_in`: Admits, in-state

Scenario admits from in-state cells. Shown on the Summary; nothing reads it.

- Client label: "Admits, in-state"
- Excel: Summary main block (Middle case) row 'Admits, in-state'
- Unit: count; dimensions: scenario x case
- Formula: SUM (or SUMPRODUCT by residency) of the Ledger column
- Fed by: [LG-027](#LG-027), [LG-008](#LG-008)
- Feeds: none
- Role: primary; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 KPIs; MR 8; sw/ledger.py kpis; tests: 3; 19

<a id="OUT-007"></a>

#### OUT-007 `admits_out`: Admits, out-of-state

Scenario admits from out-of-state cells. Shown on the Summary; nothing reads it.

- Client label: "Admits, out-of-state"
- Excel: Summary main block (Middle case) row 'Admits, out-of-state'
- Unit: count; dimensions: scenario x case
- Formula: SUM (or SUMPRODUCT by residency) of the Ledger column
- Fed by: [LG-027](#LG-027), [LG-008](#LG-008)
- Feeds: none
- Role: primary; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 KPIs; MR 8; sw/ledger.py kpis; tests: 3; 19

<a id="OUT-008"></a>

#### OUT-008 `class_mean`: Expected class

Expected entering class M: the sum of expected enrolled over cells. The center of every class probability and range, the class break-evens and the shrink path.

- Client label: "Expected class"
- Excel: Summary main block (Middle case) row 'Expected class'; Low and High rows in the 'Low and High price-response cases' block; named range SUM_CLASS_MEAN
- Unit: count; dimensions: scenario x case
- Formula: M = sum_c mu_c
- Fed by: [LG-034](#LG-034)
- Feeds: [OUT-001](#OUT-001), [OUT-011](#OUT-011), [OUT-012](#OUT-012), [OUT-131](#OUT-131), [CK-026](#CK-026), [CK-033](#CK-033)
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 5; App F 4; MR 6.2; sw/risk.py class_dist; tests: 1; 2; 3; 9

<a id="OUT-009"></a>

#### OUT-009 `class_lo90`: Class, 90% range low

Lower end of the 90% outcome range for the class (enrollment noise and year-level variation), clipped at zero.

- Client label: "Class, 90% outcome range: low"
- Excel: Summary main block (Middle case) row 'Class, 90% outcome range: low'; named range SUM_CLASS_LO90
- Unit: count; dimensions: scenario x case
- Formula: MAX(0, M - 1.645 sqrt(V))
- Fed by: [LG-034](#LG-034), [LG-027](#LG-027), [LG-032](#LG-032), [IN-041](#IN-041), [INT-026](#INT-026), [INT-038](#INT-038)
- Feeds: [OUT-131](#OUT-131)
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 5; MR 6.2; sw/risk.py class_dist; tests: 2; 3; 9; 19

<a id="OUT-010"></a>

#### OUT-010 `class_hi90`: Class, 90% range high

Upper end of the 90% outcome range for the class.

- Client label: "Class, 90% outcome range: high"
- Excel: Summary main block (Middle case) row 'Class, 90% outcome range: high'; named range SUM_CLASS_HI90
- Unit: count; dimensions: scenario x case
- Formula: M + 1.645 sqrt(V)
- Fed by: [LG-034](#LG-034), [LG-027](#LG-027), [LG-032](#LG-032), [IN-041](#IN-041), [INT-026](#INT-026), [INT-038](#INT-038)
- Feeds: [OUT-131](#OUT-131)
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 5; MR 6.2; sw/risk.py class_dist; tests: 2; 3; 9; 19

<a id="OUT-011"></a>

#### OUT-011 `p_class_over_cap`: Probability the class exceeds the cap

Probability the enrolled class is above the cap, by the normal approximation with a continuity correction.

- Client label: "P(class above cap)"
- Excel: Summary main block (Middle case) row 'P(class above cap)'; named range SUM_P_CLASS_OVER_CAP
- Unit: probability; dimensions: scenario x case
- Formula: 1 - Phi((cap + 0.5 - M) / sqrt(V))
- Fed by: [OUT-008](#OUT-008), [INT-026](#INT-026), [IN-099](#IN-099), [IN-042](#IN-042), [OUT-183](#OUT-183), [OUT-184](#OUT-184), [OUT-177](#OUT-177)
- Feeds: none
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 5; MR 6.2; sw/risk.py class_probs; tests: 2; 3; 4; 9

<a id="OUT-012"></a>

#### OUT-012 `p_class_in_band`: Probability the class lands in the target band

Probability the class is within the band around the target.

- Client label: "P(class within target band)"
- Excel: Summary main block (Middle case) row 'P(class within target band)'; named range SUM_P_CLASS_IN_BAND
- Unit: probability; dimensions: scenario x case
- Formula: Phi((target + band + 0.5 - M)/sqrt(V)) - Phi((target - band - 0.5 - M)/sqrt(V))
- Fed by: [OUT-008](#OUT-008), [INT-026](#INT-026), [IN-098](#IN-098), [IN-028](#IN-028), [IN-042](#IN-042), [OUT-183](#OUT-183), [OUT-184](#OUT-184), [OUT-177](#OUT-177)
- Feeds: none
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 5; MR 6.2; sw/risk.py class_probs; tests: 2; 3; 9

<a id="OUT-013"></a>

#### OUT-013 `enrolled_at_or_above`: Enrolled at or above a score

Expected enrolled with a score at or above each threshold (every median threshold, the pool threshold and the floor). Held when t is a median or percentile threshold and the hold is on.

- Client label: "Enrolled at or above {measure} {t}"
- Excel: Summary main block (Middle case) rows 'Enrolled at or above {measure} {t}'
- Unit: count; dimensions: scenario x case x threshold
- Formula: SUMPRODUCT((scored)*(score_lo >= t)*enrolled)
- Fed by: [LG-035](#LG-035), [LG-010](#LG-010), [LG-012](#LG-012), [INT-023](#INT-023), [INT-024](#INT-024)
- Feeds: [OUT-014](#OUT-014)
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 KPIs; sw/ledger.py kpis; tests: 3; 6; 27

<a id="OUT-014"></a>

#### OUT-014 `share_at_or_above_t`: Share at or above a score

Expected enrolled at or above t over expected enrolled with a score (a ratio of expected values).

- Client label: "Share at or above {measure} {t} (of enrolled with a score)"
- Excel: Summary main block (Middle case) rows 'Share at or above {measure} {t} (of enrolled with a score)'; named range SUM_SHARE_AT_OR_ABOVE_T
- Unit: ratio; dimensions: scenario x case x threshold
- Formula: enrolled at or above t / enrolled with a score
- Fed by: [OUT-013](#OUT-013), [LG-035](#LG-035), [LG-012](#LG-012), [INT-024](#INT-024)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 KPIs; App F 10; MR 4.6; sw/ledger.py kpis; tests: 3; 9; 14; 27

<a id="OUT-015"></a>

#### OUT-015 `enrolled_below_floor`: Enrolled below the score floor

Expected enrolled with a score below the floor. Also in the projected-outcome narrative. Held when the floor is a held threshold.

- Client label: "Enrolled below {measure} floor"
- Excel: Summary main block (Middle case) row 'Enrolled below {measure} floor'
- Unit: count; dimensions: scenario x case
- Formula: SUMPRODUCT((scored)*(score_lo < floor)*enrolled)
- Fed by: [LG-035](#LG-035), [LG-010](#LG-010), [IN-016](#IN-016), [INT-024](#INT-024)
- Feeds: [OUT-131](#OUT-131)
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 KPIs; F-1; sw/ledger.py kpis; tests: 3; 6; 27

<a id="OUT-016"></a>

#### OUT-016 `enrolled_gpa_hi`: Enrolled with high GPA

Expected enrolled in cells with GPA class hi. Held when the GPA boundary is the GPA median threshold and the hold is on.

- Client label: "Enrolled with GPA class hi"
- Excel: Summary main block (Middle case) row 'Enrolled with GPA class hi'
- Unit: count; dimensions: scenario x case
- Formula: SUMPRODUCT((gpa_class = hi)*enrolled)
- Fed by: [LG-035](#LG-035), [LG-011](#LG-011), [INT-024](#INT-024)
- Feeds: none
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 KPIs; F-1; sw/ledger.py kpis; tests: 3; 6; 27

<a id="OUT-017"></a>

#### OUT-017 `unscored_count`: Unscored enrolled

Expected enrolled without a score. Under the default counting rule they are outside both sides of every score margin and reported here instead.

- Client label: "Unscored enrolled (outside the score margins)"
- Excel: Summary main block (Middle case) row 'Unscored enrolled (outside the score margins)'; named range SUM_UNSCORED_COUNT
- Unit: count; dimensions: scenario x case
- Formula: SUMPRODUCT((scored = 0)*enrolled)
- Fed by: [LG-035](#LG-035), [LG-012](#LG-012)
- Feeds: none
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 KPIs; App F 8; sw/ledger.py kpis; tests: 3; 9

<a id="OUT-018"></a>

#### OUT-018 `gpa_blank_count`: Blank-GPA enrolled

Expected enrolled without a GPA; outside the GPA margin under the default counting rule.

- Client label: "Blank-GPA enrolled (outside the GPA margin)"
- Excel: Summary main block (Middle case) row 'Blank-GPA enrolled (outside the GPA margin)'
- Unit: count; dimensions: scenario x case
- Formula: SUMPRODUCT((gpa_class = blank)*enrolled)
- Fed by: [LG-035](#LG-035), [LG-011](#LG-011)
- Feeds: none
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 KPIs; sw/ledger.py kpis; tests: 3

<a id="OUT-019"></a>

#### OUT-019 `margin_t`: Median margin

Enrolled with a score at or above t minus enrolled below t (unscored in neither term). The median holds while it is zero or more. One row per median target, score and GPA.

- Client label: "Median margin, {measure} {t}"
- Excel: Summary main block (Middle case) rows 'Median margin, {measure} {t}'; named range SUM_MARGIN_T
- Unit: count; dimensions: scenario x case x threshold
- Formula: m = sum_c g_c x enrolled_c
- Fed by: [LG-014](#LG-014), [LG-035](#LG-035), [INT-024](#INT-024)
- Feeds: [OUT-131](#OUT-131)
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 5; App F 9; MR 4.6, 6.3; sw/risk.py median; tests: 1; 3; 9; 22; 27

<a id="OUT-020"></a>

#### OUT-020 `p_median_t`: Probability the median holds

Probability the median of scored enrollees is at or above t (inclusive tie rule), by the normal approximation with the shock correlation from Inputs.

- Client label: "P(median holds), {measure} {t}"
- Excel: Summary main block (Middle case) rows 'P(median holds), {measure} {t}'; Low and High rows in the 'Low and High price-response cases' block; named range SUM_P_MEDIAN_T
- Unit: probability; dimensions: scenario x case x threshold
- Formula: 1 - Phi((-0.5 - (G+ - G-)) / sqrt(V_m))
- Fed by: [LG-014](#LG-014), [LG-034](#LG-034), [LG-027](#LG-027), [LG-032](#LG-032), [IN-041](#IN-041), [INT-028](#INT-028), [INT-029](#INT-029), [INT-031](#INT-031), [IN-043](#IN-043), [IN-042](#IN-042), [OUT-183](#OUT-183), [OUT-184](#OUT-184), [OUT-177](#OUT-177), [INT-024](#INT-024)
- Feeds: [OUT-001](#OUT-001), [OUT-131](#OUT-131)
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 5; App F 9; MR 6.3; sw/risk.py median; tests: 2; 3; 4; 9; 27

<a id="OUT-021"></a>

#### OUT-021 `p_median_t_rho05`: Probability the median holds, rho 0.5

The same probability with the shock correlation fixed at 0.5: a sensitivity line for high-score and other admits' yields moving differently.

- Client label: "P(median holds), {measure} {t}, rho 0.5: if high-score and other admits' yields move differently year to year"
- Excel: Summary main block (Middle case) rows 'P(median holds), {measure} {t}, rho 0.5: ...'; named range SUM_P_MEDIAN_T_RHO05
- Unit: probability; dimensions: scenario x case x threshold
- Formula: as p_median_t with rho = 0.5
- Fed by: [LG-014](#LG-014), [LG-034](#LG-034), [LG-027](#LG-027), [LG-032](#LG-032), [IN-041](#IN-041), [INT-028](#INT-028), [INT-029](#INT-029), [INT-031](#INT-031), [IN-042](#IN-042), [OUT-183](#OUT-183), [OUT-184](#OUT-184), [OUT-177](#OUT-177), [INT-024](#INT-024)
- Feeds: none
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 5; MR 6.3; sw/risk.py median; tests: 2; 3; 4; 9; 19; 27

<a id="OUT-022"></a>

#### OUT-022 `margin_q_t`: Percentile margin (swaps)

q times scored enrollees minus enrollees below t: how many below-t enrollees could replace at-or-above-t enrollees at the same class size. Percentile targets other than the median only.

- Client label: "{ordinal} percentile (q {q}) at or above {measure} {t}: margin (swaps: students below t who could replace students at or above t)"
- Excel: Summary main block (Middle case) rows '{ordinal} percentile (q {q}) at or above {measure} {t}: margin (swaps: ...)'; named range SUM_MARGIN_Q_T
- Unit: count; dimensions: scenario x case x target
- Formula: q x N_scored - G- = q x sum_above enrolled - (1 - q) x sum_below enrolled
- Fed by: [LG-015](#LG-015), [LG-035](#LG-035), [IN-018](#IN-018), [INT-024](#INT-024)
- Feeds: none
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 0A A1; App F 26; MR 4.6; sw/risk.py pct; tests: 3; 9; 22; 27

<a id="OUT-023"></a>

#### OUT-023 `p_pct_q_t`: Probability the percentile target holds

Probability that at most a share q of scored enrollees score below t, by the normal approximation with the lattice continuity correction.

- Client label: "P({ordinal} percentile (q {q}) at or above {measure} {t})"
- Excel: Summary main block (Middle case) rows 'P({ordinal} percentile (q {q}) at or above {measure} {t})'; Low and High rows in the 'Low and High price-response cases' block; named range SUM_P_PCT_Q_T
- Unit: probability; dimensions: scenario x case x target
- Formula: 1 - Phi((-1/(2n) - E[M_q]) / sqrt(V_q))
- Fed by: [LG-015](#LG-015), [LG-034](#LG-034), [LG-027](#LG-027), [LG-032](#LG-032), [IN-041](#IN-041), [IN-018](#IN-018), [INT-032](#INT-032), [INT-033](#INT-033), [INT-022](#INT-022), [IN-043](#IN-043), [IN-042](#IN-042), [OUT-183](#OUT-183), [OUT-184](#OUT-184), [OUT-177](#OUT-177), [INT-024](#INT-024)
- Feeds: none
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 0A A1; App F 26; MR 6.4; sw/risk.py pct; tests: 2; 3; 4; 9; 22; 27

<a id="OUT-024"></a>

#### OUT-024 `p_pct_q_t_rho05`: Probability the percentile target holds, rho 0.5

The percentile probability with the shock correlation fixed at 0.5.

- Client label: "P({ordinal} percentile (q {q}) at or above {measure} {t}), rho 0.5: if high-score and other admits' yields move differently year to year"
- Excel: Summary main block (Middle case) rows 'P(...), rho 0.5: ...'; named range SUM_P_PCT_Q_T_RHO05
- Unit: probability; dimensions: scenario x case x target
- Formula: as p_pct_q_t with rho = 0.5
- Fed by: [LG-015](#LG-015), [LG-034](#LG-034), [LG-027](#LG-027), [LG-032](#LG-032), [IN-041](#IN-041), [IN-018](#IN-018), [INT-032](#INT-032), [INT-033](#INT-033), [INT-022](#INT-022), [IN-042](#IN-042), [OUT-183](#OUT-183), [OUT-184](#OUT-184), [OUT-177](#OUT-177), [INT-024](#INT-024)
- Feeds: none
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 0A A1; MR 6.4; sw/risk.py pct; tests: 2; 3; 9; 22; 27

<a id="OUT-025"></a>

#### OUT-025 `pct_expected_below`: Expected enrolled below a percentile threshold

Expected scored enrollees below t (G-). Fewer than 20 marks the percentile probability approximate.

- Client label: "{ordinal} percentile (q {q}) at or above {measure} {t}: expected enrolled below t"
- Excel: Summary main block (Middle case) rows '...: expected enrolled below t'
- Unit: count; dimensions: scenario x case x target
- Formula: G- = SUMPRODUCT((sign = -1) x mu)
- Fed by: [INT-029](#INT-029), [INT-024](#INT-024)
- Feeds: [OUT-026](#OUT-026)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 0A A1; sw/risk.py pct; tests: 3; 22; 27

<a id="OUT-026"></a>

#### OUT-026 `pct_approximate`: Percentile approximation flag

Shows the approximation text when fewer than 20 enrollees are expected below t; blank otherwise.

- Client label: "{ordinal} percentile (q {q}) at or above {measure} {t}: approximation flag"
- Excel: Summary main block (Middle case) rows '...: approximation flag'
- Unit: text; dimensions: scenario x case x target
- Formula: IF(G- < 20, approximation text, blank)
- Fed by: [OUT-025](#OUT-025), [INT-039](#INT-039), [OUT-194](#OUT-194), [INT-024](#INT-024)
- Feeds: none
- Role: display; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 0A A1; sw/risk.py PCT_APPROX_BELOW; tests: 3; 22; 27

<a id="OUT-027"></a>

#### OUT-027 `pct_band_q`: Spread band lower bound

For q = 0.25 and 0.75 (Middle case), the largest band lower bound with at most a share q of scored enrollees below it: the band the percentile most likely falls in, not a score.

- Client label: "Spread: {ordinal} percentile band, lower bound (band, not a score)"
- Excel: Summary rows 'Spread: {ordinal} percentile band, lower bound (band, not a score)'; named range SUM_PCT_BAND_Q
- Unit: score; dimensions: scenario x q
- Formula: MAX over bands b of (b if share below b <= q)
- Fed by: [LG-035](#LG-035), [LG-010](#LG-010), [LG-012](#LG-012), [IN-014](#IN-014), [INT-041](#INT-041), [IN-025](#IN-025), [INT-024](#INT-024)
- Feeds: [OUT-028](#OUT-028)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 0A A1; MR 6.4; sw/risk.py pct_band; tests: 3; 9; 22; 27

<a id="OUT-028"></a>

#### OUT-028 `_range_text`: Spread band (text)

The spread band as text, for example 'a to below b', or 'below b' for the lowest band.

- Client label: "Spread: {ordinal} percentile band (band, not a score)"
- Excel: Summary rows 'Spread: {ordinal} percentile band (band, not a score)'
- Unit: text; dimensions: scenario x q
- Formula: text from the band lower bound and the next band up
- Fed by: [OUT-027](#OUT-027), [OUT-214](#OUT-214), [INT-024](#INT-024)
- Feeds: none
- Role: display; response: Y; shock: N; detail: supporting; client-safe: Y; status: held under hold_position_rows
- References: spec 0A A1; sw/workbook.py sw_percentiles; tests: 3; 22; 27

<a id="OUT-029"></a>

#### OUT-029 `full_tuition_n`: Full-tuition enrolled

Expected enrolled whose award is at or above tuition.

- Client label: "Full-tuition enrolled (award at or above tuition)"
- Excel: Summary main block (Middle case) row 'Full-tuition enrolled (award at or above tuition)'; Distribution counts; named range SUM_FULL_TUITION_N
- Unit: count; dimensions: scenario x case
- Formula: SUMPRODUCT((award >= T_s) x enrolled)
- Fed by: [LG-030](#LG-030), [LG-002](#LG-002), [LG-035](#LG-035)
- Feeds: [OUT-031](#OUT-031), [OUT-131](#OUT-131)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 KPIs; MR 8; sw/ledger.py kpis; tests: 3; 6; 9

<a id="OUT-030"></a>

#### OUT-030 `no_merit_award_n`: No-merit-award enrolled

Expected enrolled with an award of zero (need aid is not assigned to cells).

- Client label: "No-merit-award enrolled (award zero)"
- Excel: Summary main block (Middle case) row 'No-merit-award enrolled (award zero)'; Distribution counts; named range SUM_NO_MERIT_AWARD_N
- Unit: count; dimensions: scenario x case
- Formula: SUMPRODUCT((award = 0) x enrolled)
- Fed by: [LG-030](#LG-030), [LG-035](#LG-035)
- Feeds: [OUT-031](#OUT-031), [OUT-131](#OUT-131)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 KPIs; sw/ledger.py kpis; tests: 3; 6; 9

<a id="OUT-031"></a>

#### OUT-031 `barbell`: Barbell index

Full-tuition plus no-merit-award enrolled over the class: the share of the class at the two ends of the award range.

- Client label: "Barbell index"
- Excel: Summary main block (Middle case) row 'Barbell index'; Distribution; named range SUM_BARBELL
- Unit: ratio; dimensions: scenario x case
- Formula: (full_tuition_n + no_merit_award_n) / class
- Fed by: [OUT-029](#OUT-029), [OUT-030](#OUT-030), [LG-035](#LG-035)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 KPIs; sw/ledger.py kpis; tests: 3; 9

<a id="OUT-032"></a>

#### OUT-032 `gross_y1`: Gross first-year tuition

Enrolled class times published first-year tuition, fees excluded.

- Client label: "gross_y1"
- Excel: Summary main block (Middle case) row 'gross_y1'; named range SUM_GROSS_Y1
- Unit: USD; dimensions: scenario x case
- Formula: class x T_s
- Fed by: [LG-035](#LG-035), [LG-002](#LG-002)
- Feeds: [OUT-038](#OUT-038), [OUT-047](#OUT-047)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 item 8; App F 11; sw/ledger.py money; tests: 1; 3; 9

<a id="OUT-033"></a>

#### OUT-033 `merit`: Merit aid

Merit dollars to the entering class in its first year: enrolled times award summed over cells, incentive included.

- Client label: "Merit"
- Excel: Summary main block (Middle case) row 'Merit'; named range SUM_MERIT
- Unit: USD; dimensions: scenario x case
- Formula: sum_c enrolled x award
- Fed by: [LG-036](#LG-036)
- Feeds: [OUT-037](#OUT-037), [CK-029](#CK-029)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 item 7; App F 12; sw/ledger.py money; tests: 1; 3; 6; 9

<a id="OUT-034"></a>

#### OUT-034 `incentive_cost`: Incentive cost

Enrolled times incentive per enrollee, over cells with an incentive. Part of merit.

- Client label: "of which incentive cost"
- Excel: Summary main block (Middle case) row 'of which incentive cost'; Summary incentive block row 'Incentive cost (C)'; named range INC_INCENTIVE_COST
- Unit: USD; dimensions: scenario x case
- Formula: C = sum_c enrolled x incentive
- Fed by: [LG-035](#LG-035), [LG-029](#LG-029)
- Feeds: [OUT-066](#OUT-066)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 item 7, incentive block; App F 19; sw/ledger.py incentive; tests: 1; 3; 9; 13

<a id="OUT-035"></a>

#### OUT-035 `need`: Need aid

Need rate times the class, plus the scenario's fixed need departure.

- Client label: "Need aid"
- Excel: Summary main block (Middle case) row 'Need aid'; named range SUM_NEED
- Unit: USD; dimensions: scenario x case
- Formula: need_rate x class + need departure
- Fed by: [LG-004](#LG-004), [LG-035](#LG-035), [LG-005](#LG-005)
- Feeds: [OUT-037](#OUT-037)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 item 7; R4-07; sw/ledger.py money; tests: 1; 3; 9; 19

<a id="OUT-036"></a>

#### OUT-036 `specialty`: Specialty aid

The scenario's specialty lump sum.

- Client label: "Specialty"
- Excel: Summary main block (Middle case) row 'Specialty'; named range SUM_SPECIALTY
- Unit: USD; dimensions: scenario x case
- Formula: = specialty_usd
- Fed by: [IN-096](#IN-096)
- Feeds: [OUT-037](#OUT-037)
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 item 8; sw/ledger.py money; tests: 1; 3; 9

<a id="OUT-037"></a>

#### OUT-037 `aid`: Total aid

Merit plus need plus specialty.

- Client label: "Aid (merit + need + specialty)"
- Excel: Summary main block (Middle case) row 'Aid (merit + need + specialty)'; named range SUM_AID
- Unit: USD; dimensions: scenario x case
- Formula: merit + need + specialty
- Fed by: [OUT-033](#OUT-033), [OUT-035](#OUT-035), [OUT-036](#OUT-036)
- Feeds: [OUT-038](#OUT-038), [OUT-047](#OUT-047), [OUT-048](#OUT-048), [CK-029](#CK-029)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 item 8; sw/ledger.py money; tests: 1; 3; 9

<a id="OUT-038"></a>

#### OUT-038 `ntr_y1`: First-year net tuition revenue

Gross first-year tuition minus merit, need and specialty for the entering class. The revenue figure every NTR probability, strip and break-even is about.

- Client label: "ntr_y1 (first-year net tuition revenue, entering class)"
- Excel: Summary main block (Middle case) row 'ntr_y1 (first-year net tuition revenue, entering class)'; Low and High rows in the 'Low and High price-response cases' block; named range SUM_NTR_Y1
- Unit: USD; dimensions: scenario x case
- Formula: gross_y1 - aid
- Fed by: [OUT-032](#OUT-032), [OUT-037](#OUT-037)
- Feeds: [OUT-001](#OUT-001), [OUT-045](#OUT-045), [OUT-049](#OUT-049), [OUT-131](#OUT-131)
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 item 8; App F 14; MR 4.5; sw/ledger.py money; tests: 1; 3; 6; 9

<a id="OUT-039"></a>

#### OUT-039 `ntr_lo90`: First-year NTR, 90% range low

Lower end of the 90% outcome range for ntr_y1 (not clipped).

- Client label: "ntr_y1, 90% outcome range: low"
- Excel: Summary main block (Middle case) row 'ntr_y1, 90% outcome range: low'
- Unit: USD; dimensions: scenario x case
- Formula: sum w mu - K - 1.645 sqrt(V_n)
- Fed by: [LG-037](#LG-037), [LG-034](#LG-034), [INT-034](#INT-034), [INT-035](#INT-035), [INT-038](#INT-038)
- Feeds: [OUT-131](#OUT-131)
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 5 NTR; MR 6.5; sw/risk.py cf_ntr; tests: 3; 19

<a id="OUT-040"></a>

#### OUT-040 `ntr_hi90`: First-year NTR, 90% range high

Upper end of the 90% outcome range for ntr_y1.

- Client label: "ntr_y1, 90% outcome range: high"
- Excel: Summary main block (Middle case) row 'ntr_y1, 90% outcome range: high'
- Unit: USD; dimensions: scenario x case
- Formula: sum w mu - K + 1.645 sqrt(V_n)
- Fed by: [LG-037](#LG-037), [LG-034](#LG-034), [INT-034](#INT-034), [INT-035](#INT-035), [INT-038](#INT-038)
- Feeds: [OUT-131](#OUT-131)
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 5 NTR; MR 6.5; sw/risk.py cf_ntr; tests: 3; 19

<a id="OUT-041"></a>

#### OUT-041 `ntr_target`: Revenue target (echo)

The revenue target from Inputs, or 'none'.

- Client label: "ntr_target (Inputs; under all_jd the total JD goal)"
- Excel: Summary main block (Middle case) row 'ntr_target (Inputs; under all_jd the total JD goal)'
- Unit: USD; dimensions: scenario
- Formula: = in_ntr_target
- Fed by: [IN-034](#IN-034)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: R4-12; sw/workbook.py sw_main; tests: 27

<a id="OUT-042"></a>

#### OUT-042 `ntr_target_effective`: Effective entering target (echo)

The target every revenue probability and break-even reads, or 'none'.

- Client label: "Effective entering target (ntr_target, less continuing revenue under all_jd)"
- Excel: Summary main block (Middle case) row 'Effective entering target (ntr_target, less continuing revenue under all_jd)'
- Unit: USD; dimensions: scenario
- Formula: = in_ntr_target_eff
- Fed by: [INT-020](#INT-020)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: R4-12; sw/config.py ntr_target_effective; tests: 25; 27

<a id="OUT-043"></a>

#### OUT-043 `p_ntr_y1_ge_target`: Probability first-year NTR meets the target

Probability ntr_y1 is at or above the effective target, by the normal approximation. Blank with no target.

- Client label: "P(ntr_y1 at or above the effective entering target)"
- Excel: Summary main block (Middle case) row 'P(ntr_y1 at or above the effective entering target)'; named range SUM_P_NTR_Y1_GE_TARGET
- Unit: probability; dimensions: scenario x case
- Formula: 1 - Phi((target_eff - (sum w mu - K)) / sqrt(V_n))
- Fed by: [LG-037](#LG-037), [LG-034](#LG-034), [INT-034](#INT-034), [INT-035](#INT-035), [INT-020](#INT-020), [IN-042](#IN-042), [OUT-183](#OUT-183), [OUT-184](#OUT-184), [OUT-177](#OUT-177)
- Feeds: [OUT-046](#OUT-046)
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 5 NTR; spec 0A A4; MR 6.5; sw/risk.py ntr; tests: 2; 3; 4; 9; 25

<a id="OUT-044"></a>

#### OUT-044 `continuing_ntr_usd`: Continuing-student net tuition (echo)

Continuing-student revenue under all_jd; 'not used (entering_y1)' otherwise.

- Client label: "Continuing-student net tuition, all_jd (continuing-student revenue as supplied by the client; attrition and renewals not modeled)"
- Excel: Summary main block (Middle case) row 'Continuing-student net tuition, all_jd (...)'
- Unit: USD; dimensions: scenario
- Formula: IF(all_jd, continuing_ntr_usd, not used)
- Fed by: [IN-036](#IN-036), [IN-035](#IN-035), [OUT-211](#OUT-211), [OUT-196](#OUT-196)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A A4; R4-12; tests: 25; 27

<a id="OUT-045"></a>

#### OUT-045 `jd_ntr`: Projected JD net tuition

Continuing-student revenue plus ntr_y1 under all_jd; 'not used (entering_y1)' otherwise.

- Client label: "Projected JD net tuition = continuing (client-supplied) + ntr_y1"
- Excel: Summary main block (Middle case) row 'Projected JD net tuition = continuing (client-supplied) + ntr_y1'
- Unit: USD; dimensions: scenario
- Formula: continuing_ntr_usd + ntr_y1
- Fed by: [IN-036](#IN-036), [OUT-038](#OUT-038), [IN-035](#IN-035)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 0A A4; sw/contract.py compute; tests: 25; 27

<a id="OUT-046"></a>

#### OUT-046 `p_jd_ntr_ge_goal`: Probability the JD revenue goal is met

Under all_jd, the probability continuing revenue plus ntr_y1 reaches the target: the same event as the first-year probability at the effective target. Blank under entering_y1.

- Client label: "P(continuing + ntr_y1 at or above ntr_target), all_jd"
- Excel: Summary main block (Middle case) row 'P(continuing + ntr_y1 at or above ntr_target), all_jd'; named range SUM_P_JD_NTR_GE_GOAL
- Unit: probability; dimensions: scenario x case
- Formula: = p_ntr_y1_ge_target under all_jd
- Fed by: [OUT-043](#OUT-043), [IN-035](#IN-035), [IN-042](#IN-042), [OUT-183](#OUT-183), [OUT-184](#OUT-184), [OUT-177](#OUT-177)
- Feeds: none
- Role: primary; response: Y; shock: Y; detail: core; client-safe: N; status: live
- References: spec 0A A4; sw/contract.py compute; tests: 3; 9; 25

<a id="OUT-047"></a>

#### OUT-047 `discount_entering_y1`: Discount rate

Aid over gross first-year tuition for the entering class (ratio of expected values).

- Client label: "Discount rate (entering class, first year)"
- Excel: Summary main block (Middle case) row 'Discount rate (entering class, first year)'; named range SUM_DISCOUNT_ENTERING_Y1
- Unit: ratio; dimensions: scenario x case
- Formula: aid / gross_y1
- Fed by: [OUT-037](#OUT-037), [OUT-032](#OUT-032)
- Feeds: [OUT-050](#OUT-050), [OUT-131](#OUT-131)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 item 8; App F 13; sw/ledger.py money; tests: 1; 3; 9

<a id="OUT-048"></a>

#### OUT-048 `avg_aid`: Average aid per enrollee

Aid over the class.

- Client label: "Average aid per enrollee"
- Excel: Summary main block (Middle case) row 'Average aid per enrollee'; named range SUM_AVG_AID
- Unit: USD; dimensions: scenario x case
- Formula: aid / class
- Fed by: [OUT-037](#OUT-037), [LG-035](#LG-035)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 item 8; sw/ledger.py money; tests: 1; 3; 9

<a id="OUT-049"></a>

#### OUT-049 `price_of_target`: Price of the target

Baseline's ntr_y1 minus the scenario's: the first-year revenue given up relative to Baseline.

- Client label: "Price of the target (Baseline ntr_y1 minus scenario ntr_y1)"
- Excel: Summary main block (Middle case) row 'Price of the target (Baseline ntr_y1 minus scenario ntr_y1)'
- Unit: USD; dimensions: scenario
- Formula: ntr_y1(Baseline) - ntr_y1(s)
- Fed by: [OUT-038](#OUT-038)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 KPIs; MR 8; sw/ledger.py price_of_target; tests: 3; 19

<a id="OUT-050"></a>

#### OUT-050 `margin_to_target`: Margin to discount target

Discount target minus the discount rate; blank without a target.

- Client label: "Margin to discount target (target minus rate)"
- Excel: Summary main block (Middle case) row 'Margin to discount target (target minus rate)'
- Unit: ratio; dimensions: scenario
- Formula: discount_target - discount_entering_y1
- Fed by: [IN-111](#IN-111), [OUT-047](#OUT-047)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 discount row; sw/ledger.py discount_row; tests: 3; 19

<a id="OUT-051"></a>

#### OUT-051 `evidence_extrapolated_share`: Evidence share

Expected enrolled in cells whose award lies outside the observed range, over the expected class. Says how much of the class rests on extrapolated yields.

- Client label: "Share of enrolled in cells where the yield is extrapolated"
- Excel: Summary main block (Middle case) row 'Share of enrolled in cells where the yield is extrapolated'; named range SUM_EVIDENCE_EXTRAPOLATED_SHARE
- Unit: ratio; dimensions: scenario x case
- Formula: SUMPRODUCT((evidence = extrapolated) x mu) / M
- Fed by: [LG-033](#LG-033), [LG-034](#LG-034)
- Feeds: [OUT-131](#OUT-131)
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 4; App F 24; MR 5.3; sw/response.py evidence; tests: 3; 9; 19

<a id="OUT-052"></a>

#### OUT-052 `active_segment`: Active segment (echo)

The scenario's active segment name.

- Client label: "Active segment"
- Excel: Summary segment block row 'Active segment'
- Unit: text; dimensions: scenario
- Formula: = Ledger block segment
- Fed by: [LG-006](#LG-006)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 segment block; sw/ledger.py active_segment; tests: 3; 18

<a id="OUT-053"></a>

#### OUT-053 `segment_apps`: Segment applications

Scenario applications in segment cells.

- Client label: "Segment applications"
- Excel: Summary segment block row 'Segment applications'
- Unit: count; dimensions: scenario x case
- Formula: SUMPRODUCT(in_seg, applications)
- Fed by: [LG-023](#LG-023), [LG-025](#LG-025)
- Feeds: none
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 segment block; sw/ledger.py segment; tests: 3; 18

<a id="OUT-054"></a>

#### OUT-054 `segment_admits`: Segment admits

Scenario admits in segment cells.

- Client label: "Segment admits"
- Excel: Summary segment block row 'Segment admits'
- Unit: count; dimensions: scenario x case
- Formula: SUMPRODUCT(in_seg, admits)
- Fed by: [LG-023](#LG-023), [LG-027](#LG-027)
- Feeds: none
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 segment block; sw/ledger.py segment; tests: 3; 18

<a id="OUT-055"></a>

#### OUT-055 `segment_enrolled`: Segment enrolled

Expected enrolled in segment cells (E_S). Shows 'no segment cells in the data' when the segment is empty.

- Client label: "Segment enrolled (E_S)"
- Excel: Summary segment block row 'Segment enrolled (E_S)'; class-size table column; named range SEG_SEGMENT_ENROLLED
- Unit: count; dimensions: scenario x case
- Formula: E_S = SUMPRODUCT(in_seg, enrolled)
- Fed by: [LG-023](#LG-023), [LG-035](#LG-035), [IN-064](#IN-064)
- Feeds: [OUT-056](#OUT-056), [OUT-131](#OUT-131)
- Role: primary; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 segment block; App F 18; MR 6.6; sw/ledger.py segment; tests: 3; 9; 11; 17; 18

<a id="OUT-056"></a>

#### OUT-056 `segment_share`: Segment share of class

Segment enrolled over the class.

- Client label: "Segment share of class"
- Excel: Summary segment block row 'Segment share of class'; named range SEG_SEGMENT_SHARE
- Unit: ratio; dimensions: scenario x case
- Formula: E_S / class
- Fed by: [OUT-055](#OUT-055), [LG-035](#LG-035)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 segment block; sw/ledger.py segment; tests: 3; 9; 18

<a id="OUT-057"></a>

#### OUT-057 `segment_merit`: Segment merit dollars

Merit dollars to segment enrollees.

- Client label: "Segment merit dollars"
- Excel: Summary segment block row 'Segment merit dollars'
- Unit: USD; dimensions: scenario x case
- Formula: SUMPRODUCT(in_seg, enrolled, award)
- Fed by: [LG-023](#LG-023), [LG-035](#LG-035), [LG-030](#LG-030)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 segment block; sw/ledger.py segment; tests: 3; 18

<a id="OUT-058"></a>

#### OUT-058 `segment_lo90`: Segment enrolled, 90% range low

Lower end of the 90% outcome range for segment enrolled, clipped at zero.

- Client label: "Segment enrolled, 90% outcome range: low"
- Excel: Summary segment block row 'Segment enrolled, 90% outcome range: low'; named range SEG_SEGMENT_LO90
- Unit: count; dimensions: scenario x case
- Formula: MAX(0, M_S - 1.645 sqrt(V_S))
- Fed by: [INT-036](#INT-036), [LG-023](#LG-023), [LG-034](#LG-034), [INT-038](#INT-038)
- Feeds: none
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 3 segment block; sw/ledger.py segment; tests: 3; 9; 18

<a id="OUT-059"></a>

#### OUT-059 `segment_hi90`: Segment enrolled, 90% range high

Upper end of the 90% outcome range for segment enrolled.

- Client label: "Segment enrolled, 90% outcome range: high"
- Excel: Summary segment block row 'Segment enrolled, 90% outcome range: high'; named range SEG_SEGMENT_HI90
- Unit: count; dimensions: scenario x case
- Formula: M_S + 1.645 sqrt(V_S)
- Fed by: [INT-036](#INT-036), [LG-023](#LG-023), [LG-034](#LG-034), [INT-038](#INT-038)
- Feeds: none
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 3 segment block; sw/ledger.py segment; tests: 3; 9; 18

<a id="OUT-060"></a>

#### OUT-060 `segment_goal`: Segment goal (rounded up)

The scenario's segment goal rounded up to a whole student.

- Client label: "Segment goal (rounded up)"
- Excel: Summary segment block row 'Segment goal (rounded up)'
- Unit: count; dimensions: scenario
- Formula: CEILING(segment_goal)
- Fed by: [IN-106](#IN-106)
- Feeds: [OUT-061](#OUT-061), [OUT-062](#OUT-062)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 segment block; tests: 3; 13

<a id="OUT-061"></a>

#### OUT-061 `p_segment_goal`: Probability segment enrolled meets the goal (normal form)

Probability segment enrolled reaches the goal, by the normal form the workbook can recalculate.

- Client label: "P(segment enrolled at or above goal), normal form"
- Excel: Summary segment block row 'P(segment enrolled at or above goal), normal form'; named range SEG_P_SEGMENT_GOAL
- Unit: probability; dimensions: scenario x case
- Formula: 1 - Phi((goal - 0.5 - M_S) / sqrt(V_S))
- Fed by: [INT-036](#INT-036), [OUT-060](#OUT-060), [LG-023](#LG-023), [LG-034](#LG-034), [IN-042](#IN-042), [OUT-183](#OUT-183), [OUT-184](#OUT-184), [OUT-177](#OUT-177)
- Feeds: none
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 3 segment block; App F 18; sw/risk.py segment_normal; tests: 3; 9; 13; 18

<a id="OUT-062"></a>

#### OUT-062 `p_segment_goal_exact`: Probability segment enrolled meets the goal (exact)

The exact probability (convolution of the cell binomials mixed over the shock), computed in Python at build and shown as a static value.

- Client label: "P(segment enrolled at or above goal), exact (static, from the build)"
- Excel: Summary segment block row 'P(segment enrolled at or above goal), exact (static, from the build)'; Python dump only (no range)
- Unit: probability; dimensions: scenario x case
- Formula: exact convolution, 20-node Gauss-Hermite over the shock
- Fed by: [INT-037](#INT-037), [OUT-060](#OUT-060), [LG-023](#LG-023)
- Feeds: [OUT-063](#OUT-063)
- Role: primary; response: Y; shock: Y; detail: core; client-safe: Y; status: display only
- References: spec 3 segment block; MR 6.6; sw/risk.py segment_exact; tests: 9; 13; 18

<a id="OUT-063"></a>

#### OUT-063 `exact_status_row`: Exact value status

'current' until the segment's expected enrollment, goal or cells change after the build; then 'stale'.

- Client label: "Exact value status (static value against the current segment enrollment and goal)"
- Excel: Summary segment block row 'Exact value status (static value against the current segment enrollment and goal)'
- Unit: text; dimensions: scenario
- Formula: IF(M_S, goal and segment equal their build values, current, stale)
- Fed by: [OUT-062](#OUT-062), [LG-023](#LG-023), [LG-034](#LG-034), [IN-106](#IN-106), [OUT-235](#OUT-235), [OUT-236](#OUT-236)
- Feeds: [CK-044](#CK-044)
- Role: display; response: Y; shock: N; detail: supporting; client-safe: Y; status: live
- References: P2-06; sw/workbook.py sw_segment; tests: 18

<a id="OUT-064"></a>

#### OUT-064 `segment_approximate`: Segment approximation flag

Shows the approximation text when fewer than 30 segment enrollees are expected.

- Client label: "Approximation flag"
- Excel: Summary segment block row 'Approximation flag'
- Unit: text; dimensions: scenario x case
- Formula: IF(M_S < 30, approximation text, blank)
- Fed by: [INT-036](#INT-036), [INT-040](#INT-040), [OUT-222](#OUT-222)
- Feeds: none
- Role: display; response: Y; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 segment block; sw/ledger.py SEGMENT_APPROX_BELOW; tests: 3; 13

<a id="OUT-065"></a>

#### OUT-065 `incentive_paid_anyway`: Incentive paid anyway

Incentive paid to students the parent scenario would have enrolled anyway: the smaller of parent and scenario enrolled times incentive, over cells with an incentive.

- Client label: "of which paid to students the parent already enrolled (C_any)"
- Excel: Summary incentive block row 'of which paid to students the parent already enrolled (C_any)'; named range INC_INCENTIVE_PAID_ANYWAY
- Unit: USD; dimensions: scenario x case
- Formula: C_any = sum min(e_parent, e_s) x incentive
- Fed by: [LG-029](#LG-029), [LG-035](#LG-035), [LG-030](#LG-030), [LG-037](#LG-037), [IN-090](#IN-090)
- Feeds: [OUT-066](#OUT-066)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 incentive block; App F 21; MR 7; sw/ledger.py incentive; tests: 3; 9; 13; 19

<a id="OUT-066"></a>

#### OUT-066 `incentive_paid_anyway_share`: Paid-anyway share

Share of the incentive cost paid to students enrolled anyway.

- Client label: "Paid-anyway share (C_any / C)"
- Excel: Summary incentive block row 'Paid-anyway share (C_any / C)'; named range INC_INCENTIVE_PAID_ANYWAY_SHARE
- Unit: ratio; dimensions: scenario x case
- Formula: C_any / C
- Fed by: [OUT-065](#OUT-065), [OUT-034](#OUT-034)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 incentive block; App F 21; tests: 3; 9; 13

<a id="OUT-067"></a>

#### OUT-067 `additional_enrollees`: Additional enrollees

Change in expected enrolled against the parent over cells with an incentive.

- Client label: "Additional enrollees (dE)"
- Excel: Summary incentive block row 'Additional enrollees (dE)'; named range INC_ADDITIONAL_ENROLLEES
- Unit: count; dimensions: scenario x case
- Formula: dE = sum (e_s - e_parent)
- Fed by: [LG-029](#LG-029), [LG-035](#LG-035), [LG-030](#LG-030), [LG-037](#LG-037), [IN-090](#IN-090)
- Feeds: [OUT-070](#OUT-070), [OUT-071](#OUT-071), [OUT-072](#OUT-072)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 incentive block; MR 7; tests: 3; 9; 13

<a id="OUT-068"></a>

#### OUT-068 `merit_change`: Change in merit dollars

Change in merit dollars against the parent over cells with an incentive.

- Client label: "Change in merit dollars (dSpend)"
- Excel: Summary incentive block row 'Change in merit dollars (dSpend)'
- Unit: USD; dimensions: scenario x case
- Formula: dSpend = sum (e_s a_s - e_parent a_parent)
- Fed by: [LG-029](#LG-029), [LG-035](#LG-035), [LG-030](#LG-030), [LG-037](#LG-037), [IN-090](#IN-090)
- Feeds: [OUT-070](#OUT-070)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 incentive block; MR 7; tests: 3; 13

<a id="OUT-069"></a>

#### OUT-069 `ntr_change`: Change in first-year NTR

Change in net tuition against the parent over the same cells.

- Client label: "Change in ntr_y1 over the same cells (dNTR)"
- Excel: Summary incentive block row 'Change in ntr_y1 over the same cells (dNTR)'
- Unit: USD; dimensions: scenario x case
- Formula: dNTR = sum (e_s w_s - e_parent w_parent)
- Fed by: [LG-029](#LG-029), [LG-035](#LG-035), [LG-030](#LG-030), [LG-037](#LG-037), [IN-090](#IN-090)
- Feeds: [OUT-072](#OUT-072)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 incentive block; tests: 3; 13

<a id="OUT-070"></a>

#### OUT-070 `aid_per_additional`: Aid per additional enrollee

Change in merit dollars per additional enrollee when the change is at least half a student either way; otherwise text.

- Client label: "Aid per additional enrollee (dSpend / dE)"
- Excel: Summary incentive block row 'Aid per additional enrollee (dSpend / dE)'; named range INC_AID_PER_ADDITIONAL
- Unit: USD; dimensions: scenario x case
- Formula: dSpend / dE if \|dE\| >= 0.5
- Fed by: [OUT-068](#OUT-068), [OUT-067](#OUT-067)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 incentive block; App F 20; tests: 3; 9; 13

<a id="OUT-071"></a>

#### OUT-071 `aid_per_additional_kind`: Reading of aid per additional enrollee

Says how to read the figure above: aid per additional enrollee, savings per enrollee lost, or change under half a student.

- Client label: "  reading"
- Excel: Summary incentive block row '  reading'
- Unit: text; dimensions: scenario x case
- Formula: by the sign and size of dE
- Fed by: [OUT-067](#OUT-067), [OUT-225](#OUT-225), [OUT-226](#OUT-226), [OUT-227](#OUT-227)
- Feeds: none
- Role: display; response: Y; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 incentive block; tests: 3; 13

<a id="OUT-072"></a>

#### OUT-072 `ntr_per_additional`: NTR change per additional enrollee

Change in net tuition per additional enrollee, on the same rule.

- Client label: "ntr_y1 change per additional enrollee (dNTR / dE)"
- Excel: Summary incentive block row 'ntr_y1 change per additional enrollee (dNTR / dE)'; named range INC_NTR_PER_ADDITIONAL
- Unit: USD; dimensions: scenario x case
- Formula: dNTR / dE if \|dE\| >= 0.5
- Fed by: [OUT-069](#OUT-069), [OUT-067](#OUT-067)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 incentive block; tests: 3; 9; 13

<a id="OUT-073"></a>

#### OUT-073 `incentive_cells`: Cells with an incentive

Number of cells receiving an incentive in the scenario.

- Client label: "Cells with an incentive"
- Excel: Summary incentive block row 'Cells with an incentive'
- Unit: count; dimensions: scenario x case
- Formula: count of cells with incentive > 0
- Fed by: [LG-029](#LG-029)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: sw/ledger.py incentive; tests: 3

<a id="OUT-074"></a>

#### OUT-074 `incentive_valid`: Incentive decomposition validity

'valid' when the scenario differs from its parent only in the incentive levers; otherwise the not-valid text.

- Client label: "Validity"
- Excel: Summary incentive block row 'Validity'; named range INC_INCENTIVE_VALID
- Unit: text; dimensions: scenario x case
- Formula: every validity lever and per-cell lever equals the parent's
- Fed by: [IN-095](#IN-095), [IN-096](#IN-096), [IN-097](#IN-097), [IN-093](#IN-093), [IN-094](#IN-094), [IN-098](#IN-098), [IN-099](#IN-099), [IN-105](#IN-105), [IN-107](#IN-107), [IN-108](#IN-108), [IN-109](#IN-109), [IN-110](#IN-110), [IN-092](#IN-092), [IN-104](#IN-104), [IN-112](#IN-112), [IN-113](#IN-113), [IN-114](#IN-114), [OUT-223](#OUT-223), [OUT-224](#OUT-224), [IN-090](#IN-090)
- Feeds: none
- Role: display; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 incentive block; sw/ledger.py VALIDITY_FIELDS; tests: 3; 9; 13

<a id="OUT-075"></a>

#### OUT-075 `bonus_implied_by_pool`: Bonus implied by a dollar pool

The dollar pool divided by Baseline's expected enrolled in the incentive's scope. Informational.

- Client label: "Bonus implied by a dollar pool (pool / Baseline enrolled in scope; informational)"
- Excel: Summary incentive block row 'Bonus implied by a dollar pool (pool / Baseline enrolled in scope; informational)'
- Unit: USD; dimensions: scenario
- Formula: bonus_pool_usd / SUMPRODUCT(Baseline enrolled, eligible)
- Fed by: [IN-103](#IN-103), [LG-035](#LG-035), [LG-024](#LG-024)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 incentive block; sw/ledger.py bonus_implied_by_pool; tests: 3; 19

<a id="OUT-076"></a>

#### OUT-076 `tuition_whatif`: Tuition what-if table

For each tuition increase on the grid, revenue with the scenario's class and mix held fixed and awards recomputed at the new tuition. No demand effect.

- Client label: "Tuition what-if (Middle case; class and mix held fixed)"
- Excel: Summary 'Tuition what-if' table; named range TW_TUITION_WHATIF (rows: scenario x grid value; columns: tuition, ntr_y1, net tuition per student, discount)
- Unit: USD; dimensions: scenario x grid value
- Formula: NTR(p) = sum_c e_c (T(p) - award_c(p)) - need - specialty
- Fed by: [LG-038](#LG-038), [LG-035](#LG-035), [LG-004](#LG-004), [INT-034](#INT-034), [IN-053](#IN-053)
- Feeds: [OUT-077](#OUT-077), [OUT-078](#OUT-078), [OUT-079](#OUT-079), [OUT-080](#OUT-080)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 tuition what-if; MR 7; sw/strip.py tuition; tests: 3; 8; 9; 15; 19

<a id="OUT-077"></a>

#### OUT-077 `tuition_whatif[tuition]`: What-if tuition

Tuition at the grid increase, rounded. One row per scenario and grid value.

- Client label: "tuition T(p)"
- Excel: Summary tuition what-if column 'tuition T(p)' (TW_TUITION_WHATIF)
- Unit: USD; dimensions: scenario x grid value
- Formula: round_to(tuition_base x (1 + p/100), unit)
- Fed by: [OUT-076](#OUT-076)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 tuition what-if; sw/contract.py strip_columns; tests: 3; 8; 9; 15; 19

<a id="OUT-078"></a>

#### OUT-078 `tuition_whatif[ntr_y1]`: What-if first-year NTR

First-year net tuition at the grid tuition. One row per scenario and grid value.

- Client label: "ntr_y1"
- Excel: Summary tuition what-if column 'ntr_y1' (TW_TUITION_WHATIF)
- Unit: USD; dimensions: scenario x grid value
- Formula: sum_c e_c (T(p) - award_c(p)) - need - K
- Fed by: [OUT-076](#OUT-076)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 tuition what-if; sw/contract.py strip_columns; tests: 3; 8; 9; 15; 19

<a id="OUT-079"></a>

#### OUT-079 `tuition_whatif[net_tuition_per_student]`: What-if net tuition per student

What-if ntr_y1 over the class. One row per scenario and grid value.

- Client label: "net tuition per student"
- Excel: Summary tuition what-if column 'net tuition per student' (TW_TUITION_WHATIF)
- Unit: USD; dimensions: scenario x grid value
- Formula: NTR(p) / class
- Fed by: [OUT-076](#OUT-076)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 tuition what-if; sw/contract.py strip_columns; tests: 3; 8; 9; 15; 19

<a id="OUT-080"></a>

#### OUT-080 `tuition_whatif[discount_entering_y1]`: What-if discount rate

What-if aid over what-if gross tuition. One row per scenario and grid value.

- Client label: "Discount rate (entering class, first year)"
- Excel: Summary tuition what-if column 'Discount rate (entering class, first year)' (TW_TUITION_WHATIF)
- Unit: ratio; dimensions: scenario x grid value
- Formula: (gross(p) - NTR(p)) / gross(p)
- Fed by: [OUT-076](#OUT-076)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 tuition what-if; sw/contract.py strip_columns; tests: 3; 8; 9; 15; 19

<a id="OUT-081"></a>

#### OUT-081 `tuition_increase_pct`: What-if tuition increase

The tuition grid value of each what-if row.

- Client label: "increase %"
- Excel: Summary tuition what-if column 'increase %'
- Unit: percent; dimensions: scenario x grid value
- Formula: = tuition grid
- Fed by: [IN-053](#IN-053)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 tuition what-if; tests: 3

<a id="OUT-082"></a>

#### OUT-082 `continuing_note`: Continuing revenue note

Under all_jd, says continuing revenue is held at the supplied figure; otherwise 'not used (entering_y1)'.

- Client label: "Continuing revenue (all_jd)"
- Excel: Summary tuition what-if row 'Continuing revenue (all_jd)'
- Unit: text; dimensions: scalar
- Formula: IF(all_jd, held text, not used)
- Fed by: [IN-035](#IN-035), [OUT-197](#OUT-197), [OUT-211](#OUT-211)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 0A A4; sw/strip.py tuition; tests: 25; 27

<a id="OUT-083"></a>

#### OUT-083 `net_tuition_line_fixed`: Fixed-dollar net-tuition line

With awards fixed in dollars, every student below full tuition pays this much more than at base-cycle tuition.

- Client label: "fixed-dollar line (T_s - T_base)"
- Excel: Summary net-tuition lines column 'fixed-dollar line (T_s - T_base)'; named range TW_NET_TUITION_LINE_FIXED; text line below
- Unit: USD; dimensions: scenario
- Formula: T_s - T_base
- Fed by: [LG-002](#LG-002), [IN-009](#IN-009)
- Feeds: [OUT-086](#OUT-086)
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 tuition what-if lines; sw/strip.py tuition; tests: 3; 9; 18; 19

<a id="OUT-084"></a>

#### OUT-084 `example_award`: Example award for the scaled line

Enrolled-weighted mean base-cycle lever award over enrollees below base-cycle tuition without the full-tuition flag, zero awards included, rounded to $1,000. The example in the scaled line.

- Client label: "example award A"
- Excel: Summary net-tuition lines column 'example award A'
- Unit: USD; dimensions: scenario
- Formula: ROUND(sum e x award_usd / sum e over qualifying cells, -3)
- Fed by: [IN-113](#IN-113), [IN-114](#IN-114), [LG-035](#LG-035), [IN-009](#IN-009)
- Feeds: [OUT-085](#OUT-085)
- Role: derived; response: Y; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 tuition what-if lines (Q-5); sw/strip.py tuition; tests: 3; 18; 19

<a id="OUT-085"></a>

#### OUT-085 `net_tuition_line_scaled`: Scaled net-tuition line

With awards scaled with tuition, the extra amount a student with the example award pays.

- Client label: "scaled line p (T_base - A)"
- Excel: Summary net-tuition lines column 'scaled line p (T_base - A)'; named range TW_NET_TUITION_LINE_SCALED; text line below
- Unit: USD; dimensions: scenario
- Formula: p x (T_base - A)
- Fed by: [LG-003](#LG-003), [IN-009](#IN-009), [OUT-084](#OUT-084)
- Feeds: [OUT-086](#OUT-086)
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 tuition what-if lines; sw/strip.py tuition; tests: 3; 9; 18; 19

<a id="OUT-086"></a>

#### OUT-086 `net_tuition_line_fixed_text`: Net-tuition lines (text)

The two net-tuition lines as sentences.

- Client label: "Awards fixed in dollars: every student below full tuition pays {diff} more than at base-cycle tuition. / Awards scaled with tuition: ..."
- Excel: Summary net-tuition lines, two text rows per scenario
- Unit: text; dimensions: scenario
- Formula: text from the two line values
- Fed by: [OUT-083](#OUT-083), [OUT-085](#OUT-085), [OUT-188](#OUT-188), [OUT-189](#OUT-189)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 tuition what-if lines; tests: 3; 18

<a id="OUT-087"></a>

#### OUT-087 `yield_strip`: Yield what-if strip

For each uniform yield shift on the grid (added to the scenario's own), the class, revenue and median figures in closed form over the Ledger columns. Ignores the yield floor and cap.

- Client label: "Yield what-if strip (Middle case; shift on top of the scenario's own shift)"
- Excel: Summary 'Yield what-if strip' table; named range YS_YIELD_STRIP (rows: scenario x shift)
- Unit: count; dimensions: scenario x grid value
- Formula: M(d) = sum A (y + d); V(d) = sum A (y + d)(1 - y - d) + s^2 M(d)^2
- Fed by: [LG-027](#LG-027), [LG-032](#LG-032), [LG-037](#LG-037), [INT-034](#INT-034), [IN-041](#IN-041), [IN-051](#IN-051)
- Feeds: [OUT-088](#OUT-088), [OUT-089](#OUT-089), [OUT-090](#OUT-090), [OUT-091](#OUT-091), [OUT-092](#OUT-092), [OUT-093](#OUT-093), [OUT-094](#OUT-094)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 yield strip; MR 7; sw/strip.py yield_strip; tests: 3; 8; 9; 15; 19

<a id="OUT-088"></a>

#### OUT-088 `yield_strip[class_mean]`: Strip expected class

Yield-strip column: expected class at each shift d.

- Client label: "expected class"
- Excel: Summary yield strip column 'expected class' (YS_YIELD_STRIP)
- Unit: count; dimensions: scenario x grid value
- Formula: M(d)
- Fed by: [OUT-087](#OUT-087)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 yield strip; sw/contract.py strip_columns; tests: 3; 8; 9; 15

<a id="OUT-089"></a>

#### OUT-089 `yield_strip[p_class_over_cap]`: Strip P(class above cap)

Yield-strip column: p(class above cap) at each shift d.

- Client label: "P(class above cap)"
- Excel: Summary yield strip column 'P(class above cap)' (YS_YIELD_STRIP)
- Unit: probability; dimensions: scenario x grid value
- Formula: 1 - Phi((cap + 0.5 - M(d)) / sqrt(V(d)))
- Fed by: [OUT-087](#OUT-087)
- Feeds: none
- Role: derived; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 3 yield strip; sw/contract.py strip_columns; tests: 3; 8; 9; 15

<a id="OUT-090"></a>

#### OUT-090 `yield_strip[p_class_in_band]`: Strip P(class within band)

Yield-strip column: p(class within band) at each shift d.

- Client label: "P(class within band)"
- Excel: Summary yield strip column 'P(class within band)' (YS_YIELD_STRIP)
- Unit: probability; dimensions: scenario x grid value
- Formula: band probability at M(d), V(d)
- Fed by: [OUT-087](#OUT-087)
- Feeds: none
- Role: derived; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 3 yield strip; sw/contract.py strip_columns; tests: 3; 8; 9; 15

<a id="OUT-091"></a>

#### OUT-091 `yield_strip[ntr_mean]`: Strip mean ntr_y1

Yield-strip column: mean ntr_y1 at each shift d.

- Client label: "mean ntr_y1"
- Excel: Summary yield strip column 'mean ntr_y1' (YS_YIELD_STRIP)
- Unit: USD; dimensions: scenario x grid value
- Formula: sum w A (y + d) - K
- Fed by: [OUT-087](#OUT-087)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 yield strip; sw/contract.py strip_columns; tests: 3; 8; 9; 15

<a id="OUT-092"></a>

#### OUT-092 `yield_strip[p_ntr_y1_ge_target]`: Strip P(ntr_y1 at or above target)

Yield-strip column: p(ntr_y1 at or above target) at each shift d.

- Client label: "P(ntr_y1 at or above target)"
- Excel: Summary yield strip column 'P(ntr_y1 at or above target)' (YS_YIELD_STRIP)
- Unit: probability; dimensions: scenario x grid value
- Formula: 1 - Phi((target_eff - mean(d)) / sqrt(V_n(d)))
- Fed by: [OUT-087](#OUT-087)
- Feeds: none
- Role: derived; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 3 yield strip; sw/contract.py strip_columns; tests: 3; 8; 9; 15

<a id="OUT-093"></a>

#### OUT-093 `yield_strip[margin_{measure}_{t}]`: Strip median margin

Yield-strip column: median margin at each shift d.

- Client label: "margin {measure} {t}"
- Excel: Summary yield strip column 'margin {measure} {t}' (YS_YIELD_STRIP)
- Unit: count; dimensions: scenario x grid value x target
- Formula: sum g A (y + d)
- Fed by: [OUT-087](#OUT-087), [INT-030](#INT-030), [INT-024](#INT-024)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 yield strip; sw/contract.py strip_columns; tests: 3; 8; 9; 15; 27

<a id="OUT-094"></a>

#### OUT-094 `yield_strip[p_median_{measure}_{t}]`: Strip P(median holds)

Yield-strip column: p(median holds) at each shift d.

- Client label: "P(median) {measure} {t}"
- Excel: Summary yield strip column 'P(median) {measure} {t}' (YS_YIELD_STRIP)
- Unit: probability; dimensions: scenario x grid value x target
- Formula: median probability at shift d
- Fed by: [OUT-087](#OUT-087), [INT-024](#INT-024)
- Feeds: none
- Role: derived; response: Y; shock: Y; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 yield strip; sw/contract.py strip_columns; tests: 3; 8; 9; 15; 27

<a id="OUT-095"></a>

#### OUT-095 `shift_pts`: Strip yield shift

The shift d of each yield-strip row.

- Client label: "shift (pts)"
- Excel: Summary yield strip column 'shift (pts)'
- Unit: points; dimensions: scenario x grid value
- Formula: = yield shift grid
- Fed by: [IN-051](#IN-051)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 yield strip; tests: 3

<a id="OUT-096"></a>

#### OUT-096 `clip_count`: Yield-strip clip count

Cells with admits whose yield would cross the floor or cap at the largest or smallest grid shift. While it is zero the strip equals the Ledger with the shift entered.

- Client label: "cells where a bound would bind at the largest shift"
- Excel: Summary 'Yield strip: clip count and break-even shifts' column 'cells where a bound would bind at the largest shift'
- Unit: count; dimensions: scenario
- Formula: count of cells with A > 0 and (y + max d > cap or y + min d < floor)
- Fed by: [LG-027](#LG-027), [LG-032](#LG-032), [LG-017](#LG-017), [LG-016](#LG-016), [IN-051](#IN-051)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 yield strip; sw/strip.py yield_strip; tests: 3; 15; 19

<a id="OUT-097"></a>

#### OUT-097 `breakeven_shift_class`: Break-even shift for the class

The uniform yield shift (points) that moves the expected class to the target, unclipped.

- Client label: "shift that moves the expected class to target (linear approximation)"
- Excel: Summary yield strip break-evens column 'shift that moves the expected class to target (linear approximation)'; named range YS_BREAKEVEN_SHIFT_CLASS
- Unit: points; dimensions: scenario
- Formula: (class_target - M) / sum A x 100
- Fed by: [LG-027](#LG-027), [LG-032](#LG-032), [IN-098](#IN-098)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 yield strip; MR 7; sw/strip.py yield_strip; tests: 3; 8; 9; 19

<a id="OUT-098"></a>

#### OUT-098 `breakeven_shift_ntr`: Break-even shift for revenue

The uniform yield shift that moves mean ntr_y1 to the effective target, unclipped; blank with no target.

- Client label: "shift that moves mean ntr_y1 to ntr_target (linear approximation)"
- Excel: Summary yield strip break-evens column 'shift that moves mean ntr_y1 to ntr_target (linear approximation)'; named range YS_BREAKEVEN_SHIFT_NTR
- Unit: points; dimensions: scenario
- Formula: (target_eff - mean) / sum w A x 100
- Fed by: [LG-027](#LG-027), [LG-032](#LG-032), [LG-037](#LG-037), [INT-034](#INT-034), [INT-020](#INT-020)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: N; status: live
- References: spec 3 yield strip; spec 0A A4; sw/strip.py yield_strip; tests: 3; 9; 19; 25

<a id="OUT-099"></a>

#### OUT-099 `pool_strip`: Pool strip

For each pool multiplier m on the grid, replacing the scenario's: class, cap probability, revenue and median and percentile figures. Each quantity is a below-threshold part plus m times an above-threshold part.

- Client label: "Pool strip (Middle case): yield held constant as the pool changes"
- Excel: Summary 'Pool strip' table; named range PS_POOL_STRIP (rows: scenario x pool multiplier)
- Unit: count; dimensions: scenario x grid value
- Formula: X(m) = X_lo + m X_hi; V(m) = V_lo + m V_hi + s^2 M(m)^2
- Fed by: [INT-042](#INT-042), [INT-043](#INT-043), [INT-044](#INT-044), [INT-045](#INT-045), [INT-046](#INT-046), [INT-047](#INT-047), [INT-048](#INT-048), [INT-049](#INT-049), [IN-052](#IN-052)
- Feeds: [OUT-100](#OUT-100), [OUT-101](#OUT-101), [OUT-102](#OUT-102), [OUT-103](#OUT-103), [OUT-104](#OUT-104), [OUT-105](#OUT-105), [OUT-106](#OUT-106), [OUT-107](#OUT-107), [OUT-108](#OUT-108)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 pool strip; spec 0A A6; MR 7; sw/strip.py pool_strip; tests: 3; 9; 15; 24

<a id="OUT-100"></a>

#### OUT-100 `pool_strip[growth]`: Pool growth

Pool-strip column: pool growth at each pool multiplier m.

- Client label: "growth (m - 1)"
- Excel: Summary pool strip column 'growth (m - 1)' (PS_POOL_STRIP)
- Unit: rate; dimensions: scenario x grid value
- Formula: m - 1
- Fed by: [OUT-099](#OUT-099)
- Feeds: none
- Role: display; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 pool strip; spec 0A A6; sw/contract.py strip_columns; tests: 3; 9; 15

<a id="OUT-101"></a>

#### OUT-101 `pool_strip[class_mean]`: Pool-strip expected class

Pool-strip column: expected class at each pool multiplier m.

- Client label: "expected class"
- Excel: Summary pool strip column 'expected class' (PS_POOL_STRIP)
- Unit: count; dimensions: scenario x grid value
- Formula: M_lo + m M_hi
- Fed by: [OUT-099](#OUT-099)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 pool strip; spec 0A A6; sw/contract.py strip_columns; tests: 3; 9; 15

<a id="OUT-102"></a>

#### OUT-102 `pool_strip[p_class_over_cap]`: Pool-strip P(class above cap)

Pool-strip column: p(class above cap) at each pool multiplier m.

- Client label: "P(class above cap)"
- Excel: Summary pool strip column 'P(class above cap)' (PS_POOL_STRIP)
- Unit: probability; dimensions: scenario x grid value
- Formula: 1 - Phi((cap + 0.5 - M(m)) / sqrt(V(m)))
- Fed by: [OUT-099](#OUT-099)
- Feeds: none
- Role: derived; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 3 pool strip; spec 0A A6; sw/contract.py strip_columns; tests: 3; 9; 15

<a id="OUT-103"></a>

#### OUT-103 `pool_strip[ntr_mean]`: Pool-strip mean ntr_y1

Pool-strip column: mean ntr_y1 at each pool multiplier m.

- Client label: "mean ntr_y1"
- Excel: Summary pool strip column 'mean ntr_y1' (PS_POOL_STRIP)
- Unit: USD; dimensions: scenario x grid value
- Formula: W_lo + m W_hi - K
- Fed by: [OUT-099](#OUT-099)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 pool strip; spec 0A A6; sw/contract.py strip_columns; tests: 3; 9; 15

<a id="OUT-104"></a>

#### OUT-104 `pool_strip[ntr_sd]`: Pool-strip SD of ntr_y1

Pool-strip column: sd of ntr_y1 at each pool multiplier m.

- Client label: "SD of ntr_y1"
- Excel: Summary pool strip column 'SD of ntr_y1' (PS_POOL_STRIP)
- Unit: USD; dimensions: scenario x grid value
- Formula: sqrt(Vn_lo + m Vn_hi + s^2 W(m)^2)
- Fed by: [OUT-099](#OUT-099)
- Feeds: none
- Role: derived; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 3 pool strip; spec 0A A6; sw/contract.py strip_columns; tests: 3; 9; 15

<a id="OUT-105"></a>

#### OUT-105 `pool_strip[margin_score_{t}]`: Pool-strip median margin

Pool-strip column: median margin at each pool multiplier m.

- Client label: "median margin {t}"
- Excel: Summary pool strip column 'median margin {t}' (PS_POOL_STRIP)
- Unit: count; dimensions: scenario x grid value x target
- Formula: G+(m) - G-(m)
- Fed by: [OUT-099](#OUT-099), [INT-024](#INT-024)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 pool strip; spec 0A A6; sw/contract.py strip_columns; tests: 3; 9; 15; 27

<a id="OUT-106"></a>

#### OUT-106 `pool_strip[p_median_score_{t}]`: Pool-strip P(median holds)

Pool-strip column: p(median holds) at each pool multiplier m.

- Client label: "P(median) {t}"
- Excel: Summary pool strip column 'P(median) {t}' (PS_POOL_STRIP)
- Unit: probability; dimensions: scenario x grid value x target
- Formula: 1 - Phi((-0.5 - G(m)) / sqrt(V_m(m)))
- Fed by: [OUT-099](#OUT-099), [INT-024](#INT-024)
- Feeds: none
- Role: derived; response: Y; shock: Y; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 pool strip; spec 0A A6; sw/contract.py strip_columns; tests: 3; 9; 15; 27

<a id="OUT-107"></a>

#### OUT-107 `pool_strip[p_pct_q{q}_{t}]`: Pool-strip P(percentile holds)

Pool-strip column: p(percentile holds) at each pool multiplier m.

- Client label: "P({ordinal} percentile at or above {t})"
- Excel: Summary pool strip column 'P({ordinal} percentile at or above {t})' (PS_POOL_STRIP)
- Unit: probability; dimensions: scenario x grid value x target
- Formula: percentile probability from the split parts at m
- Fed by: [OUT-099](#OUT-099), [INT-024](#INT-024)
- Feeds: none
- Role: derived; response: Y; shock: Y; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 pool strip; spec 0A A6; sw/contract.py strip_columns; tests: 3; 9; 15; 27

<a id="OUT-108"></a>

#### OUT-108 `pool_strip[marker]`: Growth-to-date marker

Pool-strip column: growth-to-date marker at each pool multiplier m.

- Client label: "growth to date"
- Excel: Summary pool strip column 'growth to date' (PS_POOL_STRIP)
- Unit: text; dimensions: scenario x grid value
- Formula: marker text on the row nearest 1 + pool_ytd_growth
- Fed by: [OUT-099](#OUT-099), [IN-068](#IN-068), [IN-069](#IN-069), [INT-051](#INT-051), [OUT-199](#OUT-199)
- Feeds: none
- Role: display; response: Y; shock: N; detail: core; client-safe: Y; status: display only
- References: spec 3 pool strip; spec 0A A6; sw/contract.py strip_columns; tests: 3; 9; 15; 24; 26

<a id="OUT-109"></a>

#### OUT-109 `pool_multiplier`: Strip pool multiplier

The pool multiplier m of each pool-strip row.

- Client label: "pool multiplier m"
- Excel: Summary pool strip column 'pool multiplier m'
- Unit: multiplier; dimensions: scenario x grid value
- Formula: = pool grid
- Fed by: [IN-052](#IN-052)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 pool strip; tests: 3

<a id="OUT-110"></a>

#### OUT-110 `nearest_m`: Growth to date and nearest pool multiplier

The reported growth to date, its date and the grid multiplier nearest 1 + growth (a tie goes to the upper row).

- Client label: "Pool growth to date, its date, and the pool multiplier m nearest 1 + growth"
- Excel: Summary pool strip row 'Pool growth to date, its date, and the pool multiplier m nearest 1 + growth'
- Unit: multiplier; dimensions: scalar
- Formula: INDEX(pool grid, 1 + count of midpoints <= 1 + growth)
- Fed by: [IN-068](#IN-068), [IN-069](#IN-069), [INT-051](#INT-051)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: display only
- References: spec 0A A6; R4-13; sw/strip.py pool_strip; tests: 24; 26

<a id="OUT-111"></a>

#### OUT-111 `pool_breakeven_m`: Break-even pool multipliers

The pool multiplier at which the expected class meets the target, or an expected median or percentile margin is zero. Expectations, not probabilities; a note replaces a number off the grid, and 'at most m' marks a ceiling.

- Client label: "Break-even pool multipliers (Middle case)"
- Excel: Summary 'Break-even pool multipliers' table; named range PS_POOL_BREAKEVEN_M (rows: scenarios; columns: class, each median threshold, each other percentile target)
- Unit: multiplier; dimensions: scenario x target
- Formula: m_class = (target - M_lo) / M_hi; m_q = -E[M_q]_lo / E[M_q]_hi
- Fed by: [INT-042](#INT-042), [INT-046](#INT-046), [INT-047](#INT-047), [IN-098](#IN-098), [IN-052](#IN-052), [INT-050](#INT-050)
- Feeds: [OUT-112](#OUT-112), [OUT-113](#OUT-113), [OUT-114](#OUT-114)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 0A A6; R4-04; F-2; MR 7; sw/strip.py breakeven_m; tests: 3; 9; 24

<a id="OUT-112"></a>

#### OUT-112 `pool_breakeven_m[m_class]`: Break-even pool multiplier for the class

Break-even pool multiplier for the class: a number, 'at most m', or a note.

- Client label: "expected class meets the target"
- Excel: Summary break-even table column 'expected class meets the target' (PS_POOL_BREAKEVEN_M)
- Unit: multiplier; dimensions: scenario
- Formula: see the break-even table
- Fed by: [OUT-111](#OUT-111)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 0A A6; R4-04; sw/contract.py POOL_BE; tests: 3; 9; 24

<a id="OUT-113"></a>

#### OUT-113 `pool_breakeven_m[m_median]`: Break-even pool multiplier for a median

Break-even pool multiplier for a median: a number, 'at most m', or a note.

- Client label: "expected median margin zero: {measure} {t}"
- Excel: Summary break-even table column 'expected median margin zero: {measure} {t}' (PS_POOL_BREAKEVEN_M)
- Unit: multiplier; dimensions: scenario x target
- Formula: see the break-even table
- Fed by: [OUT-111](#OUT-111), [INT-024](#INT-024)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 0A A6; R4-04; sw/contract.py POOL_BE; tests: 3; 9; 24; 27

<a id="OUT-114"></a>

#### OUT-114 `pool_breakeven_m[m_q]`: Break-even pool multiplier for a percentile

Break-even pool multiplier for a percentile: a number, 'at most m', or a note.

- Client label: "expected margin zero: {ordinal} percentile at {t}"
- Excel: Summary break-even table column 'expected margin zero: {ordinal} percentile at {t}' (PS_POOL_BREAKEVEN_M)
- Unit: multiplier; dimensions: scenario x target
- Formula: see the break-even table
- Fed by: [OUT-111](#OUT-111), [INT-024](#INT-024)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 0A A6; R4-04; sw/contract.py POOL_BE; tests: 3; 9; 24; 27

<a id="OUT-115"></a>

#### OUT-115 `class_table`: Class-size table

For each class size N up to the cap, the shrink path cuts admit rates in a fixed order to reach N, and the table shows the class, cap probability, margins, revenue, segment and the admits cut by band.

- Client label: "Class-size table (shrink path; Middle case)"
- Excel: Summary 'Class-size table (shrink path; Middle case)'; named range CT_CLASS_TABLE (rows: scenario x N); live builds only
- Unit: count; dimensions: scenario x N
- Formula: figures re-evaluated at the trimmed admit rates
- Fed by: [INT-057](#INT-057), [INT-052](#INT-052), [IN-029](#IN-029), [LG-034](#LG-034), [INT-059](#INT-059)
- Feeds: [OUT-116](#OUT-116), [OUT-117](#OUT-117), [OUT-118](#OUT-118), [OUT-119](#OUT-119), [OUT-120](#OUT-120), [OUT-121](#OUT-121), [OUT-122](#OUT-122), [OUT-123](#OUT-123), [OUT-124](#OUT-124), [OUT-125](#OUT-125), [OUT-126](#OUT-126), [OUT-127](#OUT-127), [OUT-128](#OUT-128)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 class-size table, shrink path; spec 0A A3; MR 7; sw/trim.py class_table; tests: 3; 9; 14; 16; 18

<a id="OUT-116"></a>

#### OUT-116 `class_table[f]`: Proportional factor

Class-size table column: proportional factor at each N.

- Client label: "f = N / M"
- Excel: Summary class-size table column 'f = N / M' (CT_CLASS_TABLE)
- Unit: ratio; dimensions: scenario x N
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115)
- Feeds: none
- Role: display; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14

<a id="OUT-117"></a>

#### OUT-117 `class_table[class_mean]`: Class-table expected class

Class-size table column: expected class at each N.

- Client label: "expected class"
- Excel: Summary class-size table column 'expected class' (CT_CLASS_TABLE)
- Unit: count; dimensions: scenario x N
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14

<a id="OUT-118"></a>

#### OUT-118 `class_table[p_class_over_cap]`: Class-table P(class above cap)

Class-size table column: p(class above cap) at each N.

- Client label: "P(class above cap)"
- Excel: Summary class-size table column 'P(class above cap)' (CT_CLASS_TABLE)
- Unit: probability; dimensions: scenario x N
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115)
- Feeds: none
- Role: derived; response: Y; shock: Y; detail: core; client-safe: Y; status: live
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14

<a id="OUT-119"></a>

#### OUT-119 `class_table[margin_{measure}_{t}]`: Class-table median margin

Class-size table column: median margin at each N.

- Client label: "margin {measure} {t}"
- Excel: Summary class-size table column 'margin {measure} {t}' (CT_CLASS_TABLE)
- Unit: count; dimensions: scenario x N x target
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115), [INT-024](#INT-024)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14; 27

<a id="OUT-120"></a>

#### OUT-120 `class_table[p_median_{measure}_{t}]`: Class-table P(median holds)

Class-size table column: p(median holds) at each N.

- Client label: "P(median) {measure} {t}"
- Excel: Summary class-size table column 'P(median) {measure} {t}' (CT_CLASS_TABLE)
- Unit: probability; dimensions: scenario x N x target
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115), [INT-024](#INT-024)
- Feeds: none
- Role: derived; response: Y; shock: Y; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14; 27

<a id="OUT-121"></a>

#### OUT-121 `class_table[margin_q{q}_{t}]`: Class-table percentile margin

Class-size table column: percentile margin at each N.

- Client label: "margin {ordinal} pct {t} (swaps)"
- Excel: Summary class-size table column 'margin {ordinal} pct {t} (swaps)' (CT_CLASS_TABLE)
- Unit: count; dimensions: scenario x N x target
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115), [INT-024](#INT-024)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14; 27

<a id="OUT-122"></a>

#### OUT-122 `class_table[p_pct_q{q}_{t}]`: Class-table P(percentile holds)

Class-size table column: p(percentile holds) at each N.

- Client label: "P({ordinal} pct at or above {t})"
- Excel: Summary class-size table column 'P({ordinal} pct at or above {t})' (CT_CLASS_TABLE)
- Unit: probability; dimensions: scenario x N x target
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115), [INT-024](#INT-024)
- Feeds: none
- Role: derived; response: Y; shock: Y; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14; 27

<a id="OUT-123"></a>

#### OUT-123 `class_table[ntr_y1]`: Class-table ntr_y1

Class-size table column: ntr_y1 at each N.

- Client label: "ntr_y1"
- Excel: Summary class-size table column 'ntr_y1' (CT_CLASS_TABLE)
- Unit: USD; dimensions: scenario x N
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14

<a id="OUT-124"></a>

#### OUT-124 `class_table[discount_entering_y1]`: Class-table discount rate

Class-size table column: discount rate at each N.

- Client label: "Discount rate (entering class, first year)"
- Excel: Summary class-size table column 'Discount rate (entering class, first year)' (CT_CLASS_TABLE)
- Unit: ratio; dimensions: scenario x N
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14

<a id="OUT-125"></a>

#### OUT-125 `class_table[segment_enrolled]`: Class-table segment enrolled

Class-size table column: segment enrolled at each N.

- Client label: "segment enrolled"
- Excel: Summary class-size table column 'segment enrolled' (CT_CLASS_TABLE)
- Unit: count; dimensions: scenario x N
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14

<a id="OUT-126"></a>

#### OUT-126 `class_table[lowest_band_admitted]`: Lowest band admitted

Class-size table column: lowest band admitted at each N.

- Client label: "lowest band admitted"
- Excel: Summary class-size table column 'lowest band admitted' (CT_CLASS_TABLE)
- Unit: score; dimensions: scenario x N
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14

<a id="OUT-127"></a>

#### OUT-127 `class_table[cut_{band}]`: Admits cut by band

Class-size table column: admits cut by band at each N.

- Client label: "admits cut, {band}"
- Excel: Summary class-size table column 'admits cut, {band}' (CT_CLASS_TABLE)
- Unit: count; dimensions: scenario x N x band
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115), [OUT-214](#OUT-214)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14

<a id="OUT-128"></a>

#### OUT-128 `class_table[status]`: Class-table row status

Class-size table column: row status at each N.

- Client label: "status"
- Excel: Summary class-size table column 'status' (CT_CLASS_TABLE)
- Unit: text; dimensions: scenario x N
- Formula: see the class-size table
- Fed by: [OUT-115](#OUT-115), [OUT-228](#OUT-228), [OUT-229](#OUT-229), [OUT-230](#OUT-230), [OUT-231](#OUT-231), [INT-058](#INT-058)
- Feeds: none
- Role: display; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 3 class-size table; sw/contract.py strip_columns; tests: 3; 9; 14

<a id="OUT-129"></a>

#### OUT-129 `N`: Class size N

The class size of each class-size table row (from the class what-if list).

- Client label: "N"
- Excel: Summary class-size table column 'N'
- Unit: count; dimensions: scenario x N
- Formula: = class what-if list
- Fed by: [IN-029](#IN-029)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 3 class-size table; tests: 3; 14

<a id="OUT-130"></a>

#### OUT-130 `changes`: Narrative: changes from parent

Sentence giving the pool multiplier and how many awards and admit rates differ from the parent, with any ignored award entries. Baseline reads 'Baseline: no parent scenario.'

- Client label: "Changes from parent"
- Excel: Summary 'Narratives (Middle case)', row 'Changes from parent' per scenario
- Unit: text; dimensions: scenario
- Formula: template filled from Levers counts
- Fed by: [IN-095](#IN-095), [OUT-132](#OUT-132), [OUT-133](#OUT-133), [OUT-135](#OUT-135), [OUT-233](#OUT-233), [OUT-234](#OUT-234)
- Feeds: none
- Role: display; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 8; sw/narrative.py changes; tests: 3; 18

<a id="OUT-131"></a>

#### OUT-131 `outcome`: Narrative: projected outcome

Sentence summarizing class and range, each median's margin and probability, count below the floor, full-tuition and no-award counts, NTR and range, discount, tuition, target and cap, incentive, segment and evidence share, followed by the labels that apply.

- Client label: "Projected outcome"
- Excel: Summary 'Narratives (Middle case)', row 'Projected outcome' per scenario
- Unit: text; dimensions: scenario
- Formula: template filled from Summary figures
- Fed by: [OUT-008](#OUT-008), [OUT-009](#OUT-009), [OUT-010](#OUT-010), [OUT-019](#OUT-019), [OUT-020](#OUT-020), [OUT-015](#OUT-015), [OUT-029](#OUT-029), [OUT-030](#OUT-030), [OUT-038](#OUT-038), [OUT-039](#OUT-039), [OUT-040](#OUT-040), [OUT-047](#OUT-047), [LG-002](#LG-002), [OUT-055](#OUT-055), [OUT-051](#OUT-051), [OUT-205](#OUT-205), [IN-013](#IN-013), [INT-038](#INT-038), [INT-024](#INT-024)
- Feeds: none
- Role: display; response: Y; shock: N; detail: core; client-safe: Y; status: held under hold_position_rows
- References: spec 8; F-1; sw/narrative.py outcome; tests: 3; 18; 27

<a id="OUT-132"></a>

#### OUT-132 `awards_changed`: Awards changed from parent

Cells whose award or full-tuition flag differs from the parent's (entries ignored under the flag excluded).

- Client label: "awards changed from parent (cells)"
- Excel: Levers row 'awards changed from parent (cells)'
- Unit: count; dimensions: scenario
- Formula: count of changed award cells
- Fed by: [IN-113](#IN-113), [IN-114](#IN-114), [IN-090](#IN-090)
- Feeds: [OUT-130](#OUT-130)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 6 Levers; P2-03; sw/ledger.py award_changes; tests: 3; 18; 19

<a id="OUT-133"></a>

#### OUT-133 `rates_changed`: Admit rates changed from parent

Cells whose admit rate differs from the parent's.

- Client label: "admit rates changed from parent (cells)"
- Excel: Levers row 'admit rates changed from parent (cells)'
- Unit: count; dimensions: scenario
- Formula: count of rate cells <> parent
- Fed by: [IN-112](#IN-112), [IN-090](#IN-090)
- Feeds: [OUT-130](#OUT-130)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 6 Levers; sw/workbook.py w_levers; tests: 3; 18

<a id="OUT-134"></a>

#### OUT-134 `vrow_cells_changed`: Cells changed from parent

Cells where any per-cell lever differs from the parent's.

- Client label: "cells changed from parent (any lever)"
- Excel: Levers row 'cells changed from parent (any lever)'
- Unit: count; dimensions: scenario
- Formula: count of cells with any change
- Fed by: [IN-112](#IN-112), [IN-113](#IN-113), [IN-114](#IN-114), [IN-090](#IN-090)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 6 Levers; tests: 3; 18

<a id="OUT-135"></a>

#### OUT-135 `awards_ignored`: Award entries ignored

Award entries typed on full-tuition cells, which are ignored while the flag is set; counted apart from changes and listed on Checks.

- Client label: "award entries ignored (full-tuition flag set)"
- Excel: Levers row 'award entries ignored (full-tuition flag set)'; Levers note column
- Unit: count; dimensions: scenario
- Formula: count of flagged cells whose award differs from the inherited value
- Fed by: [IN-113](#IN-113), [IN-114](#IN-114), [OUT-232](#OUT-232)
- Feeds: [OUT-130](#OUT-130)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 6 Levers; P2-03; sw/ledger.py full_tuition_conflicts; tests: 18; 19

<a id="OUT-136"></a>

#### OUT-136 `AWARD_MATRIX`: Award matrix

The resolved Middle-case award for every cell and scenario: what the policy document carries.

- Client label: "Award matrix (resolved award, plan-year dollars: after the full-tuition flag and the incentive). Named range AWARD_MATRIX."
- Excel: Levers 'Award matrix' block; named range AWARD_MATRIX (rows: cells; columns: scenarios)
- Unit: USD; dimensions: scenario x cell
- Formula: = Ledger_Middle award
- Fed by: [LG-030](#LG-030)
- Feeds: none
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 15 items 5 and 11; Q-3; sw/ledger.py awards; tests: 3; 9; 19

<a id="OUT-137"></a>

#### OUT-137 `admit rate`: History admit rate

Admits over applications per cell and cohort; the latest cohort's is Baseline's admit rate.

- Client label: "Admit rate"
- Excel: History panel 'Admit rate'
- Unit: rate; dimensions: cell x cohort
- Formula: admits / applications
- Fed by: [IN-122](#IN-122), [IN-121](#IN-121)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 6 History; App F 3, 5; tests: 3

<a id="OUT-138"></a>

#### OUT-138 `award % of tuition`: History award as share of tuition

Award over that cohort's tuition per cell and cohort.

- Client label: "Award % of tuition"
- Excel: History panel 'Award % of tuition'
- Unit: ratio; dimensions: cell x cohort
- Formula: award / tuition_by_cohort
- Fed by: [IN-123](#IN-123), [IN-008](#IN-008)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 6 History; App F 3, 5; tests: 3

<a id="OUT-139"></a>

#### OUT-139 `history yield`: History yield

Enrolled over admits per cell and cohort; base yield pools these.

- Client label: "Yield"
- Excel: History panel 'Yield'
- Unit: rate; dimensions: cell x cohort
- Formula: enrolled / admits
- Fed by: [IN-124](#IN-124), [IN-122](#IN-122)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 6 History; App F 3, 5; tests: 3

<a id="OUT-140"></a>

#### OUT-140 `history totals`: History totals

Panel totals by residency, segment and overall (award as an admit-weighted mean). Checks compares the groups with the overall total.

- Client label: "Total {group}"
- Excel: History rows 'Total in-state', 'Total out-of-state', 'Total segment {name}', 'Total outside any segment', 'Total'
- Unit: count; dimensions: group x cohort
- Formula: SUMPRODUCT by group
- Fed by: [IN-121](#IN-121), [IN-122](#IN-122), [IN-124](#IN-124), [IN-123](#IN-123), [IN-116](#IN-116), [IN-117](#IN-117)
- Feeds: [CK-018](#CK-018), [CK-019](#CK-019)
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 6 History; sw/workbook.py w_history; tests: 3

<a id="OUT-141"></a>

#### OUT-141 `history tuition row`: History tuition row

Tuition by cohort, shown with the panels.

- Client label: "Tuition (published, first year)"
- Excel: History row 'Tuition (published, first year)'
- Unit: USD; dimensions: cohort
- Formula: = tuition_by_cohort
- Fed by: [IN-008](#IN-008)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 6 History; tests: 3

<a id="OUT-142"></a>

#### OUT-142 `aba509_reconciliation[first_year_class]`: 509 check: first-year class

The cell data's count (first-year class) beside the published ABA 509 figure, and whether they agree. Report only.

- Client label: "first-year class"
- Excel: History 509 block row 'first-year class' (columns: cells, 509, verdict per cohort)
- Unit: count; dimensions: cohort
- Formula: cells: SUM over cells; verdict: agrees, differs or not given
- Fed by: [IN-124](#IN-124), [IN-118](#IN-118), [IN-119](#IN-119), [IN-076](#IN-076), [OUT-244](#OUT-244), [OUT-245](#OUT-245), [OUT-243](#OUT-243)
- Feeds: [CK-032](#CK-032)
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 0A B7; R3-4; sw/ledger.py aba509_reconciliation; tests: 3; 9

<a id="OUT-143"></a>

#### OUT-143 `aba509_reconciliation[without_score]`: 509 check: without a score

The cell data's count (without a score) beside the published ABA 509 figure, and whether they agree. Report only.

- Client label: "without a score"
- Excel: History 509 block row 'without a score' (columns: cells, 509, verdict per cohort)
- Unit: count; dimensions: cohort
- Formula: cells: SUM over cells; verdict: agrees, differs or not given
- Fed by: [IN-124](#IN-124), [IN-118](#IN-118), [IN-119](#IN-119), [IN-077](#IN-077), [OUT-244](#OUT-244), [OUT-245](#OUT-245), [OUT-243](#OUT-243)
- Feeds: [CK-032](#CK-032)
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 0A B7; R3-4; sw/ledger.py aba509_reconciliation; tests: 3; 9

<a id="OUT-144"></a>

#### OUT-144 `aba509_reconciliation[without_gpa]`: 509 check: without a GPA

The cell data's count (without a GPA) beside the published ABA 509 figure, and whether they agree. Report only.

- Client label: "without a GPA"
- Excel: History 509 block row 'without a GPA' (columns: cells, 509, verdict per cohort)
- Unit: count; dimensions: cohort
- Formula: cells: SUM over cells; verdict: agrees, differs or not given
- Fed by: [IN-124](#IN-124), [IN-118](#IN-118), [IN-119](#IN-119), [IN-078](#IN-078), [OUT-244](#OUT-244), [OUT-245](#OUT-245), [OUT-243](#OUT-243)
- Feeds: [CK-032](#CK-032)
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 0A B7; R3-4; sw/ledger.py aba509_reconciliation; tests: 3; 9

<a id="OUT-145"></a>

#### OUT-145 `aba509_reconciliation[score_p25]`: 509 check: score 25th percentile

The range of score bands that can hold the 25th percentile of enrollees with a score, beside the published figure, and whether it is consistent. Report only.

- Client label: "{measure} 25th percentile"
- Excel: History 509 block row '{measure} 25th percentile'
- Unit: text; dimensions: cohort
- Formula: band range from cumulative band shares; consistent if the published figure lies in it
- Fed by: [IN-124](#IN-124), [IN-118](#IN-118), [IN-079](#IN-079), [OUT-246](#OUT-246), [OUT-247](#OUT-247), [OUT-243](#OUT-243)
- Feeds: [CK-032](#CK-032)
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 0A B7; R3-4; sw/ledger.py aba509_reconciliation; tests: 3; 9

<a id="OUT-146"></a>

#### OUT-146 `aba509_reconciliation[score_p50]`: 509 check: score 50th percentile

The range of score bands that can hold the 50th percentile of enrollees with a score, beside the published figure, and whether it is consistent. Report only.

- Client label: "{measure} 50th percentile"
- Excel: History 509 block row '{measure} 50th percentile'
- Unit: text; dimensions: cohort
- Formula: band range from cumulative band shares; consistent if the published figure lies in it
- Fed by: [IN-124](#IN-124), [IN-118](#IN-118), [IN-080](#IN-080), [OUT-246](#OUT-246), [OUT-247](#OUT-247), [OUT-243](#OUT-243)
- Feeds: [CK-032](#CK-032)
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 0A B7; R3-4; sw/ledger.py aba509_reconciliation; tests: 3; 9

<a id="OUT-147"></a>

#### OUT-147 `aba509_reconciliation[score_p75]`: 509 check: score 75th percentile

The range of score bands that can hold the 75th percentile of enrollees with a score, beside the published figure, and whether it is consistent. Report only.

- Client label: "{measure} 75th percentile"
- Excel: History 509 block row '{measure} 75th percentile'
- Unit: text; dimensions: cohort
- Formula: band range from cumulative band shares; consistent if the published figure lies in it
- Fed by: [IN-124](#IN-124), [IN-118](#IN-118), [IN-081](#IN-081), [OUT-246](#OUT-246), [OUT-247](#OUT-247), [OUT-243](#OUT-243)
- Feeds: [CK-032](#CK-032)
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 0A B7; R3-4; sw/ledger.py aba509_reconciliation; tests: 3; 9

<a id="OUT-148"></a>

#### OUT-148 `aba509_reconciliation[gpa_p25]`: 509 check: gpa 25th percentile

The range of GPA bands that can hold the 25th percentile of enrollees with a GPA, beside the published figure, and whether it is consistent. Report only.

- Client label: "{measure} 25th percentile"
- Excel: History 509 block row '{measure} 25th percentile'
- Unit: text; dimensions: cohort
- Formula: band range from cumulative band shares; consistent if the published figure lies in it
- Fed by: [IN-124](#IN-124), [IN-119](#IN-119), [IN-082](#IN-082), [OUT-246](#OUT-246), [OUT-247](#OUT-247), [OUT-243](#OUT-243)
- Feeds: [CK-032](#CK-032)
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 0A B7; R3-4; sw/ledger.py aba509_reconciliation; tests: 3; 9

<a id="OUT-149"></a>

#### OUT-149 `aba509_reconciliation[gpa_p50]`: 509 check: gpa 50th percentile

The range of GPA bands that can hold the 50th percentile of enrollees with a GPA, beside the published figure, and whether it is consistent. Report only.

- Client label: "{measure} 50th percentile"
- Excel: History 509 block row '{measure} 50th percentile'
- Unit: text; dimensions: cohort
- Formula: band range from cumulative band shares; consistent if the published figure lies in it
- Fed by: [IN-124](#IN-124), [IN-119](#IN-119), [IN-083](#IN-083), [OUT-246](#OUT-246), [OUT-247](#OUT-247), [OUT-243](#OUT-243)
- Feeds: [CK-032](#CK-032)
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 0A B7; R3-4; sw/ledger.py aba509_reconciliation; tests: 3; 9

<a id="OUT-150"></a>

#### OUT-150 `aba509_reconciliation[gpa_p75]`: 509 check: gpa 75th percentile

The range of GPA bands that can hold the 75th percentile of enrollees with a GPA, beside the published figure, and whether it is consistent. Report only.

- Client label: "{measure} 75th percentile"
- Excel: History 509 block row '{measure} 75th percentile'
- Unit: text; dimensions: cohort
- Formula: band range from cumulative band shares; consistent if the published figure lies in it
- Fed by: [IN-124](#IN-124), [IN-119](#IN-119), [IN-084](#IN-084), [OUT-246](#OUT-246), [OUT-247](#OUT-247), [OUT-243](#OUT-243)
- Feeds: [CK-032](#CK-032)
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 0A B7; R3-4; sw/ledger.py aba509_reconciliation; tests: 3; 9

<a id="OUT-151"></a>

#### OUT-151 `top_quartile_merit`: Merit to the top quartile

Merit dollars to the first quarter of the class by academic position (score band, then GPA class; unscored last), with the position that straddles the line counted in proportion.

- Client label: "Merit dollars to the top quartile of enrolled [USD]"
- Excel: Distribution 'Counts and shares by scenario' rows 'Merit dollars to the top quartile of enrolled [USD]'
- Unit: USD; dimensions: scenario x case
- Formula: SUMPRODUCT(position share in top quartile, position merit)
- Fed by: [INT-060](#INT-060), [INT-063](#INT-063)
- Feeds: [OUT-153](#OUT-153)
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 6 Distribution; R4-16; sw/ledger.py top_quartile_merit; tests: 3; 9; 19

<a id="OUT-152"></a>

#### OUT-152 `merit (Distribution)`: Merit dollars (Distribution)

Merit dollars by scenario and case, the denominator of the top-quartile share.

- Client label: "Merit dollars [USD]"
- Excel: Distribution 'Counts and shares by scenario' rows 'Merit dollars [USD]'
- Unit: USD; dimensions: scenario x case
- Formula: SUM(merit $)
- Fed by: [LG-036](#LG-036)
- Feeds: [OUT-153](#OUT-153)
- Role: derived; response: Y; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 6 Distribution; tests: 3; 9

<a id="OUT-153"></a>

#### OUT-153 `top_quartile_merit_share`: Top-quartile merit share

Merit to the top quartile over all merit (zero when merit is zero). How concentrated merit is at the top of the class.

- Client label: "Share of merit dollars to the top quartile of enrolled [ratio]"
- Excel: Distribution 'Counts and shares by scenario' rows 'Share of merit dollars to the top quartile of enrolled [ratio]'; named range DIST_TOP_QUARTILE_MERIT_SHARE
- Unit: ratio; dimensions: scenario x case
- Formula: top-quartile merit / merit
- Fed by: [OUT-151](#OUT-151), [OUT-152](#OUT-152)
- Feeds: none
- Role: derived; response: Y; shock: N; detail: core; client-safe: Y; status: live
- References: spec 6 Distribution; spec 0A A8; R4-05; sw/ledger.py top_quartile_merit; tests: 3; 9; 19

<a id="OUT-154"></a>

#### OUT-154 `STEP_SIZES`: Step sizes

Award at a score band minus the award at the next lower band present, within each residency, segment and GPA class. A plain table with no threshold or flag.

- Client label: "Step sizes"
- Excel: Distribution 'Step sizes' table; named range STEP_SIZES (rows: adjacent band pairs within residency x segment x GPA class; columns: scenarios)
- Unit: USD; dimensions: step x scenario
- Formula: award(upper band) - award(lower band)
- Fed by: [LG-030](#LG-030)
- Feeds: none
- Role: derived; response: N; shock: N; detail: core; client-safe: Y; status: live
- References: spec 6 Distribution; spec 15 item 6; App F 25; sw/ledger.py awards; tests: 3; 9

<a id="OUT-155"></a>

#### OUT-155 `build id`: RunLog: build id

Hash of the config, cell data, scenario file, requirements.lock and generator code; two builds share it only if they are the same apart from the timestamp.

- Client label: "build id"
- Excel: RunLog row 'build id'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-156"></a>

#### OUT-156 `git commit`: RunLog: git commit

Commit of the repository at build time.

- Client label: "git commit"
- Excel: RunLog row 'git commit'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-157"></a>

#### OUT-157 `config`: RunLog: config

Path of the client config.

- Client label: "config"
- Excel: RunLog row 'config'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-158"></a>

#### OUT-158 `config hash (sha256)`: RunLog: config hash (sha256)

Hash of the config file.

- Client label: "config hash (sha256)"
- Excel: RunLog row 'config hash (sha256)'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-159"></a>

#### OUT-159 `data source`: RunLog: data source

Where the cell data came from (file, or synthetic with seed).

- Client label: "data source"
- Excel: RunLog row 'data source'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-160"></a>

#### OUT-160 `data hash (sha256 of the cell table)`: RunLog: data hash (sha256 of the cell table)

Hash of the cell table.

- Client label: "data hash (sha256 of the cell table)"
- Excel: RunLog row 'data hash (sha256 of the cell table)'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-161"></a>

#### OUT-161 `scenarios`: RunLog: scenarios

Path of the scenario file.

- Client label: "scenarios"
- Excel: RunLog row 'scenarios'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-162"></a>

#### OUT-162 `scenarios hash (sha256)`: RunLog: scenarios hash (sha256)

Hash of the scenario file.

- Client label: "scenarios hash (sha256)"
- Excel: RunLog row 'scenarios hash (sha256)'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-163"></a>

#### OUT-163 `requirements.lock hash (sha256)`: RunLog: requirements.lock hash (sha256)

Hash of the pinned dependency list.

- Client label: "requirements.lock hash (sha256)"
- Excel: RunLog row 'requirements.lock hash (sha256)'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-164"></a>

#### OUT-164 `code hash (sha256 of sw/*.py)`: RunLog: code hash (sha256 of sw/*.py)

Hash of the generator code.

- Client label: "code hash (sha256 of sw/*.py)"
- Excel: RunLog row 'code hash (sha256 of sw/*.py)'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-165"></a>

#### OUT-165 `uncommitted files`: RunLog: uncommitted files

Files changed since the commit, if any.

- Client label: "uncommitted files"
- Excel: RunLog row 'uncommitted files'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-166"></a>

#### OUT-166 `cached values`: RunLog: cached values

Whether the cached values are the build's results or the -999 sentinel.

- Client label: "cached values"
- Excel: RunLog row 'cached values'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-167"></a>

#### OUT-167 `timestamp`: RunLog: timestamp

Build time; the only field that differs between two builds of the same inputs.

- Client label: "timestamp"
- Excel: RunLog row 'timestamp'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-168"></a>

#### OUT-168 `response source`: RunLog: response source

The response's source label (placeholder slopes).

- Client label: "response source"
- Excel: RunLog row 'response source'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-169"></a>

#### OUT-169 `shock source`: RunLog: shock source

Shock source and s.

- Client label: "shock source"
- Excel: RunLog row 'shock source'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-170"></a>

#### OUT-170 `mode`: RunLog: mode

Live or Reproduce build.

- Client label: "mode"
- Excel: RunLog row 'mode'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: [IN-070](#IN-070)
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-171"></a>

#### OUT-171 `python`: RunLog: python

Python version.

- Client label: "python"
- Excel: RunLog row 'python'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-172"></a>

#### OUT-172 `xlsxwriter`: RunLog: xlsxwriter

XlsxWriter version.

- Client label: "xlsxwriter"
- Excel: RunLog row 'xlsxwriter'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-173"></a>

#### OUT-173 `LibreOffice acceptance version (config/tools.yaml)`: RunLog: LibreOffice acceptance version (config/tools.yaml)

LibreOffice version the parity results are accepted on.

- Client label: "LibreOffice acceptance version (config/tools.yaml)"
- Excel: RunLog row 'LibreOffice acceptance version (config/tools.yaml)'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-174"></a>

#### OUT-174 `hold_position_rows`: RunLog: hold_position_rows

Whether median and percentile figures are held in this build.

- Client label: "hold_position_rows"
- Excel: RunLog row 'hold_position_rows'
- Unit: text; dimensions: build
- Formula: written at build
- Fed by: [IN-085](#IN-085)
- Feeds: none
- Role: display; response: N; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 6 RunLog; P21-03; sw/build.py; sw/workbook.py w_runlog; tests: 3

<a id="OUT-175"></a>

#### OUT-175 `RESPONSE_LABEL`: Response label

Carried by every output that depends on the placeholder response slopes, on every response-dependent sheet and Summary section.

- Client label: "Response based on client-input"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 0; 7

<a id="OUT-176"></a>

#### OUT-176 `ASSUMPTION_LABEL`: Client-input assumption label

Added to the narrative of any scenario with a non-zero yield shift or application lift.

- Client label: "Includes client-input assumptions (yield shift, application lift)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 0; 7

<a id="OUT-177"></a>

#### OUT-177 `SHOCK_LABEL`: Year-to-year variation label

Beside every probability and range while the shock source is illustrative; s is filled in.

- Client label: "Year-to-year variation assumed (s = {s}), not yet calibrated"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-011](#OUT-011), [OUT-012](#OUT-012), [OUT-020](#OUT-020), [OUT-021](#OUT-021), [OUT-023](#OUT-023), [OUT-024](#OUT-024), [OUT-043](#OUT-043), [OUT-046](#OUT-046), [OUT-061](#OUT-061)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 0; 7

<a id="OUT-178"></a>

#### OUT-178 `SEGMENT_SHARE_LABEL`: Segment share label

On every segment figure while the segment share is assumed rather than from client counts.

- Client label: "Segment share assumed, not from client data"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 0; 7

<a id="OUT-179"></a>

#### OUT-179 `RANGE_OUTCOME`: Range kind: outcome range

Names the 90% outcome range (Middle case) in range labels and the README; never combined with the case range.

- Client label: "90% outcome range"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 0; 7

<a id="OUT-180"></a>

#### OUT-180 `RANGE_CASES`: Range kind: price-response cases

Names the Low and High case range in labels and the README.

- Client label: "Low and High price-response cases"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 0; 7

<a id="OUT-181"></a>

#### OUT-181 `RANGE_OUTCOME_NOTE`: Outcome range note

Explains what the 90% outcome range covers.

- Client label: "enrollment noise and year-level variation, Middle case"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7

<a id="OUT-182"></a>

#### OUT-182 `RANGE_CASES_NOTE`: Case range note

Says the Low and High cases use placeholder slopes.

- Client label: "placeholder slopes now"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7

<a id="OUT-183"></a>

#### OUT-183 `PROB_UNDER`: Probability text below 5%

Shown instead of a probability below 5% while the shock is illustrative.

- Client label: "under 5%"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-011](#OUT-011), [OUT-012](#OUT-012), [OUT-020](#OUT-020), [OUT-021](#OUT-021), [OUT-023](#OUT-023), [OUT-024](#OUT-024), [OUT-043](#OUT-043), [OUT-046](#OUT-046), [OUT-061](#OUT-061)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 0; 7; 19

<a id="OUT-184"></a>

#### OUT-184 `PROB_OVER`: Probability text above 95%

Shown instead of a probability above 95% while the shock is illustrative.

- Client label: "over 95%"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-011](#OUT-011), [OUT-012](#OUT-012), [OUT-020](#OUT-020), [OUT-021](#OUT-021), [OUT-023](#OUT-023), [OUT-024](#OUT-024), [OUT-043](#OUT-043), [OUT-046](#OUT-046), [OUT-061](#OUT-061)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 0; 7; 19

<a id="OUT-185"></a>

#### OUT-185 `DISCOUNT_LABEL`: Discount rate label

Summary and class-table label of the entering-class first-year discount rate.

- Client label: "Discount rate (entering class, first year)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7; 27

<a id="OUT-186"></a>

#### OUT-186 `NEED_LABEL`: Need aid label

Inputs label stating need total, reference class and rate per enrollee.

- Client label: "Need aid: {total} at a class of {ref} ({rate} per enrollee; scales with class)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: [INT-019](#INT-019)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 3; 7

<a id="OUT-187"></a>

#### OUT-187 `STICKER_LABEL`: Sticker-price label

On the tuition what-if: the demand effect of a tuition change is not modeled.

- Client label: "Sticker-price demand effect not modeled."
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7

<a id="OUT-188"></a>

#### OUT-188 `NET_TUITION_FIXED`: Fixed-dollar line template

Sentence template of the fixed-dollar net-tuition line.

- Client label: "Awards fixed in dollars: every student below full tuition pays {diff} more than at base-cycle tuition."
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-086](#OUT-086)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 18

<a id="OUT-189"></a>

#### OUT-189 `NET_TUITION_SCALED`: Scaled line template

Sentence template of the scaled net-tuition line.

- Client label: "Awards scaled with tuition: a student pays {p} x (base-cycle tuition minus award) more, for example {x} at an award of {award}."
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-086](#OUT-086)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 18

<a id="OUT-190"></a>

#### OUT-190 `POOL_STRIP_LABEL`: Pool strip label

Pool strip title: yield is held constant as the pool changes.

- Client label: "yield held constant as the pool changes"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7

<a id="OUT-191"></a>

#### OUT-191 `POOL_YTD_LABEL`: Growth-to-date caveat

Beside the pool growth to date: final growth may differ if applicants file earlier or later.

- Client label: "growth to date; final growth may differ if applicants file earlier or later than last year"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7

<a id="OUT-192"></a>

#### OUT-192 `LINEAR_APPROX`: Linear approximation label

On the yield-strip break-even shifts.

- Client label: "linear approximation"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7

<a id="OUT-193"></a>

#### OUT-193 `RHO_SENSITIVITY`: Correlation sensitivity text

Explains the rho 0.5 rows.

- Client label: "if high-score and other admits' yields move differently year to year"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7

<a id="OUT-194"></a>

#### OUT-194 `PCT_APPROX_LABEL`: Percentile approximation text

Flags a percentile probability with fewer than 20 expected below t.

- Client label: "approximate (fewer than 20 expected below t)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-026](#OUT-026)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7; 22

<a id="OUT-195"></a>

#### OUT-195 `BAND_NOT_SCORE_LABEL`: Band-not-score text

On the spread rows: the figure is a band, not a score.

- Client label: "band, not a score"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7; 22

<a id="OUT-196"></a>

#### OUT-196 `CONTINUING_LABEL`: Continuing revenue label

On the continuing-revenue row: client-supplied, attrition and renewals not modeled.

- Client label: "continuing-student revenue as supplied by the client; attrition and renewals not modeled"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-044](#OUT-044)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7; 25

<a id="OUT-197"></a>

#### OUT-197 `CONTINUING_HELD`: Continuing revenue held text

Tuition what-if note under all_jd.

- Client label: "continuing revenue held at the supplied figure"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-082](#OUT-082)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7; 25

<a id="OUT-198"></a>

#### OUT-198 `POOL_BREAKEVEN_LABEL`: Break-even pool multiplier label

Explains the break-even table: an expectation, not a probability.

- Client label: "pool multiplier at which the expected class meets the target / the expected margin is zero; not a probability"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7; 24

<a id="OUT-199"></a>

#### OUT-199 `POOL_YTD_MARKER`: Growth-to-date marker text

Marks the pool-strip row nearest 1 + growth.

- Client label: "growth to date ({as_of}) is about here"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-108](#OUT-108)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 24; 26

<a id="OUT-200"></a>

#### OUT-200 `POOL_YTD_NO_DATE`: No-date text

Used in the marker when no as-of date is given.

- Client label: "date not given"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 26

<a id="OUT-201"></a>

#### OUT-201 `PCT_MARGIN_UNIT`: Percentile margin unit text

Explains that the percentile margin counts swaps.

- Client label: "margin: swaps of an enrollee below t for one at or above t, at the same class size; adding k enrollees below t uses k(1 - q)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7; 22

<a id="OUT-202"></a>

#### OUT-202 `GPA_PCT_NOTE`: GPA percentile note

States that GPA percentiles are not supported.

- Client label: "GPA percentiles are not supported (the cell schema has one GPA boundary)."
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7

<a id="OUT-203"></a>

#### OUT-203 `PCT_MARGIN_SWAPS`: Swaps label

Part of each percentile margin row label.

- Client label: "swaps: students below t who could replace students at or above t"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 27

<a id="OUT-204"></a>

#### OUT-204 `PCT_TIE_RULE`: Tie rule text

States the inclusive tie rule on the Summary and README.

- Client label: "holds when exactly a share q is below t; the ABA averages the two middle scores, so near a tie this can read a few points high"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 22; 27

<a id="OUT-205"></a>

#### OUT-205 `HOLD_POSITION`: Hold text

Replaces every median and percentile figure while hold_position_rows is true.

- Client label: "held pending confirmation of the LSAT basis (OD-14)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-131](#OUT-131)
- Role: display; response: N; shock: N; detail: supporting; client-safe: N; status: held under hold_position_rows
- References: spec 4; sw/labels.py; tests: 27

<a id="OUT-206"></a>

#### OUT-206 `POOL_BE_ANY`: Break-even note: any pool size

Break-even note when the target holds with no pool growth.

- Client label: "holds at any pool size"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [INT-050](#INT-050)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 24

<a id="OUT-207"></a>

#### OUT-207 `POOL_BE_NOT_REACHED`: Break-even note: not reached

Break-even note when pool growth cannot reach the target.

- Client label: "not reached by growth"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [INT-050](#INT-050)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 24

<a id="OUT-208"></a>

#### OUT-208 `POOL_BE_ABOVE_GRID`: Break-even note: above grid

Break-even note when m is above the pool grid.

- Client label: "above the pool grid"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [INT-050](#INT-050)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 24

<a id="OUT-209"></a>

#### OUT-209 `POOL_BE_BELOW_GRID`: Break-even note: below grid

Break-even note when m is below the pool grid.

- Client label: "below the pool grid"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [INT-050](#INT-050)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 24

<a id="OUT-210"></a>

#### OUT-210 `POOL_YTD_TIE`: Marker tie rule

States that a tie between grid rows goes to the upper row.

- Client label: "a tie between two grid rows goes to the upper row"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 24; 26

<a id="OUT-211"></a>

#### OUT-211 `NOT_USED_ENTERING`: Not-used text

Shown in the JD revenue rows under entering_y1.

- Client label: "not used (entering_y1)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-044](#OUT-044), [OUT-082](#OUT-082)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 25; 27

<a id="OUT-212"></a>

#### OUT-212 `NEED_DEPARTURE_NOTE`: Need departure note

States that a scenario's need departure is a fixed amount.

- Client label: "a scenario's need_total departure from need.total is a fixed dollar amount (it does not scale with class); need.total itself scales with class"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 4; sw/labels.py; tests: 19

<a id="OUT-213"></a>

#### OUT-213 `POOL_BE_AT_MOST`: Ceiling break-even text

A break-even that is a ceiling: the target fails beyond m.

- Client label: "at most {m}"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [INT-050](#INT-050)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 24; 27

<a id="OUT-214"></a>

#### OUT-214 `LOWEST_BAND`: Lowest band text

Names the lowest score band ('below' the next bound).

- Client label: "below {b}"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-028](#OUT-028), [OUT-127](#OUT-127)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 3; 27

<a id="OUT-215"></a>

#### OUT-215 `HELD_COLUMNS`: Held columns heading

Heading of the collapsed held strip columns in the PDF render.

- Client label: "median and percentile figures"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: held under hold_position_rows
- References: spec 4; sw/labels.py; tests: 10; 27

<a id="OUT-216"></a>

#### OUT-216 `LEGEND_NAMES`: Legend names

Plain names of the labels in the Summary 'Labels and range kinds' legend.

- Client label: "SHOCK_LABEL: Year-to-year variation; RESPONSE_LABEL: Response; ASSUMPTION_LABEL: Client-input assumptions; SEGMENT_SHARE_LABEL: Segment share; PCT_APPROX_LABEL: Approximate percentile; BAND_NOT_SCORE_LABEL: Score bands; CONTINUING_LABEL: Continuing students; POOL_BREAKEVEN_LABEL: Break-even pool multiplier"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7; 27

<a id="OUT-217"></a>

#### OUT-217 `LEGEND_PROB`: Legend: probability display

Legend line on the clamped probability display.

- Client label: "while the year-to-year variation is illustrative (not yet calibrated), probabilities below 5% read '{under}' and above 95% read '{over}'"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7; 27

<a id="OUT-218"></a>

#### OUT-218 `LEGEND_NEED`: Legend: need aid

Legend line on how need aid scales.

- Client label: "need aid scales with the class at a fixed amount per enrollee; a scenario's change to total need aid is a fixed dollar amount and does not scale with the class"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7; 27

<a id="OUT-219"></a>

#### OUT-219 `LEGEND_TIE`: Legend: tie rule

Legend line stating the tie rule.

- Client label: "a median or percentile target {rule}"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7; 27

<a id="OUT-220"></a>

#### OUT-220 `LEGEND_HELD`: Legend: held figures

Legend line on held figures, with this workbook's state.

- Client label: "until the LSAT basis is confirmed, every median and percentile figure reads '{hold}'. This workbook: {state}"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7; 27

<a id="OUT-221"></a>

#### OUT-221 `NO_SEGMENT_CELLS`: No-segment text

Every segment figure when the active segment has no cells.

- Client label: "no segment cells in the data"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 17

<a id="OUT-222"></a>

#### OUT-222 `SEGMENT_APPROX`: Segment approximation text

Flags a segment probability with fewer than 30 expected.

- Client label: "approximate (fewer than 30 expected)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-064](#OUT-064)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 13

<a id="OUT-223"></a>

#### OUT-223 `INCENTIVE_VALID`: Incentive valid text

Validity row when only incentive levers differ.

- Client label: "valid"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-074](#OUT-074)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 13

<a id="OUT-224"></a>

#### OUT-224 `INCENTIVE_NOT_VALID`: Incentive not valid text

Validity row when the parent differs in more than the incentive.

- Client label: "not valid: parent differs in more than the incentive"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-074](#OUT-074)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 13

<a id="OUT-225"></a>

#### OUT-225 `AID_PER_ADDITIONAL`: Aid per additional enrollee text

Reading when at least half a student is added.

- Client label: "aid per additional enrollee"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-071](#OUT-071)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 13

<a id="OUT-226"></a>

#### OUT-226 `SAVINGS_PER_LOST`: Savings per enrollee lost text

Reading when at least half a student is lost.

- Client label: "savings per enrollee lost"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-071](#OUT-071)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 13

<a id="OUT-227"></a>

#### OUT-227 `UNDER_HALF`: Under half a student text

Reading when the change is under half a student.

- Client label: "change under half a student"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-071](#OUT-071)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 13

<a id="OUT-228"></a>

#### OUT-228 `CT_OK`: Class-table OK

Status of a reachable class size.

- Client label: "OK"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-128](#OUT-128), [INT-058](#INT-058)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 14

<a id="OUT-229"></a>

#### OUT-229 `CT_NOT_APPLICABLE`: Class-table not applicable

Status when N is at or above the expected class.

- Client label: "not applicable (N at or above expected class)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-128](#OUT-128)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 14

<a id="OUT-230"></a>

#### OUT-230 `CT_ABOVE_CAP`: Class-table above cap

Status when N is above the cap.

- Client label: "above cap"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-128](#OUT-128)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 14

<a id="OUT-231"></a>

#### OUT-231 `CT_SHORTFALL`: Class-table shortfall

Status when the walk cannot remove enough enrollment.

- Client label: "N not reachable: shortfall {shortfall}"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-128](#OUT-128), [INT-058](#INT-058)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 14

<a id="OUT-232"></a>

#### OUT-232 `AWARD_IGNORED`: Ignored award note

Levers note on a full-tuition cell with an award typed in.

- Client label: "award entry ignored: full-tuition flag set"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-135](#OUT-135)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 18

<a id="OUT-233"></a>

#### OUT-233 `AWARDS_IGNORED_ONE`: One ignored award (narrative)

Narrative text for one ignored award entry.

- Client label: "1 award entry ignored: full-tuition flag set."
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-130](#OUT-130)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 18

<a id="OUT-234"></a>

#### OUT-234 `AWARDS_IGNORED_MANY`: Ignored awards (narrative)

Narrative text for several ignored award entries.

- Client label: "{k} award entries ignored: full-tuition flag set."
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-130](#OUT-130)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 18

<a id="OUT-235"></a>

#### OUT-235 `EXACT_CURRENT`: Exact value current

Status of the static exact segment probability while current.

- Client label: "current"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-063](#OUT-063)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 18

<a id="OUT-236"></a>

#### OUT-236 `EXACT_STALE`: Exact value stale

Status of the static exact segment probability once inputs change.

- Client label: "stale: segment expected enrollment, goal or cells changed since the build; rebuild for the exact value"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-063](#OUT-063)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 18

<a id="OUT-237"></a>

#### OUT-237 `EVIDENCE_OBSERVED`: Evidence: observed

Evidence label when the award is within the observed range.

- Client label: "observed"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 19

<a id="OUT-238"></a>

#### OUT-238 `EVIDENCE_EXTRAPOLATED`: Evidence: extrapolated

Evidence label otherwise.

- Client label: "extrapolated"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 19

<a id="OUT-239"></a>

#### OUT-239 `CLASS_TARGET_NOTICE`: Class target notice

Notice when a class target is outside the supported range.

- Client label: "Class target {target} is outside the supported range ({lo} to {hi}); figures are computed, but this class size is outside the tested range."
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-028](#CK-028)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 16

<a id="OUT-240"></a>

#### OUT-240 `MARGINAL_ADMIT_NOTE`: Marginal-admit note

Notice when a marginal-admit slope is set (it is ignored).

- Client label: "marginal_admit_yield_slope is {x}; marginal-admit yield is not modeled, so the value is read and ignored."
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: [IN-059](#IN-059)
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 4; sw/labels.py; tests: 21

<a id="OUT-241"></a>

#### OUT-241 `POLICY_UNSCORED_TRIMMED_FIRST`: Policy: unscored trimmed first

README, Trim and class-table statement of the shrink-path policy.

- Client label: "The shrink path trims unscored applicants first. This is a policy choice with access implications."
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7

<a id="OUT-242"></a>

#### OUT-242 `POLICY_UNSCORED_EXCLUDED`: Policy: unscored excluded

README and Inputs statement of the counting rule.

- Client label: "Unscored enrollees are excluded from both sides of the median margins and reported as a count."
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: none
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 7

<a id="OUT-243"></a>

#### OUT-243 `ABA509_NOT_GIVEN`: 509: not given

509 verdict when no figure is entered.

- Client label: "not given"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-142](#OUT-142), [OUT-143](#OUT-143), [OUT-144](#OUT-144), [OUT-145](#OUT-145), [OUT-146](#OUT-146), [OUT-147](#OUT-147), [OUT-148](#OUT-148), [OUT-149](#OUT-149), [OUT-150](#OUT-150)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 3; 9

<a id="OUT-244"></a>

#### OUT-244 `ABA509_AGREES`: 509: agrees

509 count verdict.

- Client label: "agrees"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-142](#OUT-142), [OUT-143](#OUT-143), [OUT-144](#OUT-144)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 3; 9

<a id="OUT-245"></a>

#### OUT-245 `ABA509_DIFFERS`: 509: differs

509 count verdict.

- Client label: "differs"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-142](#OUT-142), [OUT-143](#OUT-143), [OUT-144](#OUT-144)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 3; 9

<a id="OUT-246"></a>

#### OUT-246 `ABA509_CONSISTENT`: 509: consistent

509 quartile verdict.

- Client label: "consistent"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-145](#OUT-145), [OUT-146](#OUT-146), [OUT-147](#OUT-147), [OUT-148](#OUT-148), [OUT-149](#OUT-149), [OUT-150](#OUT-150)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 3; 9

<a id="OUT-247"></a>

#### OUT-247 `ABA509_INCONSISTENT`: 509: inconsistent

509 quartile verdict.

- Client label: "inconsistent"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [OUT-145](#OUT-145), [OUT-146](#OUT-146), [OUT-147](#OUT-147), [OUT-148](#OUT-148), [OUT-149](#OUT-149), [OUT-150](#OUT-150)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 3; 9

<a id="layer-check"></a>

## Checks

Checks sheet rows and the check messages.

<a id="CK-001"></a>

#### CK-001 `ALL_JD_NEEDS_CONTINUING`: all_jd needs continuing revenue

Checks message when all_jd is chosen without continuing revenue.

- Client label: "ntr_goal_basis all_jd needs continuing_ntr_usd"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-030](#CK-030)
- Role: display; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 4; sw/labels.py; tests: 26

<a id="CK-002"></a>

#### CK-002 `FT_CONFLICT_CHECK`: Full-tuition conflict message

Checks message for each full-tuition conflict.

- Client label: "award entered on a full-tuition cell is ignored; clear the flag to use it"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-045](#CK-045)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 18

<a id="CK-003"></a>

#### CK-003 `REBUILD_NEEDED`: Rebuild needed message

Checks message when a build-time input differs from its value at build.

- Client label: "rebuild needed: differs from its value at build ({build})"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-037](#CK-037), [CK-038](#CK-038), [CK-039](#CK-039), [CK-040](#CK-040), [CK-041](#CK-041), [CK-043](#CK-043)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 18; 23

<a id="CK-004"></a>

#### CK-004 `SCOPE_ERROR`: Segment scope error

Checks message for segment scope with no segment cells.

- Client label: "error: bonus scope 'segment' with no segment cells and a bonus, lift or goal (Python refuses this scenario)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-035](#CK-035)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 18

<a id="CK-005"></a>

#### CK-005 `SEGMENT_UNNAMED`: Segment unnamed error

Checks message when several segments exist and none is named.

- Client label: "error: several segments are configured and none is named; name the active segment on Levers"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-036](#CK-036)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 17

<a id="CK-006"></a>

#### CK-006 `MODE_REPRO_OK`: Mode OK (Reproduce)

Mode check in a reproduce build set to Reproduce.

- Client label: "OK (Reproduce: the Ledgers take the loaded yields and tuition)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-016](#CK-016)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: reproduce only
- References: spec 4; sw/labels.py; tests: 6

<a id="CK-007"></a>

#### CK-007 `MODE_REPRO_LIVE`: Mode Live in a reproduce build

Mode check when a reproduce build is set to Live.

- Client label: "Live: the Ledgers take the response yields and the tuition formula; the loaded values are not read"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-016](#CK-016)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: reproduce only
- References: spec 4; sw/labels.py; tests: 3; 6

<a id="CK-008"></a>

#### CK-008 `MODE_UNKNOWN`: Unknown mode

Mode check when the switch holds anything else.

- Client label: "mode must be Live or Reproduce"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-015](#CK-015), [CK-016](#CK-016)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 3

<a id="CK-009"></a>

#### CK-009 `MODE_LIVE_BUILD`: Reproduce set in a live build

Mode check when a live build is set to Reproduce.

- Client label: "this is a live build with no loaded values; the Ledgers ignore the switch (set it back to Live)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-015](#CK-015)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 3

<a id="CK-010"></a>

#### CK-010 `REPRO_LEVERS_DIFFER`: Levers differ from loaded values

Reproduce check message.

- Client label: "{rates} admit rates and {awards} awards differ from the loaded values; pool multiplier {pool}"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-046](#CK-046)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: reproduce only
- References: spec 4; sw/labels.py; tests: 6

<a id="CK-011"></a>

#### CK-011 `REPRO_TUITION_DIFFERS`: Tuition differs from loaded

Reproduce check message.

- Client label: "tuition formula gives {formula}; loaded tuition {loaded}"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-047](#CK-047)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: reproduce only
- References: spec 4; sw/labels.py; tests: 6

<a id="CK-012"></a>

#### CK-012 `ABA509_NOT_RUN`: 509 not run

Checks summary for a cohort without 509 figures.

- Client label: "not run: no ABA 509 figures for {y} (aba_509_by_cohort)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-032](#CK-032)
- Role: display; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 4; sw/labels.py; tests: 3

<a id="CK-013"></a>

#### CK-013 `ABA509_ALL_AGREE`: 509 all agree

Checks summary when every given figure agrees.

- Client label: "report only: the cell data agree with every given 509 figure"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-032](#CK-032)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 3

<a id="CK-014"></a>

#### CK-014 `ABA509_SOME_DIFFER`: 509 some differ

Checks summary when some figures disagree.

- Client label: "report only: {k} of {n} given 509 figures disagree with the cell data (see History)"
- Excel: sw/labels.py constant; text as shown in the workbook
- Unit: text; dimensions: scalar
- Formula: fixed text
- Fed by: none
- Feeds: [CK-032](#CK-032)
- Role: display; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 4; sw/labels.py; tests: 3

<a id="CK-015"></a>

#### CK-015 `Mode: a live build has no loaded values`: Check: reports ok unless the mode switch is set to reproduce in a live build, which has no loaded values

Reports OK unless the mode switch is set to Reproduce in a live build, which has no loaded values.

- Client label: "Mode: a live build has no loaded values"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scalar
- Formula: OK or a message
- Fed by: [IN-070](#IN-070), [CK-009](#CK-009), [CK-008](#CK-008)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3

<a id="CK-016"></a>

#### CK-016 `Mode: the Ledgers take the loaded yields and tuition (Reproduce) or the response (Live)`: Check: in a reproduce build, says whether the ledgers read the loaded values or the response

In a reproduce build, says whether the Ledgers read the loaded values or the response.

- Client label: "Mode: the Ledgers take the loaded yields and tuition (Reproduce) or the response (Live)"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scalar
- Formula: OK or a message
- Fed by: [IN-070](#IN-070), [CK-006](#CK-006), [CK-007](#CK-007), [CK-008](#CK-008)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: reproduce only
- References: spec 7; sw/workbook.py w_checks; tests: 3; 6

<a id="CK-017"></a>

#### CK-017 `Rounding probe (R3-3): ROUND({expr}, 0); the argument is one binary step below 2.5. {rest}`: Check: shows the spreadsheet engine's rounding of a value one binary step below a half, so a desktop excel check can report it

Shows the spreadsheet engine's rounding of a value one binary step below a half, so a desktop Excel check can report it.

- Client label: "Rounding probe (R3-3): ROUND({expr}, 0); the argument is one binary step below 2.5. {rest}"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scalar
- Formula: fixed: ROUND(0.35/0.14, 0) evaluated by the spreadsheet engine
- Fed by: none
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: N; status: reproduce only
- References: R3-3; R4-17; tests: 3

<a id="CK-018"></a>

#### CK-018 `History: in-state plus out-of-state totals equal the overall total`: Check: residency totals on history add to the overall total

Residency totals on History add to the overall total.

- Client label: "History: in-state plus out-of-state totals equal the overall total"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: cohort
- Formula: OK or a message
- Fed by: [OUT-140](#OUT-140)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3

<a id="CK-019"></a>

#### CK-019 `History: segment totals plus cells outside any segment equal the overall total`: Check: segment totals on history add to the overall total

Segment totals on History add to the overall total.

- Client label: "History: segment totals plus cells outside any segment equal the overall total"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: cohort
- Formula: OK or a message
- Fed by: [OUT-140](#OUT-140)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3

<a id="CK-020"></a>

#### CK-020 `Ledger: totals row equals the sum of in-state and out-of-state cell rows (enrolled)`: Check: each ledger's totals row equals the sum of its cell rows

Each Ledger's totals row equals the sum of its cell rows.

- Client label: "Ledger: totals row equals the sum of in-state and out-of-state cell rows (enrolled)"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario x case
- Formula: OK or a message
- Fed by: [LG-040](#LG-040), [LG-035](#LG-035)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3

<a id="CK-021"></a>

#### CK-021 `Ledger: admits at most applications`: Check: no cell has more admits than applications

No cell has more admits than applications.

- Client label: "Ledger: admits at most applications"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario x case
- Formula: OK or a message
- Fed by: [LG-027](#LG-027), [LG-025](#LG-025)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3

<a id="CK-022"></a>

#### CK-022 `Ledger: enrolled at most admits`: Check: no cell has more enrolled than admits

No cell has more enrolled than admits.

- Client label: "Ledger: enrolled at most admits"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario x case
- Formula: OK or a message
- Fed by: [LG-035](#LG-035), [LG-027](#LG-027)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3

<a id="CK-023"></a>

#### CK-023 `Ledger: award at least zero and at most tuition after the incentive`: Check: every resolved award lies between zero and tuition

Every resolved award lies between zero and tuition.

- Client label: "Ledger: award at least zero and at most tuition after the incentive"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario x case
- Formula: OK or a message
- Fed by: [LG-030](#LG-030), [LG-002](#LG-002)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3

<a id="CK-024"></a>

#### CK-024 `Ledger: yield between 0 and 1`: Check: every yield lies between 0 and 1

Every yield lies between 0 and 1.

- Client label: "Ledger: yield between 0 and 1"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario x case
- Formula: OK or a message
- Fed by: [LG-032](#LG-032)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3

<a id="CK-025"></a>

#### CK-025 `Tuition formula reproduces the step {y0} to {y1} (increase rounded to 0.1%, tuition to tuition_rounding_usd)`: Check: the tuition rounding rule reproduces each history step

The tuition rounding rule reproduces each history step.

- Client label: "Tuition formula reproduces the step {y0} to {y1} (increase rounded to 0.1%, tuition to tuition_rounding_usd)"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: cohort
- Formula: OK or a message
- Fed by: [IN-008](#IN-008), [IN-012](#IN-012)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3

<a id="CK-026"></a>

#### CK-026 `Class against cap and target band (a result, not a warning; Middle case)`: Check: reports the middle expected class against the cap and the target band, as a result

Reports the Middle expected class against the cap and the target band, as a result.

- Client label: "Class against cap and target band (a result, not a warning; Middle case)"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario
- Formula: OK or a message
- Fed by: [OUT-008](#OUT-008), [IN-099](#IN-099), [IN-098](#IN-098), [IN-028](#IN-028)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3

<a id="CK-027"></a>

#### CK-027 `Class target at most the cap`: Check: each scenario's class target is at most its cap

Each scenario's class target is at most its cap.

- Client label: "Class target at most the cap"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario
- Formula: OK or a message
- Fed by: [IN-098](#IN-098), [IN-099](#IN-099)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3; 16

<a id="CK-028"></a>

#### CK-028 `Class target within the supported range`: Check: each class target is inside the supported range, else the class-target notice

Each class target is inside the supported range, else the class-target notice.

- Client label: "Class target within the supported range"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario
- Formula: OK or a message
- Fed by: [IN-098](#IN-098), [IN-030](#IN-030), [OUT-239](#OUT-239)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3; 16

<a id="CK-029"></a>

#### CK-029 `Spend against budget_total (Middle case; budget_basis: total aid, or merit only)`: Check: middle-case spend (total aid or merit, by the budget basis) against the budget, when one is set

Middle-case spend (total aid or merit, by the budget basis) against the budget, when one is set.

- Client label: "Spend against budget_total (Middle case; budget_basis: total aid, or merit only)"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario
- Formula: OK or a message
- Fed by: [IN-038](#IN-038), [IN-039](#IN-039), [OUT-037](#OUT-037), [OUT-033](#OUT-033)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3; 19

<a id="CK-030"></a>

#### CK-030 `Revenue goal: ntr_goal_basis all_jd needs continuing_ntr_usd`: Check: flags all_jd without continuing revenue

Flags all_jd without continuing revenue.

- Client label: "Revenue goal: ntr_goal_basis all_jd needs continuing_ntr_usd"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scalar
- Formula: OK or a message
- Fed by: [IN-035](#IN-035), [IN-036](#IN-036), [CK-001](#CK-001)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 26

<a id="CK-031"></a>

#### CK-031 `History reconciliation {y}: grid-implied merit (enrolled x award over cells) against reported merit (merit_actual_by_cohort; percent gap)`: Check: grid-implied merit for a history cohort against reported merit, as a percent gap, when reported merit is given

Grid-implied merit for a history cohort against reported merit, as a percent gap, when reported merit is given.

- Client label: "History reconciliation {y}: grid-implied merit (enrolled x award over cells) against reported merit (merit_actual_by_cohort; percent gap)"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: cohort
- Formula: OK or a message
- Fed by: [IN-124](#IN-124), [IN-123](#IN-123), [IN-040](#IN-040)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 7; Q-8f; sw/ledger.py history_reconciliation; tests: 3; 19

<a id="CK-032"></a>

#### CK-032 `History 509 reconciliation {y}: cell data against the public ABA 509 (class, without a score or GPA, quartiles; reported, not asserted)`: Check: summarizes the history 509 block for a cohort: not run, all agree, or how many disagree

Summarizes the History 509 block for a cohort: not run, all agree, or how many disagree. Report only.

- Client label: "History 509 reconciliation {y}: cell data against the public ABA 509 (class, without a score or GPA, quartiles; reported, not asserted)"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: cohort
- Formula: OK or a message
- Fed by: [OUT-142](#OUT-142), [OUT-143](#OUT-143), [OUT-144](#OUT-144), [OUT-145](#OUT-145), [OUT-146](#OUT-146), [OUT-147](#OUT-147), [OUT-148](#OUT-148), [OUT-149](#OUT-149), [OUT-150](#OUT-150), [CK-012](#CK-012), [CK-013](#CK-013), [CK-014](#CK-014)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 0A B7; R3-4; tests: 3; 9

<a id="CK-033"></a>

#### CK-033 `Summary expected class equals the Ledger total`: Check: the summary's expected class equals the ledger's expected enrolled total

The Summary's expected class equals the Ledger's expected enrolled total.

- Client label: "Summary expected class equals the Ledger total"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: case
- Formula: OK or a message
- Fed by: [OUT-008](#OUT-008), [LG-040](#LG-040)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3

<a id="CK-034"></a>

#### CK-034 `Segment cells lie within their residency`: Check: every segment cell has the segment's residency

Every segment cell has the segment's residency.

- Client label: "Segment cells lie within their residency"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: segment
- Formula: OK or a message
- Fed by: [IN-117](#IN-117), [IN-116](#IN-116), [IN-062](#IN-062)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; sw/workbook.py w_checks; tests: 3

<a id="CK-035"></a>

#### CK-035 `Bonus scope 'segment' has segment cells when a bonus, lift or goal is set`: Check: shows the scope error when a segment-scoped incentive, lift or goal has no segment cells

Shows the scope error when a segment-scoped incentive, lift or goal has no segment cells.

- Client label: "Bonus scope 'segment' has segment cells when a bonus, lift or goal is set"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario
- Formula: OK or a message
- Fed by: [IN-101](#IN-101), [IN-100](#IN-100), [IN-105](#IN-105), [IN-106](#IN-106), [LG-023](#LG-023), [CK-004](#CK-004)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; P2-07; tests: 3; 18

<a id="CK-036"></a>

#### CK-036 `Active segment named (several segments configured)`: Check: when several segments are configured, each scenario must name its active segment

When several segments are configured, each scenario must name its active segment.

- Client label: "Active segment named (several segments configured)"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario
- Formula: OK or a message
- Fed by: [IN-104](#IN-104), [IN-060](#IN-060), [CK-005](#CK-005)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; P2-07; tests: 17

<a id="CK-037"></a>

#### CK-037 `Trim order: first median threshold equals its value at build`: Check: rebuild needed when the first median threshold, which fixes the trim order, changes

Rebuild needed when the first median threshold, which fixes the trim order, changes.

- Client label: "Trim order: first median threshold equals its value at build"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scalar
- Formula: OK or a message
- Fed by: [IN-020](#IN-020), [CK-003](#CK-003)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; P2-06; tests: 18

<a id="CK-038"></a>

#### CK-038 `Trim order: trim.protect_segment equals its value at build`: Check: rebuild needed when the segment protection rule changes

Rebuild needed when the segment protection rule changes.

- Client label: "Trim order: trim.protect_segment equals its value at build"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scalar
- Formula: OK or a message
- Fed by: [IN-065](#IN-065), [CK-003](#CK-003)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 7; P2-06; tests: 18

<a id="CK-039"></a>

#### CK-039 `Trim: trim.exempt_cells equals its value at build`: Check: rebuild needed when the exempt cells change

Rebuild needed when the exempt cells change.

- Client label: "Trim: trim.exempt_cells equals its value at build"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scalar
- Formula: OK or a message
- Fed by: [IN-067](#IN-067), [CK-003](#CK-003)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 7; P2-06; tests: 18

<a id="CK-040"></a>

#### CK-040 `Trim order: score.floor equals its value at build (protect_segment above_floor)`: Check: under above_floor, rebuild needed when the floor changes

Under above_floor, rebuild needed when the floor changes.

- Client label: "Trim order: score.floor equals its value at build (protect_segment above_floor)"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scalar
- Formula: OK or a message
- Fed by: [IN-016](#IN-016), [IN-065](#IN-065), [CK-003](#CK-003)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A A5, A7; tests: 23

<a id="CK-041"></a>

#### CK-041 `Trim order: active segment equals its value at build`: Check: rebuild needed when a scenario's active segment changes

Rebuild needed when a scenario's active segment changes.

- Client label: "Trim order: active segment equals its value at build"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario
- Formula: OK or a message
- Fed by: [IN-104](#IN-104), [CK-003](#CK-003)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; P2-06; tests: 18

<a id="CK-042"></a>

#### CK-042 `Percentile target {j}: t is a band bound (score.bands)`: Check: each percentile threshold must be a band lower bound

Each percentile threshold must be a band lower bound.

- Client label: "Percentile target {j}: t is a band bound (score.bands)"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: target
- Formula: OK or a message
- Fed by: [IN-019](#IN-019), [IN-014](#IN-014)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 0A A7; tests: 23; 26

<a id="CK-043"></a>

#### CK-043 `Percentile target {j}: q equals its value at build`: Check: rebuild needed when a percentile share changes (it sets the rows and labels)

Rebuild needed when a percentile share changes (it sets the rows and labels).

- Client label: "Percentile target {j}: q equals its value at build"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: target
- Formula: OK or a message
- Fed by: [IN-018](#IN-018), [CK-003](#CK-003)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 0A A7; tests: 23

<a id="CK-044"></a>

#### CK-044 `Static exact segment probability is current (Summary segment block)`: Check: repeats the exact-value status of the segment block

Repeats the exact-value status of the segment block.

- Client label: "Static exact segment probability is current (Summary segment block)"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario
- Formula: OK or a message
- Fed by: [OUT-063](#OUT-063)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: live
- References: spec 7; P2-06; tests: 18

<a id="CK-045"></a>

#### CK-045 `Full-tuition award conflicts (P1.1-1)`: Check: counts award entries on full-tuition cells, then lists each conflicting cell ('conflict k', 'more')

Counts award entries on full-tuition cells, then lists each conflicting cell ('conflict k', 'more').

- Client label: "Full-tuition award conflicts (P1.1-1)"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario
- Formula: OK or a message
- Fed by: [IN-113](#IN-113), [IN-114](#IN-114), [CK-002](#CK-002)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: N; status: live
- References: spec 7; P1.1-1; sw/ledger.py full_tuition_conflicts; tests: 18

<a id="CK-046"></a>

#### CK-046 `Reproduce: Levers admit rates, resolved awards (Middle) and pool multiplier equal the loaded values`: Check: counts admit rates and awards that differ from the loaded values and compares the pool multiplier

Counts admit rates and awards that differ from the loaded values and compares the pool multiplier.

- Client label: "Reproduce: Levers admit rates, resolved awards (Middle) and pool multiplier equal the loaded values"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario
- Formula: OK or a message
- Fed by: [IN-112](#IN-112), [LG-030](#LG-030), [IN-095](#IN-095), [IN-128](#IN-128), [IN-129](#IN-129), [IN-130](#IN-130), [CK-010](#CK-010)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: reproduce only
- References: spec 7; sw/workbook.py w_checks; tests: 3; 6

<a id="CK-047"></a>

#### CK-047 `Reproduce: the tuition formula at the scenario's increase equals the loaded tuition`: Check: compares the tuition formula with the loaded tuition

Compares the tuition formula with the loaded tuition.

- Client label: "Reproduce: the tuition formula at the scenario's increase equals the loaded tuition"
- Excel: Checks sheet, row(s) headed by this text; column B scope, column C result
- Unit: text; dimensions: scenario
- Formula: OK or a message
- Fed by: [IN-093](#IN-093), [IN-127](#IN-127), [CK-011](#CK-011)
- Feeds: none
- Role: derived; response: N; shock: N; detail: supporting; client-safe: Y; status: reproduce only
- References: spec 7; sw/workbook.py w_checks; tests: 3; 6

<a id="layer-internal"></a>

## Internals

Python and Excel intermediates. Not client-facing; listed so a reader can see what each does and what it feeds.

<a id="INT-001"></a>

#### INT-001 `score_group_upper`: Upper score group

True for cells at or above the pool threshold (unscored cells are lower). Chooses the pool, the yield floor and cap, and which applications the pool multiplier scales.

- Client label: "upper score group (1/0)"
- Excel: Response!G
- Unit: flag; dimensions: cell
- Formula: score_lo >= score.pool_threshold
- Fed by: [IN-118](#IN-118), [IN-015](#IN-015)
- Feeds: [LG-013](#LG-013), [INT-007](#INT-007), [INT-008](#INT-008), [INT-009](#INT-009), [INT-010](#INT-010), [INT-014](#INT-014), [INT-015](#INT-015)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 2 score group; sw/response.py score_group_upper; tests: 1; 3

<a id="INT-002"></a>

#### INT-002 `n`: History admits (n)

The cell's admits summed over the history cohorts: its weight in partial pooling.

- Client label: "n (admits, all cohorts)"
- Excel: Response!H
- Unit: count; dimensions: cell
- Formula: sum over cohorts of admits
- Fed by: [IN-122](#IN-122), [IN-007](#IN-007)
- Feeds: [INT-005](#INT-005), [INT-006](#INT-006), [INT-013](#INT-013)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield; tests: 3; 11

<a id="INT-003"></a>

#### INT-003 `enrolled, all cohorts`: History enrolled (all cohorts)

The cell's enrolled summed over history cohorts; with n gives the cell's history yield.

- Client label: "enrolled, all cohorts"
- Excel: Response!I
- Unit: count; dimensions: cell
- Formula: sum over cohorts of enrolled
- Fed by: [IN-124](#IN-124)
- Feeds: [INT-005](#INT-005)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield; tests: 3; 11

<a id="INT-004"></a>

#### INT-004 `a0`: Base award (a0)

Latest-cohort award of the cell. Base yield is re-centered at it; the yield formula measures award changes from it.

- Client label: "a0 (latest award)"
- Excel: Response!J
- Unit: USD; dimensions: cell
- Formula: award at base_cycle
- Fed by: [IN-123](#IN-123), [IN-005](#IN-005)
- Feeds: [LG-018](#LG-018), [INT-013](#INT-013), [INT-018](#INT-018)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield; tests: 1; 3

<a id="INT-005"></a>

#### INT-005 `ybar`: History yield (ybar)

Admits-weighted history yield of the cell. The cell's own term in partial pooling.

- Client label: "ybar"
- Excel: Response!K
- Unit: rate; dimensions: cell
- Formula: enrolled, all cohorts / n
- Fed by: [INT-003](#INT-003), [INT-002](#INT-002)
- Feeds: [INT-013](#INT-013)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield; tests: 3; 11

<a id="INT-006"></a>

#### INT-006 `abar`: History award (abar)

Admits-weighted history award of the cell. Base yield moves the cell mean from abar to a0 along the slope.

- Client label: "abar"
- Excel: Response!L
- Unit: USD; dimensions: cell
- Formula: sum(admits x award) / n
- Fed by: [IN-122](#IN-122), [IN-123](#IN-123), [INT-002](#INT-002)
- Feeds: [INT-013](#INT-013)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield; tests: 3; 11

<a id="INT-007"></a>

#### INT-007 `pool admits: res x seg x group`: Pool totals (res x seg x group)

History admits and enrolled summed over the cell's (res x seg x group) pool. One level of the pooling fallback that gives ypool.

- Client label: "pool admits: res x seg x group"
- Excel: Response 'pool admits: res x seg x group' and 'pool enrolled: res x seg x group' columns
- Unit: count; dimensions: cell
- Formula: sum over cells in the same (res x seg x group) pool
- Fed by: [IN-122](#IN-122), [IN-124](#IN-124), [INT-001](#INT-001), [IN-116](#IN-116), [IN-117](#IN-117)
- Feeds: [INT-011](#INT-011)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield (_pool_yields); tests: 3; 11

<a id="INT-008"></a>

#### INT-008 `pool admits: res x group`: Pool totals (res x group)

History admits and enrolled summed over the cell's (res x group) pool. One level of the pooling fallback that gives ypool.

- Client label: "pool admits: res x group"
- Excel: Response 'pool admits: res x group' and 'pool enrolled: res x group' columns
- Unit: count; dimensions: cell
- Formula: sum over cells in the same (res x group) pool
- Fed by: [IN-122](#IN-122), [IN-124](#IN-124), [INT-001](#INT-001), [IN-116](#IN-116), [IN-117](#IN-117)
- Feeds: [INT-011](#INT-011)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield (_pool_yields); tests: 3; 11

<a id="INT-009"></a>

#### INT-009 `pool admits: group`: Pool totals (group)

History admits and enrolled summed over the cell's (group) pool. One level of the pooling fallback that gives ypool.

- Client label: "pool admits: group"
- Excel: Response 'pool admits: group' and 'pool enrolled: group' columns
- Unit: count; dimensions: cell
- Formula: sum over cells in the same (group) pool
- Fed by: [IN-122](#IN-122), [IN-124](#IN-124), [INT-001](#INT-001), [IN-116](#IN-116), [IN-117](#IN-117)
- Feeds: [INT-011](#INT-011)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield (_pool_yields); tests: 3; 11

<a id="INT-010"></a>

#### INT-010 `pool admits: all`: Pool totals (all)

History admits and enrolled summed over the cell's (all) pool. One level of the pooling fallback that gives ypool.

- Client label: "pool admits: all"
- Excel: Response 'pool admits: all' and 'pool enrolled: all' columns
- Unit: count; dimensions: cell
- Formula: sum over cells in the same (all) pool
- Fed by: [IN-122](#IN-122), [IN-124](#IN-124), [INT-001](#INT-001), [IN-116](#IN-116), [IN-117](#IN-117)
- Feeds: [INT-011](#INT-011)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield (_pool_yields); tests: 3; 11

<a id="INT-011"></a>

#### INT-011 `ypool`: Pool yield

Admits-weighted yield of the cell's pool: (residency, segment, score group) if it has enough admits, else (residency, score group), else score group, else all cells. The prior mean in partial pooling.

- Client label: "ypool"
- Excel: Response!U
- Unit: rate; dimensions: cell
- Formula: pool enrolled / pool admits at the first level that qualifies
- Fed by: [INT-007](#INT-007), [INT-008](#INT-008), [INT-009](#INT-009), [INT-010](#INT-010), [IN-055](#IN-055)
- Feeds: [INT-012](#INT-012), [INT-013](#INT-013)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield; tests: 3; 11

<a id="INT-012"></a>

#### INT-012 `pool_level`: Pool level used

Which pooling level gave the cell's ypool (segment, residency, group, all).

- Client label: "pool used"
- Excel: Response!V
- Unit: text; dimensions: cell
- Formula: first qualifying level
- Fed by: [INT-011](#INT-011)
- Feeds: none
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield; tests: 11

<a id="INT-013"></a>

#### INT-013 `y0`: Base yield (y0)

Base yield per cell and case by partial pooling, re-centered at the latest award. The Ledger yield starts from it.

- Client label: "y0 {case}"
- Excel: Response!W:Y (y0 Low, Middle, High)
- Unit: rate; dimensions: cell x case
- Formula: y0 = (n (ybar + b/100 (a0 - abar)/1000) + k ypool) / (n + k); no admits: ypool
- Fed by: [INT-002](#INT-002), [INT-005](#INT-005), [INT-006](#INT-006), [INT-004](#INT-004), [INT-011](#INT-011), [IN-054](#IN-054), [IN-044](#IN-044), [IN-045](#IN-045), [IN-046](#IN-046)
- Feeds: [LG-019](#LG-019), [INT-018](#INT-018)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield; tests: 1; 3; 11; 19

<a id="INT-014"></a>

#### INT-014 `floor`: Yield floor (cell)

The cell's yield floor: the upper or lower group value.

- Client label: "yield floor"
- Excel: Response!Z
- Unit: rate; dimensions: cell
- Formula: upper ? floor.upper : floor.lower
- Fed by: [INT-001](#INT-001), [IN-047](#IN-047), [IN-049](#IN-049)
- Feeds: [LG-016](#LG-016), [INT-018](#INT-018)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield; tests: 1; 3

<a id="INT-015"></a>

#### INT-015 `cap`: Yield cap (cell)

The cell's yield cap: the upper or lower group value.

- Client label: "yield cap"
- Excel: Response!AA
- Unit: rate; dimensions: cell
- Formula: upper ? cap.upper : cap.lower
- Fed by: [INT-001](#INT-001), [IN-048](#IN-048), [IN-050](#IN-050)
- Feeds: [LG-017](#LG-017), [INT-018](#INT-018)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield; tests: 1; 3

<a id="INT-016"></a>

#### INT-016 `award_lo`: Observed award low

Lowest award over history cohorts with admits (blank if none). Bounds the evidence label's observed range.

- Client label: "observed award low"
- Excel: Response!AB
- Unit: USD; dimensions: cell
- Formula: min award over cohorts with admits
- Fed by: [IN-123](#IN-123), [IN-122](#IN-122)
- Feeds: [LG-020](#LG-020)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield; tests: 3; 19

<a id="INT-017"></a>

#### INT-017 `award_hi`: Observed award high

Highest award over history cohorts with admits. Bounds the evidence label's observed range.

- Client label: "observed award high"
- Excel: Response!AC
- Unit: USD; dimensions: cell
- Formula: max award over cohorts with admits
- Fed by: [IN-123](#IN-123), [IN-122](#IN-122)
- Feeds: [LG-021](#LG-021)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 4; MR 5.1; sw/response.py base_yield; tests: 3; 19

<a id="INT-018"></a>

#### INT-018 `Yield at award rungs`: Yield at award rungs (display)

Yield at award rungs from zero to tuition for each cell and case, for display only. No Ledger formula reads it; a pipeline rung table would replace the yield column later.

- Client label: "Yield at award rungs (display only; R-01). Full-tuition rung = Baseline tuition in the plan year."
- Excel: Response from column AE: Low, Middle and High blocks
- Unit: rate; dimensions: cell x case x rung
- Formula: clip(y0 + b/100 (rung - a0)/1000, floor, cap)
- Fed by: [INT-013](#INT-013), [INT-004](#INT-004), [INT-014](#INT-014), [INT-015](#INT-015), [LG-002](#LG-002)
- Feeds: none
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: display only
- References: spec 4 yield method (R-01); sw/workbook.py w_response; tests: 3

<a id="INT-019"></a>

#### INT-019 `in_need_rate`: Need rate (Inputs)

Need total over the reference class, shown on Inputs with the need label.

- Client label: "need rate per enrollee"
- Excel: Inputs!B51 (in_need_rate)
- Unit: USD; dimensions: scalar
- Formula: need.total / need.reference_class
- Fed by: [IN-032](#IN-032), [IN-033](#IN-033)
- Feeds: [OUT-186](#OUT-186)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 2 need; sw/workbook.py w_inputs; tests: 3

<a id="INT-020"></a>

#### INT-020 `in_ntr_target_eff`: Effective entering target

The target every revenue probability, the yield-strip probability and the revenue break-even read: the target under entering_y1, the target less continuing revenue under all_jd.

- Client label: "effective entering target (what the ntr_target figures read)"
- Excel: Inputs!B58 (in_ntr_target_eff)
- Unit: USD; dimensions: scalar
- Formula: IF(all_jd, ntr_target - continuing_ntr_usd, ntr_target)
- Fed by: [IN-034](#IN-034), [IN-035](#IN-035), [IN-036](#IN-036)
- Feeds: [OUT-042](#OUT-042), [OUT-043](#OUT-043), [OUT-098](#OUT-098)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 0A A4; sw/config.py ntr_target_effective; tests: 3; 25

<a id="INT-021"></a>

#### INT-021 `in_tuition_implied_pct`: Implied tuition increase

Cumulative increase from base-cycle tuition to the plan year; a dollar tuition resets it to that figure. Baseline's tuition increase.

- Client label: "implied increase from base_cycle (%)"
- Excel: Inputs!B24 (in_tuition_implied_pct); Levers Baseline tuition_increase_pct
- Unit: percent; dimensions: scalar
- Formula: IF(dollar tuition blank, prod(1 + increase/100), tuition_by_year_usd / tuition_base) - 1, x 100
- Fed by: [IN-010](#IN-010), [IN-011](#IN-011), [IN-009](#IN-009), [IN-006](#IN-006)
- Feeds: [IN-093](#IN-093)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 0A A2; R4-14; sw/config.py plan_increase_pct; tests: 21; 26

<a id="INT-022"></a>

#### INT-022 `in_pct_corr`: Percentile continuity correction

Half the lattice step of the percentile margin, 1/(2n) with q = m/n in lowest terms. Enters every percentile probability.

- Client label: "continuity correction 1/(2n), q = m/n in lowest terms"
- Excel: Inputs!B34:E34 (in_pct_corr)
- Unit: rate; dimensions: target
- Formula: 1 / (2 n)
- Fed by: [IN-018](#IN-018)
- Feeds: [OUT-023](#OUT-023), [OUT-024](#OUT-024)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 0A A1; MR 6.4; sw/config.py pct_lattice_n; tests: 3; 22

<a id="INT-023"></a>

#### INT-023 `score_thresholds`: Score thresholds for shares

The median thresholds, pool threshold and floor, highest first: the thresholds of the 'enrolled at or above' and share rows.

- Client label: "score thresholds for the share rows" (proposed)
- Excel: Python only
- Unit: score; dimensions: threshold
- Formula: sorted set of median thresholds, pool threshold, floor
- Fed by: [IN-020](#IN-020), [IN-015](#IN-015), [IN-016](#IN-016)
- Feeds: [OUT-013](#OUT-013)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: sw/ledger.py score_thresholds; tests: 3; 9

<a id="INT-024"></a>

#### INT-024 `is_held`: Hold rule

Decides which figures read the hold text under hold_position_rows: every median and percentile figure, shares and counts at a median or percentile threshold, the count below a held floor and the GPA-hi count.

- Client label: "held figure rule" (proposed)
- Excel: Python only
- Unit: flag; dimensions: figure
- Formula: name in held set, or t in held thresholds
- Fed by: [IN-085](#IN-085), [IN-020](#IN-020), [IN-019](#IN-019), [IN-016](#IN-016), [IN-022](#IN-022)
- Feeds: [OUT-013](#OUT-013), [OUT-014](#OUT-014), [OUT-015](#OUT-015), [OUT-016](#OUT-016), [OUT-019](#OUT-019), [OUT-020](#OUT-020), [OUT-021](#OUT-021), [OUT-022](#OUT-022), [OUT-023](#OUT-023), [OUT-024](#OUT-024), [OUT-025](#OUT-025), [OUT-026](#OUT-026), [OUT-027](#OUT-027), [OUT-028](#OUT-028), [OUT-093](#OUT-093), [OUT-094](#OUT-094), [OUT-105](#OUT-105), [OUT-106](#OUT-106), [OUT-107](#OUT-107), [OUT-113](#OUT-113), [OUT-114](#OUT-114), [OUT-119](#OUT-119), [OUT-120](#OUT-120), [OUT-121](#OUT-121), [OUT-122](#OUT-122), [OUT-131](#OUT-131)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: R4-06; F-1; sw/contract.py is_held, held_ts; tests: 27

<a id="INT-025"></a>

#### INT-025 `v`: Binomial variance (v)

Variance of a cell's enrolled count given the year: admits x yield x (1 - yield). Summed into every variance.

- Client label: "binomial variance per cell" (proposed)
- Excel: Python only
- Unit: count; dimensions: scenario x case x cell
- Formula: v_c = A_c y_c (1 - y_c)
- Fed by: [LG-027](#LG-027), [LG-032](#LG-032)
- Feeds: [INT-026](#INT-026), [INT-031](#INT-031), [INT-033](#INT-033), [INT-035](#INT-035), [INT-036](#INT-036)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py cf_class; MR 3.2; tests: 2; 4

<a id="INT-026"></a>

#### INT-026 `V`: Class variance (V)

Variance of the class: binomial part plus the year-shock part. Sets the class range and probabilities.

- Client label: "class variance" (proposed)
- Excel: Python only
- Unit: count; dimensions: scenario x case
- Formula: V = sum v_c + s^2 M^2
- Fed by: [INT-025](#INT-025), [LG-034](#LG-034), [IN-041](#IN-041)
- Feeds: [OUT-009](#OUT-009), [OUT-010](#OUT-010), [OUT-011](#OUT-011), [OUT-012](#OUT-012), [INT-027](#INT-027)
- Role: internal; response: Y; shock: Y; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py cf_class; MR 6.2; tests: 2; 4

<a id="INT-027"></a>

#### INT-027 `class_sd`: Class SD

Square root of the class variance.

- Client label: "class standard deviation" (proposed)
- Excel: Python only
- Unit: count; dimensions: scenario x case
- Formula: sqrt(V)
- Fed by: [INT-026](#INT-026)
- Feeds: none
- Role: internal; response: Y; shock: Y; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py class_dist; tests: 2

<a id="INT-028"></a>

#### INT-028 `g_plus`: G+ (expected at or above t)

Expected scored enrollees at or above a threshold. With G- it gives the expected margin and the shock part of the median and percentile variances.

- Client label: "expected scored enrolled at or above t" (proposed)
- Excel: Python only
- Unit: count; dimensions: scenario x case x target
- Formula: G+ = sum over g = +1 of mu_c
- Fed by: [LG-014](#LG-014), [LG-015](#LG-015), [LG-034](#LG-034)
- Feeds: [OUT-020](#OUT-020), [OUT-021](#OUT-021), [INT-030](#INT-030), [INT-031](#INT-031), [INT-032](#INT-032), [INT-033](#INT-033)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py cf_median, cf_pct; tests: 2; 22

<a id="INT-029"></a>

#### INT-029 `g_minus`: G- (expected below t)

Expected scored enrollees below a threshold. Feeds the margin, the variances and the percentile approximation flag.

- Client label: "expected scored enrolled below t" (proposed)
- Excel: Python only
- Unit: count; dimensions: scenario x case x target
- Formula: G- = sum over g = -1 of mu_c
- Fed by: [LG-014](#LG-014), [LG-015](#LG-015), [LG-034](#LG-034)
- Feeds: [OUT-020](#OUT-020), [OUT-021](#OUT-021), [OUT-025](#OUT-025), [INT-030](#INT-030), [INT-031](#INT-031), [INT-032](#INT-032), [INT-033](#INT-033)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py cf_median, cf_pct; tests: 2; 22

<a id="INT-030"></a>

#### INT-030 `margin_expected`: Expected margin (m)

Expected margin at t from mu (unrounded); equals the Summary margin when enrolled is not rounded.

- Client label: "expected median margin" (proposed)
- Excel: Python only
- Unit: count; dimensions: scenario x case x target
- Formula: m = G+ - G-
- Fed by: [INT-028](#INT-028), [INT-029](#INT-029)
- Feeds: [OUT-093](#OUT-093)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py cf_median; tests: 2

<a id="INT-031"></a>

#### INT-031 `v_m`: Median margin variance (V_m)

Variance of the median margin: binomial part over scored cells plus the shock part with correlation rho.

- Client label: "median margin variance" (proposed)
- Excel: Python only
- Unit: count; dimensions: scenario x case x target
- Formula: V_m = sum_{g != 0} v_c + s^2 (G+^2 + G-^2 - 2 rho G+ G-)
- Fed by: [INT-025](#INT-025), [INT-028](#INT-028), [INT-029](#INT-029), [IN-041](#IN-041), [IN-043](#IN-043)
- Feeds: [OUT-020](#OUT-020), [OUT-021](#OUT-021)
- Role: internal; response: Y; shock: Y; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py cf_median; MR 6.3; tests: 2; 4

<a id="INT-032"></a>

#### INT-032 `margin_expected`: Expected percentile margin E[M_q]

Expected percentile margin with weights q at or above t and -(1 - q) below.

- Client label: "expected percentile margin" (proposed)
- Excel: Python only
- Unit: count; dimensions: scenario x case x target
- Formula: E[M_q] = q G+ - (1 - q) G-
- Fed by: [INT-028](#INT-028), [INT-029](#INT-029), [IN-018](#IN-018)
- Feeds: [OUT-023](#OUT-023), [OUT-024](#OUT-024)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py cf_pct; spec 0A A1; tests: 2; 22

<a id="INT-033"></a>

#### INT-033 `v_q`: Percentile margin variance (V_q)

Variance of the percentile margin.

- Client label: "percentile margin variance" (proposed)
- Excel: Python only
- Unit: count; dimensions: scenario x case x target
- Formula: V_q = q^2 sum_above v + (1-q)^2 sum_below v + s^2 (q^2 G+^2 + (1-q)^2 G-^2 - 2 rho q (1-q) G+ G-)
- Fed by: [INT-025](#INT-025), [INT-028](#INT-028), [INT-029](#INT-029), [IN-018](#IN-018), [IN-041](#IN-041), [IN-043](#IN-043)
- Feeds: [OUT-023](#OUT-023), [OUT-024](#OUT-024)
- Role: internal; response: Y; shock: Y; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py cf_pct; MR 6.4; tests: 2; 4; 22

<a id="INT-034"></a>

#### INT-034 `ntr_const`: Revenue constant (K)

Specialty aid plus the need departure: the constant subtracted from the sum of w x enrolled to give ntr_y1.

- Client label: "revenue constant (specialty plus need departure)" (proposed)
- Excel: Python only
- Unit: USD; dimensions: scenario
- Formula: K = specialty_usd + need departure
- Fed by: [IN-096](#IN-096), [LG-005](#LG-005)
- Feeds: [OUT-039](#OUT-039), [OUT-040](#OUT-040), [OUT-043](#OUT-043), [OUT-076](#OUT-076), [OUT-087](#OUT-087), [OUT-098](#OUT-098)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 0A B5; R4-07; sw/ledger.py LedgerCase.ntr_const; tests: 1; 3; 19

<a id="INT-035"></a>

#### INT-035 `Vn`: NTR variance (V_n)

Variance of ntr_y1: binomial part weighted by w^2 plus the shock part. Gives the NTR range and probability.

- Client label: "NTR variance" (proposed)
- Excel: Python only
- Unit: USD; dimensions: scenario x case
- Formula: V_n = sum w^2 v + s^2 (sum w mu)^2
- Fed by: [LG-037](#LG-037), [INT-025](#INT-025), [LG-034](#LG-034), [IN-041](#IN-041)
- Feeds: [OUT-039](#OUT-039), [OUT-040](#OUT-040), [OUT-043](#OUT-043)
- Role: internal; response: Y; shock: Y; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py cf_ntr; MR 6.5; tests: 2; 4

<a id="INT-036"></a>

#### INT-036 `segment_v`: Segment variance (V_S)

Mean M_S and variance V_S of segment enrolled over segment cells. Feed the segment range, normal-form probability and approximation flag.

- Client label: "segment variance" (proposed)
- Excel: Python only
- Unit: count; dimensions: scenario x case
- Formula: M_S = sum_S mu; V_S = sum_S v + s^2 M_S^2
- Fed by: [LG-023](#LG-023), [LG-034](#LG-034), [INT-025](#INT-025), [IN-041](#IN-041)
- Feeds: [OUT-058](#OUT-058), [OUT-059](#OUT-059), [OUT-061](#OUT-061), [OUT-064](#OUT-064)
- Role: internal; response: Y; shock: Y; detail: internal; client-safe: N; status: live
- References: spec 3 segment block; sw/ledger.py segment; tests: 13

<a id="INT-037"></a>

#### INT-037 `exact_pmf`: Exact distribution

Exact distribution of a sum of cell binomials mixed over the shock by 20-node Gauss-Hermite quadrature. Gives the static exact segment probability and checks the closed forms in tests.

- Client label: "exact distribution (convolution)" (proposed)
- Excel: Python only
- Unit: probability; dimensions: scenario x case
- Formula: convolution of cell pmfs, averaged over shock nodes
- Fed by: [LG-027](#LG-027), [LG-032](#LG-032), [IN-041](#IN-041)
- Feeds: [OUT-062](#OUT-062)
- Role: internal; response: Y; shock: Y; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py exact_pmf, segment_exact; MR 6.6; tests: 2; 13

<a id="INT-038"></a>

#### INT-038 `Z90`: 90% range multiplier

1.645: the normal quantile for the 90% outcome ranges.

- Client label: "90% range multiplier" (proposed)
- Excel: Python only
- Unit: rate; dimensions: scalar
- Formula: fixed: 1.645
- Fed by: none
- Feeds: [OUT-009](#OUT-009), [OUT-010](#OUT-010), [OUT-039](#OUT-039), [OUT-040](#OUT-040), [OUT-058](#OUT-058), [OUT-059](#OUT-059), [OUT-131](#OUT-131)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py Z90; tests: 2; 19

<a id="INT-039"></a>

#### INT-039 `PCT_APPROX_BELOW`: Percentile approximation threshold

20: below this many expected enrollees below t a percentile probability is marked approximate.

- Client label: "percentile approximation threshold" (proposed)
- Excel: Python only
- Unit: count; dimensions: scalar
- Formula: fixed: 20
- Fed by: none
- Feeds: [OUT-026](#OUT-026)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py PCT_APPROX_BELOW; tests: 22

<a id="INT-040"></a>

#### INT-040 `SEGMENT_APPROX_BELOW`: Segment approximation threshold

30: below this many expected segment enrollees the segment probability is marked approximate.

- Client label: "segment approximation threshold" (proposed)
- Excel: Python only
- Unit: count; dimensions: scalar
- Formula: fixed: 30
- Fed by: none
- Feeds: [OUT-064](#OUT-064)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 segment block; sw/ledger.py SEGMENT_APPROX_BELOW; tests: 13

<a id="INT-041"></a>

#### INT-041 `SPREAD_QS`: Spread band shares

0.25 and 0.75: the shares for which the Summary shows a spread band.

- Client label: "spread band shares" (proposed)
- Excel: Python only
- Unit: rate; dimensions: q
- Formula: fixed: (0.25, 0.75)
- Fed by: none
- Feeds: [OUT-027](#OUT-027)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 5; MR 6; sw/risk.py SPREAD_QS; tests: 22

<a id="INT-042"></a>

#### INT-042 `parts.M`: Pool-strip part M

Expected enrolled in the below-threshold (lo) and above-threshold (hi) parts at m = 1. The strip's expected class is M_lo + m M_hi; the class break-even reads both.

- Client label: "M"
- Excel: Summary 'Working values: pool strip split at m = 1 (not printed)', column 'M' (rows lo and hi per scenario)
- Unit: count; dimensions: scenario x part
- Formula: sum over the part of admits at m = 1 x yield
- Fed by: [LG-039](#LG-039), [LG-032](#LG-032), [LG-013](#LG-013)
- Feeds: [OUT-099](#OUT-099), [OUT-111](#OUT-111)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 pool strip; spec 0A A6; F-1; sw/strip.py pool_strip; tests: 3; 15; 24; 27

<a id="INT-043"></a>

#### INT-043 `parts.V`: Pool-strip part V

Binomial variance of each part; the strip's class variance is V_lo + m V_hi plus the shock term.

- Client label: "V"
- Excel: Summary 'Working values: pool strip split at m = 1 (not printed)', column 'V' (rows lo and hi per scenario)
- Unit: count; dimensions: scenario x part
- Formula: sum over the part of A1 y (1 - y)
- Fed by: [LG-039](#LG-039), [LG-032](#LG-032), [LG-013](#LG-013)
- Feeds: [OUT-099](#OUT-099)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 pool strip; spec 0A A6; F-1; sw/strip.py pool_strip; tests: 3; 15; 24; 27

<a id="INT-044"></a>

#### INT-044 `parts.W`: Pool-strip part W

Net tuition (w x expected enrolled) of each part; the strip's mean NTR is W_lo + m W_hi minus K.

- Client label: "W"
- Excel: Summary 'Working values: pool strip split at m = 1 (not printed)', column 'W' (rows lo and hi per scenario)
- Unit: USD; dimensions: scenario x part
- Formula: sum over the part of w A1 y
- Fed by: [LG-037](#LG-037), [LG-039](#LG-039), [LG-032](#LG-032), [LG-013](#LG-013)
- Feeds: [OUT-099](#OUT-099)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 pool strip; spec 0A A6; F-1; sw/strip.py pool_strip; tests: 3; 15; 24; 27

<a id="INT-045"></a>

#### INT-045 `parts.Vn`: Pool-strip part Vn

NTR binomial variance of each part; with the shock term gives the strip's NTR SD.

- Client label: "Vn"
- Excel: Summary 'Working values: pool strip split at m = 1 (not printed)', column 'Vn' (rows lo and hi per scenario)
- Unit: USD; dimensions: scenario x part
- Formula: sum over the part of w^2 A1 y (1 - y)
- Fed by: [LG-037](#LG-037), [LG-039](#LG-039), [LG-032](#LG-032), [LG-013](#LG-013)
- Feeds: [OUT-099](#OUT-099)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 pool strip; spec 0A A6; F-1; sw/strip.py pool_strip; tests: 3; 15; 24; 27

<a id="INT-046"></a>

#### INT-046 `med_parts.Gp`: Pool-strip part Gp

Expected scored enrolled at or above t in each part, per median threshold and percentile target. Feeds the strip margins and the margin break-evens.

- Client label: "Gp median {t} / Gp q {q}, t {t}"
- Excel: Summary 'Working values: pool strip split at m = 1 (not printed)', column 'Gp median {t} / Gp q {q}, t {t}' (rows lo and hi per scenario)
- Unit: count; dimensions: scenario x part x target
- Formula: sum over the part with sign +1 of A1 y
- Fed by: [LG-039](#LG-039), [LG-032](#LG-032), [LG-013](#LG-013), [LG-014](#LG-014), [LG-015](#LG-015)
- Feeds: [OUT-099](#OUT-099), [OUT-111](#OUT-111)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 pool strip; spec 0A A6; F-1; sw/strip.py pool_strip; tests: 3; 15; 24; 27

<a id="INT-047"></a>

#### INT-047 `med_parts.Gm`: Pool-strip part Gm

Expected scored enrolled below t in each part. Cells below t can sit above the pool threshold, so the hi part is not zero in general.

- Client label: "Gm median {t} / Gm q {q}, t {t}"
- Excel: Summary 'Working values: pool strip split at m = 1 (not printed)', column 'Gm median {t} / Gm q {q}, t {t}' (rows lo and hi per scenario)
- Unit: count; dimensions: scenario x part x target
- Formula: sum over the part with sign -1 of A1 y
- Fed by: [LG-039](#LG-039), [LG-032](#LG-032), [LG-013](#LG-013), [LG-014](#LG-014), [LG-015](#LG-015)
- Feeds: [OUT-099](#OUT-099), [OUT-111](#OUT-111)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 pool strip; spec 0A A6; F-1; sw/strip.py pool_strip; tests: 3; 15; 24; 27

<a id="INT-048"></a>

#### INT-048 `med_parts.Vm`: Pool-strip part Vm

Binomial variance of scored cells (median) or of cells below t (percentile) in each part.

- Client label: "Vm median {t} / Vm q {q}, t {t}"
- Excel: Summary 'Working values: pool strip split at m = 1 (not printed)', column 'Vm median {t} / Vm q {q}, t {t}' (rows lo and hi per scenario)
- Unit: count; dimensions: scenario x part x target
- Formula: sum over the part of A1 y (1 - y) by sign
- Fed by: [LG-039](#LG-039), [LG-032](#LG-032), [LG-013](#LG-013), [LG-014](#LG-014), [LG-015](#LG-015)
- Feeds: [OUT-099](#OUT-099)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 pool strip; spec 0A A6; F-1; sw/strip.py pool_strip; tests: 3; 15; 24; 27

<a id="INT-049"></a>

#### INT-049 `pct_parts.Vp`: Pool-strip part Vp

Binomial variance of cells at or above t in each part (percentile targets only).

- Client label: "Vp q {q}, t {t}"
- Excel: Summary 'Working values: pool strip split at m = 1 (not printed)', column 'Vp q {q}, t {t}' (rows lo and hi per scenario)
- Unit: count; dimensions: scenario x part x target
- Formula: sum over the part with sign +1 of A1 y (1 - y)
- Fed by: [LG-039](#LG-039), [LG-032](#LG-032), [LG-013](#LG-013), [LG-015](#LG-015)
- Feeds: [OUT-099](#OUT-099)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 pool strip; spec 0A A6; F-1; sw/strip.py pool_strip; tests: 3; 15; 24; 27

<a id="INT-050"></a>

#### INT-050 `breakeven_m`: Break-even rule

Turns a lo part and a hi part into the pool multiplier where their sum is zero, or a note: holds at any pool size, not reached by growth, above or below the grid, or 'at most m' for a ceiling.

- Client label: "break-even rule" (proposed)
- Excel: Python only
- Unit: multiplier; dimensions: scenario
- Formula: m = -e_lo / e_hi, checked against the grid
- Fed by: [IN-052](#IN-052), [OUT-206](#OUT-206), [OUT-207](#OUT-207), [OUT-208](#OUT-208), [OUT-209](#OUT-209), [OUT-213](#OUT-213)
- Feeds: [OUT-111](#OUT-111)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: R4-04; F-2; sw/strip.py breakeven_m; tests: 24

<a id="INT-051"></a>

#### INT-051 `nearest_row`: Nearest pool-grid row

The pool-grid row nearest 1 + growth to date; a tie goes to the upper row.

- Client label: "nearest grid row" (proposed)
- Excel: Summary pool strip, growth-to-date row, third value
- Unit: count; dimensions: scalar
- Formula: 1 + count of grid midpoints <= 1 + growth
- Fed by: [IN-068](#IN-068), [IN-052](#IN-052)
- Feeds: [OUT-108](#OUT-108), [OUT-110](#OUT-110)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 0A A6; R4-13; sw/strip.py pool_strip; tests: 24; 26

<a id="INT-052"></a>

#### INT-052 `trim_order`: Trim order

Order in which the shrink path cuts cells: lowest score first (unscored first), then GPA class blank, lo, hi; segment cells placed by the protection rule. Fixed at build.

- Client label: "k / trim position"
- Excel: Trim columns 'k', 'cell_id', 'Ledger row' (left table) and 'trim position' (right table)
- Unit: count; dimensions: scenario x cell
- Formula: sort by (protection tier, score_lo, GPA, residency/segment tie)
- Fed by: [IN-118](#IN-118), [IN-119](#IN-119), [IN-116](#IN-116), [LG-023](#LG-023), [IN-020](#IN-020), [IN-065](#IN-065), [IN-016](#IN-016)
- Feeds: [OUT-115](#OUT-115), [INT-054](#INT-054)
- Role: internal; response: N; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 shrink path; MR 7; sw/trim.py trim_order; tests: 14; 23

<a id="INT-053"></a>

#### INT-053 `rm_k`: Removable enrollment (rm)

Expected enrollment the walk can remove from a cell by cutting its admit rate to the floor rate; zero for exempt cells.

- Client label: "rm_k"
- Excel: Trim column 'rm_k'
- Unit: count; dimensions: scenario x cell
- Formula: rm_k = A_k y_k max(0, r_k - floor_rate) / r_k
- Fed by: [LG-027](#LG-027), [LG-032](#LG-032), [LG-026](#LG-026), [IN-066](#IN-066), [IN-067](#IN-067)
- Feeds: [INT-054](#INT-054), [INT-056](#INT-056)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 shrink path; MR 7; sw/trim.py trim_rates; tests: 3; 14

<a id="INT-054"></a>

#### INT-054 `R`: Cumulative removable (R)

Running total of removable enrollment in trim order; R_K at the end bounds how far the class can shrink (a larger cut is a shortfall).

- Client label: "R_k"
- Excel: Trim columns 'R_(k-1)', 'R_k', and 'R_K' in the block header
- Unit: count; dimensions: scenario x cell
- Formula: R_k = sum_{j <= k} rm_j
- Fed by: [INT-053](#INT-053), [INT-052](#INT-052)
- Feeds: [INT-056](#INT-056), [INT-058](#INT-058)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 shrink path; MR 7; sw/trim.py trim_rates; tests: 3; 14

<a id="INT-055"></a>

#### INT-055 `M (trim)`: Middle expected class (Trim)

The Middle-case expected class the walk cuts from.

- Client label: "M (Middle expected class)"
- Excel: Trim block header 'M (Middle expected class)'
- Unit: count; dimensions: scenario
- Formula: = sum of Ledger_Middle expected enrolled
- Fed by: [LG-034](#LG-034)
- Feeds: [INT-056](#INT-056), [INT-058](#INT-058)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 shrink path; MR 7; sw/trim.py trim_rates; tests: 3; 14

<a id="INT-056"></a>

#### INT-056 `removed_share`: Removed share

Share of a cell's removable enrollment the walk takes to reach N.

- Client label: "removed share"
- Excel: Trim columns 'removed share' (one per N)
- Unit: rate; dimensions: scenario x cell x N
- Formula: MIN(1, MAX(0, (M - N - R_(k-1)) / rm_k)); 0 when rm_k = 0
- Fed by: [INT-054](#INT-054), [INT-053](#INT-053), [INT-055](#INT-055), [IN-029](#IN-029)
- Feeds: [INT-057](#INT-057)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 shrink path; MR 7; sw/trim.py trim_rates; tests: 3; 14

<a id="INT-057"></a>

#### INT-057 `rates`: Trimmed admit rates

Admit rate of each cell after the walk for class size N (cells not cut keep their rates), the admits they give, and a helper that finds the lowest band still admitted. The class-size table evaluates the ledger at these rates.

- Client label: "rate(N)"
- Excel: Trim columns 'rate(N)', 'admits(N)' and 'low band helper' (right table, one group per N)
- Unit: rate; dimensions: scenario x cell x N
- Formula: rate_k(N) = r_k - (r_k - floor_rate) x removed share
- Fed by: [LG-026](#LG-026), [INT-056](#INT-056), [IN-066](#IN-066), [LG-025](#LG-025)
- Feeds: [OUT-115](#OUT-115), [INT-059](#INT-059)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 shrink path; MR 7; sw/trim.py trim_rates; tests: 3; 14

<a id="INT-058"></a>

#### INT-058 `status (trim)`: Shrink-path status

OK, or 'N not reachable: shortfall' when M - N exceeds R_K.

- Client label: "status"
- Excel: Python only; shown in the class-size table status column
- Unit: text; dimensions: scenario x N
- Formula: IF(M - N > R_K, shortfall, OK)
- Fed by: [INT-054](#INT-054), [INT-055](#INT-055), [OUT-228](#OUT-228), [OUT-231](#OUT-231)
- Feeds: [OUT-128](#OUT-128)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 shrink path; MR 7; sw/trim.py trim_rates; tests: 14

<a id="INT-059"></a>

#### INT-059 `_settle_integer`: Integer settling

With integer admits, rounds the trimmed admits and settles the residual in the last cell cut; cells the walk did not cut keep their rates exactly. Used in Python (reproduce builds have no Trim sheet).

- Client label: "integer settling" (proposed)
- Excel: Python only
- Unit: count; dimensions: scenario x N
- Formula: admits rounded; last cut cell absorbs the residual
- Fed by: [INT-057](#INT-057), [IN-056](#IN-056)
- Feeds: [OUT-115](#OUT-115)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 3 shrink path; MR 7; sw/trim.py _settle_integer; R-05; tests: 14; 19

<a id="INT-060"></a>

#### INT-060 `position_groups`: Academic positions

Academic positions highest first (score band descending, then GPA hi, lo, blank; unscored last), with the enrolled and merit dollars at each per scenario and case.

- Client label: "position (highest first)"
- Excel: Distribution 'Top quartile by academic position' table, columns 'position (highest first)', 'score_lo (lower bound)', 'gpa_class', 'cells', 'enrolled', 'merit $'
- Unit: count; dimensions: position x scenario x case
- Formula: group cells by (score_lo, gpa_class); sum enrolled and merit
- Fed by: [IN-118](#IN-118), [IN-119](#IN-119), [LG-035](#LG-035), [LG-036](#LG-036)
- Feeds: [OUT-151](#OUT-151), [INT-061](#INT-061), [INT-063](#INT-063)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: spec 6 Distribution; sw/ledger.py position_groups; tests: 3; 9; 19

<a id="INT-061"></a>

#### INT-061 `cum_before`: Enrolled at higher positions

Enrolled at all higher positions.

- Client label: "enrolled above"
- Excel: Distribution 'Top quartile by academic position' table, column 'enrolled above'
- Unit: count; dimensions: position x scenario x case
- Formula: running sum of enrolled
- Fed by: [INT-060](#INT-060)
- Feeds: [INT-063](#INT-063)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: sw/ledger.py top_quartile_merit; tests: 3; 19

<a id="INT-062"></a>

#### INT-062 `top_quartile_enrolled`: Top-quartile size

A quarter of the class: the size of the top quartile.

- Client label: "{case} case; class / 4:"
- Excel: Distribution 'Top quartile by academic position' table, header 'class / 4'
- Unit: count; dimensions: scenario x case
- Formula: class / 4
- Fed by: [LG-035](#LG-035)
- Feeds: [INT-063](#INT-063)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: sw/ledger.py top_quartile_merit; tests: 3; 19

<a id="INT-063"></a>

#### INT-063 `fraction`: Share of a position in the top quartile

Fraction of a position's enrolled inside the top quartile (the straddling position counts in proportion).

- Client label: "share in top quartile"
- Excel: Distribution 'Top quartile by academic position' table, column 'share in top quartile'
- Unit: rate; dimensions: position x scenario x case
- Formula: MIN(1, MAX(0, (class/4 - enrolled above) / enrolled))
- Fed by: [INT-062](#INT-062), [INT-061](#INT-061), [INT-060](#INT-060)
- Feeds: [OUT-151](#OUT-151)
- Role: internal; response: Y; shock: N; detail: internal; client-safe: N; status: live
- References: R4-16; sw/ledger.py top_quartile_merit; tests: 3; 19

<a id="index-by-analyst-name"></a>

## Index by analyst name

| Analyst name | Rows |
|---|---|
| `_range_text` | [OUT-028](#OUT-028) |
| `_settle_integer` | [INT-059](#INT-059) |
| `a0` | [LG-018](#LG-018), [INT-004](#INT-004) |
| `ABA509_AGREES` | [OUT-244](#OUT-244) |
| `ABA509_ALL_AGREE` | [CK-013](#CK-013) |
| `ABA509_CONSISTENT` | [OUT-246](#OUT-246) |
| `ABA509_DIFFERS` | [OUT-245](#OUT-245) |
| `ABA509_INCONSISTENT` | [OUT-247](#OUT-247) |
| `ABA509_NOT_GIVEN` | [OUT-243](#OUT-243) |
| `ABA509_NOT_RUN` | [CK-012](#CK-012) |
| `aba509_reconciliation[first_year_class]` | [OUT-142](#OUT-142) |
| `aba509_reconciliation[gpa_p25]` | [OUT-148](#OUT-148) |
| `aba509_reconciliation[gpa_p50]` | [OUT-149](#OUT-149) |
| `aba509_reconciliation[gpa_p75]` | [OUT-150](#OUT-150) |
| `aba509_reconciliation[score_p25]` | [OUT-145](#OUT-145) |
| `aba509_reconciliation[score_p50]` | [OUT-146](#OUT-146) |
| `aba509_reconciliation[score_p75]` | [OUT-147](#OUT-147) |
| `aba509_reconciliation[without_gpa]` | [OUT-144](#OUT-144) |
| `aba509_reconciliation[without_score]` | [OUT-143](#OUT-143) |
| `ABA509_SOME_DIFFER` | [CK-014](#CK-014) |
| `aba_509_by_cohort` | [IN-075](#IN-075) |
| `aba_509_by_cohort.first_year_class` | [IN-076](#IN-076) |
| `aba_509_by_cohort.gpa_p25` | [IN-082](#IN-082) |
| `aba_509_by_cohort.gpa_p50` | [IN-083](#IN-083) |
| `aba_509_by_cohort.gpa_p75` | [IN-084](#IN-084) |
| `aba_509_by_cohort.score_p25` | [IN-079](#IN-079) |
| `aba_509_by_cohort.score_p50` | [IN-080](#IN-080) |
| `aba_509_by_cohort.score_p75` | [IN-081](#IN-081) |
| `aba_509_by_cohort.without_gpa` | [IN-078](#IN-078) |
| `aba_509_by_cohort.without_score` | [IN-077](#IN-077) |
| `abar` | [INT-006](#INT-006) |
| `Active segment named (several segments configured)` | [CK-036](#CK-036) |
| `active_segment` | [OUT-052](#OUT-052) |
| `additional_enrollees` | [OUT-067](#OUT-067) |
| `admit rate` | [LG-026](#LG-026), [OUT-137](#OUT-137) |
| `admit_rate` | [IN-112](#IN-112) |
| `admits` | [IN-122](#IN-122), [LG-027](#LG-027) |
| `admits at pool multiplier 1` | [LG-039](#LG-039) |
| `admits_in` | [OUT-006](#OUT-006) |
| `admits_out` | [OUT-007](#OUT-007) |
| `admits_total` | [OUT-005](#OUT-005) |
| `aid` | [OUT-037](#OUT-037) |
| `AID_PER_ADDITIONAL` | [OUT-225](#OUT-225) |
| `aid_per_additional` | [OUT-070](#OUT-070) |
| `aid_per_additional_kind` | [OUT-071](#OUT-071) |
| `ALL_JD_NEEDS_CONTINUING` | [CK-001](#CK-001) |
| `applications` | [LG-025](#LG-025) |
| `applications (base cycle)` | [LG-022](#LG-022) |
| `apps` | [IN-121](#IN-121) |
| `apps_in` | [OUT-003](#OUT-003) |
| `apps_out` | [OUT-004](#OUT-004) |
| `apps_total` | [OUT-002](#OUT-002) |
| `ASSUMPTION_LABEL` | [OUT-176](#OUT-176) |
| `avg_aid` | [OUT-048](#OUT-048) |
| `award` | [LG-030](#LG-030) |
| `award % of tuition` | [OUT-138](#OUT-138) |
| `award at T(p)` | [LG-038](#LG-038) |
| `award base` | [LG-028](#LG-028) |
| `award high (observed)` | [LG-021](#LG-021) |
| `award low (observed)` | [LG-020](#LG-020) |
| `award_hi` | [INT-017](#INT-017) |
| `AWARD_IGNORED` | [OUT-232](#OUT-232) |
| `award_lo` | [INT-016](#INT-016) |
| `AWARD_MATRIX` | [OUT-136](#OUT-136) |
| `award_scale_with_tuition` | [IN-094](#IN-094) |
| `award_usd` | [IN-113](#IN-113), [IN-123](#IN-123) |
| `awards_changed` | [OUT-132](#OUT-132) |
| `awards_ignored` | [OUT-135](#OUT-135) |
| `AWARDS_IGNORED_MANY` | [OUT-234](#OUT-234) |
| `AWARDS_IGNORED_ONE` | [OUT-233](#OUT-233) |
| `BAND_NOT_SCORE_LABEL` | [OUT-195](#OUT-195) |
| `barbell` | [OUT-031](#OUT-031) |
| `Bonus scope 'segment' has segment cells when a bonus, lift or goal is set` | [CK-035](#CK-035) |
| `bonus_implied_by_pool` | [OUT-075](#OUT-075) |
| `bonus_min_score` | [IN-102](#IN-102) |
| `bonus_pool_usd` | [IN-103](#IN-103) |
| `bonus_scope` | [IN-101](#IN-101) |
| `bonus_usd` | [IN-100](#IN-100) |
| `breakeven_m` | [INT-050](#INT-050) |
| `breakeven_shift_class` | [OUT-097](#OUT-097) |
| `breakeven_shift_ntr` | [OUT-098](#OUT-098) |
| `budget_basis` | [IN-039](#IN-039) |
| `budget_total` | [IN-038](#IN-038) |
| `build id` | [OUT-155](#OUT-155) |
| `cached values` | [OUT-166](#OUT-166) |
| `cap` | [INT-015](#INT-015) |
| `cell_id` | [IN-115](#IN-115), [LG-007](#LG-007) |
| `changes` | [OUT-130](#OUT-130) |
| `Class against cap and target band (a result, not a warning; Middle case)` | [CK-026](#CK-026) |
| `Class target at most the cap` | [CK-027](#CK-027) |
| `Class target within the supported range` | [CK-028](#CK-028) |
| `class.band` | [IN-028](#IN-028) |
| `class.cap` | [IN-026](#IN-026) |
| `class.reject_range` | [IN-031](#IN-031) |
| `class.supported_range` | [IN-030](#IN-030) |
| `class.target` | [IN-027](#IN-027) |
| `class.what_if` | [IN-029](#IN-029) |
| `class_cap` | [IN-099](#IN-099) |
| `class_hi90` | [OUT-010](#OUT-010) |
| `class_lo90` | [OUT-009](#OUT-009) |
| `class_mean` | [OUT-008](#OUT-008) |
| `class_sd` | [INT-027](#INT-027) |
| `class_table` | [OUT-115](#OUT-115) |
| `class_table[class_mean]` | [OUT-117](#OUT-117) |
| `class_table[cut_{band}]` | [OUT-127](#OUT-127) |
| `class_table[discount_entering_y1]` | [OUT-124](#OUT-124) |
| `class_table[f]` | [OUT-116](#OUT-116) |
| `class_table[lowest_band_admitted]` | [OUT-126](#OUT-126) |
| `class_table[margin_q{q}_{t}]` | [OUT-121](#OUT-121) |
| `class_table[margin_{measure}_{t}]` | [OUT-119](#OUT-119) |
| `class_table[ntr_y1]` | [OUT-123](#OUT-123) |
| `class_table[p_class_over_cap]` | [OUT-118](#OUT-118) |
| `class_table[p_median_{measure}_{t}]` | [OUT-120](#OUT-120) |
| `class_table[p_pct_q{q}_{t}]` | [OUT-122](#OUT-122) |
| `class_table[segment_enrolled]` | [OUT-125](#OUT-125) |
| `class_table[status]` | [OUT-128](#OUT-128) |
| `class_target` | [IN-098](#IN-098) |
| `CLASS_TARGET_NOTICE` | [OUT-239](#OUT-239) |
| `client.id` | [IN-001](#IN-001) |
| `client.name` | [IN-002](#IN-002) |
| `client.small_cell_policy` | [IN-004](#IN-004) |
| `client.vertical` | [IN-003](#IN-003) |
| `clip_count` | [OUT-096](#OUT-096) |
| `code hash (sha256 of sw/*.py)` | [OUT-164](#OUT-164) |
| `cohort` | [IN-120](#IN-120) |
| `config` | [OUT-157](#OUT-157) |
| `config hash (sha256)` | [OUT-158](#OUT-158) |
| `CONTINUING_HELD` | [OUT-197](#OUT-197) |
| `CONTINUING_LABEL` | [OUT-196](#OUT-196) |
| `continuing_note` | [OUT-082](#OUT-082) |
| `continuing_ntr_usd` | [IN-036](#IN-036), [OUT-044](#OUT-044) |
| `CT_ABOVE_CAP` | [OUT-230](#OUT-230) |
| `CT_NOT_APPLICABLE` | [OUT-229](#OUT-229) |
| `CT_OK` | [OUT-228](#OUT-228) |
| `CT_SHORTFALL` | [OUT-231](#OUT-231) |
| `cum_before` | [INT-061](#INT-061) |
| `cycle.base_cycle` | [IN-005](#IN-005) |
| `cycle.history` | [IN-007](#IN-007) |
| `cycle.plan_cycle` | [IN-006](#IN-006) |
| `data hash (sha256 of the cell table)` | [OUT-160](#OUT-160) |
| `data source` | [OUT-159](#OUT-159) |
| `description` | [IN-091](#IN-091) |
| `discount_entering_y1` | [OUT-047](#OUT-047) |
| `DISCOUNT_LABEL` | [OUT-185](#OUT-185) |
| `discount_target` | [IN-037](#IN-037), [IN-111](#IN-111) |
| `enrolled` | [IN-124](#IN-124), [LG-035](#LG-035) |
| `enrolled, all cohorts` | [INT-003](#INT-003) |
| `enrolled_at_or_above` | [OUT-013](#OUT-013) |
| `enrolled_below_floor` | [OUT-015](#OUT-015) |
| `enrolled_gpa_hi` | [OUT-016](#OUT-016) |
| `evidence` | [LG-033](#LG-033) |
| `EVIDENCE_EXTRAPOLATED` | [OUT-238](#OUT-238) |
| `evidence_extrapolated_share` | [OUT-051](#OUT-051) |
| `EVIDENCE_OBSERVED` | [OUT-237](#OUT-237) |
| `evidence_tolerance_usd` | [IN-058](#IN-058) |
| `EXACT_CURRENT` | [OUT-235](#OUT-235) |
| `exact_pmf` | [INT-037](#INT-037) |
| `EXACT_STALE` | [OUT-236](#OUT-236) |
| `exact_status_row` | [OUT-063](#OUT-063) |
| `example_award` | [OUT-084](#OUT-084) |
| `expected enrolled` | [LG-034](#LG-034) |
| `floor` | [INT-014](#INT-014) |
| `fraction` | [INT-063](#INT-063) |
| `FT_CONFLICT_CHECK` | [CK-002](#CK-002) |
| `Full-tuition award conflicts (P1.1-1)` | [CK-045](#CK-045) |
| `full_tuition` | [IN-114](#IN-114) |
| `full_tuition_n` | [OUT-029](#OUT-029) |
| `g_minus` | [INT-029](#INT-029) |
| `g_plus` | [INT-028](#INT-028) |
| `generator` | [IN-087](#IN-087) |
| `git commit` | [OUT-156](#OUT-156) |
| `gpa.classes` | [IN-023](#IN-023) |
| `gpa.hi_at_or_above` | [IN-022](#IN-022) |
| `gpa.measure` | [IN-021](#IN-021) |
| `gpa.median_threshold` | [IN-024](#IN-024) |
| `gpa_blank_count` | [OUT-018](#OUT-018) |
| `gpa_class` | [IN-119](#IN-119), [LG-011](#LG-011) |
| `GPA_PCT_NOTE` | [OUT-202](#OUT-202) |
| `gross_y1` | [OUT-032](#OUT-032) |
| `HELD_COLUMNS` | [OUT-215](#OUT-215) |
| `History 509 reconciliation {y}: cell data against the public ABA 509 (class, without a score or GPA, quartiles; reported, not asserted)` | [CK-032](#CK-032) |
| `History reconciliation {y}: grid-implied merit (enrolled x award over cells) against reported merit (merit_actual_by_cohort; percent gap)` | [CK-031](#CK-031) |
| `history totals` | [OUT-140](#OUT-140) |
| `history tuition row` | [OUT-141](#OUT-141) |
| `history yield` | [OUT-139](#OUT-139) |
| `History: in-state plus out-of-state totals equal the overall total` | [CK-018](#CK-018) |
| `History: segment totals plus cells outside any segment equal the overall total` | [CK-019](#CK-019) |
| `HOLD_POSITION` | [OUT-205](#OUT-205) |
| `hold_position_rows` | [IN-085](#IN-085), [OUT-174](#OUT-174) |
| `in segment` | [LG-023](#LG-023) |
| `in_case_selector` | [IN-125](#IN-125) |
| `in_need_rate` | [INT-019](#INT-019) |
| `in_ntr_target_eff` | [INT-020](#INT-020) |
| `in_pct_corr` | [INT-022](#INT-022) |
| `in_tuition_implied_pct` | [INT-021](#INT-021) |
| `incentive` | [LG-029](#LG-029) |
| `incentive eligible` | [LG-024](#LG-024) |
| `incentive_cells` | [OUT-073](#OUT-073) |
| `incentive_cost` | [OUT-034](#OUT-034) |
| `INCENTIVE_NOT_VALID` | [OUT-224](#OUT-224) |
| `incentive_paid_anyway` | [OUT-065](#OUT-065) |
| `incentive_paid_anyway_share` | [OUT-066](#OUT-066) |
| `INCENTIVE_VALID` | [OUT-223](#OUT-223) |
| `incentive_valid` | [OUT-074](#OUT-074) |
| `increase %` | [LG-003](#LG-003) |
| `integer_admits` | [IN-056](#IN-056) |
| `integer_enrolled` | [IN-057](#IN-057) |
| `is_held` | [INT-024](#INT-024) |
| `jd_ntr` | [OUT-045](#OUT-045) |
| `Ledger: admits at most applications` | [CK-021](#CK-021) |
| `Ledger: award at least zero and at most tuition after the incentive` | [CK-023](#CK-023) |
| `Ledger: enrolled at most admits` | [CK-022](#CK-022) |
| `Ledger: totals row equals the sum of in-state and out-of-state cell rows (enrolled)` | [CK-020](#CK-020) |
| `Ledger: yield between 0 and 1` | [CK-024](#CK-024) |
| `LEGEND_HELD` | [OUT-220](#OUT-220) |
| `LEGEND_NAMES` | [OUT-216](#OUT-216) |
| `LEGEND_NEED` | [OUT-218](#OUT-218) |
| `LEGEND_PROB` | [OUT-217](#OUT-217) |
| `LEGEND_TIE` | [OUT-219](#OUT-219) |
| `LibreOffice acceptance version (config/tools.yaml)` | [OUT-173](#OUT-173) |
| `LINEAR_APPROX` | [OUT-192](#OUT-192) |
| `loaded.admit_rate` | [IN-128](#IN-128) |
| `loaded.award_usd` | [IN-129](#IN-129) |
| `loaded.need_total` | [IN-132](#IN-132) |
| `loaded.parent` | [IN-134](#IN-134) |
| `loaded.pool_multiplier` | [IN-130](#IN-130) |
| `loaded.sources` | [IN-133](#IN-133) |
| `loaded.specialty_usd` | [IN-131](#IN-131) |
| `loaded.tuition` | [IN-127](#IN-127) |
| `loaded.yield` | [IN-126](#IN-126) |
| `LOWEST_BAND` | [OUT-214](#OUT-214) |
| `M (trim)` | [INT-055](#INT-055) |
| `margin_expected` | [INT-030](#INT-030), [INT-032](#INT-032) |
| `margin_q_t` | [OUT-022](#OUT-022) |
| `margin_t` | [OUT-019](#OUT-019) |
| `margin_to_target` | [OUT-050](#OUT-050) |
| `MARGINAL_ADMIT_NOTE` | [OUT-240](#OUT-240) |
| `marginal_admit_yield_slope` | [IN-059](#IN-059) |
| `med_parts.Gm` | [INT-047](#INT-047) |
| `med_parts.Gp` | [INT-046](#INT-046) |
| `med_parts.Vm` | [INT-048](#INT-048) |
| `median sign {measure} {t}` | [LG-014](#LG-014) |
| `merit` | [OUT-033](#OUT-033) |
| `merit $` | [LG-036](#LG-036) |
| `merit (Distribution)` | [OUT-152](#OUT-152) |
| `merit_actual_by_cohort` | [IN-040](#IN-040) |
| `merit_change` | [OUT-068](#OUT-068) |
| `mode` | [IN-070](#IN-070), [OUT-170](#OUT-170) |
| `Mode: a live build has no loaded values` | [CK-015](#CK-015) |
| `Mode: the Ledgers take the loaded yields and tuition (Reproduce) or the response (Live)` | [CK-016](#CK-016) |
| `MODE_LIVE_BUILD` | [CK-009](#CK-009) |
| `MODE_REPRO_LIVE` | [CK-007](#CK-007) |
| `MODE_REPRO_OK` | [CK-006](#CK-006) |
| `MODE_UNKNOWN` | [CK-008](#CK-008) |
| `N` | [OUT-129](#OUT-129) |
| `n` | [INT-002](#INT-002) |
| `name` | [IN-089](#IN-089) |
| `nearest_m` | [OUT-110](#OUT-110) |
| `nearest_row` | [INT-051](#INT-051) |
| `need` | [OUT-035](#OUT-035) |
| `need departure` | [LG-005](#LG-005) |
| `need rate` | [LG-004](#LG-004) |
| `need.reference_class` | [IN-033](#IN-033) |
| `need.total` | [IN-032](#IN-032) |
| `NEED_DEPARTURE_NOTE` | [OUT-212](#OUT-212) |
| `NEED_LABEL` | [OUT-186](#OUT-186) |
| `need_total` | [IN-097](#IN-097) |
| `net tuition weight` | [LG-037](#LG-037) |
| `NET_TUITION_FIXED` | [OUT-188](#OUT-188) |
| `net_tuition_line_fixed` | [OUT-083](#OUT-083) |
| `net_tuition_line_fixed_text` | [OUT-086](#OUT-086) |
| `net_tuition_line_scaled` | [OUT-085](#OUT-085) |
| `NET_TUITION_SCALED` | [OUT-189](#OUT-189) |
| `no_merit_award_n` | [OUT-030](#OUT-030) |
| `NO_SEGMENT_CELLS` | [OUT-221](#OUT-221) |
| `NOT_USED_ENTERING` | [OUT-211](#OUT-211) |
| `ntr_change` | [OUT-069](#OUT-069) |
| `ntr_const` | [INT-034](#INT-034) |
| `ntr_goal_basis` | [IN-035](#IN-035) |
| `ntr_hi90` | [OUT-040](#OUT-040) |
| `ntr_lo90` | [OUT-039](#OUT-039) |
| `ntr_per_additional` | [OUT-072](#OUT-072) |
| `ntr_target` | [IN-034](#IN-034), [OUT-041](#OUT-041) |
| `ntr_target_effective` | [OUT-042](#OUT-042) |
| `ntr_y1` | [OUT-038](#OUT-038) |
| `outcome` | [OUT-131](#OUT-131) |
| `p_class_in_band` | [OUT-012](#OUT-012) |
| `p_class_over_cap` | [OUT-011](#OUT-011) |
| `p_jd_ntr_ge_goal` | [OUT-046](#OUT-046) |
| `p_median_t` | [OUT-020](#OUT-020) |
| `p_median_t_rho05` | [OUT-021](#OUT-021) |
| `p_ntr_y1_ge_target` | [OUT-043](#OUT-043) |
| `p_pct_q_t` | [OUT-023](#OUT-023) |
| `p_pct_q_t_rho05` | [OUT-024](#OUT-024) |
| `p_segment_goal` | [OUT-061](#OUT-061) |
| `p_segment_goal_exact` | [OUT-062](#OUT-062) |
| `parent` | [IN-090](#IN-090) |
| `parts.M` | [INT-042](#INT-042) |
| `parts.V` | [INT-043](#INT-043) |
| `parts.Vn` | [INT-045](#INT-045) |
| `parts.W` | [INT-044](#INT-044) |
| `PCT_APPROX_BELOW` | [INT-039](#INT-039) |
| `PCT_APPROX_LABEL` | [OUT-194](#OUT-194) |
| `pct_approximate` | [OUT-026](#OUT-026) |
| `pct_band_q` | [OUT-027](#OUT-027) |
| `pct_expected_below` | [OUT-025](#OUT-025) |
| `PCT_MARGIN_SWAPS` | [OUT-203](#OUT-203) |
| `PCT_MARGIN_UNIT` | [OUT-201](#OUT-201) |
| `pct_parts.Vp` | [INT-049](#INT-049) |
| `PCT_TIE_RULE` | [OUT-204](#OUT-204) |
| `percentile sign q {q}, t {t}` | [LG-015](#LG-015) |
| `Percentile target {j}: q equals its value at build` | [CK-043](#CK-043) |
| `Percentile target {j}: t is a band bound (score.bands)` | [CK-042](#CK-042) |
| `plan_year` | [IN-092](#IN-092) |
| `POLICY_UNSCORED_EXCLUDED` | [OUT-242](#OUT-242) |
| `POLICY_UNSCORED_TRIMMED_FIRST` | [OUT-241](#OUT-241) |
| `pool admits: all` | [INT-010](#INT-010) |
| `pool admits: group` | [INT-009](#INT-009) |
| `pool admits: res x group` | [INT-008](#INT-008) |
| `pool admits: res x seg x group` | [INT-007](#INT-007) |
| `POOL_BE_ABOVE_GRID` | [OUT-208](#OUT-208) |
| `POOL_BE_ANY` | [OUT-206](#OUT-206) |
| `POOL_BE_AT_MOST` | [OUT-213](#OUT-213) |
| `POOL_BE_BELOW_GRID` | [OUT-209](#OUT-209) |
| `POOL_BE_NOT_REACHED` | [OUT-207](#OUT-207) |
| `POOL_BREAKEVEN_LABEL` | [OUT-198](#OUT-198) |
| `pool_breakeven_m` | [OUT-111](#OUT-111) |
| `pool_breakeven_m[m_class]` | [OUT-112](#OUT-112) |
| `pool_breakeven_m[m_median]` | [OUT-113](#OUT-113) |
| `pool_breakeven_m[m_q]` | [OUT-114](#OUT-114) |
| `pool_level` | [INT-012](#INT-012) |
| `pool_multiplier` | [IN-095](#IN-095), [OUT-109](#OUT-109) |
| `pool_strip` | [OUT-099](#OUT-099) |
| `pool_strip[class_mean]` | [OUT-101](#OUT-101) |
| `pool_strip[growth]` | [OUT-100](#OUT-100) |
| `pool_strip[margin_score_{t}]` | [OUT-105](#OUT-105) |
| `pool_strip[marker]` | [OUT-108](#OUT-108) |
| `pool_strip[ntr_mean]` | [OUT-103](#OUT-103) |
| `pool_strip[ntr_sd]` | [OUT-104](#OUT-104) |
| `pool_strip[p_class_over_cap]` | [OUT-102](#OUT-102) |
| `pool_strip[p_median_score_{t}]` | [OUT-106](#OUT-106) |
| `pool_strip[p_pct_q{q}_{t}]` | [OUT-107](#OUT-107) |
| `POOL_STRIP_LABEL` | [OUT-190](#OUT-190) |
| `pool_ytd_as_of` | [IN-069](#IN-069) |
| `pool_ytd_growth` | [IN-068](#IN-068) |
| `POOL_YTD_LABEL` | [OUT-191](#OUT-191) |
| `POOL_YTD_MARKER` | [OUT-199](#OUT-199) |
| `POOL_YTD_NO_DATE` | [OUT-200](#OUT-200) |
| `POOL_YTD_TIE` | [OUT-210](#OUT-210) |
| `pooling_k` | [IN-054](#IN-054) |
| `pooling_min_admits` | [IN-055](#IN-055) |
| `position_groups` | [INT-060](#INT-060) |
| `price_of_target` | [OUT-049](#OUT-049) |
| `PROB_OVER` | [OUT-184](#OUT-184) |
| `PROB_UNDER` | [OUT-183](#OUT-183) |
| `python` | [OUT-171](#OUT-171) |
| `R` | [INT-054](#INT-054) |
| `RANGE_CASES` | [OUT-180](#OUT-180) |
| `RANGE_CASES_NOTE` | [OUT-182](#OUT-182) |
| `RANGE_OUTCOME` | [OUT-179](#OUT-179) |
| `RANGE_OUTCOME_NOTE` | [OUT-181](#OUT-181) |
| `rates` | [INT-057](#INT-057) |
| `rates_changed` | [OUT-133](#OUT-133) |
| `REBUILD_NEEDED` | [CK-003](#CK-003) |
| `removed_share` | [INT-056](#INT-056) |
| `REPRO_LEVERS_DIFFER` | [CK-010](#CK-010) |
| `REPRO_TUITION_DIFFERS` | [CK-011](#CK-011) |
| `reproduce` | [IN-071](#IN-071) |
| `reproduce.round_apps_after_pool` | [IN-074](#IN-074) |
| `reproduce.tuition_increase_pct` | [IN-072](#IN-072) |
| `reproduce.unscored_in_median` | [IN-073](#IN-073) |
| `Reproduce: Levers admit rates, resolved awards (Middle) and pool multiplier equal the loaded values` | [CK-046](#CK-046) |
| `Reproduce: the tuition formula at the scenario's increase equals the loaded tuition` | [CK-047](#CK-047) |
| `requirements.lock hash (sha256)` | [OUT-163](#OUT-163) |
| `residency` | [IN-116](#IN-116), [LG-008](#LG-008) |
| `response source` | [OUT-168](#OUT-168) |
| `RESPONSE_LABEL` | [OUT-175](#OUT-175) |
| `Revenue goal: ntr_goal_basis all_jd needs continuing_ntr_usd` | [CK-030](#CK-030) |
| `RHO_SENSITIVITY` | [OUT-193](#OUT-193) |
| `risk.common_shock_sd` | [IN-041](#IN-041) |
| `risk.pool_grid` | [IN-052](#IN-052) |
| `risk.sensitivity_slopes.high` | [IN-046](#IN-046) |
| `risk.sensitivity_slopes.low` | [IN-044](#IN-044) |
| `risk.sensitivity_slopes.middle` | [IN-045](#IN-045) |
| `risk.shock_corr_above_below` | [IN-043](#IN-043) |
| `risk.shock_source` | [IN-042](#IN-042) |
| `risk.tuition_grid` | [IN-053](#IN-053) |
| `risk.yield_cap.lower` | [IN-050](#IN-050) |
| `risk.yield_cap.upper` | [IN-048](#IN-048) |
| `risk.yield_floor.lower` | [IN-049](#IN-049) |
| `risk.yield_floor.upper` | [IN-047](#IN-047) |
| `risk.yield_shift_grid` | [IN-051](#IN-051) |
| `rm_k` | [INT-053](#INT-053) |
| `Rounding probe (R3-3): ROUND({expr}, 0); the argument is one binary step below 2.5. {rest}` | [CK-017](#CK-017) |
| `SAVINGS_PER_LOST` | [OUT-226](#OUT-226) |
| `Scenario` | [LG-001](#LG-001) |
| `scenarios` | [OUT-161](#OUT-161) |
| `scenarios hash (sha256)` | [OUT-162](#OUT-162) |
| `SCOPE_ERROR` | [CK-004](#CK-004) |
| `score.bands` | [IN-014](#IN-014) |
| `score.floor` | [IN-016](#IN-016) |
| `score.measure` | [IN-013](#IN-013) |
| `score.median_thresholds` | [IN-020](#IN-020) |
| `score.percentile_targets` | [IN-017](#IN-017) |
| `score.percentile_targets.q` | [IN-018](#IN-018) |
| `score.percentile_targets.t` | [IN-019](#IN-019) |
| `score.pool_threshold` | [IN-015](#IN-015) |
| `score_group_upper` | [INT-001](#INT-001) |
| `score_lo` | [IN-118](#IN-118) |
| `score_lo (blank = unscored)` | [LG-010](#LG-010) |
| `score_thresholds` | [INT-023](#INT-023) |
| `scored (1/0)` | [LG-012](#LG-012) |
| `segment` | [IN-104](#IN-104), [IN-117](#IN-117), [LG-006](#LG-006), [LG-009](#LG-009) |
| `Segment cells lie within their residency` | [CK-034](#CK-034) |
| `segment_admits` | [OUT-054](#OUT-054) |
| `SEGMENT_APPROX` | [OUT-222](#OUT-222) |
| `SEGMENT_APPROX_BELOW` | [INT-040](#INT-040) |
| `segment_approximate` | [OUT-064](#OUT-064) |
| `segment_apps` | [OUT-053](#OUT-053) |
| `segment_enrolled` | [OUT-055](#OUT-055) |
| `segment_goal` | [IN-106](#IN-106), [OUT-060](#OUT-060) |
| `segment_hi90` | [OUT-059](#OUT-059) |
| `segment_lo90` | [OUT-058](#OUT-058) |
| `segment_merit` | [OUT-057](#OUT-057) |
| `segment_pool_lift_pct` | [IN-105](#IN-105) |
| `segment_share` | [OUT-056](#OUT-056) |
| `SEGMENT_SHARE_LABEL` | [OUT-178](#OUT-178) |
| `SEGMENT_UNNAMED` | [CK-005](#CK-005) |
| `segment_v` | [INT-036](#INT-036) |
| `segments` | [IN-060](#IN-060) |
| `segments.members_label` | [IN-063](#IN-063) |
| `segments.name` | [IN-061](#IN-061) |
| `segments.share_source` | [IN-064](#IN-064) |
| `segments.within.residency` | [IN-062](#IN-062) |
| `share_at_or_above_t` | [OUT-014](#OUT-014) |
| `shift_pts` | [OUT-095](#OUT-095) |
| `shock source` | [OUT-169](#OUT-169) |
| `SHOCK_LABEL` | [OUT-177](#OUT-177) |
| `small_cell_suppression` | [IN-086](#IN-086) |
| `specialty` | [OUT-036](#OUT-036) |
| `specialty_usd` | [IN-096](#IN-096) |
| `Spend against budget_total (Middle case; budget_basis: total aid, or merit only)` | [CK-029](#CK-029) |
| `SPREAD_QS` | [INT-041](#INT-041) |
| `Static exact segment probability is current (Summary segment block)` | [CK-044](#CK-044) |
| `status (trim)` | [INT-058](#INT-058) |
| `STEP_SIZES` | [OUT-154](#OUT-154) |
| `STICKER_LABEL` | [OUT-187](#OUT-187) |
| `Summary expected class equals the Ledger total` | [CK-033](#CK-033) |
| `sw_selected` | [OUT-001](#OUT-001) |
| `test4` | [IN-088](#IN-088) |
| `timestamp` | [OUT-167](#OUT-167) |
| `top_quartile_enrolled` | [INT-062](#INT-062) |
| `top_quartile_merit` | [OUT-151](#OUT-151) |
| `top_quartile_merit_share` | [OUT-153](#OUT-153) |
| `Total` | [LG-040](#LG-040) |
| `Trim order: active segment equals its value at build` | [CK-041](#CK-041) |
| `Trim order: first median threshold equals its value at build` | [CK-037](#CK-037) |
| `Trim order: score.floor equals its value at build (protect_segment above_floor)` | [CK-040](#CK-040) |
| `Trim order: trim.protect_segment equals its value at build` | [CK-038](#CK-038) |
| `trim.exempt_cells` | [IN-067](#IN-067) |
| `trim.floor_rate` | [IN-066](#IN-066) |
| `trim.protect_segment` | [IN-065](#IN-065) |
| `Trim: trim.exempt_cells equals its value at build` | [CK-039](#CK-039) |
| `trim_order` | [INT-052](#INT-052) |
| `tuition` | [LG-002](#LG-002) |
| `Tuition formula reproduces the step {y0} to {y1} (increase rounded to 0.1%, tuition to tuition_rounding_usd)` | [CK-025](#CK-025) |
| `tuition_base` | [IN-009](#IN-009) |
| `tuition_by_cohort` | [IN-008](#IN-008) |
| `tuition_by_year_usd` | [IN-011](#IN-011) |
| `tuition_increase_by_year` | [IN-010](#IN-010) |
| `tuition_increase_pct` | [IN-093](#IN-093), [OUT-081](#OUT-081) |
| `tuition_rounding_usd` | [IN-012](#IN-012) |
| `tuition_whatif` | [OUT-076](#OUT-076) |
| `tuition_whatif[discount_entering_y1]` | [OUT-080](#OUT-080) |
| `tuition_whatif[net_tuition_per_student]` | [OUT-079](#OUT-079) |
| `tuition_whatif[ntr_y1]` | [OUT-078](#OUT-078) |
| `tuition_whatif[tuition]` | [OUT-077](#OUT-077) |
| `uncommitted files` | [OUT-165](#OUT-165) |
| `UNDER_HALF` | [OUT-227](#OUT-227) |
| `unscored_count` | [OUT-017](#OUT-017) |
| `unscored_in_median` | [IN-025](#IN-025) |
| `upper group (1/0)` | [LG-013](#LG-013) |
| `V` | [INT-026](#INT-026) |
| `v` | [INT-025](#INT-025) |
| `v_m` | [INT-031](#INT-031) |
| `v_q` | [INT-033](#INT-033) |
| `Vn` | [INT-035](#INT-035) |
| `vrow_cells_changed` | [OUT-134](#OUT-134) |
| `xlsxwriter` | [OUT-172](#OUT-172) |
| `y0` | [INT-013](#INT-013) |
| `y0 {case}` | [LG-019](#LG-019) |
| `ybar` | [INT-005](#INT-005) |
| `yield` | [LG-032](#LG-032) |
| `Yield at award rungs` | [INT-018](#INT-018) |
| `yield cap` | [LG-017](#LG-017) |
| `yield floor` | [LG-016](#LG-016) |
| `yield shift (pts)` | [LG-031](#LG-031) |
| `yield_shift_pts` | [IN-107](#IN-107) |
| `yield_shift_pts_in` | [IN-108](#IN-108) |
| `yield_shift_pts_out` | [IN-109](#IN-109) |
| `yield_shift_pts_segment` | [IN-110](#IN-110) |
| `yield_strip` | [OUT-087](#OUT-087) |
| `yield_strip[class_mean]` | [OUT-088](#OUT-088) |
| `yield_strip[margin_{measure}_{t}]` | [OUT-093](#OUT-093) |
| `yield_strip[ntr_mean]` | [OUT-091](#OUT-091) |
| `yield_strip[p_class_in_band]` | [OUT-090](#OUT-090) |
| `yield_strip[p_class_over_cap]` | [OUT-089](#OUT-089) |
| `yield_strip[p_median_{measure}_{t}]` | [OUT-094](#OUT-094) |
| `yield_strip[p_ntr_y1_ge_target]` | [OUT-092](#OUT-092) |
| `ypool` | [INT-011](#INT-011) |
| `Z90` | [INT-038](#INT-038) |
