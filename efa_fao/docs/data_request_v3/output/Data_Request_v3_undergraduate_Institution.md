# [Institution]: Enrollment Funnel and Financial Aid Data Request (v3)

**Program:** Undergraduate programs  
**Prepared for:** [Institution], Enrollment Management and Financial Aid  
**Prepared by:** [Frankel contact]  
**Date:** [Date]  
**Response requested by:** [Date]  


## 1. Why we are asking for more than a typical funnel study

Two questions drive this engagement. First, where do prospective students leave the funnel? Second, what award policy should guide the next discretionary aid dollar? The second question depends on knowing what each student was offered and when, so this request asks for aid in components with dates, not totals. It also asks for the rules behind your awards, which let us learn price sensitivity without guesswork.

To keep the start-up effort proportional to what you need, the request comes in two tiers.


## 2. Two tiers

| Tier | What you send | What it supports |
|---|---|---|
| Tier 1 (minimum) | Three entering cohorts; final aid packages by component; offer dates where you have them; the merit grid; the cycle calendar; your Common Data Set filings for the same years | Funnel analysis, yield forecast, in-cycle pacing and melt monitoring, loan-cap exposure, and a first estimate of price sensitivity from the merit grid (with a wider range) |
| Tier 2 (full) | Four to five cohorts; every package version with its date and reason code; the merit grid with effective dates; a price test | Everything in Tier 1, plus a recommended scholarship policy grid with budget scenarios |

You can start at Tier 1 and move to Tier 2 in a later cycle. Three cohorts is the minimum and five is ideal. If you hold more than five years of history, tell us before you pull it, especially if your award policy changed in that period: a policy change is useful evidence.


## 3. What we need

Aid offers are needed for every cohort you send, not only the most recent. We provide an Excel template with the header row, data types and code lists for every file below, so you can see the exact structure before you pull anything (Data_Request_Template). Appendix A lists every field.

| File | One row per | Key fields | Tier |
|---|---|---|---|
| `students` | Person and entry term | Entry year and term, entrant type, level, program, residency, state and ZIP3, first-touch source and date, inquiry, application, decision, deposit and census dates, plan type, campus visit, engagement counts, GPA, test scores (blank if not submitted), first-generation status, race and ethnicity and gender (audit only), age, athlete flag, excluded-group flag, housing application | 1 |
| `fafsa` | Person and aid year | Whether the student applied for federal aid, received date, need index value and type (EFC or SAI), dependency, verification selected and completed dates, Pell eligibility, institutional-methodology need and income band if used | 1 |
| `aid_offers` | Person, fund, and package version | Fund code, component, offered amount and date, renewal rule and conditions, commitment years, revision reason code, accepted and disbursed amount, PLUS decision | 1 (final package); 2 (every version) |
| `fund_crosswalk` | Fund | Fund code and name, standard component, gift or self-help, source, need-based or non-need-based rule, discretionary and excluded-group flags | 1 |
| `pricing` | Entry year, program, and residency group | Tuition, required fees, food and housing, books, transportation, other cost-of-attendance items | 1 |
| `aid_policy` | Entry year and program | Award mode, merit grid with thresholds, need-grant formula, discretionary budget, discount and class-size targets, class-size band and cap type, floors, blinding and visibility answers | 1 (grid and rules); 2 (effective dates) |
| `cycle_calendar` | Cohort and calendar event | Application dates, offer batches, aid dates, reply and deposit deadlines with amount and refund terms, housing deposit, census date | 1 |
| `award_renewals` | Person and award year | Renewed amount, outcome, reason for any reduction or loss | 2 (if any award is conditional) |
| `price_test` | Eligible admit | In-test flag, assignment date, stratum, bonus amount, randomization batch and seed | 2 (only if the screen recommends a test) |
| `activity_log` | Recorded activity | Activity type, raw source label, date | Optional |
| `zip_key` | Person | Hashed key, ZIP5, address type | Optional add-on |
| `Institutional_Reference` (worksheet) | Measure and cohort | Totals you already file or publish, for reconciliation (see Institutional reference) | 1 |
| `Scoping_Inputs` (worksheet) | Input | Answers for the price-test screen (see Scoping inputs) | 1 |

Please also send your own data dictionary: each variable you export and every possible value of each coded variable (program codes, decision codes, source labels, fund codes). We map your values to ours with you and return a list of anything we could not map.

**Excluded groups:** please flag students whose aid follows rules outside the normal process, such as athletes, tuition waivers and exchanges, employee dependents, and named special scholarships. They keep their current packages in every scenario and are reported separately so your class totals still reconcile.

If a field is not recorded, tell us. Do not fill it with zeros or a default.


## 4. Definitions we need to agree on

Where a term has a Common Data Set definition, we use it, so your totals reconcile to what you already publish. Where our analysis needs something the Common Data Set does not define, we say so.

