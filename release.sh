#!/bin/bash
set -e

echo "=== Release Script Started ==="
echo "Current directory: $(pwd)"
echo "Checking /data directory..."
ls -la /data || echo "/data directory not found or not accessible"

echo ""
echo "Running database migrations..."
python manage.py migrate --noinput

echo ""
echo "Importing books data..."
python manage.py import_books books.csv

echo ""
echo "=== Release command completed successfully! ==="
