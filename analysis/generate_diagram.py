"""Generate a clean, presentation-ready Kimball star schema diagram."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# --- Color palette (matches chart styling) ---
STEEL_BLUE = "#4682B4"
CORAL = "#E07A5F"
SAGE_GREEN = "#81B29A"
AMBER = "#F2CC8F"
SLATE = "#3D405B"
LIGHT_BG = "#FAFAFA"

DIM_COLOR = STEEL_BLUE
DIM_TEXT = "white"
FACT_COLOR = CORAL
FACT_TEXT = "white"
DETAIL_COLOR = SAGE_GREEN
DETAIL_TEXT = "white"
LINE_COLOR = "#AAAAAA"

BOX_W = 2.6
BOX_H = 0.55
CORNER = 0.08


def draw_box(ax, cx, cy, label, color, text_color, w=BOX_W, h=BOX_H):
    """Draw a rounded rectangle centered at (cx, cy) with label."""
    rect = mpatches.FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle=f"round,pad={CORNER}",
        facecolor=color, edgecolor="white", linewidth=1.5,
        zorder=3,
    )
    ax.add_patch(rect)
    ax.text(cx, cy, label, ha="center", va="center",
            fontsize=8.5, fontweight="bold", color=text_color,
            fontfamily="sans-serif", zorder=4)
    return (cx, cy)


def draw_line(ax, p1, p2, **kwargs):
    """Draw a connection line between two box centers."""
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]],
            color=LINE_COLOR, linewidth=1.0, zorder=1, **kwargs)


def main():
    fig, ax = plt.subplots(1, 1, figsize=(14, 8), dpi=300)
    ax.set_xlim(-1, 16)
    ax.set_ylim(-1, 9)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # --- Title ---
    ax.text(7, 8.4, "S'Belles Marketing Data Warehouse — Star Schema",
            ha="center", va="center", fontsize=14, fontweight="bold",
            color=SLATE, fontfamily="sans-serif")

    # --- Dimension tables (top row) ---
    dim_positions = {}
    dim_x_start = 1.5
    dim_spacing = 2.9
    dim_y = 6.8

    dims = [
        "dim_date", "dim_geography", "dim_channel",
        "dim_campaign_initiative", "dim_podcast",
    ]
    for i, name in enumerate(dims):
        x = dim_x_start + i * dim_spacing
        dim_positions[name] = draw_box(ax, x, dim_y, name, DIM_COLOR, DIM_TEXT)

    # --- Daily fact tables (middle row) ---
    fact_positions = {}
    fact_x_start = 0.5
    fact_spacing = 2.8
    fact_y = 4.2

    facts = [
        "fact_paid_social_daily", "fact_web_analytics_daily",
        "fact_ecommerce_daily", "fact_organic_social_daily",
        "fact_podcast_daily", "fact_ooh_daily",
    ]
    for i, name in enumerate(facts):
        x = fact_x_start + i * fact_spacing
        fact_positions[name] = draw_box(ax, x, fact_y, name, FACT_COLOR, FACT_TEXT)

    # --- Source-grain tables (bottom row) ---
    detail_positions = {}
    detail_y = 1.8
    details = [
        ("fact_ecommerce_transactions", 5.0),
        ("fact_web_analytics_events", 10.0),
    ]
    for name, x in details:
        detail_positions[name] = draw_box(ax, x, detail_y, name, DETAIL_COLOR, DETAIL_TEXT, w=3.0)

    # === Draw connections ===

    # Every fact connects to dim_date
    for name, pos in {**fact_positions, **detail_positions}.items():
        draw_line(ax, dim_positions["dim_date"], pos)

    # dim_geography connections
    geo_facts = [
        "fact_paid_social_daily", "fact_web_analytics_daily",
        "fact_ecommerce_daily", "fact_ooh_daily",
        "fact_ecommerce_transactions", "fact_web_analytics_events",
    ]
    for name in geo_facts:
        target = fact_positions.get(name) or detail_positions.get(name)
        draw_line(ax, dim_positions["dim_geography"], target)

    # dim_channel → fact_paid_social_daily
    draw_line(ax, dim_positions["dim_channel"], fact_positions["fact_paid_social_daily"])

    # dim_campaign_initiative → paid social + web analytics (semantic)
    draw_line(ax, dim_positions["dim_campaign_initiative"],
              fact_positions["fact_paid_social_daily"], linestyle="--")
    draw_line(ax, dim_positions["dim_campaign_initiative"],
              fact_positions["fact_web_analytics_daily"], linestyle="--")

    # dim_podcast → fact_podcast_daily
    draw_line(ax, dim_positions["dim_podcast"], fact_positions["fact_podcast_daily"])

    # Source-grain to daily relationship (dotted)
    ax.annotate("", xy=detail_positions["fact_ecommerce_transactions"],
                xytext=fact_positions["fact_ecommerce_daily"],
                arrowprops=dict(arrowstyle="->", color=SLATE,
                                linestyle=":", linewidth=1.2),
                zorder=1)
    ax.annotate("", xy=detail_positions["fact_web_analytics_events"],
                xytext=fact_positions["fact_web_analytics_daily"],
                arrowprops=dict(arrowstyle="->", color=SLATE,
                                linestyle=":", linewidth=1.2),
                zorder=1)

    # --- Legend ---
    legend_y = 0.4
    legend_items = [
        (DIM_COLOR, "Dimension Table"),
        (FACT_COLOR, "Daily Fact Table"),
        (DETAIL_COLOR, "Source-Grain Detail Table"),
    ]
    for i, (color, label) in enumerate(legend_items):
        x = 1.5 + i * 4.0
        rect = mpatches.FancyBboxPatch(
            (x - 0.3, legend_y - 0.15), 0.6, 0.3,
            boxstyle=f"round,pad=0.04",
            facecolor=color, edgecolor="white", linewidth=1,
            zorder=3,
        )
        ax.add_patch(rect)
        ax.text(x + 0.55, legend_y, label, ha="left", va="center",
                fontsize=8, color=SLATE, fontfamily="sans-serif")

    # Line legend
    ax.plot([12.5, 13.1], [legend_y, legend_y],
            color=LINE_COLOR, linewidth=1.0, zorder=1)
    ax.text(13.3, legend_y, "Join", ha="left", va="center",
            fontsize=8, color=SLATE, fontfamily="sans-serif")
    ax.plot([14.0, 14.6], [legend_y, legend_y],
            color=LINE_COLOR, linewidth=1.0, linestyle="--", zorder=1)
    ax.text(14.8, legend_y, "Semantic", ha="left", va="center",
            fontsize=8, color=SLATE, fontfamily="sans-serif")

    # --- Save ---
    out_dir = Path(__file__).resolve().parent.parent / "data_warehouse" / "documentation"
    out_path = out_dir / "final_data_model_diagram.png"
    fig.savefig(out_path, bbox_inches="tight", facecolor="white", dpi=300)
    print(f"Saved: {out_path}")

    # Also save to analysis/output for convenience
    out2 = Path(__file__).resolve().parent / "output" / "final_data_model_diagram.png"
    fig.savefig(out2, bbox_inches="tight", facecolor="white", dpi=300)
    print(f"Saved: {out2}")
    plt.close()


if __name__ == "__main__":
    main()
