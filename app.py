#LIBRARIES

import streamlit as st
import pandas as pd
import ast
import os
import json
import plotly.express as px

from wine_sommelier.pairing import suggest_food

#Aesthetics
st.set_page_config(page_title="Wine Sommelier", page_icon="🍷", layout="wide") #, layout=None, initial_sidebar_state=None, menu_items=None
st.title("Wine Sommelier")
st.write("A web app to suggest wine pairing based on the food")

##IMPORT DATA

script_dir = os.path.dirname(os.path.abspath(__file__))
# os.path.abspath(__file__) turns that into the full path of your script
user_info_path = os.path.join(script_dir, "user_info.json")

ratings_path = os.path.join(script_dir, "data", "XWines_Test_1K_ratings.csv")
if os.path.exists(ratings_path):
    ratings = pd.read_csv(ratings_path)
else: #to avoid crashes if the file is not found
    st.error("Rating database not found")
    st.stop()

wines_path = os.path.join(script_dir, "data", "XWines_Test_100_wines.csv")
if os.path.exists(wines_path):
    wines_raw = pd.read_csv(wines_path)
else:
    st.error("Wine database not found")
    st.stop()

#wines["Favorites"] = False

bodies = wines_raw["Body"].dropna().unique().tolist()
w_type = wines_raw["Type"].dropna().unique().tolist()
all_food = wines_raw["Harmonize"].dropna().apply(ast.literal_eval).explode().unique().tolist()
#.apply(ast.literal_eval) > converts the values in the harmonize column into true python list
#.explode > separate the list into single values
#tolist > transform into a list

col = ["Btn", "WineName", "Type", "Body"]

#load custom wine data
if os.path.exists(user_info_path): 
    #we are checking if there is already a file to store the custom wines, if not we are going to create it
    try:
        with open(user_info_path) as f: #let's open the file and call it f temporarily
            user_info = json.load(f) #let's create a dictionary called user_info that will contain all the info about the user, both custom wines and favorites
    except (json.JSONDecodeError, ValueError):
        # Handles corrupt json files:
        user_info = {"Custom_wine": [], "Favorites": []}
        st.warning("The user info file was corrupted. Please discard all the data and reset the file.")
        if st.button("Reset file"):
            with open(user_info_path, "w") as f:
                json.dump(user_info, f, indent=4)
            st.rerun()
else:
    user_info = {"Custom_wine": [], "Favorites": []} #since it does not already exist, we are creating the structure to save the custom wines
    with open(user_info_path, "w") as w:
        json.dump(user_info, w) #we are putting the blank dictionary user_info inside the open file w

def load_wine(w, u_info):
    #add custom wines to dataframe. To avoid duplicates, we are using the original wine database and the info from the user json file
    custom_wine = u_info["Custom_wine"]
    custom_wine_df = pd.DataFrame(custom_wine)
    w = pd.concat([wines_raw, custom_wine_df], ignore_index=True) #we want the new wine to follow the index of the main dataset it's added to

    #Adding info about favorites to the dataframe
    fav_list = u_info.get("Favorites", [])
    w["Btn"] = w["WineID"].isin(u_info.get("Favorites", [])).apply(lambda x: "⭐" if x else "☆") #full star if the WineID is in the json list, empty star if not
    return w #this is returning the wine database updated with all the user info

def build_config(df, key):
    return{"WineName": st.column_config.TextColumn("WineName"),
           "Btn": st.column_config.ButtonColumn(" ", on_click=toggle_fav, args=(df, key), key= key)}

def load_custom_list(u_info):
    custom_wine = u_info["Custom_wine"] #this is a dictionary
    if not custom_wine:
        return []
    custom_wine_df = pd.DataFrame(custom_wine) #this is now a dataframe
    try:
        all_custom = custom_wine_df["WineName"].dropna().tolist()
    except:
        st.warning("Not possible to load wine custom list")
        return []
    return all_custom

def toggle_fav(df, key):
    wine_id = int(df.iloc[st.session_state[key]["row"]]["WineID"]) #WineID of the clicked row saved in int
    with open (user_info_path) as f:
        info = json.load(f) #we reload the file to work on the latest data
    favs = info.setdefault("Favorites", [])
    if wine_id in favs:
        favs.remove(wine_id)
    else:
        favs.append(wine_id)
    with open(user_info_path, "w") as f:
        json.dump(info, f, indent=4)

def load_wine_list(w):
    return w["WineName"].dropna().unique().tolist()



wines = load_wine(wines_raw, user_info)

#MENÙ
tabs = ["Home", "Search by Wine", "Add Wine"]
tab1, tab2, tab3 = st.tabs(tabs) 
#I choose this tab method instead of the one we used in class only because of aestetic preferences

with tab1: #HOME

    st.subheader("Search pairings by food:")
    selected_food = st.selectbox("Select food", all_food)
    suggested_wines = wines[wines["Harmonize"].apply(lambda x: selected_food in x)]

    st.write(f"Suggested wines to pair with {selected_food.lower()}:")
    st.dataframe(suggested_wines, column_config=build_config(suggested_wines, "fav1"), column_order=col, hide_index=True) #I did hide the Id and changed some names to be more readable

    st.subheader("Complete list of wines:")
    st.dataframe(wines, column_config=build_config(wines, "fav2"), column_order=col, hide_index=True)

with tab2: #Suggest foods (especially useful for custom wines)
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

    # Convert Counter to a DataFrame for charting
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
    #ADDING CUSTOM WINE
    st.subheader("Add a custom wine:")
    new_name = st.text_input("Wine name:")
    new_type = st.selectbox("Wine type:", w_type)
    new_body = st.selectbox("Wine body:", bodies)
    new_ID = int(wines["WineID"].max()) + 1
    custom_wine = user_info["Custom_wine"]
    if st.button("Add"):
        custom_list = load_custom_list(user_info)
        if new_name not in custom_list:
            suggested_food, _ = suggest_food(wines, new_type, new_body, 5) #the algorithm
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

    #DELETING CUSTOM WINE
    st.subheader("Delete a custom wine:")
    custom_list = load_custom_list(user_info) #Getting the list of custom wines
    to_delete = st.selectbox('Select wine to delete', custom_list)
    if custom_list:
        if st.button("Delete custom wine"):
            # Filter out the selected wine by its WineName
            user_info["Custom_wine"] = [
                wine
                for wine in user_info["Custom_wine"]
                if wine["WineName"] != to_delete
            ]

            # Save the updated dictionary back to the json file
            with open(user_info_path, "w") as f:
                json.dump(user_info, f, indent=4)

            st.toast(f"Successfully deleted {to_delete}!")
            st.rerun()
    else:
        st.info("No custom wines available to delete yet.")