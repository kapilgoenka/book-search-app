#!/bin/bash
set -e

echo "Waiting for database..."
until python -c "
import psycopg2, os, sys
try:
    psycopg2.connect(os.environ.get('DATABASE_URL', ''))
    sys.exit(0)
except Exception as e:
    print(f'  not ready: {e}')
    sys.exit(1)
" 2>&1; do
    sleep 2
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Checking if books need to be imported..."
BOOK_COUNT=$(python manage.py shell --no-startup -c "from books.models import Book; print(Book.objects.count())" 2>/dev/null | tail -1)
if [ "$BOOK_COUNT" = "0" ]; then
    echo "Importing books (this may take a moment)..."
    python manage.py import_books books.csv
else
    echo "Books already loaded ($BOOK_COUNT), skipping import."
fi

exec "$@"
