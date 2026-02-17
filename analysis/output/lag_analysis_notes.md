# Lag Analysis Notes

## Raw Cross-Correlations

Most signal pairs peak at lag 0, but not all patterns are monotonic with lag.
Paid social spend and web sessions correlate at r = 0.94 at lag 0.
This pattern is consistent with strong shared seasonal response
(back-to-school, Black Friday/holiday) plus additional noise in weaker channels.

- Paid Social Spend → Web Sessions: r = 0.94 at lag 0, peak |r| = 0.94 at lag 0d
- Paid Social Spend → Ecomm Revenue: r = 0.77 at lag 0, peak |r| = 0.77 at lag 0d
- Web Sessions → Ecomm Revenue: r = 0.83 at lag 0, peak |r| = 0.83 at lag 0d
- Podcast Impressions → Web Sessions: r = 0.14 at lag 0, peak |r| = 0.15 at lag 14d
- Organic Impressions → Web Sessions: r = 0.28 at lag 0, peak |r| = 0.28 at lag 0d

## Deseasonalized Cross-Correlations

After removing a 14-day centered rolling mean from each signal, correlations
drop for most pairs. Residualized relationships are generally weaker, though
some weak pairs can move slightly higher at lag 0 after residualization.
Overall, this supports that raw correlations were heavily influenced by
seasonal co-movement rather than short-term causal dynamics.

- Paid Social Spend → Web Sessions: r = 0.78 at lag 0, peak |r| = 0.78 at lag 0d
- Paid Social Spend → Ecomm Revenue: r = 0.40 at lag 0, peak |r| = 0.40 at lag 0d
- Web Sessions → Ecomm Revenue: r = 0.55 at lag 0, peak |r| = 0.55 at lag 0d
- Podcast Impressions → Web Sessions: r = 0.16 at lag 0, peak |r| = 0.16 at lag 0d
- Organic Impressions → Web Sessions: r = 0.12 at lag 0, peak |r| = 0.12 at lag 0d

## Interpretation

High raw correlations between marketing spend and revenue do not establish that
spend caused revenue. Seasonal demand drives both spend (marketers increase
budgets during peak periods) and revenue (consumers buy more during
back-to-school and holidays). After controlling for this seasonal pattern, the
residual short-term relationships are substantially weaker (paid social spend →
web sessions drops from r = 0.94 to r = 0.78 at lag 0).

This demonstrates a fundamental limitation of correlation-based marketing mix
models: they cannot distinguish whether spend amplified demand or merely
coincided with it. Establishing true causal impact requires methods that can
detect directional information flow between signals while conditioning on
confounding temporal patterns. Entropy-based causal inference, such as transfer
entropy, addresses this by measuring whether the past of one signal reduces
uncertainty about the future of another, beyond what that signal's own history
explains.

## Note on Methodology

Deseasonalization uses a 14-day centered rolling mean subtracted from raw
values. This window captures weekly cyclicality and short-term seasonal trends
without over-smoothing. Percent-change residuals were considered but rejected
due to division-by-zero risk on sparse signals (podcast mentions). Pearson
correlation is scale-invariant, making absolute residuals appropriate for
cross-signal comparison.
