# O37: calibrating the year-to-year variation s from public data

Analysis for open issue O37 (methodology `02_methodology_v2.8.md` section 6, [v2.8, B4-1]). Report: `../../Report_O37_Shock_Calibration.md`. Analysis only: nothing here changes `sw/`, the configs, the spec, the methodology or `DECISIONS.md`.

Inputs are public: ABA 509 First Year Class compilations and the 2025 509 extract (read only, from the 509 dashboard repo), and IPEDS admissions files downloaded from NCES. No client data; the Yellow Arrows fixture is not an input. `data/` is git-ignored (panels, downloads, crosswalk, logs); `results/` holds aggregates only and names no school.

## Run (from the project root, project environment)

```bash
.venv/bin/python -I analysis/o37_shock_calibration/build_law_panel.py
.venv/bin/python -I analysis/o37_shock_calibration/fetch_ipeds.py
.venv/bin/python -I analysis/o37_shock_calibration/build_ug_panel.py
.venv/bin/python -I analysis/o37_shock_calibration/run_calibration.py --reps-law 2000 --reps-ug 500
.venv/bin/python -I analysis/o37_shock_calibration/sensitivity_synthetic.py --s 0.05 0.065 0.10 0.15 --seeds 101
```

The calibration takes about 15 minutes, nearly all of it the undergraduate bootstrap. The bootstrap seed is fixed (37).

## Files

| File | What |
|---|---|
| `build_law_panel.py` | Reads `First_Year_Class_<year>.xlsx` (2021 to 2024, both column schemas) and `aba509_all_schools_2025.csv`; rebuilds the name-to-`aba_school_id` match locally (the 509 repo's crosswalk is in Supabase, which is not touched): the repo's `normalize()` rules, exact match, token coverage, the review file's resolutions, then a manual table. Writes `data/law_panel.csv`, `data/law_crosswalk.csv` (every match and its method) and `data/law_jumps.csv` (size jumps to check). Uses the ABA-implied 2025 enrollee count where the scraped count disagrees (45 schools; see the report) |
| `fetch_ipeds.py` | Downloads `ADM2014` to `ADM2024` and `HD` files from NCES into `data/ipeds_raw/<file>/`. `ADM2024` (fall 2024) was not published when this ran (HTTP 404) |
| `build_ug_panel.py` | Four-year public and private nonprofit degree-granting institutions, values reported by the institution (IPEDS flag R). Writes `data/ug_panel.csv` |
| `estimators.py` | Estimators (a), (b), (c), persistence, one-year-ahead forecast errors, multiplicative check, school-resampling bootstrap |
| `run_calibration.py` | All configurations (main, size bands, year windows, control, sensitivities); writes `results/estimates.csv`, `multiplicative.csv`, `exclusions.csv`, `summary.json` |
| `sensitivity_synthetic.py` | Headline probabilities at several s on the synthetic config and scenarios, using the prototype's code read only; writes `results/synthetic_sensitivity.csv` |

## Adding the 2011 to 2020 compilations

The ABA disclosure site lists First Year Class compilations back to 2011, but downloading them goes through the site's backend, which this session could not call. To add them, download "Compilation: All Schools Data", section First Year Class, for each year from the ABA required-disclosures site by hand, save as `data/aba_extra/First_Year_Class_<year>.xlsx` (the 509 repo stays read only), and rerun. `read_fyc` already accepts both known column schemas; check older headers against `COLS` and extend the manual name table for any school the match leaves out (`data/law_unmatched.csv`).
