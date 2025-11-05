#!/bin/bash
# Move to project root (not inside src)
cd "$(dirname "$0")../../"  

# Show where this script is running from
echo "Running from: $(pwd)"

# Ensure reports directory exists
mkdir -p reports

# Run daily crawl and log output
python -m src.scheduler.daily_crawl >> reports/daily_crawl.log 2>&1
