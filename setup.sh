#!/bin/bash
# Setup script for engineering-tools monorepo (macOS/Linux)

set -e

echo "🚀 Engineering Tools Monorepo Setup"
echo "===================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "📚 Installing Python dependencies..."
if [ -f "pyproject.toml" ]; then
    pip install -e ".[all]" --quiet
    echo "✓ Installed from pyproject.toml"
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    echo "✓ Installed from requirements.txt"
else
    echo "⚠️  No pyproject.toml or requirements.txt found"
fi

# Install frontend dependencies for all apps
FRONTEND_APPS=(
    "apps/homepage/frontend:Homepage"
    "apps/data_aggregator/frontend:Data Aggregator"
    "apps/pptx_generator/frontend:PPTX Generator"
    "apps/sov_analyzer/frontend:SOV Analyzer"
)

if command -v npm &> /dev/null; then
    echo "🎨 Installing frontend dependencies..."
    for app_entry in "${FRONTEND_APPS[@]}"; do
        app_path="${app_entry%%:*}"
        app_name="${app_entry##*:}"
        if [ -d "$app_path" ]; then
            echo "  Installing $app_name dependencies..."
            cd "$app_path"
            npm install --silent 2>/dev/null
            cd - > /dev/null
        fi
    done
    echo "✓ All frontend dependencies installed"
else
    echo "⚠️  npm not found, skipping frontend setup"
fi

# Create workspace directories
echo "📁 Creating workspace directories..."
mkdir -p workspace/tools/{dat,pptx,sov}
mkdir -p workspace/datasets
mkdir -p workspace/pipelines
echo "✓ Workspace directories created"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the application:"
echo "  ./start.sh"
echo ""
echo "Or manually:"
echo "  source .venv/bin/activate"
echo "  python -m gateway.main"
echo ""
