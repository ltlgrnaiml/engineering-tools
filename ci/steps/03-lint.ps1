# CI Step 3: Linting
# Runs code quality checks

$ErrorActionPreference = "Stop"

Write-Host "=== CI Step 3: Linting ===" -ForegroundColor Cyan

$rootDir = Join-Path $PSScriptRoot "../.."

# Activate virtual environment
$venvPath = Join-Path $rootDir ".venv"
$activateScript = Join-Path $venvPath "Scripts/Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
}

# Install linting tools if not present
Write-Host "Ensuring linting tools are installed..." -ForegroundColor Yellow
pip install ruff mypy --quiet

# Run Ruff (fast Python linter)
Write-Host "Running Ruff linter..." -ForegroundColor Yellow
$ruffResult = ruff check $rootDir/shared $rootDir/gateway $rootDir/apps --ignore E501
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Ruff found issues (non-blocking)"
}

# Run MyPy type checking on shared contracts
Write-Host "Running MyPy type checker on shared contracts..." -ForegroundColor Yellow
$mypyResult = mypy $rootDir/shared/contracts --ignore-missing-imports --no-error-summary 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warning "MyPy found type issues (non-blocking)"
}

# Lint frontend
$homepageFrontend = Join-Path $rootDir "apps/homepage/frontend"
if (Test-Path $homepageFrontend) {
    Write-Host "Linting Homepage frontend..." -ForegroundColor Yellow
    Push-Location $homepageFrontend
    if (Test-Path "node_modules/.bin/eslint") {
        npm run lint 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "ESLint found issues (non-blocking)"
        }
    } else {
        Write-Host "ESLint not configured, skipping frontend lint" -ForegroundColor Yellow
    }
    Pop-Location
}

# === Contract Validation (ADR-0009, ADR-0034) ===

# Generate JSON Schemas from Pydantic contracts
Write-Host "Generating JSON Schemas from contracts..." -ForegroundColor Yellow
$genSchemaResult = python $rootDir/tools/gen_json_schema.py --validate 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warning "JSON Schema generation failed"
    Write-Host $genSchemaResult
}

# Check for contract drift
Write-Host "Checking for contract drift..." -ForegroundColor Yellow
$driftResult = python $rootDir/tools/check_contract_drift.py --fail-on-breaking 2>&1
if ($LASTEXITCODE -eq 2) {
    Write-Error "BREAKING contract changes detected! Per ADR-0016, bump version."
    exit 1
} elseif ($LASTEXITCODE -eq 1) {
    Write-Warning "Non-breaking contract drift detected"
}

Write-Host "=== Linting Complete ===" -ForegroundColor Cyan
