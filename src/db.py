import motor.motor_asyncio
from .utils.config import settings
from .utils.logger import logger


# Connect to MongoDB
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
db = client[settings.MONGO_DB]


async def ensure_indexes():
    """
    Create necessary indexes for faster lookups and uniqueness.
    """
    logger.info("Ensuring MongoDB indexes...")

    # books: main collection
    await db.books.create_index([("source_url", 1)], unique=True)
    await db.books.create_index([("upc", 1)], unique=True, sparse=True)
    await db.books.create_index([("category", 1)])
    await db.books.create_index([("crawl_timestamp", -1)])

    # history
    await db.book_history.create_index([("book_id", 1)])

    # checkpoints
    await db.checkpoints.create_index([("key", 1)], unique=True)

    logger.info("✅ Indexes ensured successfully.")


# Optional sanity check for debugging
if __name__ == "__main__":
    import asyncio

    async def test_connection():
        try:
            await ensure_indexes()
            print("MongoDB connection successful:", db.name)
        except Exception as e:
            print("MongoDB connection failed:", e)

    asyncio.run(test_connection())
