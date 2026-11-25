"""Page to look up the food pairings of a chosen wine."""

import ast

import pandas as pd
import plotly.express as px
import streamlit as st

from wine_sommelier.data_loader import load_wines
from wine_sommelier.pairing import suggest_food
from wine_sommelier.user_store import load_user_info


def format_food_list(foods):
    """Join foods into a readable sentence fragment.

    Args:
        foods (list[str]): Food names.

    Returns:
        str: e.g. "beef, lamb and pasta"; a single food is returned as is,
        and an empty list gives an empty string.
    """
    foods = [food.lower() for food in foods]
    if len(foods) > 1:
        return ", ".join(foods[:-1]) + " and " + foods[-1]
    return foods[0] if foods else ""


def build_pairings_chart(food_count):
    """Create a bar chart of how often each food is paired.

    Args:
        food_count (collections.Counter): Count of every food found.

    Returns:
        plotly.graph_objects.Figure: The bar chart, sorted by count.
    """
    data = pd.DataFrame(food_count.most_common(), columns=["Food", "Count"])
    data = data.sort_values("Count", ascending=False)
    fig = px.bar(
        data,
        x="Food",
        y="Count",
        color="Food",
        category_orders={"Food": data["Food"].tolist()},
    )
    fig.update_layout(showlegend=False)
    fig.update_traces(
        hovertemplate="<b>Food </b>%{x}<br><b>Count </b>%{y}<extra></extra>"
    )
    return fig


user_info = load_user_info()
wines = load_wines(user_info)

selected_wine = st.selectbox("Select wine", wines["WineName"].dropna().unique())
wine_row = wines[wines["WineName"] == selected_wine].iloc[0]

harmonize = wine_row["Harmonize"]
if isinstance(harmonize, str) and harmonize != "N/A":
    formatted_foods = format_food_list(ast.literal_eval(harmonize))
    st.write(f"Recommended food pairings for {selected_wine} are {formatted_foods}")
else:
    st.write(f"No food pairings available for {selected_wine}")

st.subheader(
    f"{wine_row['Type']} wines with {wine_row['Body'].lower()} body "
    "are usually paired with:"
)
_, food_count = suggest_food(wines, wine_row["Type"], wine_row["Body"], 100)
st.plotly_chart(build_pairings_chart(food_count), use_container_width=True)