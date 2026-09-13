import os
import time
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

CACHE_DIR = "cache"
USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/AhadAli11/CRUD)"
TIMEOUT = 10
DELAY = 0.5


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

    response.encoding = "utf-8"  # force correct decoding instead of requests' guess
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
                all_book_urls.append((absolute_url, current_url))  # keep source_page too

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
    """Turn a book URL into a safe cache filename."""
    return url.rstrip("/").split("/")[-2] + ".html"


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
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat()
    }


def main():
    book_urls = discover_catalogue_pages()

    records = []
    for url, source_page in book_urls:
        record = extract_book(url, source_page)
        records.append(record)

    print(f"detail_pages={len(records)}")
    sample = records[0].copy()
    sample["description"] = (sample["description"][:100] + "...") if sample["description"] else None
    print(sample)