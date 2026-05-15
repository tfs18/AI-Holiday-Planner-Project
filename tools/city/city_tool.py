# ToDo: consolidate imports, so they are only imported once at entry. 
# ToDo: figure out how to implement the package structure for better imports between systems. 

import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from tools.city.city_tool_config import (
    DEFAULT_COUNTRY_LIMIT,
    CITY_TYPE,
    SORTING_METHOD,
    API_URL,
    X_RAPIDAPI_HOST,
)

load_dotenv()

def fetch_cities_from_api(country_code: str) -> Dict[str, Any]:
    """
    Internal function to handle the API request to GeoDb Cities.
    
    Args:
        country_code: ISO 3166-1 alpha-2 country code.
        
    Returns:
        JSON response from the API.
        
    Raises:
        ValueError: If the API key is missing.
        requests.exceptions.RequestException: For network-related issues.
    """
    api_key = os.getenv("GEODB_CITIES_API_KEY")
    if not api_key:
        raise ValueError("GEODB_CITIES_API_KEY not found in environment variables.")

    querystring = {
        "types": CITY_TYPE,
        "countryIds": country_code,
        "limit": str(DEFAULT_COUNTRY_LIMIT),
        "sort": SORTING_METHOD
    }

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": X_RAPIDAPI_HOST
    }

    response = requests.get(API_URL, headers=headers, params=querystring)
    response.raise_for_status()
    return response.json()

def parse_city_data(api_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parses the raw API response into a list of simplified city dictionaries.
    
    Args:
        api_data: The raw dictionary from fetch_cities_from_api.
        
    Returns:
        A list of dictionaries with 'name', 'latitude', and 'longitude'.
    """
    cities = []
    for city in api_data.get("data", []):
        cities.append({
            "name": city.get("city"),
            "latitude": city.get("latitude"),
            "longitude": city.get("longitude")
        })
    return cities

def get_top_cities(country_code: str) -> Dict[str, Any]:
    """
    Finds the most populated cities in a country using the GeoDb Cities API.
    
    Args:
        country_code: The ISO 3166-1 alpha-2 country code (e.g., 'GB', 'US', 'FR').

    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - data: List of city dictionaries (if success)
        - message: Error description (if error)
    """
    # 1. Input Validation
    if not isinstance(country_code, str) or len(country_code) != 2:
        return {
            "status": "error",
            "message": f"Invalid country code '{country_code}'. Please provide a 2-letter ISO code (e.g., 'US', 'GB')."
        }

    try:
        data = fetch_cities_from_api(country_code)
        cities = parse_city_data(data)
        return {
            "status": "success",
            "data": cities
        }
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "Unknown"
        return {
            "status": "error",
            "message": f"API request failed with status code {status_code}."
        }
    except requests.exceptions.RequestException:
        return {
            "status": "error",
            "message": "Network error: Unable to reach the city information service."
        }
    except ValueError as e:
        return {
            "status": "error",
            "message": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }
