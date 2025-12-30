# {PLAN-ID}: {Plan Title} - L2 Execution Guide

> **Granularity**: L2 (Enhanced) - For mid-tier models needing explicit constraints
> **Target Models**: Claude Sonnet 3.5, GPT-4o-mini, Gemini 1.5 Flash, Grok-2

---

## Quick Start

```text
{PLAN-ID} L2 EXECUTION

You are executing {PLAN-ID} using L2 (Enhanced) granularity.

Plan location: .plans/{PLAN-ID}.json

For each task, you MUST read these fields:
- `context[]` - Key context with prefixes (ARCHITECTURE:, FILE:, FUNCTION:, ENUM:)
- `hints[]` - Implementation patterns to follow
- `constraints[]` - DO NOT, MUST, EXACTLY rules to obey
- `references[]` - Files to check before implementing
- `existing_patterns[]` - Code examples to match

Execute milestones in order. For each task:
1. Read ALL L2 fields before implementing
2. Check `references[]` files for patterns
3. Follow `constraints[]` EXACTLY
4. Run `verification_command` to verify
5. Log failure with caution, then continue

Create session file: .sessions/SESSION_XXX_{PLAN-ID}_<summary>.md

Begin with Milestone M1, Task T-M1-01
```

---

## Pre-Execution Checklist

- [ ] Read plan file completely
- [ ] Check all `references[]` files exist
- [ ] Create session file
- [ ] Run baseline tests: `pytest tests/ -v --tb=no -q`
- [ ] Note any pre-existing failures

---

## L2-Specific Fields Reference

### Context Prefixes

| Prefix | Meaning | Example |
|--------|---------|---------|
| `ARCHITECTURE:` | Style guidance | "Functional style, no classes" |
| `FILE:` | Exact file path | "Modify gateway/services/foo.py" |
| `FUNCTION:` | Exact signature | "def scan_items(query: str) -> list" |
| `ENUM:` | Exact values | "Status: draft, active, deprecated" |
| `VERSION:` | Format spec | "__version__ = '2025.12.01'" |
| `PARAM:` | Naming convention | "Use 'search' not 'search_query'" |

### Constraints Format

| Keyword | Meaning | Example |
|---------|---------|---------|
| `DO NOT` | Forbidden action | "DO NOT use class-based architecture" |
| `MUST` | Required action | "MUST place tests in tests/gateway/" |
| `EXACTLY` | Precise value | "EXACTLY 5 enum values, no more" |

---

## Milestone Prompts

### M1: {Milestone Name}

```text
Execute M1 of {PLAN-ID} (L2 Enhanced)

Tasks with L2 fields:

T-M1-01: {description}
  context: {list}
  hints: {list}
  constraints: {list}
  references: {list}

T-M1-02: {description}
  context: {list}
  hints: {list}
  constraints: {list}
  references: {list}

IMPORTANT: Read `constraints[]` BEFORE implementing each task.

Acceptance Criteria:
{List from plan}
```

### M2: {Milestone Name}

```text
Execute M2 of {PLAN-ID} (L2 Enhanced)

Continuation from M1:
- Files created: {list}
- Patterns to maintain: {list}

Tasks: {list with L2 fields}
```

<!-- Add more milestones as needed -->

---

## L2 Execution Rules

| Rule | Description |
|------|-------------|
| **Context** | REQUIRED - Read all context prefixes |
| **Constraints** | MUST obey all DO NOT/MUST/EXACTLY rules |
| **On Failure** | Log with caution, continue carefully |
| **References** | Check referenced files before implementing |
| **Patterns** | Match existing_patterns exactly |

---

## Post-Execution Checklist

- [ ] All `constraints[]` were followed
- [ ] All tasks have status with evidence
- [ ] `existing_patterns[]` were matched
- [ ] Session file updated with summary
- [ ] Commit: `git add -A && git commit -m "{PLAN-ID}: {summary}"`

---

## Troubleshooting

**Constraint violation detected**:
- STOP and review the constraint
- Undo the violating change
- Re-implement following the constraint

**Pattern mismatch**:
- Open the `existing_patterns[]` file
- Copy the exact structure
- Adapt only the specific logic

**Verification fails repeatedly**:
- Check if you missed a constraint
- Review hints for missed patterns
- Log issue in session file, continue with caution

---

*L2 Execution Guide per ADR-0043*
