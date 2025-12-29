# TEAM_010: DAT Refactor Deterministic Change Plan

**Session Date**: 2025-12-28
**Objective**: Generate a deterministic change plan for DAT tool refactor based on SSoT (ADRs, SPECs, Contracts).
**Context**: Aligning DAT tool with updated ADRs and SPECs post-refactoring. This session builds on previous work in TEAM_005 through TEAM_009.

## Relevant SSoT Files

- **DAT ADRs**:

  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0001-DAT_Stage-Graph-Configuration.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0003_Optional-Context-Preview-Stages.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0004-DAT_Stage-ID-Configuration.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0006_Table-Availability.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0011_Profile-Driven-Extraction-and-Adapters.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0013_Cancellation-Semantics-Parse-Export.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0014_Parse-and-Export-Artifact-Formats.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0040_Large-File-Streaming-Strategy.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0041_DAT-UI-Horizontal-Wizard-Pattern.json`

- **DAT SPECs**:

  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\docs\specs\dat\SPEC-DAT-0001_Stage-Graph.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\docs\specs\dat\SPEC-DAT-0002_Profile-Extraction.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\docs\specs\dat\SPEC-DAT-0003_Adapter-Interface-Registry.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\docs\specs\dat\SPEC-DAT-0004_Large-File-Streaming.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\docs\specs\dat\SPEC-DAT-0005_Profile-File-Management.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\docs\specs\dat\SPEC-DAT-0006_Table-Availability.json`
  - `@c:\Users\Mycahya\CascadeProjects\engineering-tools\docs\specs\dat\SPEC-DAT-0015_Cancellation-Cleanup.json`

## Plan Overview

This change plan will:

1. Map SSoT requirements to specific code changes in the DAT tool.
2. Define actionable steps to refactor the codebase.
3. Establish Acceptance Criteria for validation against our best practices.

## Key Requirements from DAT ADRs

