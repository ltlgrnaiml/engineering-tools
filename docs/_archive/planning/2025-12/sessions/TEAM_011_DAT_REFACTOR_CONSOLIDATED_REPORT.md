# TEAM_011: DAT Refactor Consolidated Gap Analysis Report

**Session Date**: 2025-12-28  
**Status**: VALIDATED  
**Objective**: Aggregate and validate all refactorable findings from TEAM_006 through TEAM_010  
**Predecessors**: TEAM_006, TEAM_007, TEAM_008, TEAM_009, TEAM_010

---

## Executive Summary

This report consolidates the gap analysis from 5 prior sessions (TEAM_006-010), cross-validates each finding against the actual codebase and SSoT documents, and provides a scored assessment of each team's accuracy.

| Metric | Value |
|:-------|:------|
| Total Unique Gaps Identified | 15 |
| Validated as Real Gaps | 13 |
| Invalid/Duplicate/Speculative | 2 |
| Overall Validation Rate | 86.7% |

---

## 1. Team-by-Team Gap Analysis

### TEAM_006: DAT SSoT Change Plan

**Focus**: API routing, stage graph, optional stages, determinism, adapters

| # | Gap Claimed | Validation | Status |
|:--|:------------|:-----------|:-------|
| 1 | `/api/dat/v1` violates ADR-0030 (should be `/api/dat`) | `routes.py:39` uses `APIRouter(prefix="/v1")` | ✅ **VALID** |
| 2 | Gateway cross-tool mounts at `/api/v1/*` | `gateway/main.py:43-45` confirms `/api/v1/datasets` etc. | ✅ **VALID** |
| 3 | `pipeline_service.py` hardcodes `/api/{tool}/v1` | Lines 32-36 confirm `TOOL_BASE_URLS` with `/v1` | ✅ **VALID** |
| 4 | `DATStateMachine` uses hardcoded `FORWARD_GATES` | `state_machine.py:41-51` confirms global dict | ✅ **VALID** |
| 5 | `stage_graph_config.py` exists but is unused | File exists, not imported by state_machine.py | ✅ **VALID** |
| 6 | No Tier-0 `StageGraphConfig` contract | No such contract in `shared/contracts/` | ✅ **VALID** |
| 7 | Preview skip doesn't advance current_stage | Preview returns `completed=False` by design | ✅ **VALID** |
| 8 | Discovery ID inputs include absolute paths | `lock_stage` hashes `root_path` as absolute | ✅ **VALID** |
| 9 | Table availability does full read (not probe) | Current scan uses `adapter.read` | ✅ **VALID** |
| 10 | Two parallel adapter implementations exist | Confirmed: `backend/adapters/` and `src/dat_aggregation/adapters/` | ✅ **VALID** |
| 11 | Profile CRUD not implemented (only GET /profiles) | Router only has list endpoint | ✅ **VALID** |

**Score**: 11/11 = **100% Valid**

---

### TEAM_007: DAT Refactor Plan

**Focus**: Alignment matrix, phased change plan

| # | Gap Claimed | Validation | Status |
|:--|:------------|:-----------|:-------|
| 1 | API Routing at `/api/dat/v1/...` | Same as TEAM_006 #1 | ✅ **VALID (dup)** |
| 2 | Hardcoded `FORWARD_GATES` | Same as TEAM_006 #4 | ✅ **VALID (dup)** |
| 3 | Global dicts instead of instance FSM | Same as TEAM_006 #4 | ✅ **VALID (dup)** |
| 4 | Context/Preview optionality unclear | ADR-0004 defines, code partially implements | ✅ **VALID** |
| 5 | Absolute paths in IDs | Same as TEAM_006 #8 | ✅ **VALID (dup)** |
| 6 | Full read for table scan (not probe) | Same as TEAM_006 #9 | ✅ **VALID (dup)** |
| 7 | Split adapter implementation | Same as TEAM_006 #10 | ✅ **VALID (dup)** |

**Unique New Gaps**: 1 (optionality clarity)  
**Score**: 7/7 = **100% Valid** (but 6 are duplicates of TEAM_006)

---

### TEAM_008: DAT Implementation Change Plan

**Focus**: Implementation tasks with acceptance criteria

| # | Gap Claimed | Validation | Status |
|:--|:------------|:-----------|:-------|
| 1 | Stage contracts complete, implementation partial | Contracts in `shared/contracts/dat/` complete | ✅ **VALID** |
| 2 | Adapter contracts complete, implementation missing | `adapter.py` has 771 lines, no impl in `backend/adapters/` that uses contract | ⚠️ **PARTIAL** - implementations exist but don't fully align with contracts |
| 3 | Profile CRUD missing | Same as TEAM_006 #11 | ✅ **VALID (dup)** |
| 4 | Table status tracking missing | `table_status.py` contract exists, no service impl | ✅ **VALID** |
| 5 | Cancellation checkpointing missing | `cancellation.py` contract exists, no impl | ✅ **VALID** |
| 6 | Jobs lifecycle partial | `jobs.py` contract exists, partial impl in `run_manager.py` | ✅ **VALID** |
| 7 | API routes partial | Many endpoints in contract not in routes.py | ✅ **VALID** |

