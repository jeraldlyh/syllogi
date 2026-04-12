#!/usr/bin/env bash
set -e

echo "Running database migrations..."
cd /app/backend
alembic upgrade head

echo "Starting web..."
cd /app/web
PORT=3000 HOSTNAME=0.0.0.0 node server.js &
WEB_PID=$!

export LOG_LEVEL=${LOG_LEVEL:-"info"}

echo "Starting backend..."
cd /app/backend
uvicorn app:app --host 0.0.0.0 --port 8000 --log-level "$LOG_LEVEL" &
BACKEND_PID=$!

echo "Starting nginx..."
nginx -g "daemon off;" &
NGINX_PID=$!

term_handler() {
  echo "Signal received, terminating processes..."
  kill "$WEB_PID" "$BACKEND_PID" "$NGINX_PID" 2>/dev/null || true
  wait "$WEB_PID" "$BACKEND_PID" "$NGINX_PID" 2>/dev/null || true
  exit 0
}

trap term_handler SIGINT SIGTERM

set +e
wait -n "$WEB_PID" "$BACKEND_PID" "$NGINX_PID"

STATUS=$?
echo "A process exited with status $STATUS, stopping remaining processes..."

kill "$WEB_PID" "$BACKEND_PID" "$NGINX_PID" 2>/dev/null || true
wait "$WEB_PID" "$BACKEND_PID" "$NGINX_PID" 2>/dev/null || true
exit "$STATUS"
