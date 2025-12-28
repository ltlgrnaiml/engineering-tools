# DAT Tool - Complete UX Flow Specification

## Based on ADRs

- **ADR-0001 (Core)**: Hybrid FSM Architecture for Guided Workflows
- **ADR-0001-DAT**: 8-Stage Pipeline with Lockable Artifacts
- **ADR-0003**: Optional Context and Preview Stages
- **ADR-0006**: Table Availability Status Model
- **ADR-0011**: Profile-Driven Extraction
- **ADR-0014**: Parse/Export Artifact Formats

---

## 8-Stage Pipeline Overview

```
┌──────────────┐     ┌───────────────┐     ┌──────────────────────┐
│  1. DISCOVERY │ ──▶ │  2. SELECTION │ ──▶ │  3. CONTEXT          │
│  (implicit)   │     │  (required)   │     │  (OPTIONAL - skip)   │
└──────────────┘     └───────────────┘     └──────────────────────┘
                              │                        │
                              ▼                        │
┌──────────────────────────────────────────────────────┘
│
▼
┌────────────────────────┐     ┌────────────────────────┐
│  4. TABLE AVAILABILITY │ ──▶ │  5. TABLE SELECTION    │
│  (required)            │     │  (required)            │
└────────────────────────┘     └────────────────────────┘
                                          │
                                          ▼
┌──────────────────────┐     ┌───────────┐     ┌───────────┐
│  6. PREVIEW          │     │  7. PARSE │ ──▶ │  8. EXPORT│
│  (OPTIONAL - skip)   │     │ (required)│     │ (terminal)│
└──────────────────────┘     └───────────┘     └───────────┘
```

---

## Stage-by-Stage UX Flow

### Stage 1: Discovery (Implicit)

**Purpose**: Scan filesystem for available files.

**UX Behavior**:
- Happens automatically when user specifies a folder path
- User does NOT see a separate "Discovery" panel
- Discovery is locked when user scans a folder (part of Selection workflow)

**Per ADR-0001-DAT**: Discovery is marked `implicit: true` - it's a technical stage that happens behind the scenes.

---

### Stage 2: Selection (File Selection)

**Purpose**: User selects which files to include in aggregation.

**UX Flow**:
1. User enters folder path
2. Click "Scan" → Backend scans directory, discovers files
3. Files displayed in list with checkboxes
4. User can filter by extension
5. User can Select All / Clear selection
6. Click "Continue" →
   - Discovery stage is locked (with scanned folder)
   - Selection stage is locked (with selected files)
7. Navigate to next stage

**Required UI Elements**:
- Folder path input
- Scan button
- File list with checkboxes (path, name, extension, size)
- Extension filter dropdown
- Select All / Clear buttons
- File count indicator
- **BACK button** (if coming from later stage)
- Continue button

**Validation**:
- At least 1 file must be selected

---

### Stage 3: Context (OPTIONAL)

**Purpose**: Set profile and aggregation configuration hints.

**UX Flow**:
1. User sees current profile settings
2. User can optionally configure:
   - Profile selection
   - Aggregation levels
   - Custom context hints
3. User can either:
   - Click "Continue" → Lock context with settings
   - Click "Skip" → Proceed without locking context

**Per ADR-0003**:
- Context is OPTIONAL
- Parse/Export will use profile defaults if context is skipped
- Context does NOT cascade unlocks to downstream stages

**Required UI Elements**:
- Profile selector (dropdown)
- Aggregation level configuration
- Context hints editor (optional)
- **Skip button** (proceeds without locking)
- Continue button (locks context)
- **BACK button** (unlocks Selection, cascades downstream)

---

### Stage 4: Table Availability

**Purpose**: Show user which tables are available in selected files.

**UX Flow**:
1. Backend scans selected files for tables
2. Display table list with status:
   - **available** (✓ green): Table found with data
   - **partial**: Table found but incomplete
   - **missing** (✗ red): Table expected but not found
   - **empty**: Table found but no rows
3. Show row count and column count for each table
4. User reviews availability
5. Click "Continue" → Lock table availability

