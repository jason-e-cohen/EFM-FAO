# EFA + FAO scenario workbook: quickstart and how-to guide

**For:** an analyst picking this project up cold, a year from now or for a new client. You should be comfortable with Excel, a terminal and basic statistics; you do not need to have read anything else first.
**State described:** November 20, 2026 (Phase 4 accepted after two fix passes; the Richmond pre-delivery pass in `DECISIONS.md`, Nov 20, is next). Section 11 says how to keep this guide current.
**Companion:** `guides/Methods_Reference.md` explains the equations and tests in depth. This guide tells you what to do; that one tells you why it is right.

---

## How to use this guide

| If you want to... | Go to |
|---|---|
| Understand what this project is in five minutes | 1 |
| Find your way around the folder | 2 |
| Get the code running on your machine | 3 |
| Build and check a workbook from synthetic data | 4 |
| Set up a new client (or the next cycle for an existing one) | 5 and 6 |
| Know what must be true before anything goes to a client | 7 |
| Understand how work gets done here (build, review, decide, commit) | 8 |
| Fix something that broke | 9 |
| Look up a term | 10 |

---

## 1. What this project is

**The problem.** A college or law school sets admit rates and scholarship awards for its incoming class. Those choices determine how many students enroll, their academic profile (for example the median LSAT) and the revenue left after scholarships. Schools plan this in spreadsheets with no measure of risk: they see one expected class, not the chance it overshoots a cap or misses a median.

**What we built.** A **scenario workbook**: a Python program that reads a school's cell-level admissions history and the scenarios it wants to test, and writes an Excel workbook with live formulas. For each scenario the workbook shows the expected class, its 90% range, the probability of exceeding the class cap, the probability of holding the median and other score percentiles, first-year net tuition revenue (`ntr_y1`) and the discount rate, plus what-if tables. It **evaluates** the client's scenarios; it never recommends one.

**What a "cell" is.** Admits are grouped into cells: residency (in-state or out-of-state) x an optional priority segment (for Richmond, NY and PA applicants) x a test-score band (LSAT 170+, 167 to 169, ...) x a GPA class (high, low, blank). Each cell has applications, admits, an award amount and enrollees per cohort. Everything is computed on cells; there is no student-level data anywhere in the workbook.

**The bigger picture.** The workbook is one piece of a larger design (`02_methodology_v2.8.md`): an estimation pipeline that measures how enrollment responds to aid (from randomized tests or natural experiments), and an optimizer that proposes award grids. Those are specified but not built. Until a school has that evidence, the workbook's response to award changes is a **placeholder the client chooses**, and every figure that depends on it says so: "Response based on client-input".

**First client.** University of Richmond School of Law (2027 entering class). Richmond gave us its consultant's scenario workbook (the "Yellow Arrows" or "YA" file), which we use as a validation fixture: our workbook reproduces its scenarios exactly ("reproduce mode").

---

## 2. Map of the folder

Top level (`~/projects/EFA_FAO`):

| Path | What it is | When you need it |
|---|---|---|
| `CLAUDE.md` | Project rules, file map, deferred features. Claude Code reads it first in every session | Always; read the Rules section before touching client data |
| `DECISIONS.md` | Every decision by date, with the reason and IDs; open questions at the end | When you wonder "why is it like this?" |
| `Prototype_Spec_Scenario_Workbook_v0.6.md` | The build specification. **Section 0A governs** where it differs from later sections | When building or changing the workbook |
| `02_methodology_v2.8.md` | The full method, including the unbuilt pipeline; Appendix F defines every metric | When you need a definition or the bigger design |
| `01_executive_read_v2.8.md`, `03_technical_roadmap_v2.8.md` | Short summary; build plan, annual cycle (5B), reproducibility (5C) | Planning |
| `S1_Requirements_and_User_Stories.md` | Functional requirements (FR-n) | Checking scope |
| `Review_*.md`, `Audit_*.md` | Independent reviews of each phase, with findings and verdicts | Understanding why a rule exists |
| `guides/` | This guide and the methods reference | Start here |
| `prototypes/scenario_workbook/` | **The code.** See below | Running anything |
| `efa_fao/` | The earlier pipeline mockup (undergraduate, synthetic) and the data request generator (`efa_fao/docs/data_request_v3/`) | Data requests; later pipeline work |
| `_superseded/` | Old versions, kept for history | Rarely |
| `Richmond Law - 2027 Scenarios for Client.xlsx` | The client's confidential workbook (git-ignored). **Never copy it off this Mac** | Reproduce mode only |

Inside `prototypes/scenario_workbook/`:

