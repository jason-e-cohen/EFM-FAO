# Data request v3: sources, gap log and judgment calls

Prepared October 22, 2026. Inputs: `../04_data_request_v2.md` (v2.1 text, "04"), the reference request (`Enrollment Funnel and Student Financial Data Request.docx`, "REF"), `CDS-PDF-2025-2026-Excel_Template.xlsx` ("CDS"), `02_methodology_v2.6.md` ("M"), `Verification_Report_Oct22.md` section 5, and `config/data_dictionary_v2.csv`. Shown versus suspected is marked where it matters.

## 1. What the reference request adds to 04

The reference is a short funnel and student-aid list written for an institution it names as SBCC. It has no offer dates, package versions, award rules, definitions, privacy terms or price-test material, so 04 stays the base. It adds the following. All are now in v3.

| # | In REF | In 04? | v3 treatment |
|---|---|---|---|
| 1 | Source and date for each activity ("Source 1, Source 2 ... date of each activity to identify the first inquiry type") | Partly: first touch only | New optional file `activity_log` (Tier 2): type, raw source, date. `first_touch_*` stays in `students` |
| 2 | Intended or actual enrollment term and year | Intended only | `actual_entry_cohort`, `actual_entry_term` (blank if same). Also answers CDS C18 deferral |
| 3 | Student level | Mentioned in the table text, no dictionary field | `student_level` (undergraduate, graduate, professional) |
| 4 | Age, or date of birth | No age field; full DOB prohibited | `age_at_application` in whole years. DOB stays prohibited (judgment call J2) |
| 5 | Applied for FAFSA | Only the received date | `fafsa_applied` |
| 6 | FAFSA verification status | Selected flag only in the dictionary | `verification_selected`, `verification_completed_date` |
| 7 | Income or EFC | EFC and SAI only | `income_band` (optional, banded; judgment call J3) |
| 8 | Veteran or active military | Dictionary N, not in the table | Kept N for both programs, now named in the file table |
| 9 | Gender | Dictionary N | Raised to Y, audit only (J4) |
| 10 | Client supplies a data dictionary that defines each variable and each possible value | "Welcome, not required" | Now requested in section 3; the template gives code lists and we return unmapped values |
| 11 | "Sample Excel file with data structure available upon request" | Not offered | The Excel template ships with the request |
| 12 | Five most recent years "or more" | Three minimum, four to five for Tier 2 | Tiers kept; longer history invited, especially across policy changes (J1) |

Already covered by 04 and unchanged: unique key (hashed), application date, admission and enrollment status, intended major, transfer status, athletic participation, residency, race and ethnicity, first-generation status, HS GPA, SAT and ACT, transfer GPA, aid by type and source (federal grants, Pell, loans, institutional, private, work-study).

## 2. What the Common Data Set adds

The CDS is undergraduate and aggregate. It gives vocabulary and reconciliation targets, not fields for unit records.

| Use | What changed in v3 |
|---|---|
| Definitions (CDS definitions sheet) | `definitions.csv` follows CDS wording for applicant, admitted, first-time first-year, transfer, full-time, residency, early decision and action, waiting list, deferral, need-based and non-need-based aid, institutional and external scholarships, tuition waivers, work study, financial aid applicant, cost of attendance |
| C1, C2 applications and waiting list | `admit_decision` gains "Waitlisted not admitted"; `waitlist_placed_date`, `waitlist_admit_date` (law, Tier 1); residency is now by known physical address at application (C1), with billing residency in `tuition_residency` |
| C10 to C12 | `hs_class_rank_pct` (optional) |
| C13 to C20 calendar and policies | New file `cycle_calendar`: deadlines, offer batches, aid dates, reply date, deposit amount and refund terms, census date. This also supplies the "decision date" and "wave" inputs the method needs |
| C21 to C22 | `plan_type` (early decision, early action, restrictive early action, regular, rolling) |
| G1 costs | `pricing` split into tuition, required fees, food and housing, books, transportation (CDS wording) |
| H definitions, H (FM or IM) | `fund_crosswalk.need_basis` classifies by the fund's own rule; `need_methodology` (federal, institutional, both) |
| Reconciliation | `Institutional_Reference` worksheet: C1, C2, C9 to C12, C21 to C22, B1, G1, H1, H2, H2A, H4 to H5 by cohort year, for QA reconciliation |

Where v3 departs from the CDS on purpose: (a) CDS counts non-need aid used to meet need as need-based (its precedence list); v3 classifies by the fund rule and reconciles the difference, because the price model needs the fund's real eligibility rule. (b) CDS reports first-time full-time students in aggregate; v3 needs every applicant and admit as unit records. (c) CDS residency is address-based; billing residency is separate.

Law has no CDS equivalent. The law reference set is the ABA Standard 509 report (M section 2, Appendix D). The audit read the ABA report form but not the ABA's definitions document, so v3 law definitions defer to "as defined in your ABA 509 report" and do not restate ABA wording.

