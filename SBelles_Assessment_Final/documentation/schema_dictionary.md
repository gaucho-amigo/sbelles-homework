# S'Belles Data Warehouse — Schema Dictionary

This document is the primary reference for anyone consuming the S'Belles marketing data warehouse. The warehouse is a Kimball star schema covering six marketing data streams: paid social, web analytics, ecommerce, organic social, podcast, and out-of-home (OOH) airport advertising. It contains six daily fact tables, two source-grain detail tables, and five conformed dimension tables. Data spans 2023-01-01 through 2024-06-30.

---

## Data Warehouse Table Inventory

| Table Name | Type | Rows | Columns | Source Files | Description |
|---|---|---|---|---|---|
| dim_date | dimension | 547 | 10 | generated programmatically | Date spine with day-of-week, month, quarter, seasonal flags |
| dim_geography | dimension | 30 | 7 | derived from all streams + airport reference | Unified geographic entities (DMAs, airports, podcast regions) |
| dim_channel | dimension | 7 | 4 | reference table | Channel taxonomy with paid/organic classification |
| dim_campaign_initiative | dimension | 6 | 5 | derived from paid social + web analytics | Campaign theme bridge for cross-channel linkage |
| dim_podcast | dimension | 5 | 4 | derived from podcast source files | Podcast reference with geographic inference |
| fact_paid_social_daily | daily fact | 24,615 | 17 | 9 files (3 Instagram, 3 Pinterest, 3 TikTok) | Paid advertising spend, impressions, clicks, video metrics |
| fact_web_analytics_daily | daily fact | 46,818 | 10 | 4 files (Q1Q2 2023, Q3Q4 2023, Q1 2024, Q2 2024) | Web traffic aggregated from events: pageviews, sessions, users |
| fact_ecommerce_daily | daily fact | 14,800 | 13 | 3 files (Q1Q2 2023, Q3Q4 2023, Q1Q2 2024) | Transaction aggregates: orders, revenue, discount, cost |
| fact_organic_social_daily | daily fact | 441 | 11 | 2 files (2023, 2024) | Owned TikTok engagement: impressions, views, likes, shares |
| fact_podcast_daily | daily fact | 85 | 10 | 2 files (part1, part2) | Podcast mentions — sparse, only dates with mentions |
| fact_ooh_daily | daily fact | 10,920 | 9 | 1 file (weekly, expanded to daily) | Airport advertising: spend, impressions, placements |
| fact_ecommerce_transactions | source-grain fact | 17,106 | 14 | 3 files (Q1Q2 2023, Q3Q4 2023, Q1Q2 2024) | Individual line items preserving discount and basket detail |
| fact_web_analytics_events | source-grain fact | 51,234 | 12 | 4 files (Q1Q2 2023, Q3Q4 2023, Q1 2024, Q2 2024) | Individual pageview events preserving session and page detail |

**Totals:** 13 tables, 166,834 rows, 21 source files

---

## Source File to Table Mapping

