"""
Crop Yield Advisory Analytics - Flask Web Application
College Mini-Project — 2nd-Year B.Tech AI & Data Science
Modules: Data Collection, Data Cleaning, Agricultural Database,
         Statistical Analysis, Crop Yield Analysis, Visualization, Advisory
"""

from flask import Flask, render_template, request, redirect, url_for, flash, Response
import sys
import os
import pandas as pd
import numpy as np
import json

sys.path.append(os.path.dirname(__file__))
from python.data_analysis import (
    load_data, filter_records, add_agricultural_record, 
    get_dashboard_summary, get_chart_data
)
from python.statistics import get_descriptive_stats, get_correlation_analysis
from python.dataset_importer import (
    read_uploaded_file, suggest_column_mappings, 
    import_records_to_db, get_imported_dataset_sources, STANDARD_FIELDS
)
from python.data_validator import validate_dataset
from python.data_cleaning import clean_and_transform_dataset
from python.advisory_engine import (
    analyze_crop_advisory, get_dataset_wide_advisories, 
    CROP_AGRONOMIC_PROFILES
)
from database.db_config import get_db_connection, reset_database_to_baseline


app = Flask(__name__)
app.secret_key = "crop_yield_analytics_mini_project_secret_key"

RAW_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")
os.makedirs(RAW_UPLOAD_DIR, exist_ok=True)

print("[OK] Application Startup: Using existing database state.")

@app.context_processor
def inject_global_data_status():
    conn, is_mysql = get_db_connection()
    count = 0
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM agricultural_data")
        row = cursor.fetchone()
        count = row[0] if row else 0
    except Exception:
        count = 0
    finally:
        if not is_mysql and hasattr(conn, 'close'):
            conn.close()
    return {
        "has_data": count > 0,
        "total_system_records": count
    }

@app.route("/reset-datasets", methods=["GET", "POST"])
def reset_datasets():
    """
    Clears all uploaded datasets and resets system to empty state.
    """
    reset_database_to_baseline()
    flash("Successfully removed all datasets! The system is now completely empty. Please upload your dataset to begin.", "success")
    return redirect(url_for("dataset_management"))

@app.route("/")
def dashboard():
    """
    Module 1: Dashboard View
    """
    source_dataset = request.args.get("dataset", None)
    metrics = get_dashboard_summary(source_dataset=source_dataset)
    chart_payload = get_chart_data(source_dataset=source_dataset)
    dataset_sources = get_imported_dataset_sources()

    return render_template(
        "dashboard.html", 
        metrics=metrics, 
        chart_data=chart_payload,
        dataset_sources=dataset_sources,
        selected_dataset=source_dataset
    )

@app.route("/data", methods=["GET"])
def agricultural_data():
    """
    Module 2: Agricultural Data Table View
    """
    search_query = request.args.get("search", "")
    crop_filter = request.args.get("crop", "All")
    soil_filter = request.args.get("soil", "All")
    season_filter = request.args.get("season", "All")
    source_dataset = request.args.get("dataset", None)

    df_filtered = filter_records(
        search=search_query, 
        crop=crop_filter, 
        soil=soil_filter, 
        season=season_filter,
        source_dataset=source_dataset
    )
    records = df_filtered.to_dict(orient="records") if not df_filtered.empty else []

    full_df = load_data()
    crop_options = ["All"] + sorted(full_df['crop_type'].dropna().unique().tolist()) if ('crop_type' in full_df and not full_df.empty) else ["All"]
    soil_options = ["All"] + sorted(full_df['soil'].dropna().unique().tolist()) if ('soil' in full_df and not full_df.empty) else ["All"]
    season_options = ["All"] + sorted(full_df['season'].dropna().unique().tolist()) if ('season' in full_df and not full_df.empty) else ["All"]

    dataset_sources = get_imported_dataset_sources()

    return render_template(
        "data.html",
        records=records,
        record_count=len(records),
        search=search_query,
        selected_crop=crop_filter,
        selected_soil=soil_filter,
        selected_season=season_filter,
        crops=crop_options,
        soils=soil_options,
        seasons=season_options,
        dataset_sources=dataset_sources,
        selected_dataset=source_dataset
    )

