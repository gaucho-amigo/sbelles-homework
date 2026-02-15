# S'Belles Data Warehouse — Schema Dictionary

This document is the primary reference for anyone consuming the S'Belles marketing data warehouse. The warehouse is a Kimball star schema covering six marketing data streams: paid social, web analytics, ecommerce, organic social, podcast, and out-of-home (OOH) airport advertising. It contains six daily fact tables, two source-grain detail tables, and five conformed dimension tables. Data spans 2023-01-01 through 2024-06-30.

---

## Dimension Tables

### dim_date

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| date | date | Calendar date; primary key | No | generated |
| day_of_week | string | Day name (Monday, Tuesday, etc.) | No | derived |
| day_of_week_num | integer | ISO day number (Monday=1, Sunday=7) | No | derived |
| week_start_date | date | Monday of the ISO week containing this date | No | derived |
| month | integer | Month number (1–12) | No | derived |
| month_name | string | Month name (January, February, etc.) | No | derived |
| quarter | integer | Quarter number (1–4) | No | derived |
| year | integer | Four-digit year | No | derived |
| is_weekend | boolean | True if Saturday or Sunday | No | derived |
| season_flag | string | Seasonal marketing period: back_to_school (Jul 15–Sep 15), black_friday_holiday (Nov 15–Dec 7), or regular | No | derived |

**Grain:** One row per calendar date.

**Source files:** None — programmatically generated date spine.

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| *(generated)* | date | Date spine from 2023-01-01 to 2024-06-30 (547 days) |
| *(generated)* | day_of_week | Derived from date using dt.day_name() |
| *(generated)* | day_of_week_num | Derived from date using ISO calendar (Monday=1) |
| *(generated)* | week_start_date | Derived from date minus (day_of_week_num - 1) days |
| *(generated)* | month | Extracted from date |
| *(generated)* | month_name | Derived from month |
| *(generated)* | quarter | Derived from month |
| *(generated)* | year | Extracted from date |
| *(generated)* | is_weekend | Derived from day_of_week_num (6 or 7 = True) |
| *(generated)* | season_flag | Rule-based: Jul 15–Sep 15 = back_to_school, Nov 15–Dec 7 = black_friday_holiday, else regular |

**Data quality notes:** No issues. Complete 547-day date spine with no gaps.

---

### dim_geography

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| geo_key | integer | Surrogate primary key | No | generated |
| dma_name | string | Designated Market Area name | Yes — null for OOH and podcast rows which have no DMA | raw |
| state | string | Two-letter state abbreviation | Yes — null for 2 podcasts with unknown geography | reference |
| zip_code | string | ZIP code | Yes — only populated for web/ecommerce rows | raw |
| airport_code | string | IATA airport code | Yes — only populated for OOH rows | raw |
| airport_name | string | Full airport name | Yes — only populated for OOH rows | raw |
| geo_scope | string | Geographic scope: local (GA digital/ecommerce), national (OOH airports), or inferred (podcast) | No | derived |

**Grain:** One row per unique geographic entity across all data streams.

**Source files:** All 21 source CSVs contribute geographic entities. OOH airport-to-state mapping from `reference/airport_lookup.csv` (OurAirports open dataset).

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| *(generated)* | geo_key | Auto-increment surrogate key |
| dma_name | dma_name | Direct from paid_social, web_analytics, ecommerce sources; null for OOH and podcast |
| state | state | Direct from paid_social, web_analytics, ecommerce; hardcoded lookup for OOH airports; inferred from podcast name for podcast |
| zip_code | zip_code | Direct from web_analytics and ecommerce; null for all other streams |
| airport_code | airport_code | Direct from OOH source; null for all other streams |
| airport_name | airport_name | Direct from OOH source; null for all other streams |
| *(derived)* | geo_scope | Rule-based: "local" for GA digital/ecommerce rows, "national" for OOH airport rows, "inferred" for podcast rows |

**Data quality notes:** Deduplicated across all source files to produce one row per unique geographic combination. OOH airport-to-state mapping covers all 20 airports in the dataset.

---

### dim_channel

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| channel_key | integer | Primary key | No | reference |
| channel_name | string | Channel identifier (e.g., instagram, tiktok) | No | reference |
| channel_group | string | Channel grouping (paid_social, organic_social, web_analytics, earned_media, ooh) | No | reference |
| is_paid | boolean | Whether the channel involves paid media spend | No | reference |

