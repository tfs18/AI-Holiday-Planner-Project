from typing import Any, Dict, List
import requests
import logging
import json
import tools.weather.weather_tool_config
from tools.city.city_tool import get_top_cities

logger = logging.getLogger(__name__)

# Function to build the api url call
def build_weather_url(lat: float, lon: float) -> str:
    """
    Constructs the weather API URL for a given set of coordinates.

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.

    Returns:
        A fully constructed URL string for the weather API request.
    """
    return (
        f"{tools.weather.weather_tool_config.WEATHER_API_BASE_URL}"
        f"?latitude={lat}&longitude={lon}"
        f"&daily={tools.weather.weather_tool_config.WEATHER_DAILY_PARAMS}"
        f"&timezone={tools.weather.weather_tool_config.WEATHER_TIMEZONE}"
    )

# Function to call the api
def fetch_weather_from_api(lat: float, lon: float) -> Dict[str, Any]:
    """
    Internal function to handle the API request to the weather service.

    Args:
        lat: Latitude of the location.
        lon: Longitude of the location.

    Returns:
        JSON response from the API.

    Raises:
        requests.exceptions.RequestException: For network-related issues.
    """
    url = build_weather_url(lat, lon)
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()

# Function to parse the data from the api call - selects required data fields
def parse_weather_data(api_data: Dict[str, Any], city_name: str) -> Dict[str, Any]:
    if not isinstance(api_data, dict):
        raise ValueError("Invalid API response format: expected a dictionary.")

    daily = api_data.get("daily")
    if daily is None:
        raise ValueError("Invalid API response format: 'daily' field is missing.")
    if not isinstance(daily, dict):
        raise ValueError("Invalid API response format: 'daily' field is not a dictionary.")

    required_fields = [
        "time", "weather_code", "temperature_2m_max", "temperature_2m_min",
        "rain_sum", "snowfall_sum", "wind_speed_10m_max", "precipitation_probability_max"
    ]
    for field in required_fields:
        if field not in daily:
            raise ValueError(f"Invalid API response format: '{field}' field is missing from daily data.")

    forecast_days = []
    for date, code, t_max, t_min, rain, snow, wind, precip_prob in zip(
        daily["time"],
        daily["weather_code"],
        daily["temperature_2m_max"],
        daily["temperature_2m_min"],
        daily["rain_sum"],
        daily["snowfall_sum"],
        daily["wind_speed_10m_max"],
        daily["precipitation_probability_max"],
    ):
        forecast_days.append({
            "date": date,
            "weather_code": code,
            "temp_max": t_max,
            "temp_min": t_min,
            "rain_sum": rain,
            "snowfall_sum": snow,
            "wind_speed_max": wind,
            "precipitation_probability_max": precip_prob,
        })

    return {
        "city": city_name,
        "forecast": forecast_days
    }

# Function to take coordinates from city tool and use them to get weather forecast
def get_weather_forecast(city: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetches and parses a daily forecast for a single city for up to 7 days.

    Args:
        city: A city dictionary with 'name', 'latitude', and 'longitude'
              as returned by parse_city_data.

    Returns:
        A dictionary containing:
        - status: "success" or "error"
        - data: Parsed forecast dictionary (if success)
        - message: Error description (if error)
    """
    name = city.get("name", "unknown")
    lat = city.get("latitude")
    lon = city.get("longitude")

    if lat is None or lon is None:
        return {
            "status": "error",
            "message": f"Missing coordinates for city '{name}'."
        }

    logger.info(f"Fetching weather forecast for city: {name}")

    try:
        api_data = fetch_weather_from_api(lat, lon)
        forecast = parse_weather_data(api_data, name)
        return {
            "status": "success",
            "data": forecast
        }
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "Unknown"
        logger.error(f"Weather API failure for {name}: {e}")
        return {
            "status": "error",
            "message": f"Weather API request failed with status code {status_code}."
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error for {name}: {e}")
        return {
            "status": "error",
            "message": "Network error: Unable to reach the weather service."
        }
    except ValueError as e:
        logger.error(f"Parsing error for {name}: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error for {name}: {e}")
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
        - data: List of forecast dictionaries (if success)
        - message: Error description (if error)
    """

    logger.info(f"Fetching forecasts for country: {country_code}")

    cities = get_top_cities(country_code)
    if cities["status"] == "error":
        return cities

    results = []
    for city in cities["data"]:
        forecast = get_weather_forecast(city)
        if forecast["status"] == "error":
            logger.warning(f"Skipping {city['name']}: {forecast['message']}")
            continue
        results.append(forecast["data"])

    return {
        "status": "success",
        "data": results
    }

# CAN BE REMOVED - pretty print output for dev purposes
def pretty_print_forecasts(result: Dict[str, Any]) -> None:
    """
    Pretty prints the forecast results to stdout for development purposes.

    Args:
        result: The dictionary returned by get_forecasts_for_country.
    """
    if result["status"] == "error":
        print(f"Error: {result['message']}")
        return

    for city_forecast in result["data"]:
        print(f"\n{'='*40}")
        print(f"  {city_forecast['city']}")
        print(f"{'='*40}")
        for day in city_forecast["forecast"]:
            print(f"  {day['date']}")
            print(f"    Max temp:      {day['temp_max']}°C")
            print(f"    Min temp:      {day['temp_min']}°C")
            print(f"    Weather Code:  {day['weather_code']}")
            print(f"    Rain:          {day['rain_sum']}mm")
            print(f"    Snowfall:      {day['snowfall_sum']}cm")
            print(f"    Wind:          {day['wind_speed_max']}km/h")
            print(f"    Precip Prob:   {day['precipitation_probability_max']}%")
            print()