@app.route("/add-record", methods=["POST"])
def add_record():
    """
    Module 2: Add Agricultural Record (Manual Entry)
    """
    try:
        crop_type = request.form.get("crop_type")
        soil = request.form.get("soil", "Unknown")
        rainfall = request.form.get("rainfall")
        temperature = request.form.get("temperature")
        fertilizer = request.form.get("fertilizer")
        irrigation = request.form.get("irrigation", "Unknown")
        yield_value = request.form.get("yield_value")
        location = request.form.get("location", "Unknown")
        season = request.form.get("season", "Unknown")

        success, msg = add_agricultural_record(
            crop_type, soil, rainfall, temperature, fertilizer, 
            irrigation, yield_value, location, season, source_dataset="Manual Entry"
        )
        if success:
            flash(msg, "success")
        else:
            flash(msg, "danger")
    except Exception as e:
        flash(f"Error adding record: {str(e)}", "danger")

    return redirect(url_for("agricultural_data"))

@app.route("/import-external-dataset", methods=["POST"])
def import_external_dataset():
    """
    Module 2: Import External Dataset (CSV/XLSX) directly from Agricultural Data page
    """
    try:
        file = request.files.get("dataset_file")
        dataset_name = request.form.get("dataset_name", "").strip()
        missing_strategy = request.form.get("missing_strategy", "keep")

        if not file or file.filename == '':
            flash("Please select a valid CSV or XLSX dataset file to upload.", "danger")
            return redirect(url_for("agricultural_data"))

        filename = file.filename
        file_path = os.path.join(RAW_UPLOAD_DIR, filename)
        file.save(file_path)

        if not dataset_name:
            dataset_name = filename

        df_raw, row_count, col_count, headers = read_uploaded_file(file_path)
        auto_mappings = suggest_column_mappings(headers)
        
        clean_opts = {
            "remove_duplicates": True,
            "remove_empty_rows": True,
            "numeric_imputation": "drop_rows" if missing_strategy == "drop" else "keep_null",
            "text_imputation": "Unknown"
        }
        df_cleaned = clean_and_transform_dataset(df_raw, auto_mappings, options=clean_opts)

        val_report = validate_dataset(df_raw, auto_mappings)
        available_fields_str = ", ".join([k for k, v in auto_mappings.items() if v != "Not Available"])

        success, msg = import_records_to_db(
            df_cleaned, dataset_name, "External File Import", "", val_report["quality_score"], available_fields_str
        )

        if success:
            flash(f"Successfully imported {len(df_cleaned)} records from '{filename}' into database beside existing data!", "success")
        else:
            flash(msg, "danger")

    except Exception as e:
        flash(f"Import Error: {str(e)}", "danger")

    return redirect(url_for("agricultural_data"))

@app.route("/statistics")
def statistics():
    """
    Module 3: Statistical Analysis View
    """
    source_dataset = request.args.get("dataset", None)
    full_df = load_data(source_dataset=source_dataset)
    dataset_sources = get_imported_dataset_sources()

    if full_df.empty:
        return render_template(
            "statistics.html", 
            has_data=False,
            stats={}, 
            correlations=[],
            dataset_sources=dataset_sources,
            selected_dataset=source_dataset
        )

    stats = get_descriptive_stats(source_dataset=source_dataset)
    correlations = get_correlation_analysis(source_dataset=source_dataset)

    return render_template(
        "statistics.html", 
        has_data=True,
        stats=stats, 
        correlations=correlations,
        dataset_sources=dataset_sources,
        selected_dataset=source_dataset
    )

