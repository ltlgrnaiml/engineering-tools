# Creating Multi-Tool Pipelines

> **Orchestrating workflows across tools**

---

## What is a Pipeline?

A Pipeline is a sequence of steps that chain tool operations together. Each step:

- Runs a specific tool action
- Takes input DataSets (from previous steps or catalog)
- Produces output DataSets for downstream steps

---

## Pipeline Structure

```yaml
name: "Weekly Analysis Pipeline"
description: "Aggregate, analyze, and report"
steps:
  - name: "Aggregate Data"
    tool: dat
    action: aggregate
    config:
      sources: [...]
    output: aggregated_data
  
  - name: "Run SOV Analysis"
    tool: sov
    action: analyze
    input: $step_0_output
    config:
      analysis_type: anova
    output: sov_results
  
  - name: "Generate Report"
    tool: pptx
    action: generate
    input: $step_1_output
    config:
      template: weekly_template.pptx
```

---

## API Reference

### Create Pipeline

```http
POST /api/pipelines/v1
```

```json
{
  "name": "My Pipeline",
  "description": "Description",
  "steps": [...],
  "auto_execute": false
}
```

### List Pipelines

```http
GET /api/pipelines/v1
```

### Get Pipeline Status

```http
GET /api/pipelines/v1/{pipeline_id}
```

### Execute Pipeline

```http
POST /api/pipelines/v1/{pipeline_id}/execute
```

### Cancel Pipeline

```http
POST /api/pipelines/v1/{pipeline_id}/cancel
```

---

## Step Types

### Data Aggregator Steps

| Action | Description |
|--------|-------------|
| `dat:aggregate` | Run aggregation job |
| `dat:transform` | Apply transformations |
| `dat:filter` | Filter rows |

### SOV Analyzer Steps

| Action | Description |
|--------|-------------|
| `sov:analyze` | Run SOV analysis |
| `sov:compare` | Compare analyses |

### PPTX Generator Steps

| Action | Description |
|--------|-------------|
| `pptx:generate` | Generate presentation |

---

## Dynamic Input References

Use `$step_N_output` to reference outputs from previous steps:

```yaml
steps:
  - name: "Step 0"
    tool: dat
    action: aggregate
    output: step_0_data
  
  - name: "Step 1"
    tool: sov
    input: $step_0_output  # References step 0's output
    action: analyze
```

---

## Pipeline States

| State | Description |
|-------|-------------|
| `draft` | Pipeline created, not yet executed |
| `queued` | Waiting to start execution |
| `running` | Currently executing |
| `completed` | All steps finished successfully |
| `failed` | A step failed |
| `cancelled` | User cancelled execution |

---

## Step States

| State | Description |
|-------|-------------|
| `pending` | Not yet started |
| `running` | Currently executing |
| `completed` | Finished successfully |
| `failed` | Failed with error |
| `cancelled` | Cancelled by user |
| `skipped` | Skipped due to earlier failure |

---

## Error Handling

When a step fails:

1. The step is marked as `failed` with error message
2. The pipeline state changes to `failed`
3. Remaining steps are **not executed**
4. Completed artifacts are **preserved** (ADR-0002)

To retry:
1. Fix the underlying issue
2. Create a new pipeline or modify configuration
3. Execute again

---

## Best Practices

1. **Start simple** - Begin with 2-3 steps, add complexity gradually
2. **Test steps individually** - Verify each tool works before chaining
3. **Use descriptive names** - Make pipeline and step names clear
4. **Handle failures gracefully** - Plan for step failures in your workflow
