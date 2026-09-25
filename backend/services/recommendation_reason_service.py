import json
from pathlib import Path
from typing import Dict, Any

METADATA_PATH = Path(__file__).parent.parent / "data" / "crop_metadata.json"

# Load metadata once
try:
    with open(METADATA_PATH, "r") as f:
        CROP_METADATA = json.load(f)
except Exception:
    CROP_METADATA = {}

def get_crop_metadata(crop_name: str) -> Dict[str, Any]:
    return CROP_METADATA.get(crop_name.lower(), {
        "season": "Year Round",
        "water_requirement": "Medium",
        "water_range": "N/A",
        "difficulty": "Moderate",
        "ideal_conditions": {},
        "description": "A highly recommended crop based on your specific environmental and soil parameters."
    })

def generate_reasons(crop_name: str, payload: Any, is_top_choice: bool) -> list[str]:
    crop_name_lower = crop_name.lower()
    if crop_name_lower not in CROP_METADATA:
        # Fallback if crop is not in metadata
        return [
            f"Strong environmental alignment with your soil (N:{payload.N}, P:{payload.P}, K:{payload.K}).",
            f"Matches your local weather profile (Temp: {payload.temperature}°C, Rain: {payload.rainfall}mm)."
        ]

    ideal = CROP_METADATA[crop_name_lower]["ideal_conditions"]
    reasons = []

    def check_range(name, value, ideal_range, unit=""):
        if value < ideal_range.get("min", 0):
            return f"{name} ({value}{unit}) is below preferred range (min {ideal_range.get('min')}{unit})."
        if "max" in ideal_range and value > ideal_range["max"]:
            return f"{name} ({value}{unit}) is slightly higher than recommended (max {ideal_range['max']}{unit})."
        return None

    checks = [
        ("Rainfall", payload.rainfall, ideal.get("rainfall", {}), " mm"),
        ("Temperature", payload.temperature, ideal.get("temperature", {}), "°C"),
        ("Humidity", payload.humidity, ideal.get("humidity", {}), "%"),
        ("Soil pH", payload.ph, ideal.get("ph", {}), ""),
        ("Nitrogen", payload.N, ideal.get("nitrogen", {}), ""),
        ("Phosphorus", payload.P, ideal.get("phosphorus", {}), ""),
        ("Potassium", payload.K, ideal.get("potassium", {}), ""),
    ]

    if is_top_choice:
        # For the top choice, list positive matches and any slight mismatches
        for name, value, ideal_range, unit in checks:
            if not ideal_range:
                continue
            
            mismatch = check_range(name, value, ideal_range, unit)
            if mismatch:
                reasons.append(mismatch)
            else:
                reasons.append(f"{name} ({value}{unit}) is optimal for this crop.")
                
        if not reasons:
            reasons.append("Recommended based on overall environmental suitability.")
    else:
        # For alternatives, focus primarily on why they scored lower (mismatches)
        for name, value, ideal_range, unit in checks:
            if not ideal_range:
                continue
            reason = check_range(name, value, ideal_range, unit)
            if reason:
                reasons.append(reason)
                
        if not reasons:
            reasons.append("Overall profile slightly less optimal than top choice.")

    return reasons
