# v2.4 Change Log

**Base:** the v2.3 documents. Methodology additions are tagged **[v2.4]**. The data request, pitch deck, and pitch slides are unchanged and remain at v2.3.

## What changed

| Change | Where |
|--------|-------|
| **ABA 509 reference layer** for law schools: peer pricing, market award gap by rank-matching (descriptive and a candidate moderator only), conditional scholarships as a candidate mechanism, a yield prior, and public parameters for a law synthetic world. Limits stated: school-level, one-year lag, ecological, never the price anchor | Methodology section 2; roadmap (new module, output, table, view note); executive read |
| **Horizon follows program length** (three years for a full-time JD) | Methodology section 5; roadmap |
| **Conditional-award persistence:** expected renewed award enters multi-year revenue; 509 loss rates as a stated prior | Methodology section 5; open issue O17 |
| **Timing and sensitivity by date:** wave-stratified randomization within the client's own test, two or three waves at most, negotiation revisions treated as endogenous | Methodology section 4; open issue O18 |
| **Forecast model rule:** regularized logit by default; boosted-tree challenger for scoring only, behind a reviewer-set margin | Methodology sections 7 and 11; open issue O19 |
| Law synthetic world calibrated to public 509 data (resolves the "public provenance" requirement for the law vertical) | Roadmap S2 and S9 |
| Open issues O16 to O19 | Methodology section 13 |
| Opus instructions: Phase 1 item 8; Phase 3 items 11 to 13 (509 layer, timing by date, boosted-model challenger) | Opus instructions |

## Closed decision

**Applicant-reported timing data from a third-party site: not used.** Considered a weekly collection of response-timing data from an applicant-reported law admissions site, to track timing by date. Decided against. The site's license excludes institutional and commercial use and prohibits scraping or bulk collection without written permission. The data are self-reported, skew toward engaged applicants, and are coarse (the share of applicants who heard back, by application period). They measure how fast schools respond, not how applicants respond to price, and they do not link to a client's students. Timing sensitivity is learned from the client's own offer waves, and public applicant-volume reports describe market pace. Revisit only if the owner offers a license on terms that fit.

Recorded in methodology section 14, the roadmap decision log, and the executive read. It is not an open issue, and the Opus instructions tell the reviewer not to revisit it.

## Files in this version

`02_methodology_v2.4.md`, `01_executive_read_v2.4.md`, `03_technical_roadmap_v2.4.md`, `Opus_S4_S5_Rereview_Instructions_v2.4.md`, `CHANGELOG_v2.4.md`. Unchanged from v2.3: `04_data_request_v2.3.md`, `EFA_FAO_Pitch_Deck_v2.3.md`, `EFA_FAO_Pitch_Slides_v2.3.html`.

## Still flagged, your call

1. **Pitch timing:** do not imply a price test's results arrive within a 4 to 6 week Phase 2.
2. **Executive read, "Competitive position":** characterizes a competitor from its deck; keep it internal.
3. **Functional requirements:** the FR table was dropped in v2.1; decide whether to restore it in S1.
4. **Sample-size assumptions** (21% yield, 0.85 adjustment, 1 to 3 point plausible effect) need confirming in S4; the screen rule goes to the reviewer.
5. **Phase 2 slide wording** implies segment-level sensitivity; the method uses one slope.
6. **File names:** archive the v2.3 files you replace.