**Grain:** One row per marketing channel (7 rows).

**Source files:** None — manually populated reference table.

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| *(manual)* | channel_key | Manually assigned: 1=instagram, 2=pinterest, 3=tiktok, 4=organic_tiktok, 5=web, 6=podcast, 7=ooh_airport |
| *(manual)* | channel_name | Standardized from source data channel column or stream identity |
| *(manual)* | channel_group | Manually classified into 5 groups |
| *(manual)* | is_paid | Manually classified: true for instagram, pinterest, tiktok, ooh_airport |

**Data quality notes:** Static reference table. No issues.

---

### dim_campaign_initiative

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| initiative_key | integer | Surrogate primary key | No | generated |
| initiative_name | string | Common campaign theme name | No | derived |
| paid_social_campaign_pattern | string | Comma-separated paid social campaign_name values that map to this initiative | Yes — null for web-only initiatives (Black Friday, Email Promo, Unattributed) | derived |
| web_analytics_campaign_value | string | Corresponding web analytics campaign column value | Yes — null for Teen Trends (no web counterpart) | derived |
| notes | string | Mapping gaps or caveats | Yes | derived |

**Grain:** One row per campaign initiative theme (6 rows).

**Source files:** None — manually derived bridge table based on campaign naming analysis from paid social and web analytics sources.

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| *(manual)* | initiative_key | Auto-increment surrogate key |
| *(manual)* | initiative_name | Manually derived common theme from campaign naming patterns |
| paid_social: campaign_name | paid_social_campaign_pattern | Extracted theme from "{Platform} {Theme}" naming convention; comma-separated list |
| web_analytics: campaign | web_analytics_campaign_value | Matched by semantic alignment to initiative theme |
| *(manual)* | notes | Documented mapping gaps |

**Data quality notes:** No direct foreign key exists between paid social campaign_id/campaign_name and web analytics campaign. This bridge table codifies a semantic mapping. Web analytics rows with null campaign (~16% of traffic) represent direct/organic traffic and are not mapped to any initiative.

---

### dim_podcast

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| podcast_key | integer | Surrogate primary key | No | generated |
| podcast_name | string | Podcast title | No | raw |
| geo_inferred | string | Geography inference method: "explicit" if name contains GA/ATL/Peach State reference, "unknown" otherwise | No | derived |
| geo_state | string | Inferred state abbreviation | Yes — null for podcasts with unknown geography (Suburban Style Chats, Teen Trend Watch) | derived |

**Grain:** One row per podcast (5 rows).

**Source files:** `sBelles_podcast_mentions_2023_2024_part1.csv`, `sBelles_podcast_mentions_2023_2024_part2.csv`

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| *(generated)* | podcast_key | Auto-increment surrogate key |
| podcast_name | podcast_name | Direct from source; deduplicated to unique values |
| *(derived)* | geo_inferred | "explicit" if podcast_name contains "GA", "ATL", or "Peach State"; "unknown" otherwise |
| *(derived)* | geo_state | "GA" where geo_inferred = "explicit"; null otherwise |

**Data quality notes:** 3 of 5 podcasts have explicit Georgia references. All 5 podcasts have founder mentions, so mentions_founder does not differentiate geography.

---

## Fact Tables

### fact_paid_social_daily

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| date | date | Activity date | No | raw |
| channel | string | Platform name (Instagram, Pinterest, TikTok) | No | raw |
| campaign_name | string | Campaign display name | No | raw |
| campaign_id | string | Campaign identifier (e.g., IN_2077) | No | raw |
| dma_name | string | Designated Market Area | No | raw |
| state | string | State abbreviation (always GA) | No | raw |
| spend | float | Daily spend in USD | No | raw |
| impressions | integer | Ad impressions | No | raw |
| clicks | integer | Link clicks | No | raw |
| video_views | integer | Video view count | No | raw |
| video_25pct | integer | Video 25% completion views | Yes — Pinterest part1 missing this column due to schema drift | raw |
| video_50pct | integer | Video 50% completion views | Yes — Pinterest part1 missing this column due to schema drift | raw |
| video_75pct | integer | Video 75% completion views | No | raw |
| video_completes | integer | Video 100% completion views | No | raw |
| optimization_goal | string | Campaign optimization objective | Yes — TikTok part2 missing this column due to schema drift | raw |
| age_target | string | Target age range | No | raw |
| audience_segment | string | Target audience segment | No | raw |