| Term | Definition we use | Source |
|---|---|---|
| **Applicant** | An individual who has fulfilled your requirements to be considered for admission (including payment or waiving of the application fee, if any) and who has been notified of admission, nonadmission, placement on the waiting list, or application withdrawn. | CDS definitions |
| **Admitted** | Offered admission to a degree-granting program, including a person admitted from the waiting list. The offer date is the date the offer was communicated. | CDS definitions |
| **Enrolled** | Enrolled at the official census date of the entry term. Please use one definition for all years. It should reconcile to enrolled first-time first-year students in your Common Data Set (C1). | M section 3; CDS C1 |
| **Entrant type** | First-time, first-year: attending any institution for the first time at the undergraduate level (including students who first attended in the prior summer, and those with college credit earned before high school graduation). Transfer: entering for the first time but known to have attended another postsecondary institution at the same level. | CDS definitions |
| **Full-time and part-time** | Full-time: 12 or more semester or quarter credits per term. Part-time: fewer. | CDS definitions |
| **Residency** | In-state, out-of-state, international or unknown, from the known physical address at the time of application (CDS C1). Billing residency, if different, goes in `tuition_residency`. | CDS C1 |
| **Plan type** | Early decision (binding; the applicant agrees to enroll if admitted and to withdraw other applications), early action (non-binding), restrictive early action, regular, rolling. | CDS C21-C22 |
| **Waiting list** | Students who meet the admission requirements but are offered a place only if space becomes available. Send the date placed and, if later admitted, the offer date. | CDS C2 |
| **Deferral** | Admitted students allowed to postpone enrollment, usually one term or one year. Send the cohort and term in which the student actually entered. | CDS C18 |
| **Offered amount** | What the student was told, on the offer date. For Tier 2, keep every package version, not only the final one. | v2.1 |
| **Decision date** | The student's deposit deadline or the date the student deposited, whichever is earlier. Awards that arrive later (for example, external scholarships reported after enrollment) must carry their true dates so we can keep them out of the price analysis. | M section 3 |
| **Revision reason code** | Every award revision carries one reason: student request, documented competing offer, staff-initiated, or appeal. | M section 3 |
| **Need-based and non-need-based aid** | Need-based scholarship or grant aid: from institutional, state, federal or other sources, for which a student must have financial need to qualify. Non-need-based: awarded solely on academic achievement, merit or any other non-need reason. We classify each fund by its own rule, not by the CDS precedence order for counting non-need aid used to meet need. | CDS H definitions |
| **Institutional scholarships and grants** | Endowed scholarships, annual gifts and tuition-funded grants for which you determine the recipient. | CDS H definitions |
| **External scholarships** | Scholarships and grants from outside sources that students bring with them (for example, National Merit). You may process the paperwork, but you do not decide the recipient or the amount. | CDS H definitions |
| **Tuition waivers** | Report waivers as their own component, not inside institutional merit. They are an excluded group. | CDS H definitions |
| **Work study and employment** | Federal and state work-study aid, and any employment packaged by your institution. | CDS H definitions |
| **Financial aid applicant** | Any applicant who submits any institutionally required aid application, such as the FAFSA. | CDS H definitions |
| **Need index** | EFC for aid years through 2023-24 and SAI for 2024-25 onward, with a column saying which. Keep negative SAI values. 'No FAFSA' is its own category. | M section 3 |
| **Cost of attendance** | Tuition, required fees (those every full-time student pays), food and housing (double occupancy, 19 meals a week or the maximum plan), books and supplies, and transportation (two round trips home for students in institutional housing). | CDS G1 and definitions |
| **Stealth applicant** | A person whose first recorded contact is the application. Flag them; do not drop them. | v2.1 |
| **Test scores** | Leave blank if not submitted. Do not impute or convert. | M section 2 |
| **Missing values** | Missing is never zero. Leave unknown values blank. If aid data does not exist for a cohort, tell us instead of sending zeros. | v2.1 |
| **Source labels** | Send your raw source strings. We apply a versioned mapping and return a list of anything unmapped for your review. | v2.1 |


## 5. Aid components

| Component | Gift or self-help | Notes |
|---|---|---|
| `inst_merit` | Gift | Institutional merit award (non-need-based) |
| `inst_need` | Gift | Institutional need-based grant |
| `inst_athletic` | Gift | Institutional athletic award |
| `inst_discretionary` | Gift | Institutional discretionary award, including appeals and reconsideration increases |
| `inst_other` | Gift | Other institutional gift aid (named, restricted or special-purpose funds) |
| `inst_remission` | Gift | Tuition waiver, remission or exchange (employee dependents, exchange programs). Excluded group |
| `state_grant` | Gift | State grant |
| `pell` | Gift | Federal Pell Grant |
| `seog` | Gift | Federal SEOG |
| `external_scholarship` | Gift | Scholarships from outside sources for which you do not choose the recipient or the amount |
| `sub_loan` | Self-help | Federal Direct Subsidized Loan |
| `unsub_loan` | Self-help | Federal Direct Unsubsidized Loan |
| `parent_plus` | Self-help | Parent PLUS |
| `grad_plus` | Self-help | Grad PLUS (cohorts before July 1 2026 and grandfathered borrowers) (if any) |
| `private_loan` | Self-help | Private or institutional loan |
| `work_study` | Self-help | Federal or state work-study and any employment packaged by your institution |

Please also send your fund-code crosswalk (file `fund_crosswalk`) so we can map your codes to these components. For each fund, state its own eligibility rule (need-based, non-need-based or mixed). We classify by the fund rule. Your Common Data Set counts non-need aid that is used to meet need as need-based; we keep the fund rule and reconcile the difference in QA.

