# PLAN-001: DevTools Workflow Manager - L3 Execution Guide

> **For AI Assistants**: This file contains prompts and instructions for executing L3 chunked plans.
> Copy the appropriate milestone section below into your AI chat to begin execution.

---

## Quick Start

1. Read `INDEX.json` to find `current_chunk`
2. Copy the prompt for that milestone below
3. Paste into your AI assistant
4. Follow the L3 execution protocol

---

## Pre-Execution Checklist

Before starting any milestone:

- [ ] Read `INDEX.json` completely
- [ ] Check `current_chunk` field
- [ ] Review `continuation_context` for files already created
- [ ] Create session file: `.sessions/SESSION_XXX_PLAN-001_<chunk>_<summary>.md`
- [ ] Run baseline tests: `pytest tests/ -v --tb=no -q`

---

## Milestone M1: Backend API Foundation

**Status**: ✅ Completed

```
PLAN-001 L3 EXECUTION: Milestone M1 - Backend API Foundation

You are executing Milestone M1 using L3 (Procedural) granularity.

Plan location: .plans/L3/PLAN-001/PLAN-001_L3_M1.json

Your task: Execute all 6 tasks by following the `steps` array in each task:
- T-M1-01: Create workflow.py contracts
- T-M1-02: Create workflow_service.py
- T-M1-03: Add artifacts list endpoint
- T-M1-04: Add graph endpoint
- T-M1-05: Add CRUD endpoints
- T-M1-06: Write unit tests

Rules:
1. Follow EACH step in the `steps` array sequentially
2. Use the `code_snippet` provided - copy it EXACTLY
3. Stop at steps marked `checkpoint: true` to verify
4. Run the task's `verification_command` after all steps
5. Create .questions/ file and STOP if any step fails

Session file: .sessions/SESSION_XXX_PLAN-001_M1_Backend-Foundation.md

Acceptance Criteria (run after all tasks):
- python -c "from shared.contracts.devtools.workflow import ArtifactType, GraphNode"
- python -c "from gateway.services.workflow_service import scan_artifacts; print(len(scan_artifacts()))"
- pytest tests/gateway/test_devtools_workflow.py -v

Begin with T-M1-01, step 1
```

---

## Milestone M2: Sidebar Component

**Status**: 📝 Ready

```
PLAN-001 L3 EXECUTION: Milestone M2 - Sidebar Component

You are executing Milestone M2 using L3 (Procedural) granularity.

Plan location: .plans/L3/PLAN-001/PLAN-001_L3_M2.json

Continuation context from M1:
- Files created: workflow.py, workflow_service.py, test_devtools_workflow.py
- Patterns: Functional style, 5-value enums, import from shared.contracts.devtools.workflow

Your task: Execute all 6 tasks by following the `steps` array:
- T-M2-01: Create components/workflow/ directory structure
- T-M2-02: Implement WorkflowSidebar.tsx
- T-M2-03: Create types.ts
- T-M2-04: Implement SidebarTabs.tsx
- T-M2-05: Implement ArtifactList.tsx
- T-M2-06: Update index.ts exports

Rules:
1. Follow EACH step sequentially
2. Use code_snippet EXACTLY as provided
3. Stop at checkpoint: true steps to verify
4. Run verification_command after each task
5. Create .questions/ file and STOP on failure

Session file: .sessions/SESSION_XXX_PLAN-001_M2_Sidebar-Component.md

Acceptance Criteria:
- ls apps/homepage/frontend/src/components/workflow/
- grep 'WorkflowSidebar' apps/homepage/frontend/src/components/workflow/index.ts

Begin with T-M2-01, step 1
```

---

## Milestone M3: Graph Visualization

**Status**: 📝 Ready

```
PLAN-001 L3 EXECUTION: Milestone M3 - Graph Visualization

Plan location: .plans/L3/PLAN-001/PLAN-001_L3_M3.json

Your task: Execute all 4 tasks:
- T-M3-01: Install graph dependencies
- T-M3-02: Create ArtifactGraph.tsx
- T-M3-03: Create GraphToolbar.tsx
- T-M3-04: Update index.ts exports

Session file: .sessions/SESSION_XXX_PLAN-001_M3_Graph-Visualization.md

Key patterns:
- TYPE_COLORS for artifact tier coloring
- ForceGraph2D for 2D graph rendering
- API: GET /api/devtools/artifacts/graph

Begin with T-M3-01, step 1
```

---

## Milestone M4: Artifact Reader Panels

**Status**: 📝 Ready

```
PLAN-001 L3 EXECUTION: Milestone M4 - Artifact Reader Panels

Plan location: .plans/L3/PLAN-001/PLAN-001_L3_M4.json

Your task: Execute all 5 tasks:
- T-M4-01: Install markdown/syntax highlighting deps
- T-M4-02: Create ArtifactReader.tsx
- T-M4-03: Create JsonRenderer.tsx
- T-M4-04: Create MarkdownRenderer.tsx
- T-M4-05: Create CodeRenderer.tsx

Session file: .sessions/SESSION_XXX_PLAN-001_M4_Reader-Panels.md

Key patterns:
- Type-based rendering (ADR/SPEC → JSON, Discussion/Plan → Markdown, Contract → Python)
- Collapsible JSON sections
- Syntax highlighting with react-syntax-highlighter

Begin with T-M4-01, step 1
```

---

## Milestone M5: Artifact Editor Panels

