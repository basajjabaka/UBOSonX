# Method notes

This page explains how the data was collected, labelled, and shown.

## Collection

- **Date:** 23 Oct 2026, about two days after the post.
- **Source:** the post's replies page and its quotes page on X, read in a
  logged-in browser session.
- **Fields:** post ID, handle, display name, time, replies, reposts, likes,
  views, and text.
- **Volume:** 390 replies and 125 quote posts. The post itself showed 417
  replies; the gap is mostly nested replies and posts that X hides.

Note: 25 responses have no text (image or video only). They are counted as
neutral with no stance.

## Labels

Each response with text was read and given three labels.

### Sentiment

The overall tone of the post.

| Label | Meaning |
| --- | --- |
| Negative | Criticism, anger, shame, mockery, or despair. |
| Neutral | Questions, tags, facts, or neutral reactions such as "Eeh". |
| Positive | Approval, support, or enjoyment. |

### Stance

Who the post blames or backs.

| Label | Meaning |
| --- | --- |
| Blames both / govt | Faults both bodies or government at large. |
| Against UBOS | Faults UBOS, its statement, or its data. |
| Backs UBOS | Agrees with UBOS. |
| Against Ministry | Faults the Ministry of ICT. |
| No clear stance | No side taken. |

### Theme

The main topic of the post.

| Label | Examples |
| --- | --- |
| Coordination and channels | "Couldn't you just call each other?" |
| Governance and leadership | "Signs of a collapsing government." |
| Humour and drama | "Time to get popcorn." |
| Data vs statistics mandate | "Data is broader than statistics." |
| Money, budget and jobs | "It's about bread." |
| Census and data quality | "Your census data was wrong." |
| Other | Tags, spam, and requests to summarise. |

## Why not VADER alone

VADER is a lexicon tool built for English social media. It is kept in the
data as `vader_score` and `vader_label` for comparison.

On these posts, VADER agrees with the reviewed labels only 48% of the time.
It misses:

- **Luganda and Runyankore**, for example *Mwekube* ("fight it out") and
  *Wano wetutuuse?* ("Where have we reached?").
- **Local memes**, for example "uncoordinated troop movements".
- **Sarcasm**, for example "Uganda the pearl of Africa!"

## Word cloud

- Mentions, links, and hashtags are removed.
- Common English filler words and a few Luganda fillers are removed.
- Spellings are merged, for example `govt` and `gov't` become `government`.

## Colours

The dashboard uses X's colours only: black `#000000`, white `#FFFFFF`, and sky
blue `#1D9BF0`. A light sky blue `#8ECDF8` marks positive posts. Every chart
also has text labels, so colour is never the only cue.
