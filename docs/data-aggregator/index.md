# Data Aggregator

> **Collect, clean, and transform data from multiple sources**

---

## What is Data Aggregator?

Data Aggregator is a tool for consolidating and transforming data from various sources into clean, analysis-ready DataSets. It provides:

- **Multi-source ingestion** - Import from CSV, Excel, databases, and APIs
- **Data cleaning** - Handle missing values, duplicates, and format issues
- **Transformations** - Filter, join, aggregate, and derive new columns
- **DataSet output** - Save results as versioned DataSets for other tools

---

## Key Features

### Data Import

| Source | Supported Formats |
|--------|------------------|
| Files | CSV, Excel (.xlsx, .xls), Parquet |
| Databases | PostgreSQL, MySQL, SQLite |
| APIs | REST endpoints with JSON response |

### Transformations

| Operation | Description |
|-----------|-------------|
| **Filter** | Select rows matching conditions |
| **Join** | Combine data from multiple sources |
| **Aggregate** | Group and summarize data |
| **Derive** | Create new columns from expressions |
| **Pivot** | Reshape data between wide and long formats |

### Quality Checks

- Missing value detection and handling
- Duplicate row identification
- Data type validation
- Outlier detection

---

## Quick Start

### 1. Create a New Aggregation

1. Navigate to Data Aggregator from the homepage
2. Click **+ New Aggregation**
3. Name your aggregation job

### 2. Import Data

1. Click **Add Source**
2. Select source type (File, Database, or API)
3. Configure connection and import settings
4. Preview imported data

### 3. Transform Data

1. Add transformation steps as needed
2. Preview results at each step
3. Validate data quality

### 4. Export as DataSet

1. Click **Save as DataSet**
2. Name and describe your DataSet
3. DataSet is now available to other tools

---

## Integration with Platform

### DataSet Output

Data Aggregator saves results to the shared DataSet store:

```python
# DataSet is automatically available to other tools
dataset_id = "dat_1703xyz..."

# Use in PPTX Generator
POST /api/pptx/api/v1/data/{project_id}/from-dataset
{
  "dataset_id": "dat_1703xyz..."
}
```

### Pipeline Integration

Data Aggregator can be used as a step in pipelines:

```yaml
steps:
  - tool: dat
    action: aggregate
    config:
      sources:
        - type: csv
          path: raw_data.csv
      transformations:
        - type: filter
          condition: "status == 'active'"
    output: cleaned_data
```

---

## API Endpoints

When running through the gateway:

| Endpoint | Description |
|----------|-------------|
| `POST /api/dat/jobs` | Create aggregation job |
| `POST /api/dat/jobs/{id}/sources` | Add data source |
| `POST /api/dat/jobs/{id}/transform` | Add transformation |
| `POST /api/dat/jobs/{id}/execute` | Execute aggregation |
| `GET /api/dat/jobs/{id}/preview` | Preview results |

---

## Status

🔄 **In Development** - Core functionality is being implemented.

### Roadmap

- [x] Basic file import (CSV, Excel)
- [x] Core transformations (filter, join, aggregate)
- [ ] Database connectors
- [ ] API connectors
- [ ] Advanced transformations
- [ ] Scheduled aggregation jobs
