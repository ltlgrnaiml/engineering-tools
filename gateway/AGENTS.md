# Gateway - AI Coding Guide

> **Scope**: API Gateway and cross-tool services.

---

## Purpose

The Gateway provides:

1. **API Routing** - Mounts tool backends at `/api/{tool}/`
2. **Cross-Tool APIs** - DataSet and Pipeline services
3. **Health Monitoring** - Platform-wide health checks

---

## Directory Structure

```text
gateway/
├── main.py               # FastAPI app entry point
├── routers/
│   ├── datasets.py       # /api/v1/datasets endpoints
│   └── pipelines.py      # /api/v1/pipelines endpoints
├── services/
│   ├── dataset_service.py    # DataSet CRUD + lineage
│   └── pipeline_service.py   # Pipeline orchestration
└── middleware/
    └── cors.py           # CORS configuration
```

---

## Tool Mounting Pattern

```python
from fastapi import FastAPI

app = FastAPI()

# Mount tool backends
app.mount("/api/dat", dat_app)
app.mount("/api/pptx", pptx_app)
app.mount("/api/sov", sov_app)

# Cross-tool APIs at root
app.include_router(datasets_router, prefix="/api/v1/datasets")
app.include_router(pipelines_router, prefix="/api/v1/pipelines")
```

---

## Cross-Tool APIs

### DataSet API (`/api/v1/datasets`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | List all datasets |
| `/{id}` | GET | Get dataset manifest |
| `/{id}/preview` | GET | Preview dataset (first N rows) |
| `/{id}/lineage` | GET | Get dataset lineage tree |

### Pipeline API (`/api/v1/pipelines`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | POST | Create pipeline |
| `/{id}` | GET | Get pipeline status |
| `/{id}/execute` | POST | Execute pipeline |
| `/{id}/cancel` | POST | Cancel running pipeline |

---

## Health Endpoint

```python
@app.get("/health")
async def health_check() -> dict:
    """Platform health check.
    
    Returns status of all tools and services.
    """
    return {
        "status": "healthy",
        "tools": {
            "dat": await check_tool_health("dat"),
            "pptx": await check_tool_health("pptx"),
            "sov": await check_tool_health("sov"),
        },
        "services": {
            "datasets": "available",
            "pipelines": "available",
        }
    }
```

---

## CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

# Development ports
ALLOWED_ORIGINS = [
    "http://localhost:3000",   # Homepage
    "http://localhost:5173",   # DAT frontend
    "http://localhost:5174",   # SOV frontend
    "http://localhost:5175",   # PPTX frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Testing

```bash
pytest tests/gateway/ -v
pytest tests/integration/test_gateway.py -v
```
