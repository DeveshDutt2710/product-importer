#!/bin/bash
set -e

celery -A product_importer worker --loglevel=info &
CELERY_PID=$!

function cleanup {
    kill $CELERY_PID 2>/dev/null || true
}
trap cleanup EXIT

exec gunicorn product_importer.wsgi:application --bind 0.0.0.0:$PORT

