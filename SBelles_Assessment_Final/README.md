# S'Belles Data Engineering & Wrangling Assessment — Final Submission

## Overview

This submission contains a unified marketing data warehouse for S'Belles, a fictional fast-fashion brand. Six marketing datastreams — paid social, web analytics, ecommerce, organic social, podcast mentions, and out-of-home airport media — have been integrated into a Kimball-style dimensional model with daily fact tables and conformed dimensions.

Data spans January 2023 through June 2024 (18 months). Twenty-one raw CSV source files were profiled, cleaned, deduplicated, temporally aligned, and loaded into 8 fact tables and 5 conformed dimension tables.

## Directory Structure

```text
SBelles_Assessment_Final/
├── paid_social/          Daily paid advertising metrics (Instagram, Pinterest, TikTok)
├── web_analytics/        Daily web traffic aggregates and event-level detail
├── ecommerce/            Daily transaction aggregates and line-item detail
├── organic_social/       Daily owned TikTok engagement metrics
├── podcast/              Podcast mention data, sparse by design
├── ooh/                  Daily out-of-home airport advertising, expanded from weekly
├── dimensions/           Five conformed dimension tables enabling cross-channel joins
├── documentation/        Schema dictionary, transformation notes, assumptions, data model
└── README.md             This file
```

### Datastream Details

- **paid_social/**: Daily paid advertising metrics across Instagram, Pinterest, and TikTok. Nine source files unified with schema drift resolved (column renames, unit standardization, consistent granularity).
- **web_analytics/**: Daily web traffic aggregates and event-level detail. Four source files with December 2023 overlap deduplicated between Q3Q4 2023 and Q1 2024 files.
- **ecommerce/**: Daily transaction aggregates and line-item detail. Three source files covering Q1 2023 through Q2 2024.
- **organic_social/**: Daily owned TikTok engagement metrics. Two source files (monthly and weekly) unified into daily grain.
- **podcast/**: Podcast mention data, sparse by design. Two source files covering 5 podcasts and 85 daily observation records.
- **ooh/**: Daily out-of-home airport advertising metrics, expanded from weekly source grain. One source file with spend allocated evenly across 7-day periods.
- **dimensions/**: Five conformed dimension tables — date, geography, channel, campaign/initiative, and podcast — enabling cross-channel joins on shared keys.
- **documentation/**: Complete schema dictionary, transformation notes, assumptions log, and data model diagram.

## Reproduction

From the repository root:

```bash
pip install -r requirements.txt
python src/rebuild_all.py
```

This single command rebuilds the entire data warehouse from raw source files, runs cross-channel analysis, assembles this submission directory, and validates every output.

## Documentation Guide

- **schema_dictionary.md**: Unified schema for every table with column definitions, data types, source-to-target mappings, and data quality notes.
- **transformation_notes.md**: Complete description of every transformation applied, including schema drift resolution, deduplication, aggregation, and temporal alignment.
- **assumptions.md**: Every judgment call made during the project, grouped by category (temporal alignment, schema resolution, aggregation, data quality).
- **final_data_model_diagram.png**: Visual representation of the Kimball star schema showing all fact and dimension tables with their join relationships.

## Design Decisions

The assignment specification suggests flat datastream folders. This submission uses a Kimball dimensional model with separate fact and dimension folders because:

1. **Cross-channel joins**: Conformed dimensions (`dim_date`, `dim_geography`) enable cross-channel analysis that flat, isolated folders cannot express. Every fact table joins to shared dimensional keys.
2. **Production alignment**: The structure mirrors how the data would be organized in a production analytical warehouse, making it immediately usable by downstream tools (BI platforms, causal models, MMM pipelines).
3. **Downstream readiness**: Causal models and media mix models require channel-separated, temporally aligned inputs with shared dimensional keys — exactly what this structure provides.

**Geographic Scope Note**

OOH airport advertising spans 20 U.S. airports (national reach), while ecommerce and web activity are limited to Georgia DMAs. This geographic scope mismatch likely contributes to the observed spend-revenue discrepancy and limits direct attribution interpretation without regional normalization.
