# Experiment EXP-001: L1 vs L3 Plan Granularity + Model Cost Comparison

## Objective

Compare the effectiveness of L1 (Standard) vs L3 (Procedural) plan granularity across 8 different AI models to determine optimal cost/quality tradeoff.

## Hypothesis

L3 plans with detailed step-by-step instructions will enable cheaper models to achieve comparable results to expensive models using L1 plans, potentially at a fraction of the cost.

## Experimental Design

### Variables

- **Independent Variables**: 
  - Plan granularity level (L1 vs L3)
  - AI Model (8 different models)
- **Controlled Variables**: 
  - Same milestone (M1: Backend API Foundation)
  - Same codebase baseline
  - Same evaluation criteria
- **Dependent Variables**: 
  - Scores on DoD criteria (0-100)
  - Cost multiplier
  - Quality per unit cost

### Model Matrix

#### L1 Models (Expensive, Less Detail)

| Model | Cost | Branch |
|-------|------|--------|
| Claude Opus 4.5 Thinking | 5x | `experiment/l1-opus` |
| Claude Sonnet 4.5 Thinking | 3x | `experiment/l1-sonnet` |
| GPT-5.2 High Reasoning Fast | 6x | `experiment/l1-gpt52` |
| Gemini 3 Pro High | 3x | `experiment/l1-gemini3pro` |

#### L3 Models (Cheap, Full Detail)

| Model | Cost | Branch |
|-------|------|--------|
| Grok Code Fast 1 | FREE (0x) | `experiment/l3-grok` |
| Claude Haiku | 1x | `experiment/l3-haiku` |
| Gemini Flash 3 High | 1x | `experiment/l3-gemini-flash` |
| GPT-5.1-Codex Max High | 1x | `experiment/l3-gpt51` |

### Key Metric: Quality Per Unit Cost

```
Score Efficiency = DoD Score / Cost Multiplier
```

Example:
- L1 + Opus (5x): Score 95 → Efficiency = 19
- L3 + Haiku (1x): Score 85 → Efficiency = 85

**Winner = Highest Score Efficiency**

## Execution Protocol

1. Create baseline branch with experiment files
2. Create 8 experiment branches from baseline
3. Open 8 Windsurf tabs (or run sequentially)
4. Each tab: checkout branch, execute plan, record results
5. Collect all 8 scorecards
6. Generate cost/quality analysis

## Files

### Plan Files
- `.plans/PLAN-001_DevTools-Workflow-Manager.json` - L1 plan (existing)
- `PLAN-001-M1-L3.json` - L3 version with procedural steps

### Instructions (per model)
- `instructions/L1_OPUS.md`
- `instructions/L1_SONNET.md`
- `instructions/L1_GPT52.md`
- `instructions/L1_GEMINI3PRO.md`
- `instructions/L3_GROK.md`
- `instructions/L3_HAIKU.md`
- `instructions/L3_GEMINI_FLASH.md`
- `instructions/L3_GPT51.md`

### Results
- `results/RESULTS_L1_OPUS.json`
- `results/RESULTS_L1_SONNET.json`
- `results/RESULTS_L1_GPT52.json`
- `results/RESULTS_L1_GEMINI3PRO.json`
- `results/RESULTS_L3_GROK.json`
- `results/RESULTS_L3_HAIKU.json`
- `results/RESULTS_L3_GEMINI_FLASH.json`
- `results/RESULTS_L3_GPT51.json`

### Analysis
- `SCORECARD_TEMPLATE.json` - Base template
- `COST_ANALYSIS.md` - Final cost/quality comparison
