# DISC-007: Unified xAI Agent Wrapper

> **Status**: `active`
> **Created**: 2025-12-31
> **Updated**: 2025-12-31 (Q1-Q4 answered)
> **Author**: USER + Cascade
> **AI Session**: SESSION_023
> **Depends On**: DISC-003, DISC-006
> **Blocks**: None
> **Dependency Level**: L2

---

## Summary

Design and implement a unified `XAIAgent` wrapper that combines LangChain's RAG capabilities with xAI's native SDK agentic tools (web search, X search, code execution, MCP) under a single interface with unified Phoenix observability.

---

## Context

### Background

The project currently has two separate integration paths for xAI:

1. **LangChain Path** (`gateway/services/llm/`):
   - `XAIChatModel` - wraps `ChatOpenAI` with xAI base URL
   - `RAGChain` - integrates with Knowledge Archive
   - Phoenix tracing enabled
   - Limited to standard chat completions + client-side function calling

2. **Native xAI Capabilities** (not yet integrated):
   - **Server-side agentic tools**: web_search, x_search, code_execution
   - **MCP integration**: Connect to external tool servers
   - **Collections/Document search**: xAI-hosted knowledge bases
   - **Citations**: Inline `[[1]](url)` markdown with position tracking
   - **Verbose streaming**: Real-time tool call visibility

### Trigger

After scraping and analyzing the complete xAI documentation (`docs/scraped/xai/`), it became clear that xAI offers powerful agentic capabilities that are inaccessible through the OpenAI-compatible API that LangChain uses. These features would significantly enhance the platform's AI capabilities.

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: Single `XAIAgent` class that provides unified access to all xAI capabilities
- [ ] **FR-2**: Support for agentic server-side tools (web search, X search, code execution)
- [ ] **FR-3**: Integration with existing RAG chain and Knowledge Archive
- [ ] **FR-4**: Hybrid queries combining local RAG + live web/X data
- [ ] **FR-5**: Client-side function calling with custom tool definitions
- [ ] **FR-6**: Remote MCP tool integration (Phase 1 per Q-3)
- [ ] **FR-7**: Citation extraction and formatting (inline + structured)
- [ ] **FR-8**: Streaming responses with real-time tool call visibility
- [ ] **FR-9**: xAI Collections integration for detailed context enrichment (per Q-4)
- [ ] **FR-10**: Auto-select backend by method with explicit `backend=` override (per Q-1)

### Non-Functional Requirements

- [ ] **NFR-1**: All calls traced in Phoenix with unified schema
- [ ] **NFR-2**: Cost tracking (tokens + tool invocations)
- [ ] **NFR-3**: Graceful fallback when xAI SDK not available
- [ ] **NFR-4**: Minimal breaking changes to existing LangChain integration

---

## Constraints

- **C-1**: Must add `xai-sdk>=1.5.0` as new dependency for full functionality
- **C-2**: Agentic tools require xAI native SDK - cannot use OpenAI-compatible API
- **C-3**: Phoenix instrumentation for native SDK requires custom `@trace_xai` decorator (per Q-2)
- **C-4**: Hybrid knowledge strategy: Local Knowledge Archive for low-token keywords/snippets; xAI Collections for detailed context (per Q-4)

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | Should wrapper auto-select between LangChain and native SDK based on requested features? | `answered` | **Yes, with explicit override.** Auto-select by method: `chat()`/`chat_with_rag()`/`chat_with_tools()` → LangChain; `search_web()`/`search_x()`/`execute_code()`/`research()` → Native SDK; `hybrid_query()` → Both. Allow `backend=` param override. **Document defaults in ADR/SPEC.** |
| Q-2 | How to handle Phoenix tracing for native SDK calls? Custom instrumentation or callback? | `answered` | **Custom Decorator (`@trace_xai`).** All three options (decorator, callback, context manager) are functionally identical - same traces in Phoenix. Decorator is cleanest code style: one-line annotation per method. |
| Q-3 | Should MCP integration be Phase 1 or deferred? | `answered` | **Phase 1 - Include MCP.** Project ethos: "We thrive in complexity and have a system DESIGNED to handle it." Full feature set from the start. |
| Q-4 | Should we expose xAI Collections or rely on local Knowledge Archive? | `answered` | **Both.** Hybrid approach: Local Knowledge Archive for keywords/snippets (low token usage) + xAI Collections for detailed context enrichment. Augment local knowledge with targeted keywords to keep tokens down, then use Collections for deep context when needed. |

