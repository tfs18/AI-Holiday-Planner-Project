from typing import Any, Dict
import requests
import logging
import tools.weather.weather_tool_config

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
def get_weather_forecast(name: str, latitude: float, longitude: float) -> Dict[str, Any]:
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

    if latitude is None or longitude is None:
        return {
            "status": "error",
            "message": f"Missing coordinates for city '{name}'."
       }

    logger.info(f"Fetching weather forecast for city: {name}")

    try:
        api_data = fetch_weather_from_api(latitude, longitude)
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