#!/usr/bin/env bash

set -e

export PATH="/app/.venv/bin:$PATH"

echo "Running database migrations..."
cd /app/backend
alembic upgrade head

echo "Starting web (dev)..."
cd /app/web
pnpm dev &
WEB_PID=$!

export WATCHFILES_FORCE_POLLING=false
export LOG_LEVEL=info

echo "Starting backend (dev)..."
cd /app/backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload --log-level "$LOG_LEVEL" &
BACKEND_PID=$!

echo "Starting nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!

term_handler() {
  echo "Signal received, terminating dev processes..."
  kill "$WEB_PID" "$BACKEND_PID" "$NGINX_PID" 2>/dev/null || true
  wait "$WEB_PID" "$BACKEND_PID" "$NGINX_PID" 2>/dev/null || true
  exit 0
}

trap term_handler SIGINT SIGTERM

set +e
wait -n "$WEB_PID" "$BACKEND_PID" "$NGINX_PID"

STATUS=$?
echo "A dev process exited with status $STATUS, stopping remaining dev processes..."

kill "$WEB_PID" "$BACKEND_PID" "$NGINX_PID" 2>/dev/null || true
wait "$WEB_PID" "$BACKEND_PID" "$NGINX_PID" 2>/dev/null || true
exit "$STATUS"
