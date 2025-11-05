import asyncio
from typing import Set, Optional, Dict
from httpx import AsyncClient, RequestError
from urllib.parse import urljoin

from src.db import db, ensure_indexes
from ..utils.logger import logger
from src.utils.helpers import gzip_bytes, compute_hash, now_utc, async_sleep
from ..models import Book
from ..utils.config import settings
from ..utils.parser import parse_listing_page, parse_book_page


# Crawl from /catalogue/
BASE = settings.START_URL.rstrip("/") + "/catalogue/"

class Crawler:
    def __init__(self, start_url: str = BASE, concurrency: Optional[int] = None):
        # Ensure the start URL is correct
        if not start_url.endswith(".html"):
            start_url = urljoin(BASE, "page-1.html")

        logger.info("start url====================== 1")
        logger.info(start_url)
        logger.info("start url====================== 2")
        self.start_url = start_url
        self.semaphore = asyncio.Semaphore(concurrency or settings.CRAWL_CONCURRENCY)
        self.visited: Set[str] = set()
        self.client = AsyncClient(headers={"User-Agent": settings.USER_AGENT}, timeout=30)
        self._stop = False

    async def load_checkpoint(self):
        cp = await db.checkpoints.find_one({"key": "listing_last"})
        if not cp or not cp.get("value"):
            return None

        next_url = cp["value"]
        # ✅ Normalize old checkpoints without /catalogue/
        if "catalogue" not in next_url:
            next_url = urljoin(BASE, "page-1.html")

        return next_url

    async def save_checkpoint(self, value):
        # ✅ Normalize before saving
        if value and "catalogue" not in value:
            value = urljoin(BASE, value)
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

    async def upsert_book(self, item: dict, raw_html: bytes) -> dict | None:
        """
        Upsert a single book.
        Returns a dict describing the change:
            {"type": "new" | "updated", "book": item, "changes": {...}}
        or None if no change.
        """
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
            if existing.get("raw_html_hash") != h:
                await db.book_history.insert_one({
                    "book_id": existing["_id"],
                    "previous": existing,
                    "ts": now_utc()
                })
                doc["has_changed"] = True
                await db.books.update_one({"_id": existing["_id"]}, {"$set": doc})
                return {"type": "updated", "book": doc, "changes": existing}
            return None
        else:
            await db.books.insert_one(doc)
            logger.info(f"✅ Inserted new book: {item['name']}")
            return {"type": "new", "book": doc}

    async def fetch_with_retry(self, url: str, attempts: Optional[int] = None):
        attempts = attempts or settings.CRAWL_RETRY_ATTEMPTS
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

    async def crawl_book(self, url: str, changes_list: list):
        if url in self.visited:
            return
        self.visited.add(url)

        res = await self.fetch_with_retry(url)
        if not res:
            return

        item = parse_book_page(res.text, url)
        change = await self.upsert_book(item, res.content)
        if change:
            changes_list.append(change)

    async def crawl_listing(self, start_url: str, changes_list: list):
        next_url = await self.load_checkpoint() or start_url

        # ✅ Auto-correct if the URL doesn’t contain /catalogue/
        if "catalogue" not in next_url:
            next_url = urljoin(BASE, "page-1.html")

        while next_url and not self._stop:
            logger.info(f"📖 Crawling page: {next_url}")
            res = await self.fetch_with_retry(next_url)
            if not res:
                break

            book_links, next_page = parse_listing_page(res.text)
            # Normalize next_page
            if next_page and "catalogue" not in next_page:
                next_page = urljoin(BASE, next_page)

            tasks = [self.crawl_book(link, changes_list) for link in book_links]
            await asyncio.gather(*tasks)

            await self.save_checkpoint(next_page)
            next_url = next_page

    async def run(self):
        logger.info("🚀 Starting crawler...")
        await ensure_indexes()
        changes = []
        try:
            await self.crawl_listing(self.start_url, changes)
            return changes
        finally:
            await self.client.aclose()
            logger.info("🛑 Crawler stopped.")
