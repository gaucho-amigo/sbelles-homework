# S'Belles Synthetic Marketing Dataset – README

This package contains synthetic but realistic multi-channel marketing and commerce data
for **S'Belles**, a fictional fast-fashion brand targeting suburban Georgia moms and their daughters.
Data spans **2023-01-01 through 2024-06-30** (~18 months) and includes seasonality for:

- Back-to-school (mid-July through mid-September)
- Black Friday / holiday (mid-November through early December)

It includes the following datastreams:
- Paid social (TikTok, Instagram, Pinterest) with intentional schema drift across files
- Web analytics pageview events (with overlapping December 2023 data in two files)
- E-commerce transaction line items
- Owned TikTok engagement for the brand's organic account
- Podcast mentions and earned impressions
- Out-of-home airport advertising on a weekly basis (top 20 U.S. airports)

Files are intended for data wrangling, schema standardization, time-series alignment,
and multi-source attribution-style exercises.