| Path | What it is |
|---|---|
| `README.md` | Commands, module table, test notes. The most current operating notes |
| `config/<client>.yaml` | One file per client: score bands, thresholds, class cap, need aid, risk settings, segments |
| `config/scenarios_<name>.yaml` | The scenarios to evaluate (Baseline first, then children that change a few levers) |
| `config/synthetic.yaml`, `scenarios_synthetic.yaml` | A synthetic client used by tests and demos |
| `config/tools.yaml` | Machine settings (LibreOffice path) |
| `requirements.lock` | Exact package versions |
| `sw/` | The program (module table in the README) |
| `tests/` | Tests 0 to 26, the mutation check and the Excel comparison script |
| `output/` | Everything generated. Git-ignored, because builds from client data contain client values |

---

## 3. Setting up your machine

You need: a Mac (the project environment `.venv` is a macOS build), Python 3.12, Git, LibreOffice, Microsoft Excel, and Claude Code.

1. **Get the code.**
   ```bash
   git clone https://github.com/jason-e-cohen/EFM-FAO.git ~/projects/EFA_FAO
   cd ~/projects/EFA_FAO
   ```
   The repository is private; you need access from Jason.
2. **Python environment.** If `.venv` is missing or broken, create it and install the locked versions:
   ```bash
   python3.12 -m venv .venv
   .venv/bin/pip install -r prototypes/scenario_workbook/requirements.lock
   ```
3. **LibreOffice.** `brew install --cask libreoffice`. It is not put on your PATH; `config/tools.yaml` holds its path (`/Applications/LibreOffice.app/Contents/MacOS/soffice`). Acceptance runs used LibreOffice 26.8; 24.2 rounds one probe cell differently (see 9).
4. **Claude Code.** Install the native build (`claude install`), make sure `~/.local/bin` comes first on your PATH, and start sessions with `claude --model opus` from the project folder. Check the version is current (`claude --version`); old versions cannot use current models.
5. **Check it works.**
   ```bash
   cd prototypes/scenario_workbook
   ../../.venv/bin/python -m pytest tests -q
   ```
   Without the client fixture, about 270 tests pass and 72 skip (the fixture tests). With it, about 340 pass and 3 skip (Baseline criteria the client file cannot supply). Those are the expected results.

**Shell tip.** When pasting command blocks into zsh, do not include `# comments` after commands; zsh passes them as arguments.

---

## 4. Your first build (synthetic data, about 10 minutes)

This walks through the whole loop on data that is not confidential.

1. **Build.**
   ```bash
   cd ~/projects/EFA_FAO/prototypes/scenario_workbook
   ../../.venv/bin/python -m sw.build --config config/synthetic.yaml --data synthetic --seed 101 \
     --scenarios config/scenarios_synthetic.yaml --out output/ --pdf --sentinel
   ```
   It writes, under `output/synthetic/2027/<build_id>/`: `workbook.xlsx` (the deliverable form), `workbook_sentinel.xlsx` (every stored value set to -999, for the Excel check) and `workbook_Summary.pdf`.
2. **Read the workbook.** Open `workbook.xlsx`. Start at `README`, then `Summary`. Inputs are blue cells on `Inputs` and `Levers`; everything else is a formula. `Checks` must show OK (integrity, not opinions about awards). `RunLog` records the build id, code hash, data hash and package versions.
3. **Prove Excel agrees with Python.** Open `workbook_sentinel.xlsx` in Excel. Excel recalculates on open, replacing every -999. Use Save As to save a copy in the same folder, then:
   ```bash
   ../../.venv/bin/python tests/compare_excel_saved.py output/synthetic/2027/<build_id>/<your copy>.xlsx
   ```
   You want 0 value mismatches, 0 cells still at -999 and 0 formula differences. The script refuses files that are not a recalculated sentinel of the current build, so it cannot pass by accident.
4. **Try a lever.** On `Levers`, change a scenario's admit rate or award, let Excel recalculate, and watch the Summary. `Checks` will say "rebuild needed" if you change something that is fixed at build time (for example the median threshold).

**What the build id means.** It is a hash of the config, the cell data, the scenario file, `requirements.lock` and the code. Two workbooks with the same id are the same apart from the timestamp. Any code change gives a new id, and the Excel check has to be redone for it.

---

## 5. Setting up a new client

Plan on two to four weeks, most of it waiting for data. Do the steps in order.

### 5.1 Confidentiality first
- Create the client's data folder **outside** the code folder (for example `~/client_data/<client>/`). Client data, fixtures and client workbooks never go into git, Supabase, a public link or another client's work (`CLAUDE.md`, Rules).
- Agree the small-cell policy in writing. The default suppresses groups under 10; a client may elect to show small cells to named, authenticated roles. Record the sign-off in the SOW (methodology section 9).
- Check before sharing anything outside Frankel that it contains no other client's information.

