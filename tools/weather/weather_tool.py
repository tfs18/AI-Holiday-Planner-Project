import json
import os
from typing import Any, Dict
import requests
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

from tools.weather.weather_tool_config import (
    WEATHER_API_BASE_URL,
    WEATHER_DAILY_PARAMS,
    WEATHER_TIMEZONE,
)

def get_weather_forecast(city: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetches a daily forecast for a city for up to 7 days.
    
    Args:
        city: A city dictionary with 'name', 'latitude', and 'longitude' 
              as returned by parse_city_data.
    
    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - data: Forecast dictionary (if success)
        - message: Error description (if error)
    """
    lat = city.get("latitude")
    lon = city.get("longitude")

    if lat is None or lon is None:
        return {
            "status": "error",
            "message": f"Missing coordinates for city '{city.get('name', 'unknown')}'."
        }

    url = (
        f"{WEATHER_API_BASE_URL}"
        f"?latitude={lat}&longitude={lon}"
        f"&daily={WEATHER_DAILY_PARAMS}"
        f"&timezone={WEATHER_TIMEZONE}"
    )

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return {
            "status": "success",
            "data": response.json()
        }
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "Unknown"
        return {
            "status": "error",
            "message": f"Weather API request failed with status code {status_code}."
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Network error: Unable to reach the weather service."
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }

def get_forecasts_for_country(country_code: str) -> Dict[str, Any]:
    """
    Fetches weather forecasts for all top cities in a country.

    Args:
        country_code: ISO 3166-1 alpha-2 country code (e.g., 'GB', 'US').

    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - data: List of {"city": ..., "forecast": ...} dicts (if success)
        - message: Error description (if error)
    """
    from tools.city.city_tool import get_top_cities

    cities = get_top_cities(country_code)
    if cities["status"] == "error":
        return cities

    results = []
    for city in cities["data"]:
        forecast = get_weather_forecast(city)
        results.append({
            "city": city["name"],
            "forecast": forecast
        })

    return {
        "status": "success",
        "data": results
    }