"""Final submission validation for SBelles_Assessment_Final/ directory."""

import pathlib
import pandas as pd

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
SUBMISSION_DIR = PROJECT_ROOT / "SBelles_Assessment_Final"

# Expected row counts for every CSV
EXPECTED_ROWS = {
    "paid_social/fact_paid_social_daily.csv": 24_615,
    "web_analytics/fact_web_analytics_daily.csv": 46_818,
    "web_analytics/fact_web_analytics_events.csv": 51_234,
    "ecommerce/fact_ecommerce_daily.csv": 14_800,
    "ecommerce/fact_ecommerce_transactions.csv": 17_106,
    "organic_social/fact_organic_social_daily.csv": 441,
    "podcast/fact_podcast_daily.csv": 85,
    "ooh/fact_ooh_daily.csv": 10_920,
    "dimensions/dim_date.csv": 547,
    "dimensions/dim_geography.csv": 30,
    "dimensions/dim_channel.csv": 7,
    "dimensions/dim_campaign_initiative.csv": 6,
    "dimensions/dim_podcast.csv": 5,
}

# Financial reconciliation targets
FINANCIAL_CHECKS = {
    "paid_social/fact_paid_social_daily.csv": ("spend", 5_986_609.08),
    "ooh/fact_ooh_daily.csv": ("spend", 29_519_757.25),
    "ecommerce/fact_ecommerce_daily.csv": ("gross_revenue", 498_071.00),
}

TOLERANCE = 0.01

DATE_START = pd.Timestamp("2023-01-01")
DATE_END = pd.Timestamp("2024-06-30")


def run_checks():
    """Run all submission checks. Returns (passed, total) counts."""
    results = []  # list of (description, pass/fail bool)

    print("=" * 60)
    print("SUBMISSION VALIDATION — SBelles_Assessment_Final/")
    print("=" * 60)

    # ------------------------------------------------------------------
    # 1. CSV file checks: existence, non-empty, row count, date range
    # ------------------------------------------------------------------
    print("\n--- CSV File Checks ---\n")

    for rel_path, expected_rows in EXPECTED_ROWS.items():
        full_path = SUBMISSION_DIR / rel_path
        label = rel_path

        # Exists and not empty
        exists = full_path.exists() and full_path.stat().st_size > 0
        results.append((f"{label} exists & non-empty", exists))
        if not exists:
            print(f"  FAIL  {label} — file missing or empty")
            continue

        df = pd.read_csv(full_path)
        rows, cols = df.shape
        print(f"  {label}: {rows:,} rows x {cols} cols", end="")

        # Row count
        row_ok = rows == expected_rows
        results.append((f"{label} row count ({expected_rows:,})", row_ok))
        if not row_ok:
            print(f"  FAIL (expected {expected_rows:,})")
        else:
            print(f"  PASS")

        # Date range (if 'date' column present)
        if "date" in df.columns:
            dates = pd.to_datetime(df["date"])
            mn, mx = dates.min(), dates.max()
            in_range = mn >= DATE_START and mx <= DATE_END
            results.append((f"{label} date range", in_range))
            if not in_range:
                print(f"         date range FAIL: {mn.date()} to {mx.date()}")

    # ------------------------------------------------------------------
    # 2. Documentation file checks
    # ------------------------------------------------------------------
    print("\n--- Documentation Checks ---\n")

    doc_files = {
        "documentation/schema_dictionary.md": True,   # must be non-empty
        "documentation/transformation_notes.md": True,
        "documentation/assumptions.md": True,
        "documentation/final_data_model_diagram.png": False,  # just exists
        "README.md": True,
    }

    for rel_path, check_content in doc_files.items():
        full_path = SUBMISSION_DIR / rel_path
        exists = full_path.exists()
        if check_content:
            ok = exists and full_path.stat().st_size > 0
            desc = f"{rel_path} exists & non-empty"
        else:
            ok = exists
            desc = f"{rel_path} exists"
        results.append((desc, ok))
        print(f"  {'PASS' if ok else 'FAIL'}  {desc}")

    # ------------------------------------------------------------------
    # 3. Financial reconciliation
    # ------------------------------------------------------------------
    print("\n--- Financial Reconciliation ---\n")

    for rel_path, (col, expected) in FINANCIAL_CHECKS.items():
        full_path = SUBMISSION_DIR / rel_path
        if not full_path.exists():
            results.append((f"{rel_path} {col} reconciliation", False))
            print(f"  FAIL  {rel_path} — file missing")
            continue

        df = pd.read_csv(full_path)
        actual = df[col].sum()
        match = abs(actual - expected) <= TOLERANCE
        results.append((f"{rel_path} {col} = ${expected:,.2f}", match))
        print(f"  {'PASS' if match else 'FAIL'}  {col} in {rel_path}")
        print(f"         expected ${expected:,.2f}  actual ${actual:,.2f}  diff ${abs(actual - expected):,.2f}")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    failed = total - passed

    print("\n" + "=" * 60)
    print(f"FINAL RESULT: {passed}/{total} checks passed, {failed} failed")
    print("=" * 60)

    if failed:
        print("\nFailed checks:")
        for desc, ok in results:
            if not ok:
                print(f"  FAIL: {desc}")
    else:
        print("\nAll checks PASSED.")

    return passed, total


def main():
    run_checks()


if __name__ == "__main__":
    main()
