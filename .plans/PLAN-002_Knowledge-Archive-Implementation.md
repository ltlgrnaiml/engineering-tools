# PLAN-002: Knowledge Archive & RAG Implementation

**Status**: draft  
**Granularity**: L3 (Procedural)  
**Version**: 2.0 (100% SPEC Compliance)  
**Created**: 2025-12-30  
**Updated**: 2025-12-30  
**Source ADR**: ADR-0047  
**Source SPEC**: SPEC-0043  
**Source DISC**: DISC-003, DISC-004, DISC-005, DISC-006  
**Estimated Duration**: 14-19 days
**SPEC Coverage**: 27/27 requirements (100%)

---

## Overview

Implement the Knowledge Archive & RAG system per ADR-0047 and SPEC-0043. This L3 plan provides step-by-step instructions suitable for budget AI models.

---

## Milestones Summary

| Milestone | Name | Tasks | Duration | Dependencies | Status |
|-----------|------|-------|----------|--------------|--------|
| M1 | Archive Core | 9 | 4-5 days | None | `pending` |
| M2 | Search Layer | 6 | 2-3 days | M1 | `pending` |
| M3 | RAG Layer | 10 | 6-8 days | M2 | `pending` |
| M4 | Integration | 4 | 2-3 days | M3 | `pending` |

**Total Tasks**: 29

---

## SPEC Requirement Traceability

| SPEC ID | Requirement | Task |
|---------|-------------|------|
| SPEC-0043-AR01 | Database Schema | T-M1-01 |
| SPEC-0043-AR02 | Document Ingest | T-M1-02 |
| SPEC-0043-AR03 | File Watcher | T-M1-04 |
| SPEC-0043-AR04 | Export to File | T-M1-07 |
| SPEC-0043-AR05 | LLM Call Logging | T-M1-08 |
| SPEC-0043-AR06 | Soft Delete Only | T-M1-03 |
| SPEC-0043-SE01 | FTS5 Search | T-M2-01 |
| SPEC-0043-SE02 | Semantic Search | T-M2-02 |
| SPEC-0043-SE03 | Hybrid Search RRF | T-M2-03 |
| SPEC-0043-SE04 | Relationship Tracking | T-M2-04 |
| SPEC-0043-EM01 | Dual-Mode Embedding | T-M3-02 |
| SPEC-0043-EM02 | Local Embedding Models | T-M3-02 |
| SPEC-0043-EM03 | Embedding Storage | T-M3-02 |
| SPEC-0043-EM04 | Batch Embedding | T-M3-03 |
| SPEC-0043-CH01 | Content-Aware Chunking | T-M3-01 |
| SPEC-0043-CH02 | Chunk Metadata | T-M3-01 |
| SPEC-0043-CH03 | Re-chunking on Update | T-M3-04 |
| SPEC-0043-SA01 | Regex Pattern Matching | T-M3-05 |
| SPEC-0043-SA02 | Reversible Redaction | T-M3-05 |
| SPEC-0043-SA03 | Sanitization Pipeline | T-M3-06 |
| SPEC-0043-RA01 | Context Builder | T-M3-06 |
| SPEC-0043-RA02 | Context Formatting | T-M3-06 |
| SPEC-0043-RA03 | Token Budget | T-M3-07 |
| SPEC-0043-RA04 | Context Caching | T-M3-08 |
| SPEC-0043-API01-11 | REST Endpoints | T-M1-05, T-M1-06, T-M2-05, T-M3-09, T-M4-02 |

---

## M1: Archive Core (4-5 days)

### Objective
Create the SQLite database schema, document ingest pipeline, bidirectional file sync, and export capability.

### Tasks

#### T-M1-01: Create Database Schema
**Description**: Create workspace/knowledge.db with all required tables.

**Context**:
- SPEC-0043-AR01 defines schema requirements
- Tables: documents, llm_calls, chunks, embeddings, relationships, content_fts

**Steps**:
1. Create `gateway/services/knowledge/` directory
2. Create `gateway/services/knowledge/__init__.py`
3. Create `gateway/services/knowledge/database.py` with schema DDL
4. Implement `init_database()` function
5. Add FTS5 virtual table for content_fts

**Code Snippet** (database.py):
```python
SCHEMA_DDL = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    title TEXT,
    status TEXT,
    file_path TEXT,
    content TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    archived_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    start_char INTEGER DEFAULT 0,
    end_char INTEGER DEFAULT 0,
    FOREIGN KEY (doc_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS embeddings (
    chunk_id INTEGER PRIMARY KEY,
    vector BLOB NOT NULL,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);

CREATE TABLE IF NOT EXISTS relationships (
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    type TEXT NOT NULL,
    PRIMARY KEY (source_id, target_id, type)
);

CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model TEXT,
    prompt TEXT,
    response TEXT,
    tokens_in INTEGER,
    tokens_out INTEGER,
    cost REAL,
    success INTEGER DEFAULT 1
);

CREATE VIRTUAL TABLE IF NOT EXISTS content_fts USING fts5(
    id, type, title, content, content='documents'
);
"""
```

**Verification**: `python -c "from gateway.services.knowledge.database import init_database; print('Schema OK')"`

---

#### T-M1-02: Create Document Parsers
**Description**: Implement parsers for each document type (markdown, JSON).

**Context**:
- SPEC-0043-AR02 defines document types: session, plan, discussion, adr, spec, contract
- Use shared.contracts.knowledge.Document model

