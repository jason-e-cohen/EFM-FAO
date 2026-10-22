# [Institution] Enrollment Funnel and Financial Aid Data Request (v2.1)

**Prepared for:** [Institution] Enrollment Management and Financial Aid
**Prepared by:** [Our team and contact]
**Date:** [Date]  **Response requested by:** [Date]

## Why we are asking for more than a typical funnel study

Two questions drive this engagement. First, where do prospective students leave the funnel? Second, what award policy should guide the next discretionary aid dollar? The second question depends on knowing what each student was offered **and when**, so this request asks for aid in components with dates, not totals. It also asks for the rules behind your awards, which let us learn price sensitivity without guesswork.

To keep the start-up effort proportional to what you need, the request comes in two tiers.

| Tier | What you send | What it supports |
|------|---------------|------------------|
| **Tier 1 (minimum)** | Three entering cohorts, final aid packages by component, offer dates where you have them, the merit grid | Funnel analysis, yield forecast, in-cycle pacing and melt monitoring, loan-cap exposure, and a first estimate of price sensitivity from the merit grid (with a wider range) |
| **Tier 2 (full)** | Four to five cohorts, every package version with its date, merit grid with effective dates, and a price test | Everything in Tier 1, plus a recommended scholarship policy grid with budget scenarios |

You can start at Tier 1 and move to Tier 2 in a later cycle.

## What we need

Aid offers are needed for **every** cohort you send, not only the most recent. A data dictionary is welcome but not required; we provide ours (`data_dictionary_v2.csv`) and will map your fields to it with you.

| File | One row per | Key fields | Tier |
|------|-------------|------------|------|
| `students` | Person and entry term | Entry year and term, student type, level (undergraduate, graduate, professional), program, residency, ZIP5, first-touch source and date, inquiry, application, decision, deposit, and census dates, decision type (early, regular, rolling), campus visit, engagement counts, GPA, test scores (SAT/ACT, or GRE, GMAT, LSAT for graduate programs; blank if not submitted), first-generation status, race and ethnicity, athlete flag, excluded-group flag (see below), housing application status and date | 1 |
| `fafsa` | Person and aid year | Received date, need index value and type (EFC or SAI), dependency, verification selected and completed dates; CSS Profile institutional-methodology need, if you use it | 1 |
| `aid_offers` | Person, fund, and package version | Fund code, component, offered amount and date, accepted amount, disbursed amount, and for PLUS loans whether the student or parent applied and was approved or denied | 1 (final package); 2 (every version) |
| `pricing` | Entry year | Tuition, fees, room and board by residency and program | 1 |
| `aid_policy` | Entry year | Merit grid with thresholds and effective dates, need-grant formula, discretionary budget, discount and class-size targets | 1 (grid); 2 (with effective dates) |
| `price_test` (if run) | Person | Assignment date, stratum, bonus amount, randomization batch | 2 |

**Excluded groups:** please flag students whose aid follows rules outside the normal process, such as athletes, tuition waivers and exchanges, employee dependents, and named special scholarships. They keep their current packages in every scenario and are reported separately so your class totals still reconcile.

## Definitions we need to agree on

1. **Enrolled** means enrolled at the official census date of the entry term. Please use one definition for all years.
2. **Offered amount** is what the student was told, on the offer date. For Tier 2, please keep every package version, not only the final one.
3. **Decision date** is the student's deposit deadline or the date the student deposited, whichever is earlier. Awards that arrive later (for example, external scholarships reported after enrollment) must carry their true dates so we can keep them out of the price analysis.
4. **Missing** is never zero. Please leave unknown values blank. If aid data does not exist for a cohort, tell us instead of sending zeros.
5. **Need index:** send EFC for aid years through 2023-24 and SAI for 2024-25 onward, with a column saying which. Keep negative SAI values.
6. **Stealth applicants:** flag people whose first recorded contact is the application.
7. **Test scores:** leave blank if not submitted. Do not impute or convert.
8. **Source labels:** send your raw source strings. We apply a versioned mapping (`source_taxonomy.csv`) and will return a list of anything unmapped for your review.

## Aid components

| Component | Gift or self-help |
|-----------|-------------------|
| Institutional merit | Gift |
| Institutional need | Gift |
| Institutional athletic | Gift |
| Institutional discretionary (including appeals) | Gift |
| Other institutional | Gift |
| State grant | Gift |
| Pell Grant | Gift |
| SEOG | Gift |
| External scholarship | Gift |
| Subsidized loan | Self-help |
| Unsubsidized loan | Self-help |
| Parent PLUS | Self-help |
| Grad PLUS (cohorts before July 1, 2026, and grandfathered borrowers) | Self-help |
| Private or institutional loan | Self-help |
| Work-study | Self-help |

Please also send your fund-code crosswalk so we can map your codes to these components.

