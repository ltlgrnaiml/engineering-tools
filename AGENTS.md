# Engineering Tools Platform - AI Coding Guide

> **Windsurf Auto-Discovery**: This file applies globally to all files in the repository.
> Tool-specific rules are in subdirectory `AGENTS.md` files.

---

## Solo-Dev Ethos

This platform follows a **first-principles, AI-assisted, greenfield** development philosophy:

| Principle | Rule |
|-----------|------|
| **Quality > Speed** | Take the correct architectural path, never the shortcut |
| **First-Principles** | Question every decision. No legacy assumptions. |
| **Breaking Changes > Shims** | No backward compatibility hacks. Fix the source directly. |
| **No Dead Code** | Remove immediately. Git history exists for reference. |
| **Automation First** | Generate docs, tests, schemas from contracts—don't write manually |

---

## Critical ADRs (Must Know)

| Priority | ADR | Key Rule |
|----------|-----|----------|
| 🔴 | **ADR-0009** | Contracts in `shared/contracts/` are SSOT. Never duplicate. |
| 🔴 | **ADR-0033** | AI-parseable patterns: `{verb}_{noun}()`, Google docstrings |
| 🔴 | **ADR-0004** | Deterministic SHA-256 IDs for reproducibility |
| 🟡 | **ADR-0002** | Never delete artifacts on unlock. Preserve user work. |
| 🟡 | **ADR-0017** | Cross-cutting guardrails (see below) |
| 🟡 | **ADR-0031** | All HTTP errors use `ErrorResponse` contract |

---

## Guardrails Checklist (ADR-0017)

Before any code change, verify:

- [ ] **path-safety**: All public paths are relative (use `assert_relpath_safe()`)
- [ ] **concurrency**: Using spawn-safe API only (no raw `multiprocessing`)
- [ ] **message-catalogs**: User messages from catalog, not hardcoded
- [ ] **cancel-behavior**: Artifacts preserved on cancel; explicit cleanup only
- [ ] **tier-boundaries**: No contract duplication across tiers

---

## Contract Discipline (ADR-0009)

```python
# ✅ CORRECT: Import from shared.contracts
from shared.contracts.core.dataset import DataSetManifest
from shared.contracts.dat.profile import DATProfile

# ❌ WRONG: Define inline Pydantic model
class DataSetManifest(BaseModel):  # NEVER DO THIS
    ...
```

**Rules**:

- ALL shared data structures → `shared/contracts/`
- ALL contracts have `__version__` attribute (YYYY.MM.PATCH per ADR-0016)
- Import, never duplicate

---

## Code Patterns (ADR-0033)

### Naming Conventions

| Element | Pattern | Example |
|---------|---------|---------|
| Files | `{domain}_{action}.py` | `dataset_loader.py`, `profile_executor.py` |
| Functions | `{verb}_{noun}()` | `load_dataset()`, `validate_profile()` |
| Classes | `PascalCase` | `ProfileExecutor`, `AdapterFactory` |

### Required Docstring Format (Google Style)

```python
def compute_stage_id(inputs: dict[str, Any], seed: int = 42) -> str:
    """Compute deterministic stage ID from inputs.

    Args:
        inputs: Dictionary of stage inputs to hash.
        seed: Random seed for determinism. Defaults to 42.

    Returns:
        8-character SHA-256 hash prefix.

    Raises:
        ValueError: If inputs is empty.
    """
    ...
```

### Type Hints

- **Required** on all function signatures
- Use `dict[str, Any]` not `Dict[str, Any]` (Python 3.9+)
- Use `list[str]` not `List[str]`
- Use `X | None` not `Optional[X]`

---

## Common Pitfalls to Avoid

| Pitfall | Correct Approach |
|---------|------------------|
| Using absolute file paths in API responses | Use relative paths; call `assert_relpath_safe()` |
| Deleting artifacts on unlock/cancel | Set `locked: false`; preserve files |
| Using raw `multiprocessing` | Use spawn-safe concurrency API (ADR-0012) |
| Hardcoding user messages | Use message catalog |
| Creating backward compatibility shims | Delete old, fix all call sites directly |

---

## Directory Structure

```
engineering-tools/
├── shared/              # Tier-0: Contracts, utilities (SSOT)
├── gateway/             # API gateway and cross-tool services
├── apps/                # Individual tool applications
│   ├── data_aggregator/ # DAT: Data extraction & aggregation
│   ├── pptx_generator/  # PPTX: PowerPoint report generation
│   └── sov_analyzer/    # SOV: Source of Variation analysis
├── workspace/           # Local artifact storage (gitignored)
├── .adrs/               # Architecture Decision Records (WHY)
├── docs/specs/          # Technical Specifications (WHAT)
└── docs/guides/         # How-to Guides (HOW)
```

---

## 3-Tier Document Model (ADR-0015)

```
Tier 0: shared/contracts/     → Pydantic models (SSOT)
Tier 1: .adrs/                → ADRs explain WHY
Tier 2: docs/specs/           → SPECs define WHAT
Tier 3: docs/guides/          → Guides show HOW
```

