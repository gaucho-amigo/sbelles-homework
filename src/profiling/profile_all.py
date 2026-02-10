"""
Phase 0 – Data Profiling & Inventory
Reads every CSV in data/, profiles columns, detects schema drift and known
data traps, and writes a summary to output/profiling/file_inventory.csv.
"""

import os
import warnings
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output" / "profiling"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_date_columns(df: pd.DataFrame) -> list[str]:
    """Return column names that look like dates/datetimes."""
    date_cols = []
    for col in df.columns:
        if df[col].dtype == "object":
            sample = df[col].dropna().head(50)
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    pd.to_datetime(sample)
                date_cols.append(col)
            except (ValueError, TypeError):
                continue
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
    return date_cols


def infer_granularity(df: pd.DataFrame, date_cols: list[str]) -> str:
    """Guess event-level / daily / weekly / monthly from date column values."""
    if not date_cols:
        return "unknown"
    col = date_cols[0]
    series = pd.to_datetime(df[col], errors="coerce").dropna().sort_values()
    if series.empty:
        return "unknown"

    # If timestamps have non-midnight times → event-level
    if (series.dt.hour != 0).any() or (series.dt.minute != 0).any():
        return "event-level"

    # Use distinct dates to avoid being fooled by repeated dates (e.g. one
    # row per airport per week)
    distinct = series.dt.normalize().drop_duplicates().sort_values()
    diffs = distinct.diff().dropna()
    if diffs.empty:
        return "unknown"
    median_days = diffs.dt.days.median()
    if median_days <= 1:
        return "daily"
    if 5 <= median_days <= 9:
        return "weekly"
    if 25 <= median_days <= 35:
        return "monthly"
    return f"~{int(median_days)}-day"


def profile_numeric(series: pd.Series) -> dict:
    """Compute summary stats for a numeric column."""
    return {
        "min": series.min(),
        "max": series.max(),
        "mean": round(series.mean(), 2),
        "median": round(series.median(), 2),
    }


def profile_categorical(series: pd.Series) -> dict:
    """Compute summary stats for a string/categorical column."""
    top = series.value_counts().head(5)
    return {
        "unique_count": series.nunique(),
        "top_5": list(top.index),
    }


def profile_date_column(series: pd.Series) -> dict:
    """Compute date range and gap info for a date column."""
    dt = pd.to_datetime(series, errors="coerce").dropna().sort_values()
    if dt.empty:
        return {"min": None, "max": None, "distinct_dates": 0, "gaps": []}
    dates = dt.dt.date
    distinct = dates.nunique()
    date_range = pd.date_range(dates.min(), dates.max(), freq="D")
    present = set(dates.unique())
    missing = sorted(set(d.date() for d in date_range) - set(present))
    return {
        "min": str(dates.min()),
        "max": str(dates.max()),
        "distinct_dates": distinct,
        "missing_date_count": len(missing),
    }


# ---------------------------------------------------------------------------
# Per-file profiling
# ---------------------------------------------------------------------------

def profile_file(filepath: Path) -> dict:
    """Profile a single CSV file and return a summary dict."""
    df = pd.read_csv(filepath, low_memory=False)
    size_bytes = filepath.stat().st_size
    date_cols = detect_date_columns(df)
    granularity = infer_granularity(df, date_cols)

    # Date range from first detected date column
    date_info = {}
    if date_cols:
        date_info = profile_date_column(df[date_cols[0]])

    # Null summary
    null_counts = df.isnull().sum()
    total_nulls = int(null_counts.sum())

    # Per-column detail
    column_profiles = []
    for col in df.columns:
        col_info = {
            "column": col,
            "dtype": str(df[col].dtype),
            "null_count": int(df[col].isnull().sum()),
            "null_pct": round(df[col].isnull().mean() * 100, 2),
        }
        if col in date_cols:
            col_info["role"] = "date"
            col_info.update(profile_date_column(df[col]))
        elif pd.api.types.is_numeric_dtype(df[col]):
            col_info["role"] = "numeric"
            col_info.update(profile_numeric(df[col]))
        else:
            col_info["role"] = "categorical"
            col_info.update(profile_categorical(df[col]))
        column_profiles.append(col_info)

    return {
        "filename": filepath.name,
        "path": str(filepath.relative_to(PROJECT_ROOT)),
        "format": filepath.suffix,
        "size_bytes": size_bytes,
        "rows": len(df),
        "cols": len(df.columns),
        "columns": list(df.columns),
        "date_columns": date_cols,
        "date_min": date_info.get("min"),
        "date_max": date_info.get("max"),
        "distinct_dates": date_info.get("distinct_dates"),
        "missing_date_count": date_info.get("missing_date_count"),
        "granularity": granularity,
        "total_nulls": total_nulls,
        "column_profiles": column_profiles,
    }