**Grain:** One row per (date, channel, campaign_id, dma_name).

**Source files:** `sBelles_paid_instagram_part1.csv`, `sBelles_paid_instagram_part2.csv`, `sBelles_paid_instagram_part3_schema_drift.csv`, `sBelles_paid_pinterest_part1_schema_drift.csv`, `sBelles_paid_pinterest_part2.csv`, `sBelles_paid_pinterest_part3.csv`, `sBelles_paid_tiktok_part1.csv`, `sBelles_paid_tiktok_part2_schema_drift.csv`, `sBelles_paid_tiktok_part3.csv`

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| date | date | Cast to DATE |
| channel | channel | Pass-through |
| campaign_name | campaign_name | Pass-through |
| campaign_id | campaign_id | Pass-through |
| dma_name | dma_name | Pass-through |
| state | state | Pass-through |
| spend | spend | Pass-through (8 of 9 files) |
| spend_usd | spend | Rename from spend_usd (Instagram part3 only) |
| spend_currency | *(dropped)* | Dropped — all values "USD", no information added |
| impressions | impressions | Pass-through |
| clicks | clicks | Pass-through (8 of 9 files) |
| link_clicks | clicks | Rename from link_clicks (Pinterest part1 only) |
| video_views | video_views | Pass-through (8 of 9 files) |
| views | video_views | Rename from views (TikTok part2 only) |
| video_25pct | video_25pct | Pass-through; filled with null for Pinterest part1 |
| video_50pct | video_50pct | Pass-through; filled with null for Pinterest part1 |
| video_75pct | video_75pct | Pass-through |
| video_completes | video_completes | Pass-through |
| optimization_goal | optimization_goal | Pass-through; filled with null for TikTok part2 |
| age_target | age_target | Pass-through |
| audience_segment | audience_segment | Pass-through |

**Data quality notes:** Three schema drift files resolved during union. No aggregation needed — source is already at target grain. All 9 files concatenated to produce 24,615 rows.

---

### fact_web_analytics_daily

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| date | date | Activity date | No | derived |
| traffic_source | string | Traffic source (google, instagram, direct, etc.) | No | raw |
| traffic_medium | string | Traffic medium (cpc, paid_social, none, etc.) | No | raw |
| campaign | string | Campaign tag | Yes — null for ~16% of traffic representing direct/organic with no campaign attribution | raw |
| device_category | string | Device type (desktop, mobile, tablet) | No | raw |
| dma_name | string | Designated Market Area | No | raw |
| pageviews | integer | Count of pageview events | No | aggregated |
| sessions | integer | Count of distinct sessions | No | aggregated |
| users | integer | Count of distinct users | No | aggregated |

**Grain:** One row per (date, traffic_source, traffic_medium, campaign, device_category, dma_name).

**Source files:** `sBelles_web_traffic_2023_Q1_Q2.csv`, `sBelles_web_traffic_2023_Q3_Q4.csv`, `sBelles_web_traffic_2024_Q1.csv`, `sBelles_web_traffic_2024_Q2.csv`

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| event_datetime | date | Extracted date portion from event_datetime, truncated to DATE |
| traffic_source | traffic_source | Group-by key, pass-through |
| traffic_medium | traffic_medium | Group-by key, pass-through |
| campaign | campaign | Group-by key, pass-through; null values preserved as-is |
| device_category | device_category | Group-by key, pass-through |
| dma_name | dma_name | Group-by key, pass-through |
| *(all rows)* | pageviews | COUNT(*) of events per group |
| session_id | sessions | COUNT(DISTINCT session_id) per group |
| user_id | users | COUNT(DISTINCT user_id) per group |
| state | *(dropped)* | Always "GA"; redundant with dma_name |
| zip_code | *(dropped)* | Aggregated away; available in dim_geography |
| page_url | *(dropped)* | Aggregated away; page-level detail not in daily grain |

