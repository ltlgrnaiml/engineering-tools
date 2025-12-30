# L3 Execution: GPT-5.1-Codex Max High

**Branch**: `experiment/l3-gpt51`
**Model**: GPT-5.1-Codex Max High
**Cost**: 1x
**Granularity**: L3 (Procedural)

## Setup

```bash
git checkout experiment/l3-gpt51
```

## Prompt to Start

Copy and paste this to the AI:

---

**EXPERIMENT EXP-001: L3 Plan Execution (GPT-5.1)**

You are executing Milestone M1 using L3 (Procedural) granularity with detailed step-by-step instructions.

**Plan location**: `.experiments/EXP-001_L1-vs-L3-Granularity/PLAN-001-M1-L3.json`

**Your task**: Execute all 6 tasks in M1 by following the `steps` array in each task:
- T-M1-01: Create workflow.py contracts (10 steps)
- T-M1-02: Create workflow_service.py (7 steps)
- T-M1-03: Add artifacts list endpoint (3 steps)
- T-M1-04: Add graph endpoint (2 steps)
- T-M1-05: Add CRUD endpoints (7 steps)
- T-M1-06: Write unit tests (3 steps)

**Rules**:
1. Follow EACH step in the `steps` array sequentially
2. Use the `code_snippet` provided - copy it exactly
3. Stop at steps marked `checkpoint: true` to verify
4. Run the task's `verification_command` after all steps
5. Report if any step is unclear

**Start time**: Record now: `____-__-__ __:__`

Begin with T-M1-01, step 1.

---

## During Execution

Track these metrics:
- [ ] Start time: ___________
- [ ] Total AI messages: ___
- [ ] Errors encountered: ___
- [ ] Steps that needed clarification: ___

## After Completion

1. End time: ___________
2. Run all verification commands
3. Copy results to `results/RESULTS_L3_GPT51.json`
4. Return to analysis tab
