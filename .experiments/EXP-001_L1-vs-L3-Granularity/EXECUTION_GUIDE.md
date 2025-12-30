# EXP-001 Execution Guide (Git Worktrees + Windsurf)

## Worktree Locations

All 8 experiment worktrees are ready in `C:\Users\Mycahya\CascadeProjects\`:

| Worktree Folder | Branch | Model | Cost | Granularity |
|-----------------|--------|-------|------|-------------|
| `exp-l1-opus` | experiment/l1-opus | Claude Opus 4.5 Thinking | 5x | L1 |
| `exp-l1-sonnet` | experiment/l1-sonnet | Claude Sonnet 4.5 Thinking | 3x | L1 |
| `exp-l1-gpt52` | experiment/l1-gpt52 | GPT-5.2 High Reasoning Fast | 6x | L1 |
| `exp-l1-gemini3pro` | experiment/l1-gemini3pro | Gemini 3 Pro High | 3x | L1 |
| `exp-l3-grok` | experiment/l3-grok | Grok Code Fast 1 | FREE | L3 |
| `exp-l3-haiku` | experiment/l3-haiku | Claude Haiku | 1x | L3 |
| `exp-l3-gemini-flash` | experiment/l3-gemini-flash | Gemini Flash 3 High | 1x | L3 |
| `exp-l3-gpt51` | experiment/l3-gpt51 | GPT-5.1-Codex Max High | 1x | L3 |

---

## Step-by-Step Execution

### Step 1: Open Windsurf Windows

For each experiment, open a **new Windsurf window**:

1. **File** → **New Window** (or `Ctrl+Shift+N`)
2. **File** → **Open Folder**
3. Navigate to `C:\Users\Mycahya\CascadeProjects\`
4. Select the worktree folder (e.g., `exp-l1-opus`)
5. Click **Select Folder**

Repeat for all 8 worktrees. You'll have 8 Windsurf windows open.

### Step 2: Configure Model in Each Window

In each Windsurf window:

1. Open Cascade panel (`Ctrl+L`)
2. Click the **model selector** (top of Cascade panel)
3. Select the appropriate model for that experiment:

| Window (Folder) | Select Model |
|-----------------|--------------|
| exp-l1-opus | Claude Opus 4.5 Thinking |
| exp-l1-sonnet | Claude Sonnet 4.5 Thinking |
| exp-l1-gpt52 | GPT-5.2 High Reasoning Fast |
| exp-l1-gemini3pro | Gemini 3 Pro High |
| exp-l3-grok | Grok Code Fast 1 |
| exp-l3-haiku | Claude Haiku |
| exp-l3-gemini-flash | Gemini Flash 3 High |
| exp-l3-gpt51 | GPT-5.1-Codex Max High |

### Step 3: Start Experiments

In each window, paste the appropriate prompt from the instruction files.

**L1 Windows** - Use this prompt:

```text
EXPERIMENT EXP-001: L1 Plan Execution

You are executing Milestone M1 of PLAN-001 using L1 (Standard) granularity.

Plan location: .plans/PLAN-001_DevTools-Workflow-Manager.json

Your task: Execute all 6 tasks in M1:
- T-M1-01: Create workflow.py contracts
- T-M1-02: Create workflow_service.py
- T-M1-03: Add artifacts list endpoint
- T-M1-04: Add graph endpoint
- T-M1-05: Add CRUD endpoints
- T-M1-06: Write unit tests

Rules:
1. Follow the plan - use only the `context` field for guidance
2. Run each task's `verification_command` after completing
3. Mark tasks complete only after verification passes
4. Report any confusion or issues

WHEN ALL TASKS COMPLETE, run this to auto-save results:
python .experiments/EXP-001_L1-vs-L3-Granularity/scripts/save_results.py

The script will ask you for: start time, end time, message count, error count.
It will auto-run verifications and save results to JSON.

Begin with T-M1-01.
```

**L3 Windows** - Use this prompt:

```text
EXPERIMENT EXP-001: L3 Plan Execution

You are executing Milestone M1 using L3 (Procedural) granularity with detailed step-by-step instructions.

Plan location: .experiments/EXP-001_L1-vs-L3-Granularity/PLAN-001-M1-L3.json

Your task: Execute all 6 tasks in M1 by following the `steps` array in each task:
- T-M1-01: Create workflow.py contracts (10 steps)
- T-M1-02: Create workflow_service.py (7 steps)
- T-M1-03: Add artifacts list endpoint (3 steps)
- T-M1-04: Add graph endpoint (2 steps)
- T-M1-05: Add CRUD endpoints (7 steps)
- T-M1-06: Write unit tests (3 steps)

Rules:
1. Follow EACH step in the `steps` array sequentially
2. Use the `code_snippet` provided - copy it exactly
3. Stop at steps marked `checkpoint: true` to verify
4. Run the task's `verification_command` after all steps
5. Report if any step is unclear

WHEN ALL TASKS COMPLETE, run this to auto-save results:
python .experiments/EXP-001_L1-vs-L3-Granularity/scripts/save_results.py

The script will ask you for: start time, end time, message count, error count.
It will auto-run verifications and save results to JSON.

Begin with T-M1-01, step 1.
```

### Step 4: Monitor Progress

Use Windsurf's **Multi-Cascade Panes** feature:
- Arrange windows side-by-side
- Or use Windows Snap (`Win + Arrow Keys`)

### Step 5: Record Results

After each experiment completes:

1. Note the **end time**
2. Count **total AI messages** in Cascade history
3. Count **errors encountered**
4. Run all **verification commands**
5. Create results file in the worktree:

```
.experiments/EXP-001_L1-vs-L3-Granularity/results/RESULTS_[MODEL].json
```

---

## Quick Verification Commands

Run these in each worktree after completion:

```bash
# T-M1-01: Contracts
python -c "from shared.contracts.devtools.workflow import ArtifactType, GraphNode"

# T-M1-02: Service
grep "def scan_artifacts" gateway/services/workflow_service.py

# T-M1-03: List endpoint
grep "artifacts" gateway/routes/devtools.py

# T-M1-04: Graph endpoint
grep "artifacts/graph" gateway/routes/devtools.py

# T-M1-05: CRUD endpoints
grep -E "@router\.(post|delete)" gateway/routes/devtools.py

# T-M1-06: Tests
test -f tests/gateway/test_devtools_workflow.py && echo "EXISTS"
```

---

## Collecting Results

After all 8 experiments complete:

1. Return to **main workspace** (`engineering-tools`)
2. Merge results from each worktree
3. Fill out `COST_ANALYSIS.md`
4. Compare scores and efficiency

### Cleanup (Optional)

To remove worktrees after experiment:

```bash
cd C:\Users\Mycahya\CascadeProjects\engineering-tools
git worktree remove ../exp-l1-opus
git worktree remove ../exp-l1-sonnet
# ... etc
```

---

## Troubleshooting

**"Branch already checked out"**: Each worktree must be on a unique branch. This is already set up correctly.

**Model not available**: Some models may require paid subscription. Check Windsurf settings.

**Worktree conflicts**: If you need to reset a worktree:
```bash
cd C:\Users\Mycahya\CascadeProjects\exp-l1-opus
git reset --hard HEAD
```
