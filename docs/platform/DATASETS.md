# Working with DataSets

> **Shared data artifacts across tools**

---

## What is a DataSet?

A DataSet is a versioned, schema-aware data artifact that can be shared between tools. Each DataSet consists of:

- **Data file** - Parquet format for efficient storage and querying
- **Manifest** - JSON metadata including schema, lineage, and provenance

---

## DataSet Structure

```text
.artifacts/datasets/{dataset_id}/
├── data.parquet          # The actual data
└── manifest.json         # Metadata and schema
```

### Manifest Schema

```json
{
  "dataset_id": "dat_1703xyz...",
  "name": "Cleaned Production Data",
  "created_at": "2024-12-27T10:30:00Z",
  "created_by_tool": "dat",
  "row_count": 1500,
  "columns": [
    {"name": "Site", "dtype": "string", "nullable": false},
    {"name": "CD", "dtype": "float64", "nullable": true}
  ],
  "parent_dataset_ids": ["dat_1702abc..."],
  "tags": ["production", "cleaned"]
}
```

---

## API Reference

### List DataSets

```http
GET /api/datasets/v1
```

Query parameters:
- `tool` - Filter by source tool (dat, sov, pptx)
- `limit` - Maximum results (default: 50)

### Get DataSet Details

```http
GET /api/datasets/v1/{dataset_id}
```

Returns the full manifest including schema and lineage.

### Preview DataSet

```http
GET /api/datasets/v1/{dataset_id}/preview?rows=100
```

Returns first N rows of data with column information.

### Get Lineage

```http
GET /api/datasets/v1/{dataset_id}/lineage
```

Returns parent and child DataSet relationships.

---

## Using DataSets in Tools

### Data Aggregator

Create DataSets from raw data:

```python
# After aggregation, save as DataSet
POST /api/dat/jobs/{job_id}/save-dataset
{
  "name": "Aggregated Q4 Data",
  "tags": ["quarterly", "aggregated"]
}
```

### SOV Analyzer

Load DataSets for analysis:

```python
# Create analysis from DataSet
POST /api/sov/analyses
{
  "name": "Q4 SOV Analysis",
  "dataset_id": "dat_1703xyz..."
}
```

### PPTX Generator

Use DataSets as input data:

```python
# Load DataSet into project
POST /api/pptx/api/v1/data/{project_id}/from-dataset
{
  "dataset_id": "dat_1703xyz..."
}
```

---

## Lineage Tracking

DataSets maintain lineage through parent references:

```text
┌─────────────────┐
│  Raw Upload     │
│  dat_001        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Cleaned Data   │
│  dat_002        │
│  parent: dat_001│
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌───────┐
│dat_003│ │sov_001│
│Subset │ │Analysis│
└───────┘ └───────┘
```

---

## Best Practices

1. **Descriptive names** - Use clear, searchable DataSet names
2. **Tag appropriately** - Add tags for filtering and organization
3. **Preserve lineage** - Always reference parent DataSets
4. **Version control** - Create new DataSets rather than modifying
