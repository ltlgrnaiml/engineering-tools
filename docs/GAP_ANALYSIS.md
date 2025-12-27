# Implementation Gap Analysis

> **Contracts ↔ ADRs ↔ SPECs vs. Actual Implementation**
> 
> Generated: 2024-12-27 | Based on full codebase review

---

## Executive Summary

This document identifies gaps between intended behavior (as defined by Contracts, ADRs, and SPECs) and actual implementation across all tools.

### Overall Gap Status

| Tool | Implemented | Gaps | Priority Gaps |
|------|-------------|------|---------------|
| **DAT** | 80% | 5 | 2 |
| **PPTX** | 75% | 6 | 3 |
| **SOV** | 60% | 7 | 4 |
| **Gateway** | 70% | 5 | 2 |
| **Homepage** | 50% | 6 | 3 |
| **Cross-Tool** | 40% | 8 | 5 |

---

## 1. Data Aggregator (DAT) Gaps

### 1.1 Implemented ✅

| AC ID | Criterion | Evidence |
|-------|-----------|----------|
| DAT-001 | FSM enforces forward gating | `DATStateMachine` in `core/state_machine.py` |
| DAT-002 | Unlock cascades downstream | `unlock_stage(cascade=True)` in routes.py:560 |
| DAT-003 | Context/Preview optional | Optional lock endpoints exist |
| DAT-008 | Cancel preserves artifacts | `CancellationToken` + artifact not deleted |
| DAT-010 | Parse outputs Parquet | `pl.write_parquet()` in parse stage |

### 1.2 Gaps 🔴

| AC ID | Gap | ADR Ref | Priority | Action Required |
|-------|-----|---------|----------|-----------------|
| DAT-004 | Parse doesn't fall back to profile defaults when context.json missing | ADR-0003 | P1 | Add profile default lookup in parse stage |
| DAT-005 | Table availability lacks `partial/empty` status types | ADR-0006 | P1 | Extend `TableStatus` enum, add probe logic |
| DAT-006 | Profile-driven extraction not fully implemented | ADR-0011 | P2 | Complete profile loader integration |
| DAT-007 | AdapterFactory pattern incomplete | ADR-0011 | P2 | Add adapter registration, catalog diagnostics |
| DAT-009 | Cancel doesn't explicitly verify no partial data | ADR-0013 | P2 | Add transaction/rollback for parse |
| DAT-011 | Export format selection not implemented | ADR-0014 | P3 | Add format param to export endpoint |

### 1.3 Missing Contract Usage

```
Contracts defined but not used in DAT:
- shared/contracts/dat/cancellation.py → CancellationRequest, CheckpointRegistry
- shared/contracts/dat/table_status.py → TableAvailabilityStatus enum values
- shared/contracts/core/id_generator.py → ParseStageInputs not used for stage IDs
```

---

## 2. PPTX Generator Gaps

### 2.1 Implemented ✅

| AC ID | Criterion | Evidence |
|-------|-----------|----------|
| PPTX-004 | Domain config validated at startup | `validate_domain_config()` in main.py:92 |
| PPTX-006 | DataSet input supported | `dataset_input.py` with `/from-dataset` endpoint |
| PPTX-007 | Generated PPTX downloadable | `generation.py` with download endpoints |

### 2.2 Gaps 🔴

| AC ID | Gap | ADR Ref | Priority | Action Required |
|-------|-----|---------|----------|-----------------|
| PPTX-001 | Named shape discovery not using `{category}_{identifier}` convention | ADR-0018 | P0 | Implement shape naming parser |
| PPTX-002 | 7-step workflow not enforced in backend | ADR-0019 | P1 | Add workflow state machine |
| PPTX-003 | Generate not gated on validation pass | ADR-0019 | P1 | Add validation check before generate |
| PPTX-005 | Renderers don't implement common BaseRenderer | ADR-0021 | P2 | Refactor renderers to use interface |
| PPTX-008 | Hardcoded messages exist, not from catalog | ADR-0017 | P2 | Replace with message catalog refs |
| - | No lineage tracking for generated PPTX | ADR-0025 | P2 | Add source_dataset_id to output |

### 2.3 Missing Contract Usage

