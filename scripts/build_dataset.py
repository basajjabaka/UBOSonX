"""Build data/posts.csv from the raw X captures and the reviewed labels.

Run from the repo root:
    python scripts/build_dataset.py
"""

import re
from pathlib import Path

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
ORIGINAL_ID = "2112882051552612637"

SOURCES = [
    (RAW / "replies_part1.txt", "Reply"),
    (RAW / "replies_part2.txt", "Reply"),
    (RAW / "quotes.txt", "Quote"),
]

LINE = re.compile(
    r"^(\d+) (@\S+) (.*?) ?(\d{4}-\d\d-\d\dT[\d:.]+Z) (\d+) (\d+) (\d+) (\d+) ?(.*)$"
)

SENTIMENT = {"N": "Negative", "U": "Neutral", "P": "Positive"}
STANCE = {
    "S": "Backs UBOS",
    "A": "Against UBOS",
    "M": "Against Ministry",
    "B": "Blames both / govt",
    "X": "No clear stance",
}
THEME = {
    "C": "Coordination and channels",
    "G": "Governance and leadership",
    "K": "Census and data quality",
    "D": "Data vs statistics mandate",
    "H": "Humour and drama",
    "$": "Money, budget and jobs",
    "O": "Other",
}


def parse_raw() -> pd.DataFrame:
    rows = []
    for path, kind in SOURCES:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            m = LINE.match(line)
            if not m:
                raise ValueError(f"Bad line in {path.name}: {line[:60]}")
            pid, handle, name, ts, rep, rt, likes, views, text = m.groups()
            rows.append(
                {
                    "id": pid,
                    "type": "Original" if pid == ORIGINAL_ID else kind,
                    "handle": handle,
                    "name": name,
                    "created_at": ts,
                    "replies": int(rep),
                    "reposts": int(rt),
                    "likes": int(likes),
                    "views": int(views),
                    "text": text.replace(" ⏎ ", "\n").replace("⏎", "").strip(),
                }
            )
    df = pd.DataFrame(rows).drop_duplicates("id").reset_index(drop=True)
    df["idx"] = df.index
    return df


def load_labels() -> pd.DataFrame:
    recs = []
    for line in (ROOT / "data" / "labels.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        idx, s, st, th = line.split()
        recs.append({"idx": int(idx), "s": s, "st": st, "th": th})
    return pd.DataFrame(recs)


def vader_label(score: float) -> str:
    if score >= 0.05:
        return "Positive"
    if score <= -0.05:
        return "Negative"
    return "Neutral"


def main() -> None:
    df = parse_raw()
    analyser = SentimentIntensityAnalyzer()
    df["vader_score"] = df["text"].apply(lambda t: analyser.polarity_scores(t)["compound"])
    df["vader_label"] = df["vader_score"].apply(vader_label)

    df = df.merge(load_labels(), on="idx", how="left")
    # Posts with no text (media only) and the original post have no review label.
    df[["s", "st", "th"]] = df[["s", "st", "th"]].fillna({"s": "U", "st": "X", "th": "O"})
    df["sentiment"] = df["s"].map(SENTIMENT)
    df["stance"] = df["st"].map(STANCE)
    df["theme"] = df["th"].map(THEME)
    df["has_text"] = df["text"].str.len() > 0

    ts = pd.to_datetime(df["created_at"], utc=True).dt.tz_convert("Africa/Kampala")
    df["created_eat"] = ts.dt.strftime("%Y-%m-%d %H:%M")
    df["hours_after_post"] = (
        (ts - ts[df["type"] == "Original"].iloc[0]).dt.total_seconds() / 3600
    ).round(2)
    df["engagement"] = df["replies"] + df["reposts"] + df["likes"]
    df["words"] = df["text"].str.split().str.len().fillna(0).astype(int)

    cols = [
        "id", "type", "handle", "name", "created_at", "created_eat", "hours_after_post",
        "replies", "reposts", "likes", "views", "engagement", "words", "has_text",
        "sentiment", "stance", "theme", "vader_score", "vader_label", "text",
    ]
    df[cols].to_csv(ROOT / "data" / "posts.csv", index=False)
    print(df["type"].value_counts().to_string())
    print(df[df["type"] != "Original"]["sentiment"].value_counts().to_string())


if __name__ == "__main__":
    main()
