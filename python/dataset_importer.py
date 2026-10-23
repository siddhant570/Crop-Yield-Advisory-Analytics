"""
Dataset Importer Module
Handles file ingestion (.csv, .xlsx, .xls), auto-column matching, 
and batch insertion into MySQL / SQLite fallback with provenance metadata.
"""

import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.db_config import get_db_connection

STANDARD_FIELDS = [
    {"key": "crop_type", "label": "Crop Type (Required)", "required": True},
    {"key": "yield_value", "label": "Crop Yield / Production (Required)", "required": True},
    {"key": "rainfall", "label": "Rainfall (mm)", "required": False},
    {"key": "temperature", "label": "Temperature (°C)", "required": False},
    {"key": "fertilizer", "label": "Fertilizer (kg/ha)", "required": False},
    {"key": "soil", "label": "Soil Type", "required": False},
    {"key": "irrigation", "label": "Irrigation Method", "required": False},
    {"key": "location", "label": "Location / State", "required": False},
    {"key": "season", "label": "Season", "required": False}
]

COLUMN_SYNONYMS = {
    "crop_type": ["crop", "crop_type", "crop type", "crop name", "crop_name", "commodity", "crop_variety"],
    "yield_value": ["yield", "crop yield", "yield_value", "production", "yield per hectare", "yield_t_ha", "yield(t/ha)", "output"],
    "rainfall": ["rainfall", "annual rainfall", "annual_rainfall", "rain", "precipitation", "precip", "total_rainfall"],
    "temperature": ["temperature", "avg temperature", "avg_temp", "temp", "average temperature", "temperature_c"],
    "fertilizer": ["fertilizer", "fertilizer used", "fertilizer_used", "fertilizer amount", "fertilizer_kg_ha", "npk_usage"],
    "soil": ["soil", "soil_type", "soil type", "soil quality", "soil_category"],
    "irrigation": ["irrigation", "irrigation method", "irrigation_type", "water_source"],
    "location": ["location", "state", "region", "district", "province"],
    "season": ["season", "cropping season", "crop_season", "weather_season"]
}

def read_uploaded_file(filepath):
    """
    Reads a CSV, XLSX, or XLS file and returns (DataFrame, row_count, col_count, column_list).
    Implements multi-engine fallback for binary XLS (xlrd), XLSX (openpyxl),
    HTML table exports, and text-based formats.
    """
    ext = os.path.splitext(filepath)[1].lower()
    df = None
    last_error = None

    if ext == '.csv':
        for encoding in ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
            try:
                df = pd.read_csv(filepath, encoding=encoding)
                break
            except Exception as e:
                last_error = e

    elif ext in ['.xlsx', '.xls']:
        # 1. Try standard pandas read_excel
        try:
            df = pd.read_excel(filepath)
        except Exception as e:
            last_error = e

        # 2. Try xlrd explicitly for .xls legacy format
        if df is None:
            try:
                df = pd.read_excel(filepath, engine='xlrd')
            except Exception as e:
                last_error = e

        # 3. Try openpyxl (in case modern XML/XLSX file is named with .xls)
        if df is None:
            try:
                df = pd.read_excel(filepath, engine='openpyxl')
            except Exception as e:
                last_error = e

        # 4. Try HTML table (many portals export HTML tables with .xls extension)
        if df is None:
            try:
                tables = pd.read_html(filepath)
                if tables:
                    df = max(tables, key=len)
            except Exception as e:
                last_error = e

        # 5. Try CSV/TSV auto-detect parser (in case text data was saved as .xls)
        if df is None:
            try:
                df = pd.read_csv(filepath, sep=None, engine='python')
            except Exception as e:
                last_error = e
    else:
        raise ValueError(f"Unsupported file format: '{ext}'. Supported formats: CSV, XLSX, XLS")

    if df is None:
        raise ValueError(f"Unable to read file: {last_error if last_error else 'corrupted or unsupported format'}")

    # Clean headers and drop completely empty rows/columns
    df = df.dropna(how='all')
    if isinstance(df.columns, pd.MultiIndex):
        new_cols = []
        for col in df.columns:
            if isinstance(col, tuple):
                parts = []
                for p in col:
                    p_str = str(p).strip()
                    if p_str and not p_str.startswith('Unnamed:') and p_str not in parts:
                        parts.append(p_str)
                new_cols.append(" - ".join(parts) if parts else "Column")
            else:
                new_cols.append(str(col).strip())
        df.columns = new_cols
    else:
        df.columns = [str(col).strip() for col in df.columns]

    return df, len(df), len(df.columns), df.columns.tolist()

