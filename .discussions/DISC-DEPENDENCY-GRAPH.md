# DISC Dependency Graph

> **Auto-generated from DISC metadata. Update when dependencies change.**
> **Last Updated**: 2025-12-30 | SESSION_020

---

## Dependency Visualization

```
Legend:
  [RESOLVED] = Discussion complete, artifacts created
  [ACTIVE]   = In progress
  [STAGED]   = Waiting for dependencies
  [BLOCKED]  = Cannot proceed until dependency resolves
  ───────►   = "depends on" (arrow points to dependency)
  - - - - ►  = "soft dependency" (can stub)

                         ┌──────────────────┐
                         │    DISC-001      │
                         │    DevTools      │
                         │    [RESOLVED]    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │    DISC-002      │
                         │    AI-Lite       │
                         │    [ACTIVE]      │
                         └────────┬─────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
            ▼                     ▼                     ▼
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   │    DISC-003      │  │    DISC-004      │  │    DISC-005      │
   │    Langchain     │  │    PII Sanitize  │  │    Embedding     │
   │    [RESOLVED]    │  │    [RESOLVED]    │  │    [RESOLVED]    │
   └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
            │                     │                     │
            │                     └──────────┬──────────┘
            │                                │
            │   ┌────────────────────────────┘
            │   │
            ▼   ▼
   ┌──────────────────┐
   │    DISC-006      │
   │    Knowledge     │
   │    Archive/RAG   │
   │    [ACTIVE]      │
   └──────────────────┘
```

---

## Dependency Matrix

| DISC | 001 | 002 | 003 | 004 | 005 | 006 |
|------|-----|-----|-----|-----|-----|-----|
| **001** | - | - | - | - | - | - |
| **002** | FS | - | - | - | - | - |
| **003** | - | FS | - | - | - | - |
| **004** | - | FS | - | - | - | - |
| **005** | - | FS | - | - | - | - |
| **006** | - | - | FF | FF | FF | - |

**Legend**: FS = Finish-to-Start, FF = Finish-to-Finish, SS = Start-to-Start

---

## Level Analysis (Topological Sort)

| Level | DISCs | Can Start When |
|-------|-------|----------------|
| L0 | DISC-002 | Immediately (DISC-001 resolved) |
| L1 | DISC-003, DISC-004, DISC-005 | After DISC-002 active |
| L2 | DISC-006 | After L1 complete (or stubbed) |

---

## Critical Path

The longest dependency chain determines minimum completion time:

```
DISC-002 → DISC-005 → DISC-006 (Phase 3)
         → DISC-004 → DISC-006 (Phase 3)
         → DISC-003 → DISC-006 (Phase 4)
```

**Bottleneck**: DISC-006 Phase 3 requires BOTH DISC-004 and DISC-005.

---

## Stub Strategy

When dependencies aren't complete, use stubs to unblock work:

| DISC | Stub Location | Stub Behavior |
|------|---------------|---------------|
| DISC-003 | `gateway/services/langchain_stub.py` | Pass-through to existing xAI calls |
| DISC-004 | `shared/sanitization/pii_stub.py` | Return content unchanged |
| DISC-005 | `shared/embedding/embedding_stub.py` | Use `all-mpnet-base-v2` default |

---

## Multi-DISC Plan Rules

### Rule 1: Single Aggregator Plan
When multiple DISCs converge on one feature, create ONE master plan that coordinates.

### Rule 2: Stub Everything Possible
Define interfaces early. Implement stubs. Replace with real impl when dependency resolves.

### Rule 3: Phase Alignment
Align plan phases with dependency levels:
- Phase 0: Resolve/stub dependencies
- Phase N: Work that depends on Phase N-1

### Rule 4: Explicit Blockers
Each task must declare if it's blocked by a stub:
```json
{
  "id": "T-M3-05",
  "description": "Integrate PII sanitizer",
  "blocked_by": "DISC-004",
  "stub_available": true
}
```

### Rule 5: Resolution Tracking
When a dependency DISC is resolved, update all dependent plans:
- Replace stubs with real implementations
- Remove `blocked_by` markers
- Run integration tests

---

## Current State Summary

| DISC | Status | Blocking | Blocked By |
|------|--------|----------|------------|
| DISC-001 | ✅ Resolved | Nothing | Nothing |
| DISC-002 | 🔄 Active | DISC-006 | Nothing |
| DISC-003 | ✅ Resolved | DISC-006 Phase 4 | Nothing |
| DISC-004 | ✅ Resolved | DISC-006 Phase 3 | Nothing |
| DISC-005 | ✅ Resolved | DISC-006 Phase 3 | Nothing |
| DISC-006 | 🔄 Active | Nothing | Nothing (all deps resolved) |

---

## Recommended Execution Order

1. ~~**Complete DISC-002** (AI-Lite Prompts)~~ - 🔄 In progress
2. ~~**Start DISC-005** (Embedding Model)~~ - ✅ Resolved: `all-mpnet-base-v2`
3. ~~**Start DISC-004** (PII Sanitization)~~ - ✅ Resolved: Regex MVP
4. **Start DISC-006 Phase 1-2** (Archive Core, Search) - ✅ UNBLOCKED
5. ~~**Complete DISC-004, DISC-005**~~ - ✅ Both resolved
6. **Start DISC-006 Phase 3** (RAG) - ✅ UNBLOCKED
7. ~~**Start DISC-003** (Langchain)~~ - ✅ Resolved: Langchain + Langgraph
8. **Start DISC-006 Phase 4** (Integration) - ✅ UNBLOCKED

