# S'Belles Dimensional Model — Schema Design

*Phase 1 | Kimball Star Schema for Marketing Data Warehouse*

---

## 1. Dimension Tables

### 1.1 dim_date

Standard date dimension spanning the full analysis period with no gaps.

**Row count:** 547 rows (2023-01-01 through 2024-06-30)

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| date | DATE | Primary key. Calendar date. | Generated from date spine 2023-01-01 to 2024-06-30 |
| day_of_week | VARCHAR | Day name (Monday, Tuesday, etc.) | Derived from date |
| day_of_week_num | INT | ISO day number (Monday=1, Sunday=7) | Derived from date |
| week_start_date | DATE | Monday of the ISO week containing this date | Derived from date; always a Monday |
| month | INT | Month number (1–12) | Extracted from date |
| month_name | VARCHAR | Month name (January, February, etc.) | Derived from month |
| quarter | INT | Quarter number (1–4) | Derived from month |
| year | INT | Four-digit year | Extracted from date |
| is_weekend | BOOLEAN | True if Saturday or Sunday | Derived from day_of_week_num (6 or 7) |
| season_flag | VARCHAR | Seasonal marketing period | Rule-based (see below) |

**season_flag rules:**

| Value | Date Range | Rationale |
|---|---|---|
| back_to_school | July 15 – September 15 (inclusive) | Aligns with BTS campaign timing in paid social data |
| black_friday_holiday | November 15 – December 10 (inclusive) | Covers Black Friday through early December holiday push |
| regular | All other dates | Default non-seasonal period |

---

### 1.2 dim_geography

Conformed geography dimension consolidating unique geographic entities across geography-bearing streams (paid social, web analytics, ecommerce, podcast, and OOH). Uses a surrogate key because no single natural key spans all streams.

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| geo_key | INT | Primary key (surrogate, auto-increment) | Generated during ETL |
| dma_name | VARCHAR (nullable) | Designated Market Area name | Direct from paid_social, web_analytics, ecommerce `dma_name` column |
| state | VARCHAR (nullable) | Two-letter state abbreviation | Direct from paid_social, web_analytics, ecommerce `state` column; airport lookup join for OOH airports |
| zip_code | VARCHAR (nullable) | ZIP code (reserved for finer geographic granularity) | Column retained in schema but currently null for all rows in this deliverable |
| airport_code | VARCHAR (nullable) | IATA airport code (OOH only) | Direct from OOH `airport_code` column; null for all other streams |
| airport_name | VARCHAR (nullable) | Full airport name (OOH only) | Direct from OOH `airport_name` column; null for all other streams |
| geo_scope | VARCHAR | Geographic scope classification | Rule-based (see below) |

**geo_scope rules:**

| Value | Applies To | Logic |
|---|---|---|
| local | Paid social, web analytics, ecommerce rows | Georgia DMAs — all digital and ecommerce activity is GA-only |
| national | OOH airport rows | 20 airports across the US; national campaign footprint |
| inferred | Podcast rows | Geography inferred from podcast name; see dim_podcast |

**OOH airport-to-state lookup mapping:**

| airport_code | airport_name | state |
|---|---|---|
| ATL | Hartsfield-Jackson Atlanta International Airport | GA |
| BOS | Logan International Airport | MA |
| BWI | Baltimore/Washington International Airport | MD |
| CLT | Charlotte Douglas International Airport | NC |
| DEN | Denver International Airport | CO |
| DFW | Dallas/Fort Worth International Airport | TX |
| DTW | Detroit Metropolitan Airport | MI |
| IAH | George Bush Intercontinental Airport | TX |
| JFK | John F. Kennedy International Airport | NY |
| LAS | Harry Reid International Airport | NV |
| LAX | Los Angeles International Airport | CA |
| LGA | LaGuardia Airport | NY |
| MCO | Orlando International Airport | FL |
| MIA | Miami International Airport | FL |
| MSP | Minneapolis-Saint Paul International Airport | MN |
| ORD | Chicago O'Hare International Airport | IL |
| PHL | Philadelphia International Airport | PA |
| PHX | Phoenix Sky Harbor International Airport | AZ |
| SEA | Seattle-Tacoma International Airport | WA |
| SFO | San Francisco International Airport | CA |

