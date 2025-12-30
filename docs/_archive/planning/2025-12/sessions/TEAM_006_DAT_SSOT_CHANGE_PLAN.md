# TEAM_006: DAT SSoT Change Plan

**Session Date**: 2025-12-28
**Status**: IN_PROGRESS
**Objective**: Turn DAT SSoT (Contracts + ADRs + SPECs) into deterministic, actionable code changes and concrete acceptance criteria.

## Session Checklist (Solo-Dev Ethos)

- [x] Read `docs/AI_CODING_GUIDE.md`
- [x] Review recent session logs in `.sessions/`
- [x] Check `.questions/` for open issues
- [x] Claim session number and maintain this session log
- [ ] Baseline tests pass before behavior changes

## Inputs (SSoT)

### ADRs

- `.adrs/dat/ADR-0001-DAT_Stage-Graph-Configuration.json`
- `.adrs/dat/ADR-0003_Optional-Context-Preview-Stages.json`
- `.adrs/dat/ADR-0005-DAT_Stage-ID-Configuration.json`
- `.adrs/dat/ADR-0006_Table-Availability.json`
- `.adrs/dat/ADR-0011_Profile-Driven-Extraction-and-Adapters.json`
- `.adrs/dat/ADR-0013_Cancellation-Semantics-Parse-Export.json`
- `.adrs/dat/ADR-0014_Parse-and-Export-Artifact-Formats.json`
- `.adrs/core/ADR-0029_API-Versioning-and-Endpoint-Naming.json`
- `.adrs/dat/ADR-0040_Large-File-Streaming-Strategy.json`
- `.adrs/dat/ADR-0041_DAT-UI-Horizontal-Wizard-Pattern.json`

### Specs

- `docs/specs/dat/SPEC-DAT-0001_Stage-Graph.json`
- `docs/specs/dat/SPEC-DAT-0002_Profile-Extraction.json`
- `docs/specs/dat/SPEC-DAT-0003_Adapter-Interface-Registry.json`
- `docs/specs/dat/SPEC-DAT-0004_Large-File-Streaming.json`
- `docs/specs/dat/SPEC-DAT-0005_Profile-File-Management.json`
- `docs/specs/dat/SPEC-DAT-0006_Table-Availability.json`
- `docs/specs/dat/SPEC-DAT-0015_Cancellation-Cleanup.json`
- `docs/specs/core/SPEC-0044_Stage-Completion-Semantics.json`

### Contracts

- `shared/contracts/dat/adapter.py`
- `shared/contracts/dat/stage.py`
- `shared/contracts/dat/profile.py`
- `shared/contracts/dat/table_status.py`
- `shared/contracts/dat/cancellation.py`
- `shared/contracts/dat/jobs.py`

## Deliverables

- Deterministic change plan (milestones + task IDs + file-level actions)
- Acceptance criteria + validation matrix (requirements → tests/commands)

## Confirmed Decisions (User)

- **ADR-0030 alignment**: Include gateway + tool API path normalization to the simplified pattern (unversioned by default).
- **Discovery UX semantics**: Discovery = user chooses a location to scan; Selection appears below on the same page as a list to pick from.

## Current Findings (Req → Code Map)

### API routing + versioning (ADR-0030)

