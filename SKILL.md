---
name: jev-cannibalization
description: Use when checking a site for keyword cannibalization, finding searches where Google splits impressions between two or more of the site's pages, or deciding which page should own a query, from Google Search Console data. Also use when someone wants Jev (TypeSafe) to judge Search Console data.
---

# Jev cannibalization check

## Overview

Search Console already shows where cannibalization is real: searches where Google shows two or more of your pages. This skill finds those searches in Python, then asks **Jev** (TypeSafe AI's decision model, which returns probabilities, never text) three things per search: which page should own it, whether the pages really serve the same need, and what the fix is. Plain rules turn Jev's probabilities into outcomes. **The rules make the calls, not the model.** The output is one interactive HTML report.

Numbers stay in Python. Jev is weak at arithmetic and dates, so it only ever sees the search plus a short snapshot of each page (title, H1, meta description, opening text).

## Run it

**1. Get the data: Search Console rows with BOTH query and page**, ideally the last 90 days. Queries alone won't work. Pick whichever source the user has:

- **Windsor.ai MCP** (if connected): `get_data` with connector `searchconsole`, the site's account, fields `["query","page","clicks","impressions","position"]`, `date_preset: "last_90d"`, filter `[["impressions","gte",3]]`. The result is usually too big to show and gets saved to a file. Pass that file straight in, since the `{"result": [...]}` format is supported.
- **CSV**: any export with Query, Page, Clicks, Impressions and Position columns, for example from the Search Console API or the Search Analytics for Sheets add-on.

**2. Run:**

```bash
python <this skill>/scripts/run.py <gsc.json|gsc.csv> --domain example.com
```

- Output goes to `./jev-cannibalization/<domain>/`. The report opens when it finishes.
- It prints a cost estimate first and stops above `--max-cost` (default $1). A typical site costs well under 1 cent: 64 searches cost $0.003.
- Jev answers are cached, so a re-run with the same data is free.

**Before the first run:**

1. **Python packages.** Run `python -c "import requests, bs4, lxml"`. If it fails, run `pip install -r <this skill>/requirements.txt`.
2. **OpenRouter key.** It must be in `OPENROUTER_API_KEY`, in `./jev-cannibalization/<domain>/.env`, or in `~/.config/jev-seo/.env` (the jev-internal-links key at `~/.config/jev-internal-links/.env` also works). If there is none, ask the user for one (openrouter.ai/keys) and save it with `chmod 600`. Never print the key.

## What to tell the user

Give the report path, then the outcome counts, the biggest group of mixed-up pages (Google's page versus Jev's pick, the number of searches and impressions), and 3 example searches with the positions of both pages. All of it is in `data/judgements.json` and the report.

## The outcomes (rules at the top of `scripts/run.py`)

- **Wrong page winning:** Jev is 70%+ sure and picked a different page from the one Google shows most.
- **Pages splitting signals:** Google's page is Jev's pick too, but Jev scores the other pages as the same need (60%+).
- **Right page already winning:** Google's page is Jev's pick and the others serve a different need.
- **Jev not sure:** under 70%. This goes to human review, never an automatic action.

Jev also suggests a fix (leave, strengthen, differentiate, merge). It's only acted on at 70%+ confidence, and in testing almost none got there. Present fixes as a human decision.

## Common mistakes

- **Treating "wrong page" as "will rank higher".** Jev judges which page fits the search best. Sometimes Google's page ranks better today. The action is usually to point internal links and focus at the better fit, not to redirect.
- **Recommending merges or redirects from this report alone.** Those can't be undone, so they need a human.
- **Feeding metrics into Jev's state.** Keep impressions and positions in Python.
- **Expecting identical runs.** Jev isn't deterministic. In testing, 1 of 64 outcomes changed between runs, and the cache is what keeps a run auditable.
- **Running it on client data without checking TypeSafe's terms.** API access is still early access.