| Source File | Rows | Output Table(s) | Notes |
|---|---|---|---|
| sBelles_paid_instagram_part1.csv | 2,735 | fact_paid_social_daily | Standard schema (17 cols) |
| sBelles_paid_instagram_part2.csv | 2,735 | fact_paid_social_daily | Standard schema (17 cols) |
| sBelles_paid_instagram_part3_schema_drift.csv | 2,735 | fact_paid_social_daily | Schema drift: spend_usd→spend, drop spend_currency (18→17 cols) |
| sBelles_paid_pinterest_part1_schema_drift.csv | 2,735 | fact_paid_social_daily | Schema drift: link_clicks→clicks, add video_25pct/video_50pct as NULL (15→17 cols) |
| sBelles_paid_pinterest_part2.csv | 2,735 | fact_paid_social_daily | Standard schema (17 cols) |
| sBelles_paid_pinterest_part3.csv | 2,735 | fact_paid_social_daily | Standard schema (17 cols) |
| sBelles_paid_tiktok_part1.csv | 2,735 | fact_paid_social_daily | Standard schema (17 cols) |
| sBelles_paid_tiktok_part2_schema_drift.csv | 2,735 | fact_paid_social_daily | Schema drift: views→video_views, add optimization_goal as NULL (16→17 cols) |
| sBelles_paid_tiktok_part3.csv | 2,735 | fact_paid_social_daily | Standard schema (17 cols) |
| sBelles_web_traffic_2023_Q1_Q2.csv | 15,296 | fact_web_analytics_daily, fact_web_analytics_events | All rows used |
| sBelles_web_traffic_2023_Q3_Q4.csv | 20,546 | fact_web_analytics_daily, fact_web_analytics_events | All rows used; authoritative for Dec 2023 |
| sBelles_web_traffic_2024_Q1.csv | 10,768 | fact_web_analytics_daily, fact_web_analytics_events | 3,072 Dec 2023 rows dropped (overlap with Q3Q4) |
| sBelles_web_traffic_2024_Q2.csv | 7,696 | fact_web_analytics_daily, fact_web_analytics_events | All rows used |
| sBelles_transactions_2023_Q1_Q2.csv | 5,110 | fact_ecommerce_daily, fact_ecommerce_transactions | All rows used |
| sBelles_transactions_2023_Q3_Q4.csv | 6,842 | fact_ecommerce_daily, fact_ecommerce_transactions | All rows used |
| sBelles_transactions_2024_Q1_Q2.csv | 5,154 | fact_ecommerce_daily, fact_ecommerce_transactions | All rows used |
| sBelles_tiktok_owned_2023.csv | 437 | fact_organic_social_daily | Post-level rows aggregated to daily |
| sBelles_tiktok_owned_2024.csv | 209 | fact_organic_social_daily | Post-level rows aggregated to daily |
| sBelles_podcast_mentions_2023_2024_part1.csv | 44 | fact_podcast_daily, dim_podcast | Mention-level rows aggregated to episode-date |
| sBelles_podcast_mentions_2023_2024_part2.csv | 43 | fact_podcast_daily, dim_podcast | Mention-level rows aggregated to episode-date |
| sBelles_ooh_airport_weekly.csv | 1,560 | fact_ooh_daily | Weekly rows expanded to daily (×7) |

**Total raw rows:** 104,291 across 21 files

---

## Dimension Tables

### dim_date

| Column | Data Type | Description | Source |
|---|---|---|---|
| date | date | Calendar date; primary key | generated |
| day_of_week | string | Day name (Monday, Tuesday, etc.) | derived from date |
| day_of_week_num | integer | ISO day number (Monday=1, Sunday=7) | derived from date |
| week_start_date | date | Monday of the ISO week containing this date | derived from date |
| month | integer | Month number (1–12) | derived from date |
| month_name | string | Month name (January, February, etc.) | derived from date |
| quarter | integer | Quarter number (1–4) | derived from date |
| year | integer | Four-digit year | derived from date |
| is_weekend | boolean | True if Saturday or Sunday | derived from day_of_week_num |
| season_flag | string | Seasonal period: back_to_school (Jul 15–Sep 15), black_friday_holiday (Nov 15–Dec 10), or regular | derived from date |

**Grain:** One row per calendar date (547 rows, 2023-01-01 through 2024-06-30).

**Source:** Programmatically generated date spine. No source files.

**Data quality notes:** Complete 547-day date spine with no gaps.

---

### dim_geography

| Column | Data Type | Description | Source |
|---|---|---|---|
| geo_key | integer | Surrogate primary key | generated |
| dma_name | string | Designated Market Area name (nullable — null for OOH and podcast rows) | paid social, web analytics, ecommerce |
| state | string | Two-letter state abbreviation (nullable — null for 2 podcasts with unknown geography) | raw + airport lookup |
| zip_code | string | ZIP code (nullable — currently null for all rows, reserved for future) | raw |
| airport_code | string | IATA airport code (nullable — only populated for OOH rows) | OOH source |
| airport_name | string | Full airport name (nullable — only populated for OOH rows) | OOH source |
| geo_scope | string | Geographic scope: local (GA digital/ecommerce), national (OOH airports), or inferred (podcast) | derived |

**Grain:** One row per unique geographic entity across all data streams (30 rows).