- **Gateway mounts (cross-tool)**: `gateway/main.py` mounts cross-tool routers at `/api/v1/*` (e.g., `/api/v1/datasets`, `/api/v1/pipelines`, `/api/v1/devtools`).
- **Gateway mounts (tool apps)**: `gateway/main.py` mounts tools at `/api/dat`, `/api/sov`, `/api/pptx`.
- **DAT tool router**: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py` uses `APIRouter(prefix="/v1")`, making effective paths `/api/dat/v1/...`.
- **SOV tool router**: `apps/sov_analyzer/backend/src/sov_analyzer/api/routes.py` uses `APIRouter(prefix="/v1")`, making effective paths `/api/sov/v1/...`.
- **PPTX tool routers**: `apps/pptx_generator/backend/main.py` includes routers under `/v1/*`, making effective paths `/api/pptx/v1/...`.
- **Gateway pipeline dispatch**: `gateway/services/pipeline_service.py` hardcodes tool base URLs with `/api/{tool}/v1`.
- **Frontend**: DAT frontend currently calls `/api/dat/v1/...` (e.g., `apps/data_aggregator/frontend/src/hooks/useRun.ts`).
- **Misalignment**: ADR-0030 requires unversioned `/api/{resource}` and `/api/{tool}/{resource}` by default (suffix versioning only on breaking changes).

### Stage graph + optional stages (ADR-0004, ADR-0004, ADR-0001 core)

- **Backend orchestrator**: `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py` hardcodes `FORWARD_GATES` and `CASCADE_TARGETS`.
- **Config module exists but unused**: `apps/data_aggregator/backend/src/dat_aggregation/core/stage_graph_config.py` defines `StageGraphConfig.default()` with gate/cascade rules; it is not currently consumed by `DATStateMachine`.
- **No Tier-0 StageGraphConfig contract found**: No `StageGraphConfig` / `StageDefinition` / `GatingRule` contract exists under `shared/contracts/*`.
- **Optional stage progression risk**: current `current_stage` derivation appears to treat optional stages as required unless explicitly completed.
- **Preview skip does not advance**: `PreviewPanel.tsx` “Skip Preview” triggers `POST /runs/{run_id}/stages/preview/lock`, but `lock_preview` always returns `completed=False`, so `GET /runs/{run_id}` computes `current_stage=preview` (locked but not completed).
- **Skip semantics not implemented**: `docs/specs/core/SPEC-0044_Stage-Completion-Semantics.json` defines `skip_complete` for optional stages (lock with `completed=true` on skip); current Preview skip does not set `completed=true`.
- **Preview acknowledgment**: Preview lock returns `completed=False`; a generic `POST /runs/{run_id}/stages/{stage}/complete` endpoint exists and sets `completed=True`.

### Deterministic stage IDs + path safety (ADR-0005, ADR-0008, ADR-0018)

- **Current ID util**: `shared/utils/stage_id.py` produces 16-hex IDs; backend uses this in `DATStateMachine.lock_stage`.
- **Contract ID util**: `shared/contracts/core/id_generator.py` produces 8-hex IDs by default and defines typed `*StageInputs` models.
- **Discovery inputs include absolute paths**: `POST /runs/{run_id}/stages/discovery/lock` hashes `{"root_path": str(source_path)}` (currently absolute), violating cross-machine determinism and path-safety expectations.

### Table availability (ADR-0008, SPEC-0008)

- **Current implementation**: `GET /runs/{run_id}/stages/table_availability/scan` reads full tables (`adapter.read`) to compute row/column counts; this may violate the “fast probe” intent and large-file streaming constraints.

### Adapters / profiles / streaming (ADR-0012, SPEC-0026/0004/0005)

- **Adapters**: two parallel implementations exist:
  - `apps/data_aggregator/backend/src/dat_aggregation/adapters/*` (sync protocol in `adapters/base.py`) used by current pipeline endpoints.
  - `apps/data_aggregator/backend/adapters/*` (contract-style adapters with `probe_schema/read_dataframe/stream_dataframe`) plus registry tests.
- **Profiles**: DAT API exposes `GET /profiles` only; profile CRUD + validation flows from SPEC-0007 are not implemented in the current router.
- **Progress / jobs**: WebSocket progress infra exists (`api/websocket.py`) and a background `JobService` exists, but parse currently runs inline and the progress endpoint is minimal (`GET /runs/{run_id}/stages/parse/progress`).

## Deterministic Change Plan (Draft)

### Milestone M1: ADR-0030 API Path Normalization (Gateway + Tools + Frontends + Tests)

**Goal**: Remove default `/v1` prefixes across gateway + tool APIs so the canonical paths are:
- cross-tool: `/api/{resource}`
- tool-specific: `/api/{tool}/{resource}`

 

#### Tasks (File-Level)

- **M1.API.001 (gateway)**: Update cross-tool mounts in `gateway/main.py`:
  - Change `/api/v1/datasets` → `/api/datasets`
  - Change `/api/v1/pipelines` → `/api/pipelines`
  - Change `/api/v1/devtools` → `/api/devtools`
- **M1.API.002 (gateway)**: Update internal tool routing in `gateway/services/pipeline_service.py`:
  - Update `TOOL_BASE_URLS` from `http://localhost:8000/api/{tool}/v1` → `http://localhost:8000/api/{tool}`
  - Update any hardcoded paths in dispatch helpers to remove `/v1`
- **M1.API.003 (dat)**: Update DAT router versioning in `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`:
  - Change `APIRouter(prefix="/v1")` → `APIRouter()`
  - Remove/update any route-level assumptions that paths include `/v1`
- **M1.API.004 (sov)**: Update SOV router versioning in `apps/sov_analyzer/backend/src/sov_analyzer/api/routes.py`:
  - Change `APIRouter(prefix="/v1")` → `APIRouter()`
- **M1.API.005 (pptx)**: Update PPTX router mounts in `apps/pptx_generator/backend/main.py`:
  - Change `prefix="/v1/projects"` → `prefix="/projects"` (and similarly for other routers)
- **M1.API.006 (dat-frontend)**: Remove `/v1` from DAT frontend fetches:
  - `apps/data_aggregator/frontend/src/hooks/useRun.ts`
  - `apps/data_aggregator/frontend/src/components/stages/*.tsx`
- **M1.API.007 (sov-frontend)**: Remove `/v1` from SOV frontend fetches:
  - `apps/sov_analyzer/frontend/src/components/*.tsx`
- **M1.API.008 (homepage-frontend)**: Remove `/v1` from homepage frontend fetches:
  - `apps/homepage/frontend/src/hooks/*.ts`
  - `apps/homepage/frontend/src/pages/*.tsx`
- **M1.API.009 (tests)**: Update endpoint paths in tests:
  - `tests/test_gateway.py`
  - `tests/test_all_endpoints.py`
  - `tests/integration/test_gateway_api.py`
  - `tests/unit/test_devtools_api.py`
  - any other tests matching `"/api/*/v1"` or `"/api/v1"`

#### Acceptance Criteria

- All gateway routes exist at the unversioned paths described in ADR-0030.
- No production code references `/api/*/v1` or `/api/v1/*` as default routes.
- All affected frontends load successfully without 404s due to path changes.
- OpenAPI specs served by gateway + tools reflect the actual, unversioned paths.

#### Validation Matrix (Commands)

- **Unit/Integration**: `pytest`
- **Contract drift**: `python tools/check_contract_drift.py`
- **Endpoint smoke**: `pytest tests/test_all_endpoints.py -q`

## Notes

- `.questions/` directory did not exist at session start; created to uphold SSoT.
