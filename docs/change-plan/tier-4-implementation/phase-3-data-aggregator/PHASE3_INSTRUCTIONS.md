# Tier 4: Phase 3 Data Aggregator - Implementation Instructions

**Document Type:** Step-by-Step Implementation Guide  
**Audience:** AI Coding Assistants, Junior Developers  
**Status:** ⚠️ BACKEND COMPLETE (frontend pending)  
**Last Updated:** 2025-01-26

---

## Phase Overview

Phase 3 implements the Data Aggregator (DAT) tool with FSM-based stage orchestration, multi-format adapters, and DataSet export.

**Duration:** Week 3-5  
**Dependencies:** Phase 1, Phase 2 complete

---

## Step 3.1: Create DAT Backend Structure ✅

**Goal:** Set up FastAPI backend for Data Aggregator

**Location:** `apps/data_aggregator/backend/`

> **Implementation Status:** Complete. Full backend structure exists with state machine, stages, adapters, and API routes.

**Files to create:**

```
apps/data-aggregator/backend/
├── src/dat_aggregation/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── deps.py
│   │   └── schemas.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── state_machine.py
│   │   ├── stage_manager.py
│   │   ├── run_manager.py
│   │   └── artifact_writer.py
│   ├── stages/
│   │   ├── __init__.py
│   │   ├── selection.py
│   │   ├── context.py
│   │   ├── table_availability.py
│   │   ├── table_selection.py
│   │   ├── preview.py
│   │   ├── parse.py
│   │   └── export.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── factory.py
│   │   ├── base.py
│   │   ├── csv_adapter.py
│   │   ├── excel_adapter.py
│   │   └── parquet_adapter.py
│   └── profiles/
│       ├── __init__.py
│       └── loader.py
├── main.py
└── pyproject.toml
```

---

## Step 3.2: Implement State Machine (ADR-0001) ✅

**Goal:** Implement hybrid FSM for stage orchestration

**File:** `src/dat_aggregation/core/state_machine.py`

> **Implementation Status:** Complete. State machine with forward gating and cascade unlock implemented.

