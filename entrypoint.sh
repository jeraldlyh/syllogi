#!/usr/bin/env bash
set -e

echo "Running database migrations..."
cd /app/backend
alembic upgrade head

echo "Starting web..."
cd /app/web
PORT=3000 HOSTNAME=0.0.0.0 node server.js &
WEB_PID=$!

echo "Starting backend..."
cd /app/backend
exec uvicorn app:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

term_handler() {
  echo "Signal received, terminating dev processes..."
  kill "$WEB_PID" "$BACKEND_PID" 2>/dev/null || true
  wait "$WEB_PID" "$BACKEND_PID" 2>/dev/null || true
  exit 0
}

trap term_handler SIGINT SIGTERM

set +e
wait -n "$WEB_PID" "$BACKEND_PID"

STATUS=$?
echo "A dev process exited with status $STATUS, stopping remaining dev processes..."

kill "$WEB_PID" "$BACKEND_PID" 2>/dev/null || true
wait "$WEB_PID" "$BACKEND_PID" 2>/dev/null || true
exit "$STATUS"
