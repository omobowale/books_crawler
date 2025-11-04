from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .logger import logger


BASE = "https://books.toscrape.com/"




def parse_listing_page(html: str):
    soup = BeautifulSoup(html, "html.parser")
    # find links to book detail pages
    links = []
    for article in soup.select("article.product_pod"):
        a = article.find("h3").find("a")
        href = a.get("href")
        links.append(urljoin(BASE, href))
    # next page
    next_btn = soup.select_one("li.next > a")
    next_href = None
    if next_btn:
        next_href = urljoin(BASE, next_btn.get("href"))
    return links, next_href




def parse_book_page(html: str, url: str):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.select_one("div.product_main > h1").text.strip()
    desc_tag = soup.select_one("#product_description ~ p")
    description = desc_tag.text.strip() if desc_tag else None
    category = soup.select_one("ul.breadcrumb li:nth-of-type(3) a").text.strip()
    img = soup.select_one("div.carousel img") or soup.select_one("div.item.active img")
    if not img:
        img = soup.select_one("div.thumbnail img")
    image_url = urljoin(BASE, img["src"]) if img else None
    # table
    table = {r.find_all("th")[0].text.strip(): r.find_all("td")[0].text.strip() for r in soup.select("table.table.table-striped tr")}
    upc = table.get("UPC")
    price_excl = float(table.get("Price (excl. tax)", "0").lstrip("£"))
    price_incl = float(table.get("Price (incl. tax)", "0").lstrip("£"))
    availability = table.get("Availability")
    num_reviews = int(table.get("Number of reviews", "0"))
    # rating from class
    rating_class = soup.select_one("p.star-rating")
    rating = None
    if rating_class:
        classes = rating_class.get("class", [])
        mapping = {"One":1, "Two":2, "Three":3, "Four":4, "Five":5}
        for c in classes:
            if c in mapping:
                rating = mapping[c]
                break
    return {
    "name": title,
    "description": description,
    "category": category,
    "price": {"including_tax": price_incl, "excluding_tax": price_excl},
    "availability": availability,
    "num_reviews": num_reviews,
    "image_url": image_url,
    "rating": rating,
    "upc": upc,
    "source_url": url,
    }