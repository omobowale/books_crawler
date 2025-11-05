# ./scripts/run_daily_crawl.sh
#!/bin/bash
# Make sure we are in the correct directory
cd /app

# Activate Python environment if needed (optional for virtualenv)
# source venv/bin/activate

# Run daily crawl and log output
python src/daily_crawl.py >> reports/daily_crawl.log 2>&1