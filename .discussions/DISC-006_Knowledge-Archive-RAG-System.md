# DISC-006: Knowledge Archive & RAG System

**Status**: resolved  
**Created**: 2025-12-30  
**Updated**: 2025-12-31  
**Author**: AI-Assisted  
**Session**: SESSION_020  
**Related**: Merges concepts from RAG + Archive discussions

## Cross-DISC Dependencies

| DISC | Relationship | Phase |
|------|--------------|-------|
| DISC-003 | Langchain adapter for RAG context injection | Phase 4 |
| DISC-004 | PII sanitization before embedding/injection | Phase 3 |
| DISC-005 | Embedding model selection | Phase 3 |

---

## Summary

Design a unified **Knowledge Archive** that serves as both:
1. **Persistent storage** for sessions, plans, artifacts (with bidirectional file sync)
2. **RAG corpus** for semantic search and LLM context injection

One system, two purposes.

---

## The Problem

| Issue | Impact |
|-------|--------|
| LLM generates generic content | 72/100 score, no project awareness |
| Historical context scattered in files | Not queryable, not linked |
| No cost tracking per session | Can't measure ROI |
| 2M token context window | Using <1% of capacity |

---

## The Solution: `workspace/knowledge.db`

```
workspace/knowledge.db
├── sessions        (markdown + metadata)
├── plans           (JSON + status)
├── discussions     (markdown + metadata)
├── adrs            (JSON + references)
├── artifacts       (generated content)
├── llm_calls       (API logs + cost)
├── relationships   (cross-references)
├── chunks          (text segments for RAG)
└── embeddings      (vector representations)
```

### Core Capabilities

| Capability | Description |
|------------|-------------|
| **Bidirectional Sync** | File saved → DB updated; DB query → file export |
| **Full-Text Search** | FTS5 across all content |
| **Semantic Search** | Vector similarity for RAG |
| **Cost Tracking** | LLM spend per session/project |
| **Relationship Graph** | Link sessions → plans → ADRs |
| **Context Builder** | Auto-inject relevant context into prompts |

---

## Architecture

### Layer 1: Archive (Storage)

```python
# Sync files to DB on change
def on_file_change(path: Path):
    content = path.read_text()
    metadata = parse_metadata(content)
    upsert_to_db(path.stem, metadata, content)

# Export from DB to file
def export_to_file(doc_id: str) -> Path:
    row = db.query(doc_id)
    return reconstruct_file(row)
```

### Layer 2: Search (Retrieval)

```python
# Full-text search
results = db.fts_search("RAG context window")

# Semantic search
query_embedding = embed("How does artifact generation work?")
results = db.vector_search(query_embedding, top_k=5)
```

### Layer 3: RAG (Context Injection)

```python
def build_context(prompt: str) -> str:
    # Find relevant chunks
    chunks = semantic_search(prompt, top_k=10)
    
    # PII sanitize
    safe_chunks = [sanitize(c) for c in chunks]
    
    # Build context string
    context = format_context(safe_chunks)
    
    return f"{context}\n\n---\n\n{prompt}"
```

---

## Schema

```sql
-- Documents (sessions, plans, DISCs, ADRs)
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,           -- session, plan, disc, adr
    title TEXT,
    status TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    file_path TEXT,
    content TEXT,                 -- Full content
    metadata JSON                 -- Type-specific fields
);

-- LLM Calls (move from llm_logs.db)
CREATE TABLE llm_calls (
    id INTEGER PRIMARY KEY,
    session_id TEXT,              -- Link to session
    timestamp TIMESTAMP,
    model TEXT,
    prompt TEXT,
    response TEXT,
    tokens_in INTEGER,
    tokens_out INTEGER,
    cost REAL,
    success INTEGER
);

-- Chunks (for RAG)
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    doc_id TEXT,
    chunk_index INTEGER,
    content TEXT,
    FOREIGN KEY (doc_id) REFERENCES documents(id)
);

-- Embeddings (vectors)
CREATE TABLE embeddings (
    chunk_id INTEGER PRIMARY KEY,
    vector BLOB,                  -- 384-dim float array
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);

-- Full-text search
CREATE VIRTUAL TABLE content_fts USING fts5(
    id, type, title, content
);

-- Relationships
CREATE TABLE relationships (
    source_id TEXT,
    target_id TEXT,
    type TEXT,                    -- implements, references, supersedes
    PRIMARY KEY (source_id, target_id, type)
);
```

---

## Implementation Phases

### Phase 1: Archive Core ✅ COMPLETE

- [x] Create `knowledge.db` schema
- [x] Document ingest (sessions, plans, DISCs, ADRs)
- [x] File watcher for auto-sync
- [x] Export to original format
- [x] Migrate `llm_logs.db` data

### Phase 2: Search ✅ COMPLETE

- [x] FTS5 indexing
- [x] Search API endpoints
- [x] Relationship tracking
- [x] Basic query UI (via API)

