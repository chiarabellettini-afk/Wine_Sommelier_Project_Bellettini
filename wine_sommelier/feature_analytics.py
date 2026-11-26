"""Relationships between wine features (ABV, body, grapes, ...) and ratings."""

import ast
from collections import Counter
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

BODY_ORDER = [
    "Very light-bodied",
    "Light-bodied",
    "Medium-bodied",
    "Full-bodied",
    "Very full-bodied",
]
ACIDITY_ORDER = ["Low", "Medium", "High"]
BODY_LEVELS = {name: i for i, name in enumerate(BODY_ORDER)}
ACIDITY_LEVELS = {name: i for i, name in enumerate(ACIDITY_ORDER)}


def _count_items(text):
    """Count the items in a string such as "['Merlot', 'Syrah']".

    Args:
        text (str): String representation of a list (or a missing value).

    Returns:
        int: Number of items, or NaN if the value is missing or "N/A".
    """
    if not isinstance(text, str) or text == "N/A":
        return np.nan
    return len(ast.literal_eval(text))


def build_feature_table(wines, stats_df):
    """Create a numeric table with one row per wine, ready for correlations.

    Args:
        wines (pd.DataFrame): Wine table with ABV, Body, Acidity, Grapes,
            Harmonize and Vintages columns.
        stats_df (pd.DataFrame): Output of ``compute_wine_rating_stats``.

    Returns:
        pd.DataFrame: Columns "WineName", "Type", "ABV", "Body_level",
        "Acidity_level", "n_grapes", "n_pairings", "n_vintages",
        "mean_rating" and "rating_count".
    """
    table = wines[["WineID", "WineName", "Type", "ABV"]].copy()
    table["Body_level"] = wines["Body"].map(BODY_LEVELS)
    table["Acidity_level"] = wines["Acidity"].map(ACIDITY_LEVELS)
    table["n_grapes"] = wines["Grapes"].apply(_count_items)
    table["n_pairings"] = wines["Harmonize"].apply(_count_items)
    table["n_vintages"] = wines["Vintages"].apply(_count_items)
    table = table.merge(
        stats_df[["WineID", "mean_rating", "rating_count"]],
        on="WineID",
        how="left",
    )
    return table.drop(columns="WineID")


def spearman_matrix(table, columns):
    """Compute the Spearman correlation matrix of the given columns.

    Args:
        table (pd.DataFrame): Table with numeric columns.
        columns (list[str]): Columns to correlate.

    Returns:
        pd.DataFrame: Square matrix of Spearman coefficients.
    """
    return table[columns].corr(method="spearman")


def spearman_test(x, y):
    """Spearman correlation between two columns, ignoring missing rows.

    Args:
        x (pd.Series): First variable.
        y (pd.Series): Second variable.

    Returns:
        tuple[float, float, int]: rho, p-value and number of rows used.
    """
    data = pd.concat([x, y], axis=1).dropna()
    if len(data) < 3:
        return np.nan, np.nan, len(data)
    res = stats.spearmanr(data.iloc[:, 0], data.iloc[:, 1])
    return float(res.statistic), float(res.pvalue), len(data)


def add_wine_age(ratings):
    """Add the age of the wine (in years) at the time it was rated.

    Args:
        ratings (pd.DataFrame): Ratings table with "Vintage" and "Date".

    Returns:
        pd.DataFrame: Copy of the table with a numeric "Age" column.
        Non-vintage wines and negative ages become NaN.
    """
    data = ratings.copy()
    year = pd.to_datetime(data["Date"], errors="coerce").dt.year
    data["Age"] = year - pd.to_numeric(data["Vintage"], errors="coerce")
    data.loc[data["Age"] < 0, "Age"] = np.nan
    return data


def food_cooccurrence(wines, top_n=12):
    """Count how often the most common foods are recommended together.

    Args:
        wines (pd.DataFrame): Wine table with a "Harmonize" column.
        top_n (int): Number of most common foods to keep.

    Returns:
        pd.DataFrame: Symmetric matrix (foods x foods) with the number of
        wines that list both foods. The diagonal is NaN.
    """
    lists = (
        wines["Harmonize"].dropna().loc[lambda s: s != "N/A"]
        .apply(ast.literal_eval)
    )
    top = [f for f, _ in Counter(f for foods in lists for f in foods)
           .most_common(top_n)]
    position = {food: i for i, food in enumerate(top)}
    counts = np.zeros((len(top), len(top)))
    for foods in lists:
        for a, b in combinations(sorted(set(foods) & set(top)), 2):
            counts[position[a], position[b]] += 1
            counts[position[b], position[a]] += 1
    np.fill_diagonal(counts, np.nan)
    matrix = pd.DataFrame(counts, index=top, columns=top)
    return matrix