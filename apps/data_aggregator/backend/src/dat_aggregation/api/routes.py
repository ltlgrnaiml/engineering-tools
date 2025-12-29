"""DAT API routes.

Per ADR-0029: All routes use /api/{tool}/{resource} pattern (no version prefix).
Per ADR-0013: Cancellation events are logged for audit.
"""
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks

from shared.contracts.dat.cancellation import (
    CancellationAuditLog,
    CleanupTarget,
)
from shared.contracts.dat.profile import (
    CreateProfileRequest,
    UpdateProfileRequest,
)
from apps.data_aggregator.backend.services.cleanup import cleanup
from apps.data_aggregator.backend.services.profile_service import ProfileService
from shared.contracts.core.path_safety import make_relative
from shared.contracts.core.error_response import (
    ErrorCategory,
    create_error_response,
)
from ..core.state_machine import Stage, StageState, StageStatus
from ..core.run_manager import RunManager
from ..stages.selection import execute_selection
from ..stages.parse import execute_parse, ParseConfig, CancellationToken
from ..stages.export import execute_export
from .schemas import (
    CreateRunRequest,
    CreateRunResponse,
    RunResponse,
    StageStatusResponse,
    ScanRequest,
    SelectionRequest,
    SelectionResponse,
    FileInfoResponse,
    TableSelectionRequest,
    ParseRequest,
    ExportRequest,
    PreviewResponse,
)

# Per ADR-0029: Tool-specific routes use no version prefix (mounted at /api/dat by gateway)
router = APIRouter()
run_manager = RunManager()
profile_service = ProfileService()

# Track active cancellation tokens
_cancel_tokens: dict[str, CancellationToken] = {}


def _raise_error(
    status_code: int,
    message: str,
    category: ErrorCategory = ErrorCategory.VALIDATION,
    details: list | None = None,
) -> None:
    """Raise HTTPException with standardized ErrorResponse per API-003.

    Args:
        status_code: HTTP status code.
        message: Error message.
        category: Error category.
        details: Optional additional details.
    """
    error = create_error_response(
        status_code=status_code,
        message=message,
        category=category,
        details=details,
        tool="dat",
    )
    raise HTTPException(
        status_code=status_code,
        detail=error.model_dump(mode="json"),
    )


@router.post("/runs", response_model=CreateRunResponse)
async def create_run(request: CreateRunRequest):
    """Create a new DAT run."""
    run = await run_manager.create_run(
        name=request.name,
        profile_id=request.profile_id,
    )
    return CreateRunResponse(
        run_id=run["run_id"],
        name=run["name"],
        created_at=run["created_at"],
        profile_id=run.get("profile_id"),
    )


@router.get("/runs")
async def list_runs(limit: int = 50):
    """List DAT runs."""
    runs = await run_manager.list_runs(limit=limit)
    return runs


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get DAT run details."""
    run = await run_manager.get_run(run_id)
    if not run:
        _raise_error(
            status_code=404,
            message=f"Run not found: {run_id}",
            category=ErrorCategory.NOT_FOUND,
        )

    # Get all stage statuses
    sm = run_manager.get_state_machine(run_id)
    statuses = await sm.get_all_statuses()

    stages = {}
    for stage, status in statuses.items():
        stages[stage.value] = StageStatusResponse(
            stage=status.stage.value,
            state=status.state.value,
            stage_id=status.stage_id,
            locked_at=status.locked_at,
            unlocked_at=status.unlocked_at,
            completed=status.completed,
            error=status.error,
        )

    # Determine current stage based on progression
    stage_order = [Stage.SELECTION, Stage.CONTEXT, Stage.TABLE_AVAILABILITY, Stage.TABLE_SELECTION, Stage.PREVIEW, Stage.PARSE, Stage.EXPORT]
    current_stage = Stage.SELECTION  # default

    for stage in stage_order:
        stage_status = statuses.get(stage)
        if stage_status and stage_status.state == StageState.LOCKED and stage_status.completed:
            # This stage is complete, check if next stage exists
            current_index = stage_order.index(stage)
            if current_index + 1 < len(stage_order):
                current_stage = stage_order[current_index + 1]
            else:
                current_stage = stage  # Stay on final stage
        elif stage_status and stage_status.state == StageState.LOCKED and not stage_status.completed:
            # This stage is locked but not completed, stay here
            current_stage = stage
            break
        elif stage_status and stage_status.state == StageState.UNLOCKED:
            # This is the first unlocked stage, current stage
            current_stage = stage
            break

    return RunResponse(
        run_id=run["run_id"],
        name=run["name"],
        created_at=run["created_at"],
        profile_id=run.get("profile_id"),
        current_stage=current_stage.value,
        stages=stages,
    )


@router.get("/runs/{run_id}/stages/{stage}")
async def get_stage_status(run_id: str, stage: str):
    """Get stage status."""
    try:
        stage_enum = Stage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    sm = run_manager.get_state_machine(run_id)
    status = await sm.store.get_stage_status(run_id, stage_enum)

    return StageStatusResponse(
        stage=status.stage.value,
        state=status.state.value,
        stage_id=status.stage_id,
        locked_at=status.locked_at,
        unlocked_at=status.unlocked_at,
        completed=status.completed,
        error=status.error,
    )


@router.post("/runs/{run_id}/stages/discovery/lock")
async def lock_discovery(run_id: str, request: ScanRequest):
    """Lock discovery stage - scan for files in a folder.
    
    Per ADR-0001-DAT: Discovery is the first stage and must be locked before Selection.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Verify run exists
    run = await run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    sm = run_manager.get_state_machine(run_id)

    # Handle both Windows and Unix paths
    folder_path = request.folder_path.strip().replace('\\', '/')
    source_path = Path(folder_path)

    if not source_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Path does not exist: {folder_path}"
        )

    if not source_path.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Path is not a directory: {folder_path}"
        )

    # Discover files
    from ..stages.discovery import execute_discovery
    from ..stages.discovery import DiscoveryConfig

    try:
        config = DiscoveryConfig(root_path=source_path)

        async def execute():
            result = await execute_discovery(run_id, config)
            return {
                "discovery_id": result.discovery_id,
                "root_path": result.root_path,
                "files": [
                    {
                        "path": str(f.path),
                        "name": f.name,
                        "extension": f.extension,
                        "size_bytes": f.size_bytes,
                    }
                    for f in result.files
                ],
                "total_files": result.total_files,
                "supported_files": result.supported_files,
                "completed": result.completed,
            }

        # Per ADR-0004-DAT: Use relative paths for deterministic IDs
        workspace_root = Path(run.get("workspace", source_path.parent))
        inputs = {"root_path": make_relative(source_path, workspace_root).path}
        status = await sm.lock_stage(Stage.DISCOVERY, inputs=inputs, execute_fn=execute)

        artifact = await sm.store.get_artifact(run_id, Stage.DISCOVERY, status.stage_id)
        return {
            "discovery_id": artifact.get("discovery_id"),
            "root_path": artifact.get("root_path"),
            "files": artifact.get("files", []),
            "total_files": artifact.get("total_files", 0),
            "supported_files": artifact.get("supported_files", 0),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error locking discovery: {e}")
        raise HTTPException(status_code=400, detail=f"Error scanning directory: {str(e)}")


@router.post("/runs/{run_id}/stages/selection/scan")
async def scan_selection(run_id: str, request: ScanRequest):
    """Scan folder for files without locking stage."""
    import logging
    logger = logging.getLogger(__name__)

    # Verify run exists
    run = await run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Handle both Windows and Unix paths
    # Normalize path: convert backslashes to forward slashes for consistent handling
    folder_path = request.folder_path.strip().replace('\\', '/')
    logger.info(f"Scanning path: {folder_path}")

    source_path = Path(folder_path)
    logger.info(f"Resolved path: {source_path}")
    logger.info(f"Path exists: {source_path.exists()}")
    logger.info(f"Is directory: {source_path.is_dir()}")

    if not source_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Path does not exist: {folder_path} (resolved to: {source_path})"
        )

    if not source_path.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Path is not a directory: {folder_path}"
        )

    # Discover files
    from ..stages.selection import discover_files
    try:
        discovered = await discover_files([source_path], recursive=request.recursive)
        logger.info(f"Discovered {len(discovered)} files")
    except Exception as e:
        logger.error(f"Error discovering files: {e}")
        raise HTTPException(status_code=400, detail=f"Error scanning directory: {str(e)}")

    # Return list of file paths for frontend
    files = [str(f.path) for f in discovered]
    return {"files": files, "count": len(files)}


