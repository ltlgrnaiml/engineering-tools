# TEAM_004: DAT Refactor Change Plan

**Session ID:** TEAM_004  
**Date:** 2025-12-28  
**Focus:** Deterministic Change Plan for DAT Tool Alignment with SSoT Documents  
**Status:** Planning Complete

---

## Executive Summary

This document provides a deterministic change plan to align the DAT tool implementation with the refactored ADRs, SPECs, and Contracts. The analysis identified **Critical**, **High**, and **Medium** priority gaps between the SSoT documents (source of truth) and the current implementation.

---

## SSoT Document Inventory Analyzed

### ADRs (9 files)
| ID | Title | Status |
|----|-------|--------|
| ADR-0001-DAT | Stage Graph Configuration (8-Stage Pipeline) | Accepted |
| ADR-0003 | Optional Context/Preview Stages | Accepted |
| ADR-0004-DAT | Stage ID Configuration | Accepted |
| ADR-0006 | Table Availability | Accepted |
| ADR-0011 | Profile-Driven Extraction and Adapters | Accepted |
| ADR-0013 | Cancellation Semantics Parse/Export | Accepted |
| ADR-0014 | Parse and Export Artifact Formats | Accepted |
| ADR-0040 | Large File Streaming Strategy (10MB) | Accepted |
| ADR-0041 | DAT UI Horizontal Wizard Pattern | Accepted |

### SPECs (7 files)
| ID | Title | Status |
|----|-------|--------|
| SPEC-DAT-0001 | Stage Graph | Draft |
| SPEC-DAT-0002 | Profile Extraction | Draft |
| SPEC-DAT-0003 | Adapter Interface Registry | Draft |
| SPEC-DAT-0004 | Large File Streaming | Draft |
| SPEC-DAT-0005 | Profile File Management | Draft |
| SPEC-DAT-0006 | Table Availability | Draft |
| SPEC-DAT-0015 | Cancellation Cleanup | Accepted |

### Contracts (6 files)
| File | Version | Status |
|------|---------|--------|
| adapter.py | 1.0.0 | ✅ Complete |
| cancellation.py | 0.1.0 | ✅ Complete |
| jobs.py | 1.0.0 | ✅ Complete |
| profile.py | 0.1.0 | ✅ Complete |
| stage.py | 0.1.0 | ⚠️ Needs Update |
| table_status.py | 0.1.0 | ✅ Complete |

---

## Critical Gap Analysis

### GAP-001: Stage Contract Mismatch [CRITICAL]

**Issue:** The `shared/contracts/dat/stage.py` defines only 3 stages (`PARSE`, `AGGREGATE`, `EXPORT`) but ADR-0001-DAT defines 8 stages.

**SSoT (ADR-0001-DAT):**
```
Discovery → Selection → Context → Table Availability → 
Table Selection → Preview → Parse → Export
```

**Current Contract (`stage.py`):**
```python
class DATStageType(str, Enum):
    PARSE = "parse"
    AGGREGATE = "aggregate"  # NOT in ADR!
    EXPORT = "export"
```

**SPEC-DAT-0001 has DIFFERENT stages:**
```
SOURCE → CONTEXT → PARSE → PREVIEW → AGGREGATE → VALIDATE → EXPORT → DONE
```

**Resolution Required:**
1. Align `stage.py` DATStageType enum with ADR-0001-DAT 8-stage pipeline
2. Update SPEC-DAT-0001 to match ADR-0001-DAT (or vice versa - need decision)
3. Remove `AGGREGATE` stage (not in ADR) or clarify its role

---

### GAP-002: SPEC vs ADR Stage Inconsistency [CRITICAL]

**Issue:** SPEC-DAT-0001 defines different stages than ADR-0001-DAT.

| ADR-0001-DAT Stages | SPEC-DAT-0001 Stages |
|---------------------|----------------------|
| discovery | SOURCE |
| selection | - |
| context | CONTEXT |
| table_availability | - |
| table_selection | - |
| preview | PREVIEW |
| parse | PARSE |
| export | EXPORT |
| - | AGGREGATE |
| - | VALIDATE |
| - | DONE |

