# DAT Example Data Files

This directory contains example data files for testing the CDU-DAT (CD-SEM Data Aggregation Tool) subsystem.

## Files

| File                 | Description                                  |
|----------------------|----------------------------------------------|
| `LOTABC12345_W01_CDSEM001_20251227_measurement.json` | Example measurement data for Lot ABC12345, Wafer 01, GATE layer |
| `LOTXYZ98765_W03_CDSEM002_20251228_measurement.json` | Example measurement data for Lot XYZ98765, Wafer 03, SPACER layer |

## File Naming Convention

Files follow the pattern:

```text
{LOT_ID}_{WAFER_ID}_{TOOL_ID}_{DATE}_measurement.json
```

This enables the profile's regex patterns to extract context automatically:

- **lot_id**: `(?P<lot_id>LOT[A-Z0-9]{6,10})`
- **wafer_id**: `(?P<wafer_id>W[0-9]{2})`
- **tool_id**: `(?P<tool_id>CDSEM[0-9]{3})`
- **measurement_date**: `(?P<measurement_date>[0-9]{8})`

## Data Structure Overview

Each JSON file contains heavily nested data matching the `cdsem_data_schema.json` schema:

### Top-Level Sections

1. **metadata** - File-level metadata (lot_id, wafer_id, layer, product)
2. **run_info** - Recipe, tool, operator, timestamps
3. **summary** - Run-level summary statistics (flat object)
4. **statistics** - Detailed statistics table (headers + data format)
5. **sites** - Per-site CD measurements (array with repeat-over extraction)
6. **uniformity** - Within-wafer uniformity metrics
7. **distributions** - Histogram data for CD and roughness
8. **roughness** - LWR/SWR analysis (Line Width Roughness, Sidewall Roughness)
9. **psd** - Power Spectral Density data (unbiased, biased, LWR, SWR)
10. **defects** - Defect analysis by category, location, severity
11. **diagnostics** - Tool diagnostic information (flat object)
12. **images** - Per-image measurements and quality metrics

### Table Extraction Strategies

The profile supports multiple extraction strategies:

| Strategy | Description | Example |
|----------|-------------|---------|
| `flat_object` | Direct key-value extraction | `summary`, `diagnostics` |
| `headers_data` | Headers array + data 2D array | `statistics`, `psd` |
| `headers_data` + `repeat_over` | Iterate over array items | `sites`, `images` |

## Usage

### Loading with Profile

```python
from dat_aggregation.profiles import load_profile
from dat_aggregation.adapters import AdapterFactory

profile = load_profile("cdsem_metrology_profile.yaml")
data = AdapterFactory.read_file(Path("examples/LOTABC12345_W01_CDSEM001_20251227_measurement.json"))
```

### Validating Against Schema

```python
import json
from jsonschema import validate

with open("cdsem_data_schema.json") as f:
    schema = json.load(f)

with open("examples/LOTABC12345_W01_CDSEM001_20251227_measurement.json") as f:
    data = json.load(f)

validate(instance=data, schema=schema)  # Raises on invalid
```

## Related Files

- `../cdsem_metrology_profile.yaml` - SSoT profile defining extraction rules
- `../cdsem_data_schema.json` - JSON Schema for data validation
- `../template_profile_schema.txt` - Typed template showing profile structure

## Test Coverage

These example files provide coverage for:

- [x] Run-level summary extraction
- [x] Run-level statistics with headers/data format
- [x] Site-level CD measurements with repeat-over
- [x] Uniformity metrics extraction
- [x] Distribution/histogram data
- [x] LWR/SWR roughness analysis
- [x] PSD (Power Spectral Density) tables
- [x] Defects by category/location/severity
- [x] Tool diagnostics
- [x] Image-level measurements with repeat-over
- [x] Image quality metrics
- [x] Context extraction via regex patterns
