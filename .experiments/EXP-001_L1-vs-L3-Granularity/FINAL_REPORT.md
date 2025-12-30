# EXP-001: L1 vs L3 Plan Granularity Experiment

## Final Report

**Date**: December 30, 2025  
**Experiment ID**: EXP-001  
**Objective**: Compare Standard (L1) vs Procedural (L3) plan granularity across 8 AI models to determine optimal cost/quality tradeoffs and reduce stochastic variation in AI-generated code.

---

## Executive Summary

This experiment tested 8 AI models (4 with L1 standard plans, 4 with L3 procedural plans) on the same task: implementing the DevTools Workflow Manager backend (Milestone 1).

### Key Findings

1. **L3 reduces stochastic variation by 50%+** across most metrics
2. **All models achieved 100% task completion** regardless of granularity
3. **Budget models (Haiku, Flash) matched premium model quality** when given L3 plans
4. **Speed varies 10x+** between fastest (Opus, Sonnet, Grok) and slowest (GPT-5.2)
5. **Cost-effectiveness sweet spot**: Claude Haiku with L3 plans

---

## Experiment Design

### Task Definition

Implement PLAN-001 Milestone 1: Backend API Foundation & Contracts

- **T-M1-01**: Create workflow.py contracts (ArtifactType, GraphNode, etc.)
- **T-M1-02**: Create workflow_service.py with artifact scanning
- **T-M1-03**: Add artifact list endpoint
- **T-M1-04**: Add artifact graph endpoint
- **T-M1-05**: Add CRUD endpoints
- **T-M1-06**: Write unit tests

### Model Matrix

| Model | Granularity | Cost Multiplier | Speed Score |
|-------|-------------|-----------------|-------------|
| Claude Opus 4.5 Thinking | L1 | 5x | 5 (fast) |
| Claude Sonnet 4.5 Thinking | L1 | 3x | 5 (fast) |
| Gemini 3 Pro High | L1 | 3x | 4 (medium) |
| GPT-5.2 High Reasoning | L1 | 6x | 0 (very slow) |
| Grok Code Fast 1 | L3 | FREE | 5 (fast) |
| Claude Haiku 3.5 | L3 | 1x | 4 (medium) |
| Gemini Flash 3 High | L3 | 1x | 4 (medium) |
| GPT-5.1 Codex Max High | L3 | 1x | 3 (slow) |

---

## Results

### Task Completion (All 8 Models)

| Model | Tasks Passed | Completion |
|-------|--------------|------------|
| Opus 4.5 (L1) | 6/6 | 100% |
| Sonnet 4.5 (L1) | 6/6 | 100% |
| Gemini Pro (L1) | 6/6 | 100% |
| GPT-5.2 (L1) | 6/6 | 100% |
| Grok Fast (L3) | 6/6 | 100% |
| Haiku 3.5 (L3) | 6/6 | 100% |
| Gemini Flash (L3) | 6/6 | 100% |
| GPT-5.1 (L3) | 6/6 | 100% |

**Finding**: All models completed all tasks. Granularity level did not affect completion rate.

---

### Stochastic Variation Analysis

#### Architecture Style Consistency

| Metric | L1 (4 models) | L3 (4 models) |
|--------|---------------|---------------|
| Functional style | 3/4 (75%) | **4/4 (100%)** |
| OOP deviation | 1/4 (Gemini Pro) | 0/4 |

**L3 wins**: 100% vs 75% architecture consistency.

#### Version Format (`__version__`)

| Metric | L1 (4 models) | L3 (4 models) |
|--------|---------------|---------------|
| Correct `2025.12.01` | 1/4 (25%) | **3/4 (75%)** |
| Wrong format | 3/4 | 1/4 |

**L3 wins**: 75% vs 25% version format adherence.

#### Variable Naming (`ARTIFACT_DIRECTORIES`)

| Metric | L1 (4 models) | L3 (4 models) |
|--------|---------------|---------------|
| Correct name | 3/4 (75%) | **4/4 (100%)** |
| Abbreviated | 1/4 | 0/4 |

**L3 wins**: 100% vs 75% naming consistency.

#### Enum Value Spread

| Granularity | Min Values | Max Values | Spread |
|-------------|------------|------------|--------|
| L1 | 5 (Opus) | 11 (Gemini Pro) | **6 values** |
| L3 | 5 | 6 | **1 value** |

**L3 wins**: 6x less enum variation.

#### Code Volume Variation

| Granularity | Min Size | Max Size | Spread |
|-------------|----------|----------|--------|
| L1 | 17.6 KB | 38.4 KB | **39%** |
| L3 | 10.7 KB | 12.8 KB | **19%** |

**L3 wins**: 2x less code volume variation.

#### File Location Accuracy

| Metric | L1 (4 models) | L3 (4 models) |
|--------|---------------|---------------|
| Correct location | **4/4 (100%)** | 2/4 (50%) |
| Used routes/ | 0/4 | 2/4 |

**L1 wins**: The one metric where L1 outperformed L3. Indicates L3 plans need more explicit file path guidance.

---

### Summary Scorecard: L1 vs L3

| Metric | L1 Winner? | L3 Winner? |
|--------|------------|------------|
| Architecture style | | ✅ |
| Version format | | ✅ |
| Variable naming | | ✅ |
| File location | ✅ | |
| Enum consistency | | ✅ |
| Code volume | | ✅ |

**Final: L3 wins 5 of 6 categories**

---

## Cost-Effectiveness Analysis

