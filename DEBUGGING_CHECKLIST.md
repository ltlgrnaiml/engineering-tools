# Endpoint Debugging Checklist

## Test Results Summary (2025-12-27)

**Total Tests:** 16  
**Passed:** 8 ✓  
**Failed:** 8 ✗

---

## Issues Identified

### 1. Gateway Health Endpoint Missing (404)
- **Status:** ❌ FAILED
- **Expected:** `GET /health` → 200
- **Actual:** 404 Not Found
- **Root Cause:** Gateway doesn't have a `/health` endpoint
- **Fix Required:** Add health endpoint to gateway

### 2. Gateway OpenAPI Docs Missing (404)
- **Status:** ❌ FAILED
- **Expected:** `GET /docs` → 200
- **Actual:** 404 Not Found
- **Root Cause:** Gateway docs might not be configured at root level
- **Fix Required:** Verify FastAPI docs configuration

### 3. PPTX Health Endpoint Missing (404)
- **Status:** ❌ FAILED
- **Expected:** `GET /api/pptx/health` → 200
- **Actual:** 404 Not Found
- **Root Cause:** PPTX backend doesn't have `/health` endpoint
- **Fix Required:** Add health endpoint to PPTX backend

### 4. PPTX Create Project Returns 201 Instead of 200
- **Status:** ⚠️ MINOR ISSUE
- **Expected:** `POST /api/pptx/api/v1/projects` → 200
- **Actual:** 201 Created (which is actually correct for REST)
- **Root Cause:** Test expectation is wrong, 201 is proper HTTP status for resource creation
- **Fix Required:** Update test to accept 201

### 5. DAT Create Run Requires Body (422)
- **Status:** ❌ FAILED
- **Expected:** `POST /api/dat/api/v1/runs` → 200
- **Actual:** 422 Unprocessable Entity - "Field required"
- **Root Cause:** API expects a request body but test sends empty POST
- **Fix Required:** Check DAT API spec and send proper request body

### 6. Cross-Tool Dataset Endpoint Missing (404)
- **Status:** ❌ FAILED
- **Expected:** `GET /api/v1/datasets` → 200
- **Actual:** 404 Not Found
- **Root Cause:** Gateway dataset service not mounted at `/api/v1/datasets`
- **Fix Required:** Verify gateway routing for dataset service

### 7. Cross-Tool Pipeline Endpoint Missing (404)
- **Status:** ❌ FAILED
- **Expected:** `GET /api/v1/pipelines` → 200
- **Actual:** 404 Not Found
- **Root Cause:** Gateway pipeline service not mounted at `/api/v1/pipelines`
- **Fix Required:** Verify gateway routing for pipeline service

---

## Working Endpoints ✓

1. ✅ PPTX OpenAPI docs - `GET /api/pptx/docs`
2. ✅ PPTX list projects - `GET /api/pptx/api/v1/projects`
3. ✅ DAT health endpoint - `GET /api/dat/health`
4. ✅ DAT OpenAPI docs - `GET /api/dat/docs`
5. ✅ DAT list runs - `GET /api/dat/api/v1/runs`
6. ✅ SOV health endpoint - `GET /api/sov/health`
7. ✅ SOV OpenAPI docs - `GET /api/sov/docs`
8. ✅ SOV list analyses - `GET /api/sov/api/v1/analyses`

---

## Fix Priority

### High Priority (Blocking Core Functionality)
1. ✅ Add gateway health endpoint
2. ✅ Fix cross-tool dataset endpoint routing
3. ✅ Fix cross-tool pipeline endpoint routing
4. ✅ Add PPTX health endpoint

### Medium Priority (API Consistency)
5. ✅ Fix DAT create run API call
6. ✅ Update test expectations for HTTP status codes

### Low Priority (Documentation)
7. ✅ Verify gateway docs configuration

---

## Fixes Applied

### Fix 1: Gateway Health Endpoint
- **File:** `gateway/main.py`
- **Action:** Add `/health` endpoint
- **Status:** PENDING

### Fix 2: Gateway Cross-Tool Routes
- **File:** `gateway/main.py`
- **Action:** Verify dataset and pipeline service routes
- **Status:** PENDING

### Fix 3: PPTX Health Endpoint
- **File:** `apps/pptx_generator/backend/main.py`
- **Action:** Add `/health` endpoint
- **Status:** PENDING

### Fix 4: DAT Create Run API
- **File:** `test_endpoints_standalone.py`
- **Action:** Send proper request body
- **Status:** PENDING

### Fix 5: Test Status Code Expectations
- **File:** `test_endpoints_standalone.py`
- **Action:** Accept 201 for POST requests
- **Status:** PENDING