**Steps**:
1. Create `gateway/services/knowledge/parsers.py`
2. Implement `parse_markdown_document()` for sessions, discussions
3. Implement `parse_json_document()` for ADRs, SPECs, plans
4. Implement `extract_metadata()` for each type
5. Implement `extract_relationships()` from cross-references

**Verification**: `python -c "from gateway.services.knowledge.parsers import parse_markdown_document; print('Parsers OK')"`

---

#### T-M1-03: Create Archive Service
**Description**: Implement ArchiveService for document CRUD operations.

**Context**:
- SPEC-0043-AR06: Soft delete only (use archived_at)
- Files are SSOT; database is cache

**Steps**:
1. Create `gateway/services/knowledge/archive_service.py`
2. Implement `ArchiveService` class with:
   - `upsert_document(doc: Document)`
   - `get_document(doc_id: str) -> Document | None`
   - `list_documents(doc_type: str | None) -> list[Document]`
   - `archive_document(doc_id: str)` (soft delete)
3. Use contracts from `shared.contracts.knowledge.archive`

**Verification**: `python -c "from gateway.services.knowledge.archive_service import ArchiveService; print('Archive OK')"`

---

#### T-M1-04: Implement File Watcher
**Description**: Create watchdog-based file sync service.

**Context**:
- SPEC-0043-AR03: Monitor .discussions/, .plans/, .sessions/, .adrs/, docs/specs/
- Debounce rapid saves (100ms)

**Steps**:
1. Create `gateway/services/knowledge/sync_service.py`
2. Implement `SyncService` class with watchdog integration
3. Implement file event handlers: on_created, on_modified, on_deleted
4. Add debounce logic (100ms delay)
5. Start watchdog in background thread

**Verification**: `python -c "from gateway.services.knowledge.sync_service import SyncService; print('Sync OK')"`

---

#### T-M1-05: Create Knowledge API Routes
**Description**: Add REST endpoints for archive operations.

**Context**:
- SPEC-0043-API: Base path /api/knowledge
- Endpoints: /docs/{id}, /sync, /sync/status

**Steps**:
1. Create `gateway/routes/knowledge.py`
2. Implement GET `/api/knowledge/docs/{id}` - get document
3. Implement POST `/api/knowledge/sync` - force sync
4. Implement GET `/api/knowledge/sync/status` - watchdog health
5. Register routes in `gateway/main.py`

**Verification**: `curl http://localhost:8000/api/knowledge/sync/status` (manual test)

---

#### T-M1-06: Add Sync by Type Endpoint

**SPEC**: SPEC-0043-API07  
**Description**: Add endpoint to sync specific document type.

**Steps**:

1. Add POST `/sync/{doc_type}` endpoint to `gateway/routes/knowledge.py`
2. Validate doc_type against DocumentType enum
3. Scan only directories for that type

**Code Snippet**:

```python
@router.post("/sync/{doc_type}", response_model=SyncStatus)
async def sync_by_type(doc_type: str) -> SyncStatus:
    """Sync specific document type (SPEC-0043-API07)."""
    valid_types = ['session', 'plan', 'discussion', 'adr', 'spec', 'contract']
    if doc_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid type: {valid_types}")
    return SyncStatus(mode=SyncMode.MANUAL, is_running=False)
```

**Verification**: `grep "sync/{doc_type}" gateway/routes/knowledge.py`

---

#### T-M1-07: Implement Export to File

**SPEC**: SPEC-0043-AR04, SPEC-0043-API05  
**Description**: Reconstruct original file format from database.

**Context**:

- Export preserves original format (JSON/Markdown)
- Round-trip: file → db → file produces identical content

**Steps**:

1. Create `gateway/services/knowledge/exporter.py`
2. Implement `export_document(doc: Document) -> str`
3. Implement `export_to_file(doc: Document, output_path: Path) -> Path`
4. Add GET `/docs/{id}/export` endpoint to routes

**Code Snippet** (exporter.py):

```python
"""Document Exporter - SPEC-0043-AR04."""
from pathlib import Path
from shared.contracts.knowledge.archive import Document

def export_document(doc: Document) -> str:
    """Export document to original format string."""
    return doc.content  # Content stored as-is

def export_to_file(doc: Document, output_path: Path | None = None) -> Path:
    """Write document to file."""
    target = output_path or Path(doc.file_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(export_document(doc), encoding='utf-8')
    return target
```

**Code Snippet** (add to routes):

```python
@router.get("/docs/{doc_id}/export")
async def export_document_endpoint(doc_id: str) -> PlainTextResponse:
    """Export document to original format (SPEC-0043-API05)."""
    doc = archive.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    content_type = "application/json" if doc.type in ['adr','spec','plan'] else "text/markdown"
    return PlainTextResponse(content=doc.content, media_type=content_type)
```

**Verification**: `python -c "from gateway.services.knowledge.exporter import export_document; print('Export OK')"`

---

#### T-M1-08: Migrate LLM Logs Database

**SPEC**: SPEC-0043-AR05  
**Description**: Migrate existing llm_logs.db data if present.

**Context**:

- Check for existing `workspace/llm_logs.db`
- Migrate data to `llm_calls` table in knowledge.db
- Preserve all historical cost data

**Steps**:

1. Create `gateway/services/knowledge/migration.py`
2. Implement `migrate_llm_logs(source_db: Path, target_conn) -> int`
3. Call migration during `init_database()` if source exists

**Code Snippet** (migration.py):

