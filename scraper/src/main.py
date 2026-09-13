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


def fetch(url, cache_filename):
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, cache_filename)

    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT: {cache_filename} ({len(html)} bytes)")
        return html

    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers, timeout=TIMEOUT)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}: status {response.status_code}")

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

    print(f"catalogue_pages={page_num} discovered={len(all_book_urls)} unique_urls={len(unique)}")
    return unique


def slugify_for_cache(url):
    return url.rstrip("/").split("/")[-2] + ".html"


def parse_price(price_text):
    """Turn '£51.77' into 51.77. Strips any currency symbol, keeps only digits and the decimal point."""
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
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    book_urls = discover_catalogue_pages()

    valid_records = []
    invalid_records = []

    for url, source_page in book_urls:
        raw = extract_book(url, source_page)
        try:
            validated = BookRecord(**raw)
            # store back as plain dict, with HttpUrl converted to plain str for clean JSON
            valid_records.append(json.loads(validated.model_dump_json()))
        except ValidationError as e:
            invalid_records.append({"record": raw, "reason": str(e)})

    with open(os.path.join(OUTPUT_DIR, "books.json"), "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)

    with open(os.path.join(OUTPUT_DIR, "errors.json"), "w", encoding="utf-8") as f:
        json.dump(invalid_records, f, indent=2, ensure_ascii=False)

    print(f"valid_records={len(valid_records)} invalid_records={len(invalid_records)}")


if __name__ == "__main__":
    main()