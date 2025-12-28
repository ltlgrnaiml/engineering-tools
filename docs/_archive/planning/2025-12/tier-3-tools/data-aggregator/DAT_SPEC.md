# Tier 3: Data Aggregator Tool Specification

**Document Type:** Tool Specification  
**Audience:** Engineers  
**Last Updated:** 2025-01-26

---

## Overview

The Data Aggregator (DAT) is the primary data ingestion tool. It extracts data from multiple sources, aggregates at user-specified levels, and exports standardized DataSets for downstream tools.

---

## Responsibilities

1. **File Selection** - Browse and select source data files
2. **Profile Management** - Load/save extraction profiles
3. **Context Configuration** - Configure parsing hints and column mappings
4. **Table Availability** - Probe and display available tables
5. **Preview** - Preview extracted data before full parse
6. **Parse** - Full data extraction with progress tracking
7. **Export** - Output DataSet with aggregation and lineage

---

## Stage Orchestration (per ADR-0001)

### Stage Flow

```text
Selection → Context → Table Availability → Table Selection → Preview → Parse → Export
    │          │              │                   │            │        │        │
    │          │              │                   │            │        │        └─ DataSet
    │          │              │                   │            │        └─ Parquet artifact
    │          │              │                   │            └─ Optional validation
    │          │              │                   └─ User selects tables to parse
    │          │              └─ Probe available tables
    │          └─ Optional parsing hints
    └─ File selection
```

### Stage States

Each stage has independent UNLOCKED ↔ LOCKED lifecycle:

```text
┌──────────┐     lock()     ┌──────────┐
│ UNLOCKED │ ──────────────▶│  LOCKED  │
│          │◀────────────── │          │
└──────────┘    unlock()    └──────────┘
                (preserves artifact)
```

### Forward Gating Rules

| Stage | Requires |
|-------|----------|
| Context | Selection.locked |
| Table Availability | Selection.locked |
| Table Selection | Table Availability.locked |
| Preview | Table Selection.locked |
| Parse | Table Selection.locked |
| Export | Parse.locked AND Parse.completed |

### Cascade Unlock Rules

When a stage unlocks, downstream stages also unlock:

- Unlock Selection → Unlocks all downstream
- Unlock Context → No cascade (independent)
- Unlock Table Selection → Unlocks Preview, Parse, Export
- Unlock Parse → Unlocks Export

---

## Acceptance Criteria (DAT)

### AC-DAT1: File Selection

- [ ] User can browse local filesystem for data files
- [ ] Supported formats: CSV, TSV, Excel, Parquet
- [ ] Multiple files can be selected
- [ ] Selection can be locked/unlocked
- [ ] Selection state persists across sessions

### AC-DAT2: Profile Management

- [ ] User can load existing extraction profiles
- [ ] User can save current configuration as profile
- [ ] Profile includes: file patterns, column mappings, aggregation levels
- [ ] Default profile used when none specified

### AC-DAT3: Context Configuration (Optional)

- [ ] User can configure parsing hints
- [ ] Column type overrides supported
- [ ] Context is optional (Parse uses profile defaults if skipped)
- [ ] Context does not cascade unlock

### AC-DAT4: Table Availability

- [ ] Tables are probed from selected files
- [ ] Status shown: available, partial, missing, empty
- [ ] Deterministic probe logic (per ADR-0006)
- [ ] Results cached with stage ID

### AC-DAT5: Table Selection

- [ ] User selects which tables to parse
- [ ] Select all / deselect all supported
- [ ] Selection state saved in artifact

### AC-DAT6: Preview (Optional)

- [ ] Preview first N rows of selected tables
- [ ] Preview is optional (can skip to Parse)
- [ ] Preview does not cascade unlock

### AC-DAT7: Parse

- [ ] Full data extraction with progress indicator
- [ ] Cancellation supported (preserves partial, per ADR-0013)
- [ ] Output saved as Parquet (per ADR-0014)
- [ ] Deterministic stage ID (per ADR-0004)

### AC-DAT8: Export

- [ ] Aggregation at user-specified levels
- [ ] Output as DataSet with manifest
- [ ] Lineage tracking (source files in manifest)
- [ ] "Pipe To" button for downstream tools

---

## Code Map

### Backend Structure

```text
apps/data_aggregator/backend/
├── src/dat_aggregation/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # FastAPI routes
│   │   ├── deps.py             # Dependencies (store, registry)
│   │   └── schemas.py          # Request/Response models
│   ├── core/
│   │   ├── __init__.py
│   │   ├── state_machine.py    # FSM orchestration (ADR-0001)
│   │   ├── stage_manager.py    # Stage lifecycle
│   │   ├── run_manager.py      # Run CRUD operations
│   │   └── artifact_writer.py  # Parquet/JSON output
│   ├── stages/
│   │   ├── __init__.py
│   │   ├── selection.py        # File selection stage
│   │   ├── context.py          # Context configuration
│   │   ├── table_availability.py
│   │   ├── table_selection.py
│   │   ├── preview.py
│   │   ├── parse.py            # Main parsing logic
│   │   └── export.py           # DataSet export
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── factory.py          # AdapterFactory (ADR-0011)
│   │   ├── csv_adapter.py
│   │   ├── excel_adapter.py
│   │   └── parquet_adapter.py
│   └── profiles/
│       ├── __init__.py
│       ├── loader.py           # Profile loading
│       └── defaults/           # Default profiles
└── main.py                     # FastAPI app
```

### Key Functions

#### `core/state_machine.py`

