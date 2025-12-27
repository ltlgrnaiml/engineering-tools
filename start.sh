#!/bin/bash
# Start script for engineering-tools monorepo (macOS/Linux)

set -e

echo "🚀 Starting Engineering Tools Platform"
echo "======================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if we should start frontend
START_FRONTEND=false
if [ "$1" == "--with-frontend" ] || [ "$1" == "-f" ]; then
    START_FRONTEND=true
fi

# Start Gateway
echo "🌐 Starting API Gateway on http://localhost:8000"
echo ""

if [ "$START_FRONTEND" = true ]; then
    # Start gateway in background
    python -m gateway.main &
    GATEWAY_PID=$!
    
    # Wait for gateway to start
    echo "⏳ Waiting for gateway to start..."
    sleep 3
    
    # Start frontend
    echo "🎨 Starting Homepage frontend on http://localhost:3000"
    echo ""
    cd apps/homepage/frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ../../..
    
    echo ""
    echo "✅ Services started!"
    echo ""
    echo "📍 Gateway:  http://localhost:8000"
    echo "📍 Homepage: http://localhost:3000"
    echo "📍 API Docs: http://localhost:8000/docs"
    echo ""
    echo "Press Ctrl+C to stop all services"
    echo ""
    
    # Wait for Ctrl+C
    trap "kill $GATEWAY_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
    wait
else
    # Start gateway only (foreground)
    echo "💡 Tip: Use --with-frontend or -f to also start the frontend"
    echo ""
    python -m gateway.main
fi
