#!/usr/bin/env bash
# =============================================================================
# Engineering Tools Platform - Development Environment Startup Script
# =============================================================================
# 
# Starts all services required for the Engineering Tools Platform development
# environment. Compatible with bash and zsh on macOS, Linux, and WSL.
#
# ARCHITECTURE REFERENCES:
#   ADR-0037: Single-Command Development Environment
#   ADR-0042: Frontend Iframe Integration Pattern  
#   ADR-0029: Simplified API Endpoint Naming (/api/{tool}/{resource})
#   SPEC-0045: Frontend Iframe Integration Implementation
#   docs/platform/ARCHITECTURE.md: Full platform architecture
#
# WHY ALL FRONTENDS BY DEFAULT?
#   The Homepage frontend embeds tool UIs via iframes (see ADR-0042). When you
#   navigate to /tools/dat, /tools/sov, or /tools/pptx in the Homepage, it loads
#   the standalone tool frontend in an iframe. This requires all frontends running.
#
# PORT ASSIGNMENTS (per SPEC-0045):
#   Backend Gateway:  8000  (API: /api/{tool}/{resource} per ADR-0029)
#   MkDocs:           8001
#   Homepage:         3000  (entry point, embeds tools via iframes)
#   DAT Frontend:     5173  (embedded at /tools/dat)
#   SOV Frontend:     5174  (embedded at /tools/sov)
#   PPTX Frontend:    5175  (embedded at /tools/pptx)
#
# API ENDPOINTS (per ADR-0029):
#   Platform:  /docs, /redoc, /openapi.json, /health
#   DAT:       /api/dat/docs, /api/dat/*
#   SOV:       /api/sov/docs, /api/sov/*
#   PPTX:      /api/pptx/docs, /api/pptx/*
#   DataSets:  /api/datasets/*
#   Pipelines: /api/pipelines/*
#
# USAGE:
#   ./start.sh                     # Start everything (default)
#   ./start.sh --backend-only      # Start only the backend API
#   ./start.sh --docs              # Start only mkdocs documentation server
#   ./start.sh --tool dat          # Backend + DAT frontend (isolated dev)
#   ./start.sh --tool sov          # Backend + SOV frontend (isolated dev)
#   ./start.sh --tool pptx         # Backend + PPTX frontend (isolated dev)
#   ./start.sh --help              # Show this help
#
# =============================================================================

set -e

# =============================================================================
# Port Configuration (per ADR-0042 / SPEC-0045)
# =============================================================================
# These port assignments are defined in SPEC-0045 and must remain consistent
# across all tool vite.config.ts files and this script.
#
# Architecture: Homepage embeds tool frontends via iframes (ADR-0042)
#   Homepage (3000) -> iframe src="localhost:5173" for DAT
#   Homepage (3000) -> iframe src="localhost:5174" for SOV
#   Homepage (3000) -> iframe src="localhost:5175" for PPTX
#
# API Routes (per ADR-0029): /api/{tool}/{resource}
#   Gateway mounts tool apps: /api/dat/*, /api/sov/*, /api/pptx/*
# =============================================================================

BACKEND_PORT=${BACKEND_PORT:-8000}   # API Gateway - hosts /api/{tool}/* routes
HOMEPAGE_PORT=3000                    # Main SPA - embeds tools via iframes
DAT_PORT=5173                         # Data Aggregator standalone frontend
SOV_PORT=5174                         # SOV Analyzer standalone frontend
PPTX_PORT=5175                        # PPTX Generator standalone frontend
MKDOCS_PORT=8001                      # Documentation server

BACKEND_ONLY=false
DOCS_MODE=false
SKIP_SETUP=false
TOOL=""

# =============================================================================
# Argument Parsing
# =============================================================================

