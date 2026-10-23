"""
Data Validator Module
Validates uploaded agricultural dataset against data quality rules, missing values, duplicates,
and numerical range boundaries to compute transparent Dataset Quality Scores.
"""

import pandas as pd
import numpy as np

def validate_dataset(df, mapping):
    """
    Validates uploaded dataset according to user's column mapping.
    
    Args:
        df: Raw pandas DataFrame
        mapping: Dict { standard_field_key: uploaded_column_name_or_'Not Available' }
        
    Returns:
        Validation report dict with metrics, invalid row details, and Dataset Quality Score.
    """
    total_rows = len(df)
    if total_rows == 0:
        return {
            "total_rows": 0,
            "valid_rows": 0,
            "missing_value_rows": 0,
            "duplicate_rows": 0,
            "invalid_numeric_rows": 0,
            "quality_score": 0.0,
            "quality_status": "EMPTY DATASET",
            "quality_badge_class": "badge-neutral",
            "errors": ["Uploaded dataset contains 0 rows."]
        }

    # Extract mapped columns
    mapped_df = pd.DataFrame()
    for std_field, col_name in mapping.items():
        if col_name and col_name != "Not Available" and col_name in df.columns:
            mapped_df[std_field] = df[col_name]
        else:
            mapped_df[std_field] = np.nan

    # Check required fields (crop_type & yield_value)
    detected_crop = None
    known_crops = ["Rice", "Wheat", "Maize", "Cotton", "Sugarcane", "Pulses", "Jowar", "Bajra", "Soybean", "Groundnut", "Barley", "Mustard", "Sunflower"]
    for c in list(mapping.values()) + list(df.columns):
        if c and c != "Not Available":
            for crop in known_crops:
                if crop.lower() in str(c).lower():
                    detected_crop = crop
                    break
            if detected_crop:
                break

    has_crop = (mapping.get("crop_type") != "Not Available" and "crop_type" in mapped_df) or (detected_crop is not None)
    has_yield = mapping.get("yield_value") != "Not Available" and "yield_value" in mapped_df
    
    errors = []
    if not has_crop:
        errors.append("Required field 'crop_type' could not be mapped (no crop column or recognized crop name in headers).")
    if not has_yield:
        errors.append("Required field 'yield_value' could not be mapped. Please select the Yield or Production column.")

    # 1. Rows with missing required values
    if detected_crop is not None and mapping.get("crop_type") in (None, "Not Available"):
        missing_crop_count = 0
    else:
        missing_crop_count = mapped_df["crop_type"].isnull().sum() if "crop_type" in mapped_df else total_rows
    missing_yield_count = mapped_df["yield_value"].isnull().sum() if "yield_value" in mapped_df else total_rows
    missing_rows_count = int(mapped_df.isnull().any(axis=1).sum())

    # 2. Duplicate rows
    duplicate_rows_count = int(df.duplicated().sum())

    # 3. Invalid numeric checks
    invalid_numeric_count = 0
    numeric_fields = ['rainfall', 'temperature', 'fertilizer', 'yield_value']
    for field in numeric_fields:
        if field in mapped_df and mapped_df[field].notnull().any():
            try:
                from python.data_cleaning import extract_numeric
                converted = mapped_df[field].apply(lambda x: extract_numeric(x, field))
                # Negative check for rainfall, fertilizer, yield
                if field in ['rainfall', 'fertilizer', 'yield_value']:
                    invalid_numeric_count += int((converted < 0).sum())
                # Extreme temperature check (-20 to 60°C)
                if field == 'temperature':
                    invalid_numeric_count += int(((converted < -20) | (converted > 60)).sum())
            except Exception:
                pass

    # Valid rows calculation (rows without missing required fields & non-negative numeric)
    valid_rows = total_rows - max(missing_crop_count, missing_yield_count) - invalid_numeric_count
    valid_rows = max(0, valid_rows)

    # 4. Compute Dataset Quality Score (0 to 100%)
    valid_ratio = (valid_rows / total_rows) * 50 if total_rows > 0 else 0
    completeness_ratio = (1 - (mapped_df.isnull().sum().sum() / (total_rows * len(mapping)))) * 30 if total_rows > 0 else 0
    duplicate_penalty = max(0, 10 - (duplicate_rows_count / total_rows) * 10) if total_rows > 0 else 0
    required_bonus = 10 if (has_crop and has_yield) else 0

    quality_score = round(valid_ratio + completeness_ratio + duplicate_penalty + required_bonus, 1)
    quality_score = min(100.0, max(0.0, quality_score))

    # Overall Status Classification
    if quality_score >= 85.0:
        quality_status = "EXCELLENT FOR ANALYSIS"
        quality_badge_class = "badge-strong"
    elif quality_score >= 65.0:
        quality_status = "GOOD FOR ANALYSIS"
        quality_badge_class = "badge-moderate"
    else:
        quality_status = "NEEDS CLEANING BEFORE IMPORT"
        quality_badge_class = "badge-neutral"

    return {
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "missing_value_rows": missing_rows_count,
        "duplicate_rows": duplicate_rows_count,
        "invalid_numeric_rows": invalid_numeric_count,
        "quality_score": quality_score,
        "quality_status": quality_status,
        "quality_badge_class": quality_badge_class,
        "has_required_fields": (has_crop and has_yield),
        "errors": errors
    }
