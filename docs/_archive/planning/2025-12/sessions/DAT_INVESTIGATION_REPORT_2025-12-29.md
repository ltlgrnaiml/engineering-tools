# DAT Investigation Report: UI Issues and Profile Usage Analysis

**Date**: 2025-12-29  
**Context**: User successfully generated a dataset, but UI interactions are not working as expected

---

## Executive Summary

This report documents findings from investigating:
1. Non-functional "Complete Export" button
2. "View Dataset", "Analyze with SOV", "Generate Report" buttons redirecting to start
3. Dataset preview showing `[object Object]`  
4. PPTX "Pipe to" action returning 404 errors
5. Whether `cdsem_metrology_profile.yaml` is being used

**Key Finding**: The profile YAML exists but its extraction logic is **NOT BEING APPLIED**. The parse stage reads raw files without using the profile's JSONPath table extraction definitions, resulting in nested JSON objects stored as column values.

---

## Issue 1: "Complete Export" Button Does Nothing

### Evidence

**Location**: `@/apps/data_aggregator/frontend/src/components/wizard/DATWizard.tsx:324-336`

```tsx
{isLastStage && (
  <button
    onClick={onNext}
    disabled={nextDisabled || isLoading}
    className="..."
  >
    {isLoading ? 'Exporting...' : 'Complete Export'}
  </button>
)}
```

### Root Cause

The "Complete Export" button calls `onNext`, but this callback **may not be wired to trigger any action** in the parent component when on the final stage. The ExportPanel.tsx already has an "Export DataSet" button that triggers `exportMutation.mutate()` - creating a disconnect between:

1. The wizard's "Complete Export" button (calls `onNext`)
2. The ExportPanel's "Export DataSet" button (calls the actual export mutation)

### Expected per ADRs

Per ADR-0001-DAT (8-stage pipeline), the Export stage should:
- Lock the stage with export execution
- Create a DataSet in shared storage
- Mark the workflow complete

### Recommendation

Either:
- A) Remove "Complete Export" from wizard and keep only ExportPanel's button
- B) Wire `onNext` on final stage to trigger the export mutation

---

## Issue 2: Navigation Buttons Redirect to Start

### Evidence

**Location**: `@/apps/data_aggregator/frontend/src/components/stages/ExportPanel.tsx:64-85`

```tsx
<a href={`/datasets/${exportedDatasetId}`} ...>View Dataset</a>
<a href={`/tools/sov?dataset=${exportedDatasetId}`} ...>Analyze with SOV</a>
<a href={`/tools/pptx?dataset=${exportedDatasetId}`} ...>Generate Report</a>
```

**Location**: `@/apps/homepage/frontend/src/pages/DataAggregatorPage.tsx:1-16`

```tsx
export function DataAggregatorPage() {
  const datAppUrl = isDev ? 'http://localhost:5173' : '/dat-app'
  return (
    <div className="w-full h-screen">
      <iframe src={datAppUrl} ... />
    </div>
  )
}
```

### Root Cause

The DAT frontend runs inside an **iframe** embedded in the Homepage. When clicking `<a href="/datasets/...">` inside the iframe:
- The navigation happens **within the iframe** (not the parent window)
- The DAT SPA has no route for `/datasets/` 
- It likely falls back to its root route, showing "Create New Run"

### Expected per ADRs

Per ADR-0042 (Frontend Iframe Integration Pattern):
- Tool UIs embedded via iframes need to communicate with parent for cross-tool navigation
- Links to other tools/pages should use `window.parent.location` or `postMessage`

### Recommendation

Change navigation buttons to use:
```tsx
onClick={() => window.parent.location.href = `/datasets/${exportedDatasetId}`}
```

Or use a `postMessage` pattern for parent-iframe communication.

---

## Issue 3: Preview Shows `[object Object]`

### Evidence

**Screenshot Analysis**: Preview table shows columns: METADATA, RUN_INFO, SUMMARY, STATISTICS, SITES
All cells display `[object Object]`

**Location**: `@/apps/homepage/frontend/src/pages/DatasetsPage.tsx:280-286`

```tsx
function formatCellValue(value: unknown): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'number') { ... }
  return String(value)  // <-- Objects become "[object Object]"
}
```

### Root Cause (ARCHITECTURAL)

The **profile extraction logic is NOT being applied**. Here's the chain:

1. **Profile YAML** defines sophisticated table extraction:
   ```yaml
   # @/apps/data_aggregator/backend/src/dat_aggregation/profiles/cdsem_metrology_profile.yaml
   levels:
     - name: "run"
       tables:
         - id: "run_summary"
           select:
             strategy: "flat_object"
             path: "$.summary"
   ```

2. **Profile Loader** exists and can parse YAML:
   ```python
   # @/apps/data_aggregator/backend/src/dat_aggregation/profiles/profile_loader.py
   def get_profile_by_id(profile_id: str) -> DATProfile | None:
       profiles = get_builtin_profiles()
       if profile_id in profiles:
           return load_profile(profiles[profile_id])
   ```

3. **Parse Stage** loads profile but DOES NOT USE IT for extraction:
   ```python
   # @/apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py:155-169
   profile: DATProfile | None = None
   if config.profile_id:
       profile = get_profile_by_id(config.profile_id)
   
   # Profile is loaded, but extraction below just reads raw files:
   df, _ = await adapter.read_dataframe(str(file_path), options)  # <-- No profile logic!
   ```

4. **Result**: Raw JSON files are read directly, with top-level keys becoming columns containing nested objects:
   - Column "METADATA" → `{"lot_id": "...", "wafer_id": "..."}`
   - Column "RUN_INFO" → `{"recipe": {...}, "tool": {...}}`
   - etc.