### 5.2 Request the data
Generate the data request from `efa_fao/docs/data_request_v3/`:
```bash
cd ~/projects/EFA_FAO/efa_fao/docs/data_request_v3
../../../.venv/bin/python build_request.py --program law --institution "<Institution>" --date "<date>" --due "<date>"
```
(`--program undergraduate` for a college.) For the scenario workbook you need, at minimum: cell-level applications, admits, award and enrollees for three cohorts; published tuition by year; the class target and cap; need and other aid totals; state-level counts if a geographic segment matters; weekly pacing if pool tripwires matter. Ask for test-score bands **by each student's highest score** (the ABA 509 basis; see 5.5).

### 5.3 Write the client config
Copy `config/richmond.yaml` to `config/<client>.yaml` and edit every value; there are no product defaults, and a missing required value stops the build with a message. The fields that matter most:

| Field | What to put | Common mistake |
|---|---|---|
| `cycle.base_cycle`, `plan_cycle`, `history` | Latest complete cohort, the year being planned, the cohorts you have | Forgetting to roll these forward next year |
| `tuition_by_cohort`, `tuition_base`, `tuition_by_year_usd` | Published tuition by cohort; base-cycle tuition; the plan-year figure in dollars if the client gives one | Using a percentage when the client quoted dollars |
| `score.bands`, `pool_threshold`, `floor`, `percentile_targets` | The client's own bands; the score above which pool growth applies; the floor; targets as `{q, t}` with each `t` a band bound | A target `t` that is not a band bound (the loader rejects it) |
| `class.cap`, `target`, `what_if` | Hard cap; planned class; sizes for the class-size table | Target above cap |
| `need.total`, `reference_class` | Need aid and the class it was budgeted for | |
| `risk.common_shock_sd` | Year-to-year variation; 0.10 is an illustrative placeholder | Presenting probabilities as calibrated |
| `segments` | Optional priority segment (one per scenario) | Defining a segment the cell data does not carry |
| `aba_509_by_cohort` | Public ABA 509 figures (law) for the History reconciliation | Leaving it out: you lose the cheapest data check |
| `hold_position_rows` | True while the score basis is unconfirmed: every median and percentile figure reads "held pending confirmation" | Forgetting to set it back to false once the basis is confirmed |

### 5.4 Prepare the cell data
The build reads a long table, one row per cell x cohort:
`cell_id, residency, segment, score_lo, gpa_class, cohort, apps, admits, award_usd, enrolled`.
`residency` is `in` or `out`; `segment` is blank or the configured segment name; `score_lo` is the band's lower bound (blank if unscored). Any other column is rejected, which keeps protected attributes out. If you have state-level counts, split each out-of-state cell into segment and non-segment parts in data preparation.

### 5.5 Check the data before modeling
Build once and read the **History** sheet's 509 reconciliation and the **Checks** sheet. For Richmond the check found that the client workbook's lower LSAT bands disagree with the published 509 percentiles. That is why the median and percentile rows are held until the score basis is confirmed. Do not skip this.

### 5.6 Write the scenarios
`config/scenarios_<client>.yaml`: Baseline first (latest-cohort rates and awards), then children that name a parent and change only what differs (pool multiplier, tuition, class target, incentive, yield shift, per-cell overrides). Use `config/scenarios_synthetic.yaml` as the pattern. A client's own scenarios can be entered here; a client workbook used as a fixture is not copied into the repository.

### 5.7 Build, check, review
Build with `--pdf --sentinel`, run the desktop Excel check (4, step 3) on a Mac **and** on Windows, read the Summary PDF, then get an independent review (8) before anything is sent.

---

## 6. The next cycle for an existing client

The annual cycle is in the roadmap (section 5B). In practice:

1. **After census (October).** Load the census actuals. Compare last cycle's adopted scenario with what happened: class, medians, `ntr_y1`, segment enrolled, each against its 90% range. Record the miss; it is the start of calibrating the year-to-year variation.
2. **Before the cycle (November to December).** In the client config, roll `base_cycle`, `plan_cycle` and `history` forward one year; add the new cohort's tuition and 509 figures; refresh the cell data. Rebuild, check, review.
3. **In cycle (January to May).** Update `pool_ytd_growth` and `pool_ytd_as_of` weekly from pacing data and read the pool strip. Save each scenario revision as a new build.
4. **At award decisions.** Mark the adopted scenario and keep its build id; next October's comparison uses it.

---

## 7. Before anything goes to a client

A checklist. All of it, every time.

