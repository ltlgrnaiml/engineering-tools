# SESSION_020: DAT Contract SSOT + Profile ID Wiring

## Objective

Make `shared/contracts` the single source of truth (SSOT) for the DAT API contracts and ensure `profile_id` is deterministically persisted and propagated through Context -> Parse so profile-driven extraction is the default behavior.

## Pre-flight Checklist (per Solo-Dev Ethos)

- [ ] Read `docs/AI_CODING_GUIDE.md`
- [ ] Review recent `.sessions/` logs
- [ ] Review `.questions/` for open implementation plans
- [ ] Run baseline tests (must pass before modifications)

## Plan

1. **Contracts SSOT**: Introduce `shared/contracts/dat/api.py` as SSOT for DAT FastAPI request/response models; remove duplicate model definitions from `apps/data_aggregator/backend/src/dat_aggregation/api/schemas.py` (convert to re-exports only).
2. **Deterministic profile_id wiring**: Persist `profile_id` into `RunStore` state, update it on Context lock, and pass into Parse config so `execute_parse()` always selects profile-driven extraction when a profile is selected.
3. **Verification**: Re-run tests and fix regressions.

## Progress Log

- Started: 2025-12-29
