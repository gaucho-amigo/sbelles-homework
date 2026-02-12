"""Transform OOH airport data: expand weekly to daily."""

import pandas as pd
from src.transforms.utils import (
    DATA_DIR, WAREHOUSE_DIR, REFERENCE_DIR, read_csv, log_step, validate_date_range,
)


def transform_ooh():
    """Read 1 CSV, expand weekly->daily (7 rows per source row),
    divide spend/impressions by 7, join airport_state from reference."""
    print("\n=== fact_ooh_daily ===")

    df = read_csv(DATA_DIR / "sBelles_ooh_airport_weekly.csv",
                  date_cols=["week_start_date"])
    rows_in = len(df)

    # Join airport state from reference
    airport_ref = read_csv(REFERENCE_DIR / "airport_lookup.csv")
    df = df.merge(
        airport_ref[["iata_code", "state"]].rename(columns={"iata_code": "airport_code"}),
        on="airport_code", how="left",
    )

    # Expand each weekly row into 7 daily rows
    expanded = []
    for _, row in df.iterrows():
        for day_offset in range(7):
            new_row = row.copy()
            new_row["date"] = row["week_start_date"] + pd.Timedelta(days=day_offset)
            new_row["spend"] = row["spend"] / 7
            new_row["impressions"] = row["impressions"] / 7
            # placements NOT divided — represents active count
            expanded.append(new_row)

    result = pd.DataFrame(expanded)

    # Select and order target columns
    result = result[["date", "airport_code", "airport_name", "state", "format",
                      "audience_segment", "spend", "impressions", "placements"]]
    result = result.sort_values(["date", "airport_code", "format", "audience_segment"]).reset_index(drop=True)

    mn, mx = validate_date_range(result, "date")

    out = WAREHOUSE_DIR / "fact_ooh" / "fact_ooh_daily.csv"
    result.to_csv(out, index=False)
    log_step("fact_ooh_daily", rows_in, len(result),
             actions=[f"expanded {rows_in} weekly -> {len(result)} daily rows",
                      "spend & impressions divided by 7",
                      "placements carried forward (not divided)",
                      "airport state joined from reference"],
             date_range=(str(mn.date()), str(mx.date())))
    return result


if __name__ == "__main__":
    transform_ooh()