show_help() {
    cat << EOF
Engineering Tools Platform - Development Environment

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --backend-only      Start only the backend API gateway
    --docs              Start only the MkDocs documentation server
    --skip-setup        Skip environment readiness checks
    --backend-port N    Override backend port (default: 8000)
    --tool NAME         Start backend + specific tool frontend only
                        Valid: dat, sov, pptx
    -h, --help          Show this help message

EXAMPLES:
    $0                  # Start everything (backend, all frontends, mkdocs)
    $0 --tool dat       # Start backend + DAT frontend (isolated development)
    $0 --backend-only   # Start only the backend API

PORT ASSIGNMENTS (per SPEC-0045):
    Backend Gateway:  $BACKEND_PORT  (API endpoints per ADR-0029)
    MkDocs:           $MKDOCS_PORT
    Homepage:         $HOMEPAGE_PORT  (embeds tools via iframes per ADR-0042)
    DAT Frontend:     $DAT_PORT
    SOV Frontend:     $SOV_PORT
    PPTX Frontend:    $PPTX_PORT

ARCHITECTURE REFERENCES:
    ADR-0037: Single-Command Development Environment
    ADR-0042: Frontend Iframe Integration Pattern
    ADR-0029: Simplified API Endpoint Naming
    SPEC-0045: Frontend Iframe Integration Implementation
    docs/platform/ARCHITECTURE.md
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend-only) BACKEND_ONLY=true; shift ;;
        --docs) DOCS_MODE=true; shift ;;
        --skip-setup) SKIP_SETUP=true; shift ;;
        --backend-port) BACKEND_PORT="$2"; shift 2 ;;
        --tool)
            TOOL="$2"
            if [[ ! "$TOOL" =~ ^(dat|sov|pptx)$ ]]; then
                echo "❌ Invalid tool: $TOOL. Valid options: dat, sov, pptx"
                exit 1
            fi
            shift 2
            ;;
        -h|--help) show_help ;;
        *) echo "❌ Unknown option: $1. Use --help for usage."; exit 1 ;;
    esac
done

# =============================================================================
# Find Repository Root
# =============================================================================

find_repo_root() {
    # Start from script location if available, otherwise current dir
    local search_path="${BASH_SOURCE[0]:-$0}"
    search_path="$(cd "$(dirname "$search_path")" && pwd)"
    
    local current="$search_path"
    while [[ "$current" != "/" ]]; do
        if [[ -d "$current/.git" ]] && [[ -f "$current/pyproject.toml" ]]; then
            echo "$current"
            return 0
        fi
        current="$(dirname "$current")"
    done
    
    # Fallback: check current directory
    if [[ -f "$(pwd)/pyproject.toml" ]]; then
        pwd
        return 0
    fi
    
    return 1
}

REPO_ROOT=$(find_repo_root) || {
    echo "❌ Could not find repository root. Ensure you're within the engineering-tools repo."
    exit 1
}

echo "🚀 Engineering Tools Platform"
echo "=============================="
echo "📁 Repository: $REPO_ROOT"
echo ""

cd "$REPO_ROOT"

# =============================================================================
# Environment Checks & Setup
# =============================================================================

check_venv_ready() {
    [[ -d "$REPO_ROOT/.venv" ]] && [[ -f "$REPO_ROOT/.venv/bin/activate" ]]
}

check_frontend_ready() {
    [[ -d "$REPO_ROOT/apps/homepage/frontend/node_modules" ]]
}

run_setup() {
    echo "📦 Running initial setup..."
    if [[ -f "$REPO_ROOT/setup.sh" ]]; then
        bash "$REPO_ROOT/setup.sh"
    else
        echo "❌ setup.sh not found at $REPO_ROOT/setup.sh"
        exit 1
    fi
}

if [[ "$SKIP_SETUP" != "true" ]]; then
    needs_setup=false
    
    if ! check_venv_ready; then
        echo "⚠️  Python virtual environment not found"
        needs_setup=true
    else
        echo "✓ Python virtual environment ready"
    fi
    
    if ! check_frontend_ready; then
        echo "⚠️  Frontend dependencies not installed"
        needs_setup=true
    else
        echo "✓ Frontend dependencies ready"
    fi
    
    if [[ "$needs_setup" == "true" ]]; then
        echo ""
        run_setup
        echo ""
    fi
fi

