"""Pipeline Service - cross-tool workflow orchestration.

Provides gateway-level APIs for:
- Creating multi-tool pipelines
- Executing pipeline steps across tools
- Tracking pipeline state and progress
"""

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException

from shared.contracts.core.pipeline import (
    CreatePipelineRequest,
    Pipeline,
    PipelineRef,
    PipelineStep,
    PipelineStepState,
)
from shared.utils.stage_id import compute_pipeline_id

router = APIRouter()

# In-memory pipeline storage (will be replaced with registry DB)
_pipelines: dict[str, Pipeline] = {}


@router.post("", response_model=Pipeline)
@router.post("/", response_model=Pipeline)
async def create_pipeline(
    request: CreatePipelineRequest,
    background_tasks: BackgroundTasks,
) -> Pipeline:
    """Create a new multi-tool pipeline."""
    now = datetime.now(timezone.utc)
    
    # Compute deterministic ID
    pipeline_id = compute_pipeline_id(
        name=request.name,
        steps=[s.model_dump() for s in request.steps],
    )
    
    # Create pipeline
    pipeline = Pipeline(
        pipeline_id=pipeline_id,
        name=request.name,
        description=request.description,
        created_at=now,
        steps=request.steps,
        tags=request.tags,
    )
    
    _pipelines[pipeline_id] = pipeline
    
    # Auto-execute if requested
    if request.auto_execute:
        background_tasks.add_task(_execute_pipeline, pipeline_id)
        pipeline.state = "queued"
    
    return pipeline


@router.get("", response_model=list[PipelineRef])
@router.get("/", response_model=list[PipelineRef])
async def list_pipelines(
    limit: int = 50,
) -> list[PipelineRef]:
    """List all pipelines."""
    refs = []
    for pipeline in list(_pipelines.values())[:limit]:
        refs.append(PipelineRef(
            pipeline_id=pipeline.pipeline_id,
            name=pipeline.name,
            state=pipeline.state,
            step_count=len(pipeline.steps),
            current_step=pipeline.current_step,
            created_at=pipeline.created_at,
            updated_at=pipeline.updated_at,
        ))
    return refs


@router.get("/{pipeline_id}", response_model=Pipeline)
async def get_pipeline(pipeline_id: str) -> Pipeline:
    """Get pipeline details and current state."""
    if pipeline_id not in _pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline not found: {pipeline_id}")
    return _pipelines[pipeline_id]


@router.post("/{pipeline_id}/execute", response_model=Pipeline)
async def execute_pipeline(
    pipeline_id: str,
    background_tasks: BackgroundTasks,
) -> Pipeline:
    """Execute all pending steps in a pipeline."""
    if pipeline_id not in _pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline not found: {pipeline_id}")
    
    pipeline = _pipelines[pipeline_id]
    
    if pipeline.state in ("running", "completed"):
        raise HTTPException(
            status_code=400,
            detail=f"Pipeline is already {pipeline.state}",
        )
    
    pipeline.state = "queued"
    pipeline.updated_at = datetime.now(timezone.utc)
    
    background_tasks.add_task(_execute_pipeline, pipeline_id)
    
    return pipeline


@router.post("/{pipeline_id}/cancel", response_model=Pipeline)
async def cancel_pipeline(pipeline_id: str) -> Pipeline:
    """Cancel a running pipeline (per ADR-0013: preserves completed artifacts)."""
    if pipeline_id not in _pipelines:
        raise HTTPException(status_code=404, detail=f"Pipeline not found: {pipeline_id}")
    
    pipeline = _pipelines[pipeline_id]
    
    if pipeline.state not in ("queued", "running"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel pipeline in state: {pipeline.state}",
        )
    
    pipeline.state = "cancelled"
    pipeline.updated_at = datetime.now(timezone.utc)
    
    # Mark current step as cancelled
    if pipeline.current_step < len(pipeline.steps):
        pipeline.steps[pipeline.current_step].state = PipelineStepState.CANCELLED
    
    return pipeline


async def _execute_pipeline(pipeline_id: str) -> None:
    """Execute pipeline steps sequentially.
    
    This is a background task that:
    1. Resolves dynamic input references ($step_N_output)
    2. Dispatches each step to the appropriate tool
    3. Tracks progress and handles errors
    """
    pipeline = _pipelines.get(pipeline_id)
    if not pipeline:
        return
    
    pipeline.state = "running"
    pipeline.started_at = datetime.now(timezone.utc)
    
    try:
        for i, step in enumerate(pipeline.steps):
            if pipeline.state == "cancelled":
                break
            
            pipeline.current_step = i
            step.state = PipelineStepState.RUNNING
            step.started_at = datetime.now(timezone.utc)
            pipeline.updated_at = step.started_at
            
            # Resolve dynamic input references
            resolved_inputs = _resolve_step_inputs(pipeline, step)
            
            try:
                # Dispatch to appropriate tool
                output_id = await _dispatch_step(step, resolved_inputs)
                
                step.output_dataset_id = output_id
                step.state = PipelineStepState.COMPLETED
                step.completed_at = datetime.now(timezone.utc)
                step.progress_pct = 100.0
                
            except Exception as e:
                step.state = PipelineStepState.FAILED
                step.error_message = str(e)
                step.completed_at = datetime.now(timezone.utc)
                pipeline.state = "failed"
                break
        
        if pipeline.state == "running":
            pipeline.state = "completed"
            pipeline.completed_at = datetime.now(timezone.utc)
            
    except Exception as e:
        pipeline.state = "failed"
    
    pipeline.updated_at = datetime.now(timezone.utc)


def _resolve_step_inputs(pipeline: Pipeline, step: PipelineStep) -> list[str]:
    """Resolve dynamic input references like $step_0_output."""
    resolved = []
    for input_id in step.input_dataset_ids:
        if input_id.startswith("$step_") and input_id.endswith("_output"):
            # Extract step index
            step_idx = int(input_id[6:-7])
            if step_idx < len(pipeline.steps):
                output_id = pipeline.steps[step_idx].output_dataset_id
                if output_id:
                    resolved.append(output_id)
        else:
            resolved.append(input_id)
    return resolved


async def _dispatch_step(step: PipelineStep, input_dataset_ids: list[str]) -> str:
    """Dispatch a step to the appropriate tool and return output dataset ID.
    
    TODO: Implement actual tool dispatch when tools are integrated.
    """
    # Placeholder implementation
    # In production, this will call the appropriate tool's API
    
    step_type = step.step_type.value
    
    if step_type.startswith("dat:"):
        # Call Data Aggregator API
        # return await dat_client.execute(step.config, input_dataset_ids)
        raise NotImplementedError("DAT tool not yet integrated")
    
    elif step_type.startswith("sov:"):
        # Call SOV Analyzer API
        # return await sov_client.execute(step.config, input_dataset_ids)
        raise NotImplementedError("SOV tool not yet integrated")
    
    elif step_type.startswith("pptx:"):
        # Call PowerPoint Generator API
        # return await pptx_client.execute(step.config, input_dataset_ids)
        raise NotImplementedError("PPTX tool not yet integrated")
    
    else:
        raise ValueError(f"Unknown step type: {step_type}")
