"""SOV Analyzer Tool - FastAPI application entry point."""
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.sov_analyzer.backend.src.sov_analyzer.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    workspace = Path.cwd() / "workspace" / "tools" / "sov"
    workspace.mkdir(parents=True, exist_ok=True)
    logger.info(f"SOV workspace initialized at {workspace}")
    yield


app = FastAPI(
    title="SOV Analyzer API",
    description="Source of Variation analysis tool with ANOVA",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
# Per ADR-0030: Router has / prefix, gateway mounts at /api/sov/
# Final routes: /api/sov/analyses, etc.
app.include_router(router, tags=["sov"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "sov-analyzer",
        "tool": "sov",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)
