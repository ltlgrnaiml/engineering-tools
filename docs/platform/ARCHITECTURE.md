# Platform Architecture

> **System design for the Engineering Tools Platform**

---

## Overview

The Engineering Tools Platform is a unified system that combines multiple engineering tools with shared data infrastructure.

```text
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Homepage   │  │  Tool UIs    │  │  API Docs    │           │
│  │  (React SPA) │  │  (iframes)   │  │  (Swagger)   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP
┌───────────────────────────▼─────────────────────────────────────┐
│                      API Gateway (FastAPI)                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  Cross-Tool APIs: /api/datasets/v1, /api/pipelines/v1      ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  /api/dat/*  │  │  /api/sov/*  │  │ /api/pptx/*  │          │
│  │  (mounted)   │  │  (mounted)   │  │  (mounted)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                      Shared Infrastructure                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ ArtifactStore│  │RegistryDB   │  │  Contracts   │          │
│  │  (DataSets)  │  │ (Pipelines) │  │  (Pydantic)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### API Gateway (`gateway/`)

The central entry point for all API requests:

- **`main.py`** - FastAPI app with CORS, health checks, and tool mounts
- **`services/dataset_service.py`** - Cross-tool DataSet APIs
- **`services/pipeline_service.py`** - Multi-tool pipeline orchestration

### Shared Infrastructure (`shared/`)

Common code and data structures used by all tools:

- **`contracts/core/`** - Pydantic models for DataSet, Pipeline, etc.
- **`storage/artifact_store.py`** - DataSet persistence (Parquet + manifest)
- **`storage/registry_db.py`** - Pipeline and metadata registry
- **`utils/stage_id.py`** - Deterministic ID generation

### Tool Applications (`apps/`)

Individual tool implementations:

- **`data_aggregator/`** - Data collection and transformation
- **`sov_analyzer/`** - Source of Variation analysis
- **`pptx_generator/`** - PowerPoint report generation
- **`homepage/`** - Platform homepage and navigation

---

## Data Flow

### Cross-Tool DataSet Flow

```text
┌─────────────────┐
│ Data Aggregator │
│   Upload CSV    │
│   Transform     │
│   Save DataSet  │─────┐
└─────────────────┘     │
                        ▼
              ┌─────────────────┐
              │ Shared DataSet  │
              │     Store       │
              │  (Parquet +     │
              │   Manifest)     │
              └────────┬────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│SOV Analyzer │ │PPTX Generator│ │Other Tools  │
│Load DataSet │ │Load DataSet │ │Load DataSet │
│  Analyze    │ │  Generate   │ │  Process    │
└─────────────┘ └─────────────┘ └─────────────┘
```

### Pipeline Execution

```text
Pipeline Definition
       │
       ▼
┌──────────────────────────────────────────────────────┐
│                 Pipeline Service                      │
│  1. Validate step dependencies                        │
│  2. Resolve dynamic inputs ($step_N_output)          │
│  3. Dispatch to tool APIs                            │
│  4. Track progress and handle errors                 │
└──────────────────────────────────────────────────────┘
       │
       ├──► DAT API ──► DataSet A
       │
       ├──► SOV API ──► DataSet B (using DataSet A)
       │
       └──► PPTX API ──► PowerPoint (using DataSet B)
```

---

## Directory Structure

```text
engineering-tools/
├── gateway/                 # API Gateway
│   ├── main.py             # FastAPI entry point
│   └── services/           # Cross-tool services
├── shared/                  # Shared infrastructure
│   ├── contracts/          # Pydantic models
│   ├── storage/            # Persistence layer
│   └── utils/              # Common utilities
├── apps/                    # Tool applications
│   ├── data_aggregator/    # DAT tool
│   ├── sov_analyzer/       # SOV tool
│   ├── pptx_generator/     # PPTX tool
│   └── homepage/           # Platform homepage
├── docs/                    # Documentation
└── tests/                   # Test suites
```

---

## Technology Stack

### Backend

- **Python 3.11+** - Core language
- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **Polars** - DataFrame operations
- **python-pptx** - PowerPoint generation

### Frontend

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **React Router** - Client-side routing

### Storage

- **Parquet** - DataSet storage format
- **JSON** - Manifest and metadata
- **In-memory** - Development mode (pipelines)

---

## Deployment Modes

### Development

```bash
# Start gateway with all frontends
./start.ps1 --with-frontend
```

- Gateway: http://localhost:8000
- Homepage: http://localhost:3000
- Individual tool UIs on separate ports

### Production

- Docker Compose deployment
- Nginx reverse proxy
- Persistent storage volumes
