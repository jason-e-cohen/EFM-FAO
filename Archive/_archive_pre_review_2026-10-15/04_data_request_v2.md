# [Institution] Enrollment Funnel and Financial Aid Data Request (v2)

**Prepared for:** [Institution] Enrollment Management and Financial Aid
**Prepared by:** [Our team and contact]
**Date:** [Date]  **Response requested by:** [Date]

## Why we are asking for more than a typical funnel study

Two questions drive this engagement. First, where do prospective students leave the funnel? Second, where should the next discretionary aid dollar go? The second question depends on knowing what each student was offered **and when**, so this request asks for aid in components with dates, not totals. It also asks for the rules behind your awards, which let us learn price sensitivity without guesswork.

## What we need

Five years of entering cohorts (minimum four) with complete aid offers for **every** cohort, not only the most recent. A data dictionary is welcome but not required; we provide ours (`data_dictionary_v2.csv`) and will map your fields to it with you.

| File | One row per | Key fields |
|------|-------------|------------|
| `students` | Person and entry term | Entry year and term, student type, residency, ZIP3, first-touch source and date, inquiry, application, decision, deposit, and census dates, engagement counts, program, GPA, test scores (blank if not submitted), first-generation status, race and ethnicity, athlete flag |
| `fafsa` | Person and aid year | Received date, need index value and type (EFC or SAI), dependency, verification |
| `aid_offers` | Person, fund, and package version | Fund code, component, offered amount and date, accepted amount, disbursed amount |
| `pricing` | Entry year | Tuition, fees, room and board by residency |
| `aid_policy` | Entry year | Merit grid with thresholds and effective dates, need-grant formula, discretionary budget, discount and class-size targets |
| `price_test` (if run) | Person | Assignment date, bonus amount, randomization batch |

## Definitions we need to agree on

1. **Enrolled** means enrolled at the official census date of the entry term. Please use one definition for all years.
2. **Offered amount** is what the student was told, on the offer date. Please keep every package version, not only the final one.
3. **Known at the decision date** means communicated before the student's decision or deposit deadline. Awards that arrive later (for example, external scholarships reported after enrollment) must carry their true dates.
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
| Work-study | Self-help |

Please also send your fund-code crosswalk so we can map your codes to these components.

## Your award rules

The merit grid is the single most valuable document for this study. Awards that change at fixed GPA or test thresholds let us estimate price sensitivity without bias. Please send:

- The grid for each cohort, with exact thresholds and effective dates.
- How need-based institutional grants are calculated.
- How discretionary awards and appeals are decided, and who decides.
- The discretionary budget and the targets for discount rate and class size.

## Optional but strongly recommended: a price test

A short randomized test of **bonus aid** for part of the incoming class makes the optimization far more trustworthy.

- **Design:** a random 40% of eligible admits (first-time freshmen, not athletes) receive an additional $0, $1,000, $2,000, $3,000, or $4,000 in discretionary aid, assigned at random.
- **Positive only:** nobody receives less than they otherwise would.
- **Approvals:** needs sign-off from [financial aid director] and [enrollment VP]. We will draft the protocol and the randomization file.
- **Timing:** assignment is made before decisions; we record the assignment date and seed.
- **Power:** at your size, expect several cycles to reach a precise estimate. We will report the smallest effect the test can detect before it starts.

## How to send data safely

- **No** names, emails, phone numbers, street addresses, full dates of birth, Social Security numbers, full ZIP codes, or free-text notes.
- Replace your student ID with a **hashed key**. Use a salted hash and keep the salt; we never need it.
- Send **ZIP3** (first three digits) and state, not full ZIP.
- Dates are welcome (they are converted to days before term start and then discarded).
- Transfer through [secure file transfer]. We delete raw files at engagement close per [retention policy].

## What we do with the data

- We check structure and logic: duplicate keys, stage order, aid for non-admitted students, offsets outside the protocol. Every check and its row count is reported back to you.
- Student-level data stay in our secure compute environment. The dashboard shows aggregates only, with groups smaller than ten suppressed.
- Race, ethnicity, and gender are used to audit results for fairness, never to decide awards.
- No recommendation is published until you and [institution counsel] have reviewed it.

## Timeline

| Step | When |
|------|------|
| Kickoff and definitions call | [Date] |
| Data delivered | [Date] |
| Data quality report back to you | [Date + 1 week] |
| Funnel analysis delivered | [Date + 6 weeks] |
| Aid optimization delivered | [Date + 10 weeks] |

## Checklist for your team

- [ ] Five cohorts (minimum four) with aid for every cohort
- [ ] Offer dates and package versions
- [ ] Merit grid and need-grant formula
- [ ] Fund-code crosswalk
- [ ] Source labels as recorded, not recoded
- [ ] Single enrolled-at-census definition
- [ ] Hashed keys, ZIP3 only, no direct identifiers
- [ ] Price test approval (if participating)
