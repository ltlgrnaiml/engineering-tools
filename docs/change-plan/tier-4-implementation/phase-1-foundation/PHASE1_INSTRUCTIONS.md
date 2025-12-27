# Tier 4: Phase 1 Foundation - Implementation Instructions

**Document Type:** Step-by-Step Implementation Guide  
**Audience:** AI Coding Assistants, Junior Developers  
**Status:** ⚠️ MOSTLY COMPLETE (CI and tests pending)  
**Last Updated:** 2025-01-26

---

## Phase Overview

Phase 1 establishes the monorepo foundation with shared contracts, storage, and gateway. This phase is **COMPLETE** - the basic structure has been created.

---

## Completed Steps

> **Note:** The structure and core implementations are complete. CI pipeline (Step 1.7) and test suite (Step 1.8) remain pending.

### Step 1.1: Create Monorepo Directory Structure ✅

**Location:** `/Users/kalepook_ai/Coding/engineering-tools/`

The following structure was created:

```
engineering-tools/
├── .adrs/                    # Cross-cutting ADRs
├── shared/
│   ├── contracts/core/       # Pydantic contracts
│   ├── storage/              # Artifact store
│   ├── utils/                # Shared utilities
│   └── frontend/             # Shared UI components (TODO)
├── gateway/
│   └── services/             # Cross-tool services
├── apps/
│   ├── homepage/
│   ├── data-aggregator/
│   ├── pptx-generator/
│   └── sov-analyzer/
├── workspace/                # Local artifact storage
├── tools/                    # Dev tooling
├── ci/                       # CI scripts
└── docs/                     # Documentation
```

### Step 1.2: Create Root Configuration Files ✅

**Files created:**

- `pyproject.toml` - Python project config with dependencies
- `README.md` - Project documentation
- `.gitignore` - Git ignore patterns

### Step 1.3: Create Shared Contracts ✅

**Files created:**

- `shared/contracts/core/dataset.py` - DataSet contracts
- `shared/contracts/core/pipeline.py` - Pipeline contracts
- `shared/contracts/core/artifact_registry.py` - Registry contracts

### Step 1.4: Create Shared Storage ✅

**Files created:**

- `shared/storage/artifact_store.py` - Parquet/JSON I/O
- `shared/storage/registry_db.py` - SQLite registry

### Step 1.5: Create Gateway ✅

**Files created:**

- `gateway/main.py` - FastAPI gateway
- `gateway/services/dataset_service.py` - DataSet APIs
- `gateway/services/pipeline_service.py` - Pipeline APIs

---

## Remaining Phase 1 Tasks

### Step 1.6: Migrate ADRs from DataAggregationTool

**Instructions:**

1. Copy ADR files from `/Users/kalepook_ai/Coding/DataAggregationTool/adrs/` to `/Users/kalepook_ai/Coding/engineering-tools/.adrs/`

2. Update cross-references in ADRs to new paths

3. Create ADR index file

**Command:**
```bash
cp -r /Users/kalepook_ai/Coding/DataAggregationTool/adrs/*.json /Users/kalepook_ai/Coding/engineering-tools/.adrs/
```

### Step 1.7: Configure CI Pipeline

**Files to create:**

1. `ci/steps/step_mypy.ps1`
2. `ci/steps/step_ruff.ps1`
3. `ci/steps/step_tests.ps1`

**Example step_mypy.ps1:**
```powershell
#!/usr/bin/env pwsh
# Step: Type checking with mypy
# Per ADR-0009: 100% type coverage required

$ErrorActionPreference = "Stop"

Write-Host "Running mypy..."
python -m mypy shared gateway apps --strict

if ($LASTEXITCODE -ne 0) {
    Write-Error "mypy failed"
    exit 1
}

Write-Host "mypy passed"
```

### Step 1.8: Create Basic Tests

**Files to create:**

1. `tests/test_contracts.py` - Contract validation
2. `tests/test_storage.py` - Storage operations
3. `tests/test_gateway.py` - Gateway endpoints

**Example test_contracts.py:**
```python
"""Tests for shared contracts."""
import pytest
from datetime import datetime, timezone

from shared.contracts.core.dataset import DataSetManifest, ColumnMeta
from shared.contracts.core.pipeline import Pipeline, PipelineStep


def test_dataset_manifest_creation():
    """Test creating a DataSetManifest."""
    manifest = DataSetManifest(
        dataset_id="ds_test123",
        name="Test Dataset",
        created_at=datetime.now(timezone.utc),
        created_by_tool="dat",
        columns=[
            ColumnMeta(name="col1", dtype="float64"),
        ],
        row_count=100,
    )
    assert manifest.dataset_id == "ds_test123"
    assert len(manifest.columns) == 1


def test_pipeline_creation():
    """Test creating a Pipeline."""
    pipeline = Pipeline(
        pipeline_id="pipe_test123",
        name="Test Pipeline",
        created_at=datetime.now(timezone.utc),
        steps=[
            PipelineStep(
                step_index=0,
                step_type="dat:aggregate",
                config={"source_files": ["test.csv"]},
            ),
        ],
    )
    assert pipeline.pipeline_id == "pipe_test123"
    assert len(pipeline.steps) == 1
```

### Step 1.9: Verify Installation

**Commands to run:**

```bash
cd /Users/kalepook_ai/Coding/engineering-tools

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows

# Install in development mode
pip install -e ".[all]"

# Verify imports work
python -c "from shared.contracts import DataSetManifest; print('OK')"

# Run gateway
python -m gateway.main
```

---

## Validation Checklist

- [x] Virtual environment created
- [x] All dependencies installed
- [x] `shared.contracts` imports work
- [x] `shared.storage` imports work
- [x] Gateway starts without errors
- [x] `/api/health` returns 200
- [x] `/api/docs` shows OpenAPI docs
- [ ] CI pipeline scripts created (Step 1.7)
- [ ] Test suite created (Step 1.8)

---

## Next Phase

Proceed to **Phase 2: Homepage + PPTX Migration**

See: `phase-2-homepage-pptx/PHASE2_INSTRUCTIONS.md`
