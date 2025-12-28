# Implementation Gap Analysis

> **Contracts ↔ ADRs ↔ SPECs vs. Actual Implementation**
> 
> Generated: 2024-12-27 | Based on full codebase review
> **Last Updated: 2024-12-27** | Gap remediation in progress

---

## Executive Summary

This document identifies gaps between intended behavior (as defined by Contracts, ADRs, and SPECs) and actual implementation across all tools.

### Overall Gap Status

| Tool | Implemented | Gaps | Priority Gaps |
|------|-------------|------|---------------|
| **DAT** | 100% ✅ | 0 | 0 |
| **PPTX** | 100% ✅ | 0 | 0 |
| **SOV** | 100% ✅ | 0 | 0 |
| **Gateway** | 100% ✅ | 0 | 0 |
| **Homepage** | 100% ✅ | 0 | 0 |
| **Cross-Tool** | 100% ✅ | 0 | 0 |

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

### 1.2 Gaps ✅ ALL FIXED 

| AC ID | Gap | ADR Ref | Priority | Action Required |
|-------|-----|---------|----------|-----------------|
| ~~DAT-004~~ | ~~Parse doesn't fall back to profile defaults when context.json missing~~ | ~~ADR-0003~~ | ~~P1~~ | **FIXED** - Added `_load_context_with_fallback()` in parse.py |
| ~~DAT-005~~ | ~~Table availability lacks `partial/empty` status types~~ | ~~ADR-0006~~ | ~~P1~~ | **FIXED** - Added PARTIAL status detection with `missing_columns` tracking |
| ~~DAT-006~~ | ~~Profile-driven extraction not fully implemented~~ | ~~ADR-0011~~ | ~~P2~~ | **FIXED** - Added `validate_profile()` using `ProfileValidationResult` |
| ~~DAT-007~~ | ~~AdapterFactory pattern incomplete~~ | ~~ADR-0011~~ | ~~P2~~ | **FIXED** - Added `AdapterRegistry` with registration API and capabilities |
| ~~DAT-009~~ | ~~Cancel doesn't explicitly verify no partial data~~ | ~~ADR-0013~~ | ~~P2~~ | **FIXED** - Added `CheckpointManager` for cancel-safe operations |
| ~~DAT-011~~ | ~~Export format selection not implemented~~ | ~~ADR-0014~~ | ~~P3~~ | **FIXED** - Added `ExportFormat` enum with CSV/Excel support |

### 1.3 Contract Usage 

```
All DAT contracts now integrated:
shared/contracts/dat/cancellation.py → CheckpointManager uses CheckpointRegistry, CancellationAuditLog
shared/contracts/dat/profile.py → ProfileValidationResult wired to profile_loader
shared/contracts/core/error_response.py → ErrorResponse used in routes
```

---

## 2. PPTX Generator Gaps

### 2.1 Implemented ✅ 

| AC ID | Criterion | Evidence |
|-------|-----------|----------|
| PPTX-004 | Domain config validated at startup | `validate_domain_config()` in main.py:92 |
| PPTX-006 | DataSet input supported | `dataset_input.py` with `/from-dataset` endpoint |
| PPTX-007 | Generated PPTX downloadable | `generation.py` with download endpoints |

### 2.2 Gaps ✅ ALL FIXED 

| AC ID | Gap | ADR Ref | Priority | Action Required |
|-------|-----|---------|----------|-----------------|
| ~~PPTX-001~~ | ~~Named shape discovery not using `{category}_{identifier}` convention~~ | ~~ADR-0018~~ | ~~P0~~ | ✅ **FIXED** - Added `shape_discovery.py` with ADR-0018 compliant parser |
| ~~PPTX-002~~ | ~~7-step workflow not enforced in backend~~ | ~~ADR-0019~~ | ~~P1~~ | ✅ **FIXED** - Added `workflow_fsm.py` with 7-step state machine |
| ~~PPTX-003~~ | ~~Generate not gated on validation pass~~ | ~~ADR-0019~~ | ~~P1~~ | ✅ **FIXED** - Added `check_generate_allowed()` validation gating |
| ~~PPTX-005~~ | ~~Renderers don't implement common BaseRenderer~~ | ~~ADR-0021~~ | ~~P2~~ | ✅ **FIXED** - Added `build_chart_spec()` to PlotRenderer, `build_table_spec()` to TableRenderer |
| ~~PPTX-008~~ | ~~Hardcoded messages exist, not from catalog~~ | ~~ADR-0017~~ | ~~P2~~ | ✅ **FIXED** - Added `ErrorResponse` helper to `generation.py` |
| ~~-~~ | ~~No lineage tracking for generated PPTX~~ | ~~ADR-0025~~ | ~~P2~~ | ✅ **FIXED** - Added `source_dataset_id` to output |

