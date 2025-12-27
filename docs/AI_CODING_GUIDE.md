# AI Coding Assistant Comprehensive Guide

> **Master Reference for AI-Assisted Development on Engineering Tools Platform**
> 
> Generated: 2024-12-27 | Based on ADR Analysis

---

## Table of Contents

1. [ADR Summary & Key Principles](#1-adr-summary--key-principles)
2. [Proposed New ADRs](#2-proposed-new-adrs)
3. [Project-Wide Acceptance Criteria](#3-project-wide-acceptance-criteria)
4. [Tool-Specific Acceptance Criteria](#4-tool-specific-acceptance-criteria)
5. [Tool Interaction Map](#5-tool-interaction-map)
6. [Codebase Compliance Scorecard](#6-codebase-compliance-scorecard)

---

## 1. ADR Summary & Key Principles

### 1.1 Existing ADRs Overview

| ADR ID | Title | Status | Scope | Key Decision |
|--------|-------|--------|-------|--------------|
| ADR-0001 | Hybrid FSM Stage Orchestration | Accepted | CDU-DAT | Per-stage FSMs with global orchestrator for unlock cascades |
| ADR-0002 | Artifact Preservation on Unlock | Accepted | CDU-DAT | Never delete artifacts on unlock; set locked:false only |
| ADR-0003 | Optional Context/Preview Stages | Accepted | CDU-DAT | Context and Preview are optional; Parse/Export use defaults |
| ADR-0004 | Deterministic Stage IDs | Accepted | CDU-DAT | SHA-256 hash of inputs + seed=42, 8-char prefix |
| ADR-0005 | Swagger-Driven E2E Validation | Proposed | Core | OpenAPI is single source of truth; Swagger UI as test harness |
| ADR-0006 | Table Availability | Proposed | CDU-DAT | Deterministic probe strategies; status: available/partial/missing/empty |
| ADR-0008 | Audit Trail Timestamps | Proposed | Cross-cutting | ISO-8601 UTC timestamps (no microseconds) for all lifecycle events |
| ADR-0009 | Type Safety & Contract Discipline | Proposed | Core | Pydantic contracts are Tier 0; auto-generate JSON Schema/OpenAPI |
| ADR-0010 | Docs-as-Code Engineering Tenets | Proposed | Core | MkDocs + mkdocstrings; Google-style docstrings; CI enforcement |
| ADR-0011 | Profile-Driven Extraction | Proposed | CDU-DAT | Versioned profiles; AdapterFactory pattern; catalog-driven diagnostics |
| ADR-0012 | Windows-First Concurrency | Proposed | Core | Spawn-safe API only; no raw multiprocessing/threading |
| ADR-0013 | Cancellation Semantics | Proposed | CDU-DAT | Soft cancel; preserve completed artifacts; no partial data persisted |
| ADR-0014 | Parse/Export Artifact Formats | Accepted | CDU-DAT | Parquet for parse; user-selectable formats for export |
| ADR-0015 | 3-Tier Document Model | Accepted | Core | ADRs (why) → Specs (what) → Guides (how); schema validation |
| ADR-0016 | Hybrid Semver Versioning | Accepted | Core | v0.x.x = relaxed; v1.x.x+ = strict semver; manual graduation |
| ADR-0017 | Cross-Cutting Guardrails | Accepted | Cross-cutting | Central catalog for path-safety, concurrency, message catalogs, etc. |
| ADR-0025 | DataSet Lineage Tracking | Accepted | Core | Cross-tool data lineage with parent_refs in manifests |
| ADR-0026 | Pipeline Error Handling | Accepted | Core | Error categorization, retry policies, graceful degradation |
| ADR-0028 | **Unified Rendering Engine** | **Accepted** | **Cross-cutting** | **Shared visualization/charting engine for all tools (DAT, SOV, PPTX)** |

### 1.2 Core Architectural Principles

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TIER 0: CONTRACTS                                 │
│    shared/contracts/ - Pydantic models (single source of truth)         │
│    Auto-generated: JSON Schema, OpenAPI, TypeScript clients             │
├─────────────────────────────────────────────────────────────────────────┤
│                        TIER 1: ADRs (WHY)                               │
│    .adrs/ - Architecture Decision Records                              │
│    Decision rationale, alternatives considered, guardrails             │
├─────────────────────────────────────────────────────────────────────────┤
│                        TIER 2: SPECS (WHAT)                             │
│    docs/specs/ - Technical specifications                              │
│    Contract references, API definitions, state machines                │
├─────────────────────────────────────────────────────────────────────────┤
│                        TIER 3: GUIDES (HOW)                             │
│    docs/guides/ - How-to guides and tutorials                          │
│    Step-by-step instructions, examples, workflows                      │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Cross-Cutting Guardrails (ADR-0017)

| Guardrail ID | Rule | Enforcement |
|--------------|------|-------------|
| `path-safety` | All public paths MUST be relative | `shared.path_safety.assert_relpath_safe()` |
| `concurrency` | Use spawn-safe API only; no raw multiprocessing | CI check for raw imports |
| `message-catalogs` | All user messages from catalog, not hardcoded | CI validation |
| `contract-versioning` | Breaking changes require /vN routing | OpenAPI drift detection |
| `tier-boundaries` | No content duplication across tiers | CI schema validation |
| `cancel-behavior` | Preserve artifacts; explicit cleanup only | State machine enforcement |

---

## 2. Proposed New ADRs

### 2.1 Missing PPTX Generator ADRs

#### ADR-0018: PPTX Template Processing Model (PROPOSED)

```json
{
  "id": "ADR-0018_PPTX-Template-Processing-Model",
  "title": "PowerPoint Template Processing: Named Shape Discovery and Mapping",
  "status": "proposed",
  "scope": "subsystem:PPTX",
  "decision_primary": "PPTX Generator uses named shape discovery to identify template placeholders. Templates MUST use PowerPoint's built-in naming feature. Shape names follow convention: {category}_{identifier} (e.g., chart_revenue, text_title). The mapping engine validates all required shapes exist before generation.",
  "key_constraints": [
    "Templates MUST be .pptx format with named shapes",
    "Shape names MUST follow {category}_{identifier} convention",
    "Categories: text, chart, table, image, metric",
    "Validation MUST fail if required shapes are missing",
    "Orphan shapes (unmapped) generate warnings, not errors"
  ],
  "guardrails": [
    {
      "rule": "All template shapes MUST have unique names within a slide",
      "enforcement": "Backend validation on template upload"
    },
    {
      "rule": "Shape name validation MUST be deterministic",
      "enforcement": "Unit tests with fixed template corpus"
    }
  ]
}
```

#### ADR-0019: PPTX Data Mapping Workflow (PROPOSED)

```json
{
  "id": "ADR-0019_PPTX-Data-Mapping-Workflow",
  "title": "PPTX Generator 7-Step Guided Workflow",
  "status": "proposed",
  "scope": "subsystem:PPTX",
  "decision_primary": "PPTX Generator enforces a 7-step workflow: (1) Upload Template, (2) Configure Environment, (3) Upload Data, (4) Map Context, (5) Map Metrics, (6) Validate, (7) Generate. Each step has completion criteria. Users cannot skip mandatory steps but can revisit completed steps.",
  "key_constraints": [
    "Steps 1-3 are sequential prerequisites",
    "Steps 4-5 can be done in any order after Step 3",
    "Step 6 (Validate) requires Steps 1-5 complete",
    "Step 7 (Generate) requires Step 6 to show 'Four Green Bars'",
    "State persists per project; users can resume workflows"
  ],
  "guardrails": [
    {
      "rule": "Generate button MUST be disabled until validation passes",
      "enforcement": "Frontend disables button; backend rejects premature requests"
    }
  ]
}
```

#### ADR-0020: PPTX Domain Configuration (PROPOSED)

```json
{
  "id": "ADR-0020_PPTX-Domain-Configuration",
  "title": "PPTX Generator Domain-Specific Configuration",
  "status": "proposed",
  "scope": "subsystem:PPTX",
  "decision_primary": "PPTX Generator uses domain configuration files (YAML/JSON) to define job contexts, canonical metrics, and rendering rules. Configuration is loaded at startup and validated against a Pydantic schema. Invalid configurations fail startup.",
  "key_constraints": [
    "Domain config MUST be validated at startup",
    "Config changes require restart (no hot-reload)",
    "Config files: apps/pptx_generator/config/domain_config.yaml",
    "All metric aliases MUST map to canonical metrics"
  ]
}
```

#### ADR-0021: PPTX Renderer Architecture (PROPOSED)

```json
{
  "id": "ADR-0021_PPTX-Renderer-Architecture",
  "title": "PPTX Generator Pluggable Renderer System",
  "status": "proposed",
  "scope": "subsystem:PPTX",
  "decision_primary": "PPTX Generator uses a pluggable renderer system where each shape category (text, chart, table, image) has a dedicated renderer class. Renderers are selected via a registry pattern. Custom renderers can be added without modifying core code.",
  "key_constraints": [
    "Each renderer implements a common interface",
    "Renderer selection is based on shape category",
    "Renderers MUST NOT modify template structure (only fill placeholders)",
    "Failed renders log errors but do not abort generation"
  ]
}
```

### 2.2 Missing SOV Analyzer ADRs

#### ADR-0022: SOV Analysis Pipeline (PROPOSED)

```json
{
  "id": "ADR-0022_SOV-Analysis-Pipeline",
  "title": "SOV Analyzer ANOVA-Based Analysis Pipeline",
  "status": "proposed",
  "scope": "subsystem:SOV",
  "decision_primary": "SOV Analyzer performs Source of Variation analysis using ANOVA methodology. The pipeline consists of: (1) Data ingestion, (2) Factor identification, (3) ANOVA computation, (4) Variance decomposition, (5) Result visualization. All computations use Polars for performance.",
  "key_constraints": [
    "Input data MUST have at least one factor column and one response column",
    "ANOVA computation uses Type III sum of squares",
    "Results include: SS, df, MS, F-statistic, p-value per factor",
    "Variance contribution percentages MUST sum to 100%"
  ],
  "guardrails": [
    {
      "rule": "All statistical computations MUST be deterministic",
      "enforcement": "Fixed random seed; reproducibility tests"
    }
  ]
}
```

#### ADR-0023: SOV DataSet Integration (PROPOSED)

```json
{
  "id": "ADR-0023_SOV-DataSet-Integration",
  "title": "SOV Analyzer Integration with Platform DataSets",
  "status": "proposed",
  "scope": "subsystem:SOV",
  "decision_primary": "SOV Analyzer consumes DataSets from the shared artifact store. Input DataSets are loaded via DataSetRef. Output results are saved as new DataSets with lineage tracking back to input DataSet.",
  "key_constraints": [
    "SOV MUST accept DataSetRef as input (not raw file uploads)",
    "Output DataSet MUST include parent_ref linking to input",
    "SOV results saved as Parquet with manifest.json",
    "Column metadata MUST be preserved from input DataSet"
  ]
}
```

#### ADR-0024: SOV Visualization Contracts (PROPOSED)

```json
{
  "id": "ADR-0024_SOV-Visualization-Contracts",
  "title": "SOV Analyzer Visualization Data Contracts",
  "status": "proposed",
  "scope": "subsystem:SOV",
  "decision_primary": "SOV Analyzer outputs visualization-ready data contracts for frontend rendering. Contracts include: VarianceBarChart, ParetoChart, MainEffectsPlot, InteractionPlot. Each contract is a Pydantic model with typed fields for chart configuration.",
  "key_constraints": [
    "All visualization contracts defined in shared/contracts/sov/",
    "Contracts include both data and chart metadata",
    "Frontend renders from contracts; no additional computation",
    "Chart types: bar, pareto, line, heatmap"
  ]
}
```

### 2.3 Missing Cross-Tool ADRs

#### ADR-0025: DataSet Lineage Tracking (PROPOSED)

```json
{
  "id": "ADR-0025_DataSet-Lineage-Tracking",
  "title": "Cross-Tool DataSet Lineage and Provenance",
  "status": "proposed",
  "scope": "core",
  "decision_primary": "All DataSets track their lineage via parent_ref and source_tool fields in the manifest. Lineage is immutable once created. The gateway provides a /lineage endpoint to retrieve the full lineage graph for any DataSet.",
  "key_constraints": [
    "DataSetManifest MUST include parent_ref (nullable for root datasets)",
    "DataSetManifest MUST include source_tool enum (dat, sov, pptx, external)",
    "Lineage is append-only; no modification of historical lineage",
    "Circular lineage references MUST be rejected"
  ]
}
```

#### ADR-0026: Pipeline Error Handling (PROPOSED)

```json
{
  "id": "ADR-0026_Pipeline-Error-Handling",
  "title": "Multi-Tool Pipeline Error Handling Strategy",
  "status": "proposed",
  "scope": "core",
  "decision_primary": "Pipeline execution follows fail-fast semantics: if any step fails, subsequent steps are skipped. Partial results from completed steps are preserved. Pipelines can be resumed from the last successful step.",
  "key_constraints": [
    "Step failures set pipeline status to 'failed'",
    "Completed step outputs are preserved as DataSets",
    "Resume requires explicit user action (not automatic)",
    "Each step logs: start_time, end_time, status, error_message"
  ]
}
```

---

## 3. Project-Wide Acceptance Criteria

### 3.1 Code Quality ACs

| AC ID | Criterion | Verification Method | Priority |
|-------|-----------|---------------------|----------|
| CQ-001 | All Python code MUST pass Ruff linting | `ruff check .` exits 0 | P0 |
| CQ-002 | All Python functions MUST have type hints | `mypy --strict` | P0 |
| CQ-003 | All public functions MUST have Google-style docstrings | `ruff check --select D` | P1 |
| CQ-004 | TypeScript code MUST pass ESLint | `npm run lint` exits 0 | P0 |
| CQ-005 | All TypeScript components MUST have typed props | TSC strict mode | P0 |
| CQ-006 | No `any` types in TypeScript without justification | ESLint rule | P1 |

### 3.2 Contract Discipline ACs

| AC ID | Criterion | Verification Method | Priority |
|-------|-----------|---------------------|----------|
| CD-001 | All API contracts MUST be Pydantic models in shared/contracts/ | Code review | P0 |
| CD-002 | Contracts MUST NOT be duplicated in ADRs/Specs/Guides | CI tier boundary check | P0 |
| CD-003 | All contracts MUST have __version__ attribute | CI contract scan | P0 |
| CD-004 | Breaking changes MUST bump major version (v1.x.x+) | CI drift detection | P0 |
| CD-005 | JSON Schema MUST be auto-generated from Pydantic | tools/gen_json_schema.py | P1 |
| CD-006 | OpenAPI MUST be generated from FastAPI | /openapi.json endpoint | P0 |

### 3.3 API Design ACs

| AC ID | Criterion | Verification Method | Priority |
|-------|-----------|---------------------|----------|
| API-001 | All endpoints MUST use /vN versioned routing | Route inspection | P0 |
| API-002 | All endpoints MUST return Pydantic models | Response model validation | P0 |
| API-003 | Error responses MUST use standard error schema | Contract test | P0 |
| API-004 | All public paths MUST be relative (path-safety) | `assert_relpath_safe()` | P0 |
| API-005 | All mutating requests MUST be idempotent or retriable | Documentation + tests | P1 |
| API-006 | Health endpoints MUST exist at /health | Integration test | P0 |

### 3.4 Testing ACs

| AC ID | Criterion | Verification Method | Priority |
|-------|-----------|---------------------|----------|
| TEST-001 | All API endpoints MUST have integration tests | pytest coverage | P0 |
| TEST-002 | Contract tests MUST validate schema compliance | test_contracts.py | P0 |
| TEST-003 | Stage ID generation MUST be tested for determinism | test_stage_id.py | P0 |
| TEST-004 | Windows concurrency MUST be tested | CI on Windows | P1 |
| TEST-005 | Cancellation behavior MUST be tested | test_cancel_behavior.py | P1 |

### 3.5 Documentation ACs

| AC ID | Criterion | Verification Method | Priority |
|-------|-----------|---------------------|----------|
| DOC-001 | All ADRs MUST follow adr_schema.json | CI schema validation | P0 |
| DOC-002 | All Specs MUST follow tech_spec.schema.json | CI schema validation | P0 |
| DOC-003 | ADRs MUST NOT contain code snippets | Tier boundary check | P0 |
| DOC-004 | README MUST include Quick Start | Manual review | P0 |
| DOC-005 | All public APIs MUST be in OpenAPI docs | /docs endpoint | P0 |

### 3.6 Artifact Management ACs

| AC ID | Criterion | Verification Method | Priority |
|-------|-----------|---------------------|----------|
| ART-001 | Unlock MUST preserve artifacts (never delete) | test_artifact_preservation.py | P0 |
| ART-002 | Stage IDs MUST be deterministic (SHA-256) | test_stage_id.py | P0 |
| ART-003 | Timestamps MUST be ISO-8601 UTC (no microseconds) | Contract validation | P0 |
| ART-004 | Parse stage MUST output Parquet format | test_parse_output.py | P0 |
| ART-005 | All manifests MUST include created_at timestamp | Contract test | P0 |

---

## 4. Tool-Specific Acceptance Criteria

### 4.1 Data Aggregator (DAT) ACs

| AC ID | Criterion | ADR Reference | Priority |
|-------|-----------|---------------|----------|
| DAT-001 | FSM MUST enforce forward gating (upstream locks required) | ADR-0001 | P0 |
| DAT-002 | Unlock MUST cascade to downstream stages | ADR-0001 | P0 |
| DAT-003 | Context and Preview stages MUST be optional | ADR-0003 | P0 |
| DAT-004 | Parse MUST use profile defaults if context.json missing | ADR-0003 | P0 |
| DAT-005 | Table availability MUST use status: available/partial/missing/empty | ADR-0006 | P0 |
| DAT-006 | Extraction MUST be profile-driven | ADR-0011 | P0 |
| DAT-007 | Adapters MUST be selected via AdapterFactory | ADR-0011 | P0 |
| DAT-008 | Cancel MUST preserve completed artifacts | ADR-0013 | P0 |
| DAT-009 | Cancel MUST NOT persist partial tables/rows | ADR-0013 | P0 |
| DAT-010 | Parse output MUST be Parquet | ADR-0014 | P0 |
| DAT-011 | Export MUST support user-selectable formats | ADR-0014 | P1 |

### 4.2 PPTX Generator ACs

| AC ID | Criterion | ADR Reference | Priority |
|-------|-----------|---------------|----------|
| PPTX-001 | Templates MUST use named shapes for placeholders | ADR-0018 (proposed) | P0 |
| PPTX-002 | 7-step workflow MUST be enforced | ADR-0019 (proposed) | P0 |
| PPTX-003 | Generate MUST be disabled until validation passes | ADR-0019 (proposed) | P0 |
| PPTX-004 | Domain config MUST be validated at startup | ADR-0020 (proposed) | P0 |
| PPTX-005 | Renderers MUST implement common interface | ADR-0021 (proposed) | P0 |
| PPTX-006 | DataSet input MUST be supported (in addition to file upload) | Platform integration | P1 |
| PPTX-007 | Generated PPTX MUST be downloadable via API | API contract | P0 |
| PPTX-008 | All user messages MUST come from message catalog | ADR-0017 | P1 |

### 4.3 SOV Analyzer ACs

| AC ID | Criterion | ADR Reference | Priority |
|-------|-----------|---------------|----------|
| SOV-001 | ANOVA computation MUST use Type III sum of squares | ADR-0022 (proposed) | P0 |
| SOV-002 | Variance percentages MUST sum to 100% | ADR-0022 (proposed) | P0 |
| SOV-003 | Input MUST accept DataSetRef from artifact store | ADR-0023 (proposed) | P0 |
| SOV-004 | Output MUST save results as DataSet with lineage | ADR-0023 (proposed) | P0 |
| SOV-005 | Visualization contracts MUST be Pydantic models | ADR-0024 (proposed) | P0 |
| SOV-006 | All computations MUST be deterministic | ADR-0012 | P0 |
| SOV-007 | Health endpoint MUST exist at /health | API standard | P0 |

### 4.4 Gateway ACs

| AC ID | Criterion | ADR Reference | Priority |
|-------|-----------|---------------|----------|
| GW-001 | All tool APIs MUST be mounted under /api/{tool}/ | Architecture | P0 |
| GW-002 | Cross-tool DataSet API MUST exist at /api/v1/datasets | Platform design | P0 |
| GW-003 | Pipeline API MUST exist at /api/v1/pipelines | Platform design | P0 |
| GW-004 | Health endpoint MUST report tool availability | Observability | P0 |
| GW-005 | CORS MUST be configured for development ports | Security | P0 |
| GW-006 | OpenAPI docs MUST be available at /docs | API standard | P0 |

---

## 5. Tool Interaction Map

### 5.1 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACE                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Homepage   │  │    DAT UI   │  │   SOV UI    │  │  PPTX UI    │        │
│  │  :3000      │  │   :5173     │  │   :5174     │  │   :5175     │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (:8000)                                  │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  Cross-Tool APIs                                                      │   │
│  │  POST /api/v1/datasets     - Create/list DataSets                    │   │
│  │  POST /api/v1/pipelines    - Create/execute pipelines                │   │
│  │  GET  /health              - Platform health                          │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐                 │
│  │ /api/dat/*     │  │ /api/sov/*     │  │ /api/pptx/*    │                 │
│  │ DAT Backend    │  │ SOV Backend    │  │ PPTX Backend   │                 │
│  │ (mounted)      │  │ (mounted)      │  │ (mounted)      │                 │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘                 │
└──────────┼───────────────────┼───────────────────┼──────────────────────────┘
           │                   │                   │
           ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SHARED INFRASTRUCTURE                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  shared/contracts/         - Pydantic models (Tier 0)                   ││
│  │  shared/storage/           - ArtifactStore (Parquet + manifest)         ││
│  │  shared/utils/             - Stage ID, path safety                      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  workspace/                                                              ││
│  │  ├── datasets/             - Shared DataSets (Parquet + manifest.json)  ││
│  │  ├── pipelines/            - Pipeline definitions and state             ││
│  │  └── tools/                                                              ││
│  │      ├── dat/              - DAT stage artifacts                        ││
│  │      ├── sov/              - SOV analysis results                       ││
│  │      └── pptx/             - PPTX projects and generated files          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Tool Interaction Specifications

#### 5.2.1 DAT → SOV Integration

| Interaction | Description | Contract |
|-------------|-------------|----------|
| **Output** | DAT exports DataSet to shared store | `DataSetManifest` with Parquet file |
| **Input** | SOV loads DataSet via `DataSetRef` | `DataSetRef.id` resolves to manifest |
| **Lineage** | SOV output includes `parent_ref` | `DataSetManifest.parent_ref = input.id` |
| **Column Metadata** | SOV inherits column metadata | `ColumnMeta` preserved from input |

**Sequence:**
```
DAT: Export Stage → Save dataset.parquet + manifest.json
     └──► workspace/datasets/{dataset_id}/
          ├── dataset.parquet
          └── manifest.json (includes column_meta)

SOV: Load DataSet → Read manifest.json → Load dataset.parquet
     └──► Validate columns match expected schema
     └──► Perform ANOVA analysis
     └──► Save results as new DataSet with parent_ref
```

#### 5.2.2 SOV → PPTX Integration

| Interaction | Description | Contract |
|-------------|-------------|----------|
| **Output** | SOV saves analysis results as DataSet | `DataSetManifest` with viz-ready data |
| **Input** | PPTX loads DataSet in Step 3 | Via "Load from DataSet" UI option |
| **Mapping** | PPTX maps DataSet columns to template shapes | Context/Metric mapping workflow |
| **Rendering** | PPTX renders charts from SOV visualization contracts | Chart renderers consume typed data |

**Sequence:**
```
SOV: Analysis Complete → Save results DataSet
     └──► workspace/datasets/{sov_result_id}/
          ├── results.parquet (variance decomposition, etc.)
          └── manifest.json (includes viz_contracts)

PPTX: Step 3 (Upload Data) → "Load from DataSet" option
      └──► List available DataSets from /api/v1/datasets
      └──► User selects SOV result DataSet
      └──► Load Parquet into PPTX data model
      └──► Proceed to Step 4 (Map Context)
```

#### 5.2.3 DAT → PPTX Integration

| Interaction | Description | Contract |
|-------------|-------------|----------|
| **Output** | DAT exports cleaned/aggregated DataSet | `DataSetManifest` with tabular data |
| **Input** | PPTX loads DataSet for report generation | Via "Load from DataSet" UI |
| **Mapping** | PPTX maps columns to template placeholders | Standard mapping workflow |

#### 5.2.4 Pipeline Orchestration

**Pipeline Definition Contract:**
```yaml
# Pipeline: Data → Analysis → Report
name: "Weekly SOV Report"
steps:
  - id: step_0
    tool: dat
    action: export
    params:
      profile: weekly_fab_data
    output: aggregated_data

  - id: step_1
    tool: sov
    action: analyze
    params:
      factors: ["lot", "wafer", "step"]
      response: "yield"
    input: $step_0.output
    output: sov_results

  - id: step_2
    tool: pptx
    action: generate
    params:
      template_id: "weekly_report_template"
    input: $step_1.output
    output: report.pptx
```

**Pipeline Execution Flow:**
```
Gateway: POST /api/v1/pipelines/execute
         │
         ├──► Validate pipeline definition
         │    └── Check all tools available
         │    └── Validate input/output references
         │
         ├──► Step 0: POST /api/dat/api/v1/export
         │    └── Save DataSet → workspace/datasets/step_0_output/
         │
         ├──► Step 1: POST /api/sov/api/v1/analyze
         │    └── Load step_0_output DataSet
         │    └── Run ANOVA
         │    └── Save DataSet → workspace/datasets/step_1_output/
         │
         └──► Step 2: POST /api/pptx/api/v1/generation
              └── Load step_1_output DataSet
              └── Apply template mapping
              └── Generate PPTX → workspace/tools/pptx/step_2_output.pptx
```

---

## 6. Codebase Compliance Scorecard

### 6.1 Overall Score: **62/100** (Developing)

### 6.2 Category Scores

| Category | Score | Max | Status |
|----------|-------|-----|--------|
| **Contract Discipline** | 12/20 | 20 | 🟡 Partial |
| **API Design** | 14/20 | 20 | 🟡 Partial |
| **Testing** | 8/15 | 15 | 🟡 Partial |
| **Documentation** | 10/15 | 15 | 🟡 Partial |
| **Artifact Management** | 10/15 | 15 | 🟡 Partial |
| **Cross-Tool Integration** | 8/15 | 15 | 🟡 Partial |

### 6.3 Detailed Findings

#### 6.3.1 Contract Discipline (12/20)

| Criterion | Status | Notes |
|-----------|--------|-------|
| Pydantic contracts in shared/contracts/ | ✅ | Core contracts exist |
| Contracts have __version__ | ⚠️ | Not all contracts versioned |
| JSON Schema auto-generation | ❌ | tools/gen_json_schema.py not found |
| OpenAPI generation | ✅ | FastAPI provides /openapi.json |
| No contract duplication in docs | ✅ | ADRs use references |
| Tier boundary enforcement | ⚠️ | CI validation not implemented |

**Gaps:**
- Missing `tools/gen_json_schema.py`
- Missing `tools/gen_openapi.py`
- Contract versioning incomplete
- CI tier boundary validation not found

#### 6.3.2 API Design (14/20)

| Criterion | Status | Notes |
|-----------|--------|-------|
| /vN versioned routing | ⚠️ | PPTX has /api/v1/, others inconsistent |
| Pydantic response models | ✅ | FastAPI enforces |
| Standard error schema | ⚠️ | Not standardized |
| Path safety enforcement | ⚠️ | `shared/path_safety.py` not found |
| Health endpoints | ✅ | All tools have /health |
| CORS configuration | ✅ | Configured for dev |

**Gaps:**
- Gateway datasets/pipelines use /v1/ but tools inconsistent
- Missing standardized error response contract
- Path safety utilities not implemented

#### 6.3.3 Testing (8/15)

| Criterion | Status | Notes |
|-----------|--------|-------|
| API integration tests | ⚠️ | test_all_endpoints.py exists, incomplete |
| Contract tests | ✅ | test_contracts.py exists |
| Stage ID determinism tests | ✅ | test_stage_id.py exists |
| Windows CI | ⚠️ | Scripts exist, CI not verified |
| Cancellation tests | ❌ | Not found |

**Gaps:**
- Missing comprehensive cancellation behavior tests
- Missing artifact preservation tests
- Windows CI pipeline not verified

#### 6.3.4 Documentation (10/15)

| Criterion | Status | Notes |
|-----------|--------|-------|
| ADRs follow schema | ✅ | All 16 ADRs in JSON format |
| 3-tier separation | ✅ | Tiers defined |
| Quick Start in README | ✅ | Present |
| OpenAPI docs accessible | ✅ | /docs endpoint works |
| CONTRIBUTING.md | ✅ | Comprehensive |

**Gaps:**
- Missing ADR schema validation in CI
- Missing tool-specific ADRs (PPTX, SOV)
- Spec tier mostly empty

#### 6.3.5 Artifact Management (10/15)

| Criterion | Status | Notes |
|-----------|--------|-------|
| Artifact preservation on unlock | ⚠️ | Logic exists in ADRs, implementation unclear |
| Deterministic stage IDs | ✅ | shared/utils/stage_id.py exists |
| ISO-8601 timestamps | ⚠️ | Not universally enforced |
| Parquet for parse output | ⚠️ | DAT uses Parquet, not verified end-to-end |
| Manifest contracts | ✅ | DataSetManifest defined |

**Gaps:**
- Artifact preservation tests missing
- Timestamp format not validated in contracts
- Parse stage Parquet output not fully verified

#### 6.3.6 Cross-Tool Integration (8/15)

| Criterion | Status | Notes |
|-----------|--------|-------|
| DataSet sharing via gateway | ✅ | /api/v1/datasets implemented |
| Pipeline orchestration | ⚠️ | Pipeline service exists, execution not tested |
| Lineage tracking | ❌ | parent_ref not implemented |
| PPTX DataSet input | ⚠️ | dataset_input.py exists, integration unclear |
| SOV DataSet integration | ❌ | SOV tool minimal, no DataSet integration |

**Gaps:**
- SOV Analyzer is skeleton only
- Lineage tracking not implemented
- Pipeline execution not end-to-end tested

### 6.4 Priority Remediation Roadmap

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P0 | Implement path safety utilities | Low | High |
| P0 | Add contract __version__ to all contracts | Low | Medium |
| P0 | Standardize error response contract | Medium | High |
| P0 | Create tool-specific ADRs (PPTX-0018-0021) | Medium | High |
| P1 | Implement JSON Schema generation tooling | Medium | Medium |
| P1 | Add artifact preservation tests | Medium | High |
| P1 | Implement SOV DataSet integration | High | High |
| P1 | Add lineage tracking to DataSetManifest | Medium | Medium |
| P2 | Implement CI tier boundary validation | Medium | Low |
| P2 | Add Windows CI pipeline | Medium | Medium |

---

## 7. AI Coding Assistant Quick Reference

### 7.1 Before Writing Code

1. **Check for existing contracts** in `shared/contracts/`
2. **Review relevant ADRs** in `.adrs/`
3. **Verify no tier boundary violations** (don't duplicate contracts in docs)
4. **Check cross-cutting guardrails** in ADR-0017

### 7.2 Code Patterns to Follow

```python
# ✅ CORRECT: Type hints + docstring
def compute_stage_id(inputs: dict[str, Any], seed: int = 42) -> str:
    """Compute deterministic stage ID from inputs.
    
    Args:
        inputs: Dictionary of stage inputs.
        seed: Random seed for determinism.
    
    Returns:
        8-character SHA-256 hash prefix.
    """
    ...

# ❌ WRONG: Missing type hints
def compute_stage_id(inputs, seed=42):
    ...
```

```python
# ✅ CORRECT: Using contracts from shared/
from shared.contracts import DataSetManifest, DataSetRef

# ❌ WRONG: Defining inline Pydantic model
class DataSetManifest(BaseModel):  # Don't duplicate!
    ...
```

### 7.3 Common Pitfalls to Avoid

| Pitfall | Correct Approach |
|---------|------------------|
| Using absolute file paths in API responses | Use relative paths; call `assert_relpath_safe()` |
| Deleting artifacts on unlock/cancel | Set `locked: false`; preserve files |
| Using raw `multiprocessing` | Use spawn-safe concurrency API |
| Hardcoding user messages | Use message catalog |
| Adding `__version__` to non-contract modules | Only Pydantic contracts need `__version__` |

### 7.4 Testing Checklist

- [ ] Unit tests for new functions
- [ ] Contract tests if adding/modifying Pydantic models
- [ ] Determinism tests if adding computation logic
- [ ] Integration tests for new API endpoints
- [ ] Run `ruff check .` before committing
- [ ] Run `pytest tests/` to verify all tests pass

---

*This document is auto-generated from ADR analysis and should be updated when ADRs change.*
