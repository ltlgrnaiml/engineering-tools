# Tier 3: Implementation Details with Code Snippets

**Purpose**: Exact code to write for new files and modifications.

---

## Milestone 1: Unify Adapter Implementations

### M1-CODE-001: Update routes.py Imports

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

Find and replace ALL occurrences:

```python
# FIND
from ..adapters.factory import AdapterFactory

# REPLACE WITH
from apps.data_aggregator.backend.adapters.registry import AdapterRegistry
```

### M1-CODE-002: Update routes.py Usage

**Pattern 1**: `AdapterFactory.get_adapter(path)`

```python
# FIND
adapter = AdapterFactory.get_adapter(Path(file_path))

# REPLACE WITH
adapter = AdapterRegistry.get_adapter(Path(file_path))
```

**Pattern 2**: `AdapterFactory.get_tables(path)`

```python
# FIND
file_tables = AdapterFactory.get_tables(Path(file_path))

# REPLACE WITH
adapter = AdapterRegistry.get_adapter(Path(file_path))
file_tables = adapter.get_tables(Path(file_path))
```

**Pattern 3**: `AdapterFactory.get_preview(path, table=table, rows=n)`

```python
# FIND
preview_df = AdapterFactory.get_preview(Path(file_path), table=table, rows=1)

# REPLACE WITH
adapter = AdapterRegistry.get_adapter(Path(file_path))
preview_df = adapter.read(Path(file_path), table=table).head(1)
```

---

## Milestone 2: API Path Normalization

### M2-CODE-001: gateway/main.py

```python
# FIND (lines ~43-45)
app.include_router(dataset_router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(pipeline_router, prefix="/api/v1/pipelines", tags=["pipelines"])
app.include_router(devtools_router, prefix="/api/v1/devtools", tags=["devtools"])

# REPLACE WITH
app.include_router(dataset_router, prefix="/api/datasets", tags=["datasets"])
app.include_router(pipeline_router, prefix="/api/pipelines", tags=["pipelines"])
app.include_router(devtools_router, prefix="/api/devtools", tags=["devtools"])
```

### M2-CODE-002: gateway/services/pipeline_service.py

```python
# FIND
TOOL_BASE_URLS = {
    "dat": "http://localhost:8000/api/dat/v1",
    "sov": "http://localhost:8000/api/sov/v1",
    "pptx": "http://localhost:8000/api/pptx/v1",
}

# REPLACE WITH
TOOL_BASE_URLS = {
    "dat": "http://localhost:8000/api/dat",
    "sov": "http://localhost:8000/api/sov",
    "pptx": "http://localhost:8000/api/pptx",
}
```

### M2-CODE-003: DAT routes.py

```python
# FIND (line 39)
router = APIRouter(prefix="/v1")

# REPLACE WITH
router = APIRouter()
```

```python
# FIND (lines 1-5 docstring)
"""DAT API routes.

Per ADR-0030: All routes use versioned /v1/ prefix.

# REPLACE WITH
"""DAT API routes.

Per ADR-0030: All routes use /api/{tool}/{resource} pattern (no version prefix).
```

### M2-CODE-004: Frontend Files Global Replace

For ALL frontend files, use find-replace:

```typescript
// FIND
/api/dat/v1/

// REPLACE WITH
/api/dat/
```

```typescript
// FIND
/api/sov/v1/

// REPLACE WITH
/api/sov/
```

```typescript
// FIND
/api/pptx/v1/

// REPLACE WITH
/api/pptx/
```

---

## Milestone 3: Externalize Stage Graph Configuration

### M3-CODE-001: NEW FILE - stage_graph.py

**File**: `shared/contracts/dat/stage_graph.py`

