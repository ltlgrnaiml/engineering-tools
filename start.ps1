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
    
    # Start homepage frontend
    Write-Host "Starting Homepage frontend on http://localhost:3000" -ForegroundColor Yellow
    Push-Location apps/homepage/frontend
    npm.cmd install 2>&1 | Out-Null
    $homepageJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        npm.cmd run dev
    }
    Pop-Location
    
    # Wait for homepage to start
    Start-Sleep -Seconds 2
    
    # Start Data Aggregator frontend
    Write-Host "Starting Data Aggregator frontend on http://localhost:5173" -ForegroundColor Yellow
    Push-Location apps/data_aggregator/frontend
    npm.cmd install 2>&1 | Out-Null
    $datJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        npm.cmd run dev
    }
    Pop-Location
    
    # Wait for DAT to start
    Start-Sleep -Seconds 2
    
    # Start PPTX Generator frontend
    Write-Host "Starting PPTX Generator frontend on http://localhost:5175" -ForegroundColor Yellow
    Push-Location apps/pptx_generator/frontend
    npm.cmd install 2>&1 | Out-Null
    $pptxJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        npm.cmd run dev
    }
    Pop-Location
    
    # Wait for PPTX to start
    Start-Sleep -Seconds 2
    
    # Start SOV Analyzer frontend
    Write-Host "Starting SOV Analyzer frontend on http://localhost:5174" -ForegroundColor Yellow
    Push-Location apps/sov_analyzer/frontend
    npm.cmd install 2>&1 | Out-Null
    $sovJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        npm.cmd run dev
    }
    Pop-Location
    
    Write-Host ""
    Write-Host "[SUCCESS] All services started!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Frontend Applications:" -ForegroundColor Cyan
    Write-Host "  Homepage:         http://localhost:3000" -ForegroundColor White
    Write-Host "  Data Aggregator:  http://localhost:5173" -ForegroundColor White
    Write-Host "  PPTX Generator:   http://localhost:5175" -ForegroundColor White
    Write-Host "  SOV Analyzer:     http://localhost:5174" -ForegroundColor White
    Write-Host ""
    Write-Host "API Gateway & Documentation:" -ForegroundColor Cyan
    Write-Host "  Gateway:         http://localhost:8000" -ForegroundColor White
    Write-Host "  Gateway Docs:    http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  PPTX Generator:  http://localhost:8000/api/pptx/docs" -ForegroundColor White
    Write-Host "  Data Aggregator: http://localhost:8000/api/dat/docs" -ForegroundColor White
    Write-Host "  SOV Analyzer:    http://localhost:8000/api/sov/docs" -ForegroundColor White
    Write-Host ""
    Write-Host "Developer Tools:" -ForegroundColor Cyan
    Write-Host "  Enable DevTools: http://localhost:3000?devmode=true" -ForegroundColor White
    Write-Host "  (Or use the debug panel button in bottom-right corner)" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
    Write-Host ""
    
    # Wait for Ctrl+C
    try {
        while ($true) {
            Start-Sleep -Seconds 1
            
            # Check if jobs are still running
            $jobs = @($gatewayJob, $homepageJob, $datJob, $pptxJob, $sovJob)
            $allRunning = $true
            foreach ($job in $jobs) {
                if ($job.State -ne "Running") {
                    $allRunning = $false
                    break
                }
            }
            
            if (-not $allRunning) {
                Write-Host "One or more services stopped unexpectedly" -ForegroundColor Red
                break
            }
        }
    } finally {
        Write-Host "Stopping services..." -ForegroundColor Yellow
        Stop-Job -Job $gatewayJob, $homepageJob, $datJob, $pptxJob, $sovJob -ErrorAction SilentlyContinue
        Remove-Job -Job $gatewayJob, $homepageJob, $datJob, $pptxJob, $sovJob -ErrorAction SilentlyContinue
        Write-Host "All services stopped." -ForegroundColor Green
    }
} else {
    # Start gateway only (foreground)
    Write-Host "Tip: Use --with-frontend or -f to also start all frontends" -ForegroundColor Cyan
    Write-Host ""
    python -m gateway.main
}
