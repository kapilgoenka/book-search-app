# Deployment Guide for Fly.io

## Prerequisites

- Fly.io CLI installed (`brew install flyctl` or see https://fly.io/docs/getting-started/installing-flyctl/)
- Fly.io account (sign up at https://fly.io)

## Initial Setup

### 1. Create a Fly.io Volume for Persistent Data

Since we're using SQLite, we need a persistent volume to store the database:

```bash
fly volumes create data --size 1 --region sjc --app book-search-app-wild-silence-8674
```

### 2. Deploy the Application

```bash
fly deploy
```

The deployment will:
- Build the Docker image using UV
- Run database migrations
- Import the book data from books.csv
- Start the application with gunicorn

## Post-Deployment

### Verify the Deployment

Visit: https://book-search-app-wild-silence-8674.fly.dev/

### Run Migrations Manually (if needed)

```bash
fly ssh console -C "python manage.py migrate"
```

### Import Books Manually (if needed)

```bash
fly ssh console -C "python manage.py import_books books.csv"
```

### Create Superuser (for admin access)

```bash
fly ssh console
python manage.py createsuperuser
```

### View Logs

```bash
fly logs
```

### SSH into the App

```bash
fly ssh console
```

## Configuration

### Environment Variables

The app uses the following configuration:
- `PORT=8000` (set in fly.toml)
- Database stored in `/data/db.sqlite3` (persistent volume)

### Scaling

To adjust resources:

```bash
# Scale memory
fly scale memory 512

# Scale VM count
fly scale count 1
```

## Troubleshooting

### Database Not Found

If you see "no such table" errors:
1. Ensure the volume is created and mounted
2. SSH into the app and run migrations manually
3. Import the book data

### Out of Memory

If the import process runs out of memory:
1. Scale up memory temporarily: `fly scale memory 2048`
2. Run the import
3. Scale back down: `fly scale memory 1024`

### Static Files Not Loading

Collect static files:
```bash
fly ssh console -C "python manage.py collectstatic --noinput"
```

## Update Deployment

After making code changes:

```bash
git add .
git commit -m "Your changes"
git push
fly deploy
```

## Monitoring

- View metrics: `fly dashboard`
- Monitor logs: `fly logs -a book-search-app-wild-silence-8674`
- Check status: `fly status`

## Cost Optimization

The current configuration:
- 1GB RAM
- Shared CPU
- Auto-stop when idle
- Auto-start on request
- Minimum 0 machines running (scales to zero)

This configuration should stay within Fly.io's free tier for low-traffic apps.
