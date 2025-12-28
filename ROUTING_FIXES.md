# API Routing Fixes - Remove /v1 Versioning

## Decision
Remove all `/v1` URL prefixes from API routes. Versioning is handled at the contract module level (`__version__` in Pydantic models) per ADR-0009, not at the URL level.

## Changes Made

### Backend Routes (Removed /v1 prefix)

#### Gateway (`gateway/main.py`)
- `/api/v1/datasets` → `/api/datasets`
- `/api/v1/pipelines` → `/api/pipelines`
- `/api/v1/devtools` → `/api/devtools`

#### DAT Backend (`apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`)
- Removed `prefix="/v1"` from APIRouter
- All routes now mount at `/api/dat/runs`, `/api/dat/stages`, etc.

#### PPTX Backend (`apps/pptx_generator/backend/main.py`)
- `/api/v1/projects` → `/api/projects`
- `/api/v1/templates` → `/api/templates`
- `/api/v1/data` → `/api/data`
- `/api/v1/generation` → `/api/generation`
- `/api/v1/requirements` → `/api/requirements`
- `/api/v1/config` → `/api/config`
- `/api/v1/preview` → `/api/preview`
- `/api/v1` (health, config defaults, data ops) → `/api`

#### SOV Backend
- Already had no `/v1` prefix ✅

### Frontend API Calls (Removed /v1)

#### DAT Frontend (`apps/data_aggregator/frontend/src/hooks/useRun.ts`)
- `/api/dat/v1/runs` → `/api/dat/runs`

#### Homepage Frontend
- `src/hooks/usePipelines.ts`: `/api/pipelines/v1/` → `/api/pipelines/`
- `src/pages/PipelinesPage.tsx`: Added trailing slash for consistency
- `src/pages/PipelineDetailsPage.tsx`: `/api/pipelines/v1/{id}` → `/api/pipelines/{id}`

#### SOV Frontend
- `src/components/AnalysisConfig.tsx`: 
  - `/api/datasets/v1/{id}` → `/api/datasets/{id}`
  - `/api/sov/v1/analysis` → `/api/sov/analysis`
- `src/components/ResultsPanel.tsx`: `/api/sov/v1/analysis/{id}` → `/api/sov/analysis/{id}`

### ADR Updates

#### ADR-0027 (DevTools)
- `approach`: Changed `/api/v1/devtools` to `/api/devtools`
- `constraints`: Changed endpoint requirement to `/api/devtools/*`

#### ADR-0017 (Cross-Cutting Guardrails)
- `contract-versioning` guardrail: Updated to clarify URL versioning is **not used**
- Enforcement now states: "API routes do NOT use /v1/ prefixes - versioning is at contract level only"

## Bugs Fixed

### Bug 1: DAT - Cannot Create New Run ✅
- **Root Cause**: Frontend calling `/api/dat/runs`, backend expecting `/api/dat/v1/runs`
- **Fix**: Removed `/v1` from DAT backend router

### Bug 2: Pipelines Page - Failed to Load ✅
- **Root Cause**: Frontend calling `/api/pipelines`, backend at `/api/v1/pipelines`
- **Fix**: Removed `/v1` from gateway pipeline router

### Bug 3: SOV Analyzer - Loading Spinner ✅
- **Root Cause**: Frontend calling `/api/sov/v1/analysis`, backend at `/api/sov/analysis`
- **Fix**: Removed `/v1` from SOV frontend calls (backend was already correct)

### Bug 4: PPTX Validation Blocking Generation ⚠️
- **Root Cause**: ADR-0019 workflow enforcement - validation must pass before generation
- **Status**: **NOT a routing bug** - this is correct behavior per ADR-0019
- **Error Message**: "Generation blocked per ADR-0019: Generation requires validation to pass ('Four Green Bars')"
- **Fix Needed**: Frontend workflow must complete validation step before attempting generation

## Testing Needed

### Quick Verification
```bash
# Start services
.\start.ps1 --with-frontend

# Test each tool:
# 1. DAT: http://localhost:5173 - Click "Create New Run"
# 2. Pipelines: http://localhost:3000/pipelines - Should load list
# 3. SOV: http://localhost:5174 - Select dataset and configure analysis
# 4. PPTX: http://localhost:5175 - Complete validation before generation
```

### API Endpoint Tests
```bash
# Gateway
curl http://localhost:8000/api/datasets/
curl http://localhost:8000/api/pipelines/

# DAT
curl -X POST http://localhost:8000/api/dat/runs -H "Content-Type: application/json" -d "{}"

# SOV
curl http://localhost:8000/api/sov/analysis

# PPTX  
curl http://localhost:8000/api/pptx/projects
```

## Documentation Updates Still Needed
- [ ] `docs/GAP_ANALYSIS.md` - Remove /v1 references
- [ ] `docs/AI_CODING_GUIDE.md` - Update API architecture diagram
- [ ] `docs/data-aggregator/DEBUG_STRATEGY.md` - Update all endpoint examples
- [ ] `docs/dat/DAT_GAP_ANALYSIS.md` - Update "API versioning" section
- [ ] Test files in `tests/` directory - Update all /v1 URLs

## Contract Discipline (ADR-0009)
Versioning is now **exclusively** at the contract level:
- Each contract module has `__version__` attribute (e.g., `__version__ = "0.1.0"`)
- Breaking changes require version bump in contract module
- API routes remain stable (no /v1, /v2 prefixes)
- OpenAPI schemas are regenerated when contracts change
- Frontend uses typed contracts from `shared/frontend/src/types/contracts.ts`
