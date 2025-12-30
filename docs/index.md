# Engineering Tools Platform Documentation

> **Unified platform for engineering data processing, analysis, and visualization**

---

## What is the Engineering Tools Platform?

The Engineering Tools Platform is a unified suite of applications that work together to transform raw engineering data into actionable insights and reports:

| Tool | Purpose | Status |
|------|---------|--------|
| **Data Aggregator** | Collect, clean, and transform data from multiple sources | ✅ Core Complete |
| **SOV Analyzer** | Source of Variation analysis and statistical insights | ✅ Core Complete |
| **PowerPoint Generator** | Automated presentation generation from data | ✅ Core Complete |

---

## Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Homepage (React SPA)                          │
│                    http://localhost:3000                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    API Gateway (FastAPI)                         │
│                    http://localhost:8000                         │
├─────────────────────────────────────────────────────────────────┤
│  /api/datasets/v1  │  /api/pipelines/v1  │  Tool APIs           │
└────────┬───────────┴──────────┬──────────┴────────┬─────────────┘
         │                      │                    │
    ┌────▼────┐           ┌────▼────┐         ┌────▼────┐
    │ DataSet │           │Pipeline │         │ Tool    │
    │ Store   │           │Registry │         │ Backends│
    └─────────┘           └─────────┘         └─────────┘
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **DataSet** | A versioned, schema-aware data artifact with lineage tracking |
| **Pipeline** | A multi-step workflow that chains tool operations together |
| **Tool** | An individual application (DAT, SOV, PPTX) with its own UI and API |
| **Gateway** | Central API that provides cross-tool services and routing |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- npm or yarn

### Installation

**Windows:**
```powershell
# Clone and setup
git clone <repository-url>
cd engineering-tools
.\setup.ps1

# Start the platform
.\start.ps1 --with-frontend
```

**Linux/macOS:**
```bash
# Clone and setup
git clone <repository-url>
cd engineering-tools
./setup.sh

# Start the platform
./start.sh --with-frontend
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Homepage | http://localhost:3000 | Main platform UI |
| Gateway API | http://localhost:8000 | Central API gateway |
| API Docs | http://localhost:8000/api/docs | OpenAPI documentation |
| PPTX Generator | http://localhost:5175 | PowerPoint Generator UI |
| Data Aggregator | http://localhost:5173 | Data Aggregator UI |
| SOV Analyzer | http://localhost:5174 | SOV Analyzer UI |

---

## Documentation by Tool

### PowerPoint Generator

| Document | Description |
|----------|-------------|
| [Overview](pptx-generator/index.md) | Introduction and key concepts |
| [Quick Start](pptx-generator/getting-started/QUICK_START.md) | 5-minute first report guide |
| [Architecture](pptx-generator/reference/ARCHITECTURE.md) | System design overview |

### Data Aggregator

| Document | Description |
|----------|-------------|
| [Overview](data-aggregator/index.md) | Introduction and key concepts |

### SOV Analyzer

| Document | Description |
|----------|-------------|
| [Overview](sov-analyzer/index.md) | Introduction and key concepts |

### Platform

| Document | Description |
|----------|-------------|
| [DataSets](platform/DATASETS.md) | Working with shared DataSets |
| [Pipelines](platform/PIPELINES.md) | Creating multi-tool pipelines |

---

## Cross-Tool Workflows

### Example: Data → Analysis → Report

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Data      │     │     SOV      │     │    PPTX      │
│  Aggregator  │ ──► │   Analyzer   │ ──► │  Generator   │
│              │     │              │     │              │
│  Upload CSV  │     │  Run SOV     │     │  Generate    │
│  Clean Data  │     │  Analysis    │     │  Report      │
│  Transform   │     │  Insights    │     │  Download    │
└──────────────┘     └──────────────┘     └──────────────┘
        ▼                   ▼                    ▼
   ┌─────────┐        ┌─────────┐          ┌─────────┐
   │ DataSet │        │ DataSet │          │  PPTX   │
   │   A     │        │   B     │          │  File   │
   └─────────┘        └─────────┘          └─────────┘
```

---

## Version

**Platform Version:** 0.1.0
**Documentation Version:** 1.1
**Last Updated:** 2025-12-28

---

## License

MIT License – See LICENSE file in repository root for details.