# =============================================================================
# Activate Virtual Environment
# =============================================================================

if [[ -f "$REPO_ROOT/.venv/bin/activate" ]]; then
    source "$REPO_ROOT/.venv/bin/activate"
    echo "✓ Virtual environment activated"
else
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# =============================================================================
# Cleanup Handler
# =============================================================================

BACKEND_PID=""
MKDOCS_PID=""
HOMEPAGE_PID=""
DAT_PID=""
SOV_PID=""
PPTX_PID=""

cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    
    for pid_var in BACKEND_PID MKDOCS_PID HOMEPAGE_PID DAT_PID SOV_PID PPTX_PID; do
        pid=${!pid_var}
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            wait "$pid" 2>/dev/null || true
            echo "  ✓ ${pid_var%_PID} stopped"
        fi
    done
    
    echo "✓ All services stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# =============================================================================
# Start Services
# =============================================================================

# Start Backend (unless Docs-only mode)
if [[ "$DOCS_MODE" != "true" ]]; then
    echo ""
    echo "🔧 Starting Backend API on http://localhost:$BACKEND_PORT"
    
    python -m uvicorn gateway.main:app \
        --host 0.0.0.0 \
        --port "$BACKEND_PORT" \
        --reload \
        2>&1 | sed 's/^/[BE] /' &
    BACKEND_PID=$!
    
    echo "   PID: $BACKEND_PID"
fi

# Start MkDocs (by default, or if --docs specified alone)
if [[ -z "$TOOL" ]] || [[ "$DOCS_MODE" == "true" ]]; then
    echo ""
    echo "📚 Starting MkDocs on http://localhost:$MKDOCS_PORT"
    
    mkdocs serve --dev-addr "127.0.0.1:$MKDOCS_PORT" 2>&1 | sed 's/^/[DOCS] /' &
    MKDOCS_PID=$!
    
    echo "   PID: $MKDOCS_PID"
fi

# Start Frontend(s) - unless BackendOnly or Docs mode
if [[ "$BACKEND_ONLY" != "true" ]] && [[ "$DOCS_MODE" != "true" ]]; then
    
    if [[ "$TOOL" == "pptx" ]]; then
        echo ""
        echo "📑 Starting PPTX Frontend on http://localhost:$PPTX_PORT"
        cd "$REPO_ROOT/apps/pptx_generator/frontend"
        npm run dev -- --port "$PPTX_PORT" --host 2>&1 | sed 's/^/[PPTX] /' &
        PPTX_PID=$!
        echo "   PID: $PPTX_PID"
        cd "$REPO_ROOT"
        
    elif [[ "$TOOL" == "dat" ]]; then
        echo ""
        echo "📊 Starting DAT Frontend on http://localhost:$DAT_PORT"
        cd "$REPO_ROOT/apps/data_aggregator/frontend"
        npm run dev -- --port "$DAT_PORT" --host 2>&1 | sed 's/^/[DAT] /' &
        DAT_PID=$!
        echo "   PID: $DAT_PID"
        cd "$REPO_ROOT"
        
    elif [[ "$TOOL" == "sov" ]]; then
        echo ""
        echo "📈 Starting SOV Frontend on http://localhost:$SOV_PORT"
        cd "$REPO_ROOT/apps/sov_analyzer/frontend"
        npm run dev -- --port "$SOV_PORT" --host 2>&1 | sed 's/^/[SOV] /' &
        SOV_PID=$!
        echo "   PID: $SOV_PID"
        cd "$REPO_ROOT"
        
    else
        # Default: ALL frontends (Homepage embeds tools via iframes)
        echo ""
        echo "🏠 Starting Homepage Frontend on http://localhost:$HOMEPAGE_PORT"
        cd "$REPO_ROOT/apps/homepage/frontend"
        npm run dev -- --port "$HOMEPAGE_PORT" --host 2>&1 | sed 's/^/[HOME] /' &
        HOMEPAGE_PID=$!
        echo "   PID: $HOMEPAGE_PID"
        cd "$REPO_ROOT"
        
        echo ""
        echo "📊 Starting DAT Frontend on http://localhost:$DAT_PORT"
        cd "$REPO_ROOT/apps/data_aggregator/frontend"
        npm run dev -- --port "$DAT_PORT" --host 2>&1 | sed 's/^/[DAT] /' &
        DAT_PID=$!
        echo "   PID: $DAT_PID"
        cd "$REPO_ROOT"
        
        echo ""
        echo "📈 Starting SOV Frontend on http://localhost:$SOV_PORT"
        cd "$REPO_ROOT/apps/sov_analyzer/frontend"
        npm run dev -- --port "$SOV_PORT" --host 2>&1 | sed 's/^/[SOV] /' &
        SOV_PID=$!
        echo "   PID: $SOV_PID"
        cd "$REPO_ROOT"
        
        echo ""
        echo "📑 Starting PPTX Frontend on http://localhost:$PPTX_PORT"
        cd "$REPO_ROOT/apps/pptx_generator/frontend"
        npm run dev -- --port "$PPTX_PORT" --host 2>&1 | sed 's/^/[PPTX] /' &
        PPTX_PID=$!
        echo "   PID: $PPTX_PID"
        cd "$REPO_ROOT"
    fi
