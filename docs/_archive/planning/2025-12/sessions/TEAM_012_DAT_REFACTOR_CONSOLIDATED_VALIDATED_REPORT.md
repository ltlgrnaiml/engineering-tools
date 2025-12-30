# TEAM_012: DAT Refactor Consolidated Validated Findings Report (TEAM_006–TEAM_010)

## Session Information

### Session Date

2025-12-29

### Status

DRAFT_COMPLETE

### Objective

Aggregate all refactorable findings from:

- `.sessions/TEAM_006_DAT_SSOT_CHANGE_PLAN.md`
- `.sessions/TEAM_007_DAT_REFACTOR_PLAN.md`
- `.sessions/TEAM_008_DAT_IMPLEMENTATION_CHANGE_PLAN.md`
- `.sessions/TEAM_009_DAT_DETERMINISTIC_CHANGE_PLAN.md`
- `.sessions/TEAM_010_DAT_REFACTOR_CHANGE_PLAN.md`

…into a single **cohesive, deduplicated, and validated** final report.

This report also:

- Scores each TEAM by how many **real + validated** gaps they identified vs. how many claims were **invalid/unsubstantiated**.
- Calls out **SSoT conflicts** discovered during validation (Tier-0 vs ADR/SPEC mismatches).

---

## 1. Methodology

### 1.1 What counts as a “gap”

A “gap” is a **concrete mismatch** between current implementation and SSoT requirements (Tier-0 contracts + accepted ADRs + accepted SPECs), or an internal SSoT inconsistency that must be resolved before implementation.

### 1.2 Validation categories

- **Validated**: Directly confirmed in code and/or Tier-0 contracts/ADRs/SPECs (with citations).
- **Partially Valid**: The underlying issue is real, but the TEAM’s claim is **overstated**, **mis-scoped**, or misses key nuance.
- **Invalid**: Claim contradicts the codebase or contradicts the authoritative SSoT.
- **Unclear**: Could not be conclusively validated without running code / deeper exploration.

### 1.3 Scoring

For each TEAM:

- **Claimed**: Number of distinct gap-claims extracted from the session file.
- **Validated**: Count of claims marked Validated.
- **Invalid**: Count of claims marked Invalid.
- **Partial**: Count of claims marked Partially Valid.
- **Unclear**: Count of claims marked Unclear.

**Precision Score (%)** = `Validated / Claimed`.

Note: “Partial” and “Unclear” are not counted as Validated; they reduce precision.

---

## 2. Canonical Gap Catalog (Deduped, Evidence-Backed)

Each gap below is listed once, with references to the TEAMS that identified it.

### GAP-001: API versioning (/v1) contradicts ADR-0030 (cross-tool + gateway + frontend)

- Validation Status: Validated

- SSoT:
  - ADR-0030 requires unversioned-by-default:
    - cross-tool: `/api/{resource}`
    - tool-specific: `/api/{tool}/{resource}`
    - suffix versioning only on breaking changes
  - Evidence: `.adrs/core/ADR-0029_API-Versioning-and-Endpoint-Naming.json:L23-90`

- Evidence (Gateway):
  - Gateway mounts cross-tool routers at `/api/v1/...`:
    - `gateway/main.py:L41-45`

- Evidence (DAT tool API):
  - DAT router explicitly uses `/v1` prefix:
    - `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py:L38-40`

- Evidence (SOV tool API):
  - SOV router uses `/v1` prefix:
    - `apps/sov_analyzer/backend/src/sov_analyzer/api/routes.py:L29-31`

- Evidence (PPTX tool API):
  - PPTX app includes routers at `/v1/...`:
    - `apps/pptx_generator/backend/main.py:L84-98`

- Evidence (Gateway pipeline dispatch):
  - Pipeline service hardcodes `/api/{tool}/v1`:
    - `gateway/services/pipeline_service.py:L30-36`

- Evidence (DAT frontend):
  - Frontend calls `/api/dat/v1/...`:
    - `apps/data_aggregator/frontend/src/hooks/useRun.ts:L15-27`
    - `apps/data_aggregator/frontend/src/components/stages/PreviewPanel.tsx:L26-27`

