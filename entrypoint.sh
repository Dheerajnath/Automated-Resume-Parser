#!/bin/sh
set -e

echo "=== Starting Resume Parser ==="

# Initialize migrations only if not already initialized
if [ ! -f "/app/migrations/alembic.ini" ]; then
    echo ">>> Initializing Flask-Migrate..."
    flask db init
fi

echo ">>> Running flask db migrate..."
flask db migrate -m "auto" 2>&1 || echo "Migrate skipped (no changes or already done)"

echo ">>> Running flask db upgrade..."
# Try normal upgrade first; if we get a stale revision error, stamp head and retry
if ! flask db upgrade 2>&1; then
    echo ">>> Upgrade failed (possibly stale revision). Stamping head and retrying..."
    flask db stamp head 2>&1 || true
    flask db upgrade 2>&1
fi

echo ">>> Starting Flask server..."
exec python run.py
