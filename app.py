import streamlit as st
import pandas as pd
import ast
import os
import json
import plotly.express as px

from wine_sommelier.pairing import suggest_food
from wine_sommelier.rating_analytics import analyze_vintage_correlation, compute_wine_rating_stats

st.set_page_config(page_title="Wine Sommelier", page_icon="🍷", layout="wide")
st.title("Wine Sommelier")
st.write("A web app to suggest wine pairing based on the food")

script_dir = os.path.dirname(os.path.abspath(__file__))
user_info_path = os.path.join(script_dir, "user_info.json")

ratings_path = os.path.join(script_dir, "data", "XWines_Test_1K_ratings.csv")
if os.path.exists(ratings_path):
    ratings = pd.read_csv(ratings_path)
else:
    st.error("Rating database not found")
    st.stop()

wines_path = os.path.join(script_dir, "data", "XWines_Test_100_wines.csv")
if os.path.exists(wines_path):
    wines_raw = pd.read_csv(wines_path)
else:
    wines_raw = pd.read_csv("https://github.com/rogerioxavier/X-Wines/tree/main/Dataset/last")
    

bodies = wines_raw["Body"].dropna().unique().tolist()
w_type = wines_raw["Type"].dropna().unique().tolist()
all_food = wines_raw["Harmonize"].dropna().apply(ast.literal_eval).explode().unique().tolist()

col = ["Btn", "WineName", "Type", "Body", "Rating"]

if os.path.exists(user_info_path): 
    try:
        with open(user_info_path) as f: 
            user_info = json.load(f) 
    except (json.JSONDecodeError, ValueError):
        user_info = {"Custom_wine": [], "Favorites": []}
        st.warning("The user info file was corrupted. Please discard all the data and reset the file.")
        if st.button("Reset file"):
            with open(user_info_path, "w") as f:
                json.dump(user_info, f, indent=4)
            st.rerun()
else:
    user_info = {"Custom_wine": [], "Favorites": []}
    with open(user_info_path, "w") as w:
        json.dump(user_info, w)

def load_wine(w, u_info):
    """Combine base wine data with custom wines and favorite indicators."""
    custom_wine = u_info["Custom_wine"]
    custom_wine_df = pd.DataFrame(custom_wine)
    w = pd.concat([wines_raw, custom_wine_df], ignore_index=True) 
    w["Btn"] = w["WineID"].isin(u_info.get("Favorites", [])).apply(lambda x: "⭐" if x else "☆")
    mean_df = compute_wine_rating_stats(ratings)[["WineID", "mean_rating"]].rename(
        columns={"mean_rating": "Rating"})
    w = w.merge(mean_df, on="WineID", how="left").round(1)
    return w

def build_config(df, key):
    return{"WineName": st.column_config.TextColumn("WineName"),
           "Btn": st.column_config.ButtonColumn(" ", on_click=toggle_fav, args=(df, key), key= key)}

def load_custom_list(u_info):
    """Return a list of custom wine names from user info."""
    custom_wine = u_info["Custom_wine"]
    if not custom_wine:
        return []
    custom_wine_df = pd.DataFrame(custom_wine)
    try:
        all_custom = custom_wine_df["WineName"].dropna().tolist()
    except:
        st.warning("Not possible to load wine custom list")
        return []
    return all_custom

def toggle_fav(df, key):
    """Toggle a wine's favorite status in the user JSON file based on the clicked row."""
    wine_id = int(df.iloc[st.session_state[key]["row"]]["WineID"])
    with open (user_info_path) as f:
        info = json.load(f)
    favs = info.setdefault("Favorites", [])
    if wine_id in favs:
        favs.remove(wine_id)
    else:
        favs.append(wine_id)
    with open(user_info_path, "w") as f:
        json.dump(info, f, indent=4)

def load_wine_list(w):
    """Return a list of unique wine names from a wine DataFrame."""
    return w["WineName"].dropna().unique().tolist()

wines = load_wine(wines_raw, user_info)

wine_stats = compute_wine_rating_stats(ratings)
wines = wines.merge(wine_stats, on="WineID", how="left")
vintage_corr = analyze_vintage_correlation(ratings)

tabs = ["Home", "Search by Wine", "Add Wine", "Analytics"]
tab1, tab2, tab3, tab4 = st.tabs(tabs) 

