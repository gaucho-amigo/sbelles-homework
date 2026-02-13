"""Compute lagged Pearson cross-correlations for five signal pairs.

Reads cross_channel_daily.csv. Writes lag_correlations.csv, lag_analysis_notes.md,
and two correlogram charts.
"""

import pathlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_ROOT / "analysis" / "output"

COLORS = {
    "steel_blue": "#4682B4",
    "coral": "#E07A5F",
    "sage": "#81B29A",
    "amber": "#F2CC8F",
    "slate": "#3D405B",
}
DPI = 300
FONT_LABEL = 11
FONT_TITLE = 13

MAX_LAG = 14

SIGNAL_PAIRS = [
    ("paid_social_spend", "web_sessions", "Paid Social Spend → Web Sessions"),
    ("paid_social_spend", "ecomm_revenue", "Paid Social Spend → Ecomm Revenue"),
    ("web_sessions", "ecomm_revenue", "Web Sessions → Ecomm Revenue"),
    ("podcast_impressions", "web_sessions", "Podcast Impressions → Web Sessions"),
    ("organic_impressions", "web_sessions", "Organic Impressions → Web Sessions"),
]


def _read(path):
    df = pd.read_csv(path, parse_dates=["date"])
    df.columns = df.columns.str.strip().str.lower()
    return df


def compute_lag_correlations(summary):
    """Compute Pearson r at lags 0-14 for each signal pair.

    For pair (X, Y), correlate X(t) with Y(t+k) for k = 0..14.
    """
    rows = []
    for x_col, y_col, label in SIGNAL_PAIRS:
        x = summary[x_col].values
        y = summary[y_col].values
        for lag in range(MAX_LAG + 1):
            if lag == 0:
                r = np.corrcoef(x, y)[0, 1]
            else:
                # X(t) with Y(t+k): align x[:-lag] with y[lag:]
                r = np.corrcoef(x[:-lag], y[lag:])[0, 1]
            rows.append({"signal_pair": label, "lag_days": lag, "pearson_r": round(r, 6)})

    return pd.DataFrame(rows)


def _setup_ax(ax, title):
    ax.set_title(title, fontsize=FONT_TITLE, fontweight="bold", pad=10)
    ax.set_xlabel("Lag (days)", fontsize=FONT_LABEL)
    ax.set_ylabel("Pearson r", fontsize=FONT_LABEL)
    ax.set_xticks(range(0, MAX_LAG + 1))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)


def chart_paid_funnel(lag_df):
    """Chart 5: Correlograms for paid social → web → revenue."""
    fig, ax = plt.subplots(figsize=(12, 6))
    pairs = SIGNAL_PAIRS[:3]
    colors = [COLORS["steel_blue"], COLORS["coral"], COLORS["sage"]]
    for (_, _, label), color in zip(pairs, colors):
        sub = lag_df[lag_df["signal_pair"] == label]
        ax.plot(sub["lag_days"], sub["pearson_r"], marker="o", markersize=4,
                linewidth=2, label=label, color=color)

    _setup_ax(ax, "Lagged Cross-Correlations: Paid Social → Web Traffic → Revenue")
    ax.legend(fontsize=9, loc="best", framealpha=0.9)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    path = OUTPUT / "chart_lag_paid_funnel.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


def chart_earned_owned(lag_df):
    """Chart 6: Correlograms for podcast and organic → web sessions."""
    fig, ax = plt.subplots(figsize=(12, 6))
    pairs = SIGNAL_PAIRS[3:]
    colors = [COLORS["amber"], COLORS["slate"]]
    for (_, _, label), color in zip(pairs, colors):
        sub = lag_df[lag_df["signal_pair"] == label]
        ax.plot(sub["lag_days"], sub["pearson_r"], marker="o", markersize=4,
                linewidth=2, label=label, color=color)

    _setup_ax(ax, "Lagged Cross-Correlations: Earned & Owned Media → Web Traffic")
    ax.legend(fontsize=9, loc="best", framealpha=0.9)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    path = OUTPUT / "chart_lag_earned_owned.png"
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


NOTES = """\
# Lag Analysis Notes

Cross-correlations are computed on raw daily values. Shared seasonal patterns
(back-to-school, Black Friday/holiday) may inflate correlation estimates at all
lags. Deseasonalizing the signals before computing correlations would isolate
short-term dynamics from seasonal confounds.

These correlations identify candidate causal relationships for further
investigation using entropy-based methods; they do not establish causality.
"""


def run():
    """Run full lag analysis: compute correlations, write CSV and charts."""
    summary = _read(OUTPUT / "cross_channel_daily.csv")
    print("Computing lagged cross-correlations (lags 0-14 days)...")

    lag_df = compute_lag_correlations(summary)

    # write CSV
    csv_path = OUTPUT / "lag_correlations.csv"
    lag_df.to_csv(csv_path, index=False)
    print(f"  Written {csv_path} ({len(lag_df)} rows)")

    # write notes
    notes_path = OUTPUT / "lag_analysis_notes.md"
    notes_path.write_text(NOTES)
    print(f"  Written {notes_path}")

    # print peak correlations
    for label in lag_df["signal_pair"].unique():
        sub = lag_df[lag_df["signal_pair"] == label]
        peak = sub.loc[sub["pearson_r"].abs().idxmax()]
        print(f"  {label}: peak |r| = {peak['pearson_r']:.4f} at lag {int(peak['lag_days'])}d")

    # charts
    chart_paid_funnel(lag_df)
    chart_earned_owned(lag_df)

    return lag_df


if __name__ == "__main__":
    run()
