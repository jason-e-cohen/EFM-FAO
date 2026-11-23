# O37: calibrating the year-to-year variation s from public data

Analysis for open issue O37 (methodology `02_methodology_v2.8.md` section 6, [v2.8, B4-1]). Report: `../../Report_O37_Shock_Calibration.md`. Analysis only: nothing here changes `sw/`, the configs, the spec, the methodology or `DECISIONS.md`.

Inputs are public: ABA 509 First Year Class compilations 2021 to 2024 and the 2025 509 extract (read only, from the 509 dashboard repo); ABA 509 compilations for 2011 to 2020 (read only, from the project's `aba509data/`, downloaded by hand Nov 23, 2026: `GPA_and_LSAT_Scores_(calendar_year)_<year>.xlsx` for 2011 to 2016 and `First_Year_Class_<year>.xlsx` for 2017 to 2020); and IPEDS admissions files downloaded from NCES. No client data; the Yellow Arrows fixture is not an input. `data/` is git-ignored (panels, downloads, crosswalk, logs); `results/` holds aggregates only and names no school.

## Run (from the project root, project environment)

```bash
.venv/bin/python -I analysis/o37_shock_calibration/build_law_panel.py
.venv/bin/python -I analysis/o37_shock_calibration/fetch_ipeds.py
.venv/bin/python -I analysis/o37_shock_calibration/build_ug_panel.py
.venv/bin/python -I analysis/o37_shock_calibration/run_calibration.py --reps-law 2000 --reps-ug 500
.venv/bin/python -I analysis/o37_shock_calibration/validate_estimators.py
.venv/bin/python -I analysis/o37_shock_calibration/sensitivity_synthetic.py --s 0.05 0.065 0.10 0.15 --seeds 101
.venv/bin/python -I analysis/o37_shock_calibration/sensitivity_synthetic.py --s 0.09 0.10 0.11 0.12 --s-base 0.045 --seeds 101 --out synthetic_sensitivity_nov23.csv
```

The full calibration takes about 20 minutes, most of it the undergraduate bootstrap. The Nov 23 rerun used `run_calibration.py --reps-law 2000 --law-only` (about 4 minutes), which reruns the law configurations and carries the undergraduate rows over from the existing `results/` files (the IPEDS panel did not change). The bootstrap seed is fixed (37). The Nov 21 results (2021 to 2025 only) are kept in `results/v1_2021_2025_nov21/`; the 2021-2025 window of the rerun reproduces them exactly.

## Files

| File | What |
|---|---|
| `build_law_panel.py` | Reads `First_Year_Class_<year>.xlsx` (2017 to 2024, three column schemas), `GPA_and_LSAT_Scores_(calendar_year)_<year>.xlsx` (2011 to 2016; stops if `Reporting Year` differs from the file year) and `aba509_all_schools_2025.csv`. Pre-2017 "matriculants" are the whole first-year class, so the main count scales them to pool enrollees by the school's 2017-2020 "other" share; `enrollees_matric_raw` and `enrollees_total` keep the alternatives. Closed, merged and split schools get ids 9001 and up (`MANUAL`, `SPLIT_BEFORE`); rebuilds the name-to-`aba_school_id` match locally (the 509 repo's crosswalk is in Supabase, which is not touched): the repo's `normalize()` rules, exact match, token coverage, the review file's resolutions, then a manual table. Writes `data/law_panel.csv`, `data/law_crosswalk.csv` (every match and its method) and `data/law_jumps.csv` (size jumps to check). Uses the ABA-implied 2025 enrollee count where the scraped count disagrees (45 schools; see the report) |
| `fetch_ipeds.py` | Downloads `ADM2014` to `ADM2024` and `HD` files from NCES into `data/ipeds_raw/<file>/`. `ADM2024` (fall 2024) was not published when this ran (HTTP 404) |
| `build_ug_panel.py` | Four-year public and private nonprofit degree-granting institutions, values reported by the institution (IPEDS flag R). Writes `data/ug_panel.csv` |
| `estimators.py` | Estimators (a), (b), (c), persistence, one-year-ahead forecast errors (k-cohort means, five-year trend line, and with the admit-rate control), lag autocovariances splitting trend, independent and random-walk parts (`persistence_lags`), per-year table (`by_target_year`), multiplicative check, school-resampling bootstrap. `flag_implausible(local=5)` is the long-panel outlier rule (median of the five nearest years) |
| `run_calibration.py` | All configurations: law 2011-2025, 2011-2020, 2021-2025, five-year windows, definition-consistent windows, peer band by window, size bands, control, sensitivities (definition break, closures, outlier rule, 2025 counts). Outlier rules are applied within each window. Writes `results/estimates.csv`, `multiplicative.csv`, `exclusions.csv`, `summary.json`, `law_by_year.csv` |
| `validate_estimators.py` | Simulated panels: the Nov 21 five-year worlds (`results/validation.csv`) and 15-year worlds with trends, random walks and partial reversion (`results/validation_15yr.csv`) |
| `sensitivity_synthetic.py` | Headline probabilities at several s on the synthetic config and scenarios, using the prototype's code read only; writes `results/synthetic_sensitivity.csv`, or `--out`. `--s-base` treats each s as s_year and runs at √(s_year² + s_base²) |

## The 2011 to 2020 compilations (added Nov 23, 2026)

Downloaded by hand from the ABA required-disclosures site into `aba509data/` at the project root and read from there (read only). 2014 is present. The builder checks the year column, prints any compilation year missing from 2011 to 2024, and writes `data/law_unmatched.csv` if a name is not matched; extend `MANUAL` (or `SPLIT_BEFORE` for a school whose earlier rows belong to a predecessor) and rerun. A further year dropped into `data/aba_extra/` is read too. Findings: report section R.
