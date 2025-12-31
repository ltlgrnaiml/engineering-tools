# PLAN-{NNN}: {Title}

> **Status**: `draft` | `active` | `in_progress` | `completed` | `blocked` | `abandoned`
> **Created**: {YYYY-MM-DD}
> **Updated**: {YYYY-MM-DD}
> **Author**: {Name}
> **Source**: DISC-{XXX} | SPEC-{XXX} | Direct Request

---

## Summary

{One paragraph describing what this plan implements}

---

## Objective

{Clear statement of what success looks like}

---

## Source References

| Type | ID | Title |
|------|----|-------|
| Discussion | DISC-{XXX} | {Title} |
| ADR | ADR-{XXXX} | {Title} |
| SPEC | SPEC-{XXX} | {Title} |

---

## Prerequisites

- [ ] {Prerequisite 1 - e.g., "Tests pass before changes"}
- [ ] {Prerequisite 2 - e.g., "Dependency X installed"}

---

## Milestones

### M1: {Milestone Name}

**Objective**: {What this milestone achieves}

**Deliverables**:

- {Deliverable 1}
- {Deliverable 2}

**Acceptance Criteria**:

| ID | Criterion | Verification Command | Status |
|----|-----------|---------------------|--------|
| AC-M1-01 | {Description} | `{command}` | `pending` / `passed` / `failed` |
| AC-M1-02 | {Description} | `{command}` | `pending` / `passed` / `failed` |

**Dependencies**: None | M{X}

**Tasks**:

- [ ] **T-M1-01**: {Task description}
  - Verification: `{grep/test command}`
- [ ] **T-M1-02**: {Task description}
  - Verification: `{grep/test command}`

---

### M2: {Milestone Name}

**Objective**: {What this milestone achieves}

**Deliverables**:

- {Deliverable 1}

**Acceptance Criteria**:

| ID | Criterion | Verification Command | Status |
|----|-----------|---------------------|--------|
| AC-M2-01 | {Description} | `{command}` | `pending` / `passed` / `failed` |

**Dependencies**: M1

**Tasks**:

- [ ] **T-M2-01**: {Task description}
  - Verification: `{grep/test command}`

---

## Global Acceptance Criteria

These apply to ALL milestones:

| ID | Criterion | Verification Command |
|----|-----------|---------------------|
| AC-GLOBAL-01 | All tests pass | `pytest tests/ -v` |
| AC-GLOBAL-02 | No linting errors | `ruff check .` |
| AC-GLOBAL-03 | Imports verified | `python -c "from {module} import {class}"` |

---

## Execution Log

### Session {XXX} - {YYYY-MM-DD}

**Started**: {HH:MM}
**Ended**: {HH:MM}

**Work Completed**:

- [x] T-M1-01: {Brief description}
- [x] T-M1-02: {Brief description}

**Verification Evidence**:

```bash
$ {verification command}
{output showing success}
```

**Blockers Encountered**:

- None | {Blocker description}

**Next Session Focus**:

- {What to work on next}

---

## Progress Summary

| Milestone | Status | Tasks Done | Tasks Total | Last Updated |
|-----------|--------|------------|-------------|--------------|
| M1 | `pending` / `in_progress` / `completed` | 0 | 2 | {DATE} |
| M2 | `pending` / `in_progress` / `completed` | 0 | 1 | {DATE} |

**Overall Progress**: 0% (0/3 tasks)

---

## Blockers

| ID | Description | Raised | Status | Resolution |
|----|-------------|--------|--------|------------|
| B-001 | {Blocker description} | {DATE} | `open` / `resolved` | {How resolved} |

---

## Lessons Learned

<!-- Capture insights for future plans -->

- {Lesson 1}
- {Lesson 2}

---

## Completion Checklist

Before marking this plan as COMPLETED:

- [ ] All milestones completed
- [ ] All acceptance criteria passed
- [ ] All tests pass
- [ ] No blockers remain open
- [ ] Known bugs documented (if any)
- [ ] Completion type selected (mvp_shipped / fully_complete)
- [ ] INDEX.md updated

---

## Completion Status

<!-- Fill this section when closing the plan -->

**Completion Type**: `mvp_shipped` | `fully_complete` | `superseded`
**Completion Date**: {YYYY-MM-DD}
**Deferred To**: {PLAN-XXX if work continues, or "None"}

### Known Bugs

<!-- Option A: Milestone-Based Closure - Bugs don't block closure, they're documented -->

| ID | Description | Severity | Component | Workaround | Deferred To |
|----|-------------|----------|-----------|------------|-------------|
| BUG-001 | {Bug description} | `low` / `medium` / `high` | {file/component} | {workaround if any} | {PLAN-XXX} |

---

## Handoff Notes

<!-- For the next session -->

**Current State**: {Brief description of where things stand}

**Immediate Next Steps**:

1. {Step 1}
2. {Step 2}

**Known Issues**:

- {Issue 1}

**Files Modified This Session**:

- `{path/to/file1.py}` - {brief change description}
- `{path/to/file2.py}` - {brief change description}

---

*Template version: 1.0.0 | See `.plans/README.md` for usage instructions*
