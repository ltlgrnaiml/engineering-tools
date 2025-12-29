# DAT Refactor Patch Plan - Master Index

**Created**: 2025-12-29  
**Session**: TEAM_017_COMPREHENSIVE_PATCH_PLAN  
**Purpose**: Complete executable patch plan for DAT refactor, tiered for smaller model execution

---

## Plan Structure

This patch plan is organized into 4 tiers, each building on the previous:

| Tier | File | Purpose | Audience |
|------|------|---------|----------|
| **1** | `01_PROJECT_ACCEPTANCE_CRITERIA.md` | Project-level success criteria | Planning/Review |
| **2** | `02_FILE_CHANGE_SPECIFICATIONS.md` | File-by-file change specs | Development |
| **3** | `03_IMPLEMENTATION_DETAILS.md` | Function-level code snippets | Implementation |
| **4** | `04_EXECUTION_CHECKLIST.md` | Step-by-step instructions | Execution |

---

## Execution Order

### Phase 1: Foundation (M1, M2)
1. **M1**: Unify Adapter Implementations
2. **M2**: API Path Normalization (Remove /v1)

### Phase 2: FSM Correctness (M3)
3. **M3**: Externalize Stage Graph Configuration

### Phase 3: Determinism (M4)
4. **M4**: Align Stage ID Generation

### Phase 4: Performance (M5, M6, M7)
5. **M5**: Table Availability Fast Probe
6. **M6**: Large File Streaming
7. **M7**: Parse/Export Artifact Formats

### Phase 5: Reliability (M8, M9)
8. **M8**: Cancellation Checkpointing
9. **M9**: Profile CRUD

---

## Quick Reference

### Key Directories
```
shared/contracts/dat/           # Tier-0 contracts (SOURCE OF TRUTH)
apps/data_aggregator/backend/   # DAT backend
  ├── adapters/                 # Contract-style adapters (KEEP)
  ├── src/dat_aggregation/
  │   ├── adapters/             # Legacy adapters (DELETE)
  │   ├── api/routes.py         # API routes
  │   └── core/state_machine.py # FSM implementation
apps/data_aggregator/frontend/  # DAT frontend
gateway/                        # API gateway
```

### Key Files to Modify
- `gateway/main.py` - Remove /v1 prefix
- `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py` - Remove /v1, add endpoints
- `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py` - Config injection
- `shared/contracts/dat/stage_graph.py` - NEW: Stage graph config contract
- All frontend `*.tsx` files - Update API paths

### Key Files to Delete
- `apps/data_aggregator/backend/src/dat_aggregation/adapters/` (entire directory)

---

## Validation Commands

```bash
# After each milestone:
ruff check .
pytest tests/dat/ -v

# Final validation:
pytest tests/ -v
python -c "from shared.contracts.dat import *"
```

---

## Dependencies Between Milestones

```
M1 (Adapters) ──────────────┬──────────────> M5 (Fast Probe)
                            │
M2 (API Paths) ─────────────┤
                            │
M3 (FSM Config) ────────────┼──────────────> M8 (Cancellation)
                            │
M4 (Stage IDs) ─────────────┘

M6 (Streaming) ─────────────────────────────> M7 (Artifact Formats)

M9 (Profile CRUD) - Independent
```

---

## Reading Order for Execution

1. Start with `01_PROJECT_ACCEPTANCE_CRITERIA.md` to understand success criteria
2. Read `02_FILE_CHANGE_SPECIFICATIONS.md` for the specific files
3. Use `03_IMPLEMENTATION_DETAILS.md` for exact code changes
4. Follow `04_EXECUTION_CHECKLIST.md` step-by-step

---

*Next: Read `01_PROJECT_ACCEPTANCE_CRITERIA.md`*