## 3. Spec gaps closed (from `Verification_Report_Oct22.md` section 5)

| Gap | Where it is in v3 |
|---|---|
| 1 LSAT, UGPA, position | `students`: `test_type`, `lsat_score`, `lsat_score_basis`, `ugpa`, `ugpa_source`, `gre_*`, `jdnext_score`. Position bands are computed by us from the prior three classes' rows, so no position field is requested |
| 2 Offer dates, versions, mode, stipends | `aid_offers.offer_date`, `package_version`, `stipend_flag`; `students.offer_release_batch`; `aid_policy.award_mode` |
| 3 Revision reason codes | `aid_offers.revision_reason_code` (Tier 2, both programs), `revision_requested_date` |
| 4 Renewal rule | `aid_offers.renewal_rule`, `renewal_conditions`, `commitment_years`; `award_renewals` file; `pricing.planned_increase_pct` |
| 5 Capacity band (mandatory, E7) | `aid_policy.capacity_type`, `capacity_band_pct`; section 7 of the document |
| 6 Blinding | `aid_policy.blind_delivery_possible`, `award_visibility`; price-test section |
| Law price-test arms | Law section 8: D is 10% to 15% of tuition, strata position band by wave |
| Law-specific fields | Program, full-time or part-time, deferral, commitment length, own ABA 509 history |
| Peer set size | Law 5 to 10 (509 procedure); undergraduate 8 to 15 |
| Tier 1 promise of a merit-grid estimate | Law Tier 1 now states that a price estimate needs a usable threshold or policy change |
| Deliverable wording and timeline | Law: position band by market; timeline restated against the screen verdict (week offsets proposed, marked "to confirm") |

Other changes versus 04:
- **Credit-data sentence removed.** 04 said "We do not request or use consumer credit data of any kind." M section 9 (narrowed) and Appendix E.3 say not to repeat it in the data request or the pitch.
- **ZIP wording replaced** per E.3: ZIP3 and state in `students`; ZIP5 only in the optional `zip_key`; purpose, 30-day deletion, no household data, no race use, match report returned. The 04 phrase "No full ZIP codes" is gone.
- **Price test is conditional.** 04 called it "Recommended for Tier 2". v3 says it is proposed only where the value-of-information screen recommends it, and adds a scoping-inputs section (M section 4, E7). This matches the audit and the updated pitch promises (pitch copy not checked; see section 6).
- **Renewal fields apply to undergraduate too** (J6).
- **Grad PLUS paragraph** kept from 04; law drops Parent PLUS and subsidized loans (not applicable to JD students under the cited summaries; unverified).

## 4. New files and fields for S2 and the loader

The v3 request has 11 files plus two worksheets; 153 fields apply to each program (13 law-only, 13 undergraduate-only). New against `data_dictionary_v2.csv`: files `fund_crosswalk`, `cycle_calendar`, `award_renewals`, `activity_log`; fields listed in `GAP_LOG` sections 1 to 3. `sql/schema.sql` holds aggregates only (no student-level table), so Supabase is unaffected. S2 (data contract) and the pipeline loader must absorb the new fields before a build; the synthetic generator emits the v2 fields only.

## 5. Judgment calls

| # | Call | What would change it |
|---|---|---|
| J1 | Keep three cohorts as the minimum and five as ideal; invite more | An S2 power result showing three cohorts cannot support the forecast: raise the minimum |
| J2 | Age in years, never DOB (REF asked for either) | You accepting DOB under the data-use agreement |
| J3 | `income_band` optional and banded, not exact income | A law client that packages on income with no SAI or EFC |
| J4 | `gender` raised to Y for the fairness audit (REF lists it) | A client unable to supply it; it stays audit only |
| J5 | Law prospect fields (`first_touch_*`, `inquiry_date`) conditional: many law schools record no prospects | A client with CRS or event data: ask for it in full |
| J6 | Renewal rule, conditions and `award_renewals` requested for undergraduate as well (M section 3 is not law-only) | Undergraduate clients with no conditional awards: the file stays "if conditional" |
| J7 | One YAML and CSV spec with program tags, two generated documents, instead of two hand-written documents | A program that diverges beyond what tags can express |
| J8 | Home is `efa_fao/docs/data_request_v3/`, with 04 untouched until S2 signs off | You wanting v3 to replace 04 now |
| J9 | Python generator with python-docx and openpyxl; the project environment may need both installed | Node `docx-js` if you prefer the skill's toolchain |
| J10 | National Student Clearinghouse match kept for law as optional with "coverage to be confirmed" | Confirming coverage with the Clearinghouse |

## 6. Not verified and open for Jason

