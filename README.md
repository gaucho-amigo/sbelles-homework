# S'Belles Marketing Data Warehouse

Alembic Field Scientist assessment: designing a Kimball dimensional model for S'Belles, a fictional fast-fashion brand. Covers six marketing streams (paid social, web analytics, e-commerce, organic social, podcast, and out-of-home) unified under conformed dimensions.

## Repository Structure

```
├── data/                       # Raw source CSVs (21 files) and data README
├── data_warehouse/             # Star-schema output (fact tables, dimensions, documentation)
│   ├── fact_paid_social/
│   ├── fact_web_analytics/
│   ├── fact_ecommerce/
│   ├── fact_organic_social/
│   ├── fact_podcast/
│   ├── fact_ooh/
│   ├── dimensions/
│   └── documentation/
├── docs/                       # Design documentation
│   ├── schema_design.md        # Kimball star-schema specification
│   ├── source_to_target_mapping.md
│   ├── grain_analysis.md
│   └── data_profile.md
├── reference_data/             # Generated lookup tables (gitignored CSVs)
├── src/                        # Python source code
│   ├── exploration/            # EDA and grain analysis scripts
│   ├── profiling/              # Data profiling scripts
│   └── reference_data/         # Reference data generation scripts
├── output/                     # Script output artifacts
└── requirements.txt
```

## Getting Started

```bash
pip install -r requirements.txt
```

### Generate airport lookup table

Downloads OurAirports data and produces a 20-row airport-to-state mapping used by the OOH fact table:

```bash
python -m src.reference_data.airports
# -> reference_data/airport_lookup.csv
```

### Run data profiling

```bash
python -m src.profiling.profile_all
```

## Design Documentation

- **Schema design:** [`docs/schema_design.md`](docs/schema_design.md)
- **Source-to-target mapping:** [`docs/source_to_target_mapping.md`](docs/source_to_target_mapping.md)
- **Grain analysis:** [`docs/grain_analysis.md`](docs/grain_analysis.md)
- **Data warehouse README:** [`data_warehouse/README.md`](data_warehouse/README.md)
