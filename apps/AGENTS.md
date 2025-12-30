# Apps Directory - AI Coding Guide

> **Scope**: This AGENTS.md applies when working with files in `apps/` and subdirectories.
> Each tool has its own AGENTS.md with tool-specific rules.

---

## Application Architecture

Each tool follows a consistent structure:

```
apps/{tool}/
├── AGENTS.md              # Tool-specific AI rules
├── backend/
│   ├── AGENTS.md          # Backend-specific rules
│   ├── api/               # FastAPI routes
│   ├── services/          # Business logic
│   └── src/{tool}/        # Core implementation
└── frontend/
    ├── AGENTS.md          # Frontend-specific rules
    └── src/               # React/TypeScript code
```

---

## Common Patterns (All Tools)

### API Design

- Mount at `/api/{tool}/` via gateway
- Use versioned routes internally: `/v1/{resource}`
- Return Pydantic models (import from `shared.contracts`)
- Use `ErrorResponse` contract for all errors (ADR-0032)

### Error Handling

```python
# Each tool has an errors.py helper
from .errors import create_error_response, handle_validation_error

# Use ErrorResponse contract
from shared.contracts.core.error_response import ErrorResponse
```

### State Management

- FSM-based workflows (ADR-0001)
- Stage states: UNLOCKED → LOCKED → COMPLETED
- Never delete artifacts on unlock (ADR-0002)

---

## Tool Overview

| Tool | Purpose | Key ADRs |
|------|---------|----------|
| **data_aggregator** | Multi-source data extraction | ADR-0012 (Profiles), ADR-0041 (Streaming) |
| **pptx_generator** | Automated PowerPoint reports | ADR-0019-0021 (Templates, Renderers) |
| **sov_analyzer** | Source of Variation analysis | ADR-0023-0024 (ANOVA, Visualization) |

---

## Cross-Tool Integration

Tools communicate via:

1. **DataSet API** - Shared datasets in `workspace/datasets/`
2. **Pipeline API** - Multi-step workflows via gateway
3. **Contracts** - Shared Pydantic models in `shared/contracts/`

See `docs/platform/PIPELINES.md` for pipeline orchestration patterns.
