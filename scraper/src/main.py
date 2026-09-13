import os
import time
import json
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pydantic import BaseModel, ValidationError, HttpUrl
from typing import Optional

CACHE_DIR = "cache"
OUTPUT_DIR = "output"
USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/AhadAli11/CRUD)"
TIMEOUT = 10
DELAY = 0.5

# Set to True to test failure handling with one fake URL — see Stage 5 checkpoint
INJECT_FAKE_URL = False

class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl
    price_text: str
    price_gbp: float
    availability_text: str
    rating_text: Optional[str] = None
    description: Optional[str] = None
    source_page: HttpUrl
    fetched_at: str


class FetchError(Exception):
    """Raised when a page could not be fetched, after any retries."""
    def __init__(self, url, status_code=None, reason=""):
        self.url = url
        self.status_code = status_code
        self.reason = reason
        super().__init__(f"{reason} (url={url}, status={status_code})")


def fetch(url, cache_filename, allow_retry=True):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        return html

    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
    except requests.exceptions.RequestException as e:
        if allow_retry:
            print(f"RETRY (network error): {url}")
            time.sleep(1)
            return fetch(url, cache_filename, allow_retry=False)
        raise FetchError(url, reason=f"network error: {e}")

    if response.status_code == 404:
        raise FetchError(url, status_code=404, reason="page not found")
    if response.status_code == 403:
        raise FetchError(url, status_code=403, reason="access forbidden")
    if response.status_code >= 500:
        if allow_retry:
            print(f"RETRY (server error {response.status_code}): {url}")
            time.sleep(1)
            return fetch(url, cache_filename, allow_retry=False)
        raise FetchError(url, status_code=response.status_code, reason="server error after retry")
    if response.status_code != 200:
        raise FetchError(url, status_code=response.status_code, reason="unexpected status")

    response.encoding = "utf-8"
    html = response.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"FETCH: {cache_filename} ({len(html)} bytes)")

    time.sleep(DELAY)
    return html


def discover_catalogue_pages(max_pages=3):
    base_url = "https://books.toscrape.com/catalogue/page-1.html"
    page_num = 1
    all_book_urls = []

    current_url = base_url
    while page_num <= max_pages:
        cache_filename = f"catalogue-page-{page_num}.html"
        html = fetch(current_url, cache_filename)
        soup = BeautifulSoup(html, "html.parser")

        for article in soup.select("article.product_pod"):
            link = article.select_one("h3 a")
            if link and link.get("href"):
                absolute_url = urljoin(current_url, link["href"])
                all_book_urls.append((absolute_url, current_url))

        if page_num == max_pages:
            break

        next_link = soup.select_one("li.next a")
        if not next_link:
            break
        current_url = urljoin(current_url, next_link["href"])
        page_num += 1

    seen = set()
    unique = []
    for url, source in all_book_urls:
        if url not in seen:
            seen.add(url)
            unique.append((url, source))

    if INJECT_FAKE_URL:
        fake_url = "https://books.toscrape.com/catalogue/this-book-does-not-exist_9999/index.html"
        unique.append((fake_url, current_url))
        print(f"[TEST MODE] injected fake URL: {fake_url}")

    print(f"catalogue_pages={page_num} discovered={len(all_book_urls)} unique_urls={len(unique)}")
    return unique


def slugify_for_cache(url):
    return url.rstrip("/").split("/")[-2] + ".html"


def parse_price(price_text):
    cleaned = "".join(c for c in price_text if c.isdigit() or c == ".")
    return float(cleaned)


def extract_book(url, source_page):
    cache_filename = slugify_for_cache(url)
    html = fetch(url, cache_filename)
    soup = BeautifulSoup(html, "html.parser")

    product_main = soup.select_one("div.product_main")
    title = product_main.select_one("h1").get_text(strip=True)
    price_text = product_main.select_one("p.price_color").get_text(strip=True)
    availability_text = product_main.select_one("p.availability").get_text(strip=True)

    rating_tag = product_main.select_one("p.star-rating")
    rating_text = None
    if rating_tag:
        classes = rating_tag.get("class", [])
        rating_words = [c for c in classes if c != "star-rating"]
        rating_text = rating_words[0] if rating_words else None

    description_tag = soup.select_one("#product_description ~ p")
    description = description_tag.get_text(strip=True) if description_tag else None

    return {
        "title": title,
        "product_url": url,
        "price_text": price_text,
        "price_gbp": parse_price(price_text),
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }


def main():
    start_time = datetime.now(timezone.utc)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    cache_hits_before = len(os.listdir(CACHE_DIR)) if os.path.exists(CACHE_DIR) else 0

    book_urls = discover_catalogue_pages()

    valid_records = []
    invalid_records = []
    failed_pages = []

    for url, source_page in book_urls:
        try:
            raw = extract_book(url, source_page)
        except FetchError as e:
            print(f"SKIPPED (fetch failed): {e.url} — {e.reason}")
            failed_pages.append({"url": e.url, "status_code": e.status_code, "reason": e.reason})
            continue

        try:
            validated = BookRecord(**raw)
            valid_records.append(json.loads(validated.model_dump_json()))
        except ValidationError as e:
            invalid_records.append({"record": raw, "reason": str(e)})

    with open(os.path.join(OUTPUT_DIR, "books.json"), "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)

    with open(os.path.join(OUTPUT_DIR, "errors.json"), "w", encoding="utf-8") as f:
        json.dump(invalid_records, f, indent=2, ensure_ascii=False)

    end_time = datetime.now(timezone.utc)
    cache_hits_after = len(os.listdir(CACHE_DIR)) if os.path.exists(CACHE_DIR) else 0

    report = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": (end_time - start_time).total_seconds(),
        "pages_fetched": len(book_urls),
        "cache_files_total": cache_hits_after,
        "valid_records": len(valid_records),
        "invalid_records": len(invalid_records),
        "failed_pages": len(failed_pages),
        "failed_page_details": failed_pages
    }
    with open(os.path.join(OUTPUT_DIR, "run-report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"valid_records={len(valid_records)} invalid_records={len(invalid_records)} failed_pages={len(failed_pages)}")


if __name__ == "__main__":
    main()