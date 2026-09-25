from typing import Optional, Dict, Any

# A small transparent metadata layer for regional suitability.
# Focuses on strongly associated regions to prevent obviously inappropriate crops from being recommended.
REGIONAL_CROP_MAP = {
    "apple": ["jammu and kashmir", "himachal pradesh", "uttarakhand"],
    "mothbeans": ["rajasthan", "gujarat", "haryana", "punjab", "maharashtra"],
    "pigeonpeas": ["maharashtra", "karnataka", "andhra pradesh", "telangana", "uttar pradesh", "gujarat", "madhya pradesh"],
    "jute": ["west bengal", "assam", "bihar", "odisha", "meghalaya"],
    "coconut": ["kerala", "tamil nadu", "karnataka", "andhra pradesh", "goa", "maharashtra", "odisha"],
    "cotton": ["gujarat", "maharashtra", "telangana", "andhra pradesh", "punjab", "haryana", "rajasthan", "karnataka", "tamil nadu"],
    "rice": ["west bengal", "punjab", "uttar pradesh", "andhra pradesh", "tamil nadu", "bihar", "odisha", "assam", "chhattisgarh"],
    "banana": ["tamil nadu", "maharashtra", "gujarat", "andhra pradesh", "karnataka", "kerala", "bihar", "assam"],
    "papaya": ["andhra pradesh", "gujarat", "karnataka", "madhya pradesh", "maharashtra", "tamil nadu", "kerala", "west bengal"],
    "coffee": ["karnataka", "kerala", "tamil nadu", "andhra pradesh", "odisha"],
    "tea": ["assam", "west bengal", "tamil nadu", "kerala", "himachal pradesh", "uttarakhand"],
    "grapes": ["maharashtra", "karnataka", "tamil nadu", "andhra pradesh", "punjab", "haryana"]
}

def get_regional_suitability(crop_name: str, state: Optional[str], country: Optional[str]) -> Dict[str, Any]:
    """
    Evaluates whether a crop is regionally appropriate for the given state.
    Returns a score modifier (bonus or penalty) and a user-friendly message.
    """
    if not state and not country:
        return {
            "is_region_aware": False,
            "score_modifier": 0.0,
            "message": "Recommendation based entirely on environmental factors (no region provided)."
        }

    normalized_crop = crop_name.lower().strip()
    normalized_state = state.lower().strip() if state else ""
    
    if normalized_crop not in REGIONAL_CROP_MAP:
        # We don't have explicit regional restrictions for this crop, so it's generally allowed
        return {
            "is_region_aware": True,
            "score_modifier": 0.0,
            "message": "Regionally suitable (general)."
        }
        
    preferred_states = REGIONAL_CROP_MAP[normalized_crop]
    
    # If the user's state is in the preferred states
    if normalized_state and any(pref_state in normalized_state for pref_state in preferred_states):
        return {
            "is_region_aware": True,
            "score_modifier": 15.0,  # Bonus for being in a highly suitable region
            "message": f"Highly suitable for {state.title()} region."
        }
    
    # If it's a known regional crop but the user is in a different state, apply a mismatch penalty
    if normalized_state:
        return {
            "is_region_aware": True,
            "score_modifier": -30.0, # Strong penalty for geographic mismatch (e.g. apple in Tamil Nadu)
            "message": f"Not typically grown in {state.title()}."
        }
        
    # Fallback if state is missing but country is provided
    return {
        "is_region_aware": True,
        "score_modifier": 0.0,
        "message": "Regional data inconclusive."
    }
