# src/api/main.py
from fastapi import FastAPI
from .routers import crawler, books
from .dependencies import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from ..utils.config import settings
import sys
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="BooksToScrape API", version="1.0")
app.state.limiter = limiter

# Startup validation
@app.on_event("startup")
async def validate_settings():
    missing = []
    if not settings.MONGO_URI:
        missing.append("MONGO_URI")
    if not settings.API_KEY:
        missing.append("API_KEY")
    if missing:
        msg = f"Required environment variables are missing: {', '.join(missing)}"
        logger.critical(msg)
        # Exit the app immediately
        sys.exit(1)
    logger.info("✅ All required environment variables are set.")

# Register routers
app.include_router(crawler.router)
app.include_router(books.router)

@app.get("/")
async def root():
    from ..utils.helpers import now_utc
    return {"message": "BooksToScrape crawler API running.", "time": now_utc()}

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return {"status": "error", "message": "Rate limit exceeded"}