```python
class DATStateMachine:
    """Hybrid FSM for DAT stage orchestration (per ADR-0001)."""
    
    async def lock_stage(self, run_id: str, stage: Stage) -> StageResult
    async def unlock_stage(self, run_id: str, stage: Stage) -> StageResult
    async def get_stage_status(self, run_id: str, stage: Stage) -> StageStatus
    async def can_lock(self, run_id: str, stage: Stage) -> tuple[bool, str]
    def get_cascade_targets(self, stage: Stage) -> list[Stage]
```

#### `stages/parse.py`

```python
async def execute_parse(
    run_id: str,
    table_selection: TableSelectionArtifact,
    profile: Profile,
    progress_callback: Callable[[float], None],
    cancel_token: CancelToken,
) -> ParseResult:
    """Execute full parse with progress and cancellation support."""
```

#### `stages/export.py`

```python
async def execute_export(
    run_id: str,
    parse_result: ParseResult,
    aggregation_levels: list[str],
    profile: Profile,
) -> DataSetManifest:
    """Export parsed data as DataSet with lineage."""
```

### Frontend Structure

```text
apps/data_aggregator/frontend/
├── src/
│   ├── components/
│   │   ├── stages/
│   │   │   ├── SelectionPanel.tsx
│   │   │   ├── ContextPanel.tsx
│   │   │   ├── TableAvailabilityPanel.tsx
│   │   │   ├── TableSelectionPanel.tsx
│   │   │   ├── PreviewPanel.tsx
│   │   │   ├── ParsePanel.tsx
│   │   │   └── ExportPanel.tsx
│   │   ├── StageIndicator.tsx
│   │   └── RunHeader.tsx
│   ├── hooks/
│   │   ├── useRun.ts
│   │   ├── useStage.ts
│   │   └── useParse.ts
│   ├── pages/
│   │   ├── DATHome.tsx
│   │   └── RunPage.tsx
│   └── App.tsx
└── package.json
```

---

## API Endpoints

### Runs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/runs` | POST | Create new run |
| `/v1/runs` | GET | List runs |
| `/v1/runs/{id}` | GET | Get run details |
| `/v1/runs/{id}` | DELETE | Delete run |

### Stages

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/runs/{id}/stages/{stage}` | GET | Get stage status |
| `/v1/runs/{id}/stages/{stage}/lock` | POST | Lock stage |
| `/v1/runs/{id}/stages/{stage}/unlock` | POST | Unlock stage |

### Selection

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/runs/{id}/selection` | GET | Get current selection |
| `/v1/runs/{id}/selection` | PUT | Update selection |
| `/v1/runs/{id}/selection/browse` | GET | Browse filesystem |

### Parse & Export

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/runs/{id}/parse` | POST | Start parse |
| `/v1/runs/{id}/parse` | GET | Get parse status |
| `/v1/runs/{id}/parse/cancel` | POST | Cancel parse |
| `/v1/runs/{id}/export` | POST | Export as DataSet |

---

## Data Flow

```text
Input Files          Profile           User Config
    │                   │                   │
    ▼                   ▼                   ▼
┌─────────────────────────────────────────────────┐
│              Adapter Factory                     │
│  (selects CSV/Excel/Parquet adapter by format)  │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│              Parse Stage                         │
│  - Read files via adapter                        │
│  - Apply column mappings                         │
│  - Type coercion                                 │
│  - Progress tracking                             │
└─────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│              Export Stage                        │
│  - Aggregate by levels                           │
│  - Compute DataSet ID (deterministic)            │
│  - Write Parquet + manifest                      │
│  - Register in artifact store                    │
└─────────────────────────────────────────────────┘
                        │
                        ▼
                   DataSet
              (ready for piping)
```

---

## Change Order

### Phase 3A: Backend Core (Week 3)

1. Create `apps/data-aggregator/backend/` structure
2. Implement `core/state_machine.py` (FSM)
3. Implement `core/run_manager.py`
4. Create API routes skeleton
5. Write unit tests for state machine

### Phase 3B: Stages (Week 3-4)

1. Implement Selection stage
2. Implement Table Availability stage
3. Implement Parse stage with adapters
4. Implement Export stage with DataSet output
5. Add Context and Preview (optional stages)

### Phase 3C: Frontend (Week 4)

1. Create frontend structure
2. Implement stage panels
3. Add progress tracking
4. Implement "Pipe To" integration

### Phase 3D: Integration (Week 4-5)

1. End-to-end testing
2. Integration with gateway
3. Integration with shared storage
4. Performance optimization

---

## Validation Plan

### Unit Tests

- [ ] State machine transitions
- [ ] Cascade unlock logic
- [ ] Adapter parsing for each format
- [ ] Deterministic ID generation

### Integration Tests

- [ ] Full run: Selection → Parse → Export
- [ ] Cancel during parse
- [ ] Unlock and re-lock
- [ ] DataSet export with lineage

### E2E Tests

- [ ] UI: Create run, select files, parse, export
- [ ] UI: Pipe to PPTX
- [ ] API: Full workflow via Swagger

---

## ADR References

| ADR | Application in DAT |
|-----|-------------------|
| ADR-0001 | Stage FSM orchestration |
| ADR-0002 | Artifact preservation on unlock |
| ADR-0003 | Optional Context and Preview |
| ADR-0004 | Deterministic stage IDs |
| ADR-0006 | Table availability status model |
| ADR-0011 | Profile-driven adapters |
| ADR-0013 | Parse cancellation semantics |
| ADR-0014 | Parquet for parse, multi-format export |
