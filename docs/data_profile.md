# S'Belles Data Profile — Phase 0

## File Inventory

| Filename | Rows | Cols | Date Range | Granularity | Stream |
|---|---:|---:|---|---|---|
| sBelles_ooh_airport_weekly.csv | 1,560 | 8 | 2023-01-02 → 2024-06-24 | weekly | ooh |
| sBelles_paid_instagram_part1.csv | 2,735 | 17 | 2023-01-01 → 2024-06-30 | daily | paid_social |
| sBelles_paid_instagram_part2.csv | 2,735 | 17 | 2023-01-01 → 2024-06-30 | daily | paid_social |
| sBelles_paid_instagram_part3_schema_drift.csv | 2,735 | 18 | 2023-01-01 → 2024-06-30 | daily | paid_social |
| sBelles_paid_pinterest_part1_schema_drift.csv | 2,735 | 15 | 2023-01-01 → 2024-06-30 | daily | paid_social |
| sBelles_paid_pinterest_part2.csv | 2,735 | 17 | 2023-01-01 → 2024-06-30 | daily | paid_social |
| sBelles_paid_pinterest_part3.csv | 2,735 | 17 | 2023-01-01 → 2024-06-30 | daily | paid_social |
| sBelles_paid_tiktok_part1.csv | 2,735 | 17 | 2023-01-01 → 2024-06-30 | daily | paid_social |
| sBelles_paid_tiktok_part2_schema_drift.csv | 2,735 | 16 | 2023-01-01 → 2024-06-30 | daily | paid_social |
| sBelles_paid_tiktok_part3.csv | 2,735 | 17 | 2023-01-01 → 2024-06-30 | daily | paid_social |
| sBelles_podcast_mentions_2023_2024_part1.csv | 44 | 11 | 2023-01-12 → 2024-06-25 | irregular (~11-day) | podcast |
| sBelles_podcast_mentions_2023_2024_part2.csv | 43 | 11 | 2023-01-22 → 2024-06-30 | irregular (~10-day) | podcast |
| sBelles_tiktok_owned_2023.csv | 437 | 12 | 2023-01-01 → 2023-12-31 | daily | organic_social |
| sBelles_tiktok_owned_2024.csv | 209 | 12 | 2024-01-02 → 2024-06-30 | daily | organic_social |
| sBelles_transactions_2023_Q1_Q2.csv | 5,110 | 14 | 2023-01-01 → 2023-06-30 | event-level | ecommerce |
| sBelles_transactions_2023_Q3_Q4.csv | 6,842 | 14 | 2023-07-01 → 2023-12-31 | event-level | ecommerce |
| sBelles_transactions_2024_Q1_Q2.csv | 5,154 | 14 | 2024-01-01 → 2024-06-30 | event-level | ecommerce |
| sBelles_web_traffic_2023_Q1_Q2.csv | 15,296 | 11 | 2023-01-01 → 2023-06-30 | event-level | web_analytics |
| sBelles_web_traffic_2023_Q3_Q4.csv | 20,546 | 11 | 2023-07-01 → 2023-12-31 | event-level | web_analytics |
| sBelles_web_traffic_2024_Q1.csv | 10,768 | 11 | 2023-12-01 → 2024-03-31 | event-level | web_analytics |
| sBelles_web_traffic_2024_Q2.csv | 7,696 | 11 | 2024-04-01 → 2024-06-30 | event-level | web_analytics |

**Total: 21 files, 98,320 rows**

---

## Per-Datastream Schema Comparison

### Paid Social — Instagram

| Column | Part 1 | Part 2 | Part 3 (drift) |
|---|:---:|:---:|:---:|
| date | Y | Y | Y |
| channel | Y | Y | Y |
| campaign_name | Y | Y | Y |
| campaign_id | Y | Y | Y |
| dma_name | Y | Y | Y |
| state | Y | Y | Y |
| **spend** | **Y** | **Y** | **—** |
| **spend_usd** | **—** | **—** | **Y** |
| **spend_currency** | **—** | **—** | **Y** |
| impressions | Y | Y | Y |
| clicks | Y | Y | Y |
| video_views | Y | Y | Y |
| video_25pct | Y | Y | Y |
| video_50pct | Y | Y | Y |
| video_75pct | Y | Y | Y |
| video_completes | Y | Y | Y |
| optimization_goal | Y | Y | Y |
| age_target | Y | Y | Y |
| audience_segment | Y | Y | Y |

