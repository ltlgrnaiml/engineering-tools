<#
.SYNOPSIS
    Engineering Tools Platform - Development Environment Startup Script

.DESCRIPTION
    Starts all services required for the Engineering Tools Platform development environment.
    Uses Honcho (Python Procfile manager) for proper process tree management.
    
    This script implements ADR-0037 (Single-Command Development Environment) and follows
    the iframe integration pattern defined in ADR-0042 / SPEC-0045.

    ARCHITECTURE REFERENCES:
    - ADR-0037: Single-Command Development Environment
    - ADR-0042: Frontend Iframe Integration Pattern
    - ADR-0029: Simplified API Endpoint Naming (/api/{tool}/{resource})
    - SPEC-0045: Frontend Iframe Integration Implementation

    WHY HONCHO?
    PowerShell Start-Job creates orphan processes that survive Ctrl+C. Honcho uses
    proper process groups so all children terminate when the parent is killed.

.PARAMETER BackendOnly
    Start only the backend API gateway (no frontends, no docs)

.PARAMETER Docs
    Start only the MkDocs documentation server

.PARAMETER SkipSetup
    Skip environment readiness checks

.PARAMETER Tool
    Start backend + specific tool frontend only (for isolated development)
    Valid values: dat, sov, pptx

.PARAMETER Clean
    Kill any stale processes on dev ports before starting

.EXAMPLE
    .\start.ps1
    # Starts everything: backend (8000), mkdocs (8001), homepage (3000), all tool frontends

.EXAMPLE
    .\start.ps1 -Tool dat
    # Starts backend + DAT frontend only (for isolated DAT development)

.EXAMPLE
    .\start.ps1 -BackendOnly
    # Starts only the backend API gateway

.EXAMPLE
    .\start.ps1 -Clean
    # Cleans stale processes then starts everything

.NOTES
    Port Assignments (per SPEC-0045):
      Backend Gateway:  8000  (API: /api/{tool}/{resource} per ADR-0029)
      MkDocs:           8001
      Homepage:         3000  (entry point, embeds tools via iframes)
      DAT Frontend:     5173  (embedded at /tools/dat)
      SOV Frontend:     5174  (embedded at /tools/sov)
      PPTX Frontend:    5175  (embedded at /tools/pptx)
#>

param(
    [switch]$BackendOnly,
    [switch]$Docs,
    [switch]$SkipSetup,
    [switch]$Clean,
    [ValidateSet("", "dat", "sov", "pptx")]
    [string]$Tool = ""
)

$ErrorActionPreference = "Stop"

# =============================================================================
# Find Repository Root
# =============================================================================

function Find-RepoRoot {
    $searchPath = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }
    $current = Get-Item $searchPath
    while ($current) {
        $gitDir = Join-Path $current.FullName ".git"
        $pyproject = Join-Path $current.FullName "pyproject.toml"
        if ((Test-Path $gitDir) -and (Test-Path $pyproject)) {
            return $current.FullName
        }
        $current = $current.Parent
    }
    if (Test-Path (Join-Path (Get-Location) "pyproject.toml")) {
        return (Get-Location).Path
    }
    return $null
}

# =============================================================================
# Port Cleanup - Kill Stale Processes
# =============================================================================

function Clear-StaleProcesses {
    param([int[]]$Ports)
    $killed = @()
    foreach ($port in $Ports) {
        try {
            $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
            foreach ($conn in $connections) {
                $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                if ($proc -and $proc.Name -ne "System") {
                    # Use taskkill /T to kill entire process tree
                    taskkill /F /T /PID $conn.OwningProcess 2>$null | Out-Null
                    $killed += "Port $port (PID $($conn.OwningProcess), $($proc.Name))"
                }
            }
        } catch { }
    }
    if ($killed.Count -gt 0) {
        Write-Host "[CLEANUP] Killed stale processes:" -ForegroundColor Yellow
        $killed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
        Start-Sleep -Milliseconds 500
    }
}

