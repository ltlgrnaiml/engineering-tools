# SESSION_020: DISC-006 Knowledge Archive & RAG System

**Date**: 2025-12-30  
**Focus**: Complete DISC-006 discussion, create xAI prompts for artifact generation  
**Status**: in_progress

---

## Objectives

1. [x] Load and review DISC-006 current state
2. [x] Gather codebase context via GREP for RAG simulation
3. [x] Resolve open questions with USER
4. [x] Update DISC-006 with finalized decisions
5. [ ] Create xAI prompts for each artifact stage (ADR, SPEC, Contract, Plan)
6. [ ] Update discussion INDEX

---

## Design Decisions Made

| Question | Decision |
|----------|----------|
| Embedding Model | Dual-mode: Local (`all-mpnet-base-v2`) + API fallback |
| Chunk Size | Hybrid: content-aware based on file type |
| Sync Frequency | Watchdog (real-time) default, on-demand fallback |
| Retention | Archive everything (soft delete with `archived_at`) |

---

## Cross-DISC Dependencies Identified

- **DISC-003** (Langchain/Langgraph): Phase 4 integration
- **DISC-004** (PII Sanitization): Phase 3 - sanitize before embedding
- **DISC-005** (Embedding Model): Update recommendation to `all-mpnet-base-v2`

---

## Codebase Context Gathered

Key files for RAG context injection:

| File | Purpose |
|------|---------|
| `shared/storage/registry_db.py` | SQLite pattern to follow |
| `gateway/services/llm_service.py` | Existing `llm_logs.db` to migrate |
| `shared/storage/artifact_store.py` | Workspace path handling |
| `shared/contracts/devtools/workflow.py` | Existing artifact enums |

---

## xAI Prompts Generated

- [ ] ADR-0046 prompt
- [ ] SPEC-0035 prompt
- [ ] Contract prompt (`shared/contracts/knowledge/`)
- [ ] PLAN-002 prompt

---

## Next Session Handoff

- Generate actual artifacts using xAI prompts
- Compare xAI output vs manual generation quality
- Begin Phase 1 implementation

