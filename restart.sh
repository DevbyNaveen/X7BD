#!/bin/bash

# Restart Analytics Dashboard Service

SERVICE_NAME="analytics-dashboard-service"
SERVICE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔄 Restarting $SERVICE_NAME..."

# Kill existing processes
pkill -f "uvicorn.*app.main:app" || true
sleep 2

# Start the service
"$SERVICE_DIR/start.sh" "$@"
