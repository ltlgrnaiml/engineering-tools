# DISC-009: Orphan ADRs and Policy Document Strategy

> **Status**: `active`
> **Created**: 2025-12-31
> **Updated**: 2025-12-31
> **Author**: Cascade AI
> **AI Session**: SESSION_024
> **Depends On**: None
> **Blocks**: None
> **Dependency Level**: L0

---

## Summary

This discussion addresses two interconnected issues discovered during the comprehensive ADR↔SPEC semantic audit (SESSION_024):

1. **Orphan ADRs**: 8 ADRs have no implementing SPECs, violating the 3-tier document model (ADR-0016)
2. **Policy Documents**: Some ADRs describe organizational policies rather than architectural decisions, suggesting a need for a distinct "Policy" document type with its own schema

---

## Context

### Background

Per **ADR-0016** (3-Tier Document Model), the documentation hierarchy is:
- **Tier 0**: Contracts (Pydantic models) - SSOT for data shapes
- **Tier 1**: ADRs - WHY decisions were made
- **Tier 2**: SPECs - WHAT to build
- **Tier 3**: Guides - HOW to do it

The semantic audit revealed that 8 ADRs have no implementing SPECs. Upon review, some of these appear to be **policy documents** (coding standards, development practices) rather than **architectural decisions** that require implementation SPECs.

### Trigger

Running `scripts/semantic_adr_spec_audit.py` identified these orphan ADRs:

| ADR ID | Title | Suspected Category |
|--------|-------|-------------------|
| `ADR-0031` | Documentation Lifecycle Management | Policy |
| `ADR-0034` | AI-Assisted Development Patterns | Policy |
| `ADR-0035` | Automated Documentation Pipeline | Needs SPEC |
| `ADR-0036` | Contract-Driven Test Generation | Needs SPEC |
| `ADR-0038` | Single-Command Development Environment | Needs SPEC |
| `ADR-0039` | CI/CD Pipeline for Data and Code | Needs SPEC |
| `ADR-0040` | Deployment Automation | Needs SPEC |
| `ADR-0048` | Unified xAI Agent Wrapper | Needs SPEC |

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: All orphan ADRs must be resolved - either by creating SPECs or reclassifying as Policy
- [ ] **FR-2**: Policy documents (if adopted) must have a defined schema
- [ ] **FR-3**: Policy documents must integrate with the existing documentation validation tooling
- [ ] **FR-4**: The `check_reference_drift.py` validator must be updated to handle Policy documents
- [ ] **FR-5**: Policy documents must be included in the knowledge.db RAG system

### Non-Functional Requirements

