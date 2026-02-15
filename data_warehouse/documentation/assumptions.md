# S'Belles Data Warehouse — Assumptions

Every judgment call made during the design, transformation, and analysis of the S'Belles marketing data warehouse is documented below. Assumptions are grouped by category and numbered for reference.

---

## Data Organization Assumptions

1. **Kimball star schema chosen** for clean analytical consumption and conformed dimension joins. Denormalized fact tables are optimized for the primary use case: cross-channel marketing analysis.

2. **One consolidated fact table per data stream** rather than per source file. Downstream consumers query a single `fact_paid_social_daily` table rather than nine separate paid social files. Schema drift is resolved once during ETL, not repeatedly by every consumer.

3. **Union schema with documented nulls** for paid social schema drift rather than intersection schema. Taking the union of all columns preserves all available information (`video_25pct`, `video_50pct`, `optimization_goal`). An intersection approach would drop these columns entirely.

4. **Six data streams defined by source system and analytical use case:** paid_social, web_analytics, ecommerce, organic_social, podcast, ooh. Each stream maps to one daily fact table.

---

## Temporal Alignment Assumptions

5. **All streams normalized to daily grain** as required by the assignment. Source granularity varies from event-level (web, ecommerce) to weekly (OOH).

6. **OOH weekly-to-daily expansion uses uniform distribution:** spend and impressions divided by 7 per day, placements carried forward unchanged. No day-of-week weighting applied because no intra-week signal exists in the source data.

7. **Podcast fact table is sparse** — only mention days have rows. Non-mention days are not zero-filled. Rationale: podcast is earned media where absence of a mention is a non-event, not a zero-impression event. Zero-filling would add ~460 rows of purely null metrics, inflating the table 6x with no analytic value.

8. **Organic social 2024-01-01 gap treated as a non-posting day** (New Year's), not a data gap. No output row is produced for this date.

---

## Data Quality Assumptions

9. **Web analytics December 2023 overlap:** Q3Q4 2023 file treated as authoritative. 3,072 duplicate rows dropped from Q1 2024 file. Rationale: Q3Q4 file was generated for the period that includes December; Q1 2024 file's December rows are a data extraction overlap.

10. **Ecommerce negative revenue:** 105 rows with discount_per_unit ($20) exceeding unit_price ($19) preserved as-is. These represent legitimate over-discounted transactions. Filtering would understate discount impact and overstate revenue.

11. **Organic social followers:** daily MAX used as end-of-day snapshot. The followers column is a noisy point-in-time value, not monotonically increasing (47.7% day-over-day decreases). SUM would double-count across posts, MEAN would smooth away actual values.

12. **Organic social post IDs recycled across years.** All 209 post IDs in 2024 reappear from 2023 with different dates and metrics. Composite key (date, post_id) used throughout to avoid miscounting.

13. **Promo_flag perfectly correlates with discount_per_unit > 0.** Both columns retained for readability — promo_flag serves as a convenient boolean filter while total_discount provides the dollar amount.

---

## Geographic Assumptions

14. **Digital marketing (paid social, web analytics, ecommerce) covers Georgia only** across 5 DMAs: Albany GA, Atlanta GA, Augusta-Aiken, Macon GA, Savannah GA.

15. **OOH covers 20 national airports.** Airport-to-state mapping sourced from OurAirports open dataset via `reference/airport_lookup.csv`. All 20 airports matched successfully.

16. **Podcast geography inferred from podcast names:** 3 podcasts tagged "explicit" Georgia reference (Carpool Chronicles GA, Mom Life in the ATL, Peach State Parenting), 2 tagged "unknown" (Suburban Style Chats, Teen Trend Watch). Founder mention presence does not differentiate geography — all 5 podcasts have founder mentions.

17. **DMA values consistent across all streams** with no normalization needed. The same 5 DMA strings appear identically in paid social, web analytics, and ecommerce sources.

---

## Campaign Linkage Assumptions

18. **No direct foreign key between paid social campaign_name/campaign_id and web analytics campaign field.** Paid social uses a "{Platform} {Theme}" naming convention; web analytics uses standalone theme names (sometimes year-suffixed).

19. **dim_campaign_initiative bridge table maps campaign themes semantically:**
    - Paid social "Always On" maps to web "Always On"
    - Paid social "BTS Moms" maps to web "BTS 2023" and "BTS 2024"
    - Paid social "Teen Trends" has no web counterpart
    - Web "Black Friday 2023" and "Email Promo" have no paid social counterpart

20. **Web analytics campaign field is an independent marketing initiative tag,** not a foreign key to paid social. It appears with every traffic_source/traffic_medium combination equally. Rows with null campaign (~16% of traffic) represent direct/organic traffic with no campaign attribution.

---

## Analytical Assumptions

21. **Cross-channel correlations computed using Pearson coefficient** on raw and deseasonalized (14-day centered rolling mean removed) daily values.

22. **Deseasonalization uses simple subtraction** (observed minus trend), not percent change, to avoid division-by-zero on sparse signals like podcast.

23. **Lagged correlations at 0–14 day offsets** used to detect temporal signal flow candidates between channels.

24. **Correlations identify association, not causation.** Establishing causal impact requires entropy-based or structural causal methods beyond the scope of this analysis.

25. **Ecommerce avg_unit_price in daily aggregate is an unweighted mean** across line items, not quantity-weighted. This means a day with one $10 item and one $50 item reports $30 avg_unit_price regardless of quantities purchased.