fi

# =============================================================================
# Wait for Services
# =============================================================================

echo ""
echo "========================================"
echo "✅ Services Started Successfully!"
echo "========================================"
echo ""

# Backend Links
if [[ "$DOCS_MODE" != "true" ]]; then
    echo "  BACKEND API"
    echo "  -----------"
    echo "  🔧 Gateway API:      http://localhost:$BACKEND_PORT"
    echo "     Health Check:     http://localhost:$BACKEND_PORT/health"
    echo ""
    echo "  SWAGGER / OPENAPI"
    echo "  -----------------"
    echo "  📖 Platform Docs:    http://localhost:$BACKEND_PORT/docs"
    echo "     Platform ReDoc:   http://localhost:$BACKEND_PORT/redoc"
    echo "  📑 PPTX Swagger:     http://localhost:$BACKEND_PORT/api/pptx/docs"
    echo "  📊 DAT Swagger:      http://localhost:$BACKEND_PORT/api/dat/docs"
    echo "  📈 SOV Swagger:      http://localhost:$BACKEND_PORT/api/sov/docs"
    echo ""
fi

# Documentation Links
if [[ -z "$TOOL" ]] || [[ "$DOCS_MODE" == "true" ]]; then
    echo "  DOCUMENTATION"
    echo "  -------------"
    echo "  📚 MkDocs:           http://localhost:$MKDOCS_PORT"
    echo ""
fi

# Frontend Links
if [[ "$BACKEND_ONLY" != "true" ]] && [[ "$DOCS_MODE" != "true" ]]; then
    echo "  FRONTENDS"
    echo "  ---------"
    if [[ "$TOOL" == "pptx" ]]; then
        echo "  📑 PPTX Tool:        http://localhost:$PPTX_PORT"
    elif [[ "$TOOL" == "dat" ]]; then
        echo "  📊 DAT Tool:         http://localhost:$DAT_PORT"
    elif [[ "$TOOL" == "sov" ]]; then
        echo "  📈 SOV Tool:         http://localhost:$SOV_PORT"
    else
        # Default: All frontends (Homepage uses iframes to embed tools)
        echo "  🏠 Homepage:         http://localhost:$HOMEPAGE_PORT"
        echo "     -> DAT:         http://localhost:$HOMEPAGE_PORT/tools/dat"
        echo "     -> SOV:         http://localhost:$HOMEPAGE_PORT/tools/sov"
        echo "     -> PPTX:        http://localhost:$HOMEPAGE_PORT/tools/pptx"
        echo "  (Standalone)"
        echo "     DAT:            http://localhost:$DAT_PORT"
        echo "     SOV:            http://localhost:$SOV_PORT"
        echo "     PPTX:           http://localhost:$PPTX_PORT"
    fi
    echo ""
fi

echo "Press Ctrl+C to stop all services..."
echo ""

# Wait for any process to exit
wait
