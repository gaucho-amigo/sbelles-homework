# S'Belles Marketing Data Warehouse

Alembic Field Scientist assessment project for building a Kimball-style marketing warehouse for a fictional fast-fashion brand.

The warehouse integrates six streams:
- paid social
- web analytics
- ecommerce
- organic social
- podcast mentions
- out-of-home airport media

Data window: `2023-01-01` through `2024-06-30`.

## Repository Structure

```text
.
├── data/                         # 21 raw CSV source files + source data README
├── src/
│   ├── run_all.py                # Main ETL orchestrator (dimensions + facts + validation)
│   ├── transforms/               # Fact and dimension build logic
│   ├── validation/               # Post-build reconciliation and QA checks
│   ├── profiling/                # Phase 0 profiling script
│   ├── exploration/              # Grain/schema design investigation scripts
│   └── reference_data/           # Airport lookup builder
├── reference_data/               # Generated lookup CSVs (airport lookup)
├── data_warehouse/               # Final warehouse outputs + warehouse documentation
├── docs/                         # Design docs (schema, mapping, grain, profiling notes)
├── analysis/                     # Cross-channel analysis scripts + output artifacts
│   └── output/
├── output/
│   └── profiling/                # Profiling output artifacts
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

## Build The Warehouse

1. Generate airport lookup table:

```bash
python3 -m src.reference_data.airports
# writes reference_data/airport_lookup.csv
```

2. Run full pipeline (dimensions, fact tables, output validation):

```bash
python3 -m src.run_all
```

3. Optional: run expanded post-build checks:

```bash
python3 -m src.validation.post_build_checks
```

## Profiling And Exploration

- Run full source profiling:

```bash
python3 -m src.profiling.profile_all
```

- Generate exploratory design investigations:

```bash
python3 -m src.exploration.grain_analysis
python3 -m src.exploration.schema_design_investigation
```

## Analysis Workflow

These scripts read from `data_warehouse/` and write to `analysis/output/`:

```bash
python3 -m analysis.cross_channel_summary
python3 -m analysis.generate_charts
python3 -m analysis.lag_analysis
python3 -m analysis.executive_outputs
python3 -m analysis.promo_analysis
python3 -m analysis.generate_slide_reference
python3 -m analysis.generate_diagram
```

## Design Documentation

- **Warehouse overview:** [`data_warehouse/README.md`](data_warehouse/README.md)
- **Schema design:** [`docs/schema_design.md`](docs/schema_design.md)
- **Source-to-target mapping:** [`docs/source_to_target_mapping.md`](docs/source_to_target_mapping.md)
- **Grain analysis:** [`docs/grain_analysis.md`](docs/grain_analysis.md)
- **Source data profile:** [`docs/data_profile.md`](docs/data_profile.md)
