import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from bson import ObjectId
from typing import List

from .crawler import Crawler
from .db import db, ensure_indexes
from .logger import logger
from .utils import now_utc

app = FastAPI(title="BooksToScrape Crawler API", version="1.0")

crawler_instance: Crawler | None = None
crawler_task: asyncio.Task | None = None


@app.on_event("startup")
async def startup():
    await ensure_indexes()
    logger.info("📦 MongoDB indexes ensured.")
    global crawler_instance
    crawler_instance = Crawler()


@app.on_event("shutdown")
async def shutdown():
    global crawler_instance
    if crawler_instance:
        crawler_instance._stop = True
    logger.info("🛑 API shutting down.")


@app.get("/status")
async def get_status():
    """Return crawler status."""
    global crawler_instance, crawler_task
    running = crawler_task is not None and not crawler_task.done()
    return {
        "running": running,
        "visited_count": len(crawler_instance.visited) if crawler_instance else 0,
        "timestamp": now_utc(),
    }


@app.post("/crawl/start")
async def start_crawl(background_tasks: BackgroundTasks):
    """Start crawl in background."""
    global crawler_instance, crawler_task

    if crawler_task and not crawler_task.done():
        raise HTTPException(status_code=400, detail="Crawler is already running")

    async def run():
        try:
            await crawler_instance.run()
        except Exception as e:
            logger.error(f"Crawler failed: {e}")
        finally:
            logger.info("Crawler finished.")

    crawler_task = asyncio.create_task(run())
    logger.info("🚀 Crawler started in background.")
    return {"message": "Crawl started", "ts": now_utc()}


@app.post("/crawl/stop")
async def stop_crawl():
    """Stop the active crawler gracefully."""
    global crawler_instance
    if not crawler_instance:
        raise HTTPException(status_code=404, detail="Crawler not initialized")
    crawler_instance._stop = True
    return {"message": "Stopping crawler...", "ts": now_utc()}


@app.get("/books")
async def list_books(limit: int = 20, skip: int = 0):
    """List stored books."""
    cursor = db.books.find({}, {"raw_html_gzip": 0}).skip(skip).limit(limit)
    books = []
    async for b in cursor:
        b["_id"] = str(b["_id"])
        books.append(b)
    return books


@app.get("/books/{book_id}")
async def get_book(book_id: str):
    """Retrieve a single book by ID."""
    try:
        oid = ObjectId(book_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    book = await db.books.find_one({"_id": oid})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book["_id"] = str(book["_id"])
    return book


@app.get("/")
async def root():
    return {"message": "BooksToScrape crawler API running.", "time": now_utc()}
