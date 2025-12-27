# Setup script for engineering-tools monorepo (Windows PowerShell)

Write-Host "Engineering Tools Monorepo Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Found $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "[ERROR] Python 3 is not installed. Please install Python 3.9+ first." -ForegroundColor Red
    exit 1
}

# Create virtual environment
if (-Not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
if (Test-Path "pyproject.toml") {
    pip install -e ".[all]" --quiet
    Write-Host "[OK] Installed from pyproject.toml" -ForegroundColor Green
} elseif (Test-Path "requirements.txt") {
    pip install -r requirements.txt --quiet
    Write-Host "[OK] Installed from requirements.txt" -ForegroundColor Green
} else {
    Write-Host "Warning: No pyproject.toml or requirements.txt found" -ForegroundColor Yellow
}

# Install frontend dependencies
if (Test-Path "apps/homepage/frontend") {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location apps/homepage/frontend
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        npm install --silent
        Write-Host "[OK] Frontend dependencies installed" -ForegroundColor Green
    } else {
        Write-Host "Warning: npm not found, skipping frontend setup" -ForegroundColor Yellow
    }
    Pop-Location
}

# Create workspace directories
Write-Host "Creating workspace directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "workspace/tools/dat" | Out-Null
New-Item -ItemType Directory -Force -Path "workspace/tools/pptx" | Out-Null
New-Item -ItemType Directory -Force -Path "workspace/tools/sov" | Out-Null
New-Item -ItemType Directory -Force -Path "workspace/datasets" | Out-Null
New-Item -ItemType Directory -Force -Path "workspace/pipelines" | Out-Null
Write-Host "[OK] Workspace directories created" -ForegroundColor Green

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the application:" -ForegroundColor Cyan
Write-Host "  .\start.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Or manually:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  python -m gateway.main" -ForegroundColor White
Write-Host ""
