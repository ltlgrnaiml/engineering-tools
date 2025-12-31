# SESSION_015: Workflow Manager File Format Fix

**Date**: 2024-12-30
**Focus**: Bug fix for Workflow Manager file type handling

---

## Problem Statement

User reported two issues with the Workflow Manager:
1. `.md` files showing "Invalid JSON content" error
2. ADR/SPEC documents causing blank screen requiring refresh

## Root Cause Analysis

### Issue 1: Invalid JSON content for Markdown files
- **Backend**: `workflow_service.py` scanned only `*.md` for plans, but `.plans/` contains BOTH `.json` and `.md` files
- **Frontend**: `ArtifactReader.tsx` routed ALL `plan` type artifacts to `PlanViewer`
- **PlanViewer**: Did `JSON.parse(content)` expecting JSON - failed for markdown
- **Root cause**: No `file_format` distinction between JSON and Markdown files

### Issue 2: Blank screen for ADR/SPEC
- Unhandled JSON parse errors crashed React component tree
- No error boundary to catch and display errors gracefully

## Solution Implemented

### 1. Contract Update (`shared/contracts/devtools/workflow.py`)
- Added `FileFormat` enum: `json`, `markdown`, `python`, `unknown`
- Added `file_format` field to `ArtifactSummary` model

### 2. Backend Update (`gateway/services/workflow_service.py`)
- Added `_get_file_format()` helper to detect format from extension
- Updated `scan_artifacts()` to scan BOTH `*.json` and `*.md` for plans
- All `_parse_*_artifact()` functions now set `file_format`

### 3. Backend API Update (`gateway/services/devtools_service.py`)
- `get_artifact()` endpoint now includes `file_format` in response

### 4. Frontend Update (`apps/homepage/frontend/src/components/workflow/`)
- `types.ts`: Added `FileFormat` type
- `ArtifactReader.tsx`: 
  - Added `fileFormat` prop and state
  - Detects format from API response or file extension
  - Routes based on `file_format` FIRST, then `artifactType`
  - Markdown files → `MarkdownRenderer`
  - JSON files → typed viewers (ADRViewer, PlanViewer, etc.)
  - Added try/catch for error handling

### 5. Page Update (`WorkflowManagerPage.tsx`)
- Updated state to include `fileFormat`
- Passes `fileFormat` prop to `ArtifactReader`

## Verification

```bash
# Backend tests pass
pytest tests/gateway/test_devtools_workflow.py -v
# Result: 11 passed

# File format detection works
python -c "from gateway.services.workflow_service import scan_artifacts; ..."
# Result: EXECUTION_L2: markdown (.plans\.templates\EXECUTION_L2.md)
```

## Files Modified

1. `shared/contracts/devtools/workflow.py` - Added FileFormat enum
2. `gateway/services/workflow_service.py` - Scan both formats, add file_format
3. `gateway/services/devtools_service.py` - Include file_format in response
4. `apps/homepage/frontend/src/components/workflow/types.ts` - Added FileFormat
5. `apps/homepage/frontend/src/components/workflow/index.ts` - Export FileFormat
6. `apps/homepage/frontend/src/components/workflow/ArtifactReader.tsx` - Route by format
7. `apps/homepage/frontend/src/pages/WorkflowManagerPage.tsx` - Pass fileFormat

## Status

✅ **COMPLETE** - Fix implemented and verified
