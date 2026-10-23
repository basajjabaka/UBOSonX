"""Shared data loading, colours and chart helpers for the dashboard."""

import re
from collections import Counter
from pathlib import Path

import matplotlib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from wordcloud import STOPWORDS, WordCloud

ROOT = Path(__file__).resolve().parents[1]
FONT = str(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans-Bold.ttf")
POST_URL = "https://x.com/StatisticsUg/status/2112882051552612637"

# X brand colours only: black, white, sky blue (plus tints of sky blue).
BLACK = "#000000"
WHITE = "#FFFFFF"
SKY = "#1D9BF0"
SKY_LIGHT = "#8ECDF8"
SKY_DEEP = "#0F5C8F"
GRID = "rgba(255,255,255,0.12)"
MUTED = "rgba(255,255,255,0.65)"

SENTIMENT_ORDER = ["Negative", "Neutral", "Positive"]
SENTIMENT_COLOURS = {"Negative": SKY, "Neutral": WHITE, "Positive": SKY_LIGHT}

STANCE_ORDER = [
    "Blames both / govt",
    "Against UBOS",
    "No clear stance",
    "Backs UBOS",
    "Against Ministry",
]
THEME_ORDER = [
    "Coordination and channels",
    "Governance and leadership",
    "Humour and drama",
    "Data vs statistics mandate",
    "Money, budget and jobs",
    "Census and data quality",
    "Other",
]

EXTRA_STOPWORDS = {
    "will", "now", "one", "us", "u", "guys", "re", "ve", "s", "t", "m", "ll", "d",
    "don", "didn", "can", "get", "also", "even", "just", "let", "etc", "eh", "ehh",
    "oh", "yet", "still", "via", "dont", "cant", "thats", "amp", "ng", "ur", "abt",
    "ya", "wa", "mu", "na", "la", "ku", "re", "im", "co", "lol", "yall", "y", "n",
    "see", "know", "make", "made", "take", "things", "thing", "way", "much", "many",
    "really", "something", "someone", "anything", "ok", "okay", "go", "come", "need",
    "two", "2", "first", "today", "yesterday", "like", "say", "says", "said", "well",
    "though", "every", "seriously", "going", "want", "think", "another", "needs", "without", "naye", "kati", "awo", "mwe", "nga",
}
STOPWORDS_ALL = {w.lower() for w in STOPWORDS} | EXTRA_STOPWORDS

# Light normalisation so spellings of the same word count together.
NORMALISE = {
    "govt": "government", "gov": "government", "gov't": "government",
    "govts": "government", "gava": "government", "governments": "government",
    "ministries": "ministry", "minstry": "ministry", "agencies": "agency",
    "institutions": "institution", "entities": "entity", "ugandans": "ugandan",
    "ubos's": "ubos", "moict&ng": "moict", "moictng": "moict", "cencus": "census",
    "statistic": "statistics", "mandates": "mandate", "troop": "troops",
}


@st.cache_data
def load_posts() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "data" / "posts.csv", dtype={"id": str})
    df["text"] = df["text"].fillna("")
    df["url"] = "https://x.com/" + df["handle"].str.lstrip("@") + "/status/" + df["id"]
    return df


def responses(df: pd.DataFrame) -> pd.DataFrame:
    """Replies and quotes only, without the original UBOS post."""
    return df[df["type"] != "Original"].copy()


def tokens(texts) -> list[str]:
    words = []
    for t in texts:
        t = re.sub(r"https?://\S+", " ", t)
        t = re.sub(r"[@#]\w+", " ", t)
        t = t.lower().replace("’", "'")
        for w in re.findall(r"[a-z][a-z'&]+", t):
            w = NORMALISE.get(w.strip("'"), w.strip("'"))
            if len(w) > 2 and w not in STOPWORDS_ALL:
                words.append(w)
    return words


def word_counts(texts) -> Counter:
    return Counter(tokens(texts))


def _colour_func(top: set):
    def f(word, **_):
        return WHITE if word in top else SKY
    return f


@st.cache_data
def wordcloud_image(texts: tuple, width: int = 1200, height: int = 560):
    counts = word_counts(texts)
    if not counts:
        return None
    top = {w for w, _ in counts.most_common(8)}
    wc = WordCloud(
        font_path=FONT, width=width, height=height, background_color=BLACK, max_words=120,
        prefer_horizontal=0.95, margin=6, random_state=7, collocations=False,
        min_font_size=10,
    ).generate_from_frequencies(counts)
    wc.recolor(color_func=_colour_func(top))
    return wc.to_array()