- Teams that identified:
  - TEAM_006, TEAM_007, TEAM_009

- Recommended remediation (high-level):
  - Remove tool router `/v1` prefixes and remove gateway cross-tool `/api/v1` prefixes.
  - Replace with ADR-0030 canonical paths.
  - Update pipeline dispatch URLs, tests, and all frontend fetch paths.

---

### GAP-002: Duplicate adapter stacks (contract-style vs legacy) create SSoT drift risk

- Validation Status: Validated

- Evidence (two stacks exist):
  - Contract-style adapters:
    - `apps/data_aggregator/backend/adapters/*`
  - Legacy adapters used by current pipeline endpoints:
    - `apps/data_aggregator/backend/src/dat_aggregation/adapters/*`

- Evidence (directory listings):
  - `apps/data_aggregator/backend/adapters/` contains full contract-style adapters:
    - csv/excel/json/parquet + registry
  - `apps/data_aggregator/backend/src/dat_aggregation/adapters/` contains legacy adapters and a separate registry

- Evidence (legacy adapters are actively used):
  - `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py:L19-20` imports legacy `AdapterFactory`

- Teams that identified:
  - TEAM_006, TEAM_007, TEAM_009

- Recommended remediation (high-level):
  - Converge on **one** adapter stack.
  - Prefer Tier-0 contract-aligned adapters in `apps/data_aggregator/backend/adapters/*`.
  - Remove/replace legacy adapter stack usage in `src/dat_aggregation/*`.

---

### GAP-003: Stage graph configuration exists but is not the single source of truth (hardcoded dicts in state machine)

- Validation Status: Validated

- Evidence (hardcoded gates/cascades):
  - `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py:L40-71` defines `FORWARD_GATES` and `CASCADE_TARGETS` as module-level dicts.

- Evidence (config module exists):
  - `apps/data_aggregator/backend/src/dat_aggregation/core/stage_graph_config.py` defines `StageGraphConfig` and validation.

- Evidence (config not used):
  - `DATStateMachine` in `state_machine.py` does not accept or reference `StageGraphConfig`.

- Teams that identified:
  - TEAM_006, TEAM_007

- Recommended remediation (high-level):
  - Make a single authoritative stage-graph module used by:
    - forward gating
    - cascade unlock
    - UI `current_stage` computation
  - Decide whether stage graph belongs in Tier-0 contracts or is an internal module (see GAP-011: SSoT decisions).

---

### GAP-004: Optional stage semantics are broken for “skip” and for current_stage progression

- Validation Status: Validated

This is a *behavioral* bug: the workflow can get stuck on optional stages.

- Evidence (current_stage algorithm is linear and treats optional stages as blocking):
  - `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py:L122-143`
  - `stage_order` includes `Stage.CONTEXT` and `Stage.PREVIEW`.

- Evidence (Preview lock sets completed=false by design):
  - `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py:L839-847`

- Evidence (Preview skip calls lock, does not mark completed):
  - `apps/data_aggregator/frontend/src/components/stages/PreviewPanel.tsx:L118-123`

- Evidence (Parse gating does NOT require Preview):
  - `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py:L47-50` (PARSE gate is TABLE_SELECTION only)

- SSoT nuance:
  - SPEC-0022 defines three-state semantics (UNLOCKED/LOCKED/COMPLETED).
  - It explicitly defines `skip_complete` behavior where skip should result in completed=true.
  - Evidence: `docs/specs/core/SPEC-0044_Stage-Completion-Semantics.json:L64-69`

- Teams that identified:
  - TEAM_006, TEAM_009

- Recommended remediation (high-level):
  - Implement a skip path for optional stages:
    - either don’t lock at all
    - or lock with `completed=true` when skip is chosen
  - Make `current_stage` computation graph-aware and optional-stage-aware.

---

### GAP-005: Deterministic Stage ID generation mismatched vs Tier-0 contract and includes non-portable inputs

- Validation Status: Validated

- Evidence (implementation uses shared.utils.stage_id.compute_stage_id):
  - `apps/data_aggregator/backend/src/dat_aggregation/core/state_machine.py:L110-120`