**Why loans matter now:** Grad PLUS closed to new borrowers on July 1, 2026, and new annual and aggregate caps apply to graduate and professional borrowing and to Parent PLUS. Prior-year PLUS amounts, approvals and denials let us show how many of your admits, by program, now face a financing gap and what that could mean for enrollment and revenue. Loans are never treated as a price reduction in our models.


## 6. Your award rules

The merit grid is the single most valuable document for this study. Awards that change at fixed GPA or test thresholds let us estimate price sensitivity without bias. Please send:

- The grid for each cohort, with exact thresholds and effective dates.
- How need-based institutional grants are calculated.
- How discretionary awards and appeals are decided, and who decides.
- Whether the award is the total institutional scholarship or a supplement added after formula awards, and how stipends above tuition are handled.
- The scholarship budget and your targets for discount rate and class size.
- The class-size band you accept (for example 3, 5 or 10 percent) and whether the class target is a hard seat cap or a soft target. We need this before we say anything about a price test.
- Planned tuition changes for the next entering class, if decided.
- Any limits you want on change: for example, the largest cut any group's award may take, or minimum awards for particular groups.


## 7. Scoping inputs for the price-test screen

Before we propose any price test, we run a short value-of-information screen. It can conclude that a test is not worth its cost. The verdict depends on your class-size band, which is why we ask for it up front. We compute the first group of inputs from your data. You confirm them and supply the rest.

| Who supplies it | Input | Description |
|---|---|---|
| We compute from your data (you confirm) | **Eligible admits per cohort (N)** | Admits who are not in an excluded group and are eligible for a discretionary award |
| We compute from your data (you confirm) | **Eligible yield (p)** | Share of eligible admits who enroll at census |
| We compute from your data (you confirm) | **Annual tuition** | Published tuition for the entering class |
| We compute from your data (you confirm) | **Mean institutional award per enrollee** | From the final packages |
| We compute from your data (you confirm) | **Award commitment length and persistence** | Years the award is committed and the share that renews |
| You supply | **Class-size band and cap type** | The band you accept around the class target (for example 3, 5 or 10 percent) and whether it is a hard cap or a soft target. Mandatory: the verdict depends on it |
| You supply | **Floors and targets** | Minimum awards for groups, and class-profile targets you manage to |
| You supply | **Who decides** | The VP or Director of Enrollment, or a Dean, who decides whether a test runs |
| You supply | **Cycles of use** | How many cycles you would use a result for (default 3) |
| You supply | **Operating cost of a test** | Staff time and system cost per cycle of running a test |
| You supply | **Blinding** | Whether staff can deliver the bonus as a formula line with no test flag in your systems |


## 8. Optional price test (only where the screen recommends one)

A short randomized test of bonus aid for part of the incoming class makes a policy recommendation far more trustworthy. We propose it only where the screen says it pays off, and the decision to run it is yours.

- **Design:** a random 40% of eligible admits (first-time students, not in an excluded group) receive an additional $0, $2,000, or $4,000 in discretionary aid, in a 40% / 20% / 40% split. Assignment is balanced within need band and residency.
- **Why these amounts:** concentrating bonuses at the ends gives a more precise answer than spreading them evenly, at the same average cost per student.
- **Positive only:** nobody receives less than they otherwise would. The bonus is part of the first offer, never a later revision.
- **Cost:** an award that renews costs its first-year amount times the number of years it is committed. We report the cost, and the smallest effect the test could detect, before you decide.
- **Keep the test clean:** please do not adjust other discretionary aid for students because of their test assignment. If staff can deliver the bonus as a formula line with no test flag visible in your systems, our estimate is stronger; tell us whether that is possible. We check for offsetting behavior and report it.
- **Approvals:** needs sign-off from [financial aid director] and [admissions dean or enrollment VP]. We draft the protocol and the randomization file.
- **Timing:** assignment is made before decisions; we record the assignment date and seed. Please send every eligible admit, not only the test students (file `price_test`).
- **Power:** at your size, expect several cycles to reach a precise estimate. We report the smallest effect the test can detect before it starts.


## 9. Institutional reference and reconciliation

Please send your Common Data Set for the same years as your cohorts. We reconcile your student-level files to the totals you publish, report any difference, and check our yield forecast against your own history. The worksheet `Institutional_Reference` in the template lists the figures; most can be copied from your Common Data Set.

| Group | Figure, for each cohort year | Source | Note |
|---|---|---|---|
| Applications | Applied, admitted and enrolled: first-time, first-year, total | CDS C1 | Enrolled should reconcile to enrolled_census |
| Applications | Applied, admitted and enrolled: by sex, and full-time or part-time | CDS C1 |  |
| Applications | Applied, admitted and enrolled: by in-state, out-of-state, international, unknown | CDS C1 | By known physical address at application |
| Applications | Waiting list: offered a place, accepted, admitted | CDS C2 |  |
| Applications | Early decision and early action: applicants and admits | CDS C21-C22 |  |
| Profile | SAT and ACT: percent submitting, 25th / 50th / 75th percentiles | CDS C9 |  |
| Profile | High school class rank: percent in top tenth / quarter / half and percent reporting | CDS C10 |  |
| Profile | High school GPA distribution and average GPA | CDS C11-C12 |  |
| Enrollment | First-time, first-year enrollment by race and ethnicity and gender | CDS B1 | Used only to reconcile the fairness audit |
| Price | Tuition, required fees, food and housing, books, transportation | CDS G1 |  |
| Aid | Aid awarded to enrolled undergraduates: counts and dollars by source | CDS H1 |  |
| Aid | First-time, full-time students: applied for need-based aid, determined to have need, awarded aid, need fully met | CDS H2 |  |
| Aid | Average aid package, average need-based grant, percent of need met | CDS H2 |  |
| Aid | Non-need-based institutional aid: number and average (and athletic awards) | CDS H2A |  |
| Aid | Graduates with debt and average indebtedness | CDS H4-H5 | Confirm item numbers against your own filing |