@app.route("/visualization")
def visualization():
    """
    Module 4: Crop Yield Visualization View
    """
    source_dataset = request.args.get("dataset", None)
    full_df = load_data(source_dataset=source_dataset)
    dataset_sources = get_imported_dataset_sources()

    if full_df.empty:
        return render_template(
            "visualization.html",
            has_data=False,
            chart_data={"crop_labels": [], "crop_yields": [], "has_rainfall": False, "rainfall_scatter": [], "has_temp": False, "temp_scatter": [], "has_fert": False, "fert_scatter": [], "has_irr": False, "irr_labels": [], "irr_yields": []},
            crops=["All"],
            selected_crop="All",
            dataset_sources=dataset_sources,
            selected_dataset=source_dataset
        )

    crop_options = ["All"] + sorted(full_df['crop_type'].dropna().unique().tolist()) if ('crop_type' in full_df and not full_df.empty) else ["All"]
    selected_crop = request.args.get("crop", "All")
    chart_payload = get_chart_data(crop_filter=selected_crop, source_dataset=source_dataset)

    return render_template(
        "visualization.html",
        has_data=True,
        chart_data=chart_payload,
        crops=crop_options,
        selected_crop=selected_crop,
        dataset_sources=dataset_sources,
        selected_dataset=source_dataset
    )

# =========================================================================
# NEW DATASET MANAGEMENT & IMPORT PIPELINE ROUTES
# =========================================================================

@app.route("/datasets")
def dataset_management():
    """
    Dataset Management Portal: Wizard for CSV/XLSX Upload, Column Mapping, Validation & Import
    """
    dataset_sources = get_imported_dataset_sources()
    return render_template("dataset_management.html", standard_fields=STANDARD_FIELDS, dataset_sources=dataset_sources, step=1)

@app.route("/upload-dataset", methods=["POST"])
def upload_dataset():
    """
    Step 1 -> Step 2: Upload Raw File (CSV/XLSX), auto-map columns, validate quality, clean data, and show preview.
    """
    try:
        file = request.files.get("dataset_file")
        dataset_name = request.form.get("dataset_name", "").strip()
        source_name = request.form.get("source_name", "Public Source").strip()
        source_url = request.form.get("source_url", "").strip()

        if not file or file.filename == '':
            flash("Please select a valid CSV or XLSX file to upload.", "danger")
            return redirect(url_for("dataset_management"))

        filename = file.filename
        file_path = os.path.join(RAW_UPLOAD_DIR, filename)
        file.save(file_path)

        if not dataset_name:
            dataset_name = filename

        # 1. Read file and auto-detect columns
        df_raw, row_count, col_count, headers = read_uploaded_file(file_path)
        auto_mappings = suggest_column_mappings(headers)

        # 2. Validation Report
        val_report = validate_dataset(df_raw, auto_mappings)
        if val_report.get("errors"):
            for err in val_report["errors"]:
                flash(f"Validation Note: {err}", "warning")

        # 3. Automatic Data Cleaning
        clean_options = {
            "remove_duplicates": True,
            "remove_empty_rows": True,
            "numeric_imputation": "keep_null",
            "text_imputation": "Unknown"
        }
        df_cleaned = clean_and_transform_dataset(df_raw, auto_mappings, options=clean_options)

        if len(df_cleaned) == 0:
            flash(f"Warning: No valid records could be extracted from '{filename}'. Please ensure the file contains crop names and yield values.", "danger")
            return redirect(url_for("dataset_management"))

        # Save temporary cleaned CSV for preview confirmation
        cleaned_temp_path = os.path.join(RAW_UPLOAD_DIR, "temp_cleaned.csv")
        df_cleaned.to_csv(cleaned_temp_path, index=False)

        preview_rows = df_cleaned.head(20).to_dict(orient="records")
        available_fields = [k for k, v in auto_mappings.items() if v and v != "Not Available"]
        available_fields_str = ", ".join(available_fields)

        dataset_sources = get_imported_dataset_sources()

        return render_template(
            "dataset_management.html",
            step=2,
            filename=filename,
            filepath=file_path,
            cleaned_temp_path=cleaned_temp_path,
            dataset_name=dataset_name,
            source_name=source_name,
            source_url=source_url,
            row_count=row_count,
            col_count=col_count,
            val_report=val_report,
            preview_rows=preview_rows,
            total_cleaned_records=len(df_cleaned),
            available_fields_str=available_fields_str,
            auto_mappings=auto_mappings,
            dataset_sources=dataset_sources
        )
    except Exception as e:
        flash(f"Upload Error: {str(e)}", "danger")
        return redirect(url_for("dataset_management"))

