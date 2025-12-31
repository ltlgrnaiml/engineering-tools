# Plans - AI Agent Instructions

<!-- WINDSURF_SPECIFIC: This file contains Windsurf Cascade-specific instructions.
     To migrate to a different AI tool, search for "WINDSURF_SPECIFIC" and remove/replace
     this file with instructions for your new tool. -->

> **Applies to**: All files in `.plans/` directory
> **AI Tool**: Windsurf Cascade
> **ADR Reference**: ADR-0043 (AI Development Workflow)

---

## Purpose

This directory contains **Plan** artifacts (Tier 4 of the AI Development Workflow).
Plans break down implementation work into milestones, tasks, and acceptance criteria.

---

## WINDSURF_SPECIFIC: Cascade Behavior Rules

### When to Create a Plan

**ALWAYS** create a plan when:

1. Work has **more than 3 tasks**
2. Work spans **multiple sessions**
3. USER explicitly requests structured implementation
4. Implementing from a **SPEC** or **Discussion**

**MAY SKIP** plan for:

1. Single-file bug fixes
2. Documentation updates
3. Simple refactoring (< 3 files)
4. Direct, clear implementation requests

### How to Create a Plan

1. **Check INDEX.md** for highest PLAN-XXX number
2. **Claim next number** (e.g., PLAN-003)
3. **Copy template**: `.templates/PLAN_TEMPLATE.md`
4. **Define milestones** with explicit acceptance criteria
5. **Break into tasks** with verification commands
6. **Update INDEX.md** with new plan

```markdown
Example prompt to USER:
"This implementation has multiple steps. I'll create a plan (PLAN-XXX) with 
milestones and tasks. Each task will have a verification command. Proceed?"
```

---

## WINDSURF_SPECIFIC: Fragment-Based Execution

### The Golden Rule

**NEVER mark a task complete without running its verification command.**

This rule exists because of SESSION_017 and SESSION_018 lessons:
- Creating code is NOT the same as wiring code
- Tests must pass, not just exist
- Imports must be verified, not assumed

### Execution Flow

For each task:

```text
1. READ the task description and verification command
2. IMPLEMENT the change
3. RUN the verification command
4. IF passes → Mark [x] and log evidence
5. IF fails → Debug, fix, re-verify
6. ONLY THEN proceed to next task
```

### Verification Evidence

Log verification evidence in the Execution Log:

```markdown
**Verification Evidence**:
$ grep "from shared.contracts.pptx import PPTXStageId" apps/pptx_generator/
apps/pptx_generator/backend/src/routes.py:from shared.contracts.pptx import PPTXStageId
✓ Import verified

$ pytest tests/pptx/test_workflow.py -v
======================== 3 passed in 0.42s ========================
✓ Tests pass
```

---

## WINDSURF_SPECIFIC: Session Management

### At Session Start

1. **Read** `.plans/INDEX.md` for active plans
2. **Read** the active plan file
3. **Check** Progress Summary for current state
4. **Read** Handoff Notes from previous session
5. **Announce** what you'll work on this session

```markdown
Example session start message:
"Continuing PLAN-002. Last session completed M1. Starting M2 today.
First task: T-M2-01 (Add streaming endpoint)."
```

### During Session

1. **Work one task at a time**
2. **Update task checkbox** when verified complete
3. **Log work** in Execution Log section
4. **Note blockers** immediately in Blockers table

### At Session End

1. **Update Progress Summary** table
2. **Write Handoff Notes** for next session
3. **List files modified** this session
4. **Update INDEX.md** with current progress

---

## WINDSURF_SPECIFIC: Gate Rules

### Gate: Plan → Active

Before starting execution:

- [ ] All milestones have acceptance criteria
- [ ] All tasks have verification commands
- [ ] Prerequisites are met (tests pass, deps installed)
- [ ] USER has approved the plan

### Gate: Milestone → Complete

Before marking milestone complete:

- [ ] All tasks in milestone are [x] verified
- [ ] All acceptance criteria pass (run verification commands)
- [ ] No open blockers for this milestone

### Gate: Plan → Complete

Before marking plan complete:

- [ ] All milestones completed
- [ ] Global acceptance criteria pass
- [ ] No open blockers
- [ ] Known bugs documented (if any)
- [ ] Completion type selected
- [ ] INDEX.md updated

