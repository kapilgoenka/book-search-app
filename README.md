# Book Search Web Application

A Django-based web application for searching and browsing books with advanced filtering capabilities.

## Features

- **Comprehensive Search**: Search books by title, authors, ISBN, publisher, and more
- **Advanced Filters**: Filter by rating, page count, publication date, language, and review counts
- **Beautiful UI**: Modern, responsive design with a two-pane layout
- **Book Covers**: Automatically fetches book cover images from Open Library API
- **Pagination**: Efficiently browse through large result sets
- **11,000+ Books**: Pre-loaded with a comprehensive book dataset

## Technology Stack

- **Backend**: Django 5.2.8
- **Package Manager**: UV
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript (vanilla)

## Installation & Setup

### Prerequisites

- Python 3.10+
- UV package manager

### Setup Instructions

1. The project is already set up in the current directory

2. The database is already migrated and populated with 11,127 books

3. Start the development server:
   ```bash
   uv run python manage.py runserver
   ```

4. Open your browser and navigate to:
   ```
   http://127.0.0.1:8000/
   ```

## Usage

### Search Filters

The application supports the following search criteria:

#### Basic Information
- **Title**: Substring search (case-insensitive)
- **Authors**: Substring search (case-insensitive)
- **Publisher**: Substring search (case-insensitive)

#### Identifiers
- **ISBN**: Exact match
- **ISBN13**: Exact match

#### Ratings & Reviews
- **Average Rating**: Range filter (min/max)
- **Ratings Count**: Range filter (min/max)
- **Text Reviews Count**: Range filter (min/max)

#### Publication Details
- **Language**: Dropdown selection
- **Publication Date**: Range filter (from/to dates)

#### Physical Details
- **Number of Pages**: Range filter (min/max)

### Search Tips

1. **Multiple Filters**: You can combine multiple filters - they work together with AND logic
2. **Range Filters**: For numeric fields, you can specify minimum, maximum, or both
3. **Empty Search**: Leave all filters empty to browse all books
4. **Reset**: Use the Reset button to clear all filters

## Project Structure

```
book_search_app/
├── books/                          # Main app directory
│   ├── management/
│   │   └── commands/
│   │       └── import_books.py    # CSV import command
│   ├── migrations/                # Database migrations
│   ├── templates/
│   │   └── books/
│   │       ├── base.html         # Base template with styles
│   │       └── search.html       # Main search page
│   ├── admin.py                  # Admin configuration
│   ├── models.py                 # Book model
│   ├── urls.py                   # URL routing
│   └── views.py                  # Search view logic
├── config/                        # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py                      # Django management script
├── books.csv                      # Book data source
└── db.sqlite3                     # SQLite database
```

## Management Commands

### Import Books from CSV

To re-import books from a CSV file:

```bash
uv run python manage.py import_books path/to/books.csv
```

This will:
- Clear existing book data
- Import new books from the CSV
- Handle data validation and type conversion
- Show progress during import

## Admin Interface

Access the Django admin at `http://127.0.0.1:8000/admin/` to manage books directly.

To create an admin user:
```bash
uv run python manage.py createsuperuser
```

## API Integration

The application uses the **Open Library Covers API** to fetch book cover images:
- Primary lookup: ISBN13
- Fallback: ISBN
- Default: SVG placeholder for books without covers

## Performance

- Database indexes on frequently queried fields
- Efficient pagination (25 books per page)
- Bulk insert for CSV imports (1000 records per batch)
- Query optimization with Django ORM

## Browser Support

- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest 2 versions)
- Edge (latest 2 versions)

## Responsive Design

The application is fully responsive:
- **Desktop**: Two-pane layout (search panel + results)
- **Tablet**: Adjusted two-pane layout
- **Mobile**: Stacked layout with collapsible search

## Future Enhancements

Potential features for future versions:
- User authentication and saved searches
- Book details page with more information
- Export search results (CSV, PDF)
- Advanced sorting options
- User reviews and ratings
- Wishlist/favorites functionality
- Social sharing features

## License

This project is created for educational and demonstration purposes.

## Data Source

Book data sourced from: https://github.com/MainakRepositor/Datasets/blob/master/books.csv
