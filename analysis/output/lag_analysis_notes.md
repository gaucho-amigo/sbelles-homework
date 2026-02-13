# Lag Analysis Notes

Cross-correlations are computed on raw daily values. Shared seasonal patterns
(back-to-school, Black Friday/holiday) may inflate correlation estimates at all
lags. Deseasonalizing the signals before computing correlations would isolate
short-term dynamics from seasonal confounds.

These correlations identify candidate causal relationships for further
investigation using entropy-based methods; they do not establish causality.