---

## WINDSURF_SPECIFIC: Option A - Milestone-Based Closure

### Completion Types

| Type | When to Use | Known Bugs |
|------|-------------|------------|
| `mvp_shipped` | Core functionality works, polish/edge cases remain | Document in `known_bugs[]` |
| `fully_complete` | All work done, no known bugs | Empty `known_bugs[]` |
| `superseded` | Replaced by another plan | Link via `deferred_to` |

### Known Bug Documentation

When closing a plan with `mvp_shipped`:

1. **Document each bug** with ID, severity, and description
2. **Assess severity**: low (cosmetic), medium (workaround exists), high (significant)
3. **Optionally defer** to a follow-up plan via `deferred_to`
4. **Bugs do NOT block closure** - they're tracked, not blockers

```json
{
  "completion_type": "mvp_shipped",
  "completion_date": "2025-12-30",
  "known_bugs": [
    {
      "id": "BUG-001",
      "description": "AI input box doesn't shrink on small screens",
      "severity": "low",
      "affected_component": "WorkflowStepper.tsx",
      "workaround": "Scroll the page",
      "deferred_to": "PLAN-002"
    }
  ],
  "deferred_to": "PLAN-002"
}
```

### Why This Pattern?

1. **Clean signal**: Plan is DONE even if imperfect
2. **Bug visibility**: Future developers see known bugs
3. **No infinite plans**: Bugs don't keep plans open forever
4. **Traceability**: Bugs link to follow-up work

---

## WINDSURF_SPECIFIC: Blocker Handling

When encountering a blocker:

1. **STOP** current task immediately
2. **LOG** blocker in Blockers table with date
3. **ASK** USER for guidance
4. **DO NOT** work around or skip blocker

```markdown
Example blocker message:
"BLOCKER encountered on T-M2-03: The streaming API requires websocket 
support which isn't configured. Options:
1. Add websocket configuration (scope creep)
2. Use polling instead (design change)
3. Defer this milestone

Which approach should I take?"
```

---

## WINDSURF_SPECIFIC: File Operations

### Reading Plans

```text
1. Read .plans/INDEX.md for active plans
2. Read active plan file
3. Check Progress Summary for current milestone
4. Read Handoff Notes if continuing previous work
```

### Updating Plans

```text
1. Mark completed tasks with [x]
2. Update Progress Summary percentages
3. Add entries to Execution Log
4. Update milestone status
5. Write Handoff Notes before session end
```

### Indexing

```text
1. Keep INDEX.md in sync with plan states
2. Update statistics at bottom
3. Move plans between sections as status changes
```

---

## WINDSURF_SPECIFIC: Plan Granularity Levels

Per ADR-0043, plans support three granularity levels matched to AI model capability:

### L1: Standard (Premium Models)

**Target Models**: Claude Opus, Claude Sonnet 3.5+, GPT-4o, Gemini 1.5 Pro

**Template**: `.templates/PLAN_TEMPLATE.json`

**Task Schema**:
- `id`, `description`, `verification_command`, `status` (required)
- `context[]` (optional but recommended)

**Execution**: Models infer implementation from context. Log and continue on failure.

### L2: Enhanced (Mid-Tier Models)

**Target Models**: Claude Sonnet 3.5, GPT-4o-mini, Gemini 1.5 Flash, Grok-2

**Template**: `.templates/PLAN_TEMPLATE_L2.json`

**Task Schema** (L1 + these fields):
- `context[]` (REQUIRED - use prefixes: ARCHITECTURE:, FILE:, FUNCTION:, ENUM:)
- `hints[]` - Implementation hints and patterns
- `constraints[]` - DO NOT, MUST, EXACTLY rules
- `references[]` - File paths to reference
- `existing_patterns[]` - Examples to match

**When to use L2**:
- Task involves multiple files
- Task has complex dependencies
- Task requires specific naming conventions
- Previous similar task failed verification

**Execution**: Log and continue with caution on failure.

### L3: Procedural (Budget Models)

**Target Models**: Claude Haiku, Gemini Flash 8B, Grok-fast, GPT-4o-mini (strict)

