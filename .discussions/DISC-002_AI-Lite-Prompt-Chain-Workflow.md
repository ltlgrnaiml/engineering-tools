# DISC-002: AI-Lite Prompt Chain Workflow

> **Status**: `resolved`
> **Created**: 2025-12-30
> **Updated**: 2025-12-31
> **Author**: Mycahya Eggleston
> **AI Session**: SESSION_016

---

## Summary

Design and implementation of the AI-Lite workflow that enables users to start with a natural conversation with AI, capture it as a Discussion artifact, and then chain through structured prompts to generate ADR → SPEC → Contract → Plan artifacts. This is the core value proposition of the DevTools Workflow Manager.

---

## Context

### Background

The DevTools Workflow Manager supports three modes:
- **Manual**: User writes all artifacts themselves
- **AI-Lite**: User creates artifacts step-by-step with AI-generated prompts to help
- **AI-Full**: One-click generation of all artifacts

The AI-Lite mode is the most valuable because it:
1. Preserves human oversight and decision-making
2. Leverages AI to reduce boilerplate and ensure schema compliance
3. Creates a clear audit trail from discussion to implementation

### Trigger

User feedback that the most natural workflow starts with a conversation that evolves into a feature discussion, which should then be saveable as a DISC file and chainable through the artifact hierarchy.

---

## Requirements

### Functional Requirements

- [x] **FR-1**: Discussion files can be created from natural conversation
- [x] **FR-2**: Each artifact type has a "Copy AI Prompt" button that generates a context-aware prompt
- [x] **FR-3**: Prompts include source artifact content and target schema
- [x] **FR-4**: Prompts chain correctly: DISC → ADR → SPEC → Contract → Plan
- [x] **FR-5**: Contract generation is optional (only when data structures needed)
- [x] **FR-6**: Plan generation incorporates all upstream artifacts

### Non-Functional Requirements

- [x] **NFR-1**: Prompts should be under 4000 tokens to work with most LLMs (verified: all <600 tokens)
- [x] **NFR-2**: Generated artifacts validate against Pydantic schemas (DiscussionSchema, ADRSchema, etc.)
- [x] **NFR-3**: Prompt templates are versioned (`prompt_version: 2.0` in response context)

---

## Constraints

- **C-1**: Must use existing Pydantic schemas (ADRSchema, SPECSchema, PlanSchema)
- **C-2**: Discussion schema must be backward-compatible with existing markdown templates
- **C-3**: Prompts must work with any LLM (ChatGPT, Claude, Gemini, etc.)

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | Should Discussion have a JSON format alongside markdown? | `answered` | Yes - Pydantic schema for structured extraction, markdown for human readability |
| Q-2 | How to handle multi-step context (SPEC needs both DISC and ADR)? | `answered` | Prompts include references to all upstream artifacts |
| Q-3 | Should prompts include JSON schema or example? | `answered` | Include minimal schema with required fields highlighted |

---

## Design Decisions

### D-1: Discussion Schema Structure

The Discussion Pydantic schema will mirror the markdown template structure:
- Metadata (id, title, status, dates, author)
- Summary and context
- Requirements (functional, non-functional)
- Open questions with status
- Options considered (for architectural decisions)
- Decision points
- Resulting artifacts (links to created ADRs, SPECs, etc.)

### D-2: Prompt Template Architecture

Prompts are structured as:
1. **Role**: "You are helping create a {TARGET_TYPE} from a {SOURCE_TYPE}"
2. **Source Context**: Extracted content from source artifact
3. **Task Description**: What the AI should produce
4. **Target Schema**: Minimal schema definition with required fields
5. **Output Instruction**: "Output valid JSON/Python matching this schema"

### D-3: Artifact Chain Logic

| Source Type | Target Type | Context Included |
|-------------|-------------|------------------|
| Discussion | ADR | DISC summary, requirements, open questions, options |
| ADR | SPEC | ADR decision, constraints, guardrails |
| SPEC | Contract | SPEC API models, data structures |
| SPEC | Plan | SPEC + ADR + Contract references, all requirements |
| ADR | Plan | ADR + SPEC (if exists), guardrails as constraints |

---

## Scope Definition

### In Scope

- Pydantic schema for Discussion artifacts
- Prompt template generation for all artifact transitions
- Backend API endpoint for prompt generation
- Frontend integration with existing "Copy AI Prompt" button

### Out of Scope

- Automatic LLM integration (user pastes prompt manually)
- Real-time streaming of AI responses
- Automatic schema validation of AI output (future enhancement)

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status |
|---------------|----|-------|--------|
| Contract | `shared/contracts/devtools/discussion.py` | Discussion Schema | `completed` |
| Code | `gateway/services/workflow_service.py` | Prompt Templates | `completed` |
| Code | `gateway/services/devtools_service.py` | Prompt Endpoint | `completed` |
| Tests | `tests/gateway/test_devtools_workflow.py` | Prompt Tests | `completed` |

---

## Conversation Log

### 2025-12-30 - SESSION_016

**Topics Discussed**:
- User's natural workflow starting with AI conversation
- Need for structured prompt chain from DISC to PLAN
- Existing schemas (ADR, SPEC, Plan) and missing Discussion schema
- Prompt template design for each artifact transition

**Key Insights**:
- Discussion is the most valuable entry point (captures design thinking)
- Prompts need to include both source content and target schema
- Chain logic varies by artifact type (SPEC→Plan needs all upstream context)

**Action Items**:
- [x] Create DISC-002 to capture this discussion
- [x] Create Discussion Pydantic schema (`shared/contracts/devtools/discussion.py`)
- [x] Implement prompt templates in backend (`gateway/services/workflow_service.py`)
- [x] Add prompt generation endpoint (`generate_prompt()`)
- [x] Add tests (`tests/gateway/test_devtools_workflow.py`)

---

## Resolution

**Resolution Date**: 2025-12-31

**Outcome**: All requirements implemented and verified.

**Implemented**:
1. ✅ Discussion Pydantic schema with full validation
2. ✅ Rich prompt templates for all artifact transitions (DISC→ADR→SPEC→Plan/Contract)
3. ✅ `generate_prompt()` API endpoint
4. ✅ All prompts verified under 4000 tokens (~344-576 tokens)
5. ✅ Template versioning (`prompt_version: 2.0`)

**Next Steps**: 
- Integrate with DevTools UI (PLAN-001)
- Add real-time AI response streaming (future enhancement)

---

*Template version: 1.0.0 | See `.discussions/README.md` for usage instructions*
