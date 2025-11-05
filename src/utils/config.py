from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base crawl URL
    START_URL: str = "https://books.toscrape.com/"

    # MongoDB
    MONGO_URI: str  # required, no default
    MONGO_DB: str = "books_to_scrape"  # can have a default

    # Crawler
    CRAWL_CONCURRENCY: int = 5
    USER_AGENT: str = "BooksToScrapeCrawler/1.0 (+https://example.com)"
    CRAWL_RETRY_ATTEMPTS: int = 3
    CRAWL_RETRY_BACKOFF: float = 2.0
    CRAWL_DELAY: float = 0.5  # seconds between retries or pages

    # Logging
    LOG_LEVEL: str = "INFO"

    # API auth
    API_KEY: str  # required, no default

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
