"""Pipeline Service - cross-tool workflow orchestration.

Provides gateway-level APIs for:
- Creating multi-tool pipelines
- Executing pipeline steps across tools
- Tracking pipeline state and progress

Per ADR-0026: Pipeline error handling with fail-fast semantics.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException

from shared.contracts.core.pipeline import (
    CreatePipelineRequest,
    Pipeline,
    PipelineRef,
    PipelineStep,
    PipelineStepState,
    PipelineStepType,
)
from shared.utils.stage_id import compute_pipeline_id

logger = logging.getLogger(__name__)

# Tool API base URLs (internal routing via gateway mounts)
TOOL_BASE_URLS = {
    "dat": "http://localhost:8000/api/dat",
    "sov": "http://localhost:8000/api/sov",
    "pptx": "http://localhost:8000/api/pptx",
}

# Timeout for tool API calls (seconds)
TOOL_API_TIMEOUT = 300.0

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

    Per ADR-0026: Fail-fast semantics with explicit error handling.

    Args:
        step: Pipeline step to execute.
        input_dataset_ids: Resolved input dataset IDs.

    Returns:
        Output dataset ID from the step execution.

    Raises:
        ValueError: If step type is unknown.
        httpx.HTTPError: If tool API call fails.
    """
    step_type = step.step_type.value
    tool_name = step_type.split(":")[0]
    action = step_type.split(":")[1] if ":" in step_type else ""

    base_url = TOOL_BASE_URLS.get(tool_name)
    if not base_url:
        raise ValueError(f"Unknown tool: {tool_name}")

    async with httpx.AsyncClient(timeout=TOOL_API_TIMEOUT) as client:
        if step_type == PipelineStepType.DAT_AGGREGATE.value:
            return await _dispatch_dat_aggregate(client, base_url, step, input_dataset_ids)

        elif step_type == PipelineStepType.DAT_EXPORT.value:
            return await _dispatch_dat_export(client, base_url, step, input_dataset_ids)

        elif step_type == PipelineStepType.SOV_ANOVA.value:
            return await _dispatch_sov_anova(client, base_url, step, input_dataset_ids)

        elif step_type == PipelineStepType.SOV_VARIANCE_COMPONENTS.value:
            return await _dispatch_sov_variance(client, base_url, step, input_dataset_ids)

        elif step_type == PipelineStepType.PPTX_GENERATE.value:
            return await _dispatch_pptx_generate(client, base_url, step, input_dataset_ids)

        elif step_type == PipelineStepType.PPTX_RENDER.value:
            return await _dispatch_pptx_render(client, base_url, step, input_dataset_ids)

        else:
            raise ValueError(f"Unknown step type: {step_type}")


async def _dispatch_dat_aggregate(
    client: httpx.AsyncClient,
    base_url: str,
    step: PipelineStep,
    input_dataset_ids: list[str],
) -> str:
    """Dispatch DAT aggregate step."""
    logger.info(f"Dispatching DAT aggregate step: {step.name or step.step_index}")

    # DAT aggregation typically uses profile-based extraction
    payload = {
        "profile_id": step.config.get("profile_id"),
        "source_files": step.config.get("source_files", []),
        "output_name": step.config.get("output_name", f"pipeline_step_{step.step_index}"),
        **step.config,
    }

    response = await client.post(
        f"{base_url}/api/v1/runs",
        json=payload,
    )
    response.raise_for_status()

    result = response.json()
    return result.get("dataset_id", result.get("run_id", ""))


async def _dispatch_dat_export(
    client: httpx.AsyncClient,
    base_url: str,
    step: PipelineStep,
    input_dataset_ids: list[str],
) -> str:
    """Dispatch DAT export step."""
    logger.info(f"Dispatching DAT export step: {step.name or step.step_index}")

    run_id = input_dataset_ids[0] if input_dataset_ids else step.config.get("run_id")
    if not run_id:
        raise ValueError("DAT export requires input run_id")

    payload = {
        "format": step.config.get("format", "parquet"),
        "output_name": step.config.get("output_name"),
    }

    response = await client.post(
        f"{base_url}/api/v1/runs/{run_id}/export",
        json=payload,
    )
    response.raise_for_status()

    result = response.json()
    return result.get("dataset_id", "")


