# S'Belles Data Warehouse — Assumptions

Every judgment call made during the design, transformation, and analysis of the S'Belles marketing data warehouse is documented below. Assumptions are grouped into five categories and numbered for reference. Bold titles are designed to be scannable — a reader should be able to skim the bold titles and understand every decision without reading the detail.

---

## Temporal Assumptions

Decisions about time grain, date alignment, and temporal normalization.

1. **All streams normalized to daily grain.** The assignment requires daily granularity. Source granularity varies from event-level (web analytics, ecommerce) to weekly (OOH). Each stream is aggregated or expanded to produce one row per day per grain key combination.

2. **OOH weekly-to-daily expansion uses uniform 1/7 distribution.** Spend and impressions are divided equally across 7 days (Monday through Sunday). Placements are carried forward unchanged as a concurrent count. No day-of-week weighting is applied because no intra-week signal exists in the source data.

3. **Podcast fact table is sparse — no zero-fill.** Only dates with actual mentions have rows. Zero-filling would add ~460 rows of purely null metrics, inflating the table 6× with no analytic value. Podcast is earned media where absence of a mention is a non-event, not a zero-impression event. Downstream analysis can LEFT JOIN from dim_date if a complete calendar spine is needed.

4. **Organic social 2024-01-01 gap treated as a non-posting day.** New Year's Day has no source rows. No output row is produced — this is treated as a legitimate non-posting day, not a data gap.

5. **dim_date seasonal flag date ranges are hard-coded.** Back-to-school: Jul 15–Sep 15. Black Friday/Holiday: Nov 15–Dec 10. All other dates: regular. These ranges are based on typical retail marketing calendars and can be adjusted if S'Belles uses different seasonal boundaries.

---

## Schema Assumptions

Decisions about column naming, data types, and structural standardization.

6. **Union schema with documented nulls for paid social schema drift.** Taking the union of all columns across 9 paid social files preserves all available information (video_25pct, video_50pct, optimization_goal). An intersection approach would drop these columns entirely. Nulls are documented in the schema dictionary with source file attribution.

7. **One consolidated fact table per data stream.** Downstream consumers query a single fact_paid_social_daily table rather than nine separate paid social files. Schema drift is resolved once during ETL, not repeatedly by every consumer.

8. **Kimball star schema chosen over flat file organization.** Denormalized fact tables with conformed dimensions enable cross-channel joins (e.g., joining paid social and web analytics on date and geography). The assignment spec suggests flat datastream folders; this structure was chosen because it mirrors production analytical warehouses and supports downstream causal modeling.

9. **Six data streams defined by source system and analytical use case.** Paid social, web analytics, ecommerce, organic social, podcast, and OOH each map to one daily fact table. This grouping reflects how the data would be queried by analysts and consumed by media mix models.

10. **Source-grain preservation for ecommerce and web analytics.** Both streams have analytically valuable sub-daily detail (line-item transactions, individual pageview events) that is lost during daily aggregation. The pipeline produces both daily aggregate tables and source-grain detail tables from a single read pass.

---

## Aggregation Assumptions

Decisions about how metrics are computed during daily rollup.

11. **Ecommerce avg_unit_price is an unweighted mean.** MEAN(unit_price) per daily group, not quantity-weighted. A day with one $10 item and one $50 item reports $30 avg_unit_price regardless of quantities purchased. This was chosen for simplicity; quantity-weighted average is available by computing gross_revenue / total_quantity.

12. **Organic social followers uses daily MAX.** The followers column is a noisy point-in-time snapshot, not monotonically increasing (47.7% day-over-day decreases). MAX captures the highest observed value per day as a proxy for end-of-day count. SUM would double-count across posts; MEAN would smooth away actual values.

13. **Web analytics sessions = COUNT DISTINCT session_id, users = COUNT DISTINCT user_id.** These are computed per daily group key. Pageviews = COUNT(*) of event rows. These metrics are not additive across groups — summing sessions across traffic sources overcounts users with multiple sources.

