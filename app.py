"""
Wine Sommelier - Streamlit entry point.

This file only declares the pages of the app; the content of each page
lives in the ``pages/`` folder.

Run with:  streamlit run app.py
"""

import streamlit as st

st.set_page_config(page_title="Wine Sommelier", page_icon="🍷", layout="wide")
st.title("Wine Sommelier")

pages = [
    st.Page("pages/home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/search_by_wine.py", title="Search by Wine", icon="🔍"),
    st.Page("pages/add_wine.py", title="Add Wine", icon="➕"),
    st.Page("pages/analytics.py", title="Analytics", icon="📊"),
]

st.navigation(pages).run()

