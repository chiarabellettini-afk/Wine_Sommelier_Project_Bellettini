"""Loading and preparing the wine and rating tables."""

import os

import pandas as pd
import streamlit as st

from wine_sommelier.rating_analytics import compute_wine_rating_stats

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


@st.cache_data
def load_ratings():
    """Load the ratings CSV.

    Returns:
        pd.DataFrame: One row per rating.
    """
    return pd.read_csv(os.path.join(DATA_DIR, "XWines_Test_1K_ratings.csv"))


@st.cache_data
def load_wines_raw():
    """Load the base wines CSV.

    Returns:
        pd.DataFrame: One row per wine.
    """
    return pd.read_csv(os.path.join(DATA_DIR, "XWines_Test_100_wines.csv"))


def load_wines(user_info):
    """Combine base wines, custom wines, favorite icons and rating stats.

    Args:
        user_info (dict): User info with "Custom_wine" and "Favorites".

    Returns:
        pd.DataFrame: Full wine table with "Btn", "Rating" and the
        columns produced by ``compute_wine_rating_stats``.
    """
    custom = pd.DataFrame(user_info.get("Custom_wine", []))
    wines = pd.concat([load_wines_raw(), custom], ignore_index=True)
    favorites = user_info.get("Favorites", [])
    wines["Btn"] = wines["WineID"].isin(favorites).map({True: "⭐", False: "☆"})

    stats = compute_wine_rating_stats(load_ratings())
    wines = wines.merge(stats, on="WineID", how="left")
    wines["Rating"] = wines["mean_rating"].round(1)
    return wines