# Discussions - AI Agent Instructions

<!-- WINDSURF_SPECIFIC: This file contains Windsurf Cascade-specific instructions.
     To migrate to a different AI tool, search for "WINDSURF_SPECIFIC" and remove/replace
     this file with instructions for your new tool. -->

> **Applies to**: All files in `.discussions/` directory
> **AI Tool**: Windsurf Cascade
> **ADR Reference**: ADR-0043 (AI Development Workflow)

---

## Purpose

This directory contains **Discussion** artifacts (Tier 0 of the AI Development Workflow).
Discussions capture the exploratory conversation between USER and AI before formal artifacts are created.

---

## WINDSURF_SPECIFIC: Cascade Behavior Rules

### When to Create a Discussion

**ALWAYS** prompt USER to create a discussion when:

1. USER proposes a **new feature** or **enhancement**
2. Conversation involves **architectural decisions**
3. Work may require an **ADR** or **SPEC**
4. Scope is **unclear** and needs exploration

**NEVER** create a discussion for:

1. Bug fixes with clear scope
2. Simple refactoring tasks
3. Documentation updates
4. Direct implementation requests with clear requirements

### How to Create a Discussion

1. **Check INDEX.md** for highest DISC-XXX number
2. **Claim next number** (e.g., DISC-003)
3. **Copy template**: `.templates/DISC_TEMPLATE.md`
4. **Fill in metadata**: Title, date, session ID
5. **Update INDEX.md** with new discussion

```markdown
Example prompt to USER:
"This looks like it needs architectural exploration. Should I create a discussion 
file (DISC-XXX) to capture our requirements and options before proceeding?"
```

### During a Discussion

1. **Update the discussion file** as conversation progresses
2. **Log key insights** in the Conversation Log section
3. **Track open questions** in the Open Questions table
4. **Mark decisions** when USER confirms choices

### Completing a Discussion

When discussion is ready to transition:

1. **Create resulting artifacts** (ADR, SPEC, Plan as needed)
2. **Link artifacts** in the Resulting Artifacts table
3. **Change status** to `resolved`
4. **Update INDEX.md** to move from Active to Resolved
5. **Write resolution summary**

---

## WINDSURF_SPECIFIC: Option A - Milestone-Based Closure

### Discussion Closure Criteria

**A Discussion is RESOLVED when DESIGN is complete, NOT when implementation is done.**

| Artifact | Closes When |
|----------|-------------|
| **Discussion** | Architectural questions answered, artifacts created |
| **Plan** | Acceptance criteria met (MVP or full) |
| **Bugs** | Documented in Plan's `known_bugs[]`, don't block closure |

### Resolution Types

| Type | When to Use |
|------|-------------|
| `design_complete` | All design decisions made, ADR/SPEC/Plan created |
| `deferred` | Parked for later, context preserved |
| `abandoned` | No longer relevant, document why |

### Example Resolution

```markdown
## Resolution

**Resolution Date**: 2025-12-30
**Resolution Type**: design_complete
**Outcome**: UI & workflow design complete

**Artifacts Created**:
- ADR-0045: UI Architecture
- SPEC-0034: Workflow Manager
- PLAN-001: Implementation

**Known Bugs**: Tracked in PLAN-001 (don't block DISC closure)
```

---

## WINDSURF_SPECIFIC: Gate Rules

### Gate: Discussion → ADR

Before creating an ADR from a discussion:

- [ ] USER has explicitly approved architectural decision is needed
- [ ] Options have been documented in discussion
- [ ] Recommendation has been stated
- [ ] USER has selected an option

### Gate: Discussion → SPEC

Before creating a SPEC from a discussion:

- [ ] Requirements are clear and agreed
- [ ] Scope is defined (in scope / out of scope)
- [ ] No blocking open questions remain

### Gate: Discussion → Plan

Before creating a Plan from a discussion:

- [ ] Implementation approach is clear
- [ ] Work can be broken into milestones
- [ ] Acceptance criteria can be defined

---

## WINDSURF_SPECIFIC: File Operations

### Reading Discussions

At session start, if continuing previous work:

```
1. Read .discussions/INDEX.md
2. Check for active discussions related to current work
3. Read active discussion file if exists
4. Reference discussion context in your responses
```

### Updating Discussions

When conversation reveals new information:

```
1. Update relevant section of discussion file
2. Add entry to Conversation Log with session ID
3. Update Open Questions table if new questions arise
4. Update Decision Points table if decisions made
```

### Indexing

After any discussion file change:

```
1. Ensure INDEX.md reflects current state
2. Update statistics at bottom of INDEX.md
3. Move discussions between sections as status changes
```

---

## Schema Reference

See `.templates/DISC_TEMPLATE.md` for complete schema.

Key sections:

| Section | Purpose | Update Frequency |
|---------|---------|------------------|
| Summary | One-paragraph overview | Once at creation |
| Requirements | Functional and non-functional | During discussion |
| Open Questions | Questions needing answers | Continuously |
| Options Considered | For architectural decisions | When options identified |
| Decision Points | Key decisions to make | When decisions needed |
| Resulting Artifacts | Links to created artifacts | At resolution |
| Conversation Log | Session-by-session notes | Every session |

---

## Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Jumping to code without discussion | Create discussion first for complex work |
| Leaving discussions orphaned | Resolve or abandon with clear status |
| Not linking resulting artifacts | Always update Resulting Artifacts table |
| Skipping conversation log | Log key points every session |

---

## WINDSURF_SPECIFIC: Multi-DISC Dependencies

### Dependency Types

| Type | Notation | Meaning |
|------|----------|---------|
| **Finish-to-Start (FS)** | DISC-B depends on DISC-A | B can't start until A complete |
| **Finish-to-Finish (FF)** | DISC-C aggregates A,B | C can't finish until A,B finish |
| **Start-to-Start (SS)** | DISC-A,B parallel | A,B can start together |
| **Soft Dependency** | DISC-B soft-depends A | B can use stub until A complete |

### When Creating Discussions with Dependencies

1. **Check DISC-DEPENDENCY-GRAPH.md** for existing dependency chains
2. **Add `Depends On:` field** in discussion metadata
3. **Update dependency graph** when adding new dependencies
4. **Identify dependency type** (FS, FF, SS, soft)

### Aggregator Discussions

When a DISC depends on multiple other DISCs (like DISC-006):

1. **List all dependencies** in Cross-DISC Dependencies section
2. **Map phases to dependencies**: Which phase needs which DISC?
3. **Identify stubbable dependencies**: Can we proceed with a stub?
4. **Plan for integration**: Last phase should integrate all dependencies

### Stub Pattern for Soft Dependencies

When a dependency isn't complete but work can proceed:

```python
# Example: DISC-004-STUB
def sanitize_pii(content: str) -> str:
    """Stub: Pass-through until DISC-004 complete."""
    # TODO(DISC-004): Replace with real implementation
    return content
```

### Multi-DISC Plan Strategy

| Approach | When to Use |
|----------|-------------|
| **Hierarchical Phased Plan** | One DISC aggregates multiple dependencies |
| **Parallel Independent Plans** | DISCs at same level, no cross-deps |
| **Sequential Plans** | Strict finish-to-start dependency |

### Recommended Execution Order

Always use **topological sort** based on dependency levels:

1. **Level 0**: No dependencies (start first)
2. **Level 1**: Depends only on Level 0
3. **Level N**: Depends on Level N-1

See `DISC-DEPENDENCY-GRAPH.md` for current project state.

---

<!-- WINDSURF_SPECIFIC: End of Windsurf-specific instructions -->
