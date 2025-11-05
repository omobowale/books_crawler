from fastapi.responses import JSONResponse
from datetime import datetime

def _serialize(obj):
    """Convert non-serializable objects (like datetime) to JSON-safe values."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj

def success(message: str, data=None):
    payload = {"status": "success", "message": message}
    if data is not None:
        payload["data"] = _serialize(data)
    return JSONResponse(content=payload)

def warning(message: str):
    return JSONResponse(content={"status": "warning", "message": message})

def error(message: str, status_code=500):
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "message": message},
    )