- Evidence (shared.utils.stage_id uses 16 hex chars + optional prefix):
  - `shared/utils/stage_id.py:L1-47`

- Evidence (Tier-0 contract expects 8-char prefix by default):
  - `shared/contracts/core/id_generator.py:L35-48`
  - `shared/contracts/core/id_generator.py:L269-309` (`compute_deterministic_id`, default prefix_length=8)

- Evidence (absolute path appears in discovery inputs):
  - `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py:L234-235` uses `{"root_path": str(source_path)}`
  - `source_path` is derived from user-provided OS path.

- Teams that identified:
  - TEAM_006, TEAM_007, TEAM_009

- Recommended remediation (high-level):
  - Align DAT stage IDs to Tier-0 `compute_deterministic_id` (8-char default), and enforce stable, stage-specific inputs.
  - Eliminate absolute paths (or strictly normalize to workspace-relative).

---

### GAP-006: Path safety violations in stage inputs and outputs (conflicts with Tier-0 contracts)

- Validation Status: Validated

- Tier-0 contract requires relative paths for Discovery/Parse configs:
  - `shared/contracts/dat/stage.py:L167-206` validates `root_paths` are relative
  - `shared/contracts/dat/stage.py:L155-165` validates `source_paths` are relative

- Evidence (Discovery API accepts absolute OS paths + returns absolute paths):
  - `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py:L192-245` accepts `folder_path` and returns `files[].path` as `str(f.path)`.

- Teams that identified:
  - TEAM_006, TEAM_007, TEAM_009

- Recommended remediation (high-level):
  - Decide on one of:
    - **Strict**: accept only workspace-relative paths
    - **Hybrid**: accept absolute in request, but normalize to relative for persisted artifacts and all responses
  - Enforce with Tier-0 `RelativePath` contract (if available) and tests.

---

### GAP-007: Table availability implementation is not “probe-only” and will be slow for large files

- Validation Status: Validated

- Evidence (table availability endpoint reads full dataframes):
  - `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py:L596-646` reads `full_df = adapter.read(...)` to compute counts.
  - `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py:L649-706` does the same inside stage lock.

- Evidence (stage implementation also reads full table):
  - `apps/data_aggregator/backend/src/dat_aggregation/stages/table_availability.py:L73-99`

- SSoT:
  - ADR-0008 requires deterministic availability checks independent from Preview.
    - Evidence: `.adrs/dat/ADR-0006_Table-Availability.json:L22-30`

- Teams that identified:
  - TEAM_006, TEAM_007, TEAM_009

- Recommended remediation (high-level):
  - Add a fast probe API that uses lightweight metadata/schema probing.
  - Ensure it is independent from Preview.

---

### GAP-008: Large file streaming strategy is not implemented in the active parse path

- Validation Status: Validated

- Evidence (parse uses eager reads via AdapterFactory.read_file):
  - `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py:L201-203` calls `AdapterFactory.read_file(...)`.

- Evidence (legacy CSV adapter is eager-only):
  - `apps/data_aggregator/backend/src/dat_aggregation/adapters/csv_adapter.py:L17-33` uses `pl.read_csv`.

- Teams that identified:
  - TEAM_006, TEAM_007, TEAM_009

- Recommended remediation (high-level):
  - Route parse for files > 10MB through streaming codepaths (LazyFrame scan + chunking).
  - Align adapters and stage logic to support streaming.

---

### GAP-009: Profile management is incomplete (only list endpoint; CRUD/validation missing)

- Validation Status: Validated

- Evidence (profiles endpoint exists but is list-only):
  - `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py:L577-594` implements `GET /profiles`.
  - No `POST/PUT/DELETE /profiles` endpoints found.

- Teams that identified:
  - TEAM_006

- Recommended remediation (high-level):
  - Implement CRUD + validation endpoints per SPEC-0007.

---

### GAP-010: Cancellation is present but incomplete vs full ADR-0014/SPEC-0010 requirements

- Validation Status: Partially Valid

- Evidence (parse cancellation endpoint exists):
  - `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py:L487-518`