```python
"""Stage graph configuration contract.

Per ADR-0004: 8-stage pipeline with lockable artifacts.
Per SPEC-0024: Dependencies and cascade targets defined.
"""

from typing import FrozenSet

from pydantic import BaseModel, Field

from .stage import DATStageType

__version__ = "1.0.0"


class StageDefinition(BaseModel):
    """Definition of a single stage in the pipeline."""

    stage_type: DATStageType
    is_optional: bool = False
    description: str = ""


class GatingRule(BaseModel):
    """Forward gating rule for stage progression."""

    target_stage: DATStageType
    required_stages: list[DATStageType]
    require_completion: bool = False


class CascadeRule(BaseModel):
    """Cascade unlock rule when a stage is unlocked."""

    trigger_stage: DATStageType
    cascade_targets: list[DATStageType]


class StageGraphConfig(BaseModel):
    """Complete stage graph configuration.

    Single source of truth for DAT pipeline structure.
    Per ADR-0004 and SPEC-0024.
    """

    stages: list[StageDefinition]
    gating_rules: list[GatingRule]
    cascade_rules: list[CascadeRule]
    optional_stages: FrozenSet[DATStageType] = frozenset({
        DATStageType.CONTEXT,
        DATStageType.PREVIEW,
    })

    @classmethod
    def default(cls) -> "StageGraphConfig":
        """Return the default DAT 8-stage pipeline configuration.

        Returns:
            StageGraphConfig: Default configuration per ADR-0004.
        """
        return cls(
            stages=[
                StageDefinition(
                    stage_type=DATStageType.DISCOVERY,
                    description="Scan filesystem for data files",
                ),
                StageDefinition(
                    stage_type=DATStageType.SELECTION,
                    description="Select files to process",
                ),
                StageDefinition(
                    stage_type=DATStageType.CONTEXT,
                    is_optional=True,
                    description="Set profile and aggregation context",
                ),
                StageDefinition(
                    stage_type=DATStageType.TABLE_AVAILABILITY,
                    description="Detect available tables in selected files",
                ),
                StageDefinition(
                    stage_type=DATStageType.TABLE_SELECTION,
                    description="Select tables to extract",
                ),
                StageDefinition(
                    stage_type=DATStageType.PREVIEW,
                    is_optional=True,
                    description="Preview data before parsing",
                ),
                StageDefinition(
                    stage_type=DATStageType.PARSE,
                    description="Extract and transform data",
                ),
                StageDefinition(
                    stage_type=DATStageType.EXPORT,
                    description="Export data as DataSet",
                ),
            ],
            gating_rules=[
                GatingRule(
                    target_stage=DATStageType.SELECTION,
                    required_stages=[DATStageType.DISCOVERY],
                ),
                GatingRule(
                    target_stage=DATStageType.CONTEXT,
                    required_stages=[DATStageType.SELECTION],
                ),
                GatingRule(
                    target_stage=DATStageType.TABLE_AVAILABILITY,
                    required_stages=[DATStageType.SELECTION],
                ),
                GatingRule(
                    target_stage=DATStageType.TABLE_SELECTION,
                    required_stages=[DATStageType.TABLE_AVAILABILITY],
                ),
                GatingRule(
                    target_stage=DATStageType.PREVIEW,
                    required_stages=[DATStageType.TABLE_SELECTION],
                ),
                GatingRule(
                    target_stage=DATStageType.PARSE,
                    required_stages=[DATStageType.TABLE_SELECTION],
                ),
                GatingRule(
                    target_stage=DATStageType.EXPORT,
                    required_stages=[DATStageType.PARSE],
                    require_completion=True,
                ),
            ],
            cascade_rules=[
                CascadeRule(
                    trigger_stage=DATStageType.DISCOVERY,
                    cascade_targets=[
                        DATStageType.SELECTION,
                        DATStageType.CONTEXT,
                        DATStageType.TABLE_AVAILABILITY,
                        DATStageType.TABLE_SELECTION,
                        DATStageType.PREVIEW,
                        DATStageType.PARSE,
                        DATStageType.EXPORT,
                    ],
                ),
                CascadeRule(
                    trigger_stage=DATStageType.SELECTION,
                    cascade_targets=[
                        DATStageType.CONTEXT,
                        DATStageType.TABLE_AVAILABILITY,
                        DATStageType.TABLE_SELECTION,
                        DATStageType.PREVIEW,
                        DATStageType.PARSE,
                        DATStageType.EXPORT,
                    ],
                ),
                CascadeRule(
                    trigger_stage=DATStageType.TABLE_AVAILABILITY,
                    cascade_targets=[
                        DATStageType.TABLE_SELECTION,
                        DATStageType.PREVIEW,
                        DATStageType.PARSE,
                        DATStageType.EXPORT,
                    ],
                ),
                CascadeRule(
                    trigger_stage=DATStageType.TABLE_SELECTION,
                    cascade_targets=[
                        DATStageType.PREVIEW,
                        DATStageType.PARSE,
                        DATStageType.EXPORT,
                    ],
                ),
                CascadeRule(
                    trigger_stage=DATStageType.PARSE,
                    cascade_targets=[DATStageType.EXPORT],
                ),
                # Context and Preview do NOT cascade (per ADR-0004)
                CascadeRule(
                    trigger_stage=DATStageType.CONTEXT,
                    cascade_targets=[],
                ),
                CascadeRule(
                    trigger_stage=DATStageType.PREVIEW,
                    cascade_targets=[],
                ),
            ],
        )

    class Config:
        """Pydantic config."""

        frozen = True
```

