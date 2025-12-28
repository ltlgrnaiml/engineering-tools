# CI Step 2: Install Dependencies
# Installs Python and Node.js dependencies for all components

$ErrorActionPreference = "Stop"

Write-Host "=== CI Step 2: Install Dependencies ===" -ForegroundColor Cyan

$rootDir = Join-Path $PSScriptRoot "../.."

# Activate virtual environment
$venvPath = Join-Path $rootDir ".venv"
$activateScript = Join-Path $venvPath "Scripts/Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
}

# Install root package in editable mode (includes shared, gateway, apps via setuptools.packages.find)
Write-Host "Installing root package in editable mode..." -ForegroundColor Yellow
pip install -e "$rootDir[all]"
Write-Host "Root package installed" -ForegroundColor Green

# Install test dependencies
Write-Host "Installing test dependencies..." -ForegroundColor Yellow
pip install pytest pytest-asyncio pytest-cov httpx

# Install Homepage frontend dependencies
$homepageFrontend = Join-Path $rootDir "apps/homepage/frontend"
if (Test-Path $homepageFrontend) {
    Write-Host "Installing Homepage frontend dependencies..." -ForegroundColor Yellow
    Push-Location $homepageFrontend
    try {
        # Use npm install instead of npm ci for better compatibility on Windows
        # npm ci can fail with EPERM errors when node_modules exists with locked files
        npm install --prefer-offline
        Write-Host "Homepage frontend dependencies installed" -ForegroundColor Green
    } catch {
        Write-Warning "npm install failed (may need to close IDE/processes using node_modules): $_"
        Write-Warning "Continuing CI - frontend deps may need manual installation"
    }
    Pop-Location
}

Write-Host "=== Dependencies Installation Complete ===" -ForegroundColor Cyan