---

## Options Considered

### Option A: Thin Wrapper (Recommended)

**Description**: Create `XAIAgent` as a facade that delegates to either LangChain or native SDK based on the operation. Minimal abstraction, maximum flexibility.

**Pros**:

- Direct access to all xAI features
- Easy to understand and maintain
- Can expose native SDK objects when needed
- Phoenix tracing via callbacks/decorators

**Cons**:

- Two underlying implementations to maintain
- Slight API inconsistency between operations

### Option B: Full Abstraction

**Description**: Create unified abstraction layer that completely hides LangChain/native SDK differences.

**Pros**:

- Consistent API for all operations
- Easier to swap implementations

**Cons**:

- More complex implementation
- May lose access to advanced features
- Higher maintenance burden

### Option C: Native SDK Only

**Description**: Migrate entirely to xAI native SDK, abandon LangChain.

**Pros**:

- Single implementation
- Full feature access

**Cons**:

- Lose LangChain ecosystem (tools, chains, agents)
- Breaking change to existing RAG integration
- Less flexibility for future provider swaps

### Recommendation

**Option A: Thin Wrapper** - Provides full feature access with minimal complexity. LangChain continues to handle RAG and client-side tools; native SDK handles agentic server-side features.

---

## Decision Points

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | Wrapper architecture approach | `decided` | Option A - Thin Wrapper |
| D-2 | Primary methods to expose | `decided` | See Exposed Functionality below |
| D-3 | Phoenix instrumentation approach | `decided` | Custom `@trace_xai` decorator (per Q-2) |
| D-4 | MCP integration scope | `decided` | Phase 1 - full integration (per Q-3) |

---

## Scope Definition

### In Scope

- `XAIAgent` unified wrapper class
- Server-side agentic tools (web_search, x_search, code_execution)
- **Remote MCP tool integration** (Phase 1 per Q-3)
- Hybrid RAG + live data queries
- **Both local Knowledge Archive AND xAI Collections** (per Q-4)
- Phoenix tracing for all operations (custom `@trace_xai` decorator per Q-2)
- Cost estimation/tracking
- Streaming with tool call visibility
- Auto-select backend with explicit override (per Q-1)

### Out of Scope

- Voice API integration (defer to future DISC)
- Image generation (defer to future DISC)
- Multi-turn agentic conversations (Phase 2)

---

## Proposed Architecture

### File Structure

```text
gateway/services/llm/
├── __init__.py           # Updated exports
├── xai_langchain.py      # Existing - unchanged
├── rag_chain.py          # Existing - unchanged
├── xai_agent.py          # NEW - unified wrapper
├── xai_native.py         # NEW - xAI SDK integration
└── tracing.py            # NEW - Phoenix instrumentation
```

### Class Design

```python
class XAIAgent:
    """Unified xAI agent with full capability access."""
    
    # Simple chat (LangChain)
    def chat(query: str, **kwargs) -> str
    
    # RAG chat (LangChain + Knowledge Archive)
    def chat_with_rag(query: str, **kwargs) -> RAGResponse
    
    # Web research (xAI native - agentic)
    def search_web(query: str, **kwargs) -> AgenticResponse
    
    # X/Twitter research (xAI native - agentic)
    def search_x(query: str, **kwargs) -> AgenticResponse
    
    # Code execution (xAI native - agentic)
    def execute_code(query: str) -> AgenticResponse
    
    # Full research mode (xAI native - multi-tool)
    def research(query: str, tools: list, **kwargs) -> AgenticResponse
    
    # Hybrid: RAG + live data
    def hybrid_query(query: str, rag: bool, web: bool, x: bool) -> HybridResponse
    
    # Client-side tools (LangChain)
    def chat_with_tools(query: str, tools: list) -> ToolResponse
    
    # xAI Collections search (per Q-4)
    def search_collection(query: str, collection_id: str) -> CollectionResponse
    
    # Remote MCP tool connection (per Q-3)
    def connect_mcp(server_url: str, **kwargs) -> MCPConnection
```

### Response Models