with tab1:

    st.subheader("Search pairings by food:")
    selected_food = st.selectbox("Select food", all_food)
    suggested_wines = wines[wines["Harmonize"].apply(lambda x: selected_food in x)]

    st.write(f"Suggested wines to pair with {selected_food.lower()}:")
    st.dataframe(suggested_wines, column_config=build_config(suggested_wines, "fav1"), column_order=col, hide_index=True) #I did hide the Id and changed some names to be more readable

    st.subheader("Complete list of wines:")
    st.dataframe(wines, column_config=build_config(wines, "fav2"), column_order=col, hide_index=True)

with tab2:
    all_wines = load_wine_list(wines)
    selected_wine = st.selectbox("Select wine", all_wines)

    food_list = ast.literal_eval(wines[wines["WineName"] == selected_wine]["Harmonize"].values[0])
    food_list = [food.lower() for food in food_list]
    
    if len(food_list) > 1:
        formatted_foods = ", ".join(food_list[:-1]) + " and " + food_list[-1]
    else:
        formatted_foods = food_list[0]
    st.write(f"Recommended food pairings for {selected_wine} are {formatted_foods}")

    st.subheader("Wines with this type and body are usually paired with:")

    _, food_count = suggest_food(wines, wines.loc[wines["WineName"] == selected_wine, "Type"].iloc[0], wines.loc[wines["WineName"] == selected_wine, "Body"].iloc[0], 100)

    pairings_chart = (pd.DataFrame(food_count.most_common(), columns=["Food", "Count"]).sort_values("Count", ascending=False)) #
    pairings_chart["Food"] = pd.Categorical(pairings_chart["Food"], categories=pairings_chart["Food"], ordered=True)
    
    fig = px.bar(
        pairings_chart,
        x="Food",
        y="Count",
        color="Food",
        category_orders={"Food": pairings_chart["Food"].tolist()}
    )
    fig.update_layout(showlegend=False)
    fig.update_traces(hovertemplate="<b>Food </b>%{x}<br><b>Count </b>%{y}<extra></extra>")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Add a custom wine:")
    new_name = st.text_input("Wine name:")
    new_type = st.selectbox("Wine type:", w_type)
    new_body = st.selectbox("Wine body:", bodies)
    new_ID = int(wines["WineID"].max()) + 1
    custom_wine = user_info["Custom_wine"]
    if st.button("Add"):
        custom_list = load_custom_list(user_info)
        if new_name not in custom_list:
            suggested_food, _ = suggest_food(wines, new_type, new_body, 5)
            new_wine = {"WineID": new_ID, "WineName": new_name, "Type": new_type, "Body": new_body, "Harmonize": str(suggested_food)}
            if "Custom_wine" not in user_info:
                user_info["Custom_wine"] = []
            custom_wine = user_info["Custom_wine"]
            if new_wine in custom_wine:
                st.error("Wine already in the list")
            else:
                custom_wine.append(new_wine)
            with open (user_info_path, "w") as f:
                json.dump(user_info, f, indent=4)
                st.toast("Wine added correctly")
                st.rerun()
        else:
            st.warning("Name already in use, please choose another name")

    st.subheader("Delete a custom wine:")
    custom_list = load_custom_list(user_info) 
    to_delete = st.selectbox('Select wine to delete', custom_list)
    if custom_list:
        if st.button("Delete custom wine"):
            user_info["Custom_wine"] = [
                wine
                for wine in user_info["Custom_wine"]
                if wine["WineName"] != to_delete]
            with open(user_info_path, "w") as f:
                json.dump(user_info, f, indent=4)
            st.toast(f"Successfully deleted {to_delete}!")
            st.rerun()
    else:
        st.info("No custom wines available to delete yet.")

with tab4:
    with st.expander("Rating & Vintage Statistical Insights"):
        st.write(
            f"Vintage vs. Rating Spearman $\\rho$: **{vintage_corr['rho']:.3f}** "
            f"(p-value: **{vintage_corr['p_value']:.4f}**, n = {vintage_corr['n']})"
        )
        st.dataframe(
            wines[["WineName", "rating_count", "mean_rating", "bayesian_score", "ci_low", "ci_high"]].dropna(subset=["bayesian_score"]),
            hide_index=True,
        )