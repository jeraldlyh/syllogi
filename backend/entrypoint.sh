#!/usr/bin/env bash

echo "Running database migrations..."
alembic upgrade head
exec "$@"