def suggest_column_mappings(df_columns):
    """
    Suggests standard field mappings for uploaded dataset column names.
    Returns dict: { standard_field_key: matched_uploaded_column_or_None }
    """
    suggestions = {}
    normalized_cols = {col.strip().lower(): col for col in df_columns}

    for field_key, synonyms in COLUMN_SYNONYMS.items():
        matched_col = None
        # 1. Exact match
        for syn in synonyms:
            if syn in normalized_cols:
                matched_col = normalized_cols[syn]
                break
        
        # 2. Substring match
        if not matched_col:
            for syn in synonyms:
                for norm_key, orig_col in normalized_cols.items():
                    if syn in norm_key:
                        matched_col = orig_col
                        break
                if matched_col:
                    break

        suggestions[field_key] = matched_col if matched_col else "Not Available"

    return suggestions

def import_records_to_db(df_mapped, dataset_name, source_name, source_url, quality_score, available_fields_str):
    """
    Inserts clean mapped records into agricultural_data and logs metadata into dataset_sources.
    """
    conn, is_mysql = get_db_connection()
    try:
        cursor = conn.cursor()
        
        # 1. Log metadata in dataset_sources
        if is_mysql:
            sql_ds = """
                INSERT INTO dataset_sources 
                (dataset_name, source_name, source_url, record_count, available_fields, quality_score, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql_ds, (dataset_name, source_name, source_url, len(df_mapped), available_fields_str, float(quality_score), 'Active'))
        else:
            sql_ds = """
                INSERT INTO dataset_sources 
                (dataset_name, source_name, source_url, record_count, available_fields, quality_score, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql_ds, (dataset_name, source_name, source_url, len(df_mapped), available_fields_str, float(quality_score), 'Active'))
            
        conn.commit()

        # 2. Insert records into agricultural_data
        records = df_mapped.to_dict(orient='records')
        for r in records:
            crop_type = str(r.get('crop_type', 'Unknown'))
            soil = str(r.get('soil', 'Unknown')) if pd.notnull(r.get('soil')) else 'Unknown'
            rainfall = float(r['rainfall']) if pd.notnull(r.get('rainfall')) and r.get('rainfall') != '' else None
            temperature = float(r['temperature']) if pd.notnull(r.get('temperature')) and r.get('temperature') != '' else None
            fertilizer = float(r['fertilizer']) if pd.notnull(r.get('fertilizer')) and r.get('fertilizer') != '' else None
            irrigation = str(r.get('irrigation', 'Unknown')) if pd.notnull(r.get('irrigation')) else 'Unknown'
            yield_value = float(r['yield_value'])
            location = str(r.get('location', 'Unknown')) if pd.notnull(r.get('location')) else 'Unknown'
            season = str(r.get('season', 'Unknown')) if pd.notnull(r.get('season')) else 'Unknown'

            if is_mysql:
                sql_rec = """
                    INSERT INTO agricultural_data 
                    (crop_type, soil, rainfall, temperature, fertilizer, irrigation, yield_value, location, season, source_dataset)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql_rec, (crop_type, soil, rainfall, temperature, fertilizer, irrigation, yield_value, location, season, dataset_name))
            else:
                sql_rec = """
                    INSERT INTO agricultural_data 
                    (crop_type, soil, rainfall, temperature, fertilizer, irrigation, yield_value, location, season, source_dataset)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(sql_rec, (crop_type, soil, rainfall, temperature, fertilizer, irrigation, yield_value, location, season, dataset_name))

        conn.commit()
        return True, f"Successfully imported {len(df_mapped)} records into database from '{dataset_name}'."
    except Exception as e:
        return False, f"Database import failed: {str(e)}"
    finally:
        if hasattr(conn, 'close'):
            conn.close()

def get_imported_dataset_sources():
    """
    Fetches the catalog of imported dataset sources.
    """
    conn, is_mysql = get_db_connection()
    try:
        if is_mysql:
            df = pd.read_sql("SELECT * FROM dataset_sources ORDER BY id DESC", conn)
        else:
            df = pd.read_sql_query("SELECT * FROM dataset_sources ORDER BY id DESC", conn)
        return df.to_dict(orient='records')
    except Exception:
        return []
    finally:
        if not is_mysql and hasattr(conn, 'close'):
            conn.close()