### Phase 3: RAG ✅ COMPLETE

- [x] Chunking pipeline
- [x] Embedding generation (sentence-transformers)
- [x] Vector similarity search
- [x] Context builder
- [x] PII sanitizer

### Phase 4: Integration ✅ COMPLETE

- [x] Inject context into LLM prompts
- [x] Langchain adapter (DISC-003)
- [x] Phoenix observability (replaced LangSmith)

**Completed**: SESSION_021, SESSION_022

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/knowledge/search?q=...` | Full-text search |
| GET | `/api/knowledge/semantic?q=...` | Semantic search |
| GET | `/api/knowledge/docs/{id}` | Get document |
| GET | `/api/knowledge/docs/{id}/export` | Export to file |
| POST | `/api/knowledge/sync` | Force file sync |
| GET | `/api/knowledge/stats` | Usage statistics |
| GET | `/api/knowledge/context?prompt=...` | Build RAG context |

---

## Dependencies (Staged DISCs)

| DISC | Topic | When Needed |
|------|-------|-------------|
| DISC-003 | Langchain/Langgraph | Phase 4 |
| DISC-004 | PII Sanitization | Phase 3 |
| DISC-005 | Embedding Model Selection | Phase 3 |

---

## Design Decisions (Finalized)

### 1. Embedding Model: Dual-Mode (Local + API)

**Decision**: Support BOTH local and API embeddings with runtime switching.

| Mode | Model | Dimensions | Use Case |
|------|-------|------------|----------|
| Local (default) | `all-mpnet-base-v2` | 768 | High-memory desktops, offline |
| Local (fallback) | `all-MiniLM-L6-v2` | 384 | Resource-constrained |
| API | xAI/OpenAI embeddings | varies | Cloud deployment, latest models |

**Config**: `KNOWLEDGE_EMBEDDING_MODE=local|api` environment variable.

> **Cross-ref**: DISC-005 will benchmark these models. Update DISC-005 to include `all-mpnet-base-v2` as primary recommendation.

---

### 2. Chunk Size: Hybrid Strategy

**Decision**: Content-aware chunking based on file type.

| File Type | Chunking Strategy | Target Size |
|-----------|-------------------|-------------|
| Markdown (DISC, ADR prose) | Split on `##` headers, then paragraphs | 256-512 tokens |
| Python (.py) | Function/class-level | 256-512 tokens |
| JSON (ADR, Plan, SPEC) | Whole document (already structured) | Full document |
| Session logs | Section-based | 256-512 tokens |

---

### 3. Sync Frequency: Watchdog (Real-time) with Fallback

**Decision**: Real-time file watching as default, with on-demand fallback.

| Mode | Trigger | Use Case |
|------|---------|----------|
| **Watchdog (default)** | File save event | Desktop with resources |
| **On-demand** | Manual API call | Laptop/resource-limited |

**Config**: `KNOWLEDGE_SYNC_MODE=watchdog|manual` environment variable.

**API Endpoints**:
- `POST /api/knowledge/sync` - Force full sync
- `POST /api/knowledge/sync/{type}` - Sync specific artifact type
- `GET /api/knowledge/sync/status` - Watchdog health check

---

### 4. Retention: Archive Everything (Soft Delete)

**Decision**: Never delete, use `archived_at` timestamp for soft archival.

```sql
-- Query active documents (default)
SELECT * FROM documents WHERE archived_at IS NULL;

-- Query all including archived
SELECT * FROM documents;
```

**Future (PROD)**: Add configurable retention limits per artifact type.

> **Cross-ref**: Aligns with ADR-0002 artifact preservation principle.

---

## Next Steps

- [x] USER approval on unified design ✅
- [x] Generate ADR-0047: Knowledge Archive & RAG System ✅
- [x] Generate SPEC-0043: Knowledge Archive Specification ✅
- [x] Create `shared/contracts/knowledge/` contracts ✅
- [x] Generate PLAN-002: Knowledge Archive Implementation ✅
- [x] Implement Phase 1 (Archive Core) ✅
- [x] Implement Phase 2 (Search) ✅
- [x] Implement Phase 3 (RAG) ✅
- [x] Implement Phase 4 (Integration) ✅
- [x] Phoenix observability integration ✅
- [x] LangChain + xAI adapter ✅

## Resulting Artifacts

| Type | ID | Title | Status |
|------|-----|-------|--------|
| ADR | ADR-0047 | Knowledge Archive & RAG System Architecture | `active` |
| SPEC | SPEC-0043 | Knowledge Archive & RAG Specification | `active` |
| Plan | PLAN-002 | Knowledge Archive Implementation | `complete` |
| Session | SESSION_021 | PLAN-002 M1-M4 Execution | `complete` |
| Session | SESSION_022 | Phoenix + LangChain Integration | `complete` |

