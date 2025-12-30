# L1 Execution: Gemini 3 Pro High

**Branch**: `experiment/l1-gemini3pro`
**Model**: Gemini 3 Pro High
**Cost**: 3x
**Granularity**: L1 (Standard)

## Setup

```bash
git checkout experiment/l1-gemini3pro
```

## Prompt to Start

Copy and paste this to the AI:

---

**EXPERIMENT EXP-001: L1 Plan Execution (Gemini 3 Pro)**

You are executing Milestone M1 of PLAN-001 using L1 (Standard) granularity.

**Plan location**: `.plans/PLAN-001_DevTools-Workflow-Manager.json`

**Your task**: Execute all 6 tasks in M1:
- T-M1-01: Create workflow.py contracts
- T-M1-02: Create workflow_service.py
- T-M1-03: Add artifacts list endpoint
- T-M1-04: Add graph endpoint
- T-M1-05: Add CRUD endpoints
- T-M1-06: Write unit tests

**Rules**:
1. Follow the plan - use only the `context` field for guidance
2. Run each task's `verification_command` after completing
3. Mark tasks complete only after verification passes
4. Report any confusion or issues

**Start time**: Record now: `____-__-__ __:__`

Begin with T-M1-01.

---

## During Execution

Track these metrics:
- [ ] Start time: ___________
- [ ] Total AI messages: ___
- [ ] Errors encountered: ___
- [ ] Points of confusion: ___

## After Completion

1. End time: ___________
2. Run all verification commands
3. Copy results to `results/RESULTS_L1_GEMINI3PRO.json`
4. Return to analysis tab
