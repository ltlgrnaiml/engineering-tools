"""Main FastAPI application entry point.

Per ADR-0029: Tool-specific routes use /v1/ prefix internally.
Gateway mounts this app at /api/pptx, yielding /api/pptx/v1/{resource}.
Per ADR-0031: All errors use ErrorResponse contract.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.pptx_generator.backend.api import (
    config,
    config_defaults,
    data,
    data_operations,
    dataset_input,
    generation,
    health,
    preview,
    projects,
    requirements,
    templates,
)
from apps.pptx_generator.backend.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.

    Args:
        app: The FastAPI application instance.

    Yields:
        None: Control back to the application.
    """
    # Startup
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    generated_dir = Path(settings.GENERATED_DIR)
    generated_dir.mkdir(parents=True, exist_ok=True)

    # Validate domain config at startup
    _validate_domain_config()

    yield
    # Shutdown (nothing to do currently)


app = FastAPI(
    title="PowerPoint Generator API",
    description="RESTful API for automated PowerPoint generation with guided workflow",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Per ADR-0029: Health endpoints are unversioned (accessible at /health when mounted)
app.include_router(health.router, tags=["health"])
# Per ADR-0029: Tool-specific routes use /v1/ prefix internally
# Gateway mounts at /api/pptx, so routes become /api/pptx/v1/{resource}
app.include_router(projects.router, prefix="/v1/projects", tags=["projects"])
app.include_router(templates.router, prefix="/v1/templates", tags=["templates"])
app.include_router(data.router, prefix="/v1/data", tags=["data"])
app.include_router(dataset_input.router, prefix="/v1/data", tags=["dataset-input"])
app.include_router(generation.router, prefix="/v1/generation", tags=["generation"])
app.include_router(requirements.router, prefix="/v1/requirements", tags=["requirements"])
app.include_router(config.router, prefix="/v1/config", tags=["config"])
app.include_router(config_defaults.router, prefix="/v1", tags=["config"])
app.include_router(data_operations.router, prefix="/v1", tags=["data-operations"])
app.include_router(preview.router, prefix="/v1/preview", tags=["preview"])


logger = logging.getLogger(__name__)


def _validate_domain_config() -> None:
    """Validate domain configuration at startup."""
    from apps.pptx_generator.backend.core.domain_config_service import get_domain_config
    try:
        domain_config = get_domain_config()
        logger.info(
            f"Domain config validated: {len(domain_config.job_contexts)} job contexts, "
            f"{len(domain_config.metrics.canonical)} canonical metrics"
        )
    except Exception as e:
        logger.error(f"Domain config validation failed: {e}")


@app.exception_handler(Exception)
async def global_exception_handler(_request: Any, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions.

    Per ADR-0031: Uses ErrorResponse contract for standardized error format.

    Args:
        request: The incoming request.
        exc: The exception that was raised.

    Returns:
        JSONResponse: Error response with status code 500.
    """
    from shared.contracts.core.error_response import create_error_response, ErrorCategory

    error = create_error_response(
        status_code=500,
        message=f"Internal server error: {str(exc)}",
        category=ErrorCategory.INTERNAL,
        tool="pptx",
    )
    return JSONResponse(
        status_code=500,
        content=error.model_dump(mode="json"),
    )