```
Contracts defined but not used in PPTX:
- shared/contracts/pptx/template.py → ShapeDiscoveryResult not used
- shared/contracts/core/rendering.py → RenderSpec not integrated with renderers
- shared/contracts/messages/catalog.py → No catalog integration
```

---

## 3. SOV Analyzer Gaps

### 3.1 Implemented ✅

| AC ID | Criterion | Evidence |
|-------|-----------|----------|
| SOV-001 | ANOVA uses Type III SS | `analysis/anova.py` config.anova_type |
| SOV-007 | Health endpoint exists | `/health` in main.py:51 |

### 3.2 Gaps 🔴

| AC ID | Gap | ADR Ref | Priority | Action Required |
|-------|-----|---------|----------|-----------------|
| SOV-002 | Variance percentages don't verify sum to 100% | ADR-0022 | P0 | Add validation in ANOVA computation |
| SOV-003 | Input doesn't use DataSetRef contract | ADR-0023 | P1 | Refactor to load via ArtifactStore |
| SOV-004 | Output doesn't save with lineage (parent_ref) | ADR-0023 | P1 | Add parent_dataset_ids to manifest |
| SOV-005 | Visualization not using typed Pydantic contracts | ADR-0024 | P1 | Use ChartSpec from rendering.py |
| SOV-006 | Determinism not verified (no seed) | ADR-0012 | P2 | Add seed param, verify reproducibility |
| - | No `/api/v1/` versioned routing | API-001 | P1 | Add /v1/ prefix to SOV routes |
| - | Routes use `/api/` but tool is mounted at `/api/sov/api/` | Architecture | P1 | Fix route prefix duplication |

### 3.3 Missing Contract Usage

```
Contracts defined but not used in SOV:
- shared/contracts/sov/visualization.py → Not integrated with frontend
- shared/contracts/core/rendering.py → ChartSpec not used
- shared/contracts/core/dataset.py → DataSetRef not used for inputs
```

---

## 4. Gateway Gaps

### 4.1 Implemented ✅

| AC ID | Criterion | Evidence |
|-------|-----------|----------|
| GW-001 | Tools mounted under /api/{tool}/ | gateway/main.py:127-147 |
| GW-002 | DataSet API at /api/v1/datasets | dataset_service.py |
| GW-003 | Pipeline API at /api/v1/pipelines | pipeline_service.py |
| GW-004 | Health reports tool availability | /health endpoint |
| GW-005 | CORS configured | main.py:32-38 |
| GW-006 | OpenAPI at /docs | FastAPI default |

### 4.2 Gaps 🔴

| Gap | ADR Ref | Priority | Action Required |
|-----|---------|----------|-----------------|
| Pipeline dispatch not implemented (TODO in code) | ADR-0026 | P0 | Implement `_dispatch_step()` |
| Pipeline storage is in-memory only | Architecture | P1 | Integrate with registry_db.py |
| Lineage endpoint exists but children scan is O(n) | ADR-0025 | P2 | Add reverse index for lineage |
| No error response standardization | API-003 | P2 | Add ErrorResponse contract |
| DevTools service incomplete | ADR-0027 | P3 | Complete ADR editor, schema validator |

---

## 5. Homepage/Frontend Gaps

### 5.1 Current State

The homepage frontend exists at `apps/homepage/frontend/` with React + Vite + TailwindCSS setup.

### 5.2 Gaps 🔴

| Gap | Priority | Action Required |
|-----|----------|-----------------|
| No tool launcher/dashboard | P1 | Create main dashboard with tool cards |
| No DataSet browser component | P1 | Add DataSet list/preview UI |
| No pipeline visualization | P2 | Add pipeline builder/monitor |
| No lineage graph visualization | P2 | Add DAG visualization for lineage |
| DevTools page not implemented | P3 | Create ADR reader, config editor |
| No shared TypeScript types from contracts | P2 | Generate TS types from Pydantic |

---

## 6. Cross-Tool Integration Gaps

### 6.1 Data Flow Gaps

| Flow | Status | Gap |
|------|--------|-----|
| DAT → SOV | ⚠️ Partial | SOV doesn't use DataSetRef to load |
| SOV → PPTX | ⚠️ Partial | PPTX loads but no viz contract mapping |
| DAT → PPTX | ✅ Works | dataset_input.py functional |
| Pipeline Orchestration | 🔴 Stub | `_dispatch_step()` not implemented |

