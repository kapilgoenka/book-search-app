ARG PYTHON_VERSION=3.12-slim

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

# Copy dependency files for better layer caching
COPY pyproject.toml /code/

# Install dependencies using uv (gunicorn is now in pyproject.toml)
RUN uv pip install --system --no-cache django gunicorn

# Copy application code
COPY . /code

# Create necessary directories
RUN mkdir -p /code/staticfiles /code/media

# Collect static files
RUN python manage.py collectstatic --noinput --clear || true

# Run migrations and import data into the image
RUN python manage.py migrate --noinput && \
    python manage.py import_books books.csv

EXPOSE 8000

# Use gunicorn for production
CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "config.wsgi"]