function Stop-ProcessTree {
    <#
    .SYNOPSIS
        Kill a process and all its descendants using taskkill /T
    #>
    param([int]$ProcessId)
    if ($ProcessId -gt 0) {
        taskkill /F /T /PID $ProcessId 2>$null | Out-Null
    }
}

# =============================================================================
# Main Script
# =============================================================================

$REPO_ROOT = Find-RepoRoot
if (-not $REPO_ROOT) {
    Write-Host "[ERROR] Could not find repository root." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Engineering Tools Platform" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host "Repository: $REPO_ROOT" -ForegroundColor Gray
Write-Host ""

Push-Location $REPO_ROOT

try {
    # -------------------------------------------------------------------------
    # Environment Checks
    # -------------------------------------------------------------------------
    
    $venvPath = Join-Path $REPO_ROOT ".venv"
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    
    if (-not $SkipSetup) {
        if (-not (Test-Path $activateScript)) {
            Write-Host "[SETUP] Virtual environment not found. Running setup.ps1..." -ForegroundColor Yellow
            & (Join-Path $REPO_ROOT "setup.ps1")
        }
        
        $homepageModules = Join-Path $REPO_ROOT "apps\homepage\frontend\node_modules"
        if (-not (Test-Path $homepageModules)) {
            Write-Host "[SETUP] Frontend dependencies not found. Running setup.ps1..." -ForegroundColor Yellow
            & (Join-Path $REPO_ROOT "setup.ps1")
        }
    }
    
    # -------------------------------------------------------------------------
    # Activate Virtual Environment
    # -------------------------------------------------------------------------
    
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Virtual environment not found. Run setup.ps1 first." -ForegroundColor Red
        exit 1
    }
    
    # -------------------------------------------------------------------------
    # Verify Honcho is installed
    # -------------------------------------------------------------------------
    
    $honchoPath = Join-Path $venvPath "Scripts\honcho.exe"
    if (-not (Test-Path $honchoPath)) {
        Write-Host "[INSTALL] Installing honcho..." -ForegroundColor Yellow
        pip install honcho --quiet
    }
    Write-Host "[OK] Honcho process manager ready" -ForegroundColor Green
    
    # -------------------------------------------------------------------------
    # Clean stale processes (if requested or always for safety)
    # -------------------------------------------------------------------------
    
    $ALL_PORTS = @(8000, 8001, 3000, 5173, 5174, 5175)
    
    if ($Clean) {
        Clear-StaleProcesses -Ports $ALL_PORTS
    }
    
    # -------------------------------------------------------------------------
    # Determine which services to start
    # -------------------------------------------------------------------------
    
    $services = @()
    
    if ($Docs) {
        $services = @("mkdocs")
    } elseif ($BackendOnly) {
        $services = @("backend")
    } elseif ($Tool -eq "dat") {
        $services = @("backend", "mkdocs", "dat")
    } elseif ($Tool -eq "sov") {
        $services = @("backend", "mkdocs", "sov")
    } elseif ($Tool -eq "pptx") {
        $services = @("backend", "mkdocs", "pptx")
    } else {
        # Default: start everything
        $services = @()  # Empty = all services in Procfile
    }
    
    # -------------------------------------------------------------------------
    # Print startup info
    # -------------------------------------------------------------------------
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " Starting Services via Honcho" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  ENDPOINTS" -ForegroundColor Yellow
    Write-Host "  ---------" -ForegroundColor Yellow
    Write-Host "  Backend API:      http://localhost:8000" -ForegroundColor White
    Write-Host "  Swagger Docs:     http://localhost:8000/docs" -ForegroundColor Gray
    Write-Host "  MkDocs:           http://localhost:8001" -ForegroundColor White
    Write-Host "  Homepage:         http://localhost:3000" -ForegroundColor White
    Write-Host "  DAT Frontend:     http://localhost:5173" -ForegroundColor Gray
    Write-Host "  SOV Frontend:     http://localhost:5174" -ForegroundColor Gray
    Write-Host "  PPTX Frontend:    http://localhost:5175" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Press Ctrl+C to stop all services (clean shutdown)" -ForegroundColor Yellow
    Write-Host ""
    
    # -------------------------------------------------------------------------
    # Start Honcho with proper process tree management
    # -------------------------------------------------------------------------
    
    # All ports used by our services
    $ALL_PORTS = @(8000, 8001, 3000, 5173, 5174, 5175)
    
    # Start honcho as a background job so we can control cleanup
    $honchoArgs = if ($services.Count -eq 0) { "start" } else { "start $($services -join ' ')" }
    
    $honchoJob = Start-Job -ScriptBlock {
        param($repoRoot, $honchoCommand)
        Set-Location $repoRoot
        & honcho $honchoCommand.Split(' ')
    } -ArgumentList $REPO_ROOT, $honchoArgs
    
    Write-Host "[INFO] Honcho job started (Job ID: $($honchoJob.Id))" -ForegroundColor Gray
    Write-Host "[INFO] Waiting for services to start..." -ForegroundColor Gray
    
    # Wait a bit for services to start, then show endpoints
    Start-Sleep -Seconds 3
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " ENDPOINTS (Services Running)" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Homepage:         " -NoNewline -ForegroundColor White
    Write-Host "http://localhost:3000" -ForegroundColor Cyan
    Write-Host "  Backend API:      " -NoNewline -ForegroundColor White
    Write-Host "http://localhost:8000" -ForegroundColor Cyan
    Write-Host "  Swagger Docs:     " -NoNewline -ForegroundColor Gray
    Write-Host "http://localhost:8000/docs" -ForegroundColor Cyan
    Write-Host "  MkDocs:           " -NoNewline -ForegroundColor White
    Write-Host "http://localhost:8001" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Tool Frontends (embedded in Homepage):" -ForegroundColor Gray
    Write-Host "    DAT:  http://localhost:5173" -ForegroundColor DarkGray
    Write-Host "    SOV:  http://localhost:5174" -ForegroundColor DarkGray
    Write-Host "    PPTX: http://localhost:5175" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "  Press Ctrl+C to stop all services" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    try {
        # Wait for job while streaming output - Ctrl+C will throw and land in finally block
        while ($honchoJob.State -eq 'Running') {
            # Receive and display job output
            $output = Receive-Job -Job $honchoJob -ErrorAction SilentlyContinue
            if ($output) {
                $output | ForEach-Object {
                    # Filter out the InterruptedError traceback noise
                    if ($_ -notmatch "InterruptedError|Traceback|File.*runpy|frozen runpy") {
                        Write-Host $_
                    }
                }
            }
            Start-Sleep -Milliseconds 100
        }
    } catch {
        # Ctrl+C throws - this is expected, cleanup will run in finally
    } finally {
        Write-Host "`n[SHUTDOWN] Stopping all services..." -ForegroundColor Yellow
        
        # Stop the job first
        Stop-Job -Job $honchoJob -ErrorAction SilentlyContinue
        Remove-Job -Job $honchoJob -Force -ErrorAction SilentlyContinue
        
        # Kill ALL processes on our ports using taskkill /T (kills entire process tree)
        foreach ($port in $ALL_PORTS) {
            try {
                $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
                foreach ($conn in $connections) {
                    $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                    if ($proc -and $proc.Name -ne "System") {
                        Write-Host "  Stopping $($proc.Name) (PID $($conn.OwningProcess)) on port $port" -ForegroundColor Gray
                        taskkill /F /T /PID $conn.OwningProcess 2>$null | Out-Null
                    }
                }
            } catch { }
        }
        
        # Also kill any remaining python/node processes that might be orphaned
        # Only kill those started recently (within last hour) to avoid killing unrelated processes
        $recentThreshold = (Get-Date).AddHours(-1)
        Get-Process -Name "python", "node" -ErrorAction SilentlyContinue | Where-Object {
            $_.StartTime -gt $recentThreshold
        } | ForEach-Object {
            Write-Host "  Stopping orphan $($_.Name) (PID $($_.Id))" -ForegroundColor Gray
            taskkill /F /T /PID $_.Id 2>$null | Out-Null
        }
        
        Write-Host "[OK] All services stopped." -ForegroundColor Green
    }
    
} finally {
    Pop-Location
}
