# Grain Analysis & Metric Feasibility — Pre-Schema Design

*Generated 2026-02-10 | Phase 0 profiling for S'Belles take-home*

---

## 1. Fact Table Grain Analysis

### 1a. Paid Social (9 files, 2,735 rows each)

**Grain: one row per date × channel × campaign_id × dma_name**

The minimal unique key `(date, channel, campaign_id, dma_name)` holds across all 9 files. Adding `age_target`, `audience_segment`, or `optimization_goal` to the key is also unique but redundant — these are functionally determined by the 4-column key. The one exception is `sBelles_paid_tiktok_part2_schema_drift.csv`, which is missing the `optimization_goal` column entirely.

| Candidate Key | Result (all 9 files) |
|---|---|
| `(date, channel, campaign_id, dma_name)` | UNIQUE |
| `(date, channel, campaign_id, dma_name, optimization_goal)` | UNIQUE (1 file skipped — missing col) |
| `(date, channel, campaign_id, dma_name, age_target)` | UNIQUE |
| `(date, channel, campaign_id, dma_name, audience_segment)` | UNIQUE |
| `(date, channel, campaign_id, dma_name, age_target, audience_segment)` | UNIQUE |

**Sample rows (paid_instagram_part1):**

| date | channel | campaign_name | dma_name | age_target | audience_segment | optimization_goal |
|---|---|---|---|---|---|---|
| 2023-10-17 | Instagram | Instagram BTS Moms | Columbus, GA | 35-44 | Moms & Daughters | Traffic |
| 2023-09-25 | Instagram | Instagram Always On | Augusta, GA | 35-44 | Teen Daughters | Conversions |
| 2023-07-28 | Instagram | Instagram BTS Moms | Augusta, GA | 25-34 | Suburban Moms | Traffic |
| 2023-11-28 | Instagram | Instagram Always On | Savannah, GA | 13-17 | Teen Daughters | Video Views |
| 2023-07-26 | Instagram | Instagram Always On | Savannah, GA | 25-34 | Moms & Daughters | Video Views |

**Schema implication:** Natural key is the 4-column composite. `age_target`, `audience_segment`, and `optimization_goal` are dimensional attributes, not grain components.

---

### 1b. Web Analytics (4 files, 54,306 total rows)

**Grain: one row per pageview event (event-level)**

Each row represents a single pageview event. The key `(event_datetime, user_id, session_id, page_url)` is unique within individual files but has **3,072 duplicate rows** when combining all files — caused by a date overlap between the Q3Q4 2023 and Q1 2024 files.

| Dimension | Unique Values |
|---|---|
| traffic_source | `direct`, `email`, `facebook`, `google`, `instagram`, `tiktok` |
| traffic_medium | `cpc`, `email`, `none`, `paid_social` |
| device_category | `desktop`, `mobile`, `tablet` |

**Cross-file overlap (DATA QUALITY ISSUE):**

| File Pair | Overlapping Keys |
|---|---|
| Q3Q4 2023 ↔ Q1 2024 | **3,072 rows** (December 2023 — 31 days) |
| All other file pairs | 0 |

The Q3Q4 2023 file covers 2023-07-01 to 2023-12-31. The Q1 2024 file covers **2023-12-01** to 2024-03-31 — it starts a month early. All 3,072 overlapping December rows are byte-identical across all columns. **Deduplication required during ETL.**

**Session/user volume (sample days):**

| Date | Unique Sessions | Unique Users |
|---|---|---|
| 2023-01-01 | 96 | 93 |
| 2023-01-02 | 79 | 76 |
| 2023-01-03 | 80 | 77 |
| 2024-06-28 | 80 | 77 |
| 2024-06-29 | 94 | 95 |
| 2024-06-30 | 96 | 92 |

~80-96 sessions/day, roughly 1:1 sessions to users.

---

### 1c. Ecommerce (3 files, 17,106 total rows)

**Grain: one row per line item (product within an order)**

Multiple rows can share the same `order_id`. Each row represents one product line in an order.

| Metric | Value |
|---|---|
| Total rows | 17,106 |
| Unique order_ids | 11,385 |
| Single-line-item orders | 6,809 (59.8%) |
| Multi-line-item orders | 4,576 (40.2%) |
| Avg line items per order | 1.50 |

**Line items per order distribution:**

| Line Items | Orders |
|---:|---:|
| 1 | 6,809 |
| 2 | 3,437 |
| 3 | 1,134 |
| 4 | 4 |
| 5 | 1 |