**Population approach:** Collect all distinct geographic entities from all six streams, deduplicate, and assign surrogate keys. A single row exists for each unique combination of populated fields. For example, (dma_name="Atlanta, GA", state="GA", zip_code=null, airport_code=null) is one row for the paid social/ecommerce geography, while (dma_name=null, state="GA", airport_code="ATL", airport_name="Hartsfield-Jackson...") is a separate row for the OOH geography.

---

### 1.3 dim_channel

Static channel taxonomy table. Populated manually based on the six data streams.

**Row count:** 7 rows

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| channel_key | INT | Primary key | Manually assigned |
| channel_name | VARCHAR | Channel identifier | Standardized from source data `channel` column or stream identity |
| channel_group | VARCHAR | Channel grouping | Manually classified |
| is_paid | BOOLEAN | Whether the channel involves paid media spend | Manually classified |

**Reference data:**

| channel_key | channel_name | channel_group | is_paid |
|---|---|---|---|
| 1 | instagram | paid_social | true |
| 2 | pinterest | paid_social | true |
| 3 | tiktok | paid_social | true |
| 4 | organic_tiktok | organic_social | false |
| 5 | web | web_analytics | false |
| 6 | podcast | earned_media | false |
| 7 | ooh_airport | ooh | true |

---

### 1.4 dim_campaign_initiative

Semantic bridge table mapping campaign themes across paid social and web analytics. No direct foreign key exists between these streams — linkage is thematic, based on campaign naming patterns identified during Phase 0 profiling.

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| initiative_key | INT | Primary key (surrogate) | Generated during ETL |
| initiative_name | VARCHAR | Common campaign theme name | Manually derived from campaign naming analysis |
| paid_social_campaign_pattern | VARCHAR | Comma-separated list of paid social `campaign_name` values that map to this initiative | Matched by extracting theme from "{Platform} {Theme}" naming convention |
| web_analytics_campaign_value | VARCHAR (nullable) | Corresponding web analytics `campaign` column value | Matched by substring/semantic alignment |
| notes | VARCHAR (nullable) | Mapping gaps or caveats | Documented during design |

**Reference data:**

| initiative_key | initiative_name | paid_social_campaign_pattern | web_analytics_campaign_value | notes |
|---|---|---|---|---|
| 1 | Always On | Instagram Always On, Pinterest Always On, TikTok Always On | Always On | Direct theme match across both streams |
| 2 | BTS | Instagram BTS Moms, Pinterest BTS Moms, TikTok BTS Moms | BTS 2023, BTS 2024 | Web uses year-suffixed variants; paid social does not distinguish by year |
| 3 | Teen Trends | Instagram Teen Trends, Pinterest Teen Trends, TikTok Teen Trends | *(null)* | No web analytics counterpart found |
| 4 | Black Friday | *(null)* | Black Friday 2023 | Web/promo only — no paid social campaign for Black Friday |
| 5 | Email Promo | *(null)* | Email Promo | Web/promo only — no paid social campaign; driven by email channel |
| 6 | Unattributed | *(null)* | None | Web traffic with explicit "None" campaign value |

**Notes:**
- Web analytics rows with null/empty `campaign` values (~16% of traffic) represent direct/organic traffic with no campaign attribution. These are not mapped to any initiative — they are preserved as-is in the fact table.
- The `traffic_source` + `traffic_medium` combination in web analytics can identify the originating paid social platform (e.g., instagram/paid_social), but `campaign` is an independent tag not directly tied to paid social campaign IDs.

---

### 1.5 dim_podcast

Podcast reference table with inferred geography based on podcast name analysis.

**Row count:** 5 rows

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| podcast_key | INT | Primary key (surrogate) | Generated during ETL |
| podcast_name | VARCHAR | Podcast title | Direct from source `podcast_name` column |
| geo_inferred | VARCHAR | Geography inference method | "explicit" if name contains GA/ATL/Georgia/Peach State reference; "unknown" otherwise |
| geo_state | VARCHAR (nullable) | Inferred state | "GA" where geo_inferred = "explicit"; null where "unknown" |

**Reference data:**

