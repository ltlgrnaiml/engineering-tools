"""API endpoints for domain configuration.

Per ADR-0031: All errors use ErrorResponse contract via errors.py helper.
"""

import logging
from typing import Any

from fastapi import APIRouter

from apps.pptx_generator.backend.api.errors import raise_internal_error
from apps.pptx_generator.backend.core.domain_config_service import (
    ConfigurationError,
    get_domain_config,
)

router = APIRouter(tags=["config"])
logger = logging.getLogger(__name__)


@router.get("")
async def get_config() -> dict[str, Any]:
    """Get the full domain configuration."""
    try:
        config = get_domain_config()
        return config.model_dump()
    except ConfigurationError as e:
        logger.error(f"Failed to load configuration: {e}")
        raise_internal_error(f"Failed to load configuration: {str(e)}", e)


@router.get("/job-contexts")
async def get_job_contexts() -> dict[str, Any]:
    """Get job contexts configuration."""
    try:
        config = get_domain_config()
        return {
            "job_contexts": [ctx.model_dump() for ctx in config.job_contexts],
            "primary_job_context": config.primary_job_context,
        }
    except ConfigurationError as e:
        logger.error(f"Failed to load configuration: {e}")
        raise_internal_error(f"Failed to load job contexts: {str(e)}", e)


@router.get("/plotting")
async def get_plotting_config() -> dict[str, Any]:
    """Get plotting configuration."""
    try:
        config = get_domain_config()
        return config.plotting.model_dump()
    except ConfigurationError as e:
        logger.error(f"Failed to load configuration: {e}")
        raise_internal_error(f"Failed to load plotting config: {str(e)}", e)


@router.get("/shape-naming")
async def get_shape_naming_config() -> dict[str, Any]:
    """Get shape naming configuration."""
    try:
        config = get_domain_config()
        return config.shape_naming.model_dump()
    except ConfigurationError as e:
        logger.error(f"Failed to load configuration: {e}")
        raise_internal_error(f"Failed to load shape naming config: {str(e)}", e)


@router.get("/metrics")
async def get_metrics_config() -> dict[str, Any]:
    """Get metrics configuration."""
    try:
        config = get_domain_config()
        return config.metrics.model_dump()
    except ConfigurationError as e:
        logger.error(f"Failed to load configuration: {e}")
        raise_internal_error(f"Failed to load metrics config: {str(e)}", e)


@router.get("/defaults")
async def get_defaults_config() -> dict[str, Any]:
    """Get renderer defaults configuration."""
    try:
        config = get_domain_config()
        return config.defaults.model_dump()
    except ConfigurationError as e:
        logger.error(f"Failed to load configuration: {e}")
        raise_internal_error(f"Failed to load defaults config: {str(e)}", e)
