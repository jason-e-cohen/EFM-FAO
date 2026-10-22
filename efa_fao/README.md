# EFA + FAO v2

Enrollment funnel analysis and financial aid optimization: a Python build pipeline, a Supabase schema, and (next phase) a Vercel dashboard. This repository contains the pipeline, a synthetic institution with a known causal truth, the schema, the data request, and tests.

All data here are **synthetic**. They were built from aggregate shapes printed in prior deliverables; no student records were copied.

## Run it

```bash
python -m efa_fao.synth.generate --out data/synthetic            # about 5 seconds
PYTHONPATH=src python -m efa_fao.run_pipeline --boot 40           # about 2 minutes
```

Outputs land in `outputs/`. Tests: `tests/test_guardrails.py` (plain functions; run with pytest or any loop over `test_*`).

## Layout

| Path | What |
|------|------|
| `config/institution.yaml` | Prices, aid policy, guardrails, privacy, experiment design |
| `config/data_dictionary_v2.csv` | Client data dictionary (71 fields) |
| `config/source_taxonomy.csv` | Versioned source mapping rules |
| `src/efa_fao/synth/` | Synthetic world and generator (`world.py` is the ground truth; the pipeline never imports it) |
| `src/efa_fao/pipeline/prepare.py` | Validation, cleaning rules, features |
| `src/efa_fao/pipeline/models.py` | Estimators: legacy replica, observational, experiment, discontinuity, anchored, hybrid |
| `src/efa_fao/pipeline/optimize.py` | Net tuition revenue optimizer (MILP) |
| `src/efa_fao/pipeline/aggregate.py` | Aggregation and disclosure control |
| `src/efa_fao/pipeline/validate.py` | Synthetic-only validation against truth |
| `src/efa_fao/run_pipeline.py` | End-to-end run |
| `sql/schema.sql` | Supabase schema with row-level security |
| `docs/` | Executive read, methodology, technical roadmap, data request |
| `outputs/` | Generated artifacts (one file per dashboard table) |
