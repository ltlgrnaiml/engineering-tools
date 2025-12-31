# DISC-003: Langchain/Langgraph Integration

**Status**: resolved  
**Created**: 2025-12-30  
**Author**: AI-Assisted  
**Depends On**: DISC-002

---

## Summary

Integrate Langchain and Langgraph to provide unified LLM orchestration, tool calling, and multi-step agent workflows for the engineering tools platform.

---

## Context

Currently using direct xAI API calls. Langchain/Langgraph would provide:

- Unified interface across LLM providers
- Built-in retry, caching, and observability
- State machines for complex multi-step generation
- Tool/function calling abstraction
- Memory and conversation history

---

## Requirements (To Be Filled)

### Functional

- [ ] FR-1: TBD
- [ ] FR-2: TBD

### Non-Functional

- [ ] NFR-1: TBD
- [ ] NFR-2: TBD

---

## Options Considered

### Option A: Langchain Only

**Pros**: Simpler, well-documented, large ecosystem  
**Cons**: Limited state management for complex flows

### Option B: Langchain + Langgraph

**Pros**: Full state machine support, parallel execution, cycles  
**Cons**: Higher complexity, newer/less stable

### Option C: Custom Orchestration

**Pros**: Full control, no dependencies  
**Cons**: Reinventing the wheel, maintenance burden

---

## Decision

**Chosen: Option B - Langchain + Langgraph**

**Rationale**:
1. Full state machine support needed for complex multi-step artifact generation
2. Parallel execution and cycles enable sophisticated workflows
3. Industry momentum and ecosystem growth
4. Compatible with future RAG integration (DISC-006)

**Implementation Approach**:
- Wrap existing xAI calls with Langchain adapter
- Use Langgraph for multi-step workflows (DISC→ADR→SPEC→Plan)
- Memory persistence via `knowledge.db` (aligns with DISC-006)

---

## Deferred Decisions

| Decision | Reason | Resolution |
|----------|--------|------------|
| ~~LangSmith tier~~ | ~~Depends on usage patterns~~ | **Resolved**: Using Phoenix (free, local) instead |
| Agent patterns | Need real workflow data | Deferred to future iteration |

---

## Open Questions

1. ~~Which LangSmith tier for observability?~~ → **Deferred**
2. ~~How to migrate existing LLM service calls?~~ → **Adapter pattern**
3. ~~Agent patterns for artifact generation?~~ → **Deferred to implementation**
4. ~~Memory persistence strategy?~~ → **Use knowledge.db (DISC-006)**

---

## Next Steps

- [x] Decision: Langchain + Langgraph ✅
- [x] Create adapter for existing xAI calls ✅ (`gateway/services/llm/xai_langchain.py`)
- [x] Phoenix observability integration ✅ (`gateway/services/observability/`)
- [x] RAG chain with Knowledge Archive ✅ (`gateway/services/llm/rag_chain.py`)
- [ ] Design first Langgraph workflow (future)
- [ ] Integrate with knowledge.db for memory (future)

## Implementation Completed (SESSION_022)

| File | Purpose |
|------|---------|
| `gateway/services/llm/__init__.py` | LLM module |
| `gateway/services/llm/xai_langchain.py` | xAI LangChain adapter |
| `gateway/services/llm/rag_chain.py` | RAG chain with Knowledge Archive |
| `gateway/services/observability/__init__.py` | Observability module |
| `gateway/services/observability/phoenix_tracer.py` | Phoenix initialization |
| `scripts/demo_phoenix_rag.py` | Demo script |