@app.route("/confirm-import", methods=["POST"])
def confirm_import():
    """
    Step 2 -> Confirm final import of cleaned records into SQLite / MySQL database.
    """
    try:
        cleaned_temp_path = request.form.get("cleaned_temp_path")
        dataset_name = request.form.get("dataset_name")
        source_name = request.form.get("source_name")
        source_url = request.form.get("source_url")
        quality_score = float(request.form.get("quality_score", 100.0))
        available_fields_str = request.form.get("available_fields_str", "")

        if not cleaned_temp_path or not os.path.exists(cleaned_temp_path):
            flash("Import session expired. Please upload your dataset file again.", "danger")
            return redirect(url_for("dataset_management"))

        df_cleaned = pd.read_csv(cleaned_temp_path)
        if len(df_cleaned) == 0:
            flash("Cannot import: dataset contains 0 valid records.", "danger")
            return redirect(url_for("dataset_management"))

        success, msg = import_records_to_db(
            df_cleaned, dataset_name, source_name, source_url, quality_score, available_fields_str
        )

        if success:
            flash(f"Success! {len(df_cleaned)} records imported from '{dataset_name}'.", "success")
            return redirect(url_for("agricultural_data"))
        else:
            flash(msg, "danger")
            return redirect(url_for("dataset_management"))
    except Exception as e:
        flash(f"Import Failure: {str(e)}", "danger")
        return redirect(url_for("dataset_management"))



# =========================================================================
# MODULE 5: RULE-BASED ADVISORY RECOMMENDATION ENGINE
# =========================================================================

