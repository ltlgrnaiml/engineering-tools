"""Data Aggregator Tool - FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.data_aggregator.backend.src.dat_aggregation.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    # Ensure workspace directory exists
    workspace = Path.cwd() / "workspace" / "tools" / "dat"
    workspace.mkdir(parents=True, exist_ok=True)
    logger.info(f"DAT workspace initialized at {workspace}")
    yield


app = FastAPI(
    title="Data Aggregator API",
    description="Data extraction and aggregation tool with FSM stage orchestration",
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
app.include_router(router, prefix="/api", tags=["dat"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "tool": "dat", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
