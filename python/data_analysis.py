"""
Data Analysis Helper Functions
Handles dataset loading, filtering, record insertion, dashboard metrics, 
and chart aggregations with graceful missing-field handling.
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.db_config import get_db_connection

def load_data(source_dataset=None):
    """
    Loads agricultural data from database into a pandas DataFrame.
    """
    conn, is_mysql = get_db_connection()
    try:
        if source_dataset and source_dataset != 'All':
            if is_mysql:
                query = "SELECT * FROM agricultural_data WHERE source_dataset = %s ORDER BY id DESC"
                df = pd.read_sql(query, conn, params=(source_dataset,))
            else:
                query = "SELECT * FROM agricultural_data WHERE source_dataset = ? ORDER BY id DESC"
                df = pd.read_sql_query(query, conn, params=(source_dataset,))
        else:
            query = "SELECT * FROM agricultural_data ORDER BY id DESC"
            df = pd.read_sql(query, conn)
    except Exception:
        df = pd.DataFrame(columns=['id', 'crop_type', 'soil', 'rainfall', 'temperature', 'fertilizer', 'irrigation', 'yield_value', 'location', 'season', 'source_dataset'])
    finally:
        if not is_mysql and hasattr(conn, 'close'):
            conn.close()
            
    return df

def filter_records(search="", crop=None, soil=None, season=None, source_dataset=None):
    """
    Filters agricultural records based on user search query and dropdown selections.
    """
    df = load_data(source_dataset=source_dataset)
    
    if df.empty:
        return df

    if search:
        search = search.lower().strip()
        mask = df['crop_type'].astype(str).str.lower().str.contains(search)
        if 'soil' in df:
            mask = mask | df['soil'].astype(str).str.lower().str.contains(search)
        if 'location' in df:
            mask = mask | df['location'].astype(str).str.lower().str.contains(search)
        if 'season' in df:
            mask = mask | df['season'].astype(str).str.lower().str.contains(search)
        df = df[mask]
        
    if crop and crop != 'All' and 'crop_type' in df:
        df = df[df['crop_type'] == crop]
        
    if soil and soil != 'All' and 'soil' in df:
        df = df[df['soil'] == soil]
        
    if season and season != 'All' and 'season' in df:
        df = df[df['season'] == season]
        
    return df

def add_agricultural_record(crop_type, soil, rainfall, temperature, fertilizer, irrigation, yield_value, location, season, source_dataset="Manual Entry"):
    """
    Inserts a single manual agricultural record into the database.
    """
    conn, is_mysql = get_db_connection()
    try:
        cursor = conn.cursor()
        rain_val = float(rainfall) if rainfall and rainfall != '' else None
        temp_val = float(temperature) if temperature and temperature != '' else None
        fert_val = float(fertilizer) if fertilizer and fertilizer != '' else None

        if is_mysql:
            sql = """
                INSERT INTO agricultural_data
                (crop_type, soil, rainfall, temperature, fertilizer, irrigation, yield_value, location, season, source_dataset)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (crop_type, soil, rain_val, temp_val, fert_val, irrigation, float(yield_value), location, season, source_dataset))
        else:
            sql = """
                INSERT INTO agricultural_data 
                (crop_type, soil, rainfall, temperature, fertilizer, irrigation, yield_value, location, season, source_dataset)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(sql, (crop_type, soil, rain_val, temp_val, fert_val, irrigation, float(yield_value), location, season, source_dataset))
            
        conn.commit()
        return True, "Record added successfully to database."
    except Exception as e:
        return False, f"Failed to add record: {str(e)}"
    finally:
        if hasattr(conn, 'close'):
            conn.close()

def get_dashboard_summary(source_dataset=None):
    """
    Calculates key metrics for Dashboard cards with optional field availability checks.
    """
    df = load_data(source_dataset=source_dataset)
    _, is_mysql = get_db_connection()

    if df.empty:
        return {
            "total_records": 0,
            "total_crops": 0,
            "avg_yield": 0.0,
            "avg_rainfall": "N/A",
            "db_mode": "MySQL Connected" if is_mysql else "SQLite/CSV Mode",
            "active_dataset_name": source_dataset if source_dataset else "All Imported Datasets",
            "has_rainfall": False,
            "has_temperature": False,
            "has_fertilizer": False
        }
        
    avg_rainfall = round(float(df['rainfall'].dropna().mean()), 1) if ('rainfall' in df and df['rainfall'].notnull().any()) else "N/A"
    avg_yield = round(float(df['yield_value'].dropna().mean()), 2) if ('yield_value' in df and df['yield_value'].notnull().any()) else 0.0

    return {
        "total_records": int(len(df)),
        "total_crops": int(df['crop_type'].nunique()) if 'crop_type' in df else 0,
        "avg_yield": avg_yield,
        "avg_rainfall": avg_rainfall,
        "db_mode": "MySQL Connected" if is_mysql else "SQLite/CSV Mode",
        "active_dataset_name": source_dataset if source_dataset else "All Combined Datasets",
        "has_rainfall": bool('rainfall' in df and df['rainfall'].notnull().any()),
        "has_temperature": bool('temperature' in df and df['temperature'].notnull().any()),
        "has_fertilizer": bool('fertilizer' in df and df['fertilizer'].notnull().any()),
        "has_irrigation": bool('irrigation' in df and df['irrigation'].notnull().any() and (df['irrigation'] != 'Unknown').any())
    }

def get_chart_data(crop_filter=None, source_dataset=None):
    """
    Prepares JSON dataset structures for Chart.js dashboards with missing-field safety.
    """
    df = load_data(source_dataset=source_dataset)
    if df.empty:
        return {
            "crop_labels": [], "crop_yields": [],
            "has_rainfall": False, "rainfall_scatter": [],
            "has_temp": False, "temp_scatter": [],
            "has_fert": False, "fert_scatter": [],
            "has_irr": False, "irr_labels": [], "irr_yields": []
        }

    if crop_filter and crop_filter != 'All' and 'crop_type' in df:
        df = df[df['crop_type'] == crop_filter]

    # 1. Crop Type vs Average Yield (sorted descending so chart shows highest first)
    crop_labels, crop_yields = [], []
    if 'crop_type' in df and 'yield_value' in df:
        crop_yield_df = df.groupby('crop_type')['yield_value'].mean().reset_index()
        crop_yield_df = crop_yield_df.sort_values('yield_value', ascending=False)
        crop_labels = crop_yield_df['crop_type'].tolist()
        crop_yields = [round(float(val), 2) for val in crop_yield_df['yield_value'].tolist()]

    # 2. Rainfall vs Yield Scatter
    has_rainfall = bool('rainfall' in df and df['rainfall'].notnull().any())
    rainfall_scatter = []
    if has_rainfall:
        valid_rain = df.dropna(subset=['rainfall', 'yield_value'])
        rainfall_scatter = [{"x": round(float(row['rainfall']), 1), "y": round(float(row['yield_value']), 2)} for _, row in valid_rain.iterrows()]

    # 3. Temp vs Yield Scatter
    has_temp = bool('temperature' in df and df['temperature'].notnull().any())
    temp_scatter = []
    if has_temp:
        valid_temp = df.dropna(subset=['temperature', 'yield_value'])
        temp_scatter = [{"x": round(float(row['temperature']), 1), "y": round(float(row['yield_value']), 2)} for _, row in valid_temp.iterrows()]

    # 4. Fertilizer vs Yield Scatter
    has_fert = bool('fertilizer' in df and df['fertilizer'].notnull().any())
    fert_scatter = []
    if has_fert:
        valid_fert = df.dropna(subset=['fertilizer', 'yield_value'])
        fert_scatter = [{"x": round(float(row['fertilizer']), 1), "y": round(float(row['yield_value']), 2)} for _, row in valid_fert.iterrows()]

    # 5. Irrigation vs Avg Yield
    has_irr = bool('irrigation' in df and df['irrigation'].notnull().any() and (df['irrigation'] != 'Unknown').any())
    irr_labels, irr_yields = [], []
    if has_irr:
        irr_df = df[df['irrigation'] != 'Unknown'].groupby('irrigation')['yield_value'].mean().reset_index()
        irr_labels = irr_df['irrigation'].tolist()
        irr_yields = [round(float(val), 2) for val in irr_df['yield_value'].tolist()]

    return {
        "crop_labels": crop_labels,
        "crop_yields": crop_yields,
        "has_rainfall": has_rainfall,
        "rainfall_scatter": rainfall_scatter,
        "has_temp": has_temp,
        "temp_scatter": temp_scatter,
        "has_fert": has_fert,
        "fert_scatter": fert_scatter,
        "has_irr": has_irr,
        "irr_labels": irr_labels,
        "irr_yields": irr_yields
    }
