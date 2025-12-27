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


@router.post("/v1/runs", response_model=CreateRunResponse)
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


@router.get("/v1/runs")
async def list_runs(limit: int = 50):
    """List DAT runs."""
    runs = await run_manager.list_runs(limit=limit)
    return runs


@router.get("/v1/runs/{run_id}")
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
    
    return RunResponse(
        run_id=run["run_id"],
        name=run["name"],
        created_at=run["created_at"],
        profile_id=run.get("profile_id"),
        stages=stages,
    )


@router.get("/v1/runs/{run_id}/stages/{stage}")
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


@router.post("/v1/runs/{run_id}/stages/selection/lock")
async def lock_selection(run_id: str, request: SelectionRequest):
    """Lock selection stage - discover and select files."""
    sm = run_manager.get_state_machine(run_id)
    
    source_paths = [Path(p) for p in request.source_paths]
    selected = [Path(p) for p in request.selected_files] if request.selected_files else None
    
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


@router.post("/v1/runs/{run_id}/stages/table_selection/lock")
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


@router.post("/v1/runs/{run_id}/stages/parse/lock")
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


@router.post("/v1/runs/{run_id}/stages/parse/cancel")
async def cancel_parse(run_id: str):
    """Cancel ongoing parse operation."""
    token = _cancel_tokens.get(run_id)
    if token:
        token.cancel()
        return {"status": "cancellation_requested"}
    return {"status": "no_active_parse"}


@router.post("/v1/runs/{run_id}/stages/{stage}/unlock")
async def unlock_stage(run_id: str, stage: str):
    """Unlock a stage (cascades to downstream)."""
    try:
        stage_enum = Stage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {stage}")
    
    sm = run_manager.get_state_machine(run_id)
    unlocked = await sm.unlock_stage(stage_enum)
    return {"unlocked": [s.stage.value for s in unlocked]}


@router.post("/v1/runs/{run_id}/export")
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


@router.get("/v1/runs/{run_id}/preview")
async def get_preview(run_id: str, rows: int = 100):
    """Get preview of parsed data."""
    sm = run_manager.get_state_machine(run_id)
    
    parse_status = await sm.store.get_stage_status(run_id, Stage.PARSE)
    if parse_status.state != StageState.LOCKED:
        raise HTTPException(status_code=400, detail="Parse stage must be locked first")
    
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
