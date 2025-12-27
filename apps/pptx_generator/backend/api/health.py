"""Health check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """
    Health check response model.

    Attributes:
        status: Health status of the service.
        version: API version.
        service: Service name.
    """

    status: str
    version: str
    service: str = "pptx-generator"


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Health status and version information.
    """
    return HealthResponse(status="healthy", version="0.1.0", service="pptx-generator")