### M3-CODE-002: Update __init__.py

**File**: `shared/contracts/dat/__init__.py`

Add to imports section (after existing imports):

```python
from shared.contracts.dat.stage_graph import (
    CascadeRule,
    GatingRule,
    StageDefinition,
    StageGraphConfig,
)
```

Add to `__all__` list:

```python
    # Stage graph contracts (per ADR-0004)
    "CascadeRule",
    "GatingRule",
    "StageDefinition",
    "StageGraphConfig",
```

### M3-CODE-003: Update state_machine.py

**File**: `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py`

**DELETE** lines 40-71 (the FORWARD_GATES and CASCADE_TARGETS dicts)

**REPLACE** class definition:

```python
# FIND
class DATStateMachine:
    """Hybrid FSM for DAT stage orchestration."""

    def __init__(self, run_id: str, store: "RunStore"):
        self.run_id = run_id
        self.store = store

# REPLACE WITH
from shared.contracts.dat.stage_graph import StageGraphConfig


class DATStateMachine:
    """Hybrid FSM for DAT stage orchestration.

    Per ADR-0004: Config-driven stage graph.
    """

    def __init__(
        self,
        run_id: str,
        store: "RunStore",
        config: StageGraphConfig | None = None,
    ):
        """Initialize the state machine.

        Args:
            run_id: Unique run identifier.
            store: Run store for persistence.
            config: Stage graph configuration. Defaults to standard 8-stage pipeline.
        """
        self.run_id = run_id
        self.store = store
        self.config = config or StageGraphConfig.default()
        self._build_lookup_tables()

    def _build_lookup_tables(self) -> None:
        """Build fast lookup dicts from config."""
        self._forward_gates: dict[Stage, list[tuple[Stage, bool]]] = {}
        for rule in self.config.gating_rules:
            self._forward_gates[rule.target_stage] = [
                (s, rule.require_completion) for s in rule.required_stages
            ]

        self._cascade_targets: dict[Stage, list[Stage]] = {}
        for rule in self.config.cascade_rules:
            self._cascade_targets[rule.trigger_stage] = list(rule.cascade_targets)
```

**UPDATE** `can_lock` method to use instance variables:

```python
# FIND
gates = FORWARD_GATES.get(stage, [])

# REPLACE WITH
gates = self._forward_gates.get(stage, [])
```

**UPDATE** `unlock_stage` method to use instance variables:

```python
# FIND
for target in CASCADE_TARGETS.get(stage, []):

# REPLACE WITH
for target in self._cascade_targets.get(stage, []):
```

---

## Milestone 4: Align Stage ID Generation

### M4-CODE-001: Update stage_id.py

**File**: `shared/utils/stage_id.py`

```python
# FIND (line ~44)
hash_digest = hashlib.sha256(serialized.encode()).hexdigest()[:16]

# REPLACE WITH
hash_digest = hashlib.sha256(serialized.encode()).hexdigest()[:8]
```

### M4-CODE-002: Update routes.py Discovery Inputs

**File**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`

```python
# FIND (around line 234)
inputs = {"root_path": str(source_path)}

# REPLACE WITH
from shared.contracts.core.path_safety import to_relative_path

