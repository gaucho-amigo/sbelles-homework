"""Transform web analytics data: dedup, aggregate events to daily grain."""

import pandas as pd
from src.transforms.utils import (
    DATA_DIR, WAREHOUSE_DIR, read_csv, log_step, validate_date_range,
)


def transform_web_analytics():
    """Read 4 CSVs, drop Dec 2023 from Q1 2024 file, concat,
    aggregate to daily grain by (date, traffic_source, traffic_medium,
    campaign, device_category, dma_name, state)."""
    print("\n=== fact_web_analytics_daily ===")

    file_map = {
        "q1q2_23": DATA_DIR / "sBelles_web_traffic_2023_Q1_Q2.csv",
        "q3q4_23": DATA_DIR / "sBelles_web_traffic_2023_Q3_Q4.csv",
        "q1_24":   DATA_DIR / "sBelles_web_traffic_2024_Q1.csv",
        "q2_24":   DATA_DIR / "sBelles_web_traffic_2024_Q2.csv",
    }

    dfs = {}
    for key, path in file_map.items():
        dfs[key] = read_csv(path, date_cols=["event_datetime"])

    rows_in = sum(len(d) for d in dfs.values())

    # Dedup: drop Dec 2023 rows from Q1 2024 file
    q1_24 = dfs["q1_24"]
    dec_mask = q1_24["event_datetime"].dt.year.eq(2023) & q1_24["event_datetime"].dt.month.eq(12)
    dec_dropped = dec_mask.sum()
    dfs["q1_24"] = q1_24[~dec_mask]

    df = pd.concat(dfs.values(), ignore_index=True)
    rows_after_dedup = len(df)

    # Derive date
    df["date"] = df["event_datetime"].dt.normalize()

    # Aggregate to daily grain
    groupby_cols = ["date", "traffic_source", "traffic_medium", "campaign",
                    "device_category", "dma_name", "state"]
    agg = df.groupby(groupby_cols, dropna=False).agg(
        pageviews=("event_datetime", "count"),
        sessions=("session_id", "nunique"),
        users=("user_id", "nunique"),
    ).reset_index()

    agg = agg.sort_values(["date", "traffic_source", "dma_name"]).reset_index(drop=True)
    mn, mx = validate_date_range(agg, "date")

    out = WAREHOUSE_DIR / "fact_web_analytics" / "fact_web_analytics_daily.csv"
    agg.to_csv(out, index=False)
    log_step("fact_web_analytics_daily", rows_in, len(agg),
             actions=[f"dropped {dec_dropped} Dec 2023 rows from Q1 2024 file",
                      f"rows after dedup: {rows_after_dedup:,}",
                      f"aggregated events to {len(agg):,} daily rows",
                      "groupby: date, traffic_source, traffic_medium, campaign, device_category, dma_name, state"],
             date_range=(str(mn.date()), str(mx.date())))
    return agg


if __name__ == "__main__":
    transform_web_analytics()
