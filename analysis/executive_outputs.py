"""Generate executive-ready analytical outputs from lag and cross-channel tables.

Outputs:
- analysis/output/seasonal_inflation_summary.csv
- analysis/output/partial_correlation_paid_to_revenue.csv
- Appended executive section in analysis/output/lag_analysis_notes.md
"""

import pathlib
import numpy as np
import pandas as pd

from analysis.utils import add_residual_columns

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_ROOT / "analysis" / "output"


def _read(path, parse_dates=False):
    if parse_dates:
        df = pd.read_csv(path, parse_dates=["date"])
    else:
        df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()
    return df


def build_seasonal_inflation_summary():
    raw = _read(OUTPUT / "lag_correlations.csv")
    resid = _read(OUTPUT / "lag_correlations_resid.csv")

    raw0 = raw[raw["lag_days"] == 0][["signal_pair", "pearson_r"]].rename(
        columns={"pearson_r": "raw_r"}
    )
    resid0 = resid[resid["lag_days"] == 0][["signal_pair", "pearson_r"]].rename(
        columns={"pearson_r": "residual_r"}
    )

    merged = raw0.merge(resid0, on="signal_pair", how="inner")
    merged["percent_reduction"] = np.where(
        merged["raw_r"] != 0,
        (merged["raw_r"] - merged["residual_r"]) / merged["raw_r"],
        np.nan,
    )
    merged = merged.sort_values("percent_reduction", ascending=False).reset_index(drop=True)

    out_path = OUTPUT / "seasonal_inflation_summary.csv"
    merged.to_csv(out_path, index=False)
    print(f"  Written {out_path} ({len(merged)} rows)")
    return merged


def _residualize_for_partial(summary):
    cols = ["paid_social_spend", "ecomm_revenue", "web_sessions"]
    return add_residual_columns(summary, cols, window=14)


def _interpret_partial(simple_corr, partial_corr):
    direction = "positive" if partial_corr >= 0 else "negative"
    attenuation = abs(simple_corr) - abs(partial_corr)
    if attenuation > 0.15:
        strength_note = "meaningfully weaker after conditioning on sessions"
    elif attenuation > 0.05:
        strength_note = "modestly weaker after conditioning on sessions"
    else:
        strength_note = "similar after conditioning on sessions"
    return (
        "After removing 14-day trends and controlling for residual web sessions, "
        f"the paid spend to revenue relationship remains {direction} but is {strength_note}."
    )


def build_partial_correlation():
    summary = _read(OUTPUT / "cross_channel_daily.csv", parse_dates=True)
    resid = _residualize_for_partial(summary)

    cols = ["paid_social_spend__resid", "ecomm_revenue__resid", "web_sessions__resid"]
    sub = resid[cols].dropna().copy()

    x_sessions = sub["web_sessions__resid"].values
    y_revenue = sub["ecomm_revenue__resid"].values
    spend_resid = sub["paid_social_spend__resid"].values

    slope, intercept = np.polyfit(x_sessions, y_revenue, deg=1)
    revenue_hat_error = y_revenue - (slope * x_sessions + intercept)

    simple_corr = float(np.corrcoef(spend_resid, y_revenue)[0, 1])
    partial_corr = float(np.corrcoef(spend_resid, revenue_hat_error)[0, 1])
    interpretation = _interpret_partial(simple_corr, partial_corr)

    out = pd.DataFrame(
        [
            {
                "simple_corr": round(simple_corr, 6),
                "partial_corr": round(partial_corr, 6),
                "interpretation": interpretation,
            }
        ]
    )

    out_path = OUTPUT / "partial_correlation_paid_to_revenue.csv"
    out.to_csv(out_path, index=False)
    print(f"  Written {out_path} (1 row)")
    return out


def update_notes(seasonal_df, partial_df):
    notes_path = OUTPUT / "lag_analysis_notes.md"
    existing = notes_path.read_text() if notes_path.exists() else "# Lag Analysis Notes\n"

    marker = "## Executive Addendum"
    if marker in existing:
        existing = existing.split(marker)[0].rstrip() + "\n\n"
    else:
        existing = existing.rstrip() + "\n\n"

    mean_reduction = seasonal_df["percent_reduction"].mean()
    max_row = seasonal_df.loc[seasonal_df["percent_reduction"].idxmax()]
    min_row = seasonal_df.loc[seasonal_df["percent_reduction"].idxmin()]
    simple_corr = partial_df.loc[0, "simple_corr"]
    partial_corr = partial_df.loc[0, "partial_corr"]
    interpretation = partial_df.loc[0, "interpretation"]

    addendum = f"""## Executive Addendum

- Seasonal inflation: At lag 0, raw correlations are materially inflated by shared seasonality. Mean reduction from raw to residualized r is {mean_reduction:.1%}.
- Residual correlation readout: The largest reduction is for {max_row['signal_pair']} ({max_row['percent_reduction']:.1%}), while the smallest reduction is for {min_row['signal_pair']} ({min_row['percent_reduction']:.1%}).
- Partial correlation readout: Simple residualized paid-to-revenue correlation is r = {simple_corr:.2f}; controlling for residual web sessions yields partial r = {partial_corr:.2f}. {interpretation}
- Limits of correlation: Correlation (including partial correlation) indicates association, not causal lift. Causal impact still requires an explicit identification strategy.
"""

    notes_path.write_text(existing + addendum)
    print(f"  Updated {notes_path}")


def run():
    print("Generating executive-ready analytical outputs...")
    seasonal = build_seasonal_inflation_summary()
    partial = build_partial_correlation()
    update_notes(seasonal, partial)
    print("Done.")


if __name__ == "__main__":
    run()
