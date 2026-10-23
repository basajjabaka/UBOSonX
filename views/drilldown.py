"""Drill down page: filter the responses and compare slices."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.data import (
    BLACK, MUTED, SENTIMENT_COLOURS, SENTIMENT_ORDER, SKY, STANCE_ORDER, THEME_ORDER,
    WHITE, kpi, load_posts, responses, sentiment_split, style, wordcloud_image,
    word_counts,
)

r = responses(load_posts())

st.markdown("Pick the slice you want. Leave a filter empty to keep all. Every chart below follows the filters.")

# Filters: one row of controls above the charts
with st.container(border=True):
    f1, f2, f3 = st.columns(3)
    types = f1.multiselect("Post type", ["Reply", "Quote"], placeholder="All")
    sents = f2.multiselect("Sentiment", SENTIMENT_ORDER, placeholder="All")
    stances = f3.multiselect("Stance", STANCE_ORDER, placeholder="All")
    f4, f5, f6 = st.columns(3)
    themes = f4.multiselect("Theme", THEME_ORDER, placeholder="All")
    max_h = float(np.ceil(r["hours_after_post"].max()))
    hours = f5.slider("Hours after the UBOS post", 0.0, max_h, (0.0, max_h), step=1.0, format="%.0f h")
    min_likes = f6.select_slider("Minimum likes", options=[0, 1, 2, 5, 10, 25, 50, 100], value=0)
    search = st.text_input("Keyword", placeholder="Enter Keyword")

def pick(col: str, chosen: list) -> pd.Series:
    """An empty selection means no filter on that column."""
    return r[col].isin(chosen) if chosen else pd.Series(True, index=r.index)


m = (
    pick("type", types)
    & pick("sentiment", sents)
    & pick("stance", stances)
    & pick("theme", themes)
    & r["hours_after_post"].between(*hours)
    & (r["likes"] >= min_likes)
)
if search.strip():
    m &= r["text"].str.contains(search.strip(), case=False, regex=False)
d = r[m]

if d.empty:
    st.info("No posts match these filters. Kindly widen the selection.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
kpi(c1, "Posts in slice", f"{len(d):,}", f"of {len(r):,} responses")
kpi(c2, "Negative", f"{(d.sentiment == 'Negative').mean():.0%}",
    f"{(d.sentiment == 'Positive').sum()} positive")
kpi(c3, "Likes", f"{int(d.likes.sum()):,}", f"median {int(d.likes.median())} per post")
kpi(c4, "Views", f"{int(d.views.sum()):,}", f"top post {int(d.views.max()):,}")

st.write("")

left, right = st.columns([7, 5], gap="large")
with left:
    st.subheader("Words in this slice")
    img = wordcloud_image(tuple(d["text"]), 1000, 520)
    if img is not None:
        st.image(img, width="stretch")
    else:
        st.caption("These posts have no text to count.")
with right:
    st.subheader("Top 12 words")
    top = word_counts(d["text"]).most_common(12)
    if top:
        w, n = zip(*top)
        fig = go.Figure(go.Bar(
            x=list(n), y=list(w), orientation="h", marker=dict(color=SKY, cornerradius=4),
            text=list(n), textposition="outside", textfont=dict(color=WHITE), cliponaxis=False,
            hovertemplate="%{y}: %{x}<extra></extra>",
        ))
        fig.update_yaxes(autorange="reversed", showgrid=False)
        fig.update_xaxes(showgrid=False, showticklabels=False, range=[0, max(n) * 1.2])
        st.plotly_chart(style(fig, 420), width="stretch", config={"displayModeBar": False})

st.divider()

left, right = st.columns(2, gap="large")
with left:
    st.subheader("Sentiment by theme")
    st.plotly_chart(sentiment_split(d, "theme", THEME_ORDER), width="stretch",
                    config={"displayModeBar": False})
with right:
    st.subheader("Sentiment by stance")
    st.plotly_chart(sentiment_split(d, "stance", STANCE_ORDER), width="stretch",
                    config={"displayModeBar": False})

st.divider()

left, right = st.columns(2, gap="large")
with left:
    st.subheader("Reach vs reaction")
    fig = go.Figure()
    for s in SENTIMENT_ORDER:
        part = d[d.sentiment == s]
        if part.empty:
            continue
        fig.add_scatter(
            x=part["views"].clip(lower=1), y=part["likes"] + 1, mode="markers", name=s,
            marker=dict(size=9, color=SENTIMENT_COLOURS[s], line=dict(color=BLACK, width=1.5)),
            customdata=np.stack([part["handle"], part["text"].str.slice(0, 90)], axis=-1),
            hovertemplate="%{customdata[0]}<br>%{x:,} views · %{y} likes (+1)"
                          "<br>%{customdata[1]}<extra></extra>",
        )
    fig.update_xaxes(type="log", title=dict(text="Views (log)", font=dict(color=MUTED)))
    fig.update_yaxes(type="log", title=dict(text="Likes + 1 (log)", font=dict(color=MUTED)))
    st.plotly_chart(style(fig, 380), width="stretch", config={"displayModeBar": False})

with right:
    st.subheader("Reviewed labels vs VADER")
    t = d[d.has_text]
    tab = pd.crosstab(t["sentiment"], t["vader_label"]).reindex(
        index=SENTIMENT_ORDER, columns=SENTIMENT_ORDER, fill_value=0)
    fig = go.Figure(go.Heatmap(
        z=tab.values, x=[f"VADER {c}" for c in tab.columns], y=list(tab.index),
        colorscale=[[0, BLACK], [1, SKY]], showscale=False, xgap=2, ygap=2,
        text=tab.values, texttemplate="%{text}", textfont=dict(color=WHITE, size=15),
        hovertemplate="Reviewed %{y} · %{x}: %{z} posts<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showgrid=False, side="top")
    st.plotly_chart(style(fig, 330), width="stretch", config={"displayModeBar": False})
    agree = np.trace(tab.values) / max(tab.values.sum(), 1)
    st.caption(f"Agreement: {agree:.0%}. VADER often reads sarcasm and Luganda as neutral or positive.")

st.divider()

st.subheader("Posts")
show = d.sort_values("likes", ascending=False)[
    ["created_eat", "handle", "type", "sentiment", "stance", "theme", "likes", "views", "text", "url"]
]
st.dataframe(
    show, width="stretch", hide_index=True, height=420,
    column_config={
        "created_eat": st.column_config.TextColumn("Time (EAT)"),
        "handle": "Handle", "type": "Type", "sentiment": "Sentiment", "stance": "Stance",
        "theme": "Theme",
        "likes": st.column_config.NumberColumn("Likes", format="%d"),
        "views": st.column_config.NumberColumn("Views", format="%d"),
        "text": st.column_config.TextColumn("Post", width="large"),
        "url": st.column_config.LinkColumn("Link", display_text="Open"),
    },
)
st.download_button("Download Dataset", show.to_csv(index=False).encode("utf-8"),
                   "ubos_on_x_slice.csv", "text/csv")