**Source:** Geography-bearing columns from paid social, web analytics, ecommerce, podcast, and OOH sources. OOH airport-to-state mapping from `reference_data/airport_lookup.csv` (OurAirports open dataset).

**Data quality notes:** Deduplicated across all source files. All 20 OOH airports matched to states.

---

### dim_channel

| Column | Data Type | Description | Source |
|---|---|---|---|
| channel_key | integer | Primary key | reference |
| channel_name | string | Channel identifier (instagram, pinterest, tiktok, organic_tiktok, web, podcast, ooh_airport) | reference |
| channel_group | string | Grouping (paid_social, organic_social, web_analytics, earned_media, ooh) | reference |
| is_paid | boolean | Whether the channel involves paid media spend | reference |

**Grain:** One row per marketing channel (7 rows).

**Source:** Manually populated reference table.

**Data quality notes:** Static reference table. No issues.

---

### dim_campaign_initiative

| Column | Data Type | Description | Source |
|---|---|---|---|
| initiative_key | integer | Surrogate primary key | generated |
| initiative_name | string | Common campaign theme name | derived from campaign naming patterns |
| paid_social_campaign_pattern | string | Comma-separated paid social campaign_name values (nullable — null for web-only initiatives) | paid social campaign_name |
| web_analytics_campaign_value | string | Corresponding web analytics campaign value (nullable — null for Teen Trends) | web analytics campaign |
| notes | string | Mapping gaps or caveats (nullable) | manual |

**Grain:** One row per campaign initiative theme (6 rows).

**Source:** Manually derived bridge table based on campaign naming analysis from paid social and web analytics sources.

**Data quality notes:** No direct foreign key between paid social and web analytics campaigns. This bridge codifies a semantic mapping. Web analytics rows with null campaign (~16% of traffic) represent direct/organic traffic and are not mapped.

---

### dim_podcast

| Column | Data Type | Description | Source |
|---|---|---|---|
| podcast_key | integer | Surrogate primary key | generated |
| podcast_name | string | Podcast title | podcast source files |
| geo_inferred | string | Geography inference: "explicit" if name contains GA/ATL/Peach State, "unknown" otherwise | derived from podcast_name |
| geo_state | string | Inferred state abbreviation (nullable — null for 2 podcasts with unknown geography) | derived |

**Grain:** One row per podcast (5 rows).

**Source:** `sBelles_podcast_mentions_2023_2024_part1.csv`, `sBelles_podcast_mentions_2023_2024_part2.csv`

**Data quality notes:** 3 of 5 podcasts have explicit Georgia references. All 5 have founder mentions, so mentions_founder does not differentiate geography.

---

## Fact Tables

### fact_paid_social_daily

| Column | Data Type | Description | Nullable |
|---|---|---|---|
| date | date | Activity date | No |
| channel | string | Platform name (Instagram, Pinterest, TikTok) | No |
| campaign_name | string | Campaign display name | No |
| campaign_id | string | Campaign identifier (e.g., IN_2077) | No |
| dma_name | string | Designated Market Area | No |
| state | string | State abbreviation (always GA) | No |
| spend | float | Daily spend in USD | No |
| impressions | integer | Ad impressions | No |
| clicks | integer | Link clicks | No |
| video_views | integer | Video view count | No |
| video_25pct | integer | Video 25% completion views | Yes — 2,735 nulls from Pinterest part1 |
| video_50pct | integer | Video 50% completion views | Yes — 2,735 nulls from Pinterest part1 |
| video_75pct | integer | Video 75% completion views | No |
| video_completes | integer | Video 100% completion views | No |
| optimization_goal | string | Campaign optimization objective | Yes — 2,735 nulls from TikTok part2 |
| age_target | string | Target age range | No |
| audience_segment | string | Target audience segment | No |

**Grain:** One row per (date, channel, campaign_id, dma_name). 24,615 rows.

**Source files:** 9 paid social CSVs (3 Instagram, 3 Pinterest, 3 TikTok). See Source File to Table Mapping above.

#### Source-to-Target Column Mapping