@app.route("/advisory", methods=["GET", "POST"])
def advisory():
    """
    Module 5: Rule-Based Crop Yield Advisory & Stress Diagnostic System
    """
    source_dataset = request.args.get("dataset", None)
    full_df = load_data(source_dataset=source_dataset)
    dataset_sources = get_imported_dataset_sources()

    if full_df.empty:
        return render_template(
            "advisory.html",
            has_data=False,
            advisory=None,
            dataset_advisories=[],
            crops=[],
            soils=[],
            irrigations=[],
            seasons=[],
            dataset_sources=dataset_sources,
            selected_dataset=source_dataset
        )

    # Available options from dataset
    crop_options = sorted(full_df['crop_type'].dropna().unique().tolist()) if ('crop_type' in full_df and not full_df.empty) else []
    soil_options = sorted(full_df['soil'].dropna().unique().tolist()) if ('soil' in full_df and not full_df.empty) else ["Alluvial", "Black", "Red", "Clay", "Loam"]
    irr_options = [i for i in sorted(full_df['irrigation'].dropna().unique().tolist()) if i != 'Unknown'] if ('irrigation' in full_df and not full_df.empty) else ["Canal", "Drip", "Tube Well", "Rainfed"]
    season_options = sorted(full_df['season'].dropna().unique().tolist()) if ('season' in full_df and not full_df.empty) else ["Kharif", "Rabi", "Zaid"]

    if not irr_options:
        irr_options = ["Canal", "Drip", "Tube Well", "Rainfed"]

    # Parameter extraction
    if request.method == "POST":
        sel_crop = request.form.get("crop_type", crop_options[0] if crop_options else "Rice")
        sel_soil = request.form.get("soil", "Alluvial")
        sel_rainfall = request.form.get("rainfall")
        sel_temp = request.form.get("temperature")
        sel_fert = request.form.get("fertilizer")
        sel_irr = request.form.get("irrigation", "Canal")
        sel_season = request.form.get("season", "Kharif")
        sel_loc = request.form.get("location", "Punjab")
    else:
        sel_crop = request.args.get("crop", crop_options[0] if crop_options else "Rice")
        # Pre-fill defaults from dataset median for this crop if available
        crop_subset = full_df[full_df['crop_type'] == sel_crop] if ('crop_type' in full_df and not full_df.empty) else pd.DataFrame()
        
        sel_soil = crop_subset['soil'].mode().iloc[0] if ('soil' in crop_subset and not crop_subset['soil'].empty) else "Alluvial"
        sel_rainfall = round(float(crop_subset['rainfall'].median()), 1) if ('rainfall' in crop_subset and crop_subset['rainfall'].notnull().any()) else 850.0
        sel_temp = round(float(crop_subset['temperature'].median()), 1) if ('temperature' in crop_subset and crop_subset['temperature'].notnull().any()) else 26.5
        sel_fert = round(float(crop_subset['fertilizer'].median()), 1) if ('fertilizer' in crop_subset and crop_subset['fertilizer'].notnull().any()) else 120.0
        sel_irr = crop_subset['irrigation'].mode().iloc[0] if ('irrigation' in crop_subset and not crop_subset['irrigation'].empty and crop_subset['irrigation'].mode().iloc[0] != 'Unknown') else "Canal"
        sel_season = crop_subset['season'].mode().iloc[0] if ('season' in crop_subset and not crop_subset['season'].empty) else "Kharif"
        sel_loc = crop_subset['location'].mode().iloc[0] if ('location' in crop_subset and not crop_subset['location'].empty) else "Punjab"

    advisory_result = analyze_crop_advisory(
        crop_type=sel_crop,
        soil=sel_soil,
        rainfall=sel_rainfall,
        temperature=sel_temp,
        fertilizer=sel_fert,
        irrigation=sel_irr,
        season=sel_season,
        location=sel_loc,
        source_dataset=source_dataset
    )

    dataset_advisories = get_dataset_wide_advisories(source_dataset=source_dataset)

    return render_template(
        "advisory.html",
        has_data=True,
        advisory=advisory_result,
        dataset_advisories=dataset_advisories,
        crops=crop_options,
        soils=soil_options,
        irrigations=irr_options,
        seasons=season_options,
        selected_crop=sel_crop,
        selected_soil=sel_soil,
        selected_rainfall=sel_rainfall,
        selected_temperature=sel_temp,
        selected_fertilizer=sel_fert,
        selected_irrigation=sel_irr,
        selected_season=sel_season,
        selected_location=sel_loc,
        dataset_sources=dataset_sources,
        selected_dataset=source_dataset
    )

# =========================================================================
# MODULE 5: CROP YIELD ANALYSIS
# =========================================================================

