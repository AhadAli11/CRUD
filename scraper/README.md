# The Polite Scraper

## Target classification

- **Site:** Books to Scrape (https://books.toscrape.com)
- **Why:** A public sandbox site built specifically for people to practice scraping.
- **Scope:** The first 3 catalogue pages only (60 books total).
- **Data collected:** Title, price, availability, star rating, description, and product URL — publicly displayed book listing data, nothing account-gated or personal.
- **robots.txt result:** Requested `https://books.toscrape.com/robots.txt` and got a `404 Not Found`. No robots file exists on this site. A missing file is not permission — it's just a missing file.
- **Why this is appropriate here:** The site exists for this exact purpose, the scope is small and bounded (3 pages, 60 books), and no login, paywall, or access restriction is being bypassed.

I will not reuse this code on another site without checking its rules and terms first.

## Setup & run

```powershell
python -m venv venv
venv\Scripts\activate
pip install requests beautifulsoup4 pydantic
python src\main.py
```

Produces `output/books.json`, `output/errors.json`, and `output/run-report.json`.

## Record schema

Each validated record in `books.json`:

| Field | Type | Notes |
|---|---|---|
| title | string | |
| product_url | URL | canonical identity — de-duplicated on this |
| price_text | string | raw, as shown on the page (e.g. `"£51.77"`) |
| price_gbp | number | parsed from price_text |
| availability_text | string | raw stock text |
| rating_text | string or null | e.g. `"Three"` |
| description | string or null | null when the book has no description — never invented |
| source_page | URL | which catalogue page this book was discovered on |
| fetched_at | ISO 8601 timestamp | when this record was fetched |

## Politeness rules

- Every real request sends an honest `User-Agent`: `FlyRankInternshipA9/1.0 (+https://github.com/AhadAli11/CRUD)`
- 10-second timeout on every request — never waits forever
- 0.5-second delay between real requests (not applied to cache hits)
- Status code checked before anything else: only `200` is treated as a page
- Development reads from `cache/` — the live site is only ever touched once per page

## Retry & failure rules

- Network errors and `5xx` server errors get one retry after a short wait
- `404` and `403` never retry — asking again won't create a missing page, and retrying a refusal is how a polite scraper becomes a pest
- A broken page is logged and skipped; the rest of the run continues

## Sample run report

```json
{
  "start_time": "2026-09-13T13:22:11.137653+00:00",
  "end_time": "2026-09-13T13:22:13.762655+00:00",
  "duration_seconds": 2.625002,
  "pages_fetched": 60,
  "cache_files_total": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "failed_page_details": []
}
```

(This run was fully cached — a cold run against the live site takes roughly 60–90 seconds, due to the politeness delay on 60+ real requests.)

## Why no browser was needed

The book data — title, price, availability, description — is already present in the
HTML the server sends on first response; nothing is loaded afterward by JavaScript.
A tool like Playwright would add real startup cost (launching a browser engine) for
zero benefit here, since a plain HTTP request already receives everything needed.

## A real bug this caught

Some book descriptions on the source site are duplicated within the page's own
HTML — the raw markup itself repeats the paragraph mid-sentence before restarting
it. This isn't a scraper bug; it's genuinely messy source data. Per Stage 4's rule
("trust nothing you scraped"), the description is stored exactly as found rather
than guessed at or silently "cleaned" — a concrete example of why scraped input is
untrusted until validated.

## Ethics note

This scraper only touches a public sandbox built for this exact purpose. In any
other context: check for an official API first, never bypass a login or paywall,
respect `robots.txt` when one exists, and collect only the data actually needed —
not everything a page happens to expose.
## Target classification

- **Site:** Books to Scrape (https://books.toscrape.com)
- **Why:** A public sandbox site built specifically for people to practice scraping — confirmed by reading toscrape.com, which describes itself as existing for exactly this purpose.
- **Scope:** The first 3 catalogue pages only (60 books total).
- **Data collected:** Title, price, availability, star rating, description, and product URL — publicly displayed book listing data, nothing account-gated or personal.
- **robots.txt result:** Requested `https://books.toscrape.com/robots.txt` and got a `404 Not Found`. No robots file exists on this site. A missing file is not permission — it's just a missing file.
- **Why this is appropriate here:** The site exists for this exact purpose, the scope is small and bounded (3 pages, 60 books), and no login, paywall, or access restriction is being bypassed.

I will not reuse this code on another site without checking its rules and terms first.