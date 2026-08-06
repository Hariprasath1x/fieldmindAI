import logging
import requests

logger = logging.getLogger("fieldmind.location")

def get_location_info(lat: float, lon: float) -> dict:
    """
    Fetches location information from OpenStreetMap Nominatim API.
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "lat": lat,
        "lon": lon,
        "format": "json"
    }
    headers = {
        "User-Agent": "FieldMind-App/1.0 (contact@fieldmind.local)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        address = data.get("address", {})
        return {
            "village": address.get("village") or address.get("town") or address.get("city") or "Unknown",
            "district": address.get("county") or address.get("state_district") or "Unknown",
            "state": address.get("state") or "Unknown",
            "country": address.get("country") or "Unknown",
            "formatted_address": data.get("display_name", "Unknown location")
        }
    except Exception as e:
        logger.error(f"Failed to fetch location data for {lat},{lon}: {e}")
        return {}
