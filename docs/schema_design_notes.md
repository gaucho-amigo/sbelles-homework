# Schema Design Notes: Targeted Profiling Findings

*Generated 2026-02-10 | Phase 0 profiling for S'Belles take-home*

---

## 1. DMA Standardization Analysis

**Summary:** DMA values are perfectly consistent across all three data streams. All 5 DMAs use identical `"City, ST"` formatting with no whitespace, case, or punctuation drift. All DMAs are in Georgia. No normalization needed.

| dma_name | paid_social | web_traffic | transactions |
|---|:---:|:---:|:---:|
| Atlanta, GA | YES | YES | YES |
| Augusta, GA | YES | YES | YES |
| Columbus, GA | YES | YES | YES |
| Macon, GA | YES | YES | YES |
| Savannah, GA | YES | YES | YES |

- **Unique DMAs per stream:** 5 in each (paid_social, web_traffic, transactions)
- **Near-match/formatting issues:** None detected
- **Schema implication:** `dma_name` can be used as a direct join key across streams with no transformation. A `dim_dma` table is straightforward.

---

## 2. State Standardization Analysis

**Summary:** Only one state value exists across the entire dataset: `"GA"` (2-letter uppercase abbreviation). All three streams are consistent. No full-name vs. abbreviation conflicts.

| state | paid_social | web_traffic | transactions |
|---|:---:|:---:|:---:|
| GA | YES | YES | YES |

- **Format:** 2-letter uppercase abbreviation only
- **Schema implication:** Single-state dataset. State can be used as-is for joins. If mapping OOH airports to geography, the airport lookup will bring in non-GA states (see Section 3).

---

## 3. Airport-to-Geography Mapping

**Summary:** The OOH airport file contains 20 major US airports spanning many states. The file has **no state, DMA, or geographic fields** beyond airport_code and airport_name. An external lookup table is required to map airports to state/DMA.

### OOH File Columns
`week_start_date`, `airport_code`, `airport_name`, `spend`, `impressions`, `placements`, `format`, `audience_segment`

### Unique Airports (20)

| airport_code | airport_name |
|---|---|
| ATL | Hartsfield-Jackson Atlanta International Airport |
| BOS | Logan International Airport |
| BWI | Baltimore/Washington International Airport |
| CLT | Charlotte Douglas International Airport |
| DEN | Denver International Airport |
| DFW | Dallas/Fort Worth International Airport |
| DTW | Detroit Metropolitan Airport |
| IAH | George Bush Intercontinental Airport |
| JFK | John F. Kennedy International Airport |
| LAS | Harry Reid International Airport |
| LAX | Los Angeles International Airport |
| LGA | LaGuardia Airport |
| MCO | Orlando International Airport |
| MIA | Miami International Airport |
| MSP | Minneapolis-Saint Paul International Airport |
| ORD | Chicago O'Hare International Airport |
| PHL | Philadelphia International Airport |
| PHX | Phoenix Sky Harbor International Airport |
| SEA | Seattle-Tacoma International Airport |
| SFO | San Francisco International Airport |

- **Geographic fields in OOH data:** NONE
- **Schema implication:** Must create a `dim_airport` lookup table mapping `airport_code` -> state, city, DMA. Only ATL is in Georgia; the other 19 airports are in other states, making OOH the only stream with significant out-of-state geographic scope. This is a national OOH campaign vs. a Georgia-focused digital/ecommerce operation.

---

## 4. Campaign Linkage Investigation

**Summary:** There are **no exact matches** between paid social `campaign_name` and web analytics `campaign`. The linkage is thematic, not ID-based. Paid social uses a `"{Platform} {Theme}"` naming convention; web analytics uses just the theme or a year-suffixed variant. The web `campaign` field acts as a marketing initiative tag rather than a foreign key to paid social campaigns. A **campaign mapping/bridge table** is needed for cross-stream analysis.

### Paid Social Campaigns

| campaign_id | campaign_name | Platform | Theme |
|---|---|---|---|
| IN_2077 | Instagram Always On | Instagram | Always On |
| IN_6601 | Instagram BTS Moms | Instagram | BTS Moms |
| IN_1278 | Instagram Teen Trends | Instagram | Teen Trends |
| PI_4556 | Pinterest Always On | Pinterest | Always On |
| PI_6623 | Pinterest BTS Moms | Pinterest | BTS Moms |
| PI_4922 | Pinterest Teen Trends | Pinterest | Teen Trends |
| TI_1103 | TikTok Always On | TikTok | Always On |
| TI_3966 | TikTok BTS Moms | TikTok | BTS Moms |
| TI_4212 | TikTok Teen Trends | TikTok | Teen Trends |

- **ID pattern:** 2-letter platform prefix + underscore + 4-digit number (e.g., `IN_2077`)
- **3 themes** across 3 platforms = 9 campaigns total