**Template**: `.templates/L3_FRAGMENT_TEMPLATE.json`

**Task Schema** (L2 + these fields):
- `steps[]` (REQUIRED) - Step-by-step instructions with code snippets
  - `step_number`, `instruction`, `verification_hint` (required per step)
  - `code_snippet`, `file_path`, `checkpoint` (optional)

**Fragmentation**: L3 plans are split into 600-line fragments (800 soft limit)
- Index file: `.plans/L3/<PLAN-ID>/INDEX.json`
- Fragment files: `.plans/L3/<PLAN-ID>/PLAN-XXX_L3_<milestone>.json`

**Execution**: STOP and escalate to `.questions/` on failure (no log_and_continue).

### Execution Guides (Standard Artifacts)

Every plan SHOULD include an `EXECUTION.md` file with copy-paste prompts for AI execution.

**Templates by Granularity**:

| Level | Template | Location |
|-------|----------|----------|
| L1 | `.templates/EXECUTION_L1.md` | `.plans/{PLAN-ID}_EXECUTION.md` |
| L2 | `.templates/EXECUTION_L2.md` | `.plans/{PLAN-ID}_EXECUTION.md` |
| L3 | `.templates/EXECUTION_L3.md` | `.plans/L3/{PLAN-ID}/EXECUTION.md` |

**L3 Directory Structure**:

```text
.plans/L3/<PLAN-ID>/
├── INDEX.json           # Fragment index and continuation context
├── EXECUTION.md         # Human/AI-readable execution prompts
├── PLAN-XXX_L3_M1.json  # Fragment files
├── PLAN-XXX_L3_M2.json
└── ...
```

**Purpose**:
- Provides copy-paste prompts for each milestone
- Contains pre/post-execution checklists
- Documents troubleshooting steps
- Serves as the "how to run this plan" guide

**Required Sections**:
1. Quick Start - Prompt with rules and plan location
2. Pre-Execution Checklist - Session file, baseline tests
3. Milestone Prompts - One per milestone with task list
4. Post-Execution Checklist - Updates, commits
5. Troubleshooting - Failure handling per granularity

**Failure Handling by Level**:

| Level | On Failure |
|-------|------------|
| L1 | Log and continue (self-correct) |
| L2 | Log with caution, continue carefully |
| L3 | STOP, create `.questions/` file |

**When creating a new plan**:
1. Choose granularity (L1/L2/L3)
2. Create plan from appropriate template
3. Create EXECUTION.md from matching template
4. Fill in milestone prompts with task lists and ACs

### Validation

Run validation before execution:

```bash
python scripts/workflow/verify_plan.py .plans/PLAN-XXX.json
python scripts/workflow/verify_plan.py --all  # Validate all plans
```

---

## Schema Reference

See `.templates/PLAN_TEMPLATE.json` for L1 schema.
See `.templates/PLAN_TEMPLATE_L2.json` for L2 schema.
See `.templates/L3_FRAGMENT_TEMPLATE.json` for L3 fragment schema.

Key sections:

| Section | Purpose | Update Frequency |
|---------|---------|------------------|
| Milestones | Major checkpoints with ACs | At creation |
| Tasks | Atomic work units with verification | During execution |
| Execution Log | Session-by-session work record | Every session |
| Progress Summary | Quick status view | After each task |
| Blockers | Issues preventing progress | When encountered |
| Handoff Notes | Context for next session | End of session |

---

## Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Marking task done without verification | Run verification command first |
| Working multiple tasks in parallel | Complete one task fully before next |
| Skipping blockers | Stop, log, ask USER |
| Not updating progress | Update after every task |
| Empty handoff notes | Always write next steps |
| Breadth over depth | Depth first: complete one milestone fully |

---

## Quick Reference: Task Verification Commands

Common verification patterns:

```bash
# Verify import exists
grep "from module import Class" path/to/files/

# Verify method is called
grep "method_name(" path/to/files/

# Verify tests pass
pytest tests/specific_test.py -v

# Verify no lint errors
ruff check path/to/file.py

# Verify module imports
python -c "from module import Class; print('OK')"

# Verify endpoint exists
grep "@router.post" path/to/routes.py
```

---

<!-- WINDSURF_SPECIFIC: End of Windsurf-specific instructions -->