# Get workspace root from run or default
workspace_root = Path(run.get("workspace", source_path.parent))
inputs = {"root_path": to_relative_path(source_path, workspace_root)}
```

---

## Milestone 5: Table Availability Fast Probe

### M5-CODE-001: NEW FILE - table_probe.py

**File**: `apps/data_aggregator/backend/services/table_probe.py`

```python
"""Fast table probing service.

Per ADR-0008: Probe must complete in <1s per table.
Per SPEC-0008: Use adapter.probe_schema(), not full reads.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from shared.contracts.dat.table_status import (
    TableAvailability,
    TableAvailabilityStatus,
)

if TYPE_CHECKING:
    from shared.contracts.dat.adapter import BaseFileAdapter

__version__ = "1.0.0"

PROBE_TIMEOUT_SECONDS = 1.0


async def probe_table(
    adapter: "BaseFileAdapter",
    file_path: str | Path,
    table_name: str | None = None,
) -> TableAvailability:
    """Probe a single table for availability status.

    Per ADR-0008: Fast probe without loading full data.

    Args:
        adapter: File adapter instance.
        file_path: Path to the file.
        table_name: Optional table/sheet name.

    Returns:
        TableAvailability: Status of the table.
    """
    file_path = Path(file_path) if isinstance(file_path, str) else file_path
    table_id = f"{file_path}::{table_name}" if table_name else str(file_path)

    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(adapter.probe_schema, file_path, table_name),
            timeout=PROBE_TIMEOUT_SECONDS,
        )

        if result.row_count == 0:
            status = TableAvailabilityStatus.EMPTY
        elif result.error:
            status = TableAvailabilityStatus.PARTIAL
        else:
            status = TableAvailabilityStatus.AVAILABLE

        return TableAvailability(
            table_id=table_id,
            status=status,
            column_count=len(result.columns) if result.columns else 0,
            row_estimate=result.row_count,
            probed_at=datetime.now(timezone.utc),
        )

    except asyncio.TimeoutError:
        return TableAvailability(
            table_id=table_id,
            status=TableAvailabilityStatus.ERROR,
            error_message="Probe timeout exceeded",
            probed_at=datetime.now(timezone.utc),
        )

    except FileNotFoundError:
        return TableAvailability(
            table_id=table_id,
            status=TableAvailabilityStatus.MISSING,
            probed_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        return TableAvailability(
            table_id=table_id,
            status=TableAvailabilityStatus.ERROR,
            error_message=str(e),
            probed_at=datetime.now(timezone.utc),
        )


async def probe_tables_batch(
    adapter: "BaseFileAdapter",
    file_path: str | Path,
    table_names: list[str],
) -> list[TableAvailability]:
    """Probe multiple tables in parallel.

    Args:
        adapter: File adapter instance.
        file_path: Path to the file.
        table_names: List of table/sheet names.

    Returns:
        List of TableAvailability results.
    """
    tasks = [
        probe_table(adapter, file_path, table_name)
        for table_name in table_names
    ]
    return await asyncio.gather(*tasks)
```

---

## Milestone 6: Large File Streaming

### M6-CODE-001: Update parse.py

**File**: `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py`

Add constant at module level:

```python
STREAMING_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10MB per ADR-0041
```

Update parse execution logic:

```python
async def execute_parse(
    run_id: str,
    config: ParseConfig,
    workspace_path: Path,
    cancel_token: CancellationToken | None = None,
) -> ParseResult:
    """Execute parse stage with streaming for large files.

    Per ADR-0041: Files >10MB use streaming.
    """
    all_data = []

    for file_path in config.selected_files:
        adapter = AdapterRegistry.get_adapter(file_path)
        file_size = file_path.stat().st_size

        if file_size > STREAMING_THRESHOLD_BYTES:
            # Use streaming for large files
            async for chunk in adapter.stream_dataframe(
                file_path,
                chunk_size=50000,
                table=config.selected_tables.get(str(file_path)),
            ):
                if cancel_token and cancel_token.is_cancelled:
                    break
                all_data.append(chunk)
        else:
            # Eager load for small files
            df = adapter.read_dataframe(file_path)
            all_data.append(df)

    # Combine and return
    combined = pl.concat(all_data) if all_data else pl.DataFrame()
    # ... rest of implementation
```

---

## Milestone 7: Parse/Export Artifact Formats

### M7-CODE-001: Enforce Parquet in parse.py

```python
# Add constant
OUTPUT_FORMAT = "parquet"  # Enforced per ADR-0015


async def save_parse_output(df: pl.DataFrame, output_dir: Path, parse_id: str) -> Path:
    """Save parse output as Parquet.

    Per ADR-0015: Parse always outputs Parquet.

    Args:
        df: DataFrame to save.
        output_dir: Output directory.
        parse_id: Parse stage ID.

    Returns:
        Path to saved file.
    """
    output_path = output_dir / f"{parse_id}.parquet"
    df.write_parquet(output_path)
    return output_path
```

### M7-CODE-002: Multi-format export.py

```python
SUPPORTED_EXPORT_FORMATS = {"parquet", "csv", "excel", "json"}


async def execute_export(
    run_id: str,
    parse_result: ParseResult,
    name: str,
    format: str = "parquet",
    **options,
) -> DataSetManifest:
    """Export data in specified format.

    Per ADR-0015: Export supports multiple formats.

    Args:
        run_id: Run identifier.
        parse_result: Parse stage result.
        name: DataSet name.
        format: Output format (parquet, csv, excel, json).
        **options: Format-specific options.

    Returns:
        DataSetManifest for the exported data.

    Raises:
        ValueError: If format is not supported.
    """
    if format not in SUPPORTED_EXPORT_FORMATS:
        raise ValueError(
            f"Unsupported format: {format}. "
            f"Supported: {SUPPORTED_EXPORT_FORMATS}"
        )

    df = parse_result.data

    if format == "parquet":
        output_path = output_dir / f"{name}.parquet"
        df.write_parquet(output_path, **options)
    elif format == "csv":
        output_path = output_dir / f"{name}.csv"
        df.write_csv(output_path, **options)
    elif format == "excel":
        output_path = output_dir / f"{name}.xlsx"
        df.write_excel(output_path, **options)
    elif format == "json":
        output_path = output_dir / f"{name}.json"
        df.write_json(output_path, **options)

    # Create manifest...
```

---

## Milestone 8: Cancellation Checkpointing

### M8-CODE-001: NEW FILE - checkpoint.py

**File**: `apps/data_aggregator/backend/services/checkpoint.py`

```python
"""Checkpoint registry for cancellation safety.

