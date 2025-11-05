# models.py
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Optional
from datetime import datetime


class Price(BaseModel):
    including_tax: float
    excluding_tax: float


class Book(BaseModel):
    name: str
    description: Optional[str]
    category: Optional[str]
    price: Price
    availability: Optional[str]
    num_reviews: Optional[int]
    image_url: Optional[HttpUrl]
    rating: Optional[int]

    # Metadata (not part of scraped "data" per se)
    crawl_timestamp: datetime = Field(default_factory=datetime.utcnow)
    source_url: HttpUrl
    raw_html_hash: Optional[str]
    raw_html_snapshot_id: Optional[str]


    @validator("rating", pre=True)
    def normalize_rating(cls, v):
        # expects 1–5
        if v is None:
            return None
        return int(v)
