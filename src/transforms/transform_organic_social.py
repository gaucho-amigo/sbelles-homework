"""Transform organic social (owned TikTok) data: aggregate post-level to daily."""

import pandas as pd
from src.transforms.utils import (
    DATA_DIR, WAREHOUSE_DIR, read_csv, log_step, validate_date_range,
)


def transform_organic_social():
    """Read 2 CSVs, concat, aggregate to daily grain by date."""
    print("\n=== fact_organic_social_daily ===")

    files = sorted(DATA_DIR.glob("sBelles_tiktok_owned_*.csv"))
    dfs = [read_csv(f, date_cols=["date"]) for f in files]
    rows_in = sum(len(d) for d in dfs)
    df = pd.concat(dfs, ignore_index=True)

    # Aggregate to daily grain
    agg = df.groupby("date").agg(
        posts=("post_id", "nunique"),
        followers_eod=("followers", "max"),
        impressions=("impressions", "sum"),
        video_views=("video_views", "sum"),
        video_completes=("video_completes", "sum"),
        likes=("likes", "sum"),
        comments=("comments", "sum"),
        shares=("shares", "sum"),
        clicks=("clicks", "sum"),
        saves=("saves", "sum"),
    ).reset_index()

    agg = agg.sort_values("date").reset_index(drop=True)
    mn, mx = validate_date_range(agg, "date")

    out = WAREHOUSE_DIR / "fact_organic_social" / "fact_organic_social_daily.csv"
    agg.to_csv(out, index=False)
    log_step("fact_organic_social_daily", rows_in, len(agg),
             actions=[f"aggregated {rows_in} post-level rows to {len(agg)} daily rows",
                      "followers_eod = MAX(followers) per day",
                      "all other metrics summed"],
             date_range=(str(mn.date()), str(mx.date())))
    return agg


if __name__ == "__main__":
    transform_organic_social()
