import pytest
from unittest.mock import AsyncMock
from src.crawler.crawler import Crawler

@pytest.mark.asyncio
async def test_full_run(monkeypatch):
    c = Crawler()

    async def fake_fetch(url):
        class FakeResponse:
            status_code = 200
            text = "<html></html>"
            content = b"<html></html>"
        return FakeResponse()

    # Async mocks for db
    mock_checkpoints = AsyncMock()
    mock_checkpoints.find_one.return_value = None
    mock_books = AsyncMock()
    mock_books.insert_one.return_value = {"inserted_id": "xyz"}
    mock_html_snapshots = AsyncMock()
    mock_html_snapshots.insert_one.return_value = {"inserted_id": "snap"}

    monkeypatch.setattr("src.crawler.crawler.db.checkpoints", mock_checkpoints)
    monkeypatch.setattr("src.crawler.crawler.db.books", mock_books)
    monkeypatch.setattr("src.crawler.crawler.db.html_snapshots", mock_html_snapshots)
    monkeypatch.setattr("src.crawler.crawler.ensure_indexes", AsyncMock())
    monkeypatch.setattr(c, "fetch_with_retry", fake_fetch)
    monkeypatch.setattr("src.crawler.crawler.parse_listing_page", lambda html: (["url_1", "url_2"], None))
    monkeypatch.setattr("src.crawler.crawler.parse_book_page", lambda html, url: {"name": "Book", "source_url": url})
    monkeypatch.setattr(c, "upsert_book", AsyncMock(return_value={"type": "new", "book": {"name": "Book"}}))

    changes = await c.run()
    assert all(c["type"] == "new" for c in changes)
