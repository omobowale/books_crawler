FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY ./src ./src
COPY ./src/scripts ./scripts
COPY ./daily_cron /etc/cron.d/daily_cron

# Make reports directory
RUN mkdir -p reports

# --- Install cron before using it ---
RUN apt-get update && apt-get install -y cron

# Give execution rights to cron file
RUN chmod 0644 /etc/cron.d/daily_cron
RUN crontab /etc/cron.d/daily_cron

# Install cron
RUN apt-get update && apt-get install -y cron

# Expose API port
EXPOSE 8000

# Start both cron and uvicorn using a simple script
COPY ./src/scripts/start.sh ./scripts/start.sh
RUN chmod +x ./scripts/start.sh

CMD ["./scripts/start.sh"]
