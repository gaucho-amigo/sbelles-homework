"""Generate four time-series charts from the cross-channel summary and fact tables.

Charts saved as PNGs at 300 DPI to analysis/output/.
"""

import pathlib
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
WAREHOUSE = PROJECT_ROOT / "data_warehouse"
OUTPUT = PROJECT_ROOT / "analysis" / "output"

# --- style constants ---
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


def _read(path):
    df = pd.read_csv(path, parse_dates=["date"])
    df.columns = df.columns.str.strip().str.lower()
    return df


def _setup_ax(ax, title, ylabel, figsize=None):
    ax.set_title(title, fontsize=FONT_TITLE, fontweight="bold", pad=10)
    ax.set_ylabel(ylabel, fontsize=FONT_LABEL)
    ax.set_xlabel("")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.tick_params(axis="x", rotation=45)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(False)


def _save(fig, name):
    path = OUTPUT / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {path}")


def chart_revenue_seasonal(summary):
    """Chart 1: Daily ecomm revenue with seasonal shading and 7-day rolling avg."""
    fig, ax = plt.subplots(figsize=(12, 6))

    raw = summary.set_index("date")["ecomm_revenue"]
    rolling = raw.rolling(7, min_periods=1).mean()

    ax.plot(raw.index, raw.values, color=COLORS["steel_blue"], alpha=0.25, linewidth=0.8, label="Daily")
    ax.plot(rolling.index, rolling.values, color=COLORS["steel_blue"], linewidth=2, label="7-Day Rolling Avg")

    # seasonal bands
    bands = [
        ("2023-07-15", "2023-09-15", "Back-to-School 2023"),
        ("2024-07-15", "2024-06-30", "Back-to-School 2024"),  # data ends Jun 30
        ("2023-11-15", "2023-12-10", "Black Friday / Holiday"),
    ]
    # correct BTS 2024: data only goes to Jun 30, so skip if band starts after data end
    bands = [
        ("2023-07-15", "2023-09-15", "Back-to-School 2023"),
        ("2023-11-15", "2023-12-10", "Black Friday / Holiday"),
        ("2024-07-15", "2024-09-15", "Back-to-School 2024"),
    ]
    band_colors = [COLORS["amber"], COLORS["coral"], COLORS["amber"]]
    for (start, end, label), color in zip(bands, band_colors):
        s, e = pd.Timestamp(start), pd.Timestamp(end)
        # clip to data range
        e = min(e, raw.index.max())
        if s > raw.index.max():
            continue
        ax.axvspan(s, e, alpha=0.15, color=color, label=label)
        mid = s + (e - s) / 2
        ax.text(mid, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else raw.max() * 0.95,
                label, ha="center", va="top", fontsize=8, fontstyle="italic", color=COLORS["slate"])

    _setup_ax(ax, "Daily Ecommerce Revenue with Seasonal Periods", "Revenue ($)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend(fontsize=9, loc="upper left", framealpha=0.9)
    _save(fig, "chart_revenue_seasonal.png")


def chart_spend_vs_revenue(summary):
    """Chart 2: Dual-axis marketing spend vs ecommerce revenue (7-day rolling)."""
    fig, ax1 = plt.subplots(figsize=(12, 6))

    df = summary.set_index("date").sort_index()
    spend = (df["paid_social_spend"] + df["ooh_spend"]).rolling(7, min_periods=1).mean()
    revenue = df["ecomm_revenue"].rolling(7, min_periods=1).mean()

    ax1.plot(spend.index, spend.values, color=COLORS["coral"], linewidth=2, label="Marketing Spend")
    _setup_ax(ax1, "Marketing Spend vs. Ecommerce Revenue (7-Day Rolling Avg)", "Marketing Spend ($)")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))

    ax2 = ax1.twinx()
    ax2.plot(revenue.index, revenue.values, color=COLORS["steel_blue"], linewidth=2, label="Ecomm Revenue")
    ax2.set_ylabel("Ecomm Revenue ($)", fontsize=FONT_LABEL)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax2.spines["top"].set_visible(False)
    ax2.grid(False)

    # combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=9, loc="upper left", framealpha=0.9)

    total_spend = df["paid_social_spend"].sum() + df["ooh_spend"].sum()
    total_rev = df["ecomm_revenue"].sum()
    fig.subplots_adjust(bottom=0.22)
    fig.text(0.5, 0.02,
             f"\\${total_spend / 1e6:.0f}M total spend vs \\${total_rev / 1e3:.0f}K tracked revenue "
             "\u2014 the measurement gap causal AI can close.",
             ha="center", fontsize=10, fontstyle="italic", color=COLORS["slate"])

    _save(fig, "chart_spend_vs_revenue.png")


def chart_paid_by_platform(summary):
    """Chart 3: Paid social spend by platform (7-day rolling avg)."""
    ps = _read(WAREHOUSE / "fact_paid_social" / "fact_paid_social_daily.csv")
    by_channel = (ps.groupby(["date", "channel"], as_index=False)["spend"].sum()
                  .pivot(index="date", columns="channel", values="spend")
                  .fillna(0)
                  .sort_index())

    fig, ax = plt.subplots(figsize=(12, 6))
    channel_colors = {"Instagram": COLORS["coral"], "Pinterest": COLORS["sage"],
                      "TikTok": COLORS["slate"]}
    # normalize column names for matching
    for col in by_channel.columns:
        color = channel_colors.get(col, COLORS["amber"])
        rolled = by_channel[col].rolling(7, min_periods=1).mean()
        ax.plot(rolled.index, rolled.values, linewidth=2, label=col, color=color)

    _setup_ax(ax, "Paid Social Spend by Platform (7-Day Rolling Avg)", "Daily Spend ($)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend(fontsize=9, loc="upper right", framealpha=0.9)
    _save(fig, "chart_paid_by_platform.png")


def chart_web_traffic_sources(summary):
    """Chart 4: Web sessions by traffic source (7-day rolling avg)."""
    wa = _read(WAREHOUSE / "fact_web_analytics" / "fact_web_analytics_daily.csv")
    by_source = (wa.groupby(["date", "traffic_source"], as_index=False)["sessions"].sum()
                 .pivot(index="date", columns="traffic_source", values="sessions")
                 .fillna(0)
                 .sort_index())

    fig, ax = plt.subplots(figsize=(12, 6))
    palette = list(COLORS.values())
    for i, col in enumerate(sorted(by_source.columns)):
        rolled = by_source[col].rolling(7, min_periods=1).mean()
        ax.plot(rolled.index, rolled.values, linewidth=2, label=col,
                color=palette[i % len(palette)])

    _setup_ax(ax, "Web Sessions by Traffic Source (7-Day Rolling Avg)", "Sessions")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.legend(fontsize=9, loc="upper right", framealpha=0.9)
    _save(fig, "chart_web_traffic_sources.png")


def generate_all():
    """Generate all four charts."""
    summary = _read(OUTPUT / "cross_channel_daily.csv")
    print("Generating charts...")
    chart_revenue_seasonal(summary)
    chart_spend_vs_revenue(summary)
    chart_paid_by_platform(summary)
    chart_web_traffic_sources(summary)
    print("All charts generated.")


if __name__ == "__main__":
    generate_all()
