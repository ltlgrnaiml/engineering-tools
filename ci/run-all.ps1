# CI Runner: Execute all CI steps
# Usage: ./ci/run-all.ps1 [-SkipLint] [-Coverage]

param(
    [switch]$SkipLint,
    [switch]$Coverage
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Engineering Tools CI Pipeline" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$stepsDir = Join-Path $PSScriptRoot "steps"

# Step 1: Setup
& "$stepsDir/01-setup.ps1"
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""

# Step 2: Install Dependencies
& "$stepsDir/02-install-deps.ps1"
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""

# Step 3: Lint (optional)
if (-not $SkipLint) {
    & "$stepsDir/03-lint.ps1"
    # Lint failures are warnings, not errors
}

Write-Host ""

# Step 3a: Contract Validation
$contractValidation = Join-Path $stepsDir "03a-validate-contracts.ps1"
if (Test-Path $contractValidation) {
    & $contractValidation
    if ($LASTEXITCODE -eq 2) {
        Write-Warning "Contract validation failed - continuing with warnings"
    }
}

Write-Host ""

# Step 4: Test
$testArgs = @()
if ($Coverage) {
    $testArgs += "-Coverage"
}
& "$stepsDir/04-test.ps1" @testArgs
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""

# Step 5: Build
& "$stepsDir/05-build.ps1"
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  CI Pipeline Completed Successfully" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
