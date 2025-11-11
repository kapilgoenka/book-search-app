#!/bin/bash
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Importing books data..."
python manage.py import_books books.csv

echo "Release command completed successfully!"