| Source File(s) | Original Column | Standardized Column | Data Type | Transformation | Null Handling |
|---|---|---|---|---|---|
| all 9 files | date | date | date | cast to DATE | not nullable |
| all 9 files | channel | channel | string | pass-through | not nullable |
| all 9 files | campaign_name | campaign_name | string | pass-through | not nullable |
| all 9 files | campaign_id | campaign_id | string | pass-through | not nullable |
| all 9 files | dma_name | dma_name | string | pass-through | not nullable |
| all 9 files | state | state | string | pass-through | not nullable |
| 8 standard files | spend | spend | float | pass-through | not nullable |
| instagram_part3 | spend_usd | spend | float | rename spend_usd → spend | not nullable |
| instagram_part3 | spend_currency | *(dropped)* | — | dropped — all values "USD" | — |
| all 9 files | impressions | impressions | integer | pass-through | not nullable |
| 8 standard files | clicks | clicks | integer | pass-through | not nullable |
| pinterest_part1 | link_clicks | clicks | integer | rename link_clicks → clicks | not nullable |
| 8 standard files | video_views | video_views | integer | pass-through | not nullable |
| tiktok_part2 | views | video_views | integer | rename views → video_views | not nullable |
| 7 standard files | video_25pct | video_25pct | integer | pass-through | not nullable in these files |
| pinterest_part1 | *(missing)* | video_25pct | integer | filled with NULL | 2,735 nulls — column absent from source |
| 7 standard files | video_50pct | video_50pct | integer | pass-through | not nullable in these files |
| pinterest_part1 | *(missing)* | video_50pct | integer | filled with NULL | 2,735 nulls — column absent from source |
| all 9 files | video_75pct | video_75pct | integer | pass-through | not nullable |
| all 9 files | video_completes | video_completes | integer | pass-through | not nullable |
| 8 standard files | optimization_goal | optimization_goal | string | pass-through | not nullable in these files |
| tiktok_part2 | *(missing)* | optimization_goal | string | filled with NULL | 2,735 nulls — column absent from source |
| all 9 files | age_target | age_target | string | pass-through | not nullable |
| all 9 files | audience_segment | audience_segment | string | pass-through | not nullable |

**Data quality notes:** Three schema drift files resolved during union. No aggregation needed — source is already at target grain. Financial reconciliation: total spend $5,986,609.08 matches sum across all 9 source files.

---

### fact_web_analytics_daily

| Column | Data Type | Description | Nullable |
|---|---|---|---|
| date | date | Activity date | No |
| traffic_source | string | Traffic source (google, instagram, direct, etc.) | No |
| traffic_medium | string | Traffic medium (cpc, paid_social, none, etc.) | No |
| campaign | string | Campaign tag | Yes — ~16% null, represents direct/organic traffic with no campaign attribution, preserved as-is |
| device_category | string | Device type (desktop, mobile, tablet) | No |
| dma_name | string | Designated Market Area | No |
| state | string | State abbreviation (always GA) | No |
| pageviews | integer | Count of pageview events | No |
| sessions | integer | Count of distinct sessions | No |
| users | integer | Count of distinct users | No |

**Grain:** One row per (date, traffic_source, traffic_medium, campaign, device_category, dma_name, state). 46,818 rows.

**Source files:** 4 web traffic CSVs covering Q1Q2 2023 through Q2 2024.

#### Source-to-Target Column Mapping

| Source File(s) | Original Column | Standardized Column | Data Type | Transformation | Null Handling |
|---|---|---|---|---|---|
| all 4 files | event_datetime | date | date | extract date portion, truncate to DATE | not nullable |
| all 4 files | traffic_source | traffic_source | string | group-by key, pass-through | not nullable |
| all 4 files | traffic_medium | traffic_medium | string | group-by key, pass-through | not nullable |
| all 4 files | campaign | campaign | string | group-by key, pass-through | ~16% null — direct/organic traffic with no campaign tag, preserved as-is |
| all 4 files | device_category | device_category | string | group-by key, pass-through | not nullable |
| all 4 files | dma_name | dma_name | string | group-by key, pass-through | not nullable |
| all 4 files | state | state | string | group-by key, pass-through | not nullable |
| all 4 files | *(all rows)* | pageviews | integer | COUNT(*) of events per group | not nullable (aggregated) |
| all 4 files | session_id | sessions | integer | COUNT(DISTINCT session_id) per group | not nullable (aggregated) |
| all 4 files | user_id | users | integer | COUNT(DISTINCT user_id) per group | not nullable (aggregated) |
| all 4 files | zip_code | *(dropped)* | — | aggregated away; available in dim_geography | — |
| all 4 files | page_url | *(dropped)* | — | aggregated away; page-level detail not in daily grain | — |

