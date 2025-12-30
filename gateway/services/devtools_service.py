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
    ArtifactCreateRequest,
    ArtifactCreateResponse,
    ArtifactDeleteRequest,
    ArtifactDeleteResponse,
    ArtifactGraphResponse,
    ArtifactListResponse,
    ArtifactReadResponse,
    ArtifactSummary,
    ArtifactStatus,
    ArtifactType,
    ArtifactUpdateRequest,
    ArtifactUpdateResponse,
)
from gateway.services.workflow_service import (
    build_artifact_graph,
    scan_artifacts,
)

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


# =============================================================================
# Workflow Artifact Endpoints
# =============================================================================


@router.get("/artifacts", response_model=ArtifactListResponse)
async def list_artifacts(
    type: ArtifactType | None = Query(None, description="Filter by artifact type"),
    search: str | None = Query(None, description="Text search filter"),
) -> ArtifactListResponse:
    """List all workflow artifacts with optional filtering.
    
    GET /api/devtools/artifacts
    """
    artifacts = scan_artifacts(artifact_type=type, search=search)
    unique_types = list({a.type for a in artifacts})
    return ArtifactListResponse(
        items=artifacts,
        total=len(artifacts),
        types=unique_types,
    )


@router.get("/artifacts/graph", response_model=ArtifactGraphResponse)
async def get_artifact_graph() -> ArtifactGraphResponse:
    """Get artifact relationship graph with nodes and edges.
    
    GET /api/devtools/artifacts/graph
    """
    nodes, edges = build_artifact_graph()
    return ArtifactGraphResponse(
        nodes=nodes,
        edges=edges,
        node_count=len(nodes),
        edge_count=len(edges),
    )


@router.post("/artifacts", response_model=ArtifactCreateResponse)
async def create_artifact(request: ArtifactCreateRequest) -> ArtifactCreateResponse:
    """Create a new workflow artifact.
    
    POST /api/devtools/artifacts
    """
    # Determine target directory and file extension
    directory = {
        ArtifactType.DISCUSSION: PROJECT_ROOT / ".discussions",
        ArtifactType.ADR: PROJECT_ROOT / ".adrs",
        ArtifactType.SPEC: PROJECT_ROOT / "docs" / "specs",
        ArtifactType.PLAN: PROJECT_ROOT / ".plans",
        ArtifactType.CONTRACT: PROJECT_ROOT / "shared" / "contracts",
    }.get(request.type)

    if not directory:
        return ArtifactCreateResponse(
            success=False,
            message=f"Unknown artifact type: {request.type}",
        )

    directory.mkdir(parents=True, exist_ok=True)

    # Generate filename
    if request.file_path:
        filepath = PROJECT_ROOT / request.file_path
    else:
        ext = ".json" if request.type in (ArtifactType.ADR, ArtifactType.SPEC) else ".md"
        safe_title = request.title.replace(" ", "-").replace("/", "-")[:50]
        filename = f"{safe_title}{ext}"
        filepath = directory / filename

    # Security check
    try:
        filepath.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return ArtifactCreateResponse(
            success=False,
            message="Invalid file path - outside project root",
        )

    if filepath.exists():
        return ArtifactCreateResponse(
            success=False,
            message=f"File already exists: {filepath.relative_to(PROJECT_ROOT)}",
        )

    # Write content
    try:
        if isinstance(request.content, dict):
            content_str = json.dumps(request.content, indent=2, ensure_ascii=False)
        else:
            content_str = request.content

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content_str)
            if not content_str.endswith("\n"):
                f.write("\n")

        rel_path = str(filepath.relative_to(PROJECT_ROOT))
        artifact = ArtifactSummary(
            id=filepath.stem,
            type=request.type,
            title=request.title,
            status=ArtifactStatus.DRAFT,
            file_path=rel_path,
            created_date=datetime.utcnow().strftime("%Y-%m-%d"),
            updated_date=None,
        )
        return ArtifactCreateResponse(
            success=True,
            artifact=artifact,
            file_path=rel_path,
            message=f"Created {request.type.value}: {rel_path}",
        )
    except OSError as e:
        return ArtifactCreateResponse(
            success=False,
            message=f"Failed to create file: {e}",
        )


@router.put("/artifacts", response_model=ArtifactUpdateResponse)
async def update_artifact(request: ArtifactUpdateRequest) -> ArtifactUpdateResponse:
    """Update an existing workflow artifact.
    
    PUT /api/devtools/artifacts
    """
    filepath = PROJECT_ROOT / request.file_path

    # Security check
    try:
        filepath.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return ArtifactUpdateResponse(
            success=False,
            message="Invalid file path - outside project root",
        )

    if not filepath.exists():
        return ArtifactUpdateResponse(
            success=False,
            message=f"File not found: {request.file_path}",
        )

    # Create backup if requested
    backup_path = None
    if request.create_backup:
        backup_dir = filepath.parent / ".backup"
        backup_dir.mkdir(exist_ok=True)
        backup_filename = f"{filepath.stem}.{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.bak"
        backup_path = backup_dir / backup_filename
        try:
            import shutil
            shutil.copy2(filepath, backup_path)
        except OSError:
            pass  # Non-fatal if backup fails

    # Write updated content
    try:
        if isinstance(request.content, dict):
            content_str = json.dumps(request.content, indent=2, ensure_ascii=False)
        else:
            content_str = request.content

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content_str)
            if not content_str.endswith("\n"):
                f.write("\n")

        # Re-scan to get updated artifact summary
        artifacts = scan_artifacts()
        artifact = next((a for a in artifacts if a.file_path == request.file_path), None)

        return ArtifactUpdateResponse(
            success=True,
            artifact=artifact,
            backup_path=str(backup_path.relative_to(PROJECT_ROOT)) if backup_path else None,
            message=f"Updated: {request.file_path}",
        )
    except OSError as e:
        return ArtifactUpdateResponse(
            success=False,
            message=f"Failed to update file: {e}",
        )


@router.delete("/artifacts", response_model=ArtifactDeleteResponse)
async def delete_artifact(request: ArtifactDeleteRequest) -> ArtifactDeleteResponse:
    """Delete a workflow artifact (moves to backup by default).
    
    DELETE /api/devtools/artifacts
    """
    filepath = PROJECT_ROOT / request.file_path

    # Security check
    try:
        filepath.resolve().relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return ArtifactDeleteResponse(
            success=False,
            message="Invalid file path - outside project root",
        )

    if not filepath.exists():
        return ArtifactDeleteResponse(
            success=False,
            message=f"File not found: {request.file_path}",
        )

    try:
        if request.permanent:
            filepath.unlink()
            return ArtifactDeleteResponse(
                success=True,
                message=f"Permanently deleted: {request.file_path}",
            )
        else:
            # Move to backup
            backup_dir = filepath.parent / ".backup"
            backup_dir.mkdir(exist_ok=True)
            backup_filename = f"{filepath.stem}.{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.deleted"
            backup_path = backup_dir / backup_filename
            filepath.rename(backup_path)
            return ArtifactDeleteResponse(
                success=True,
                backup_path=str(backup_path.relative_to(PROJECT_ROOT)),
                message=f"Moved to backup: {request.file_path}",
            )
    except OSError as e:
        return ArtifactDeleteResponse(
            success=False,
            message=f"Failed to delete file: {e}",
        )
