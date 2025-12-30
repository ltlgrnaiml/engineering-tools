# SESSION_001: Profile-Driven ETL Validation (Contracts → ADR → Specs)

**Date**: 2025-12-30

## Scope

Validate the Profile-Driven ETL work bottom-up:

- Tier-0 contracts (`shared/contracts/`)
- ADR layer (`.adrs/`)
- Spec layer (`docs/specs/`)

## Inputs Reviewed

- `.questions/DESIGN_Profile-Driven-ETL-Architecture.md`
- `.questions/IMPL_Profile-Executor-Implementation-Plan.md`
- `.adrs/dat/ADR-0011_Profile-Driven-Extraction-and-Adapters.json`
- `docs/specs/dat/SPEC-DAT-0011_Profile-Schema.json`
- `docs/specs/dat/SPEC-DAT-0012_Extraction-Strategies.json`
- `docs/specs/dat/SPEC-DAT-0002_Profile-Extraction.json`

## Notes

- Existing session logs were found under `docs/_archive/planning/2025-12/sessions/` (e.g., `SESSION_018...SESSION_021`). The repository root `.sessions/` currently contains only `PATCH_PLAN/`. This session number follows the current `.sessions/` directory state.

## Findings (In Progress)

### Tier-0 Contract Alignment

- **Contract drift detected**: `shared/contracts/dat/profile.py` defines `ExtractionProfile` (file_patterns / column_mappings / aggregation_levels), but the new ADR/specs reference `shared.contracts.dat.profile.DATProfile`, `TableConfig`, `SelectConfig`, `LevelConfig`, `ContextDefaults`, `OutputConfig`, etc.

## Next Actions

- Validate whether `DATProfile` (and related classes) exist anywhere in codebase.
- Decide whether to migrate Tier-0 contracts to the new profile schema (breaking change) and update call sites.
- Run baseline tests before making any behavior changes.
