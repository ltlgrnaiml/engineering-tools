# PowerPoint Generator - Quick Start

> **Your First Report in 5 Minutes** 🚀

---

## The 7-Step Workflow at a Glance

```
┌──────────┐   ┌─────────────┐   ┌──────────┐   ┌─────────────┐
│ Template │ → │ Environment │ → │   Data   │ → │   Context   │
│  Upload  │   │   Profile   │   │  Upload  │   │   Mapping   │
└──────────┘   └─────────────┘   └──────────┘   └─────────────┘
                                                       │
                                                       ▼
┌──────────┐   ┌─────────────┐   ┌──────────┐   ┌─────────────┐
│ Generate │ ← │  Validate   │ ← │   Plan   │ ← │   Metrics   │
│   🎉     │   │ (4 Bars)    │   │  Build   │   │   Mapping   │
└──────────┘   └─────────────┘   └──────────┘   └─────────────┘
```

---

## Quick Start Guide

### Step 1: Create Project
1. Click **+ New Project** on the home page
2. Enter a project name (e.g., "Q4 Sales Report")
3. Click **Create Project**

### Step 2: Upload Template
1. Click **Choose Template File**
2. Select your `.pptx` file with labeled shapes
3. Wait for automatic parsing (DRM extraction)

### Step 3: Select Environment
1. Choose a preset:
   - **Local Filesystem** – For local development
   - **Azure Data Lake** – For production ADLS Gen2
2. Click to select and proceed

### Step 4: Upload Data
1. Click **Choose Data File**
2. Select your `.csv` or `.xlsx` file
3. Wait for auto-suggestions to generate

### Step 5: Map Context & Metrics
1. Review suggested mappings (blue highlights)
2. Click **Accept** for good suggestions
3. Or expand rows to configure manually
4. Click **Save Mappings** when done

### Step 6: Validate (Four Green Bars)
1. Review all four validation bars
2. Fix any red/yellow items
3. Click **Build Plan** when all green

### Step 7: Generate
1. Click **Generate Presentation**
2. Download your completed PowerPoint!

---

## Understanding the Four Bars

| Bar | What It Checks | How to Fix |
|-----|----------------|------------|
| ✅ **Required Context** | All context dimensions mapped | Map missing contexts in Step 5 |
| ✅ **Required Metrics** | All numeric metrics mapped | Map missing metrics in Step 5 |
| ✅ **Required Data Levels** | Correct data cardinality | Check data file structure |
| ✅ **Required Renderers** | All shape renderers available | Verify template shape names |

### Bar Colors

| Color | Meaning | Can Proceed? |
|-------|---------|--------------|
| 🟢 Green | All good! | Yes |
| 🟡 Yellow | Warnings present | Review recommended |
| 🔴 Red | Critical issues | Must fix first |

---

## Mapping Quick Tips

### Context Mappings

| Source Type | When to Use | Example |
|-------------|-------------|---------|
| **Column** | Value exists directly in data | `site` → `Site_Name` column |
| **Regex** | Extract from another column | `run_key` → Extract `DZ\d+` from filename |
| **Default** | Hardcoded value | `report_type` → `"Quarterly"` |

### Metrics Mappings

| Field | Purpose | Example |
|-------|---------|---------|
| **Source Column** | Data column containing values | `SpaceCD_nm` |
| **Aggregation** | How to combine multiple rows | `mean`, `median`, `3sigma` |
| **Rename To** | Optional display name | `Space CD` |

---

## Common Workflows

### "I need to change my data file"

1. Click **Data** in the breadcrumb
2. Confirm rollback (clears mappings)
3. Upload new file
4. Re-map context and metrics

### "I want to try different mappings"

1. Click **Context Mapping** or **Metrics Mapping**
2. Modify mappings as needed
3. Save and re-validate

### "My template changed"

1. Click **Template** in the breadcrumb
2. Confirm rollback (clears everything)
3. Upload updated template
4. Start fresh from Step 2

---

## File Format Requirements

### Template (.pptx)
- PowerPoint 2016 or later
- Shapes named with `[TYPE].[NAME]` convention
- At least one data-bound shape

### Data Files
| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | UTF-8 recommended |
| Excel | `.xlsx`, `.xls` | First sheet used |

### Required Columns
- At least one context column
- At least one numeric metric column
- Consistent naming (no special characters)

---

## Need Help?

- 🔧 **Troubleshooting:** See [Troubleshooting](../user-guide/TROUBLESHOOTING.md)