**Rule**: Never duplicate content across tiers. Reference, don't copy.

---

## Quick Commands

| Command | Purpose |
|---------|---------|
| `uv sync` | Install all dependencies |
| `ruff check .` | Run linting |
| `ruff format .` | Auto-format code |
| `pytest tests/ -v` | Run all tests |
| `./start.ps1` | Start platform (Windows) |
| `./start.sh` | Start platform (Linux/macOS) |

---

## Session Discipline

Every AI session must:

1. Check `.sessions/` for highest SESSION_XXX number
2. Claim next number and create session file
3. Ensure tests pass before making changes
4. Update session file with progress
5. Document remaining work before ending

---

<!-- WINDSURF_SPECIFIC: AI Development Workflow section -->

## AI Development Workflow (ADR-0041)

### 6-Tier Hierarchy

| Tier | Artifact | Purpose | Directory |
|------|----------|---------|-----------|
| T0 | Discussion | Design conversation capture | `.discussions/` |
| T1 | Decision | Architecture decisions (ADR) | `.adrs/` |
| T2 | Specification | Behavioral requirements (SPEC) | `docs/specs/` |
| T3 | Contract | Data shapes (Pydantic SSOT) | `shared/contracts/` |
| T4 | Plan | Implementation milestones & tasks | `.plans/` |
| T5 | Fragment | Single verifiable work unit | Per-task execution |

### Workflow Entry Points

| Scenario | Start At | Skip |
|----------|----------|------|
| Architectural change | T0 (Discussion) | None |
| New feature | T0 or T2 | Depends on complexity |
| Simple enhancement | T2 (SPEC) | T0, T1 |
| New data structure | T3 (Contract) | T0-T2 |
| Bug fix / Refactor | T4 (Plan) | T0-T3 |

### Fragment-Based Execution (CRITICAL)

Per SESSION_017/018 lessons:

```text
1. IMPLEMENT one task
2. VERIFY with command (grep, pytest, import check)
3. DOCUMENT evidence in plan
4. ONLY THEN mark complete
```

**NEVER mark a task complete without running verification.**

### Gate Rules

| Gate | Requirement |
|------|-------------|
| Discussion → ADR | USER approves decision is needed |
| ADR → SPEC | ADR status is 'active' |
| SPEC → Contract | SPEC status is 'active' |
| Contract → Plan | Imports verified |
| Task → Complete | Verification command passes |

### L3 Execution Protocol (Budget Models)

L3 plans are chunked for smaller context windows. Target: 600 lines, Soft limit: 800 lines.

**Before Starting Any Chunk:**

1. Read `.plans/L3/<PLAN>/INDEX.json` first
2. Check `current_chunk` field to know which chunk to execute
3. Read the chunk file specified in `chunks[current_chunk].chunk_file`
4. Create session file: `.sessions/SESSION_XXX_<plan>_<chunk>_<summary>.md`
5. Run baseline tests and document result in session file
6. If baseline fails with unrelated errors, document and proceed
7. If baseline fails with related errors, create `.questions/` file and STOP

**During Execution:**

1. Follow each step in order - do not skip steps
2. Copy code snippets EXACTLY - do not modify
3. Run `verification_hint` after each step
4. If any step fails, create `.questions/` file and STOP (L3 is strict)
5. After every 5 tasks, update session file with progress

**Self-Reflection Checkpoint (every 5 tasks):**

```text
CHECKPOINT:
- [ ] Am I following established patterns from continuation_context?
- [ ] Did I create files in the correct locations?
- [ ] Did I run verification commands for completed tasks?
- [ ] Should I escalate any blockers to .questions/?
```

**After Completing Chunk:**

1. Run all acceptance criteria verification commands
2. Update INDEX.json: `current_chunk`, `last_completed_task`, `continuation_context`
3. Add entry to `execution_history` with your model name (self-report!)
4. Update session file with handoff notes
5. Commit: `git add -A && git commit -m 'PLAN-XXX <chunk>: <summary>'`

**Verification Strictness by Granularity:**

| Granularity | On Failure |
|-------------|------------|
| L1 (Premium) | Log and continue - models can self-correct |
| L2 (Mid-tier) | Log failure, continue with caution |
| L3 (Budget) | STOP and create `.questions/` file |

### Quick Reference: New Artifacts

```bash
# Create new discussion
python scripts/workflow/new_discussion.py "Title"

# Create new plan
python scripts/workflow/new_plan.py "Title"
```

See `.discussions/AGENTS.md` and `.plans/AGENTS.md` for detailed instructions.

<!-- WINDSURF_SPECIFIC: End of AI Development Workflow section -->

---

## Where to Find Things

| Need | Location |
|------|----------|
| Data contracts | `shared/contracts/core/dataset.py` |
| DAT contracts | `shared/contracts/dat/` |
| ADR Index | `.adrs/INDEX.md` |
| SPEC Index | `docs/specs/INDEX.md` |
| Test fixtures | `tests/fixtures/` |
| CI scripts | `ci/steps/` |

---

*This AGENTS.md follows Windsurf's hierarchical pattern. See subdirectory AGENTS.md files for tool-specific rules.*
