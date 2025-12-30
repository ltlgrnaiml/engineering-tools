# EXP-001: Cost Analysis Results

## Model Matrix

### L1 Models (Expensive, Less Detail)

| Model | Cost | Branch | Score | Efficiency |
|-------|------|--------|-------|------------|
| Claude Opus 4.5 Thinking | 5x | `experiment/l1-opus` | ___ | ___/5 |
| Claude Sonnet 4.5 Thinking | 3x | `experiment/l1-sonnet` | ___ | ___/3 |
| GPT-5.2 High Reasoning Fast | 6x | `experiment/l1-gpt52` | ___ | ___/6 |
| Gemini 3 Pro High | 3x | `experiment/l1-gemini3pro` | ___ | ___/3 |

### L3 Models (Cheap, Full Detail)

| Model | Cost | Branch | Score | Efficiency |
|-------|------|--------|-------|------------|
| Grok Code Fast 1 | FREE | `experiment/l3-grok` | ___ | ∞ (if score > 0) |
| Claude Haiku | 1x | `experiment/l3-haiku` | ___ | ___/1 |
| Gemini Flash 3 High | 1x | `experiment/l3-gemini-flash` | ___ | ___/1 |
| GPT-5.1-Codex Max High | 1x | `experiment/l3-gpt51` | ___ | ___/1 |

## Efficiency Formula

```
Score Efficiency = DoD Score / Cost Multiplier
```

Higher is better. A model that scores 80 at 1x cost is more efficient than one scoring 95 at 6x cost.

## Results Summary

### Best L1 Result

- **Model**: ___________
- **Score**: ___/100
- **Cost**: ___x
- **Efficiency**: ___

### Best L3 Result

- **Model**: ___________
- **Score**: ___/100
- **Cost**: ___x
- **Efficiency**: ___

### Overall Winner

- **Model**: ___________
- **Granularity**: L_
- **Score**: ___/100
- **Efficiency**: ___

## Cost-Effectiveness Ranking

| Rank | Model | Gran | Score | Cost | Efficiency |
|------|-------|------|-------|------|------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |
| 6 | | | | | |
| 7 | | | | | |
| 8 | | | | | |

## Key Findings

### Does L3 enable cheaper models to succeed?

___ (Yes/No/Partially)

### Quality threshold for acceptable output

___ points minimum

### Recommended configuration for production

- **Budget-conscious**: ___________
- **Quality-focused**: ___________
- **Balanced**: ___________

## Qualitative Observations

### L1 Group

- Common issues: ___
- Strengths: ___

### L3 Group

- Common issues: ___
- Strengths: ___

## Conclusion

___________
