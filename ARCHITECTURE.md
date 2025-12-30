# Engineering Tools Platform - Architecture

> System design overview for human developers.
> For AI assistant rules, see hierarchical `AGENTS.md` files.

---

## Overview

The Engineering Tools Platform is a **multi-tool monorepo** for semiconductor manufacturing data processing:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACES                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │ Homepage │  │   DAT    │  │   SOV    │  │   PPTX   │                     │
│  │  :3000   │  │  :5173   │  │  :5174   │  │  :5175   │                     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                     │
└───────┼─────────────┼─────────────┼─────────────┼───────────────────────────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────────────┐
│                        API GATEWAY (:8000)                                   │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Cross-Tool APIs: /api/v1/datasets, /api/v1/pipelines, /health        │   │
│  ├──────────────────────────────────────────────────────────────────────┤   │
│  │ Tool Mounts: /api/dat/*, /api/sov/*, /api/pptx/*                     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                        SHARED LAYER                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   Contracts     │  │    Storage      │  │    Utilities    │              │
│  │  (Pydantic)     │  │ (Parquet+JSON)  │  │ (ID, Path, etc) │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Tools

### Data Aggregator (DAT)

**Purpose**: Extract, transform, and aggregate data from multiple file formats.

**Architecture**: 8-stage guided workflow with profile-driven extraction.

```
Upload → Context → Preview → Select → Aggregate → Parse → Export → Complete
```

**Key Features**:
- Profile-driven extraction (YAML configuration)
- Adapter pattern for file types (CSV, Excel, JSON, XML)
- Large file streaming (>10MB threshold)
- Deterministic stage IDs (SHA-256)

### SOV Analyzer

**Purpose**: Source of Variation analysis using ANOVA.

**Architecture**: 5-stage analysis pipeline with visualization.

```
Load DataSet → Configure Factors → Compute ANOVA → Visualize → Export Results
```

**Key Features**:
- Type III Sum of Squares
- Variance decomposition (sums to 100%)
- Box plots, interaction plots, Pareto charts
- DataSet lineage tracking

### PowerPoint Generator (PPTX)

**Purpose**: Generate PowerPoint reports from data using templates.

**Architecture**: 7-step guided workflow with shape-based templating.

```
Upload Template → Upload Data → Map Context → Map Metrics → Validate → Generate → Download
```

**Key Features**:
- Named shape discovery (`{category}_{identifier}` pattern)
- Pluggable renderers (text, table, chart, image)
- "Four Green Bars" validation gate
- Domain configuration for metric canonicalization

---

## Data Flow

### Cross-Tool DataSet Sharing

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│     DAT      │         │     SOV      │         │    PPTX      │
│   (Extract)  │────────▶│  (Analyze)   │────────▶│  (Report)    │
└──────────────┘         └──────────────┘         └──────────────┘
       │                        │                        │
       ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    workspace/datasets/                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ dataset_A/      │  │ dataset_B/      │  │ dataset_C/      │  │
│  │ ├─ data.parquet │  │ ├─ data.parquet │  │ ├─ data.parquet │  │
│  │ └─ manifest.json│  │ └─ manifest.json│  │ └─ manifest.json│  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
│                                                                  │
│  Lineage: dataset_B.parent_ids = ["dataset_A"]                  │
│           dataset_C.parent_ids = ["dataset_B"]                  │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Orchestration

Tools can be chained via the Pipeline API:

```yaml
name: "Weekly SOV Report"
steps:
  - tool: dat
    action: export
    output: aggregated_data

  - tool: sov
    action: analyze
    input: $step_0.output
    output: sov_results

  - tool: pptx
    action: generate
    input: $step_1.output
    output: report.pptx
```

---

## 3-Tier Document Model

```
Tier 0: shared/contracts/     → Pydantic models (SSOT)
        │
        │  implements
        ▼
Tier 1: .adrs/                → ADRs explain WHY
        │
        │  details
        ▼
Tier 2: docs/specs/           → SPECs define WHAT
        │
        │  guides
        ▼
Tier 3: docs/guides/          → Guides show HOW
```

**Rule**: Content flows down, never duplicated across tiers.

---

## Key Architectural Decisions

| ADR | Decision | Impact |
|-----|----------|--------|
| ADR-0001 | FSM-based workflows | All tools use state machines |
| ADR-0005 | SHA-256 stage IDs | Reproducible, cacheable |
| ADR-0010 | Pydantic contracts | Type safety, auto-generated schemas |
| ADR-0012 | Profile-driven extraction | Declarative data pipelines |
| ADR-0026 | DataSet lineage | Cross-tool data tracking |
| ADR-0029 | Unified rendering | Shared visualization contracts |
| ADR-0034 | AI-parseable patterns | Consistent naming, docstrings |

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, FastAPI, Pydantic |
| **Data Processing** | Polars (NOT pandas) |
| **Frontend** | React 18+, TypeScript, TailwindCSS |
| **Storage** | Parquet (data), JSON (manifests) |
| **API** | REST, OpenAPI/Swagger |

---

## Directory Structure

```
engineering-tools/
├── AGENTS.md              # AI assistant rules (root)
├── ARCHITECTURE.md        # This file
├── README.md              # Quick start
├── SETUP.md               # Detailed setup
├── CONTRIBUTING.md        # Contribution guide
│
├── shared/                # Tier-0: Contracts, utilities
│   ├── contracts/         # Pydantic models (SSOT)
│   ├── middleware/        # Shared FastAPI middleware
│   ├── rendering/         # Unified rendering engine
│   └── utils/             # Stage ID, path safety, etc.
│
├── gateway/               # API gateway
│   ├── main.py            # FastAPI entry point
│   ├── routers/           # Cross-tool APIs
│   └── services/          # DataSet, Pipeline services
│
├── apps/                  # Tool applications
│   ├── data_aggregator/   # DAT
│   ├── pptx_generator/    # PPTX
│   └── sov_analyzer/      # SOV
│
├── workspace/             # Artifact storage (gitignored)
│   ├── datasets/          # Shared DataSets
│   └── tools/             # Tool-specific artifacts
│
├── .adrs/                 # Architecture Decision Records
├── docs/                  # Documentation
│   ├── specs/             # Technical specifications
│   └── guides/            # How-to guides
│
└── tests/                 # Test suite
```

---

## Further Reading

- **ADRs**: `.adrs/INDEX.md` - Why decisions were made
- **SPECs**: `docs/specs/INDEX.md` - What is being built
- **Contracts**: `shared/contracts/` - Data structure definitions
