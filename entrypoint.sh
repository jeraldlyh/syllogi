#!/usr/bin/env bash
set -e

echo "Running database migrations..."
cd /app/backend
alembic upgrade head

echo "Starting web..."
cd /app/web
PORT=3000 HOSTNAME=0.0.0.0 node server.js &

echo "Starting backend..."
cd /app/backend
exec uvicorn app:app --host 0.0.0.0 --port 8000
