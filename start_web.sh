#!/bin/bash
set -e

exec gunicorn product_importer.wsgi:application --bind 0.0.0.0:$PORT

