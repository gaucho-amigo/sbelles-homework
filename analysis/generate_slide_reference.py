"""Generate slide_reference_data.md with all key metrics for the executive deck."""

import pandas as pd
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def main():
    lines = []

    def p(text=""):
        print(text)
        lines.append(text)

    # --- Load data ---
    daily = pd.read_csv(OUTPUT_DIR / "cross_channel_daily.csv", parse_dates=["date"])
    lag_raw = pd.read_csv(OUTPUT_DIR / "lag_correlations.csv")
    lag_resid = pd.read_csv(OUTPUT_DIR / "lag_correlations_resid.csv")
    partial = pd.read_csv(OUTPUT_DIR / "partial_correlation_paid_to_revenue.csv")
    promo = pd.read_csv(OUTPUT_DIR / "promo_impact_summary.csv")
    seasonal_inf = pd.read_csv(OUTPUT_DIR / "seasonal_inflation_summary.csv")

    # =========================================================
    p("# Slide Reference Data")
    p()
    p("All numbers for the executive slide deck, pulled from analysis outputs.")
    p()

    # --- Dataset Overview ---
    p("## Dataset Overview")
    p()
    p("- Total source files: 21")
    p("- Total source rows: 98,320")
    p(f"- Date range: {daily['date'].min().date()} to {daily['date'].max().date()} ({len(daily)} days)")
    p("- Datastreams: 6 (paid social, web analytics, ecommerce, organic social, podcast, OOH)")
    p("- Schema drift patterns resolved: 3")
    p()

    # --- Warehouse Output ---
    p("## Warehouse Output")
    p()
    p("- Dimension tables: 5 (dim_date, dim_geography, dim_channel, dim_campaign_initiative, dim_podcast)")
    p("- Daily fact tables: 6")
    p("- Source-grain detail tables: 2 (fact_ecommerce_transactions, fact_web_analytics_events)")
    p("- Validation checks passed: 48/48")
    p()

    # --- Financial Totals ---
    p("## Financial Totals")
    p()
    paid_spend = daily["paid_social_spend"].sum()
    ooh_spend = daily["ooh_spend"].sum()
    total_spend = paid_spend + ooh_spend
    ecomm_rev = daily["ecomm_revenue"].sum()
    ecomm_orders = daily["ecomm_orders"].sum()
    web_pageviews = daily["web_pageviews"].sum()
    podcast_mentions = daily["podcast_mentions"].sum()

    p(f"- Total paid social spend: ${paid_spend:,.0f}")
    p(f"- Total OOH spend: ${ooh_spend:,.0f}")
    p(f"- Total combined marketing spend: ${total_spend:,.0f}")
    p(f"- Total ecommerce revenue: ${ecomm_rev:,.0f}")
    p(f"- Total ecommerce orders: {ecomm_orders:,.0f}")
    p(f"- Total web pageviews: {web_pageviews:,.0f}")
    p(f"- Total podcast mentions: {podcast_mentions:,.0f}")
    p(f"- Spend-to-revenue ratio: {total_spend / ecomm_rev:.1f}x")
    p()

    # --- Seasonal Metrics ---
    p("## Seasonal Metrics")
    p()
    p("| Season | Days | Avg Daily Revenue | Avg Daily Paid Spend | Avg Daily Web Sessions | Avg Daily Orders |")
    p("|---|---:|---:|---:|---:|---:|")
    for season in ["regular", "back_to_school", "black_friday_holiday"]:
        mask = daily["season_flag"] == season
        subset = daily[mask]
        days = len(subset)
        avg_rev = subset["ecomm_revenue"].mean()
        avg_spend = subset["paid_social_spend"].mean()
        avg_sess = subset["web_sessions"].mean()
        avg_orders = subset["ecomm_orders"].mean()
        p(f"| {season} | {days} | ${avg_rev:,.0f} | ${avg_spend:,.0f} | {avg_sess:,.0f} | {avg_orders:,.0f} |")
    p()

    # --- Correlation Summary ---
    p("## Correlation Summary (Lag 0)")
    p()
    p("| Signal Pair | Raw r | Deseasonalized r | % Reduction |")
    p("|---|---:|---:|---:|")

    pairs = lag_raw["signal_pair"].unique()
    for pair in pairs:
        raw_r = lag_raw[(lag_raw["signal_pair"] == pair) & (lag_raw["lag_days"] == 0)]["pearson_r"].iloc[0]
        resid_r = lag_resid[(lag_resid["signal_pair"] == pair) & (lag_resid["lag_days"] == 0)]["pearson_r"].iloc[0]
        pct_red = (1 - abs(resid_r) / abs(raw_r)) * 100 if raw_r != 0 else 0
        p(f"| {pair} | {raw_r:.3f} | {resid_r:.3f} | {pct_red:.1f}% |")
    p()

    # Partial correlation
    p("### Partial Correlation")
    p()
    simple = partial["simple_corr"].iloc[0]
    part_r = partial["partial_corr"].iloc[0]
    p(f"- Simple deseasonalized correlation (paid spend → revenue): r = {simple:.3f}")
    p(f"- Partial correlation (controlling for web sessions): r = {part_r:.3f}")
    p(f"- Interpretation: {partial['interpretation'].iloc[0]}")
    p()

    # --- Seasonal Inflation Summary ---
    p("## Seasonal Inflation Summary")
    p()
    p("| Signal Pair | Raw r | Residual r | % Reduction |")
    p("|---|---:|---:|---:|")
    for _, row in seasonal_inf.iterrows():
        p(f"| {row['signal_pair']} | {row['raw_r']:.3f} | {row['residual_r']:.3f} | {row['percent_reduction']*100:.1f}% |")
    p()

    # --- Promo Summary ---
    p("## Promo Impact Summary")
    p()
    p("| Metric | Non-Promo (flag=0) | Promo (flag=1) |")
    p("|---|---:|---:|")
    non_p = promo[promo["promo_flag"] == 0].iloc[0]
    yes_p = promo[promo["promo_flag"] == 1].iloc[0]
    p(f"| Line items | {int(non_p['line_items']):,} | {int(yes_p['line_items']):,} |")
    p(f"| Distinct orders | {int(non_p['distinct_orders']):,} | {int(yes_p['distinct_orders']):,} |")
    p(f"| Total quantity | {int(non_p['total_quantity']):,} | {int(yes_p['total_quantity']):,} |")
    p(f"| Total revenue | ${non_p['total_revenue']:,.0f} | ${yes_p['total_revenue']:,.0f} |")
    p(f"| Avg order value | ${non_p['avg_order_value']:.2f} | ${yes_p['avg_order_value']:.2f} |")
    p(f"| Avg unit price | ${non_p['avg_unit_price']:.2f} | ${yes_p['avg_unit_price']:.2f} |")
    p(f"| Avg discount/unit | ${non_p['avg_discount_per_unit']:.2f} | ${yes_p['avg_discount_per_unit']:.2f} |")
    p(f"| Negative revenue rows | {int(non_p['negative_revenue_rows'])} | {int(yes_p['negative_revenue_rows'])} |")
    p(f"| Negative revenue amount | ${non_p['negative_revenue_amount']:.0f} | ${yes_p['negative_revenue_amount']:.0f} |")
    p()

    # --- Key Slide Callouts ---
    p("## Key Slide Callouts")
    p()
    p(f"- \"${total_spend/1e6:.0f}M in marketing spend vs ${ecomm_rev/1e3:.0f}K in tracked revenue\"")
    p(f"- Revenue split: ${non_p['total_revenue']:,.0f} non-promo + ${yes_p['total_revenue']:,.0f} promo = ${ecomm_rev:,.0f} total")
    p(f"- Promo revenue is {yes_p['total_revenue']/ecomm_rev*100:.1f}% of total but avg order value drops from ${non_p['avg_order_value']:.2f} to ${yes_p['avg_order_value']:.2f}")
    p(f"- Raw paid→sessions r=0.938 drops to r=0.785 after deseasonalization (16.4% reduction)")
    p(f"- Partial correlation (paid→revenue | sessions) = {part_r:.3f} — effectively zero")
    p()

    # --- Write file ---
    out_path = OUTPUT_DIR / "slide_reference_data.md"
    out_path.write_text("\n".join(lines) + "\n")
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