**Resolution Required:**
1. **Decision needed:** Which is authoritative - ADR or SPEC?
2. Update SPEC-DAT-0001 to align with ADR-0001-DAT (recommended - ADR is WHY, SPEC is WHAT)
3. Update `stage.py` contracts accordingly

---

### GAP-003: Missing Stage Implementations [HIGH]

**Issue:** Backend stage implementations exist but may not align with contract definitions.

**Current `stages/` directory:**
- ✅ context.py
- ✅ discovery.py
- ✅ export.py
- ✅ parse.py
- ✅ preview.py
- ✅ selection.py
- ✅ table_availability.py
- ✅ table_selection.py

**Action Required:**
1. Audit each stage implementation against ADR-0001-DAT requirements
2. Ensure each stage produces artifacts per ADR-0014
3. Ensure each stage supports cancellation per ADR-0013
4. Verify deterministic stage IDs per ADR-0004-DAT

---

### GAP-004: Profile Contract vs SPEC Alignment [MEDIUM]

**Issue:** `profile.py` contract needs validation against SPEC-DAT-0002 and SPEC-DAT-0005.

**Current Contract Classes:**
- ExtractionProfile ✅
- ColumnMapping ✅
- AggregationRule ✅
- FilePattern ✅
- ValidationRule ✅

**Missing per SPEC-DAT-0005:**
- Profile storage location validation (`apps/data_aggregator/config/profiles/`)
- System vs User profile distinction
- Profile versioning bump logic

---

### GAP-005: Adapter Implementation Gaps [MEDIUM]

**Issue:** Adapters implemented but need validation against SPEC-DAT-0003 requirements.

**Per SPEC-DAT-0003 Requirements:**
| Requirement | CSV | Excel | JSON | Parquet |
|-------------|-----|-------|------|---------|
| probe_schema < 5s | ❓ | ❓ | ❓ | ❓ |
| stream_dataframe | ❓ | N/A | ❓ | ❓ |
| validate_file | ❓ | ❓ | ❓ | ❓ |
| read_dataframe | ❓ | ❓ | ❓ | ❓ |

**Action Required:**
1. Run acceptance criteria tests (`tests/dat/ACCEPTANCE_CRITERIA_ADAPTERS.md`)
2. Fix any failing requirements
3. Achieve 100% compliance score

---

### GAP-006: Large File Streaming Not Fully Implemented [MEDIUM]

**Per ADR-0040 and SPEC-DAT-0004:**
- [ ] 10MB threshold automatic mode selection
- [ ] Tiered file handling (small/medium/large/very_large/massive)
- [ ] Memory cap enforcement (200MB default)
- [ ] Progress updates every 5 seconds
- [ ] Checkpoint preservation on cancellation

**Missing Implementation:**
- `memory_manager.py` (referenced in ADR but not found)
- WebSocket progress endpoint (`/ws/dat/runs/{run_id}/progress`)

---

### GAP-007: Table Availability Stage Alignment [MEDIUM]

**Per ADR-0006 and SPEC-DAT-0006:**
- Table status: AVAILABLE, PARTIAL, MISSING, EMPTY, ERROR
- Status check < 1 second per table
- Health metrics per column
- Independent from Preview stage

**Current `table_status.py` Contract:** ✅ Appears complete

**Action Required:**
1. Verify backend `table_availability.py` stage uses contract correctly
2. Verify frontend `TableAvailabilityPanel.tsx` displays status correctly

---

### GAP-008: Cancellation Checkpointing [MEDIUM]

**Per ADR-0013 and SPEC-DAT-0015:**
- Soft cancellation preserves completed artifacts
- No partial tables/rows/values persisted
- Explicit cleanup (dry_run=True default)
- Audit trail with ISO-8601 UTC timestamps

**Current `cancellation.py` Contract:** ✅ Complete

**Missing Backend:**
- `checkpoint_manager.py` exists but needs validation
- Integration with Parse/Export stages

