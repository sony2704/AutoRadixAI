#!/bin/sh
# Start Celery worker in background, then start FastAPI
# Both share the same container on Render free tier

celery -A app.workers.celery_app worker \
  -Q inference,processing,reporting \
  -c 1 \
  --loglevel=info &

exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers 1
