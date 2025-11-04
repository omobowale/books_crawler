import asyncio
import json
from typing import Set, Optional, Dict
from urllib.parse import urljoin, urlparse

from httpx import AsyncClient, RequestError

from .db import db, ensure_indexes
from .logger import logger
from .utils import gzip_bytes, compute_hash, now_utc, async_sleep
from .models import Book
from .config import settings


BASE = settings.START_URL or "https://books.toscrape.com/"


class Crawler:
    def __init__(self, start_url: str = BASE, concurrency: Optional[int] = None):
        self.start_url = start_url
        self.semaphore = asyncio.Semaphore(concurrency or settings.CRAWL_CONCURRENCY)
        self.visited: Set[str] = set()
        self.client = AsyncClient(headers={"User-Agent": settings.USER_AGENT}, timeout=30)
        self._stop = False

    async def load_checkpoint(self):
        cp = await db.checkpoints.find_one({"key": "listing_last"})
        if cp:
            return cp.get("value")
        return None

    async def save_checkpoint(self, value):
        await db.checkpoints.update_one(
            {"key": "listing_last"},
            {"$set": {"value": value}},
            upsert=True,
        )

    async def save_raw_html(self, url: str, html: bytes):
        payload = gzip_bytes(html)
        res = await db.html_snapshots.insert_one({
            "url": url,
            "html_gzip": payload,
            "ts": now_utc()
        })
        return str(res.inserted_id)

    async def upsert_book(self, item: dict, raw_html: bytes):
        # compute hash
        h = compute_hash(raw_html)
        existing = await db.books.find_one({"source_url": item["source_url"]})
        doc = {
            **item,
            "crawl_timestamp": now_utc(),
            "raw_html_hash": h,
        }

        raw_id = await self.save_raw_html(item["source_url"], raw_html)
        doc["raw_html_snapshot_id"] = raw_id

        if existing:
            # detect change
            if existing.get("raw_html_hash") != h:
                await db.book_history.insert_one({
                    "book_id": existing["_id"],
                    "previous": existing,
                    "ts": now_utc()
                })
                doc["has_changed"] = True
                await db.books.update_one({"_id": existing["_id"]}, {"$set": doc})
        else:
            await db.books.insert_one(doc)

    async def fetch_with_retry(self, url: str, attempts: Optional[int] = None):
        attempts = attempts or settings.CRAWL_RETRIES
        delay = 1
        for i in range(attempts):
            try:
                async with self.semaphore:
                    res = await self.client.get(url)
                    if res.status_code == 200:
                        return res
                    else:
                        logger.warning(f"[{res.status_code}] Retrying {url}")
            except RequestError as e:
                logger.warning(f"Error fetching {url}: {e}")
            await async_sleep(delay)
            delay *= 2
        logger.error(f"Failed after {attempts} attempts: {url}")
        return None

    async def parse_listing_page(self, html: str):
        """
        Extract book URLs and next-page link from a listing page.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        book_links = [
            urljoin(BASE, a["href"])
            for a in soup.select(".product_pod h3 a")
        ]
        next_page = soup.select_one("li.next a")
        next_url = urljoin(BASE, next_page["href"]) if next_page else None
        return book_links, next_url

    async def parse_book_page(self, html: str, url: str) -> Dict:
        """
        Extract book details from a book detail page.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one("h1").text.strip()
        price = soup.select_one(".price_color").text.strip()
        availability = soup.select_one(".instock.availability").text.strip()
        description_el = soup.select_one("#product_description ~ p")
        description = description_el.text.strip() if description_el else ""

        return {
            "title": title,
            "price": price,
            "availability": availability,
            "description": description,
            "source_url": url,
        }

    async def crawl_book(self, url: str):
        if url in self.visited:
            return
        self.visited.add(url)

        res = await self.fetch_with_retry(url)
        if not res:
            return

        item = await self.parse_book_page(res.text, url)
        await self.upsert_book(item, res.content)
        logger.info(f"✅ Saved book: {item['title']}")

    async def crawl_listing(self, start_url: str):
        next_url = await self.load_checkpoint() or start_url

        while next_url and not self._stop:
            logger.info(f"📖 Crawling page: {next_url}")
            res = await self.fetch_with_retry(next_url)
            if not res:
                break

            book_links, next_page = await self.parse_listing_page(res.text)
            tasks = [self.crawl_book(link) for link in book_links]
            await asyncio.gather(*tasks)

            await self.save_checkpoint(next_page)
            next_url = next_page

    async def run(self):
        logger.info("🚀 Starting crawler...")
        await ensure_indexes()
        try:
            await self.crawl_listing(self.start_url)
        finally:
            await self.client.aclose()
            logger.info("🛑 Crawler stopped.")
