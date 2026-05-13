import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_top_cities(country_code):
    """
    Finds the 10 most populated cities in a country using the GeoDb Cities API.
    
    Args:
        country_code (str): The ISO 3166-1 alpha-2 country code (e.g., 'GB', 'US', 'FR').
        
    Returns:
        list: A list of dictionaries containing city name, latitude, and longitude.
    """
    api_key = os.getenv("GEODB_CITIES_API_KEY")
    if not api_key:
        raise ValueError("GEODB_CITIES_API_KEY not found in environment variables.")

    url = "https://wft-geo-db.p.rapidapi.com/v1/geo/cities"
    querystring = {
        "types": "CITY",
        "countryIds": country_code,
        "limit": "10",
        "sort": "-population"
    }

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "wft-geo-db.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        data = response.json()
        
        cities = []
        for city in data.get("data", []):
            cities.append({
                "name": city.get("city"),
                "latitude": city.get("latitude"),
                "longitude": city.get("longitude")
            })
        return cities
    except requests.exceptions.RequestException as e:
        print(f"Error fetching cities: {e}")
        return []