**Per ADR-0006**:
- Status model is deterministic and reproducible
- Status must be surfaced BEFORE parse
- Independent from Preview stage

**Required UI Elements**:
- Table list with status icons
- Row count per table (MUST show actual counts, not 0)
- Column count per table
- Source file path per table
- Summary (X of Y tables available)
- Progress bar
- Continue button
- **BACK button** (unlocks Selection, cascades)

---

### Stage 5: Table Selection

**Purpose**: User chooses which tables to include in parse/export.

**UX Flow**:
1. Display all available tables from previous stage
2. Each table has a checkbox
3. User selects tables to include
4. User can Select All / Clear
5. Click "Continue" → Lock table selection

**Required UI Elements**:
- Table grid with checkboxes
- Table name, row count, column count per table
- Source file per table
- Select All / Clear buttons
- Selected count indicator
- Continue button
- **BACK button** (unlocks Table Availability, cascades)

**Validation**:
- At least 1 table must be selected

---

### Stage 6: Preview (OPTIONAL)

**Purpose**: Preview extraction results before full parse.

**UX Flow**:
1. User sees preview of selected tables
2. Shows first N rows of each table
3. User can verify data looks correct
4. User can either:
   - Click "Continue" → Lock preview, proceed to Parse
   - Click "Skip" → Proceed to Parse without preview

**Per ADR-0003**:
- Preview is OPTIONAL
- Parse does NOT require preview.json to exist
- Preview does NOT cascade unlocks

**Required UI Elements**:
- Table preview grid (first 100 rows)
- Column headers
- Data type indicators
- Skip button
- Continue button
- **BACK button** (unlocks Table Selection, cascades)

---

### Stage 7: Parse

**Purpose**: Execute full data extraction to Parquet.

**UX Flow**:
1. User clicks "Start Parse"
2. Progress indicator shows extraction status
3. Can be cancelled (preserves partial artifacts per ADR-0013)
4. On completion:
   - Parquet file created
   - Manifest.json created
   - Prep report generated
5. Click "Continue" → Proceed to Export

**Per ADR-0014**:
- Parse output is ALWAYS Parquet
- Metadata is always JSON/YAML
- Parquet for scalability, columnar storage, schema enforcement

**Required UI Elements**:
- Start Parse button
- Progress bar with percentage
- Cancel button (during parse)
- Success/error status
- Output file location
- Continue button (after success)
- **BACK button** (unlocks Table Selection, cascades)

---

### Stage 8: Export (Terminal)

**Purpose**: Export parsed data in user-selected format.

**UX Flow**:
1. User selects output format:
   - Parquet (default)
   - CSV
   - TSV
   - JSON
   - Excel
2. User configures export options
3. Click "Export" → Generate output file
4. Show download link or file location
5. Pipeline complete

**Per ADR-0014**:
- Export format is user-selectable at runtime
- Metadata remains in canonical JSON/YAML format
- Data can be exported in any supported format

**Gating Requirement (ADR-0001-DAT)**:
- Export REQUIRES Parse.locked == true AND Parse.completed == true

**Required UI Elements**:
- Format selector dropdown
- Export options (encoding, compression, etc.)
- Export button
- Progress indicator
- Download link / file location
- Success message
- "Start New Run" button
- **BACK button** (unlocks Parse, cascades)

---

## Backward Navigation (Critical Missing Feature)

### Per ADR-0001 Core FSM and ADR-0002 Artifact Preservation

Users MUST be able to go backward to any previous stage.

**Backward Navigation Rules**:

1. **Unlock with Cascade**: When user goes back to Stage N:
   - Stage N is unlocked
   - All stages after N are automatically unlocked
   - All artifacts are PRESERVED (locked: false, not deleted)

2. **Re-lock Preserves Artifacts**: When user re-locks with same inputs:
   - Deterministic stage ID matches previous
   - Existing artifact is reused (idempotent)

