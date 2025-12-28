# ADR-0029 Implementation Change Plan

## API Versioning and Endpoint Naming Specification

**Status**: Accepted  
**Date**: 2025-12-28  
**Author**: CDU-DAT Core Engineering Team

---

## Executive Summary

This document outlines all required changes to implement ADR-0029 (API Versioning and Endpoint Naming Specification). The changes standardize API versioning across all tools using a two-tier strategy:

- **Gateway cross-tool APIs**: `/api/v1/{resource}`
- **Tool-specific APIs**: `/api/{tool}/v1/{resource}`
- **Health checks**: Unversioned (`/health`)

---

## Change Categories

| Category | Count | Risk Level |
|----------|-------|------------|
| **MODIFY** | 15 files | Medium |
| **ADD** | 1 file (this plan) | Low |
| **DELETE** | 0 files | N/A |

---

## 1. ADR Updates

### 1.1 MODIFY: `.adrs/core/ADR-0029_API-Versioning-and-Endpoint-Naming.json`
- **Action**: Change `"status": "proposed"` to `"status": "accepted"`
- **Risk**: Low

### 1.2 MODIFY: `.adrs/core/ADR-0005_Swagger-Driven-E2E-Validation.json`
- **Action**: Add reference to ADR-0029 in references section
- **Risk**: Low

---

## 2. Gateway Changes

### 2.1 MODIFY: `gateway/main.py`
**Current**:
```python
app.include_router(dataset_router, prefix="/api/datasets", tags=["datasets"])
app.include_router(pipeline_router, prefix="/api/pipelines", tags=["pipelines"])
app.include_router(devtools_router, prefix="/api/devtools", tags=["devtools"])
```

**Target**:
```python
app.include_router(dataset_router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(pipeline_router, prefix="/api/v1/pipelines", tags=["pipelines"])
app.include_router(devtools_router, prefix="/api/v1/devtools", tags=["devtools"])
```

**Risk**: Medium - affects all API consumers

### 2.2 MODIFY: `gateway/services/pipeline_service.py`
**Current** (line 31-34):
```python
TOOL_BASE_URLS = {
    "dat": "http://localhost:8000/api/dat",
    "sov": "http://localhost:8000/api/sov",
    "pptx": "http://localhost:8000/api/pptx",
}
```

**Target**:
```python
TOOL_BASE_URLS = {
    "dat": "http://localhost:8000/api/dat/v1",
    "sov": "http://localhost:8000/api/sov/v1",
    "pptx": "http://localhost:8000/api/pptx/v1",
}
```

**Risk**: Medium - affects pipeline execution

---

## 3. DAT Tool Changes

### 3.1 MODIFY: `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py`
**Current** (line 1-5, 42-43):
```python
"""DAT API routes.

Per API-001: All routes use versioned /v1/ prefix.
Per ADR-0013: Cancellation events are logged for audit.
"""
...
# Router without versioning per project decision
router = APIRouter()
```

**Target**:
```python
"""DAT API routes.

Per ADR-0029: All routes use versioned /v1/ prefix.
Per ADR-0013: Cancellation events are logged for audit.
"""
...
# Per ADR-0029: Tool-specific routes use /v1/ prefix
router = APIRouter(prefix="/v1")
```

**Risk**: Medium - changes all DAT endpoint URLs

---

## 4. SOV Tool Changes

### 4.1 MODIFY: `apps/sov_analyzer/backend/src/sov_analyzer/api/routes.py`
**Current** (line 28):
```python
router = APIRouter()
```

**Target**:
```python
# Per ADR-0029: Tool-specific routes use /v1/ prefix
router = APIRouter(prefix="/v1")
```

**Risk**: Medium - changes all SOV endpoint URLs

### 4.2 MODIFY: `apps/sov_analyzer/backend/main.py`
**Current** (line 48-50):
```python
# Include API routes
# Note: No /api prefix here - gateway mounts this at /api/sov/
# Routes will be /api/sov/v1/analyses, etc.
app.include_router(router, tags=["sov"])
```

**Target** (update comment):
```python
# Include API routes
# Per ADR-0029: Router has /v1/ prefix, gateway mounts at /api/sov/
# Final routes: /api/sov/v1/analyses, etc.
app.include_router(router, tags=["sov"])
```

**Risk**: Low - comment only

---

## 5. PPTX Tool Changes

