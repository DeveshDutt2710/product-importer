#!/bin/bash
set -e

echo "Starting Celery worker..."
celery -A product_importer worker --loglevel=info &
CELERY_PID=$!

function cleanup {
    echo "Shutting down Celery worker (PID: $CELERY_PID)..."
    kill $CELERY_PID 2>/dev/null || true
    wait $CELERY_PID 2>/dev/null || true
    echo "Celery worker shut down."
}
trap cleanup SIGTERM SIGINT

echo "Starting Gunicorn..."
exec gunicorn product_importer.wsgi:application --bind 0.0.0.0:$PORT --timeout 120