@router.post("/runs/{run_id}/stages/selection/lock")
async def lock_selection(run_id: str, request: SelectionRequest):
    """Lock selection stage - finalize file selection."""
    import logging
    logger = logging.getLogger(__name__)

    # Verify run exists
    run = await run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    sm = run_manager.get_state_machine(run_id)

    # Normalize paths (handle Windows backslashes)
    normalized_files = [p.replace('\\', '/') for p in request.selected_files]
    logger.info(f"Locking selection with {len(normalized_files)} files")

    # Validate files exist
    selected = []
    for p in normalized_files:
        path = Path(p)
        if not path.exists():
            logger.warning(f"File does not exist: {p}")
        selected.append(path)

    if request.source_paths:
        source_paths = [Path(p.replace('\\', '/')) for p in request.source_paths]
    else:
        # Derive source paths from selected files (use parent directories)
        source_paths = list(set(p.parent for p in selected))

    async def execute():
        result = await execute_selection(source_paths, selected, request.recursive)
        return {
            "discovered_files": [
                {
                    "path": str(f.path),
                    "name": f.name,
                    "extension": f.extension,
                    "size_bytes": f.size_bytes,
                    "tables": f.tables,
                }
                for f in result.discovered_files
            ],
            "selected_files": [str(p) for p in result.selected_files],
            "completed": result.completed,
        }

    try:
        inputs = {"source_paths": request.source_paths, "recursive": request.recursive}
        status = await sm.lock_stage(Stage.SELECTION, inputs=inputs, execute_fn=execute)

        # Get artifact for response
        artifact = await sm.store.get_artifact(run_id, Stage.SELECTION, status.stage_id)

        return SelectionResponse(
            discovered_files=[FileInfoResponse(**f) for f in artifact.get("discovered_files", [])],
            selected_files=artifact.get("selected_files", []),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/stages/context/lock")
async def lock_context(run_id: str, request: dict | None = None):
    """Lock context stage - set profile and aggregation levels."""
    import logging
    logger = logging.getLogger(__name__)

    run = await run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    sm = run_manager.get_state_machine(run_id)

    # Context is optional, just store the settings
    request_data = request if request else {}
    profile_id = request_data.get("profile_id") if isinstance(request_data, dict) else None
    aggregation_levels = request_data.get("aggregation_levels", []) if isinstance(request_data, dict) else []

    logger.info(f"Locking context: profile={profile_id}, levels={aggregation_levels}")

    async def execute():
        return {
            "profile_id": profile_id,
            "aggregation_levels": aggregation_levels,
            "completed": True,
        }

    try:
        inputs = {"profile_id": profile_id, "aggregation_levels": aggregation_levels}
        status = await sm.lock_stage(Stage.CONTEXT, inputs=inputs, execute_fn=execute)
        return {"status": "locked", "stage_id": status.stage_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Removed duplicate - using the correct implementation below


@router.post("/runs/{run_id}/stages/table_selection/lock")
async def lock_table_selection(run_id: str, request: TableSelectionRequest):
    """Lock table selection stage."""
    sm = run_manager.get_state_machine(run_id)

    async def execute():
        return {
            "selected_tables": request.selected_tables,
            "completed": True,
        }

    try:
        inputs = {"tables": request.selected_tables}
        status = await sm.lock_stage(Stage.TABLE_SELECTION, inputs=inputs, execute_fn=execute)
        return {"status": "locked", "stage_id": status.stage_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/stages/parse/lock")
async def lock_parse(run_id: str, request: ParseRequest | None = None, background_tasks: BackgroundTasks = None):
    """Lock parse stage - start data extraction."""
    sm = run_manager.get_state_machine(run_id)

    # Get selection result for file list
    selection_status = await sm.store.get_stage_status(run_id, Stage.SELECTION)
    if selection_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Selection stage must be locked first")

    selection_artifact = await sm.store.get_artifact(run_id, Stage.SELECTION, selection_status.stage_id)

    # Get table selection
    table_status = await sm.store.get_stage_status(run_id, Stage.TABLE_SELECTION)
    selected_tables = {}
    if table_status.state == StageState.LOCKED and table_status.stage_id:
        table_artifact = await sm.store.get_artifact(run_id, Stage.TABLE_SELECTION, table_status.stage_id)
        selected_tables = table_artifact.get("selected_tables", {})

    # Handle optional request body
    column_mappings = request.column_mappings if request else None

    config = ParseConfig(
        selected_files=[Path(p) for p in selection_artifact.get("selected_files", [])],
        selected_tables=selected_tables,
        column_mappings=column_mappings,
    )

    # Create cancellation token
    cancel_token = CancellationToken()
    _cancel_tokens[run_id] = cancel_token

    async def execute():
        result = await execute_parse(
            run_id=run_id,
            config=config,
            workspace_path=sm.store.workspace,
            cancel_token=cancel_token,
        )
        return {
            "row_count": result.row_count,
            "column_count": result.column_count,
            "source_files": result.source_files,
            "completed": result.completed,
            "parse_id": result.parse_id,
            "output_path": result.output_path,
        }

    try:
        inputs = {
            "files": selection_artifact.get("selected_files", []),
            "tables": selected_tables,
            "mappings": column_mappings,
        }
        status = await sm.lock_stage(Stage.PARSE, inputs=inputs, execute_fn=execute)

        # Clean up cancel token
        _cancel_tokens.pop(run_id, None)

        artifact = await sm.store.get_artifact(run_id, Stage.PARSE, status.stage_id)
        return {
            "status": "locked",
            "stage_id": status.stage_id,
            "row_count": artifact.get("row_count"),
            "column_count": artifact.get("column_count"),
            "completed": artifact.get("completed"),
        }
    except ValueError as e:
        _cancel_tokens.pop(run_id, None)
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/stages/parse/cancel")
async def cancel_parse(run_id: str, reason: str = "user_requested", actor: str = "user"):
    """Cancel ongoing parse operation.

    Per ADR-0013: Cancellation events are logged for audit.
    """
    token = _cancel_tokens.get(run_id)
    if token:
        token.cancel()

        # Create audit log entry per ADR-0013
        audit_log = CancellationAuditLog(job_id=run_id)
        audit_log = audit_log.add_entry(
            event_type="cancel_requested",
            actor=actor,
            stage_id="parse",
            details={
                "reason": reason,
                "requested_at": datetime.now(timezone.utc).isoformat(),
            },
            message=f"Parse cancellation requested by {actor}: {reason}",
        )

        return {
            "status": "cancellation_requested",
            "run_id": run_id,
            "stage": "parse",
            "reason": reason,
            "actor": actor,
            "audit_entries": len(audit_log.entries),
        }
    return {"status": "no_active_parse", "run_id": run_id}


# Removed duplicate - using ADR-compliant implementation below


@router.post("/runs/{run_id}/export")
async def export_dataset(run_id: str, request: ExportRequest):
    """Export run as DataSet."""
    sm = run_manager.get_state_machine(run_id)

    # Get parse result
    parse_status = await sm.store.get_stage_status(run_id, Stage.PARSE)
    if parse_status.state != StageState.LOCKED or not parse_status.completed:
        raise HTTPException(status_code=400, detail="Parse stage must be completed first")

    parse_artifact = await sm.store.get_artifact(run_id, Stage.PARSE, parse_status.stage_id)
    if not parse_artifact:
        raise HTTPException(status_code=400, detail="Parse artifact not found")

    # Load the parsed data
    import polars as pl
    output_path = Path(parse_artifact["output_path"])
    data = pl.read_parquet(output_path)

    # Create a ParseResult-like object for export
    from ..stages.parse import ParseResult
    parse_result = ParseResult(
        data=data,
        row_count=parse_artifact["row_count"],
        column_count=parse_artifact["column_count"],
        source_files=parse_artifact["source_files"],
        completed=True,
        parse_id=parse_artifact["parse_id"],
        output_path=str(output_path),
    )

    manifest = await execute_export(
        run_id=run_id,
        parse_result=parse_result,
        name=request.name,
        description=request.description,
        aggregation_levels=request.aggregation_levels,
    )

    # Lock export stage
    async def execute():
        return {
            "dataset_id": manifest.dataset_id,
            "name": manifest.name,
            "row_count": manifest.row_count,
            "completed": True,
        }

    await sm.lock_stage(Stage.EXPORT, execute_fn=execute)

    return manifest.model_dump()


@router.get("/profiles")
async def list_profiles():
    """List available profiles."""
    from ..profiles.profile_loader import get_builtin_profiles, get_profile_by_id

    profiles = get_builtin_profiles()
    result = []

    for profile_id, profile_path in profiles.items():
        profile = get_profile_by_id(profile_id)
        if profile:
            result.append({
                "id": profile_id,
                "name": profile.title if hasattr(profile, 'title') else profile_id,
                "description": profile.description if hasattr(profile, 'description') else "",
                "table_count": len(profile.get_all_tables()) if hasattr(profile, 'get_all_tables') else 0,
            })

    return result


@router.get("/profiles/{profile_id}/tables")
async def get_profile_tables(profile_id: str):
    """Get tables defined in a profile per ADR-0011.
    
    Returns all table definitions from the profile YAML for UI display.
    Tables are grouped by level (run, image, etc.) per ui.table_selection config.
    """
    from ..profiles.profile_loader import get_profile_by_id

    profile = get_profile_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile not found: {profile_id}")

    tables_by_level = {}
    for level_name, table_config in profile.get_all_tables():
        if level_name not in tables_by_level:
            tables_by_level[level_name] = []
        
        tables_by_level[level_name].append({
            "id": table_config.id,
            "label": table_config.label,
            "description": table_config.description,
            "strategy": table_config.select.strategy if table_config.select else None,
            "stable_columns": table_config.stable_columns,
        })

    # Per DESIGN §9: Include UI hints in response
    ui_config = None
    if profile.ui:
        ui_config = {
            "show_file_preview": profile.ui.show_file_preview,
            "max_preview_files": profile.ui.max_preview_files,
            "highlight_matching": profile.ui.highlight_matching,
            "show_regex_matches": profile.ui.show_regex_matches,
            "editable_fields": profile.ui.editable_fields,
            "readonly_fields": profile.ui.readonly_fields,
            "default_name_template": profile.ui.default_name_template,
            "formats": profile.ui.formats,
        }
        if profile.ui.table_selection:
            ui_config["table_selection"] = {
                "group_by_level": profile.ui.table_selection.group_by_level,
                "default_selected": profile.ui.table_selection.default_selected,
                "collapsed_by_default": profile.ui.table_selection.collapsed_by_default,
            }
        if profile.ui.preview:
            ui_config["preview"] = {
                "max_rows": profile.ui.preview.max_rows,
                "max_columns": profile.ui.preview.max_columns,
                "number_format": profile.ui.preview.number_format,
                "null_display": profile.ui.preview.null_display,
            }

    return {
        "profile_id": profile_id,
        "profile_name": profile.title,
        "levels": tables_by_level,
        "total_tables": len(profile.get_all_tables()),
        "ui": ui_config,
    }


@router.post("/runs/{run_id}/stages/parse/profile-extract")
async def execute_profile_extraction(run_id: str, request: ParseRequest):
    """Execute profile-driven extraction per ADR-0011.
    
    Uses ProfileExecutor to extract tables defined in the profile YAML.
    Returns extraction results with validation summary.
    """
    from ..profiles.profile_loader import get_profile_by_id
    from ..profiles.profile_executor import ProfileExecutor
    from ..profiles.context_extractor import ContextExtractor
    from ..profiles.validation_engine import ValidationEngine
    from ..profiles.transform_pipeline import TransformPipeline

    sm = run_manager.get_state_machine(run_id)
    run_state = await sm.store.get_run(run_id)
    profile_id = run_state.get("profile_id")

    if not profile_id:
        raise HTTPException(status_code=400, detail="Run has no profile_id set")

    profile = get_profile_by_id(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Profile not found: {profile_id}")

    # Get selected files from selection stage
    selection_status = await sm.store.get_stage_status(run_id, Stage.SELECTION)
    if selection_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Selection stage must be locked first")

    selection_artifact = await sm.store.get_artifact(run_id, Stage.SELECTION, selection_status.stage_id)
    selected_files = [Path(f) for f in selection_artifact.get("selected_files", [])]

    if not selected_files:
        raise HTTPException(status_code=400, detail="No files selected")

    # Extract context
    context_extractor = ContextExtractor()
    context = {}
    for file_path in selected_files:
        file_context = context_extractor.extract(profile=profile, file_path=file_path)
        context.update(file_context)

    # Execute profile extraction
    executor = ProfileExecutor()
    extracted_tables = await executor.execute(
        profile=profile,
        files=selected_files,
        context=context,
        selected_tables=request.selected_tables if hasattr(request, 'selected_tables') else None,
    )

    # Validate extraction
    validation_engine = ValidationEngine()
    validation_summary = validation_engine.validate_extraction(extracted_tables, profile)

    # Apply transforms
    transform_pipeline = TransformPipeline()
    for table_id, df in extracted_tables.items():
        extracted_tables[table_id] = transform_pipeline.apply_normalization(df, profile)

    # Return results summary
    return {
        "run_id": run_id,
        "profile_id": profile_id,
        "tables_extracted": len(extracted_tables),
        "table_details": {
            table_id: {
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": df.columns,
            }
            for table_id, df in extracted_tables.items()
        },
        "validation": {
            "valid": validation_summary.valid,
            "error_count": validation_summary.error_count,
            "warning_count": validation_summary.warning_count,
        },
        "context": context,
    }


@router.get("/runs/{run_id}/stages/table_availability/scan")
async def scan_table_availability(run_id: str):
    """Scan for available tables from selected files.
    
    Per ADR-0006: Table availability must show actual row/column counts.
    """
    import logging
    logger = logging.getLogger(__name__)

    sm = run_manager.get_state_machine(run_id)

    # Get selection result
    selection_status = await sm.store.get_stage_status(run_id, Stage.SELECTION)
    if selection_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Selection stage must be locked first")

    selection_artifact = await sm.store.get_artifact(run_id, Stage.SELECTION, selection_status.stage_id)
    selected_files = selection_artifact.get("selected_files", [])

    # Get tables from selected files with actual row/column counts
    from apps.data_aggregator.backend.adapters import create_default_registry
    from shared.contracts.dat.adapter import ReadOptions
    
    registry = create_default_registry()
    tables = []
    for file_path in selected_files:
        try:
            adapter = registry.get_adapter_for_file(file_path)
            # Get table names using async probe_schema
            if adapter.metadata.capabilities.supports_multiple_sheets:
                probe_result = await adapter.probe_schema(file_path)
                file_tables = [s.sheet_name for s in probe_result.sheets] if probe_result.sheets else [Path(file_path).name]
            else:
                file_tables = [Path(file_path).name]
            
            for table in file_tables:
                # Get actual row and column counts using async adapter
                try:
                    options = ReadOptions(extra={"sheet_name": table} if table != Path(file_path).name else {})
                    full_df, _ = await adapter.read_dataframe(file_path, options)
                    row_count = len(full_df)
                    column_count = len(full_df.columns)
                except Exception as e:
                    logger.warning(f"Could not get counts for table {table} in {file_path}: {e}")
                    row_count = 0
                    column_count = 0

                tables.append({
                    "name": table,
                    "file": file_path,
                    "available": row_count > 0 or column_count > 0,
                    "row_count": row_count,
                    "column_count": column_count,
                })
        except Exception as e:
            logger.warning(f"Could not get tables from {file_path}: {e}")

    return tables


@router.post("/runs/{run_id}/stages/table_availability/lock")
async def lock_table_availability(run_id: str):
    """Lock table availability stage with discovered tables.
    
    Per ADR-0006: Table availability must show actual row/column counts.
    """
    import logging
    logger = logging.getLogger(__name__)

    sm = run_manager.get_state_machine(run_id)

    # Get selection result
    selection_status = await sm.store.get_stage_status(run_id, Stage.SELECTION)
    if selection_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Selection stage must be locked first")

    selection_artifact = await sm.store.get_artifact(run_id, Stage.SELECTION, selection_status.stage_id)
    selected_files = selection_artifact.get("selected_files", [])

    # Discover tables from selected files with actual row/column counts
    from apps.data_aggregator.backend.adapters import create_default_registry
    from shared.contracts.dat.adapter import ReadOptions
    
    registry = create_default_registry()
    tables = []
    for file_path in selected_files:
        try:
            adapter = registry.get_adapter_for_file(file_path)
            # Get table names using async probe_schema
            if adapter.metadata.capabilities.supports_multiple_sheets:
                probe_result = await adapter.probe_schema(file_path)
                file_tables = [s.sheet_name for s in probe_result.sheets] if probe_result.sheets else [Path(file_path).name]
            else:
                file_tables = [Path(file_path).name]
            
            for table in file_tables:
                # Get actual row and column counts using async adapter
                try:
                    options = ReadOptions(extra={"sheet_name": table} if table != Path(file_path).name else {})
                    full_df, _ = await adapter.read_dataframe(file_path, options)
                    row_count = len(full_df)
                    column_count = len(full_df.columns)
                except Exception as e:
                    logger.warning(f"Could not get counts for table {table}: {e}")
                    row_count = 0
                    column_count = 0

                tables.append({
                    "name": table,
                    "file": file_path,
                    "available": row_count > 0 or column_count > 0,
                    "row_count": row_count,
                    "column_count": column_count,
                })
        except Exception as e:
            logger.warning(f"Could not get tables from {file_path}: {e}")

    async def execute():
        return {
            "discovered_tables": tables,
            "completed": True,
        }

    try:
        inputs = {"files": selected_files}
        status = await sm.lock_stage(Stage.TABLE_AVAILABILITY, inputs=inputs, execute_fn=execute)
        return {"status": "locked", "stage_id": status.stage_id, "discovered_tables": tables}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/runs/{run_id}/stages/table_selection/tables")
async def get_table_selection_tables(run_id: str):
    """Get available tables for selection."""
    sm = run_manager.get_state_machine(run_id)

    # Get table availability result
    table_avail_status = await sm.store.get_stage_status(run_id, Stage.TABLE_AVAILABILITY)
    if table_avail_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Table availability stage must be locked first")

    # Get discovered tables from table availability artifact
    table_avail_artifact = await sm.store.get_artifact(run_id, Stage.TABLE_AVAILABILITY, table_avail_status.stage_id)
    discovered_tables = table_avail_artifact.get("discovered_tables", [])

    return discovered_tables


# Complete stage endpoint - marks a locked stage as completed (per SPEC-0044)
@router.post("/runs/{run_id}/stages/{stage}/complete")
async def complete_stage(run_id: str, stage: str):
    """Mark a locked stage as completed to advance the wizard."""
    try:
        stage_enum = Stage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    sm = run_manager.get_state_machine(run_id)

    # Get current status
    status = await sm.store.get_stage_status(run_id, stage_enum)
    if status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail=f"Stage {stage} must be locked first")

    if status.completed:
        return {"status": "already_completed", "stage": stage}

    # Update status to completed
    updated_status = StageStatus(
        stage=stage_enum,
        state=StageState.LOCKED,
        stage_id=status.stage_id,
        locked_at=status.locked_at,
        completed=True,
        artifact_path=status.artifact_path,
    )
    await sm.store.set_stage_status(run_id, stage_enum, updated_status)

    return {"status": "completed", "stage": stage}


# Unlock endpoints per ADR-0002: Artifact Preservation on Unlock
@router.post("/runs/{run_id}/stages/{stage}/unlock")
async def unlock_stage(run_id: str, stage: str):
    """Unlock a stage with artifact preservation per ADR-0002."""
    try:
        stage_enum = Stage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")

    sm = run_manager.get_state_machine(run_id)

    try:
        # Unlock with cascade - preserves artifacts per ADR-0002
        unlocked = await sm.unlock_stage(stage_enum, cascade=True)
        primary_status = unlocked[0] if unlocked else None
        return {
            "status": "unlocked",
            "stage": stage,
            "unlocked_at": primary_status.unlocked_at.isoformat() if primary_status and primary_status.unlocked_at else None,
            "cascade_unlocked": len(unlocked) > 1
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/stages/preview/lock")
async def lock_preview(run_id: str):
    """Lock preview stage with generated preview data from selected tables.
    
    Per ADR-0001-DAT: Preview is an optional stage BEFORE Parse.
    It shows a preview of selected tables to verify data before parsing.
    """
    import logging
    logger = logging.getLogger(__name__)

    sm = run_manager.get_state_machine(run_id)

    # Get table selection result (Preview comes AFTER Table Selection, BEFORE Parse)
    table_sel_status = await sm.store.get_stage_status(run_id, Stage.TABLE_SELECTION)
    if table_sel_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Table Selection stage must be locked first")

    table_sel_artifact = await sm.store.get_artifact(run_id, Stage.TABLE_SELECTION, table_sel_status.stage_id)
    if not table_sel_artifact:
        raise HTTPException(status_code=400, detail="Table Selection artifact not found")

    async def execute():
        # Generate preview data from selected tables
        from apps.data_aggregator.backend.adapters import create_default_registry
        from shared.contracts.dat.adapter import ReadOptions

        registry = create_default_registry()
        selected_tables = table_sel_artifact.get("selected_tables", {})
        all_rows = []
        all_columns = set()

        preview_rows_per_table = 20  # Limit per table

        for file_path, tables in selected_tables.items():
            adapter = registry.get_adapter_for_file(file_path)
            for table_name in tables[:5]:  # Limit tables per file
                try:
                    options = ReadOptions(extra={"sheet_name": table_name} if table_name != Path(file_path).name else {})
                    df, _ = await adapter.read_dataframe(file_path, options)

                    if len(df) > 0:
                        preview_df = df.head(preview_rows_per_table)
                        
                        # Per DESIGN §10: Apply PII masking in preview
                        context_status = await sm.store.get_stage_status(run_id, Stage.CONTEXT)
                        if context_status.stage_id:
                            ctx_artifact = await sm.store.get_artifact(
                                run_id, Stage.CONTEXT, context_status.stage_id
                            )
                            if ctx_artifact and ctx_artifact.get("profile_id"):
                                from ..profiles.profile_loader import get_profile_by_id
                                from ..profiles.transform_pipeline import TransformPipeline
                                profile = get_profile_by_id(ctx_artifact["profile_id"])
                                if profile and profile.governance and profile.governance.compliance:
                                    pii_cols = profile.governance.compliance.pii_columns
                                    mask_cols = profile.governance.compliance.mask_in_preview
                                    if pii_cols or mask_cols:
                                        pipeline = TransformPipeline()
                                        preview_df = pipeline.apply_pii_masking(
                                            preview_df, pii_cols, mask_cols
                                        )
                        
                        rows = preview_df.to_dicts()

                        # Add source info to each row
                        for row in rows:
                            row["_source_table"] = table_name
                            row["_source_file"] = Path(file_path).name

                        all_rows.extend(rows)
                        all_columns.update(preview_df.columns)
                except Exception as e:
                    logger.warning(f"Could not preview {table_name} from {file_path}: {e}")

        # Ensure consistent column order
        columns = ["_source_file", "_source_table"] + sorted(all_columns - {"_source_file", "_source_table"})

        return {
            "preview_data": {
                "columns": columns,
                "rows": all_rows[:100],  # Total limit
                "row_count": min(len(all_rows), 100),
                "total_rows": len(all_rows)
            },
            "completed": False  # User should stay on Preview to see data before advancing
        }

    try:
        inputs = {"table_selection_id": table_sel_status.stage_id}
        status = await sm.lock_stage(Stage.PREVIEW, inputs=inputs, execute_fn=execute)
        return {"status": "locked", "stage_id": status.stage_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/runs/{run_id}/stages/preview/data")
async def get_preview(run_id: str, rows: int = 100):
    """Get preview of parsed data from preview stage artifact."""
    sm = run_manager.get_state_machine(run_id)

    # Get preview artifact first (if stage is locked)
    preview_status = await sm.store.get_stage_status(run_id, Stage.PREVIEW)
    if preview_status.state == StageState.LOCKED and preview_status.stage_id:
        preview_artifact = await sm.store.get_artifact(run_id, Stage.PREVIEW, preview_status.stage_id)
        if preview_artifact and preview_artifact.get("preview_data"):
            preview_data = preview_artifact["preview_data"]
            return PreviewResponse(
                columns=preview_data["columns"],
                rows=preview_data["rows"][:rows],  # Limit to requested rows
                row_count=min(len(preview_data["rows"]), rows),
                total_rows=preview_data["total_rows"],
            )

    # Fallback: generate preview from parse data if no preview artifact
    parse_status = await sm.store.get_stage_status(run_id, Stage.PARSE)
    if parse_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Parse or Preview stage must be locked first")

    parse_artifact = await sm.store.get_artifact(run_id, Stage.PARSE, parse_status.stage_id)
    if not parse_artifact:
        raise HTTPException(status_code=400, detail="Parse artifact not found")

    import polars as pl
    output_path = Path(parse_artifact["output_path"])
    data = pl.read_parquet(output_path)

    preview = data.head(rows)

    return PreviewResponse(
        columns=preview.columns,
        rows=preview.to_dicts(),
        row_count=len(preview),
        total_rows=len(data),
    )


@router.post("/runs/{run_id}/stages/export/lock")
async def lock_export(run_id: str, request: ExportRequest):
    """Lock export stage with dataset generation."""
    import logging
    import traceback
    
    logger = logging.getLogger(__name__)

    try:
        sm = run_manager.get_state_machine(run_id)

        # Get parse result
        parse_status = await sm.store.get_stage_status(run_id, Stage.PARSE)
        if parse_status.state != StageState.LOCKED or not parse_status.completed:
            raise HTTPException(status_code=400, detail="Parse stage must be completed first")

        parse_artifact = await sm.store.get_artifact(run_id, Stage.PARSE, parse_status.stage_id)
        if not parse_artifact:
            raise HTTPException(status_code=400, detail="Parse artifact not found")

        logger.info(f"Export lock: parse_artifact keys = {list(parse_artifact.keys())}")
        logger.info(f"Export lock: output_path = {parse_artifact.get('output_path')}")

        async def execute():
            # Load the parsed data
            import polars as pl
            output_path = Path(parse_artifact["output_path"])
            logger.info(f"Loading parquet from: {output_path}")
            data = pl.read_parquet(output_path)
            logger.info(f"Loaded data: {len(data)} rows, {len(data.columns)} columns")

            # Create a ParseResult-like object for export
            from ..stages.parse import ParseResult
            parse_result = ParseResult(
                data=data,
                row_count=parse_artifact["row_count"],
                column_count=parse_artifact["column_count"],
                source_files=parse_artifact["source_files"],
                completed=True,
                parse_id=parse_artifact["parse_id"],
                output_path=str(output_path),
            )

            logger.info(f"Calling execute_export with name={request.name}")
            manifest = await execute_export(
                run_id=run_id,
                parse_result=parse_result,
                name=request.name,
                description=request.description,
                aggregation_levels=request.aggregation_levels,
            )
            logger.info(f"Export completed: dataset_id={manifest.dataset_id}")

            return {
                "dataset_id": manifest.dataset_id,
                "name": manifest.name,
                "row_count": manifest.row_count,
                "completed": True,
                "manifest": manifest.model_dump()
            }

        inputs = {
            "name": request.name,
            "description": request.description,
            "aggregation_levels": request.aggregation_levels
        }
        status = await sm.lock_stage(Stage.EXPORT, inputs=inputs, execute_fn=execute)

        # Get artifact for response
        artifact = await sm.store.get_artifact(run_id, Stage.EXPORT, status.stage_id)
        return {
            "status": "locked",
            "stage_id": status.stage_id,
            "dataset_id": artifact.get("dataset_id"),
            "manifest": artifact.get("manifest")
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except FileNotFoundError as e:
        logger.error(f"Run not found in export lock: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(f"ValueError in export lock: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in export lock: {type(e).__name__}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@router.get("/runs/{run_id}/stages/export/summary")
async def get_export_summary(run_id: str):
    """Get export summary before executing export."""
    sm = run_manager.get_state_machine(run_id)

    # Get parse result
    parse_status = await sm.store.get_stage_status(run_id, Stage.PARSE)
    if parse_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Parse stage must be locked first")

    parse_artifact = await sm.store.get_artifact(run_id, Stage.PARSE, parse_status.stage_id)
    if not parse_artifact:
        raise HTTPException(status_code=400, detail="Parse artifact not found")

    # Get columns from parsed data if available
    columns: list[str] = []
    output_path = parse_artifact.get("output_path")
    if output_path:
        try:
            import polars as pl
            df = pl.read_parquet(output_path)
            columns = df.columns
        except Exception:
            pass

    # Get aggregation levels from context stage if available
    aggregation_levels: list[str] = []
    try:
        context_status = await sm.store.get_stage_status(run_id, Stage.CONTEXT)
        if context_status.state == StageState.LOCKED and context_status.stage_id:
            context_artifact = await sm.store.get_artifact(run_id, Stage.CONTEXT, context_status.stage_id)
            if context_artifact:
                aggregation_levels = context_artifact.get("aggregation_levels", [])
    except Exception:
        pass

    return {
        "row_count": parse_artifact.get("row_count", 0),
        "column_count": parse_artifact.get("column_count", 0),
        "columns": columns,
        "aggregation_levels": aggregation_levels,
        "source_files": parse_artifact.get("source_files", []),
        "ready": parse_artifact.get("completed", False),
    }


@router.post("/runs/{run_id}/stages/export/execute")
async def execute_export_stage(run_id: str, request: ExportRequest):
    """Execute export stage."""
    import logging
    logger = logging.getLogger(__name__)

    sm = run_manager.get_state_machine(run_id)

    # Get parse result
    parse_status = await sm.store.get_stage_status(run_id, Stage.PARSE)
    if parse_status.state != StageState.LOCKED or not parse_status.completed:
        raise HTTPException(status_code=400, detail="Parse stage must be completed first")

    parse_artifact = await sm.store.get_artifact(run_id, Stage.PARSE, parse_status.stage_id)
    if not parse_artifact:
        raise HTTPException(status_code=400, detail="Parse artifact not found")

    logger.info(f"Executing export for run {run_id}")

    # Load the parsed data
    import polars as pl
    output_path = Path(parse_artifact["output_path"])
    data = pl.read_parquet(output_path)

    # Create a ParseResult-like object for export
    from ..stages.parse import ParseResult
    parse_result = ParseResult(
        data=data,
        row_count=parse_artifact["row_count"],
        column_count=parse_artifact["column_count"],
        source_files=parse_artifact["source_files"],
        completed=True,
        parse_id=parse_artifact["parse_id"],
        output_path=str(output_path),
    )

    manifest = await execute_export(
        run_id=run_id,
        parse_result=parse_result,
        name=request.name,
        description=request.description,
        aggregation_levels=request.aggregation_levels,
    )

    # Lock export stage
    async def execute():
        return {
            "dataset_id": manifest.dataset_id,
            "name": manifest.name,
            "row_count": manifest.row_count,
            "completed": True,
        }

    await sm.lock_stage(Stage.EXPORT, execute_fn=execute)

    return manifest.model_dump()


@router.get("/runs/{run_id}/stages/parse/progress")
async def get_parse_progress(run_id: str):
    """Get parse stage progress."""
    sm = run_manager.get_state_machine(run_id)

    parse_status = await sm.store.get_stage_status(run_id, Stage.PARSE)

    # Determine status
    if parse_status.state == StageState.UNLOCKED:
        status = "idle"
    elif not parse_status.completed:
        status = "running"
    else:
        status = "completed"

    # Base response
    response = {
        "status": status,
        "completed": parse_status.completed,
        "error": parse_status.error,
        "progress": 0,
        "processed_files": 0,
        "total_files": 0,
        "processed_rows": 0,
    }

    # If completed, get artifact data for counts
    if parse_status.completed and parse_status.stage_id:
        try:
            artifact = await sm.store.get_artifact(run_id, Stage.PARSE, parse_status.stage_id)
            response["processed_rows"] = artifact.get("row_count", 0)
            response["processed_files"] = len(artifact.get("source_files", []))
            response["total_files"] = response["processed_files"]
            response["progress"] = 100
        except Exception:
            pass

    return response


@router.post("/runs/{run_id}/stages/parse/start")
async def start_parse(run_id: str):
    """Start parse stage execution with table selection data."""
    sm = run_manager.get_state_machine(run_id)

    # Verify prerequisites
    selection_status = await sm.store.get_stage_status(run_id, Stage.SELECTION)
    if selection_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Selection stage must be locked first")

    # Get selection artifact
    selection_artifact = await sm.store.get_artifact(run_id, Stage.SELECTION, selection_status.stage_id)

    # Get table selection if available
    table_status = await sm.store.get_stage_status(run_id, Stage.TABLE_SELECTION)
    selected_tables = {}
    if table_status.state == StageState.LOCKED and table_status.stage_id:
        table_artifact = await sm.store.get_artifact(run_id, Stage.TABLE_SELECTION, table_status.stage_id)
        selected_tables = table_artifact.get("selected_tables", {})

    config = ParseConfig(
        selected_files=[Path(p) for p in selection_artifact.get("selected_files", [])],
        selected_tables=selected_tables,
        column_mappings=None,
    )

    cancel_token = CancellationToken()
    _cancel_tokens[run_id] = cancel_token

    async def execute():
        result = await execute_parse(
            run_id=run_id,
            config=config,
            workspace_path=sm.store.workspace,
            cancel_token=cancel_token,
        )
        return {
            "row_count": result.row_count,
            "column_count": result.column_count,
            "source_files": result.source_files,
            "completed": result.completed,
            "parse_id": result.parse_id,
            "output_path": result.output_path,
        }

    try:
        inputs = {
            "files": selection_artifact.get("selected_files", []),
            "tables": selected_tables
        }
        status = await sm.lock_stage(Stage.PARSE, inputs=inputs, execute_fn=execute)
        _cancel_tokens.pop(run_id, None)

        artifact = await sm.store.get_artifact(run_id, Stage.PARSE, status.stage_id)
        return {
            "status": "started",
            "completed": artifact.get("completed", False),
            "row_count": artifact.get("row_count", 0),
            "column_count": artifact.get("column_count", 0),
        }
    except ValueError as e:
        _cancel_tokens.pop(run_id, None)
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Cleanup Endpoints (M8: Cancellation Checkpointing per ADR-0013)
# =============================================================================


@router.post("/runs/{run_id}/cleanup")
async def cleanup_run(
    run_id: str,
    targets: list[CleanupTarget] | None = None,
    dry_run: bool = True,
):
    """Explicitly clean up partial artifacts from cancelled runs.

    Per ADR-0013: Cleanup is user-initiated only, dry-run by default.

    Args:
        run_id: Run identifier.
        targets: Optional list of cleanup targets. If None, discovers targets.
        dry_run: If True, only report what would be cleaned (default: True).

    Returns:
        CleanupResult with details of cleanup actions.
    """
    if targets is None:
        targets = []

    result = await cleanup(
        run_id=run_id,
        targets=targets,
        dry_run=dry_run,
    )
    return result


# =============================================================================
# Profile CRUD Endpoints (M9: Profile Management per SPEC-DAT-0005)
# =============================================================================


@router.post("/profiles")
async def create_profile(request: CreateProfileRequest):
    """Create a new extraction profile.

    Per SPEC-DAT-0005: Profile management with deterministic IDs.
    """
    try:
        return await profile_service.create(request)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """Get a profile by ID."""
    profile = await profile_service.get(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/profiles/{profile_id}")
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
