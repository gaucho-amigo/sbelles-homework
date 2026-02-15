"""Transform paid social data: union 9 CSVs with schema drift resolution."""

import pandas as pd
from src.transforms.utils import (
    DATA_DIR, WAREHOUSE_DIR, read_csv, log_step, validate_date_range,
)

# Target column order for the fact table
TARGET_COLS = [
    "date", "channel", "campaign_name", "campaign_id", "dma_name", "state",
    "spend", "impressions", "clicks", "video_views",
    "video_25pct", "video_50pct", "video_75pct", "video_completes",
    "optimization_goal", "age_target", "audience_segment",
]


def _resolve_schema_drift(df, filename):
    """Resolve known schema drift issues per source-to-target mapping."""
    fname = filename.lower()

    if "instagram_part3" in fname:
        # spend_usd -> spend, drop spend_currency
        if "spend_usd" in df.columns:
            df = df.rename(columns={"spend_usd": "spend"})
        if "spend_currency" in df.columns:
            df = df.drop(columns=["spend_currency"])

    if "pinterest_part1" in fname:
        # link_clicks -> clicks, fill missing video_25pct/video_50pct
        if "link_clicks" in df.columns:
            df = df.rename(columns={"link_clicks": "clicks"})
        for col in ["video_25pct", "video_50pct"]:
            if col not in df.columns:
                df[col] = pd.NA

    if "tiktok_part2" in fname:
        # views -> video_views, fill missing optimization_goal
        if "views" in df.columns:
            df = df.rename(columns={"views": "video_views"})
        if "optimization_goal" not in df.columns:
            df["optimization_goal"] = pd.NA

    return df


def transform_paid_social():
    """Read 9 CSVs, resolve schema drift, concat, verify grain, write."""
    print("\n=== fact_paid_social_daily ===")

    files = sorted(DATA_DIR.glob("sBelles_paid_*.csv"))
    dfs = []
    for f in files:
        df = read_csv(f, date_cols=["date"])
        df = _resolve_schema_drift(df, f.name)
        dfs.append(df)

    rows_in = sum(len(d) for d in dfs)
    result = pd.concat(dfs, ignore_index=True)

    # Ensure all target columns exist
    for col in TARGET_COLS:
        if col not in result.columns:
            result[col] = pd.NA

    result = result[TARGET_COLS]

    # Verify grain: (date, channel, campaign_id, dma_name) should be unique
    grain_cols = ["date", "channel", "campaign_id", "dma_name"]
    dupes = result.duplicated(subset=grain_cols, keep=False).sum()
    grain_ok = dupes == 0

    result = result.sort_values(["date", "channel", "campaign_id", "dma_name"]).reset_index(drop=True)
    mn, mx = validate_date_range(result, "date")

    out = WAREHOUSE_DIR / "fact_paid_social" / "fact_paid_social_daily.csv"
    result.to_csv(out, index=False)
    log_step("fact_paid_social_daily", rows_in, len(result),
             actions=[f"unioned {len(files)} files",
                      "schema drift resolved (3 files)",
                      f"grain check (date,channel,campaign_id,dma_name): {'PASS' if grain_ok else f'FAIL ({dupes} dupes)'}"],
             date_range=(str(mn.date()), str(mx.date())))
    return result


if __name__ == "__main__":
    transform_paid_social()
