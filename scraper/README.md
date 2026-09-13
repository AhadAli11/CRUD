# The Polite Scraper

## Target classification

- **Site:** Books to Scrape (https://books.toscrape.com)
- **Why:** A public sandbox site built specifically for people to practice scraping — confirmed by reading toscrape.com, which describes itself as existing for exactly this purpose.
- **Scope:** The first 3 catalogue pages only (60 books total).
- **Data collected:** Title, price, availability, star rating, description, and product URL — publicly displayed book listing data, nothing account-gated or personal.
- **robots.txt result:** Requested `https://books.toscrape.com/robots.txt` and got a `404 Not Found`. No robots file exists on this site. A missing file is not permission — it's just a missing file.
- **Why this is appropriate here:** The site exists for this exact purpose, the scope is small and bounded (3 pages, 60 books), and no login, paywall, or access restriction is being bypassed.

I will not reuse this code on another site without checking its rules and terms first.