### 6.2 Contract Integration Gaps

| Contract | DAT | SOV | PPTX | Gateway |
|----------|-----|-----|------|---------|
| `DataSetManifest` | ✅ | ⚠️ | ✅ | ✅ |
| `DataSetRef` | ✅ | 🔴 | ✅ | ✅ |
| `RenderSpec` | 🔴 | 🔴 | 🔴 | N/A |
| `Pipeline` | N/A | N/A | N/A | ⚠️ |
| `AuditTrail` | 🔴 | 🔴 | 🔴 | 🔴 |
| `CancellationRequest` | 🔴 | N/A | N/A | ⚠️ |
| `MessageCatalog` | 🔴 | 🔴 | 🔴 | 🔴 |

### 6.3 Missing Shared Infrastructure

| Component | Status | Gap |
|-----------|--------|-----|
| Unified error responses | 🔴 | Each tool has different error format |
| Message catalog integration | 🔴 | No tool uses catalog.py |
| Rendering engine | 🔴 | shared/rendering/ not used by any tool |
| Audit trail logging | 🔴 | AuditTrail contract not integrated |
| Deterministic IDs | ⚠️ | Used in gateway, not in tools |

---

## 7. Priority Action Items

### P0 - Critical (Must Fix)

1. **SOV-002**: Add variance percentage validation (sum to 100%)
2. **PPTX-001**: Implement named shape discovery with `{category}_{identifier}`
3. **Pipeline dispatch**: Implement `_dispatch_step()` in gateway

### P1 - High Priority

4. **SOV routing**: Fix double `/api/` prefix issue
5. **DAT-004**: Profile default fallback when context missing
6. **PPTX-002/003**: Add workflow state machine and validation gating
7. **SOV-003/004**: Use DataSetRef for input, add lineage to output
8. **Homepage**: Create tool launcher dashboard

### P2 - Medium Priority

9. **Error standardization**: Unified ErrorResponse across all tools
10. **RenderSpec integration**: Connect rendering engine to all tools
11. **Message catalog**: Replace hardcoded messages
12. **TypeScript types**: Generate from Pydantic contracts
13. **Lineage optimization**: Add reverse index for children lookup

### P3 - Low Priority

14. **DAT-011**: Multi-format export
15. **DevTools**: Complete ADR editor, schema validator
16. **Audit trail**: Integrate AuditTrail contract

---

## 8. Recommended Implementation Order

```
Phase 1: Critical Fixes (P0)
├── 1.1 SOV variance validation
├── 1.2 PPTX shape naming
└── 1.3 Pipeline dispatch stub → real implementation

Phase 2: Integration (P1)
├── 2.1 SOV DataSetRef integration
├── 2.2 PPTX workflow enforcement
├── 2.3 DAT profile defaults
└── 2.4 Homepage dashboard

Phase 3: Standardization (P2)
├── 3.1 Unified error responses
├── 3.2 Rendering engine integration
├── 3.3 Message catalog adoption
└── 3.4 TypeScript type generation

Phase 4: Polish (P3)
├── 4.1 Multi-format export
├── 4.2 DevTools completion
└── 4.3 Audit trail integration
```

---

## Appendix: File-Level Gap Summary

### Files Needing Updates

| File | Gaps | Priority Changes |
|------|------|------------------|
| `apps/sov_analyzer/backend/src/sov_analyzer/analysis/anova.py` | Variance validation, seed | P0, P2 |
| `apps/sov_analyzer/backend/main.py` | Route prefix fix | P1 |
| `apps/pptx_generator/backend/services/` | Shape discovery, workflow FSM | P0, P1 |
| `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py` | Profile fallback | P1 |
| `gateway/services/pipeline_service.py` | _dispatch_step implementation | P0 |
| `apps/homepage/frontend/src/` | Dashboard, DataSet browser | P1 |

### New Files Needed

| File | Purpose | Priority |
|------|---------|----------|
| `shared/errors/responses.py` | Unified error response contract | P2 |
| `apps/homepage/frontend/src/components/Dashboard.tsx` | Tool launcher | P1 |
| `apps/homepage/frontend/src/components/DataSetBrowser.tsx` | DataSet list/preview | P1 |
| `tools/gen_typescript.py` | TS type generation from Pydantic | P2 |
