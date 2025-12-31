# Grading Rubrics for AI-Generated Documentation

Each document type is scored on a 25-point scale (total 100 points across all 4 documents).

---

## Discussion (DISC) Rubric - 25 Points

| Criterion | Points | 0 (Missing) | 1 (Weak) | 2 (Adequate) | 3 (Strong) |
|-----------|--------|-------------|----------|--------------|------------|
| **Problem Statement** | 3 | Not stated | Vague/generic | Clear but incomplete | Precise with context |
| **Stakeholder Identification** | 2 | None | Only developers | Multiple roles listed | Roles + their concerns |
| **Option Analysis** | 5 | No options | 1 option only | 2-3 options listed | 3+ with pros/cons |
| **Technical Depth** | 5 | Surface-level | Some technical detail | Good technical coverage | Deep architecture insight |
| **Project Awareness** | 5 | Generic/boilerplate | Mentions project name | References existing patterns | Cites specific ADRs/contracts |
| **Open Questions** | 3 | None listed | Generic questions | Relevant questions | Actionable decision points |
| **Clarity & Structure** | 2 | Disorganized | Some structure | Well-organized | Excellent flow |

**Scoring Guide:**
- **20-25**: Excellent - Ready for review, minimal edits needed
- **15-19**: Good - Usable with moderate editing
- **10-14**: Fair - Needs significant rework
- **0-9**: Poor - Better to start fresh

---

## ADR Rubric - 25 Points

| Criterion | Points | 0 (Missing) | 1 (Weak) | 2 (Adequate) | 3 (Strong) |
|-----------|--------|-------------|----------|--------------|------------|
| **Decision Statement** | 4 | No decision | Vague decision | Clear decision | Decision + rationale |
| **Context Accuracy** | 3 | Wrong context | Partial context | Accurate context | Rich context + history |
| **Alternatives Considered** | 4 | None | 1 alternative | 2-3 alternatives | 3+ with trade-offs |
| **Consequences** | 4 | Not listed | Only positive | Positive + negative | Detailed impact analysis |
| **Schema Compliance** | 3 | Wrong format | Missing fields | All required fields | Complete with metadata |
| **Architectural Fit** | 4 | Conflicts with existing | Ignores existing | Compatible | Builds on existing ADRs |
| **Actionability** | 3 | Too abstract | Somewhat actionable | Actionable | Clear next steps |

**Key ADR Fields to Check:**
- `id`, `title`, `status` (required)
- `context`, `decision`, `consequences` (required)
- `alternatives` (should have 2+)
- `references` to related ADRs

---

## SPEC Rubric - 25 Points

| Criterion | Points | 0 (Missing) | 1 (Weak) | 2 (Adequate) | 3 (Strong) |
|-----------|--------|-------------|----------|--------------|------------|
| **Requirements Coverage** | 5 | Missing requirements | Partial coverage | All requirements | Requirements + edge cases |
| **API Contract Definition** | 5 | No API defined | Incomplete endpoints | All endpoints listed | Full request/response schemas |
| **Data Model** | 4 | No data model | Incomplete schema | Complete schema | Schema + validation rules |
| **UI/UX Specification** | 3 | No UI mention | Vague description | Component list | Wireframes/behavior detail |
| **Error Handling** | 3 | Not mentioned | Generic errors | Error types listed | Error codes + messages |
| **Integration Points** | 3 | Not mentioned | Listed only | Described | Sequence/flow diagrams |
| **Testability** | 2 | No test criteria | Vague criteria | Test cases listed | Acceptance criteria |

**Key SPEC Sections to Check:**
- Functional requirements (numbered list)
- API endpoints (method, path, request, response)
- Data contracts (Pydantic-compatible)
- UI components affected
- Non-functional requirements

---

## PLAN Rubric - 25 Points

| Criterion | Points | 0 (Missing) | 1 (Weak) | 2 (Adequate) | 3 (Strong) |
|-----------|--------|-------------|----------|--------------|------------|
| **Task Granularity** | 5 | Too coarse | Mixed granularity | Consistent sizing | 1-4 hour tasks |
| **Dependency Ordering** | 4 | No order | Some ordering | Logical sequence | DAG with clear deps |
| **Completeness** | 4 | Missing major work | Missing some tasks | All work covered | Work + contingencies |
| **Verification Steps** | 4 | No verification | Some tests | Test per feature | TDD approach |
| **Milestone Definition** | 3 | No milestones | Vague milestones | Clear milestones | Milestones + criteria |
| **Effort Estimation** | 3 | No estimates | Some estimates | All estimated | Estimates + confidence |
| **Context Provision** | 2 | No context | Minimal context | Good context | Rich context per task |

**Key PLAN Elements to Check:**
- `milestones[]` with clear deliverables
- `tasks[]` with `id`, `title`, `description`
- `dependencies[]` between tasks
- `verification` commands/criteria
- `context[]` for AI execution

---

## Scoring Sheet Template

```
Model: ________________  Date: ________________

DISCUSSION                          SCORE
├─ Problem Statement      ___/3
├─ Stakeholder ID         ___/2
├─ Option Analysis        ___/5
├─ Technical Depth        ___/5
├─ Project Awareness      ___/5
├─ Open Questions         ___/3
└─ Clarity & Structure    ___/2
                    DISC: ___/25

ADR                                 SCORE
├─ Decision Statement     ___/4
├─ Context Accuracy       ___/3
├─ Alternatives           ___/4
├─ Consequences           ___/4
├─ Schema Compliance      ___/3
├─ Architectural Fit      ___/4
└─ Actionability          ___/3
                     ADR: ___/25

SPEC                                SCORE
├─ Requirements Coverage  ___/5
├─ API Contract           ___/5
├─ Data Model             ___/4
├─ UI/UX Specification    ___/3
├─ Error Handling         ___/3
├─ Integration Points     ___/3
└─ Testability            ___/2
                    SPEC: ___/25

PLAN                                SCORE
├─ Task Granularity       ___/5
├─ Dependency Ordering    ___/4
├─ Completeness           ___/4
├─ Verification Steps     ___/4
├─ Milestone Definition   ___/3
├─ Effort Estimation      ___/3
└─ Context Provision      ___/2
                    PLAN: ___/25

═══════════════════════════════════════
                   TOTAL: ___/100
═══════════════════════════════════════

Notes:
_________________________________________
_________________________________________
_________________________________________
```

---

## Quick Evaluation Checklist

For rapid assessment, use this pass/fail checklist:

### DISC Quick Check
- [ ] States the problem clearly in first paragraph
- [ ] Lists at least 2 implementation options
- [ ] Mentions existing project architecture
- [ ] Has actionable open questions

### ADR Quick Check
- [ ] Has a clear "We will..." decision statement
- [ ] Lists at least 2 alternatives considered
- [ ] Includes both positive and negative consequences
- [ ] Valid JSON matching ADR schema

### SPEC Quick Check
- [ ] All 4 requirements from prompt are addressed
- [ ] API endpoints have request/response defined
- [ ] Data schema is Pydantic-compatible
- [ ] Error scenarios are covered

### PLAN Quick Check
- [ ] Tasks are 1-4 hours each
- [ ] Dependencies form valid DAG (no cycles)
- [ ] Has contract, backend, frontend, test tasks
- [ ] Each task has verification criteria