```python
"""Database Migration - SPEC-0043-AR05."""
import sqlite3
from pathlib import Path

def migrate_llm_logs(source_db: Path, target_conn: sqlite3.Connection) -> int:
    """Migrate LLM call logs from legacy database."""
    if not source_db.exists():
        return 0
    
    source = sqlite3.connect(source_db)
    source.row_factory = sqlite3.Row
    
    rows = source.execute("SELECT * FROM llm_calls").fetchall()
    migrated = 0
    
    for row in rows:
        try:
            target_conn.execute("""
                INSERT OR IGNORE INTO llm_calls 
                (session_id, timestamp, model, prompt, response, tokens_in, tokens_out, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (row['session_id'], row['timestamp'], row['model'], 
                  row.get('prompt'), row.get('response'),
                  row.get('tokens_in', 0), row.get('tokens_out', 0), row.get('cost', 0.0)))
            migrated += 1
        except Exception:
            continue
    
    target_conn.commit()
    source.close()
    return migrated
```

**Verification**: `python -c "from gateway.services.knowledge.migration import migrate_llm_logs; print('Migration OK')"`

---

#### T-M1-09: Write M1 Tests

**Description**: Create unit tests for archive layer.

**Steps**:

1. Create `tests/knowledge/__init__.py`
2. Create `tests/knowledge/test_archive.py`
3. Test document parser for markdown
4. Test document parser for JSON
5. Test archive service CRUD
6. Test soft delete behavior (NO DELETE statements)
7. Test export round-trip

**Verification**: `pytest tests/knowledge/test_archive.py -v`

**⏱️ CHECKPOINT M1**: All imports work, tests pass

---

### M1 Acceptance Criteria

- [ ] Database created at workspace/knowledge.db on first run
- [ ] All 6 tables exist with correct schema
- [ ] Documents can be parsed from markdown and JSON
- [ ] Archive service can upsert, get, list, archive documents
- [ ] File watcher detects changes in configured directories
- [ ] Export produces identical content (round-trip test)
- [ ] LLM logs migrated if legacy db exists
- [ ] API endpoints return correct responses (including /sync/{type}, /export)
- [ ] All M1 tests pass

---

## M2: Search Layer (2-3 days)

### Objective
Implement full-text and semantic search capabilities.

### Tasks

#### T-M2-01: Implement FTS5 Search
**Description**: Full-text search using SQLite FTS5.

**Context**:
- SPEC-0043-SE01: Search on id, type, title, content
- Return ranked results with snippets

**Steps**:
1. Create `gateway/services/knowledge/search_service.py`
2. Implement `SearchService` class
3. Implement `fts_search(query: str, limit: int) -> list[SearchResult]`
4. Use FTS5 `highlight()` for snippets
5. Use BM25 ranking

**Verification**: `python -c "from gateway.services.knowledge.search_service import SearchService; print('FTS OK')"`

---

#### T-M2-02: Implement Vector Search
**Description**: Semantic search using embedding vectors.

**Context**:
- SPEC-0043-SE02: Cosine similarity on embeddings
- Uses stub embedding contracts for now

**Steps**:
1. Add `vector_search(query: str, top_k: int) -> list[SearchResult]` to SearchService
2. Implement cosine similarity calculation
3. Query embeddings table for nearest neighbors
4. Return results with similarity scores

**Verification**: `python -c "from gateway.services.knowledge.search_service import SearchService; s=SearchService(); print('Vector OK')"`

---

#### T-M2-03: Implement Hybrid Search (RRF)
**Description**: Combine FTS and vector results using Reciprocal Rank Fusion.

**Context**:
- SPEC-0043-SE03: RRF formula: score = sum(1 / (k + rank))
- k=60 default

**Steps**:
1. Add `hybrid_search(query: str, top_k: int, config: HybridSearchConfig) -> list[SearchResult]`
2. Get results from both FTS and vector search
3. Apply RRF fusion formula
4. Merge and sort by fused score
5. Return top_k results

**Verification**: `python -c "from gateway.services.knowledge.search_service import SearchService; s=SearchService(); print('Hybrid OK')"`

---

#### T-M2-04: Implement Relationship Tracking
**Description**: Store and query document relationships.

**Context**:
- SPEC-0043-SE04: Types: implements, references, supersedes, creates
- Query by source or target

**Steps**:
1. Add relationship methods to ArchiveService:
   - `add_relationship(source_id, target_id, type)`
   - `get_relationships(doc_id) -> list[Relationship]`
2. Extract relationships during document parsing
3. Store in relationships table

**Verification**: `python -c "from gateway.services.knowledge.archive_service import ArchiveService; print('Relations OK')"`

---

#### T-M2-05: Add Search API Endpoints
**Description**: REST endpoints for search operations.

**Context**:
- SPEC-0043-API01-03: /search, /semantic, /hybrid

**Steps**:
1. Add GET `/api/knowledge/search?q=...` - FTS search
2. Add GET `/api/knowledge/semantic?q=...` - vector search
3. Add GET `/api/knowledge/hybrid?q=...` - hybrid search
4. Add GET `/api/knowledge/relationships/{id}` - get relationships

**Verification**: `curl "http://localhost:8000/api/knowledge/search?q=test"` (manual)

---

#### T-M2-06: Write M2 Tests
**Description**: Unit tests for search layer.

**Steps**:
1. Create `tests/knowledge/test_search.py`
2. Test FTS search returns ranked results
3. Test vector search returns similar documents
4. Test hybrid search merges correctly
5. Test relationship queries