| podcast_key | podcast_name | geo_inferred | geo_state |
|---|---|---|---|
| 1 | Carpool Chronicles GA | explicit | GA |
| 2 | Mom Life in the ATL | explicit | GA |
| 3 | Peach State Parenting | explicit | GA |
| 4 | Suburban Style Chats | unknown | *(null)* |
| 5 | Teen Trend Watch | unknown | *(null)* |

**Inference logic:** Podcast names containing "GA" (state abbreviation), "ATL" (city/airport code), or "Peach State" (regional reference) are classified as explicitly Georgia-market podcasts. All three geo-tagged podcasts reference the Atlanta/Georgia market, aligning with the core DMA footprint of the digital and ecommerce streams.

---

## 2. Fact Tables

### 2.1 fact_paid_social_daily

Daily paid social advertising metrics across Instagram, Pinterest, and TikTok.

**Grain:** One row per (date, channel, campaign_id, dma_name)

**Source files:** 9 files — 3 per platform (Instagram parts 1–3, Pinterest parts 1–3, TikTok parts 1–3)

**Derivation:** Already at daily grain in source. Union all 9 files with schema drift resolution. No aggregation needed.

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| date | DATE | Activity date (FK to dim_date) | Direct from source `date` |
| channel | VARCHAR | Platform name (FK to dim_channel via lookup) | Direct from source `channel` |
| campaign_name | VARCHAR | Campaign display name | Direct from source `campaign_name` |
| campaign_id | VARCHAR | Campaign identifier (e.g., IN_2077) | Direct from source `campaign_id` |
| dma_name | VARCHAR | Designated Market Area (FK to dim_geography via lookup) | Direct from source `dma_name` |
| state | VARCHAR | State abbreviation | Direct from source `state` |
| spend | FLOAT | Daily spend in USD | Direct from `spend`; renamed from `spend_usd` for Instagram part3 |
| impressions | INT | Ad impressions | Direct from source |
| clicks | INT | Link clicks | Direct from `clicks`; renamed from `link_clicks` for Pinterest part1 |
| video_views | INT | Video view count | Direct from `video_views`; renamed from `views` for TikTok part2 |
| video_25pct | INT (nullable) | Video 25% completion views | Direct from source; null for Pinterest part1 (missing column) |
| video_50pct | INT (nullable) | Video 50% completion views | Direct from source; null for Pinterest part1 (missing column) |
| video_75pct | INT | Video 75% completion views | Direct from source |
| video_completes | INT | Video 100% completion views | Direct from source |
| optimization_goal | VARCHAR (nullable) | Campaign optimization objective | Direct from source; null for TikTok part2 (missing column) |
| age_target | VARCHAR | Target age range | Direct from source |
| audience_segment | VARCHAR | Target audience segment | Direct from source |

**Schema drift resolution:**

| File | Issue | Resolution |
|---|---|---|
| Instagram part3 | `spend` renamed to `spend_usd`; extra `spend_currency` column | Rename `spend_usd` → `spend`; drop `spend_currency` (all values = "USD") |
| Pinterest part1 | `clicks` renamed to `link_clicks`; missing `video_25pct`, `video_50pct` | Rename `link_clicks` → `clicks`; fill `video_25pct` and `video_50pct` with null |
| TikTok part2 | `video_views` renamed to `views`; missing `optimization_goal` | Rename `views` → `video_views`; fill `optimization_goal` with null |

---

### 2.2 fact_web_analytics_daily

Daily web traffic metrics aggregated from event-level pageview data.

**Grain:** One row per (date, traffic_source, traffic_medium, campaign, device_category, dma_name, state)

**Source files:** 4 files — web_traffic_2023_Q1_Q2, web_traffic_2023_Q3_Q4, web_traffic_2024_Q1, web_traffic_2024_Q2