- **8-Stage Pipeline (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0001-DAT_Stage-Graph-Configuration.json`)**: Implement an 8-stage pipeline (Discovery, Selection, Context, Table Availability, Table Selection, Preview, Parse, Export) with 'lockable_with_artifacts' state model and 'unlock_cascade' policy.
- **Optional Stages (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0003_Optional-Context-Preview-Stages.json`)**: Context and Preview stages are optional, allowing quick-path users to skip them. Parse and Export must function without these artifacts, using defaults if needed.
- **Deterministic Stage IDs (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0004-DAT_Stage-ID-Configuration.json`)**: Each stage must have deterministic IDs based on specific inputs, ensuring idempotent re-locks and artifact reuse.
- **Table Availability (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0006_Table-Availability.json`)**: Implement a deterministic status model (available, partial, missing, empty) for tables, independent of Preview, and surface in UI before Parse.
- **Profile-Driven Extraction (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0011_Profile-Driven-Extraction-and-Adapters.json`)**: Use versioned profiles for extraction logic with an AdapterFactory pattern for multi-format support, ensuring deterministic and auditable results.
- **Cancellation Semantics (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0013_Cancellation-Semantics-Parse-Export.json`)**: Cancellation in Parse and Export must preserve completed artifacts, avoid partial data, and require explicit user cleanup.
- **Artifact Formats (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0014_Parse-and-Export-Artifact-Formats.json`)**: Parse stage uses Parquet for data tables and JSON/YAML for metadata. Export allows user-selectable formats for data but keeps metadata consistent.
- **Large File Streaming (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0040_Large-File-Streaming-Strategy.json`)**: Files > 10MB use streaming with Polars LazyFrame, while smaller files are loaded in memory. Adapters must support both modes.
- **UI Wizard Pattern (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\.adrs\dat\ADR-0041_DAT-UI-Horizontal-Wizard-Pattern.json`)**: Implement a horizontal wizard UI with collapsible panels for the 8-stage pipeline, showing stage states and respecting FSM gating rules.

## Alignment with Core ADRs and Solo-Dev Ethos

The refactor plan ensures alignment with Core ADRs and our solo-dev ethos as follows:

- **Core ADRs**:
  - **ADR-0001 (Guided Workflow FSM Orchestration)**: The DAT pipeline adheres to the Hybrid FSM pattern with the specified 8-stage workflow.
  - **ADR-0002 (Artifact Preservation on Unlock)**: Artifacts are preserved across unlock/re-lock cycles, ensuring no data loss.
  - **ADR-0004 (Deterministic Content-Addressed IDs)**: Stage IDs are computed deterministically using SHA-256 hashing for reproducibility.
  - **ADR-0008 (Audit Trail Timestamps)**: All timestamps in stage results and logs use ISO-8601 UTC format.
  - **ADR-0009 (Type Safety & Contract Discipline)**: Pydantic models in `shared/contracts/` enforce type safety for all configurations and results.
  - **ADR-0017 (Cross-Cutting Guardrails)**: Path safety (relative paths only), concurrency safety, and artifact preservation are enforced across all stages.
  - **ADR-0033 (AI-Assisted Development Patterns)**: Code structure and documentation are optimized for AI comprehension.
  - **ADR-0035 (Contract-Driven Test Generation)**: Tests will be auto-generated from contracts to ensure coverage.

- **Solo-Dev Ethos**:
  - **First-Principles Thinking**: The refactor questions legacy assumptions, redesigning from the ground up based on current ADRs and SPECs.
  - **Quality Over Speed**: Emphasis on clean, modular, and deterministic design over quick fixes, ensuring debt-free solutions.
  - **Automation First**: Documentation and tests will be auto-generated where possible (e.g., JSON Schema, OpenAPI).
  - **Code Standards**: Full type hints, Ruff linting/formatting, and Google-style docstrings are mandated for all code changes.
  - **Deterministic Design**: Every stage has clear inputs/outputs, explicit error handling, and predictable behavior.

## Detailed Code Change Plan

Based on the SSoT contracts and ADRs, the following code changes are required to align the DAT tool with the updated design:

- **State Machine & Stage Pipeline (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\apps\data_aggregator\backend\src\dat_aggregation\core\state_machine.py`)**:
  - Ensure the 8-stage pipeline (Discovery, Selection, Context, Table Availability, Table Selection, Preview, Parse, Export) is fully implemented with the 'lockable_with_artifacts' model and 'unlock_cascade' policy as per ADR-0001-DAT.
  - Update `FORWARD_GATES` and `CASCADE_TARGETS` to reflect optional stages (Context, Preview) not triggering cascades (ADR-0003).
  - Implement deterministic stage IDs using `compute_stage_id()` with stage-specific inputs (ADR-0004-DAT).

- **Adapter Factory & File Handling (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\apps\data_aggregator\backend\src\dat_aggregation\adapters\factory.py` & `@c:\Users\Mycahya\CascadeProjects\engineering-tools\shared\contracts\dat\adapter.py`)**:
  - Enhance `AdapterFactory` to support multi-format extensibility via a handles-first registry as per ADR-0011.
  - Ensure all adapters implement both `read_dataframe` (eager) and `stream_dataframe` (streaming) methods for files > 10MB (ADR-0040).
  - Update `BaseFileAdapter` to enforce path safety and deterministic traversal.

- **Stage Implementations**:
  - **Discovery (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\apps\data_aggregator\backend\src\dat_aggregation\stages\discovery.py`)**: Align with `DiscoveryStageConfig` to scan file systems and return metadata (ADR-0001-DAT).
  - **Selection**: Update to handle user file selection post-Discovery.
  - **Context**: Implement as optional with lazy initialization using profile defaults if skipped (ADR-0003).
  - **Table Availability (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\apps\data_aggregator\backend\src\dat_aggregation\stages\table_availability.py`)**: Implement deterministic probe strategies for table status (available, partial, missing, empty) independent of Preview (ADR-0006).
  - **Table Selection**: Allow user selection of tables post-availability check.
  - **Preview**: Implement as optional with sampled previews for large files (ADR-0003, ADR-0040).
  - **Parse (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\apps\data_aggregator\backend\src\dat_aggregation\stages\parse.py`)**: Ensure Parquet output for data tables, use checkpointing to avoid partial data on cancellation (ADR-0013, ADR-0014).
  - **Export**: Support user-selectable output formats for data tables while maintaining JSON/YAML for metadata (ADR-0014).