**Verification**: `pytest tests/knowledge/test_search.py -v`

---

### M2 Acceptance Criteria
- [ ] FTS search returns highlighted snippets
- [ ] Vector search returns similarity scores
- [ ] Hybrid search correctly applies RRF fusion
- [ ] Relationships extracted and queryable
- [ ] Search endpoints return correct results
- [ ] All M2 tests pass

---

## M3: RAG Layer (6-8 days)

### Objective
Implement chunking, embedding, PII sanitization, and context building.

### Tasks

#### T-M3-01: Implement Chunking Pipeline

**SPEC**: SPEC-0043-CH01, SPEC-0043-CH02  
**Description**: Content-aware text segmentation with metadata tracking.

**Context**:

- Strategies: markdown headers, python functions, json whole, paragraph fallback
- Target: 256-512 tokens, 50 token overlap
- Track chunk metadata: doc_id, chunk_index, start_char, end_char

**Steps**:

1. Create `gateway/services/knowledge/chunking.py`
2. Implement `ChunkingService` class
3. Implement `chunk_markdown(content: str) -> list[Chunk]` - split on ## headers
4. Implement `chunk_python(content: str) -> list[Chunk]` - function/class boundaries
5. Implement `chunk_json(content: str) -> list[Chunk]` - whole document
6. Add token estimation (chars / 4 approximation)

**Code Snippet** (chunking.py):

```python
"""Chunking Service - SPEC-0043-CH01, CH02."""
import re
from shared.contracts.knowledge.rag import Chunk, ChunkingStrategy

class ChunkingService:
    TARGET_TOKENS = 384  # Middle of 256-512
    CHARS_PER_TOKEN = 4
    
    def chunk_document(self, doc_id: str, content: str, file_ext: str) -> list[Chunk]:
        if file_ext in ('.md', '.markdown'):
            return self._chunk_markdown(doc_id, content)
        elif file_ext == '.py':
            return self._chunk_python(doc_id, content)
        elif file_ext == '.json':
            return self._chunk_json(doc_id, content)
        return self._chunk_paragraphs(doc_id, content)
    
    def _chunk_markdown(self, doc_id: str, content: str) -> list[Chunk]:
        """Split on ## headers."""
        sections = re.split(r'\n(?=## )', content)
        return [
            Chunk(doc_id=doc_id, chunk_index=i, content=s.strip(),
                  token_count=len(s)//self.CHARS_PER_TOKEN, strategy=ChunkingStrategy.MARKDOWN_HEADERS)
            for i, s in enumerate(sections) if s.strip()
        ]
```

**Verification**: `python -c "from gateway.services.knowledge.chunking import ChunkingService; print('Chunking OK')"`

**⏱️ CHECKPOINT M3-01**: Markdown splits on headers

---

#### T-M3-02: Implement Embedding Service

**SPEC**: SPEC-0043-EM01, SPEC-0043-EM02, SPEC-0043-EM03  
**Description**: Generate embeddings with dual-mode support and auto-fallback.

**Context**:

- Primary: all-mpnet-base-v2 (768 dims)
- Fallback: all-MiniLM-L6-v2 (384 dims) - auto on MemoryError
- KNOWLEDGE_EMBEDDING_MODE env var: local|api
- Lazy model loading

**Steps**:

1. Create `gateway/services/knowledge/embedding_service.py`
2. Implement `EmbeddingService` class with config
3. Add sentence-transformers integration for local mode
4. Implement `embed(text: str) -> EmbeddingResult`
5. Implement `embed_batch(texts: list[str]) -> BatchEmbeddingResult`
6. Add auto-fallback to smaller model on MemoryError

**Code Snippet** (embedding_service.py):

```python
"""Embedding Service - SPEC-0043-EM01, EM02, EM03."""
import os
from shared.contracts.embedding.model import EmbeddingConfig, EmbeddingResult, EmbeddingMode, EmbeddingModel

class EmbeddingService:
    def __init__(self, config: EmbeddingConfig | None = None):
        self.config = config or EmbeddingConfig()
        self._model = None
        self._model_name = None
    
    def _load_model(self, model_name: str):
        if self._model_name == model_name:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name)
            self._model_name = model_name
        except MemoryError:
            # Auto-fallback (SPEC-0043-EM02)
            if model_name == EmbeddingModel.MPNET_BASE.value:
                self._load_model(EmbeddingModel.MINILM_L6.value)
    
    def embed(self, text: str) -> EmbeddingResult:
        self._load_model(self.config.model.value)
        vec = self._model.encode(text, normalize_embeddings=True)
        return EmbeddingResult(vector=vec.tolist(), model=self.config.model, dimensions=len(vec))
```

**Verification**: `python -c "from gateway.services.knowledge.embedding_service import EmbeddingService; print('Embedding OK')"`

---

#### T-M3-03: Implement Batch Embedding with Resume

**SPEC**: SPEC-0043-EM04  
**Description**: Efficient batch processing with progress callback and resume capability.

**Context**:

- Batch size configurable (default: 32)
- Progress callback for UI feedback
- Resume: only embed chunks without embeddings

**Steps**:

1. Add `embed_all_chunks(conn, progress_callback) -> int` to EmbeddingService
2. Query chunks LEFT JOIN embeddings WHERE embedding IS NULL
3. Process in batches with progress callback
4. Store embeddings as BLOB

**Code Snippet** (add to embedding_service.py):

