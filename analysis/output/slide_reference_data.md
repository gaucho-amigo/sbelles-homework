# Slide Reference Data

All numbers for the executive slide deck, pulled from analysis outputs.

## Dataset Overview

- Total source files: 21
- Total source rows: 98,320
- Date range: 2023-01-01 to 2024-06-30 (547 days)
- Datastreams: 6 (paid social, web analytics, ecommerce, organic social, podcast, OOH)
- Schema drift patterns resolved: 3

## Warehouse Output

- Dimension tables: 5 (dim_date, dim_geography, dim_channel, dim_campaign_initiative, dim_podcast)
- Daily fact tables: 6
- Source-grain detail tables: 2 (fact_ecommerce_transactions, fact_web_analytics_events)
- Validation checks passed: 48/48

## Financial Totals

- Total paid social spend: $5,986,609
- Total OOH spend: $29,519,757
- Total combined marketing spend: $35,506,366
- Total ecommerce revenue: $498,071
- Total ecommerce orders: 16,828
- Total web pageviews: 51,234
- Total podcast mentions: 87
- Spend-to-revenue ratio: 71.3x

## Seasonal Metrics

| Season | Days | Avg Daily Revenue | Avg Daily Paid Spend | Avg Daily Web Sessions | Avg Daily Orders |
|---|---:|---:|---:|---:|---:|
| regular | 458 | $825 | $9,885 | 85 | 28 |
| back_to_school | 63 | $1,290 | $16,036 | 135 | 44 |
| black_friday_holiday | 26 | $1,493 | $17,266 | 153 | 50 |

## Correlation Summary (Lag 0)

| Signal Pair | Raw r | Deseasonalized r | % Reduction |
|---|---:|---:|---:|
| Paid Social Spend → Web Sessions | 0.938 | 0.785 | 16.4% |
| Paid Social Spend → Ecomm Revenue | 0.768 | 0.400 | 48.0% |
| Web Sessions → Ecomm Revenue | 0.830 | 0.545 | 34.3% |
| Podcast Impressions → Web Sessions | 0.143 | 0.162 | -13.7% |
| Organic Impressions → Web Sessions | 0.284 | 0.125 | 56.0% |

### Partial Correlation

- Simple deseasonalized correlation (paid spend → revenue): r = 0.400
- Partial correlation (controlling for web sessions): r = -0.033
- Interpretation: After removing 14-day trends and controlling for residual web sessions, the paid spend to revenue relationship remains negative but is meaningfully weaker after conditioning on sessions.

## Seasonal Inflation Summary

| Signal Pair | Raw r | Residual r | % Reduction |
|---|---:|---:|---:|
| Organic Impressions → Web Sessions | 0.284 | 0.125 | 56.0% |
| Paid Social Spend → Ecomm Revenue | 0.768 | 0.400 | 48.0% |
| Web Sessions → Ecomm Revenue | 0.830 | 0.545 | 34.3% |
| Paid Social Spend → Web Sessions | 0.938 | 0.785 | 16.4% |
| Podcast Impressions → Web Sessions | 0.143 | 0.162 | -13.7% |

## Promo Impact Summary

| Metric | Non-Promo (flag=0) | Promo (flag=1) |
|---|---:|---:|
| Line items | 8,543 | 8,563 |
| Distinct orders | 6,979 | 6,988 |
| Total quantity | 11,914 | 12,027 |
| Total revenue | $337,965 | $160,106 |
| Avg order value | $48.43 | $22.91 |
| Avg unit price | $28.33 | $28.30 |
| Avg discount/unit | $0.00 | $15.03 |
| Negative revenue rows | 0 | 105 |
| Negative revenue amount | $0 | $-144 |

## Key Slide Callouts

- "$36M in marketing spend vs $498K in tracked revenue"
- Revenue split: $337,965 non-promo + $160,106 promo = $498,071 total
- Promo revenue is 32.1% of total but avg order value drops from $48.43 to $22.91
- Raw paid→sessions r=0.938 drops to r=0.785 after deseasonalization (16.4% reduction)
- Partial correlation (paid→revenue | sessions) = -0.033 — effectively zero

