from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import asyncio
from ..dependencies import get_api_key
from src.utils.logger import logger
from src.db import ensure_indexes
from src.crawler.crawler import Crawler
from src.utils.helpers import now_utc
from src.api.responses import success

router = APIRouter()
crawler_instance: Optional[Crawler] = None
crawler_task: Optional[asyncio.Task] = None

# ----------------------------
# Pydantic Response Models
# ----------------------------

class CrawlStatusResponse(BaseModel):
    running: bool
    visited_count: int
    timestamp: str

class CrawlActionResponse(BaseModel):
    message: str
    ts: str

# ----------------------------
# Startup & Shutdown
# ----------------------------

@router.on_event("startup")
async def startup():
    global crawler_instance
    await ensure_indexes()
    logger.info("📦 MongoDB indexes ensured.")
    crawler_instance = Crawler()

@router.on_event("shutdown")
async def shutdown():
    global crawler_instance
    if crawler_instance:
        crawler_instance._stop = True
    logger.info("🛑 API shutting down.")

# ----------------------------
# Endpoints
# ----------------------------

@router.get("/status", response_model=CrawlStatusResponse)
async def get_status(api_key: str = Depends(get_api_key)):
    global crawler_instance, crawler_task
    running = crawler_task is not None and not crawler_task.done()
    visited_count = len(crawler_instance.visited) if crawler_instance else 0
    return success("Crawler status fetched", data={
        "running": running,
        "visited_count": visited_count,
        "timestamp": now_utc()
    })


@router.post("/crawl/start", response_model=CrawlActionResponse)
async def start_crawl(background_tasks: BackgroundTasks, api_key: str = Depends(get_api_key)):
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

    return success("Crawl has started", data={"message": "Crawl has started", "ts": now_utc()})


@router.post("/crawl/stop", response_model=CrawlActionResponse)
async def stop_crawl(api_key: str = Depends(get_api_key)):
    global crawler_instance
    if not crawler_instance:
        raise HTTPException(status_code=404, detail="Crawler not initialized")
    crawler_instance._stop = True
    logger.info("🛑 Crawler stopping requested")
    return success("Crawler stopping", data={"message": "Stopping crawler...", "ts": now_utc()})
