import schedule
import time
import subprocess
import sys

def run_crawl():
    print("Running scheduled task...")
    subprocess.run([sys.executable, "-m", "src.scheduler.daily_crawl"], check=True)

schedule.every(10).seconds.do(run_crawl)

while True:
    schedule.run_pending()
    time.sleep(10)
