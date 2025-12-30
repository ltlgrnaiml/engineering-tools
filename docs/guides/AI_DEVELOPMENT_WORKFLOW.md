# AI Development Workflow Guide

<!-- WINDSURF_SPECIFIC: This guide contains Windsurf-specific sections.
     Search for "WINDSURF_SPECIFIC" to find and remove/replace when migrating. -->

> **ADR Reference**: ADR-0041 (AI Development Workflow Orchestration)
> **Version**: 1.0.0
> **Last Updated**: 2025-12-30

---

## Overview

This guide explains how to use the AI Development Workflow for structured, spec-driven development with your AI coding assistant.

The workflow provides:

- **Structured conversations** that lead to traceable artifacts
- **Verifiable execution** that prevents incomplete implementations
- **Session continuity** for multi-session work
- **Clear handoffs** between development sessions

---

## Quick Start

### Creating a New Discussion

When exploring a new feature or architectural decision:

```bash
python scripts/workflow/new_discussion.py "Feature Name"
```

This creates `.discussions/DISC-XXX_Feature-Name.md` and updates the index.

### Creating a New Plan

When ready to implement:

```bash
python scripts/workflow/new_plan.py "Implementation Name"
```

This creates `.plans/PLAN-XXX_Implementation-Name.md` and updates the index.

---

## The 6-Tier Hierarchy

| Tier | Artifact | Purpose | When to Use |
|------|----------|---------|-------------|
| **T0** | Discussion | Capture design conversations | New features, architectural exploration |
| **T1** | ADR | Record architecture decisions | When choices have long-term impact |
| **T2** | SPEC | Define behavioral requirements | When scope is finalized |
| **T3** | Contract | Define data shapes (Pydantic) | When data structures are needed |
| **T4** | Plan | Track implementation work | When ready to code |
| **T5** | Fragment | Execute one task | During plan execution |

---

## Workflow Entry Points

Not all work requires the full workflow. Choose your entry point based on complexity:

| Scenario | Start At | Example |
|----------|----------|---------|
| **Architectural change** | T0 (Discussion) | "Should we use WebSockets or SSE?" |
| **New feature** | T0 or T2 | "Add streaming data support" |
| **Simple enhancement** | T2 (SPEC) | "Add validation to existing endpoint" |
| **New data structure** | T3 (Contract) | "Create new Pydantic model" |
| **Bug fix** | T4 (Plan) | "Fix null handling in parser" |
| **Refactor** | T4 (Plan) | "Extract service from route handler" |

---

## Detailed Workflow

### Phase 1: Discussion (T0)

**When**: You have an idea but need to explore requirements, constraints, or options.

**Steps**:

1. Create discussion: `python scripts/workflow/new_discussion.py "Title"`
2. Fill in Context and Requirements sections
3. Document constraints and open questions
4. Explore options with AI assistant
5. Record decisions as they're made

**Outputs**:

- Clear requirements
- Resolved questions
- Decision on approach
- Links to resulting ADRs/SPECs

### Phase 2: Decision (T1 - ADR)

**When**: An architectural decision needs to be recorded for future reference.

**Steps**:

1. Create ADR in `.adrs/` directory
2. Document context, options, decision, consequences
3. Set status to `active`
4. Reference from discussion

**Output**: ADR file that explains WHY a decision was made.

### Phase 3: Specification (T2 - SPEC)

**When**: Behavioral requirements need to be defined.

**Steps**:

1. Create SPEC in `docs/specs/` directory
2. Define requirements with acceptance criteria
3. Reference Tier-0 contracts
4. Set status to `active`

**Output**: SPEC file that defines WHAT to build.

### Phase 4: Contract (T3)

**When**: Data structures need to be defined.

**Steps**:

1. Create Pydantic models in `shared/contracts/`
2. Add `__version__` attribute
3. Export in `__init__.py`
4. Verify imports work

**Verification**:

```bash
python -c "from shared.contracts.module import NewModel; print('OK')"
```

### Phase 5: Plan (T4)

**When**: Ready to implement.

**Format**: JSON with Pydantic schema validation (`shared/contracts/plan_schema.py`)

**Steps**:

1. Create plan: `python scripts/workflow/new_plan.py "Title"`
2. Define milestones with acceptance criteria
3. Break into tasks with verification commands
4. Link source references (DISC, ADR, SPEC)

**Output**: JSON plan file (`.plans/PLAN-XXX_Name.json`) with executable tasks.

