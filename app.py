"""UBOS on X: entry point for the Streamlit dashboard."""

import streamlit as st

from lib.data import CSS

st.set_page_config(page_title="UBOS on X", page_icon="📊", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

pages = [
    st.Page("views/general.py", title="General", icon=":material/insights:", default=True),
    st.Page("views/drilldown.py", title="Drill down", icon=":material/filter_alt:"),
]
st.navigation(pages).run()
