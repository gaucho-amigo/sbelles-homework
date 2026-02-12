"""Transform ecommerce transaction data: aggregate line-items to daily grain."""

import pandas as pd
from src.transforms.utils import (
    DATA_DIR, WAREHOUSE_DIR, read_csv, log_step, validate_date_range,
)


def transform_ecommerce():
    """Read 3 CSVs, concat, derive date, aggregate to daily grain by
    (date, dma_name, state, product_category, size, promo_flag)."""
    print("\n=== fact_ecommerce_daily ===")

    files = sorted(DATA_DIR.glob("sBelles_transactions_*.csv"))
    dfs = [read_csv(f, date_cols=["order_datetime"]) for f in files]
    rows_in = sum(len(d) for d in dfs)
    df = pd.concat(dfs, ignore_index=True)

    # Derive date from order_datetime
    df["date"] = df["order_datetime"].dt.normalize()

    # Log negative revenue rows
    neg_rev = df[df["line_revenue"] < 0]
    print(f"    [data quality] {len(neg_rev)} rows with negative line_revenue (preserved)")

    # Compute derived columns for aggregation
    df["discount_x_qty"] = df["discount_per_unit"] * df["quantity"]
    df["cost_x_qty"] = df["unit_cost"] * df["quantity"]

    # Aggregate to daily grain
    groupby_cols = ["date", "dma_name", "state", "product_category", "size", "promo_flag"]
    agg = df.groupby(groupby_cols).agg(
        orders=("order_id", "nunique"),
        line_items=("order_id", "count"),
        total_quantity=("quantity", "sum"),
        gross_revenue=("line_revenue", "sum"),
        total_discount=("discount_x_qty", "sum"),
        total_cost=("cost_x_qty", "sum"),
        avg_unit_price=("unit_price", "mean"),
    ).reset_index()

    agg = agg.sort_values(["date", "dma_name", "product_category", "size"]).reset_index(drop=True)
    mn, mx = validate_date_range(agg, "date")

    out = WAREHOUSE_DIR / "fact_ecommerce" / "fact_ecommerce_daily.csv"
    agg.to_csv(out, index=False)
    log_step("fact_ecommerce_daily", rows_in, len(agg),
             actions=[f"aggregated {rows_in} line-items to {len(agg)} daily rows",
                      f"negative revenue rows (preserved): {len(neg_rev)}",
                      "groupby: date, dma_name, state, product_category, size, promo_flag"],
             date_range=(str(mn.date()), str(mx.date())))
    return agg


if __name__ == "__main__":
    transform_ecommerce()
