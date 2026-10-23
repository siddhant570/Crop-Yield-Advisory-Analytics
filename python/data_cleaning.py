"""
Data Cleaning Module
Applies transparent Pandas cleaning operations (whitespace trimming, numerical coercion,
unit extraction, duplicate removal, missing value imputation / row dropping) before database import.
"""

import re
import pandas as pd
import numpy as np


def extract_numeric(val, field=None):
    """
    Extracts a clean floating-point number from strings that may contain
    measurement units (e.g. '13.93 tonnes/ha', '11.2 quintals/ha (1.12 t/ha)',
    '98.6 mm', '23.4°C', '30:60:30 NPK kg/ha').
    """
    if pd.isnull(val):
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)

    val_str = str(val).strip()
    if not val_str or val_str.lower() in ('nan', 'none', 'null', 'unknown', 'n/a', '-', ''):
        return np.nan

    # 1. Specialized handling for yield_value:
    if field == 'yield_value':
        # E.g. "11.2 quintals/ha (1.12 t/ha)" -> extract the t/ha inside parentheses
        match_paren = re.search(r'\(\s*([\d.]+)\s*t(?:onnes?)?/ha\s*\)', val_str, re.I)
        if match_paren:
            try:
                return float(match_paren.group(1))
            except ValueError:
                pass

        # E.g. "13.93 tonnes/ha" or "4.2 t/ha"
        match_t = re.search(r'([\d.]+)\s*t(?:onnes?)?(?:/ha)?', val_str, re.I)
        if match_t:
            try:
                return float(match_t.group(1))
            except ValueError:
                pass

        # E.g. "15 quintals/ha" (1 quintal = 0.1 tonnes)
        match_q = re.search(r'([\d.]+)\s*q(?:uintals?)?(?:/ha)?', val_str, re.I)
        if match_q:
            try:
                return round(float(match_q.group(1)) * 0.1, 2)
            except ValueError:
                pass

    # 2. Specialized handling for fertilizer:
    if field == 'fertilizer':
        # E.g. "30:60:30 NPK kg/ha" or "NPK 19:48:23 kg/ha" -> sum N+P+K components
        npk_match = re.search(r'(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)', val_str)
        if npk_match:
            try:
                return round(float(npk_match.group(1)) + float(npk_match.group(2)) + float(npk_match.group(3)), 1)
            except ValueError:
                pass

    # 3. General numeric extraction for rainfall, temperature, fertilizer, yield:
    # Strip degree symbol, celsius, mm, kg/ha, quotes, etc.
    cleaned_str = re.sub(r'[°º\xc2\xa0CFfMm%]', '', val_str).strip()
    m = re.search(r'[-+]?\d*\.?\d+', cleaned_str)
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            return np.nan

    return np.nan


def clean_and_transform_dataset(df_raw, mapping, options=None):
    """
    Transforms raw DataFrame into standard schema using column mapping and user cleaning options.
    
    Args:
        df_raw: Raw pandas DataFrame
        mapping: Dict { standard_field_key: uploaded_column_name }
        options: Dict with flags:
            - remove_duplicates (bool)
            - remove_empty_rows (bool)
            - numeric_imputation (str: 'keep_null', 'drop_rows', 'mean')
            - text_imputation (str: 'Unknown', 'drop_rows')
            
    Returns:
        Cleaned pandas DataFrame matching standard schema columns.
    """
    if options is None:
        options = {
            "remove_duplicates": True,
            "remove_empty_rows": True,
            "numeric_imputation": "keep_null",
            "text_imputation": "Unknown"
        }

    cleaned_df = pd.DataFrame()

    # 1. Map columns into standard names
    for std_field, col_name in mapping.items():
        if col_name and col_name != "Not Available" and col_name in df_raw.columns:
            series = df_raw[col_name]
            # Trim whitespace for string columns
            if series.dtype == 'object':
                series = series.astype(str).str.strip()
            cleaned_df[std_field] = series
        else:
            cleaned_df[std_field] = np.nan

    # Auto-infer crop_type if omitted or if crop is embedded in header
    detected_crop = None
    known_crops = ["Rice", "Wheat", "Maize", "Cotton", "Sugarcane", "Pulses", "Jowar", "Bajra", "Soybean", "Groundnut", "Barley", "Mustard", "Sunflower", "Pomegranate", "Gram", "Onion"]
    for c in list(mapping.values()) + list(df_raw.columns):
        if c and c != "Not Available":
            for crop in known_crops:
                if crop.lower() in str(c).lower():
                    detected_crop = crop
                    break
            if detected_crop:
                break

    # If crop_type is missing or numeric (e.g. area selected), replace with detected crop name
    if 'crop_type' not in cleaned_df or cleaned_df['crop_type'].isnull().all():
        cleaned_df['crop_type'] = detected_crop if detected_crop else "Unknown"
    else:
        # Check if mapped values are all numeric (user mapped a numerical column to crop_type)
        is_num = pd.to_numeric(cleaned_df['crop_type'], errors='coerce').notnull().all()
        if is_num and detected_crop:
            cleaned_df['crop_type'] = detected_crop

    # 2. Coerce numeric columns using robust unit-aware extraction
    numeric_fields = ['rainfall', 'temperature', 'fertilizer', 'yield_value']
    for field in numeric_fields:
        if field in cleaned_df:
            cleaned_df[field] = cleaned_df[field].apply(lambda x: extract_numeric(x, field))

    # 3. Handle duplicates
    if options.get("remove_duplicates"):
        cleaned_df = cleaned_df.drop_duplicates().reset_index(drop=True)

    # 4. Remove empty rows (rows where required fields are missing)
    if options.get("remove_empty_rows"):
        cleaned_df = cleaned_df.dropna(subset=['crop_type', 'yield_value']).reset_index(drop=True)

    # 5. Handle missing numerical values
    num_impute = options.get("numeric_imputation", "keep_null")
    if num_impute == "drop_rows":
        cleaned_df = cleaned_df.dropna(subset=numeric_fields).reset_index(drop=True)
    elif num_impute == "mean":
        for field in numeric_fields:
            if field in cleaned_df and cleaned_df[field].isnull().any():
                mean_val = cleaned_df[field].mean()
                if pd.notnull(mean_val):
                    cleaned_df[field] = cleaned_df[field].fillna(round(mean_val, 2))

    # 6. Handle missing categorical text values
    text_fields = ['soil', 'irrigation', 'location', 'season']
    text_impute = options.get("text_imputation", "Unknown")
    for field in text_fields:
        if field in cleaned_df:
            if text_impute == "drop_rows":
                cleaned_df = cleaned_df.dropna(subset=[field]).reset_index(drop=True)
            else:
                cleaned_df[field] = cleaned_df[field].fillna("Unknown").replace(['nan', 'None', '', 'NaN'], "Unknown")

    return cleaned_df