- Evidence (parse stage supports cancellation token and checkpoints):
  - `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py:L118-227`

- What’s incomplete / unclear without deeper inspection:
  - No explicit cleanup API (dry-run default) identified in validated reads.
  - Audit log is created but persistence/retention semantics were not validated here.

- Teams that identified:
  - TEAM_007 (as a requirement), TEAM_008 (as missing), TEAM_009 (as milestone)

- Recommended remediation (high-level):
  - Ensure cancel behavior matches Tier-0 cancellation contracts end-to-end (including cleanup and audit trail persistence).

---

### GAP-011: StageGraph Tier-0 contract missing (or stage graph SSOT decision unresolved)

- Validation Status: Validated (Architectural / SSOT gap)

- Evidence:
  - No `StageGraphConfig` / `StageDefinition` / `GatingRule` models exist in `shared/contracts/**`.
  - `stage_graph_config.py` is currently an internal module.

- Teams that identified:
  - TEAM_006, TEAM_009 (as an open question)

- Recommended remediation (high-level):
  - Decide the SSOT location:
    - Tier-0 contract (preferred if stage graph is a “public” contract for UI and orchestration)
    - or internal module (if it’s strictly internal)

---

### GAP-012: SSoT internal inconsistencies discovered during validation

- Validation Status: Validated (SSoT conflict)

This is not “code drift” — it’s **documentation/contract drift inside the SSoT itself**.

#### GAP-012.A: ADR-0030 says “no /v1 by default”, but SPEC-0022 hardcodes /api/dat/v1

- ADR-0030 (unversioned default):
  - `.adrs/core/ADR-0029_API-Versioning-and-Endpoint-Naming.json:L23-90`

- SPEC-0022 (hardcoded `/api/dat/v1/...`):
  - `docs/specs/core/SPEC-0044_Stage-Completion-Semantics.json:L71-94`

**Interpretation**:

- ADR is higher-tier than SPEC and is the accepted decision.
- SPEC-0022 should be updated to match ADR-0030 path conventions.

#### GAP-012.B: ADR-0008 status model vs Tier-0 `TableAvailabilityStatus` enum appear inconsistent

- **ADR-0008** enumerates statuses: available, partial, missing, empty.
  - `.adrs/dat/ADR-0006_Table-Availability.json:L22-30`

- **Tier-0 contract** defines statuses: pending/parsing/available/partial/failed/stale.
  - `shared/contracts/dat/table_status.py:L24-39`

**Interpretation**:

- Tier-0 contracts are authoritative in this repo’s 4-tier model.
- Either ADR-0008 must be updated, or the Tier-0 contract must be revised (breaking change) — but this needs an explicit decision.

---

## 3. Per-TEAM Gap Claims (with Validity)

### 3.1 TEAM_006

**Primary strengths**:

- Most concrete, code-referenced misalignments (API, adapters, IDs, optional stages).

**Claim inventory**

| Claim | Status | Notes / Evidence | Maps to |
| --- | --- | --- | --- |
| Gateway cross-tool mounts use `/api/v1/*` | Validated | `gateway/main.py:L41-45` | GAP-001 |
| DAT router uses `APIRouter(prefix="/v1")` | Validated | `dat api routes.py:L38-40` | GAP-001 |
| SOV router uses `/v1` | Validated | `sov routes.py:L29-31` | GAP-001 |
| PPTX routers use `/v1` | Validated | `pptx main.py:L84-98` | GAP-001 |
| Gateway pipeline dispatch hardcodes `/api/{tool}/v1` | Validated | `pipeline_service.py:L30-36` | GAP-001 |
| DAT frontend uses `/api/dat/v1` | Validated | `useRun.ts:L15-27`, `PreviewPanel.tsx:L26-27` | GAP-001 |
| Stage graph hardcoded in FSM | Validated | `state_machine.py:L40-71` | GAP-003 |
| StageGraphConfig exists but unused | Validated | `stage_graph_config.py`, no usage in FSM | GAP-003 |
| Optional stages block progression (preview) | Validated | `routes.py:L122-143` + `lock_preview completed=false` | GAP-004 |
| Preview skip doesn’t complete | Validated | `PreviewPanel.tsx:L118-123` | GAP-004 |
| Stage ID util mismatch (16 vs 8) | Validated | `shared/utils/stage_id.py` vs `contracts/core/id_generator.py` | GAP-005 |
| Discovery stage ID inputs include absolute paths | Validated | `dat routes.py:L234-235` | GAP-005/GAP-006 |
| Table availability reads full DF | Validated | `dat routes.py:L596-706` | GAP-007 |
| Duplicate adapter stacks | Validated | both adapter directories exist | GAP-002 |
| Profile CRUD not implemented (list-only) | Validated | `dat routes.py:L577-594`; no POST/PUT/DELETE | GAP-009 |

