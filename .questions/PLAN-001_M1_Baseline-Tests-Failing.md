# PLAN-001 / M1 Execution Blocker: Baseline Tests Failing

## Context

Per PLAN-001 prerequisites and global workflow rules, baseline tests should pass before implementing Milestone M1 changes.

I ran:

```bash
pytest tests/ -v
```

Result: **FAIL** (10 failing tests).

## Failure Summary

The failures appear unrelated to DevTools Workflow Manager and look like contract/test drift in DAT profiles.

Examples from the output:

- `pydantic_core._pydantic_core.ValidationError`: `TableConfig.select` field required
- `pydantic_core._pydantic_core.ValidationError`: `OutputConfig` validation error
- `TypeError`: `'RepeatOverConfig' object is not subscriptable`
- `TypeError`: `argument of type 'ExtractionResult' is not a container or iterable`

## Decision Needed

How do you want to proceed?

### Option A (Strict)

Fix the failing baseline tests first (outside PLAN-001 scope), then resume PLAN-001/M1. This preserves regression protection.

### Option B (Proceed with PLAN-001 anyway)

Proceed with M1 tasks despite failing baseline tests. We can still run each M1 task verification command + the new DevTools unit tests, but we cannot claim "full-suite non-regression" until the baseline failures are resolved.

## Recommendation

Option A if you want strict regression guarantees.
Option B if you want to prioritize DevTools work and accept temporary inability to validate with full suite.