```python
def embed_all_chunks(
    self,
    conn,
    progress_callback: Callable[[int, int], None] | None = None
) -> int:
    """Embed all chunks without embeddings (resume-capable)."""
    # Find unembedded chunks
    rows = conn.execute("""
        SELECT c.id, c.content FROM chunks c
        LEFT JOIN embeddings e ON e.chunk_id = c.id
        WHERE e.chunk_id IS NULL
    """).fetchall()
    
    total, embedded = len(rows), 0
    for i in range(0, total, self.config.batch_size):
        batch = rows[i:i + self.config.batch_size]
        texts = [r['content'] for r in batch]
        vectors = self._model.encode(texts, normalize_embeddings=True)
        
        for row, vec in zip(batch, vectors):
            conn.execute(
                "INSERT INTO embeddings (chunk_id, vector, model, dimensions) VALUES (?,?,?,?)",
                (row['id'], self.vector_to_blob(vec), self._model_name, len(vec))
            )
            embedded += 1
        
        conn.commit()
        if progress_callback:
            progress_callback(embedded, total)
    
    return embedded
```

**Verification**: Batch embedding stores vectors in DB (integration test)

---

#### T-M3-04: Implement Re-chunking on Update

**SPEC**: SPEC-0043-CH03  
**Description**: Update chunks when source document changes.

**Context**:

- Detect document content changes via updated_at
- Delete old chunks for document
- Re-chunk and re-embed updated content

**Steps**:

1. Add `rechunk_document(doc_id: str)` to ChunkingService
2. Delete existing chunks for doc_id (CASCADE deletes embeddings)
3. Re-parse and chunk document content
4. Store new chunks
5. Trigger embedding for new chunks

**Code Snippet** (add to chunking.py):

```python
def rechunk_document(self, conn, doc_id: str) -> int:
    """Re-chunk document after update (SPEC-0043-CH03)."""
    # Delete old chunks (embeddings cascade delete)
    conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
    
    # Get document content
    row = conn.execute(
        "SELECT content, file_path FROM documents WHERE id = ?", (doc_id,)
    ).fetchone()
    
    if not row:
        return 0
    
    # Re-chunk based on file extension
    ext = Path(row['file_path']).suffix
    chunks = self.chunk_document(doc_id, row['content'], ext)
    
    # Store new chunks
    for chunk in chunks:
        conn.execute("""
            INSERT INTO chunks (doc_id, chunk_index, content, start_char, end_char, token_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (chunk.doc_id, chunk.chunk_index, chunk.content, 
              chunk.start_char, chunk.end_char, chunk.token_count))
    
    conn.commit()
    return len(chunks)
```

**Verification**: `grep "rechunk_document" gateway/services/knowledge/chunking.py`

**⏱️ CHECKPOINT M3-04**: Re-chunking deletes old chunks and creates new

---

#### T-M3-05: Implement PII Sanitizer

**SPEC**: SPEC-0043-SA01, SPEC-0043-SA02  
**Description**: Regex-based PII detection and redaction.

**Context**:

- Pattern categories from DISC-004: API keys, secrets, emails, IPs, URLs
- <5% false positive rate
- Reversible redaction in dev mode only (IS_DEV_MODE flag)

**Steps**:

1. Create `gateway/services/knowledge/sanitizer.py`
2. Create `config/pii_patterns.yaml` with default patterns
3. Implement `Sanitizer` class
4. Implement `sanitize(content: str, reversible: bool) -> SanitizeResult`
5. Store redaction log for dev mode restore

**Code Snippet** (sanitizer.py):

```python
"""PII Sanitizer - SPEC-0043-SA01, SA02."""
import re
import os
from shared.contracts.sanitization.pii import SanitizeResult, RedactionEntry

class Sanitizer:
    PATTERNS = {
        'api_key': (r'sk-[a-zA-Z0-9]{20,}', '[REDACTED_API_KEY]'),
        'aws_key': (r'AKIA[A-Z0-9]{16}', '[REDACTED_AWS_KEY]'),
        'email': (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL]'),
        'internal_ip': (r'\b(?:10|172\.(?:1[6-9]|2[0-9]|3[01])|192\.168)\.[0-9.]+\b', '[INTERNAL_IP]'),
    }
    
    def sanitize(self, content: str, reversible: bool = False) -> SanitizeResult:
        sanitized = content
        redactions = []
        
        for category, (pattern, replacement) in self.PATTERNS.items():
            for match in re.finditer(pattern, sanitized):
                if reversible:
                    redactions.append(RedactionEntry(
                        original=match.group(), replacement=replacement, category=category
                    ))
                sanitized = sanitized[:match.start()] + replacement + sanitized[match.end():]
        
        return SanitizeResult(sanitized_content=sanitized, redactions=redactions if reversible else [])
```

**Verification**: `python -c "from gateway.services.knowledge.sanitizer import Sanitizer; print('Sanitizer OK')"`

---

#### T-M3-06: Implement Context Builder

**SPEC**: SPEC-0043-RA01, SPEC-0043-RA02, SPEC-0043-SA03  
**Description**: Build RAG context from relevant chunks with sanitization.

**Context**:

- Use hybrid search to find relevant chunks
- GUARDRAIL: ALL chunks MUST pass through sanitizer before LLM
- Format with source attribution

**Steps**:

1. Create `gateway/services/knowledge/context_builder.py`
2. Implement `ContextBuilder` class
3. Implement `build_context(request: ContextRequest) -> RAGContext`
4. Sanitize all chunks before assembly
5. Format with template: "## From {source}: {title}\n\n{content}"

