import logging
import requests

logger = logging.getLogger("fieldmind.soil")

def get_soil_info(lat: float, lon: float) -> dict:
    """
    Fetches soil information from ISRIC SoilGrids REST API.
    Note: The SoilGrids REST API expects lon, lat format for properties.
    """
    url = f"https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lon": lon,
        "lat": lat,
        "property": ["phh2o", "soc", "clay", "sand", "silt"],
        "depth": ["0-5cm"],
        "value": ["mean"]
    }
    
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        properties = data.get("properties", {})
        layers = properties.get("layers", [])
        
        soil_data = {}
        for layer in layers:
            name = layer.get("name")
            depths = layer.get("depths", [])
            if depths:
                # Get the mean value for the first depth (0-5cm)
                values = depths[0].get("values", {})
                mean_val = values.get("mean")
                if mean_val is not None:
                    # SoilGrids returns pH multiplied by 10
                    if name == "phh2o":
                        soil_data["ph"] = mean_val / 10.0
                    # SOC is in dg/kg
                    elif name == "soc":
                        soil_data["organic_carbon"] = mean_val
                    else:
                        soil_data[name] = mean_val
        
        return soil_data
    except Exception as e:
        logger.error(f"Failed to fetch soil data for {lat},{lon}: {e}")
        return {}
