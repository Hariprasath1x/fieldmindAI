import logging

logger = logging.getLogger("fieldmind.estimation")

def estimate_npk(soil_data: dict, weather_data: dict) -> dict:
    """
    Estimates N, P, K values based on available soil and weather data.
    This is a heuristic fallback since SoilGrids doesn't provide direct NPK.
    """
    ph = soil_data.get("ph", 6.5)
    soc = soil_data.get("organic_carbon", 150) # default dg/kg
    
    # Simple heuristic
    # Nitrogen correlates somewhat with organic carbon
    n_est = min(140, max(20, soc * 0.3)) 
    
    # Phosphorus and Potassium have complex relationships with pH and clay,
    # Here we use a generic baseline modulated slightly by pH.
    p_est = 40 + (ph - 6.0) * 5
    k_est = 40 + (ph - 6.0) * 4
    
    # Ensure they are within sensible bounds for standard crops
    p_est = min(100, max(10, p_est))
    k_est = min(100, max(10, k_est))
    
    return {
        "nitrogen": round(n_est, 1),
        "phosphorus": round(p_est, 1),
        "potassium": round(k_est, 1),
        "is_estimated": True
    }