---

### GAP-009: Frontend Wizard State Integration [MEDIUM]

**Per ADR-0041:**
- Horizontal stepper with 8 stages ✅
- State indicators (pending, active, completed, locked, error) ✅
- Optional stages marked ✅
- Unlock confirmation dialog ❓

**Missing:**
- Cascade unlock confirmation dialog
- Tooltip with gating reason for disabled stages
- WebSocket integration for real-time progress

---

## Deterministic Change Plan

### Phase 1: Contract Alignment [Priority: CRITICAL]

#### CP-1.1: Fix Stage Contract (1 day)
```
File: shared/contracts/dat/stage.py
Action: Replace DATStageType enum to match ADR-0001-DAT
```

**Before:**
```python
class DATStageType(str, Enum):
    PARSE = "parse"
    AGGREGATE = "aggregate"
    EXPORT = "export"
```

**After:**
```python
class DATStageType(str, Enum):
    DISCOVERY = "discovery"
    SELECTION = "selection"
    CONTEXT = "context"
    TABLE_AVAILABILITY = "table_availability"
    TABLE_SELECTION = "table_selection"
    PREVIEW = "preview"
    PARSE = "parse"
    EXPORT = "export"
```

**Acceptance Criteria:**
- [ ] AC-CP-1.1.1: DATStageType has exactly 8 values matching ADR-0001-DAT
- [ ] AC-CP-1.1.2: StageState enum unchanged (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED, LOCKED, UNLOCKED)
- [ ] AC-CP-1.1.3: Stage configurations updated for all 8 stages
- [ ] AC-CP-1.1.4: Ruff linting passes
- [ ] AC-CP-1.1.5: All existing tests updated and passing

#### CP-1.2: Update SPEC-DAT-0001 (0.5 day)
```
File: docs/specs/dat/SPEC-DAT-0001_Stage-Graph.json
Action: Align stages with ADR-0001-DAT
```

**Acceptance Criteria:**
- [ ] AC-CP-1.2.1: SPEC stages match ADR-0001-DAT exactly
- [ ] AC-CP-1.2.2: tier_0_contracts reference updated classes
- [ ] AC-CP-1.2.3: stage_dependencies match ADR cascade rules
- [ ] AC-CP-1.2.4: JSON schema validates

---

### Phase 2: Backend Stage Implementations [Priority: HIGH]

#### CP-2.1: Audit Stage Implementations (1 day)
```
Directory: apps/data_aggregator/backend/src/dat_aggregation/stages/
Action: Verify each stage against ADR requirements
```

**Acceptance Criteria per Stage:**
- [ ] AC-CP-2.1.1: Each stage uses contracts from `shared/contracts/dat/`
- [ ] AC-CP-2.1.2: Each stage computes deterministic stage_id (ADR-0004-DAT)
- [ ] AC-CP-2.1.3: Parse stage outputs Parquet (ADR-0014)
- [ ] AC-CP-2.1.4: Export stage supports multi-format (ADR-0014)
- [ ] AC-CP-2.1.5: Context/Preview optional handling (ADR-0003)
- [ ] AC-CP-2.1.6: Cancellation checkpointing (ADR-0013)

#### CP-2.2: Implement Memory Manager (0.5 day)
```
File: apps/data_aggregator/backend/core/memory_manager.py (NEW)
Action: Create memory manager for large file handling
```

**Acceptance Criteria:**
- [ ] AC-CP-2.2.1: Tracks current memory usage
- [ ] AC-CP-2.2.2: Enforces max_memory_mb limit (default 200MB)
- [ ] AC-CP-2.2.3: Triggers garbage collection when threshold reached
- [ ] AC-CP-2.2.4: Integrates with StreamOptions from adapter contract

#### CP-2.3: Implement Progress WebSocket (0.5 day)
```
File: apps/data_aggregator/backend/api/websocket.py (NEW)
Action: Create WebSocket endpoint for progress updates
```

