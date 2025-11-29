#!/bin/bash
set -e

PORT=${PORT:-8000}

python3 -m http.server $PORT &
HTTP_SERVER_PID=$!

celery -A product_importer worker --loglevel=info &
CELERY_PID=$!

function cleanup {
    kill $HTTP_SERVER_PID 2>/dev/null || true
    kill $CELERY_PID 2>/dev/null || true
}
trap cleanup EXIT

wait $CELERY_PID