```python
"""Hybrid FSM for DAT stage orchestration.

Per ADR-0001: Each stage manages its own UNLOCKED ↔ LOCKED lifecycle,
while a global orchestrator coordinates unlock cascades.
"""
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from shared.utils.stage_id import compute_stage_id


class Stage(str, Enum):
    """DAT pipeline stages."""
    SELECTION = "selection"
    CONTEXT = "context"
    TABLE_AVAILABILITY = "table_availability"
    TABLE_SELECTION = "table_selection"
    PREVIEW = "preview"
    PARSE = "parse"
    EXPORT = "export"


class StageState(str, Enum):
    """State of a stage."""
    UNLOCKED = "unlocked"
    LOCKED = "locked"


@dataclass
class StageStatus:
    """Current status of a stage."""
    stage: Stage
    state: StageState
    stage_id: str | None = None
    locked_at: datetime | None = None
    unlocked_at: datetime | None = None
    completed: bool = False
    error: str | None = None


# Forward gating rules (per ADR-0001)
FORWARD_GATES: dict[Stage, list[tuple[Stage, bool]]] = {
    # Stage: [(required_stage, must_be_completed), ...]
    Stage.CONTEXT: [(Stage.SELECTION, False)],
    Stage.TABLE_AVAILABILITY: [(Stage.SELECTION, False)],
    Stage.TABLE_SELECTION: [(Stage.TABLE_AVAILABILITY, False)],
    Stage.PREVIEW: [(Stage.TABLE_SELECTION, False)],
    Stage.PARSE: [(Stage.TABLE_SELECTION, False)],
    Stage.EXPORT: [(Stage.PARSE, True)],  # Must be completed
}

# Cascade unlock rules (per ADR-0001)
CASCADE_TARGETS: dict[Stage, list[Stage]] = {
    Stage.SELECTION: [
        Stage.CONTEXT, Stage.TABLE_AVAILABILITY, Stage.TABLE_SELECTION,
        Stage.PREVIEW, Stage.PARSE, Stage.EXPORT
    ],
    Stage.TABLE_AVAILABILITY: [
        Stage.TABLE_SELECTION, Stage.PREVIEW, Stage.PARSE, Stage.EXPORT
    ],
    Stage.TABLE_SELECTION: [Stage.PREVIEW, Stage.PARSE, Stage.EXPORT],
    Stage.PARSE: [Stage.EXPORT],
    # Context and Preview do NOT cascade (per ADR-0003)
    Stage.CONTEXT: [],
    Stage.PREVIEW: [],
}


class DATStateMachine:
    """Hybrid FSM for DAT stage orchestration."""
    
    def __init__(self, run_id: str, store: "RunStore"):
        self.run_id = run_id
        self.store = store
    
    async def can_lock(self, stage: Stage) -> tuple[bool, str | None]:
        """Check if a stage can be locked (forward gating).
        
        Returns:
            (can_lock, reason) - reason is None if can_lock is True
        """
        gates = FORWARD_GATES.get(stage, [])
        
        for required_stage, must_complete in gates:
            status = await self.store.get_stage_status(self.run_id, required_stage)
            
            if status.state != StageState.LOCKED:
                return False, f"{required_stage.value} must be locked first"
            
            if must_complete and not status.completed:
                return False, f"{required_stage.value} must be completed first"
        
        return True, None
    
    async def lock_stage(
        self,
        stage: Stage,
        execute_fn: Callable[[], dict] | None = None,
    ) -> StageStatus:
        """Lock a stage, optionally executing its logic.
        
        Per ADR-0002: If stage ID exists, reuse artifact (idempotent re-lock).
        """
        # Check forward gating
        can_lock, reason = await self.can_lock(stage)
        if not can_lock:
            raise ValueError(f"Cannot lock {stage.value}: {reason}")
        
        # Get inputs for deterministic ID
        inputs = await self._get_stage_inputs(stage)
        stage_id = compute_stage_id(inputs, prefix=f"{stage.value}_")
        
        # Check for existing artifact (idempotent re-lock per ADR-0004)
        existing = await self.store.get_artifact(self.run_id, stage, stage_id)
        if existing:
            # Reuse existing artifact
            await self.store.set_stage_status(
                self.run_id, stage,
                StageStatus(
                    stage=stage,
                    state=StageState.LOCKED,
                    stage_id=stage_id,
                    locked_at=datetime.now(timezone.utc),
                    completed=existing.get("completed", False),
                )
            )
            return await self.store.get_stage_status(self.run_id, stage)
        
        # Execute stage logic if provided
        result = {}
        if execute_fn:
            result = await execute_fn()
        
        # Save artifact and update status
        await self.store.save_artifact(self.run_id, stage, stage_id, result)
        await self.store.set_stage_status(
            self.run_id, stage,
            StageStatus(
                stage=stage,
                state=StageState.LOCKED,
                stage_id=stage_id,
                locked_at=datetime.now(timezone.utc),
                completed=result.get("completed", True),
            )
        )
        
        return await self.store.get_stage_status(self.run_id, stage)
    
    async def unlock_stage(self, stage: Stage) -> list[StageStatus]:
        """Unlock a stage and cascade to downstream stages.
        
        Per ADR-0002: Artifacts are preserved (never deleted).
        """
        now = datetime.now(timezone.utc)
        unlocked: list[StageStatus] = []
        
        # Unlock this stage (preserve artifact)
        await self.store.set_stage_status(
            self.run_id, stage,
            StageStatus(
                stage=stage,
                state=StageState.UNLOCKED,
                unlocked_at=now,
            )
        )
        unlocked.append(await self.store.get_stage_status(self.run_id, stage))
        
        # Cascade to downstream stages
        for target in CASCADE_TARGETS.get(stage, []):
            status = await self.store.get_stage_status(self.run_id, target)
            if status.state == StageState.LOCKED:
                await self.store.set_stage_status(
                    self.run_id, target,
                    StageStatus(
                        stage=target,
                        state=StageState.UNLOCKED,
                        unlocked_at=now,
                    )
                )
                unlocked.append(await self.store.get_stage_status(self.run_id, target))
        
        return unlocked
    
    async def _get_stage_inputs(self, stage: Stage) -> dict:
        """Get inputs for deterministic stage ID computation."""
        # Implementation depends on stage
        # Returns dict of inputs that affect the stage result
        return {"run_id": self.run_id, "stage": stage.value}
```

---

## Step 3.3: Implement Adapter Factory (ADR-0011) ✅

**Goal:** Create extensible adapter pattern for file formats

**File:** `src/dat_aggregation/adapters/factory.py`

