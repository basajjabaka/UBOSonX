"""UBOS on X: entry point for the Streamlit dashboard."""

import streamlit as st

from lib.data import CSS

st.set_page_config(page_title="UBOS on X", page_icon="📊", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

pages = [
    st.Page("views/general.py", title="General", icon=":material/insights:", default=True),
    st.Page("views/drilldown.py", title="Drill down", icon=":material/filter_alt:"),
]
current = st.navigation(pages, position="hidden")

# Title, then the page tabs centred below it. The active tab shows in sky blue.
st.markdown('<h1 class="app-title">UBOS on X</h1>', unsafe_allow_html=True)
with st.container(horizontal=True, horizontal_alignment="center", key="tabs"):
    for i, page in enumerate(pages):
        state = "on" if page.title == current.title else "off"
        with st.container(width="content", key=f"tab-{state}-{i}"):
            st.page_link(page, label=page.title, icon=page.icon)

current.run()
