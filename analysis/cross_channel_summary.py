"""Build a single cross-channel daily summary table from six fact tables and dim_date.

Reads from data_warehouse/ only. Writes analysis/output/cross_channel_daily.csv.
"""

import pathlib
import pandas as pd

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
WAREHOUSE = PROJECT_ROOT / "data_warehouse"
OUTPUT = PROJECT_ROOT / "analysis" / "output"


def _read(path):
    df = pd.read_csv(path, parse_dates=["date"])
    df.columns = df.columns.str.strip().str.lower()
    return df


def build_summary():
    """Build 547-row cross-channel daily summary and write to CSV."""

    # ----- dim_date spine -----
    dim_date = _read(WAREHOUSE / "dimensions" / "dim_date.csv")
    spine = dim_date[["date", "day_of_week", "season_flag", "is_weekend",
                       "month", "quarter", "year"]].copy()

    # ----- paid social -----
    ps = _read(WAREHOUSE / "fact_paid_social" / "fact_paid_social_daily.csv")
    ps_daily = (ps.groupby("date", as_index=False)
                .agg(paid_social_spend=("spend", "sum"),
                     paid_social_impressions=("impressions", "sum"),
                     paid_social_clicks=("clicks", "sum"),
                     paid_social_video_views=("video_views", "sum")))

    # ----- web analytics -----
    wa = _read(WAREHOUSE / "fact_web_analytics" / "fact_web_analytics_daily.csv")
    wa_daily = (wa.groupby("date", as_index=False)
                .agg(web_pageviews=("pageviews", "sum"),
                     web_sessions=("sessions", "sum"),
                     web_users=("users", "sum")))

    # ----- ecommerce -----
    ec = _read(WAREHOUSE / "fact_ecommerce" / "fact_ecommerce_daily.csv")
    ec_daily = (ec.groupby("date", as_index=False)
                .agg(ecomm_revenue=("gross_revenue", "sum"),
                     ecomm_orders=("orders", "sum"),
                     ecomm_units=("total_quantity", "sum"),
                     ecomm_discount=("total_discount", "sum")))

    # ----- organic social -----
    org = _read(WAREHOUSE / "fact_organic_social" / "fact_organic_social_daily.csv")
    org_daily = (org.groupby("date", as_index=False)
                 .agg(followers_eod=("followers_eod", "first"),
                      organic_impressions=("impressions", "sum"),
                      organic_likes=("likes", "sum"),
                      organic_shares=("shares", "sum"),
                      organic_comments=("comments", "sum")))

    # ----- podcast -----
    pod = _read(WAREHOUSE / "fact_podcast" / "fact_podcast_daily.csv")
    pod_daily = (pod.groupby("date", as_index=False)
                 .agg(podcast_mentions=("mentions", "sum"),
                      podcast_impressions=("estimated_impressions", "sum")))

    # ----- out-of-home -----
    ooh = _read(WAREHOUSE / "fact_ooh" / "fact_ooh_daily.csv")
    # Column names from exploration: spend, impressions (already daily after Phase 2 expansion)
    spend_col = "spend_daily" if "spend_daily" in ooh.columns else "spend"
    imp_col = "impressions_daily" if "impressions_daily" in ooh.columns else "impressions"
    ooh_daily = (ooh.groupby("date", as_index=False)
                 .agg(ooh_spend=(spend_col, "sum"),
                      ooh_impressions=(imp_col, "sum")))

    # ----- left-join everything onto spine -----
    summary = spine.copy()
    for df in [ps_daily, wa_daily, ec_daily, org_daily, pod_daily, ooh_daily]:
        summary = summary.merge(df, on="date", how="left")

    # fill nulls with 0 for numeric columns
    num_cols = summary.select_dtypes(include="number").columns
    summary[num_cols] = summary[num_cols].fillna(0)

    # ----- write -----
    OUTPUT.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT / "cross_channel_daily.csv"
    summary.to_csv(out_path, index=False)

    # ----- logging -----
    print(f"Cross-channel daily summary: {len(summary)} rows, {len(summary.columns)} columns")
    print(f"  Total paid social spend:  ${summary['paid_social_spend'].sum():,.2f}")
    print(f"  Total ecommerce revenue:  ${summary['ecomm_revenue'].sum():,.2f}")
    print(f"  Total OOH spend:          ${summary['ooh_spend'].sum():,.2f}")
    print(f"  Date range: {summary['date'].min().date()} to {summary['date'].max().date()}")
    print(f"  Written to {out_path}")

    return summary


if __name__ == "__main__":
    build_summary()