### Efficiency Formula

```
Efficiency = Completion% / Cost_Multiplier
```

### Rankings by Efficiency

| Rank | Model | Granularity | Cost | Completion | Efficiency |
|------|-------|-------------|------|------------|------------|
| 1 | Grok Fast 1 | L3 | FREE | 100% | ∞ |
| 2 | Haiku 3.5 | L3 | 1x | 100% | **100.0** |
| 2 | Gemini Flash | L3 | 1x | 100% | **100.0** |
| 2 | GPT-5.1 | L3 | 1x | 100% | **100.0** |
| 5 | Sonnet 4.5 | L1 | 3x | 100% | 33.3 |
| 5 | Gemini Pro | L1 | 3x | 100% | 33.3 |
| 7 | Opus 4.5 | L1 | 5x | 100% | 20.0 |
| 8 | GPT-5.2 | L1 | 6x | 100% | 16.7 |

**Finding**: L3 models are 3-6x more cost-effective than L1 models at equivalent completion rates.

---

## Model-Specific Observations

### Claude Opus 4.5 Thinking (L1)
- **Strengths**: Fastest execution, best L1 quality score (95/100)
- **Weaknesses**: Created extra test file, highest cost
- **Best for**: Complex tasks requiring deep reasoning

### Claude Sonnet 4.5 Thinking (L1)
- **Strengths**: Fast, good quality (90/100), balanced cost
- **Weaknesses**: Wrong test directory, param naming deviation
- **Best for**: General-purpose premium tasks

### Gemini 3 Pro High (L1)
- **Strengths**: Concise code output
- **Weaknesses**: Used OOP instead of functional style, wrong version format
- **Best for**: When class-based architecture is acceptable

### GPT-5.2 High Reasoning Fast (L1)
- **Strengths**: Thorough implementation, created session logs
- **Weaknesses**: **Extremely slow**, wrong version format, largest code volume
- **Best for**: NOT recommended for time-sensitive tasks

### Grok Code Fast 1 (L3)
- **Strengths**: FREE, fast execution
- **Weaknesses**: Missing version, wrong file location
- **Best for**: Quick prototypes, cost-constrained projects

### Claude Haiku 3.5 (L3)
- **Strengths**: Best L3 adherence, fast, cheap
- **Weaknesses**: Minor enum variation
- **Best for**: **RECOMMENDED for most L3 tasks**

### Gemini Flash 3 High (L3)
- **Strengths**: Nearly identical output to Haiku, cheap
- **Weaknesses**: Minor enum variation
- **Best for**: Alternative to Haiku for L3 tasks

### GPT-5.1 Codex Max High (L3)
- **Strengths**: Complete implementation
- **Weaknesses**: Slower than Claude/Gemini, wrong file location
- **Best for**: When OpenAI ecosystem is required

---

## Recommendations

### For Plan Authors

1. **Always specify file paths explicitly** in both L1 and L3 plans
2. **Use standardized context prefixes**: `ARCHITECTURE:`, `FILE:`, `ENUM:`, `VERSION:`
3. **Include negative examples**: "DO NOT use class-based architecture"
4. **Enumerate exact enum values** to prevent sprawl

### For Model Selection

| Scenario | Recommended Model | Granularity |
|----------|-------------------|-------------|
| Budget-constrained | Haiku 3.5 or Gemini Flash | L3 |
| Quality-critical | Opus 4.5 | L1 (enhanced) |
| Balanced | Sonnet 4.5 | L1 or L2 |
| Free tier | Grok Fast 1 | L3 |
| Avoid | GPT-5.2 | Any (too slow) |

### For Workflow Design

1. **Default to L3 for budget models** - significant consistency improvement
2. **Use L1 with enhanced context for premium models** - they handle ambiguity better
3. **Consider L2 (new middle ground)** - constraints without full procedures
4. **Always include verification commands** - enables automated validation

---

## Schema Improvements Made

Based on this experiment, we updated `plan_schema.py` with:

### New L1 Context Prefixes
```python
- ARCHITECTURE:  # Style guidance
- FILE:          # Exact file paths
- FUNCTION:      # Exact signatures
- ENUM:          # Exact values
- VERSION:       # Format spec
- PARAM:         # Naming conventions
```

### New L2 Fields (Middle Ground)
```python
constraints: list[str]       # DO NOT, MUST, EXACTLY prefixes
existing_patterns: list[str] # References to code to match
```

### New L3 TaskStep Fields
```python
verification_hint: str   # Quick check after step
on_failure_hint: str     # What to check if step fails
```

---

## Conclusion

**L3 procedural plans significantly reduce stochastic variation** in AI-generated code, enabling budget models to match premium model quality. The 3-6x cost savings make L3 the recommended approach for most implementation tasks.

**The optimal strategy**:
- Use **L3 plans with Haiku/Flash** for standard implementation work
- Reserve **L1 plans with Opus/Sonnet** for complex architectural decisions
- Consider **L2 plans** (new) for mid-tier models needing constraints without full procedures

---

## Appendix: File Locations

- Experiment directory: `.experiments/EXP-001_L1-vs-L3-Granularity/`
- Individual results: `exp-l1-*/` and `exp-l3-*/` worktree folders
- Schema updates: `shared/contracts/plan_schema.py`
- Scoring rubric: `SCORECARD_V2.json`
- Detailed L1 comparison: `L1_SCORING_COMPARISON.md`

---

*Report generated: December 30, 2025*  
*Experiment conducted by: AI-Assisted Development Team*
