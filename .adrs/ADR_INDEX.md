# ADR Index: Engineering Tools Platform

> **Status**: This is the authoritative, cohesive set of Architectural Decision Records (ADRs) for the Engineering Tools platform. All code creation and modifications must align with these ADRs.
>
> **Context**: Solo-dev, greenfield, AI-assisted development. ADRs are optimized for first-principles approach, automation, and deterministic systems.
>
> **Naming Convention**: ADRs use globally unique sequential numbering (BKM per adr.github.io). Format: `ADR-XXXX_kebab-case-title.json`. Numbers are never reused.

## ADR Hierarchy

```text
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

### Foundational Architecture

| ID | Title | Scope | Purpose |
|----|-------|-------|---------|
| ADR-0001 | Hybrid FSM Architecture for Guided Workflow Orchestration | core | Unified state machine pattern for all guided workflows |
| ADR-0002 | Artifact Preservation on Unlock | shared | Never delete user work on state changes |
| ADR-0005 | Deterministic Content-Addressed IDs | core | SHA-256 hash-based IDs for reproducibility |
| ADR-0009 | Audit Trail Timestamps | core | ISO-8601 UTC timestamps for all artifacts |
| ADR-0013 | Cross-Platform Concurrency | core | Unified async, threading, process parallelism for all OS |
| ADR-0018 | Cross-Cutting Guardrails | cross-cutting | Shared constraints: path safety, concurrency, etc. |

### Contract & API Discipline

| ID | Title | Scope | Purpose |
|----|-------|-------|---------|
| ADR-0007 | Swagger/OpenAPI as Executable Contract | core | API contracts validated via Swagger UI |
| ADR-0010 | Type-Safety & Contract Discipline | core | Pydantic-first contracts as Tier 0 |
| ADR-0017 | Calendar Versioning for Contracts | core | YYYY.MM.PATCH format; no pre-1.0/post-1.0 phases |
| ADR-0030 | Simplified API Endpoint Naming | core | /api/{tool}/{resource} pattern; no version prefix by default |
| ADR-0032 | HTTP Error Response Contracts | core | Standardized ErrorResponse schema for all HTTP 4xx/5xx responses |
| ADR-0033 | HTTP Request Idempotency Semantics | core | Idempotency keys and retry-safe API design patterns |

### Data & Lineage

| ID | Title | Scope | Purpose |
|----|-------|-------|---------|
| ADR-0026 | DataSet Lineage & Version Tracking | core | Cross-tool lineage with version_id (SHA-256) and parent_version_id |
| ADR-0027 | Pipeline Error Handling | core | Unified error handling patterns |
| ADR-0029 | Unified Rendering Engine | cross-cutting | Shared visualization, charting, and rendering for all tools |

### Documentation

| ID | Title | Scope | Purpose |
|----|-------|-------|---------|
| ADR-0011 | Docs-as-Code Engineering Tenets | core | MkDocs, docstrings, CI enforcement |
| ADR-0016 | 3-Tier Document Model | core | ADRs → Specs → Guides separation |
| ADR-0031 | Documentation Lifecycle Management | core | 5-category doc classification, archival policy, CHANGELOG |

### Solo-Dev Optimizations

| ID | Title | Scope | Purpose |
|----|-------|-------|---------|
| ADR-0034 | AI-Assisted Development Patterns | core | AI-parseable code: naming conventions, docstrings, flat structure |
| ADR-0035 | Automated Documentation Pipeline | core | Generate docs from code: JSON Schema, OpenAPI, mkdocstrings, git-cliff |
| ADR-0036 | Contract-Driven Test Generation | core | Pydantic → Hypothesis tests; FSM exhaustive path testing |
| ADR-0037 | Observability & Debugging First (Backend + Frontend) | core | Unified observability: structured logging, request tracing, state snapshots, frontend debug panels |
| ADR-0038 | Single-Command Development Environment | core | ./start.ps1 starts everything; uv for deps; Docker Compose option |
| ADR-0039 | CI/CD Pipeline for Data & Code | core | Pre-commit + PR checks + main deploy; GitHub Actions |
| ADR-0040 | Deployment Automation | core | Pulumi IaC; environment parity; feature flags |
| ADR-0043 | AI Development Workflow | core | 6-tier hierarchical workflow for structured AI-assisted development |
| ADR-0044 | Frontend Iframe Integration Pattern | core | Homepage embeds tool UIs via iframes; all frontends required |

## Tool-Specific ADRs

### DAT (Data Aggregation Tool)

| ID | Title | Extends |
|----|-------|---------|
| ADR-0003 | DAT-Specific Stage Graph (8-Stage Pipeline) | ADR-0001 |
| ADR-0004 | Optional Context and Preview Stages | ADR-0003 |
| ADR-0006 | DAT-Specific Stage ID Configuration | ADR-0005 |
| ADR-0008 | Table Availability Detection | - |
| ADR-0012 | Profile-Driven Extraction and Adapters | - |
| ADR-0014 | Cancellation Semantics for Parse and Export | ADR-0002 |
| ADR-0015 | Parse and Export Artifact Formats | ADR-0009 |
| ADR-0041 | Large File Streaming Strategy (10MB threshold) | ADR-0012 |
| ADR-0042 | DAT UI Horizontal Wizard Pattern | ADR-0003 |

### PPTX Generator

| ID | Title | Extends |
|----|-------|---------|
| ADR-0019 | PPTX Template Processing Model | - |
| ADR-0020 | PPTX Guided Workflow | ADR-0001 |
| ADR-0021 | PPTX Domain Configuration | - |
| ADR-0022 | PPTX Renderer Architecture | - |

### SOV Analyzer

| ID | Title | Extends |
|----|-------|---------|
| ADR-0023 | SOV Analysis Pipeline | ADR-0001 |
| ADR-0024 | SOV DataSet Integration | ADR-0026 |
| ADR-0025 | SOV Visualization Contracts | ADR-0010 |

### DevTools

| ID | Title | Extends |
|----|-------|---------|
| ADR-0028 | DevTools Page Architecture | ADR-0001 |
| ADR-0045 | DevTools Workflow Manager UI | ADR-0028 |

### Knowledge & AI

| ID | Title | Extends |
|----|-------|--------|
| ADR-0047 | Knowledge Archive & RAG System | ADR-0043 |
| ADR-0048 | Unified xAI Agent Wrapper Architecture | ADR-0047 |

## Orthogonality Matrix

Each ADR addresses a distinct concern (no overlaps):

| Concern | Core ADR | Tool Extensions |
|---------|----------|-----------------|
| Workflow Orchestration | ADR-0001 | ADR-0003, ADR-0020, ADR-0023, ADR-0028 |
| Artifact Preservation | ADR-0002 | ADR-0014 |
| Deterministic IDs | ADR-0005 | ADR-0006 |
| API Contracts | ADR-0007, ADR-0010, ADR-0030 | ADR-0025 |
| Timestamps/Audit | ADR-0009 | ADR-0015 |
| Documentation | ADR-0011, ADR-0016, ADR-0031, ADR-0035 | - |
| Concurrency | ADR-0013 | - |
| Versioning | ADR-0017 | - |
| Guardrails | ADR-0018 | - |
| Data Lineage | ADR-0026 | ADR-0024 |
| Error Handling | ADR-0027, ADR-0032 | - |
| Visualization/Rendering | ADR-0029 | ADR-0022, ADR-0025 |
| API Reliability | ADR-0033 | - |
| AI-Assisted Dev | ADR-0034 | - |
| Test Generation | ADR-0036 | - |
| Observability | ADR-0037 | - |
| Dev Environment | ADR-0038 | - |
| CI/CD | ADR-0039 | - |
| Deployment | ADR-0040 | - |
| AI Workflow | ADR-0043 | ADR-0047 |
| Knowledge/RAG | ADR-0047, ADR-0048 | - |
| Frontend Integration | ADR-0044 | - |

## ADR Numbering Refactor (2025-12-30)

All ADRs were renumbered to follow industry BKM (Best Known Method) per adr.github.io:
- Global sequential numbering (no duplicates across domains)
- Contiguous numbering (no gaps)
- Lowercase kebab-case titles
- Format: `ADR-XXXX_title.json`

### Mapping Reference

| Old ID | New ID |
|--------|--------|
| ADR-0001-DAT | ADR-0003 |
| ADR-0003 (dat) | ADR-0004 |
| ADR-0004 (core) | ADR-0005 |
| ADR-0004-DAT | ADR-0006 |
| ADR-0005 | ADR-0007 |
| ADR-0006 | ADR-0008 |
| ADR-0008 | ADR-0009 |
| ADR-0009 | ADR-0010 |
| ADR-0010 | ADR-0011 |
| ADR-0011 | ADR-0012 |
| ADR-0012 | ADR-0013 |
| ADR-0013 | ADR-0014 |
| ADR-0014 | ADR-0015 |
| ADR-0015 | ADR-0016 |
| ADR-0016 | ADR-0017 |
| ADR-0017 | ADR-0018 |
| ADR-0018 | ADR-0019 |
| ADR-0019 | ADR-0020 |
| ADR-0020 | ADR-0021 |
| ADR-0021 | ADR-0022 |
| ADR-0022 | ADR-0023 |
| ADR-0023 | ADR-0024 |
| ADR-0024 | ADR-0025 |
| ADR-0025 | ADR-0026 |
| ADR-0026 | ADR-0027 |
| ADR-0027 | ADR-0028 |
| ADR-0028 | ADR-0029 |
| ADR-0029 | ADR-0030 |
| ADR-0030 | ADR-0031 |
| ADR-0031 | ADR-0032 |
| ADR-0032 | ADR-0033 |
| ADR-0033 | ADR-0034 |
| ADR-0034 | ADR-0035 |
| ADR-0035 | ADR-0036 |
| ADR-0036 | ADR-0037 |
| ADR-0037 | ADR-0038 |
| ADR-0038 | ADR-0039 |
| ADR-0039 | ADR-0040 |
| ADR-0040 | ADR-0041 |
| ADR-0041 (dat) | ADR-0042 |
| ADR-0041 (root) | ADR-0043 |
| ADR-0042 | ADR-0044 |
| ADR-0043 | ADR-0045 |

## Validation TODO

**Action Required**: Validate all current code aligns with this ADR set.

See `.adrs/TODO_CODE_VALIDATION.md` for the validation checklist.

---

*Last Updated: 2025-12-31*
*Maintainer: Mycahya Eggleston*
*Total ADRs: 47 (30 core + 9 DAT + 4 PPTX + 3 SOV + 2 DevTools - 1 shared)*
