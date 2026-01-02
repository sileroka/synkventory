#!/bin/bash
# =============================================================================
# Synkventory Backend Entrypoint Script
# =============================================================================
# This script runs database migrations before starting the application.
# It's designed to work in both development and production environments.
# =============================================================================

set -e

echo "========================================"
echo "Synkventory Backend Starting..."
echo "========================================"

# Wait for the database to be ready
echo "Waiting for database to be ready..."
while ! pg_isready -h "${POSTGRES_SERVER:-db}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-postgres}" -q; do
    echo "Database is not ready. Waiting..."
    sleep 2
done
echo "Database is ready!"

# Run database migrations
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "Running database migrations..."
    # Use admin database URL for migrations if provided (for RLS setup)
    # Otherwise fall back to regular DATABASE_URL
    if [ -n "${DATABASE_URL_ADMIN}" ]; then
        echo "Using admin credentials for migrations..."
        DATABASE_URL="${DATABASE_URL_ADMIN}" alembic upgrade head
    else
        alembic upgrade head
    fi
    echo "Migrations complete!"
else
    echo "Skipping migrations (RUN_MIGRATIONS=${RUN_MIGRATIONS})"
fi

# Run database seeds
if [ "${RUN_SEEDS:-true}" = "true" ]; then
    echo "Running database seeds..."
    # Use admin database URL for seeds if provided
    if [ -n "${DATABASE_URL_ADMIN}" ]; then
        echo "Using admin credentials for seeds..."
        DATABASE_URL="${DATABASE_URL_ADMIN}" python -c "
from app.db.session import SessionLocal
from app.db.seed import run_seeds
db = SessionLocal()
try:
    run_seeds(db)
finally:
    db.close()
"
    else
        python -c "
from app.db.session import SessionLocal
from app.db.seed import run_seeds
db = SessionLocal()
try:
    run_seeds(db)
finally:
    db.close()
"
    fi
    echo "Seeds complete!"
else
    echo "Skipping seeds (RUN_SEEDS=${RUN_SEEDS})"
fi

echo "========================================"
echo "Starting application..."
echo "========================================"

# Execute the main command (passed as arguments)
exec "$@"
