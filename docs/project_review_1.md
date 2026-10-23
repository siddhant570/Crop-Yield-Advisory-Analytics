# Project Review 1 — CROP YIELD ADVISORY ANALYTICS

**Department of Computer Science / AI & Data Science**  
**Academic Year:** 2nd-Year B.Tech Mini-Project  
**Target Completion:** 50%–60% Prototype Review

---

## 1. Problem Statement & Context

Agricultural crop yield is governed by multiple interconnected natural and anthropogenic factors, including soil properties, temperature variations, precipitation levels, fertilizer usage, and irrigation methods. Farmers and agricultural analysts often lack accessible tools to quickly visualize historical dataset trends and compute statistical dependencies between environmental drivers and crop yields.

The **Crop Yield Advisory Analytics** project provides a prototype web-based analytics dashboard that connects to an agricultural database, computes descriptive statistics, renders interactive visualizations, and prepares a foundation for future advisory and prediction modules.

---

## 2. Project Objectives & Scope

### Primary Objectives:
1. Build a functional relational database (MySQL/SQLite) storing agricultural records across diverse Indian regions and crops.
2. Develop a Python Flask web application allowing data viewing, searching, filtering, and record insertion.
3. Compute baseline descriptive statistics (Mean, Median, Std Dev, Min, Max) and bivariate Pearson correlation coefficients.
4. Render responsive canvas visualizations using Chart.js.
5. Clearly delineate completed functional modules (50–60% stage) from planned advisory and prediction modules.

### Scope Boundaries:
- Academic prototype stage for project review evaluation.
- Focuses on analytics and statistical indicators; does not claim scientifically validated real-time farming advice.

---

## 3. Dataset Attributes & Schema

The system utilizes an agricultural dataset with the following 10 parameters:

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | INT (PK) | Unique Record Identifier |
| `crop_type` | VARCHAR(50) | Rice, Wheat, Maize, Cotton, Sugarcane, Pulses |
| `soil` | VARCHAR(50) | Alluvial, Black, Red, Clay, Loam |
| `rainfall` | FLOAT | Seasonal Rainfall in millimeters (mm) |
| `temperature` | FLOAT | Ambient Temperature in °C |
| `fertilizer` | FLOAT | Fertilizer application rate in kg/ha |
| `irrigation` | VARCHAR(50) | Canal, Drip, Tube Well, Rainfed |
| `yield_value` | FLOAT | Crop Yield output in tons/ha |
| `location` | VARCHAR(100) | State / Region in India |
| `season` | VARCHAR(50) | Kharif, Rabi, Zaid |

---

## 4. Module Implementation Status Matrix (Final Complete Implementation)

| Module ID | Module Title | Target Stage | Status | Implementation Details |
| :--- | :--- | :--- | :--- | :--- |
| **MODULE 1** | Dashboard | Functional | ✅ Completed | Real-time metric cards, overview charts, 100% completion progress tracker |
| **MODULE 2** | Agricultural Data & Upload | Functional | ✅ Completed | Table view, search, dropdown filter, manual entry, 3-step CSV/XLSX import wizard |
| **MODULE 3** | Statistical Analysis | Functional | ✅ Completed | Mean, Median, Std Dev, Min/Max, Pearson Correlation analysis (missing field safe) |
| **MODULE 4** | Yield Visualization | Functional | ✅ Completed | 5 dynamic Chart.js canvas charts with interactive crop filter |
| **MODULE 5** | Advisory Recommendation | Functional | ✅ Completed | Scientific rule-based stress diagnostic engine (moisture, thermal, nutrient, soil & IPM advice) |
| **MODULE 6** | Advanced ML Prediction | Functional | ✅ Completed | Supervised regression (Random Forest, Ridge, Gradient Boosting) with R², MAE, RMSE & feature weights |
| **MODULE 7** | Advanced Academic Reports | Functional | ✅ Completed | Clean print-ready / PDF report generator, benchmarks matrix & one-click CSV exports |


---

## 5. Review Presentation Highlights

When demonstrating the project during Review 1, highlight:
1. **Database Integration**: Add a new record in the Agricultural Data page and verify that it updates the Dashboard metrics and charts dynamically.
2. **Statistical Rigor**: Show the Pearson Correlation calculations and explain that correlation indicates directional linear relationship without asserting direct causation.
3. **Visual Exploration**: Filter visualizations by specific crop types (e.g. Rice or Wheat) on the Crop Yield Visualization page.
