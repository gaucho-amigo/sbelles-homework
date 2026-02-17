# S'Belles Marketing Data Warehouse

Alembic Field Scientist assessment: a Kimball-style marketing data warehouse for S'Belles, a fictional fast-fashion brand. Integrates six marketing datastreams into a unified dimensional model with conformed dimensions enabling cross-channel analysis.

Data window: `2023-01-01` through `2024-06-30` (18 months, 21 raw source files).

## Quick Start

```bash
pip install -r requirements.txt
python src/rebuild_all.py
```

This single command rebuilds the entire data warehouse from raw data, runs cross-channel analysis, assembles the submission directory, and validates all outputs.

## Key Results

- 6 daily fact tables + 2 source-grain tables + 5 conformed dimensions
- 48/48 validation checks passed
- Financial reconciliation to the penny ($6.0M paid social, $29.5M OOH, $498K ecommerce)
- Full reproducibility from a single script

## Repository Structure

```text
.
├── data/                         # 21 raw CSV source files (read-only)
├── src/
│   ├── rebuild_all.py            # Master reproducibility script (single entry point)
│   ├── run_all.py                # ETL orchestrator (dimensions + facts + validation)
│   ├── transforms/               # Fact and dimension build logic
│   ├── validation/               # Post-build and submission validation checks
│   ├── profiling/                # Phase 0 source data profiling
│   ├── exploration/              # Grain/schema design investigation scripts
│   └── reference_data/           # Airport lookup builder
├── analysis/                     # Cross-channel analysis scripts
│   └── output/                   # Charts, summaries, lag analysis artifacts
├── data_warehouse/               # Working warehouse (13 CSVs + documentation)
├── SBelles_Assessment_Final/     # Submission deliverable (copy of warehouse outputs)
├── docs/                         # Working design documentation
├── reference_data/               # Generated lookup CSVs
├── output/profiling/             # Profiling output artifacts
└── requirements.txt
```

### Directory Details

- **data/**: Raw source CSV files. Read-only input to the pipeline — never modified.
- **src/**: All transformation, validation, and orchestration code. `rebuild_all.py` is the single entry point that runs everything.
- **analysis/**: Cross-channel analysis scripts (spend trends, lag analysis, promo impact) that read from the warehouse and produce charts and summaries.
- **data_warehouse/**: The working warehouse with fact tables organized by datastream, conformed dimensions, and full documentation.
- **SBelles_Assessment_Final/**: The submission-ready deliverable. Contains the same warehouse outputs reorganized into the assessment structure with a self-contained README.
- **docs/**: Working design documentation (schema design, source-to-target mapping, grain analysis, data profiles).

## Build Steps (Manual)

If you prefer to run steps individually:

```bash
# 1. Generate airport lookup
python3 -m src.reference_data.airports

# 2. Build warehouse (dimensions + facts + validation)
python3 -m src.run_all

# 3. Run analysis
python3 -m analysis.cross_channel_summary
python3 -m analysis.generate_charts
python3 -m analysis.lag_analysis
python3 -m analysis.promo_analysis

# 4. Validate submission
python3 -m src.validation.submission_check
```

## Design Documentation

- **Warehouse overview:** [`data_warehouse/README.md`](data_warehouse/README.md)
- **Schema dictionary:** [`data_warehouse/documentation/schema_dictionary.md`](data_warehouse/documentation/schema_dictionary.md)
- **Transformation notes:** [`data_warehouse/documentation/transformation_notes.md`](data_warehouse/documentation/transformation_notes.md)
- **Assumptions:** [`data_warehouse/documentation/assumptions.md`](data_warehouse/documentation/assumptions.md)
- **Schema design:** [`docs/schema_design.md`](docs/schema_design.md)
- **Source-to-target mapping:** [`docs/source_to_target_mapping.md`](docs/source_to_target_mapping.md)
- **Grain analysis:** [`docs/grain_analysis.md`](docs/grain_analysis.md)
- **Source data profile:** [`docs/data_profile.md`](docs/data_profile.md)
