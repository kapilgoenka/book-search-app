# ADR: Book Search Application Architecture

**Status:** Living document — updated commit by commit  
**Last updated:** PostgreSQL migration, Docker Compose local dev, book detail page

---

## Context

A web application to search and explore a catalog of books. The primary goals are fast, multi-criteria search over a fixed dataset of ~11,000 books, and a clean browsable UI.

---

## Decision 1: Django as the Web Framework

**Chosen:** Django 5.2.8

Django was chosen over lighter alternatives (Flask, FastAPI) because it provides a full-featured ORM, admin interface, templating, pagination, and management commands out of the box. For a data-heavy search app with an admin need and no custom API requirements, Django's batteries-included approach reduces boilerplate significantly.

---

## Decision 2: Database — SQLite → PostgreSQL

### Original choice: SQLite

The dataset is read-only — 11,127 books imported once from a CSV. SQLite was chosen because it requires no server process and is trivially portable. (See Decision 9 for the full evolution of how this played out on Fly.io.)

### Current choice: PostgreSQL 16

SQLite was replaced with PostgreSQL after the app was fully Dockerized. The trigger was containerization: once the app runs in Docker Compose, a managed Postgres container (`postgres:16-alpine`) is as operationally simple as SQLite, and it unlocks proper concurrent access, standard connection pooling, and compatibility with Fly.io's managed Postgres offering for production.

**Dependencies added:**
- `psycopg2-binary>=2.9` — Postgres adapter for Python
- `dj-database-url>=2.0` — parses a `DATABASE_URL` env var into Django's `DATABASES` dict

**Settings (`config/settings.py`):**
```python
import dj_database_url
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://postgres:postgres@localhost:5432/book_search',
        conn_max_age=600,
    )
}
```

`conn_max_age=600` enables persistent connections (Django connection pooling) — connections are reused for up to 10 minutes instead of being opened and closed per request.

`DATABASE_URL` is injected by Docker Compose at runtime (`postgresql://postgres:postgres@db:5432/book_search`), with the `db` hostname resolving to the Postgres container on the shared compose network.

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

## Decision 9: Database Persistence — Evolution

This decision evolved through four phases as the app moved from a simple local project to a fully containerized one.

### Phase 1 — Persistent Volume (12307bf, 849361c, a13b8b1) ❌ Did not work

**Approach:** Mount a Fly.io persistent volume at `/data` and store SQLite there.

**Problem:** Fly.io does **not** mount volumes during `release_command` — only during the running app. The `release_command` created the DB at `/code/db.sqlite3` but the app looked for it at `/data/db.sqlite3`. A secondary bug: `fly.toml` used `[mounts]` (single table) instead of `[[mounts]]` (array of tables), silently ignoring the mount.

### Phase 2 — Ephemeral Storage (b6d58b6) ❌ Works but fragile

**Approach:** Drop the volume. Store SQLite at `/code/db.sqlite3` in both dev and prod. Recreate on every deploy via `release_command`.

**Problem:** `release_command` runs in a separate container. Files written there are not guaranteed to carry into the running app container.

### Phase 3 — SQLite Baked into Docker Image (727820f) ✅ Worked for read-only

**Approach:** Bake migrations and import into `RUN` steps in `Dockerfile`. Every container starts with a pre-populated database.

```dockerfile
RUN python manage.py migrate --noinput && \
    python manage.py import_books books.csv
```

This worked well for a read-only catalog — simple, reliable, no runtime dependencies.

### Phase 4 — PostgreSQL via Docker Compose (current) ✅ Current approach

**Approach:** Replace SQLite entirely with a PostgreSQL 16 container. Data lives in a named Docker volume (`postgres_data`) that persists across container restarts but is managed outside the image.

The entrypoint script (see Decision 16) handles migrations and first-run book import at container startup. `fly.toml` uses `release_command = 'python manage.py migrate --noinput'` for the Fly.io deployment path.

**Why the switch from Phase 3:** Phase 3 (baked SQLite) broke the moment the app was containerized with Docker Compose — migrations can't run at build time because the Postgres server isn't available yet. PostgreSQL is the natural fit once you have a compose network.

**Data durability:**
- Local dev: data persists in the `postgres_data` named volume between `docker compose up/down` cycles
- Wiped only with `docker compose down -v` (explicit volume removal)
- Fly.io: `release_command` runs migrations on each deploy; data lives in Fly Postgres

---

## Decision 10: Health Check Endpoint for Deployment Observability

**Chosen:** `/health/` JSON endpoint (`books/views.py::health_check`)

To diagnose the volume-mount issues, a `/health/` endpoint was added that returns a JSON payload with:
- Database path and whether the file exists on disk
- `/data` directory existence and writability
- Django `DEBUG` flag and `ALLOWED_HOSTS`
- Live database connection test (`SELECT 1`)
- Book count query result