```python
@dataclass
class AgenticResponse:
    answer: str
    citations: list[str]           # All source URLs
    inline_citations: list[dict]   # Position-tracked citations
    tool_calls: list[ToolCall]     # Tools invoked
    usage: TokenUsage
    cost_estimate: float

@dataclass
class HybridResponse:
    answer: str
    rag_sources: list[str]         # Local Knowledge Archive
    web_sources: list[str]         # Live web citations
    x_sources: list[str]           # X post citations

@dataclass
class CollectionResponse:
    """Response from xAI Collections search (per Q-4)."""
    answer: str
    collection_id: str
    documents: list[dict]          # Retrieved documents
    citations: list[str]
    usage: TokenUsage
```

---

## Cross-DISC Dependencies

| Dependency | Type | Status | Blocker For | Notes |
|------------|------|--------|-------------|-------|
| DISC-003   | `FS` | `resolved` | Core implementation | LangChain integration complete |
| DISC-006   | `soft` | `active` | RAG integration | Can use existing RAGChain as stub |

### Stub Strategy (if applicable)

| DISC | Stub Location | Stub Behavior |
|------|---------------|---------------|
| DISC-006 | `gateway/services/llm/rag_chain.py` | Existing RAGChain works as-is |

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status |
|---------------|-----|-------|--------|
| ADR | ADR-0048 | Unified xAI Agent Wrapper Architecture | `proposed` |
| Contract | `shared/contracts/llm/responses.py` | Agent response models | `pending` |
| Plan | PLAN-{TBD} | XAI Agent Implementation | `pending` |

---

## Conversation Log

### 2025-12-31 - SESSION_023

**Topics Discussed**:

- xAI documentation review (`docs/scraped/xai/`)
- Current LangChain integration capabilities vs xAI native features
- Gap analysis: what's missing via OpenAI-compatible API
- Proposed unified wrapper architecture

**Key Insights**:

1. xAI's **agentic server-side tools** (web search, X search, code execution) require the native `xai-sdk` - they cannot be accessed via the OpenAI-compatible API that LangChain uses
2. **Remote MCP Tools** allow xAI to connect to external tool servers on the API side
3. **Inline citations** with position tracking is a powerful feature for grounded responses
4. **Hybrid queries** combining local RAG + live data would be extremely powerful
5. Current `XAIChatModel` (LangChain) handles: chat, streaming, client-side function calling, RAG
6. Native SDK would add: web search, X search, code execution, MCP, citations

**Exposed Functionality Agreed**:

- `chat()` - Simple chat via LangChain
- `chat_with_rag()` - RAG with Knowledge Archive
- `search_web()` - Agentic web search
- `search_x()` - Agentic X/Twitter search
- `execute_code()` - Sandboxed Python execution
- `research()` - Multi-tool agentic research
- `hybrid_query()` - RAG + live data combined
- `chat_with_tools()` - Client-side function calling
- `search_collection()` - xAI Collections search (NEW per Q-4)
- `connect_mcp()` - Remote MCP tool integration (NEW per Q-3)

**Open Questions Resolved**:

| Q-ID | Decision | Rationale |
|------|----------|----------|
| Q-1 | Auto-select + explicit override | Method determines backend; `backend=` param for override. Document defaults in ADR/SPEC. |
| Q-2 | Custom `@trace_xai` decorator | Functionally identical to callback/context manager, cleanest code style. |
| Q-3 | MCP in Phase 1 | "We thrive in complexity" - full feature set from start. |
| Q-4 | Both local + xAI Collections | Local for low-token keywords/snippets; Collections for detailed context enrichment. |

**Action Items**:

- [x] Answer open questions (Q-1 through Q-4)
- [ ] Create ADR for wrapper architecture (include backend defaults per Q-1)
- [ ] Add `xai-sdk>=1.5.0` to dependencies
- [ ] Implement `XAIAgent` core class
- [ ] Implement Phoenix tracing decorator (`@trace_xai`)
- [ ] Implement MCP integration (Phase 1)
- [ ] Implement xAI Collections integration
- [ ] Create demo script showing all capabilities
- [ ] Update AGENTS.md with xAI wrapper documentation

---

## Resolution

<!-- Filled when discussion is resolved -->

**Resolution Date**: {TBD}

**Outcome**: {TBD}

**Next Steps**:
1. {TBD}
2. {TBD}

---

*Template version: 1.0.0 | See `.discussions/README.md` for usage instructions*
