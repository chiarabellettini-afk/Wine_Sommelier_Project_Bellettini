"""Analytics page: rating statistics, vintage correlation and charts."""

import pandas as pd
import plotly.express as px
import streamlit as st

from wine_sommelier.data_loader import load_ratings, load_wines, load_wines_raw
from wine_sommelier.feature_analytics import (
    add_wine_age,
    build_feature_table,
    food_cooccurrence,
    spearman_matrix,
    spearman_test,
)
from wine_sommelier.rating_analytics import (
    analyze_vintage_correlation,
    compute_wine_rating_stats,
)
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

CORR_LABELS = {
    "ABV": "Alcohol (ABV)",
    "Body_level": "Body",
    "Acidity_level": "Acidity",
    "n_grapes": "No. of grapes",
    "n_pairings": "No. of food pairings",
    "n_vintages": "No. of vintages",
    "mean_rating": "Mean rating",
}
AGE_BINS = [-1, 5, 10, 20, 100]
AGE_LABELS = ["0-5 years", "6-10 years", "11-20 years", "20+ years"]
MAX_ABV = 25
WINE_COLORS = {
    "Red": "#8E1B3A",
    "White": "#E3D36B",
    "Rosé": "#F4A6B8",
    "Sparkling": "#C9D6A3",
    "Dessert": "#E08E2B",
    "Dessert/Port": "#A0522D",
}


def build_correlation_heatmap(table):
    """Heatmap of the Spearman correlations between wine features.

    Args:
        table (pd.DataFrame): Output of ``build_feature_table``.

    Returns:
        plotly.graph_objects.Figure: Annotated heatmap from -1 to 1.
    """
    corr = spearman_matrix(table, list(CORR_LABELS)).rename(
        index=CORR_LABELS, columns=CORR_LABELS
    )
    fig = px.imshow(
        corr,
        text_auto=".2f",
        zmin=-1,
        zmax=1,
        color_continuous_scale="RdBu_r",
    )
    fig.update_layout(coloraxis_colorbar_title="Spearman ρ")
    return fig


def build_age_chart(rated):
    """Bar chart of the mean rating by age of the wine when it was rated.

    Args:
        rated (pd.DataFrame): Output of ``add_wine_age``.

    Returns:
        plotly.graph_objects.Figure: Mean rating per age group, with the
        number of ratings written on each bar.
    """
    data = rated.dropna(subset=["Age"]).copy()
    data["Age group"] = pd.cut(data["Age"], AGE_BINS, labels=AGE_LABELS)
    summary = (
        data.groupby("Age group", observed=True)["Rating"]
        .agg(mean_rating="mean", n_ratings="count")
        .reset_index()
    )
    fig = px.bar(
        summary,
        x="Age group",
        y="mean_rating",
        text=summary["n_ratings"].apply(lambda n: f"n = {n}"),
    )
    fig.update_layout(yaxis_title="Mean rating", yaxis_range=[3, 4.3])
    return fig


def build_abv_chart(table):
    """Scatter plot of alcohol content against mean rating.

    Args:
        table (pd.DataFrame): Output of ``build_feature_table``.

    Returns:
        plotly.graph_objects.Figure: One point per wine, coloured by wine
        type and sized by the number of ratings. Wines above ``MAX_ABV`` are
        left out so that one extreme value does not squash the plot.
    """
    data = table[table["ABV"] <= MAX_ABV]
    fig = px.scatter(
        data,
        x="ABV",
        y="mean_rating",
        color="Type",
        color_discrete_map=WINE_COLORS,
        category_orders={"Type": list(WINE_COLORS)},
        size="rating_count",
        hover_name="WineName",
    )
    fig.update_traces(marker_line_width=1, marker_line_color="rgba(0, 0, 0, 0.4)")
    fig.update_layout(xaxis_title="Alcohol (ABV %)", yaxis_title="Mean rating")
    return fig


def build_cooccurrence_heatmap(wines):
    """Heatmap of the foods most often recommended together.

    Args:
        wines (pd.DataFrame): Wine table with a "Harmonize" column.

    Returns:
        plotly.graph_objects.Figure: Foods x foods heatmap with the number
        of wines recommending both.
    """
    fig = px.imshow(
        food_cooccurrence(wines),
        text_auto=".0f",
        color_continuous_scale="Purples",
    )
    fig.update_layout(coloraxis_colorbar_title="Wines")
    return fig

raw_wines = load_wines_raw()
feature_table = build_feature_table(raw_wines, compute_wine_rating_stats(ratings))
rated = add_wine_age(ratings)

st.header("Beyond the ratings: what do wines have in common?")

st.subheader("Which wine features go together?")
st.caption(
    "Spearman correlations between wine characteristics. Red means the two "
    "grow together, blue means one goes up as the other goes down."
)
st.plotly_chart(build_correlation_heatmap(feature_table), use_container_width=True)

st.subheader("Do stronger wines get better ratings?")
rho, p_value, n = spearman_test(feature_table["ABV"], feature_table["mean_rating"])
st.caption(
    f"Spearman ρ = {rho:.2f} (p = {p_value:.4f}, n = {n} wines). "
    f"Wines above {MAX_ABV}% ABV are not shown."
)
st.plotly_chart(build_abv_chart(feature_table), use_container_width=True)

st.subheader("Do wines get better with age?")
rho, p_value, n = spearman_test(rated["Age"], rated["Rating"])
st.caption(
    "Age = year of the rating minus vintage year. "
    f"Spearman ρ = {rho:.2f} (p = {p_value:.4g}, n = {n} ratings)."
)
st.plotly_chart(build_age_chart(rated), use_container_width=True)

st.subheader("Which foods are recommended together?")
st.plotly_chart(build_cooccurrence_heatmap(raw_wines), use_container_width=True)