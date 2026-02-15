"""Shared utilities for S'Belles ETL pipeline."""

import pathlib
import pandas as pd

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
WAREHOUSE_DIR = PROJECT_ROOT / "data_warehouse"
REFERENCE_DIR = PROJECT_ROOT / "reference_data"

DATE_START = pd.Timestamp("2023-01-01")
DATE_END = pd.Timestamp("2024-06-30")


def read_csv(path, date_cols=None):
    """Read CSV, standardize column names (lowercase, strip), parse dates."""
    df = pd.read_csv(path, parse_dates=date_cols or [])
    df.columns = df.columns.str.strip().str.lower()
    return df


def log_step(step, rows_in, rows_out, actions=None, date_range=None):
    """Structured print for pipeline logging."""
    print(f"  [{step}]")
    print(f"    rows in:  {rows_in:,}")
    print(f"    rows out: {rows_out:,}")
    if actions:
        for a in actions:
            print(f"    -> {a}")
    if date_range:
        print(f"    date range: {date_range[0]} to {date_range[1]}")


def validate_date_range(df, date_col, start=DATE_START, end=DATE_END):
    """Assert all dates within expected range."""
    dates = pd.to_datetime(df[date_col])
    mn, mx = dates.min(), dates.max()
    if mn < start or mx > end:
        raise ValueError(
            f"Date range violation: {mn} to {mx} "
            f"(expected {start} to {end})"
        )
    return mn, mx
