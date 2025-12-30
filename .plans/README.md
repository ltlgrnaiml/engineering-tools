# Plans Directory

> **Purpose**: Track implementation plans with milestones, tasks, and acceptance criteria for AI-assisted development.

## Overview

The `.plans/` directory contains **Implementation Plans** that break down work into verifiable milestones and tasks. Plans are created after requirements are understood (from Discussions, SPECs, or direct requests).

## When to Create a Plan

Create a plan when:

- Implementing a feature from a **SPEC**
- Executing a **refactoring** with multiple steps
- Any work with **more than 3 tasks**
- Work that spans **multiple sessions**

## File Naming Convention

```text
PLAN-{NNN}_{Brief-Description}.json
```

Examples:

- `PLAN-001_DAT-Streaming-Implementation.json`
- `PLAN-002_PPTX-Renderer-Refactor.json`
- `PLAN-003_SOV-Pipeline-Integration.json`

> **Note**: Plans use JSON format with Pydantic schema validation via `shared/contracts/plan_schema.py`

## Plan Lifecycle

```text
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   DRAFT     │ ──► │   ACTIVE    │ ──► │ IN_PROGRESS │ ──► │  COMPLETED  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │   BLOCKED   │
                                        └─────────────┘
```

## Quick Start

1. **Create from template**:

   ```bash
   python scripts/workflow/new_plan.py "Brief Description"
   ```

2. **Or copy template manually**:

   ```bash
   # Template is now JSON-based
   cp .plans/.templates/PLAN_TEMPLATE.json .plans/PLAN-XXX_Name.json
   ```

3. **Define milestones** with explicit acceptance criteria

4. **Execute tasks** one at a time, verifying each before proceeding

## Directory Structure

```text
.plans/
├── README.md                    # This file
├── INDEX.md                     # Index of all plans
├── .templates/
│   ├── PLAN_TEMPLATE.json       # JSON template for new plans
│   └── PLAN_TEMPLATE.md         # Markdown template (legacy)
├── PLAN-001_Example.json        # Individual plans (JSON)
└── ...
```

## Key Concepts

### Milestones

Milestones are major checkpoints with:

- Clear **deliverables**
- **Acceptance criteria** with verification commands
- **Dependencies** on other milestones

### Tasks

Tasks are atomic units of work:

- One task = one verifiable change
- Each task has a **verification command**
- Tasks are marked complete **only after verification passes**

### Fragment-Based Execution

Per SESSION_018 lessons learned:

1. **Implement** the change
2. **Verify** with grep/test command
3. **Document** evidence of verification
4. **Proceed** only after verification passes

## Integration with AI Assistant

The AI assistant (Cascade) will:

1. **Reference** the active plan at session start
2. **Execute** one task at a time
3. **Verify** before marking complete
4. **Update** progress in the plan file
5. **Handoff** notes for next session

## Related Directories

| Directory | Purpose | Relationship |
|-----------|---------|--------------|
| `.discussions/` | Design conversations | Plans created FROM discussions |
| `.adrs/` | Architecture decisions | Plans implement ADR decisions |
| `docs/specs/` | Behavioral specs | Plans implement SPEC requirements |
| `.sessions/` | Session logs | Sessions reference active plans |

## Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Marking task done without verification | Run verification command first |
| Working on multiple tasks simultaneously | Complete one task fully before next |
| Skipping blocked tasks | Document blocker and ask USER |
| Creating tasks without ACs | Every task needs verification criteria |

---

*Part of the AI Development Workflow. See `docs/guides/AI_DEVELOPMENT_WORKFLOW.md` for complete documentation.*
