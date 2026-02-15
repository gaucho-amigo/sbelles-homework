"""Build the 5 dimension tables for the S'Belles data warehouse."""

import pandas as pd
from src.transforms.utils import (
    DATA_DIR, WAREHOUSE_DIR, REFERENCE_DIR, read_csv, log_step,
    DATE_START, DATE_END,
)

DIM_DIR = WAREHOUSE_DIR / "dimensions"


def build_dim_date():
    """dim_date: 547 rows, 2023-01-01 to 2024-06-30."""
    print("\n=== dim_date ===")
    dates = pd.date_range(DATE_START, DATE_END, freq="D")
    df = pd.DataFrame({"date": dates})
    df["day_of_week"] = df["date"].dt.day_name()
    df["day_of_week_num"] = df["date"].dt.isocalendar().day.astype(int)
    df["week_start_date"] = df["date"] - pd.to_timedelta(
        df["day_of_week_num"] - 1, unit="D"
    )
    df["month"] = df["date"].dt.month
    df["month_name"] = df["date"].dt.month_name()
    df["quarter"] = df["date"].dt.quarter
    df["year"] = df["date"].dt.year
    df["is_weekend"] = df["day_of_week_num"].isin([6, 7])

    def _season(d):
        md = (d.month, d.day)
        if (7, 15) <= md <= (9, 15):
            return "back_to_school"
        if (11, 15) <= md <= (12, 10):
            return "black_friday_holiday"
        return "regular"

    df["season_flag"] = df["date"].apply(_season)

    out = DIM_DIR / "dim_date.csv"
    df.to_csv(out, index=False)
    log_step("dim_date", len(df), len(df),
             actions=[f"season_flag distribution: {df['season_flag'].value_counts().to_dict()}"],
             date_range=(str(df["date"].min().date()), str(df["date"].max().date())))
    return df


def build_dim_geography():
    """dim_geography: collect unique geos from all sources + airport lookup."""
    print("\n=== dim_geography ===")
    rows = []

    # --- Local geos from paid social, web, ecommerce ---
    local_files = (
        list(DATA_DIR.glob("sBelles_paid_*.csv"))
        + list(DATA_DIR.glob("sBelles_web_*.csv"))
        + list(DATA_DIR.glob("sBelles_transactions_*.csv"))
    )
    local_geos = set()
    for f in local_files:
        df = read_csv(f)
        if "dma_name" in df.columns and "state" in df.columns:
            pairs = df[["dma_name", "state"]].drop_duplicates()
            for _, r in pairs.iterrows():
                local_geos.add((r["dma_name"], r["state"]))

    for dma, state in sorted(local_geos):
        rows.append({
            "dma_name": dma, "state": state,
            "zip_code": None, "airport_code": None, "airport_name": None,
            "geo_scope": "local",
        })

    # --- National geos from OOH + airport_lookup ---
    airport_ref = read_csv(REFERENCE_DIR / "airport_lookup.csv")
    ooh = read_csv(DATA_DIR / "sBelles_ooh_airport_weekly.csv")
    ooh_airports = ooh[["airport_code", "airport_name"]].drop_duplicates()

    for _, r in ooh_airports.iterrows():
        match = airport_ref[airport_ref["iata_code"] == r["airport_code"]]
        state = match["state"].iloc[0] if len(match) else None
        rows.append({
            "dma_name": None, "state": state,
            "zip_code": None,
            "airport_code": r["airport_code"],
            "airport_name": r["airport_name"],
            "geo_scope": "national",
        })

    # --- Inferred geos from podcast ---
    podcast_names = set()
    for f in DATA_DIR.glob("sBelles_podcast_*.csv"):
        df = read_csv(f)
        podcast_names.update(df["podcast_name"].unique())

    ga_keywords = ["GA", "ATL", "Peach State"]
    for name in sorted(podcast_names):
        state = "GA" if any(kw in name for kw in ga_keywords) else None
        rows.append({
            "dma_name": None, "state": state,
            "zip_code": None, "airport_code": None, "airport_name": None,
            "geo_scope": "inferred",
        })

    dim = pd.DataFrame(rows)
    dim.insert(0, "geo_key", range(1, len(dim) + 1))

    out = DIM_DIR / "dim_geography.csv"
    dim.to_csv(out, index=False)
    log_step("dim_geography", 0, len(dim),
             actions=[f"local: {(dim['geo_scope']=='local').sum()}, "
                      f"national: {(dim['geo_scope']=='national').sum()}, "
                      f"inferred: {(dim['geo_scope']=='inferred').sum()}"])
    return dim


