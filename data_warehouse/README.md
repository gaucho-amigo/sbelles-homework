# S'Belles Data Warehouse — Deliverable Structure

This directory contains the final deliverables for the S'Belles marketing data warehouse assessment. The data model follows a Kimball star schema with six daily fact tables and five conformed dimension tables.

## Directory Layout

```
data_warehouse/
├── fact_paid_social/        # Daily paid social metrics (Instagram, Pinterest, TikTok)
├── fact_web_analytics/      # Daily web traffic metrics aggregated from event-level data
├── fact_ecommerce/          # Daily e-commerce transaction metrics aggregated from line items
├── fact_organic_social/     # Daily owned TikTok engagement metrics
├── fact_podcast/            # Podcast mention-level records keyed by date
├── fact_ooh/                # Daily out-of-home airport advertising (expanded from weekly)
├── dimensions/              # Conformed dimension tables (date, geography, channel, campaign, podcast)
├── documentation/           # Data dictionary, lineage, and design documentation
└── README.md                # This file
```

## Fact Tables

| Table | Grain | Source Files |
|---|---|---|
| fact_paid_social | date × channel × campaign_id × dma_name | 9 paid social CSVs (3 per platform) |
| fact_web_analytics | date × traffic_source × traffic_medium × campaign × device_category × dma_name | 4 web traffic CSVs |
| fact_ecommerce | date × dma_name × product_category × size × promo_flag | 3 transaction CSVs |
| fact_organic_social | date | 2 owned TikTok CSVs |
| fact_podcast | date × podcast_name × episode_title | 2 podcast mention CSVs |
| fact_ooh | date × airport_code × format × audience_segment | 1 weekly OOH CSV (expanded to daily) |

## Dimension Tables

| Table | Description |
|---|---|
| dim_date | Date spine 2023-01-01 through 2024-06-30 with seasonal flags |
| dim_geography | Conformed geography across all streams (DMA, state, zip, airport) |
| dim_channel | Channel taxonomy with paid/organic grouping |
| dim_campaign_initiative | Semantic bridge mapping campaign themes across paid social and web |
| dim_podcast | Podcast reference with inferred geography |

## Design Documentation

Full schema specifications, design rationale, and source-to-target mappings are in `docs/` at the repository root.
