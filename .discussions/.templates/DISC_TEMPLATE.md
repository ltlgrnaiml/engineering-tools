# DISC-{NNN}: {Title}

> **Status**: `draft` | `active` | `resolved` | `abandoned`
> **Created**: {YYYY-MM-DD}
> **Updated**: {YYYY-MM-DD}
> **Author**: {Name}
> **AI Session**: SESSION_{XXX}
> **Depends On**: {DISC-XXX, DISC-YYY} | None
> **Blocks**: {DISC-ZZZ} | None
> **Dependency Level**: L0 | L1 | L2 | ...

---

## Summary

<!-- One paragraph describing what this discussion is about -->

{Brief description of the feature, enhancement, or topic being discussed}

---

## Context

<!-- Why are we having this discussion? What triggered it? -->

### Background

{Describe the current state and why change is needed}

### Trigger

{What event or need triggered this discussion?}

---

## Requirements

<!-- What must the solution achieve? Use natural language. -->

### Functional Requirements

- [ ] **FR-1**: {Requirement description}
- [ ] **FR-2**: {Requirement description}
- [ ] **FR-3**: {Requirement description}

### Non-Functional Requirements

- [ ] **NFR-1**: {Performance, security, maintainability, etc.}
- [ ] **NFR-2**: {Requirement description}

---

## Constraints

<!-- Hard limits that cannot be violated -->

- **C-1**: {Constraint description}
- **C-2**: {Constraint description}

---

## Open Questions

<!-- Questions that need answers before proceeding -->

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | {Question text} | `open` / `answered` | {Answer if resolved} |
| Q-2 | {Question text} | `open` / `answered` | {Answer if resolved} |

---

## Options Considered

<!-- If architectural decision needed, document options here -->

### Option A: {Name}

**Description**: {How this option works}

**Pros**:
- {Advantage 1}
- {Advantage 2}

**Cons**:
- {Disadvantage 1}
- {Disadvantage 2}

### Option B: {Name}

**Description**: {How this option works}

**Pros**:
- {Advantage 1}

**Cons**:
- {Disadvantage 1}

### Recommendation

{Which option is recommended and why}

---

## Decision Points

<!-- Key decisions that need to be made -->

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | {Decision description} | `pending` / `decided` | {Outcome if decided} |
| D-2 | {Decision description} | `pending` / `decided` | {Outcome if decided} |

---

## Scope Definition

<!-- What is in scope and out of scope for this work -->

### In Scope

- {Item 1}
- {Item 2}

### Out of Scope

- {Item 1 - reason}
- {Item 2 - reason}

---

## Cross-DISC Dependencies

<!-- Document dependencies on other DISCs (per ADR-0043 disc_dependency_management) -->

| Dependency | Type | Status | Blocker For | Notes |
|------------|------|--------|-------------|-------|
| DISC-{XXX} | `FS` / `FF` / `SS` / `soft` | `pending` / `stub` / `resolved` | {Milestones} | {Notes} |

### Stub Strategy (if applicable)

<!-- Document stubs used when dependencies aren't resolved -->

| DISC | Stub Location | Stub Behavior |
|------|---------------|---------------|
| DISC-{XXX} | `path/to/stub.py` | {What the stub does} |

---

## Resulting Artifacts

<!-- Link to artifacts created from this discussion -->

| Artifact Type | ID | Title | Status |
|---------------|----|-------|--------|
| ADR | ADR-{XXXX} | {Title} | `draft` / `active` |
| SPEC | SPEC-{XXX} | {Title} | `draft` / `active` |
| Contract | `shared/contracts/{path}` | {Description} | `created` |
| Plan | PLAN-{XXX} | {Title} | `draft` / `active` |

---

## Conversation Log

<!-- Key points from AI ↔ Human discussion (auto-updated by AI) -->

### {YYYY-MM-DD} - SESSION_{XXX}

**Topics Discussed**:
- {Topic 1}
- {Topic 2}

**Key Insights**:
- {Insight 1}
- {Insight 2}

**Action Items**:
- [ ] {Action 1}
- [ ] {Action 2}

---

## Resolution

<!-- Filled when discussion is resolved -->

**Resolution Date**: {YYYY-MM-DD}

**Outcome**: {Summary of what was decided/created}

**Next Steps**:
1. {Step 1}
2. {Step 2}

---

*Template version: 1.0.0 | See `.discussions/README.md` for usage instructions*