**Drift:** Part 3 renames `spend` → `spend_usd` and adds `spend_currency` (all values = "USD"). Standardization: rename `spend_usd` → `spend`, drop `spend_currency`.

### Paid Social — Pinterest

| Column | Part 1 (drift) | Part 2 | Part 3 |
|---|:---:|:---:|:---:|
| date | Y | Y | Y |
| channel | Y | Y | Y |
| campaign_name | Y | Y | Y |
| campaign_id | Y | Y | Y |
| dma_name | Y | Y | Y |
| state | Y | Y | Y |
| spend | Y | Y | Y |
| impressions | Y | Y | Y |
| **clicks** | **—** | **Y** | **Y** |
| **link_clicks** | **Y** | **—** | **—** |
| video_views | Y | Y | Y |
| **video_25pct** | **—** | **Y** | **Y** |
| **video_50pct** | **—** | **Y** | **Y** |
| video_75pct | Y | Y | Y |
| video_completes | Y | Y | Y |
| optimization_goal | Y | Y | Y |
| age_target | Y | Y | Y |
| audience_segment | Y | Y | Y |

**Drift:** Part 1 uses `link_clicks` instead of `clicks` and is missing `video_25pct`/`video_50pct`. Standardization: rename `link_clicks` → `clicks`; accept missing video quartile columns as null.

### Paid Social — TikTok

| Column | Part 1 | Part 2 (drift) | Part 3 |
|---|:---:|:---:|:---:|
| date | Y | Y | Y |
| channel | Y | Y | Y |
| campaign_name | Y | Y | Y |
| campaign_id | Y | Y | Y |
| dma_name | Y | Y | Y |
| state | Y | Y | Y |
| spend | Y | Y | Y |
| impressions | Y | Y | Y |
| clicks | Y | Y | Y |
| **video_views** | **Y** | **—** | **Y** |
| **views** | **—** | **Y** | **—** |
| video_25pct | Y | Y | Y |
| video_50pct | Y | Y | Y |
| video_75pct | Y | Y | Y |
| video_completes | Y | Y | Y |
| **optimization_goal** | **Y** | **—** | **Y** |
| age_target | Y | Y | Y |
| audience_segment | Y | Y | Y |

**Drift:** Part 2 renames `video_views` → `views` and drops `optimization_goal` entirely. Standardization: rename `views` → `video_views`; accept missing `optimization_goal` as null.

### Web Analytics

All 4 files share an identical schema:

`event_datetime, user_id, session_id, page_url, traffic_source, traffic_medium, campaign, device_category, dma_name, state, zip_code`

No schema drift detected.

### E-commerce (Transactions)

All 3 files share an identical schema:

`order_id, order_datetime, user_id, dma_name, state, zip_code, product_category, size, quantity, unit_price, unit_cost, discount_per_unit, line_revenue, promo_flag`

No schema drift detected.

### Organic Social (Owned TikTok)

Both files share an identical schema:

`date, post_id, caption, followers, impressions, video_views, video_completes, likes, comments, shares, clicks, saves`

No schema drift detected.

### Podcast Mentions

Both files share an identical schema:

`podcast_name, episode_title, episode_release_date, mention_datetime, host_name, mentions_brand, mentions_founder, transcript_snippet, estimated_impressions, episode_rating, sentiment`

No schema drift detected. 1 shared episode title ("Teen Trend Watch - Jun 29 2023") appears in both files but with different mention details — not a true duplicate.

### OOH (Airport Advertising)

Single file with columns:

`week_start_date, airport_code, airport_name, spend, impressions, placements, format, audience_segment`

---

## Known Issues

### 1. Schema Drift in Paid Social Files

Three distinct schema drift patterns were identified (see schema tables above for full detail):

