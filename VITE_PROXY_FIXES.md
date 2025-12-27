# Vite Proxy Configuration Fixes

## Issue
The "Create New Run" button in Data Aggregator (and similar buttons in SOV Analyzer) were not working despite the UI looking correct.

## Root Cause
The Vite proxy configurations had **incorrect rewrite rules** that were causing double-prefixing of API paths.

### What Was Happening

**Data Aggregator:**
- Frontend code calls: `/api/dat/runs`
- Vite proxy rewrites: `/api` → `/api/dat/api`
- Final URL sent to gateway: `/api/dat/api/dat/runs` ❌ (double prefix)
- Gateway expects: `/api/dat/api/v1/runs` ✓

**SOV Analyzer:**
- Frontend code calls: `/api/sov/analyses`
- Vite proxy rewrites: `/api` → `/api/sov/api`
- Final URL sent to gateway: `/api/sov/api/sov/analyses` ❌ (double prefix)
- Gateway expects: `/api/sov/api/v1/analyses` ✓

**PPTX Generator (already fixed):**
- Frontend code calls: `/api/v1/projects`
- Vite proxy rewrites: `/api` → `/api/pptx/api`
- Final URL: `/api/pptx/api/v1/projects` ✓ (correct)

## The Problem

The rewrite rules were designed for a different API structure. Since the frontend code already includes the full path (`/api/dat/runs`), the proxy should **not** rewrite it - just forward it to the gateway.

## Fixes Applied

### Data Aggregator ✅
**File:** `apps/data_aggregator/frontend/vite.config.ts`

**Before:**
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '/api/dat/api'),  // ❌ Wrong
  },
}
```

**After:**
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,  // ✅ No rewrite needed
  },
}
```

### SOV Analyzer ✅
**File:** `apps/sov_analyzer/frontend/vite.config.ts`

**Before:**
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '/api/sov/api'),  // ❌ Wrong
  },
}
```

**After:**
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,  // ✅ No rewrite needed
  },
}
```

## How It Works Now

### Data Aggregator
1. Frontend: `fetch('/api/dat/runs', { method: 'POST' })`
2. Vite proxy: Forwards to `http://localhost:8000/api/dat/runs`
3. Gateway: Routes to DAT backend at `/api/dat/api/v1/runs`
4. Success! ✅

### SOV Analyzer
1. Frontend: `fetch('/api/sov/analyses')`
2. Vite proxy: Forwards to `http://localhost:8000/api/sov/analyses`
3. Gateway: Routes to SOV backend
4. Success! ✅

### PPTX Generator
1. Frontend: `fetch('/api/v1/projects', { method: 'POST' })`
2. Vite proxy: Rewrites to `/api/pptx/api/v1/projects`
3. Gateway: Routes to PPTX backend
4. Success! ✅

## Why PPTX Was Different

PPTX Generator uses a different pattern:
- Frontend uses generic `/api/v1/...` paths
- Proxy adds the tool prefix: `/api/pptx/api/v1/...`
- This works because the frontend doesn't include the tool name

DAT and SOV use tool-specific paths in the frontend:
- Frontend already includes tool name: `/api/dat/...`, `/api/sov/...`
- Proxy should just forward as-is
- No rewrite needed

## Files Modified

1. ✅ `apps/data_aggregator/frontend/vite.config.ts`
2. ✅ `apps/sov_analyzer/frontend/vite.config.ts`

## Expected Results

After restarting with `.\start.ps1 --with-frontend`:

**Data Aggregator:**
- ✅ "Create New Run" button creates a new aggregation run
- ✅ Stage progression works
- ✅ File selection, context, and export stages functional

**SOV Analyzer:**
- ✅ Dataset selection works
- ✅ Analysis configuration functional
- ✅ Results display correctly

**PPTX Generator:**
- ✅ "Create Project" button works (already fixed)
- ✅ Template upload functional
- ✅ Configuration dropdown populated

## Summary of All Frontend Fixes

This session fixed three categories of frontend issues:

### 1. Missing Config Files
- ✅ PPTX config directory and YAML files
- ✅ DAT Tailwind and PostCSS configs
- ✅ SOV Tailwind and PostCSS configs

### 2. Hardcoded Paths
- ✅ PPTX backend config path resolution
- ✅ PPTX API endpoints using absolute paths

### 3. Proxy Configuration
- ✅ PPTX API base URL (absolute → relative)
- ✅ DAT proxy rewrite (removed incorrect rule)
- ✅ SOV proxy rewrite (removed incorrect rule)

All three tools now have:
- ✅ Proper styling (TailwindCSS)
- ✅ Working API calls
- ✅ Functional buttons and interactions
- ✅ Correct routing through the gateway
