# CI Step 5: Build
# Builds frontend assets and validates packages

$ErrorActionPreference = "Stop"

Write-Host "=== CI Step 5: Build ===" -ForegroundColor Cyan

$rootDir = Join-Path $PSScriptRoot "../.."

# Build Homepage frontend
$homepageFrontend = Join-Path $rootDir "apps/homepage/frontend"
if (Test-Path $homepageFrontend) {
    Write-Host "Building Homepage frontend..." -ForegroundColor Yellow
    Push-Location $homepageFrontend
    npm run build
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Homepage frontend build failed"
        exit 1
    }
    Pop-Location
    Write-Host "Homepage frontend built successfully" -ForegroundColor Green
}

# Validate Python packages can be imported
Write-Host "Validating Python package imports..." -ForegroundColor Yellow

# Activate virtual environment
$venvPath = Join-Path $rootDir ".venv"
$activateScript = Join-Path $venvPath "Scripts/Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
}

$imports = @(
    "from shared.contracts.core.dataset import DataSetManifest",
    "from shared.contracts.core.pipeline import Pipeline",
    "from shared.storage.artifact_store import ArtifactStore",
    "from shared.storage.registry_db import RegistryDB"
)

foreach ($import in $imports) {
    python -c $import 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to import: $import"
        exit 1
    }
}
Write-Host "All Python imports validated" -ForegroundColor Green

Write-Host "=== Build Complete ===" -ForegroundColor Cyan
