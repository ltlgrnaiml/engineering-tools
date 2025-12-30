# Tier 1: Engineering Tools Platform Vision

**Document Type:** Vision & Strategy  
**Audience:** Architects, Product Managers, Senior Engineers  
**Last Updated:** 2025-01-26

---

## Executive Summary

The Engineering Tools Platform is a unified monorepo providing semiconductor manufacturing engineers with integrated data analysis and reporting tools. The platform enables seamless data flow between tools, reducing manual data transfer and enabling complex multi-stage workflows.

---

## Platform Vision

### Mission Statement

> Provide 30-50 semiconductor engineers with a cohesive, locally-deployable suite of analysis tools that work together seamlessly, enabling data-driven decision making through automated aggregation, statistical analysis, and professional report generation.

### Core Principles

1. **Data Flows Freely** - Tools produce and consume standardized DataSets, enabling piping workflows
2. **Solo-Dev Sustainable** - Architecture supports single-developer maintenance with strong CI guardrails
3. **Local-First** - All tools run locally on engineer workstations (Windows primary, Mac secondary)
4. **Contract-Driven** - Pydantic contracts are the single source of truth (per ADR-0010)
5. **Fail-Safe** - Artifacts are preserved on cancel/unlock (per ADR-0002, ADR-0014)

---

## Platform Goals

### G1: Unified Tool Access
Engineers access all tools from a single homepage that displays tool status, recent work, and available DataSets.

### G2: Cross-Tool Data Piping
Data flows between tools without manual export/import. A DataSet created in the Data Aggregator can be directly piped to SOV Analyzer or PowerPoint Generator.

### G3: Pipeline Orchestration
Multi-step workflows (DAT → SOV → PPTX) can be defined and executed as pipelines with progress tracking and error recovery.

### G4: Shared Artifact Storage
All tools read/write from a common artifact store with lineage tracking, enabling reproducibility and audit trails.

### G5: Consistent UX
All tools share common UI components (DataSet picker, progress indicators, error handling) for a cohesive user experience.

---

## Acceptance Criteria (Platform-Level)

### AC-P1: Homepage Functional
- [ ] Homepage displays all available tools with status indicators
- [ ] Homepage shows recent DataSets across all tools
- [ ] Tools can be launched from homepage
- [ ] Health check shows tool availability

### AC-P2: DataSet Universality
- [ ] DataSets are stored in Parquet format with JSON manifests
- [ ] All tools can list, read, and preview DataSets
- [ ] DataSet lineage (parent/child relationships) is tracked
- [ ] DataSets have deterministic IDs (per ADR-0005)

### AC-P3: Cross-Tool Piping
- [ ] DAT can pipe output to SOV or PPTX
- [ ] SOV can pipe output to PPTX
- [ ] "Pipe To" button available after any tool's export stage
- [ ] Receiving tool pre-populates with piped DataSet

### AC-P4: Pipeline Execution
- [ ] Pipelines can be created with multiple steps
- [ ] Pipeline steps execute sequentially
- [ ] Pipeline state is tracked (pending/running/completed/failed)
- [ ] Cancellation preserves completed artifacts (per ADR-0014)

### AC-P5: Gateway Routing
- [ ] Single API gateway routes to all tools
- [ ] Cross-tool APIs (datasets, pipelines) at gateway level
- [ ] Health check aggregates tool status
- [ ] OpenAPI docs available at /api/docs

### AC-P6: CI/CD Pipeline
- [ ] Type checking (mypy strict) passes
- [ ] Linting (ruff) passes
- [ ] Contract drift detection works
- [ ] All tests pass
- [ ] Documentation builds successfully

---

## Tools Overview

| Tool | Status | Primary Function |
|------|--------|------------------|
| **Homepage** | Phase 2 | Tool launcher, DataSet browser, pipeline builder |
| **Data Aggregator** | Phase 3 | Multi-source data extraction and aggregation |
| **PowerPoint Generator** | Phase 2 | Template-based report generation |
| **SOV Analyzer** | Phase 4 | Source of Variation (ANOVA) analysis |

### Tool Interaction Matrix

```
                    ┌──────────────┐
                    │   Homepage   │
                    │  (Launcher)  │
                    └──────┬───────┘
                           │ launches
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │     DAT      │ │     SOV      │ │     PPTX     │
    │ (Aggregator) │ │  (Analyzer)  │ │ (Generator)  │
    └──────┬───────┘ └──────┬───────┘ └──────────────┘
           │                │                ▲
           │   DataSet      │   DataSet      │
           ├────────────────┼────────────────┤
           │                │                │
           └────────────────┴────────────────┘
                    pipes to
```

---

## Architecture Layers