## 10. Optional additions

- **In-cycle export:** a weekly or biweekly extract of the `students` and `aid_offers` files during yield season (from first release to census) powers pacing against last year and melt monitoring. We give you a saved query or export spec. Please include the date and reason code for any award revision.
- **Activity history:** every recorded activity with its raw source label and date, not only the first (file `activity_log`). It lets us identify the first inquiry type and report source effectiveness.
- **Where admitted students went:** a National Student Clearinghouse StudentTracker match for admits who did not enroll, ordered by your office. We join it to public net-price data to show which institutions you lose students to, and at what cost difference.
- **Admitted-student survey:** a short survey of enrolling and non-enrolling admits on competing offers and reasons for their choice, designed and fielded by [our team] with your approval.
- **Peer set:** a list of 8 to 15 institutions you consider peers, for sticker and net-price comparison from public data.
- **Neighborhood context:** if you want neighborhood indicators (for example, educational attainment or median income by Census tract), we supply a script your office runs before removing addresses. Only the resulting indicators are sent to us.
- **Neighborhood capacity indicators (ZIP5 add-on):** with your written approval under your data-use agreement, you send a separate file (`zip_key`) with the ZIP5 of each applicant's permanent address at application. We attach neighborhood-level indicators from a licensed or public dataset, replace the ZIP5 with derived fields, and delete the file within 30 days of append QA or at engagement close. We receive no household-level data and no street addresses. Race, ethnicity and gender are never used to build or adjust these indicators. We return a match report. No such indicator enters an award grid without your sign-off at the alignment gate and review with counsel.


## 11. How to send data safely

- **No** names, emails, phone numbers, street addresses, full dates of birth, Social Security numbers, or free-text notes. Send age in whole years, not date of birth.
- Replace your student ID with a **hashed key**. Use a salted hash and keep the salt; we never need it. Use the same key in every file and every in-cycle export.
- `students` carries state and **ZIP3** (first three digits). ZIP5 is sent only in the optional `zip_key` file, through your secure channel.
- Dates are welcome (they are converted to days before term start and then discarded).
- Transfer through [secure file transfer]. We delete raw files at engagement close per [retention policy].


## 12. What we do with the data

- We check structure and logic: duplicate keys, stage order, aid for non-admitted students, offsets outside the protocol, and reconciliation to your published totals. Every check and its row count is reported back to you.
- Student-level data stay in our secure compute environment. The dashboard shows aggregates only, with groups smaller than ten suppressed. If you request a student-level list (for example, students at risk of melt), it comes back through your secure channel, not the dashboard.
- Race, ethnicity and gender are used to audit results for fairness, never to decide awards.
- Recommendations are delivered as a scholarship policy (award levels by academic, need, and residency group) that your staff can apply as offers go out.
- No recommendation is published until you and [institution counsel] have reviewed it.


## 13. Timeline

| Step | When |
|---|---|
| Kickoff and definitions call | [Date] |
| Data delivered | [Date] |
| Data quality report back to you | [Date + 1 week] |
| Funnel analysis delivered | [Date + 6 weeks] |
| Aid policy recommendation delivered (Tier 2) | [Date + 10 weeks] |
| In-cycle monitoring begins | [First admit release] |


## 14. Checklist for your team

- [ ] Tier chosen (1 or 2)
- [ ] Three cohorts (Tier 1) or four to five cohorts (Tier 2), with aid for every cohort
- [ ] Offer dates (Tier 1 where available; Tier 2 every package version with a reason code)
- [ ] Merit grid and need-grant formula
- [ ] Fund-code crosswalk, with each fund's eligibility rule
- [ ] Cycle calendar: offer batches, deposit deadlines, census date
- [ ] Class-size band, hard cap or soft target, and who decides on a test
- [ ] PLUS approval and denial history
- [ ] Excluded-group flags
- [ ] Source labels as recorded, not recoded
- [ ] Single enrolled-at-census definition
- [ ] Your own data dictionary, with every code value
- [ ] Common Data Set for the same years
- [ ] Hashed keys, ZIP3 only (ZIP5 only in `zip_key`), no direct identifiers
- [ ] Price test approval (Tier 2, only if the screen recommends one)
- [ ] Optional: in-cycle export, activity history, Clearinghouse match, survey, peer set, `zip_key`
- [ ] If `zip_key` is sent: written approval of the transfer under your data-use agreement; which address field is the permanent address at application; signed acknowledgment of the consumer-data purpose statement at the alignment gate


## Appendix A. Field specification

Required: Y = send it; C = send it under the condition stated; N = optional; blank row = not requested for this program. Tier: 1 = Tier 1; 2 = Tier 2 only; A = optional add-on. The same specification is in the Excel template and in `data_dictionary_v3` (CSV).


