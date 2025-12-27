# Engineering Tools Platform - Setup Guide

Cross-platform setup and startup scripts for the Engineering Tools monorepo.

## Quick Start

### macOS / Linux

```bash
# Initial setup (run once)
./setup.sh

# Start the platform
./start.sh

# Start with frontend (gateway + homepage)
./start.sh --with-frontend
```

### Windows (PowerShell)

```powershell
# Initial setup (run once)
.\setup.ps1

# Start the platform
.\start.ps1

# Start with frontend (gateway + homepage)
.\start.ps1 --with-frontend
```

---

## Setup Scripts

### `setup.sh` / `setup.ps1`

**What it does:**
- ✅ Checks Python 3.9+ is installed
- ✅ Creates virtual environment (`.venv/`)
- ✅ Installs Python dependencies from `pyproject.toml`
- ✅ Installs frontend dependencies (npm packages)
- ✅ Creates workspace directory structure

**When to run:**
- First time cloning the repository
- After pulling major dependency changes
- When setting up on a new machine

**Requirements:**
- Python 3.9 or higher
- Node.js 18+ and npm (for frontend)

---

## Start Scripts

### `start.sh` / `start.ps1`

**What it does:**
- ✅ Activates virtual environment
- ✅ Starts API Gateway on `http://localhost:8000`
- ✅ Optionally starts Homepage frontend on `http://localhost:3000`

**Usage:**

```bash
# Gateway only (API backend)
./start.sh

# Gateway + Frontend (full platform)
./start.sh --with-frontend
# or
./start.sh -f
```

**Endpoints when running:**
- **Gateway API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Homepage:** http://localhost:3000 (with `--with-frontend`)

**Available APIs:**
- `/api/health` - Platform health check
- `/api/datasets` - Cross-tool DataSets
- `/api/pipelines` - Multi-tool pipelines
- `/api/dat/...` - Data Aggregator tool
- `/api/sov/...` - SOV Analyzer tool
- `/api/pptx/...` - PowerPoint Generator tool

---

## Manual Setup (Alternative)

If you prefer manual setup or need to troubleshoot:

### macOS / Linux

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
pip install -e ".[all]"

# Install frontend dependencies
cd apps/homepage/frontend
npm install
cd ../../..

# Create workspace directories
mkdir -p workspace/tools/{dat,pptx,sov}
mkdir -p workspace/{datasets,pipelines}

# Start gateway
python -m gateway.main

# In another terminal: Start frontend
cd apps/homepage/frontend
npm run dev
```

### Windows (PowerShell)

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -e ".[all]"

# Install frontend dependencies
cd apps\homepage\frontend
npm install
cd ..\..\..

# Create workspace directories
New-Item -ItemType Directory -Force -Path workspace\tools\dat
New-Item -ItemType Directory -Force -Path workspace\tools\pptx
New-Item -ItemType Directory -Force -Path workspace\tools\sov
New-Item -ItemType Directory -Force -Path workspace\datasets
New-Item -ItemType Directory -Force -Path workspace\pipelines

# Start gateway
python -m gateway.main

# In another terminal: Start frontend
cd apps\homepage\frontend
npm run dev
```

---

## Troubleshooting

### "Python not found"
- **macOS/Linux:** Install Python 3.9+ via Homebrew: `brew install python@3.12`
- **Windows:** Download from [python.org](https://www.python.org/downloads/)

### "npm not found"
- **macOS/Linux:** Install Node.js via Homebrew: `brew install node`
- **Windows:** Download from [nodejs.org](https://nodejs.org/)

### "Address already in use" (Port 8000 or 3000)
```bash
# macOS/Linux - Find and kill process
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9

# Windows - Find and kill process
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process
```

### "Module not found" errors
Run setup again to reinstall dependencies:
```bash
./setup.sh          # macOS/Linux
.\setup.ps1         # Windows
```

### Virtual environment not activating automatically
- **macOS/Linux:** Check `~/.zshrc` or `~/.bashrc` for venv activation function
- **Windows:** PowerShell execution policy may need adjustment:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

---

## Development Workflow

### Typical workflow:

1. **One-time setup:**
   ```bash
   ./setup.sh
   ```

2. **Daily development:**
   ```bash
   # Start backend only (for API development)
   ./start.sh
   
   # OR start full platform (for frontend development)
   ./start.sh --with-frontend
   ```

3. **After pulling changes:**
   ```bash
   # Reinstall dependencies if needed
   ./setup.sh
   ```

### Working on individual tools:

Each tool can be run standalone for development:

```bash
# Activate venv
source .venv/bin/activate  # macOS/Linux
.\.venv\Scripts\Activate.ps1  # Windows

# Run individual tool
python -m apps.data_aggregator.backend.main      # DAT on port 8001
python -m apps.sov_analyzer.backend.main         # SOV on port 8002
python -m apps.pptx_generator.backend.main       # PPTX on port 8003
```

---

## Project Structure

```
engineering-tools/
├── setup.sh / setup.ps1       # Setup scripts
├── start.sh / start.ps1       # Startup scripts
├── apps/                      # Tool applications
│   ├── homepage/frontend/     # React homepage
│   ├── data_aggregator/       # DAT tool
│   ├── sov_analyzer/          # SOV tool
│   └── pptx_generator/        # PPTX tool
├── shared/                    # Shared code
│   ├── contracts/             # Pydantic contracts
│   ├── storage/               # Artifact store
│   └── frontend/              # Shared React components
├── gateway/                   # API Gateway
├── workspace/                 # Runtime data (gitignored)
│   ├── tools/                 # Tool-specific data
│   ├── datasets/              # Shared datasets
│   └── pipelines/             # Pipeline definitions
└── docs/                      # Documentation
```

---

## Next Steps

After setup, explore:

1. **API Documentation:** http://localhost:8000/docs
2. **Homepage:** http://localhost:3000
3. **Architecture Docs:** `docs/change-plan/`
4. **ADRs:** `.adrs/`

For detailed implementation guides, see `docs/change-plan/tier-4-implementation/`.