**Data quality notes:** 3,072 duplicate December 2023 rows dropped from Q1 2024 file before concatenation. Q3Q4 2023 file treated as authoritative for December. 54,306 raw rows → 51,234 after dedup → 46,818 daily rows after aggregation.

---

### fact_ecommerce_daily

| Column | Data Type | Description | Nullable |
|---|---|---|---|
| date | date | Order date | No |
| dma_name | string | Designated Market Area | No |
| state | string | State abbreviation (always GA) | No |
| product_category | string | Product category (Girls Bottoms, Girls Dresses, Girls Tops) | No |
| size | string | Product size (XS, S, M, L) | No |
| promo_flag | integer | Whether a promotion was applied (0/1) | No |
| orders | integer | Count of distinct orders | No |
| line_items | integer | Number of line items (transaction rows) | No |
| total_quantity | integer | Total units sold | No |
| gross_revenue | float | Total line revenue (may include negative values from over-discounted items) | No |
| total_discount | float | Total discount amount in dollars | No |
| total_cost | float | Total product cost | No |
| avg_unit_price | float | Average unit selling price (unweighted mean across line items) | No |

**Grain:** One row per (date, dma_name, state, product_category, size, promo_flag). 14,800 rows.

**Source files:** 3 transaction CSVs covering Q1Q2 2023 through Q1Q2 2024.

#### Source-to-Target Column Mapping

| Source File(s) | Original Column | Standardized Column | Data Type | Transformation | Null Handling |
|---|---|---|---|---|---|
| all 3 files | order_datetime | date | date | extract date portion, truncate to DATE | not nullable |
| all 3 files | dma_name | dma_name | string | group-by key, pass-through | not nullable |
| all 3 files | state | state | string | group-by key, pass-through | not nullable |
| all 3 files | product_category | product_category | string | group-by key, pass-through | not nullable |
| all 3 files | size | size | string | group-by key, pass-through | not nullable |
| all 3 files | promo_flag | promo_flag | integer | group-by key, pass-through | not nullable |
| all 3 files | order_id | orders | integer | COUNT(DISTINCT order_id) per group | not nullable (aggregated) |
| all 3 files | *(all rows)* | line_items | integer | COUNT(*) of line-item rows per group | not nullable (aggregated) |
| all 3 files | quantity | total_quantity | integer | SUM(quantity) per group | not nullable (aggregated) |
| all 3 files | line_revenue | gross_revenue | float | SUM(line_revenue) per group; includes 105 negative-revenue rows | not nullable (aggregated) |
| all 3 files | discount_per_unit, quantity | total_discount | float | SUM(discount_per_unit × quantity) per group | not nullable (aggregated) |
| all 3 files | unit_cost, quantity | total_cost | float | SUM(unit_cost × quantity) per group | not nullable (aggregated) |
| all 3 files | unit_price | avg_unit_price | float | MEAN(unit_price) per group — unweighted | not nullable (aggregated) |
| all 3 files | zip_code | *(dropped)* | — | aggregated away; available in dim_geography | — |
| all 3 files | user_id | *(dropped)* | — | aggregated away; user-level detail not in daily grain | — |

**Data quality notes:** 105 rows (0.6%) have negative line_revenue where discount_per_unit ($20) exceeds unit_price ($19). These flow into gross_revenue as negative contributions and are preserved as legitimate over-discounted transactions. Financial reconciliation: total gross_revenue $498,071.00 matches sum of line_revenue across all 3 source files.

---

### fact_organic_social_daily