### `students`

| Field | Type | Req | Tier | Description | Values or format |
|---|---|---|---|---|---|
| `student_key` | text | Y | 1 | Opaque person key. Hash your institutional ID with a salt you keep. Same key in every file and every in-cycle export. | Stable across files and terms |
| `cohort` | int | Y | 1 | Intended entry year (fall-term year for fall entrants). | Four-digit year |
| `entry_term` | text | Y | 1 | Intended entry term. | Fall; Spring; Summer |
| `actual_entry_cohort` | int | N | 1 | Actual entry year if different from the intended year (deferral, or entered in another term). Blank if the same. | Four-digit year |
| `actual_entry_term` | text | N | 1 | Actual entry term if different from the intended term. Blank if the same. | Fall; Spring; Summer |
| `student_type` | text | Y | 1 | What kind of entrant this is. Other types go to a separate file or are excluded. First-time, first-year as defined in CDS (attending any institution for the first time at the undergraduate level). Transfer as defined in CDS. | First-time first-year; Transfer; Other (excluded) |
| `student_level` | text | Y | 1 | Level of the program applied to. | Undergraduate; Graduate; Professional |
| `program_code` | text | Y | 1 | Program or division the student applied to, as you record it. College, school or division within the university, if you use more than one. | Free text with a code list |
| `enrollment_load` | text | Y | 1 | Full-time or part-time at entry. Full-time = 12 or more semester or quarter credits per term (CDS definition). | Full-time; Part-time |
| `intended_program` | text | Y | 1 | Intended major or program of study at application. Plus a mapping to broad program areas. | Free text with a code list |
| `residency` | text | Y | 1 | Residency at application, based on the known physical address at the time of application. In-state, out-of-state, international or unknown, as in CDS C1. | In-state; Out-of-state; International; Unknown |
| `tuition_residency` | text | N | 1 | Residency class used for billing, only if it differs from `residency`. | Resident; Nonresident |
| `region_code` | text | Y | 1 | State plus the first three ZIP digits (ZIP3), from the permanent address at application. Never the full ZIP. ZIP5 goes only in the optional `zip_key` file. | e.g. VA-232 |
| `cbsa_code` | text | N | 1 | Metropolitan or micropolitan area code. If you send it, produce it with the script we supply, before addresses are removed. | CBSA code or blank |
| `distance_band` | text | N | 1 | Distance-to-campus band from the same script. | e.g. 0-50 mi; 50-150 mi; 150+ mi |
| `first_touch_source_raw` | text | Y | 1 | Raw label for the earliest recorded contact. Do not recode. | Free text; we map it with a versioned source taxonomy |
| `first_touch_date` | date | Y | 1 | Date of the earliest recorded contact (converted to days before term start, then dropped). | On or before inquiry_date |
| `first_touch_is_application` | bool | Y | 1 | True when the application is the first recorded contact (stealth applicant). | true; false |
| `inquiry_date` | date | Y | 1 | Date the person became a prospect or inquiry. | Blank only if first_touch_is_application |
| `application_start_date` | date | N | 1 | Date the application was started. |  |
| `application_submit_date` | date | Y | 1 | Date the application was complete and actionable (all required items received). As in the CDS definition of applicant. | Blank if never completed |
| `plan_type` | text | Y | 1 | Admission plan the applicant applied under. As defined in CDS: early decision (binding), early action (non-binding), restrictive early action, regular, rolling. | Early decision; Early action; Restrictive early action; Regular; Rolling |
| `admit_decision` | text | Y | 1 | Final admission decision at the term census. Applicants placed on a waiting list and never admitted are their own category. | Admitted; Denied; Waitlisted not admitted; Withdrawn before decision; Incomplete |
| `admit_decision_date` | date | Y | 1 | Date of the admission decision (the offer date for admits). |  |
| `offer_release_batch` | text | N | 1 | Label of the batch or wave in which the decision or offer was released. | e.g. Batch 1 Dec 12 |
| `waitlist_placed_date` | date | N | 1 | Date the applicant was placed on the waiting list, if any. | Blank if not waitlisted |
| `waitlist_admit_date` | date | N | 1 | Date a waitlisted applicant was offered admission, if any. | Blank if not admitted from the list |
| `deposit_date` | date | Y | 1 | Date the first enrollment (seat) deposit was received. | Blank if no deposit |
| `enrolled_census` | bool | Y | 1 | Enrolled at the official census date of the entry term. One definition for every cohort. Reconciles to CDS C1 enrolled. | true; false |
| `withdrawal_date` | date | N | 1 | Date of withdrawal before census, if any. | Supports melt analysis |
| `retained_y2` | bool | Y | 1 | Enrolled at the census of the next fall term. | Blank for the current cohort |
| `retained_y3` | bool | N | 1 | Enrolled at the census two falls later. |  |
| `campus_visit_count` | int | Y | 1 | Number of recorded campus visits before the admit decision. | Counts before the decision date only |
| `event_attended_count` | int | N | 1 | Number of recorded events attended before the decision date. |  |
| `engagement_touches` | int | Y | 1 | Count of meaningful two-way contacts (calls, meetings, replies) before the decision date. | Exclude mass-email opens |
| `hs_gpa` | decimal | Y | 1 | High school GPA on a 4.0 scale, as used for merit awards. | Blank if not submitted |
| `hs_gpa_type` | text | Y | 1 | Weighted or unweighted. | Weighted; Unweighted |
| `hs_class_rank_pct` | decimal | N | 1 | High school class rank as a percentile, if you collect it. | 0-100; blank if not reported |
| `act_composite` | int | N | 1 | Best ACT composite. Blank if not submitted. | Do not impute |
| `sat_total` | int | N | 1 | Best SAT total. Blank if not submitted. We convert with the official concordance. | Do not impute |
| `test_optional_flag` | bool | Y | 1 | Applied under a test-optional policy. |  |
| `transfer_gpa` | decimal | N | 1 | Cumulative GPA at prior institutions (transfers). |  |
| `transfer_credits` | int | N | 1 | Credits accepted at admission (transfers). |  |
| `first_gen` | bool | Y | 1 | First-generation status. Blank if unknown. Do not code unknown as No. | true; false; blank |
| `race_ethnicity` | text | Y | 1 | IPEDS categories. Used only to audit results for fairness. Never a model input, grid dimension or target. | IPEDS categories plus Unknown |
| `gender` | text | Y | 1 | As recorded. Used only to audit results for fairness. | As recorded; Unknown |
| `age_at_application` | int | Y | 1 | Age in whole years at the application date. Not the date of birth. | Integer |
| `athlete_recruited` | bool | Y | 1 | Recruited athlete flag. |  |
| `sport` | text | N | 1 | Sport for recruited athletes. |  |
| `military_status` | text | N | 1 | Veteran or active military status. | Veteran; Active; Dependent; None; Unknown |
| `legacy_status` | bool | N | 1 | Alumni family connection. |  |
| `housing_applied` | bool | Y | 1 | Applied for campus housing before census. | Used in melt flags |
| `housing_applied_date` | date | N | 1 | Date the housing application was received. |  |
| `excluded_group_flag` | bool | Y | 1 | True if the student receives aid under rules outside the normal process. | true; false |
| `excluded_group_type` | text | Y | 1 | Why the student is excluded. Recruited athlete, tuition waiver or exchange, employee dependent, named special scholarship, or other. | Free text with a code list |


