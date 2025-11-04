import hashlib
import gzip
import asyncio
from datetime import datetime
from .logger import logger


async def async_sleep(seconds: float):
    await asyncio.sleep(seconds)




def compute_hash(obj_bytes: bytes) -> str:
    return hashlib.sha256(obj_bytes).hexdigest()




def gzip_bytes(b: bytes) -> bytes:
    return gzip.compress(b)




def now_utc():
    return datetime.utcnow()