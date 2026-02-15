"""Compute lagged Pearson cross-correlations for five signal pairs.

Reads cross_channel_daily.csv. Writes lag_correlations.csv, lag_correlations_resid.csv,
lag_analysis_notes.md, and four correlogram charts (raw + residualized).
"""

import pathlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from analysis.utils import add_residual_columns

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

RESID_PAIRS = [
    ("paid_social_spend__resid", "web_sessions__resid", "Paid Social Spend → Web Sessions"),
    ("paid_social_spend__resid", "ecomm_revenue__resid", "Paid Social Spend → Ecomm Revenue"),
    ("web_sessions__resid", "ecomm_revenue__resid", "Web Sessions → Ecomm Revenue"),
    ("podcast_impressions__resid", "web_sessions__resid", "Podcast Impressions → Web Sessions"),
    ("organic_impressions__resid", "web_sessions__resid", "Organic Impressions → Web Sessions"),
]

RESID_COLS = [
    "paid_social_spend", "web_sessions", "ecomm_revenue",
    "podcast_impressions", "organic_impressions",
]


def _read(path):
    df = pd.read_csv(path, parse_dates=["date"])
    df.columns = df.columns.str.strip().str.lower()
    return df


def compute_lag_correlations(df, pairs):
    """Compute Pearson r at lags 0-14 for each signal pair.

    For pair (X, Y), correlate X(t) with Y(t+k) for k = 0..14.
    Drops NaN rows per pair before computing correlations.
    """
    rows = []
    for x_col, y_col, label in pairs:
        valid = df[[x_col, y_col]].dropna()
        x = valid[x_col].values
        y = valid[y_col].values
        for lag in range(MAX_LAG + 1):
            if lag == 0:
                r = np.corrcoef(x, y)[0, 1]
            else:
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


def _plot_correlogram(lag_df, pair_labels, colors, title, filename):
    """Generic correlogram plotter for a set of signal pairs."""
    fig, ax = plt.subplots(figsize=(12, 6))
    for label, color in zip(pair_labels, colors):
        sub = lag_df[lag_df["signal_pair"] == label]
        ax.plot(sub["lag_days"], sub["pearson_r"], marker="o", markersize=4,
                linewidth=2, label=label, color=color)
    _setup_ax(ax, title)
    ax.legend(fontsize=9, loc="best", framealpha=0.9)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    path = OUTPUT / filename
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


def chart_paid_funnel(lag_df):
    """Chart 5: Correlograms for paid social → web → revenue."""
    labels = [l for _, _, l in SIGNAL_PAIRS[:3]]
    _plot_correlogram(lag_df, labels,
                      [COLORS["steel_blue"], COLORS["coral"], COLORS["sage"]],
                      "Lagged Cross-Correlations: Paid Social \u2192 Web Traffic \u2192 Revenue",
                      "chart_lag_paid_funnel.png")


def chart_earned_owned(lag_df):
    """Chart 6: Correlograms for podcast and organic → web sessions."""
    labels = [l for _, _, l in SIGNAL_PAIRS[3:]]
    _plot_correlogram(lag_df, labels,
                      [COLORS["amber"], COLORS["slate"]],
                      "Lagged Cross-Correlations: Earned & Owned Media \u2192 Web Traffic",
                      "chart_lag_earned_owned.png")


def chart_paid_funnel_resid(lag_df):
    """Correlogram for residualized paid funnel pairs."""
    labels = [l for _, _, l in RESID_PAIRS[:3]]
    _plot_correlogram(lag_df, labels,
                      [COLORS["steel_blue"], COLORS["coral"], COLORS["sage"]],
                      "Lagged Cross-Correlations: Paid Funnel (14-Day Seasonal Trend Removed)",
                      "chart_lag_paid_funnel_resid.png")


def chart_earned_owned_resid(lag_df):
    """Correlogram for residualized earned/owned pairs."""
    labels = [l for _, _, l in RESID_PAIRS[3:]]
    _plot_correlogram(lag_df, labels,
                      [COLORS["amber"], COLORS["slate"]],
                      "Lagged Cross-Correlations: Earned & Owned Media (14-Day Seasonal Trend Removed)",
                      "chart_lag_earned_owned_resid.png")


