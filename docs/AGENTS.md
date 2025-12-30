# Documentation Directory - AI Coding Guide

> **Scope**: Documentation authoring and maintenance.

---

## Documentation Hierarchy (ADR-0015)

```text
Tier 0: shared/contracts/     → Pydantic models (SSOT)
Tier 1: .adrs/                → ADRs explain WHY
Tier 2: docs/specs/           → SPECs define WHAT  ← THIS DIRECTORY
Tier 3: docs/guides/          → Guides show HOW    ← THIS DIRECTORY
```

**Golden Rule**: Never duplicate content across tiers. Reference, don't copy.

---

## Directory Structure

```text
docs/
├── index.md              # MkDocs entry point
├── specs/                # Technical specifications (Tier 2)
│   ├── INDEX.md          # SPEC master list
│   ├── core/             # Platform-wide SPECs
│   ├── dat/              # DAT SPECs
│   ├── pptx/             # PPTX SPECs
│   └── sov/              # SOV SPECs
├── guides/               # How-to guides (Tier 3)
│   ├── development/      # Developer guides
│   └── deployment/       # Deployment guides
├── platform/             # Cross-tool documentation
│   ├── ARCHITECTURE.md
│   ├── DATASETS.md
│   └── PIPELINES.md
└── _archive/             # Archived/deprecated docs
```

---

## SPEC Authoring Rules

SPECs define **WHAT** is being built (implementation details).

1. **Link to ADR** - Every SPEC must reference its parent ADR
2. **Link to Contracts** - Reference Tier-0 contracts, don't duplicate
3. **Include API definitions** - Endpoints, request/response schemas
4. **Include state machines** - FSM diagrams if applicable

### SPEC Naming

Format: `SPEC-{domain}-{NNNN}_{Title}.md`

Examples:
- `SPEC-0001_Stage-Orchestration-FSM.md`
- `SPEC-DAT-0011_Profile-YAML-Schema.md`

---

## Guide Authoring Rules

Guides show **HOW** to do things (step-by-step instructions).

1. **Task-focused** - Each guide solves one problem
2. **Concrete examples** - Include code and commands
3. **Testable steps** - User can verify each step worked
4. **Link to SPECs** - Reference specifications for details

---

## MkDocs Configuration

Docs are built with MkDocs:

```bash
# Preview docs locally
mkdocs serve

# Build static site
mkdocs build
```

---

## Auto-Generated Documentation (ADR-0034)

Some documentation is generated from code:

| Doc Type | Source | Generator |
|----------|--------|-----------|
| API Reference | FastAPI routes | OpenAPI / Swagger |
| Contract Reference | Pydantic models | mkdocstrings |
| JSON Schemas | Pydantic models | `tools/gen_json_schema.py` |
| Changelog | Git commits | git-cliff |

**Rule**: Don't manually edit auto-generated docs. Fix the source.

---

## What NOT to Put in Docs

| Content | Correct Location |
|---------|------------------|
| Pydantic model definitions | `shared/contracts/` |
| Decision rationale | `.adrs/` |
| Code comments | In the code itself |
| Test documentation | Test file docstrings |
