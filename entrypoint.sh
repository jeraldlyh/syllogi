#!/usr/bin/env bash

set -e

export PATH="/app/.venv/bin:$PATH"

echo "Running database migrations..."
cd /app/backend
alembic upgrade head

export LOG_LEVEL=${LOG_LEVEL:-"info"}

echo "Starting backend..."
cd /app/backend
uvicorn app:app --host 0.0.0.0 --port 8000 --log-level "$LOG_LEVEL" &
BACKEND_PID=$!

term_handler() {
  echo "Signal received, terminating processes..."
  kill "$BACKEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" 2>/dev/null || true
  exit 0
}

trap term_handler SIGINT SIGTERM

wait "$BACKEND_PID"

STATUS=$?
echo "Backend process exited with status $STATUS"
exit "$STATUS"
