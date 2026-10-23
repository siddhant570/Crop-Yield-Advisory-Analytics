# Flexible Dataset Import Workflow & Provenance Documentation

**Crop Yield Advisory Analytics** — College Mini-Project (50–60% Implementation Stage)

---

## 📌 Architecture Overview

Instead of hardcoding Python data ingestion logic for a single fixed dataset, the system provides a flexible **Dataset Management & Import Pipeline**. Users can legally download publicly available agricultural datasets (from Kaggle, Government open-data portals, or UN FAO) in **CSV** or **XLSX** format and upload them directly into the web application.

```
Public Dataset (Kaggle / Open Data)
               ↓
      Upload CSV / XLSX File
               ↓
   Read File & Auto-Column Matching
               ↓
    User Column Mapping UI (Dropdowns)
               ↓
  Validation Rules & Quality Score (0-100%)
               ↓
   Pandas Data Cleaning Pipeline
               ↓
 Mapped Data Preview Table (First 20 Rows)
               ↓
 Batch MySQL / SQLite Database Import
               ↓
Dynamic Dashboard, Statistics & Charts Update
```

---

## 🔍 Step-by-Step Technical Pipeline

### Step 1: File Upload & Metadata Registration
- Supported Formats: `.csv`, `.xlsx`, `.xls`
- Max Recommended File Size: 50MB
- Metadata Captured:
  - `Dataset Name`: User-friendly title
  - `Source Portal`: e.g., Kaggle, Data.gov.in, FAO
  - `Source URL`: Public link to dataset source for attribution & traceability

### Step 2: Auto Column Matching & Mapping Engine
The system uses fuzzy keyword matching (`python/dataset_importer.py`) to suggest column mappings for standard system fields:

| Standard Field | Required | Synonym Keywords |
| :--- | :--- | :--- |
| `crop_type` | **Yes** | `crop`, `crop_type`, `crop type`, `crop name`, `commodity` |
| `yield_value` | **Yes** | `yield`, `crop yield`, `production`, `yield per hectare`, `yield(t/ha)` |
| `rainfall` | Optional | `rainfall`, `annual rainfall`, `rain`, `precipitation` |
| `temperature` | Optional | `temperature`, `avg temperature`, `avg_temp`, `temp` |
| `fertilizer` | Optional | `fertilizer`, `fertilizer used`, `fertilizer amount` |
| `soil` | Optional | `soil`, `soil_type`, `soil type`, `soil quality` |
| `irrigation` | Optional | `irrigation`, `irrigation method`, `water_source` |
| `location` | Optional | `location`, `state`, `region`, `district` |
| `season` | Optional | `season`, `cropping season`, `crop_season` |

> **Flexibility Rule**: Only `crop_type` and `yield_value` are mandatory. For omitted fields, users select **"Not Available"**. The system handles missing optional fields gracefully across all analytics pages without producing fake values or crashing.

### Step 3: Data Validation & Quality Score Calculation
Validation checks (`python/data_validator.py`):
1. **Total & Valid Rows**: Counts rows without missing required fields.
2. **Duplicate Rows**: Identifies exact duplicate rows across mapped columns.
3. **Invalid Numeric Values**: Detects negative values for rainfall, fertilizer, or yield, and unrealistic ambient temperatures ($<-20^\circ\text{C}$ or $>60^\circ\text{C}$).

#### Quality Score Formula:
$$\text{Quality Score} = \text{Valid Ratio} (50\%) + \text{Completeness Ratio} (30\%) + \text{Duplicate Penalty} (10\%) + \text{Required Bonus} (10\%)$$

Status Badges:
- **`85.0% – 100%`**: `EXCELLENT FOR ANALYSIS`
- **`65.0% – 84.9%`**: `GOOD FOR ANALYSIS`
- **`< 65.0%`**: `NEEDS CLEANING BEFORE IMPORT`

### Step 4: Pandas Data Cleaning
Cleaning operations (`python/data_cleaning.py`):
- Trims whitespace from text fields.
- Converts numerical columns safely with `pd.to_numeric(..., errors='coerce')`.
- Removes duplicate rows and completely empty rows.
- User choice for missing value handling (Drop affected rows OR impute with mean/median for numeric and `'Unknown'` for categorical).

### Step 5: Provenance & Source Tracking
Every imported dataset logs an entry into the `dataset_sources` table containing:
- `dataset_name`, `source_name`, `source_url`, `import_date`, `record_count`, `available_fields`, `quality_score`.

All individual agricultural records store `source_dataset` name in the `agricultural_data` table, allowing side-by-side comparison and filtered viewing!
