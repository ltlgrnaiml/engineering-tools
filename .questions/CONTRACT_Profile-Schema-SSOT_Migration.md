# QUESTION: Tier-0 Contract SSOT for Profile Schema (DAT)

## Context

We are validating the work from:

- `.questions/DESIGN_Profile-Driven-ETL-Architecture.md`
- `.questions/IMPL_Profile-Executor-Implementation-Plan.md`

And the downstream docs:

- `.adrs/dat/ADR-0011_Profile-Driven-Extraction-and-Adapters.json`
- `docs/specs/dat/SPEC-DAT-0011_Profile-Schema.json`
- `docs/specs/dat/SPEC-DAT-0012_Extraction-Strategies.json`
- `docs/specs/dat/SPEC-DAT-0002_Profile-Extraction.json`

All three specs + ADR-0011 reference Tier-0 contracts that should live in `shared/contracts/dat/profile.py`:

- `DATProfile`
- `TableConfig`
- `SelectConfig`
- `LevelConfig`
- `ContextDefaults`
- `OutputConfig`

## Observed State (Repo)

- `shared/contracts/dat/profile.py` currently defines an older contract model: `ExtractionProfile` (file_patterns/column_mappings/aggregation_levels)
- The “new” profile schema *does* exist, but as **app-layer dataclasses** in:
  - `apps/data_aggregator/backend/src/dat_aggregation/profiles/profile_loader.py` (`DATProfile`, `TableConfig`, `LevelConfig`, etc.)
  - Strategy `SelectConfig` also exists as an app-layer dataclass in `apps/.../profiles/strategies/base.py`

This violates the stated rule that **Contracts are Tier-0 SSOT**.

## Decision Needed

**Should we perform a breaking migration of Tier‑0 contracts so that the new Profile YAML schema is represented in `shared/contracts/dat/profile.py` (Pydantic), and then update all call sites to use that?**

### Option A (Recommended, per Contracts-as-SSOT)

- Replace (or deprecate-remove) `ExtractionProfile` in `shared/contracts/dat/profile.py`
- Add Pydantic contracts implementing the new schema:
  - `DATProfile`, `LevelConfig`, `TableConfig`, `SelectConfig`, `RepeatOverConfig`, `ContextDefaults`, `ContextConfig`, `OutputConfig`, etc.
- Update code to import these contracts from `shared.contracts.dat.profile` (no app-local dataclasses)
- Update specs to reference only Tier-0 contracts (and remove any “tier_0_contracts” pointing into `apps/...`)

### Option B (Not recommended)

- Keep Tier-0 as `ExtractionProfile`
- Treat the new profile schema as an app-layer “implementation detail”
- Update ADR/specs to stop claiming those types are Tier‑0 contracts

## My Recommendation

Option A.

It aligns with:

- Your explicit instruction: “Contracts are Tier‑0 SSOT”
- ADR-0009 contract discipline
- The stated bottom-up validation approach

## Questions

1. Do you approve Option A (breaking migration) as the authoritative fix?
2. If yes: should `ExtractionProfile` be deleted immediately (greenfield rule), or do you want to keep it only if it still powers profile CRUD elsewhere?
3. Should the profile YAML schema be validated by constructing Pydantic models directly (preferred), instead of maintaining a parallel dataclass parser?
