# {PLAN-ID}: {Plan Title} - L1 Execution Guide

> **Granularity**: L1 (Standard) - For premium models with strong inference capability
> **Target Models**: Claude Opus, Claude Sonnet 3.5+, GPT-4o, Gemini 1.5 Pro

---

## Quick Start

```text
{PLAN-ID} L1 EXECUTION

You are executing {PLAN-ID} using L1 (Standard) granularity.

Plan location: .plans/{PLAN-ID}.json

Read the plan file and execute milestones in order. For each task:
1. Read the `description` and `context[]` fields
2. Implement based on your understanding of the context
3. Run `verification_command` to verify completion
4. Update task `status` to "passed" with `evidence`

On verification failure: Log the issue and continue (L1 allows inference-based recovery).

Create session file: .sessions/SESSION_XXX_{PLAN-ID}_<summary>.md

Begin with Milestone M1, Task T-M1-01
```

---

## Pre-Execution Checklist

- [ ] Read plan file completely
- [ ] Create session file
- [ ] Run baseline tests: `pytest tests/ -v --tb=no -q`
- [ ] Note any pre-existing failures (unrelated = proceed)

---

## Milestone Prompts

### M1: {Milestone Name}

```text
Execute M1 of {PLAN-ID}

Tasks:
- T-M1-01: {description}
- T-M1-02: {description}
...

Use the `context[]` field in each task for implementation hints.
Run `verification_command` after each task.

Acceptance Criteria:
{List from plan}
```

### M2: {Milestone Name}

```text
Execute M2 of {PLAN-ID}

Continuation from M1:
- Files created: {list}
- Patterns established: {list}

Tasks:
- T-M2-01: {description}
...
```

<!-- Add more milestones as needed -->

---

## L1 Execution Rules

| Rule | Description |
|------|-------------|
| **Inference** | Use context to infer implementation details |
| **On Failure** | Log and continue - you can self-correct |
| **Verification** | Run verification_command after each task |
| **Evidence** | Record command output in task.evidence |

---

## Post-Execution Checklist

- [ ] All tasks have status: "passed" or "failed" with evidence
- [ ] Acceptance criteria verified
- [ ] Session file updated with summary
- [ ] Commit: `git add -A && git commit -m "{PLAN-ID}: {summary}"`

---

## Troubleshooting

**Verification fails**: 
- Review your implementation
- Check if context was misunderstood
- Log the issue in session file
- Attempt fix, then continue

**Unclear context**:
- Check related files mentioned in context
- Infer from existing codebase patterns
- If truly stuck, create `.questions/` file

---

*L1 Execution Guide per ADR-0043*
