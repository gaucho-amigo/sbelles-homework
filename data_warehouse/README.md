# S'Belles Data Warehouse — Deliverable Structure

This directory contains the warehouse outputs produced by the ETL in `src/`.

The model includes:
- 6 daily fact tables
- 2 source-grain detail fact tables
- 5 conformed dimension tables

All tables span the project analysis window (`2023-01-01` to `2024-06-30`).

## Directory Layout

```text
data_warehouse/
├── fact_paid_social/        # Daily paid social metrics
├── fact_web_analytics/      # Daily web metrics + event-level detail
├── fact_ecommerce/          # Daily ecommerce metrics + transaction detail
├── fact_organic_social/     # Daily organic TikTok metrics
├── fact_podcast/            # Daily podcast mention metrics
├── fact_ooh/                # Daily OOH metrics (expanded from weekly)
├── dimensions/              # Conformed dimensions
├── documentation/           # Data dictionary, assumptions, and model artifacts
└── README.md
```

## Daily Fact Tables

| Table | Grain | Source Files |
|---|---|---|
| fact_paid_social_daily | date × channel × campaign_id × dma_name | 9 paid social CSVs |
| fact_web_analytics_daily | date × traffic_source × traffic_medium × campaign × device_category × dma_name × state | 4 web traffic CSVs (after Dec 2023 dedup) |
| fact_ecommerce_daily | date × dma_name × state × product_category × size × promo_flag | 3 transaction CSVs |
| fact_organic_social_daily | date | 2 owned TikTok CSVs |
| fact_podcast_daily | date × podcast_name × episode_title | 2 podcast mention CSVs |
| fact_ooh_daily | date × airport_code × format × audience_segment | 1 weekly OOH CSV expanded to daily |

## Source-Grain Detail Tables

| Table | Grain | Purpose |
|---|---|---|
| fact_web_analytics_events | event-level pageview | Preserves deduplicated event detail before daily aggregation |
| fact_ecommerce_transactions | line-item transaction | Preserves transaction detail before daily aggregation |

## Dimension Tables

| Table | Description |
|---|---|
| dim_date | 547-row date spine with calendar attributes and `season_flag` |
| dim_geography | Geographic entities across local DMAs, national airports, and inferred podcast geos (`zip_code` retained but currently null in this deliverable) |
| dim_channel | Channel taxonomy with paid/organic grouping |
| dim_campaign_initiative | Semantic bridge mapping campaign themes across paid social and web |
| dim_podcast | Podcast reference with inferred geography |

## Related Documentation

- Warehouse dictionary: `data_warehouse/documentation/schema_dictionary.md`
- Transform notes: `data_warehouse/documentation/transformation_notes.md`
- Assumptions: `data_warehouse/documentation/assumptions.md`
- Schema design + source mapping: `docs/` at the repo root
