# SEO SERP Analyzer

Analyzes the **top 10 organic Google results** for a search query and exports everything
to a sorted Excel file (`.xlsx`):

- URL and rank of each result
- Meta title and meta description (with character counts)
- All H1 / H2 / H3 headings
- Total visible character count and word count per page
- Most frequent words, bigrams and trigrams per page, plus an aggregate "Overview" sheet

Results are fetched through the **Google Programmable Search Engine (Custom Search JSON
API)** — no scraping of google.com — and each result page is then fetched and parsed
locally. Paid ads never appear in the API response, so only organic results are analyzed.

## Setup

1. **API key:** in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials),
   create a project and an API key, then enable the **Custom Search API** for it.
2. **Search engine ID (cx):** create a search engine at
   [programmablesearchengine.google.com](https://programmablesearchengine.google.com/controlpanel/all),
   and in its settings enable **"Search the entire web"** so it returns general web
   results instead of only sites you added. Copy the search engine ID.
3. Configure credentials (pick one):
   - `cp .env.example .env` and fill in `GOOGLE_API_KEY` and `GOOGLE_CSE_ID`, or
   - `export GOOGLE_API_KEY=... GOOGLE_CSE_ID=...`, or
   - pass `--api-key` / `--cx` on the command line.

```bash
pip install -r requirements.txt
```

Free tier: **100 queries per day** (each run = 1 query). The API returns at most 10
results per query, which matches this tool exactly.

## Usage

```bash
python -m seo_analyzer "best crm for startups" --gl us --lr lang_en
python -m seo_analyzer "zahnarzt berlin" --gl de --lr lang_de -o berlin.xlsx
python -m seo_analyzer "seo tools" --no-fetch        # SERP data only, no page fetching
python -m seo_analyzer "seo tools" --top 30 --delay 2 --num 10
```

Options:

| Option | Default | Description |
| --- | --- | --- |
| `-o/--out` | auto-generated name | Output `.xlsx` path |
| `--num` | 10 | Number of organic results (1–10) |
| `--gl` | – | Country code, e.g. `us`, `de` |
| `--lr` | – | Language restriction, e.g. `lang_en` |
| `--hl` | – | Interface language |
| `--top` | 20 | How many top words/phrases to list |
| `--delay` | 1.5 | Seconds between page fetches |
| `--no-robots` | off | Skip robots.txt checks |
| `--no-fetch` | off | Only collect SERP titles/snippets |

## Output

`seo_results_<query>_<timestamp>.xlsx` with two sheets:

- **Results** — one row per organic result, sorted by rank: URL, fetch status, title,
  title length, meta description, description length, H1/H2/H3 counts and full heading
  text, total characters, word count, top words/bigrams/trigrams.
- **Overview** — query metadata plus cross-page aggregates: averages (title length,
  description length, page size, headings per page) and the most common words/phrases
  across all top-10 pages — the sheet that answers "what do the ranking pages have in
  common".

Pages that fail to load (HTTP error, non-HTML, blocked by robots.txt, timeout) are kept
in the sheet with status `error` and the reason, so the file always has 10 rows.

## Notes

- robots.txt is respected by default; use `--no-robots` only for pages you own.
- Only public pages are fetched, with a polite delay between requests.
- Run tests with: `python -m unittest discover -s tests -t . -v`

## Project layout

```
seo_analyzer/
  config.py     # credentials from env / .env / CLI args
  serp.py       # Google Custom Search JSON API (top organic results)
  fetcher.py    # page fetching with robots.txt, UA, timeout, size cap
  parser.py     # title, meta description, H1-H3, visible text extraction
  analysis.py   # char counts, stopword-filtered word/bigram/trigram frequency
  exporter.py   # sorted Excel export (Results + Overview sheets)
  cli.py        # argument parsing and pipeline
tests/          # unit tests + mocked end-to-end test
```
