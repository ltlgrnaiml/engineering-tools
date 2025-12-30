# TEAM_009: DAT Deterministic Change Plan (SSoT → Code)

## Session Information

### Session Date

2025-12-29

### Status

PLANNED

### Objective

Convert the DAT SSoT (Tier-0 Contracts + ADRs + SPECs) into an ordered, deterministic refactor plan with validation-grade acceptance criteria.

### Predecessors

- `TEAM_006_DAT_SSOT_CHANGE_PLAN.md`
- `TEAM_008_DAT_IMPLEMENTATION_CHANGE_PLAN.md`

---

## 0. Inputs (Single Source of Truth)

### 0.1 DAT ADRs

- `.adrs/dat/ADR-0001-DAT_Stage-Graph-Configuration.json`
- `.adrs/dat/ADR-0003_Optional-Context-Preview-Stages.json`
- `.adrs/dat/ADR-0005-DAT_Stage-ID-Configuration.json`
- `.adrs/dat/ADR-0006_Table-Availability.json`
- `.adrs/dat/ADR-0011_Profile-Driven-Extraction-and-Adapters.json`
- `.adrs/dat/ADR-0013_Cancellation-Semantics-Parse-Export.json`
- `.adrs/dat/ADR-0014_Parse-and-Export-Artifact-Formats.json`
- `.adrs/dat/ADR-0040_Large-File-Streaming-Strategy.json`
- `.adrs/dat/ADR-0041_DAT-UI-Horizontal-Wizard-Pattern.json`

### 0.2 Core ADRs (must hold)

- `.adrs/core/ADR-0029_API-Versioning-and-Endpoint-Naming.json`
- Plus platform guardrails: determinism, path safety, error contracts, idempotency, audit timestamps.

### 0.3 DAT SPECS

- `docs/specs/dat/SPEC-DAT-0001_Stage-Graph.json`
- `docs/specs/dat/SPEC-DAT-0002_Profile-Extraction.json`
- `docs/specs/dat/SPEC-DAT-0003_Adapter-Interface-Registry.json`
- `docs/specs/dat/SPEC-DAT-0004_Large-File-Streaming.json`
- `docs/specs/dat/SPEC-DAT-0005_Profile-File-Management.json`
- `docs/specs/dat/SPEC-DAT-0006_Table-Availability.json`
- `docs/specs/dat/SPEC-DAT-0015_Cancellation-Cleanup.json`

### 0.4 Tier-0 Contracts (authoritative)

- `shared/contracts/dat/stage.py`
- `shared/contracts/dat/adapter.py`
- `shared/contracts/dat/profile.py`
- `shared/contracts/dat/table_status.py`
- `shared/contracts/dat/cancellation.py`
- `shared/contracts/dat/jobs.py`
- `shared/contracts/core/id_generator.py`
- `shared/contracts/core/path_safety.py`
- `shared/contracts/core/error_response.py`
- `shared/contracts/core/idempotency.py`

---

## 1. Current Misalignments (Observed)

### 1.1 Duplicate implementations (SSoT drift risk)

- There are **two adapter stacks**:
  - `apps/data_aggregator/backend/adapters/*` (contract-style; tests target this)
  - `apps/data_aggregator/backend/src/dat_aggregation/adapters/*` (legacy; used by current stage endpoints)

### 1.2 API versioning contradicts ADR-0030

- `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py` uses `APIRouter(prefix="/v1")`.
- ADR-0030 requires unversioned-by-default `/api/{tool}/{resource}`.

### 1.3 Stage graph + optional stages not correctly reflected in progression UX

- `GET /runs/{run_id}` derives `current_stage` by scanning a linear list that includes optional stages.
- Preview stage is locked with `completed=False`, which can trap `current_stage="preview"` even when Parse is eligible (Parse depends on Table Selection, not Preview per SPEC-0024).

### 1.4 Deterministic IDs mismatch

- Orchestrator currently uses `shared/utils/stage_id.py` (16 hex chars) while Tier-0 contract expects default 8-char IDs (`shared/contracts/core/id_generator.py`).
- Stage ID inputs are not stage-specific per ADR-0008; Discovery currently hashes absolute paths in inputs.

### 1.5 Table availability is too slow / not "probe-only"

- Current table availability scan reads full dataframes for counts; violates SPEC-0008 probe strategy + ADR-0041 streaming constraints.

---

## 2. Deterministic Change Plan (Milestones)

### Milestone M0: Baseline + Regression Protection (before behavior changes)

- **M0.1** Run and record baseline:
  - `pytest -q`
  - `pytest tests/dat -q`
  - `pytest tests/integration -q`
- **M0.2** Capture baseline OpenAPI:
  - Save current gateway + DAT `/openapi.json` outputs as artifacts for diffing (do not change baselines without explicit approval).

#### Acceptance Criteria for M0

- **AC-M0.1** All existing tests pass before code changes.

---

### Milestone M1: Converge on a Single Adapter Implementation (ADR-0012, SPEC-0026)

