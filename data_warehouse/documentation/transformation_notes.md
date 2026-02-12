# S'Belles Data Warehouse — Transformation Notes

> Phase 2 pipeline documentation. Covers every transformation decision
> so a reader can understand the data warehouse without opening the code.

---

## 1. Schema Drift Resolution

Three of the nine paid social source files had non-standard schemas.
The pipeline detects the filename and applies targeted renames/fills
before the union step.

| File | Issue | Resolution |
|------|-------|------------|
| `sBelles_paid_instagram_part3_schema_drift.csv` | `spend_usd` instead of `spend`; extra `spend_currency` column | Renamed `spend_usd` → `spend`; dropped `spend_currency` |
| `sBelles_paid_pinterest_part1_schema_drift.csv` | `link_clicks` instead of `clicks`; missing `video_25pct`, `video_50pct` | Renamed `link_clicks` → `clicks`; filled `video_25pct` and `video_50pct` with `NULL` |
| `sBelles_paid_tiktok_part2_schema_drift.csv` | `views` instead of `video_views`; missing `optimization_goal` | Renamed `views` → `video_views`; filled `optimization_goal` with `NULL` |

After resolution, all 9 files share 17 columns and are concatenated
into `fact_paid_social_daily` with no aggregation (source grain =
target grain).

---

## 2. Web Analytics Deduplication

### Overlap identified

The Q1 2024 file (`sBelles_web_traffic_2024_Q1.csv`) contains
**3,072 rows** dated December 2023, which overlap with the Q3Q4 2023
file (`sBelles_web_traffic_2023_Q3_Q4.csv`).

### Resolution

All rows where `event_datetime` falls in December 2023 are dropped
from the Q1 2024 file before concatenation. The Q3Q4 2023 file is
treated as the authoritative source for Dec 2023 data.

### Row counts

| Step | Rows |
|------|------|
| Total raw rows across 4 files | 54,306 |
| Dec 2023 rows dropped from Q1 2024 | 3,072 |
| Post-dedup concat (pre-aggregation) | 51,234 |
| Post-aggregation (daily grain) | 46,818 |

---

## 3. Daily Aggregation Approach

Each data stream is aggregated from its source grain to a daily grain.
Below are the specifics for each.

### fact_paid_social_daily

- **Source grain:** daily row per (date, channel, campaign_id, dma_name) — already at target grain
- **Target grain:** same — no aggregation needed
- **Action:** Union 9 files, resolve schema drift, sort, write

### fact_web_analytics_daily

- **Source grain:** individual page-view events (one row per event)
- **Target grain:** (date, traffic_source, traffic_medium, campaign, device_category, dma_name, state)
- **Metrics:**
  - `pageviews` = COUNT of events
  - `sessions` = COUNT DISTINCT of `session_id`
  - `users` = COUNT DISTINCT of `user_id`

### fact_ecommerce_daily

- **Source grain:** individual line items (one row per product in an order)
- **Target grain:** (date, dma_name, state, product_category, size, promo_flag)
- **Metrics:**
  - `orders` = COUNT DISTINCT of `order_id`
  - `line_items` = COUNT of rows
  - `total_quantity` = SUM of `quantity`
  - `gross_revenue` = SUM of `line_revenue`
  - `total_discount` = SUM of (`discount_per_unit` * `quantity`)
  - `total_cost` = SUM of (`unit_cost` * `quantity`)
  - `avg_unit_price` = MEAN of `unit_price`

### fact_organic_social_daily

- **Source grain:** post-level rows (one row per post per day)
- **Target grain:** (date) — single row per day
- **Metrics:**
  - `posts` = COUNT DISTINCT of `post_id`
  - `followers_eod` = MAX of `followers` (see Section 6)
  - All engagement metrics (`impressions`, `video_views`, `video_completes`, `likes`, `comments`, `shares`, `clicks`, `saves`) = SUM

### fact_podcast_daily

- **Source grain:** individual mention-level rows
- **Target grain:** (date, podcast_name, episode_title)
- **Metrics:**
  - `host_name` = FIRST (stable per episode)
  - `mentions_brand` = MAX (binary flag — 1 if any mention is brand)
  - `mentions_founder` = MAX (binary flag)
  - `sentiment` = FIRST (stable per episode-date)
  - `estimated_impressions` = SUM
  - `episode_rating` = FIRST (stable per episode)
  - `mentions` = COUNT of mention rows

### fact_ooh_daily

- **Source grain:** weekly rows (one per week-airport-format-segment)
- **Target grain:** (date, airport_code, format, audience_segment)
- **Action:** Weekly-to-daily expansion (see Section 4)

---

## 4. OOH Weekly-to-Daily Expansion

### Source structure

The raw file `sBelles_ooh_airport_weekly.csv` has one row per
(week_start_date, airport_code, format, audience_segment) with weekly
totals for spend, impressions, and placements.

### Expansion logic

Each source row produces **7 daily rows** (day 0 through day 6 from
`week_start_date`).

| Column | Daily value | Rationale |
|--------|-------------|-----------|
| `spend` | `weekly_spend / 7` | Uniform distribution assumption — no intra-week signal available |
| `impressions` | `weekly_impressions / 7` | Same uniform assumption |
| `placements` | `weekly_placements` (unchanged) | Represents active placement count, not a flow metric |

### Date boundary note

The last `week_start_date` in the raw data is 2024-06-24. Expanding 7
days forward produces dates through 2024-06-30, which stays within the
warehouse boundary. The `validate_date_range` check in the pipeline
confirms no dates exceed 2024-06-30.

### Scale

1,560 weekly rows → 10,920 daily rows (7x expansion confirmed).

---

## 5. Ecommerce Negative Revenue

### Observation

A subset of transaction line items have `line_revenue < 0`. This occurs
when `discount_per_unit > unit_price`, making the effective per-unit
revenue negative.

### Decision

**Preserved as-is.** These rows are legitimate records of deeply
discounted sales (e.g., promo overshoot). Filtering them out would
understate discount impact and overstate revenue. They flow through
aggregation into `gross_revenue` as negative contributions.

---

## 6. Organic Social Followers: Noisy Snapshot Behavior

### Observation

The `followers` column in the owned TikTok data is a point-in-time
snapshot, not a delta. Multiple posts on the same day can report
different `followers` values because the count changes intra-day.

### Decision

**Daily MAX** is used for `followers_eod` (end-of-day followers).
MAX captures the highest observed snapshot for the day, which is the
closest proxy for the end-of-day value in a growing-follower scenario.
SUM would be meaningless (double-counting), and MEAN would smooth away
the actual count.

---

## 7. Podcast Sparsity

### Observation

Podcast mentions are sporadic — only 85 episode-date rows across 18
months. Many calendar days have zero mentions.

### Decision

**No zero-fill.** The fact table only contains rows where a mention
occurred. Rationale:

1. Zero-fill would add ~460 rows of purely NULL metrics, inflating the
   table 6x with no analytic value.
2. Podcast is earned media — absence of a mention is not a
   "zero impressions" event; it's a non-event.
3. Downstream analysis can LEFT JOIN from `dim_date` if a complete
   calendar spine is needed.
