"""Orchestrator: run all dimension builds and fact transforms, then validate."""

import time
import pandas as pd
from src.transforms.utils import WAREHOUSE_DIR, DATE_START, DATE_END
from src.transforms.build_dimensions import build_all_dimensions
from src.transforms.transform_ooh import transform_ooh
from src.transforms.transform_organic_social import transform_organic_social
from src.transforms.transform_podcast import transform_podcast
from src.transforms.transform_paid_social import transform_paid_social
from src.transforms.transform_ecommerce import transform_ecommerce
from src.transforms.transform_web_analytics import transform_web_analytics


def validate_outputs():
    """Validate all output CSVs: date range, no fully-empty cols, row count > 0."""
    print("\n" + "=" * 60)
    print("VALIDATION")
    print("=" * 60)

    checks = []

    # All expected output files
    outputs = {
        "dim_date": WAREHOUSE_DIR / "dimensions" / "dim_date.csv",
        "dim_geography": WAREHOUSE_DIR / "dimensions" / "dim_geography.csv",
        "dim_channel": WAREHOUSE_DIR / "dimensions" / "dim_channel.csv",
        "dim_campaign_initiative": WAREHOUSE_DIR / "dimensions" / "dim_campaign_initiative.csv",
        "dim_podcast": WAREHOUSE_DIR / "dimensions" / "dim_podcast.csv",
        "fact_paid_social_daily": WAREHOUSE_DIR / "fact_paid_social" / "fact_paid_social_daily.csv",
        "fact_web_analytics_daily": WAREHOUSE_DIR / "fact_web_analytics" / "fact_web_analytics_daily.csv",
        "fact_ecommerce_daily": WAREHOUSE_DIR / "fact_ecommerce" / "fact_ecommerce_daily.csv",
        "fact_organic_social_daily": WAREHOUSE_DIR / "fact_organic_social" / "fact_organic_social_daily.csv",
        "fact_podcast_daily": WAREHOUSE_DIR / "fact_podcast" / "fact_podcast_daily.csv",
        "fact_ooh_daily": WAREHOUSE_DIR / "fact_ooh" / "fact_ooh_daily.csv",
    }

    # Date columns in each fact table
    date_cols = {
        "dim_date": "date",
        "fact_paid_social_daily": "date",
        "fact_web_analytics_daily": "date",
        "fact_ecommerce_daily": "date",
        "fact_organic_social_daily": "date",
        "fact_podcast_daily": "date",
        "fact_ooh_daily": "date",
    }

    for name, path in outputs.items():
        print(f"\n  --- {name} ---")

        # Check 1: file exists
        exists = path.exists()
        status = "PASS" if exists else "FAIL"
        checks.append((name, "file_exists", status))
        print(f"    file exists: {status}")
        if not exists:
            continue

        df = pd.read_csv(path)

        # Check 2: row count > 0
        row_ok = len(df) > 0
        status = "PASS" if row_ok else "FAIL"
        checks.append((name, "row_count>0", status))
        print(f"    row count: {len(df):,} — {status}")

        # Check 3: no fully-empty columns (excluding known-nullable by design)
        nullable_by_design = {
            "dim_geography": {"zip_code"},  # not populated at this grain
        }
        allowed = nullable_by_design.get(name, set())
        empty_cols = [c for c in df.columns
                      if df[c].isna().all() and c not in allowed]
        no_empty = len(empty_cols) == 0
        status = "PASS" if no_empty else "FAIL"
        checks.append((name, "no_empty_cols", status))
        if not no_empty:
            print(f"    empty columns: {empty_cols} — {status}")
        else:
            print(f"    no empty columns: {status}")

        # Check 4: date range (for tables with date columns)
        if name in date_cols:
            dcol = date_cols[name]
            dates = pd.to_datetime(df[dcol])
            mn, mx = dates.min(), dates.max()
            in_range = mn >= DATE_START and mx <= DATE_END
            status = "PASS" if in_range else "FAIL"
            checks.append((name, "date_range", status))
            print(f"    date range: {mn.date()} to {mx.date()} — {status}")

    # Summary
    total = len(checks)
    passed = sum(1 for _, _, s in checks if s == "PASS")
    failed = sum(1 for _, _, s in checks if s == "FAIL")

    print("\n" + "=" * 60)
    print(f"SUMMARY: {passed}/{total} checks passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        print("\nFailed checks:")
        for name, check, status in checks:
            if status == "FAIL":
                print(f"  FAIL: {name} / {check}")

    return failed == 0


def main():
    start = time.time()

    # 1. Build dimensions first
    build_all_dimensions()

    # 2. Run all 6 fact transforms
    print("\n" + "=" * 60)
    print("BUILDING FACT TABLES")
    print("=" * 60)

    transform_ooh()
    transform_organic_social()
    transform_podcast()
    transform_paid_social()
    transform_ecommerce()
    transform_web_analytics()

    # 3. Validate
    all_ok = validate_outputs()

    elapsed = time.time() - start
    print(f"\nTotal elapsed: {elapsed:.1f}s")
    print(f"Pipeline status: {'SUCCESS' if all_ok else 'FAILURE'}")


if __name__ == "__main__":
    main()
