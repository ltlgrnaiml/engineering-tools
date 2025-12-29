# TEAM_013: DAT Refactor Consolidated Findings & Master Plan

**Session Date**: 2025-12-28
**Status**: FINAL_CONSOLIDATION
**Objective**: Aggregate findings from TEAM_006 through TEAM_010 into a single, cohesive, validated master plan for the DAT refactor.
**Driver**: Cascade

## 1. Executive Summary

We have analyzed the DAT subsystem across five planning sessions (TEAM_006–010). The consensus is clear: **The current DAT implementation significantly deviates from the SSoT (ADRs/SPECs)**, particularly regarding API versioning, deterministic ID generation, adapter architecture, and stage orchestration.

This document serves as the **Final Authority** for the refactor, superseding previous partial plans. It combines the rigorous gap analysis of TEAM_006, the implementation details of TEAM_008, and the deterministic phasing of TEAM_009.

---

## 2. Team Assessments & Scorecard

We evaluated each team's contribution to identifying valid gaps and defining the solution.

| Team Session | Focus Area | Key Findings / Contributions | Score (Valid Gaps) |
| :--- | :--- | :--- | :--- |
| **TEAM_006** | **SSoT Gap Analysis** | • Identified `/v1` API violation (ADR-0029). • Found hardcoded FSM logic vs Configurable Graph. • Discovered absolute paths in Stage IDs (Determinism fail). • Flagged duplicate adapter stacks. | **10/10** (Found root causes) |
| **TEAM_007** | **High-Level Planning** | • Defined "Lazy Initialization" for optional stages. • Proposed "Fast Probe" for Table Availability. • Mapped tasks to CORE/SAFE/STAGE categories. | **9/10** (Strong architectural plan) |
| **TEAM_008** | **Implementation Details** | • Detailed missing contracts (Profile CRUD, Jobs). • Defined class-level implementation for Adapter Registry. • Spec'd out CSV/Excel/JSON adapter logic. | **9/10** (Excellent low-level detail) |
| **TEAM_009** | **Deterministic Plan** | • Refined ID inputs per stage (ADR-0004-DAT). • Defined Streaming threshold strategies (ADR-0040). • Created the most actionable Milestone sequence (M0-M9). | **10/10** (Best actionable roadmap) |
| **TEAM_010** | **Summary & Alignment** | • Validated alignment with Core ADRs/Solo-Dev Ethos. • Synthesized previous plans. • Re-affirmed Acceptance Criteria. | **8/10** (Good summary, mostly derivative) |

---

## 3. Consolidated Gap Matrix (The "What")

These are the validated issues that **must** be resolved.

| Component | Current State (The Problem) | SSoT Requirement (The Fix) | Criticality |
| :--- | :--- | :--- | :--- |
| **API Routing** | `APIRouter(prefix="/v1")` resulting in `/api/dat/v1/...` | Unversioned `/api/dat/...` by default (ADR-0029) | **CRITICAL** |
| **Adapters** | Split stack: Legacy `src/dat_aggregation/adapters` vs New `backend/adapters` | Single `AdapterRegistry` using Contract-style `BaseFileAdapter` (ADR-0011) | **CRITICAL** |
| **Stage Graph** | Hardcoded `FORWARD_GATES` and `CASCADE_TARGETS` dicts | Instance-based `StageGraphConfig` injected into FSM (ADR-0001-DAT) | **HIGH** |
| **Determinism** | Stage IDs use 16-char hex; Inputs include absolute paths | 8-char IDs; Inputs use relative paths & stage-specific data (ADR-0004) | **CRITICAL** |
| **Table Probe** | Reads full dataframe (slow) | Metadata-only probe (`probe_schema`) returning `TableStatus` (ADR-0006) | **HIGH** |
| **Large Files** | Eager loading default | Streaming for >10MB via `scan_csv`/`LazyFrame` (ADR-0040) | **MEDIUM** |
| **Optionality** | Implicit; Preview "skips" but stays locked/incomplete | Explicit `CONTEXT`/`PREVIEW` optionality; Lazy init for downstream (ADR-0003) | **HIGH** |
| **Cancellation** | No checkpointing guarantees | Soft-cancel; rollback partials; preserve completed (ADR-0013) | **MEDIUM** |
| **Artifacts** | Mixed output formats | Parse=Parquet (Strict); Export=Multi-format (ADR-0014) | **HIGH** |

---

## 4. The Master Plan (The "How")

We will execute the **TEAM_009** milestone structure, augmented with **TEAM_008** implementation details.

### Phase 1: Foundation & Cleanup (M0 - M2)

- **M0: Baseline**: Run tests, snapshot OpenAPI.
- **M1: Unify Adapters**:
  - Delete legacy `src/dat_aggregation/adapters`.
  - Promote `backend/adapters` to primary.
  - Implement `AdapterRegistry` (from TEAM_008).
- **M2: API Normalization**:
  - Remove `/v1` prefix from DAT Router.
  - Update Gateway and Frontend references.

### Phase 2: Core Orchestration (M3 - M4)

- **M3: Configurable FSM**:
  - Inject `StageGraphConfig` into `DATStateMachine`.
  - Implement correct Optional Stage logic (Lazy Init).
- **M4: Determinism**:
  - Switch to `compute_deterministic_id` (8-char).
  - Implement stage-specific ID input generation (Relative paths only).

### Phase 3: Capability & Performance (M5 - M7)

- **M5: Fast Probe**: Refactor `TableAvailability` to use `adapter.probe_schema()`.
- **M6: Streaming**: Implement >10MB streaming threshold in adapters.
- **M7: Artifact Bundles**: Enforce Parquet for Parse; Implement Export handlers.

### Phase 4: Reliability & UI (M8 - M9)

- **M8: Cancellation**: Implement soft-cancel and checkpointing.
- **M9: Wizard UI**: Update Frontend to reflect 8-stage horizontal wizard.

---

## 5. Next Steps

1. **Freeze this Plan**: TEAM_013 is the reference.
2. **Begin Phase 1**: Start with **M1 (Unify Adapters)** as it unlocks the "Fast Probe" capability needed later.
3. **Execute**: Proceed sequentially through M1 -> M9.

**Ready to Execute.**