> **Implementation Status:** Complete. Adapters for CSV, Excel, and Parquet implemented.

```python
"""Adapter factory for multi-format file parsing.

Per ADR-0011: Adapters are selected via handles-first registry.
"""
from pathlib import Path
from typing import Protocol

import polars as pl


class FileAdapter(Protocol):
    """Protocol for file adapters."""
    
    @staticmethod
    def can_handle(path: Path) -> bool:
        """Check if this adapter can handle the file."""
        ...
    
    @staticmethod
    def read(path: Path, **options) -> pl.DataFrame:
        """Read file and return DataFrame."""
        ...
    
    @staticmethod
    def get_tables(path: Path) -> list[str]:
        """Get list of tables/sheets in file."""
        ...


class CSVAdapter:
    """Adapter for CSV files."""
    
    EXTENSIONS = {".csv", ".tsv", ".txt"}
    
    @staticmethod
    def can_handle(path: Path) -> bool:
        return path.suffix.lower() in CSVAdapter.EXTENSIONS
    
    @staticmethod
    def read(path: Path, **options) -> pl.DataFrame:
        separator = options.get("separator", ",")
        if path.suffix.lower() == ".tsv":
            separator = "\t"
        return pl.read_csv(path, separator=separator)
    
    @staticmethod
    def get_tables(path: Path) -> list[str]:
        return [path.stem]


class ExcelAdapter:
    """Adapter for Excel files."""
    
    EXTENSIONS = {".xlsx", ".xls", ".xlsm"}
    
    @staticmethod
    def can_handle(path: Path) -> bool:
        return path.suffix.lower() in ExcelAdapter.EXTENSIONS
    
    @staticmethod
    def read(path: Path, **options) -> pl.DataFrame:
        sheet = options.get("sheet", 0)
        return pl.read_excel(path, sheet_name=sheet)
    
    @staticmethod
    def get_tables(path: Path) -> list[str]:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True)
        return wb.sheetnames


class ParquetAdapter:
    """Adapter for Parquet files."""
    
    EXTENSIONS = {".parquet", ".pq"}
    
    @staticmethod
    def can_handle(path: Path) -> bool:
        return path.suffix.lower() in ParquetAdapter.EXTENSIONS
    
    @staticmethod
    def read(path: Path, **options) -> pl.DataFrame:
        return pl.read_parquet(path)
    
    @staticmethod
    def get_tables(path: Path) -> list[str]:
        return [path.stem]


# Adapter registry
ADAPTERS: list[type[FileAdapter]] = [
    CSVAdapter,
    ExcelAdapter,
    ParquetAdapter,
]


class AdapterFactory:
    """Factory for selecting and using file adapters."""
    
    @classmethod
    def get_adapter(cls, path: Path) -> FileAdapter:
        """Get appropriate adapter for file."""
        for adapter in ADAPTERS:
            if adapter.can_handle(path):
                return adapter
        raise ValueError(f"No adapter found for: {path}")
    
    @classmethod
    def read_file(cls, path: Path, **options) -> pl.DataFrame:
        """Read file using appropriate adapter."""
        adapter = cls.get_adapter(path)
        return adapter.read(path, **options)
    
    @classmethod
    def get_tables(cls, path: Path) -> list[str]:
        """Get tables/sheets from file."""
        adapter = cls.get_adapter(path)
        return adapter.get_tables(path)
```

---

## Step 3.4: Implement Parse Stage ✅

**Goal:** Full data extraction with progress and cancellation

**File:** `src/dat_aggregation/stages/parse.py`

> **Implementation Status:** Complete. Parse stage with progress tracking implemented.

