# PowerPoint Generator

> **Automated PowerPoint generation with a guided workflow**

---

## What is PowerPoint Generator?

PowerPoint Generator transforms your data into fully automated presentations through a simple 7-step workflow:

1. **Upload Template** – PowerPoint with named shapes
2. **Configure Environment** – Select data source settings
3. **Upload Data** – CSV or Excel data files
4. **Map Context** – Connect dimensions to columns
5. **Map Metrics** – Configure numeric mappings
6. **Validate** – Four Green Bars confirmation
7. **Generate** – Download completed presentation

---

## Quick Links

### Getting Started

| Document | Description |
|----------|-------------|
| [Quick Start](getting-started/QUICK_START.md) | 5-minute first report guide |

### User Guides

| Document | Description |
|----------|-------------|
| [Troubleshooting](user-guide/TROUBLESHOOTING.md) | Common issues and solutions |

### Technical Reference

| Document | Description |
|----------|-------------|
| [Architecture](reference/ARCHITECTURE.md) | System design overview |

---

## Integration with Engineering Tools Platform

PowerPoint Generator is fully integrated with the Engineering Tools Platform:

### Using Platform DataSets

Instead of uploading data files directly, you can use DataSets from other tools:

1. Navigate to a PPTX project
2. In the Data step, click **Load from DataSet**
3. Select a DataSet from the catalog
4. Continue with the mapping workflow

### Pipeline Integration

PowerPoint Generator can be used as a step in cross-tool pipelines:

```yaml
# Example pipeline definition
name: "Weekly Report Pipeline"
steps:
  - tool: dat
    action: aggregate
    output: aggregated_data
  
  - tool: sov
    action: analyze
    input: $step_0_output
    output: sov_results
  
  - tool: pptx
    action: generate
    input: $step_1_output
    template: weekly_report_template.pptx
```

---

## API Endpoints

When running through the gateway, PPTX Generator APIs are available at:

| Endpoint | Description |
|----------|-------------|
| `GET /api/pptx/docs` | Interactive API documentation |
| `POST /api/pptx/api/v1/projects` | Create new project |
| `POST /api/pptx/api/v1/templates/{id}/upload` | Upload template |
| `POST /api/pptx/api/v1/generation` | Generate presentation |

See [API Documentation](reference/API.md) for complete reference.

---

## Version

**Current Version:** 0.2.0
**Documentation Version:** 1.1
**Last Updated:** 2024-12-27