- **No counsel review** of the privacy, ZIP5 add-on or data-use language. Placeholders for the data-use agreement are in the text.
- **Word rendering** was checked in LibreOffice only (fonts substituted). Excel list validations are warning-style and were not opened in Excel.
- **CDS item numbers** for H4 to H5 and the other codes come from the 2025-26 template; confirm against the client's own CDS.
- **Law timeline offsets** (+6 and +8 weeks) are proposed, not from the plan; S1 should confirm.
- **Grad PLUS and loan-limit statements** repeat 04 and M section 8 (public summaries). Confirm against Federal Student Aid before sending.
- **Pitch deck copy** was not checked against v3 (the folder copy appeared stale earlier). Its privacy paragraph and Tier 1 promise need the same changes.
- **The undergraduate document is a template** with an `[Institution]` placeholder, generated from the spec and checked for law-term leakage only. It has not been run against a real undergraduate client.
- **Richmond call answers** are not in the capture sheet yet. Field requirements for Richmond (conditional scholarships, need use, offer batches, hard or soft cap) should be tuned once they are.
- **Tier flag on `package_version`** is 2 because Tier 1 only needs the final package; the field is still present at Tier 1 with version 1.
- The reference request names another institution (SBCC). v3 reuses its field ideas, not its text.

## 7. V27A-07 early-delivery additions (Session A, November 16, 2026)

Added for the law request only (the undergraduate document and dictionary are unchanged apart from the small-cell sentence in section "What we do with the data"). Three aggregate files, `early_funnel_by_state`, `early_pacing` and `early_planning_path` (spec `files.csv` order 12 to 14, 19 rows in `fields.csv`), a paragraph and three bullets in section 3 (after the file list), and one checklist line. Source: `Prototype_Spec_Scenario_Workbook_v0.5.md` section 15 item 10, `CHANGELOG_v2.7.md` V27A-07, and the Session A brief. Nothing was sent to the client.

Judgment calls:

| # | Call | What would change it |
|---|---|---|
| J11 | Counts are applications, admits and deposits, and pacing is against the prior two cycles. **Confirmed by Jason, Nov 16.** Spec section 15 item 10 was aligned to this; the Nov 13 draft email still says "enrolled" and "last year" and needs the same change | None |
| J12 | Field `tier` is "1" so the file passes the tier test; the files table shows "Early delivery (aggregates)". Tier "A" would label the files optional, which they are not | A separate tier label for early delivery |
| J13 | Text uses `{institution}` and generic wording (every state as its own row; target-state grouping agreed with the client), not New York and Pennsylvania, so the law spec stays reusable and carries no client-specific target states | Using the spec for Richmond only |
| J14 | `week_of_cycle` counts from the application open date for each cohort (week 1 is the first seven days), so "same week" is the same point in each cycle | Client's own weekly reporting calendar |
| J15 | Small counts are requested as they are (no suppression or rounding). This is inbound data and does not change the output rule in methodology section 9 | Counsel review |

Found while rebuilding and fixed on Jason's approval (November 16): the law-only paragraph "What you receive depends on the evidence your history contains..." in `request_spec.yaml` section "why" is written as `p: {only: law, text: ...}`, which `blocks_to_ir` resolves to no text, so it appears in no output, and the sentence "We do not recommend a change in price level without design-based evidence" is missing from the law document. Fixed by writing it as `p: {law: "..."}`; the sentence now appears in the law document and not in the undergraduate one.

Small-cell wording (section "What we do with the data") now reads: default suppression under ten with complementary suppression; a client may elect to show small groups to named, authenticated staff, recorded in the statement of work. It follows methodology section 9 and FR-76; the sign-off record (O40) is not yet written, so the text does not say that any client has elected.

Tests: `test_spec.py` has 8 tests; all pass (run through a plain Python loop because `pytest` is not installed in the environment used). Law and undergraduate outputs regenerated.

## 8. Session B reconciliation (November 16, 2026)

Applied on Jason's acceptance of `Audit_Session_B_Design_Report.md`:
- **B2-11:** `aid_policy.guardrail_max_cut_pct` (the removed 5% guardrail) replaced by `client_max_cut_pct`: any limit the client's own policy sets, reported against, never imposed.
- **B3-4:** `early_funnel_by_state.deposits` is labeled net of withdrawals by census; `early_pacing.deposits_cumulative` is labeled gross; `early_pacing.applications_cumulative` counts complete applications (the Applicant definition); `early_pacing.lsat_band` added (conditional) so growth in high-LSAT applications can be computed at the same week of the cycle.
- Law and undergraduate outputs regenerated; `test_spec.py` 8 of 8 pass (plain Python loop).

## 9. Spec v0.6.3 additions (November 18, 2026)

- **R3-4:** `early_funnel_by_state.lsat_band` now asks for bands by each applicant's highest LSAT (the ABA 509 basis), because the History-sheet 509 check found the scenario workbook's lower bands disagree with Richmond's 509 percentiles.
- **BM-4:** `early_planning_path.continuing_ntr_usd` (conditional): continuing-student net tuition for the plan year, for a revenue goal stated for the whole JD body.
- **BM-1:** `early_planning_path.lsat_p25_target` and `lsat_p10_target` (conditional): the scores the school tracks at those percentiles.
- Outputs regenerated; `test_spec.py` passes (plain Python loop).