Per ADR-0014: Checkpoints are safe points where data integrity is guaranteed.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from shared.contracts.dat.cancellation import CheckpointType

__version__ = "1.0.0"


@dataclass
class Checkpoint:
    """A checkpoint marking a safe point in processing."""

    checkpoint_type: CheckpointType
    artifact_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)


class CheckpointRegistry:
    """Registry for tracking checkpoints during processing.

    Per ADR-0014: Track safe points for cancellation recovery.
    """

    def __init__(self, run_id: str):
        """Initialize checkpoint registry.

        Args:
            run_id: Run identifier.
        """
        self.run_id = run_id
        self._checkpoints: list[Checkpoint] = []

    def mark_checkpoint(
        self,
        checkpoint_type: CheckpointType,
        artifact_id: str,
        metadata: dict | None = None,
    ) -> Checkpoint:
        """Mark a safe checkpoint.

        Args:
            checkpoint_type: Type of checkpoint.
            artifact_id: ID of the artifact at this checkpoint.
            metadata: Optional additional metadata.

        Returns:
            The created Checkpoint.
        """
        checkpoint = Checkpoint(
            checkpoint_type=checkpoint_type,
            artifact_id=artifact_id,
            metadata=metadata or {},
        )
        self._checkpoints.append(checkpoint)
        return checkpoint

    def get_last_safe_point(self) -> Checkpoint | None:
        """Get the last safe checkpoint for rollback.

        Returns:
            Last checkpoint or None if no checkpoints exist.
        """
        return self._checkpoints[-1] if self._checkpoints else None

    def get_all_checkpoints(self) -> list[Checkpoint]:
        """Get all checkpoints.

        Returns:
            List of all checkpoints.
        """
        return list(self._checkpoints)

    def clear(self) -> None:
        """Clear all checkpoints."""
        self._checkpoints.clear()
