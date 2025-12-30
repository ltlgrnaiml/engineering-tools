# DAT Backend - AI Coding Guide

> **Scope**: Python/FastAPI backend for Data Aggregator tool.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI |
| Data Processing | Polars (NOT pandas) |
| Validation | Pydantic (from shared.contracts) |
| File I/O | Adapters pattern |

---

## Directory Structure

```text
backend/
├── api/
│   ├── routes.py          # FastAPI route definitions
│   ├── errors.py          # ErrorResponse helpers
│   └── dependencies.py    # Dependency injection
├── services/
│   ├── stage_service.py   # Stage execution logic
│   ├── profile_service.py # Profile management
│   └── adapter_service.py # File adapter coordination
└── src/dat_aggregation/
    ├── adapters/          # File type adapters
    ├── profiles/          # Profile execution engine
    └── stages/            # Stage implementations
```

---

## API Patterns

### Route Definition

```python
from fastapi import APIRouter, Depends, HTTPException
from shared.contracts.dat.stage import DATStageState
from .errors import create_error_response

router = APIRouter(prefix="/v1", tags=["dat"])

@router.post("/stages/{stage_id}/lock")
async def lock_stage(stage_id: str) -> DATStageState:
    """Lock a stage after validation."""
    ...
```

### Error Handling

```python
from shared.contracts.core.error_response import ErrorResponse
from .errors import create_error_response

# Always use ErrorResponse contract
raise HTTPException(
    status_code=400,
    detail=create_error_response(
        code="DAT_VALIDATION_ERROR",
        message="Invalid profile configuration"
    ).model_dump()
)
```

---

## Adapter Pattern

All file adapters inherit from `BaseFileAdapter`:

```python
from shared.contracts.dat.adapter import BaseFileAdapter, SchemaProbeResult

class CSVAdapter(BaseFileAdapter):
    """CSV file adapter."""

    def probe_schema(self, path: Path) -> SchemaProbeResult:
        """Probe file schema without loading entire file."""
        ...

    def read_data(self, path: Path, options: ReadOptions) -> pl.DataFrame:
        """Read data using Polars."""
        ...
```

---

## Data Processing Rules

```python
# ✅ CORRECT - Use Polars
import polars as pl

df = pl.read_csv("data.csv")
result = df.filter(pl.col("value") > 0)

# ❌ WRONG - No pandas
import pandas as pd  # NEVER USE
```

---

## Testing

Run DAT backend tests:

```bash
pytest tests/dat/ -v
pytest tests/dat/test_adapters/ -v  # Adapter tests
pytest tests/dat/test_api/ -v       # API tests
```