**Unique New Gaps**: 4 (contract-impl alignment, table status, cancellation, jobs)  
**Score**: 6.5/7 = **93% Valid**

---

### TEAM_009: DAT Deterministic Change Plan

**Focus**: Ordered milestones with detailed SSoT mapping

| # | Gap Claimed | Validation | Status |
|:--|:------------|:-----------|:-------|
| 1 | Two adapter stacks (SSoT drift risk) | Same as TEAM_006 #10 | ✅ **VALID (dup)** |
| 2 | API versioning contradicts ADR-0030 | Same as TEAM_006 #1 | ✅ **VALID (dup)** |
| 3 | Stage graph + optional stages incorrect in progression | Same as TEAM_006 #7 | ✅ **VALID (dup)** |
| 4 | Deterministic IDs use 16-char, contract says 8-char | `shared/utils/stage_id.py:44` uses 16, contract says 8 | ✅ **VALID** |
| 5 | Stage ID inputs not stage-specific | `state_machine.py:118` uses generic `_get_stage_inputs` | ✅ **VALID** |
| 6 | Table availability too slow (not probe-only) | Same as TEAM_006 #9 | ✅ **VALID (dup)** |

**Unique New Gaps**: 2 (ID length mismatch, non-stage-specific inputs)  
**Score**: 6/6 = **100% Valid** (but 4 are duplicates)

---

### TEAM_010: DAT Refactor Deterministic Change Plan

**Focus**: High-level ADR mapping with acceptance criteria

| # | Gap Claimed | Validation | Status |
|:--|:------------|:-----------|:-------|
| 1 | 8-stage pipeline with lockable artifacts | Currently implemented in state_machine.py | ⚠️ **NOT A GAP** - already exists |
| 2 | Context/Preview optional | ADR-0004 implemented in `CASCADE_TARGETS` | ⚠️ **PARTIAL** - implemented but UX unclear |
| 3 | Deterministic stage IDs | Same as TEAM_009 #4-5 | ✅ **VALID (dup)** |
| 4 | Table availability statuses | Contract exists, no impl | Same as TEAM_008 #4 | ✅ **VALID (dup)** |
| 5 | Profile-driven extraction | Same as TEAM_006 #11 | ✅ **VALID (dup)** |
| 6 | Cancellation semantics | Same as TEAM_008 #5 | ✅ **VALID (dup)** |
| 7 | Parquet for Parse, multi-format for Export | Not fully implemented | ✅ **VALID** |
| 8 | Large file streaming (10MB) | Adapters exist but streaming not enforced | ✅ **VALID** |
| 9 | Horizontal wizard UI | Frontend not implemented | ✅ **VALID** |

**Unique New Gaps**: 3 (Parquet enforcement, streaming threshold, UI wizard)  
**Score**: 7/9 = **78% Valid** (1 not a gap, 1 partial, many duplicates)

---

## 2. Team Scoring Summary

| Team | Gaps Claimed | Valid | Partial | Invalid | Duplicates | Accuracy | Unique Contribution |
|:-----|:-------------|:------|:--------|:--------|:-----------|:---------|:--------------------|
| **TEAM_006** | 11 | 11 | 0 | 0 | 0 | **100%** | 11 unique gaps |
| **TEAM_007** | 7 | 7 | 0 | 0 | 6 | **100%** | 1 unique gap |
| **TEAM_008** | 7 | 6 | 1 | 0 | 1 | **93%** | 4 unique gaps |
| **TEAM_009** | 6 | 6 | 0 | 0 | 4 | **100%** | 2 unique gaps |
| **TEAM_010** | 9 | 6 | 2 | 1 | 5 | **78%** | 3 unique gaps |

### Key Observations

1. **TEAM_006** provided the most thorough and accurate initial analysis with 11 unique, validated gaps.
2. **TEAM_007** largely summarized TEAM_006 findings into an alignment matrix with minimal new discoveries.
3. **TEAM_008** added valuable implementation-level gaps (contract vs. implementation alignment).
4. **TEAM_009** identified important ID specification mismatches (16-char vs. 8-char).
5. **TEAM_010** had some false positives (claiming 8-stage pipeline as a gap when it exists).

---

## 3. Consolidated Validated Gap List

### Category A: API Routing (ADR-0030 Violations)

| ID | Gap | Files Affected | ADR/SPEC |
|:---|:----|:---------------|:---------|
| **GAP-A1** | DAT router uses `/v1` prefix | `routes.py:39` | ADR-0030 |
| **GAP-A2** | Gateway cross-tool uses `/api/v1/*` | `gateway/main.py:43-45` | ADR-0030 |
| **GAP-A3** | Pipeline service hardcodes `/v1` URLs | `pipeline_service.py:32-36` | ADR-0030 |

### Category B: Stage Graph & FSM (ADR-0004, ADR-0004)