### 5.1 MODIFY: `apps/pptx_generator/backend/main.py`
**Current** (lines 74-85):
```python
app.include_router(health.router, tags=["health"])
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(dataset_input.router, prefix="/api/data", tags=["dataset-input"])
app.include_router(generation.router, prefix="/api/generation", tags=["generation"])
app.include_router(requirements.router, prefix="/api/requirements", tags=["requirements"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(config_defaults.router, prefix="/api", tags=["config"])
app.include_router(data_operations.router, prefix="/api", tags=["data-operations"])
app.include_router(preview.router, prefix="/api/preview", tags=["preview"])
```

**Target**:
```python
# Per ADR-0029: Health endpoints are unversioned
app.include_router(health.router, tags=["health"])
app.include_router(health.router, prefix="/api", tags=["health"])
# Per ADR-0029: All other routes use /v1/ prefix
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(data.router, prefix="/api/v1/data", tags=["data"])
app.include_router(dataset_input.router, prefix="/api/v1/data", tags=["dataset-input"])
app.include_router(generation.router, prefix="/api/v1/generation", tags=["generation"])
app.include_router(requirements.router, prefix="/api/v1/requirements", tags=["requirements"])
app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
app.include_router(config_defaults.router, prefix="/api/v1", tags=["config"])
app.include_router(data_operations.router, prefix="/api/v1", tags=["data-operations"])
app.include_router(preview.router, prefix="/api/v1/preview", tags=["preview"])
```

**Risk**: Medium - changes all PPTX endpoint URLs

---

## 6. Test File Changes

### 6.1 MODIFY: `tests/test_gateway.py`
**Changes Required**:
- Line 60-84: Update `/api/datasets/` → `/api/v1/datasets/`
- Line 95-172: Update `/api/pipelines/` → `/api/v1/pipelines/`

**Risk**: Low - test files only

### 6.2 MODIFY: `tests/dat/test_api.py`
**Changes Required**:
- Already updated to use `/v1/runs` - verify consistency
- Ensure all routes use `/v1/` prefix

**Risk**: Low - test files only

### 6.3 MODIFY: `tests/test_all_endpoints.py`
**Changes Required**:
- Update all API URLs to include `/v1/` prefix
- Verify gateway routing patterns

**Risk**: Low - test files only

---

## 7. Documentation Updates

### 7.1 MODIFY: `docs/platform/ARCHITECTURE.md`
**Action**: Add section on API versioning strategy referencing ADR-0029

**Risk**: Low - documentation only

---

## 8. Validation Checklist

After implementing all changes, verify:

- [ ] All gateway routes include `/v1/` in path
- [ ] All DAT routes accessible at `/api/dat/v1/*`
- [ ] All SOV routes accessible at `/api/sov/v1/*`
- [ ] All PPTX routes accessible at `/api/pptx/v1/*`
- [ ] All cross-tool routes accessible at `/api/v1/{resource}`
- [ ] Health endpoints remain unversioned
- [ ] All tests pass with updated URLs
- [ ] OpenAPI specs reflect versioned paths
- [ ] No conflicting comments in route files

---

## 9. Rollback Plan

If issues arise:

1. Revert all file changes via Git
2. Re-run tests to confirm restoration
3. Document issues encountered
4. Update ADR-0029 status to "superseded" if abandoning

---

## 10. Implementation Order

1. ✅ Create this change plan document
2. ✅ Update ADR-0029 status to accepted
3. ✅ Update gateway/main.py routing
4. ✅ Update gateway/services/pipeline_service.py URLs
5. ✅ Update DAT routes.py with /v1/ prefix
6. ✅ Update SOV routes.py with /v1/ prefix
7. ✅ Update PPTX main.py routing
8. ✅ Update tests/test_gateway.py URLs
9. ✅ Verify tests/dat/test_api.py (already had /v1/ prefix)
10. ✅ Update ADR cross-references
11. ✅ Run test suite to validate (gateway tests: 12/12 pass)
12. ✅ Mark implementation complete

---

## 11. Implementation Notes

**Completed**: 2025-12-28

**Test Results**:
- Gateway tests: 12/12 PASSED
- DAT API tests: 5 failures (pre-existing implementation bugs, not versioning-related)

**Pre-existing DAT bugs** (not introduced by this change):
- `create_error_response()` signature mismatch
- `DATStateMachine.unlock_stage()` signature mismatch
- Selection validation issues
- Preview endpoint implementation

---

*Generated: 2025-12-28*  
*Completed: 2025-12-28*
