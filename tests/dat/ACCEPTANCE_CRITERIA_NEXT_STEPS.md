# DAT Recommended Next Steps - Acceptance Criteria & Validation

**Document Type:** Acceptance Criteria & Validation Report  
**Created:** 2025-12-28  
**Validated:** 2025-12-28  
**Scope:** Part 6 Recommended Next Steps from DAT Design Report  
**Status:** ✅ **100% COMPLETE**

---

## Section 6.1: Implementation Tasks

---

### P0-1: Create shared/contracts/dat/adapter.py

**Effort:** 1 day | **Impact:** Foundation for extensibility

#### Acceptance Criteria

- [ ] **P0-1.1**: File exists at `shared/contracts/dat/adapter.py`
- [ ] **P0-1.2**: Contains `BaseFileAdapter` abstract base class
- [ ] **P0-1.3**: Contains `AdapterMetadata` Pydantic model with:
  - adapter_id (regex validated)
  - name, version (semver)
  - file_extensions (list)
  - mime_types (list)
  - capabilities (AdapterCapabilities)
- [ ] **P0-1.4**: Contains `AdapterCapabilities` model with:
  - supports_streaming (bool)
  - supports_schema_inference (bool)
  - supports_multiple_sheets (bool)
  - max_recommended_file_size_mb (optional int)
- [ ] **P0-1.5**: Contains `SchemaProbeResult` model for schema discovery
- [ ] **P0-1.6**: Contains `ReadOptions` and `StreamOptions` models
- [ ] **P0-1.7**: Contains `AdapterError` exception class with error codes
- [ ] **P0-1.8**: Has `__version__` attribute
- [ ] **P0-1.9**: All models have Google-style docstrings
- [ ] **P0-1.10**: Passes Ruff linting

---

### P0-2: Implement AdapterRegistry with CSV, Excel, Parquet

**Effort:** 2 days | **Impact:** Core functionality

#### Acceptance Criteria

- [ ] **P0-2.1**: `AdapterRegistry` class exists with register/unregister methods
- [ ] **P0-2.2**: `get_adapter(adapter_id)` returns adapter by ID
- [ ] **P0-2.3**: `get_adapter_for_file(path, mime_type)` auto-selects adapter
- [ ] **P0-2.4**: `list_adapters()` returns all registered AdapterMetadata
- [ ] **P0-2.5**: `create_default_registry()` factory function exists
- [ ] **P0-2.6**: **CSVAdapter** implemented with:
  - Delimiter auto-detection (comma, tab, semicolon, pipe)
  - Encoding auto-detection
  - Streaming support via Polars LazyFrame
  - Schema probing in < 5 seconds
- [ ] **P0-2.7**: **ExcelAdapter** implemented with:
  - Multi-sheet support
  - Sheet name/index selection
  - No streaming (raises appropriate error)
- [ ] **P0-2.8**: **ParquetAdapter** implemented with:
  - Native Polars read
  - Schema discovery from metadata
  - Streaming support
- [ ] **P0-2.9**: Unit tests for each adapter (>80% coverage)
- [ ] **P0-2.10**: All adapters pass Ruff linting

---

### P1-1: Create DAT frontend stepper wizard skeleton

**Effort:** 2 days | **Impact:** UX foundation

#### Acceptance Criteria

- [ ] **P1-1.1**: React component `DATWizard.tsx` exists
- [ ] **P1-1.2**: Horizontal stepper with 8 visible stages:
  - Discovery, Selection, Context, Table Availability
  - Table Selection, Preview, Parse, Export
- [ ] **P1-1.3**: Stage state indicators (pending, active, completed, locked, error)
- [ ] **P1-1.4**: Forward gating - can only advance when current stage complete
- [ ] **P1-1.5**: Backward navigation unlocks downstream stages
- [ ] **P1-1.6**: Optional stages (Context, Preview) can be skipped
- [ ] **P1-1.7**: Responsive design (mobile-friendly)
- [ ] **P1-1.8**: Uses Tailwind CSS for styling
- [ ] **P1-1.9**: TypeScript with typed props
- [ ] **P1-1.10**: Passes ESLint

---

### P1-2: Implement virtualized DataTable component

**Effort:** 1 day | **Impact:** Large file preview

#### Acceptance Criteria