**Code Snippet** (context_builder.py):

```python
"""Context Builder - SPEC-0043-RA01, RA02, SA03."""
from shared.contracts.knowledge.rag import RAGContext, ContextRequest

CONTEXT_TEMPLATE = """## Relevant Context

{chunks}

---

## Your Task

{prompt}"""

CHUNK_TEMPLATE = "### From {doc_type}: {title}\n\n{content}\n"

class ContextBuilder:
    def __init__(self, search_service, sanitizer):
        self.search = search_service
        self.sanitizer = sanitizer
    
    def build_context(self, request: ContextRequest) -> RAGContext:
        # Retrieve relevant chunks
        results = self.search.hybrid_search(request.prompt, top_k=request.top_k)
        
        # GUARDRAIL: Sanitize ALL chunks (SPEC-0043-SA03)
        chunks_text = []
        for r in results:
            sanitized = self.sanitizer.sanitize(r.snippet, reversible=False)
            chunks_text.append(CHUNK_TEMPLATE.format(
                doc_type=r.doc_type, title=r.title, content=sanitized.sanitized_content
            ))
        
        context = CONTEXT_TEMPLATE.format(chunks="\n".join(chunks_text), prompt=request.prompt)
        return RAGContext(context=context, sources=[r.doc_id for r in results])
```

**Verification**: `python -c "from gateway.services.knowledge.context_builder import ContextBuilder; print('Context OK')"`

**⏱️ CHECKPOINT M3-06**: Context builder sanitizes before assembly

---

#### T-M3-07: Add Token Budget Management

**SPEC**: SPEC-0043-RA03  
**Description**: Ensure context fits within model limits.

**Context**:

- Default max_context_tokens=4000
- Prioritize most relevant chunks
- Truncate or drop low-relevance chunks

**Steps**:

1. Add `_estimate_tokens(text: str) -> int` (chars / 4)
2. Add `_fit_to_budget(chunks: list, max_tokens: int) -> list`
3. Keep highest-scored chunks first
4. Return actual token count in RAGContext

**Code Snippet** (add to context_builder.py):

```python
def _estimate_tokens(self, text: str) -> int:
    return len(text) // 4

def _fit_to_budget(self, chunks: list[SearchResult], max_tokens: int) -> list[SearchResult]:
    """Keep chunks until budget exhausted (SPEC-0043-RA03)."""
    total = 0
    selected = []
    for chunk in chunks:  # Already sorted by relevance
        tokens = self._estimate_tokens(chunk.snippet)
        if total + tokens > max_tokens:
            break
        selected.append(chunk)
        total += tokens
    return selected
```

**Verification**: Context respects token budget (unit test)

---

#### T-M3-08: Add Context Caching

**SPEC**: SPEC-0043-RA04  
**Description**: Cache context for repeated queries.

**Context**:

- TTL 5 minutes (configurable)
- Invalidate cache on document update
- Optional disable via cache_enabled param

**Steps**:

1. Add query hash generation (hashlib.sha256)
2. Implement TTL cache with dict + timestamps
3. Hook cache invalidation to document update events
4. Add cache_enabled parameter to ContextRequest

**Code Snippet** (add to context_builder.py):

```python
import hashlib
import time

class ContextCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._cache: dict[str, tuple[RAGContext, float]] = {}
    
    def _hash_query(self, prompt: str, top_k: int) -> str:
        return hashlib.sha256(f"{prompt}:{top_k}".encode()).hexdigest()[:16]
    
    def get(self, prompt: str, top_k: int) -> RAGContext | None:
        key = self._hash_query(prompt, top_k)
        if key in self._cache:
            ctx, ts = self._cache[key]
            if time.time() - ts < self.ttl:
                return ctx
            del self._cache[key]
        return None
    
    def set(self, prompt: str, top_k: int, ctx: RAGContext):
        key = self._hash_query(prompt, top_k)
        self._cache[key] = (ctx, time.time())
    
    def invalidate_all(self):
        self._cache.clear()
```

**Verification**: Second identical query returns cached result (unit test)

---

#### T-M3-09: Add RAG API Endpoint

**SPEC**: SPEC-0043-API10  
**Description**: REST endpoint for context building.

**Steps**:

1. Add GET `/api/knowledge/context` endpoint
2. Accept params: prompt, max_tokens, doc_types, cache_enabled
3. Return RAGContext as JSON

**Code Snippet** (add to routes/knowledge.py):

```python
@router.get("/context", response_model=RAGContext)
async def build_context(
    prompt: str,
    max_tokens: int = 4000,
    cache_enabled: bool = True,
    context_builder: ContextBuilder = Depends(get_context_builder)
) -> RAGContext:
    """Build RAG context for prompt (SPEC-0043-API10)."""
    request = ContextRequest(prompt=prompt, max_tokens=max_tokens, cache_enabled=cache_enabled)
    return context_builder.build_context(request)
```

**Verification**: `curl "http://localhost:8000/api/knowledge/context?prompt=test"` (manual)

---

#### T-M3-10: Write M3 Tests

**Description**: Unit and integration tests for RAG layer.

**Steps**:

1. Create `tests/knowledge/test_chunking.py`
2. Create `tests/knowledge/test_embedding.py`
3. Create `tests/knowledge/test_sanitizer.py`
4. Create `tests/knowledge/test_context_builder.py`
5. Test end-to-end RAG pipeline