### 2.3 Contract Usage ✅

```
All PPTX contracts now integrated:
✅ shared/contracts/pptx/template.py → ShapeDiscoveryResult used in templates.py
✅ shared/contracts/core/rendering.py → ChartSpec/TableSpec in renderers
✅ shared/contracts/core/error_response.py → ErrorResponse in generation.py
✅ shared/contracts/core/dataset.py → DomainConfig Pydantic schema
```

---

## 3. SOV Analyzer Gaps

### 3.1 Implemented ✅ 

| AC ID | Criterion | Evidence |
|-------|-----------|----------|
| SOV-001 | ANOVA uses Type III SS | `analysis/anova.py` config.anova_type |
| SOV-007 | Health endpoint exists | `/health` in main.py:51 |

### 3.2 Gaps ✅ ALL FIXED 

| AC ID | Gap | ADR Ref | Priority | Action Required |
|-------|-----|---------|----------|-----------------|
| ~~SOV-002~~ | ~~Variance percentages don't verify sum to 100%~~ | ~~ADR-0022~~ | ~~P0~~ | **FIXED** - Added `VarianceValidationError` and `validate_variance_sum()` in anova.py |
| ~~SOV-003~~ | ~~Input doesn't use DataSetRef contract~~ | ~~ADR-0023~~ | ~~P1~~ | **FIXED** - Added `dataset_ref` param to `create_analysis()` |
| ~~SOV-004~~ | ~~Output doesn't save with lineage (parent_ref)~~ | ~~ADR-0023~~ | ~~P1~~ | **FIXED** - Added `parent_dataset_ids` to manifest in `export_as_dataset()` |
| ~~SOV-005~~ | ~~Visualization not using typed Pydantic contracts~~ | ~~ADR-0024~~ | ~~P1~~ | **FIXED** - Created `visualization_service.py` with typed contracts |
| ~~SOV-006~~ | ~~Determinism not verified (no seed)~~ | ~~ADR-0012~~ | ~~P2~~ | **FIXED** - Added `seed` param to ANOVAConfig |
| ~~-~~ | ~~No `/api/v1/` versioned routing~~ | ~~API-001~~ | ~~P1~~ | **FIXED** - Routes use `/v1/` prefix |
| ~~-~~ | ~~Routes use `/api/` but tool is mounted at `/api/sov/api/`~~ | ~~Architecture~~ | ~~P1~~ | **FIXED** - Removed duplicate prefix in main.py |

### 3.3 Contract Usage 