| Column | Data Type | Description | Nullable |
|---|---|---|---|
| date | date | Post date | No |
| posts | integer | Number of posts published that day | No |
| followers_eod | integer | End-of-day follower count (snapshot, not cumulative) | No |
| impressions | integer | Total impressions across all posts | No |
| video_views | integer | Total video views | No |
| video_completes | integer | Total video completions | No |
| likes | integer | Total likes | No |
| comments | integer | Total comments | No |
| shares | integer | Total shares | No |
| clicks | integer | Total clicks | No |
| saves | integer | Total saves | No |

**Grain:** One row per date. 441 rows.

**Source files:** `sBelles_tiktok_owned_2023.csv` (437 rows), `sBelles_tiktok_owned_2024.csv` (209 rows).

#### Source-to-Target Column Mapping

| Source File(s) | Original Column | Standardized Column | Data Type | Transformation | Null Handling |
|---|---|---|---|---|---|
| both files | date | date | date | group-by key, cast to DATE | not nullable |
| both files | post_id | posts | integer | COUNT(DISTINCT post_id) per date, using (date, post_id) composite key | not nullable (aggregated) |
| both files | followers | followers_eod | integer | MAX(followers) per date — end-of-day snapshot | not nullable (aggregated) |
| both files | impressions | impressions | integer | SUM(impressions) per date | not nullable (aggregated) |
| both files | video_views | video_views | integer | SUM(video_views) per date | not nullable (aggregated) |
| both files | video_completes | video_completes | integer | SUM(video_completes) per date | not nullable (aggregated) |
| both files | likes | likes | integer | SUM(likes) per date | not nullable (aggregated) |
| both files | comments | comments | integer | SUM(comments) per date | not nullable (aggregated) |
| both files | shares | shares | integer | SUM(shares) per date | not nullable (aggregated) |
| both files | clicks | clicks | integer | SUM(clicks) per date | not nullable (aggregated) |
| both files | saves | saves | integer | SUM(saves) per date | not nullable (aggregated) |
| both files | caption | *(dropped)* | — | text content not included in daily aggregation | — |

