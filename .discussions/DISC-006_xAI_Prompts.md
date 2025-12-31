# DISC-006: xAI Generation Prompts

**Purpose**: Test prompts for xAI artifact generation system  
**Source Discussion**: DISC-006_Knowledge-Archive-RAG-System.md  
**Created**: 2025-12-30 | SESSION_020

---

## How to Use These Prompts

Each prompt below is self-contained with:
1. **System context** - Project patterns and conventions
2. **RAG context** - Relevant codebase snippets (simulated retrieval)
3. **Source DISC summary** - The discussion that drives this artifact
4. **Generation instructions** - What to produce

Copy the entire prompt block and send to xAI API.

---

# PROMPT 1: ADR Generation (ADR-0046)

```
<SYSTEM_CONTEXT>
You are generating an Architecture Decision Record (ADR) for the engineering-tools platform.

## Project Conventions
- ADRs are JSON files in `.adrs/` directory
- Follow ADR-0034 naming: `ADR-XXXX_{title}.json`
- Status values: proposed, active, deprecated, superseded
- All ADRs must reference related DISCs, SPECs, and other ADRs
- Use Calendar Versioning: YYYY.MM.PATCH (per ADR-0016)

## ADR JSON Schema
{
  "id": "ADR-XXXX",
  "title": "string",
  "status": "proposed|active|deprecated|superseded",
  "created": "YYYY-MM-DD",
  "updated": "YYYY-MM-DD", 
  "context": "string - why this decision is needed",
  "decision": "string - the primary decision",
  "decision_details": ["array of implementation details"],
  "consequences": ["array of outcomes"],
  "alternatives_considered": [{"option": "string", "pros": "string", "cons": "string", "rejected_reason": "string"}],
  "references": {"discs": [], "adrs": [], "specs": []}
}
</SYSTEM_CONTEXT>

<RAG_CONTEXT>
## Existing Codebase Patterns (Retrieved)

### 1. SQLite Database Pattern (from shared/storage/registry_db.py)
```python
class RegistryDB:
    """SQLite-backed artifact registry."""
    
    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is None:
            workspace = get_workspace_path()
            workspace.mkdir(parents=True, exist_ok=True)
            db_path = workspace / ".registry.db"
        self.db_path = db_path
    
    async def initialize(self) -> None:
        """Initialize database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(CREATE_TABLES_SQL)
```

### 2. Existing LLM Logging (from gateway/services/llm_service.py)
```python
LLM_LOG_DB = Path(__file__).parent.parent.parent / "workspace" / "llm_logs.db"

def _init_llm_log_db() -> None:
    """Initialize the SQLite database for LLM logging."""
    LLM_LOG_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(LLM_LOG_DB))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt TEXT NOT NULL,
            ...
        )
    """)
```

### 3. Artifact Enums (from shared/contracts/devtools/workflow.py)
```python
class ArtifactType(str, Enum):
    DISCUSSION = "discussion"
    ADR = "adr"
    SPEC = "spec"
    PLAN = "plan"
    CONTRACT = "contract"

class RelationshipType(str, Enum):
    IMPLEMENTS = "implements"
    REFERENCES = "references"
    CREATES = "creates"
    SUPERSEDES = "supersedes"
    DEPENDS_ON = "depends_on"
```

### 4. Workspace Path Handling (from shared/storage/artifact_store.py)
```python
def get_workspace_path() -> Path:
    """Get the workspace directory path."""
    import os
    workspace = os.environ.get("ENGINEERING_TOOLS_WORKSPACE")
    if workspace:
        return Path(workspace)
    # Default: workspace/ in repo root
    current = Path.cwd()
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current / "workspace"
        current = current.parent
    return Path.cwd() / "workspace"
