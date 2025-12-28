# CI Step 3a: Contract Validation
# Validates all Pydantic contracts, schemas, messages, and ADR/SPEC files
# Per ADR-0009, ADR-0015, ADR-0017

$ErrorActionPreference = "Stop"

Write-Host "=== CI Step 3a: Contract Validation ===" -ForegroundColor Cyan

$rootDir = Join-Path $PSScriptRoot "../.."

# Activate virtual environment
$venvPath = Join-Path $rootDir ".venv"
$activateScript = Join-Path $venvPath "Scripts/Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
}

# Run unified contract validation
Write-Host "Running contract validation..." -ForegroundColor Yellow
$validateScript = Join-Path $rootDir "tools/validate_contracts.py"

if (Test-Path $validateScript) {
    python $validateScript --output-schemas --report-file "$rootDir/validation-report.json"
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host "All contract validations passed" -ForegroundColor Green
    } elseif ($exitCode -eq 1) {
        Write-Warning "Contract validation completed with warnings"
    } else {
        Write-Error "Contract validation failed with errors"
        exit $exitCode
    }
} else {
    Write-Warning "Contract validation script not found: $validateScript"
}

# Check for contract drift (if schemas exist)
$schemasDir = Join-Path $rootDir "schemas"
if (Test-Path $schemasDir) {
    Write-Host "Checking for contract drift..." -ForegroundColor Yellow
    $driftScript = Join-Path $rootDir "tools/check_contract_drift.py"
    
    if (Test-Path $driftScript) {
        python $driftScript --schemas-dir $schemasDir
        if ($LASTEXITCODE -eq 2) {
            Write-Warning "Breaking contract changes detected - review before merging"
        }
    }
}

Write-Host "=== Contract Validation Complete ===" -ForegroundColor Cyan
