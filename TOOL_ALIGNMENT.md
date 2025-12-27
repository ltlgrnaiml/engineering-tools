# Tool Alignment Reference

This document tracks the port and API configuration alignment across all tools.

## Frontend Ports

| Tool | Port | Vite Config | Status |
|------|------|-------------|--------|
| Homepage | 3000 | ✅ Exists | Running |
| Data Aggregator | 5173 | ✅ Created | Ready |
| SOV Analyzer | 5174 | ✅ Created | Ready |
| PPTX Generator | 5175 | ✅ Exists | Running |

## API Gateway Routes

All tools route through the gateway at `http://localhost:8000`:

| Tool | Gateway Path | Backend Mount | Status |
|------|--------------|---------------|--------|
| Data Aggregator | `/api/dat/*` | Mounted | ✅ |
| SOV Analyzer | `/api/sov/*` | Mounted | ✅ |
| PPTX Generator | `/api/pptx/*` | Mounted | ✅ |

## Frontend-to-Backend Routing

Each frontend uses Vite proxy to rewrite API calls:

### Data Aggregator Frontend
- **Port:** 5173
- **Proxy Rule:** `/api` → `http://localhost:8000/api/dat/api`
- **Config File:** `apps/data_aggregator/frontend/vite.config.ts`

### SOV Analyzer Frontend
- **Port:** 5174
- **Proxy Rule:** `/api` → `http://localhost:8000/api/sov/api`
- **Config File:** `apps/sov_analyzer/frontend/vite.config.ts`

### PPTX Generator Frontend
- **Port:** 5175
- **Proxy Rule:** `/api` → `http://localhost:8000/api/pptx/api`
- **Config File:** `apps/pptx_generator/frontend/vite.config.ts`

## Homepage Tool Links

All tools are linked from the Homepage via iframe:

| Tool | Route | iframe src | Status |
|------|-------|-----------|--------|
| Data Aggregator | `/tools/dat` | `http://localhost:5173` | ✅ |
| SOV Analyzer | `/tools/sov` | `http://localhost:5174` | ✅ |
| PPTX Generator | `/tools/pptx` | `http://localhost:5175` | ✅ |

## Start Script Alignment

The `start.ps1` script starts all services in the correct order:

1. API Gateway (port 8000)
2. Homepage frontend (port 3000)
3. Data Aggregator frontend (port 5173)
4. PPTX Generator frontend (port 5175)
5. SOV Analyzer frontend (port 5174)

All ports match the vite.config.ts configurations.

## Files Created/Updated

### New Files
- `apps/data_aggregator/frontend/vite.config.ts`
- `apps/data_aggregator/frontend/tsconfig.json`
- `apps/data_aggregator/frontend/tsconfig.node.json`
- `apps/sov_analyzer/frontend/vite.config.ts`
- `apps/sov_analyzer/frontend/tsconfig.json`
- `apps/sov_analyzer/frontend/tsconfig.node.json`

### Updated Files
- `apps/data_aggregator/frontend/package.json` (added @types/node)
- `apps/sov_analyzer/frontend/package.json` (added @types/node)
- `apps/homepage/frontend/src/pages/HomePage.tsx` (added appUrl to tools)

## Verification Checklist

- [x] All frontend ports configured in vite.config.ts
- [x] All frontends have tsconfig.json and tsconfig.node.json
- [x] All frontends have @types/node in devDependencies
- [x] All API proxy rules configured correctly
- [x] All tools linked in Homepage with correct ports
- [x] start.ps1 script ports match vite configs
- [x] Gateway mounts all tool backends
