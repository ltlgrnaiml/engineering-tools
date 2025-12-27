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

# Install root Python dependencies
Write-Host "Installing root Python dependencies..." -ForegroundColor Yellow
$requirementsPath = Join-Path $rootDir "requirements.txt"
if (Test-Path $requirementsPath) {
    pip install -r $requirementsPath
    Write-Host "Root dependencies installed" -ForegroundColor Green
}

# Install shared package in editable mode
Write-Host "Installing shared package..." -ForegroundColor Yellow
pip install -e "$rootDir/shared"

# Install gateway
Write-Host "Installing gateway package..." -ForegroundColor Yellow
pip install -e "$rootDir/gateway"

# Install app packages
$apps = @("data_aggregator", "pptx_generator", "sov_analyzer")
foreach ($app in $apps) {
    $appPath = Join-Path $rootDir "apps/$app"
    if (Test-Path $appPath) {
        Write-Host "Installing $app..." -ForegroundColor Yellow
        pip install -e $appPath
    }
}

# Install test dependencies
Write-Host "Installing test dependencies..." -ForegroundColor Yellow
pip install pytest pytest-asyncio pytest-cov httpx

# Install Homepage frontend dependencies
$homepageFrontend = Join-Path $rootDir "apps/homepage/frontend"
if (Test-Path $homepageFrontend) {
    Write-Host "Installing Homepage frontend dependencies..." -ForegroundColor Yellow
    Push-Location $homepageFrontend
    npm ci
    Pop-Location
    Write-Host "Homepage frontend dependencies installed" -ForegroundColor Green
}

Write-Host "=== Dependencies Installation Complete ===" -ForegroundColor Cyan
