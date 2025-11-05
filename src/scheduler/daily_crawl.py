import asyncio
import json
import csv
from datetime import datetime
from pathlib import Path

from crawler.crawler import Crawler
from src.db import ensure_indexes
from utils.logger import logger

REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

async def run_daily_crawl():
    await ensure_indexes()
    logger.info("🚀 Starting daily scheduled crawl...")

    crawler = Crawler()
    # `crawler.run()` now returns the list of new/updated books
    changes = await crawler.run()

    if changes:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        json_path = REPORT_DIR / f"daily_changes_{timestamp}.json"
        csv_path = REPORT_DIR / f"daily_changes_{timestamp}.csv"

        # JSON report
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(changes, f, default=str, indent=2)

        # CSV report
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["type", "book", "changes"])
            writer.writeheader()
            for row in changes:
                writer.writerow(row)

        logger.info(f"✅ Daily report generated: {json_path} & {csv_path}")
    else:
        logger.info("No changes detected today.")

    logger.info("🛑 Daily scheduled crawl finished.")


if __name__ == "__main__":
    asyncio.run(run_daily_crawl())