```python
"""Parse stage - full data extraction.

Per ADR-0013: Cancellation preserves completed work, no partial data.
Per ADR-0014: Output saved as Parquet.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import polars as pl

from dat_aggregation.adapters.factory import AdapterFactory
from shared.storage.artifact_store import ArtifactStore


@dataclass
class ParseConfig:
    """Configuration for parse stage."""
    selected_files: list[Path]
    selected_tables: dict[str, list[str]]  # file -> tables
    column_mappings: dict[str, str] | None = None


@dataclass
class ParseResult:
    """Result of parse stage."""
    data: pl.DataFrame
    row_count: int
    column_count: int
    source_files: list[str]
    completed: bool
    parse_id: str


class CancellationToken:
    """Token for checking cancellation status."""
    
    def __init__(self):
        self._cancelled = False
    
    def cancel(self):
        self._cancelled = True
    
    @property
    def is_cancelled(self) -> bool:
        return self._cancelled


async def execute_parse(
    run_id: str,
    config: ParseConfig,
    progress_callback: Callable[[float, str], None] | None = None,
    cancel_token: CancellationToken | None = None,
) -> ParseResult:
    """Execute full parse with progress and cancellation support.
    
    Per ADR-0013: If cancelled, only fully completed tables are kept.
    """
    all_dfs: list[pl.DataFrame] = []
    source_files: list[str] = []
    total_files = len(config.selected_files)
    
    for i, file_path in enumerate(config.selected_files):
        # Check cancellation before each file
        if cancel_token and cancel_token.is_cancelled:
            break
        
        if progress_callback:
            progress_callback(
                (i / total_files) * 100,
                f"Processing {file_path.name}..."
            )
        
        tables = config.selected_tables.get(str(file_path), [])
        
        for table in tables:
            if cancel_token and cancel_token.is_cancelled:
                break
            
            # Read table
            df = AdapterFactory.read_file(file_path, sheet=table)
            
            # Apply column mappings if provided
            if config.column_mappings:
                df = df.rename(config.column_mappings)
            
            all_dfs.append(df)
            source_files.append(f"{file_path.name}:{table}")
    
    # Combine all DataFrames
    if all_dfs:
        combined = pl.concat(all_dfs, how="diagonal")
    else:
        combined = pl.DataFrame()
    
    # Compute parse ID
    from shared.utils.stage_id import compute_stage_id
    parse_id = compute_stage_id({
        "run_id": run_id,
        "files": sorted(source_files),
        "row_count": len(combined),
    }, prefix="parse_")
    
    # Save to workspace
    store = ArtifactStore()
    workspace = store.workspace / "tools" / "dat" / "runs" / run_id
    workspace.mkdir(parents=True, exist_ok=True)
    
    output_path = workspace / f"{parse_id}.parquet"
    combined.write_parquet(output_path)
    
    if progress_callback:
        progress_callback(100, "Parse complete")
    
    return ParseResult(
        data=combined,
        row_count=len(combined),
        column_count=len(combined.columns),
        source_files=source_files,
        completed=not (cancel_token and cancel_token.is_cancelled),
        parse_id=parse_id,
    )
```

---

## Step 3.5: Implement Export Stage ✅

**Goal:** Export parsed data as DataSet with lineage

**File:** `src/dat_aggregation/stages/export.py`

> **Implementation Status:** Complete. Export stage implemented.

```python
"""Export stage - create DataSet from parsed data.

Per ADR-0014: Output as Parquet with JSON manifest.
"""
from datetime import datetime, timezone

import polars as pl

from shared.contracts.core.dataset import DataSetManifest, ColumnMeta
from shared.storage.artifact_store import ArtifactStore
from shared.utils.stage_id import compute_dataset_id


async def execute_export(
    run_id: str,
    parse_result: "ParseResult",
    aggregation_levels: list[str] | None = None,
    profile_id: str | None = None,
) -> DataSetManifest:
    """Export parsed data as a shareable DataSet.
    
    Args:
        run_id: DAT run ID
        parse_result: Result from parse stage
        aggregation_levels: Optional levels used for aggregation
        profile_id: Optional extraction profile ID
        
    Returns:
        DataSetManifest for the created DataSet
    """
    data = parse_result.data
    
    # Apply aggregation if levels specified
    if aggregation_levels:
        # Group by aggregation levels and compute summary stats
        agg_exprs = []
        for col in data.columns:
            if col not in aggregation_levels:
                if data[col].dtype in [pl.Float64, pl.Float32, pl.Int64, pl.Int32]:
                    agg_exprs.extend([
                        pl.col(col).mean().alias(f"{col}_mean"),
                        pl.col(col).std().alias(f"{col}_std"),
                        pl.col(col).count().alias(f"{col}_count"),
                    ])
        
        if agg_exprs:
            data = data.group_by(aggregation_levels).agg(agg_exprs)
    
    # Compute deterministic DataSet ID
    dataset_id = compute_dataset_id(
        run_id=run_id,
        columns=data.columns,
        row_count=len(data),
        aggregation_levels=aggregation_levels,
    )
    
    # Build manifest
    now = datetime.now(timezone.utc)
    manifest = DataSetManifest(
        dataset_id=dataset_id,
        name=f"DAT Export - {run_id[:8]}",
        created_at=now,
        created_by_tool="dat",
        columns=[
            ColumnMeta(
                name=col,
                dtype=str(data[col].dtype),
                nullable=data[col].null_count() > 0,
                source_tool="dat",
            )
            for col in data.columns
        ],
        row_count=len(data),
        aggregation_levels=aggregation_levels,
        source_files=parse_result.source_files,
        profile_id=profile_id,
    )
    
    # Write to shared storage
    store = ArtifactStore()
    await store.write_dataset(dataset_id, data, manifest)
    
    return manifest
```

