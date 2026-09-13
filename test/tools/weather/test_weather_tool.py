import pytest
import requests
from unittest.mock import patch, MagicMock

from tools.weather.weather_tool import (
    build_weather_url,
    fetch_weather_from_api,
    parse_weather_data,
    get_weather_forecast,
)


# ----------------------------
# build_weather_url
# ----------------------------

@patch("tools.weather.weather_tool_config.WEATHER_API_BASE_URL", "https://api.test.com/v1/forecast")
@patch("tools.weather.weather_tool_config.WEATHER_DAILY_PARAMS", "params")
@patch("tools.weather.weather_tool_config.WEATHER_TIMEZONE", "UTC")
def test_build_weather_url():
    """Test URL construction."""
    url = build_weather_url(51.5, -0.1)

    assert "latitude=51.5" in url
    assert "longitude=-0.1" in url
    assert "daily=params" in url
    assert "timezone=UTC" in url
    assert url.startswith("https://api.test.com/v1/forecast")


# ----------------------------
# fetch_weather_from_api
# ----------------------------

@patch("tools.weather.weather_tool.requests.get")
def test_fetch_weather_success(mock_get):
    """Test successful API call."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"daily": {"time": []}}
    mock_get.return_value = mock_response

    result = fetch_weather_from_api(51.5, -0.1)

    assert result == {"daily": {"time": []}}
    mock_get.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


@patch("tools.weather.weather_tool.requests.get")
def test_fetch_weather_http_error(mock_get):
    """Test HTTP error propagation."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 error")
    mock_get.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError, match="500 error"):
        fetch_weather_from_api(51.5, -0.1)


@patch("tools.weather.weather_tool.requests.get")
def test_fetch_weather_network_error(mock_get):
    """Test network error handling."""
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")

    with pytest.raises(requests.exceptions.RequestException, match="Connection error"):
        fetch_weather_from_api(51.5, -0.1)


# ----------------------------
# parse_weather_data
# ----------------------------

def test_parse_weather_data_success():
    """Test valid API parsing."""
    api_data = {
        "daily": {
            "time": ["2026-06-01"],
            "weather_code": [1],
            "temperature_2m_max": [20],
            "temperature_2m_min": [10],
            "rain_sum": [0],
            "snowfall_sum": [0],
            "wind_speed_10m_max": [15],
            "precipitation_probability_max": [30],
        }
    }

    result = parse_weather_data(api_data, "London")

    assert result["city"] == "London"
    assert len(result["forecast"]) == 1
    assert result["forecast"][0]["date"] == "2026-06-01"


def test_parse_weather_data_invalid_type():
    """Top-level invalid type."""
    with pytest.raises(ValueError, match="expected a dictionary"):
        parse_weather_data("not a dict", "London")


def test_parse_weather_data_missing_daily():
    """Missing daily field."""
    with pytest.raises(ValueError, match="'daily' field is missing"):
        parse_weather_data({}, "London")


def test_parse_weather_data_daily_not_dict():
    """Daily not dict."""
    with pytest.raises(ValueError, match="'daily' field is not a dictionary"):
        parse_weather_data({"daily": "bad"}, "London")


def test_parse_weather_data_missing_field():
    """Missing required field."""
    api_data = {
        "daily": {
            "time": ["2026-06-01"],
            "weather_code": [1],
        }
    }

    with pytest.raises(ValueError, match="missing from daily data"):
        parse_weather_data(api_data, "London")


# ----------------------------
# get_weather_forecast
# ----------------------------

@patch("tools.weather.weather_tool.fetch_weather_from_api")
def test_get_weather_forecast_success(mock_fetch):
    """Test successful orchestration."""
    mock_fetch.return_value = {
        "daily": {
            "time": ["2026-06-01"],
            "weather_code": [1],
            "temperature_2m_max": [20],
            "temperature_2m_min": [10],
            "rain_sum": [0],
            "snowfall_sum": [0],
            "wind_speed_10m_max": [15],
            "precipitation_probability_max": [30],
        }
    }

    city = {"name": "London", "latitude": 51.5, "longitude": -0.1}

    result = get_weather_forecast(city)

    assert result["status"] == "success"
    assert result["data"]["city"] == "London"


def test_get_weather_forecast_missing_coords():
    """Missing latitude/longitude."""
    city = {"name": "London"}

    result = get_weather_forecast(city)

    assert result["status"] == "error"
    assert "Missing coordinates" in result["message"]


@patch("tools.weather.weather_tool.fetch_weather_from_api")
def test_get_weather_forecast_http_error(mock_fetch):
    """HTTP error handling."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_fetch.side_effect = requests.exceptions.HTTPError(
        "404 error", response=mock_response
    )

    city = {"name": "London", "latitude": 1, "longitude": 2}

    result = get_weather_forecast(city)

    assert result["status"] == "error"
    assert "404" in result["message"]


@patch("tools.weather.weather_tool.fetch_weather_from_api")
def test_get_weather_forecast_network_error(mock_fetch):
    """Network error handling."""
    mock_fetch.side_effect = requests.exceptions.RequestException("down")

    city = {"name": "London", "latitude": 1, "longitude": 2}

    result = get_weather_forecast(city)

    assert result["status"] == "error"
    assert "Network error" in result["message"]


@patch("tools.weather.weather_tool.fetch_weather_from_api")
def test_get_weather_forecast_value_error(mock_fetch):
    """ValueError propagation."""
    mock_fetch.side_effect = ValueError("Bad format")

    city = {"name": "London", "latitude": 1, "longitude": 2}

    result = get_weather_forecast(city)

    assert result["status"] == "error"
    assert "Bad format" in result["message"]


@patch("tools.weather.weather_tool.fetch_weather_from_api")
def test_get_weather_forecast_unexpected_error(mock_fetch):
    """Unexpected error handling."""
    mock_fetch.side_effect = Exception("boom")

    city = {"name": "London", "latitude": 1, "longitude": 2}

    result = get_weather_forecast(city)

    assert result["status"] == "error"
    assert "unexpected error" in result["message"].lower()