- [ ] The full suite passes on the Mac `.venv`, with and without the fixture where one applies.
- [ ] The desktop Excel check passes on this exact build id, on Mac **and** Windows Excel.
- [ ] `Checks` shows OK; the History 509 reconciliation has been read and any disagreement explained or held.
- [ ] Every probability and range carries its labels: response basis, year-to-year variation, segment share if assumed. Probabilities near 0 or 1 read "under 5%" or "over 95%".
- [ ] Held rows (for example `hold_position_rows`) are held.
- [ ] An independent review has been done (8) and its findings resolved.
- [ ] No other client's information is in the file; the small-cell policy matches the client's written election.
- [ ] Jason has reviewed the workbook and the Summary PDF. Nothing client-facing goes out without human review.

---

## 8. How work gets done here

The project runs as a loop of separate Claude Code sessions, with Jason deciding:

| Role | What it does | Where |
|---|---|---|
| **Builder** | Implements a phase or fix pass against the spec; runs every test; reports; never edits specs or commits | Fresh Claude Code session, Opus, high effort |
| **Reviewer** | Independent: re-runs tests, checks formulas by hand, tries its own mutants, checks the fixture rule, writes `Review_<phase>.md` | Fresh session; never the builder's |
| **Advisor** | Turns reviews into decisions and prompts; edits spec, methodology and `DECISIONS.md` | A planning session (chat) |
| **Jason** | Decides; runs the desktop Excel check; commits and tags | Terminal and Excel |

The cycle for each phase: **spec change, then build, then review, then decisions, then fix pass, then Excel check, then commit and tag.** Tags mark accepted states (`phase3-accepted`, `phase2.2-accepted`, ...). Commit only through Jason, from the Mac terminal.

Rules that matter in every session: the spec is the brief (section 0A governs); report test failures rather than tuning to pass; keep fixture values out of everything except `output/`; decisions go in `DECISIONS.md` with a date and reason.

---

## 9. When something breaks

| Symptom | Likely cause | Fix |
|---|---|---|
| `claude` shows an old version or old models | Old npm copy first on PATH | `claude install`; put `~/.local/bin` first in `~/.zshrc` |
| Tests that use LibreOffice skip | `soffice` not found | Check `config/tools.yaml` or set `SOFFICE_PATH` |
| Excel parity test passes but you doubt it | Never trust a parity run without the sentinel | Use the sentinel copy and `compare_excel_saved.py` |
| The rounding probe on `Checks` differs | Old LibreOffice (24.2 rounds one boundary case differently) | Use LibreOffice 26.8; follow desktop Excel if engines differ |
| Compare script refuses your file | Not a recalculated sentinel of the current build id, or code changed since the build | Rebuild with `--sentinel`, open in Excel, Save As, compare again |
| Config error at build | A required value is missing or invalid (by design) | Read the message; fill the value in `config/<client>.yaml` |
| `Checks` says "rebuild needed" | A build-time input was edited in Excel | Change it in the config and rebuild |
| Mutation run stops | Memory | `--jobs 2` |
| zsh errors like `command not found: not` | Comments pasted after commands | Paste commands without `#` comments |

---

## 10. Glossary

| Term | Meaning |
|---|---|
| Cell | A group of admits sharing residency, segment, score band and GPA class |
| Cohort, base cycle, plan cycle | An entering class; the latest complete one; the one being planned |
| Scenario, Baseline, parent | A set of lever values; the status quo; the scenario a child changes |
| Lever | A scenario input: admit rate, award, pool multiplier, tuition, class target, incentive, yield shift |
| Pool multiplier | Growth in applications at or above the pool threshold, relative to the base cycle |
| Segment | A client-defined priority group of cells (Richmond: NY and PA) |
| `ntr_y1` | First-year net tuition revenue of the entering class: tuition minus merit, need and specialty aid |
| Discount rate (entering, first year) | Institutional aid divided by gross first-year tuition of the entering class |
| Margin | Enrolled at or above a score threshold minus enrolled below it |
| Percentile target `{q, t}` | "At most a share q of scored enrollees below score t" (median: q = 0.5) |
| Shrink path | The rule that cuts admits from the lowest bands first to reach a smaller class |
| Pool strip, yield strip | Tables of outcomes across pool multipliers and yield shifts |
| Year-to-year variation (s) | A common shock to all yields in a cycle; 0.10 is illustrative |
| Reproduce mode | Running the client's own workbook scenarios through our ledger to prove we match it |
| Sentinel copy | A workbook whose stored values are all -999, so an Excel check cannot pass without recalculation |
| Mutation check | Deliberately breaking one formula at a time to prove the tests notice |
| Fixture | The client's workbook used only for validation; it stays on the Mac |
| "Response based on client-input" | The label on figures that depend on assumed, not estimated, price sensitivity |

---

## 11. Keeping this guide current

Update this guide when a phase is accepted or a rule changes. The facts most likely to go stale: test counts (3, 4), commands and file names (4, 5.2), the config fields (5.3) and the checklist (7). The README in `prototypes/scenario_workbook/` is updated by every build session and is the place to check first if this guide and the code disagree.
