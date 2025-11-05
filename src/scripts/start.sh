#!/bin/bash
# Start cron in the background
cron

# Start FastAPI server
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000