**Why loans matter now:** Grad PLUS closed to new borrowers on July 1, 2026, and new annual and lifetime caps apply to graduate, professional, and Parent PLUS borrowing. Prior-year PLUS amounts, approvals, and denials let us show how many of your admits, by program, now face a financing gap and what that could mean for enrollment and revenue. Loans are never treated as a price reduction in our models.

## Your award rules

The merit grid is the single most valuable document for this study. Awards that change at fixed GPA or test thresholds let us estimate price sensitivity without bias. Please send:

- The grid for each cohort, with exact thresholds and effective dates.
- How need-based institutional grants are calculated.
- How discretionary awards and appeals are decided, and who decides.
- The discretionary budget and the targets for discount rate and class size.
- Any limits you want on change: for example, the largest cut any group's award may take, or minimum awards for particular groups.

## Recommended for Tier 2: a price test

A short randomized test of **bonus aid** for part of the incoming class makes the policy recommendation far more trustworthy.

- **Design:** a random 40% of eligible admits (first-time students, not in an excluded group) receive an additional $0, $2,000, or $4,000 in discretionary aid, in a 40% / 20% / 40% split. Assignment is balanced within need band and residency.
- **Why these amounts:** concentrating bonuses at the ends gives a more precise answer than spreading them evenly, at the same average cost per student.
- **Positive only:** nobody receives less than they otherwise would.
- **Keep the test clean:** please do not adjust other discretionary aid for students because of their test assignment. We check for this and report it.
- **Approvals:** needs sign-off from [financial aid director] and [enrollment VP]. We will draft the protocol and the randomization file.
- **Timing:** assignment is made before decisions; we record the assignment date and seed.
- **Power:** at your size, expect several cycles to reach a precise estimate. We will report the smallest effect the test can detect before it starts.

## Optional additions

- **In-cycle export:** a weekly or biweekly extract of the `students` and `aid_offers` files during yield season (January to census) powers pacing against last year and melt monitoring. We will give you a saved query or export spec. Please include the date and reason for any award revision.
- **Where admitted students went:** a National Student Clearinghouse StudentTracker match for admits who did not enroll, ordered by your office. We join it to public net-price data to show which institutions you lose students to, and at what cost difference.
- **Admitted-student survey:** a short survey of enrolling and non-enrolling admits on competing offers and reasons for their choice, designed and fielded by [our team] with your approval.
- **Peer set:** a list of 8 to 15 institutions you consider peers, for sticker and net-price comparison from public data.
- **Neighborhood context:** if you want neighborhood indicators (for example, educational attainment or median income by Census tract), we supply a script your office runs **before** removing addresses. Only the resulting indicators are sent to us.

We do not request or use consumer credit data of any kind.

## How to send data safely

- **No** names, emails, phone numbers, street addresses, full dates of birth, Social Security numbers, full ZIP codes, or free-text notes.
- Replace your student ID with a **hashed key**. Use a salted hash and keep the salt; we never need it. Use the same key in every file and every in-cycle export.
- Send **ZIP3** (first three digits) and state, not full ZIP.
- Dates are welcome (they are converted to days before term start and then discarded).
- Transfer through [secure file transfer]. We delete raw files at engagement close per [retention policy].

## What we do with the data

- We check structure and logic: duplicate keys, stage order, aid for non-admitted students, offsets outside the protocol. Every check and its row count is reported back to you.
- Student-level data stay in our secure compute environment. The dashboard shows aggregates only, with groups smaller than ten suppressed. If you request a student-level list (for example, students at risk of melt), it comes back to you through your secure channel, not the dashboard.
- Race, ethnicity, and gender are used to audit results for fairness, never to decide awards.
- Recommendations are delivered as a scholarship policy (award levels by academic, need, and residency group) that your staff can apply as offers go out.
- No recommendation is published until you and [institution counsel] have reviewed it.

## Timeline

| Step | When |
|------|------|
| Kickoff and definitions call | [Date] |
| Data delivered | [Date] |
| Data quality report back to you | [Date + 1 week] |
| Funnel analysis delivered | [Date + 6 weeks] |
| Aid policy recommendation delivered (Tier 2) | [Date + 10 weeks] |
| In-cycle monitoring begins | [First admit release] |

## Checklist for your team

- [ ] Tier chosen (1 or 2)
- [ ] Three cohorts (Tier 1) or four to five cohorts (Tier 2), with aid for every cohort
- [ ] Offer dates (Tier 1 where available; Tier 2 every package version)
- [ ] Merit grid and need-grant formula
- [ ] Fund-code crosswalk, including PLUS and private loans
- [ ] PLUS approval and denial history
- [ ] Excluded-group flags
- [ ] Source labels as recorded, not recoded
- [ ] Single enrolled-at-census definition
- [ ] Hashed keys, ZIP3 only, no direct identifiers
- [ ] Price test approval (Tier 2)
- [ ] Optional: in-cycle export, Clearinghouse match, survey, peer set
