"""
scrape_msu.py — representative async web scraper for the Makena knowledge base.

This is a clean, runnable reconstruction of the targeted scraper built for the
Makena project (INFO 401, Spring 2026). It demonstrates the patterns that made
the pipeline a good citizen of the university network and kept the knowledge
base small enough for Chatbase's 10 MB first-year tier:

  * asyncio + aiohttp for concurrent fetching, compiled deterministically
  * asyncio.Semaphore(2) so we never hit the server with more than 2 requests
  * tenacity exponential-backoff retries for transient network failures
  * domain bounding so the spider never wanders off the Feliciano domain
  * DOM cleansing (drop nav/footer/script/etc.) before saving
  * [SOURCE: url] citation metadata wrapped around every chunk
  * a hard storage-size guard against the 10 MB platform limit

No credentials, no scraped university data, and no trading content live here.
Point STARTING_URLS at pages you are authorized to crawl.
"""

import asyncio
import os
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

# --- Configuration -----------------------------------------------------------

ALLOWED_DOMAIN = "montclair.edu/business"   # spider stays inside this scope
MAX_CONCURRENT_REQUESTS = 2                  # firewall-friendly rate limit
MAX_KB_BYTES = 10 * 1024 * 1024              # 10 MB Chatbase storage ceiling
OUTPUT_FILE = "msu_kb_export.txt"            # git-ignored; not committed
HEADERS = {"User-Agent": "MakenaKBBuilder/1.0 (academic project; contact via repo)"}

# Tags that are structural noise rather than policy content.
NOISE_TAGS = ["script", "style", "nav", "footer", "header", "aside", "form"]

STARTING_URLS = [
    # Replace with the specific pages you are authorized to scrape.
    "https://www.montclair.edu/business/academic-programs/",
]


class MSUScraper:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self.seen = set()

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3))
    async def fetch(self, session, url):
        """Fetch one page, capped by the semaphore and auto-retried on failure."""
        async with self.semaphore:
            async with session.get(url, timeout=20) as resp:
                resp.raise_for_status()
                return await resp.text()

    @staticmethod
    def clean(html):
        """Strip structural noise, leaving only plain policy text."""
        soup = BeautifulSoup(html, "html.parser")
        for element in soup(NOISE_TAGS):
            element.extract()
        return soup.get_text(separator="\n", strip=True)

    @staticmethod
    def discover_links(html, base_url):
        """Find in-scope links, normalizing relative paths and dropping anchors."""
        soup = BeautifulSoup(html, "html.parser")
        links = set()
        for a in soup.find_all("a", href=True):
            full_url = urljoin(base_url, a["href"]).split("#")[0]
            if ALLOWED_DOMAIN in full_url:
                links.add(full_url)
        return links

    async def scrape_one(self, session, url):
        if url in self.seen:
            return ""
        self.seen.add(url)
        try:
            html = await self.fetch(session, url)
        except Exception as exc:  # noqa: BLE001 - log and skip a bad page
            print(f"  ! skipped {url}: {exc}")
            return ""
        text = self.clean(html)
        # Citation metadata so the LLM can cite the source of each fact.
        return f"--- [SOURCE: {url}] ---\n{text}\n--- [END SOURCE] ---\n\n"

    async def run(self):
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            tasks = [self.scrape_one(session, url) for url in STARTING_URLS]
            chunks = await asyncio.gather(*tasks)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.writelines(chunks)

        # Storage-tier guard: stay under the platform's hard limit.
        size = os.path.getsize(OUTPUT_FILE)
        if size > MAX_KB_BYTES:
            print(f"  ! {OUTPUT_FILE} is {size} bytes — exceeds the "
                  f"{MAX_KB_BYTES} byte limit; truncate before upload.")
        else:
            print(f"  ✓ wrote {OUTPUT_FILE} ({size} bytes, under the 10 MB limit)")


if __name__ == "__main__":
    asyncio.run(MSUScraper().run())