**Goal**: One adapter implementation, using `shared.contracts.dat.adapter.BaseFileAdapter` everywhere.

- **M1.1 (Delete legacy adapter stack)**
  - Remove usage of `apps/data_aggregator/backend/src/dat_aggregation/adapters/*`.
  - Update any imports in stages/routes to use `apps.data_aggregator.backend.adapters.*`.
- **M1.2 (Single registry)**
  - Canonical registry: `apps/data_aggregator/backend/adapters/registry.py`.
  - Ensure built-ins registered at startup: csv/excel/json (+ parquet passthrough).

#### Acceptance Criteria for M1

- **AC-M1.1** No production code imports from `backend/src/dat_aggregation/adapters/*`.
- **AC-M1.2** `pytest tests/dat/test_adapter_registry.py -q` passes.
- **AC-M1.3** Adapter detection works by extension and returns `AdapterMetadata`.

---

### Milestone M2: API Path Normalization (ADR-0030)

**Goal**: DAT routes are unversioned by default when mounted under `/api/dat`.

- **M2.1 (DAT)** Remove `APIRouter(prefix="/v1")` in `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`.
- **M2.2 (Gateway)** Remove tool dispatch references to `/api/{tool}/v1` (e.g., `gateway/services/pipeline_service.py`).
- **M2.3 (Frontends + tests)** Remove `/v1` usage in DAT frontend hooks/components and all tests.

#### Acceptance Criteria for M2

- **AC-M2.1** `grep` finds no default `/api/*/v1` usage in code (except explicitly suffix-versioned endpoints).
- **AC-M2.2** `pytest tests/test_all_endpoints.py -q` passes.

---

### Milestone M3: Stage Graph as Data + Correct Optional Stage Semantics (ADR-0004, ADR-0004, SPEC-0024)

**Goal**: One source for dependencies/cascade targets, and correct progression logic.

- **M3.1** Implement a single `stage_graph` module used by:
  - `DATStateMachine` forward gating
  - unlock cascade
  - "current stage" computation for the UI

#### Implementation strategy

- Derive dependencies + cascade targets directly from `SPEC-DAT-0001_Stage-Graph.json` (copy values into code once, then keep them centralized in a single module).
- Optional stages are:
  - `CONTEXT`
  - `PREVIEW`

- **M3.2 (Current stage algorithm)** Replace linear scan with graph-aware logic:
  - Compute the earliest stage that is *actionable* given gating rules.
  - Do **not** block progression on optional stages when skipped or incomplete.

#### Acceptance Criteria for M3

- **AC-M3.1** Forward gates match `stage_dependencies` exactly.
- **AC-M3.2** Cascade targets match `cascade_targets` exactly.
- **AC-M3.3** `Preview` locked but incomplete does not prevent the run from progressing to `Parse`.
- **AC-M3.4** Unlocking `Selection` unlocks downstream stages per SPEC-0024.

---

### Milestone M4: Deterministic Stage IDs + Path Safety (ADR-0008, ADR-0018)

**Goal**: Stage IDs are deterministic and stage-specific; no absolute paths in public contracts.

- **M4.1** Replace `shared/utils/stage_id.compute_stage_id` usage in DAT with `shared.contracts.core.id_generator.compute_deterministic_id` (8-char default).
- **M4.2** Implement stage-specific ID inputs per ADR-0008:
  - `DISCOVERY`: normalized `root_paths`, include patterns, exclude patterns, recursive
  - `SELECTION`: `discovery_stage_id`, selected file relpaths, `profile_id`
  - `CONTEXT`: `selection_stage_id`, sorted context hints
  - `TABLE_AVAILABILITY`: `selection_stage_id`, `profile_id`, probe options
  - `TABLE_SELECTION`: `table_availability_stage_id`, selected tables
  - `PREVIEW`: `table_selection_stage_id`, preview options
  - `PARSE`: `table_selection_stage_id`, `profile_id`, parse options
  - `EXPORT`: `parse_stage_id`, output_formats, output_path
- **M4.3** Add collision detection (ID exists with different input hash → error).

#### Acceptance Criteria for M4

- **AC-M4.1** Same semantic inputs across machines produce the same stage IDs.
- **AC-M4.2** ID prefix length is 8 characters (default).
- **AC-M4.3** All API responses contain only relative paths (`RelativePath`).

---

### Milestone M5: Table Availability = Fast Probe + Status Model (ADR-0008, SPEC-0008)

**Goal**: Deterministic, preview-independent probing.

- **M5.1** Implement a probe service that uses `BaseFileAdapter.probe_schema()` and file metadata only (no full reads).
- **M5.2** Produce `TableStatusReport` with statuses:
  - `AVAILABLE`, `PARTIAL`, `MISSING`, `EMPTY`, `ERROR`
- **M5.3** Ensure probe timeout per table = 1000ms.

#### Acceptance Criteria for M5

- **AC-M5.1** Probe completes in < 1s per table (unit/integration tested with timeouts).
- **AC-M5.2** Status report includes health metrics per SPEC.

