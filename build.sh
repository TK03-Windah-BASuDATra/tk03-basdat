#!/bin/bash
# Build script for Render deployment

set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run init.sql to set up the schema and tables
# This needs to connect to the database
if [ ! -z "$DATABASE_URL" ]; then
    echo "Running init.sql from DATABASE_URL..."
    psql "$DATABASE_URL" -f init.sql
    
    # Set search_path to windah_basudatra for the default connection
    psql "$DATABASE_URL" -c "SET search_path = windah_basudatra;"
else
    echo "DATABASE_URL not set, skipping init.sql"
fi

# Run Django migrations (if there are any)
python manage.py migrate --run-syncdb 2>/dev/null || true

echo "Build complete!"
