ARG PYTHON_VERSION=3.12-slim

FROM python:${PYTHON_VERSION}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code

# Copy dependency files for better layer caching
COPY pyproject.toml uv.lock /code/

# Install dependencies from lockfile so versions are pinned
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY . /code

# Create necessary directories and make entrypoint executable
RUN mkdir -p /code/staticfiles /code/media && chmod +x /code/entrypoint.sh

# Collect static files
RUN python manage.py collectstatic --noinput --clear || true

EXPOSE 8000

ENTRYPOINT ["/code/entrypoint.sh"]
CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "config.wsgi"]