def build_dim_channel():
    """dim_channel: 7 hardcoded rows."""
    print("\n=== dim_channel ===")
    data = [
        (1, "instagram", "paid_social", True),
        (2, "pinterest", "paid_social", True),
        (3, "tiktok", "paid_social", True),
        (4, "organic_tiktok", "organic_social", False),
        (5, "web", "web_analytics", False),
        (6, "podcast", "earned_media", False),
        (7, "ooh_airport", "ooh", True),
    ]
    df = pd.DataFrame(data, columns=["channel_key", "channel_name", "channel_group", "is_paid"])
    out = DIM_DIR / "dim_channel.csv"
    df.to_csv(out, index=False)
    log_step("dim_channel", 7, 7)
    return df


def build_dim_campaign_initiative():
    """dim_campaign_initiative: 6-row bridge table."""
    print("\n=== dim_campaign_initiative ===")
    data = [
        (1, "Always On",
         "Instagram Always On, Pinterest Always On, TikTok Always On",
         "Always On",
         "Direct theme match across both streams"),
        (2, "BTS",
         "Instagram BTS Moms, Pinterest BTS Moms, TikTok BTS Moms",
         "BTS 2023, BTS 2024",
         "Web uses year-suffixed variants"),
        (3, "Teen Trends",
         "Instagram Teen Trends, Pinterest Teen Trends, TikTok Teen Trends",
         None,
         "No web analytics counterpart found"),
        (4, "Black Friday",
         None,
         "Black Friday 2023",
         "Web/promo only — no paid social campaign"),
        (5, "Email Promo",
         None,
         "Email Promo",
         "Web/promo only — no paid social campaign"),
        (6, "Unattributed",
         None,
         "None",
         "Web traffic with explicit 'None' campaign value"),
    ]
    df = pd.DataFrame(data, columns=[
        "initiative_key", "initiative_name",
        "paid_social_campaign_pattern", "web_analytics_campaign_value", "notes",
    ])
    out = DIM_DIR / "dim_campaign_initiative.csv"
    df.to_csv(out, index=False)
    log_step("dim_campaign_initiative", 6, 6)
    return df


def build_dim_podcast():
    """dim_podcast: 5 rows with geo_inferred logic."""
    print("\n=== dim_podcast ===")
    podcasts = [
        (1, "Carpool Chronicles GA", "explicit", "GA"),
        (2, "Mom Life in the ATL", "explicit", "GA"),
        (3, "Peach State Parenting", "explicit", "GA"),
        (4, "Suburban Style Chats", "unknown", None),
        (5, "Teen Trend Watch", "unknown", None),
    ]
    df = pd.DataFrame(podcasts, columns=["podcast_key", "podcast_name", "geo_inferred", "geo_state"])
    out = DIM_DIR / "dim_podcast.csv"
    df.to_csv(out, index=False)
    log_step("dim_podcast", 5, 5)
    return df


def build_all_dimensions():
    """Build all dimension tables."""
    print("=" * 60)
    print("BUILDING DIMENSION TABLES")
    print("=" * 60)
    build_dim_date()
    build_dim_geography()
    build_dim_channel()
    build_dim_campaign_initiative()
    build_dim_podcast()
    print("\nAll dimensions built.\n")


if __name__ == "__main__":
    build_all_dimensions()
