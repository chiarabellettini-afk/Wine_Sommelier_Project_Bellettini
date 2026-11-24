import numpy as np
import pandas as pd
from scipy import stats


def compute_wine_rating_stats(ratings_df: pd.DataFrame, confidence: float = 0.95) -> pd.DataFrame:
    """Compute sample stats, 95% t-intervals, and Bayesian weighted ratings per WineID."""
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
    """Test monotonic relationship between numeric Vintage year and Rating using Spearman correlation."""
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