This endpoint is not protected by authentication. It is appropriate for a non-sensitive read-only catalog but would require auth or removal before exposing user data.

---

## Decision 11: UI Design System

### Phase 1 — Dark Theme (b616967, d4e2d12)

Inline `<style>` block in `base.html`, no CSS framework. Dark palette centered on `#1a1a1a` body / `#2d2d2d` panels. Max content width 1600px. Flexbox two-pane layout. System font stack (`-apple-system`, `Segoe UI`, etc.).

### Phase 2 — Full Redesign (current)

The dark theme was replaced wholesale with a light editorial design system. The redesign touches every visual layer.

**Why inline CSS was kept over a framework:** Same rationale as Phase 1 — a single-page app with no build step has no need for Tailwind or Bootstrap. The template remains self-contained.

**Design system — CSS custom properties defined in `:root`:**

| Variable | Value | Role |
|---|---|---|
| `--bg` | `#f6f4ef` | Page background (warm off-white) |
| `--paper` | `#ffffff` | Card/cover backgrounds |
| `--ink` | `#1a1a1a` | Primary text |
| `--ink-2` | `#44443f` | Secondary text |
| `--ink-3` | `#76746d` | Muted labels, metadata |
| `--ink-4` | `#a9a69d` | Placeholders, disabled state |
| `--rule` | `#e6e2d7` | Borders and dividers |
| `--rule-2` | `#efece4` | Lighter dividers (book row separators) |
| `--accent` | `oklch(0.55 0.10 55)` | Warm muted terracotta (stars, dot) |
| `--focus` | `oklch(0.55 0.10 55 / 0.25)` | Focus ring |

`oklch` was chosen for the accent color to give perceptually uniform lightness — it stays readable and accessible at the chosen chroma without needing manual dark/light adjustments.

**Typography — Google Fonts CDN (3 families):**

| Family | Use |
|---|---|
| Source Serif 4 (400/500/600, optical size 8–60) | Page headings, book titles, rating numbers |
| Inter (400/500/600) | Body text, labels, inputs |
| JetBrains Mono (400/500) | Metadata, counts, filter group titles, pagination |

Fonts are loaded via two `<link rel="preconnect">` hints + one stylesheet import in `base.html`. This is an external CDN dependency — the app requires internet access to render correctly. An alternative would be self-hosted fonts (avoids the CDN dependency but adds build complexity).

**Layout:**
- CSS grid (`grid-template-columns: 260px 1fr`, `gap: 48px`) in `.shell` replacing the old flexbox container. Max width 1280px (down from 1600px).
- Sidebar: `position: sticky; top: calc(57px + 24px)` — anchored below the sticky header with a gap. `max-height: calc(100vh - 57px - 48px); overflow-y: auto` so long filter lists scroll independently.
- Book rows: 3-column grid (`96px 1fr auto`) — cover thumbnail, metadata, rating panel.

**Book cover placeholder:** CSS hatched background using two layered `repeating-linear-gradient` patterns, replacing the old SVG inline fallback. Same Open Library ISBN cover API for real covers with `onerror` fallback to the placeholder.

**Number formatting:** `django.contrib.humanize` added to `INSTALLED_APPS`; `{% load humanize %}` + `|intcomma` used in the template for ratings counts and page totals (e.g. "32,213 ratings" instead of "32213").

---

## Decision 12: Default Landing Page — Top Rated Books

**Chosen:** Show top-rated books by default instead of an empty state

The original landing page showed a "Start Searching" placeholder when no filters were applied. This was replaced with a default query that surfaces the top-rated books immediately on load.

**Query:** `Book.objects.filter(ratings_count__gte=1000).order_by('-average_rating', 'title')`

- `ratings_count__gte=1000` — filters out books with very few ratings, which tend to have artificially inflated average scores (a book with one 5-star review ranks higher than a book with 50,000 ratings averaging 4.8). 1,000 was chosen as a threshold that surfaces well-known titles without being so high it excludes good niche books.
- `order_by('-average_rating', 'title')` — primary sort by rating descending, secondary by title for stable tie-breaking.

**Template change:** The `{% if filters_applied or request.GET %}` gate was removed. The results panel now always renders. When `showing_top_rated` is True, the header reads "Top Rated Books"; when filters are active, it shows the result count as before.

**Why not most popular (by ratings_count)?** Most popular would surface the most-read books, but those are already universally known (Harry Potter, Twilight, etc.). Top-rated with a meaningful count floor surfaces high-quality books that users may not have encountered.

---

## Decision 13: Global Quick-Search (`q` parameter)

**Chosen:** A header search bar that submits a single `q` parameter, searched across `title` OR `authors` using Django's `Q` objects.

