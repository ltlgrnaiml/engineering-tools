# Shared Module - AI Coding Guide

> **Scope**: This AGENTS.md applies when working with files in `shared/` and subdirectories.

---

## This Directory is Tier-0 (SSOT)

Everything in `shared/contracts/` is the **single source of truth** for data structures.

**Golden Rule**: If a Pydantic model needs to be shared across tools, it belongs here.

---

## Contract Rules

| Rule | Description |
|------|-------------|
| **No duplication** | NEVER create Pydantic models outside this directory for shared data |
| **Version required** | ALL contracts MUST have `__version__` attribute (YYYY.MM.PATCH) |
| **Exports required** | Add new contracts to `__init__.py` for public API |
| **Breaking changes** | Require version bump per ADR-0016 |

---

## Directory Organization

```
shared/
├── contracts/           # Pydantic models (Tier-0 SSOT)
│   ├── core/            # Platform-wide: DataSet, Pipeline, Audit, etc.
│   ├── dat/             # Data Aggregator contracts
│   ├── pptx/            # PowerPoint Generator contracts
│   ├── sov/             # SOV Analyzer contracts
│   ├── messages/        # User-facing message catalogs
│   └── devtools/        # DevTools contracts
├── middleware/          # Shared FastAPI middleware
├── rendering/           # Unified rendering engine (ADR-0028)
├── storage/             # Artifact storage utilities
└── utils/               # Shared utilities (stage_id, path_safety, etc.)
```

---

## When Adding/Modifying Contracts

1. **Check if contract already exists** - search `shared/contracts/`
2. **Add/modify in appropriate subdirectory** - core/ for platform-wide, tool-specific otherwise
3. **Add `__version__`** - format: `__version__ = "2025.01.001"`
4. **Update `__init__.py` exports** - for public API exposure
5. **Run schema generation** - `python tools/gen_json_schema.py`

---

## Contract Template

```python
"""Module docstring describing the contract domain.

This module contains contracts for [domain description].
"""

from pydantic import BaseModel, Field

__version__ = "2025.01.001"


class MyContract(BaseModel):
    """Brief description of what this contract represents.

    Attributes:
        field_name: Description of the field.
    """

    field_name: str = Field(..., description="Field description")
```

---

## Utilities in shared/utils/

| Utility | Purpose | ADR |
|---------|---------|-----|
| `stage_id.py` | Deterministic SHA-256 stage IDs | ADR-0004 |
| `path_safety.py` | Relative path validation | ADR-0017 |
| `concurrency.py` | Spawn-safe parallel execution | ADR-0012 |

---

## What Does NOT Belong Here

- Tool-specific business logic → `apps/{tool}/`
- Tool-specific API routes → `apps/{tool}/backend/api/`
- Frontend code → `apps/{tool}/frontend/`
- Configuration files → tool directories or root
