# Book Search Application - Quick Start Guide

## What's Been Built

A complete Django-based book search web application with:
- 11,127 books imported from the dataset
- Advanced search with 11 different filter types
- Beautiful, responsive UI with two-pane layout
- Book cover thumbnails from Open Library API
- Pagination for efficient browsing

## Project Location

```
/Users/kapil/Desktop/book_search/book_search_app/
```

## Running the Application

The server is currently running at:
```
http://127.0.0.1:8000/
```

To start it again later:
```bash
cd book_search_app
uv run python manage.py runserver
```

## Key Features Implemented

### Search Filters
1. **Title** - substring search
2. **Authors** - substring search
3. **Average Rating** - min/max range
4. **ISBN** - exact match
5. **ISBN13** - exact match
6. **Language** - dropdown selection
7. **Number of Pages** - min/max range
8. **Ratings Count** - min/max range
9. **Text Reviews Count** - min/max range
10. **Publication Date** - date range
11. **Publisher** - substring search

### UI Layout
- **Header**: Application title with gradient background
- **Left Pane**: Search form with all filters organized by category
- **Right Pane**: Search results with book cards showing:
  - Cover thumbnail
  - Title and authors
  - Rating (star + number)
  - Publication info
  - Page count, language, ISBN

### Technical Implementation
- Django 5.2.8 with UV package management
- SQLite database with indexed fields for performance
- Responsive CSS (works on desktop, tablet, mobile)
- Pagination (25 books per page)
- Open Library API integration for book covers

## Project Files

### Key Files Created
- `books/models.py` - Book model with all fields
- `books/views.py` - Search view with filter logic
- `books/templates/books/search.html` - Main search interface
- `books/templates/books/base.html` - Base template with styling
- `books/management/commands/import_books.py` - CSV import command
- `books/admin.py` - Admin interface configuration

### Configuration
- `config/settings.py` - Updated with books app
- `config/urls.py` - URL routing configured
- `books/urls.py` - App-specific URLs

### Data
- `books.csv` - Source dataset (1.5MB)
- `db.sqlite3` - Database with 11,127 books

## Testing the Application

1. Open http://127.0.0.1:8000/ in your browser

2. Try these example searches:
   - Search for "Harry Potter" in title
   - Filter by average rating >= 4.0
   - Select "eng" language and 200-400 pages
   - Search by author "J.K. Rowling"

3. Test responsive design by resizing browser window

## Next Steps (Optional)

1. **Create admin user** to access Django admin:
   ```bash
   uv run python manage.py createsuperuser
   ```
   Then visit: http://127.0.0.1:8000/admin/

2. **Customize styling** - Edit `books/templates/books/base.html`

3. **Add more features** - See README.md for enhancement ideas

## Documentation

- Full documentation: `book_search_app/README.md`
- PRD: `/Users/kapil/Desktop/book_search/PRD.md`

## Success Criteria ✓

All requirements from the PRD have been implemented:
- ✓ Django with UV package management
- ✓ SQLite database
- ✓ CSV data imported
- ✓ All 11 search filters working
- ✓ Two-pane UI layout
- ✓ Book thumbnails from API
- ✓ Responsive design
- ✓ Pagination
- ✓ Clean, professional interface

Enjoy your book search application!