**Derivation:** Aggregated from event-level rows. Deduplicate December 2023 overlap before aggregating.

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| date | DATE | Activity date (FK to dim_date) | Extracted from `event_datetime` (date portion) |
| traffic_source | VARCHAR | Traffic source (google, instagram, etc.) | Direct from source `traffic_source` |
| traffic_medium | VARCHAR | Traffic medium (cpc, paid_social, etc.) | Direct from source `traffic_medium` |
| campaign | VARCHAR (nullable) | Campaign tag | Direct from source `campaign`; null for ~16% of traffic (direct/organic) |
| device_category | VARCHAR | Device type (desktop, mobile, tablet) | Direct from source `device_category` |
| dma_name | VARCHAR | Designated Market Area (FK to dim_geography via lookup) | Direct from source `dma_name` |
| state | VARCHAR | State abbreviation | Direct from source `state` |
| pageviews | INT | Count of pageview events | COUNT(*) of events in group |
| sessions | INT | Distinct sessions | COUNT(DISTINCT session_id) in group |
| users | INT | Distinct users | COUNT(DISTINCT user_id) in group |

**Data quality handling:**

| Issue | Treatment |
|---|---|
| 3,072 duplicate rows in December 2023 (Q3Q4 file overlaps Q1 2024 file) | Deduplicate by dropping December 2023 rows from Q1 2024 file before concatenation |
| Null campaign values (~16% of traffic) | Preserve as-is — represents direct/organic traffic with no campaign attribution |

---

### 2.3 fact_ecommerce_daily

Daily e-commerce transaction metrics aggregated from line-item-level data.

**Grain:** One row per (date, dma_name, state, product_category, size, promo_flag)

**Source files:** 3 files — transactions_2023_Q1_Q2, transactions_2023_Q3_Q4, transactions_2024_Q1_Q2

**Derivation:** Aggregated from line-item rows grouped by grain dimensions.

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| date | DATE | Order date (FK to dim_date) | Extracted from `order_datetime` (date portion) |
| dma_name | VARCHAR | Designated Market Area (FK to dim_geography via lookup) | Direct from source `dma_name` |
| state | VARCHAR | State abbreviation | Direct from source `state` |
| product_category | VARCHAR | Product category (Girls Bottoms, Girls Dresses, Girls Tops) | Direct from source `product_category` |
| size | VARCHAR | Product size (XS, S, M, L) | Direct from source `size` |
| promo_flag | INT | Whether a promotion was applied (0/1) | Direct from source `promo_flag` |
| orders | INT | Distinct orders | COUNT(DISTINCT order_id) in group |
| line_items | INT | Number of line items | COUNT(*) of rows in group |
| total_quantity | INT | Total units sold | SUM(quantity) in group |
| gross_revenue | FLOAT | Total line revenue | SUM(line_revenue) in group |
| total_discount | FLOAT | Total discount amount | SUM(discount_per_unit * quantity) in group |
| total_cost | FLOAT | Total product cost | SUM(unit_cost * quantity) in group |
| avg_unit_price | FLOAT | Average unit selling price | MEAN(unit_price) in group |

**Data quality handling:**

| Issue | Treatment |
|---|---|
| 105 rows with negative line_revenue (discount $20 > unit_price $19) | Preserve as-is. These are valid promo transactions where discount exceeds price. Document in data dictionary. |
| promo_flag and discount_per_unit > 0 have perfect 1:1 correlation | Keep both columns. promo_flag is retained as a convenient filter; total_discount provides the dollar amount. Relationship documented. |

---

### 2.4 fact_organic_social_daily

Daily owned TikTok engagement metrics aggregated from post-level data.

**Grain:** One row per date

**Source files:** 2 files — tiktok_owned_2023, tiktok_owned_2024

**Derivation:** Aggregated from post-level rows. Multiple posts on the same day are summed (except followers, which uses MAX as an end-of-day snapshot).

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| date | DATE | Post date (FK to dim_date) | Direct from source `date` |
| posts | INT | Number of posts published | COUNT(DISTINCT post_id) per date, using (date, post_id) as composite key |
| followers_eod | INT | End-of-day follower count (snapshot) | MAX(followers) per date |
| impressions | INT | Total impressions across all posts | SUM(impressions) per date |
| video_views | INT | Total video views | SUM(video_views) per date |
| video_completes | INT | Total video completions | SUM(video_completes) per date |
| likes | INT | Total likes | SUM(likes) per date |
| comments | INT | Total comments | SUM(comments) per date |
| shares | INT | Total shares | SUM(shares) per date |
| clicks | INT | Total clicks | SUM(clicks) per date |
| saves | INT | Total saves | SUM(saves) per date |