### Expected per ADRs

Per ADR-0011 (Profile-Driven Extraction):
- Profiles are the **Single Source of Truth** for extraction logic
- The profile's `select.strategy` and `select.path` should be used to:
  - Navigate JSONPath to find tables
  - Flatten nested objects per strategy (`flat_object` or `headers_data`)
  - Extract only the specified columns

Per SPEC-DAT-0002 (Profile-Driven Extraction):
- `column_mappings` should define source→target transformations
- Profile structure defines how to parse source data

### What Data SHOULD Look Like

Given the profile defines:
```yaml
- id: "run_summary"
  select:
    strategy: "flat_object"
    path: "$.summary"
  stable_columns:
    - "total_images"
    - "valid_images"
    - "mean_cd"
    - "sigma_cd"
    - "range_cd"
```

The dataset should have **flat columns**:
| total_images | valid_images | mean_cd | sigma_cd | range_cd |
|--------------|--------------|---------|----------|----------|
| 50           | 48           | 45.2    | 1.3      | 4.1      |

**NOT nested objects.**

### Recommendation (ARCHITECTURAL DECISION REQUIRED)

**Option A: Implement Profile Extraction Logic**
- Modify `parse.py` to use profile's `select` config for JSONPath extraction
- Implement `flat_object` and `headers_data` strategies
- This aligns with ADR-0011 but requires significant work

**Option B: Simplify Profile to Match Current Behavior**
- Accept that raw data is read directly
- Remove complex extraction logic from profile YAML
- Add post-processing/flattening in UI or export stage

**Option C: Hybrid Approach**
- Keep current raw read behavior for non-JSON sources
- Add specialized JSON profile extraction only when profile specifies JSON strategy

---

## Issue 4: PPTX "Pipe to" Returns 404

### Evidence

**Screenshot Console Errors**:
```
GET http://localhost:5175/api/v1/projects api.ts:88
404 (Not Found)
```

### Root Cause

PPTX frontend is calling `/api/v1/projects` but per ADR-0029 (Simplified API Naming):
- No version prefix should be used
- Correct endpoint: `/api/pptx/projects`

### Evidence of Correct Pattern

```python
# @/gateway/main.py:128
app.mount("/api/pptx", pptx_app)
```

### Recommendation

Update PPTX frontend API client to use `/api/pptx/projects` instead of `/api/v1/projects`.

---

## Issue 5: Is `cdsem_metrology_profile.yaml` Being Used?

### Answer: **NO** (infrastructure exists, logic not wired)

### Evidence

1. **Profile file exists** at:
   `@/apps/data_aggregator/backend/src/dat_aggregation/profiles/cdsem_metrology_profile.yaml`

2. **Profile loader finds it**:
   ```python
   # @/apps/data_aggregator/backend/src/dat_aggregation/profiles/profile_loader.py:323-338
   def get_builtin_profiles() -> dict[str, Path]:
       profiles_dir = Path(__file__).parent
       for yaml_file in profiles_dir.glob("*.yaml"):
           # ... extracts profile_id from each
   ```

3. **Profile is NOT automatically selected**:
   - Context stage accepts `profile_id` but doesn't default to one
   - Parse stage only loads profile IF `config.profile_id` is set

4. **Profile extraction logic is NOT implemented**:
   - Parse stage loads profile but only uses `context_defaults`
   - The `levels`, `tables`, `select.strategy`, `select.path` are IGNORED
   - Data is read raw via adapters without JSONPath extraction

### Grep Evidence

```bash
grep -r "cdsem" apps/data_aggregator/
# No results - filename/profile_id is never referenced explicitly
```

---

## Summary of Issues

| Issue | Severity | Root Cause | Fix Complexity |
|-------|----------|------------|----------------|
| Complete Export button | Medium | Missing callback wiring | Low |
| Navigation buttons | High | Iframe navigation context | Medium |
| Preview `[object Object]` | Critical | Profile extraction not implemented | High |
| PPTX 404 | High | Wrong API path prefix | Low |
| Profile not used | Critical | Architecture gap | High |

---

## Decisions Required

### Decision 1: Profile Extraction Implementation

The profile YAML defines sophisticated table extraction logic (JSONPath, strategies, column mappings) that is NOT implemented in the parse stage.

**Options**:
- A) **Implement full profile extraction**: Parse stage applies JSONPath selectors, flattens nested data per strategy. Aligns with ADR-0011.
- B) **Simplify expectations**: Accept raw data reads, handle flattening elsewhere. Update ADRs/Contracts to match reality.
- C) **Defer profile extraction**: Focus on getting basic flow working, implement profile logic later as enhancement.

### Decision 2: Iframe Navigation Pattern

Tool frontends run in iframes but need to navigate to parent routes.

**Options**:
- A) Use `window.parent.location.href` for cross-tool links
- B) Implement `postMessage` protocol for parent-child communication
- C) Open cross-tool links in new tabs: `target="_blank"`

### Decision 3: DataSet Preview Handling

When data contains nested objects, preview is unreadable.

**Options**:
- A) Flatten data at parse/export time (profile extraction)
- B) Add nested object rendering in preview UI (expandable cells)
- C) Serialize nested objects to JSON strings for display

---

## Next Steps (Pending Your Input)

1. **Quick Wins** (can fix now):
   - Fix PPTX API path prefix (Low effort)
   - Fix navigation button context (Medium effort)
   - Wire Complete Export button (Low effort)

2. **Architectural Decisions** (need discussion):
   - Profile extraction implementation scope
   - Expected data structure for DataSets
   - Whether to update ADRs/Contracts or implement missing logic

---

*Report generated by CASCADE session*
