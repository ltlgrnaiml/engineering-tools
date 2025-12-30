<#
.SYNOPSIS
    Engineering Tools Platform - Development Environment Startup Script

.DESCRIPTION
    Starts all services required for the Engineering Tools Platform development environment.
    This script implements ADR-0037 (Single-Command Development Environment) and follows
    the iframe integration pattern defined in ADR-0042 / SPEC-0045.

    ARCHITECTURE REFERENCES:
    - ADR-0037: Single-Command Development Environment
    - ADR-0042: Frontend Iframe Integration Pattern
    - ADR-0029: Simplified API Endpoint Naming (/api/{tool}/{resource})
    - SPEC-0045: Frontend Iframe Integration Implementation
    - docs/platform/ARCHITECTURE.md: Full platform architecture

    WHY ALL FRONTENDS BY DEFAULT?
    The Homepage frontend embeds tool UIs via iframes (see ADR-0042). When you navigate
    to /tools/dat, /tools/sov, or /tools/pptx in the Homepage, it loads the standalone
    tool frontend in an iframe. This requires all tool frontends to be running.

.PARAMETER BackendOnly
    Start only the backend API gateway (no frontends, no docs)

.PARAMETER Docs
    Start only the MkDocs documentation server

.PARAMETER SkipSetup
    Skip environment readiness checks

.PARAMETER Tool
    Start backend + specific tool frontend only (for isolated development)
    Valid values: dat, sov, pptx

.PARAMETER BackendPort
    Override the default backend port (default: 8000)

.EXAMPLE
    .\start.ps1
    # Starts everything: backend (8000), mkdocs (8001), homepage (3000), all tool frontends

.EXAMPLE
    .\start.ps1 -Tool dat
    # Starts backend + DAT frontend only (for isolated DAT development)

.EXAMPLE
    .\start.ps1 -BackendOnly
    # Starts only the backend API gateway