```
</RAG_CONTEXT>

<SOURCE_DISCUSSION>
## DISC-006: Knowledge Archive & RAG System (Summary)

### Problem
- LLM generates generic content (72/100 score, no project awareness)
- Historical context scattered in files (not queryable, not linked)
- No cost tracking per session (can't measure ROI)
- 2M token context window using <1% of capacity

### Solution
Unified `workspace/knowledge.db` serving dual purposes:
1. **Archive** - Persistent storage for sessions, plans, artifacts with bidirectional file sync
2. **RAG Corpus** - Semantic search and context injection for LLM prompts

### Design Decisions
1. **Embedding Model**: Dual-mode (local `all-mpnet-base-v2` + API fallback)
2. **Chunk Size**: Hybrid content-aware strategy
3. **Sync**: Watchdog real-time with on-demand fallback
4. **Retention**: Archive everything (soft delete)

### Cross-DISC Dependencies
- DISC-003: Langchain adapter (Phase 4)
- DISC-004: PII sanitization (Phase 3)
- DISC-005: Embedding model selection (Phase 3)

### Implementation Phases
- Phase 1: Archive Core (3-4 days)
- Phase 2: Search (2-3 days)
- Phase 3: RAG (5-7 days)
- Phase 4: Integration (2-3 days)
</SOURCE_DISCUSSION>

<GENERATION_INSTRUCTIONS>
Generate ADR-0046 as a JSON object for the Knowledge Archive & RAG System.

Requirements:
1. ID must be "ADR-0046"
2. Title: "Knowledge Archive & RAG System"
3. Context must explain WHY we need unified knowledge storage
4. Decision must state the primary architectural choice (unified SQLite DB)
5. Decision details must cover the 4 design decisions from DISC-006
6. Consequences must include both positive outcomes and technical debt
7. Alternatives considered must include: separate DBs, cloud vector store, file-only approach
8. References must include: DISC-003, DISC-004, DISC-005, DISC-006, ADR-0002 (artifact preservation)

Output ONLY valid JSON matching the schema above.
</GENERATION_INSTRUCTIONS>
```

---

# PROMPT 2: SPEC Generation (SPEC-0035)

```
<SYSTEM_CONTEXT>
You are generating a Technical Specification (SPEC) for the engineering-tools platform.

## Project Conventions
- SPECs are JSON files in `docs/specs/` directory
- Follow naming: `SPEC-XXXX_{title}.json`
- Status values: draft, active, deprecated
- SPECs define WHAT (behavioral requirements), not HOW (implementation)
- Must include functional requirements (FR-X) and non-functional requirements (NFR-X)
- API endpoints follow pattern: /api/{tool}/{resource}

## SPEC JSON Schema
{
  "id": "SPEC-XXXX",
  "title": "string",
  "status": "draft|active|deprecated",
  "created": "YYYY-MM-DD",
  "implements_adr": "ADR-XXXX",
  "purpose": "string",
  "scope": "string - what is in/out of scope",
  "functional_requirements": [
    {"id": "FR-1", "description": "string", "priority": "must|should|could"}
  ],
  "non_functional_requirements": [
    {"id": "NFR-1", "category": "performance|security|reliability", "description": "string", "metric": "string"}
  ],
  "api_endpoints": [
    {"method": "GET|POST|PUT|DELETE", "path": "/api/...", "description": "string", "request_body": "string|null", "response": "string"}
  ],
  "acceptance_criteria": ["string"],
  "references": {"discs": [], "adrs": [], "specs": []}
}
</SYSTEM_CONTEXT>

<RAG_CONTEXT>
## Existing API Patterns (Retrieved)

### 1. DevTools Service Endpoints (from gateway/services/devtools_service.py)
Pattern: FastAPI router with typed Pydantic responses
- GET /api/devtools/artifacts - List all artifacts
- GET /api/devtools/artifacts/graph - Get relationship graph
- POST /api/devtools/artifacts - Create artifact

### 2. LLM Service Stats Endpoint (from gateway/services/llm_service.py)
```python
def get_llm_usage_stats() -> dict:
    """Get usage statistics from the log database."""
    return {
        "total_calls": row[0] or 0,
        "total_cost": row[1] or 0.0,
        "total_input_tokens": row[2] or 0,
        "total_output_tokens": row[3] or 0,
    }
```

### 3. Existing Contract Patterns (from shared/contracts/devtools/workflow.py)
```python
class ArtifactListResponse(BaseModel):
    items: list[ArtifactSummary] = Field(default_factory=list)
    total: int = Field(...)

