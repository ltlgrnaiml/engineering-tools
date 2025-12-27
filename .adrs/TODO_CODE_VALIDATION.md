# TODO: Code Validation Against ADRs

> **Status**: PENDING
> **Priority**: High
> **Created**: 2025-12-27

## Objective

Validate that all current code in the Engineering Tools platform aligns with the newly minted, cohesive set of ADRs. This is a one-time audit to establish baseline compliance.

## Validation Checklist

### Core Pattern Compliance

- [ ] **ADR-0001 (FSM Orchestration)**: All guided workflows use the Hybrid FSM pattern
  - [ ] DAT: 8-stage pipeline with lockable artifacts
  - [ ] PPTX: Guided workflow stages
  - [ ] SOV: Analysis pipeline stages
  - [ ] DevTools: Page navigation states

- [ ] **ADR-0002 (Artifact Preservation)**: No code deletes user artifacts on unlock
  - [ ] Check all unlock/reset handlers
  - [ ] Verify cancel operations preserve partial outputs

- [ ] **ADR-0004 (Deterministic IDs)**: All artifact IDs use SHA-256 content-addressing
  - [ ] Verify `shared/workflows/id_generator.py` exists and is used
  - [ ] Check DAT stage IDs follow ADR-0004-DAT inputs
  - [ ] Ensure seed=42 is used consistently

- [ ] **ADR-0008 (Audit Timestamps)**: All artifacts include ISO-8601 UTC timestamps
  - [ ] Check manifest.json, prep_report.json, etc.
  - [ ] Verify no microseconds in timestamps
  - [ ] Confirm all lifecycle events are logged

- [ ] **ADR-0009 (Type Safety)**: All contracts in `shared/contracts/` as Pydantic
  - [ ] Verify 100% type hint coverage (mypy strict)
  - [ ] Check no hand-written JSON schemas
  - [ ] Confirm Specs/Guides don't duplicate contract definitions

### API & Contract Compliance

- [ ] **ADR-0005 (Swagger/OpenAPI)**: All endpoints have OpenAPI specs
  - [ ] FastAPI routes generate OpenAPI automatically
  - [ ] Swagger UI available for all environments
  - [ ] CI validates contract drift

- [ ] **ADR-0016 (Semver Versioning)**: Contract versions follow hybrid semver
  - [ ] Pre-1.0 contracts use 0.x.y
  - [ ] Breaking changes documented with ADR linkage

### Cross-Cutting Guardrails (ADR-0017)

- [ ] **Path Safety**: No absolute paths in API responses
  - [ ] Check `shared/path_safety.py` usage
  - [ ] Run `tools/check_path_safety.py`

- [ ] **Concurrency**: No raw multiprocessing/threading
  - [ ] Verify spawn-safe API usage
  - [ ] Run `tools/check_no_raw_multiprocessing.py`

- [ ] **Message Catalogs**: All user messages from catalog
  - [ ] Check `shared/contracts/messages_*.json` usage
  - [ ] Run `tools/validate_message_catalogs.py`

- [ ] **Tier Boundaries**: ADRs/Specs/Guides have correct content
  - [ ] No code snippets in ADRs
  - [ ] No ADR justifications in Specs
  - [ ] Run `tools/validate_tier_boundaries.py`

### Tool-Specific Compliance

#### DAT
- [ ] ADR-0001-DAT: 8-stage pipeline implemented
- [ ] ADR-0003: Context/Preview stages are optional
- [ ] ADR-0004-DAT: Stage IDs use correct inputs
- [ ] ADR-0006: Table availability detection works
- [ ] ADR-0011: Profile-driven extraction with adapter registry
- [ ] ADR-0013: Cancel preserves partial artifacts
- [ ] ADR-0014: Parquet for data, JSON/YAML for metadata

#### PPTX
- [ ] ADR-0018: Template processing model implemented
- [ ] ADR-0019: Guided workflow follows FSM pattern
- [ ] ADR-0020: Domain configuration schema exists
- [ ] ADR-0021: Renderer architecture follows contracts

#### SOV
- [ ] ADR-0022: ANOVA pipeline with Polars
- [ ] ADR-0023: DataSet integration with lineage
- [ ] ADR-0024: Visualization contracts in Pydantic

## Remediation Process

1. For each non-compliant item:
   - Create a GitHub issue with ADR reference
   - Tag with `adr-compliance` label
   - Assign priority based on impact

2. For patterns not yet implemented:
   - Create implementation plan
   - Update relevant Specs (Tier 2)
   - Add to sprint backlog

## Completion Criteria

- [ ] All checklist items verified
- [ ] No open `adr-compliance` issues (or all tracked)
- [ ] CI pipeline enforces critical guardrails
- [ ] Team trained on ADR compliance workflow

---
*Created: 2025-12-27*
*Assignee: TBD*
*Target Completion: TBD*