```

### M8-CODE-002: NEW FILE - cleanup.py

**File**: `apps/data_aggregator/backend/services/cleanup.py`

```python
"""Explicit cleanup service.

Per ADR-0014: Cleanup is user-initiated only, dry-run by default.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from shared.contracts.dat.cancellation import CleanupTarget, CleanupResult

__version__ = "1.0.0"


@dataclass
class CleanupAction:
    """A single cleanup action."""

    target: CleanupTarget
    action: Literal["delete", "archive", "skip"]
    path: Path | None
    reason: str


async def cleanup(
    run_id: str,
    targets: list[CleanupTarget],
    dry_run: bool = True,
    archive_dir: Path | None = None,
) -> CleanupResult:
    """Clean up partial artifacts from cancelled runs.

    Per ADR-0014: Dry-run by default, explicit cleanup only.

    Args:
        run_id: Run identifier.
        targets: List of cleanup targets.
        dry_run: If True, only report what would be cleaned (default: True).
        archive_dir: Optional directory to archive instead of delete.

    Returns:
        CleanupResult with details of cleanup actions.
    """
    actions: list[CleanupAction] = []
    deleted_count = 0
    archived_count = 0
    skipped_count = 0

    for target in targets:
        # Determine action based on target type
        if target.is_checkpoint_safe:
            actions.append(CleanupAction(
                target=target,
                action="skip",
                path=None,
                reason="Checkpoint-safe artifact preserved",
            ))
            skipped_count += 1
            continue

        target_path = Path(target.path) if target.path else None

        if not target_path or not target_path.exists():
            actions.append(CleanupAction(
                target=target,
                action="skip",
                path=target_path,
                reason="Path does not exist",
            ))
            skipped_count += 1
            continue

        if dry_run:
            action_type = "archive" if archive_dir else "delete"
            actions.append(CleanupAction(
                target=target,
                action=action_type,
                path=target_path,
                reason=f"Would {action_type} (dry-run)",
            ))
        else:
            if archive_dir:
                # Move to archive
                archive_path = archive_dir / target_path.name
                target_path.rename(archive_path)
                actions.append(CleanupAction(
                    target=target,
                    action="archive",
                    path=archive_path,
                    reason="Archived",
                ))
                archived_count += 1
            else:
                # Delete
                if target_path.is_file():
                    target_path.unlink()
                else:
                    import shutil
                    shutil.rmtree(target_path)
                actions.append(CleanupAction(
                    target=target,
                    action="delete",
                    path=target_path,
                    reason="Deleted",
                ))
                deleted_count += 1

    return CleanupResult(
        run_id=run_id,
        dry_run=dry_run,
        deleted_count=deleted_count,
        archived_count=archived_count,
        skipped_count=skipped_count,
        actions=[a.__dict__ for a in actions],
        completed_at=datetime.now(timezone.utc),
    )
```

---

## Milestone 9: Profile CRUD

### M9-CODE-001: NEW FILE - profile_service.py

**File**: `apps/data_aggregator/backend/services/profile_service.py`

```python
"""Profile CRUD service.

Per SPEC-0007: Profile management with deterministic IDs.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json

from shared.contracts.dat.profile import (
    ExtractionProfile,
    CreateProfileRequest,
    UpdateProfileRequest,
)
from shared.utils.stage_id import compute_stage_id

__version__ = "1.0.0"

# Default profile storage directory
PROFILES_DIR = Path("data/profiles")


