# Changelog

All notable changes to the Engineering Tools Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Note**: During development (pre-1.0.0), minor version bumps may include breaking changes.
> See ADR-0017 for versioning policy details.

## [Unreleased]

### Added

- ADR-0031: Documentation Lifecycle Management for multi-project monorepo
- CHANGELOG.md for release-level change tracking

### Changed

- Documentation structure reorganization per ADR-0031

## [0.1.0] - 2025-12-28

### Added

- **Platform Infrastructure**
  - API Gateway with cross-tool routing (`gateway/`)
  - Shared contracts in Pydantic (`shared/contracts/`)
  - ArtifactStore for DataSet persistence (`shared/storage/`)
  - 29 ADRs defining architectural decisions (`.adrs/`)
  - 22 SPECs defining implementation details (`docs/specs/`)

- **Data Aggregator (DAT)**
  - 8-stage pipeline with FSM orchestration
  - File adapters (CSV, Excel, Parquet, JSON)
  - Profile-driven extraction system
  - Cancellation with checkpoint preservation

- **PowerPoint Generator (PPTX)**
  - 7-step guided workflow
  - Template shape discovery (ADR-0019 compliant)
  - DataSet input integration
  - Chart, table, and text renderers

- **SOV Analyzer**
  - ANOVA computation (Type III SS)
  - Variance component analysis
  - Visualization contracts
  - DataSet lineage tracking

- **Homepage**
  - Tool launcher with status indicators
  - DataSet browser and preview
  - Pipeline builder UI
  - DevTools page for ADR management

- **Shared Infrastructure**
  - Unified rendering engine (ADR-0029)
  - Deterministic ID generation (ADR-0005)
  - Cross-platform concurrency (ADR-0013)
  - Message catalog system (ADR-0018)

### Core ADRs Accepted

- ADR-0001: Hybrid FSM Architecture
- ADR-0002: Artifact Preservation on Unlock
- ADR-0005: Deterministic Content-Addressed IDs
- ADR-0007: Swagger/OpenAPI as Executable Contract
- ADR-0009: Audit Trail Timestamps
- ADR-0010: Type Safety & Contract Discipline
- ADR-0011: Docs-as-Code Engineering Tenets
- ADR-0013: Cross-Platform Concurrency
- ADR-0016: 3-Tier Document Model
- ADR-0017: Hybrid Semver Contract Versioning
- ADR-0018: Cross-Cutting Guardrails
- ADR-0026: DataSet Lineage Tracking
- ADR-0027: Pipeline Error Handling
- ADR-0029: Unified Rendering Engine
- ADR-0030: API Versioning and Endpoint Naming

---

[Unreleased]: https://github.com/user/engineering-tools/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/user/engineering-tools/releases/tag/v0.1.0