### `fafsa`

| Field | Type | Req | Tier | Description | Values or format |
|---|---|---|---|---|---|
| `student_key` | text | Y | 1 | Same key as students. |  |
| `aid_year` | text | Y | 1 | Aid year. | e.g. 2026-27 |
| `fafsa_applied` | bool | Y | 1 | Applied for federal aid (FAFSA) for this aid year. | true; false |
| `fafsa_received_date` | date | Y | 1 | Date your office received the first FAFSA record. | Blank if none |
| `need_index_value` | int | Y | 1 | EFC (aid years through 2023-24) or SAI (2024-25 and later). Keep the sign: SAI can be negative. | Integer |
| `need_index_type` | text | Y | 1 | EFC or SAI. The two are not comparable without this label. | EFC; SAI |
| `dependency_status` | text | N | 1 | Dependent or independent. |  |
| `verification_selected` | bool | N | 1 | Selected for verification. |  |
| `verification_completed_date` | date | N | 1 | Date verification was completed. | Blank if not selected or not completed |
| `pell_eligible` | bool | N | 1 | Federal Pell eligibility as packaged. |  |
| `need_methodology` | text | N | 1 | Methodology used to determine need for institutional aid. Federal methodology, institutional methodology, or both (CDS H). | FM; IM; Both; None |
| `institutional_need_amount` | decimal | N | 1 | Need as determined by your institutional methodology (CSS Profile or your own form), if you use one. | Blank if not used |
| `income_band` | text | N | 1 | Household income band from the aid application, only where you package on income or no need index exists. Banded, never exact. | e.g. under 30k; 30-60k; 60-110k; over 110k; unknown |
| `coa_budget_total` | decimal | N | 1 | Cost-of-attendance budget used to package this student, if it varies by student. |  |


### `aid_offers`

| Field | Type | Req | Tier | Description | Values or format |
|---|---|---|---|---|---|
| `student_key` | text | Y | 1 | Same key as students. One row per student, fund and package version. |  |
| `aid_year` | text | Y | 1 | Aid year. | e.g. 2026-27 |
| `fund_code` | text | Y | 1 | Your fund code. Send a crosswalk (file `fund_crosswalk`). |  |
| `component` | text | Y | 1 | Standard component we map the fund code to. You may leave it blank; we map from the crosswalk. | See the component table |
| `offered_amount` | decimal | Y | 1 | Annual amount offered, in dollars. | Never blank. Zero only if you offered zero. Unknown is blank, never zero |
| `offer_date` | date | Y | 1 | Date this amount was first communicated to the student. | Required to exclude aid not known at the decision date |
| `package_version` | int | Y | 2 | Package revision number (1 = first offer). Tier 1: the final package only. Tier 2: every version. | Keep every version at Tier 2 |
| `accepted_amount` | decimal | N | 1 | Amount the student accepted. Post-decision; excluded from price models. |  |
| `disbursed_amount` | decimal | N | 1 | Amount disbursed. Post-enrollment; excluded from price models. |  |
| `renewable_flag` | bool | Y | 1 | Whether the award renews. |  |
| `renewal_rule` | text | C | 1 | How the award renews. Fixed dollars or a percentage of tuition. | Fixed dollars; Percent of tuition; Other |
| `renewal_conditions` | text | C | 1 | Conditions to keep the award (GPA, class rank, credits), stated exactly. Required if any award is conditional on GPA, credits or similar. | Free text |
| `renewal_threshold` | decimal | C | 1 | Numeric threshold for the condition (for example a minimum GPA). |  |
| `commitment_years` | int | Y | 1 | Number of years the award is committed for. Up to program length, as you elect. | Integer |
| `revision_reason_code` | text | Y | 2 | Why a later version differs from the one before it. | Student request; Documented competing offer; Staff-initiated; Appeal; Other |
| `revision_requested_date` | date | N | 2 | Date the student asked for reconsideration, if applicable. |  |
| `plus_borrower` | text | C | 1 | For PLUS loans only: who applied. Parent PLUS: the parent. Grad PLUS: the student. | Student; Parent |
| `plus_decision` | text | C | 1 | For PLUS loans only: credit decision. | Approved; Denied; Not applied |
| `plus_decision_date` | date | C | 1 | For PLUS loans only: date of the credit decision. |  |


