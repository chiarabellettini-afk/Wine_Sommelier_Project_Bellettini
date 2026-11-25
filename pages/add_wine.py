"""Page to add and delete custom wines."""

import streamlit as st

from wine_sommelier.data_loader import load_wines, load_wines_raw
from wine_sommelier.pairing import suggest_food
from wine_sommelier.user_store import custom_wine_names, load_user_info, save_user_info


def add_custom_wine(user_info, wines, name, wine_type, body):
    """Create a custom wine with suggested pairings and save it.

    Args:
        user_info (dict): User info with "Custom_wine" and "Favorites".
        wines (pd.DataFrame): Full wine table, used to pick the new ID
            and to suggest food pairings.
        name (str): Name of the new wine.
        wine_type (str): Wine type, e.g. "Red".
        body (str): Wine body, e.g. "Full-bodied".
    """
    foods, _ = suggest_food(wines, wine_type, body, 5)
    user_info.setdefault("Custom_wine", []).append({
        "WineID": int(wines["WineID"].max()) + 1,
        "WineName": name,
        "Type": wine_type,
        "Body": body,
        "Harmonize": str(foods),
    })
    save_user_info(user_info)


def delete_custom_wine(user_info, name):
    """Delete a custom wine and remove it from the favorites.

    Args:
        user_info (dict): User info with "Custom_wine" and "Favorites".
        name (str): Name of the custom wine to delete.
    """
    deleted_ids = {
        wine["WineID"] for wine in user_info["Custom_wine"]
        if wine["WineName"] == name
    }
    user_info["Custom_wine"] = [
        wine for wine in user_info["Custom_wine"] if wine["WineName"] != name
    ]
    user_info["Favorites"] = [
        wine_id for wine_id in user_info.get("Favorites", [])
        if wine_id not in deleted_ids
    ]
    save_user_info(user_info)


user_info = load_user_info()
wines = load_wines(user_info)
wines_raw = load_wines_raw()
custom_names = custom_wine_names(user_info)

st.subheader("Add a custom wine:")
new_name = st.text_input("Wine name:").strip()
new_type = st.selectbox("Wine type:", wines_raw["Type"].dropna().unique())
new_body = st.selectbox("Wine body:", wines_raw["Body"].dropna().unique())

if st.button("Add"):
    if not new_name:
        st.warning("Please enter a wine name")
    elif new_name in custom_names:
        st.warning("Name already in use, please choose another name")
    else:
        add_custom_wine(user_info, wines, new_name, new_type, new_body)
        st.toast("Wine added correctly")
        st.rerun()

st.subheader("Delete a custom wine:")
if custom_names:
    to_delete = st.selectbox("Select wine to delete", custom_names)
    if st.button("Delete custom wine"):
        delete_custom_wine(user_info, to_delete)
        st.toast(f"Successfully deleted {to_delete}!")
        st.rerun()
else:
    st.info("No custom wines available to delete yet.")