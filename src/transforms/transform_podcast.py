"""Transform podcast mention data: group by (date, podcast_name, episode_title)."""

import pandas as pd
from src.transforms.utils import (
    DATA_DIR, WAREHOUSE_DIR, read_csv, log_step, validate_date_range,
)


def transform_podcast():
    """Read 2 CSVs, concat, derive date, group by (date, podcast_name, episode_title)."""
    print("\n=== fact_podcast_daily ===")

    files = sorted(DATA_DIR.glob("sBelles_podcast_mentions_*.csv"))
    dfs = [read_csv(f, date_cols=["mention_datetime", "episode_release_date"]) for f in files]
    rows_in = sum(len(d) for d in dfs)
    df = pd.concat(dfs, ignore_index=True)

    # Derive date from mention_datetime
    df["date"] = df["mention_datetime"].dt.normalize()

    # Group by grain
    groupby_cols = ["date", "podcast_name", "episode_title"]
    agg = df.groupby(groupby_cols).agg(
        host_name=("host_name", "first"),
        mentions_brand=("mentions_brand", "max"),
        mentions_founder=("mentions_founder", "max"),
        sentiment=("sentiment", "first"),
        estimated_impressions=("estimated_impressions", "sum"),
        episode_rating=("episode_rating", "first"),
        mentions=("podcast_name", "count"),
    ).reset_index()

    agg = agg.sort_values(["date", "podcast_name"]).reset_index(drop=True)
    mn, mx = validate_date_range(agg, "date")

    out = WAREHOUSE_DIR / "fact_podcast" / "fact_podcast_daily.csv"
    agg.to_csv(out, index=False)
    log_step("fact_podcast_daily", rows_in, len(agg),
             actions=[f"grouped {rows_in} mention rows to {len(agg)} episode-date rows",
                      "mentions_brand/founder: MAX (binary flags)",
                      "estimated_impressions: SUM",
                      f"multi-mention episodes: {(agg['mentions'] > 1).sum()}"],
             date_range=(str(mn.date()), str(mx.date())))
    return agg


if __name__ == "__main__":
    transform_podcast()