### `fund_crosswalk`

| Field | Type | Req | Tier | Description | Values or format |
|---|---|---|---|---|---|
| `fund_code` | text | Y | 1 | Your fund code, as it appears in aid_offers. |  |
| `fund_name` | text | Y | 1 | Name of the fund or scholarship. |  |
| `component` | text | Y | 1 | Standard component (see the component table). | See the component table |
| `aid_category` | text | Y | 1 | Gift or self-help. | Gift; Self-help |
| `funding_source` | text | Y | 1 | Who funds it. | Institutional; Federal; State; External |
| `need_basis` | text | Y | 1 | The fund's own eligibility rule. Classify by the fund rule, not by CDS H precedence. CDS counts non-need aid used to meet need as need-based; we keep the fund rule and reconcile. | Need-based; Non-need-based; Mixed |
| `discretionary_fund` | bool | Y | 1 | True if staff can award from the fund at their discretion (the flexible pool). |  |
| `excluded_group_fund` | bool | Y | 1 | True if awards from the fund follow rules outside the normal process. |  |
| `effective_start` | date | N | 1 | First date the fund was used. |  |
| `effective_end` | date | N | 1 | Last date the fund was used, if retired. |  |


### `pricing`

| Field | Type | Req | Tier | Description | Values or format |
|---|---|---|---|---|---|
| `cohort` | int | Y | 1 | Entry year. |  |
| `program_code` | text | Y | 1 | Program the price applies to. |  |
| `residency_group` | text | Y | 1 | Residency group the price applies to, if prices differ. | Resident; Nonresident; All |
| `tuition_billing_basis` | text | N | 1 | How tuition is billed. | Annual; Per credit; Per term |
| `tuition` | decimal | Y | 1 | Published annual tuition, in dollars. Full-time, first-year, as in CDS G1. |  |
| `credit_hours_per_year` | decimal | N | 1 | Credit hours billed in a standard full-time year. |  |
| `required_fees` | decimal | Y | 1 | Mandatory fees that every full-time student pays. CDS G1 definition: required fees only, not optional fees. |  |
| `food_housing_on` | decimal | Y | 1 | On-campus food and housing. CDS G1: double occupancy and 19 meals a week or the maximum plan. |  |
| `room_board_other` | decimal | N | 1 | Standard housing and food budget used in your cost of attendance. |  |
| `books_supplies` | decimal | Y | 1 | Average books and supplies. |  |
| `transportation` | decimal | Y | 1 | Transportation budget. CDS definition: two round trips home for students in institutional housing. |  |
| `other_coa` | decimal | N | 1 | Personal and other cost-of-attendance items. |  |
| `planned_increase_pct` | decimal | N | 1 | Planned tuition increase for the next entering class, if decided. | Percent |


### `aid_policy`

| Field | Type | Req | Tier | Description | Values or format |
|---|---|---|---|---|---|
| `cohort` | int | Y | 1 | Entry year the policy applies to. |  |
| `program_code` | text | Y | 1 | Program the policy applies to. |  |
| `award_mode` | text | Y | 1 | Whether the scholarship award is the whole institutional award or a supplement on top of formula awards. | Total; Supplement |
| `merit_grid` | json | Y | 1 | The grid, matrix or index that sets awards: thresholds (test, GPA, index) and award amounts, with effective dates. | JSON or an attached table |
| `grid_effective_dates` | text | Y | 2 | Effective dates for each version of the grid and any change in thresholds or amounts. |  |
| `decision_process` | text | N | 1 | Who decides awards and how: committee, matrix, discretionary, or a mix. | Free text |
| `need_grant_formula` | text | Y | 1 | How institutional need grants are computed. |  |
| `discretionary_budget` | decimal | Y | 1 | Annual discretionary aid budget, and the rules for appeals. |  |
| `appeals_reserve` | decimal | N | 1 | Amount set aside for appeals and reconsideration, if any. |  |
| `discount_rate_target` | decimal | N | 1 | Board or president target for the institutional discount rate. |  |
| `class_size_target` | int | Y | 1 | Target entering-class headcount by student type. |  |
| `capacity_type` | text | Y | 1 | Whether the class target is a hard seat cap or a soft target. | Hard cap; Soft target; Uncapped |
| `capacity_band_pct` | decimal | Y | 1 | Accepted band around the class target, as a percent (for example 3, 5 or 10). Mandatory. The price-test verdict depends on it. | Percent |
| `floors_requested` | text | N | 1 | Minimum awards or limits on change for particular groups. | Free text |
| `guardrail_max_cut_pct` | decimal | N | 1 | Largest cut any group's award may take, as a percent of tuition. | Default 5% if blank |
| `conditional_scholarships` | bool | Y | 1 | Whether any scholarship is conditional on performance. |  |
| `blind_delivery_possible` | bool | Y | 2 | Can staff deliver a test bonus as a formula line, with no test flag in the CRM or aid system? This decides whether the all-eligible analysis is primary (methodology section 4). | true; false |
| `award_visibility` | text | Y | 2 | Who sees award details and test membership. | Free text |