**Acceptance Criteria:**
- [ ] AC-CP-2.3.1: Endpoint at `/ws/dat/runs/{run_id}/progress`
- [ ] AC-CP-2.3.2: Sends updates every 5 seconds during streaming
- [ ] AC-CP-2.3.3: Payload matches SPEC-DAT-0004 format
- [ ] AC-CP-2.3.4: Handles disconnect gracefully

---

### Phase 3: Adapter Compliance [Priority: HIGH]

#### CP-3.1: Run Adapter Acceptance Tests (0.5 day)
```
Command: pytest tests/dat/test_adapters.py -v --tb=short
Action: Execute all 91 acceptance criteria from ACCEPTANCE_CRITERIA_ADAPTERS.md
```

**Acceptance Criteria:**
- [ ] AC-CP-3.1.1: All AC-1.x (Interface Compliance) passing
- [ ] AC-CP-3.1.2: All AC-2.x (Registry) passing
- [ ] AC-CP-3.1.3: All AC-3.x (CSV Adapter) passing
- [ ] AC-CP-3.1.4: All AC-4.x (Excel Adapter) passing
- [ ] AC-CP-3.1.5: All AC-5.x (JSON Adapter) passing
- [ ] AC-CP-3.1.6: All AC-6.x (Cross-Cutting) passing
- [ ] AC-CP-3.1.7: All AC-7.x (Test Coverage) passing
- [ ] AC-CP-3.1.8: 100% compliance score (91/91)

#### CP-3.2: Fix Failing Criteria (1-2 days, depends on failures)
```
Action: Address any failing acceptance criteria
```

---

### Phase 4: Frontend Alignment [Priority: MEDIUM]

#### CP-4.1: Add Unlock Confirmation Dialog (0.5 day)
```
File: apps/data_aggregator/frontend/src/components/wizard/UnlockConfirmDialog.tsx (NEW)
Action: Create confirmation dialog per ADR-0041
```

**Acceptance Criteria:**
- [ ] AC-CP-4.1.1: Dialog shows list of downstream stages to unlock
- [ ] AC-CP-4.1.2: Confirm/Cancel buttons
- [ ] AC-CP-4.1.3: Integrated with DATWizard onBack handler

#### CP-4.2: Add Gating Tooltips (0.5 day)
```
File: apps/data_aggregator/frontend/src/components/wizard/DATWizard.tsx
Action: Add tooltips explaining why stages are disabled
```

**Acceptance Criteria:**
- [ ] AC-CP-4.2.1: Disabled stages show tooltip on hover
- [ ] AC-CP-4.2.2: Tooltip explains gating reason (e.g., "Selection must be locked first")
- [ ] AC-CP-4.2.3: Uses ADR-0041 gating rules

#### CP-4.3: WebSocket Progress Integration (0.5 day)
```
File: apps/data_aggregator/frontend/src/hooks/useProgress.ts (NEW)
Action: Create hook for WebSocket progress updates
```

**Acceptance Criteria:**
- [ ] AC-CP-4.3.1: Connects to `/ws/dat/runs/{run_id}/progress`
- [ ] AC-CP-4.3.2: Updates ParsePanel progress bar
- [ ] AC-CP-4.3.3: Shows ETA when available
- [ ] AC-CP-4.3.4: Handles reconnection gracefully

---

### Phase 5: Testing & Validation [Priority: HIGH]

#### CP-5.1: Contract Validation Tests (0.5 day)
```
File: tests/dat/test_contract_alignment.py (NEW)
Action: Create tests validating contracts match ADRs/SPECs
```

**Acceptance Criteria:**
- [ ] AC-CP-5.1.1: Test DATStageType matches ADR-0001-DAT stages
- [ ] AC-CP-5.1.2: Test checkpoint types match ADR-0013
- [ ] AC-CP-5.1.3: Test table status values match ADR-0006
- [ ] AC-CP-5.1.4: Test adapter capabilities match ADR-0040

#### CP-5.2: Integration Tests (1 day)
```
File: tests/integration/test_dat_pipeline.py (NEW)
Action: End-to-end pipeline tests
```

