# DISC-008: Open Questions Workflow UX

> **Status**: `active`
> **Created**: 2025-12-31
> **Updated**: 2025-12-31
> **Author**: USER + Cascade
> **AI Session**: SESSION_023
> **Depends On**: DISC-001
> **Blocks**: None
> **Dependency Level**: L1

---

## Summary

Design and implement a comprehensive UX/UI workflow for managing Open Questions across all artifact types (DISC, SPEC, Contract, ADR). This includes validation gates, wizard-based question resolution, and integration with the AI Prompt Copy feature.

---

## Context

### Background

The current workflow artifacts (DISC, SPEC, ADR, etc.) contain Open Questions tables that track unresolved design decisions. However, there is no UX/UI enforcement or guidance to ensure users resolve these questions before proceeding to downstream artifacts (e.g., DISC → ADR → Plan).

### Trigger

During DISC-007 creation, it became apparent that:

1. Users may not realize open questions need answers before ADR creation
2. No validation exists to warn users about unanswered questions
3. No wizard or guided workflow exists to help users work through questions
4. The "AI Prompt Copy" feature should validate question status before generating prompts

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: Display warning when user attempts "AI Prompt Copy" with unanswered open questions
- [ ] **FR-2**: Show open questions count/status badge on artifact cards in DevTools UI
- [ ] **FR-3**: Provide quick wizard to guide users through answering open questions
- [ ] **FR-4**: Block or warn on ADR creation from DISC with unanswered questions
- [ ] **FR-5**: Apply open questions workflow to all artifact types (DISC, SPEC, Contract, ADR)
- [ ] **FR-6**: Allow users to mark questions as "deferred" with reason (not blocking)
- [ ] **FR-7**: Track question resolution history (who answered, when, original vs revised)

### Non-Functional Requirements

- [ ] **NFR-1**: Wizard should be non-intrusive - optional, not forced
- [ ] **NFR-2**: Warning dialogs should be dismissible (user can proceed with risk)
- [ ] **NFR-3**: Question status should persist across sessions
- [ ] **NFR-4**: Integration with existing DevTools Workflow Manager (DISC-001/PLAN-001)

---

## Constraints

- **C-1**: Must integrate with existing artifact schema (Open Questions table format)
- **C-2**: Must not break existing markdown-based workflow (files remain human-editable)
- **C-3**: Must work with current DevTools frontend architecture (React + TypeScript)

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | Should unanswered questions hard-block ADR creation or just warn? | `open` | - |
| Q-2 | What triggers the question wizard - button click, automatic on artifact open, or both? | `open` | - |
| Q-3 | Should the wizard support AI-assisted question answering (suggest answers)? | `open` | - |
| Q-4 | How should "deferred" questions be visually distinguished from "open"? | `open` | - |
| Q-5 | Should question resolution require approval for multi-user scenarios (future)? | `open` | - |
| Q-6 | What constitutes "properly answered"? Just table update, or full document integration? | `open` | - |

---

## Key Insight: Question Closure Gap (2025-12-31)

**Problem Identified**: During DISC-007 question resolution, we discovered that marking a question `answered` in the table is insufficient. The answer was recorded, but:

1. The answer wasn't integrated into relevant document sections (Scope, Requirements, etc.)
2. No validation exists to ensure answers are propagated
3. The document wasn't truly "ready for ADR" despite all questions being marked answered

**Proposed Solution - Question Closure Checklist**:

When marking a question `answered`, the following must occur:

| Step | Action | Verification |
|------|--------|--------------|
| 1 | Update `Status` to `answered` | Table check |
| 2 | Record answer in `Answer` column | Table check |
| 3 | Update **Scope Definition** if answer affects scope | Section review |
| 4 | Update **Decision Points** if answer is a decision | Table check |
| 5 | Update **Constraints** if answer adds constraints | Section review |
| 6 | Update **Conversation Log** with rationale | Section review |
| 7 | Cross-reference answer in related sections | grep check |

