#!/bin/bash
set -e

echo "=== Release Script Started ==="
echo "Running database migrations..."
python manage.py migrate --noinput

echo ""
echo "Importing books data (this may take a minute)..."
python manage.py import_books books.csv

echo "=== Release command completed successfully! ==="
