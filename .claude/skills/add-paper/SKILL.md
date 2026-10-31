---
name: add-paper
description: Use when a paper should be added to the homepage or its entry changed, for example a new acceptance, an arXiv preprint, an award or oral, a camera-ready update, or a preprint that was accepted. Input can be an arXiv, DOI, OpenReview or proceedings link, BibTeX, a PDF, or a short note from the user.
argument-hint: "[link | BibTeX | PDF path | note]"
---

# Adding or updating a paper

Request: $ARGUMENTS

## 1. Pick the type

Every paper goes in the one list under Selected publications, as `<article class="pub">`. The first tag in its venue line gives the type.

| Status | Type tag | Venue |
|---|---|---|
| Accepted at a conference | `Conference` | `<em>VENUE</em> YYYY` |
| Journal article | `Journal` | `<em>Journal name</em> YYYY` |
| Workshop paper | `Workshop` | `<em>Workshop name</em>, YYYY` |
| Public on arXiv, not accepted yet | `Preprint` | `<em>arXiv</em> YYYY` |
| Under review with no public version | Not on the page. Tell the user, and offer to add it once it is on arXiv or accepted | |

A preprint that gets accepted keeps its entry and its `id`. Change its type tag and venue, then move it to its new place in the order.

## 2. Fill the record

Fill every field from the source in the third column. Open sources in this order and stop as soon as all fields are filled:

1. what the user gave you
2. the arXiv abstract page (WebFetch `https://arxiv.org/abs/<id>`)
3. the full text (WebFetch `https://arxiv.org/html/<id>`, or the PDF the user gave)
4. the code repo README

| Field | Rule | Source |
|---|---|---|
| `id` | lowercase short name of the method (`duelrec`). It is also the teaser filename. An existing entry keeps its `id` | — |
| title | exact, with the published capitalization | paper |
| authors | full list in order, spelled as in the paper; `<strong>Chung Park</strong>`, `†` after the corresponding author | paper (user for `†`) |
| venue | type tag, then `<em>VENUE</em> YYYY`, plus the track if it is not the main track | user or acceptance notice |
| award | Oral, Spotlight, Best Paper… only when announced | user |
| links | Paper, arXiv, Code, Project, Press, in that order, only those that exist | paper page, repo |
| impact | only a production or online A/B result that the paper or public repo states, with its number and baseline | full text, repo |
| summary | one sentence, at most 30 words, in your own words: the problem, then the idea | abstract |

The user's word is enough for status, award, venue and dates. Do not search the web to confirm an acceptance.

When an existing entry moves, carry over its impact line. Recheck that line only if the user says the numbers changed.

If a field can't be filled, write `<span class="todo">…</span>` there and list it in your report.

## 3. Edit `index.html`

- Copy the matching block from [templates.html](templates.html). Do not invent new markup.
- Order is newest first, by venue year. Within a year, the later conference goes first.
- News: add one item for an acceptance, award or oral, dated the month the user told you, unless they give another date. Link it with `<a href="#id">`.
- Footer: "Last updated" becomes the current month.

## 4. Teaser (if a figure is available)

Run `python3 scripts/make_teaser.py <figure-or-pdf> <id> [--page N] [--crop X,Y,W,H]`. Then open the PNG with Read and check it shows the main figure.

With no figure, skip this step; the page shows the `data-label` tile.

## 5. Finish

1. Run `python3 scripts/check_site.py` and fix errors until it reports 0.
2. Report to the user in this shape:
   - **Changed:** list, news, footer (one line each)
   - **Left as TODO:** fields, if any
   - **Question:** "Update the CV (`assets/cv.pdf`) too?"
