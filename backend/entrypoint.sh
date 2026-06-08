#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.environ.get('DATABASE_URL', ''))
    conn.close()
except Exception:
    exit(1)
"; do
  sleep 2
done
echo "PostgreSQL is ready."

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
mkdir -p ${STATIC_ROOT:-/var/lib/monitocam/staticfiles}
python manage.py collectstatic --noinput

echo "Starting application..."
exec "$@"
