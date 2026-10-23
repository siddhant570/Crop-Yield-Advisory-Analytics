# Crop Yield Advisory Analytics

**College Mini-Project Implementation (All 7 Syllabus Modules)**  
*2nd-Year B.Tech AI & Data Science Project*

---

## 📌 Problem Statement

> *Farmers often find it difficult to understand how factors such as soil conditions, rainfall, temperature, fertilizer usage, and irrigation affect crop yield. The proposed system analyzes agricultural data and presents useful insights through analytics and visualizations to support better crop-related decisions.*

### Foundational Course Mapping:
- **Python**: Data processing, wrangling, and analysis (Pandas, NumPy)
- **DBMS**: Relational dataset storage and management (MySQL / SQLite fallback)
- **Statistics**: Analysis of agricultural factors (Mean, Median, Std Dev, Pearson Correlation)
- **Data Visualization**: Graphs, charts, and dashboards (Chart.js, KPI metric cards)
- **Web/Software Development**: User interface and system integration (Flask, HTML, CSS, JavaScript)

---

## 📋 The 7 Project Modules

| Module # | Module Name | Route | Description |
|:---:|:---|:---|:---|
| **1** | **Data Collection** | `/datasets` | 2-step upload pipeline for CSV/XLSX datasets with auto column detection |
| **2** | **Data Cleaning & Preprocessing** | `/data` | Missing value handling, duplicate removal, record filtering, and manual entry |
| **3** | **Agricultural Database** | Backend | Relational storage via MySQL with automatic SQLite fallback (`db_config.py`) |
| **4** | **Statistical Analysis** | `/statistics` | Mean, Median, Standard Deviation, and Pearson correlation coefficients |
| **5** | **Crop Yield Analysis** | `/crop-analysis` | Aggregated yield performance grouped by crop type, soil, season, and irrigation |
| **6** | **Data Visualization & Dashboard** | `/` & `/visualization` | Executive KPI cards and interactive Chart.js visualizations |
| **7** | **Advisory Recommendation** | `/advisory` | Rule-based stress diagnostics (moisture, temperature, fertilizer) and action plans |

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, Vanilla CSS3 (Emerald Theme), JavaScript, Chart.js, FontAwesome
- **Backend**: Python 3.x, Flask Web Framework
- **Database**: MySQL (`crop_yield_advisory`) with automatic fallback to SQLite (`database/crop_yield.db`)
- **Data Analysis & Processing**: Pandas, NumPy, openpyxl

---

## 📁 Project Folder Structure

```
CropYieldAdvisoryAnalytics/
├── app.py                      # Flask Controller & Module Routes
├── requirements.txt            # Python Dependencies (Flask, pandas, numpy, openpyxl)
├── README.md                   # Project Documentation & Guide
│
├── data/
│   ├── raw/                    # Uploaded raw CSV/XLSX files
│   └── cleaned/                # Processed datasets
│
├── database/
│   ├── schema.sql              # MySQL DDL Schema
│   └── db_config.py            # MySQL & SQLite Database Connection Handler
│
├── python/
│   ├── data_analysis.py        # Data Wrangling & Dynamic Chart Aggregations
│   ├── statistics.py          # Descriptive Statistics & Pearson Correlation
│   ├── dataset_importer.py     # CSV/XLSX Reader, Auto-Column Matcher & DB Batch Importer
│   ├── data_validator.py       # Validation Rules & Dataset Quality Score Meter
│   ├── data_cleaning.py        # Whitespace Trimming, Type Coercion & Missing Value Handling
│   └── advisory_engine.py      # Module 7: Rule-Based Stress Diagnostic & Advisory Engine
│
├── templates/
│   ├── base.html               # Master Page Layout & Navigation Bar
│   ├── dashboard.html          # Module 6: Metric Cards & Overview Charts
│   ├── data.html               # Module 2: Data Table & Manual Entry
│   ├── dataset_management.html # Module 1: 2-Step Dataset Upload & Quality Validation
│   ├── statistics.html         # Module 4: Mean/Median/Std & Correlation Analysis
│   ├── crop_analysis.html      # Module 5: Grouped Yield Comparisons & Top Performers
│   ├── visualization.html      # Module 6: Interactive Charts with Crop Filtering
│   ├── advisory.html           # Module 7: Field Stress Diagnostics & Recommendations
│   └── about.html              # Academic Info & Schema Table
│
└── static/
    ├── css/
    │   └── style.css           # Academic Emerald CSS Theme
    └── js/
        └── script.js           # Chart.js Integration
```

---

## 🚀 Step-by-Step Execution Guide

### 1. Install Dependencies
Open terminal in the project directory and run:

```bash
pip install -r requirements.txt
```

### 2. Configure Database (Optional MySQL)
- The system connects to **MySQL** by default if available.
- If MySQL is not running locally, **the system automatically uses SQLite (`database/crop_yield.db`)**, so the application runs immediately without any setup.

### 3. Run the Flask Web Application
Launch the app with:

```bash
python app.py
```

Open your browser and navigate to:
👉 **`http://127.0.0.1:5000/`**

---

## 📊 Dataset Import Workflow (2-Step Pipeline)

1. Navigate to **Datasets** (`/datasets`).
2. **Step 1 — Upload File**: Select your agricultural CSV or XLSX file and enter a dataset name.
3. **Step 2 — Quality Validation & Preview**: The system automatically detects columns, cleans missing/duplicate data, calculates the **Quality Score (%)**, and previews the cleaned records.
4. Click **Confirm & Import Records to Database** — data is saved and you are redirected to the **Data Table**!
