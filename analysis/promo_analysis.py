"""Promo impact analysis on ecommerce transactions.

Reads fact_ecommerce_transactions.csv. Writes promo_impact_summary.csv.
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


def run():
    """Compute promo vs non-promo metrics and write summary."""
    txn = _read(WAREHOUSE / "fact_ecommerce" / "fact_ecommerce_transactions.csv")

    results = []
    for flag in sorted(txn["promo_flag"].unique()):
        sub = txn[txn["promo_flag"] == flag]
        neg = sub[sub["line_revenue"] < 0]
        distinct_orders = sub["order_id"].nunique()
        total_rev = sub["line_revenue"].sum()
        results.append({
            "promo_flag": flag,
            "line_items": len(sub),
            "distinct_orders": distinct_orders,
            "total_quantity": sub["quantity"].sum(),
            "total_revenue": round(total_rev, 2),
            "avg_order_value": round(total_rev / distinct_orders, 2) if distinct_orders else 0,
            "avg_unit_price": round(sub["unit_price"].mean(), 2),
            "avg_discount_per_unit": round(sub["discount_per_unit"].mean(), 2),
            "negative_revenue_rows": len(neg),
            "negative_revenue_amount": round(neg["line_revenue"].sum(), 2),
        })

    summary = pd.DataFrame(results)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT / "promo_impact_summary.csv"
    summary.to_csv(out_path, index=False)

    # print formatted table
    print("\nPromo Impact Summary")
    print("=" * 80)
    for _, row in summary.iterrows():
        label = "PROMO" if row["promo_flag"] == 1 else "NO PROMO"
        print(f"\n  {label} (promo_flag={int(row['promo_flag'])})")
        print(f"    Line items:          {int(row['line_items']):,}")
        print(f"    Distinct orders:     {int(row['distinct_orders']):,}")
        print(f"    Total quantity:      {int(row['total_quantity']):,}")
        print(f"    Total revenue:       ${row['total_revenue']:,.2f}")
        print(f"    Avg order value:     ${row['avg_order_value']:,.2f}")
        print(f"    Avg unit price:      ${row['avg_unit_price']:,.2f}")
        print(f"    Avg discount/unit:   ${row['avg_discount_per_unit']:,.2f}")
        print(f"    Negative rev rows:   {int(row['negative_revenue_rows']):,}")
        print(f"    Negative rev amount: ${row['negative_revenue_amount']:,.2f}")

    print(f"\n  Written to {out_path}")
    return summary


if __name__ == "__main__":
    run()
