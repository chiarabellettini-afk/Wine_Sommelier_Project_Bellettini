"""Analytics page: rating statistics, vintage correlation and charts."""

import pandas as pd
import plotly.express as px
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
TOP_N = 15


def build_rating_distribution(ratings):
    """Create a histogram of all the ratings.

    Args:
        ratings (pd.DataFrame): Ratings table with a "Rating" column.

    Returns:
        plotly.graph_objects.Figure: The histogram.
    """
    fig = px.histogram(ratings, x="Rating")
    fig.update_layout(yaxis_title="Number of ratings", bargap=0.1)
    return fig


def build_top_wines_chart(wines, top_n=TOP_N):
    """Plot the best wines by Bayesian score with 95% confidence intervals.

    Args:
        wines (pd.DataFrame): Wine table with the columns produced by
            ``compute_wine_rating_stats``.
        top_n (int): Number of wines to show.

    Returns:
        plotly.graph_objects.Figure: Dot plot of the mean rating with
        horizontal error bars.
    """
    data = (
        wines.dropna(subset=["bayesian_score", "ci_low", "ci_high"])
        .nlargest(top_n, "bayesian_score")
        .sort_values("bayesian_score")
    )
    fig = px.scatter(
        data,
        x="mean_rating",
        y="WineName",
        error_x=data["ci_high"] - data["mean_rating"],
        error_x_minus=data["mean_rating"] - data["ci_low"],
        hover_data=["rating_count", "bayesian_score"],
    )
    fig.update_layout(xaxis_title="Mean rating (95% CI)", yaxis_title="")
    return fig


def build_vintage_chart(ratings, rho, p_value):
    """Plot the mean rating for each vintage year.

    Args:
        ratings (pd.DataFrame): Ratings table with "Vintage" and "Rating".
        rho (float): Spearman coefficient, shown in the title.
        p_value (float): Spearman p-value, shown in the title.

    Returns:
        plotly.graph_objects.Figure: Scatter plot, one point per vintage,
        sized by the number of ratings.
    """
    data = ratings.copy()
    data["Vintage"] = pd.to_numeric(data["Vintage"], errors="coerce")
    by_year = (
        data.dropna(subset=["Vintage"])
        .groupby("Vintage")["Rating"]
        .agg(mean_rating="mean", n_ratings="count")
        .reset_index()
    )
    fig = px.scatter(by_year, x="Vintage", y="mean_rating", size="n_ratings")
    fig.update_layout(
        title=f"Spearman ρ = {rho:.3f} (p = {p_value:.4f})",
        yaxis_title="Mean rating",
    )
    return fig


def build_rating_by_type_chart(ratings, wines):
    """Compare the rating distribution of each wine type.

    Args:
        ratings (pd.DataFrame): Ratings table with "WineID" and "Rating".
        wines (pd.DataFrame): Wine table with "WineID" and "Type".

    Returns:
        plotly.graph_objects.Figure: Box plot of ratings per wine type.
    """
    merged = ratings.merge(wines[["WineID", "Type"]], on="WineID", how="left")
    merged = merged.dropna(subset=["Type"])
    fig = px.box(merged, x="Type", y="Rating", color="Type")
    fig.update_layout(showlegend=False)
    return fig


user_info = load_user_info()
wines = load_wines(user_info)
ratings = load_ratings()
vintage_corr = analyze_vintage_correlation(ratings)

with st.expander("Rating & Vintage Statistical Insights"):
    st.write(
        f"Vintage vs. Rating Spearman $\\rho$: **{vintage_corr['rho']:.3f}** "
        f"(p-value: **{vintage_corr['p_value']:.4f}**, n = {vintage_corr['n']})"
    )
    st.dataframe(
        wines[STATS_COLUMNS].dropna(subset=["bayesian_score"]),
        hide_index=True,
    )

st.subheader("Distribution of ratings")
st.plotly_chart(build_rating_distribution(ratings), use_container_width=True)

st.subheader(f"Top {TOP_N} wines by Bayesian score")
st.caption(
    "Dots show the mean rating, bars the 95% confidence interval. Wines with "
    "few ratings have wide intervals."
)
st.plotly_chart(build_top_wines_chart(wines), use_container_width=True)

st.subheader("Mean rating by vintage")
st.plotly_chart(
    build_vintage_chart(ratings, vintage_corr["rho"], vintage_corr["p_value"]),
    use_container_width=True,
)

st.subheader("Ratings by wine type")
st.plotly_chart(
    build_rating_by_type_chart(ratings, wines), use_container_width=True
)