**Verification**: `pytest tests/knowledge/ -v`

**⏱️ CHECKPOINT M3**: All M3 imports work, tests pass

---

### M3 Acceptance Criteria

- [ ] Markdown chunked on headers, Python on functions
- [ ] Embeddings generated with sentence-transformers
- [ ] Auto-fallback to smaller model on MemoryError
- [ ] Batch embedding with resume capability
- [ ] Re-chunking triggered on document update
- [ ] PII patterns detected and redacted (<5% FP)
- [ ] Context formatted with source attribution
- [ ] Token budget respected
- [ ] Context caching works with TTL
- [ ] API endpoint returns valid RAGContext
- [ ] All M3 tests pass

---

## M4: Integration (2-3 days)

### Objective
Integrate knowledge system with DevTools and LLM services.

### Tasks

#### T-M4-01: Add Langchain Adapter

**SPEC**: DISC-003 decision  
**Description**: Wrap knowledge service for Langchain integration.

**Context**:

- Create retriever compatible with Langchain BaseRetriever
- Return Langchain Document format for chain compatibility

**Steps**:

1. Create `gateway/services/knowledge/langchain_adapter.py`
2. Implement `KnowledgeRetriever(BaseRetriever)` class
3. Implement `_get_relevant_documents(query: str) -> list[Document]`
4. Use hybrid search internally

**Code Snippet** (langchain_adapter.py):

```python
"""Langchain Adapter - DISC-003 decision."""
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document as LCDocument

class KnowledgeRetriever(BaseRetriever):
    """Langchain-compatible retriever for Knowledge Archive."""
    
    search_service: Any
    embedding_service: Any
    top_k: int = 10
    
    def _get_relevant_documents(self, query: str) -> list[LCDocument]:
        query_vec = self.embedding_service.embed(query).vector
        results = self.search_service.hybrid_search(query, query_vec, top_k=self.top_k)
        
        return [
            LCDocument(
                page_content=r.snippet,
                metadata={"source": r.doc_id, "title": r.title, "score": r.score}
            )
            for r in results
        ]
```

**Verification**: `python -c "from gateway.services.knowledge.langchain_adapter import KnowledgeRetriever; print('Langchain OK')"`

---

#### T-M4-02: Add Statistics Endpoint

**SPEC**: SPEC-0043-API09  
**Description**: Usage statistics and cost tracking.

**Steps**:

1. Implement `get_stats() -> KnowledgeStats` in ArchiveService
2. Count documents by type
3. Sum LLM costs by session
4. Add GET `/api/knowledge/stats` endpoint

**Code Snippet** (add to archive_service.py):

```python
from dataclasses import dataclass

@dataclass
class KnowledgeStats:
    total_documents: int
    documents_by_type: dict[str, int]
    total_chunks: int
    total_embeddings: int
    total_llm_cost: float
    llm_calls_count: int

def get_stats(self) -> KnowledgeStats:
    """Get knowledge archive statistics (SPEC-0043-API09)."""
    docs_by_type = dict(self.conn.execute(
        "SELECT type, COUNT(*) FROM documents WHERE archived_at IS NULL GROUP BY type"
    ).fetchall())
    
    stats = self.conn.execute("""
        SELECT 
            (SELECT COUNT(*) FROM documents WHERE archived_at IS NULL) as docs,
            (SELECT COUNT(*) FROM chunks) as chunks,
            (SELECT COUNT(*) FROM embeddings) as embeds,
            (SELECT COALESCE(SUM(cost), 0) FROM llm_calls) as cost,
            (SELECT COUNT(*) FROM llm_calls) as calls
    """).fetchone()
    
    return KnowledgeStats(
        total_documents=stats[0], documents_by_type=docs_by_type,
        total_chunks=stats[1], total_embeddings=stats[2],
        total_llm_cost=stats[3], llm_calls_count=stats[4]
    )
```

**Verification**: `curl http://localhost:8000/api/knowledge/stats` (manual)

---

#### T-M4-03: Integrate with DevTools Service

**Description**: Add knowledge panel to DevTools.

**Steps**:

1. Import knowledge service in devtools_service.py
2. Add knowledge search to artifact graph
3. Expose RAG context in workflow prompts

**Verification**: DevTools workflow can query knowledge (manual test)

---

#### T-M4-04: Write Integration Tests

**Description**: End-to-end tests for full system.

**Steps**:

1. Create `tests/integration/test_knowledge_system.py`
2. Test: file create → sync → search → context
3. Test: Langchain retriever integration
4. Test: statistics accuracy

**Verification**: `pytest tests/integration/test_knowledge_system.py -v`

**⏱️ CHECKPOINT M4**: Full system integration works end-to-end

---

### M4 Acceptance Criteria

- [ ] Langchain retriever returns knowledge documents
- [ ] Statistics endpoint returns accurate counts/costs
- [ ] DevTools can query knowledge system
- [ ] All integration tests pass

---

## Global Acceptance Criteria

1. **AC-001**: `workspace/knowledge.db` created and queryable
2. **AC-002**: All document types can be ingested
3. **AC-003**: FTS search returns results in <100ms
4. **AC-004**: Hybrid search combines FTS + vector correctly
5. **AC-005**: RAG context includes sanitized, attributed chunks
6. **AC-006**: Context respects token budget
7. **AC-007**: All tests pass: `pytest tests/knowledge/ -v`
8. **AC-008**: API endpoints documented in OpenAPI

---

## Files to Create

