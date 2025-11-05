# parser.py
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Tuple, Dict, Optional
from src.utils.config import settings

BASE_URL = settings.START_URL.rstrip("/") + "/catalogue/"

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}


def parse_listing_page(html: str) -> Tuple[list[str], Optional[str]]:
    """Extract all book URLs and the next page link from a listing page."""
    soup = BeautifulSoup(html, "html.parser")
    book_links = [urljoin(BASE_URL, a["href"]) for a in soup.select(".product_pod h3 a")]
    next_page = soup.select_one("li.next a")
    next_url = urljoin(BASE_URL, next_page["href"]) if next_page else None
    return book_links, next_url


def parse_book_page(html: str, url: str) -> Dict:
    """Extract structured book information from a book details page."""
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("h1").get_text(strip=True)
    description_el = soup.select_one("#product_description ~ p")
    description = description_el.get_text(strip=True) if description_el else ""

    category_el = soup.select_one("ul.breadcrumb li:nth-of-type(3) a")
    category = category_el.get_text(strip=True) if category_el else ""

    price_incl = soup.find("th", string="Price (incl. tax)")
    price_excl = soup.find("th", string="Price (excl. tax)")
    price_incl = float(price_incl.find_next("td").text.strip()[1:]) if price_incl else 0.0
    price_excl = float(price_excl.find_next("td").text.strip()[1:]) if price_excl else 0.0

    availability = soup.select_one(".instock.availability").get_text(strip=True)

    image_rel = soup.select_one(".item.active img")["src"]
    image_url = urljoin(BASE_URL, image_rel)

    rating_class = soup.select_one(".star-rating")
    rating = None
    if rating_class:
        for cls in rating_class["class"]:
            if cls in RATING_MAP:
                rating = RATING_MAP[cls]
                break

    num_reviews_el = soup.find("th", string="Number of reviews")
    num_reviews = int(num_reviews_el.find_next("td").text) if num_reviews_el else 0

    return {
        "name": title,
        "description": description,
        "category": category,
        "price": {
            "including_tax": price_incl,
            "excluding_tax": price_excl,
        },
        "availability": availability,
        "num_reviews": num_reviews,
        "image_url": image_url,
        "rating": rating,
        "source_url": url,
    }
