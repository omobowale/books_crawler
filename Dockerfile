FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code and scripts
COPY ./src ./src
COPY ./src/scripts ./scripts
COPY ./daily_cron /etc/cron.d/daily_cron
COPY .env.example .env

# Make sure reports directory exists
RUN mkdir -p /app/reports

# Install cron
RUN apt-get update && apt-get install -y cron

# Give execution rights to cron job file and register it
RUN chmod 0644 /etc/cron.d/daily_cron
RUN crontab /etc/cron.d/daily_cron

# Ensure script permissions
RUN chmod +x ./scripts/run_daily_crawl.sh
RUN chmod +x ./scripts/start.sh

# Expose the FastAPI port
EXPOSE 8000

# Run both cron and your app
CMD ["./scripts/start.sh"]
