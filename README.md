# Books to Scrape Crawler

A scalable async web crawler and API for https://books.toscrape.com using FastAPI, MongoDB, and asyncio.

## Table of Contents
- [Installation](#installation)
  - [Docker Setup (Recommended)](#docker-setup-recommended)
  - [Manual Setup](#manual-setup)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Running Tests](#running-tests)
- [Database Schema](#database-schema)

## Installation

Clone the repository:
```bash
git clone https://github.com/omobowale/books_crawler.git
cd books_crawler
```

### Docker Setup (Recommended)

The fastest way to get started is using Docker.

**Build the Docker image:**
```bash
docker build -t books_api .
```

**Run the container:**
```bash
docker run -d --name books_api -p 8000:8000 books_api
```

This will:
- Start the FastAPI server on port 8000
- Automatically schedule a daily crawl at 2 AM
- Store crawler logs at `/app/reports/daily_crawler.log` inside the container

**Verify the cron job is active:**
```bash
docker exec -it books_api crontab -l
```

Expected output:
```
0 2 * * * /src/scripts/run_daily_crawl.sh
```

**Manually trigger the crawler:**
```bash
docker exec -it books_api bash /src/scripts/run_daily_crawl.sh
```

**Check crawler logs:**
```bash
docker exec -it books_api cat /app/reports/daily_crawl.log
```

### Manual Setup

**Navigate to the project directory:**
```bash
cd books_crawler
```

**Create a `.env` file:**
Copy the contents of `.env.example` into a new `.env` file.

**Create and activate a virtual environment:**
```bash
# macOS/Linux
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Start the FastAPI server:**
```bash
uvicorn src.app.main:app --reload --host 0.0.0.0 --port 8000
```

**Schedule daily crawls:**
- On Windows: Use Task Scheduler to run the crawl script daily
- On macOS/Linux: Set up a cron job

## Usage

### Interacting with the API

1. **Authenticate** using the API key from your `.env` file in the Swagger UI

2. **Start crawling:**
   - Hit the `POST /crawl/start` endpoint

3. **Fetch crawled books:**
   - Get all books: `GET /books`
   - Get specific book: `GET /books/{id}` (where `id` is the `_id` attribute)

4. **View data changes:**
   - Hit the `GET /change` endpoint

## API Documentation

Swagger documentation is available at:
```
http://localhost:8000/docs
```

## Running Tests

Tests are located in the `tests` folder. Run them using:
```bash
python -m pytest
```

## Database Schema

### Sample MongoDB Document Structure

```json
{
  "_id": "ObjectId('690bc672e0bca3e95eb1d0c7')",
  "name": "A Light in the Attic",
  "description": "It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition. Silverstein's humorous and creative verse can amuse the dowdiest of readers. Lemon-faced adults and fidgety kids sit still and read these rhythmic words and laugh and smile and love th It's hard to imagine a world without A Light in the Attic. This now-classic collection of poetry and drawings from Shel Silverstein celebrates its 20th anniversary with this special edition. Silverstein's humorous and creative verse can amuse the dowdiest of readers. Lemon-faced adults and fidgety kids sit still and read these rhythmic words and laugh and smile and love that Silverstein. Need proof of his genius? RockabyeRockabye baby, in the treetopDon't you know a treetopIs no safe place to rock?And who put you up there,And your cradle, too?Baby, I think someone down here'sGot it in for you. Shel, you never sounded so good. ...more",
  "category": "Poetry",
  "price": {
    "including_tax": 51.77,
    "excluding_tax": 51.77
  },
  "availability": "In stock (22 available)",
  "num_reviews": 0,
  "image_url": "https://books.toscrape.com/media/cache/fe/72/fe72f0532301ec28892ae79a629a293c.jpg",
  "rating": 3,
  "source_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "crawl_timestamp": "ISODate('2025-11-05T21:49:38.610Z')",
  "raw_html_hash": "a6e572bec156bf80ff3149b89b6d218cdcf8866ccc26ccf69a5431db8e142c6a",
  "raw_html_snapshot_id": "690bc672e0bca3e95eb1d0c6"
}
```

## Dependencies

All project dependencies are listed in `requirements.txt`.

### With versions:
Package                  Version
------------------------ ---------
annotated-doc            0.0.3
annotated-types          0.7.0
anyio                    4.11.0
backports.asyncio.runner 1.2.0
beautifulsoup4           4.14.2
certifi                  2025.10.5
click                    8.3.0
cssselect                1.3.0
Deprecated               1.3.1
dnspython                2.8.0
exceptiongroup           1.3.0
fastapi                  0.121.0
h11                      0.16.0
h2                       4.3.0
hpack                    4.1.0
httpcore                 1.0.9
httptools                0.7.1
httpx                    0.28.1
hyperframe               6.1.0
idna                     3.11
iniconfig                2.3.0
limits                   5.6.0
motor                    3.7.1
orjson                   3.11.4
packaging                25.0
pip                      23.0.1
pluggy                   1.6.0
pydantic                 2.12.4
pydantic_core            2.41.5
pydantic-settings        2.2.1
Pygments                 2.19.2
pymongo                  4.15.3
pytest                   8.4.2
pytest-asyncio           1.2.0
python-dotenv            1.2.1
python-multipart         0.0.20
PyYAML                   6.0.3
schedule                 1.2.2
setuptools               79.0.1
slowapi                  0.1.9
sniffio                  1.3.1
soupsieve                2.8
starlette                0.49.3
tomli                    2.3.0
typing_extensions        4.15.0
typing-inspection        0.4.2
uvicorn                  0.38.0
uvloop                   0.22.1
watchfiles               1.1.1
websockets               15.0.1
wheel                    0.45.1
wrapt                    2.0.0

Python Version: 3.10.19+

## Screenshots
- Screenshots of logs of successful + scheduler runs 

![alt text](<Screenshot 2025-11-06 024520.png>)

![alt text](<Screenshot 2025-11-06 024555.png>)