async def _dispatch_sov_anova(
    client: httpx.AsyncClient,
    base_url: str,
    step: PipelineStep,
    input_dataset_ids: list[str],
) -> str:
    """Dispatch SOV ANOVA analysis step."""
    logger.info(f"Dispatching SOV ANOVA step: {step.name or step.step_index}")

    # Create analysis
    dataset_id = input_dataset_ids[0] if input_dataset_ids else None
    create_payload = {
        "name": step.config.get("name", f"Pipeline ANOVA {step.step_index}"),
        "dataset_id": dataset_id,
    }

    create_response = await client.post(
        f"{base_url}/api/v1/analyses",
        json=create_payload,
    )
    create_response.raise_for_status()
    analysis = create_response.json()
    analysis_id = analysis["analysis_id"]

    # Run ANOVA
    run_payload = {
        "factors": step.config.get("factors", []),
        "response_columns": step.config.get("response_columns", []),
        "alpha": step.config.get("alpha", 0.05),
        "anova_type": step.config.get("anova_type", "one-way"),
    }

    run_response = await client.post(
        f"{base_url}/api/v1/analyses/{analysis_id}/run",
        json=run_payload,
    )
    run_response.raise_for_status()

    # Export as dataset
    export_payload = {
        "name": step.config.get("output_name", f"SOV Results {analysis_id[:8]}"),
    }

    export_response = await client.post(
        f"{base_url}/api/v1/analyses/{analysis_id}/export",
        json=export_payload,
    )
    export_response.raise_for_status()

    result = export_response.json()
    return result.get("dataset_id", analysis_id)


async def _dispatch_sov_variance(
    client: httpx.AsyncClient,
    base_url: str,
    step: PipelineStep,
    input_dataset_ids: list[str],
) -> str:
    """Dispatch SOV variance components step."""
    logger.info(f"Dispatching SOV variance components step: {step.name or step.step_index}")

    # Similar to ANOVA but with variance components analysis type
    step.config["anova_type"] = "n-way"
    return await _dispatch_sov_anova(client, base_url, step, input_dataset_ids)


async def _dispatch_pptx_generate(
    client: httpx.AsyncClient,
    base_url: str,
    step: PipelineStep,
    input_dataset_ids: list[str],
) -> str:
    """Dispatch PPTX generation step."""
    logger.info(f"Dispatching PPTX generate step: {step.name or step.step_index}")

    # Create project
    project_payload = {
        "name": step.config.get("project_name", f"Pipeline Report {step.step_index}"),
        "description": step.config.get("description", "Generated by pipeline"),
    }

    project_response = await client.post(
        f"{base_url}/api/v1/projects",
        json=project_payload,
    )
    project_response.raise_for_status()
    project = project_response.json()
    project_id = project["id"]

    # Load dataset if provided
    if input_dataset_ids:
        dataset_payload = {
            "dataset_id": input_dataset_ids[0],
        }
        await client.post(
            f"{base_url}/api/v1/projects/{project_id}/from-dataset",
            json=dataset_payload,
        )

    # Generate PPTX
    template_id = step.config.get("template_id")
    if template_id:
        generate_payload = {
            "template_id": template_id,
            "output_filename": step.config.get("output_filename", "report.pptx"),
        }

        generate_response = await client.post(
            f"{base_url}/api/v1/projects/{project_id}/generate",
            json=generate_payload,
        )
        generate_response.raise_for_status()

    return project_id


async def _dispatch_pptx_render(
    client: httpx.AsyncClient,
    base_url: str,
    step: PipelineStep,
    input_dataset_ids: list[str],
) -> str:
    """Dispatch PPTX render step."""
    logger.info(f"Dispatching PPTX render step: {step.name or step.step_index}")

    # Render is similar to generate but for existing projects
    project_id = step.config.get("project_id")
    if not project_id and input_dataset_ids:
        project_id = input_dataset_ids[0]

    if not project_id:
        raise ValueError("PPTX render requires project_id")

    render_payload = {
        "output_path": step.config.get("output_path", "output.pptx"),
        "overwrite_existing": step.config.get("overwrite_existing", True),
    }

    response = await client.post(
        f"{base_url}/api/v1/projects/{project_id}/render",
        json=render_payload,
    )
    response.raise_for_status()

    result = response.json()
    return result.get("render_id", project_id)