| Path | Purpose | Task |
|------|---------|------|
| `gateway/services/knowledge/__init__.py` | Package init | T-M1-01 |
| `gateway/services/knowledge/database.py` | Schema and DB connection | T-M1-01 |
| `gateway/services/knowledge/parsers.py` | Document parsers | T-M1-02 |
| `gateway/services/knowledge/archive_service.py` | Document CRUD + stats | T-M1-03, T-M4-02 |
| `gateway/services/knowledge/sync_service.py` | File watcher | T-M1-04 |
| `gateway/services/knowledge/exporter.py` | Export to file | T-M1-07 |
| `gateway/services/knowledge/migration.py` | LLM logs migration | T-M1-08 |
| `gateway/services/knowledge/search_service.py` | FTS + vector + hybrid | T-M2-01-03 |
| `gateway/services/knowledge/chunking.py` | Content chunking + rechunk | T-M3-01, T-M3-04 |
| `gateway/services/knowledge/embedding_service.py` | Vector generation + batch | T-M3-02, T-M3-03 |
| `gateway/services/knowledge/sanitizer.py` | PII sanitization | T-M3-05 |
| `gateway/services/knowledge/context_builder.py` | RAG context + cache | T-M3-06-08 |
| `gateway/services/knowledge/langchain_adapter.py` | Langchain integration | T-M4-01 |
| `gateway/routes/knowledge.py` | API routes (11 endpoints) | T-M1-05-06, T-M2-05, T-M3-09, T-M4-02 |
| `config/pii_patterns.yaml` | PII patterns config | T-M3-05 |
| `tests/knowledge/test_archive.py` | Archive layer tests | T-M1-09 |
| `tests/knowledge/test_search.py` | Search layer tests | T-M2-06 |
| `tests/knowledge/test_chunking.py` | Chunking tests | T-M3-10 |
| `tests/knowledge/test_embedding.py` | Embedding tests | T-M3-10 |
| `tests/knowledge/test_sanitizer.py` | Sanitizer tests | T-M3-10 |
| `tests/knowledge/test_context_builder.py` | Context builder tests | T-M3-10 |
| `tests/integration/test_knowledge_system.py` | E2E integration tests | T-M4-04 |

**Total Files**: 22

---

## Verification Commands Summary

```bash
# M1 Verification (9 tasks)
python -c "from gateway.services.knowledge.database import init_database; print('M1-01 OK')"
python -c "from gateway.services.knowledge.parsers import parse_markdown_document; print('M1-02 OK')"
python -c "from gateway.services.knowledge.archive_service import ArchiveService; print('M1-03 OK')"
python -c "from gateway.services.knowledge.sync_service import SyncService; print('M1-04 OK')"
python -c "from gateway.routes.knowledge import router; print('M1-05 OK')"
grep "sync/{doc_type}" gateway/routes/knowledge.py  # M1-06
python -c "from gateway.services.knowledge.exporter import export_document; print('M1-07 OK')"
python -c "from gateway.services.knowledge.migration import migrate_llm_logs; print('M1-08 OK')"
pytest tests/knowledge/test_archive.py -v  # M1-09

# M2 Verification (6 tasks)
python -c "from gateway.services.knowledge.search_service import SearchService; print('M2-01 OK')"
# M2-02, M2-03: Vector and hybrid search in same class
grep "get_relationships" gateway/services/knowledge/archive_service.py  # M2-04
pytest tests/knowledge/test_search.py -v  # M2-06

# M3 Verification (10 tasks)
python -c "from gateway.services.knowledge.chunking import ChunkingService; print('M3-01 OK')"
python -c "from gateway.services.knowledge.embedding_service import EmbeddingService; print('M3-02 OK')"
grep "embed_all_chunks" gateway/services/knowledge/embedding_service.py  # M3-03
grep "rechunk_document" gateway/services/knowledge/chunking.py  # M3-04
python -c "from gateway.services.knowledge.sanitizer import Sanitizer; print('M3-05 OK')"
python -c "from gateway.services.knowledge.context_builder import ContextBuilder; print('M3-06 OK')"
grep "_fit_to_budget" gateway/services/knowledge/context_builder.py  # M3-07
grep "ContextCache" gateway/services/knowledge/context_builder.py  # M3-08
grep "/context" gateway/routes/knowledge.py  # M3-09
pytest tests/knowledge/ -v  # M3-10

# M4 Verification (4 tasks)
python -c "from gateway.services.knowledge.langchain_adapter import KnowledgeRetriever; print('M4-01 OK')"
grep "get_stats" gateway/services/knowledge/archive_service.py  # M4-02
grep "knowledge" gateway/services/devtools_service.py  # M4-03
pytest tests/integration/test_knowledge_system.py -v  # M4-04

# Full Test Suite
pytest tests/knowledge/ tests/integration/test_knowledge_system.py -v
```

---

## Task Count Summary

| Milestone | Tasks | SPEC Requirements |
|-----------|-------|-------------------|
| M1 Archive | 9 | AR01-06, API04-08 |
| M2 Search | 6 | SE01-04, API01-03, API11 |
| M3 RAG | 10 | CH01-03, EM01-04, SA01-03, RA01-04, API10 |
| M4 Integration | 4 | API09, DISC-003 |
| **TOTAL** | **29** | **27/27 (100%)** |

---

*Plan created: 2025-12-30*  
*Plan updated: 2025-12-30*  
*Version: 2.0 (100% SPEC Compliance)*  
*Granularity: L3 (Procedural)*
