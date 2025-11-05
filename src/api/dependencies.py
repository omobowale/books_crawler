from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from slowapi.util import get_remote_address
from slowapi import Limiter
from ..utils.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=True)

limiter = Limiter(key_func=get_remote_address)

async def get_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key
