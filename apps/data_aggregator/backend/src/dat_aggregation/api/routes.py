"""DAT API routes."""
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks

from ..core.state_machine import DATStateMachine, Stage, StageState
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

router = APIRouter()
run_manager = RunManager()

# Track active cancellation tokens
_cancel_tokens: dict[str, CancellationToken] = {}


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
        raise HTTPException(status_code=404, detail="Run not found")
    
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
    from fastapi import Body
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
async def lock_parse(run_id: str, request: ParseRequest, background_tasks: BackgroundTasks):
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
    
    config = ParseConfig(
        selected_files=[Path(p) for p in selection_artifact.get("selected_files", [])],
        selected_tables=selected_tables,
        column_mappings=request.column_mappings,
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
            "mappings": request.column_mappings,
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
async def cancel_parse(run_id: str):
    """Cancel ongoing parse operation."""
    token = _cancel_tokens.get(run_id)
    if token:
        token.cancel()
        return {"status": "cancellation_requested"}
    return {"status": "no_active_parse"}


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
                "name": profile.title if hasattr(profile, 'title') else profile_id
            })
    
    return result


@router.get("/runs/{run_id}/stages/table_availability/scan")
async def scan_table_availability(run_id: str):
    """Scan for available tables from selected files."""
    sm = run_manager.get_state_machine(run_id)
    
    # Get selection result
    selection_status = await sm.store.get_stage_status(run_id, Stage.SELECTION)
    if selection_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Selection stage must be locked first")
    
    selection_artifact = await sm.store.get_artifact(run_id, Stage.SELECTION, selection_status.stage_id)
    selected_files = selection_artifact.get("selected_files", [])
    
    # Get tables from selected files
    from ..adapters.factory import AdapterFactory
    tables = []
    for file_path in selected_files:
        try:
            file_tables = AdapterFactory.get_tables(Path(file_path))
            for table in file_tables:
                tables.append({
                    "name": table,
                    "file": file_path,
                    "available": True,
                    "row_count": 0,
                    "column_count": 0,
                })
        except Exception:
            pass
    
    return tables


@router.post("/runs/{run_id}/stages/table_availability/lock")
async def lock_table_availability(run_id: str):
    """Lock table availability stage with discovered tables."""
    sm = run_manager.get_state_machine(run_id)
    
    # Get selection result
    selection_status = await sm.store.get_stage_status(run_id, Stage.SELECTION)
    if selection_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Selection stage must be locked first")
    
    selection_artifact = await sm.store.get_artifact(run_id, Stage.SELECTION, selection_status.stage_id)
    selected_files = selection_artifact.get("selected_files", [])
    
    # Discover tables from selected files
    from ..adapters.factory import AdapterFactory
    tables = []
    for file_path in selected_files:
        try:
            file_tables = AdapterFactory.get_tables(Path(file_path))
            for table in file_tables:
                tables.append({
                    "name": table,
                    "file": file_path,
                    "available": True,
                    "row_count": 0,
                    "column_count": 0,
                })
        except Exception:
            pass
    
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
        status = await sm.unlock_stage(stage_enum, cascade=True)
        return {
            "status": "unlocked", 
            "stage": stage,
            "unlocked_at": status.unlocked_at.isoformat() if status.unlocked_at else None,
            "cascade_unlocked": True
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/runs/{run_id}/stages/preview/lock")
async def lock_preview(run_id: str):
    """Lock preview stage with generated preview data."""
    sm = run_manager.get_state_machine(run_id)
    
    # Get parse result for preview generation
    parse_status = await sm.store.get_stage_status(run_id, Stage.PARSE)
    if parse_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Parse stage must be locked first")
    
    parse_artifact = await sm.store.get_artifact(run_id, Stage.PARSE, parse_status.stage_id)
    if not parse_artifact:
        raise HTTPException(status_code=400, detail="Parse artifact not found")
    
    async def execute():
        # Generate preview data from parse results
        import polars as pl
        output_path = Path(parse_artifact["output_path"])
        data = pl.read_parquet(output_path)
        
        preview_rows = 100
        preview_data = data.head(preview_rows)
        
        return {
            "preview_data": {
                "columns": preview_data.columns,
                "rows": preview_data.to_dicts(),
                "row_count": len(preview_data),
                "total_rows": len(data)
            },
            "completed": True
        }
    
    try:
        inputs = {"parse_artifact_id": parse_status.stage_id}
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
    sm = run_manager.get_state_machine(run_id)
    
    # Get parse result
    parse_status = await sm.store.get_stage_status(run_id, Stage.PARSE)
    if parse_status.state != StageState.LOCKED or not parse_status.completed:
        raise HTTPException(status_code=400, detail="Parse stage must be completed first")
    
    parse_artifact = await sm.store.get_artifact(run_id, Stage.PARSE, parse_status.stage_id)
    if not parse_artifact:
        raise HTTPException(status_code=400, detail="Parse artifact not found")
    
    async def execute():
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
        
        return {
            "dataset_id": manifest.dataset_id,
            "name": manifest.name,
            "row_count": manifest.row_count,
            "completed": True,
            "manifest": manifest.model_dump()
        }
    
    try:
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    
    return {
        "row_count": parse_artifact.get("row_count", 0),
        "column_count": parse_artifact.get("column_count", 0),
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
    
    # Return progress info
    return {
        "status": "idle" if parse_status.state == StageState.UNLOCKED else "running" if not parse_status.completed else "completed",
        "completed": parse_status.completed,
        "error": parse_status.error,
    }


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
