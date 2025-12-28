# TEAM_003: Unified Observability (Backend + Frontend)

**Date**: 2025-12-28
**Task**: Extend ADR-0036 to include frontend debugging patterns for unified observability

## Summary

Extended ADR-0036 (Observability & Debugging First) to cover both backend and frontend debugging patterns as a unified observability story. This maintains orthogonality - one ADR for all observability concerns.

## Changes Made

### ADR Updates
- **ADR-0036**: Extended title to "(Backend + Frontend)", added frontend_debugging section with:
  - DebugContext architecture
  - DebugPanel component specifications
  - useDebugFetch hook patterns
  - Frontend log format schemas
  - Export format for debug sessions
  - Frontend-specific guardrails

### SPEC Updates
- **SPEC-0040**: Extended with frontend debugging specification:
  - Component architecture (DebugContext, DebugPanel, useDebugFetch)
  - Integration patterns for React apps
  - Log schemas for frontend events
  - Requirements REQ-OBS-006 through REQ-OBS-010

### New Contracts Created
- **shared/contracts/core/frontend_logging.py**:
  - `FrontendLogLevel` - enum for log levels
  - `FrontendLogCategory` - enum for log categories
  - `FrontendLogEntry` - structured log entry
  - `FrontendAPICall` - API call logging
  - `FrontendStateTransition` - state transition logging
  - `FrontendDebugExport` - export format
  - `DebugPanelConfig` - panel configuration

### Index Updates
- **ADR_INDEX.md**: Updated ADR-0036 title and description
- **SPEC_INDEX.md**: Updated SPEC-0040 and added contracts to Tier-0 status

### Schema Generation
- Updated `tools/gen_json_schema.py` to include `frontend_logging` module
- Generated 5 new JSON schemas for frontend logging contracts

### Code Updates
- Updated `shared/contracts/core/__init__.py` to export new logging contracts
- Added debugging logs to DAT tool's DebugPanel.tsx and DebugContext.tsx
- Updated `useRun.ts` to use `useDebugFetch` for API call logging

## Files Modified

1. `.adrs/core/ADR-0036_Observability-and-Debugging-First.json`
2. `docs/specs/core/SPEC-0040_Observability-and-Tracing.json`
3. `shared/contracts/core/frontend_logging.py` (NEW)
4. `shared/contracts/core/__init__.py`
5. `.adrs/ADR_INDEX.md`
6. `docs/specs/SPEC_INDEX.md`
7. `tools/gen_json_schema.py`
8. `apps/data_aggregator/frontend/src/hooks/useRun.ts`
9. `apps/data_aggregator/frontend/src/components/debug/DebugPanel.tsx`
10. `apps/data_aggregator/frontend/src/components/debug/DebugContext.tsx`

## Rationale

Per Solo-Dev Ethos and orthogonality principles:
- ADR-0036 already covered "every operation must be traceable"
- Frontend debug panels are another surface for the same observability data
- Unified approach maintains single source of truth for debugging patterns
- Avoids creating separate ADR for frontend debugging (would violate orthogonality)

## Handoff Checklist

- [x] ADR-0036 extended with frontend debugging
- [x] SPEC-0040 extended with frontend specifications
- [x] Frontend logging contracts created
- [x] __init__.py updated with exports
- [x] ADR_INDEX.md updated
- [x] SPEC_INDEX.md updated
- [x] JSON schemas generated (218 total, 5 new)
- [x] DAT tool useRun.ts updated to use debugFetch

## Remaining TODOs

1. PPTX Generator and SOV Analyzer need DebugPanel integration (same pattern as DAT)
2. Shared debug components could be extracted to `shared/frontend/src/debug/`
3. DevTools trace viewer (backend) not yet connected to frontend debug logs
4. Remove temporary console.log debugging statements from DebugPanel.tsx and DebugContext.tsx

---
*Team completed: 2025-12-28*
