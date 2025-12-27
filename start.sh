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
    
    # Start homepage frontend
    echo "🎨 Starting Homepage frontend on http://localhost:3000"
    cd apps/homepage/frontend
    npm install > /dev/null 2>&1
    npm run dev &
    HOMEPAGE_PID=$!
    cd ../../..
    
    # Wait for homepage to start
    sleep 2
    
    # Start Data Aggregator frontend
    echo "📊 Starting Data Aggregator frontend on http://localhost:5173"
    cd apps/data_aggregator/frontend
    npm install > /dev/null 2>&1
    npm run dev &
    DAT_PID=$!
    cd ../../..
    
    # Wait for DAT to start
    sleep 2
    
    # Start PPTX Generator frontend
    echo "📊 Starting PPTX Generator frontend on http://localhost:5175"
    cd apps/pptx_generator/frontend
    npm install > /dev/null 2>&1
    npm run dev &
    PPTX_PID=$!
    cd ../../..
    
    # Wait for PPTX to start
    sleep 2
    
    # Start SOV Analyzer frontend
    echo "📈 Starting SOV Analyzer frontend on http://localhost:5174"
    cd apps/sov_analyzer/frontend
    npm install > /dev/null 2>&1
    npm run dev &
    SOV_PID=$!
    cd ../../..
    
    echo ""
    echo "✅ All services started!"
    echo ""
    echo "📍 Frontend Applications:"
    echo "  Homepage:         http://localhost:3000"
    echo "  Data Aggregator:  http://localhost:5173"
    echo "  PPTX Generator:   http://localhost:5175"
    echo "  SOV Analyzer:     http://localhost:5174"
    echo ""
    echo "🔗 API Gateway & Documentation:"
    echo "  Gateway:         http://localhost:8000"
    echo "  Gateway Docs:    http://localhost:8000/docs"
    echo "  PPTX Generator:  http://localhost:8000/api/pptx/docs"
    echo "  Data Aggregator: http://localhost:8000/api/dat/docs"
    echo "  SOV Analyzer:    http://localhost:8000/api/sov/docs"
    echo ""
    echo "Press Ctrl+C to stop all services"
    echo ""
    
    # Wait for Ctrl+C
    trap "kill $GATEWAY_PID $HOMEPAGE_PID $DAT_PID $PPTX_PID $SOV_PID 2>/dev/null; exit" INT TERM
    wait
else
    # Start gateway only (foreground)
    echo "💡 Tip: Use --with-frontend or -f to also start all frontends"
    echo ""
    python -m gateway.main
fi
