from fastapi import APIRouter, HTTPException, Query, Security, Request
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from bson import ObjectId
from src.db import db
from ..dependencies import get_api_key, limiter
from src.utils.helpers import now_utc
from src.api.responses import success, warning, error

router = APIRouter()


# ----------------------------
# Pydantic Response Models
# ----------------------------

class PriceModel(BaseModel):
    including_tax: float
    excluding_tax: float

class BookResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    description: Optional[str]
    category: Optional[str]
    price: PriceModel
    availability: Optional[str]
    num_reviews: Optional[int]
    image_url: Optional[HttpUrl]
    rating: Optional[int]
    source_url: HttpUrl
    crawl_timestamp: str

class BooksListResponse(BaseModel):
    status: str
    message: str
    data: List[BookResponse]

class ChangeResponse(BaseModel):
    id: str = Field(..., alias="_id")
    book_id: Optional[str]
    previous: dict
    ts: str

class ChangesListResponse(BaseModel):
    status: str
    message: str
    data: List[ChangeResponse]

# ----------------------------
# Endpoints
# ----------------------------

@router.get("/books", response_model=BooksListResponse)
@limiter.limit("100/hour")
async def list_books(
    request: Request,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    rating: Optional[int] = None,
    sort_by: Optional[str] = None,
    limit: int = 20,
    skip: int = 0,
    api_key: str = Security(get_api_key)
):
    query = {}
    if category:
        query["category"] = category
    if rating:
        query["rating"] = rating
    if min_price is not None or max_price is not None:
        query["price.including_tax"] = {}
        if min_price is not None:
            query["price.including_tax"]["$gte"] = min_price
        if max_price is not None:
            query["price.including_tax"]["$lte"] = max_price

    cursor = db.books.find(query, {"raw_html_gzip": 0})
    if sort_by:
        sort_field = {
            "rating": ("rating", -1),
            "price": ("price.including_tax", 1),
            "reviews": ("num_reviews", -1)
        }.get(sort_by)
        if sort_field:
            cursor = cursor.sort(*sort_field)

    cursor = cursor.skip(skip).limit(limit)
    books = []
    async for b in cursor:
        b["_id"] = str(b["_id"])
        books.append(b)

    return success("Books fetched successfully", data=books)


@router.get("/books/{book_id}", response_model=BookResponse)
@limiter.limit("100/hour")
async def get_book(request: Request, book_id: str, api_key: str = Security(get_api_key)):
    try:
        oid = ObjectId(book_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    book = await db.books.find_one({"_id": oid}, {"raw_html_gzip": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book["_id"] = str(book["_id"])
    return success("Book fetched successfully", data=book)


@router.get("/changes", response_model=ChangesListResponse)
@limiter.limit("100/hour")
async def get_recent_changes(
    request: Request,
    limit: int = 20,
    skip: int = 0,
    api_key: str = Security(get_api_key)
):
    cursor = db.book_history.find({}).sort("ts", -1).skip(skip).limit(limit)
    changes = []
    async for c in cursor:
        c["_id"] = str(c["_id"])
        if "book_id" in c:
            c["book_id"] = str(c["book_id"])
        if isinstance(c.get("ts"), (bytes, bytearray)):
            c["ts"] = c["ts"].decode("utf-8")
        elif hasattr(c.get("ts"), "isoformat"):
            c["ts"] = c["ts"].isoformat()

        # Convert nested ObjectIds inside 'previous'
        prev = c.get("previous")
        if isinstance(prev, dict):
            prev["_id"] = str(prev["_id"]) if "_id" in prev else None
            if "book_id" in prev and isinstance(prev["book_id"], ObjectId):
                prev["book_id"] = str(prev["book_id"])

        changes.append(c)

    return success("Recent changes fetched successfully", data=changes)



# This is just for testing purposes
@router.delete("/books/clear")
@limiter.limit("1/minute")
async def clear_all_books(request: Request, confirm: bool = Query(False), api_key: str = Security(get_api_key)):
    if not confirm:
        return warning("Pass ?confirm=true to delete all books.")
    result = await db.books.delete_many({})
    return success(f"Deleted {result.deleted_count} books")
