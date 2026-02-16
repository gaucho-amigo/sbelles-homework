# Source-to-Target Mapping

*Phase 1 | S'Belles Marketing Data Warehouse*

---

## 1. fact_paid_social_daily

**Source files:** sBelles_paid_instagram_part1.csv, sBelles_paid_instagram_part2.csv, sBelles_paid_instagram_part3_schema_drift.csv, sBelles_paid_pinterest_part1_schema_drift.csv, sBelles_paid_pinterest_part2.csv, sBelles_paid_pinterest_part3.csv, sBelles_paid_tiktok_part1.csv, sBelles_paid_tiktok_part2_schema_drift.csv, sBelles_paid_tiktok_part3.csv

**Transformation:** Union all 9 files after resolving schema drift. No aggregation — source is already at target grain.

| Source Column | Target Column | Transformation | Notes |
|---|---|---|---|
| date | date | Cast to DATE | Direct pass-through |
| channel | channel | Pass-through | Values: Instagram, Pinterest, TikTok |
| campaign_name | campaign_name | Pass-through | |
| campaign_id | campaign_id | Pass-through | Format: XX_NNNN |
| dma_name | dma_name | Pass-through | 5 GA DMAs |
| state | state | Pass-through | Always "GA" |
| spend | spend | Pass-through | Standard column in 8 of 9 files |
| spend_usd | spend | Rename | Instagram part3 only; rename to `spend` |
| spend_currency | *(dropped)* | Drop column | Instagram part3 only; all values = "USD"; no information added |
| impressions | impressions | Pass-through | |
| clicks | clicks | Pass-through | Standard column in 8 of 9 files |
| link_clicks | clicks | Rename | Pinterest part1 only; rename to `clicks` |
| video_views | video_views | Pass-through | Standard column in 8 of 9 files |
| views | video_views | Rename | TikTok part2 only; rename to `video_views` |
| video_25pct | video_25pct | Pass-through | Missing in Pinterest part1 → fill with null |
| video_50pct | video_50pct | Pass-through | Missing in Pinterest part1 → fill with null |
| video_75pct | video_75pct | Pass-through | |
| video_completes | video_completes | Pass-through | |
| optimization_goal | optimization_goal | Pass-through | Missing in TikTok part2 → fill with null |
| age_target | age_target | Pass-through | |
| audience_segment | audience_segment | Pass-through | |

---

## 2. fact_web_analytics_daily

**Source files:** sBelles_web_traffic_2023_Q1_Q2.csv, sBelles_web_traffic_2023_Q3_Q4.csv, sBelles_web_traffic_2024_Q1.csv, sBelles_web_traffic_2024_Q2.csv

**Transformation:** Deduplicate December 2023 overlap (drop Dec 2023 rows from Q1 2024 file), concatenate, then aggregate from event-level to daily grain.

| Source Column | Target Column | Transformation | Notes |
|---|---|---|---|
| event_datetime | date | Extract date portion | Cast datetime to DATE for grouping |
| traffic_source | traffic_source | Group-by key | Values: direct, email, facebook, google, instagram, tiktok |
| traffic_medium | traffic_medium | Group-by key | Values: cpc, email, none, paid_social |
| campaign | campaign | Group-by key | Nullable; ~16% null = direct/organic traffic; preserved as-is |
| device_category | device_category | Group-by key | Values: desktop, mobile, tablet |
| dma_name | dma_name | Group-by key | 5 GA DMAs |
| state | state | Group-by key | Always "GA" in this dataset; retained for schema consistency |
| *(all rows)* | pageviews | Aggregate: COUNT(*) | Count of event rows per group |
| session_id | sessions | Aggregate: COUNT(DISTINCT) | Distinct sessions per group |
| user_id | users | Aggregate: COUNT(DISTINCT) | Distinct users per group |
| zip_code | *(not in target)* | Dropped | Not included in daily grain; preserved in `fact_web_analytics_events` |
| page_url | *(not in target)* | Dropped | Aggregated away; page-level detail not in daily grain |

**Deduplication detail:** The Q3Q4 2023 file covers through 2023-12-31 and the Q1 2024 file starts at 2023-12-01. All 3,072 December 2023 rows in the Q1 2024 file are exact duplicates of rows in the Q3Q4 file. Drop December 2023 rows from the Q1 2024 file before concatenation.

---

## 3. fact_ecommerce_daily

**Source files:** sBelles_transactions_2023_Q1_Q2.csv, sBelles_transactions_2023_Q3_Q4.csv, sBelles_transactions_2024_Q1_Q2.csv

**Transformation:** Concatenate all 3 files (no overlap), then aggregate from line-item-level to daily grain.

| Source Column | Target Column | Transformation | Notes |
|---|---|---|---|
| order_datetime | date | Extract date portion | Cast datetime to DATE for grouping |
| dma_name | dma_name | Group-by key | 5 GA DMAs |
| state | state | Group-by key | Always "GA" in this dataset; retained for schema consistency |
| product_category | product_category | Group-by key | Values: Girls Bottoms, Girls Dresses, Girls Tops |
| size | size | Group-by key | Values: XS (4-5), S (6-7), M (8-10), L (12-14) |
| promo_flag | promo_flag | Group-by key | Values: 0, 1 |
| order_id | orders | Aggregate: COUNT(DISTINCT) | Distinct orders per group |
| *(all rows)* | line_items | Aggregate: COUNT(*) | Count of line-item rows per group |
| quantity | total_quantity | Aggregate: SUM | Total units sold per group |
| line_revenue | gross_revenue | Aggregate: SUM | Total revenue per group; includes 105 negative-revenue rows |
| discount_per_unit, quantity | total_discount | Aggregate: SUM(discount_per_unit * quantity) | Total discount dollars per group |
| unit_cost, quantity | total_cost | Aggregate: SUM(unit_cost * quantity) | Total product cost per group |
| unit_price | avg_unit_price | Aggregate: MEAN | Average selling price per group |
| zip_code | *(not in target)* | Dropped | Not included in daily grain; preserved in `fact_ecommerce_transactions` |
| user_id | *(not in target)* | Dropped | Aggregated away; user-level detail not in daily grain |