```
All SOV contracts now integrated:
shared/contracts/sov/visualization.py → VisualizationService generates all chart types
shared/contracts/sov/anova.py → to_pydantic() converter in local dataclasses
shared/contracts/core/dataset.py → DataSetRef used for inputs, visualization_specs in output
shared/contracts/core/error_response.py → ErrorResponse used in routes.py
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

### 4.2 Gaps ✅ ALL FIXED 

| Gap | ADR Ref | Priority | Action Required |
|-----|---------|----------|-----------------|
| ~~Pipeline dispatch not implemented (TODO in code)~~ | ~~ADR-0026~~ | ~~P0~~ | **FIXED** - Implemented `_dispatch_step()` with HTTP client calls to tool APIs |
| ~~Pipeline storage is in-memory only~~ | ~~Architecture~~ | ~~P1~~ | **FIXED** - Integrated with `registry_db.py` |
| ~~Lineage endpoint exists but children scan is O(n)~~ | ~~ADR-0025~~ | ~~P2~~ | **FIXED** - Added `lineage_edges` table with reverse index in `registry_db.py` |
| ~~No error response standardization~~ | ~~API-003~~ | ~~P2~~ | **FIXED** - Added `shared/contracts/core/error_response.py` with unified ErrorResponse |
| ~~DevTools service incomplete~~ | ~~ADR-0027~~ | ~~P3~~ | **FIXED** - Full ADR editor and schema validator in `devtools_service.py` (346 lines) |

---

## 5. Homepage/Frontend Gaps

### 5.1 Current State COMPLETE

The homepage frontend at `apps/homepage/frontend/` is fully implemented with React + Vite + TailwindCSS.

### 5.2 Gaps ALL FIXED

| Gap | Priority | Status |
|-----|----------|--------|
| ~~No tool launcher/dashboard~~ | ~~P1~~ | **FIXED** - `HomePage.tsx` with tool cards and status indicators |
| ~~No DataSet browser component~~ | ~~P1~~ | **FIXED** - `DatasetsPage.tsx` and `DataSetDetailsPage.tsx` |
| ~~No pipeline visualization~~ | ~~P2~~ | **FIXED** - `PipelinesPage.tsx`, `PipelineBuilderPage.tsx`, `PipelineDetailsPage.tsx` |
| ~~No lineage graph visualization~~ | ~~P2~~ | **FIXED** - Lineage display in `DataSetDetailsPage.tsx` |
| ~~DevTools page not implemented~~ | ~~P3~~ | **FIXED** - `DevToolsPage.tsx` (573 lines) with ADR reader/editor |
| ~~No shared TypeScript types from contracts~~ | ~~P2~~ | **FIXED** - Created `shared/frontend/src/types/contracts.ts` |

---

## 6. Cross-Tool Integration Gaps

### 6.1 Data Flow Gaps

| Flow | Status | Gap |
|------|--------|-----|
| DAT → SOV | ✅ Works | SOV now uses DataSetRef for input |
| SOV → PPTX | ✅ Works | PPTX loads datasets with visualization contracts |
| DAT → PPTX | ✅ Works | dataset_input.py functional |
| Pipeline Orchestration | ✅ Works | `_dispatch_step()` implemented with HTTP clients |

### 6.2 Contract Integration Gaps

| Contract | DAT | SOV | PPTX | Gateway |
|----------|-----|-----|------|---------|
| `DataSetManifest` | ✅ | ✅ | ✅ | ✅ |
| `DataSetRef` | ✅ | ✅ | ✅ | ✅ |
| `RenderSpec` | ✅ | ✅ | ✅ | N/A |
| `Pipeline` | N/A | N/A | N/A | ✅ |
| `AuditTrail` | ✅ | ✅ | ✅ | ✅ |
| `CancellationRequest` | ✅ | N/A | N/A | ✅ |
| `MessageCatalog` | ✅ | ✅ | ✅ | ✅ |

### 6.3 Missing Shared Infrastructure

| Component | Status | Gap |
|-----------|--------|-----|
| Unified error responses | ✅ | Created `shared/contracts/core/error_response.py` |
| Message catalog integration | ✅ | Created `shared/contracts/messages/builtin_catalogs.py` |
| Rendering engine | ✅ | PPTX renderers use ChartSpec/TableSpec |
| Audit trail logging | ✅ | AuditTrail integrated in cancellation |
| Deterministic IDs | ✅ | Used across all tools |

---

## 7. Priority Action Items

### P0 - Critical (Must Fix)

1. ~~**SOV-002**: Add variance percentage validation (sum to 100%)~~ ✅ **DONE**
2. ~~**PPTX-001**: Implement named shape discovery with `{category}_{identifier}`~~ ✅ **DONE**
3. ~~**Pipeline dispatch**: Implement `_dispatch_step()` in gateway~~ ✅ **DONE**

### P1 - High Priority

4. ~~**SOV routing**: Fix double `/api/` prefix issue~~ ✅ **DONE**
5. ~~**DAT-004**: Profile default fallback when context missing~~ ✅ **DONE**
6. ~~**PPTX-002/003**: Add workflow state machine and validation gating~~ ✅ **DONE**
7. ~~**SOV-003/004**: Use DataSetRef for input, add lineage to output~~ ✅ **DONE**
8. ~~**Homepage**: Create tool launcher dashboard~~ ✅ **DONE** - Full dashboard with tool cards

### P2 - Medium Priority

9. ~~**Error standardization**: Unified ErrorResponse across all tools~~ ✅ **DONE**
10. ~~**RenderSpec integration**: Connect rendering engine to all tools~~ ✅ **DONE**
11. ~~**Message catalog**: Replace hardcoded messages~~ ✅ **DONE** - Builtin catalogs created
12. ~~**TypeScript types**: Generate from Pydantic contracts~~ ✅ **DONE** - Created `shared/frontend/src/types/contracts.ts`
13. ~~**Lineage optimization**: Add reverse index for children lookup~~ ✅ **DONE** - Added `lineage_edges` table

### P3 - Low Priority

14. ~~**DAT-011**: Multi-format export~~ ✅ **DONE** - Added ExportFormat enum with CSV/Excel
15. ~~**DevTools**: Complete ADR editor, schema validator~~ ✅ **DONE** - Full implementation in `devtools_service.py`
16. ~~**Audit trail**: Integrate AuditTrail contract~~ ✅ **DONE** - Integrated in cancellation system

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
