#!/bin/bash

# X-sevenAI Analytics Dashboard Service Startup Script
# Handles uvloop compatibility issues with uvicorn reload

SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="analytics-dashboard-service"

echo "🚀 Starting $SERVICE_NAME..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run setup first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Install/upgrade dependencies if needed
echo "📦 Ensuring dependencies are up to date..."
pip install --quiet --upgrade uvicorn==0.32.0

# Set environment variables
export PYTHONPATH="$SERVICE_DIR:$PYTHONPATH"
export SERVICE_NAME="$SERVICE_NAME"

# Detect if we're in development mode (has --reload flag)
if [[ "$*" == *"--reload"* ]]; then
    echo "🔄 Starting in development mode with auto-reload..."
    echo "⚠️  Note: Reload mode uses asyncio instead of uvloop for compatibility"
    python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8060 \
        --reload \
        --log-level info \
        --loop asyncio
else
    echo "🏭 Starting in production mode with uvloop..."
    python -m uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8060 \
        --log-level info
fi

echo "✅ $SERVICE_NAME started successfully!"