**Data quality note:** 105 rows (0.6%) have negative `line_revenue` where `discount_per_unit` ($20) exceeds `unit_price` ($19). These flow into `gross_revenue` as-is. The `promo_flag` and `discount_per_unit > 0` have perfect 1:1 correlation — both columns are retained.

---

## 4. fact_organic_social_daily

**Source files:** sBelles_tiktok_owned_2023.csv, sBelles_tiktok_owned_2024.csv

**Transformation:** Concatenate both files, then aggregate from post-level to daily grain.

| Source Column | Target Column | Transformation | Notes |
|---|---|---|---|
| date | date | Group-by key | Direct pass-through as DATE |
| post_id | posts | Aggregate: COUNT(DISTINCT) | Uses (date, post_id) composite key; post IDs are recycled across years |
| followers | followers_eod | Aggregate: MAX | End-of-day snapshot; MAX chosen because followers is noisy (47.7% day-over-day decreases) |
| impressions | impressions | Aggregate: SUM | Summed across all posts on the date |
| video_views | video_views | Aggregate: SUM | |
| video_completes | video_completes | Aggregate: SUM | |
| likes | likes | Aggregate: SUM | |
| comments | comments | Aggregate: SUM | |
| shares | shares | Aggregate: SUM | |
| clicks | clicks | Aggregate: SUM | |
| saves | saves | Aggregate: SUM | |
| caption | *(not in target)* | Dropped | Text content not included in daily aggregation |

**Data quality notes:**
- Post IDs are recycled across years (all 209 IDs in 2024 reappear from 2023 with different dates/metrics). The (date, post_id) composite key is used during COUNT(DISTINCT) to avoid miscounting.
- 2024-01-01 has no rows (non-posting day). No output row is produced for this date.

---

## 5. fact_podcast_daily

**Source files:** sBelles_podcast_mentions_2023_2024_part1.csv, sBelles_podcast_mentions_2023_2024_part2.csv

**Transformation:** Concatenate both files. Group by (date, podcast_name, episode_title) — most groups have 1 row; 2 episodes have 2 mentions each.

| Source Column | Target Column | Transformation | Notes |
|---|---|---|---|
| mention_datetime | date | Extract date portion | Cast datetime to DATE |
| podcast_name | podcast_name | Group-by key / pass-through | FK to dim_podcast |
| episode_title | episode_title | Group-by key / pass-through | |
| host_name | host_name | Pass-through | Constant within episode; take first value |
| mentions_brand | mentions_brand | Pass-through | Binary 0/1; take MAX within group (1 if any mention is brand) |
| mentions_founder | mentions_founder | Pass-through | Binary 0/1; take MAX within group |
| sentiment | sentiment | Pass-through | Take first value within group (or mode if multiple) |
| estimated_impressions | estimated_impressions | Aggregate: SUM | Sum if multiple mentions in same episode-date |
| episode_rating | episode_rating | Pass-through | Constant within episode; take first value |
| *(all rows)* | mentions | Aggregate: COUNT(*) | Number of distinct mention rows per episode-date |
| episode_release_date | *(not in target)* | Dropped | Always equals mention_datetime date; redundant |
| transcript_snippet | *(not in target)* | Dropped | Free text not included in fact table |

**Data quality note:** "Teen Trend Watch - Jun 29 2023" appears in both source files with different mention details (different hosts/timestamps). These are separate mentions within the same episode — both are preserved, and the `mentions` column will show count = 2.

---

## 6. fact_ooh_daily

**Source file:** sBelles_ooh_airport_weekly.csv

**Transformation:** Expand each weekly row into 7 daily rows (Monday through Sunday). Divide spend and impressions by 7.

| Source Column | Target Column | Transformation | Notes |
|---|---|---|---|
| week_start_date | date | Expand: generate 7 dates | Monday (week_start_date) through Sunday (+6 days) |
| airport_code | airport_code | Pass-through | FK to dim_geography via airport lookup |
| airport_name | airport_name | Pass-through | |
| format | format | Pass-through | Values: Baggage Claim Display, Concourse Wrap, Digital Board, Jet Bridge |
| audience_segment | audience_segment | Pass-through | Values: Family Leisure Travelers, Frequent Flyers, General Travelers, Traveling Moms |
| spend | spend | Derive: source / 7 | Uniform daily distribution of weekly spend |
| impressions | impressions | Derive: source / 7 | Uniform daily distribution of weekly impressions |
| placements | placements | Pass-through | Active placement count; not divided (represents concurrent placements) |

**Expansion detail:** Each of the 1,560 source rows (78 weeks × 20 airports) produces 7 daily rows, yielding 10,920 rows in the target table. The `date` column ranges from 2023-01-02 (Monday) through 2024-06-30 (Sunday of the week starting 2024-06-24).
