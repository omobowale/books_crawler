import pytest
import asyncio
from httpx import Response, RequestError
from unittest.mock import AsyncMock
from src.crawler.crawler import Crawler
from src.utils.helpers import compute_hash
from types import SimpleNamespace


@pytest.mark.asyncio
async def test_checkpoint_save_and_load(monkeypatch):
    c = Crawler()
    fake_db = {}

    async def fake_update_one(filter, data, upsert):
        fake_db["listing_last"] = data["$set"]["value"]

    async def fake_find_one(filter):
        return {"key": "listing_last", "value": fake_db.get("listing_last")}

    monkeypatch.setattr("src.crawler.crawler.db.checkpoints.update_one", fake_update_one)
    monkeypatch.setattr("src.crawler.crawler.db.checkpoints.find_one", fake_find_one)

    await c.save_checkpoint("page-1.html")
    result = await c.load_checkpoint()
    assert "catalogue" in result


@pytest.mark.asyncio
async def test_fetch_with_retry(monkeypatch):
    c = Crawler()
    calls = {"count": 0}

    async def fake_get(url):
        calls["count"] += 1
        if calls["count"] < 2:
            raise RequestError("network error", request=None)
        return Response(200, text="OK")

    monkeypatch.setattr(c.client, "get", fake_get)

    res = await c.fetch_with_retry("http://example.com")
    assert res.status_code == 200
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_upsert_book_new(monkeypatch):
    c = Crawler()
    book_item = {"name": "Test Book", "source_url": "http://example.com/test"}
    html = b"<html></html>"

    # Async mocks for db
    mock_books = AsyncMock()
    mock_books.find_one.return_value = None
    mock_books.insert_one.return_value = SimpleNamespace(inserted_id="abc")

    mock_html_snapshots = AsyncMock()
    mock_html_snapshots.insert_one.return_value = SimpleNamespace(inserted_id="snap123")

    # Patch the collections
    monkeypatch.setattr("src.crawler.crawler.db.books", mock_books)
    monkeypatch.setattr("src.crawler.crawler.db.html_snapshots", mock_html_snapshots)

    result = await c.upsert_book(book_item, html)

    assert result["type"] == "new"
    assert result["book"]["name"] == "Test Book"
    mock_books.insert_one.assert_awaited_once()
    mock_html_snapshots.insert_one.assert_awaited_once()