**Data quality notes:** Followers column is a noisy point-in-time snapshot, not monotonically increasing (47.7% day-over-day decreases). MAX chosen as end-of-day proxy. Post IDs recycled across years — (date, post_id) composite key used during counting. 2024-01-01 has no rows (non-posting day, New Year's). 646 post-level rows → 441 daily rows.

---

### fact_podcast_daily

| Column | Data Type | Description | Nullable |
|---|---|---|---|
| date | date | Mention date | No |
| podcast_name | string | Podcast title (FK to dim_podcast) | No |
| episode_title | string | Episode title | No |
| host_name | string | Host name | No |
| mentions_brand | integer | Whether brand was mentioned (0/1) | No |
| mentions_founder | integer | Whether founder was mentioned (0/1) | No |
| sentiment | string | Mention sentiment (positive, neutral, mixed) | No |
| estimated_impressions | integer | Estimated audience impressions | No |
| episode_rating | float | Episode rating (3.3–5.0 scale) | No |
| mentions | integer | Number of distinct mentions in this episode on this date | No |

**Grain:** One row per (date, podcast_name, episode_title). 85 rows. Table is sparse — only dates with actual mentions have rows.

**Source files:** `sBelles_podcast_mentions_2023_2024_part1.csv` (44 rows), `sBelles_podcast_mentions_2023_2024_part2.csv` (43 rows).

#### Source-to-Target Column Mapping

| Source File(s) | Original Column | Standardized Column | Data Type | Transformation | Null Handling |
|---|---|---|---|---|---|
| both files | mention_datetime | date | date | extract date portion, truncate to DATE | not nullable |
| both files | podcast_name | podcast_name | string | group-by key, pass-through | not nullable |
| both files | episode_title | episode_title | string | group-by key, pass-through | not nullable |
| both files | host_name | host_name | string | FIRST value within group (stable per episode) | not nullable |
| both files | mentions_brand | mentions_brand | integer | MAX within group (1 if any mention is brand) | not nullable |
| both files | mentions_founder | mentions_founder | integer | MAX within group (1 if any mention is founder) | not nullable |
| both files | sentiment | sentiment | string | FIRST value within group (stable per episode-date) | not nullable |
| both files | estimated_impressions | estimated_impressions | integer | SUM within group (if multiple mentions in same episode-date) | not nullable |
| both files | episode_rating | episode_rating | float | FIRST value within group (stable per episode) | not nullable |
| both files | *(all rows)* | mentions | integer | COUNT(*) of mention rows per (date, podcast_name, episode_title) | not nullable (aggregated) |
| both files | episode_release_date | *(dropped)* | — | always equals mention_datetime date; redundant | — |
| both files | transcript_snippet | *(dropped)* | — | free text not included in fact table | — |

**Data quality notes:** "Teen Trend Watch - Jun 29 2023" appears in both source files with different mention details — separate mentions within the same episode, not duplicates. Both preserved. 87 raw mention rows → 85 episode-date rows. Sparse: 79 unique dates out of 547 possible. Non-mention days are not zero-filled.

---

### fact_ooh_daily

| Column | Data Type | Description | Nullable |
|---|---|---|---|
| date | date | Activity date | No |
| airport_code | string | IATA airport code (FK to dim_geography) | No |
| airport_name | string | Full airport name | No |
| state | string | Two-letter state abbreviation (joined from airport lookup) | No |
| format | string | Ad format (Digital Board, Jet Bridge, Concourse Wrap, Baggage Claim Display) | No |
| audience_segment | string | Target audience segment (Family Leisure Travelers, Frequent Flyers, General Travelers, Traveling Moms) | No |
| spend | float | Daily spend in USD (1/7 of weekly total) | No |
| impressions | float | Daily impressions (1/7 of weekly total) | No |
| placements | integer | Number of active placements (not divided, represents concurrent count) | No |

**Grain:** One row per (date, airport_code, format, audience_segment). 10,920 rows.

**Source files:** `sBelles_ooh_airport_weekly.csv` (1,560 weekly rows).

#### Source-to-Target Column Mapping

| Source File(s) | Original Column | Standardized Column | Data Type | Transformation | Null Handling |
|---|---|---|---|---|---|
| ooh_airport_weekly | week_start_date | date | date | expanded: 7 dates generated per source row (Monday through Sunday) | not nullable |
| ooh_airport_weekly | airport_code | airport_code | string | pass-through | not nullable |
| ooh_airport_weekly | airport_name | airport_name | string | pass-through | not nullable |
| airport_lookup.csv | state | state | string | joined from airport reference on airport_code | not nullable — all 20 airports matched |
| ooh_airport_weekly | format | format | string | pass-through | not nullable |
| ooh_airport_weekly | audience_segment | audience_segment | string | pass-through | not nullable |
| ooh_airport_weekly | spend | spend | float | weekly spend / 7 (uniform daily distribution) | not nullable |
| ooh_airport_weekly | impressions | impressions | float | weekly impressions / 7 (uniform daily distribution) | not nullable |
| ooh_airport_weekly | placements | placements | integer | pass-through (active count, not divided) | not nullable |

**Data quality notes:** 1,560 weekly rows expanded to 10,920 daily rows (7× expansion). Uniform 1/7 distribution for spend and impressions — no day-of-week weighting because no intra-week signal exists in source data. Date range: 2023-01-02 (first Monday) through 2024-06-30. Financial reconciliation: total spend $29,519,757.25 matches source weekly totals.

---

## Source-Grain Detail Tables

### fact_ecommerce_transactions

| Column | Data Type | Description | Nullable |
|---|---|---|---|
| date | date | Order date | No |
| order_id | string | Order identifier | No |
| user_id | string | Customer identifier | No |
| dma_name | string | Designated Market Area | No |
| state | string | State abbreviation (always GA) | No |
| zip_code | string | Customer ZIP code | No |
| product_category | string | Product category (Girls Bottoms, Girls Dresses, Girls Tops) | No |
| size | string | Product size (XS, S, M, L) | No |
| quantity | integer | Units purchased | No |
| unit_price | float | Price per unit in USD | No |
| unit_cost | float | Cost per unit in USD | No |
| discount_per_unit | float | Discount applied per unit in USD | No |
| line_revenue | float | Total line revenue (may be negative when discount exceeds price) | No |
| promo_flag | integer | Whether a promotion was applied (0/1) | No |

**Grain:** One row per line item (one product within an order). 17,106 rows.

**Source files:** 3 transaction CSVs covering Q1Q2 2023 through Q1Q2 2024.

#### Source-to-Target Column Mapping

| Source File(s) | Original Column | Standardized Column | Data Type | Transformation | Null Handling |
|---|---|---|---|---|---|
| all 3 files | order_datetime | date | date | extract date portion, truncate to DATE | not nullable |
| all 3 files | order_id | order_id | string | pass-through | not nullable |
| all 3 files | user_id | user_id | string | pass-through | not nullable |
| all 3 files | dma_name | dma_name | string | pass-through | not nullable |
| all 3 files | state | state | string | pass-through | not nullable |
| all 3 files | zip_code | zip_code | string | pass-through | not nullable |
| all 3 files | product_category | product_category | string | pass-through | not nullable |
| all 3 files | size | size | string | pass-through | not nullable |
| all 3 files | quantity | quantity | integer | pass-through | not nullable |
| all 3 files | unit_price | unit_price | float | pass-through | not nullable |
| all 3 files | unit_cost | unit_cost | float | pass-through | not nullable |
| all 3 files | discount_per_unit | discount_per_unit | float | pass-through | not nullable |
| all 3 files | line_revenue | line_revenue | float | pass-through; includes 105 negative-revenue rows | not nullable |
| all 3 files | promo_flag | promo_flag | integer | pass-through | not nullable |

**Data quality notes:** 17,106 line items concatenated from 3 source files. No rows removed, no aggregation. 105 rows with negative line_revenue preserved. Relationship: SUM(line_revenue) here equals SUM(gross_revenue) in fact_ecommerce_daily for the same group.

---

### fact_web_analytics_events

| Column | Data Type | Description | Nullable |
|---|---|---|---|
| date | date | Event date | No |
| event_datetime | string | Full event timestamp | No |
| user_id | string | User identifier | No |
| session_id | string | Session identifier | No |
| page_url | string | Page URL visited | No |
| traffic_source | string | Traffic source (google, instagram, direct, etc.) | No |
| traffic_medium | string | Traffic medium (cpc, paid_social, none, etc.) | No |
| campaign | string | Campaign tag | Yes — ~16% null, represents direct/organic traffic, preserved as-is |
| device_category | string | Device type (desktop, mobile, tablet) | No |
| dma_name | string | Designated Market Area | No |
| state | string | State abbreviation (always GA) | No |
| zip_code | string | Visitor ZIP code | No |

**Grain:** One row per pageview event. 51,234 rows.

**Source files:** 4 web traffic CSVs covering Q1Q2 2023 through Q2 2024.

#### Source-to-Target Column Mapping

| Source File(s) | Original Column | Standardized Column | Data Type | Transformation | Null Handling |
|---|---|---|---|---|---|
| all 4 files | event_datetime | date | date | extract date portion, truncate to DATE | not nullable |
| all 4 files | event_datetime | event_datetime | string | pass-through | not nullable |
| all 4 files | user_id | user_id | string | pass-through | not nullable |
| all 4 files | session_id | session_id | string | pass-through | not nullable |
| all 4 files | page_url | page_url | string | pass-through | not nullable |
| all 4 files | traffic_source | traffic_source | string | pass-through | not nullable |
| all 4 files | traffic_medium | traffic_medium | string | pass-through | not nullable |
| all 4 files | campaign | campaign | string | pass-through | ~16% null — direct/organic traffic, preserved as-is |
| all 4 files | device_category | device_category | string | pass-through | not nullable |
| all 4 files | dma_name | dma_name | string | pass-through | not nullable |
| all 4 files | state | state | string | pass-through | not nullable |
| all 4 files | zip_code | zip_code | string | pass-through | not nullable |

**Data quality notes:** 3,072 December 2023 rows dropped from Q1 2024 file to resolve overlap with Q3Q4 2023 file. 54,306 raw rows → 51,234 after dedup. No aggregation. Relationship: COUNT(*) here per group equals pageviews in fact_web_analytics_daily for the same group.
