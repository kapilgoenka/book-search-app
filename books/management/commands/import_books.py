import csv
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from books.models import Book


class Command(BaseCommand):
    help = 'Import books from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file containing book data'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']

        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Starting import from {csv_file}...'))

        # Clear existing data
        Book.objects.all().delete()
        self.stdout.write('Cleared existing book data')

        imported_count = 0
        error_count = 0

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            books_to_create = []

            for row in reader:
                try:
                    # Parse publication date
                    publication_date = None
                    if row.get('publication_date'):
                        try:
                            # Try different date formats
                            for date_format in ['%m/%d/%Y', '%Y-%m-%d', '%d/%m/%Y', '%Y']:
                                try:
                                    publication_date = datetime.strptime(row['publication_date'], date_format).date()
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            pass

                    # Parse numeric fields
                    average_rating = None
                    if row.get('average_rating'):
                        try:
                            average_rating = float(row['average_rating'])
                        except ValueError:
                            pass

                    num_pages = None
                    if row.get('num_pages'):
                        try:
                            num_pages = int(float(row['num_pages']))
                        except ValueError:
                            pass

                    ratings_count = 0
                    if row.get('ratings_count'):
                        try:
                            ratings_count = int(float(row['ratings_count']))
                        except ValueError:
                            pass

                    text_reviews_count = 0
                    if row.get('text_reviews_count'):
                        try:
                            text_reviews_count = int(float(row['text_reviews_count']))
                        except ValueError:
                            pass

                    bookID = 0
                    if row.get('bookID'):
                        try:
                            bookID = int(float(row['bookID']))
                        except ValueError:
                            pass

                    book = Book(
                        bookID=bookID,
                        title=row.get('title', '')[:500],
                        authors=row.get('authors', '')[:500],
                        average_rating=average_rating,
                        isbn=row.get('isbn', '')[:20] if row.get('isbn') else None,
                        isbn13=row.get('isbn13', '')[:20] if row.get('isbn13') else None,
                        language_code=row.get('language_code', 'en')[:10],
                        num_pages=num_pages,
                        ratings_count=ratings_count,
                        text_reviews_count=text_reviews_count,
                        publication_date=publication_date,
                        publisher=row.get('publisher', '')[:500] if row.get('publisher') else None,
                    )

                    books_to_create.append(book)
                    imported_count += 1

                    # Bulk create in batches
                    if len(books_to_create) >= 1000:
                        Book.objects.bulk_create(books_to_create)
                        self.stdout.write(f'Imported {imported_count} books...')
                        books_to_create = []

                except Exception as e:
                    error_count += 1
                    if error_count <= 10:  # Only show first 10 errors
                        self.stdout.write(self.style.WARNING(f'Error importing row: {str(e)}'))

            # Create remaining books
            if books_to_create:
                Book.objects.bulk_create(books_to_create)

        self.stdout.write(self.style.SUCCESS(
            f'Successfully imported {imported_count} books with {error_count} errors'
        ))
