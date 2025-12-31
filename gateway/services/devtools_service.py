"""DevTools Service - API endpoints for developer/power-user utilities.

This service provides endpoints for managing ADRs, config files, and other
development artifacts. Access is controlled by runtime flags.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError

from gateway.services.workflow_service import (
    build_artifact_graph,
    scan_artifacts,
    _get_file_format,
    create_workflow,
    get_workflow_status,
    advance_workflow,
    generate_prompt,
    generate_artifact_content,
    generate_full_workflow,
)
from shared.contracts.adr_schema import (
    ADRCreateRequest as SchemaADRCreateRequest,
    ADRFieldValidationRequest,
    ADRFieldValidationResponse,
    ADRSchema,
)
from shared.contracts.spec_schema import SPECSchema
from shared.contracts.plan_schema import PlanSchema
from shared.contracts.devtools.workflow import (
    ArtifactListResponse,
    ArtifactResponse,
    ArtifactStatus,
    ArtifactSummary,
    ArtifactType,
    CreateArtifactRequest,
    CreateWorkflowRequest,
    GraphResponse,
    GenerationRequest,
    GenerationResponse,
    PromptResponse,
    UpdateArtifactRequest,
    WorkflowResponse,
)

router = APIRouter()


def get_knowledge_context(prompt: str, max_tokens: int = 4000) -> dict | None:
    """Get RAG context from knowledge archive for DevTools.

    PLAN-002 M4: Integration with Knowledge Archive.
    """
    try:
        from gateway.services.knowledge.database import init_database
        from gateway.services.knowledge.search_service import SearchService
        from gateway.services.knowledge.context_builder import ContextBuilder
        from gateway.services.knowledge.sanitizer import Sanitizer

        conn = init_database()
        search = SearchService(conn)
        builder = ContextBuilder(search, Sanitizer())

        ctx = builder.build_context(prompt, max_tokens=max_tokens)
        return {
            'context': ctx.context,
            'sources': ctx.sources,
            'token_count': ctx.token_count
        }
    except Exception:
        return None


# Get project root (parent of gateway/)
PROJECT_ROOT = Path(__file__).parent.parent.parent
ADRS_DIR = PROJECT_ROOT / ".adrs"


class ADRSummary(BaseModel):
    """Summary of an ADR file."""

    id: str
    title: str
    status: str
    date: str
    scope: str
    filename: str
    folder: str


class ADRContent(BaseModel):
    """Full content of an ADR file."""

    filename: str
    content: dict[str, Any]
    raw_json: str


class ADRUpdateRequest(BaseModel):
    """Request to update an ADR file."""

    content: dict[str, Any]


class ADRCreateRequest(BaseModel):
    """Request to create a new ADR file."""

    id: str = Field(..., description="ADR ID like 'ADR-0027_My-New-ADR'")
    title: str
    status: str = "proposed"
    scope: str
    context: str
    decision_primary: str
    content: dict[str, Any] | None = None


class ValidationResult(BaseModel):
    """Result of ADR validation."""

    valid: bool
    errors: list[str]
    warnings: list[str]


class DevToolsConfig(BaseModel):
    """DevTools configuration and feature flags."""

    enabled: bool
    mode: str  # 'dev', 'power_user', 'hidden'
    features: dict[str, bool]


# In-memory config (would be loaded from env/config file in production)
_devtools_config = DevToolsConfig(
    enabled=True,
    mode="dev",
    features={
        "adr_editor": True,
        "config_editor": False,  # Earmarked for future
        "domain_mapper": False,  # Earmarked for future
        "schema_validator": False,  # Earmarked for future
    },
)


@router.get("/config", response_model=DevToolsConfig)
async def get_devtools_config() -> DevToolsConfig:
    """Get DevTools configuration and feature flags."""
    return _devtools_config


@router.post("/config", response_model=DevToolsConfig)
async def update_devtools_config(
    enabled: bool | None = None,
    mode: str | None = None,
) -> DevToolsConfig:
    """Update DevTools configuration."""
    global _devtools_config
    if enabled is not None:
        _devtools_config.enabled = enabled
    if mode is not None:
        if mode not in ("dev", "power_user", "hidden"):
            raise HTTPException(400, f"Invalid mode: {mode}")
        _devtools_config.mode = mode
    return _devtools_config


# =============================================================================
# JSON Schema Endpoints - Serve Pydantic schemas for dynamic UI rendering
# =============================================================================

# Schema registry mapping artifact types to their Pydantic models
SCHEMA_REGISTRY: dict[str, type] = {
    "adr": ADRSchema,
    "spec": SPECSchema,
    "plan": PlanSchema,
}


@router.get("/schemas")
async def list_schemas() -> dict[str, Any]:
    """List all available JSON schemas.
    
    Returns:
        Dict with schema names and their metadata.
    """
    schemas = {}
    for name, model_class in SCHEMA_REGISTRY.items():
        schema = model_class.model_json_schema()
        schemas[name] = {
            "title": schema.get("title", name),
            "description": schema.get("description", ""),
            "type": name,
        }
    return {"schemas": schemas}


@router.get("/schemas/{schema_type}")
async def get_schema(schema_type: str) -> dict[str, Any]:
    """Get JSON Schema for a specific artifact type.
    
    This endpoint serves Pydantic-generated JSON Schema that can be used
    by the frontend to dynamically render forms and viewers.
    
    Args:
        schema_type: One of 'adr', 'spec', 'plan'
        
    Returns:
        Full JSON Schema for the artifact type.
    """
    if schema_type not in SCHEMA_REGISTRY:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown schema type: {schema_type}. Available: {list(SCHEMA_REGISTRY.keys())}"
        )
    
    model_class = SCHEMA_REGISTRY[schema_type]
    schema = model_class.model_json_schema()
    
    # Add metadata for frontend consumption
    schema["$schema_type"] = schema_type
    schema["$generated_from"] = model_class.__module__
    
    return schema


# =============================================================================
# ADR Endpoints
# =============================================================================

@router.get("/adrs", response_model=list[ADRSummary])
async def list_adrs() -> list[ADRSummary]:
    """List all ADR files with summary information from all subfolders."""
    if not ADRS_DIR.exists():
        return []

    adrs = []
    # Scan both root and subfolders
    for filepath in sorted(ADRS_DIR.rglob("*.json")):
        # Determine folder (relative to .adrs/)
        relative_path = filepath.relative_to(ADRS_DIR)
        folder = str(relative_path.parent) if relative_path.parent != Path(".") else "root"
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            adrs.append(
                ADRSummary(
                    id=data.get("id", filepath.stem),
                    title=data.get("title", "Untitled"),
                    status=data.get("status", "unknown"),
                    date=data.get("date", ""),
                    scope=data.get("scope", ""),
                    filename=filepath.name,
                    folder=folder,
                )
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Include file with error indication
            adrs.append(
                ADRSummary(
                    id=filepath.stem,
                    title=f"[Error loading: {e}]",
                    status="error",
                    date="",
                    scope="",
                    filename=filepath.name,
                    folder=folder,
                )
            )
    return adrs


@router.get("/adrs/{folder}/{filename}", response_model=ADRContent)
async def get_adr(folder: str, filename: str) -> ADRContent:
    """Get full content of an ADR file from a specific folder."""
    filepath = ADRS_DIR / folder / filename
    if not filepath.exists():
        raise HTTPException(404, f"ADR not found: {folder}/{filename}")

    # Security check: ensure we're reading from within ADRS_DIR
    try:
        filepath.resolve().relative_to(ADRS_DIR.resolve())
    except ValueError:
        raise HTTPException(400, "Invalid folder/filename path")

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            raw_json = f.read()
        content = json.loads(raw_json)
        return ADRContent(filename=filename, content=content, raw_json=raw_json)
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"Invalid JSON in ADR: {e}")


@router.put("/adrs/{folder}/{filename}", response_model=ADRContent)
async def update_adr(folder: str, filename: str, request: ADRUpdateRequest) -> ADRContent:
    """Update an existing ADR file."""
    filepath = ADRS_DIR / folder / filename
    if not filepath.exists():
        raise HTTPException(404, f"ADR not found: {folder}/{filename}")

    # Security check: ensure we're writing within ADRS_DIR
    try:
        filepath.resolve().relative_to(ADRS_DIR.resolve())
    except ValueError:
        raise HTTPException(400, "Invalid folder/filename path")

    # Add/update provenance
    content = request.content
    if "provenance" not in content:
        content["provenance"] = []
    content["provenance"].append(
        {
            "at": datetime.utcnow().strftime("%Y-%m-%d"),
            "by": "DevTools Editor",
            "note": "Updated via DevTools ADR Editor",
        }
    )

    # Write with pretty formatting
    raw_json = json.dumps(content, indent=2, ensure_ascii=False)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(raw_json)
        f.write("\n")

    return ADRContent(filename=filename, content=content, raw_json=raw_json)


@router.post("/adrs", response_model=ADRContent)
async def create_adr(request: SchemaADRCreateRequest) -> ADRContent:
    """Create a new ADR file."""
    # Validate the ADR data first
    try:
        adr_instance = ADRSchema(**request.adr_data)
    except ValidationError as e:
        errors = [f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in e.errors()]
        raise HTTPException(400, f"Invalid ADR data: {'; '.join(errors)}")
    
    # Generate filename from ID
    adr_id = request.adr_data.get("id", "ADR-0000_Untitled")
    filename = f"{adr_id}.json"
    folder_path = ADRS_DIR / request.folder
    folder_path.mkdir(exist_ok=True, parents=True)
    filepath = folder_path / filename

    if filepath.exists():
        raise HTTPException(400, f"ADR already exists: {request.folder}/{filename}")

    # Security check: ensure we're writing within ADRS_DIR
    try:
        filepath.resolve().relative_to(ADRS_DIR.resolve())
    except ValueError:
        raise HTTPException(400, "Invalid folder path")

    # Use validated data
    content = adr_instance.model_dump(mode='json')
    
    # Add creation provenance if not present
    if not content.get("provenance"):
        content["provenance"] = []
    content["provenance"].insert(0, {
        "at": datetime.utcnow().strftime("%Y-%m-%d"),
        "by": "DevTools Editor",
        "note": "Created via DevTools ADR Editor",
    })

    raw_json = json.dumps(content, indent=2, ensure_ascii=False)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(raw_json)
        f.write("\n")

    return ADRContent(filename=filename, content=content, raw_json=raw_json)


@router.post("/adrs/{folder}/{filename}/validate", response_model=ValidationResult)
async def validate_adr(folder: str, filename: str) -> ValidationResult:
    """Validate an ADR file against the Pydantic schema."""
    filepath = ADRS_DIR / folder / filename
    if not filepath.exists():
        raise HTTPException(404, f"ADR not found: {folder}/{filename}")

    errors: list[str] = []
    warnings: list[str] = []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = json.load(f)
    except json.JSONDecodeError as e:
        return ValidationResult(valid=False, errors=[f"Invalid JSON: {e}"], warnings=[])

    # Validate using Pydantic schema
    try:
        ADRSchema(**content)
        return ValidationResult(valid=True, errors=[], warnings=warnings)
    except ValidationError as e:
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append(f"{field}: {error['msg']}")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)


@router.delete("/adrs/{folder}/{filename}")
async def delete_adr(folder: str, filename: str, confirm: bool = Query(False)) -> dict[str, str]:
    """Delete an ADR file (requires confirmation)."""
    if not confirm:
        raise HTTPException(400, "Deletion requires confirm=true query parameter")

    filepath = ADRS_DIR / folder / filename
    if not filepath.exists():
        raise HTTPException(404, f"ADR not found: {folder}/{filename}")

    # Security check: ensure we're deleting from within ADRS_DIR
    try:
        filepath.resolve().relative_to(ADRS_DIR.resolve())
    except ValueError:
        raise HTTPException(400, "Invalid folder/filename path")

    # Move to backup instead of deleting
    backup_dir = ADRS_DIR / ".backup"
    backup_dir.mkdir(exist_ok=True)
    backup_path = backup_dir / f"{filename}.{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.bak"
    filepath.rename(backup_path)

    return {"status": "deleted", "backup": str(backup_path.relative_to(PROJECT_ROOT))}


@router.post("/adrs/validate-field", response_model=ADRFieldValidationResponse)
async def validate_field(request: ADRFieldValidationRequest) -> ADRFieldValidationResponse:
    """Validate a single ADR field in real-time."""
    try:
        # Build a minimal ADR with just this field to test validation
        test_data = {
            "schema_type": "adr",
            "id": request.context.get("id", "ADR-0000_Test"),
            "title": request.context.get("title", "Test"),
            "status": request.context.get("status", "proposed"),
            "date": request.context.get("date", "2024-01-01"),
            "deciders": request.context.get("deciders", "Test"),
            "scope": request.context.get("scope", "core"),
            "context": request.context.get("context", "Test context"),
            "decision_primary": request.context.get("decision_primary", "Test decision"),
        }
        # Update with the field being validated
        test_data[request.field_name] = request.field_value
        
        # Try to validate
        ADRSchema(**test_data)
        return ADRFieldValidationResponse(valid=True, error=None)
    except ValidationError as e:
        # Find error for this specific field
        for error in e.errors():
            if request.field_name in [str(loc) for loc in error["loc"]]:
                return ADRFieldValidationResponse(valid=False, error=error["msg"])
        return ADRFieldValidationResponse(valid=True, error=None)
    except Exception as e:
        return ADRFieldValidationResponse(valid=False, error=str(e))


# =============================================================================
# Workflow Manager Endpoints (ADR-0045, PLAN-001 M1)
# =============================================================================


@router.get("/artifacts", response_model=ArtifactListResponse)
async def list_artifacts(
    artifact_type: ArtifactType | None = Query(None, description="Filter by type"),
    search: str | None = Query(None, description="Filter by title/ID"),
) -> ArtifactListResponse:
    """List workflow artifacts with optional filtering.

    Args:
        artifact_type: Filter by type (optional).
        search: Filter by title/ID (optional).

    Returns:
        ArtifactListResponse with matching artifacts.
    """
    items = scan_artifacts(artifact_type=artifact_type, search=search)
    return ArtifactListResponse(items=items, total=len(items))


@router.get("/artifacts/graph", response_model=GraphResponse)
async def get_artifact_graph() -> GraphResponse:
    """Get the artifact relationship graph.

    Returns:
        GraphResponse with nodes and edges.
    """
    return build_artifact_graph()


@router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str) -> dict[str, Any]:
    """Get a single artifact's content by ID.

    Args:
        artifact_id: The artifact ID (e.g., ADR-0001, DISC-001).

    Returns:
        Dict with artifact metadata and content.
    """
    from gateway.services.workflow_service import get_generated_content

    # Check if this is a generated artifact first
    if "-GEN-" in artifact_id:
        content = get_generated_content(artifact_id)
        if content:
            return {"id": artifact_id, "content": content}
        raise HTTPException(status_code=404, detail=f"Generated artifact {artifact_id} not found")

    # Find the artifact in all scanned artifacts
    artifacts = scan_artifacts()
    artifact = next((a for a in artifacts if a.id == artifact_id), None)

    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")

    file_path = Path(artifact.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact file not found: {file_path}")

    # Read content based on file type
    try:
        with open(file_path, encoding="utf-8") as f:
            raw_content = f.read()

        # Parse JSON for ADR/SPEC, return raw for others
        if artifact.type in (ArtifactType.ADR, ArtifactType.SPEC):
            content = json.loads(raw_content)
        else:
            content = raw_content

        return {
            "id": artifact.id,
            "type": artifact.type.value,
            "title": artifact.title,
            "status": artifact.status.value,
            "file_path": str(file_path),
            "file_format": _get_file_format(file_path).value,
            "content": content,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading artifact: {e}")


@router.post("/artifacts", response_model=ArtifactResponse)
async def create_artifact(request: CreateArtifactRequest) -> ArtifactResponse:
    """Create a new workflow artifact.

    Args:
        request: Creation request with type, title, content.

    Returns:
        ArtifactResponse with created artifact summary.
    """
    from gateway.services.workflow_service import ARTIFACT_DIRECTORIES

    # Determine file path based on artifact type
    base_dir = Path(ARTIFACT_DIRECTORIES.get(request.type, "."))
    
    # Generate artifact ID and filename
    if request.type == ArtifactType.ADR:
        # Find next ADR number
        existing = list(base_dir.rglob("ADR-*.json"))
        numbers = [int(f.stem.split("_")[0].replace("ADR-", "")) for f in existing if f.stem.startswith("ADR-")]
        next_num = max(numbers, default=0) + 1
        slug = request.title.lower().replace(" ", "-").replace("_", "-")[:50]
        artifact_id = f"ADR-{next_num:04d}_{slug}"
        filename = f"{artifact_id}.json"
        file_path = base_dir / "core" / filename
    elif request.type == ArtifactType.DISCUSSION:
        existing = list(base_dir.rglob("DISC-*.md"))
        numbers = [int(f.stem.split("_")[0].replace("DISC-", "")) for f in existing if f.stem.startswith("DISC-")]
        next_num = max(numbers, default=0) + 1
        slug = request.title.lower().replace(" ", "-").replace("_", "-")[:50]
        artifact_id = f"DISC-{next_num:03d}_{slug}"
        filename = f"{artifact_id}.md"
        file_path = base_dir / filename
    elif request.type == ArtifactType.PLAN:
        existing = list(base_dir.rglob("PLAN-*.md"))
        numbers = [int(f.stem.split("_")[0].replace("PLAN-", "")) for f in existing if f.stem.startswith("PLAN-")]
        next_num = max(numbers, default=0) + 1
        slug = request.title.lower().replace(" ", "-").replace("_", "-")[:50]
        artifact_id = f"PLAN-{next_num:03d}_{slug}"
        filename = f"{artifact_id}.md"
        file_path = base_dir / filename
    elif request.type == ArtifactType.SPEC:
        existing = list(base_dir.rglob("SPEC-*.json"))
        numbers = [int(f.stem.split("_")[0].replace("SPEC-", "").replace("SPEC-", "")) for f in existing if "SPEC-" in f.stem]
        next_num = max(numbers, default=0) + 1
        slug = request.title.lower().replace(" ", "-").replace("_", "-")[:50]
        artifact_id = f"SPEC-{next_num:04d}_{slug}"
        filename = f"{artifact_id}.json"
        file_path = base_dir / "core" / filename
    else:
        slug = request.title.lower().replace(" ", "-").replace("_", "-")[:50]
        artifact_id = slug
        filename = f"{slug}.py"
        file_path = base_dir / filename

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate content based on type
    if request.type in (ArtifactType.ADR, ArtifactType.SPEC):
        content = {
            "id": artifact_id,
            "title": request.title,
            "status": "draft",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "context": request.content or "",
            "decision_primary": "",
            "consequences": [],
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)
    else:
        content = f"# {request.title}\n\n{request.content or ''}\n"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    artifact = ArtifactSummary(
        id=artifact_id,
        type=request.type,
        title=request.title,
        status=ArtifactStatus.DRAFT,
        file_path=str(file_path),
    )
    return ArtifactResponse(artifact=artifact, message=f"Created {artifact_id}")


@router.put("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def update_artifact(
    artifact_id: str,
    request: UpdateArtifactRequest,
) -> ArtifactResponse:
    """Update an existing workflow artifact.

    Args:
        artifact_id: ID of artifact to update.
        request: Update request with optional fields.

    Returns:
        ArtifactResponse with updated artifact summary.
    """
    # Find the artifact
    artifacts = scan_artifacts()
    artifact = next((a for a in artifacts if a.id == artifact_id), None)

    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")

    file_path = Path(artifact.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact file not found: {file_path}")

    try:
        # Handle content update
        if request.content is not None:
            if artifact.type in (ArtifactType.ADR, ArtifactType.SPEC):
                # For JSON files, merge or replace content
                if isinstance(request.content, dict):
                    content = request.content
                else:
                    # Try to parse as JSON
                    try:
                        content = json.loads(request.content)
                    except json.JSONDecodeError:
                        raise HTTPException(status_code=400, detail="Invalid JSON content for ADR/SPEC")
                
                # Update status and title if provided
                if request.status:
                    content["status"] = request.status.value
                if request.title:
                    content["title"] = request.title
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(content, f, indent=2)
            else:
                # For markdown/text files, write content directly
                content = request.content if isinstance(request.content, str) else json.dumps(request.content, indent=2)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

        updated_artifact = ArtifactSummary(
            id=artifact_id,
            type=artifact.type,
            title=request.title or artifact.title,
            status=request.status or artifact.status,
            file_path=str(file_path),
        )
        return ArtifactResponse(artifact=updated_artifact, message=f"Updated {artifact_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating artifact: {e}")


@router.delete("/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def delete_artifact(
    artifact_id: str,
    backup: bool = Query(True, description="Create backup before deleting"),
) -> ArtifactResponse:
    """Delete a workflow artifact.

    Args:
        artifact_id: ID of artifact to delete.
        backup: If True, create backup before deleting.

    Returns:
        ArtifactResponse confirming deletion.
    """
    import shutil

    # Find the artifact
    artifacts = scan_artifacts()
    artifact = next((a for a in artifacts if a.id == artifact_id), None)

    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")

    file_path = Path(artifact.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Artifact file not found: {file_path}")

    try:
        # Create backup if requested (per ADR-0002: Never delete artifacts on unlock)
        if backup:
            backup_dir = Path(".backups") / datetime.now().strftime("%Y-%m-%d")
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f"{file_path.name}.{datetime.now().strftime('%H%M%S')}.bak"
            shutil.copy2(file_path, backup_path)

        # Delete the file
        file_path.unlink()

        deleted_artifact = ArtifactSummary(
            id=artifact_id,
            type=artifact.type,
            title=artifact.title,
            status=ArtifactStatus.DEPRECATED,
            file_path=str(file_path),
        )
        backup_msg = f" (backup at {backup_path})" if backup else ""
        return ArtifactResponse(artifact=deleted_artifact, message=f"Deleted {artifact_id}{backup_msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting artifact: {e}")


# =============================================================================
# Workflow Mode Endpoints (ADR-0045, PLAN-001 M10)
# =============================================================================


@router.post("/workflows", response_model=WorkflowResponse)
async def create_workflow_endpoint(request: CreateWorkflowRequest) -> WorkflowResponse:
    """Create a new workflow session.

    Args:
        request: Workflow creation request.

    Returns:
        WorkflowResponse with created workflow state.
    """
    workflow = create_workflow(
        mode=request.mode,
        scenario=request.scenario,
        title=request.title,
    )
    return WorkflowResponse(workflow=workflow, message=f"Created workflow {workflow.id}")


@router.get("/workflows/{workflow_id}/status", response_model=WorkflowResponse)
async def get_workflow_status_endpoint(workflow_id: str) -> WorkflowResponse:
    """Get current status of a workflow.

    Args:
        workflow_id: The workflow ID.

    Returns:
        WorkflowResponse with current state.
    """
    workflow = get_workflow_status(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    return WorkflowResponse(workflow=workflow)


@router.post("/workflows/{workflow_id}/advance", response_model=WorkflowResponse)
async def advance_workflow_endpoint(workflow_id: str) -> WorkflowResponse:
    """Advance workflow to the next stage.

    Args:
        workflow_id: The workflow ID.

    Returns:
        WorkflowResponse with updated state.
    """
    new_stage = advance_workflow(workflow_id)
    if new_stage is None:
        raise HTTPException(status_code=400, detail=f"Cannot advance workflow {workflow_id}")
    workflow = get_workflow_status(workflow_id)
    return WorkflowResponse(workflow=workflow, message=f"Advanced to {new_stage.value}")


@router.get("/artifacts/{artifact_id}/prompt", response_model=PromptResponse)
async def get_artifact_prompt(
    artifact_id: str,
    target_type: ArtifactType = Query(..., description="Target artifact type to create"),
) -> PromptResponse:
    """Get context-aware AI prompt for creating next artifact.

    Args:
        artifact_id: Source artifact ID.
        target_type: Target artifact type.

    Returns:
        PromptResponse with generated prompt.
    """
    return generate_prompt(artifact_id=artifact_id, target_type=target_type)


# =============================================================================
# AI-Full Mode Endpoints (M12)
# =============================================================================


@router.post("/artifacts/generate", response_model=GenerationResponse)
async def generate_artifacts_endpoint(request: GenerationRequest) -> GenerationResponse:
    """Generate artifact content using AI-Full mode.

    Args:
        request: Generation request with workflow and target types.

    Returns:
        GenerationResponse with created artifacts.
    """
    artifacts = []
    errors = []

    for target_type in request.target_types:
        try:
            content = generate_artifact_content(
                artifact_type=target_type,
                title=request.context.get("title", "Generated"),
                description=request.context.get("description", ""),
            )
            artifact = ArtifactSummary(
                id=f"{target_type.value.upper()}-GEN-{request.workflow_id}",
                type=target_type,
                title=request.context.get("title", "Generated"),
                status=ArtifactStatus.DRAFT,
                file_path=f"generated/{target_type.value}/{request.workflow_id}.json",
            )
            artifacts.append(artifact)
        except Exception as e:
            errors.append(f"Failed to generate {target_type.value}: {e}")

    from shared.contracts.devtools.workflow import GenerationStatus
    status = GenerationStatus.COMPLETED if not errors else GenerationStatus.FAILED
    return GenerationResponse(artifacts=artifacts, status=status, errors=errors)


class GenerateAllRequest(BaseModel):
    """Request body for generate-all endpoint."""
    use_reranking: bool = True  # UI toggle for LLM re-ranking


@router.post("/workflows/{workflow_id}/generate-all", response_model=GenerationResponse)
async def generate_all_endpoint(
    workflow_id: str,
    request: GenerateAllRequest | None = None,
) -> GenerationResponse:
    """Generate all artifacts for a workflow (AI-Full mode).

    Args:
        workflow_id: The workflow ID.
        request: Optional request body with generation options.

    Returns:
        GenerationResponse with all created artifacts.
    """
    workflow = get_workflow_status(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")

    use_reranking = request.use_reranking if request else True

    return generate_full_workflow(
        workflow_id=workflow_id,
        title=workflow.title,
        description="",
        use_reranking=use_reranking,
    )


# =============================================================================
# LLM Health Check
# =============================================================================


class ModelInfoResponse(BaseModel):
    """Model information for frontend."""
    id: str
    name: str
    context_window: int
    rpm: int
    input_price: float
    output_price: float
    category: str
    reasoning: bool = False


class LLMHealthResponse(BaseModel):
    """Response for LLM health check."""
    status: str
    message: str
    model: str | None = None
    available: bool = False
    models: list[ModelInfoResponse] = []


@router.get("/llm/health", response_model=LLMHealthResponse)
async def get_llm_health(refresh: bool = False) -> LLMHealthResponse:
    """Check if the LLM service (xAI) is available.

    Args:
        refresh: Force refresh the health check cache.

    Returns:
        LLMHealthResponse with status and availability.
    """
    from gateway.services.llm_service import (
        check_health,
        LLMStatus,
        get_available_models,
        get_current_model,
    )

    health = check_health(force_refresh=refresh)
    models = get_available_models()

    return LLMHealthResponse(
        status=health.status.value,
        message=health.message,
        model=get_current_model(),
        available=health.status == LLMStatus.AVAILABLE,
        models=[
            ModelInfoResponse(
                id=m.id,
                name=m.name,
                context_window=m.context_window,
                rpm=m.rpm,
                input_price=m.input_price,
                output_price=m.output_price,
                category=m.category,
                reasoning=m.reasoning,
            )
            for m in models
        ],
    )


class SetModelRequest(BaseModel):
    """Request to set the current model."""
    model_id: str


class SetModelResponse(BaseModel):
    """Response after setting model."""
    success: bool
    model_id: str
    message: str


class LLMUsageStats(BaseModel):
    """Usage statistics for LLM API calls."""
    total_calls: int
    total_cost: float
    total_input_tokens: int
    total_output_tokens: int


@router.post("/llm/model", response_model=SetModelResponse)
async def set_llm_model(request: SetModelRequest) -> SetModelResponse:
    """Set the current LLM model.

    Args:
        request: Request with model_id to use.

    Returns:
        SetModelResponse with success status.
    """
    from gateway.services.llm_service import set_current_model, get_model_info

    success = set_current_model(request.model_id)
    model_info = get_model_info(request.model_id)

    if success and model_info:
        return SetModelResponse(
            success=True,
            model_id=request.model_id,
            message=f"Model set to {model_info.name}",
        )
    else:
        return SetModelResponse(
            success=False,
            model_id=request.model_id,
            message=f"Unknown model: {request.model_id}",
        )


@router.get("/llm/usage", response_model=LLMUsageStats)
async def get_llm_usage() -> LLMUsageStats:
    """Get LLM API usage statistics.

    Returns:
        LLMUsageStats with total calls, tokens, and cost.
    """
    from gateway.services.llm_service import get_llm_usage_stats

    stats = get_llm_usage_stats()
    return LLMUsageStats(**stats)
