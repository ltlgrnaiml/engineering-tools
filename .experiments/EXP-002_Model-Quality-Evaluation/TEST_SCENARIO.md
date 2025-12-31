# Model Quality Evaluation - Test Scenario

## Test Subject: Artifact Version History

**Why this is a good test case:**
- **Relevant**: Directly applicable to the DevTools Workflow Manager
- **Bounded**: Clear scope with well-defined requirements
- **Measurable**: Has concrete success criteria that can be verified
- **Complex enough**: Touches storage, API, UI, and contracts
- **Domain-specific**: Tests understanding of existing architecture

---

## The Prompt (Use this exact text)

```
Title: Artifact Version History

Description: Add version history tracking to artifacts in the DevTools Workflow Manager. 
When an artifact (Discussion, ADR, SPEC, or Plan) is saved, the system should:
1. Create a new version snapshot before overwriting
2. Store version metadata (timestamp, author hint, change summary)
3. Allow viewing previous versions
4. Support restoring a previous version as the current version

Key constraints:
- Must work with the existing file-based artifact storage
- Should not significantly increase storage requirements for small edits
- Version data should be stored alongside artifacts, not in a separate database
- Must integrate with the existing artifact API endpoints
```

---

## Expected Output Quality

### What a HIGH-QUALITY response should demonstrate:

| Aspect | High Quality Indicators |
|--------|------------------------|
| **Architecture Understanding** | References existing patterns (ADR-0010 contracts, file-based storage) |
| **Tradeoff Analysis** | Discusses storage vs. granularity, full-copy vs. diff-based |
| **Completeness** | Covers all 4 requirements (snapshot, metadata, view, restore) |
| **Integration Awareness** | Mentions existing endpoints, contracts, UI components |
| **Practicality** | Proposes realistic implementation, not over-engineered |

### What a LOW-QUALITY response looks like:

- Generic boilerplate with no project-specific details
- Missing key requirements from the prompt
- Proposing solutions that conflict with existing architecture
- Overly abstract without concrete details
- Copy-paste patterns that don't fit the use case

---

## Ground Truth Reference

For grading, compare against these expected elements:

### Discussion Should Mention:
- [ ] Storage strategy options (full copy, diff, hybrid)
- [ ] Impact on existing artifact API
- [ ] UI/UX for version browsing
- [ ] Performance considerations for large artifacts
- [ ] Migration strategy for existing artifacts

### ADR Should Decide:
- [ ] Storage format choice (e.g., `.versions/` subfolder per artifact)
- [ ] Version identifier format (timestamp-based, sequential, hash)
- [ ] Retention policy (keep all, limit count, time-based)
- [ ] API design choice (separate endpoints vs. query params)

### SPEC Should Define:
- [ ] API endpoints with request/response schemas
- [ ] Version metadata schema (VersionInfo contract)
- [ ] Storage file structure
- [ ] UI wireframe/behavior description
- [ ] Error handling scenarios

### PLAN Should Include:
- [ ] Contract definition task
- [ ] Backend implementation tasks (storage, API)
- [ ] Frontend implementation tasks (version list, diff view)
- [ ] Migration task for existing artifacts
- [ ] Testing tasks

---

## Evaluation Timeline

| Model Run | Timestamp | Model Used | Total Score | Notes |
|-----------|-----------|------------|-------------|-------|
| Run 1 | | grok-4-fast-reasoning | /100 | |
| Run 2 | | grok-4-0709 | /100 | |
| Run 3 | | grok-3 | /100 | |
| Run 4 | | grok-code-fast-1 | /100 | |

