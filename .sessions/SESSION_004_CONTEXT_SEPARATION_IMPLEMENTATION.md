# SESSION_004: Context Separation Implementation

**Date**: 2025-12-29  
**Status**: COMPLETED  
**Scope**: Implement context separation in profile-driven ETL architecture

---

## Objective

Implement the context separation pattern per DESIGN §4, §9 where:
- Raw data tables are extracted WITHOUT context baked in
- Context is stored separately (run-level and image-level)
- User controls context application via simple checkboxes at output time

## Problem Statement

The previous implementation in `ProfileExecutor.execute()` automatically applied context to ALL tables during extraction. There was no user control over which context columns were added to output.

**User requirement**: "Context should be separated from the raw data tables, as the context can be applied to each of the output tables that the user selects if available and the user has selected it."

## Changes Made

### 1. ProfileExecutor (`profile_executor.py`)

- **Added `ExtractionResult` dataclass** with separated fields:
  - `tables`: Dict[str, DataFrame] - raw tables without context
  - `run_context`: Dict[str, Any] - run-level context values
  - `image_contexts`: Dict[str, Dict] - image-level context by image_id
  - `file_contexts`: Dict[str, Dict] - per-file context values
  - `validation_warnings`: List[str]

- **Added methods on ExtractionResult**:
  - `apply_run_context()` - apply run context to specified tables
  - `apply_image_context()` - apply image context based on image_id
  - `get_tables_with_context()` - primary method with toggle flags

- **Updated `execute()` method**:
  - Added `apply_context: bool = False` parameter
  - Returns `ExtractionResult` instead of `dict[str, DataFrame]`
  - Context extracted and stored separately by default

- **Added helper methods**:
  - `_extract_file_context()` - extract context from single file
  - `_extract_image_contexts()` - extract image-level context
  - `_get_nested_value()` - utility for dot-notation path access

### 2. OutputBuilder (`output_builder.py`)

- **Added `ContextOptions` dataclass**:
  - `include_run_context: bool = True`
  - `include_image_context: bool = False`
  - `run_context_keys: list[str] | None` - specific keys to include
  - `image_context_keys: list[str] | None`

- **Updated `build_outputs()` method**:
  - Added `run_context`, `image_contexts`, `context_options` parameters
  - Context applied based on user options, not baked in

- **Added `_apply_image_context_to_df()` method**:
  - Joins image context to DataFrame based on image_id column

### 3. API Schemas (`schemas.py`)

- **Added `ContextOptionsRequest`** - Pydantic model for API requests
- **Added `ContextInfo`** - response model with context information
- **Added `ExtractionResponse`** - full response with separated tables/context
- **Updated `ParseRequest`** - added `context_options` field
- **Updated `TableSelectionRequest`** - added `context_options` field

### 4. API Routes (`routes.py`)

- **Updated `/runs/{run_id}/stages/parse/profile-extract`**:
  - Returns `ExtractionResponse` with separated tables and context
  - Documents available context keys for UI checkbox rendering

- **Added `/runs/{run_id}/stages/parse/apply-context`**:
  - New endpoint for user-controlled context application
  - Accepts `ContextOptionsRequest` with toggle flags
  - Returns tables with context applied per user selection

### 5. Tests (`test_context_separation.py`)

- Added comprehensive tests for:
  - `ExtractionResult` dataclass methods
  - `ContextOptions` defaults and configuration
  - `OutputBuilder` context application
  - Acceptance criteria validation

### 6. Documentation (`DESIGN_Profile-Driven-ETL-Architecture.md`)

- Added section **9.1 Context Separation Architecture**:
  - ASCII diagram showing extraction → selection → output flow
  - API endpoint documentation
  - Benefits of the approach

## Files Modified

| File | Changes |
|------|---------|
| `profile_executor.py` | +150 lines (ExtractionResult, helper methods) |
| `output_builder.py` | +80 lines (ContextOptions, context application) |
| `schemas.py` | +80 lines (new request/response models) |
| `routes.py` | +100 lines (new endpoint, updated profile-extract) |
| `test_context_separation.py` | NEW - 200 lines |
| `DESIGN_Profile-Driven-ETL-Architecture.md` | +120 lines (§9.1) |

## API Usage Example

```python
# 1. Extract tables and context (separately)
POST /api/dat/runs/{run_id}/stages/parse/profile-extract

# Response shows raw tables + available context
{
    "tables_extracted": 5,
    "context": {
        "run_context": {"LotID": "LOT123", "WaferID": "W01"},
        "available_run_keys": ["LotID", "WaferID", "RecipeName"],
        "available_image_keys": ["ImageName", "AcquisitionTime"]
    }
}

# 2. User checks boxes in UI, then applies context
POST /api/dat/runs/{run_id}/stages/parse/apply-context
{
    "include_run_context": true,
    "include_image_context": false
}

# Response: tables with selected context columns added
```

## Verification Checklist

- [x] ProfileExecutor returns ExtractionResult with separated tables/context
- [x] OutputBuilder accepts context toggle options
- [x] API exposes context options to frontend
- [x] Tests cover key scenarios
- [x] Documentation updated with architecture diagram

## Next Steps

1. Frontend implementation of context toggle checkboxes
2. Caching of ExtractionResult to avoid re-extraction on apply-context
3. Integration tests with real profile/data files

---

## Session Handoff

- [x] All code changes complete
- [x] Tests added (not run - need pytest execution)
- [x] Documentation updated
- [ ] Frontend UI needs implementation
- [ ] Integration tests need verification
