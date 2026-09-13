import os
import time
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

    html = response.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"FETCH: {cache_filename} ({len(html)} bytes)")

    time.sleep(DELAY)  # politeness delay — only after a REAL request, never after a cache hit
    return html


def discover_catalogue_pages(max_pages=3):
    """Follow the catalogue's own 'next' link, starting at page 1, stopping after max_pages."""
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
                all_book_urls.append(absolute_url)

        if page_num == max_pages:
            break

        next_link = soup.select_one("li.next a")
        if not next_link:
            break  # site ran out of pages before we hit our limit
        current_url = urljoin(current_url, next_link["href"])
        page_num += 1

    unique_urls = list(dict.fromkeys(all_book_urls))
    print(f"catalogue_pages={page_num} discovered={len(all_book_urls)} unique_urls={len(unique_urls)}")
    return unique_urls

def main():
    urls = discover_catalogue_pages()


if __name__ == "__main__":
    main()