### Web Analytics Campaigns

| campaign | Notes |
|---|---|
| Always On | Matches paid social "Always On" theme |
| BTS 2023 | Likely maps to paid "BTS Moms" (2023 season) |
| BTS 2024 | Likely maps to paid "BTS Moms" (2024 season) |
| Black Friday 2023 | Web/promo only - no paid social counterpart |
| Email Promo | Web/promo only - no paid social counterpart |
| None | Unattributed traffic |
| *(empty string)* | Missing/null campaign value |

### Traffic Source / Medium Combinations

| traffic_source | traffic_medium | Row Count (approx) |
|---|---|---|
| direct | none | ~7,600 |
| email | email | ~7,500 |
| facebook | paid_social | ~7,500 |
| google | cpc | ~7,500 |
| instagram | paid_social | ~7,600 |
| tiktok | paid_social | ~7,400 |

### Substring Matches (Paid Social <-> Web)

| Web campaign | Paid Social campaign_name | Match Type |
|---|---|---|
| Always On | Instagram Always On | substring |
| Always On | Pinterest Always On | substring |
| Always On | TikTok Always On | substring |

### Web Campaign x Source/Medium Cross-Tab

Every web `campaign` value appears with every `traffic_source`/`traffic_medium` combination (roughly equal row counts ~1,200-1,600 per cell). This confirms the web `campaign` field is **not** directly tied to a specific paid social channel — it is an independent marketing initiative tag applied at the session level.

### Key Schema Design Implications

1. **No direct foreign key** between paid social `campaign_id`/`campaign_name` and web `campaign`
2. **Need a bridge/mapping table** (`dim_campaign_initiative`) that groups:
   - Paid social theme "Always On" -> Web "Always On"
   - Paid social theme "BTS Moms" -> Web "BTS 2023" + "BTS 2024"
   - Paid social theme "Teen Trends" -> No web counterpart
   - Web "Black Friday 2023" / "Email Promo" -> No paid social counterpart
3. **Web traffic_source + traffic_medium** can link to paid social platform:
   - `instagram` / `paid_social` -> Instagram paid campaigns
   - `tiktok` / `paid_social` -> TikTok paid campaigns
   - `facebook` / `paid_social` -> Note: Facebook is a traffic source but NOT a paid social platform in this dataset (no Facebook paid files exist)
4. **Attribution model needed:** Since web sessions combine campaign + source/medium independently, attribution requires joining on both time window and geography, not just campaign name.

---

## 5. Podcast Geography Signals

**Summary:** 3 of 5 podcasts have obvious geographic references in their names — all pointing to Georgia/Atlanta. The remaining 2 are non-geographic. All 5 podcasts have founder (Karen LeSac) mentions across multiple episodes. There are no non-geo podcasts without founder mentions.

### Podcast Geographic Classification

| podcast_name | Geo Reference | Type | mentions_founder | Episodes w/ Founder |
|---|---|---|:---:|:---:|
| Carpool Chronicles GA | GA (state abbrev) | Georgia | YES | 7 |
| Mom Life in the ATL | ATL (city/airport) | Atlanta | YES | 6 |
| Peach State Parenting | Peach State (regional) | Georgia | YES | 7 |
| Suburban Style Chats | *(none)* | Non-geo | YES | 7 |
| Teen Trend Watch | *(none)* | Non-geo | YES | 7 |

### Cross-Reference: Geography vs. Founder Mentions

- **All 5 podcasts** have founder mentions — no differentiation between geo and non-geo podcasts
- Non-geo podcasts with founder mentions: 2 (Suburban Style Chats, Teen Trend Watch)
- Non-geo podcasts without founder mentions: 0
- **Schema implication:** Podcast geography cannot be inferred from founder mentions. A `podcast_geo_flag` or manual geo-tagging column would be needed in a `dim_podcast` table. The 3 geo-tagged podcasts all reference the Georgia/Atlanta market, aligning with the core DMA footprint. The 2 non-geo podcasts may have national or undefined geographic reach.

---

## Summary of Schema Design Decisions

| Decision | Recommendation |
|---|---|
| DMA normalization | Not needed - values are consistent across streams |
| State normalization | Not needed - single value "GA" |
| Airport-to-geo mapping | Create `dim_airport` with external lookup for state/city/DMA |
| Campaign linkage | Create `dim_campaign_initiative` bridge table; do NOT attempt direct FK join |
| Web attribution | Use `traffic_source` + `traffic_medium` to identify channel; `campaign` is an independent initiative tag |
| Podcast geography | Add manual `geo_market` column to `dim_podcast`; 3 GA-market, 2 unknown |
| OOH geographic scope | National (20 airports across US) vs. digital/ecomm (GA only) - flag in analysis |
