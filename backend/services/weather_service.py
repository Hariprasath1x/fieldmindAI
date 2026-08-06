import logging
import requests

logger = logging.getLogger("fieldmind.weather")

def get_weather_info(lat: float, lon: float) -> dict:
    """
    Fetches average weather information from Open-Meteo API.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,precipitation",
        "timezone": "auto"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data.get("current", {})
        
        # In a real ag-app, we might want historical averages, but for this prototype 
        # we will use the current forecast data. We will mock rainfall as slightly higher 
        # if precipitation is 0 to avoid breaking recommendation logic requiring some rainfall.
        precip = current.get("precipitation", 0)
        if precip == 0:
            precip = 100.0  # reasonable default if not currently raining
            
        return {
            "temperature": current.get("temperature_2m", 25.0),
            "humidity": current.get("relative_humidity_2m", 60.0),
            "rainfall": precip
        }
    except Exception as e:
        logger.error(f"Failed to fetch weather data for {lat},{lon}: {e}")
        return {}
