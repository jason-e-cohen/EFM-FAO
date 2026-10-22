# Data request v3

One specification, two documents: a law (JD) request and an undergraduate request, plus Excel templates and field dictionaries for each. Built from `02_methodology_v2.6.md`, the v2.1 request (`../04_data_request_v2.md`), Jason's reference request, and the Common Data Set 2025-26 template. Sources, gaps and judgment calls are in `GAP_LOG.md`.

Status: draft for Jason's review (plan of action, Step 3b, D1 to D4). `../04_data_request_v2.md` is unchanged. Promote v3 over it after S2 signs off. Nothing here touches `efa_fao/src/`, `config/` or `sql/`.

## Generate

```bash
cd efa_fao/docs/data_request_v3
python build_request.py --program law --institution "University of Richmond School of Law" --contact "[Name, email]" --date "[Date]" --due "[Date]"
python build_request.py --program undergraduate --institution "[Institution]"
python build_request.py --program all
python -m pytest test_spec.py -q   # spec checks
```

Needs `python-docx`, `openpyxl` and `pyyaml`. The first two are not in the project's pinned list as far as the verification report shows; install them in the environment you use (`pip install python-docx openpyxl`).

Each run writes to `output/`:

| File | What |
|---|---|
| `Data_Request_v3_<program>_<institution>.docx` | Client-facing request (body, then Appendix A fields and Appendix B calendar events) |
| `Data_Request_v3_<program>_<institution>.md` | Same content as text, for diffs |
| `Data_Request_Template_<program>.xlsx` | One sheet per file (field, type, required, tier, allowed values, hover description), plus `Institutional_Reference`, `Scoping_Inputs`, `Components`, `Event_Types`, `Codes`, `Dictionary` |
| `data_dictionary_v3_<program>.csv` | Field specification for the program, in the layout of `config/data_dictionary_v2.csv` plus `ref` |

Bracketed placeholders (`[secure file transfer]`, `[retention policy]`, `[institution counsel]`, dates) are left for the account lead to fill.

## Source files (edit these, never the output)

| File | Controls |
|---|---|
| `spec/request_spec.yaml` | Narrative sections, tables, checklist, calendar events. A block can carry `only: law` or `only: undergraduate`, or a `{law:, undergraduate:}` text |
| `spec/fields.csv` | Every field. `law` and `ug` columns: Y send, C send under the stated condition, N optional, `-` not requested. `tier`: 1, 2 or A (add-on). `law_note` and `ug_note` add program wording. `values` may be `Law: ... UG: ...` |
| `spec/files.csv` | File list, row grain, tier and key fields by program, and order |
| `spec/components.csv` | Aid components by program |
| `spec/definitions.csv` | Definitions table, with CDS or other source |
| `spec/reference_items.csv` | Institutional reference figures (CDS for undergraduate, ABA 509 for law) |
| `spec/scoping.csv` | Price-test screen inputs |
| `test_spec.py` | Spec checks: ZIP5 only in `zip_key`; no credit-data statement; protected attributes audit-only; no direct identifiers; no law terms in the undergraduate document or the reverse; all outputs build |

## Add another program (for example a graduate business program)

1. Add a profile under `profiles:` in `request_spec.yaml`.
2. Add a column for it in `fields.csv`, `components.csv`, `scoping.csv` and `files.csv`, and `programs`/`only` tags in the YAML and `definitions.csv`.
3. Add the program name to `PROGRAMS` and the `col()` function in `build_request.py`, and a reference-items group.
4. Run `test_spec.py`, extend its leak checks, and read the generated document end to end.