.NOTES
    Port Assignments (per SPEC-0045):
      Backend Gateway:  8000  (API: /api/{tool}/{resource} per ADR-0029)
      MkDocs:           8001
      Homepage:         3000  (entry point, embeds tools via iframes)
      DAT Frontend:     5173  (embedded at /tools/dat)
      SOV Frontend:     5174  (embedded at /tools/sov)
      PPTX Frontend:    5175  (embedded at /tools/pptx)

    API Endpoints (per ADR-0029):
      Platform:  /docs, /redoc, /openapi.json, /health
      DAT:       /api/dat/docs, /api/dat/*
      SOV:       /api/sov/docs, /api/sov/*
      PPTX:      /api/pptx/docs, /api/pptx/*
      DataSets:  /api/datasets/*
      Pipelines: /api/pipelines/*
#>

param(
    [switch]$BackendOnly,
    [switch]$Docs,
    [switch]$SkipSetup,
    [ValidateSet("", "dat", "sov", "pptx")]
    [string]$Tool = "",
    [int]$BackendPort = 8000
)

$ErrorActionPreference = "Stop"

# =============================================================================
# Python Cache Cleanup - Ensure Fresh Code
# =============================================================================
# Per ADR-0037: Clear Python bytecode cache to ensure fresh code is loaded.
# This prevents stale .pyc files from being used instead of updated .py files.

function Clear-PythonCache {
    param([string]$Root)
    
    $cacheCount = 0
    $dirs = Get-ChildItem -Path $Root -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue
    foreach ($dir in $dirs) {
        try {
            Remove-Item -Path $dir.FullName -Recurse -Force -ErrorAction SilentlyContinue
            $cacheCount++
        } catch {
            # Ignore errors - directory may be in use
        }
    }
    
    if ($cacheCount -gt 0) {
        Write-Host "[CACHE] Cleared $cacheCount Python __pycache__ directories" -ForegroundColor Yellow
    }
}

# =============================================================================
# Port Cleanup - Kill Stale Processes
# =============================================================================
# Per ADR-0037: Ensure clean startup by killing any stale processes on our ports.
# This prevents "port already in use" errors and ensures fresh code is loaded.

function Clear-StaleProcesses {
    param([int[]]$Ports)
    
    $killed = @()
    foreach ($port in $Ports) {
        try {
            $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
            foreach ($conn in $connections) {
                $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                if ($proc -and $proc.Name -ne "System") {
                    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
                    $killed += "Port $port (PID $($conn.OwningProcess), $($proc.Name))"
                }
            }
        } catch {
            # Ignore errors - port may not be in use
        }
    }
    
    if ($killed.Count -gt 0) {
        Write-Host "[CLEANUP] Killed stale processes:" -ForegroundColor Yellow
        $killed | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
        Write-Host ""
        Start-Sleep -Milliseconds 500  # Give OS time to release ports
    }
}

# =============================================================================
# Find Repository Root
# =============================================================================

function Find-RepoRoot {
    # Start from script location if invoked directly, otherwise from current dir
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
    
    # Fallback: check if we're already at the root
    if (Test-Path (Join-Path (Get-Location) "pyproject.toml")) {
        return (Get-Location).Path
    }
    
    return $null
}

$REPO_ROOT = Find-RepoRoot
if (-not $REPO_ROOT) {
    Write-Host "[ERROR] Could not find repository root. Ensure you're within the engineering-tools repo." -ForegroundColor Red
    exit 1
}

Write-Host "Engineering Tools Platform" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host "Repository: $REPO_ROOT" -ForegroundColor Gray
Write-Host ""

# Change to repo root for all operations
Push-Location $REPO_ROOT

try {
    # =============================================================================
    # Environment Checks & Setup
    # =============================================================================

    function Test-VenvReady {
        $venvPath = Join-Path $REPO_ROOT ".venv"
        $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
        return (Test-Path $venvPath) -and (Test-Path $activateScript)
    }

    function Test-FrontendReady {
        $homepagePath = Join-Path $REPO_ROOT "apps\homepage\frontend"
        $nodeModules = Join-Path $homepagePath "node_modules"
        return Test-Path $nodeModules
    }

    function Invoke-Setup {
        Write-Host "[SETUP] Running initial setup..." -ForegroundColor Yellow
        $setupScript = Join-Path $REPO_ROOT "setup.ps1"
        if (Test-Path $setupScript) {
            & $setupScript
        } else {
            Write-Host "[ERROR] setup.ps1 not found at $setupScript" -ForegroundColor Red
            exit 1
        }
    }

    if (-not $SkipSetup) {
        $needsSetup = $false
        
        if (-not (Test-VenvReady)) {
            Write-Host "[CHECK] Python virtual environment not found" -ForegroundColor Yellow
            $needsSetup = $true
        } else {
            Write-Host "[OK] Python virtual environment ready" -ForegroundColor Green
        }
        
        if (-not (Test-FrontendReady)) {
            Write-Host "[CHECK] Frontend dependencies not installed" -ForegroundColor Yellow
            $needsSetup = $true
        } else {
            Write-Host "[OK] Frontend dependencies ready" -ForegroundColor Green
        }
        
        if ($needsSetup) {
            Write-Host ""
            Invoke-Setup
            Write-Host ""
        }
    }

    # =============================================================================
    # Activate Virtual Environment
    # =============================================================================

    $activateScript = Join-Path $REPO_ROOT ".venv\Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Virtual environment not found. Run setup.ps1 first." -ForegroundColor Red
        exit 1
    }

    # =============================================================================
    # Clear Python Cache (ensure fresh code loads)
    # =============================================================================
    Clear-PythonCache -Root $REPO_ROOT

    # =============================================================================
    # Port Configuration (per ADR-0042 / SPEC-0045)
    # =============================================================================
    # These port assignments are defined in SPEC-0045 and must remain consistent
    # across all tool vite.config.ts files and this script.
    #
    # Architecture: Homepage embeds tool frontends via iframes (ADR-0042)
    #   Homepage (3000) -> iframe src="localhost:5173" for DAT
    #   Homepage (3000) -> iframe src="localhost:5174" for SOV
    #   Homepage (3000) -> iframe src="localhost:5175" for PPTX
    #
    # API Routes (per ADR-0029): /api/{tool}/{resource}
    #   Gateway mounts tool apps: /api/dat/*, /api/sov/*, /api/pptx/*
    # =============================================================================
    
    $PORTS = @{
        Backend  = $BackendPort  # API Gateway - hosts /api/{tool}/* routes
        Homepage = 3000          # Main SPA - embeds tools via iframes
        DAT      = 5173          # Data Aggregator standalone frontend
        SOV      = 5174          # SOV Analyzer standalone frontend
        PPTX     = 5175          # PPTX Generator standalone frontend
        MkDocs   = 8001          # Documentation server
    }

    # =============================================================================
    # Clean Up Stale Processes
    # =============================================================================
    # Kill any processes still listening on our ports from previous runs
    
    $portsToClean = @($PORTS.Backend, $PORTS.MkDocs, $PORTS.Homepage, $PORTS.DAT, $PORTS.SOV, $PORTS.PPTX)
    Clear-StaleProcesses -Ports $portsToClean

    # =============================================================================
    # Start Services
    # =============================================================================

    $jobs = @()

    # Start Backend (unless Docs-only mode)
    if (-not $Docs) {
        Write-Host ""
        Write-Host "[STARTING] Backend API on http://localhost:$($PORTS.Backend)" -ForegroundColor Cyan
        
        $backendJob = Start-Job -Name "Backend" -ScriptBlock {
            param($root, $port)
            Set-Location $root
            & "$root\.venv\Scripts\Activate.ps1"
            python -m uvicorn gateway.main:app --host 0.0.0.0 --port $port --reload
        } -ArgumentList $REPO_ROOT, $PORTS.Backend
        
        $jobs += $backendJob
        Write-Host "  Backend PID: $($backendJob.Id)" -ForegroundColor Gray
    }

    # Start MkDocs (by default, or if -Docs specified alone)
    if (-not $Tool -or $Docs) {
        Write-Host ""
        Write-Host "[STARTING] MkDocs on http://localhost:$($PORTS.MkDocs)" -ForegroundColor Cyan
        
        $mkdocsJob = Start-Job -Name "MkDocs" -ScriptBlock {
            param($root, $port)
            Set-Location $root
            & "$root\.venv\Scripts\Activate.ps1"
            mkdocs serve --dev-addr "127.0.0.1:$port"
        } -ArgumentList $REPO_ROOT, $PORTS.MkDocs
        
        $jobs += $mkdocsJob
        Write-Host "  MkDocs PID: $($mkdocsJob.Id)" -ForegroundColor Gray
    }

    # Start Frontend(s) - unless BackendOnly or Docs mode
    if (-not $BackendOnly -and -not $Docs) {
        # Determine which frontends to start
        $frontendsToStart = @()
        
        if ($Tool -eq "pptx") {
            $frontendsToStart = @(
                @{ Name = "PPTX"; Path = "apps\pptx_generator\frontend"; Port = $PORTS.PPTX }
            )
        } elseif ($Tool -eq "dat") {
            $frontendsToStart = @(
                @{ Name = "DAT"; Path = "apps\data_aggregator\frontend"; Port = $PORTS.DAT }
            )
        } elseif ($Tool -eq "sov") {
            $frontendsToStart = @(
                @{ Name = "SOV"; Path = "apps\sov_analyzer\frontend"; Port = $PORTS.SOV }
            )
        } else {
            # Default: ALL frontends (Homepage embeds tools via iframes)
            $frontendsToStart = @(
                @{ Name = "Homepage"; Path = "apps\homepage\frontend"; Port = $PORTS.Homepage },
                @{ Name = "DAT"; Path = "apps\data_aggregator\frontend"; Port = $PORTS.DAT },
                @{ Name = "SOV"; Path = "apps\sov_analyzer\frontend"; Port = $PORTS.SOV },
                @{ Name = "PPTX"; Path = "apps\pptx_generator\frontend"; Port = $PORTS.PPTX }
            )
        }
        
        foreach ($fe in $frontendsToStart) {
            Write-Host ""
            Write-Host "[STARTING] $($fe.Name) Frontend on http://localhost:$($fe.Port)" -ForegroundColor Cyan
            
            $fePath = Join-Path $REPO_ROOT $fe.Path
            $fePort = $fe.Port
            $feName = $fe.Name
            
            $feJob = Start-Job -Name $feName -ScriptBlock {
                param($path, $port)
                Set-Location $path
                npm run dev -- --port $port --host
            } -ArgumentList $fePath, $fePort
            
            $jobs += $feJob
            Write-Host "  $feName PID: $($feJob.Id)" -ForegroundColor Gray
        }
    }

    # =============================================================================
    # Wait and Handle Shutdown
    # =============================================================================

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " Services Started Successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    # Backend Links
    if (-not $Docs) {
        Write-Host "  BACKEND API" -ForegroundColor Yellow
        Write-Host "  -----------" -ForegroundColor Yellow
        Write-Host "  Gateway API:      http://localhost:$($PORTS.Backend)" -ForegroundColor White
        Write-Host "  Health Check:     http://localhost:$($PORTS.Backend)/health" -ForegroundColor Gray
        Write-Host ""
        Write-Host "  SWAGGER / OPENAPI" -ForegroundColor Yellow
        Write-Host "  -----------------" -ForegroundColor Yellow
        Write-Host "  Platform Docs:    http://localhost:$($PORTS.Backend)/docs" -ForegroundColor White
        Write-Host "  Platform ReDoc:   http://localhost:$($PORTS.Backend)/redoc" -ForegroundColor Gray
        Write-Host "  PPTX Swagger:     http://localhost:$($PORTS.Backend)/api/pptx/docs" -ForegroundColor White
        Write-Host "  DAT Swagger:      http://localhost:$($PORTS.Backend)/api/dat/docs" -ForegroundColor White
        Write-Host "  SOV Swagger:      http://localhost:$($PORTS.Backend)/api/sov/docs" -ForegroundColor White
        Write-Host ""
    }
    
    # Documentation Links
    if (-not $Tool -or $Docs) {
        Write-Host "  DOCUMENTATION" -ForegroundColor Yellow
        Write-Host "  -------------" -ForegroundColor Yellow
        Write-Host "  MkDocs:           http://localhost:$($PORTS.MkDocs)" -ForegroundColor White
        Write-Host ""
    }
    
    # Frontend Links
    if (-not $BackendOnly -and -not $Docs) {
        Write-Host "  FRONTENDS" -ForegroundColor Yellow
        Write-Host "  ---------" -ForegroundColor Yellow
        if ($Tool -eq "pptx") {
            Write-Host "  PPTX Tool:        http://localhost:$($PORTS.PPTX)" -ForegroundColor White
        } elseif ($Tool -eq "dat") {
            Write-Host "  DAT Tool:         http://localhost:$($PORTS.DAT)" -ForegroundColor White
        } elseif ($Tool -eq "sov") {
            Write-Host "  SOV Tool:         http://localhost:$($PORTS.SOV)" -ForegroundColor White
        } else {
            # Default: All frontends (Homepage uses iframes to embed tools)
            Write-Host "  Homepage:         http://localhost:$($PORTS.Homepage)" -ForegroundColor White
            Write-Host "    -> DAT:         http://localhost:$($PORTS.Homepage)/tools/dat" -ForegroundColor Gray
            Write-Host "    -> SOV:         http://localhost:$($PORTS.Homepage)/tools/sov" -ForegroundColor Gray
            Write-Host "    -> PPTX:        http://localhost:$($PORTS.Homepage)/tools/pptx" -ForegroundColor Gray
            Write-Host "  (Standalone)" -ForegroundColor DarkGray
            Write-Host "    DAT:            http://localhost:$($PORTS.DAT)" -ForegroundColor DarkGray
            Write-Host "    SOV:            http://localhost:$($PORTS.SOV)" -ForegroundColor DarkGray
            Write-Host "    PPTX:           http://localhost:$($PORTS.PPTX)" -ForegroundColor DarkGray
        }
        Write-Host ""
    }
    
    Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor Yellow
    Write-Host ""

    # Stream output from jobs
    try {
        while ($true) {
            foreach ($job in $jobs) {
                $output = Receive-Job -Job $job -ErrorAction SilentlyContinue
                if ($output) {
                    $prefixMap = @{
                        "Backend" = "[BE]"
                        "MkDocs" = "[DOCS]"
                        "Homepage" = "[HOME]"
                        "DAT" = "[DAT]"
                        "SOV" = "[SOV]"
                        "PPTX" = "[PPTX]"
                    }
                    $prefix = if ($prefixMap.ContainsKey($job.Name)) { $prefixMap[$job.Name] } else { "[$($job.Name)]" }
                    $colorMap = @{
                        "Backend" = "Cyan"
                        "MkDocs" = "DarkYellow"
                        "Homepage" = "Magenta"
                        "DAT" = "Green"
                        "SOV" = "DarkCyan"
                        "PPTX" = "Blue"
                    }
                    $color = if ($colorMap.ContainsKey($job.Name)) { $colorMap[$job.Name] } else { "White" }
                    $output | ForEach-Object { Write-Host "$prefix $_" -ForegroundColor $color }
                }
                
                if ($job.State -eq "Failed") {
                    Write-Host "[$($job.Name)] Job failed!" -ForegroundColor Red
                    Receive-Job -Job $job -ErrorAction SilentlyContinue | Write-Host
                }
            }
            Start-Sleep -Milliseconds 500
        }
    }
    finally {
        Write-Host ""
        Write-Host "[SHUTDOWN] Stopping all services..." -ForegroundColor Yellow
        
        # First, kill processes on our ports BEFORE stopping jobs
        # This ensures clean socket release
        $portsToClean = @($PORTS.Backend, $PORTS.MkDocs, $PORTS.Homepage, $PORTS.DAT, $PORTS.SOV, $PORTS.PPTX)
        foreach ($port in $portsToClean) {
            try {
                $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
                foreach ($conn in $connections) {
                    $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                    if ($proc) {
                        # Kill entire process tree
                        $proc | Stop-Process -Force -ErrorAction SilentlyContinue
                        Write-Host "  Killed process on port $port (PID: $($conn.OwningProcess))" -ForegroundColor Gray
                    }
                }
            } catch {
                # Ignore - process may already be gone
            }
        }
        
        # Small delay to allow sockets to release
        Start-Sleep -Milliseconds 500
        
        # Then stop PowerShell jobs
        $jobs | Stop-Job -PassThru | Remove-Job -Force -ErrorAction SilentlyContinue
        
        # Final cleanup pass - kill any orphaned processes
        foreach ($port in $portsToClean) {
            try {
                $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
                foreach ($conn in $connections) {
                    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
                }
            } catch {
                # Ignore
            }
        }
        
        Write-Host "[OK] All services stopped" -ForegroundColor Green
    }

}
finally {
    Pop-Location
}