def style(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor=BLACK,
        plot_bgcolor=BLACK,
        font=dict(color=WHITE, size=13),
        margin=dict(l=8, r=8, t=36, b=8),
        legend=dict(orientation="h", y=1.12, x=0, font=dict(color=MUTED), traceorder="normal"),
        hoverlabel=dict(bgcolor=BLACK, bordercolor=SKY, font=dict(color=WHITE)),
        bargap=0.25,
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID,
                     tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID,
                     tickfont=dict(color=MUTED))
    return fig


def hbar(counts: pd.Series, order: list[str], colour: str = SKY, title: str = "") -> go.Figure:
    """Horizontal bar of counts with value and share labels."""
    counts = counts.reindex([o for o in order if o in counts.index]).fillna(0)
    total = counts.sum() or 1
    fig = go.Figure(
        go.Bar(
            x=counts.values, y=counts.index, orientation="h",
            marker=dict(color=colour, cornerradius=4),
            text=[f"{int(v)}  ({v / total:.0%})" for v in counts.values],
            textposition="outside", textfont=dict(color=WHITE),
            hovertemplate="%{y}: %{x} posts<extra></extra>", cliponaxis=False,
        )
    )
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(showgrid=False, showticklabels=False,
                     range=[0, counts.max() * 1.35 if counts.max() else 1])
    fig.update_layout(title=dict(text=title, font=dict(size=15)))
    return style(fig, height=60 + 42 * len(counts))


def sentiment_split(df: pd.DataFrame, by: str, order: list[str]) -> go.Figure:
    """100% stacked bars of sentiment per group, labelled in the segments."""
    tab = pd.crosstab(df[by], df["sentiment"]).reindex(columns=SENTIMENT_ORDER, fill_value=0)
    tab = tab.reindex([o for o in order if o in tab.index])
    share = tab.div(tab.sum(axis=1), axis=0)
    fig = go.Figure()
    for s in SENTIMENT_ORDER:
        fig.add_bar(
            y=share.index, x=share[s], name=s, orientation="h",
            marker=dict(color=SENTIMENT_COLOURS[s], line=dict(color=BLACK, width=2)),
            text=[f"{v:.0%}" if v >= 0.08 else "" for v in share[s]],
            textposition="inside", insidetextanchor="middle",
            textfont=dict(color=BLACK),
            customdata=tab[s], hovertemplate=f"%{{y}}<br>{s}: %{{x:.0%}} (%{{customdata}} posts)<extra></extra>",
        )
    fig.update_layout(barmode="stack")
    fig.update_xaxes(tickformat=".0%", range=[0, 1], showgrid=False)
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return style(fig, height=110 + 46 * len(share))


def kpi(col, label: str, value: str, note: str = "") -> None:
    col.markdown(
        f"""<div class="kpi"><div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>""",
        unsafe_allow_html=True,
    )


CSS = f"""
<style>
.block-container {{padding-top: 2rem; max-width: 1200px;}}
h1, h2, h3 {{letter-spacing: -0.01em;}}
.kpi {{border: 1px solid rgba(255,255,255,0.18); border-radius: 16px; padding: 14px 16px;}}
.kpi-label {{color: {MUTED}; font-size: 0.85rem;}}
.kpi-value {{color: {WHITE}; font-size: clamp(1.25rem, 2.1vw, 1.9rem); font-weight: 700;
  line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}}
.kpi-note {{color: {SKY}; font-size: 0.8rem; min-height: 1rem;}}
.post {{border-left: 3px solid {SKY}; padding: 4px 0 4px 14px; margin: 6px 0 14px;}}
.post .who {{color: {MUTED}; font-size: 0.85rem;}}
a, [data-testid="stMarkdownContainer"] a {{color: {SKY} !important;}}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stExpandSidebarButton"] {{display: none;}}
.app-title {{text-align: center; margin: 0 0 0.6rem; padding: 0;}}
[class*="st-key-tab-"] a {{border-radius: 999px; padding: 6px 20px; text-decoration: none;}}
[class*="st-key-tab-off"] a {{border: 1px solid rgba(255,255,255,0.35); background: transparent;}}
[class*="st-key-tab-off"] a p, [class*="st-key-tab-off"] a span {{color: {WHITE} !important;}}
[class*="st-key-tab-on"] a {{border: 1px solid {SKY}; background: {SKY};}}
[class*="st-key-tab-on"] a p, [class*="st-key-tab-on"] a span {{color: {WHITE} !important; font-weight: 700;}}
.st-key-tabs {{margin-bottom: 1.2rem;}}
hr {{border-color: rgba(255,255,255,0.18);}}
</style>
"""
