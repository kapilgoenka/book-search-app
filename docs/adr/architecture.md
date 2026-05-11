# ADR: Book Search Application Architecture

**Status:** Living document — updated commit by commit  
**Last updated:** 5ef9747 — Change Python version to 3.12

---

## Context

A web application to search and explore a catalog of books. The primary goals are fast, multi-criteria search over a fixed dataset of ~11,000 books, and a clean browsable UI.

---

## Decision 1: Django as the Web Framework

**Chosen:** Django 5.2.8

Django was chosen over lighter alternatives (Flask, FastAPI) because it provides a full-featured ORM, admin interface, templating, pagination, and management commands out of the box. For a data-heavy search app with an admin need and no custom API requirements, Django's batteries-included approach reduces boilerplate significantly.

---

## Decision 2: SQLite as the Database

**Chosen:** SQLite (via Django's default backend)

The dataset is read-only — 11,127 books imported once from a CSV. SQLite is a single-file database that requires no server process, is trivially portable, and performs well for read-heavy workloads at this scale. A server-based database (PostgreSQL, MySQL) would add operational overhead without benefit for this use case.

**Data model (`Book`):**

| Field | Type | Notes |
|---|---|---|
| `bookID` | IntegerField | Indexed |
| `title` | CharField(500) | Indexed |
| `authors` | CharField(500) | Indexed |
| `average_rating` | DecimalField(3,2) | Indexed |
| `isbn` / `isbn13` | CharField(20) | Indexed |
| `language_code` | CharField(10) | Indexed |
| `num_pages` | IntegerField | Indexed |
| `ratings_count` | IntegerField | Indexed |
| `text_reviews_count` | IntegerField | Indexed |
| `publication_date` | DateField | Indexed |
| `publisher` | CharField(500) | Indexed |

Composite indexes: `(title, authors)` and `(average_rating, ratings_count)`.  
Default ordering: `[-average_rating, title]`.

---

## Decision 3: CSV → SQLite via Management Command

**Chosen:** A custom `import_books` Django management command

The dataset (`books.csv`, ~11,128 rows) is imported once via `python manage.py import_books books.csv`. This approach keeps the data loading separate from application startup and gives full control over parsing, validation, and error handling. The CSV ships with the codebase.

---

## Decision 4: Search Filter Design

**Chosen:** Django ORM queryset chaining with GET parameters

The search view (`books/views.py`) builds a queryset by progressively chaining `.filter()` calls based on the presence of GET parameters. Filters are applied only when their parameter is non-empty, so the base query returns all books when no filters are set.

11 filter types supported:

| Filter | Strategy |
|---|---|
| Title, Authors, Publisher | `__icontains` (substring, case-insensitive) |
| ISBN, ISBN13 | `__iexact` (exact match, case-insensitive) |
| Language | Exact match via dropdown |
| Average Rating, Pages, Ratings Count, Reviews Count | Range (`__gte` / `__lte`) |
| Publication Date | Range on `DateField` |

Pagination: 25 books per page using Django's `Paginator`.

---

## Decision 5: Book Cover Thumbnails via Open Library API

**Chosen:** Open Library Covers API (client-side, no server proxy)

Book cover images are fetched directly from the Open Library API using ISBN. This avoids storing binary image data locally and keeps the Docker image small. The fetch happens in the browser, so cover loading doesn't block server-side rendering.

---

## Decision 6: Python Version

**Chosen:** Python 3.12 (pinned via `.python-version`, `requires-python = ">=3.12"` in `pyproject.toml`)

The project was initially scaffolded targeting Python 3.14 (pre-release). It was immediately corrected to 3.12 — the most recent stable release with broad library support. Python 3.12 is pinned explicitly so that local environments and Docker images use the same interpreter version.

---

## Decision 7a: Documentation Strategy

**Chosen:** Markdown docs (`PRD.md`, `QUICK_START.md`, `README.md`) committed to the repo

Product requirements live in `PRD.md` (what the app should do and why). Developer onboarding lives in `QUICK_START.md` (how to run it locally). `README.md` covers usage. All docs are co-located with code so they stay in sync with the implementation.

---

## Decision 7: Package Manager

**Chosen:** UV

UV is used as the package manager (faster than pip/Poetry, native lockfile support). Dependencies are declared in `pyproject.toml`. The virtual environment is managed by UV locally via `.venv/`.