**Data quality notes:** 3,072 duplicate December 2023 rows dropped from Q1 2024 file before concatenation. Q3Q4 2023 file treated as authoritative for December. 54,306 raw rows → 51,234 after dedup → 46,818 daily rows after aggregation.

---

### fact_ecommerce_daily

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| date | date | Order date | No | derived |
| dma_name | string | Designated Market Area | No | raw |
| product_category | string | Product category (Girls Bottoms, Girls Dresses, Girls Tops) | No | raw |
| size | string | Product size (XS, S, M, L) | No | raw |
| promo_flag | integer | Whether a promotion was applied (0/1) | No | raw |
| orders | integer | Count of distinct orders | No | aggregated |
| line_items | integer | Number of line items (transaction rows) | No | aggregated |
| total_quantity | integer | Total units sold | No | aggregated |
| gross_revenue | float | Total line revenue (may include negative values from over-discounted items) | No | aggregated |
| total_discount | float | Total discount amount in dollars | No | aggregated |
| total_cost | float | Total product cost | No | aggregated |
| avg_unit_price | float | Average unit selling price (unweighted mean across line items) | No | aggregated |

**Grain:** One row per (date, dma_name, product_category, size, promo_flag).

**Source files:** `sBelles_transactions_2023_Q1_Q2.csv`, `sBelles_transactions_2023_Q3_Q4.csv`, `sBelles_transactions_2024_Q1_Q2.csv`

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| order_datetime | date | Extracted date portion from order_datetime, truncated to DATE |
| dma_name | dma_name | Group-by key, pass-through |
| product_category | product_category | Group-by key, pass-through |
| size | size | Group-by key, pass-through |
| promo_flag | promo_flag | Group-by key, pass-through |
| order_id | orders | COUNT(DISTINCT order_id) per group |
| *(all rows)* | line_items | COUNT(*) of line-item rows per group |
| quantity | total_quantity | SUM(quantity) per group |
| line_revenue | gross_revenue | SUM(line_revenue) per group; includes 105 negative-revenue rows |
| discount_per_unit, quantity | total_discount | SUM(discount_per_unit * quantity) per group |
| unit_cost, quantity | total_cost | SUM(unit_cost * quantity) per group |
| unit_price | avg_unit_price | MEAN(unit_price) per group (unweighted) |
| state | *(dropped)* | Always "GA"; redundant |
| zip_code | *(dropped)* | Aggregated away; available in dim_geography |
| user_id | *(dropped)* | Aggregated away; user-level detail not in daily grain |

**Data quality notes:** 105 rows (0.6%) have negative line_revenue where discount_per_unit ($20) exceeds unit_price ($19). These flow into gross_revenue as negative contributions and are preserved as legitimate over-discounted transactions. promo_flag and discount_per_unit > 0 have perfect 1:1 correlation; both columns retained.

---

### fact_organic_social_daily

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| date | date | Post date | No | raw |
| posts | integer | Number of posts published that day | No | aggregated |
| followers_eod | integer | End-of-day follower count (snapshot, not cumulative) | No | aggregated |
| impressions | integer | Total impressions across all posts | No | aggregated |
| video_views | integer | Total video views | No | aggregated |
| video_completes | integer | Total video completions | No | aggregated |
| likes | integer | Total likes | No | aggregated |
| comments | integer | Total comments | No | aggregated |
| shares | integer | Total shares | No | aggregated |
| clicks | integer | Total clicks | No | aggregated |
| saves | integer | Total saves | No | aggregated |

**Grain:** One row per date.

**Source files:** `sBelles_tiktok_owned_2023.csv`, `sBelles_tiktok_owned_2024.csv`

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| date | date | Group-by key, pass-through |
| post_id | posts | COUNT(DISTINCT post_id) per date, using (date, post_id) composite key |
| followers | followers_eod | MAX(followers) per date — end-of-day snapshot |
| impressions | impressions | SUM(impressions) per date |
| video_views | video_views | SUM(video_views) per date |
| video_completes | video_completes | SUM(video_completes) per date |
| likes | likes | SUM(likes) per date |
| comments | comments | SUM(comments) per date |
| shares | shares | SUM(shares) per date |
| clicks | clicks | SUM(clicks) per date |
| saves | saves | SUM(saves) per date |
| caption | *(dropped)* | Text content not included in daily aggregation |