**Validation Gate for ADR Creation**:

```text
Can create ADR if:
  ✅ All questions status = `answered` OR `deferred`
  ✅ All answers integrated into relevant sections
  ✅ Decision Points table fully populated
  ✅ Scope Definition reflects all decisions
```

This insight should inform FR-3 (wizard) and FR-4 (ADR creation gate).

---

## Options Considered

### Option A: Validation-First (Warning Dialogs)

**Description**: Add validation checkpoints that show warning dialogs when users attempt actions with unresolved questions.

**Pros**:

- Minimal UI changes
- Non-intrusive - users can dismiss and proceed
- Easy to implement

**Cons**:

- Passive - doesn't help users answer questions
- Users may habitually dismiss warnings

### Option B: Wizard-First (Guided Resolution)

**Description**: Provide a dedicated wizard that walks users through each open question with context and input fields.

**Pros**:

- Active guidance helps users resolve questions
- Better UX for complex decisions
- Can include AI suggestions

**Cons**:

- More complex implementation
- May feel heavyweight for simple questions

### Option C: Hybrid (Recommended)

**Description**: Combine validation warnings with an optional wizard. Warnings offer a "Resolve Now" button that launches the wizard.

**Pros**:

- Best of both approaches
- Users choose their preferred workflow
- Progressive complexity

**Cons**:

- Most implementation effort

### Recommendation

**Option C: Hybrid** - Provides flexibility while ensuring users are informed about unresolved questions.

---

## Proposed UX Flows

### Flow 1: AI Prompt Copy with Open Questions

```text
User clicks "AI Prompt Copy" on DISC-007
    │
    ▼
System detects 4 unanswered questions
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  ⚠️ Open Questions Detected                         │
│                                                     │
│  This discussion has 4 unanswered questions.        │
│  Resolving them before creating an ADR is           │
│  recommended for better AI prompt quality.          │
│                                                     │
│  [ View Questions ]  [ Resolve Now ]  [ Copy Anyway ]│
└─────────────────────────────────────────────────────┘
```

### Flow 2: Question Resolution Wizard

```text
┌─────────────────────────────────────────────────────┐
│  Open Questions Wizard (1 of 4)                     │
│                                                     │
│  Q-1: Should wrapper auto-select between LangChain  │
│       and native SDK based on requested features?   │
│                                                     │
│  Context:                                           │
│  • LangChain handles: RAG, client-side tools        │
│  • Native SDK handles: agentic server-side tools    │
│                                                     │
│  Your Answer:                                       │
│  ┌─────────────────────────────────────────────┐   │
│  │                                             │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  [ 🤖 Suggest Answer ]  [ Defer ]  [ Save & Next ] │
└─────────────────────────────────────────────────────┘
```

### Flow 3: Artifact Card with Question Badge

```text
┌─────────────────────────────────────────────────────┐
│  📋 DISC-007                           🟡 4 Open    │
│  Unified xAI Agent Wrapper                          │
│                                                     │
│  Status: active                                     │
│  Level: L2                                          │
│                                                     │
│  [ Open ]  [ AI Prompt ]  [ → ADR ]                │
└─────────────────────────────────────────────────────┘
```

---

## Integration Points

| Component | Integration |
|-----------|-------------|
| DevTools Workflow Manager | Add question validation to artifact transitions |
| AI Prompt Copy | Pre-flight validation for open questions |
| Artifact Reader Panel | Display question status badge |
| Artifact Editor Panel | Question wizard integration |
| Backend API | Endpoint for question status queries |

---

## Decision Points

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | Overall approach | `pending` | - |
| D-2 | Warning behavior (block vs warn) | `pending` | - |
| D-3 | AI suggestion integration | `pending` | - |
| D-4 | Artifact types to support | `pending` | - |

---

## Scope Definition

### In Scope