**Acceptance Criteria:**
- [ ] AC-CP-5.2.1: Discovery → Export pipeline completes
- [ ] AC-CP-5.2.2: Optional stages can be skipped
- [ ] AC-CP-5.2.3: Cancellation preserves completed work
- [ ] AC-CP-5.2.4: Large file (>10MB) uses streaming

#### CP-5.3: Regression Tests (0.5 day)
```
Command: pytest tests/dat/ -v
Action: Ensure all existing tests pass
```

**Acceptance Criteria:**
- [ ] AC-CP-5.3.1: test_state_machine.py passing
- [ ] AC-CP-5.3.2: test_stages.py passing
- [ ] AC-CP-5.3.3: test_adapters.py passing
- [ ] AC-CP-5.3.4: test_profiles.py passing

---

## Implementation Order

| Order | Change Plan | Effort | Dependencies |
|-------|-------------|--------|--------------|
| 1 | CP-1.1: Fix Stage Contract | 1 day | None |
| 2 | CP-1.2: Update SPEC-DAT-0001 | 0.5 day | CP-1.1 |
| 3 | CP-5.3: Regression Tests | 0.5 day | CP-1.1 |
| 4 | CP-2.1: Audit Stage Implementations | 1 day | CP-1.1 |
| 5 | CP-3.1: Run Adapter Acceptance | 0.5 day | None |
| 6 | CP-3.2: Fix Failing Criteria | 1-2 days | CP-3.1 |
| 7 | CP-2.2: Memory Manager | 0.5 day | CP-2.1 |
| 8 | CP-2.3: Progress WebSocket | 0.5 day | CP-2.2 |
| 9 | CP-4.1: Unlock Confirmation | 0.5 day | None |
| 10 | CP-4.2: Gating Tooltips | 0.5 day | None |
| 11 | CP-4.3: WebSocket Progress | 0.5 day | CP-2.3 |
| 12 | CP-5.1: Contract Validation | 0.5 day | CP-1.1 |
| 13 | CP-5.2: Integration Tests | 1 day | All above |

**Total Estimated Effort:** 8-9 days

---

## Validation Commands

```bash
# Phase 1: Contract Alignment
ruff check shared/contracts/dat/stage.py
pytest tests/dat/test_contracts.py -v

# Phase 2: Backend
pytest tests/dat/test_stages.py -v
pytest tests/dat/test_state_machine.py -v

# Phase 3: Adapters
pytest tests/dat/test_adapters.py -v --cov=apps/data_aggregator/backend/adapters

# Phase 4: Frontend
cd apps/data_aggregator/frontend && npm run lint
cd apps/data_aggregator/frontend && npm test

# Phase 5: Full Integration
pytest tests/dat/ -v
pytest tests/integration/test_dat_pipeline.py -v
```

---

## Open Questions for USER

1. **GAP-001/002 Resolution:** ADR-0001-DAT and SPEC-DAT-0001 have different stage names. Which is authoritative?
   - **Recommendation:** ADR is WHY (authoritative), SPEC is WHAT. Update SPEC to match ADR.

2. **AGGREGATE Stage:** The contract has `AGGREGATE` but ADR does not. Is aggregation happening within Parse stage?
   - **Recommendation:** Remove AGGREGATE from contract; aggregation is part of Parse per ADR-0014.

3. **Priority Sequence:** Do you want to address CRITICAL gaps first, or should we run adapter acceptance tests in parallel?

---

## Next Session Handoff

**Completed:**
- Full SSoT document analysis (9 ADRs, 7 SPECs, 6 Contracts)
- Gap identification with severity levels
- Deterministic change plan with 13 action items
- Acceptance criteria for each action item

**Ready for Implementation:**
- CP-1.1 can begin immediately after USER confirms GAP-001/002 resolution
- CP-3.1 (adapter acceptance tests) can run in parallel

**Blockers:**
- Decision needed on AGGREGATE stage disposition
- Decision needed on ADR vs SPEC authority for stage names