3. **Cascade Behavior** (per ADR-0001-DAT):
   ```
   Unlock Discovery  → Unlocks ALL downstream stages
   Unlock Selection  → Unlocks Context, Table Availability, Table Selection, Preview, Parse, Export
   Unlock Context    → NO cascade (optional stage)
   Unlock Table Avail→ Unlocks Table Selection, Preview, Parse, Export
   Unlock Table Sel  → Unlocks Preview, Parse, Export
   Unlock Preview    → NO cascade (optional stage)
   Unlock Parse      → Unlocks Export
   ```

4. **UI Implementation**:
   - Each stage panel MUST have a "Back" or "Edit Previous" button
   - Clicking navigates to previous stage
   - Backend unlock is called with cascade=true
   - Frontend refreshes stage status

---

## Stage Sidebar Navigation

**Current Issue**: Sidebar stages are display-only, not clickable.

**Required Behavior**:

1. **Completed stages (✓)**: Should be clickable
   - Click → Unlock that stage and all downstream
   - Navigate to that stage panel

2. **Current stage**: Highlighted, active panel displayed

3. **Future stages**: Grayed out, not clickable (forward gating)

**Visual States**:
- **Active**: Green highlight, current panel
- **Completed**: Checkmark, clickable to revisit
- **Locked (future)**: Gray, disabled

---

## Current Bugs Identified

### Bug 1: Row Counts Show 0

**Location**: `routes.py:628-630`
```python
tables.append({
    "name": table,
    "file": file_path,
    "available": True,
    "row_count": 0,      # ← HARDCODED TO 0
    "column_count": 0,   # ← HARDCODED TO 0
})
```

**Fix**: Actually read the table data and count rows/columns.

### Bug 2: Only 18 of 36 Tables Selectable

**Possible Causes**:
- Adapter throwing exceptions for some files
- Table names being duplicated and overwriting
- Frontend rendering issue

**Investigation Needed**: Check adapter logs, validate table discovery.

### Bug 3: No Backward Navigation

**Root Cause**: Frontend has no UI to trigger unlock endpoints.

**Fix Needed**:
- Add Back button to each stage panel
- Make sidebar stages clickable
- Call `POST /runs/{run_id}/stages/{stage}/unlock` on back navigation

---

## API Endpoints Required

### Stage Lock Endpoints (Existing)
- `POST /runs/{run_id}/stages/discovery/lock`
- `POST /runs/{run_id}/stages/selection/lock`
- `POST /runs/{run_id}/stages/context/lock`
- `POST /runs/{run_id}/stages/table_availability/lock`
- `POST /runs/{run_id}/stages/table_selection/lock`
- `POST /runs/{run_id}/stages/preview/lock`
- `POST /runs/{run_id}/stages/parse/lock`
- `POST /runs/{run_id}/stages/export/lock`

### Stage Unlock Endpoint (Existing but unused by frontend)
- `POST /runs/{run_id}/stages/{stage}/unlock`

### Stage Scan/Preview Endpoints
- `POST /runs/{run_id}/stages/selection/scan`
- `GET /runs/{run_id}/stages/table_availability/scan`
- `GET /runs/{run_id}/stages/table_selection/tables`

---

## Summary of Required Fixes

| Priority | Issue | Fix |
|----------|-------|-----|
| **P0** | Row counts show 0 | Read actual data from tables |
| **P0** | No backward navigation | Add Back buttons, make sidebar clickable |
| **P1** | Only 18/36 tables | Debug adapter, check for exceptions |
| **P1** | Skip buttons missing | Add Skip for Context/Preview stages |
| **P2** | Better error handling | Show user-facing error messages |
| **P2** | Progress indicators | Add progress bars for long operations |

---

## Quick Reference: Stage Dependencies

```
Stage                  | Required Upstream | Cascade on Unlock
-----------------------|-------------------|------------------
Discovery              | (none)            | All stages
Selection              | Discovery         | Context → Export
Context (optional)     | Selection         | None
Table Availability     | Selection         | Table Sel → Export
Table Selection        | Table Availability| Preview → Export
Preview (optional)     | Table Selection   | None
Parse                  | Table Selection   | Export
Export                 | Parse (completed) | None (terminal)
```