# ---------------------------------------------------------------------------
# Schema drift detection
# ---------------------------------------------------------------------------

DATASTREAM_MAP = {
    "paid_instagram": "paid_social",
    "paid_pinterest": "paid_social",
    "paid_tiktok": "paid_social",
    "web_traffic": "web_analytics",
    "transactions": "ecommerce",
    "tiktok_owned": "organic_social",
    "podcast_mentions": "podcast",
    "ooh_airport": "ooh",
}


def classify_file(filename: str) -> str:
    """Map a filename to a datastream key."""
    fname = filename.lower()
    for key in DATASTREAM_MAP:
        if key in fname:
            return key
    return "unknown"


def detect_schema_drift(profiles: list[dict]) -> dict:
    """Group files by datastream and compare column sets."""
    groups: dict[str, list[dict]] = {}
    for p in profiles:
        key = classify_file(p["filename"])
        groups.setdefault(key, []).append(p)

    drift_report = {}
    for key, group in groups.items():
        if len(group) < 2:
            continue
        col_sets = {p["filename"]: set(p["columns"]) for p in group}
        all_cols = set().union(*col_sets.values())
        common = set.intersection(*col_sets.values())
        diffs = all_cols - common
        if diffs:
            detail = {}
            for col in sorted(diffs):
                present_in = [f for f, cs in col_sets.items() if col in cs]
                absent_from = [f for f, cs in col_sets.items() if col not in cs]
                detail[col] = {"present_in": present_in, "absent_from": absent_from}
            drift_report[key] = {
                "files": [p["filename"] for p in group],
                "common_columns": sorted(common),
                "differing_columns": detail,
            }
    return drift_report


# ---------------------------------------------------------------------------
# Web analytics overlap detection
# ---------------------------------------------------------------------------

def detect_web_overlap(profiles: list[dict]) -> dict | None:
    """Check for date overlap between web_traffic files."""
    web_files = [p for p in profiles if classify_file(p["filename"]) == "web_traffic"]
    if len(web_files) < 2:
        return None

    ranges = {}
    for p in web_files:
        if p["date_min"] and p["date_max"]:
            ranges[p["filename"]] = (
                pd.Timestamp(p["date_min"]),
                pd.Timestamp(p["date_max"]),
            )

    overlaps = []
    filenames = list(ranges.keys())
    for i in range(len(filenames)):
        for j in range(i + 1, len(filenames)):
            a_start, a_end = ranges[filenames[i]]
            b_start, b_end = ranges[filenames[j]]
            overlap_start = max(a_start, b_start)
            overlap_end = min(a_end, b_end)
            if overlap_start <= overlap_end:
                # Count rows in overlap window for each file
                row_counts = {}
                for fname in [filenames[i], filenames[j]]:
                    df = pd.read_csv(DATA_DIR / fname, low_memory=False)
                    date_col = [c for c in df.columns if "date" in c.lower()][0]
                    dt = pd.to_datetime(df[date_col], errors="coerce")
                    mask = (dt >= overlap_start) & (dt <= overlap_end)
                    row_counts[fname] = int(mask.sum())
                overlaps.append({
                    "file_a": filenames[i],
                    "file_b": filenames[j],
                    "overlap_start": str(overlap_start.date()),
                    "overlap_end": str(overlap_end.date()),
                    "rows_in_overlap": row_counts,
                })
    return overlaps if overlaps else None