### Layer 0: Shared Contracts (`shared/contracts/`)
Per ADR-0010, Pydantic models are the source of truth:
- `DataSetManifest` - Universal data format
- `Pipeline` - Multi-tool workflow definition
- `ArtifactRecord` - Registry entry for tracking

### Layer 1: Shared Storage (`shared/storage/`)
- `ArtifactStore` - Parquet/JSON I/O for DataSets
- `RegistryDB` - SQLite artifact registry

### Layer 2: Gateway (`gateway/`)
- FastAPI router mounting tool APIs
- Cross-tool services (datasets, pipelines)
- Health check aggregation

### Layer 3: Tools (`apps/`)
- Independent FastAPI apps per tool
- Tool-specific frontend SPAs
- Tool-specific ADRs and docs

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Backend | Python 3.11+, FastAPI, Pydantic | Type safety, async, contract-driven |
| Data | Polars, Parquet, PyArrow | Performance, columnar storage |
| Database | SQLite (aiosqlite) | Local-first, zero config |
| Frontend | React, TypeScript, Vite | Modern, fast, type-safe |
| UI Components | TailwindCSS, shadcn/ui | Consistent styling |
| Testing | pytest, pytest-asyncio | Async-native testing |
| CI | PowerShell scripts, Azure DevOps | Windows-first (per ADR-0013) |
| Docs | MkDocs, mkdocstrings | Docs-as-code (per ADR-0011) |

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [x] Monorepo structure created
- [x] Shared contracts defined
- [x] Artifact storage implemented
- [x] Gateway skeleton with cross-tool APIs
- [x] ADRs migrated (16 ADRs in .adrs/)
- [ ] CI pipeline configured
- [ ] Basic test suite

### Phase 2: Homepage + PPTX Migration (Week 2-3)
- [x] Homepage frontend with tool grid
- [x] DataSet browser component
- [x] Migrate PowerPointGenerator to apps/pptx_generator/
- [x] Update PPTX to use shared contracts
- [x] Shared UI components (DataSetPicker, PipeToButton, DataSetCard)
- [x] Pipeline builder page
- [ ] PPTX accepts DataSet inputs
- [ ] DataSetDetailsPage
- [ ] PipelineDetailsPage

### Phase 3: Data Aggregator (Week 3-5)
- [x] DAT backend with FSM orchestration (per ADR-0001)
- [x] Stage implementations (Selection → Parse → Export)
- [x] Core state machine and run manager
- [x] File adapters (CSV, Excel, Parquet)
- [x] API routes implemented
- [ ] DAT frontend with stage panels
- [ ] DataSet export with lineage
- [ ] "Pipe To" integration

### Phase 4: SOV Analyzer (Week 5-6)
- [x] SOV backend with ANOVA implementation
- [x] API routes implemented
- [ ] SOV accepts DataSet inputs
- [ ] SOV produces analysis DataSets
- [ ] SOV frontend with configuration
- [ ] Integration with PPTX for reports

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Tool Launch Time | < 5 seconds | Time from click to tool ready |
| DataSet Preview | < 2 seconds | Time to display 100 rows |
| Pipeline Step | < 30 seconds | Average step execution time |
| CI Pass Rate | > 95% | Percentage of green builds |
| Type Coverage | 100% | mypy strict mode compliance |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Scope creep | Strict acceptance criteria, phased rollout |
| Integration complexity | Contract-first design, shared storage |
| Solo-dev burnout | Strong CI guardrails, incremental progress |
| Windows compatibility | Windows-first testing (per ADR-0013) |
| Data loss on cancel | Artifact preservation (per ADR-0002, ADR-0014) |

---

## ADR References

| ADR | Topic | Application |
|-----|-------|-------------|
| ADR-0001 | Hybrid FSM Orchestration | DAT stage lifecycle |
| ADR-0002 | Artifact Preservation | All tools preserve on unlock |
| ADR-0005 | Deterministic IDs | DataSet and Pipeline IDs |
| ADR-0009 | Audit Trail Timestamps | All artifacts timestamped |
| ADR-0010 | Type Safety | Pydantic contracts |
| ADR-0011 | Docs-as-Code | MkDocs documentation |
| ADR-0013 | Windows-First | CI and concurrency |
| ADR-0014 | Cancellation Semantics | Pipeline cancel behavior |
| ADR-0015 | Artifact Formats | Parquet + JSON |
| ADR-0016 | 3-Tier Document Model | Documentation structure |
| ADR-0017 | Hybrid Semver | Contract versioning |
| ADR-0018 | Cross-Cutting Guardrails | Path safety, concurrency |

---

## Next Steps

1. Review and approve this vision document
2. Proceed to Tier 2 for integration details
3. Review Tier 3 for individual tool specs
4. Execute from Tier 4 step-by-step instructions
