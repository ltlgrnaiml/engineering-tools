# Start script for engineering-tools monorepo (Windows PowerShell)

Write-Host "Starting Engineering Tools Platform" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path ".venv")) {
    Write-Host "[ERROR] Virtual environment not found. Please run .\setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Activate virtual environment
& .\.venv\Scripts\Activate.ps1

# Check if we should start frontend
$StartFrontend = $false
if ($args -contains "--with-frontend" -or $args -contains "-f") {
    $StartFrontend = $true
}

# Start Gateway
Write-Host "Starting API Gateway on http://localhost:8000" -ForegroundColor Yellow
Write-Host ""

if ($StartFrontend) {
    # Start gateway in background
    $gatewayJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        & .\.venv\Scripts\Activate.ps1
        & ".\.venv\Scripts\python.exe" -m gateway.main
    }
    
    # Wait for gateway to start
    Write-Host "Waiting for gateway to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    # Start frontend
    Write-Host "Starting Homepage frontend on http://localhost:3000" -ForegroundColor Yellow
    Write-Host ""
    Push-Location apps/homepage/frontend
    npm.cmd install
    $frontendJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        npm.cmd run dev
    }
    Pop-Location
    
    Write-Host ""
    Write-Host "Services started!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Gateway:  http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Homepage: http://localhost:3000" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "API Documentation:" -ForegroundColor Cyan
    Write-Host "  Gateway:         http://localhost:8000/api/docs" -ForegroundColor White
    Write-Host "  PPTX Generator:  http://localhost:8000/api/pptx/docs" -ForegroundColor White
    Write-Host "  Data Aggregator: http://localhost:8000/api/dat/docs" -ForegroundColor White
    Write-Host "  SOV Analyzer:    http://localhost:8000/api/sov/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
    Write-Host ""
    
    # Wait for Ctrl+C
    try {
        while ($true) {
            Start-Sleep -Seconds 1
            
            # Check if jobs are still running
            if ($gatewayJob.State -ne "Running" -or $frontendJob.State -ne "Running") {
                if ($gatewayJob.State -ne "Running") { Write-Host "Gateway stopped unexpectedly" -ForegroundColor Red }
                if ($frontendJob.State -ne "Running") { Write-Host "Frontend stopped unexpectedly" -ForegroundColor Red }
                Receive-Job -Job $gatewayJob
                Receive-Job -Job $frontendJob
                break
            }
        }
    } finally {
        Write-Host "Stopping services..." -ForegroundColor Yellow
        Write-Host "Gateway job output:" -ForegroundColor Yellow
        Receive-Job -Job $gatewayJob | Out-Host
        Write-Host "Frontend job output:" -ForegroundColor Yellow
        Receive-Job -Job $frontendJob | Out-Host
        Stop-Job -Job $gatewayJob, $frontendJob
        Remove-Job -Job $gatewayJob, $frontendJob
    }
} else {
    # Start gateway only (foreground)
    Write-Host "Tip: Use --with-frontend or -f to also start the frontend" -ForegroundColor Cyan
    Write-Host ""
    python -m gateway.main
}
