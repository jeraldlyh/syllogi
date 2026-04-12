#!/usr/bin/env bash

export PATH="/app/.venv/bin:$PATH"

echo "Running database migrations..."
alembic upgrade head
exec "$@"