class ProfileService:
    """Service for managing extraction profiles.

    Per ADR-0012: Profile-driven extraction.
    Per ADR-0005: Deterministic IDs.
    """

    def __init__(self, profiles_dir: Path | None = None):
        """Initialize profile service.

        Args:
            profiles_dir: Directory for profile storage.
        """
        self.profiles_dir = profiles_dir or PROFILES_DIR
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def _compute_profile_id(self, profile: ExtractionProfile) -> str:
        """Compute deterministic profile ID.

        Per ADR-0005: SHA-256 based IDs.
        """
        inputs = {
            "name": profile.name,
            "file_patterns": [p.model_dump() for p in profile.file_patterns],
            "column_mappings": [m.model_dump() for m in profile.column_mappings],
        }
        return compute_stage_id(inputs, prefix="profile_")

    def _get_profile_path(self, profile_id: str) -> Path:
        """Get path to profile JSON file."""
        return self.profiles_dir / f"{profile_id}.json"

    async def create(self, request: CreateProfileRequest) -> ExtractionProfile:
        """Create a new profile.

        Args:
            request: Profile creation request.

        Returns:
            Created ExtractionProfile.

        Raises:
            ValueError: If profile with same ID already exists.
        """
        profile = ExtractionProfile(
            name=request.name,
            description=request.description,
            file_patterns=request.file_patterns,
            column_mappings=request.column_mappings,
            aggregation_rules=request.aggregation_rules,
            validation_rules=request.validation_rules,
            created_at=datetime.now(timezone.utc),
        )

        profile_id = self._compute_profile_id(profile)
        profile_path = self._get_profile_path(profile_id)

        if profile_path.exists():
            raise ValueError(f"Profile already exists: {profile_id}")

        # Add ID to profile
        profile_dict = profile.model_dump()
        profile_dict["profile_id"] = profile_id

        profile_path.write_text(json.dumps(profile_dict, default=str, indent=2))

        return ExtractionProfile(**profile_dict)

    async def get(self, profile_id: str) -> ExtractionProfile | None:
        """Get a profile by ID.

        Args:
            profile_id: Profile identifier.

        Returns:
            ExtractionProfile or None if not found.
        """
        profile_path = self._get_profile_path(profile_id)

        if not profile_path.exists():
            return None

        data = json.loads(profile_path.read_text())
        return ExtractionProfile(**data)

    async def update(
        self,
        profile_id: str,
        request: UpdateProfileRequest,
    ) -> ExtractionProfile | None:
        """Update an existing profile.

        Args:
            profile_id: Profile identifier.
            request: Update request.

        Returns:
            Updated ExtractionProfile or None if not found.
        """
        existing = await self.get(profile_id)
        if not existing:
            return None

        # Apply updates
        update_data = request.model_dump(exclude_unset=True)
        profile_dict = existing.model_dump()
        profile_dict.update(update_data)
        profile_dict["updated_at"] = datetime.now(timezone.utc)

        profile_path = self._get_profile_path(profile_id)
        profile_path.write_text(json.dumps(profile_dict, default=str, indent=2))

        return ExtractionProfile(**profile_dict)

    async def delete(self, profile_id: str) -> bool:
        """Delete a profile.

        Args:
            profile_id: Profile identifier.

        Returns:
            True if deleted, False if not found.
        """
        profile_path = self._get_profile_path(profile_id)

        if not profile_path.exists():
            return False

        profile_path.unlink()
        return True

    async def list_all(self) -> list[ExtractionProfile]:
        """List all profiles.

        Returns:
            List of all profiles.
        """
        profiles = []
        for profile_path in self.profiles_dir.glob("*.json"):
            data = json.loads(profile_path.read_text())
            profiles.append(ExtractionProfile(**data))
        return profiles
```

### M9-CODE-002: Add CRUD Endpoints to routes.py

```python
# Add to routes.py

from apps.data_aggregator.backend.services.profile_service import ProfileService
from shared.contracts.dat.profile import (
    CreateProfileRequest,
    UpdateProfileRequest,
    ExtractionProfile,
)

profile_service = ProfileService()


@router.post("/profiles", response_model=ExtractionProfile)
async def create_profile(request: CreateProfileRequest):
    """Create a new extraction profile."""
    try:
        return await profile_service.create(request)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/profiles/{profile_id}", response_model=ExtractionProfile)
async def get_profile(profile_id: str):
    """Get a profile by ID."""
    profile = await profile_service.get(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/profiles/{profile_id}", response_model=ExtractionProfile)
async def update_profile(profile_id: str, request: UpdateProfileRequest):
    """Update an existing profile."""
    profile = await profile_service.update(profile_id, request)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete a profile."""
    deleted = await profile_service.delete(profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "deleted", "profile_id": profile_id}
```

---

*Next: Read `04_EXECUTION_CHECKLIST.md`*