```python
books = books.filter(Q(title__icontains=q) | Q(authors__icontains=q))
```

The header form is separate from the sidebar filter form. Submitting the header search clears all sidebar filter state (only `?q=value` is in the URL). Submitting the sidebar form clears `q`. This keeps the two search modes distinct and avoids complex state-merging logic.

`q` can be combined with sidebar filters if both are present in the URL (e.g. navigating back after using the header then adding a filter), since they are both handled in the same `if request.GET:` block.

---

## Decision 14: Result Sorting

**Chosen:** A `sort` GET parameter with 4 options, applied as a final `.order_by()` after all filtering.

| `sort` value | Order |
|---|---|
| `rating` (default) | `-average_rating, title` |
| `count` | `-ratings_count` |
| `date` | `-publication_date, title` |
| `title` | `title` |

Sorting is decoupled from the default top-rated query — both the filtered and default (top-rated) querysets pass through the same sort step. A `<select>` in the results header changes the URL via JavaScript (`url.searchParams.set('sort', value)`) without resetting the page, preserving all other GET parameters.

---

## Decision 15: Book Detail Page

**Chosen:** A dedicated route and template for individual book detail, using Django's `get_object_or_404`.

**URL pattern:** `book/<int:pk>/` → `books:detail`

**View:**
```python
def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'books/detail.html', {'book': book})
```

`get_object_or_404` is used rather than `Book.objects.get()` so that a missing PK returns an HTTP 404 (standard web behavior) rather than an unhandled 500.

**Navigation from the list:** Search result rows are made clickable with an inline `onclick` handler:
```html
onclick="window.location='{% url 'books:detail' book.pk %}'"
```

This avoids wrapping the entire `<article>` in an `<a>` tag, which would require restructuring the 3-column grid layout. The trade-off is that the link is not keyboard-navigable or right-click-copyable as a native anchor would be. A more accessible implementation would use `<a>` with CSS `display: contents` or a stretch pseudo-element.

**Detail page content:** Hero 2-column grid (large cover + metadata). Displays: cover (Open Library `-L` size, 200×292px), rating (48px serif number + star icons + count), facts grid (publication date, publisher, pages, language), identifiers (ISBN, ISBN-13, Book ID), and a back-navigation link (`javascript:history.back()`).

---

## Decision 16: Docker Compose Local Development + Entrypoint Startup Script

**Chosen:** Docker Compose with two services (web + db) and a shell entrypoint for runtime initialization.

**Compose architecture (`docker-compose.yml`):**

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: book_search
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/book_search
    depends_on:
      db:
        condition: service_healthy
```

`depends_on: condition: service_healthy` prevents the web container from starting until `pg_isready` succeeds inside the db container. This eliminates a whole class of race conditions at startup.

**Entrypoint script (`entrypoint.sh`):**

```bash
# Wait for the DB to accept connections (belt-and-suspenders beyond depends_on)
until python -c "import psycopg2, os, sys; psycopg2.connect(os.environ.get('DATABASE_URL', '')); sys.exit(0)" 2>&1; do
    sleep 2
done

python manage.py migrate --noinput

BOOK_COUNT=$(python manage.py shell --no-startup -c \
    "from books.models import Book; print(Book.objects.count())" 2>/dev/null | tail -1)
if [ "$BOOK_COUNT" = "0" ]; then
    python manage.py import_books books.csv
fi

exec "$@"
```

Key decisions within the entrypoint:

- **Double-check with psycopg2:** Despite `depends_on: service_healthy`, the Python connection check runs as an extra guard — `pg_isready` only verifies the port is open, not that Postgres is ready to accept application connections.
- **Conditional import:** Book import only runs when the table is empty. This prevents re-importing 11,127 books on every container restart. The named volume (`postgres_data`) persists data across restarts; only `docker compose down -v` triggers a fresh import.
- **Shell noise fix:** `python manage.py shell` without `--no-startup` emits Django startup messages that pollute stdout and corrupt the count comparison. `--no-startup 2>/dev/null | tail -1` isolates the last line of output (the count).
- **`exec "$@"`:** The entrypoint hands off to CMD (`gunicorn ...`) via exec, replacing the shell process so gunicorn receives signals (SIGTERM, etc.) directly from Docker.

**Dockerfile changes to support this:**
- `COPY pyproject.toml uv.lock /code/` — lockfile is now copied and used (`-r pyproject.toml`) to pin exact dependency versions rather than installing free-floating latest versions.
- `RUN ... && chmod +x /code/entrypoint.sh` — makes the script executable inside the image.
- `RUN python manage.py migrate && import_books` removed — initialization now happens at runtime, not build time, because Postgres isn't available during `docker build`.
- `ENTRYPOINT ["/code/entrypoint.sh"]` added; `CMD` remains as the gunicorn invocation.