- [ ] **NFR-1**: Policy schema should be simpler than ADR schema (policies don't need decision_details, alternatives_considered, etc.)
- [ ] **NFR-2**: Documentation strategy must remain deterministic and automatable
- [ ] **NFR-3**: CI enforcement must validate policy documents like ADRs and SPECs

---

## Constraints

- **C-1**: Must maintain backward compatibility with existing ADR/SPEC tooling
- **C-2**: Cannot introduce manual documentation processes (per SOLO-DEV ETHOS: Automation First)
- **C-3**: All document types must have JSON schema for validation

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | Should policies be a separate document type or a subtype of ADR? | `open` | |
| Q-2 | Where should policy documents live? `.policies/` or `.adrs/policies/`? | `open` | |
| Q-3 | Do policies need version tracking like ADRs? | `open` | |
| Q-4 | Should policies reference ADRs that established them? | `open` | |
| Q-5 | How do we migrate existing policy-like ADRs to the new format? | `open` | |

---

## Options Considered

### Option A: Policy as ADR Subtype

**Description**: Add a `document_type: policy | decision` field to ADRSchema. Policies skip SPEC validation.

**Pros**:
- Minimal schema changes
- Reuses existing validation infrastructure
- No new directories needed

**Cons**:
- Pollutes ADR schema with policy concerns
- `decision_details` field doesn't make sense for policies
- Harder to query policies separately from decisions

### Option B: Separate Policy Document Type

**Description**: Create new `PolicySchema` in `shared/contracts/policy_schema.py` with dedicated `.policies/` directory.

**Pros**:
- Clean separation of concerns
- Schema tailored to policy needs
- Clear organizational structure
- Easier to query/filter in RAG

**Cons**:
- New schema to maintain
- New directory to manage
- Updates needed to all validators, knowledge ingestion, etc.

### Option C: Policy as SPEC Variant

**Description**: Create "Policy SPECs" that don't implement ADRs but define organizational standards.

**Pros**:
- Reuses SPEC infrastructure
- No new document type

**Cons**:
- Confuses SPEC purpose (WHAT to build vs organizational rules)
- Semantic mismatch

### Recommendation

**Option B: Separate Policy Document Type** is recommended because:
1. Policies have fundamentally different structure (rules, enforcement, scope) than decisions
2. Clean separation supports deterministic validation
3. Aligns with SOLO-DEV ETHOS first-principles approach

---

## Decision Points

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | Adopt Policy as separate document type | `pending` | |
| D-2 | Define minimum viable PolicySchema | `pending` | |
| D-3 | Determine migration strategy for policy-like ADRs | `pending` | |
| D-4 | Update tooling (validator, knowledge ingestion) | `pending` | |

---

## Scope Definition

### In Scope

- Documenting the 8 orphan ADRs and their resolution path
- Proposing Policy document type schema
- Defining where policies fit in the 3-tier (now 4-tier?) model
- Updating validators to handle policies

### Out of Scope

- Implementing all missing SPECs (separate work per ADR)
- Migrating existing ADRs to policies (follow-up work)
- Full CI/CD enforcement of policies (follow-up work)

---

## Cross-DISC Dependencies

| Dependency | Type | Status | Blocker For | Notes |
|------------|------|--------|-------------|-------|
| None | - | - | - | This is a foundational discussion |

---

## Orphan ADR Analysis

### ADRs Requiring SPECs

These ADRs describe architectural decisions that need implementing SPECs:

#### ADR-0035: Automated Documentation Pipeline

**Decision**: Auto-generate documentation from code (docstrings → API docs)
**Missing SPEC**: SPEC for mkdocs pipeline, docstring extraction, API doc generation
**Priority**: Medium

#### ADR-0036: Contract-Driven Test Generation

**Decision**: Generate tests from Pydantic contracts automatically
**Missing SPEC**: SPEC for test generation from contracts, pytest fixtures from schemas
**Priority**: Medium

#### ADR-0038: Single-Command Development Environment

**Decision**: `./start.ps1` or `./start.sh` brings up entire dev environment
**Missing SPEC**: SPEC for dev environment setup, dependencies, hot reload
**Priority**: Low (already implemented, needs documentation)

#### ADR-0039: CI/CD Pipeline for Data and Code

**Decision**: Automated quality gates, test runs, deployments
**Missing SPEC**: SPEC for CI steps, quality gates, deployment triggers
**Priority**: Medium

#### ADR-0040: Deployment Automation

**Decision**: Automated deployment to production
**Missing SPEC**: SPEC for deployment process, rollback procedures
**Priority**: Medium

#### ADR-0048: Unified xAI Agent Wrapper

**Decision**: Unified wrapper for xAI API interactions with LangChain
**Missing SPEC**: SPEC for agent interface, tool integration, response handling
**Priority**: High (active development)

### ADRs That Are Policies (Candidates for Reclassification)

These ADRs describe organizational policies/standards rather than architectural decisions:

#### ADR-0031: Documentation Lifecycle Management

**Content**: Rules for when/how documentation is updated, versioned, deprecated
**Why Policy**: Describes organizational process, not technical architecture
**Recommendation**: Migrate to `POLICY-0001_Documentation-Lifecycle.md`

#### ADR-0034: AI-Assisted Development Patterns

**Content**: Guidelines for AI-parseable code patterns, naming conventions
**Why Policy**: Describes coding standards, not system architecture
**Recommendation**: Migrate to `POLICY-0002_AI-Assisted-Development.md`

---

## Proposed Policy Schema (Draft)

```python
class PolicySchema(BaseModel):
    """Schema for organizational policy documents."""
    
    schema_type: Literal["policy"] = "policy"
    id: str  # POLICY-XXXX
    title: str
    version: str
    status: PolicyStatus  # draft, active, deprecated
    created_date: str
    updated_date: str
    
    # Policy-specific fields
    scope: str  # What this policy covers
    enforcement: str  # How this policy is enforced (CI, review, etc.)
    rules: list[PolicyRule]  # The actual policy rules
    exceptions: list[str]  # Known exceptions
    
    # References
    established_by: list[str]  # ADRs that established this policy
    related_policies: list[str]  # Other related policies
    references: list[str]  # External references
```

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status |
|---------------|----|-------|--------|
| ADR | ADR-XXXX | Policy Document Type | `pending` |
| Contract | `shared/contracts/policy_schema.py` | Policy Schema | `pending` |
| SPEC | SPEC-XXXX | Policy Validation Pipeline | `pending` |

---

## Conversation Log

### 2025-12-31 - SESSION_024

**Topics Discussed**:
- Semantic audit of ADR↔SPEC connections revealed 8 orphan ADRs
- Some orphan ADRs are actually policies, not architectural decisions
- Need strategy for handling policy documents

**Key Insights**:
- ADR format is not adequate for policy documents
- Policies need their own schema with rules, enforcement, scope
- 6 orphan ADRs need SPECs, 2 should be reclassified as policies

**Action Items**:
- [ ] Decide on Policy document type adoption (Option A, B, or C)
- [ ] Create PolicySchema if Option B selected
- [ ] Create missing SPECs for 6 ADRs requiring them
- [ ] Migrate 2 policy-like ADRs to Policy format

---

## Resolution

**Resolution Date**: (pending)

**Outcome**: (pending)

**Next Steps**:
1. USER decision on Policy document strategy
2. Create PolicySchema if approved
3. Create missing SPECs for architectural ADRs
4. Migrate policy-like ADRs

---

*Template version: 1.0.0 | See `.discussions/README.md` for usage instructions*
