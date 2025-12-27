# CI Step 4: Run Tests
# Executes unit and integration tests

param(
    [switch]$Coverage,
    [string]$TestPath = ""
)

$ErrorActionPreference = "Stop"

Write-Host "=== CI Step 4: Run Tests ===" -ForegroundColor Cyan

$rootDir = Join-Path $PSScriptRoot "../.."

# Activate virtual environment
$venvPath = Join-Path $rootDir ".venv"
$activateScript = Join-Path $venvPath "Scripts/Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
}

# Build pytest arguments
$pytestArgs = @("-v", "--tb=short")

if ($Coverage) {
    $pytestArgs += "--cov=shared"
    $pytestArgs += "--cov=gateway"
    $pytestArgs += "--cov=apps"
    $pytestArgs += "--cov-report=term-missing"
    $pytestArgs += "--cov-report=html:coverage_report"
}

# Determine test path
if ($TestPath) {
    $testDir = $TestPath
} else {
    $testDir = Join-Path $rootDir "tests"
}

# Run unit tests
Write-Host "Running unit tests..." -ForegroundColor Yellow
$unitTestDir = Join-Path $testDir "unit"
if (Test-Path $unitTestDir) {
    pytest $unitTestDir @pytestArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Unit tests failed"
        exit 1
    }
    Write-Host "Unit tests passed" -ForegroundColor Green
} else {
    Write-Host "No unit tests found at $unitTestDir" -ForegroundColor Yellow
}

# Run integration tests
Write-Host "Running integration tests..." -ForegroundColor Yellow
$integrationTestDir = Join-Path $testDir "integration"
if (Test-Path $integrationTestDir) {
    pytest $integrationTestDir @pytestArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Integration tests failed"
        exit 1
    }
    Write-Host "Integration tests passed" -ForegroundColor Green
} else {
    Write-Host "No integration tests found at $integrationTestDir" -ForegroundColor Yellow
}

Write-Host "=== Tests Complete ===" -ForegroundColor Cyan
