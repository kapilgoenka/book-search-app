# ADR: Book Search Application Architecture

**Status:** Living document — updated commit by commit  
**Last updated:** 12307bf — Fix database migration and persistence for Fly.io

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

**Chosen:** UV (replacing Poetry)

UV is used instead of Poetry because it is significantly faster at dependency resolution and installation, is a single binary with no system-level install requirements, and supports the standard `pyproject.toml` format natively. In Docker, UV is copied from its official image (`ghcr.io/astral-sh/uv:latest`) via a `COPY --from` layer, keeping the build simple.

Dependencies are declared in `pyproject.toml`; the lockfile is `uv.lock`.

---

## Decision 8: Containerization and Production Server

**Chosen:** Docker + Gunicorn, deployed to Fly.io

**Docker:** The app is containerized using a `python:3.12-slim` base image. UV installs dependencies system-wide (`uv pip install --system`). Static files are collected at build time (`collectstatic`). The image is built remotely on Fly.io's infrastructure (`flyctl deploy --remote-only`).

**Gunicorn:** Django's development server is replaced with Gunicorn for production (`gunicorn --bind :8000 --workers 2 config.wsgi`). Two workers are configured, sized for the 1GB / 1 shared-CPU Fly.io VM.

**Fly.io:** Chosen as the deployment platform. Key configuration (`fly.toml`):
- App name: `book-search-app-wild-silence-8674`
- Primary region: `sjc` (San Jose)
- Auto-stop when idle, auto-start on request, minimum 0 machines running (scales to zero)
- 1GB RAM, 1 shared CPU
- Static files served by Fly.io's edge directly from `/code/static`

**CI/CD:** GitHub Actions workflow (`.github/workflows/fly-deploy.yml`) triggers `flyctl deploy --remote-only` on every push to `main`, using a `FLY_API_TOKEN` secret.

**Static files:** `STATIC_ROOT = BASE_DIR / 'staticfiles'` and `MEDIA_ROOT = BASE_DIR / 'media'` configured in `settings.py`. Collected into the image at build time.

**`ALLOWED_HOSTS`:** Set to `['localhost', '127.0.0.1', 'book-search-app-wild-silence-8674.fly.dev', '.fly.dev']`. The `.fly.dev` wildcard covers all Fly.io preview URLs. `DEBUG` remains `True` in production (acceptable for a non-sensitive read-only catalog; a future hardening step would set this via an env var).

---

## Decision 9: Database Persistence on Fly.io (Evolution)

SQLite is a file on disk. Fly.io machines use ephemeral filesystems that are wiped on each deployment. This forced an explicit decision about where the database lives in production. The solution evolved through three phases.

### Phase 1 — Persistent Volume (12307bf, 849361c, a13b8b1) ❌ Did not work

**Approach:** Mount a Fly.io persistent volume at `/data` and store the database there.

`fly.toml`:
```toml
[[mounts]]
  source = 'data'
  destination = '/data'
```

`settings.py`: Database path switched at runtime using `os.path.exists('/data')`:
```python
if os.path.exists('/data'):
    DB_PATH = Path('/data/db.sqlite3')
else:
    DB_PATH = BASE_DIR / 'db.sqlite3'
```

A `release_command` was added to run migrations and import data on each deploy:
```toml
[deploy]
  release_command = 'sh release.sh'
```

`release.sh` runs `manage.py migrate --noinput` then `manage.py import_books books.csv` sequentially with `set -e`.

**Problem encountered:** Fly.io does **not** mount volumes during the `release_command` phase — the volume is only available to the running app process. So `release.sh` created the database at `/code/db.sqlite3`, but the running app looked for it at `/data/db.sqlite3` (which was empty).

A secondary bug: `fly.toml` used `[mounts]` (single table) instead of `[[mounts]]` (array of tables), which caused the mount to be silently ignored. Fixed in a13b8b1.