| Dimension | Unique Values |
|---|---|
| product_category | `Girls Bottoms`, `Girls Dresses`, `Girls Tops` |
| size | `XS (4-5)`, `S (6-7)`, `M (8-10)`, `L (12-14)` |
| promo_flag | `0`, `1` |

**Order value statistics:**

| Metric | Value |
|---|---|
| Average order value | $43.75 |
| Min order value | **-$3.00** |
| Max order value | $258.00 |

**Negative revenue note:** 105 rows have negative `line_revenue`, all caused by `discount_per_unit` ($20) exceeding `unit_price` ($19). These are all promo orders — likely a data quality issue or an aggressive promo on the cheapest products. See Section 2a for details.

---

### 1d. Organic Social (2 files, 646 total rows)

**Grain: one row per post per day — key is `(date, post_id)`**

Multiple posts can occur on the same date (156 dates have >1 row). The key `(date, post_id)` is unique across all rows.

| Metric | Value |
|---|---|
| Total rows | 646 |
| Unique dates | 441 |
| Dates with >1 row | 156 |
| Unique post_ids | 437 |

**Post ID recycling (DATA QUALITY ISSUE):** All 209 post_ids in the 2024 file also appear in the 2023 file, but mapped to different dates and different metric values. Post IDs are recycled/reused across years — they are NOT globally unique identifiers. The `(date, post_id)` composite key is required.

| post_id | 2023 file | 2024 file |
|---|---|---|
| tt_post_110 | 2023-04-08, 5,374 followers | 2024-04-06, 7,368 followers |
| tt_post_80 | 2023-03-17, 5,371 followers | 2024-03-07, 6,880 followers |
| tt_post_54 | 2023-02-22, 5,487 followers | 2024-02-12, 6,833 followers |

**Followers behavior:** The `followers` column is NOT monotonically increasing. It fluctuates significantly day-over-day (210 decreases out of 440 transitions), and multiple posts on the same day can report different follower counts (156 days with inconsistent values). This suggests `followers` is a noisy snapshot at the time of data pull, not a reliable end-of-day metric.

| Metric | Value |
|---|---|
| First value (2023-01-01) | 4,934 |
| Last value (2024-06-30) | 7,577 |
| Overall trend | Increasing (~+54%) |
| Day-over-day decreases | 210 / 440 (47.7%) |
| Days with inconsistent counts | 156 |

**Schema implication:** Use a daily snapshot approach — pick one follower value per day (e.g., max, or first post of the day). Do not treat as a precise metric.

---

### 1e. Podcast (2 files, 87 total rows)

**Grain: one row per mention per episode — key is `(podcast_name, episode_title, mention_datetime)`**

Most episodes have exactly 1 row. Two episodes have 2 rows each (multiple brand mentions within the same episode).

| Metric | Value |
|---|---|
| Total rows | 87 |
| Unique podcasts | 5 |
| Total unique episodes | 85 |
| Episodes with >1 mention row | 2 |

**Multi-mention episodes:**

| Podcast | Episode | Rows |
|---|---|---|
| Teen Trend Watch | Teen Trend Watch - Jun 29 2023 | 2 |
| Peach State Parenting | Peach State Parenting - Aug 29 2023 | 2 |

**Release date vs. mention date:** Always identical (`mention_datetime` date = `episode_release_date` for all 87 rows). Mentions are recorded at release time, not post-release.

| Dimension | Values |
|---|---|
| sentiment | `positive` (31), `neutral` (30), `mixed` (26) |
| podcast_name | Carpool Chronicles GA, Mom Life in the ATL, Peach State Parenting, Suburban Style Chats, Teen Trend Watch |

**Episodes per podcast:**

| Podcast | Episodes |
|---|---|
| Carpool Chronicles GA | 19 |
| Suburban Style Chats | 19 |
| Teen Trend Watch | 17 |
| Mom Life in the ATL | 15 |
| Peach State Parenting | 15 |

---

### 1f. OOH Airport (1 file, 1,560 rows)

**Grain: one row per week × airport — key is `(week_start_date, airport_code)`**

Each airport has exactly one row per week (1,560 / 20 airports = 78 weeks). The `format` and `audience_segment` values vary per row but are unique within each airport-week — they are attributes of the row, not grain components.

| Candidate Key | Result |
|---|---|
| `(week_start_date, airport_code)` | **UNIQUE** |
| `(week_start_date, airport_code, format)` | UNIQUE (redundant) |
| `(week_start_date, airport_code, audience_segment)` | UNIQUE (redundant) |