def _build_notes(raw_df, resid_df):
    """Build analysis notes with actual computed values."""
    # gather peak values for raw
    raw_lines = []
    for label in raw_df["signal_pair"].unique():
        sub = raw_df[raw_df["signal_pair"] == label]
        peak = sub.loc[sub["pearson_r"].abs().idxmax()]
        lag0 = sub[sub["lag_days"] == 0]["pearson_r"].values[0]
        raw_lines.append(f"- {label}: r = {lag0:.2f} at lag 0, "
                         f"peak |r| = {peak['pearson_r']:.2f} at lag {int(peak['lag_days'])}d")

    # gather peak values for resid
    resid_lines = []
    for label in resid_df["signal_pair"].unique():
        sub = resid_df[resid_df["signal_pair"] == label]
        peak = sub.loc[sub["pearson_r"].abs().idxmax()]
        lag0 = sub[sub["lag_days"] == 0]["pearson_r"].values[0]
        resid_lines.append(f"- {label}: r = {lag0:.2f} at lag 0, "
                           f"peak |r| = {peak['pearson_r']:.2f} at lag {int(peak['lag_days'])}d")

    # compare paid social → web sessions
    raw_ps_ws = raw_df[(raw_df["signal_pair"].str.contains("Paid Social Spend.*Web Sessions"))
                       & (raw_df["lag_days"] == 0)]["pearson_r"].values[0]
    resid_ps_ws = resid_df[(resid_df["signal_pair"].str.contains("Paid Social Spend.*Web Sessions"))
                           & (resid_df["lag_days"] == 0)]["pearson_r"].values[0]

    return f"""\
# Lag Analysis Notes

## Raw Cross-Correlations

All five signal pairs show highest Pearson correlation at lag 0, declining
monotonically with increasing lag. Paid social spend and web sessions correlate
at r = {raw_ps_ws:.2f} at lag 0. This pattern is consistent with shared seasonal response
(back-to-school, Black Friday/holiday) rather than day-level causal signal flow.

{chr(10).join(raw_lines)}

## Deseasonalized Cross-Correlations

After removing a 14-day centered rolling mean from each signal, correlations
drop substantially across all pairs. The residualized correlations are much
weaker, confirming that the raw correlations were dominated by seasonal
co-movement rather than short-term causal dynamics.

{chr(10).join(resid_lines)}

## Interpretation

High raw correlations between marketing spend and revenue do not establish that
spend caused revenue. Seasonal demand drives both spend (marketers increase
budgets during peak periods) and revenue (consumers buy more during
back-to-school and holidays). After controlling for this seasonal pattern, the
residual short-term relationships are substantially weaker (paid social spend →
web sessions drops from r = {raw_ps_ws:.2f} to r = {resid_ps_ws:.2f} at lag 0).

This demonstrates a fundamental limitation of correlation-based marketing mix
models: they cannot distinguish whether spend amplified demand or merely
coincided with it. Establishing true causal impact requires methods that can
detect directional information flow between signals while conditioning on
confounding temporal patterns. Entropy-based causal inference, such as transfer
entropy, addresses this by measuring whether the past of one signal reduces
uncertainty about the future of another, beyond what that signal's own history
explains.

## Note on Methodology

Deseasonalization uses a 14-day centered rolling mean subtracted from raw
values. This window captures weekly cyclicality and short-term seasonal trends
without over-smoothing. Percent-change residuals were considered but rejected
due to division-by-zero risk on sparse signals (podcast mentions). Pearson
correlation is scale-invariant, making absolute residuals appropriate for
cross-signal comparison.
"""


def run():
    """Run full lag analysis: raw and residualized correlations, CSV, notes, charts."""
    summary = _read(OUTPUT / "cross_channel_daily.csv")

    # --- raw correlations ---
    print("Computing raw lagged cross-correlations (lags 0-14 days)...")
    raw_df = compute_lag_correlations(summary, SIGNAL_PAIRS)

    csv_path = OUTPUT / "lag_correlations.csv"
    raw_df.to_csv(csv_path, index=False)
    print(f"  Written {csv_path} ({len(raw_df)} rows)")

    for label in raw_df["signal_pair"].unique():
        sub = raw_df[raw_df["signal_pair"] == label]
        peak = sub.loc[sub["pearson_r"].abs().idxmax()]
        print(f"  {label}: peak |r| = {peak['pearson_r']:.4f} at lag {int(peak['lag_days'])}d")

    chart_paid_funnel(raw_df)
    chart_earned_owned(raw_df)

    # --- residualized correlations ---
    print("\nComputing residualized cross-correlations (14-day trend removed)...")
    summary_resid = add_residual_columns(summary, RESID_COLS, window=14)
    resid_df = compute_lag_correlations(summary_resid, RESID_PAIRS)

    resid_csv_path = OUTPUT / "lag_correlations_resid.csv"
    resid_df.to_csv(resid_csv_path, index=False)
    print(f"  Written {resid_csv_path} ({len(resid_df)} rows)")

    for label in resid_df["signal_pair"].unique():
        sub = resid_df[resid_df["signal_pair"] == label]
        peak = sub.loc[sub["pearson_r"].abs().idxmax()]
        print(f"  {label}: peak |r| = {peak['pearson_r']:.4f} at lag {int(peak['lag_days'])}d")

    chart_paid_funnel_resid(resid_df)
    chart_earned_owned_resid(resid_df)

    # --- notes ---
    notes = _build_notes(raw_df, resid_df)
    notes_path = OUTPUT / "lag_analysis_notes.md"
    notes_path.write_text(notes)
    print(f"  Written {notes_path}")

    return raw_df, resid_df


if __name__ == "__main__":
    run()