# ---------------------------------------------------------------------------
# Print summary
# ---------------------------------------------------------------------------

def print_summary(profiles: list[dict], drift: dict, overlaps) -> None:
    """Print a human-readable summary to stdout."""
    print("=" * 80)
    print("S'BELLES DATA PROFILING SUMMARY")
    print("=" * 80)

    print(f"\nFiles profiled: {len(profiles)}")
    total_rows = sum(p["rows"] for p in profiles)
    print(f"Total rows across all files: {total_rows:,}")
    print()

    # File inventory table
    header = f"{'Filename':<55} {'Rows':>7} {'Cols':>4} {'Date Range':<25} {'Granularity':<14} {'Stream'}"
    print(header)
    print("-" * len(header))
    for p in profiles:
        drange = f"{p['date_min'] or '?'} → {p['date_max'] or '?'}"
        stream = DATASTREAM_MAP.get(classify_file(p["filename"]), "?")
        print(f"{p['filename']:<55} {p['rows']:>7,} {p['cols']:>4} {drange:<25} {p['granularity']:<14} {stream}")

    # Schema drift
    if drift:
        print("\n" + "=" * 80)
        print("SCHEMA DRIFT DETECTED")
        print("=" * 80)
        for key, info in drift.items():
            print(f"\n  [{key}]")
            for col, detail in info["differing_columns"].items():
                print(f"    Column '{col}':")
                print(f"      Present in:  {', '.join(detail['present_in'])}")
                print(f"      Absent from: {', '.join(detail['absent_from'])}")

    # Overlaps
    if overlaps:
        print("\n" + "=" * 80)
        print("DATE OVERLAPS DETECTED")
        print("=" * 80)
        for o in overlaps:
            print(f"\n  {o['file_a']}  ↔  {o['file_b']}")
            print(f"    Overlap window: {o['overlap_start']} → {o['overlap_end']}")
            for fname, cnt in o["rows_in_overlap"].items():
                print(f"    Rows in overlap ({fname}): {cnt:,}")

    print()


# ---------------------------------------------------------------------------
# Save inventory CSV
# ---------------------------------------------------------------------------

def save_inventory(profiles: list[dict], output_path: Path) -> None:
    """Save one-row-per-file summary CSV."""
    rows = []
    for p in profiles:
        rows.append({
            "filename": p["filename"],
            "path": p["path"],
            "format": p["format"],
            "size_bytes": p["size_bytes"],
            "rows": p["rows"],
            "cols": p["cols"],
            "columns": "; ".join(p["columns"]),
            "date_columns": "; ".join(p["date_columns"]),
            "date_min": p["date_min"],
            "date_max": p["date_max"],
            "distinct_dates": p["distinct_dates"],
            "missing_date_count": p["missing_date_count"],
            "granularity": p["granularity"],
            "total_nulls": p["total_nulls"],
            "datastream": classify_file(p["filename"]),
            "stream_group": DATASTREAM_MAP.get(classify_file(p["filename"]), "unknown"),
        })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, index=False)
    print(f"Inventory saved to {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    csv_files = sorted(DATA_DIR.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in", DATA_DIR)
        return

    print(f"Found {len(csv_files)} CSV files in {DATA_DIR}\n")

    profiles = []
    for f in csv_files:
        print(f"  Profiling {f.name} ...")
        profiles.append(profile_file(f))

    drift = detect_schema_drift(profiles)
    overlaps = detect_web_overlap(profiles)

    print_summary(profiles, drift, overlaps)
    save_inventory(profiles, OUTPUT_DIR / "file_inventory.csv")

    return profiles, drift, overlaps


if __name__ == "__main__":
    main()