---

## Step 3.6: Create DAT API Routes ✅

**Goal:** FastAPI routes for DAT operations

**File:** `src/dat_aggregation/api/routes.py`

> **Implementation Status:** Complete. API routes implemented and mounted in gateway.

```python
"""DAT API routes."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from dat_aggregation.core.state_machine import DATStateMachine, Stage
from dat_aggregation.core.run_manager import RunManager

router = APIRouter()
run_manager = RunManager()


class CreateRunRequest(BaseModel):
    name: str | None = None
    profile_id: str | None = None


class LockStageRequest(BaseModel):
    # Stage-specific config goes here
    pass


@router.post("/v1/runs")
async def create_run(request: CreateRunRequest):
    """Create a new DAT run."""
    run = await run_manager.create_run(
        name=request.name,
        profile_id=request.profile_id,
    )
    return run


@router.get("/v1/runs")
async def list_runs(limit: int = 50):
    """List DAT runs."""
    return await run_manager.list_runs(limit=limit)


@router.get("/v1/runs/{run_id}")
async def get_run(run_id: str):
    """Get DAT run details."""
    run = await run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/v1/runs/{run_id}/stages/{stage}")
async def get_stage_status(run_id: str, stage: str):
    """Get stage status."""
    try:
        stage_enum = Stage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
    
    sm = DATStateMachine(run_id, run_manager.store)
    status = await sm.store.get_stage_status(run_id, stage_enum)
    return status


@router.post("/v1/runs/{run_id}/stages/{stage}/lock")
async def lock_stage(run_id: str, stage: str, request: LockStageRequest):
    """Lock a stage."""
    try:
        stage_enum = Stage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
    
    sm = DATStateMachine(run_id, run_manager.store)
    
    try:
        status = await sm.lock_stage(stage_enum)
        return status
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/v1/runs/{run_id}/stages/{stage}/unlock")
async def unlock_stage(run_id: str, stage: str):
    """Unlock a stage (cascades to downstream)."""
    try:
        stage_enum = Stage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
    
    sm = DATStateMachine(run_id, run_manager.store)
    unlocked = await sm.unlock_stage(stage_enum)
    return {"unlocked": [s.stage.value for s in unlocked]}


@router.post("/v1/runs/{run_id}/export")
async def export_dataset(
    run_id: str,
    aggregation_levels: list[str] | None = None,
):
    """Export run as DataSet."""
    from dat_aggregation.stages.export import execute_export
    
    # Get parse result
    parse_result = await run_manager.get_parse_result(run_id)
    if not parse_result:
        raise HTTPException(status_code=400, detail="Parse not completed")
    
    manifest = await execute_export(
        run_id=run_id,
        parse_result=parse_result,
        aggregation_levels=aggregation_levels,
    )
    
    return manifest
```

---

## Validation Checklist

### Backend Implementation

- [x] State machine forward gating
- [x] State machine cascade unlock
- [x] Adapter factory file detection
- [x] CSV/Excel/Parquet adapters
- [x] All 7 stages implemented
- [x] API routes implemented
- [x] Gateway mount configured

### Unit Tests (pending)

- [ ] State machine tests
- [ ] Adapter tests
- [ ] Stage logic tests

### Integration Tests (pending)

- [ ] Full run: Selection → Parse → Export
- [ ] Unlock and re-lock (idempotent)
- [ ] Cancel during parse

### Frontend (pending)

- [ ] DAT frontend with stage panels
- [ ] Progress tracking UI
- [ ] "Pipe To" integration

---

## Next Phase

Proceed to **Phase 4: SOV Analyzer**

See: `phase-4-sov-analyzer/PHASE4_INSTRUCTIONS.md`
