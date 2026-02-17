"""Master reproducibility script — rebuilds everything from raw data to final submission.

Usage:
    python src/rebuild_all.py        (from repo root)
    python -m src.rebuild_all        (module form)
"""

import shutil
import time
import pathlib
import subprocess
import sys
from datetime import datetime

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
WAREHOUSE_DIR = PROJECT_ROOT / "data_warehouse"
SUBMISSION_DIR = PROJECT_ROOT / "SBelles_Assessment_Final"

# Mapping: submission relative path -> warehouse source path
FILE_MAP = {
    "paid_social/fact_paid_social_daily.csv":
        "fact_paid_social/fact_paid_social_daily.csv",
    "web_analytics/fact_web_analytics_daily.csv":
        "fact_web_analytics/fact_web_analytics_daily.csv",
    "web_analytics/fact_web_analytics_events.csv":
        "fact_web_analytics/fact_web_analytics_events.csv",
    "ecommerce/fact_ecommerce_daily.csv":
        "fact_ecommerce/fact_ecommerce_daily.csv",
    "ecommerce/fact_ecommerce_transactions.csv":
        "fact_ecommerce/fact_ecommerce_transactions.csv",
    "organic_social/fact_organic_social_daily.csv":
        "fact_organic_social/fact_organic_social_daily.csv",
    "podcast/fact_podcast_daily.csv":
        "fact_podcast/fact_podcast_daily.csv",
    "ooh/fact_ooh_daily.csv":
        "fact_ooh/fact_ooh_daily.csv",
    "dimensions/dim_date.csv":
        "dimensions/dim_date.csv",
    "dimensions/dim_geography.csv":
        "dimensions/dim_geography.csv",
    "dimensions/dim_channel.csv":
        "dimensions/dim_channel.csv",
    "dimensions/dim_campaign_initiative.csv":
        "dimensions/dim_campaign_initiative.csv",
    "dimensions/dim_podcast.csv":
        "dimensions/dim_podcast.csv",
    "documentation/schema_dictionary.md":
        "documentation/schema_dictionary.md",
    "documentation/transformation_notes.md":
        "documentation/transformation_notes.md",
    "documentation/assumptions.md":
        "documentation/assumptions.md",
    "documentation/final_data_model_diagram.png":
        "documentation/final_data_model_diagram.png",
}


def banner(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def run_module(module_name):
    """Run a Python module as a subprocess, streaming output."""
    print(f"\n  Running {module_name} ...")
    result = subprocess.run(
        [sys.executable, "-m", module_name],
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode != 0:
        print(f"  ERROR: {module_name} exited with code {result.returncode}")
        sys.exit(1)


def assemble_submission():
    """Copy warehouse outputs into SBelles_Assessment_Final/."""
    banner("STEP 3: ASSEMBLE SUBMISSION DIRECTORY")

    # Clear and recreate
    if SUBMISSION_DIR.exists():
        shutil.rmtree(SUBMISSION_DIR)
    SUBMISSION_DIR.mkdir()

    # Create subdirectories and copy files
    for dest_rel, src_rel in FILE_MAP.items():
        dest = SUBMISSION_DIR / dest_rel
        src = WAREHOUSE_DIR / src_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        print(f"  {src_rel}  ->  {dest_rel}")

    # Write the submission README (always regenerated since rmtree wipes it)
    _write_submission_readme(SUBMISSION_DIR / "README.md")

    print(f"\n  Submission directory assembled: {SUBMISSION_DIR.relative_to(PROJECT_ROOT)}/")


def main():
    start = time.time()

    banner("S'BELLES ASSESSMENT — FULL REBUILD")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Project root: {PROJECT_ROOT}")

    # ------------------------------------------------------------------
    # Step 1: Build data warehouse (dimensions + fact tables + validation)
    # ------------------------------------------------------------------
    banner("STEP 1: BUILD DATA WAREHOUSE")
    run_module("src.reference_data.airports")
    run_module("src.run_all")

    # ------------------------------------------------------------------
    # Step 2: Run analysis scripts
    # ------------------------------------------------------------------
    banner("STEP 2: RUN ANALYSIS SCRIPTS")
    run_module("analysis.cross_channel_summary")
    run_module("analysis.generate_charts")
    run_module("analysis.lag_analysis")
    run_module("analysis.promo_analysis")

    # ------------------------------------------------------------------
    # Step 3: Assemble submission directory
    # ------------------------------------------------------------------
    assemble_submission()

    # ------------------------------------------------------------------
    # Step 4: Run final validation on submission directory
    # ------------------------------------------------------------------
    banner("STEP 4: FINAL SUBMISSION VALIDATION")
    run_module("src.validation.submission_check")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    elapsed = time.time() - start
    banner("REBUILD COMPLETE")
    print(f"  Total elapsed: {elapsed:.1f}s")
    print()
    print("  Produced:")
    print("    - data_warehouse/        13 CSV tables + documentation")
    print("    - analysis/output/        Cross-channel analysis & charts")
    print("    - SBelles_Assessment_Final/  Submission-ready directory")
    print()
    print("  Key metrics:")
    print("    - 6 daily fact tables + 2 source-grain tables + 5 dimensions")
    print("    - Financial reconciliation to the penny")
    print("    - All validation checks passed")


def _write_submission_readme(path):
    """Write the submission README."""
    content = """\
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
"""
    path.write_text(content)
    print(f"  README.md written")


if __name__ == "__main__":
    main()
