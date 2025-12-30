"""DevTools Service - API endpoints for developer/power-user utilities.

This service provides endpoints for managing ADRs, config files, and other
development artifacts. Access is controlled by runtime flags.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError

from shared.contracts.adr_schema import (
    ADRCreateRequest as SchemaADRCreateRequest,
    ADRFieldValidationRequest,
    ADRFieldValidationResponse,
    ADRSchema,
)
from shared.contracts.devtools.workflow import (
    ArtifactType,
    ArtifactListResponse,
    ArtifactGraphResponse,
    ArtifactCreateRequest,
    ArtifactCreateResponse,
    ArtifactDeleteResponse,
)
from gateway.services import workflow_service

router = APIRouter()

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


# === Workflow Artifact Endpoints ===

@router.get("/artifacts", response_model=ArtifactListResponse)
async def list_artifacts(
    type: ArtifactType | None = Query(None, description="Filter by artifact type"),
    search: str | None = Query(None, description="Search text in title"),
) -> ArtifactListResponse:
    """List all workflow artifacts.

    Args:
        type: Optional filter by artifact type.
        search: Optional text search in title.

    Returns:
        List of artifacts with total count.
    """
    return await workflow_service.scan_artifacts(artifact_type=type, search=search)


@router.get("/artifacts/graph", response_model=ArtifactGraphResponse)
async def get_artifact_graph(
    focus: str | None = Query(None, description="Artifact ID to center graph on"),
    depth: int = Query(2, ge=1, le=5, description="Levels of relationships to include"),
) -> ArtifactGraphResponse:
    """Get artifact relationship graph.

    Args:
        focus: Optional artifact ID to center graph on.
        depth: How many levels of relationships to include.

    Returns:
        Graph with nodes and edges for visualization.
    """
    return await workflow_service.get_artifact_graph(focus=focus, depth=depth)


@router.post("/artifacts", response_model=ArtifactCreateResponse)
async def create_artifact(
    request: ArtifactCreateRequest,
) -> ArtifactCreateResponse:
    """Create a new workflow artifact.

    Args:
        request: Artifact creation request.

    Returns:
        Created artifact with file path.
    """
    artifact, path = await workflow_service.create_artifact(
        artifact_type=request.type,
        title=request.title,
        content=request.content,
    )
    return ArtifactCreateResponse(artifact=artifact, path=path)


@router.delete("/artifacts/{artifact_type}/{artifact_id}", response_model=ArtifactDeleteResponse)
async def delete_artifact(
    artifact_type: ArtifactType = Query(..., description="Artifact type"),
    artifact_id: str = Query(..., description="Artifact ID"),
) -> ArtifactDeleteResponse:
    """Soft delete an artifact (moves to .backup/).

    Args:
        artifact_type: Type of artifact.
        artifact_id: ID of artifact to delete.

    Returns:
        Deletion result with backup path.
    """
    success, backup_path = await workflow_service.delete_artifact(
        artifact_type=artifact_type,
        artifact_id=artifact_id,
    )
    return ArtifactDeleteResponse(success=success, backup_path=backup_path)