**Data quality handling:**

| Issue | Treatment |
|---|---|
| Followers is noisy (47.7% day-over-day decreases) | Use MAX(followers) per day as end-of-day snapshot; do not sum across posts |
| Post IDs recycled across years | Use (date, post_id) composite key during processing; never rely on post_id alone |
| 1-day gap on 2024-01-01 | Non-posting day (New Year's), not a data gap. No row produced for this date. |

---

### 2.5 fact_podcast_daily

Podcast mention records keyed by date, podcast, and episode.

**Grain:** One row per (date, podcast_name, episode_title)

**Source files:** 2 files — podcast_mentions_2023_2024_part1, podcast_mentions_2023_2024_part2

**Derivation:** Derived from mention_datetime. Table is sparse — only dates with actual mentions have rows. Downstream joins to dim_date handle date coverage.

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| date | DATE | Mention date (FK to dim_date) | Extracted from `mention_datetime` (date portion) |
| podcast_name | VARCHAR | Podcast title (FK to dim_podcast via lookup) | Direct from source `podcast_name` |
| episode_title | VARCHAR | Episode title | Direct from source `episode_title` |
| host_name | VARCHAR | Host name | Direct from source `host_name` |
| mentions_brand | INT | Whether brand was mentioned (0/1) | Direct from source `mentions_brand` |
| mentions_founder | INT | Whether founder was mentioned (0/1) | Direct from source `mentions_founder` |
| sentiment | VARCHAR | Mention sentiment (positive, neutral, mixed) | Direct from source `sentiment` |
| estimated_impressions | INT | Estimated audience impressions | Direct from source `estimated_impressions` |
| episode_rating | FLOAT | Episode rating (3.3–5.0 scale) | Direct from source `episode_rating` |
| mentions | INT | Number of distinct mentions in this episode on this date | COUNT(*) of rows matching (date, podcast_name, episode_title) |

**Data quality handling:**

| Issue | Treatment |
|---|---|
| 1 episode ("Teen Trend Watch - Jun 29 2023") appears in both source files with different mention details | These are separate mentions within the same episode, not duplicates. Both rows are preserved. The `mentions` count reflects this. |
| Sparse data (79 unique dates out of 547) | Do not zero-fill. Sparse representation is correct for episodic data. |

---

### 2.6 fact_ooh_daily

Daily out-of-home airport advertising metrics expanded from weekly source data.

**Grain:** One row per (date, airport_code, format, audience_segment)

**Source files:** 1 file — ooh_airport_weekly

**Derivation:** Each weekly source row is expanded into 7 daily rows (Monday through Sunday of that week). Spend and impressions are divided by 7 for uniform daily distribution. Placements carry forward as-is.

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| date | DATE | Activity date (FK to dim_date) | Generated: 7 dates per source row, starting from `week_start_date` (Monday) through Sunday |
| airport_code | VARCHAR | IATA airport code (FK to dim_geography via lookup) | Direct from source `airport_code` |
| airport_name | VARCHAR | Full airport name | Direct from source `airport_name` |
| format | VARCHAR | Ad format (Digital Board, Jet Bridge, etc.) | Direct from source `format` |
| audience_segment | VARCHAR | Target audience segment | Direct from source `audience_segment` |
| spend | FLOAT | Daily spend (1/7 of weekly) | source `spend` / 7 |
| impressions | FLOAT | Daily impressions (1/7 of weekly) | source `impressions` / 7 |
| placements | INT | Number of active placements | Direct from source `placements` (not divided — represents active count) |

**Data quality handling:**

| Issue | Treatment |
|---|---|
| Weekly-to-daily expansion | Uniform 1/7 distribution for spend and impressions. This is the simplest defensible assumption given no day-of-week signal in source data. |
| Source data is clean — no quality issues found | No special handling needed |
| OOH date range (2023-01-02 to 2024-06-24) is slightly narrower than other streams | Acceptable. First Monday falls on Jan 2, 2023; last complete week ends June 30, 2024 (Sun after June 24 Mon). |

---

### 2.7 fact_ecommerce_transactions

Transaction-level (line-item) ecommerce data preserving full source granularity. Cleaned and date-standardized but not aggregated. Complements `fact_ecommerce_daily` for analyses requiring individual transaction detail.

**Grain:** One row per line item (one row per product within an order)

**Source files:** 3 files — transactions_2023_Q1_Q2, transactions_2023_Q3_Q4, transactions_2024_Q1_Q2

**Derivation:** Concatenated from 3 source files. Date derived from `order_datetime`. No aggregation, no rows removed (including negative revenue rows).

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| date | DATE | Order date (FK to dim_date) | Extracted from `order_datetime` (date portion) |
| order_id | VARCHAR | Order identifier | Direct from source `order_id` |
| user_id | VARCHAR | Customer identifier | Direct from source `user_id` |
| dma_name | VARCHAR | Designated Market Area (FK to dim_geography via lookup) | Direct from source `dma_name` |
| state | VARCHAR | State abbreviation | Direct from source `state` |
| zip_code | VARCHAR | Customer ZIP code | Direct from source `zip_code` |
| product_category | VARCHAR | Product category (Girls Bottoms, Girls Dresses, Girls Tops) | Direct from source `product_category` |
| size | VARCHAR | Product size (XS, S, M, L) | Direct from source `size` |
| quantity | INT | Units purchased | Direct from source `quantity` |
| unit_price | FLOAT | Price per unit | Direct from source `unit_price` |
| unit_cost | FLOAT | Cost per unit | Direct from source `unit_cost` |
| discount_per_unit | FLOAT | Discount applied per unit | Direct from source `discount_per_unit` |
| line_revenue | FLOAT | Total line revenue (may be negative when discount > price) | Direct from source `line_revenue` |
| promo_flag | INT | Whether a promotion was applied (0/1) | Direct from source `promo_flag` |

**Relationship to daily table:** `fact_ecommerce_daily` is the daily rollup of this table, grouped by (date, dma_name, state, product_category, size, promo_flag). SUM(line_revenue) here equals SUM(gross_revenue) in the daily table.

---

### 2.8 fact_web_analytics_events

Event-level (pageview) web analytics data preserving full source granularity. Cleaned, deduplicated (Dec 2023 overlap removed), and date-standardized but not aggregated. Complements `fact_web_analytics_daily` for analyses requiring individual event detail.

**Grain:** One row per pageview event

**Source files:** 4 files — web_traffic_2023_Q1_Q2, web_traffic_2023_Q3_Q4, web_traffic_2024_Q1, web_traffic_2024_Q2

**Derivation:** Concatenated from 4 source files. December 2023 rows dropped from Q1 2024 file to resolve overlap. Date derived from `event_datetime`. No aggregation.

| Column | Data Type | Description | Derivation |
|---|---|---|---|
| date | DATE | Event date (FK to dim_date) | Extracted from `event_datetime` (date portion) |
| event_datetime | DATETIME | Full event timestamp | Direct from source `event_datetime` |
| user_id | VARCHAR | User identifier | Direct from source `user_id` |
| session_id | VARCHAR | Session identifier | Direct from source `session_id` |
| page_url | VARCHAR | Page URL visited | Direct from source `page_url` |
| traffic_source | VARCHAR | Traffic source (google, instagram, etc.) | Direct from source `traffic_source` |
| traffic_medium | VARCHAR | Traffic medium (cpc, paid_social, etc.) | Direct from source `traffic_medium` |
| campaign | VARCHAR (nullable) | Campaign tag; null for direct/organic traffic | Direct from source `campaign` |
| device_category | VARCHAR | Device type (desktop, mobile, tablet) | Direct from source `device_category` |
| dma_name | VARCHAR | Designated Market Area (FK to dim_geography via lookup) | Direct from source `dma_name` |
| state | VARCHAR | State abbreviation | Direct from source `state` |
| zip_code | VARCHAR | Visitor ZIP code | Direct from source `zip_code` |

**Relationship to daily table:** `fact_web_analytics_daily` is the daily rollup of this table, grouped by (date, traffic_source, traffic_medium, campaign, device_category, dma_name, state). COUNT(*) here per group equals `pageviews` in the daily table.

---

## 3. Design Decisions

### 1. Why Kimball star schema

A Kimball-style star schema provides a clean handoff to downstream causal and attribution models. Conformed dimensions (particularly dim_date and dim_geography) enable cross-channel joins, allowing analysts to combine paid social spend with web traffic and ecommerce revenue by date and geography without ad hoc mappings. The denormalized fact tables are optimized for analytical queries — the primary use case for this data warehouse.

### 2. Why one consolidated fact table per stream rather than per source file

Downstream consumers want one table per channel with consistent columns, not nine separate paid social files or four web traffic files. Consolidation during ETL means analysts query a single `fact_paid_social_daily` table rather than joining or unioning files themselves. Schema drift is resolved once during transformation, not repeatedly by every consumer.

### 3. Why union schema with documented nulls for paid social drift rather than intersection

Taking the union of all columns (and filling missing columns with null) preserves all available information. An intersection approach would drop `video_25pct`, `video_50pct`, and `optimization_goal` entirely because they are missing from one file each. The union approach lets downstream consumers decide what to include or exclude based on their analysis needs, rather than making that decision irreversibly at the warehouse level.

### 4. Why dim_date includes seasonal flags

The `season_flag` column directly supports attribution analysis around the two key marketing periods identified in the data: back-to-school (July–September, aligning with the "BTS Moms" campaigns) and Black Friday/holiday (November–December, aligning with the "Black Friday 2023" web campaign). Embedding these flags in the date dimension eliminates the need for downstream consumers to hardcode date ranges in their queries.

### 5. Why dim_campaign_initiative exists

There is no direct foreign key between paid social `campaign_id`/`campaign_name` and web analytics `campaign`. Paid social uses a "{Platform} {Theme}" naming convention while web analytics uses standalone theme names (sometimes year-suffixed). The bridge table codifies the semantic mapping discovered during Phase 0 profiling, enabling cross-channel campaign analysis without requiring analysts to reverse-engineer the relationship.

### 6. Why podcast fact is sparse rather than zero-filled

Podcast mentions are episodic events occurring on ~79 of 547 days. Zero-filling the remaining 468 days would create artificial rows that distort aggregations (e.g., average impressions per day would be drastically understated). Sparse representation accurately reflects that no mention occurred. Downstream consumers join to dim_date when they need a complete date spine, and the absence of a row correctly signals "no data" rather than "zero activity."

### 7. Why OOH uses uniform daily distribution

The source OOH data is weekly with no day-of-week signal (no indication that weekday vs. weekend traffic differs). Uniform 1/7 distribution is the simplest defensible assumption. More sophisticated models (e.g., weighting by airport passenger traffic patterns) would require external data not available in this dataset. The uniform assumption is documented so downstream consumers can apply their own weighting if desired.

### 8. How the two-tier geographic scope works

The digital and ecommerce streams operate exclusively within Georgia (5 DMAs, all in GA). The OOH stream covers 20 airports across the US — a national footprint. The `geo_scope` column in dim_geography distinguishes these tiers: "local" for GA digital/ecommerce, "national" for OOH airports, and "inferred" for podcast geography (derived from podcast names). This allows analysts to filter or segment by geographic scope when combining streams, avoiding misleading aggregations that mix local and national metrics.

### 9. Why source-grain fact tables for ecommerce and web analytics

Daily aggregation is lossy. Discount distributions, basket composition, individual session behavior, and user-level patterns cannot be recovered from daily rollups. Two streams — ecommerce and web analytics — have analytically valuable sub-daily granularity. The pipeline produces both daily aggregates (for cross-channel analysis) and cleaned source-grain tables (for deeper investigation). The other four streams do not warrant source-grain preservation: paid social is already at daily grain, OOH is expanded from weekly (synthetic daily rows), and organic social and podcast are too sparse to justify a separate detail table.

### 10. Cross-channel join pattern

Any combination of fact tables can be joined through dim_date (all facts have a `date` column) and dim_geography (all facts reference a geographic entity that maps to dim_geography). For example, to analyze whether paid social spend in Atlanta correlates with ecommerce revenue in Atlanta, join fact_paid_social_daily and fact_ecommerce_daily on date and dma_name, filtering dim_geography to geo_scope = "local". The dim_campaign_initiative bridge enables further alignment by campaign theme across paid social and web analytics.
