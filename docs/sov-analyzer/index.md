# SOV Analyzer

> **Source of Variation analysis and statistical insights**

---

## What is SOV Analyzer?

SOV (Source of Variation) Analyzer is a statistical analysis tool that helps identify and quantify the sources of variation in your data. It provides:

- **Variance decomposition** - Break down total variation into components
- **Factor analysis** - Identify which factors contribute most to variation
- **Statistical tests** - ANOVA, regression, and hypothesis testing
- **Visualization** - Charts and plots for understanding variation

---

## Key Features

### Analysis Types

| Analysis | Description |
|----------|-------------|
| **One-way ANOVA** | Variation analysis with single factor |
| **Two-way ANOVA** | Variation analysis with two factors |
| **Nested ANOVA** | Hierarchical factor analysis |
| **Regression** | Linear and multiple regression |
| **Control Charts** | Process stability monitoring |

### Visualization

| Chart Type | Use Case |
|------------|----------|
| **Box Plots** | Distribution by factor |
| **Pareto Charts** | Ranked contribution to variation |
| **Control Charts** | Time-series process monitoring |
| **Scatter Plots** | Relationship between variables |
| **Histograms** | Distribution shape and spread |

### Output Reports

- Statistical summary tables
- Variance component estimates
- Factor significance rankings
- Recommendations for variation reduction

---

## Quick Start

### 1. Select Data

1. Navigate to SOV Analyzer from the homepage
2. Click **+ New Analysis**
3. Select a DataSet from the catalog or upload new data

### 2. Configure Analysis

1. Select response variable (the metric to analyze)
2. Select factor variables (potential sources of variation)
3. Choose analysis type (ANOVA, regression, etc.)

### 3. Run Analysis

1. Click **Run Analysis**
2. Review statistical results
3. Explore interactive visualizations

### 4. Export Results

1. Save as DataSet for use in other tools
2. Generate PDF/Excel report
3. Export charts as images

---

## Integration with Platform

### DataSet Input/Output

SOV Analyzer reads from and writes to the shared DataSet store:

```python
# Input: Load DataSet from Data Aggregator
dataset_id = "dat_1703xyz..."

# Output: Save analysis results
output_dataset_id = "sov_1703abc..."
```

### Pipeline Integration

SOV Analyzer can be used in pipelines:

```yaml
steps:
  - tool: dat
    action: aggregate
    output: raw_data
  
  - tool: sov
    action: analyze
    config:
      analysis_type: anova
      response: CD
      factors: [Site, Equipment, Wafer]
    input: $step_0_output
    output: sov_results
  
  - tool: pptx
    action: generate
    input: $step_1_output
    template: sov_report.pptx
```

---

## API Endpoints

When running through the gateway:

| Endpoint | Description |
|----------|-------------|
| `POST /api/sov/analyses` | Create analysis job |
| `PUT /api/sov/analyses/{id}/config` | Configure analysis |
| `POST /api/sov/analyses/{id}/run` | Execute analysis |
| `GET /api/sov/analyses/{id}/results` | Get results |
| `GET /api/sov/analyses/{id}/charts` | Get chart data |

---

## Statistical Methods

### ANOVA

Analysis of Variance decomposes total variation:

```text
Total SS = Between-group SS + Within-group SS

Variance Explained = Between-group SS / Total SS
```

### Variance Components

For nested designs:

```text
σ²_total = σ²_site + σ²_equipment(site) + σ²_wafer(equipment) + σ²_error
```

### Significance Testing

- F-tests for factor significance
- p-values for hypothesis testing
- Confidence intervals for estimates

---

## Status

✅ **Core Complete** - ANOVA pipeline with visualization contracts implemented.

### Roadmap

- [x] Basic ANOVA (one-way, two-way, n-way)
- [x] Box plot visualization
- [x] Variance bar charts
- [x] DataSet integration with lineage
- [x] Visualization contracts (ADR-0025)
- [ ] Nested ANOVA (future)
- [ ] Regression analysis (future)
- [ ] Control charts (future)
- [ ] PDF report generation (future)
