"""
Statistical Analysis Module
Calculates Pandas/NumPy descriptive statistics (Mean, Median, Std Dev, Min, Max) 
and Pearson Correlation coefficients with dynamic missing field handling.
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from python.data_analysis import load_data

def get_descriptive_stats(source_dataset=None):
    """
    Computes summary statistics for key numerical variables in the active dataset.
    If a variable is not available in the dataset, returns available=False.
    """
    df = load_data(source_dataset=source_dataset)
    numerical_cols = [
        ('rainfall', 'Rainfall (mm)'),
        ('temperature', 'Temperature (°C)'),
        ('fertilizer', 'Fertilizer (kg/ha)'),
        ('yield_value', 'Crop Yield (tons/ha)')
    ]
    
    stats = {}
    for col, label in numerical_cols:
        if col in df and df[col].notnull().any():
            series = pd.to_numeric(df[col], errors='coerce').dropna()
            if not series.empty:
                stats[col] = {
                    "available": True,
                    "label": label,
                    "mean": round(float(series.mean()), 2),
                    "median": round(float(series.median()), 2),
                    "std": round(float(series.std()), 2) if len(series) > 1 else 0.0,
                    "min": round(float(series.min()), 2),
                    "max": round(float(series.max()), 2)
                }
                continue
                
        stats[col] = {
            "available": False,
            "label": label,
            "message": "Not available in current dataset."
        }

    return stats

def get_correlation_analysis(source_dataset=None):
    """
    Computes Pearson Correlation coefficients (r) between agricultural drivers and Crop Yield.
    If a variable is absent or has insufficient data, returns clear non-available status.
    """
    df = load_data(source_dataset=source_dataset)
    
    correlations = []
    pairs = [
        ('rainfall', 'yield_value', 'Rainfall ↔ Crop Yield', 'Rainfall'),
        ('temperature', 'yield_value', 'Temperature ↔ Crop Yield', 'Temperature'),
        ('fertilizer', 'yield_value', 'Fertilizer Usage ↔ Crop Yield', 'Fertilizer')
    ]
    
    for col1, col2, label, var1_name in pairs:
        if (col1 in df and col2 in df and 
            df[col1].notnull().sum() >= 3 and df[col2].notnull().sum() >= 3):
            
            clean_df = df.dropna(subset=[col1, col2])
            if len(clean_df) >= 3:
                r_value = float(clean_df[col1].corr(clean_df[col2]))
                if pd.notnull(r_value):
                    r_rounded = round(r_value, 3)
                    
                    if abs(r_rounded) >= 0.7:
                        strength = "Strong Positive" if r_rounded > 0 else "Strong Negative"
                        badge_class = "badge-strong"
                    elif abs(r_rounded) >= 0.4:
                        strength = "Moderate Positive" if r_rounded > 0 else "Moderate Negative"
                        badge_class = "badge-moderate"
                    elif abs(r_rounded) >= 0.1:
                        strength = "Weak Positive" if r_rounded > 0 else "Weak Negative"
                        badge_class = "badge-weak"
                    else:
                        strength = "Negligible / No Correlation"
                        badge_class = "badge-neutral"

                    correlations.append({
                        "available": True,
                        "pair_label": label,
                        "var1": var1_name,
                        "var2": "Crop Yield",
                        "r_value": r_rounded,
                        "strength": strength,
                        "badge_class": badge_class
                    })
                    continue

        correlations.append({
            "available": False,
            "pair_label": label,
            "var1": var1_name,
            "message": f"{var1_name} data is not available in the current dataset."
        })
        
    return correlations
