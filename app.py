"""
Wine Sommelier - Streamlit entry point.

This file only declares the pages of the app; the content of each page
lives in the ``pages/`` folder.

Run with:  streamlit run app.py
"""

import streamlit as st
from wine_sommelier.data_loader import DATA_DIR, missing_datasets


st.set_page_config(page_title="Wine Sommelier", page_icon="🍷", layout="wide")
st.title("Wine Sommelier")

missing = missing_datasets()
if missing:
    st.error(
        f"Missing dataset file(s): {', '.join(missing)}. "
        f"Download them from the X-Wines repository and place them in "
        f"`{DATA_DIR}` (see the Setup section of the README)."
    )
    st.stop()

pages = [
    st.Page("pages/home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/search_by_wine.py", title="Search by Wine", icon="🔍"),
    st.Page("pages/add_wine.py", title="Add Wine", icon="➕"),
    st.Page("pages/analytics.py", title="Analytics", icon="📊"),
]

st.navigation(pages).run()

