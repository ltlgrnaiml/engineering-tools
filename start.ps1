# Start script for engineering-tools monorepo (Windows PowerShell)

Write-Host "🚀 Starting Engineering Tools Platform" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found. Please run .\setup.ps1 first." -ForegroundColor Red
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
Write-Host "🌐 Starting API Gateway on http://localhost:8000" -ForegroundColor Yellow
Write-Host ""

if ($StartFrontend) {
    # Start gateway in background
    $gatewayJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        & .\.venv\Scripts\Activate.ps1
        python -m gateway.main
    }
    
    # Wait for gateway to start
    Write-Host "⏳ Waiting for gateway to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    
    # Start frontend
    Write-Host "🎨 Starting Homepage frontend on http://localhost:3000" -ForegroundColor Yellow
    Write-Host ""
    Push-Location apps/homepage/frontend
    $frontendJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        npm run dev
    }
    Pop-Location
    
    Write-Host ""
    Write-Host "✅ Services started!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Gateway:  http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📍 Homepage: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "📍 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Press Ctrl+C to stop all services" -ForegroundColor Yellow
    Write-Host ""
    
    # Wait for Ctrl+C
    try {
        while ($true) {
            Start-Sleep -Seconds 1
            
            # Check if jobs are still running
            if ($gatewayJob.State -ne "Running" -or $frontendJob.State -ne "Running") {
                Write-Host "⚠️  A service has stopped unexpectedly" -ForegroundColor Yellow
                break
            }
        }
    } finally {
        Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
        Stop-Job -Job $gatewayJob, $frontendJob
        Remove-Job -Job $gatewayJob, $frontendJob
    }
} else {
    # Start gateway only (foreground)
    Write-Host "💡 Tip: Use --with-frontend or -f to also start the frontend" -ForegroundColor Cyan
    Write-Host ""
    python -m gateway.main
}