- Warning dialogs for AI Prompt Copy
- Question resolution wizard
- Status badges on artifact cards
- Integration with DevTools Workflow Manager
- Support for DISC, SPEC, ADR, Contract artifacts

### Out of Scope

- Multi-user approval workflows (future enhancement)
- Question templates/suggestions library
- Analytics on question resolution time
- Mobile UI optimization

---

## Cross-DISC Dependencies

| Dependency | Type | Status | Blocker For | Notes |
|------------|------|--------|-------------|-------|
| DISC-001 | `FS` | `resolved` | UI integration | DevTools Workflow Manager complete |

### Stub Strategy (if applicable)

N/A - DISC-001 is resolved.

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status |
|---------------|-----|-------|--------|
| ADR | ADR-{TBD} | Open Questions Workflow Architecture | `pending` |
| SPEC | SPEC-{TBD} | Question Wizard Specification | `pending` |
| Plan | PLAN-{TBD} | Open Questions UX Implementation | `pending` |

---

## Conversation Log

### 2025-12-31 - SESSION_023

**Topics Discussed**:

- Need for open questions validation before ADR creation
- Wizard workflow for guided question resolution
- Integration with AI Prompt Copy feature
- Cross-artifact type support (DISC, SPEC, Contract, ADR)

**Key Insights**:

1. Users may not realize open questions block downstream artifact quality
2. "AI Prompt Copy" is a natural validation checkpoint
3. Wizard should be optional, not forced
4. "Deferred" status allows non-blocking postponement
5. Question badges provide at-a-glance status on artifact cards

**Use Cases Identified**:

- **UC-1**: User clicks "AI Prompt Copy" with open questions → warning + options
- **UC-2**: User opens artifact with open questions → badge visible
- **UC-3**: User wants guided help → launches wizard
- **UC-4**: User wants to postpone decision → marks as "deferred"
- **UC-5**: User creates ADR from DISC → validation checkpoint

**Action Items**:

- [ ] Answer open questions (Q-1 through Q-6)
- [ ] Create ADR for architecture decision
- [ ] Create SPEC for wizard behavior
- [ ] Create Plan for implementation

### 2025-12-31 - SESSION_023 (continued)

**Topics Discussed**:

- Discovered "Question Closure Gap" during DISC-007 resolution
- Defined proper closure checklist (7 steps)
- Applied closure checklist to DISC-007 as validation

**Key Insights**:

1. Marking a question `answered` in the table is **necessary but not sufficient**
2. Answers must propagate to: Requirements, Constraints, Scope, Class Design, Response Models
3. This gap is exactly what DISC-008 should address in the UX
4. The wizard should enforce/guide this propagation

**Pattern Identified - Question Answer Propagation**:

| Question Type | Propagation Target |
|---------------|-------------------|
| Scope-affecting | Scope Definition, Requirements |
| Technical approach | Constraints, Class Design |
| Architecture | Decision Points, Proposed Architecture |
| Data model | Response Models, Contracts |

**DISC-007 Closure Validation**:

Applied checklist to DISC-007 Q-1 through Q-4:

| Step | Q-1 | Q-2 | Q-3 | Q-4 |
|------|-----|-----|-----|-----|
| Table status | ✅ | ✅ | ✅ | ✅ |
| Answer column | ✅ | ✅ | ✅ | ✅ |
| Scope updated | ✅ | ✅ | ✅ | ✅ |
| Decision Points | - | ✅ | ✅ | - |
| Constraints | - | ✅ | - | ✅ |
| Requirements | ✅ | - | ✅ | ✅ |
| Class Design | - | - | ✅ | ✅ |
| Response Models | - | - | - | ✅ |

This checklist should become FR-3's wizard behavior.

---

## Resolution

<!-- Filled when discussion is resolved -->

**Resolution Date**: {TBD}

**Outcome**: {TBD}

**Next Steps**:
1. {TBD}
2. {TBD}

---

*Template version: 1.0.0 | See `.discussions/README.md` for usage instructions*