**Validation**:

```bash
python -c "from shared.contracts.plan_schema import PlanSchema; import json; PlanSchema(**json.load(open('.plans/PLAN-XXX.json')))"
```

### Plan Granularity Levels

Plans support **tiered granularity** for cost-effective AI execution (per ADR-0043):

| Level | Detail | Model Tier | Task Fields |
|-------|--------|------------|-------------|
| **L1 Standard** | Baseline with context | Mid-tier ($$) | `description`, `context[]`, `verification_command` |
| **L2 Enhanced** | + hints and references | Smaller ($) | + `hints[]`, `references[]` |
| **L3 Procedural** | + step-by-step instructions | Cheapest ($) | + `steps[]` with `code_snippet`, `checkpoint` |

**When to use each level**:

- **L1**: Standard work, have budget for capable model
- **L2**: Large scope, want guardrails against common mistakes
- **L3**: Massive project, budget-constrained, using smaller model

**Example L1 Task** (baseline):

```json
{
  "id": "T-M1-01",
  "description": "Add artifact list endpoint",
  "context": [
    "Endpoint: GET /api/devtools/artifacts",
    "Query params: type, search",
    "Response: ArtifactListResponse"
  ],
  "verification_command": "grep 'artifacts' gateway/routes/devtools.py"
}
```

**Example L3 Task** (procedural, for smaller models):

```json
{
  "id": "T-M1-01",
  "description": "Add artifact list endpoint",
  "context": ["..."],
  "hints": ["Use async def for FastAPI", "Watch for circular imports"],
  "references": ["gateway/routes/devtools.py"],
  "steps": [
    {"step_number": 1, "instruction": "Open gateway/routes/devtools.py"},
    {"step_number": 2, "instruction": "Add import:", "code_snippet": "from shared.contracts..."},
    {"step_number": 3, "instruction": "Add endpoint after line 87:", "code_snippet": "@router.get...", "checkpoint": true}
  ],
  "verification_command": "grep 'artifacts' gateway/routes/devtools.py"
}
```

**Expanding tasks**: Start at L1, ask AI to expand specific tasks to L2/L3 as needed.

### L3 Chunking Protocol (Budget Models)

For L3 plans targeting budget models (Haiku, Flash, Grok, GPT-4o-mini), plans are **chunked** to fit smaller context windows.

**Chunk Limits** (per ADR-0041):

| Limit | Lines | Rationale |
|-------|-------|-----------|
| Target | 600 | Optimal for budget model context |
| Soft | 800 | Acceptable with justification |

**L3 Directory Structure**:

```text
.plans/L3/PLAN-001/
├── INDEX.json              # Master index (read first!)
├── PLAN-001_L3_M1.json     # Milestone 1 chunk
├── PLAN-001_L3_M2.json     # Milestone 2 chunk
└── ...
```

**INDEX.json** contains:
- `current_chunk`: Which chunk to execute next
- `continuation_context`: Files created, patterns established
- `execution_history`: Which models executed which chunks

**Chunk Execution Protocol**:

1. **Before**: Read INDEX.json, create session file, run baseline tests
2. **During**: Follow steps exactly, verify each step, checkpoint every 5 tasks
3. **After**: Update INDEX.json, add to execution_history, commit

**Verification Strictness by Granularity**:

| Granularity | On Failure |
|-------------|------------|
| L1 (Premium) | Log and continue |
| L2 (Mid-tier) | Log, continue with caution |
| L3 (Budget) | STOP and create `.questions/` file |

See `AGENTS.md` for full L3 Execution Protocol.

### Phase 6: Fragment Execution (T5)

**When**: Executing plan tasks.

**The Golden Rule**: NEVER mark a task complete without verification.

**Steps** (for each task):

1. **Read** task description and verification command
2. **Implement** the change
3. **Run** verification command
4. **Pass** → Mark `[x]` and log evidence
5. **Fail** → Debug, fix, re-verify
6. **Proceed** to next task

---

## Fragment-Based Execution

This is the most critical part of the workflow. Per SESSION_017/018 lessons:

### The Pattern That Failed

```text
1. Create code (modules, methods, dataclasses)
2. Claim "complete" based on code existence
3. Never verify the code is called from execution path
```

### The Pattern That Works

```text
1. IMPLEMENT one task
2. VERIFY with command (grep, pytest, import check)
3. DOCUMENT evidence in plan
4. ONLY THEN mark complete
```

### Common Verification Commands