**Status**: 📝 Ready

```
PLAN-001 L3 EXECUTION: Milestone M5 - Artifact Editor Panels

Plan location: .plans/L3/PLAN-001/PLAN-001_L3_M5.json

Your task: Execute all 3 tasks:
- T-M5-01: Install Monaco editor
- T-M5-02: Create ArtifactEditor.tsx (slide-in panel)
- T-M5-03: Create EditorForm.tsx (structured editing)

Session file: .sessions/SESSION_XXX_PLAN-001_M5_Editor-Panels.md

Key patterns:
- Slide-in animation (translate-x, 200ms transition)
- Keyboard shortcuts: Ctrl+S saves, Escape closes
- Dirty state confirmation before close
- Monaco for unstructured, EditorForm for ADR/SPEC

Begin with T-M5-01, step 1
```

---

## Milestone M6: Header & Command Palette

**Status**: 📝 Ready

```
PLAN-001 L3 EXECUTION: Milestone M6 - Header & Command Palette

Plan location: .plans/L3/PLAN-001/PLAN-001_L3_M6.json

Your task: Execute all 3 tasks:
- T-M6-01: Create WorkflowHeader.tsx
- T-M6-02: Create NewWorkflowDropdown.tsx
- T-M6-03: Create CommandPalette.tsx

Session file: .sessions/SESSION_XXX_PLAN-001_M6_Command-Palette.md

Key patterns:
- Cmd+K opens command palette
- Arrow keys navigate, Enter selects
- Fuzzy search on artifact ID and title
- Recent items prioritized

Begin with T-M6-01, step 1
```

---

## Milestone M7: Activity Feed & Empty States

**Status**: 📝 Ready

```
PLAN-001 L3 EXECUTION: Milestone M7 - Activity Feed & Empty States

Plan location: .plans/L3/PLAN-001/PLAN-001_L3_M7.json

Your task: Execute all 2 tasks:
- T-M7-01: Create ActivityFeed.tsx
- T-M7-02: Create EmptyState.tsx

Session file: .sessions/SESSION_XXX_PLAN-001_M7_Activity-Feed.md

Key patterns:
- Recent activity sorted by updated_date
- Empty states with helpful CTAs per artifact type
- Tier-specific icons and colors

Begin with T-M7-01, step 1
```

---

## Milestone M8: Workflow Stepper

**Status**: 📝 Ready

```
PLAN-001 L3 EXECUTION: Milestone M8 - Workflow Stepper

Plan location: .plans/L3/PLAN-001/PLAN-001_L3_M8.json

Your task: Execute all 2 tasks:
- T-M8-01: Create WorkflowStepper.tsx
- T-M8-02: Create useWorkflowState.ts hook

Session file: .sessions/SESSION_XXX_PLAN-001_M8_Workflow-Stepper.md

Key patterns:
- 6 stages: Discussion → ADR → SPEC → Contract → Plan → Fragment
- sessionStorage persistence for workflow state
- Stage progression with artifact ID tracking

Begin with T-M8-01, step 1
```

---

## Milestone M9: Integration & Polish

**Status**: 📝 Ready

```
PLAN-001 L3 EXECUTION: Milestone M9 - Integration & Polish

Plan location: .plans/L3/PLAN-001/PLAN-001_L3_M9.json

Your task: Execute all 4 tasks:
- T-M9-01: Create WorkflowManagerPage.tsx
- T-M9-02: Update App.tsx with route
- T-M9-03: Update workflow index.ts exports
- T-M9-04: Verify view toggle works

Session file: .sessions/SESSION_XXX_PLAN-001_M9_Integration.md

Key patterns:
- Global Cmd+K listener
- List/Graph view toggle
- All components composed in WorkflowManagerPage

Final verification:
- cd apps/homepage/frontend && npm run build
- cd apps/homepage/frontend && npm run typecheck

Begin with T-M9-01, step 1
```

---

## Post-Execution Checklist

After completing a milestone:

- [ ] All tasks marked complete with evidence
- [ ] Acceptance criteria verified
- [ ] Session file updated with handoff notes
- [ ] INDEX.json updated:
  - `current_chunk` → next milestone
  - `last_completed_task` → last task ID
  - `continuation_context.files_created` updated
  - `chunks[completed].status` → "completed"
- [ ] Commit changes: `git add -A && git commit -m "PLAN-001 M<N>: <summary>"`

---

## Troubleshooting

### Step fails verification

```
1. Do NOT proceed to next step
2. Create .questions/IMPL_PLAN-001_M<N>_<issue>.md
3. Document: task, step, error, what you tried
4. STOP and wait for user guidance
```

### Code snippet doesn't apply cleanly

```
1. Check if file already exists with different content
2. Check continuation_context for previous modifications
3. If conflict, document in .questions/ and STOP
```

### Baseline tests fail

```
1. Document which tests fail in session file
2. If failures are UNRELATED to current milestone → proceed
3. If failures are RELATED → create .questions/ and STOP
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python scripts/workflow/verify_plan.py .plans/PLAN-001.json` | Validate plan |
| `pytest tests/gateway/test_devtools_workflow.py -v` | Run M1 tests |
| `cd apps/homepage/frontend && npm run build` | Build frontend |
| `cd apps/homepage/frontend && npm run typecheck` | Check types |

---

*This EXECUTION.md is a standard L3 artifact per ADR-0043.*
