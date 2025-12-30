# {PLAN-ID}: {Plan Title} - L3 Execution Guide

> **For AI Assistants**: This file contains prompts and instructions for executing L3 chunked plans.
> Copy the appropriate milestone section below into your AI chat to begin execution.

---

## Quick Start

1. Read `INDEX.json` to find `current_chunk`
2. Copy the prompt for that milestone below
3. Paste into your AI assistant
4. Follow the L3 execution protocol

---

## Pre-Execution Checklist

Before starting any milestone:

- [ ] Read `INDEX.json` completely
- [ ] Check `current_chunk` field
- [ ] Review `continuation_context` for files already created
- [ ] Create session file: `.sessions/SESSION_XXX_{PLAN-ID}_<chunk>_<summary>.md`
- [ ] Run baseline tests: `pytest tests/ -v --tb=no -q`

---

## Milestone M1: {Milestone Name}

**Status**: {pending|in_progress|completed}

```text
{PLAN-ID} L3 EXECUTION: Milestone M1 - {Milestone Name}

You are executing Milestone M1 using L3 (Procedural) granularity.

Plan location: .plans/L3/{PLAN-ID}/{PLAN-ID}_L3_M1.json

Your task: Execute all {N} tasks by following the `steps` array in each task:
- T-M1-01: {Task description}
- T-M1-02: {Task description}
- ...

Rules:
1. Follow EACH step in the `steps` array sequentially
2. Use the `code_snippet` provided - copy it EXACTLY
3. Stop at steps marked `checkpoint: true` to verify
4. Run the task's `verification_command` after all steps
5. Create .questions/ file and STOP if any step fails

Session file: .sessions/SESSION_XXX_{PLAN-ID}_M1_{summary}.md

Acceptance Criteria (run after all tasks):
- {AC-M1-01 verification command}
- {AC-M1-02 verification command}

Begin with T-M1-01, step 1
```

---

## Milestone M2: {Milestone Name}

**Status**: {pending|in_progress|completed}

```text
{PLAN-ID} L3 EXECUTION: Milestone M2 - {Milestone Name}

Plan location: .plans/L3/{PLAN-ID}/{PLAN-ID}_L3_M2.json

Continuation context from M1:
- Files created: {list from INDEX.json continuation_context}
- Patterns: {list from continuation_context.patterns_established}

Your task: Execute all {N} tasks:
- T-M2-01: {Task description}
- ...

Session file: .sessions/SESSION_XXX_{PLAN-ID}_M2_{summary}.md

Begin with T-M2-01, step 1
```

---

<!-- Repeat for each milestone -->

---

## Post-Execution Checklist

After completing a milestone:

- [ ] All tasks marked complete with evidence
- [ ] Acceptance criteria verified
- [ ] Session file updated with handoff notes
- [ ] INDEX.json updated:
  - `current_chunk` → next milestone
  - `last_completed_task` → last task ID
  - `continuation_context.files_created` updated
  - `chunks[completed].status` → "completed"
- [ ] Commit changes: `git add -A && git commit -m "{PLAN-ID} M<N>: <summary>"`

---

## Troubleshooting

### Step fails verification

```text
1. Do NOT proceed to next step
2. Create .questions/IMPL_{PLAN-ID}_M<N>_<issue>.md
3. Document: task, step, error, what you tried
4. STOP and wait for user guidance
```

### Code snippet doesn't apply cleanly

```text
1. Check if file already exists with different content
2. Check continuation_context for previous modifications
3. If conflict, document in .questions/ and STOP
```

### Baseline tests fail

```text
1. Document which tests fail in session file
2. If failures are UNRELATED to current milestone → proceed
3. If failures are RELATED → create .questions/ and STOP
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python scripts/workflow/verify_plan.py .plans/{PLAN-ID}.json` | Validate plan |
| `pytest tests/ -v` | Run all tests |
| `ruff check .` | Lint Python |
| `cd apps/*/frontend && npm run build` | Build frontend |

---

*This EXECUTION.md is a standard L3 artifact per ADR-0043.*