class GraphResponse(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
```
</RAG_CONTEXT>

<SOURCE_DISCUSSION>
## DISC-006: Knowledge Archive & RAG System

### Core Capabilities Required
1. **Bidirectional Sync**: File saved → DB updated; DB query → file export
2. **Full-Text Search**: FTS5 across all content
3. **Semantic Search**: Vector similarity for RAG
4. **Cost Tracking**: LLM spend per session/project
5. **Relationship Graph**: Link sessions → plans → ADRs
6. **Context Builder**: Auto-inject relevant context into prompts

### Proposed API Endpoints
- GET /api/knowledge/search?q=... - Full-text search
- GET /api/knowledge/semantic?q=... - Semantic search
- GET /api/knowledge/docs/{id} - Get document
- GET /api/knowledge/docs/{id}/export - Export to file
- POST /api/knowledge/sync - Force file sync
- GET /api/knowledge/stats - Usage statistics
- GET /api/knowledge/context?prompt=... - Build RAG context

### Design Decisions
- Watchdog sync (real-time) with manual fallback
- Dual embedding mode (local + API)
- Soft delete retention policy
</SOURCE_DISCUSSION>

<GENERATION_INSTRUCTIONS>
Generate SPEC-0035 as a JSON object for the Knowledge Archive & RAG System.

Requirements:
1. ID must be "SPEC-0035"
2. Title: "Knowledge Archive & RAG System Specification"
3. implements_adr: "ADR-0046"
4. Purpose must explain the behavioral goals
5. Functional requirements (at least 10):
   - FR-1 through FR-4: Archive operations (ingest, sync, export, query)
   - FR-5 through FR-7: Search operations (FTS, semantic, hybrid)
   - FR-8 through FR-10: RAG operations (chunking, embedding, context building)
6. Non-functional requirements (at least 5):
   - Performance: search latency, sync speed
   - Reliability: data consistency, crash recovery
   - Security: PII handling (reference DISC-004)
7. API endpoints must match the patterns from DISC-006
8. Acceptance criteria must be testable statements
9. References must include DISC-003, DISC-004, DISC-005, DISC-006, ADR-0046

Output ONLY valid JSON matching the schema above.
</GENERATION_INSTRUCTIONS>
```

---

# PROMPT 3: Contract Generation (Pydantic Models)

```
<SYSTEM_CONTEXT>
You are generating Pydantic contracts for the engineering-tools platform.

## Project Conventions
- Contracts go in `shared/contracts/{domain}/` directory
- All contracts are Pydantic BaseModel classes
- Must include `__version__ = "YYYY.MM.PATCH"` at module level
- Use Python 3.11+ type hints: `list[str]` not `List[str]`, `X | None` not `Optional[X]`
- All fields must have Field() with description
- Enums use `str, Enum` pattern for JSON serialization
- Google-style docstrings required

## Example Contract Pattern
```python
"""Domain contracts for {feature}.

Per ADR-XXXX: {brief description}.
"""

from enum import Enum
from pydantic import BaseModel, Field

__version__ = "2025.12.01"

class SomeEnum(str, Enum):
    """Description."""
    VALUE_A = "value_a"
    VALUE_B = "value_b"

class SomeModel(BaseModel):
    """Description of the model."""
    
    field_name: str = Field(..., description="What this field is")
    optional_field: int | None = Field(None, description="Optional field")
```
</SYSTEM_CONTEXT>

<RAG_CONTEXT>
## Existing Contract Patterns (Retrieved)

### 1. Workflow Contracts (from shared/contracts/devtools/workflow.py)
```python
__version__ = "2025.12.01"

class ArtifactType(str, Enum):
    """Types of workflow artifacts."""
    DISCUSSION = "discussion"
    ADR = "adr"
    SPEC = "spec"
    PLAN = "plan"
    CONTRACT = "contract"

class GraphNode(BaseModel):
    """A node in the artifact relationship graph."""
    id: str = Field(..., description="Unique artifact ID")
    type: ArtifactType = Field(..., description="Artifact type")
    label: str = Field(..., description="Display label")
    status: ArtifactStatus = Field(..., description="Current status")
    file_path: str = Field(..., description="Relative path to artifact file")
```

### 2. Registry Contracts (from shared/contracts/core/artifact_registry.py)
```python
class ArtifactRecord(BaseModel):
    """Record of an artifact in the registry."""
    artifact_id: str
    artifact_type: ArtifactType
    name: str
    relative_path: str
    created_at: datetime
    updated_at: datetime
    state: ArtifactState
    parent_ids: list[str] = Field(default_factory=list)
```

### 3. Dataset Contracts (from shared/contracts/core/dataset.py)
```python
class DataSetManifest(BaseModel):
    """Manifest for a DataSet."""
    dataset_id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Human-readable name")
    created_at: str = Field(..., description="ISO-8601 timestamp")
    columns: list[ColumnSchema] = Field(..., description="Column definitions")
```
</RAG_CONTEXT>

<SOURCE_DISCUSSION>
## DISC-006: Knowledge Archive Schema

### Database Tables Needed
- documents: sessions, plans, DISCs, ADRs (id, type, title, status, content, metadata)
- llm_calls: API logs with cost tracking (session_id, model, tokens, cost)
- chunks: Text segments for RAG (doc_id, chunk_index, content)
- embeddings: Vector representations (chunk_id, vector blob)
- relationships: Cross-references (source_id, target_id, type)

### Document Types
- session, plan, discussion, adr, spec, contract

### Search Capabilities
- Full-text search (FTS5)
- Semantic search (vector similarity)
- Relationship traversal
</SOURCE_DISCUSSION>

<GENERATION_INSTRUCTIONS>
Generate Python code for `shared/contracts/knowledge/__init__.py` with Pydantic models.

Required models:
1. **Enums**:
   - `DocumentType`: session, plan, discussion, adr, spec, contract
   - `EmbeddingMode`: local, api
   - `SyncMode`: watchdog, manual
   - `SearchType`: fulltext, semantic, hybrid

2. **Core Models**:
   - `KnowledgeDocument`: id, type, title, status, file_path, content, metadata (JSON), created_at, updated_at, archived_at
   - `DocumentChunk`: id, doc_id, chunk_index, content, token_count
   - `ChunkEmbedding`: chunk_id, vector (list[float]), model_name, dimensions
   - `DocumentRelationship`: source_id, target_id, relationship_type

3. **LLM Tracking Models**:
   - `LLMCall`: id, session_id, timestamp, model, prompt, response, tokens_in, tokens_out, cost, success
   - `LLMUsageStats`: total_calls, total_cost, total_input_tokens, total_output_tokens, by_model (dict)

4. **Search Models**:
   - `SearchQuery`: query, search_type, top_k, filters (optional)
   - `SearchResult`: doc_id, chunk_id, content, score, metadata
   - `SearchResponse`: results (list), total_count, search_type, latency_ms

5. **RAG Models**:
   - `RAGContext`: chunks (list[SearchResult]), total_tokens, sanitized (bool)
   - `ContextRequest`: prompt, max_tokens, include_types (list[DocumentType])

Include proper imports, __version__, and docstrings.
Output ONLY valid Python code.
</GENERATION_INSTRUCTIONS>
```

---

# PROMPT 4: PLAN Generation (PLAN-002)

```
<SYSTEM_CONTEXT>
You are generating an Implementation Plan for the engineering-tools platform.

## Project Conventions
- Plans are JSON files in `.plans/` directory
- Follow naming: `PLAN-XXX_{title}.json`
- Plans contain milestones with tasks
- Each task has acceptance criteria with verification commands
- Granularity levels: L1 (premium models), L2 (mid-tier), L3 (budget)
- Tasks should be atomic and verifiable

## PLAN JSON Schema
{
  "id": "PLAN-XXX",
  "title": "string",
  "status": "draft|active|completed|superseded",
  "created": "YYYY-MM-DD",
  "implements_spec": "SPEC-XXXX",
  "objective": "string",
  "granularity": "L1|L2|L3",
  "milestones": [
    {
      "id": "M1",
      "title": "string",
      "description": "string",
      "tasks": [
        {
          "id": "T-M1-01",
          "description": "string",
          "acceptance_criteria": ["string with verification command"],
          "context": ["FILE: path", "FUNCTION: name"],
          "estimated_hours": 1
        }
      ]
    }
  ],
  "success_criteria": ["string"],
  "references": {"discs": [], "adrs": [], "specs": []}
}
</SYSTEM_CONTEXT>

<RAG_CONTEXT>
## Existing Plan Patterns (Retrieved)

### 1. PLAN-001 Structure (DevTools Workflow Manager)
- M1: Backend API Foundation (contracts, services)
- M2-M9: Frontend components
- M10-M12: Integration and polish

### 2. Implementation Phases from DISC-006
- Phase 1: Archive Core (3-4 days) - Schema, ingest, watcher, export, migrate llm_logs
- Phase 2: Search (2-3 days) - FTS5, search API, relationships, basic UI
- Phase 3: RAG (5-7 days) - Chunking, embeddings, vector search, context builder, PII
- Phase 4: Integration (2-3 days) - Prompt injection, Langchain adapter, cost dashboard

### 3. File Locations to Create
- `shared/contracts/knowledge/__init__.py` - Pydantic models
- `shared/storage/knowledge_db.py` - SQLite database class
- `gateway/services/knowledge_service.py` - Business logic
- `gateway/services/embedding_service.py` - Embedding generation
- `gateway/routes/knowledge.py` - API endpoints (or add to devtools_service.py)
</RAG_CONTEXT>

<SOURCE_DISCUSSION>
## DISC-006: Implementation Details

### Phase 1: Archive Core
- Create knowledge.db schema (documents, llm_calls, relationships)
- Document ingest (parse sessions, plans, DISCs, ADRs)
- File watcher for auto-sync (watchdog library)
- Export to original format
- Migrate existing llm_logs.db data

### Phase 2: Search
- FTS5 virtual table indexing
- Search API endpoints
- Relationship tracking on ingest
- Basic search UI component

### Phase 3: RAG
- Chunking pipeline (content-aware)
- Embedding generation (sentence-transformers)
- Vector similarity search
- Context builder
- PII sanitizer integration (DISC-004)

### Phase 4: Integration
- Inject context into LLM prompts
- Langchain adapter (DISC-003)
- Cost dashboard component
</SOURCE_DISCUSSION>

<GENERATION_INSTRUCTIONS>
Generate PLAN-002 as a JSON object for the Knowledge Archive & RAG System implementation.

Requirements:
1. ID must be "PLAN-002"
2. Title: "Knowledge Archive & RAG System Implementation"
3. implements_spec: "SPEC-0035"
4. Granularity: "L1" (this is a complex feature)
5. Objective must state the measurable goal

6. Milestones (4 total, matching phases):
   **M1: Archive Core** (5-6 tasks)
   - T-M1-01: Create contracts in shared/contracts/knowledge/
   - T-M1-02: Create KnowledgeDB class with schema
   - T-M1-03: Implement document ingest (parse all artifact types)
   - T-M1-04: Implement file watcher (watchdog)
   - T-M1-05: Implement export functionality
   - T-M1-06: Migrate llm_logs.db data
   
   **M2: Search** (4 tasks)
   - T-M2-01: Add FTS5 virtual table
   - T-M2-02: Implement search API endpoints
   - T-M2-03: Add relationship tracking on ingest
   - T-M2-04: Basic search UI component
   
   **M3: RAG** (5 tasks)
   - T-M3-01: Implement chunking pipeline
   - T-M3-02: Add embedding service (dual-mode)
   - T-M3-03: Implement vector similarity search
   - T-M3-04: Build context builder
   - T-M3-05: Integrate PII sanitizer (stub, depends on DISC-004)
   
   **M4: Integration** (3 tasks)
   - T-M4-01: Inject RAG context into LLM service
   - T-M4-02: Add Langchain adapter (stub, depends on DISC-003)
   - T-M4-03: Cost dashboard component

7. Each task must have:
   - Clear description
   - At least 2 acceptance criteria with grep/pytest verification commands
   - Context references (files to modify/create)
   - Estimated hours (1-4 per task)

8. Success criteria must include:
   - All tests pass
   - Search returns relevant results
   - RAG context improves LLM output quality
   - Cost tracking accurate

9. References: DISC-003, DISC-004, DISC-005, DISC-006, ADR-0046, SPEC-0035

Output ONLY valid JSON matching the schema above.
</GENERATION_INSTRUCTIONS>
```

---

## Prompt Usage Notes

1. **Context Window**: Each prompt is ~3-4K tokens. xAI's 2M context window can easily handle adding more RAG context if needed.

2. **Temperature**: Use 0.3-0.5 for structured output (JSON), 0.7 for prose sections.

3. **Validation**: All outputs should be validated against the schemas before saving.

4. **Iteration**: If output quality is low, add more RAG context from the codebase or increase specificity in instructions.

5. **Cross-DISC Awareness**: Each prompt references dependent DISCs (003, 004, 005) to maintain consistency.

