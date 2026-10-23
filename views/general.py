"""General page: the big picture of how X responded."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.data import (
    MUTED, POST_URL, SENTIMENT_ORDER, SKY, STANCE_ORDER, THEME_ORDER, WHITE,
    hbar, kpi, load_posts, responses, sentiment_split, style, wordcloud_image,
    word_counts,
)

df = load_posts()
orig = df[df["type"] == "Original"].iloc[0]
r = responses(df)

st.title("UBOS on X")
st.markdown(
    f"How people on X responded to the Uganda Bureau of Statistics' "
    f"[public statement]({POST_URL}) (21 Oct 2026) against the Ministry of ICT's "
    f"National Data Strategy."
)

# KPI row
neg = (r["sentiment"] == "Negative").mean()
c1, c2, c3, c4 = st.columns(4)
kpi(c1, "Responses analysed", f"{len(r):,}",
    f"{(r.type == 'Reply').sum()} replies · {(r.type == 'Quote').sum()} quotes")
kpi(c2, "Negative", f"{neg:.0%}", f"{(r.sentiment == 'Positive').sum()} positive posts only")
top_theme = r["theme"].value_counts().idxmax()
kpi(c3, "Top theme", top_theme.split(" and ")[0], top_theme)
kpi(c4, "Original post views", f"{int(orig.views):,}",
    f"{int(orig.likes):,} likes · {int(orig.reposts):,} reposts")

st.write("")

# Sentiment and word cloud
left, right = st.columns([5, 7], gap="large")
with left:
    st.subheader("Sentiment")
    st.plotly_chart(sentiment_split(r, "type", ["Reply", "Quote"]), width="stretch",
                    config={"displayModeBar": False})
    st.caption(
        "Labels come from a review of every post, not just a lexicon. "
        "Luganda, slang and sarcasm are read in context."
    )
    st.plotly_chart(hbar(r["stance"].value_counts(), STANCE_ORDER, title="Who gets the blame"),
                    width="stretch", config={"displayModeBar": False})

with right:
    st.subheader("Most used words")
    img = wordcloud_image(tuple(r["text"]))
    if img is not None:
        st.image(img, width="stretch")
    top = word_counts(r["text"]).most_common(10)
    st.caption("Top 10: " + " · ".join(f"**{w}** {n}" for w, n in top))

st.divider()

# Themes and timing
left, right = st.columns(2, gap="large")
with left:
    st.subheader("What people talked about")
    st.plotly_chart(hbar(r["theme"].value_counts(), THEME_ORDER),
                    width="stretch", config={"displayModeBar": False})

with right:
    st.subheader("When they responded")
    hrs = r["hours_after_post"].clip(upper=36)
    bins = pd.cut(hrs, bins=range(0, 37, 2), right=False, include_lowest=True)
    counts = bins.value_counts().sort_index()
    labels = [f"{int(b.left)}-{int(b.right)}h" for b in counts.index]
    fig = go.Figure(go.Bar(
        x=labels, y=counts.values, marker=dict(color=SKY, cornerradius=4),
        hovertemplate="%{x} after post: %{y} posts<extra></extra>",
    ))
    first = (r["hours_after_post"] <= 4).mean()
    fig.add_annotation(x=labels[1], y=counts.max(), text=f"{first:.0%} came in the first 4 hours",
                       showarrow=False, xanchor="left", font=dict(color=WHITE), yshift=10)
    fig.update_yaxes(title=dict(text="Posts", font=dict(color=MUTED)))
    fig.update_xaxes(title=dict(text="Hours after the UBOS post (last bin includes later)",
                                font=dict(color=MUTED)), showgrid=False)
    st.plotly_chart(style(fig, 360), width="stretch", config={"displayModeBar": False})

st.divider()

# Loudest voices
st.subheader("Loudest responses")
st.caption("Top 5 by likes. Follow the handle to read the full post on X.")
for row in r.sort_values("likes", ascending=False).head(5).itertuples():
    text = row.text.replace("\n", " ") or "_(media only)_"
    st.markdown(
        f"""<div class="post"><div class="who"><a href="{row.url}" target="_blank">{row.handle}</a>
        · {row.type} · {row.likes:,} likes · {row.views:,} views · {row.sentiment}</div>
        {text}</div>""",
        unsafe_allow_html=True,
    )

st.divider()
agree = (r.loc[r.has_text, "sentiment"] == r.loc[r.has_text, "vader_label"]).mean()
st.caption(
    f"Data: {len(r)} replies and quote posts captured from X on 23 Oct 2026. "
    f"VADER agrees with the reviewed labels on {agree:.0%} of posts with text; "
    "see the Drill down page for the comparison."
)
