import pytest
from src.utils.config import settings
from src.utils.parser import parse_listing_page, parse_book_page

def test_parse_listing_page():
    html = """
    <html>
        <body>
            <section>
                <article class="product_pod">
                    <h3><a href="book_1.html">Book One</a></h3>
                </article>
                <article class="product_pod">
                    <h3><a href="book_2.html">Book Two</a></h3>
                </article>
            </section>
            <li class="next"><a href="page-2.html">next</a></li>
        </body>
    </html>
    """
    links, next_url = parse_listing_page(html)
    assert len(links) == 2
    assert all(settings.START_URL.rstrip("/") + "/catalogue/" in link for link in links)
    assert "page-2.html" in next_url


def test_parse_book_page():
    html = """
    <html>
        <h1>Sample Book</h1>
        <ul class="breadcrumb">
            <li></li><li></li><li><a>Fiction</a></li>
        </ul>
        <th>Price (incl. tax)</th><td>£20.00</td>
        <th>Price (excl. tax)</th><td>£18.00</td>
        <p id="product_description"></p>
        <p>Description of the book.</p>
        <div class="instock availability">In stock</div>
        <div class="item active"><img src="images/sample.jpg" /></div>
        <p class="star-rating Three"></p>
        <th>Number of reviews</th><td>5</td>
    </html>
    """
    data = parse_book_page(html, "http://example.com/book_1.html")

    assert data["name"] == "Sample Book"
    assert data["category"] == "Fiction"
    assert data["price"]["including_tax"] == 20.0
    assert data["rating"] == 3
    assert data["availability"] == "In stock"
    assert data["num_reviews"] == 5