@app.route("/crop-analysis")
def crop_analysis():
    """
    Module 5: Crop Yield Analysis
    Analyzes which crops yield the best under which conditions using
    Pandas group-by aggregations — no ML needed.
    """
    source_dataset = request.args.get("dataset", None)
    full_df = load_data(source_dataset=source_dataset)
    dataset_sources = get_imported_dataset_sources()

    if full_df.empty:
        return render_template(
            "crop_analysis.html",
            has_data=False,
            crop_yield_table=[],
            soil_yield_table=[],
            season_yield_table=[],
            irrigation_yield_table=[],
            top_crop="N/A",
            top_soil="N/A",
            top_season="N/A",
            top_irrigation="N/A",
            dataset_sources=dataset_sources,
            selected_dataset=source_dataset
        )

    # --- Crop Yield Rankings ---
    crop_yield_table = []
    if 'crop_type' in full_df and 'yield_value' in full_df:
        crop_group = full_df.groupby('crop_type')['yield_value'].agg(['mean', 'median', 'min', 'max', 'count']).reset_index()
        crop_group.columns = ['crop_type', 'avg_yield', 'median_yield', 'min_yield', 'max_yield', 'records']
        crop_group = crop_group.sort_values('avg_yield', ascending=False)
        for _, row in crop_group.iterrows():
            crop_yield_table.append({
                'crop_type': row['crop_type'],
                'avg_yield': round(row['avg_yield'], 2),
                'median_yield': round(row['median_yield'], 2),
                'min_yield': round(row['min_yield'], 2),
                'max_yield': round(row['max_yield'], 2),
                'records': int(row['records'])
            })
    top_crop = crop_yield_table[0]['crop_type'] if crop_yield_table else "N/A"

    # --- Yield by Soil Type ---
    soil_yield_table = []
    if 'soil' in full_df and 'yield_value' in full_df:
        soil_group = full_df.groupby('soil')['yield_value'].agg(['mean', 'median', 'count']).reset_index()
        soil_group.columns = ['soil', 'avg_yield', 'median_yield', 'records']
        soil_group = soil_group.sort_values('avg_yield', ascending=False)
        for _, row in soil_group.iterrows():
            soil_yield_table.append({
                'soil': row['soil'],
                'avg_yield': round(row['avg_yield'], 2),
                'median_yield': round(row['median_yield'], 2),
                'records': int(row['records'])
            })
    top_soil = soil_yield_table[0]['soil'] if soil_yield_table else "N/A"

    # --- Yield by Season ---
    season_yield_table = []
    if 'season' in full_df and 'yield_value' in full_df:
        season_group = full_df.groupby('season')['yield_value'].agg(['mean', 'median', 'count']).reset_index()
        season_group.columns = ['season', 'avg_yield', 'median_yield', 'records']
        season_group = season_group.sort_values('avg_yield', ascending=False)
        for _, row in season_group.iterrows():
            season_yield_table.append({
                'season': row['season'],
                'avg_yield': round(row['avg_yield'], 2),
                'median_yield': round(row['median_yield'], 2),
                'records': int(row['records'])
            })
    top_season = season_yield_table[0]['season'] if season_yield_table else "N/A"

    # --- Yield by Irrigation Method ---
    irrigation_yield_table = []
    if 'irrigation' in full_df and 'yield_value' in full_df:
        irr_group = full_df.groupby('irrigation')['yield_value'].agg(['mean', 'median', 'count']).reset_index()
        irr_group.columns = ['irrigation', 'avg_yield', 'median_yield', 'records']
        irr_group = irr_group.sort_values('avg_yield', ascending=False)
        for _, row in irr_group.iterrows():
            irrigation_yield_table.append({
                'irrigation': row['irrigation'],
                'avg_yield': round(row['avg_yield'], 2),
                'median_yield': round(row['median_yield'], 2),
                'records': int(row['records'])
            })
    top_irrigation = irrigation_yield_table[0]['irrigation'] if irrigation_yield_table else "N/A"

    return render_template(
        "crop_analysis.html",
        has_data=True,
        crop_yield_table=crop_yield_table,
        soil_yield_table=soil_yield_table,
        season_yield_table=season_yield_table,
        irrigation_yield_table=irrigation_yield_table,
        top_crop=top_crop,
        top_soil=top_soil,
        top_season=top_season,
        top_irrigation=top_irrigation,
        dataset_sources=dataset_sources,
        selected_dataset=source_dataset
    )


@app.route("/about")
def about():
    """
    About Project Page
    """
    return render_template("about.html")

if __name__ == "__main__":
    print("=========================================================")
    print(" CROP YIELD ADVISORY ANALYTICS - FLASK DASHBOARD ")
    print(" Running at: http://127.0.0.1:5000/")
    print("=========================================================")
    app.run(debug=True, port=5000)