**Data quality notes:** Followers column is a noisy point-in-time snapshot, not monotonically increasing (47.7% day-over-day decreases). MAX chosen as end-of-day proxy. Post IDs recycled across years — (date, post_id) composite key used during counting. 2024-01-01 has no rows (non-posting day, New Year's).

---

### fact_podcast_daily

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| date | date | Mention date | No | derived |
| podcast_name | string | Podcast title (FK to dim_podcast) | No | raw |
| episode_title | string | Episode title | No | raw |
| host_name | string | Host name | No | raw |
| mentions_brand | integer | Whether brand was mentioned (0/1) | No | raw |
| mentions_founder | integer | Whether founder was mentioned (0/1) | No | raw |
| sentiment | string | Mention sentiment (positive, neutral, mixed) | No | raw |
| estimated_impressions | integer | Estimated audience impressions | No | aggregated |
| episode_rating | float | Episode rating (3.3–5.0 scale) | No | raw |
| mentions | integer | Number of distinct mentions in this episode on this date | No | aggregated |

**Grain:** One row per (date, podcast_name, episode_title). Table is sparse — only dates with actual mentions have rows.

**Source files:** `sBelles_podcast_mentions_2023_2024_part1.csv`, `sBelles_podcast_mentions_2023_2024_part2.csv`

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| mention_datetime | date | Extracted date portion from mention_datetime, truncated to DATE |
| podcast_name | podcast_name | Group-by key, pass-through |
| episode_title | episode_title | Group-by key, pass-through |
| host_name | host_name | FIRST value within group (stable per episode) |
| mentions_brand | mentions_brand | MAX within group (1 if any mention is brand) |
| mentions_founder | mentions_founder | MAX within group (1 if any mention is founder) |
| sentiment | sentiment | FIRST value within group |
| estimated_impressions | estimated_impressions | SUM within group (if multiple mentions in same episode-date) |
| episode_rating | episode_rating | FIRST value within group (stable per episode) |
| *(all rows)* | mentions | COUNT(*) of mention rows per (date, podcast_name, episode_title) |
| episode_release_date | *(dropped)* | Always equals mention_datetime date; redundant |
| transcript_snippet | *(dropped)* | Free text not included in fact table |

**Data quality notes:** "Teen Trend Watch - Jun 29 2023" appears in both source files with different mention details — these are separate mentions within the same episode, not duplicates. Both preserved. Sparse data: 79 unique dates out of 547 possible. Non-mention days are not zero-filled.

---

### fact_ooh_daily

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| date | date | Activity date | No | derived |
| airport_code | string | IATA airport code (FK to dim_geography) | No | raw |
| airport_name | string | Full airport name | No | raw |
| format | string | Ad format (Digital Board, Jet Bridge, Concourse Wrap, Baggage Claim Display) | No | raw |
| audience_segment | string | Target audience segment (Family Leisure Travelers, Frequent Flyers, General Travelers, Traveling Moms) | No | raw |
| spend | float | Daily spend in USD (1/7 of weekly total) | No | derived |
| impressions | float | Daily impressions (1/7 of weekly total) | No | derived |
| placements | integer | Number of active placements (not divided, represents concurrent count) | No | raw |

**Grain:** One row per (date, airport_code, format, audience_segment).

**Source files:** `sBelles_ooh_airport_weekly.csv`

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| week_start_date | date | Expanded: 7 dates generated per source row, Monday (week_start_date) through Sunday (+6 days) |
| airport_code | airport_code | Pass-through |
| airport_name | airport_name | Pass-through |
| format | format | Pass-through |
| audience_segment | audience_segment | Pass-through |
| spend | spend | Source weekly spend / 7 (uniform daily distribution) |
| impressions | impressions | Source weekly impressions / 7 (uniform daily distribution) |
| placements | placements | Pass-through (active count, not divided) |

**Data quality notes:** 1,560 weekly rows expanded to 10,920 daily rows (7x). Uniform 1/7 distribution for spend and impressions — no day-of-week weighting because no intra-week signal exists in source data. Date range: 2023-01-02 (first Monday) through 2024-06-30 (Sunday of last week).

---

## Source-Grain Detail Tables

### fact_ecommerce_transactions

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| date | date | Order date | No | derived |
| order_id | string | Order identifier | No | raw |
| user_id | string | Customer identifier | No | raw |
| dma_name | string | Designated Market Area | No | raw |
| state | string | State abbreviation (always GA) | No | raw |
| zip_code | string | Customer ZIP code | No | raw |
| product_category | string | Product category (Girls Bottoms, Girls Dresses, Girls Tops) | No | raw |
| size | string | Product size (XS, S, M, L) | No | raw |
| quantity | integer | Units purchased | No | raw |
| unit_price | float | Price per unit in USD | No | raw |
| unit_cost | float | Cost per unit in USD | No | raw |
| discount_per_unit | float | Discount applied per unit in USD | No | raw |
| line_revenue | float | Total line revenue (may be negative when discount exceeds price) | No | raw |
| promo_flag | integer | Whether a promotion was applied (0/1) | No | raw |

**Grain:** One row per line item (one product within an order).

**Source files:** `sBelles_transactions_2023_Q1_Q2.csv`, `sBelles_transactions_2023_Q3_Q4.csv`, `sBelles_transactions_2024_Q1_Q2.csv`

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| order_datetime | date | Extracted date portion from order_datetime, truncated to DATE |
| order_id | order_id | Pass-through |
| user_id | user_id | Pass-through |
| dma_name | dma_name | Pass-through |
| state | state | Pass-through |
| zip_code | zip_code | Pass-through |
| product_category | product_category | Pass-through |
| size | size | Pass-through |
| quantity | quantity | Pass-through |
| unit_price | unit_price | Pass-through |
| unit_cost | unit_cost | Pass-through |
| discount_per_unit | discount_per_unit | Pass-through |
| line_revenue | line_revenue | Pass-through (includes 105 negative-revenue rows) |
| promo_flag | promo_flag | Pass-through |

**Data quality notes:** 17,106 line items concatenated from 3 source files. No rows removed, no aggregation. 105 rows with negative line_revenue preserved as legitimate over-discounted transactions. Relationship: SUM(line_revenue) here equals SUM(gross_revenue) in fact_ecommerce_daily for the same group.

---

### fact_web_analytics_events

| Column Name | Data Type | Description | Nullable | Source |
|---|---|---|---|---|
| date | date | Event date | No | derived |
| event_datetime | string | Full event timestamp | No | raw |
| user_id | string | User identifier | No | raw |
| session_id | string | Session identifier | No | raw |
| page_url | string | Page URL visited | No | raw |
| traffic_source | string | Traffic source (google, instagram, direct, etc.) | No | raw |
| traffic_medium | string | Traffic medium (cpc, paid_social, none, etc.) | No | raw |
| campaign | string | Campaign tag | Yes — null for ~16% of traffic representing direct/organic with no campaign attribution | raw |
| device_category | string | Device type (desktop, mobile, tablet) | No | raw |
| dma_name | string | Designated Market Area | No | raw |
| state | string | State abbreviation (always GA) | No | raw |
| zip_code | string | Visitor ZIP code | No | raw |

**Grain:** One row per pageview event.

**Source files:** `sBelles_web_traffic_2023_Q1_Q2.csv`, `sBelles_web_traffic_2023_Q3_Q4.csv`, `sBelles_web_traffic_2024_Q1.csv`, `sBelles_web_traffic_2024_Q2.csv`

**Source-to-Target Field Mapping:**

| Source Column | Target Column | Transformation |
|---|---|---|
| event_datetime | date | Extracted date portion from event_datetime, truncated to DATE |
| event_datetime | event_datetime | Pass-through |
| user_id | user_id | Pass-through |
| session_id | session_id | Pass-through |
| page_url | page_url | Pass-through |
| traffic_source | traffic_source | Pass-through |
| traffic_medium | traffic_medium | Pass-through |
| campaign | campaign | Pass-through; null values preserved |
| device_category | device_category | Pass-through |
| dma_name | dma_name | Pass-through |
| state | state | Pass-through |
| zip_code | zip_code | Pass-through |

**Data quality notes:** 3,072 December 2023 rows dropped from Q1 2024 file to resolve overlap with Q3Q4 2023 file. 54,306 raw rows → 51,234 after dedup. No aggregation. Relationship: COUNT(*) here per group equals pageviews in fact_web_analytics_daily for the same group.