**TEAM_006 gaps (missed items)**

- Did not call out SSoT conflicts discovered later (GAP-012).

---

### 3.2 TEAM_007

**Primary strengths**:

- Clean, concise gap set; correct prioritization (routing → stage graph → IDs → adapters → probe).

**Claim inventory**

| Claim | Status | Notes / Evidence | Maps to |
| --- | --- | --- | --- |
| `/api/dat/v1` should be `/api/dat` | Validated | `dat routes.py:L38-40` and ADR-0030 | GAP-001 |
| Hardcoded `FORWARD_GATES` should be config-driven | Validated | `state_machine.py:L40-71` | GAP-003 |
| Optional Context/Preview must not block Parse | Validated | `routes.py:L122-143` + PARSE gate is TABLE_SELECTION | GAP-004 |
| Absolute paths in IDs break determinism | Validated | `routes.py:L234-235` | GAP-005/GAP-006 |
| Table scan should be probe-only | Validated | `routes.py:L596-706` | GAP-007 |
| Adapter implementation split | Validated | two adapter stacks exist | GAP-002 |

**TEAM_007 gaps (missed items)**

- Did not mention gateway cross-tool `/api/v1` mounts.
- Did not mention profile CRUD gap.
- Did not mention SSoT conflicts (GAP-012).

---

### 3.3 TEAM_008

**Primary strengths**:

- Strong execution planning structure and acceptance criteria.

**Claim inventory (focus on “gap analysis” claims)**

| Claim | Status | Notes / Evidence | Maps to |
| --- | --- | --- | --- |
| Adapter implementation missing | Partially Valid | Contract-style adapters exist (`backend/adapters/*`), but active pipeline uses legacy adapters (`src/dat_aggregation/adapters/*`). Gap is “integration”, not “missing adapters”. | GAP-002 |
| Profile CRUD + validation missing | Validated | Only `GET /profiles` exists | GAP-009 |
| Table status probe + reporting missing | Validated | Current code reads full DFs; no probe-only path | GAP-007 |
| Cancellation + cleanup missing | Partially Valid | Parse cancel exists + checkpointing exists; cleanup semantics not validated | GAP-010 |
| API routes incomplete vs spec | Partially Valid | Routes exist, but ADR-0030 mismatch is the bigger confirmed gap | GAP-001 |

**TEAM_008 gaps (missed items)**

- Did not clearly call out ADR-0030 mismatch as a concrete implementation bug.
- Some “missing” claims are overbroad (adapters exist but are duplicated/not integrated).
- Did not call out SSoT conflicts (GAP-012).

---

### 3.4 TEAM_009

**Primary strengths**:

- Best overall “misalignment snapshot” list; tight mapping to staged milestones.

**Claim inventory**

| Claim | Status | Notes / Evidence | Maps to |
| --- | --- | --- | --- |
| Duplicate adapter stacks | Validated | Both adapter directories exist | GAP-002 |
| DAT router uses `/v1` (contradicts ADR-0030) | Validated | `dat routes.py:L38-40` + ADR-0030 | GAP-001 |
| Optional stages not correctly reflected in progression | Validated | `current_stage` algorithm is linear, includes optional stages | GAP-004 |
| Deterministic IDs mismatch (16 vs 8) + absolute path inputs | Validated | `shared/utils/stage_id.py` and `routes.py:L234-235` | GAP-005/GAP-006 |
| Table availability too slow / not probe-only | Validated | `routes.py:L596-706` | GAP-007 |

