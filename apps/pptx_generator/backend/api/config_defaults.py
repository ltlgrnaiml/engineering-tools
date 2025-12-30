"""API endpoints for loading configuration defaults.

Per ADR-0032: All errors use ErrorResponse contract via errors.py helper.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml
from fastapi import APIRouter, status
from pydantic import BaseModel

from apps.pptx_generator.backend.api.errors import (
    raise_not_found,
    raise_validation_error,
    raise_internal_error,
    raise_conflict_error,
)

from apps.pptx_generator.backend.models.drm import AggregationType, MappingSourceType
from apps.pptx_generator.backend.models.mapping_manifest import ContextMapping, MetricMapping

router = APIRouter()
logger = logging.getLogger(__name__)


class SaveConfigRequest(BaseModel):
    """Request body for saving config mappings."""

    context_mappings: list[dict[str, Any]] | None = None
    metrics_mappings: list[dict[str, Any]] | None = None
    filename: str | None = None
    overwrite: bool = False


def _get_config_dir() -> Path:
    """Get the absolute path to the config directory."""
    # Get the absolute path to the pptx_generator app directory
    app_root = Path(__file__).parent.parent.parent.resolve()
    return app_root / "config"


@router.get("/config/defaults")
async def get_config_defaults() -> dict[str, Any]:
    """Load test defaults from configuration file.

    Returns:
        Dict with context_mappings and metrics_mappings.
    """
    config_dir = _get_config_dir()
    config_path = config_dir / "example_config_production.yaml"

    if not config_path.exists():
        # Try custom config as fallback
        config_path = config_dir / "custom_config.yaml"

    if not config_path.exists():
        raise_not_found("ConfigFile", f"Configuration file not found in {config_dir}")

    try:
        with config_path.open() as f:
            config = yaml.safe_load(f)

        test_defaults = config.get("test_defaults", {})

        if not test_defaults:
            raise_not_found("ConfigSection", "No test_defaults section found in config")

        # Convert to API format
        context_mappings = []
        for ctx in test_defaults.get("context_mappings", []):
            context_mappings.append(
                {
                    "context_name": ctx["context_name"],
                    "source_type": ctx["source_type"],
                    "source_column": ctx.get("source_column"),
                    "regex_pattern": ctx.get("regex_pattern"),
                    "default_value": ctx.get("default_value"),
                    "description": ctx.get("description", ""),
                }
            )

        metrics_mappings = []
        for metric in test_defaults.get("metrics_mappings", []):
            metrics_mappings.append(
                {
                    "metric_name": metric["metric_name"],
                    "source_column": metric["source_column"],
                    "rename_to": metric.get("rename_to"),
                    "aggregation_semantics": metric["aggregation_semantics"],
                    "data_type": metric.get("data_type", "float"),
                    "unit": metric.get("unit"),
                    "description": metric.get("description", ""),
                }
            )

        logger.info(
            f"Loaded {len(context_mappings)} context and {len(metrics_mappings)} metrics defaults"
        )

        return {
            "context_mappings": context_mappings,
            "metrics_mappings": metrics_mappings,
            "project_name": test_defaults.get("project_name", "Test Project"),
            "template_file": test_defaults.get("template_file"),
            "data_file": test_defaults.get("data_file"),
        }

    except Exception as e:
        logger.error(f"Failed to load config defaults: {e}", exc_info=True)
        raise_internal_error(f"Failed to load config defaults: {str(e)}", e)


def _get_or_create_manifest(project_id: UUID):
    """Get existing manifest or create new one for a project."""
    from apps.pptx_generator.backend.api.projects import projects_db
    from apps.pptx_generator.backend.api.requirements import mapping_manifests_db
    from apps.pptx_generator.backend.models.mapping_manifest import MappingManifest

    if project_id not in projects_db:
        raise_not_found("Project", str(project_id))

    project = projects_db[project_id]
    manifest_id = project.context_mapping_id or project.metrics_mapping_id

    if manifest_id and manifest_id in mapping_manifests_db:
        manifest = mapping_manifests_db[manifest_id]
    else:
        manifest = MappingManifest(project_id=project_id)
        mapping_manifests_db[manifest.id] = manifest
        project.context_mapping_id = manifest.id
        project.metrics_mapping_id = manifest.id

    return manifest, project


@router.post("/apply-defaults/{project_id}/contexts")
async def apply_context_defaults(project_id: UUID) -> dict[str, Any]:
    """Apply only context defaults to a project.

    Args:
        project_id: Project ID to apply defaults to.

    Returns:
        Success message with applied context mappings.
    """
    defaults = await get_config_defaults()
    manifest, _ = _get_or_create_manifest(project_id)

    manifest.context_mappings = [
        ContextMapping(
            context_name=ctx["context_name"],
            source_type=MappingSourceType(ctx["source_type"]),
            source_column=ctx.get("source_column"),
            regex_pattern=ctx.get("regex_pattern"),
            default_value=ctx.get("default_value"),
            description=ctx.get("description"),
        )
        for ctx in defaults["context_mappings"]
    ]

    logger.info(
        f"Applied context defaults to project {project_id}: {len(manifest.context_mappings)} contexts"
    )

    return {
        "message": "Context defaults applied successfully",
        "context_mappings_count": len(manifest.context_mappings),
        "context_mappings": [m.model_dump() for m in manifest.context_mappings],
    }


@router.post("/apply-defaults/{project_id}/metrics")
async def apply_metric_defaults(project_id: UUID) -> dict[str, Any]:
    """Apply only metric defaults to a project.

    Args:
        project_id: Project ID to apply defaults to.

    Returns:
        Success message with applied metric mappings.
    """
    defaults = await get_config_defaults()
    manifest, _ = _get_or_create_manifest(project_id)

    manifest.metrics_mappings = [
        MetricMapping(
            metric_name=metric["metric_name"],
            source_column=metric["source_column"],
            rename_to=metric.get("rename_to"),
            aggregation_semantics=AggregationType(metric["aggregation_semantics"]),
            data_type=metric.get("data_type", "float"),
            unit=metric.get("unit"),
            description=metric.get("description"),
        )
        for metric in defaults["metrics_mappings"]
    ]

    logger.info(
        f"Applied metric defaults to project {project_id}: {len(manifest.metrics_mappings)} metrics"
    )

    return {
        "message": "Metric defaults applied successfully",
        "metrics_mappings_count": len(manifest.metrics_mappings),
        "metrics_mappings": [m.model_dump() for m in manifest.metrics_mappings],
    }


@router.post("/apply-defaults/{project_id}/all")
async def apply_all_defaults(project_id: UUID) -> dict[str, Any]:
    """Apply both context and metric defaults to a project.

    Args:
        project_id: Project ID to apply defaults to.

    Returns:
        Success message with all applied mappings.
    """
    defaults = await get_config_defaults()
    manifest, _ = _get_or_create_manifest(project_id)

    manifest.context_mappings = [
        ContextMapping(
            context_name=ctx["context_name"],
            source_type=MappingSourceType(ctx["source_type"]),
            source_column=ctx.get("source_column"),
            regex_pattern=ctx.get("regex_pattern"),
            default_value=ctx.get("default_value"),
            description=ctx.get("description"),
        )
        for ctx in defaults["context_mappings"]
    ]

    manifest.metrics_mappings = [
        MetricMapping(
            metric_name=metric["metric_name"],
            source_column=metric["source_column"],
            rename_to=metric.get("rename_to"),
            aggregation_semantics=AggregationType(metric["aggregation_semantics"]),
            data_type=metric.get("data_type", "float"),
            unit=metric.get("unit"),
            description=metric.get("description"),
        )
        for metric in defaults["metrics_mappings"]
    ]

    logger.info(
        f"Applied all defaults to project {project_id}: "
        f"{len(manifest.context_mappings)} contexts, {len(manifest.metrics_mappings)} metrics"
    )

    return {
        "message": "All defaults applied successfully",
        "context_mappings_count": len(manifest.context_mappings),
        "metrics_mappings_count": len(manifest.metrics_mappings),
        "context_mappings": [m.model_dump() for m in manifest.context_mappings],
        "metrics_mappings": [m.model_dump() for m in manifest.metrics_mappings],
    }


@router.post("/apply-defaults/{project_id}")
async def apply_defaults_to_project(project_id: UUID) -> dict[str, Any]:
    """Apply config defaults to a project's mappings (combined endpoint).

    Args:
        project_id: Project ID to apply defaults to.

    Returns:
        Success message with applied mappings.
    """
    result = await apply_all_defaults(project_id)

    # Add manifest for backward compatibility
    manifest, _ = _get_or_create_manifest(project_id)
    result["manifest"] = manifest.model_dump()

    return result


@router.post("/config/save")
async def save_config_mappings(request: SaveConfigRequest) -> dict[str, Any]:
    """Save mapping configurations to a new or existing config file.

    Args:
        request: SaveConfigRequest with mappings and filename.

    Returns:
        Success message with saved file path.
    """
    config_dir = _get_config_dir()
    config_dir.mkdir(exist_ok=True)

    # Determine filename
    if request.filename:
        filename = request.filename
        if not filename.endswith(".yaml"):
            filename = f"{filename}.yaml"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"config_custom_{timestamp}.yaml"

    config_path = config_dir / filename

    # Check if file exists and overwrite is not allowed
    if config_path.exists() and not request.overwrite:
        raise_conflict_error(f"Config file '{filename}' already exists. Set overwrite=true to replace it.")

    # Load existing config as base or create new one
    base_config_path = config_dir / "example_config_production.yaml"
    if base_config_path.exists():
        with base_config_path.open() as f:
            config = yaml.safe_load(f)
    else:
        config = {}

    # Update test_defaults with new mappings
    if "test_defaults" not in config:
        config["test_defaults"] = {}

    if request.context_mappings is not None:
        config["test_defaults"]["context_mappings"] = request.context_mappings

    if request.metrics_mappings is not None:
        config["test_defaults"]["metrics_mappings"] = request.metrics_mappings

    # Write to file
    try:
        with config_path.open("w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        logger.info(f"Saved config to {config_path}")

        return {
            "message": "Config saved successfully",
            "filename": filename,
            "filepath": str(config_path),
            "context_mappings_count": len(request.context_mappings) if request.context_mappings else 0,
            "metrics_mappings_count": len(request.metrics_mappings) if request.metrics_mappings else 0,
        }
    except Exception as e:
        logger.error(f"Failed to save config: {e}", exc_info=True)
        raise_internal_error(f"Failed to save config: {str(e)}", e)


@router.get("/config/list")
async def list_config_files() -> dict[str, Any]:
    """List available config files with metadata.

    Returns:
        List of config file names with metadata.
    """
    config_dir = _get_config_dir()
    if not config_dir.exists():
        logger.warning(f"Config directory not found: {config_dir}")
        return {"files": [], "count": 0}

    files_info = []
    for f in config_dir.glob("*.yaml"):
        try:
            stat = f.stat()
            files_info.append({
                "name": f.name,
                "path": str(f),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })
        except Exception:
            files_info.append({"name": f.name, "path": str(f)})

    # Sort by name
    files_info.sort(key=lambda x: x["name"])
    return {"files": files_info, "count": len(files_info)}


@router.get("/config/load/{filename:path}")
async def load_config_file(filename: str) -> dict[str, Any]:
    """Load and return the contents of a specific config file.

    Args:
        filename: Name of the config file to load.

    Returns:
        Full config file contents with validation status.
    """
    config_dir = _get_config_dir()
    config_path = config_dir / filename

    if not config_path.exists():
        raise_not_found("ConfigFile", f"Config file '{filename}' not found")

    try:
        with config_path.open() as f:
            config = yaml.safe_load(f)

        # Validate required sections
        validation = {
            "has_job_contexts": "job_contexts" in config,
            "has_metrics": "metrics" in config,
            "has_defaults": "defaults" in config,
            "has_test_defaults": "test_defaults" in config,
            "is_valid": True,
            "errors": [],
        }

        # Check for required fields
        if not validation["has_job_contexts"]:
            validation["errors"].append("Missing 'job_contexts' section")
            validation["is_valid"] = False

        logger.info(f"Loaded config file: {filename}, valid: {validation['is_valid']}")

        return {
            "filename": filename,
            "filepath": str(config_path),
            "config": config,
            "validation": validation,
        }

    except yaml.YAMLError as e:
        raise_validation_error(f"Invalid YAML in config file: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}", exc_info=True)
        raise_internal_error(f"Failed to load config: {str(e)}", e)


@router.put("/config/save-full")
async def save_full_config(request: dict[str, Any]) -> dict[str, Any]:
    """Save a full config file (not just mappings).

    Args:
        request: Dict with 'filename', 'config', and optional 'overwrite'.

    Returns:
        Success message with saved file path.
    """
    config_dir = _get_config_dir()
    config_dir.mkdir(exist_ok=True)

    filename = request.get("filename")
    config = request.get("config")
    overwrite = request.get("overwrite", False)

    if not filename:
        raise_validation_error("Filename is required", field="filename")

    if not config:
        raise_validation_error("Config content is required", field="config")

    if not filename.endswith(".yaml"):
        filename = f"{filename}.yaml"

    config_path = config_dir / filename

    # Check if file exists and overwrite is not allowed
    if config_path.exists() and not overwrite:
        raise_conflict_error(f"Config file '{filename}' already exists. Set overwrite=true to replace it.")

    try:
        with config_path.open("w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        logger.info(f"Saved full config to {config_path}")

        return {
            "message": "Config saved successfully",
            "filename": filename,
            "filepath": str(config_path),
        }
    except Exception as e:
        logger.error(f"Failed to save config: {e}", exc_info=True)
        raise_internal_error(f"Failed to save config: {str(e)}", e)
