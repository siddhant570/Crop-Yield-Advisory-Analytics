"""
Module 5: Rule-Based Agricultural Advisory Recommendation Engine
Evaluates environmental and agronomic factors against scientific crop thresholds
to identify yield stress patterns and generate actionable farming recommendations.
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from python.data_analysis import load_data

# Scientific Agronomic Baseline Profiles for Major Crops in India
CROP_AGRONOMIC_PROFILES = {
    "Rice": {
        "optimal_rainfall": (1000.0, 1500.0), # mm
        "optimal_temp": (20.0, 35.0),         # °C
        "optimal_fertilizer": (100.0, 160.0),  # kg/ha NPK
        "suitable_soils": ["Alluvial", "Clay", "Loam"],
        "ideal_irrigation": ["Canal", "Flooding", "Drip", "Tube Well"],
        "recommended_season": "Kharif",
        "fert_advice": "Split nitrogen application: 50% basal at transplanting, 25% at tillering, 25% at panicle initiation. Apply zinc sulphate (25 kg/ha) in zinc-deficient soils.",
        "irr_advice": "Maintain 2-5 cm shallow standing water during early tillering and flowering. Adopt Alternate Wetting and Drying (AWD) to conserve water without penalizing yield.",
        "soil_advice": "Puddled clay and alluvial soils maximize water retention. Incorporate green manure (Sesbania) prior to puddling to enhance organic carbon.",
        "pest_warning": "High humidity fosters bacterial leaf blight and stem borer. Use pheromone traps and avoid excessive early nitrogen application."
    },
    "Wheat": {
        "optimal_rainfall": (350.0, 650.0),
        "optimal_temp": (14.0, 25.0),
        "optimal_fertilizer": (80.0, 130.0),
        "suitable_soils": ["Loam", "Alluvial", "Clay"],
        "ideal_irrigation": ["Tube Well", "Canal", "Sprinkler"],
        "recommended_season": "Rabi",
        "fert_advice": "Standard 120:60:40 NPK ratio. Apply entire phosphorus and potassium as basal dose; split nitrogen between crown root initiation and first node stage.",
        "irr_advice": "Critical irrigation stages: Crown Root Initiation (CRI at 21 days), Tillering, Flowering, and Milking stages. Avoid terminal heat stress during grain filling.",
        "soil_advice": "Well-drained loam and alluvial soils with pH 6.0-7.5. Avoid heavy compaction; ensure leveled seedbeds to prevent water stagnation.",
        "pest_warning": "Watch for yellow rust and loose smut in humid cold spells. Treat seeds with Carboxin/Thiram before sowing."
    },
    "Maize": {
        "optimal_rainfall": (500.0, 850.0),
        "optimal_temp": (18.0, 30.0),
        "optimal_fertilizer": (80.0, 130.0),
        "suitable_soils": ["Loam", "Alluvial", "Red"],
        "ideal_irrigation": ["Drip", "Tube Well", "Rainfed"],
        "recommended_season": "Kharif",
        "fert_advice": "Apply 120 kg N, 60 kg P2O5, 40 kg K2O per hectare. Split nitrogen across knee-high, tasseling, and grain formation phases.",
        "irr_advice": "Highly sensitive to both drought and waterlogging. Silking and tasseling stages require consistent moisture. Ridge and furrow planting prevents waterlogging.",
        "soil_advice": "Deep, fertile loam or sandy-loam with excellent aeration. Does not tolerate soil salinity or prolonged standing water.",
        "pest_warning": "Monitor actively for Fall Armyworm (FAW). Intercrop with pulses and spray neem formulations during early whorl stage."
    },
    "Cotton": {
        "optimal_rainfall": (600.0, 950.0),
        "optimal_temp": (21.0, 34.0),
        "optimal_fertilizer": (90.0, 140.0),
        "suitable_soils": ["Black", "Alluvial", "Red"],
        "ideal_irrigation": ["Drip", "Canal", "Tube Well"],
        "recommended_season": "Kharif",
        "fert_advice": "Balanced 100:50:50 NPK with foliar sprays of 2% DAP or Potassium Nitrate during square and boll development to prevent boll shedding.",
        "irr_advice": "Drip irrigation gives 30% yield boost and saves 40% water. Avoid excessive late-season irrigation which induces vegetative rank growth instead of boll opening.",
        "soil_advice": "Deep Black Regur soils retain deep moisture suitable for long taproots. Ensure subsoil drainage to avoid root rot.",
        "pest_warning": "Scout for pink bollworm and whiteflies. Install yellow sticky traps and rotate insecticide chemistries to avoid resistance."
    },
    "Sugarcane": {
        "optimal_rainfall": (1200.0, 2000.0),
        "optimal_temp": (20.0, 36.0),
        "optimal_fertilizer": (160.0, 250.0),
        "suitable_soils": ["Alluvial", "Black", "Loam"],
        "ideal_irrigation": ["Canal", "Drip", "Tube Well"],
        "recommended_season": "Kharif",
        "fert_advice": "Heavy feeder: 250 kg N, 100 kg P, 120 kg K per hectare. Complete nitrogen application within 90-120 days after planting to ensure sucrose accumulation.",
        "irr_advice": "Sub-surface drip irrigation delivers substantial yield enhancement and water economy. Trash mulching in inter-rows conserves soil moisture.",
        "soil_advice": "Deep, well-aerated loam or alluvial soils rich in organic matter. Implement earthing-up to anchor canes against lodging.",
        "pest_warning": "Early shoot borer and red rot monitoring. Treat setts with Carbendazim before furrow planting."
    },
    "Pulses": {
        "optimal_rainfall": (350.0, 650.0),
        "optimal_temp": (18.0, 28.0),
        "optimal_fertilizer": (25.0, 60.0),
        "suitable_soils": ["Loam", "Red", "Alluvial"],
        "ideal_irrigation": ["Rainfed", "Drip", "Sprinkler"],
        "recommended_season": "Rabi",
        "fert_advice": "Inoculate seeds with Rhizobium and PSB biofertilizers. Requires low starter nitrogen (20 kg/ha) as legumes fix atmospheric nitrogen; prioritize phosphorus (40-50 kg/ha).",
        "irr_advice": "Typically rainfed; one protective irrigation at flowering and another at pod-development stage substantially boosts pulse grain weight.",
        "soil_advice": "Light to medium textured loams with neutral pH. Avoid saline and heavy waterlogged soils.",
        "pest_warning": "Helicoverpa armigera (pod borer) is the main yield limiter. Install bird perches and spray bio-agents like NPV."
    }
}

def get_dynamic_crop_profile(crop_name, df):
    """
    Computes empirical agronomic ranges from top 25% yield records in the dataset 
    if the crop is not pre-registered in standard botanical profiles.
    """
    crop_df = df[df['crop_type'].str.lower() == str(crop_name).lower()] if ('crop_type' in df and not df.empty) else pd.DataFrame()
    
    if crop_df.empty or len(crop_df) < 2:
        return {
            "optimal_rainfall": (500.0, 1200.0),
            "optimal_temp": (18.0, 32.0),
            "optimal_fertilizer": (60.0, 150.0),
            "suitable_soils": ["Alluvial", "Loam", "Black", "Red", "Clay"],
            "ideal_irrigation": ["Canal", "Drip", "Tube Well", "Rainfed"],
            "recommended_season": "Kharif/Rabi",
            "fert_advice": "Apply balanced NPK compound fertilizer based on local soil health card recommendations.",
            "irr_advice": "Schedule irrigation to maintain optimal soil moisture tension during vegetative and flowering phases.",
            "soil_advice": "Maintain soil organic matter through regular application of well-decomposed FYM or compost.",
            "pest_warning": "Practice regular field scouting and adopt Integrated Pest Management (IPM) protocols."
        }

    # Derive from top 30% yield performers
    q70 = crop_df['yield_value'].quantile(0.7) if 'yield_value' in crop_df else 0
    top_records = crop_df[crop_df['yield_value'] >= q70]
    if top_records.empty:
        top_records = crop_df

    r_min = float(top_records['rainfall'].min()) if ('rainfall' in top_records and top_records['rainfall'].notnull().any()) else 400.0
    r_max = float(top_records['rainfall'].max()) if ('rainfall' in top_records and top_records['rainfall'].notnull().any()) else 1200.0
    t_min = float(top_records['temperature'].min()) if ('temperature' in top_records and top_records['temperature'].notnull().any()) else 18.0
    t_max = float(top_records['temperature'].max()) if ('temperature' in top_records and top_records['temperature'].notnull().any()) else 34.0
    f_min = float(top_records['fertilizer'].min()) if ('fertilizer' in top_records and top_records['fertilizer'].notnull().any()) else 50.0
    f_max = float(top_records['fertilizer'].max()) if ('fertilizer' in top_records and top_records['fertilizer'].notnull().any()) else 160.0

    suitable_soils = top_records['soil'].dropna().unique().tolist() if 'soil' in top_records else ["Loam", "Alluvial"]
    ideal_irrigation = top_records['irrigation'].dropna().unique().tolist() if 'irrigation' in top_records else ["Canal", "Drip"]

    return {
        "optimal_rainfall": (round(max(100.0, r_min * 0.9), 1), round(r_max * 1.1, 1)),
        "optimal_temp": (round(max(10.0, t_min - 2.0), 1), round(t_max + 2.0, 1)),
        "optimal_fertilizer": (round(max(20.0, f_min * 0.9), 1), round(f_max * 1.1, 1)),
        "suitable_soils": suitable_soils if suitable_soils else ["Alluvial", "Loam"],
        "ideal_irrigation": ideal_irrigation if ideal_irrigation else ["Canal", "Tube Well"],
        "recommended_season": "Variable",
        "fert_advice": f"Apply balanced NPK at rates between {round(f_min,1)} - {round(f_max,1)} kg/ha based on top-yielding historical benchmarks.",
        "irr_advice": "Ensure adequate moisture matching historical top yields, particularly in critical flowering and grain-fill phases.",
        "soil_advice": f"Soils demonstrating superior yield: {', '.join(suitable_soils[:3]) if suitable_soils else 'Well-aerated loams'}.",
        "pest_warning": "Implement standard regional Integrated Pest Management and clean cultivation practices."
    }

def analyze_crop_advisory(crop_type, soil="Alluvial", rainfall=None, temperature=None, 
                          fertilizer=None, irrigation="Canal", season="Kharif", 
                          location="Punjab", source_dataset=None):
    """
    Module 5: Generates comprehensive rule-based agricultural advisory recommendations, 
    stress diagnostics, and yield health evaluation.
    """
    df = load_data(source_dataset=source_dataset)
    if df.empty:
        return {
            "has_data": False,
            "crop": crop_type,
            "health_score": 0,
            "health_category": "No Dataset Loaded",
            "health_badge": "badge-neutral",
            "avg_historical_yield": "N/A",
            "projected_yield": "N/A",
            "stresses": [],
            "advisories": [],
            "profile": None
        }
    
    # 1. Retrieve or derive agronomic reference profile
    if crop_type in CROP_AGRONOMIC_PROFILES:
        profile = CROP_AGRONOMIC_PROFILES[crop_type]
    else:
        profile = get_dynamic_crop_profile(crop_type, df)

    # Coerce numerical parameters
    rain_val = float(rainfall) if rainfall not in (None, "", "None") else None
    temp_val = float(temperature) if temperature not in (None, "", "None") else None
    fert_val = float(fertilizer) if fertilizer not in (None, "", "None") else None

    health_score = 100
    stresses = []
    advisories = []

    # 2. Moisture Stress Diagnostic
    opt_rain_min, opt_rain_max = profile["optimal_rainfall"]
    if rain_val is not None:
        if rain_val < opt_rain_min * 0.7:
            severity = "Severe Drought Deficit"
            penalty = 25
            health_score -= penalty
            stresses.append({
                "type": "Moisture Deficit",
                "status": "Severe Deficit",
                "severity": "danger",
                "icon": "fa-cloud-rain",
                "description": f"Rainfall ({rain_val} mm) is critically below the optimal range ({opt_rain_min}–{opt_rain_max} mm) for {crop_type}.",
                "action": "Immediate supplemental irrigation required. Switch to Drip or Furrow irrigation and apply mulch to curb soil moisture evaporation."
            })
            advisories.append({
                "category": "Water & Irrigation Management",
                "priority": "High",
                "icon": "fa-droplet-slash",
                "title": "Mitigate Moisture Deficit",
                "detail": f"Rainfall is {round(opt_rain_min - rain_val, 1)} mm below minimum threshold. Ensure frequent light irrigations (intervals of 4–6 days) rather than heavy flooding. Utilize tube well or drip systems."
            })
        elif rain_val < opt_rain_min:
            severity = "Mild Moisture Stress"
            penalty = 12
            health_score -= penalty
            stresses.append({
                "type": "Moisture Deficit",
                "status": "Mild Stress",
                "severity": "warning",
                "icon": "fa-cloud-sun",
                "description": f"Rainfall ({rain_val} mm) is slightly below ideal minimum ({opt_rain_min} mm).",
                "action": "Provide 1-2 critical supplemental irrigations during flowering and grain/pod development."
            })
            advisories.append({
                "category": "Water & Irrigation Management",
                "priority": "Medium",
                "icon": "fa-droplet",
                "title": "Scheduled Supplemental Irrigation",
                "detail": profile["irr_advice"]
            })
        elif rain_val > opt_rain_max * 1.35:
            severity = "Excess Moisture Risk"
            penalty = 18
            health_score -= penalty
            stresses.append({
                "type": "Excess Moisture",
                "status": "Waterlogging Risk",
                "severity": "danger",
                "icon": "fa-water",
                "description": f"Rainfall ({rain_val} mm) exceeds upper threshold ({opt_rain_max} mm). Root asphyxiation and damping-off risk.",
                "action": "Open field drainage channels immediately to prevent standing water. Avoid applying basal fertilizers until soil dries."
            })
            advisories.append({
                "category": "Water & Drainage Management",
                "priority": "High",
                "icon": "fa-water",
                "title": "Field Drainage & Aeration",
                "detail": "High precipitation increases fungal root infections. Create surface drainage trenches and aerate wet soil as soon as possible."
            })
        else:
            stresses.append({
                "type": "Moisture Level",
                "status": "Optimal Hydration",
                "severity": "success",
                "icon": "fa-cloud-showers-heavy",
                "description": f"Rainfall ({rain_val} mm) falls within the ideal agronomic range ({opt_rain_min}–{opt_rain_max} mm).",
                "action": "Maintain routine soil moisture monitoring; avoid unnecessary overhead irrigation."
            })
            advisories.append({
                "category": "Water & Irrigation Management",
                "priority": "Normal",
                "icon": "fa-check-circle",
                "title": "Irrigation Guidance",
                "detail": profile["irr_advice"]
            })
    else:
        advisories.append({
            "category": "Water & Irrigation Management",
            "priority": "Normal",
            "icon": "fa-droplet",
            "title": "General Irrigation Recommendation",
            "detail": profile["irr_advice"]
        })

    # 3. Thermal Stress Diagnostic
    opt_t_min, opt_t_max = profile["optimal_temp"]
    if temp_val is not None:
        if temp_val > opt_t_max:
            penalty = min(25, int((temp_val - opt_t_max) * 4) + 10)
            health_score -= penalty
            stresses.append({
                "type": "Thermal Stress",
                "status": "Heat Stress",
                "severity": "danger",
                "icon": "fa-temperature-high",
                "description": f"Temperature ({temp_val}°C) exceeds upper tolerance limit ({opt_t_max}°C) for {crop_type}.",
                "action": "Spray foliar 1% potassium nitrate (KNO3) to boost cellular osmoregulation and heat shock resilience. Irrigate in early mornings."
            })
            advisories.append({
                "category": "Microclimate & Temperature",
                "priority": "High",
                "icon": "fa-temperature-arrow-up",
                "title": "Heat Stress Mitigation",
                "detail": f"Extreme heat accelerates pollen sterility and rapid evapotranspiration. Water during cool evening/dawn hours and preserve surface straw mulch."
            })
        elif temp_val < opt_t_min:
            penalty = min(20, int((opt_t_min - temp_val) * 3) + 8)
            health_score -= penalty
            stresses.append({
                "type": "Thermal Stress",
                "status": "Cold / Chill Stress",
                "severity": "warning",
                "icon": "fa-temperature-low",
                "description": f"Temperature ({temp_val}°C) is below minimum threshold ({opt_t_min}°C). Growth rate and germination may be retarded.",
                "action": "Provide light evening irrigation to moderate micro-temperature. Delay sowing of non-hardy cultivars."
            })
            advisories.append({
                "category": "Microclimate & Temperature",
                "priority": "Medium",
                "icon": "fa-snowflake",
                "title": "Cold & Frost Management",
                "detail": "Cold soils impair root nutrient uptake. Consider light smoke generation or sprinkler application during frosty nights for frost-sensitive crops."
            })
        else:
            stresses.append({
                "type": "Thermal Condition",
                "status": "Optimal Temperature",
                "severity": "success",
                "icon": "fa-sun",
                "description": f"Ambient temperature ({temp_val}°C) is in the sweet spot ({opt_t_min}–{opt_t_max}°C).",
                "action": "Conditions are conducive for vigorous photosynthesis and reproductive development."
            })
            advisories.append({
                "category": "Microclimate & Temperature",
                "priority": "Normal",
                "icon": "fa-sun",
                "title": "Temperature Condition",
                "detail": f"Thermal profile aligns with {crop_type} physiological requirements across vegetative and grain development stages."
            })

    # 4. Fertilizer & Nutrient Diagnostic
    opt_f_min, opt_f_max = profile["optimal_fertilizer"]
    if fert_val is not None:
        if fert_val < opt_f_min:
            deficit = round(opt_f_min - fert_val, 1)
            penalty = 15
            health_score -= penalty
            stresses.append({
                "type": "Nutrient Status",
                "status": "Nutrient Deficiency Risk",
                "severity": "warning",
                "icon": "fa-seedling",
                "description": f"Fertilizer rate ({fert_val} kg/ha) is below recommended standard ({opt_f_min}–{opt_f_max} kg/ha).",
                "action": f"Top-dress with nitrogen/phosphorus to close the {deficit} kg/ha deficit before panicle/flowering initiation."
            })
            advisories.append({
                "category": "Nutrient Management",
                "priority": "High",
                "icon": "fa-flask",
                "title": "Targeted Nutrient Supplementation",
                "detail": profile["fert_advice"]
            })
        elif fert_val > opt_f_max * 1.3:
            excess = round(fert_val - opt_f_max, 1)
            penalty = 15
            health_score -= penalty
            stresses.append({
                "type": "Nutrient Status",
                "status": "Excess Nitrogen / Toxicity",
                "severity": "warning",
                "icon": "fa-triangle-exclamation",
                "description": f"Fertilizer dosage ({fert_val} kg/ha) significantly exceeds optimal range ({opt_f_min}–{opt_f_max} kg/ha).",
                "action": "Halt further chemical nitrogen additions. Excessive nitrogen causes weak vegetative stems, lodging, and high insect infestation."
            })
            advisories.append({
                "category": "Nutrient Management",
                "priority": "Medium",
                "icon": "fa-scale-unbalanced",
                "title": "Fertilizer Rationalization",
                "detail": f"Dosage is {excess} kg/ha above agronomic ceiling. Balance with potassium foliar spray to strengthen straw strength and prevent crop lodging."
            })
        else:
            stresses.append({
                "type": "Nutrient Status",
                "status": "Balanced Fertilizer",
                "severity": "success",
                "icon": "fa-check-double",
                "description": f"Fertilizer application ({fert_val} kg/ha) matches agronomic guidelines.",
                "action": "Maintain split application schedule to maximize nutrient use efficiency (NUE)."
            })
            advisories.append({
                "category": "Nutrient Management",
                "priority": "Normal",
                "icon": "fa-flask-vial",
                "title": "Nutrient Optimization",
                "detail": profile["fert_advice"]
            })
    else:
        advisories.append({
            "category": "Nutrient Management",
            "priority": "Normal",
            "icon": "fa-flask",
            "title": "Nutrient Optimization",
            "detail": profile["fert_advice"]
        })

    # 5. Soil Suitability & Conditioning
    soil_match = soil in profile.get("suitable_soils", [])
    if not soil_match and soil != "Unknown":
        health_score -= 8
        advisories.append({
            "category": "Soil Conditioning & Amendment",
            "priority": "Medium",
            "icon": "fa-mountain",
            "title": f"Soil Conditioning for {soil} Soil",
            "detail": f"{crop_type} achieves peak yield on {', '.join(profile['suitable_soils'])}. For {soil} soil: {profile['soil_advice']}"
        })
    else:
        advisories.append({
            "category": "Soil Conditioning & Health",
            "priority": "Normal",
            "icon": "fa-layer-group",
            "title": "Soil Management Guidance",
            "detail": profile["soil_advice"]
        })

    # 6. Pest & Seasonal Alert
    advisories.append({
        "category": "Pest & Disease Vigilance",
        "priority": "Medium",
        "icon": "fa-shield-halved",
        "title": f"Crop Protection for {season} Season",
        "detail": profile["pest_warning"]
    })

    # Clamp health score
    health_score = max(25, min(100, health_score))

    if health_score >= 80:
        health_category = "Optimal Agronomic Health"
        health_color = "#2d6a4f"
        health_badge = "badge-strong"
    elif health_score >= 60:
        health_category = "Moderate Stress Factors Detected"
        health_color = "#f4a261"
        health_badge = "badge-moderate"
    else:
        health_category = "High Stress / Intervention Required"
        health_color = "#e76f51"
        health_badge = "badge-weak"

    # Compute expected yield benchmark from active data
    crop_data = df[df['crop_type'] == crop_type] if ('crop_type' in df and not df.empty) else pd.DataFrame()
    if not crop_data.empty and 'yield_value' in crop_data:
        avg_hist_yield = round(float(crop_data['yield_value'].mean()), 2)
        max_hist_yield = round(float(crop_data['yield_value'].max()), 2)
        potential_yield = round(avg_hist_yield * (health_score / 100.0) * 1.15, 2)
        potential_yield = min(max_hist_yield * 1.05, max(1.0, potential_yield))
    else:
        avg_hist_yield = 3.5
        potential_yield = round(3.5 * (health_score / 100.0), 2)

    return {
        "crop_type": crop_type,
        "soil": soil,
        "rainfall": rain_val,
        "temperature": temp_val,
        "fertilizer": fert_val,
        "irrigation": irrigation,
        "season": season,
        "location": location,
        "health_score": health_score,
        "health_category": health_category,
        "health_color": health_color,
        "health_badge": health_badge,
        "avg_historical_yield": avg_hist_yield,
        "projected_yield": potential_yield,
        "stresses": stresses,
        "advisories": advisories,
        "profile": profile
    }

def get_dataset_wide_advisories(source_dataset=None):
    """
    Computes summary advisory diagnostics across all distinct crops in the active dataset.
    """
    df = load_data(source_dataset=source_dataset)
    if df.empty or 'crop_type' not in df:
        return []

    crop_summaries = []
    unique_crops = sorted(df['crop_type'].dropna().unique().tolist())

    for crop in unique_crops:
        cdf = df[df['crop_type'] == crop]
        avg_rain = float(cdf['rainfall'].mean()) if ('rainfall' in cdf and cdf['rainfall'].notnull().any()) else None
        avg_temp = float(cdf['temperature'].mean()) if ('temperature' in cdf and cdf['temperature'].notnull().any()) else None
        avg_fert = float(cdf['fertilizer'].mean()) if ('fertilizer' in cdf and cdf['fertilizer'].notnull().any()) else None
        top_soil = cdf['soil'].mode().iloc[0] if ('soil' in cdf and not cdf['soil'].empty) else "Alluvial"
        top_irr = cdf['irrigation'].mode().iloc[0] if ('irrigation' in cdf and not cdf['irrigation'].empty) else "Canal"
        top_season = cdf['season'].mode().iloc[0] if ('season' in cdf and not cdf['season'].empty) else "Kharif"

        advisory_result = analyze_crop_advisory(
            crop_type=crop,
            soil=top_soil,
            rainfall=round(avg_rain, 1) if avg_rain else None,
            temperature=round(avg_temp, 1) if avg_temp else None,
            fertilizer=round(avg_fert, 1) if avg_fert else None,
            irrigation=top_irr,
            season=top_season,
            source_dataset=source_dataset
        )

        crop_summaries.append({
            "crop": crop,
            "record_count": len(cdf),
            "avg_yield": round(float(cdf['yield_value'].mean()), 2) if 'yield_value' in cdf else 0.0,
            "health_score": advisory_result["health_score"],
            "health_category": advisory_result["health_category"],
            "health_badge": advisory_result["health_badge"],
            "primary_stress": advisory_result["stresses"][0]["status"] if advisory_result["stresses"] else "Optimal",
            "stress_severity": advisory_result["stresses"][0]["severity"] if advisory_result["stresses"] else "success",
            "top_advice": advisory_result["advisories"][0]["detail"] if advisory_result["advisories"] else "Follow balanced agronomic practices."
        })

    return crop_summaries


def evaluate_land_crop_suitability(soil="Alluvial", rainfall=750.0, temperature=26.0, 
                                   fertilizer=110.0, irrigation="Canal", season="Kharif", 
                                   source_dataset=None):
    """
    Evaluates which crop is suitable or favourable to cultivate on the specified land
    by considering all environmental, soil, climatic, and management conditions.
    """
    df = load_data(source_dataset=source_dataset)
    if df.empty:
        return {
            "has_data": False,
            "top_crop": None,
            "alternatives": [],
            "all_crops": [],
            "total_evaluated": 0,
            "favourable_count": 0,
            "message": "No agricultural dataset loaded. Please upload a dataset (.csv, .xlsx, or .xls) to evaluate crop cultivation suitability."
        }

    # 1. Identify all crops to evaluate from uploaded dataset
    crops_in_df = sorted(df['crop_type'].dropna().unique().tolist()) if ('crop_type' in df and not df.empty) else []
    all_crops = crops_in_df if crops_in_df else list(CROP_AGRONOMIC_PROFILES.keys())

    # Coerce input parameters
    try:
        u_rain = float(rainfall) if rainfall not in (None, "", "None") else 750.0
    except (ValueError, TypeError):
        u_rain = 750.0

    try:
        u_temp = float(temperature) if temperature not in (None, "", "None") else 26.0
    except (ValueError, TypeError):
        u_temp = 26.0

    try:
        u_fert = float(fertilizer) if fertilizer not in (None, "", "None") else 110.0
    except (ValueError, TypeError):
        u_fert = 110.0

    u_soil = str(soil).strip() if soil else "Alluvial"
    u_irr = str(irrigation).strip() if irrigation else "Canal"
    u_season = str(season).strip() if season else "Kharif"

    has_irrigation = u_irr.lower() in ["canal", "drip", "tube well", "sprinkler"]

    evaluated_crops = []

    for crop in all_crops:
        profile = CROP_AGRONOMIC_PROFILES.get(crop) or get_dynamic_crop_profile(crop, df)

        # Baseline yield from data
        crop_data = df[df['crop_type'] == crop] if ('crop_type' in df and not df.empty) else pd.DataFrame()
        hist_yield = round(float(crop_data['yield_value'].mean()), 2) if ('yield_value' in crop_data and crop_data['yield_value'].notnull().any()) else 3.5

        strengths = []
        concerns = []

        # ---------------------------------------------------------
        # Factor 1: Soil Compatibility (Weight: 25%)
        # ---------------------------------------------------------
        suitable_soils = [s.strip().lower() for s in profile.get("suitable_soils", [])]
        if u_soil.lower() in suitable_soils:
            soil_score = 100.0
            soil_match = "Optimal"
            soil_reason = f"{u_soil} soil perfectly matches {crop}'s root aeration and drainage needs."
            strengths.append(f"{u_soil} soil is optimal for {crop} cultivation.")
        elif u_soil.lower() in ["loam", "alluvial"]:
            soil_score = 78.0
            soil_match = "Compatible"
            soil_reason = f"{u_soil} is a versatile fertile soil; moderately compatible for {crop}."
            strengths.append(f"{u_soil} soil provides good fertility and moisture retention.")
        elif u_soil.lower() == "black" and crop in ["Cotton", "Sugarcane", "Wheat"]:
            soil_score = 95.0
            soil_match = "Optimal"
            soil_reason = f"Black regur soil has deep moisture holding capacity, highly suited for {crop}."
            strengths.append("Deep black soil retains excellent root moisture.")
        elif u_soil.lower() == "clay" and crop in ["Rice"]:
            soil_score = 100.0
            soil_match = "Optimal"
            soil_reason = "Heavy clay soil prevents water percolation, creating the ideal ponded bed for Paddy/Rice."
            strengths.append("Clay soil maximizes standing water retention.")
        else:
            soil_score = 42.0
            soil_match = "Suboptimal"
            pref_soils = ", ".join(profile.get("suitable_soils", ["Loam", "Alluvial"]))
            soil_reason = f"{u_soil} soil is less suitable for {crop} (prefers {pref_soils})."
            concerns.append(f"Soil type ({u_soil}) may require significant organic amendments or aeration.")

        # ---------------------------------------------------------
        # Factor 2: Temperature Suitability (Weight: 25%)
        # ---------------------------------------------------------
        t_min, t_max = profile.get("optimal_temp", (18.0, 32.0))
        if t_min <= u_temp <= t_max:
            temp_score = 100.0
            temp_match = "Optimal"
            temp_reason = f"Temperature ({u_temp}°C) is well within the physiological comfort zone ({t_min}–{t_max}°C)."
            strengths.append(f"Ambient temperature ({u_temp}°C) supports rapid vegetative growth and pollination.")
        else:
            t_diff = min(abs(u_temp - t_min), abs(u_temp - t_max))
            if t_diff <= 3.0:
                temp_score = 75.0
                temp_match = "Acceptable"
                temp_reason = f"Temperature ({u_temp}°C) is slightly outside optimal ({t_min}–{t_max}°C), but manageable."
            else:
                temp_score = max(18.0, round(100.0 - t_diff * 14.0, 1))
                temp_match = "Thermal Stress"
                if u_temp < t_min:
                    temp_reason = f"Cold stress risk: {u_temp}°C is colder than minimum {t_min}°C required for {crop}."
                    concerns.append(f"Low temperature ({u_temp}°C) risks delayed emergence and stunted growth.")
                else:
                    temp_reason = f"Heat stress risk: {u_temp}°C exceeds maximum threshold of {t_max}°C for {crop}."
                    concerns.append(f"Excess temperature ({u_temp}°C) risks pollen sterility and high transpiration.")

        # ---------------------------------------------------------
        # Factor 3: Moisture (Precipitation + Irrigation) (Weight: 25%)
        # ---------------------------------------------------------
        r_min, r_max = profile.get("optimal_rainfall", (500.0, 1000.0))
        if r_min <= u_rain <= r_max:
            water_score = 100.0
            water_match = "Optimal"
            water_reason = f"Rainfall ({u_rain} mm) satisfies natural crop water requirement ({r_min}–{r_max} mm)."
            strengths.append(f"Precipitation ({u_rain} mm) meets crop evapotranspiration demand.")
        elif u_rain < r_min:
            deficit = r_min - u_rain
            if has_irrigation:
                water_score = max(72.0, round(100.0 - (deficit / r_min) * 28.0, 1))
                water_match = "Irrigated"
                water_reason = f"Rainfall ({u_rain} mm) is below optimal ({r_min} mm), but {u_irr} irrigation bridges the water demand."
                strengths.append(f"Active {u_irr} irrigation reliably supplements rainfall deficit.")
            else:
                water_score = max(10.0, round(100.0 - (deficit / r_min) * 95.0, 1))
                water_match = "Severe Drought Risk"
                water_reason = f"Critical moisture deficit ({u_rain} mm vs {r_min} mm needed). Without irrigation, rainfed crop will fail."
                concerns.append("Critical rainfall deficit without supplemental irrigation.")
        else:
            # u_rain > r_max
            excess = u_rain - r_max
            if crop in ["Rice", "Sugarcane"]:
                water_score = 92.0
                water_match = "High Moisture Tolerant"
                water_reason = f"High rainfall ({u_rain} mm) is well-tolerated by water-intensive {crop}."
                strengths.append(f"{crop} thrives in abundant moisture environments.")
            else:
                water_score = max(30.0, round(100.0 - (excess / r_max) * 55.0, 1))
                water_match = "Waterlogging Risk"
                water_reason = f"Precipitation ({u_rain} mm) exceeds upper threshold ({r_max} mm); root asphyxiation risk."
                concerns.append(f"Excessive rainfall ({u_rain} mm) creates root rot and water stagnation hazards.")

        # ---------------------------------------------------------
        # Factor 4: Cropping Season Alignment (Weight: 15%)
        # ---------------------------------------------------------
        rec_season = profile.get("recommended_season", "Variable")
        if rec_season.lower() in ["variable", "any"] or u_season.lower() in rec_season.lower():
            season_score = 100.0
            season_match = "Optimal Season"
            season_reason = f"{u_season} is the recognized agro-climatic season for {crop}."
            strengths.append(f"Season ({u_season}) matches optimal photoperiod and sowing window.")
        else:
            season_score = 40.0
            season_match = "Off-Season"
            season_reason = f"{crop} is predominantly cultivated in {rec_season}; planting in {u_season} risks photoperiod mismatch."
            concerns.append(f"Cultivating in {u_season} is off-season (recommended: {rec_season}).")

        # ---------------------------------------------------------
        # Factor 5: Fertilizer / Nutrient Sufficiency (Weight: 10%)
        # ---------------------------------------------------------
        f_min, f_max = profile.get("optimal_fertilizer", (60.0, 140.0))
        if f_min <= u_fert <= f_max:
            fert_score = 100.0
            fert_match = "Optimal"
            fert_reason = f"Fertilizer application ({u_fert} kg/ha) matches {crop}'s NPK requirement ({f_min}–{f_max} kg/ha)."
            strengths.append("Nutrient application rate meets crop agronomic target.")
        elif u_fert < f_min:
            fert_score = max(50.0, round(100.0 - ((f_min - u_fert) / f_min) * 50.0, 1))
            fert_match = "Under-fertilized"
            fert_reason = f"Fertilizer ({u_fert} kg/ha) is under the recommended {f_min} kg/ha; top-dressing advised."
            concerns.append(f"Fertilizer dose ({u_fert} kg/ha) is below recommended ({f_min} kg/ha).")
        else:
            fert_score = max(65.0, round(100.0 - ((u_fert - f_max) / f_max) * 35.0, 1))
            fert_match = "High Nutrients"
            fert_reason = f"Fertilizer ({u_fert} kg/ha) is ample; monitor for vegetative rank growth."

        # ---------------------------------------------------------
        # Composite Suitability Score (0 to 100%)
        # ---------------------------------------------------------
        suitability_score = round(
            0.25 * soil_score +
            0.25 * temp_score +
            0.25 * water_score +
            0.15 * season_score +
            0.10 * fert_score,
            1
        )

        # Classification
        if suitability_score >= 85.0:
            favourability = "Highly Favourable"
            favourability_class = "favourable-high"
            badge_class = "badge-strong"
            verdict = "Strongly Recommended for Cultivation"
            status_icon = "fa-circle-check"
            color_accent = "#15803d"
        elif suitability_score >= 70.0:
            favourability = "Favourable"
            favourability_class = "favourable-medium"
            badge_class = "badge-info"
            verdict = "Recommended with Standard Care"
            status_icon = "fa-thumbs-up"
            color_accent = "#1d4ed8"
        elif suitability_score >= 50.0:
            favourability = "Moderately Suitable"
            favourability_class = "favourable-moderate"
            badge_class = "badge-warning"
            verdict = "Conditionally Suitable (Requires Management)"
            status_icon = "fa-triangle-exclamation"
            color_accent = "#d97706"
        else:
            favourability = "Unfavourable"
            favourability_class = "favourable-low"
            badge_class = "badge-danger"
            verdict = "Not Recommended for this Land"
            status_icon = "fa-circle-xmark"
            color_accent = "#dc2626"

        potential_yield = round(hist_yield * (suitability_score / 100.0), 2)

        evaluated_crops.append({
            "crop": crop,
            "suitability_score": suitability_score,
            "favourability": favourability,
            "favourability_class": favourability_class,
            "badge_class": badge_class,
            "verdict": verdict,
            "status_icon": status_icon,
            "color_accent": color_accent,
            "historical_yield": hist_yield,
            "projected_yield": potential_yield,
            "factors": {
                "soil": {"score": soil_score, "match": soil_match, "reason": soil_reason},
                "temperature": {"score": temp_score, "match": temp_match, "reason": temp_reason},
                "water": {"score": water_score, "match": water_match, "reason": water_reason},
                "season": {"score": season_score, "match": season_match, "reason": season_reason},
                "fertilizer": {"score": fert_score, "match": fert_match, "reason": fert_reason}
            },
            "strengths": strengths if strengths else ["Standard regional agronomic profile."],
            "concerns": concerns if concerns else ["No significant agronomic constraints detected."],
            "agronomic_guidelines": {
                "soil_prep": profile.get("soil_advice", "Ensure well-ploughed leveled land."),
                "fertilizer_plan": profile.get("fert_advice", "Apply balanced NPK as per soil test."),
                "irrigation_plan": profile.get("irr_advice", "Maintain timely irrigation at critical growth stages."),
                "pest_management": profile.get("pest_warning", "Monitor regularly for regional insect pests.")
            }
        })

    # Sort crops descending by suitability score
    evaluated_crops = sorted(evaluated_crops, key=lambda x: x["suitability_score"], reverse=True)

    # Top Recommended Crop
    top_crop = evaluated_crops[0] if evaluated_crops else None

    # Alternative favourable crops (suitability >= 70% and not top crop)
    alternatives = [c for c in evaluated_crops[1:] if c["suitability_score"] >= 65.0]

    return {
        "land_conditions": {
            "soil": u_soil,
            "rainfall": u_rain,
            "temperature": u_temp,
            "fertilizer": u_fert,
            "irrigation": u_irr,
            "season": u_season
        },
        "top_crop": top_crop,
        "alternatives": alternatives,
        "all_crops": evaluated_crops,
        "total_evaluated": len(evaluated_crops),
        "favourable_count": sum(1 for c in evaluated_crops if c["suitability_score"] >= 70.0)
    }