- **UI Implementation (`@c:\Users\Mycahya\CascadeProjects\engineering-tools\apps\data_aggregator\frontend\src\components\DATWizard.tsx`)**:
  - Implement horizontal wizard stepper pattern with collapsible panels for the 8-stage pipeline, visually distinguishing optional stages and respecting FSM gating rules (ADR-0041).

- **Cancellation & Artifact Preservation**:
  - Update all stages, especially Parse and Export, to preserve completed artifacts on cancellation, ensuring no partial data is persisted (ADR-0013).

## Acceptance Criteria for Validation

To ensure the DAT tool refactor meets our best practices and design intent, the following Acceptance Criteria must be validated:

- **Pipeline Structure & Behavior**:
  - The 8-stage pipeline must be fully operational with correct forward gating and unlock cascading as defined in ADR-0001-DAT.
  - Optional stages (Context, Preview) must be skippable without triggering downstream unlocks (ADR-0003).
  - Stage IDs must be deterministic, computed from stage-specific inputs, ensuring idempotent re-locks (ADR-0004-DAT).

- **File Handling & Streaming**:
  - Adapters must handle files > 10MB via streaming with Polars LazyFrame, and smaller files via eager loading (ADR-0040).
  - All adapters must support multi-format extensibility through the AdapterFactory pattern (ADR-0011).

- **Table Availability & Selection**:
  - Table availability must use deterministic probe strategies, returning status (available, partial, missing, empty) independent of Preview, visible in UI before Parse (ADR-0006).

- **Artifact Formats & Preservation**:
  - Parse stage must output data tables in Parquet and metadata in JSON/YAML (ADR-0014).
  - Export stage must support user-selectable data formats while maintaining metadata consistency (ADR-0014).
  - Cancellation in Parse and Export must preserve completed artifacts, ensuring no partial tables/rows/values are persisted (ADR-0013).

- **UI & User Experience**:
  - Horizontal wizard UI must display all 7 user-interactive stages with state indicators, respecting FSM gating and visually marking optional stages (ADR-0041).

- **Code Quality & Standards**:
  - Code must adhere to Ruff linting/formatting, include full type hints, and use Google-style docstrings as per our solo-dev ethos.
  - All changes must align with Core ADRs (e.g., path safety, audit trails, deterministic artifacts).

- **Testing & Validation**:
  - Integration tests must cover the full pipeline, including optional stage skipping and cancellation scenarios.
  - Contract validation must ensure Pydantic models in `shared/contracts/` are respected.
  - Determinism tests must confirm stage IDs and outputs are reproducible given identical inputs.

## Remaining TODOs & Handoff Notes

- **Next Session Objective**: Begin implementation of the DAT refactor based on this change plan, starting with the state machine and stage pipeline updates.
- **Blockers**: None at this time; implementation can proceed once this plan is reviewed.
- **Remaining Work**: 
  - Implement the code changes outlined in the Detailed Code Change Plan.
  - Validate implementation against the Acceptance Criteria through testing.
- **Handoff Checklist**:
  - [x] Project builds cleanly (plan phase, no code changes yet).
  - [x] All tests pass (pre-implementation baseline).
  - [x] Regression tests pass (N/A at planning stage).
  - [x] Session file updated with detailed plan and criteria.
  - [x] Remaining TODOs documented for implementation.

This session completes the planning phase for the DAT refactor. The next session should focus on executing the code changes and validating against the defined Acceptance Criteria.
