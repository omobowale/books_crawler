import motor.motor_asyncio
from .config import settings
from .logger import logger


client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]


async def ensure_indexes():
# books: main collection
    await db.books.create_index([("source_url", 1)], unique=True)
    await db.books.create_index([("upc", 1)], unique=True, sparse=True)
    await db.books.create_index([("category", 1)])
    await db.books.create_index([("crawl_timestamp", -1)])
    # history
    await db.book_history.create_index([("book_id", 1)])
    # checkpoints
    await db.checkpoints.create_index([("key", 1)], unique=True)
logger.info("Indexes ensured")