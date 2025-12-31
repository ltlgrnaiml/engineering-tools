# EXP-002: Model Quality Evaluation

Evaluate xAI model performance on generating DevTools workflow documentation.

## Files

| File | Purpose |
|------|---------|
| `TEST_SCENARIO.md` | The exact prompt and expected outputs |
| `RUBRICS.md` | Detailed scoring rubrics (25 pts each, 100 total) |
| `results/` | Store generated outputs per model |

## How to Run the Evaluation

### Step 1: Prepare

Ensure your `.env` has `XAI_API_KEY` set.

### Step 2: Generate with Each Model

1. Start the platform: `.\start.ps1`
2. Open the Workflow Manager
3. Click **New Workflow** → **AI-Full**
4. Use this exact input:

   **Title:** `Artifact Version History`
   
   **Description:**
   ```text
   Add version history tracking to artifacts in the DevTools Workflow Manager. 
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

5. Select a model from the dropdown
6. Click **Generate**
7. Save the 4 generated artifacts to `results/{model_name}/`
8. Repeat for each model

### Step 3: Grade Each Output

Use the scoring sheet in `RUBRICS.md` to grade each document.

### Step 4: Record Results

Update the evaluation table in `TEST_SCENARIO.md`.

## Models to Test

| Model | Category | Expected Strength |
|-------|----------|-------------------|
| `grok-4-fast-reasoning` | Fast + Reasoning | Good balance, default |
| `grok-4-0709` | Premium | Highest quality expected |
| `grok-3` | Premium | Strong baseline |
| `grok-code-fast-1` | Code-focused | May excel at SPEC/PLAN |
| `grok-3-mini` | Budget | Lower quality expected |

## Success Criteria

- **Minimum Viable**: 60/100 (usable with heavy editing)
- **Good**: 75/100 (usable with moderate editing)
- **Excellent**: 85/100 (minimal editing needed)

## Cost Tracking

| Model | Input Price | Output Price | Est. Cost per Run |
|-------|-------------|--------------|-------------------|
| grok-4-fast-reasoning | $0.20/M | $0.50/M | ~$0.01 |
| grok-4-0709 | $3.00/M | $15.00/M | ~$0.10 |
| grok-3 | $3.00/M | $15.00/M | ~$0.10 |
| grok-code-fast-1 | $0.20/M | $1.50/M | ~$0.02 |
| grok-3-mini | $0.30/M | $0.50/M | ~$0.01 |

## Analysis Questions

After running all models, answer:

1. **Quality vs Cost**: Is the premium model worth 10x the cost?
2. **Reasoning Models**: Do reasoning models produce better architecture docs?
3. **Code Models**: Does `grok-code-fast-1` excel at SPEC/PLAN?
4. **Minimum Viable**: Which is the cheapest model that scores 60+?
5. **Recommendation**: Which model should be the default?
