import pytest
import requests.exceptions
from unittest.mock import patch, MagicMock
from tools.city.city_tool import fetch_cities_from_api, parse_city_data, get_top_cities

# Fixtures for shared mocks
@pytest.fixture
def mock_api_key():
    with patch(
        'tools.city.city_tool.os.getenv',
        return_value="fake_api_key"
    ) as mock:
        yield mock

@pytest.fixture
def mock_response():
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"data": [{"city": "London"}]}
    return response

# --- Tests for fetch_cities_from_api ---

def test_fetch_cities_success(mock_api_key, mock_response):
    """Test successful API fetch."""
    with patch("tools.city.city_tool.requests.get", return_value=mock_response) as mock_get:
        result = fetch_cities_from_api("GB")
        assert result == {"data": [{"city": "London"}]}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

@pytest.mark.parametrize("country_code", ["GB", "US", "DE", "FR"])
def test_fetch_cities_success_multiple_countries(country_code, mock_api_key, mock_response):
    """Test successful API fetch for multiple countries."""
    with patch('tools.city.city_tool.requests.get', return_value=mock_response) as mock_get:
        result = fetch_cities_from_api(country_code)
        assert result == {"data": [{"city": "London"}]}
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

def test_fetch_cities_empty_response(mock_api_key):
    """Test API fetch with an empty data response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": []}
    with patch('tools.city.city_tool.requests.get', return_value=mock_response):
        result = fetch_cities_from_api("GB")
        assert result == {"data": []}

@patch('tools.city.city_tool.os.getenv')
def test_fetch_cities_missing_api_key(mock_getenv):
    """Test fetch failure when API key is missing."""
    mock_getenv.return_value = None
    with pytest.raises(ValueError, match="GEODB_CITIES_API_KEY not found"):
        fetch_cities_from_api("GB")

@patch('tools.city.city_tool.requests.get')
def test_fetch_cities_http_error(mock_get, mock_api_key):
    """Test fetch failure when API returns an HTTP error."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
    mock_get.return_value = mock_response
    with pytest.raises(requests.exceptions.HTTPError, match="404 Client Error"):
        fetch_cities_from_api("GB")

@patch('tools.city.city_tool.requests.get')
def test_fetch_cities_network_error(mock_get, mock_api_key):
    """Test fetch failure when a network error occurs."""
    mock_get.side_effect = requests.exceptions.RequestException("Connection error")
    with pytest.raises(requests.exceptions.RequestException, match="Connection error"):
        fetch_cities_from_api("GB")

# --- Tests for parse_city_data ---

def test_parse_city_data_success():
    """Test parsing valid API response."""
    api_data = {
        "data": [
            {"city": "London", "latitude": 51.5074, "longitude": -0.1278},
            {"city": "Manchester", "latitude": 53.4808, "longitude": -2.2426}
        ]
    }
    expected = [
        {"name": "London", "latitude": 51.5074, "longitude": -0.1278},
        {"name": "Manchester", "latitude": 53.4808, "longitude": -2.2426}
    ]
    assert parse_city_data(api_data) == expected

def test_parse_city_data_empty():
    """Test parsing empty or malformed responses."""
    assert parse_city_data({"data": []}) == []
    assert parse_city_data({}) == []

def test_parse_city_data_missing_fields():
    """Test parsing response items with missing fields."""
    api_data = {
        "data": [
            {"city": "London"} # missing lat/long
        ]
    }
    expected = [{"name": "London", "latitude": None, "longitude": None}]
    assert parse_city_data(api_data) == expected

# --- Tests for get_top_cities ---

@patch('tools.city.city_tool.fetch_cities_from_api')
def test_get_top_cities_success(mock_fetch):
    """Test successful orchestration of get_top_cities."""
    mock_fetch.return_value = {
        "data": [{"city": "London", "latitude": 51.5, "longitude": -0.1}]
    }
    result = get_top_cities("GB")
    
    assert result["status"] == "success"
    assert result["data"] == [{"name": "London", "latitude": 51.5, "longitude": -0.1}]

@pytest.mark.parametrize("invalid_code", ["G", "GBR", 12, None])
def test_get_top_cities_invalid_input(invalid_code):
    """Test input validation for country codes."""
    result = get_top_cities(invalid_code)
    assert result["status"] == "error"
    assert "Invalid country code" in result["message"]

@patch('tools.city.city_tool.fetch_cities_from_api')
def test_get_top_cities_http_error(mock_fetch):
    """Test handling of HTTP errors from the internal API fetch."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    error = requests.exceptions.HTTPError("Not Found", response=mock_response)
    mock_fetch.side_effect = error
    
    result = get_top_cities("GB")
    assert result["status"] == "error"
    assert "API request failed with status code 404" in result["message"]

@patch('tools.city.city_tool.fetch_cities_from_api')
def test_get_top_cities_network_error(mock_fetch):
    """Test handling of network-related errors."""
    mock_fetch.side_effect = requests.exceptions.RequestException("Conn error")
    
    result = get_top_cities("GB")
    assert result["status"] == "error"
    assert "Network error" in result["message"]

@patch('tools.city.city_tool.fetch_cities_from_api')
def test_get_top_cities_value_error(mock_fetch):
    """Test handling of configuration/value errors."""
    mock_fetch.side_effect = ValueError("Missing API Key")
    
    result = get_top_cities("GB")
    assert result["status"] == "error"
    assert "Missing API Key" in result["message"]

@patch('tools.city.city_tool.fetch_cities_from_api')
def test_get_top_cities_unexpected_error(mock_fetch):
    """Test handling of any other unexpected exceptions."""
    mock_fetch.side_effect = Exception("Boom")
    
    result = get_top_cities("GB")
    assert result["status"] == "error"
    assert "An unexpected error occurred" in result["message"]