| Channel | Drifted File | Issue | Resolution |
|---|---|---|---|
| Instagram | part3 | `spend` → `spend_usd`; added `spend_currency` | Rename `spend_usd` → `spend`; drop `spend_currency` |
| Pinterest | part1 | `clicks` → `link_clicks`; missing `video_25pct`, `video_50pct` | Rename `link_clicks` → `clicks`; fill missing cols with null |
| TikTok | part2 | `video_views` → `views`; missing `optimization_goal` | Rename `views` → `video_views`; fill missing col with null |

### 2. Overlapping December 2023 in Web Analytics

`sBelles_web_traffic_2023_Q3_Q4.csv` covers 2023-07-01 → 2023-12-31 and `sBelles_web_traffic_2024_Q1.csv` covers 2023-12-01 → 2024-03-31. The entire month of December 2023 is duplicated:

- Rows in overlap window from Q3/Q4 file: **3,072**
- Rows in overlap window from Q1 2024 file: **3,072**
- All 3,072 rows are **exact duplicates** across all columns

**Resolution:** De-duplicate when concatenating. Drop December 2023 rows from one file (e.g., the Q1 2024 file) before combining.

### 3. OOH Weekly Granularity

- 78 distinct weeks × 20 airports = 1,560 rows (complete grid, no gaps)
- Week start dates are Mondays
- Daily normalization will require expanding each row into 7 daily rows
- Uniform distribution assumption: divide `spend` and `impressions` by 7 for each day
- Alternatively, keep weekly and align other streams to weekly aggregation

### 4. Null Values in Web Analytics `campaign` Column

| File | Null Count | Null % |
|---|---:|---:|
| web_traffic_2023_Q1_Q2.csv | 2,479 | 16.2% |
| web_traffic_2023_Q3_Q4.csv | 3,537 | 17.2% |
| web_traffic_2024_Q1.csv | 1,768 | 16.4% |
| web_traffic_2024_Q2.csv | 1,225 | 15.9% |

These likely represent direct/organic traffic with no campaign attribution. All other files across all streams have zero nulls.

### 5. Podcast Episode Irregularity

- Episodes are irregularly spaced (~10-11 day median interval), not on a fixed schedule
- 1 episode title appears in both part 1 and part 2 but with different mention details (different timestamps, hosts) — these are separate mentions within the same episode, not duplicates
- `mentions_brand` and `mentions_founder` are clean binary (0/1) flags

### 6. Organic TikTok — 2024 Starts Jan 2

The 2024 owned TikTok file begins 2024-01-02 (not 2024-01-01). This is a 1-day gap between the 2023 file (ends 2023-12-31) and 2024 file. Likely a non-posting day (New Year's) but worth noting for completeness.

### 7. No Issues Found

The following checks returned clean results:
- **No exact duplicate rows** in any individual file
- **Date formats are consistent**: `YYYY-MM-DD` for date columns, `YYYY-MM-DD HH:MM:SS` for datetime columns across all files
- **No unexpected dtypes** — all numeric columns parse as int/float, all text as object

---

## Datastream Mapping

| Stream | Files | Total Rows | Date Range | Granularity |
|---|---|---:|---|---|
| **paid_social** | paid_instagram (3), paid_pinterest (3), paid_tiktok (3) | 24,615 | 2023-01-01 → 2024-06-30 | daily |
| **web_analytics** | web_traffic (4) | 54,306 | 2023-01-01 → 2024-06-30 | event-level |
| **ecommerce** | transactions (3) | 17,106 | 2023-01-01 → 2024-06-30 | event-level |
| **organic_social** | tiktok_owned (2) | 646 | 2023-01-01 → 2024-06-30 | daily |
| **podcast** | podcast_mentions (2) | 87 | 2023-01-12 → 2024-06-30 | irregular |
| **ooh** | ooh_airport_weekly (1) | 1,560 | 2023-01-02 → 2024-06-24 | weekly |

**Note:** The web_analytics total of 54,306 includes ~3,072 duplicate December 2023 rows. After de-duplication the true count is ~51,234.
