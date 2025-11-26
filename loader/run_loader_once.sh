#!/bin/sh

MARKER_FILE="/var/lib/postgresql/data/.311_data_loaded"

echo "Waiting for Postgres..."
./wait-for-it.sh postgres:5432 --timeout=60 --strict -- echo "Postgres is up."

if [ -f "$MARKER_FILE" ]; then
    echo "Data already loaded. Skipping load."
    exit 0
fi

echo "Starting data load..."
python load_311_data.py

if [ $? -eq 0 ]; then
    echo "Data load completed successfully."
    touch "$MARKER_FILE"
else
    echo "Data load failed."
    exit 1
fi
