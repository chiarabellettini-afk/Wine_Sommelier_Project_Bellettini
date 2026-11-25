"""Analytics page: rating statistics and vintage correlation."""

import streamlit as st

from wine_sommelier.data_loader import load_ratings, load_wines
from wine_sommelier.rating_analytics import analyze_vintage_correlation
from wine_sommelier.user_store import load_user_info

STATS_COLUMNS = [
    "WineName",
    "rating_count",
    "mean_rating",
    "bayesian_score",
    "ci_low",
    "ci_high",
]

user_info = load_user_info()
wines = load_wines(user_info)
vintage_corr = analyze_vintage_correlation(load_ratings())

with st.expander("Rating & Vintage Statistical Insights"):
    st.write(
        f"Vintage vs. Rating Spearman $\\rho$: **{vintage_corr['rho']:.3f}** "
        f"(p-value: **{vintage_corr['p_value']:.4f}**, n = {vintage_corr['n']})"
    )
    st.dataframe(
        wines[STATS_COLUMNS].dropna(subset=["bayesian_score"]),
        hide_index=True,
    )