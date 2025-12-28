# ADR Index: Engineering Tools Platform

> **Status**: This is the authoritative, cohesive set of Architectural Decision Records (ADRs) for the Engineering Tools platform. All code creation and modifications must align with these ADRs.

## ADR Hierarchy

```
Tier 0: Contracts (Pydantic in shared/contracts/) - SOURCE OF TRUTH
  ↓
Tier 1: ADRs (WHY) - This document
  ↓
Tier 2: Specs (WHAT) - Implementation specifications
  ↓
Tier 3: Guides (HOW) - Developer guides
```

## Core ADRs (Platform-Wide)

These ADRs define patterns that ALL tools (DAT, PPTX, SOV) MUST follow:

| ID | Title | Scope | Purpose |
|----|-------|-------|---------|
| ADR-0001 | Hybrid FSM Architecture for Guided Workflow Orchestration | core | Unified state machine pattern for all guided workflows |
| ADR-0002 | Artifact Preservation on Unlock | shared | Never delete user work on state changes |
| ADR-0004 | Deterministic Content-Addressed IDs | core | SHA-256 hash-based IDs for reproducibility |
| ADR-0005 | Swagger/OpenAPI as Executable Contract | core | API contracts validated via Swagger UI |
| ADR-0008 | Audit Trail Timestamps | core | ISO-8601 UTC timestamps for all artifacts |
| ADR-0009 | Type-Safety & Contract Discipline | core | Pydantic-first contracts as Tier 0 |
| ADR-0010 | Docs-as-Code Engineering Tenets | core | MkDocs, docstrings, CI enforcement |
| ADR-0012 | Cross-Platform Concurrency | core | Unified async, threading, process parallelism for all OS |
| ADR-0015 | 3-Tier Document Model | core | ADRs → Specs → Guides separation |
| ADR-0016 | Hybrid Semver Contract Versioning | core | Pre-1.0 iteration, post-1.0 strict semver |
| ADR-0017 | Cross-Cutting Guardrails | cross-cutting | Shared constraints: path safety, concurrency, etc. |
| ADR-0025 | DataSet Lineage Tracking | core | Cross-tool data lineage |
| ADR-0026 | Pipeline Error Handling | core | Unified error handling patterns |
| **ADR-0028** | **Unified Rendering Engine** | **cross-cutting** | **Shared visualization, charting, and rendering for all tools** |
| **ADR-0029** | **API Versioning and Endpoint Naming** | **core** | **Two-tier versioning: /api/v1/{resource} for gateway, /api/{tool}/v1/{resource} for tools** |
| **ADR-0030** | **Documentation Lifecycle Management** | **core** | **5-category doc classification, archival policy, CHANGELOG, ADR mutability during dev** |
| **ADR-0031** | **HTTP Error Response Contracts** | **core** | **Standardized ErrorResponse schema for all HTTP 4xx/5xx responses** |
| **ADR-0032** | **HTTP Request Idempotency Semantics** | **core** | **Idempotency keys and retry-safe API design patterns** |

## Tool-Specific ADRs

### DAT (Data Aggregation Tool)

| ID | Title | Extends |
|----|-------|---------|
| ADR-0001-DAT | DAT-Specific Stage Graph (8-Stage Pipeline) | ADR-0001 |
| ADR-0003 | Optional Context and Preview Stages | ADR-0001-DAT |
| ADR-0004-DAT | DAT-Specific Stage ID Configuration | ADR-0004 |
| ADR-0006 | Table Availability Detection | - |
| ADR-0011 | Profile-Driven Extraction and Adapters | - |
| ADR-0013 | Cancellation Semantics for Parse and Export | ADR-0002 |
| ADR-0014 | Parse and Export Artifact Formats | ADR-0008 |

### PPTX Generator

| ID | Title | Extends |
|----|-------|---------|
| ADR-0018 | PPTX Template Processing Model | - |
| ADR-0019 | PPTX Guided Workflow | ADR-0001 |
| ADR-0020 | PPTX Domain Configuration | - |
| ADR-0021 | PPTX Renderer Architecture | - |

### SOV Analyzer

| ID | Title | Extends |
|----|-------|---------|
| ADR-0022 | SOV Analysis Pipeline | ADR-0001 |
| ADR-0023 | SOV DataSet Integration | ADR-0025 |
| ADR-0024 | SOV Visualization Contracts | ADR-0009 |

### DevTools

| ID | Title | Extends |
|----|-------|---------|
| ADR-0027 | DevTools Page Architecture | ADR-0001 |

## Orthogonality Matrix

Each ADR addresses a distinct concern:

| Concern | Core ADR | Tool Extensions |
|---------|----------|-----------------|
| Workflow Orchestration | ADR-0001 | ADR-0001-DAT, ADR-0019, ADR-0022 |
| Artifact Preservation | ADR-0002 | ADR-0013 |
| Deterministic IDs | ADR-0004 | ADR-0004-DAT |
| API Contracts | ADR-0005, ADR-0009 | ADR-0024 |
| Timestamps/Audit | ADR-0008 | ADR-0014 |
| Documentation | ADR-0010, ADR-0015, ADR-0030 | - |
| Concurrency | ADR-0012 | - (cross-platform: async, threads, processes) |
| Versioning | ADR-0016, ADR-0029 | - |
| Guardrails | ADR-0017 | - |
| Data Lineage | ADR-0025 | ADR-0023 |
| Error Handling | ADR-0026, **ADR-0031** | - |
| **Visualization/Rendering** | **ADR-0028** | ADR-0021, ADR-0024 |
| **API Reliability** | **ADR-0032** | - |

## Validation TODO

**Action Required**: Validate all current code aligns with this ADR set.

See `.adrs/TODO_CODE_VALIDATION.md` for the validation checklist.

---

*Last Updated: 2025-12-28*
*Maintainer: Mycahya Eggleston*