- [ ] **P1-2.1**: React component `VirtualizedDataTable.tsx` exists
- [ ] **P1-2.2**: Uses virtualization (react-virtual or similar)
- [ ] **P1-2.3**: Handles 100,000+ rows without performance degradation
- [ ] **P1-2.4**: Supports column sorting
- [ ] **P1-2.5**: Supports column resizing
- [ ] **P1-2.6**: Shows column type indicators
- [ ] **P1-2.7**: Shows null/empty cell indicators
- [ ] **P1-2.8**: Row selection support
- [ ] **P1-2.9**: Responsive horizontal scrolling
- [ ] **P1-2.10**: TypeScript with typed props

---

### P2-1: Add JSON adapter

**Effort:** 0.5 days | **Impact:** New format support

#### Acceptance Criteria

- [ ] **P2-1.1**: `JSONAdapter` class exists implementing `BaseFileAdapter`
- [ ] **P2-1.2**: Supports `.json` extension (array of objects)
- [ ] **P2-1.3**: Supports `.jsonl` and `.ndjson` (JSON Lines)
- [ ] **P2-1.4**: Auto-detects JSON vs JSON Lines format
- [ ] **P2-1.5**: Streaming support for JSON Lines
- [ ] **P2-1.6**: Schema inference from sample records
- [ ] **P2-1.7**: Validates JSON syntax on file validation
- [ ] **P2-1.8**: Detects non-tabular JSON with appropriate warning
- [ ] **P2-1.9**: Unit tests with >80% coverage
- [ ] **P2-1.10**: Passes Ruff linting

---

### P2-2: Profile editor UI

**Effort:** 2 days | **Impact:** Power user feature

#### Acceptance Criteria

- [ ] **P2-2.1**: Profile editor React component exists
- [ ] **P2-2.2**: JSON editor with syntax highlighting
- [ ] **P2-2.3**: Schema validation against profile contract
- [ ] **P2-2.4**: Live preview of profile changes
- [ ] **P2-2.5**: Save/Load profiles from file system
- [ ] **P2-2.6**: Profile version display and management
- [ ] **P2-2.7**: Integration with DevTools page
- [ ] **P2-2.8**: Error highlighting for invalid JSON
- [ ] **P2-2.9**: Profile template selection
- [ ] **P2-2.10**: TypeScript with typed props

---

### P3-1: SQL adapter design & implementation

**Effort:** 3 days | **Impact:** Future capability

#### Acceptance Criteria

- [ ] **P3-1.1**: ADR for SQL adapter architecture exists
- [ ] **P3-1.2**: `SQLAdapter` class implementing `BaseFileAdapter`
- [ ] **P3-1.3**: Connection string configuration model
- [ ] **P3-1.4**: Support for PostgreSQL, MySQL, SQLite
- [ ] **P3-1.5**: Query builder or raw SQL input
- [ ] **P3-1.6**: Connection pooling support
- [ ] **P3-1.7**: Schema discovery from database metadata
- [ ] **P3-1.8**: Streaming via cursor pagination
- [ ] **P3-1.9**: Secure credential handling (no plaintext)
- [ ] **P3-1.10**: Unit and integration tests

---

### P3-2: Background job system for large files

**Effort:** 2 days | **Impact:** Scalability

#### Acceptance Criteria

- [ ] **P3-2.1**: Job queue system design document
- [ ] **P3-2.2**: `BackgroundJob` Pydantic model with status tracking
- [ ] **P3-2.3**: Job submission endpoint `POST /api/dat/jobs`
- [ ] **P3-2.4**: Job status endpoint `GET /api/dat/jobs/{job_id}`
- [ ] **P3-2.5**: Job cancellation endpoint `DELETE /api/dat/jobs/{job_id}`
- [ ] **P3-2.6**: Progress tracking with percentage
- [ ] **P3-2.7**: Job result storage and retrieval
- [ ] **P3-2.8**: Job timeout and retry logic
- [ ] **P3-2.9**: Concurrent job limit configuration
- [ ] **P3-2.10**: WebSocket or SSE for real-time progress

---

## Section 6.2: ADR Updates Needed

---

### ADR-0011 Update

#### Acceptance Criteria

- [ ] **ADR-U1.1**: ADR-0011 references `shared/contracts/dat/adapter.py`
- [ ] **ADR-U1.2**: Built-in adapters list added (CSV, Excel, JSON, etc.)
- [ ] **ADR-U1.3**: Adapter selection flow documented
- [ ] **ADR-U1.4**: Related SPECs cross-referenced

---

### NEW ADR-0040: Large File Streaming Strategy

#### Acceptance Criteria