```bash
# Verify import exists
grep "from module import Class" path/to/files/

# Verify method is called
grep "method_name(" path/to/files/

# Verify tests pass
pytest tests/specific_test.py -v

# Verify no lint errors
ruff check path/to/file.py

# Verify module imports correctly
python -c "from module import Class; print('OK')"

# Verify endpoint exists
grep "@router.post" path/to/routes.py
```

---

## Session Management

### At Session Start

1. Check `.plans/INDEX.md` for active plans
2. Read the active plan file
3. Check Progress Summary for current state
4. Read Handoff Notes from previous session
5. Announce what you'll work on

### During Session

1. Work one task at a time
2. Update task checkbox when verified
3. Log work in Execution Log section
4. Note blockers immediately

### At Session End

1. Update Progress Summary table
2. Write Handoff Notes for next session
3. List files modified this session
4. Update INDEX.md with current progress

---

## Gate Rules

Gates prevent premature transitions:

| Gate | Requirement |
|------|-------------|
| Discussion → ADR | USER approves decision is needed |
| ADR → SPEC | ADR status is 'active' |
| SPEC → Contract | SPEC status is 'active' |
| Contract → Plan | Imports verified |
| Plan → Active | All tasks have verification commands |
| Task → Complete | Verification command passes |
| Milestone → Complete | All tasks verified, ACs pass |
| Plan → Complete | All milestones verified |

---

## Handling Blockers

When encountering a blocker:

1. **STOP** current task immediately
2. **LOG** blocker in Blockers table with date
3. **ASK** USER for guidance
4. **DO NOT** work around or skip

Example blocker message:

```text
BLOCKER on T-M2-03: The streaming API requires websocket support 
which isn't configured. Options:
1. Add websocket configuration (scope creep)
2. Use polling instead (design change)
3. Defer this milestone

Which approach should I take?
```

---

## Directory Structure

```text
engineering-tools/
├── .discussions/           # T0: Design conversations
│   ├── INDEX.md
│   ├── AGENTS.md          # WINDSURF_SPECIFIC
│   ├── .templates/
│   │   └── DISC_TEMPLATE.md
│   └── DISC-001_*.md
├── .plans/                 # T4: Implementation plans
│   ├── INDEX.md
│   ├── AGENTS.md          # WINDSURF_SPECIFIC
│   ├── .templates/
│   │   └── PLAN_TEMPLATE.md
│   └── PLAN-001_*.md
├── .adrs/                  # T1: Architecture decisions
├── docs/specs/             # T2: Specifications
├── shared/contracts/       # T3: Pydantic models
├── scripts/workflow/       # Automation scripts
│   ├── new_discussion.py
│   └── new_plan.py
└── AGENTS.md               # Root AI instructions
```

---

<!-- WINDSURF_SPECIFIC: Migrating to Other AI Tools section -->

## Migrating to Other AI Tools

When migrating from Windsurf to another AI tool:

1. **Search** for `WINDSURF_SPECIFIC` in all files
2. **Review** each marked section
3. **Replace or remove** Windsurf-specific instructions
4. **Update** AGENTS.md files with new tool's format

Files containing Windsurf-specific content:

- `.discussions/AGENTS.md` - Cascade behavior rules
- `.plans/AGENTS.md` - Cascade execution rules
- `AGENTS.md` - AI Development Workflow section
- `docs/guides/AI_DEVELOPMENT_WORKFLOW.md` - This file

The schema and templates are tool-agnostic and can remain unchanged.

<!-- WINDSURF_SPECIFIC: End of migration section -->

---

## Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Jumping to code without discussion | Create discussion first for complex work |
| Marking task done without verification | Run verification command first |
| Working multiple tasks in parallel | Complete one task fully before next |
| Skipping blockers | Stop, log, ask USER |
| Empty handoff notes | Always write next steps |
| Breadth over depth | Complete one milestone fully first |
| Creating backward compatibility shims | Delete old, fix all call sites |

---

## Quick Reference

### Create Discussion

```bash
python scripts/workflow/new_discussion.py "Title"
```

### Create Plan

```bash
python scripts/workflow/new_plan.py "Title"
```

### Verify Import

```bash
python -c "from module import Class; print('OK')"
```

### Run Tests

```bash
pytest tests/path/test_file.py -v
```

### Check Lint

```bash
ruff check path/to/file.py
```

---

*For detailed AI instructions, see the AGENTS.md files in `.discussions/` and `.plans/`.*