### `cycle_calendar`

| Field | Type | Req | Tier | Description | Values or format |
|---|---|---|---|---|---|
| `cohort` | int | Y | 1 | Entry year. |  |
| `event_type` | text | Y | 1 | What the date is. | See the event list in the document |
| `event_label` | text | Y | 1 | Batch or event label, for example the offer batch name. |  |
| `event_date` | date | Y | 1 | The date. |  |
| `deposit_amount` | decimal | Y | 1 | Deposit amount, for deposit events. |  |
| `deposit_refundable` | text | Y | 1 | Whether and until when the deposit is refundable, for deposit events. | Free text |


### `award_renewals`

| Field | Type | Req | Tier | Description | Values or format |
|---|---|---|---|---|---|
| `student_key` | text | C | 2 | Same key as students. |  |
| `award_year` | int | C | 2 | Award year (1 = first year). |  |
| `aid_year` | text | C | 2 | Aid year. |  |
| `renewed_amount` | decimal | C | 2 | Amount actually renewed for that year. |  |
| `renewal_status` | text | C | 2 | Outcome of renewal. | Renewed in full; Reduced; Eliminated; Not tested (withdrew or left) |
| `renewal_reason` | text | C | 2 | Reason for any reduction or loss. | GPA; Class rank; Credits; Withdrew; Other |


### `price_test`

| Field | Type | Req | Tier | Description | Values or format |
|---|---|---|---|---|---|
| `student_key` | text | Y | 2 | Every eligible admit appears, whether assigned to the test or not. |  |
| `in_test` | bool | Y | 2 | True if assigned to the test; false for eligible admits left out. | Needed for the all-eligible analysis |
| `assignment_date` | date | Y | 2 | Date the random assignment was made. |  |
| `stratum` | text | Y | 2 | Stratum used for blocked randomization. Need band by residency. |  |
| `arm_offset_usd` | int | Y | 2 | Bonus aid added for this student. Arms $0, $2,000 and $4,000. | Whole dollars |
| `randomization_batch` | text | Y | 2 | Batch label and the seed record, documented before outcomes were known. |  |


### `activity_log`

| Field | Type | Req | Tier | Description | Values or format |
|---|---|---|---|---|---|
| `student_key` | text | N | 2 | Same key as students. One row per recorded activity. |  |
| `activity_type` | text | N | 2 | What the activity was. | Inquiry; Visit; Event; Call; Email reply; Application started; Application submitted; Other |
| `activity_source_raw` | text | N | 2 | Raw source label for the activity (Source 1, Source 2 and so on). |  |
| `activity_date` | date | N | 2 | Date of the activity. Use to identify the first inquiry type. |  |


### `zip_key`

| Field | Type | Req | Tier | Description | Values or format |
|---|---|---|---|---|---|
| `student_key` | text | N | A | Same hashed key as the other files. |  |
| `zip5` | text | N | A | ZIP5 of the permanent address at application. Blank if unknown. Used once by the append job, then deleted within 30 days of append QA. | 5 digits; blank |
| `address_type` | text | N | A | Which address the ZIP comes from. | Permanent; Current |


## Appendix B. Cycle calendar events and code lists

| event_type | What the date is | Reference |
|---|---|---|
| `application_open` | Date applications open. | CDS C13-C14 |
| `priority_date` | Priority or early consideration deadline, if any. | CDS C14 |
| `application_deadline` | Application closing date. | CDS C14 |
| `scholarship_deadline` | Last date to be considered for scholarships, if separate. |  |
| `aid_form_priority_date` | Priority date for financial aid forms. | CDS H8 |
| `aid_form_deadline` | Deadline for financial aid forms. | CDS H8 |
| `decision_batch_release` | Each release of admission decisions or offers. One row per batch; use event_label for the batch name. | CDS C16; M section 4 |
| `aid_notification` | Date or rolling start for aid notification. | CDS H9 |
| `reply_deadline` | Date by which students must reply to the offer. | CDS C17 |
| `deposit_deadline_1` | First enrollment (seat) deposit deadline. Give amount and refund terms. | CDS C17 |
| `housing_deposit_deadline` | Housing deposit deadline. | CDS C17 |
| `census_date` | Official census date of the entry term. Same definition in every year. | M section 3 |
| `term_start` | First day of classes. |  |

Code lists for coded fields are in the Excel template (`Codes` worksheet). Send your own code lists with your data dictionary; we map them.
