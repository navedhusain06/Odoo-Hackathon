#!/bin/sh
set -e

# Apply migrations
alembic -c /app/alembic.ini upgrade head

# Seed demo users (ignore failures if already seeded)
python -m app.scripts.seed_users || true

# Start API
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
