"""Shared utilities for Phase 3 analysis."""

import pandas as pd


def add_residual_columns(df, cols, window=14):
    """Add deseasonalized residual columns by subtracting a centered rolling mean.

    For each column in cols, computes:
        resid = value - rolling_mean(window, center=True)

    Residual columns are named f"{col}__resid". NaN rows from the rolling
    window edges are preserved (not dropped).

    Simple subtraction is used because percent change introduces
    division-by-zero errors on sparse signals like podcast_impressions.
    Pearson correlation is scale-invariant, so absolute residuals are
    appropriate.
    """
    df = df.sort_values("date").copy()
    for col in cols:
        trend = df[col].rolling(window, center=True, min_periods=window).mean()
        df[f"{col}__resid"] = df[col] - trend
    return df
