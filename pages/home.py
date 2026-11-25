"""Home page: suggest wines to pair with a chosen food."""

import ast

import streamlit as st

from wine_sommelier.data_loader import load_wines, load_wines_raw
from wine_sommelier.user_store import load_user_info, toggle_favorite

DISPLAY_COLUMNS = ["Btn", "WineName", "Type", "Body", "Rating"]


def toggle_fav(df, key):
    """Toggle the favorite status of the wine in the clicked table row.

    Used as the ``on_click`` callback of the favorites button column.

    Args:
        df (pd.DataFrame): The table that was displayed (needed to map the
            clicked row position to a WineID).
        key (str): Streamlit key of the table, used to read the clicked row
            from ``st.session_state``.
    """
    row = st.session_state[key]["row"]
    toggle_favorite(int(df.iloc[row]["WineID"]))


def build_config(df, key):
    """Build the column configuration for a wine table.

    Args:
        df (pd.DataFrame): The table that will be displayed.
        key (str): Unique Streamlit key for the table's button column.

    Returns:
        dict: Column configuration to pass to ``st.dataframe``.
    """
    return {
        "WineName": st.column_config.TextColumn("WineName"),
        "Btn": st.column_config.ButtonColumn(
            " ", on_click=toggle_fav, args=(df, key), key=key
        ),
    }


def has_food(harmonize, food):
    """Check whether a wine's pairing list contains a given food.

    Args:
        harmonize (str): String representation of a list of foods,
            e.g. "['Beef', 'Lamb']". Missing values or "N/A" never match.
        food (str): Food to look for.

    Returns:
        bool: True if the food is in the wine's pairing list.
    """
    if not isinstance(harmonize, str) or harmonize == "N/A":
        return False
    return food in ast.literal_eval(harmonize)


user_info = load_user_info()
wines = load_wines(user_info)
all_food = (
    load_wines_raw()["Harmonize"]
    .dropna()
    .apply(ast.literal_eval)
    .explode()
    .unique()
    .tolist()
)

st.subheader("Search pairings by food:")
selected_food = st.selectbox("Select food", all_food)
suggested_wines = wines[wines["Harmonize"].apply(has_food, food=selected_food)]

st.write(f"Suggested wines to pair with {selected_food.lower()}:")
st.dataframe(
    suggested_wines,
    column_config=build_config(suggested_wines, "fav1"),
    column_order=DISPLAY_COLUMNS,
    hide_index=True,
)

st.subheader("Complete list of wines:")
st.dataframe(
    wines,
    column_config=build_config(wines, "fav2"),
    column_order=DISPLAY_COLUMNS,
    hide_index=True,
)