---

### Milestone M6: Large File Streaming + Sampling (ADR-0041, SPEC-0027)

**Goal**: >10MB uses streaming, preview is sampled, memory capped.

- **M6.1** Automatic mode selection by file size threshold (10MB).
- **M6.2** Streaming uses adapter `stream_dataframe()` with chunk metadata.
- **M6.3** Preview sampling tiers:
  - 10–100MB: 10,000 rows
  - 100MB–1GB: 5,000 rows
  - >1GB: 1,000 rows
- **M6.4** Progress updates at least every 5 seconds (WebSocket or polling).

#### Acceptance Criteria for M6

- **AC-M6.1** Files > 10MB never eager-load by default.
- **AC-M6.2** Preview loads quickly with sampling and reports sampling to UI.

---

### Milestone M7: Parse + Export Artifact Bundles (ADR-0015)

**Goal**: Parse always produces Parquet + metadata bundle; Export is multi-format.

- **M7.1 (Parse)** Output bundle under stage artifact directory:
  - `dataset.parquet`
  - `manifest.json`
  - `prep_report.json`
  - `transform_plan.json`
  - `roles.yaml`
- **M7.2 (Export)** User-selectable formats for data tables; metadata stays JSON/YAML.

#### Acceptance Criteria for M7

- **AC-M7.1** Parse output is always Parquet.
- **AC-M7.2** Export supports at least `parquet`, `csv`, `excel`, `json`.

---

### Milestone M8: Cancellation + Cleanup + Auditability (ADR-0014, SPEC-0010)

**Goal**: Soft cancellation preserves completed work, discards partials, cleanup is explicit.

- **M8.1** Introduce checkpoint registry with safe points:
  - `TABLE_COMPLETE`
  - `STAGE_COMPLETE`
- **M8.2** Implement explicit cleanup API (dry-run default).
- **M8.3** Ensure audit timestamps are ISO-8601 UTC, no microseconds.

#### Acceptance Criteria for M8

- **AC-M8.1** Cancelling mid-stream never leaves partial persisted output.
- **AC-M8.2** Cleanup never deletes completed artifacts.

---

### Milestone M9: DAT Frontend Horizontal Wizard (ADR-0043)

**Goal**: Horizontal stepper reflecting FSM, with gating tooltips and unlock confirmation.

- **M9.1** Implement stepper + collapsible panels fed by stage graph + run status.
- **M9.2** Optional stage UI:
  - mark optional with badge
  - provide Skip action
- **M9.3** Unlock action shows cascade confirmation listing downstream stages.

#### Acceptance Criteria for M9

- **AC-M9.1** Stepper shows all user-interactive stages (Selection..Export).
- **AC-M9.2** UI navigation respects forward gating.

---

## 3. Acceptance Criteria Matrix (SSoT → Verification)

| Requirement | Source | Verification |
| --- | --- | --- |
| Optional stages do not block progression | ADR-0004, SPEC-0024 | `tests/dat/test_state_machine.py`, `tests/dat/test_api.py` |
| Export requires Parse locked + completed | ADR-0004, SPEC-0024 | `tests/dat/test_stages.py` |
| Stage IDs deterministic, seed=42, 8-char | ADR-0008, core ADR-0005 | `tests/dat/test_state_machine.py` + new `test_stage_ids.py` |
| Table availability probe-only, <1s/table | ADR-0008, SPEC-0008 | new `tests/dat/test_table_availability_probe.py` |
| Streaming for files >10MB | ADR-0041, SPEC-0027 | `tests/dat/test_csv_adapter.py` + new streaming tests |
| Soft cancel preserves completed artifacts only | ADR-0014, SPEC-0010 | `tests/dat/test_stages.py`, new cancel tests |
| Parse outputs Parquet + metadata bundle | ADR-0015 | `tests/dat/test_stages.py` |
| API paths unversioned by default | ADR-0030 | `tests/integration/test_gateway_api.py` |

---

## 4. Validation Runbook (end-to-end)

```bash
# Lint/format
ruff check .
ruff format --check .

# DAT-focused tests
pytest tests/dat -q

# Integration tests
pytest tests/integration -q

# Contract validation
pytest tests/test_contracts.py -q
python tools/check_contract_drift.py
```

---

## 5. Open Questions (must resolve before M4)

1. **Path-safety vs user-selected OS paths**: Should Discovery/Selection accept only workspace-relative paths (recommended for determinism), or do we allow absolute paths in requests but strictly normalize/redact in all persisted artifacts and responses?
2. **StageGraphConfig SSOT**: Do we want a Tier-0 contract for stage graph/dependencies (preferred SSOT), or keep it as an internal module derived from SPEC-0024 and treat the SPEC as "the source"?

---

## 6. Handoff Notes

- Execute milestones in order (M0 → M9). Avoid partial migrations that keep both adapter stacks alive.
- Do not change baseline fixtures/snapshots without explicit approval.
