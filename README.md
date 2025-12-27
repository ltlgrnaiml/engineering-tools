# Engineering Tools Platform

A modular monorepo containing engineering analysis and reporting tools designed for semiconductor manufacturing workflows.

## Tools

| Tool | Status | Description |
|------|--------|-------------|
| **Homepage** | 🚧 In Progress | Tool launcher and DataSet browser |
| **Data Aggregator** | 🚧 In Progress | Multi-source data extraction and aggregation |
| **PowerPoint Generator** | 🔄 Migration | Automated report generation from templates |
| **SOV Analyzer** | 📋 Planned | Source of Variation (ANOVA) analysis |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                            │
│                    (FastAPI Router)                         │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  Homepage   │    DAT      │    SOV      │      PPTX       │
│  /app       │  /api/dat   │  /api/sov   │   /api/pptx     │
└─────────────┴──────┬──────┴──────┬──────┴────────┬────────┘
                     │             │               │
                     ▼             ▼               ▼
              ┌──────────────────────────────────────────┐
              │           Shared Contracts               │
              │         (Pydantic Models)                │
              │     DataSet • Pipeline • Registry        │
              └──────────────────────────────────────────┘
                                  │
                                  ▼
              ┌──────────────────────────────────────────┐
              │        Shared Artifact Storage           │
              │    workspace/ (Parquet + SQLite)         │
              └──────────────────────────────────────────┘
```

## Quick Start

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows

# Install all dependencies
pip install -e ".[all]"

# Run the platform
python -m gateway.main

# Open browser
open http://localhost:8000
```

## Project Structure

```
engineering-tools/
├── shared/              # Tier 0: Contracts, utilities, storage
├── gateway/             # API gateway and cross-tool services
├── apps/                # Individual tool applications
│   ├── homepage/        # Tool launcher
│   ├── data-aggregator/ # Data extraction & aggregation
│   ├── pptx-generator/  # PowerPoint report generation
│   └── sov-analyzer/    # Source of Variation analysis
├── workspace/           # Local artifact storage (gitignored)
├── tools/               # Development tooling
├── ci/                  # CI pipeline scripts
├── docs/                # Cross-cutting documentation
└── .adrs/               # Architecture Decision Records
```

## Documentation Hierarchy (3-Tier Model)

Per [ADR-0015](/.adrs/ADR-0015_3-Tier-Document-Model.json):

- **Tier 0**: `shared/contracts/` - Pydantic models (source of truth)
- **Tier 1**: `.adrs/` - ADRs explain WHY decisions were made
- **Tier 2**: `docs/specs/` - Specs define WHAT we're building
- **Tier 3**: `docs/guides/` - Guides show HOW to do things

## Key ADRs

| ADR | Topic |
|-----|-------|
| ADR-0009 | Type Safety & Contract Discipline |
| ADR-0015 | 3-Tier Document Model |
| ADR-0016 | Hybrid Semver Contract Versioning |
| ADR-0017 | Cross-Cutting Guardrails |

## Development

See [docs/guides/developer/local_setup.md](docs/guides/developer/local_setup.md) for detailed setup instructions.

## License

MIT