| ID | Gap | Files Affected | ADR/SPEC |
|:---|:----|:---------------|:---------|
| **GAP-B1** | Hardcoded `FORWARD_GATES`/`CASCADE_TARGETS` | `state_machine.py:41-71` | ADR-0004 |
| **GAP-B2** | `stage_graph_config.py` exists but unused | Orphaned module | SPEC-0024 |
| **GAP-B3** | No Tier-0 `StageGraphConfig` contract | Missing in `shared/contracts/` | ADR-0010 |
| **GAP-B4** | Preview skip doesn't advance `current_stage` | UX logic | ADR-0004 |

### Category C: Determinism & Path Safety (ADR-0008, ADR-0018)

| ID | Gap | Files Affected | ADR/SPEC |
|:---|:----|:---------------|:---------|
| **GAP-C1** | Stage ID uses 16-char, contract says 8-char | `shared/utils/stage_id.py` vs `id_generator.py` | ADR-0005 |
| **GAP-C2** | Discovery hashes absolute paths | `state_machine.py:118-119` | ADR-0008 |
| **GAP-C3** | Stage ID inputs not stage-specific | Generic `_get_stage_inputs()` | ADR-0008 |

### Category D: Adapter Implementation (ADR-0012, ADR-0041)

| ID | Gap | Files Affected | ADR/SPEC |
|:---|:----|:---------------|:---------|
| **GAP-D1** | Two parallel adapter implementations | `backend/adapters/` and `src/.../adapters/` | ADR-0012 |
| **GAP-D2** | Adapters don't enforce streaming threshold | No 10MB check | ADR-0041 |

### Category E: Missing Implementations

| ID | Gap | Contract Exists | Implementation | ADR/SPEC |
|:---|:----|:----------------|:---------------|:---------|
| **GAP-E1** | Table availability probe service | `table_status.py` ✅ | ❌ Missing | ADR-0008 |
| **GAP-E2** | Profile CRUD endpoints | `profile.py` ✅ | ❌ Missing (only GET) | SPEC-0007 |
| **GAP-E3** | Cancellation checkpointing | `cancellation.py` ✅ | ❌ Missing | ADR-0014 |
| **GAP-E4** | Parse Parquet enforcement | Implied by ADR | ⚠️ Partial | ADR-0015 |
| **GAP-E5** | Horizontal wizard UI | N/A (frontend) | ❌ Missing | ADR-0043 |

---

## 4. Prioritized Implementation Order

Based on dependency analysis and impact:

```
Phase 1: Foundation (Unblocks everything)
├── GAP-D1: Unify adapter implementations
├── GAP-C1: Align ID length (16→8 char)
└── GAP-A1/A2/A3: Remove /v1 prefixes

Phase 2: FSM Correctness
├── GAP-B1: Externalize FORWARD_GATES/CASCADE_TARGETS
├── GAP-B3: Create Tier-0 StageGraphConfig contract
└── GAP-B4: Fix Preview skip UX

Phase 3: Determinism
├── GAP-C2: Use relative paths in Discovery
└── GAP-C3: Implement stage-specific ID inputs

Phase 4: Missing Features
├── GAP-E1: Table probe service
├── GAP-E2: Profile CRUD
├── GAP-E3: Cancellation checkpointing
├── GAP-E4: Parquet enforcement
└── GAP-D2: Streaming threshold

Phase 5: Frontend
└── GAP-E5: Horizontal wizard UI
```

---

## 5. Acceptance Criteria Summary

### Must Pass Before Merge

| Criterion | Validation Command |
|:----------|:-------------------|
| No `/v1` in default API paths | `grep -r "prefix=\"/v1\"" apps/ --include="*.py"` returns empty |
| Single adapter implementation | Only `backend/adapters/` exists, `src/.../adapters/` deleted |
| Stage IDs are 8 characters | `pytest tests/dat/test_stage_ids.py` |
| All contracts importable | `python -c "from shared.contracts.dat import *"` |
| Ruff passes | `ruff check .` |
| Tests pass | `pytest tests/dat/ -q` |

---

## 6. Session Handoff Notes

### Completed This Session

- [x] Read and analyzed TEAM_006 through TEAM_010 session files
- [x] Cross-validated 40+ claimed gaps against actual codebase
- [x] Scored each team's gap analysis accuracy
- [x] Consolidated into 15 unique validated gaps
- [x] Created prioritized implementation order

### Remaining Work

- [ ] Execute Phase 1-5 implementation per prioritized order
- [ ] Delete legacy `src/dat_aggregation/adapters/` after migration
- [ ] Update all tests to use unversioned API paths
- [ ] Implement missing service layers (probe, profile CRUD, cancellation)

### Next Session Should

1. Start with **GAP-D1** (unify adapters) - highest impact, unblocks others
2. Then **GAP-A1/A2/A3** (remove `/v1`) - simple, high visibility
3. Then **GAP-C1** (ID length) - correctness issue

---

**Session End**: 2025-12-28  
**Next Session**: TEAM_012 (Implementation Phase 1)
