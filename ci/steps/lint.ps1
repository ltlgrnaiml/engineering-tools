# CI Step: Lint
# Runs Python linting with ruff

param(
    [string]$WorkspaceRoot = (Get-Location).Path
)

Write-Host "=== Running Linting ===" -ForegroundColor Cyan

Set-Location $WorkspaceRoot

# Check if ruff is available
if (-not (Get-Command ruff -ErrorAction SilentlyContinue)) {
    Write-Host "Installing ruff..." -ForegroundColor Yellow
    pip install ruff
}

# Run ruff check
Write-Host "Running ruff check..." -ForegroundColor Yellow
ruff check shared/ gateway/ apps/ --output-format=github

if ($LASTEXITCODE -ne 0) {
    Write-Host "Linting failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Linting passed!" -ForegroundColor Green
exit 0
