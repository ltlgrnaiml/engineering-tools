# CI Step 1: Environment Setup
# Per ADR-0012: Windows-first development environment

param(
    [string]$PythonVersion = "3.11",
    [string]$NodeVersion = "20"
)

$ErrorActionPreference = "Stop"

Write-Host "=== CI Step 1: Environment Setup ===" -ForegroundColor Cyan

# Check Python version
Write-Host "Checking Python installation..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Error "Python not found. Please install Python $PythonVersion or later."
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Check Node.js version
Write-Host "Checking Node.js installation..." -ForegroundColor Yellow
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCmd) {
    Write-Error "Node.js not found. Please install Node.js $NodeVersion or later."
    exit 1
}

$nodeVersion = node --version 2>&1
Write-Host "Found: Node.js $nodeVersion" -ForegroundColor Green

# Create virtual environment if not exists
$venvPath = Join-Path $PSScriptRoot "../../.venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "Virtual environment created at $venvPath" -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
$activateScript = Join-Path $venvPath "Scripts/Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
    Write-Host "Virtual environment activated" -ForegroundColor Green
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host "=== Environment Setup Complete ===" -ForegroundColor Cyan
