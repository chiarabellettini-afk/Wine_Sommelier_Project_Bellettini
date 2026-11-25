"""Analytics page: rating statistics and vintage correlation."""

import numpy as np
import pandas as pd
from scipy import stats


def compute_wine_rating_stats(ratings_df: pd.DataFrame, confidence: float = 0.95) -> pd.DataFrame:
    """Compute rating statistics for every wine.

    For each WineID it computes the number of ratings, the mean, the sample
    standard deviation, a Bayesian weighted score (the wine's mean is pulled
    towards the global mean, more strongly when it has few ratings; the prior
    weight is the median number of ratings per wine) and a confidence
    interval of the mean based on Student's t-distribution.

    Args:
        ratings_df (pd.DataFrame): Ratings table with "WineID" and "Rating"
            columns, one row per rating.
        confidence (float): Confidence level of the interval. Defaults to 0.95.

    Returns:
        pd.DataFrame: One row per WineID with the columns "rating_count",
        "mean_rating", "std_rating", "bayesian_score", "ci_low" and
        "ci_high". The interval bounds are clipped to the 1-5 rating scale
        and are NaN for wines with a single rating.
    """
    grouped = ratings_df.groupby("WineID")["Rating"].agg(
        rating_count="count",
        mean_rating="mean",
        std_rating=lambda s: float(np.std(s.to_numpy(dtype=float), ddof=1)) if len(s) > 1 else 0.0,
    ).reset_index()

    global_mean = float(np.mean(ratings_df["Rating"].to_numpy(dtype=float)))
    prior_weight = float(np.percentile(grouped["rating_count"].to_numpy(dtype=float), 50))

    n = grouped["rating_count"].to_numpy(dtype=float)
    mean = grouped["mean_rating"].to_numpy(dtype=float)
    std = grouped["std_rating"].to_numpy(dtype=float)

    # Bayesian weighted rating
    grouped["bayesian_score"] = (n / (n + prior_weight)) * mean + (prior_weight / (n + prior_weight)) * global_mean

    # 95% confidence interval using Student's t-distribution
    se = np.where(n > 1, std / np.sqrt(n), np.nan)
    df_t = np.maximum(n - 1, 1)
    t_crit = stats.t.ppf((1.0 + confidence) / 2.0, df=df_t)
    margin = t_crit * se

    grouped["ci_low"] = np.clip(mean - margin, 1.0, 5.0)
    grouped["ci_high"] = np.clip(mean + margin, 1.0, 5.0)

    return grouped


def analyze_vintage_correlation(ratings_df: pd.DataFrame) -> dict:
    """Measure the monotonic relationship between vintage year and rating.

    Uses the Spearman rank correlation. Rows whose vintage is not numeric
    (e.g. non-vintage wines) are ignored.

    Args:
        ratings_df (pd.DataFrame): Ratings table with "Vintage" and "Rating"
            columns.

    Returns:
        dict: Dictionary with "n" (number of ratings used), "rho" (Spearman
        coefficient) and "p_value". "rho" and "p_value" are NaN if fewer than
        3 valid rows are available.
    """
    df = ratings_df.copy()
    df["Vintage_num"] = pd.to_numeric(df["Vintage"], errors="coerce")
    df = df.dropna(subset=["Vintage_num", "Rating"])

    if len(df) < 3:
        return {"n": len(df), "rho": np.nan, "p_value": np.nan}

    res = stats.spearmanr(df["Vintage_num"].to_numpy(dtype=float), df["Rating"].to_numpy(dtype=float))
    return {
        "n": int(len(df)),
        "rho": float(res.statistic),
        "p_value": float(res.pvalue),
    }