**TEAM_009 gaps (missed items)**

- Did not call out SSoT conflicts (GAP-012).

---

### 3.5 TEAM_010

**Primary strengths**:

- Good narrative alignment to ADRs; useful for onboarding.

**Claim inventory**

TEAM_010 is largely a requirements restatement, but it implies some “gaps”:

| Claim (implied) | Status | Notes / Evidence | Maps to |
| --- | --- | --- | --- |
| Ensure optional stages don’t trigger cascades | Invalid | FSM already sets Context/Preview cascades to empty lists (`state_machine.py:L68-71`). | None |
| Implement deterministic stage IDs with stage-specific inputs | Validated | Current IDs use `shared.utils.stage_id` and include absolute paths; not stage-specific | GAP-005 |
| Table availability must be deterministic and independent of Preview | Validated | Current implementation reads full DFs; still independent of Preview but not probe-only | GAP-007 |
| Adapters must support streaming for >10MB | Validated | Parse uses eager reads; legacy adapters eager-only | GAP-008 |

**TEAM_010 gaps (missed items)**

- Missed ADR-0030 mismatch explicitly (and reinforces the outdated “/v1” convention in places).
- Contains at least one invalid “gap” (optional stage cascade already handled).
- Did not call out SSoT conflicts (GAP-012).

---

## 4. TEAM Scoring Summary

| TEAM | Claimed | Validated | Partial | Invalid | Unclear | Precision (Validated/Claimed) |
| --- | --- | --- | --- | --- | --- | --- |
| TEAM_006 | 15 | 15 | 0 | 0 | 0 | 100% |
| TEAM_007 | 6 | 6 | 0 | 0 | 0 | 100% |
| TEAM_008 | 5 | 2 | 3 | 0 | 0 | 40% |
| TEAM_009 | 5 | 5 | 0 | 0 | 0 | 100% |
| TEAM_010 | 4 | 3 | 0 | 1 | 0 | 75% |

**Notes on scoring**:

- TEAM_008 is penalized because several claims are correct in spirit but **overstated** (“missing” vs “duplicated/not integrated”).
- TEAM_010 is penalized for at least one **already-implemented** item being presented as a gap.

---

## 5. Consolidated, Prioritized Remediation Backlog

1. **Fix ADR-0030 drift (GAP-001)**
   - Remove default `/v1` pathing across gateway/tools/frontends.
2. **Unify adapters (GAP-002)**
   - Remove legacy adapter stack usage from the active pipeline.
3. **Fix optional stage skip/progression (GAP-004)**
   - Implement skip semantics; make current_stage optional-aware.
4. **Stage IDs + path safety alignment (GAP-005 + GAP-006)**
   - Move to Tier-0 ID generator and stable inputs.
5. **Table availability probe-only design (GAP-007)**
   - Replace full reads with lightweight probing.
6. **Large file streaming (GAP-008)**
   - Ensure parse path uses streaming for >10MB.
7. **Profile CRUD + validation (GAP-009)**
   - Implement full lifecycle per SPEC.
8. **Cancellation + cleanup closure (GAP-010)**
   - Ensure full compliance (cleanup + audit persistence).
9. **Resolve SSoT conflicts (GAP-012)**
   - ADR-0030 vs SPEC-0022 path conventions
   - ADR-0008 vs Tier-0 table status enum

---

## 6. Open SSoT Questions / Decisions Needed

1. **API naming conflict**: Update SPEC-0022 to match ADR-0030 (recommended).
2. **Table status model conflict**: Decide whether ADR-0008 status model is updated to match Tier-0, or Tier-0 is revised (breaking change).
3. **Stage graph SSOT**: Decide whether stage graph becomes Tier-0 contract or remains internal.
4. **Path safety policy**: Strict-relative vs hybrid-normalization policy for Discovery/Selection.

---

## 7. Handoff Notes

- This report intentionally avoids duplicating full content from earlier TEAM files; it summarizes and cites.
- Next implementation work should follow the prioritized backlog and should treat Tier-0 contracts as authoritative.
