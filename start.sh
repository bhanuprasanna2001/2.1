#!/bin/bash
# Startup script for cloud deployment
# Runs migrations then starts the server

set -e

echo "🔄 Running database migrations..."
alembic upgrade head

echo "🚀 Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