14. **Podcast aggregation: FIRST for stable fields, MAX for binary flags, SUM for impressions.** Within each (date, podcast_name, episode_title) group: host_name, sentiment, and episode_rating use FIRST (stable per episode). mentions_brand and mentions_founder use MAX (1 if any mention in the group). estimated_impressions uses SUM. mentions = COUNT(*).

---

## Data Quality Assumptions

Decisions about how anomalies and issues are handled.

15. **Web analytics December 2023 overlap: Q3Q4 file treated as authoritative.** 3,072 rows dated December 2023 appear in both the Q3Q4 2023 file and the Q1 2024 file. The Q3Q4 file was generated for the period that includes December; the Q1 2024 file's December rows are a data extraction overlap. All December rows dropped from Q1 2024 before concatenation.

16. **Ecommerce negative revenue preserved as-is.** 105 rows (0.6%) have discount_per_unit ($20) exceeding unit_price ($19), producing negative line_revenue. These represent legitimate over-discounted transactions. Filtering would understate discount impact and overstate revenue.

17. **Organic social post IDs recycled across years — composite key used.** All 209 post IDs in 2024 reappear from 2023 with different dates and metrics. The pipeline uses (date, post_id) as a composite key throughout to avoid miscounting.

18. **Promo_flag and discount_per_unit have perfect 1:1 correlation — both retained.** promo_flag serves as a convenient boolean filter for daily aggregation group-by. discount_per_unit provides the dollar amount for unit economics analysis. Retaining both avoids information loss.

---

## Attribution and Analytical Assumptions

Decisions about cross-channel linkage and statistical methods.

19. **No direct campaign foreign key between paid social and web analytics.** Paid social uses a "{Platform} {Theme}" naming convention (e.g., "Instagram BTS Moms"). Web analytics uses standalone theme names (e.g., "BTS 2023"). dim_campaign_initiative provides a semantic bridge mapping these conventions.

20. **Web analytics campaign field is an initiative tag, not a paid social FK.** The campaign field appears with every traffic_source/traffic_medium combination equally. Rows with null campaign (~16% of traffic) represent direct/organic traffic with no campaign attribution.

21. **Podcast geography inferred from podcast names, not founder mentions.** 3 podcasts tagged "explicit" Georgia reference (names containing GA, ATL, or Peach State). 2 tagged "unknown" (Suburban Style Chats, Teen Trend Watch). Founder mention presence does not differentiate geography — all 5 podcasts have founder mentions.

22. **DMA values consistent across all streams — no normalization needed.** The same 5 DMA strings (Atlanta GA, Augusta GA, Columbus GA, Macon GA, Savannah GA) appear identically in paid social, web analytics, and ecommerce sources with no spelling variations or formatting differences.

23. **Pearson cross-correlation used for lag analysis.** Raw and deseasonalized (14-day centered rolling mean removed) daily values are correlated at 0–14 day offsets to detect temporal signal flow candidates between channels.

24. **Deseasonalization uses simple subtraction, not percent change.** Observed value minus 14-day centered rolling mean trend. Subtraction avoids division-by-zero on sparse signals like podcast (many days with zero impressions).

25. **Correlations identify association, not causation.** Establishing causal impact requires entropy-based or structural causal methods (e.g., Granger causality, do-calculus) beyond the scope of this analysis. The lag correlations are signal candidates for a proper causal model, not causal claims.

26. **Geographic scope mismatch in spend-to-revenue analysis.** Total marketing spend ($35.5M) includes $29.5M in national OOH airport advertising across 20 states. Ecommerce revenue ($498K) is tracked in Georgia only. Direct spend-to-revenue comparisons at the aggregate level overstate the gap because 83% of spend targets geographies with no tracked conversion path. Georgia-specific analysis compares $6M paid social spend to $498K revenue.