| Dimension | Unique Values |
|---|---|
| format | `Baggage Claim Display`, `Concourse Wrap`, `Digital Board`, `Jet Bridge` |
| audience_segment | `Family Leisure Travelers`, `Frequent Flyers`, `General Travelers`, `Traveling Moms` |

---

## 2. Metric Feasibility

### 2a. Ecommerce Revenue Formula

**Formula verified:** `line_revenue = quantity × unit_price − discount_per_unit × quantity`

Tested on 20 random rows: **0 mismatches**. Tested on all 17,106 rows: **0 mismatches**. The formula is reliable.

| Metric | Value |
|---|---|
| Discount range | $0.00 – $20.00 |
| Mean discount | $7.52 |
| Rows with zero discount | 8,543 (49.9%) |
| Rows with non-zero discount | 8,563 (50.1%) |

**Promo flag vs. discount correlation: perfect 1:1**

| | discount > 0 | discount = 0 |
|---|---:|---:|
| promo_flag = 1 | 8,563 | 0 |
| promo_flag = 0 | 0 | 8,543 |

`promo_flag` is fully determined by `discount_per_unit > 0`. No information loss either way.

**Negative revenue rows:** 105 rows (0.6%) have `line_revenue < 0`. All occur when `discount_per_unit = $20` exceeds `unit_price = $19`, yielding -$1/unit. These are all `promo_flag = 1`. This is a data quality issue — the discount exceeds the item price for the cheapest products.

---

### 2b. Organic Social Followers

**Not monotonically increasing.** While the overall trend is upward (+54% from 4,934 to 7,577), the `followers` value decreases day-over-day in 47.7% of transitions (210 out of 440). Multiple posts on the same day also show different follower counts (156 days affected).

**Interpretation:** The `followers` field appears to be a noisy point-in-time snapshot, not a reliable daily metric. For modeling, recommend taking `MAX(followers)` per day as a daily snapshot.

---

### 2c. Podcast Metrics

**Estimated impressions:**

| Stat | Value |
|---|---|
| Min | 5,629 |
| Max | 22,634 |
| Mean | 10,892 |
| Median | 10,117 |
| Stdev | 3,845 |

**Sentiment distribution:**

| Sentiment | Count | % |
|---|---:|---:|
| positive | 31 | 35.6% |
| neutral | 30 | 34.5% |
| mixed | 26 | 29.9% |

**Episode rating:** Range 3.3 – 5.0, mean 4.3, median 4.3.

---

## 3. Date Spine Check

**Full coverage from 2023-01-01 to 2024-06-30 — no gaps.**

| Metric | Value |
|---|---|
| Earliest date (any stream) | 2023-01-01 |
| Latest date (any stream) | 2024-06-30 |
| Total days in range | 547 |
| Days with data in ≥1 stream | **547 (100%)** |
| Days with no data | **0** |

**Per-stream date coverage:**

| Stream | Date Range | Unique Days | Cadence |
|---|---|---:|---|
| paid_social | 2023-01-01 → 2024-06-30 | 547 | Daily (full) |
| web_analytics | 2023-01-01 → 2024-06-30 | 547 | Daily (full) |
| ecommerce | 2023-01-01 → 2024-06-30 | 547 | Daily (full) |
| organic_social | 2023-01-01 → 2024-06-30 | 441 | Near-daily (81%) |
| podcast | 2023-01-12 → 2024-06-30 | 79 | Irregular (~11-day intervals) |
| ooh | 2023-01-02 → 2024-06-24 | 78 | Weekly (Mondays) |

**Schema implication:** A `dim_date` table spanning 2023-01-01 to 2024-06-30 (547 rows) covers all streams. OOH and podcast will have sparse join patterns against a daily date spine — consider a weekly rollup table for OOH analysis.

---

## Data Quality Issues Summary

| Issue | Stream | Severity | Action |
|---|---|---|---|
| 3,072 duplicate rows (Dec 2023 overlap) | Web Analytics | HIGH | Deduplicate during ETL — Q3Q4 2023 and Q1 2024 files overlap |
| Post ID recycling across years | Organic Social | MEDIUM | Use `(date, post_id)` composite key, never `post_id` alone |
| Noisy follower snapshots | Organic Social | LOW | Use daily MAX aggregation |
| 105 negative revenue rows | Ecommerce | LOW | Discount ($20) > unit_price ($19) for cheapest items; flag or cap |
| Missing `optimization_goal` column | Paid Social (TikTok part2) | MEDIUM | Schema drift — handle as NULL during union |
