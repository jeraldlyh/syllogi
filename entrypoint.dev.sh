#!/usr/bin/env bash
set -e

echo "Running database migrations..."
cd /app/backend
alembic upgrade head

echo "Starting web (dev)..."
cd /app/web
pnpm dev &

export WATCHFILES_FORCE_POLLING=false

echo "Starting backend (dev)..."
cd /app/backend
exec uvicorn app:app --host 0.0.0.0 --port 8000 --reload
