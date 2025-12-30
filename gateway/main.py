"""API Gateway - main entrypoint for Engineering Tools Platform.

The gateway:
1. Mounts individual tool APIs under /api/{tool}/
2. Provides cross-tool APIs (DataSets, Pipelines)
3. Serves the homepage SPA

Run with: python -m gateway.main
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from gateway.services.dataset_service import router as dataset_router
from gateway.services.pipeline_service import router as pipeline_router
from gateway.services.devtools_service import router as devtools_router

__version__ = "0.1.0"

app = FastAPI(
    title="Engineering Tools Platform",
    description="Unified API for Data Aggregator, SOV Analyzer, and PowerPoint Generator",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === Cross-Tool APIs (gateway-level) ===
# Per ADR-0029: Gateway cross-tool APIs use /api/{resource} pattern (no version prefix)
app.include_router(dataset_router, prefix="/api/datasets", tags=["datasets"])
app.include_router(pipeline_router, prefix="/api/pipelines", tags=["pipelines"])
app.include_router(devtools_router, prefix="/api/devtools", tags=["devtools"])


# === Health Check ===
# Track which tools were successfully mounted
_tool_status: dict[str, str] = {
    "dat": "coming_soon",
    "sov": "coming_soon", 
    "pptx": "coming_soon",
}


def _check_tool_health(tool: str, app_module: str) -> str:
    """Check if a tool is available."""
    try:
        __import__(app_module)
        return "available"
    except ImportError:
        return "coming_soon"
    except Exception:
        return "error"


async def _get_storage_stats() -> dict:
    """Get storage statistics."""
    try:
        from shared.storage.artifact_store import ArtifactStore
        store = ArtifactStore()
        datasets = await store.list_datasets()
        
        total_size = sum(ds.size_bytes or 0 for ds in datasets)
        
        return {
            "datasets": len(datasets),
            "pipelines": 0,  # TODO: get from registry
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }
    except Exception:
        return {
            "datasets": 0,
            "pipelines": 0,
            "total_size_mb": 0,
        }


@app.get("/health")
@app.get("/api/health")
async def health_check() -> dict:
    """Health check endpoint with dynamic tool status."""
    # Check tool health
    tools = {
        "dat": _check_tool_health("dat", "apps.data_aggregator.backend.main"),
        "sov": _check_tool_health("sov", "apps.sov_analyzer.backend.main"),
        "pptx": _check_tool_health("pptx", "apps.pptx_generator.backend.main"),
    }
    
    # Get storage stats
    storage = await _get_storage_stats()
    
    # Determine overall status
    tool_statuses = list(tools.values())
    if all(s == "available" for s in tool_statuses):
        status = "healthy"
    elif any(s == "error" for s in tool_statuses):
        status = "unhealthy"
    elif any(s == "available" for s in tool_statuses):
        status = "degraded"
    else:
        status = "degraded"
    
    return {
        "status": status,
        "version": __version__,
        "tools": tools,
        "storage": storage,
    }


# === Tool API Mounts ===
# Import and mount tool-specific FastAPI apps

try:
    from apps.pptx_generator.backend.main import app as pptx_app
    app.mount("/api/pptx", pptx_app)
    import logging
    logging.info("PPTX Generator mounted successfully at /api/pptx")
except ImportError as e:
    import logging
    logging.error(f"PPTX Generator import failed: {e}", exc_info=True)
except Exception as e:
    import logging
    logging.error(f"PPTX Generator mount failed: {e}", exc_info=True)

try:
    # Force fresh import of DAT app by clearing module cache
    import sys
    import importlib
    
    # Clear ALL cached modules that could affect DAT loading
    prefixes_to_clear = ['apps.data_aggregator', 'shared.contracts.dat']
    modules_to_clear = [k for k in list(sys.modules.keys()) 
                        if any(k.startswith(p) for p in prefixes_to_clear)]
    for mod in modules_to_clear:
        del sys.modules[mod]
    
    from apps.data_aggregator.backend.main import app as dat_app
    app.mount("/api/dat", dat_app)
    logging.info(f"DAT mounted with fresh code, cleared {len(modules_to_clear)} modules")
except ImportError as e:
    logging.warning(f"Data Aggregator not available: {e}")
except Exception as e:
    logging.error(f"DAT mount failed with error: {e}", exc_info=True)

try:
    from apps.sov_analyzer.backend.main import app as sov_app
    app.mount("/api/sov", sov_app)
except ImportError as e:
    logging.warning(f"SOV Analyzer not available: {e}")


# === Static File Serving (Homepage) ===
# Uncomment when frontend is built
# app.mount("/", StaticFiles(directory="apps/homepage/frontend/dist", html=True))


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = True,
) -> None:
    """Run the development server."""
    uvicorn.run(
        "gateway.main:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    run_server()