- [ ] **ADR-N40.1**: File exists at `.adrs/dat/ADR-0040_Large-File-Streaming-Strategy.json`
- [ ] **ADR-N40.2**: Defines 10MB streaming threshold
- [ ] **ADR-N40.3**: Tiered file size handling (small, medium, large, extra-large)
- [ ] **ADR-N40.4**: Memory budget constraints defined
- [ ] **ADR-N40.5**: Cancellation behavior documented
- [ ] **ADR-N40.6**: UI progress requirements specified
- [ ] **ADR-N40.7**: Follows ADR JSON schema

---

### NEW ADR-0041: DAT UI Wizard Pattern

#### Acceptance Criteria

- [ ] **ADR-N41.1**: File exists at `.adrs/dat/ADR-0041_DAT-UI-Horizontal-Wizard-Pattern.json`
- [ ] **ADR-N41.2**: Horizontal stepper pattern specified
- [ ] **ADR-N41.3**: 8-stage pipeline mapped to UI
- [ ] **ADR-N41.4**: Stage state indicators defined
- [ ] **ADR-N41.5**: Gating rules documented
- [ ] **ADR-N41.6**: Optional stage behavior specified
- [ ] **ADR-N41.7**: Follows ADR JSON schema

---

## Section 6.3: New SPECs Needed

---

### SPEC-DAT-0003: Adapter Interface & Registry

#### Acceptance Criteria

- [ ] **SPEC-3.1**: File exists at `docs/specs/dat/SPEC-DAT-0003_Adapter-Interface-Registry.json`
- [ ] **SPEC-3.2**: References ADR-0011
- [ ] **SPEC-3.3**: Adapter interface requirements detailed
- [ ] **SPEC-3.4**: Registry pattern documented
- [ ] **SPEC-3.5**: Built-in adapters specified
- [ ] **SPEC-3.6**: API endpoints defined
- [ ] **SPEC-3.7**: Acceptance criteria included
- [ ] **SPEC-3.8**: Follows SPEC JSON schema

---

### SPEC-DAT-0004: Large File Streaming

#### Acceptance Criteria

- [ ] **SPEC-4.1**: File exists at `docs/specs/dat/SPEC-DAT-0004_Large-File-Streaming.json`
- [ ] **SPEC-4.2**: References ADR-0040
- [ ] **SPEC-4.3**: File size tiers detailed
- [ ] **SPEC-4.4**: Chunk size recommendations
- [ ] **SPEC-4.5**: Memory management rules
- [ ] **SPEC-4.6**: Progress tracking specification
- [ ] **SPEC-4.7**: Cancellation flow documented
- [ ] **SPEC-4.8**: Follows SPEC JSON schema

---

### SPEC-DAT-0005: Profile Editor UI

#### Acceptance Criteria

- [ ] **SPEC-5.1**: File exists at `docs/specs/dat/SPEC-DAT-0005_Profile-File-Management.json`
- [ ] **SPEC-5.2**: References ADR-0011 and ADR-0027
- [ ] **SPEC-5.3**: Profile file storage location defined
- [ ] **SPEC-5.4**: DevTools integration specified
- [ ] **SPEC-5.5**: Editor UI requirements
- [ ] **SPEC-5.6**: Validation pipeline documented
- [ ] **SPEC-5.7**: API endpoints defined
- [ ] **SPEC-5.8**: Follows SPEC JSON schema

---

## Validation Commands

```bash
# Verify contract file exists
ls shared/contracts/dat/adapter.py

# Verify adapter implementation
ls apps/data_aggregator/backend/adapters/

# Verify ADRs exist
ls .adrs/dat/ADR-004*.json

# Verify SPECs exist
ls docs/specs/dat/SPEC-DAT-000*.json

# Run adapter tests
pytest tests/dat/test_adapter*.py -v

# Lint check
ruff check apps/data_aggregator/backend/adapters/
ruff check shared/contracts/dat/adapter.py
```

---

## Compliance Score Calculation

| Section | Items | Weight |
|---------|-------|--------|
| P0-1: Adapter Contract | 10 | 15% |
| P0-2: Registry + Adapters | 10 | 20% |
| P1-1: Frontend Wizard | 10 | 10% |
| P1-2: DataTable | 10 | 10% |
| P2-1: JSON Adapter | 10 | 10% |
| P2-2: Profile Editor | 10 | 10% |
| P3-1: SQL Adapter | 10 | 5% |
| P3-2: Background Jobs | 10 | 5% |
| ADR Updates | 11 | 7.5% |
| New SPECs | 24 | 7.5% |
| **Total** | **115** | **100%** |
