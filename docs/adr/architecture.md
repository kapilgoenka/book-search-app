# ADR: Book Search Application Architecture

**Status:** Living document — updated commit by commit  
**Last updated:** Full UI redesign — light design system, global search, sort

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

### Phase 2 — Ephemeral Storage (b6d58b6) ❌ Works but fragile

**Approach:** Accept that the volume cannot be used during `release_command`. Instead, store the database at `/code/db.sqlite3` in both dev and prod. The `release_command` creates it there, and the app reads it from the same location.

This meant the volume mount was removed entirely and the runtime path check (`os.path.exists('/data')`) was deleted. The database is recreated fresh on every deployment via `release_command`.

**Trade-off acknowledged in the commit message:** "For a production app with user-generated data, you'd want to use PostgreSQL. For this read-only book catalog, ephemeral storage is fine."

**Remaining problem:** `release_command` runs in a separate container from the main app. Files written during `release_command` are not guaranteed to persist into the app container's filesystem. This makes the database unreliable between the release phase and app startup.

### Phase 3 — Database Baked into Docker Image (727820f) ✅ Current approach

**Approach:** Run migrations and data import as `RUN` steps inside the `Dockerfile`, making the pre-populated SQLite database part of the immutable image layer.

```dockerfile
RUN python manage.py migrate --noinput && \
    python manage.py import_books books.csv
```

The `release_command` is removed from `fly.toml` entirely. Every deployed container starts with a fully populated database already on disk at `/code/db.sqlite3`.

**Why this works for this app:** The book catalog is read-only and static. There are no user writes, no per-instance state, and no need for the database to survive beyond a deployment. Baking the database into the image is actually the most reliable strategy for a read-only dataset.

**Trade-offs:**
- ✅ Eliminates all volume-mount and release-command complexity
- ✅ Every machine gets an identical, immediately-ready database
- ✅ Rollbacks are safe — the old image has the old database
- ❌ Docker image is larger (~6MB for the SQLite file)
- ❌ Updating the dataset requires a full image rebuild and redeploy
- ❌ Would not work if any writes to the database were needed

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
