import pytest
import datetime
from unittest.mock import patch, MagicMock, mock_open
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from tools.calendar.calendar_tool import (
    build_event_payload,
    get_calendar_service,
    create_holiday_event,
    delete_calendar_event
)
from tools.calendar.calendar_tool_config import TOKEN_PATH, CREDENTIALS_PATH, SCOPES

# --- Tests for build_event_payload ---

def test_build_event_payload_success():
    """Test building a payload with valid inputs."""
    destination = "Paris, France"
    start_date = "2025-07-14"
    end_date = "2025-07-21"
    notes = "Booking Ref: 12345"
    
    payload = build_event_payload(destination, start_date, end_date, notes)
    
    assert payload["summary"] == f"🌍 Holiday: {destination}"
    assert payload["description"] == notes
    assert payload["start"]["date"] == start_date
    assert payload["end"]["date"] == end_date
    assert "timeZone" in payload["start"]
    assert "reminders" in payload

@pytest.mark.parametrize("start, end, error_match", [
    ("2025-07-21", "2025-07-14", "must be after start date"),  # End before start
    ("2025-07-14", "2025-07-14", "must be after start date"),  # End same as start
    ("invalid-date", "2025-07-21", "Invalid start_date format"), # Wrong format start
    ("2025-07-14", "21-07-2025", "Invalid end_date format"),    # Wrong format end
    ("", "2025-07-21", "Invalid start_date format"),            # Empty string
    ("2025-02-30", "2025-03-01", "Invalid start_date format"),  # Non-existent date
])
def test_build_event_payload_validation_failures(start, end, error_match):
    """Test that build_event_payload raises ValueError for various invalid inputs."""
    with pytest.raises(ValueError, match=error_match):
        build_event_payload("Test City", start, end)

def test_build_event_payload_leap_year():
    """Test handling of leap years."""
    # 2024 is a leap year
    payload = build_event_payload("Leap City", "2024-02-28", "2024-02-29")
    assert payload["end"]["date"] == "2024-02-29"
    
    # 2025 is not a leap year
    with pytest.raises(ValueError, match="Invalid start_date format"):
        build_event_payload("Non-Leap City", "2025-02-29", "2025-03-01")

def test_build_event_payload_extreme_values():
    """Test with very long strings for destination and notes."""
    destination = "A" * 1000
    notes = "B" * 5000
    payload = build_event_payload(destination, "2025-01-01", "2025-01-02", notes)
    assert payload["summary"] == f"🌍 Holiday: {destination}"
    assert payload["description"] == notes

# --- Tests for get_calendar_service ---

@patch("tools.calendar.calendar_tool.os.path.exists")
@patch("tools.calendar.calendar_tool.Credentials.from_authorized_user_file")
@patch("tools.calendar.calendar_tool.build")
def test_get_calendar_service_valid_token(mock_build, mock_from_file, mock_exists):
    """Test when a valid token already exists."""
    mock_exists.return_value = True
    mock_creds = MagicMock(spec=Credentials)
    mock_creds.valid = True
    mock_from_file.return_value = mock_creds
    
    get_calendar_service()
    
    mock_build.assert_called_once_with("calendar", "v3", credentials=mock_creds)

@patch("tools.calendar.calendar_tool.os.path.exists")
@patch("tools.calendar.calendar_tool.Credentials.from_authorized_user_file")
@patch("tools.calendar.calendar_tool.Request")
@patch("tools.calendar.calendar_tool.build")
@patch("builtins.open", new_callable=mock_open)
def test_get_calendar_service_expired_token_refresh(mock_file, mock_build, mock_request, mock_from_file, mock_exists):
    """Test when token is expired but can be refreshed."""
    mock_exists.return_value = True
    mock_creds = MagicMock(spec=Credentials)
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = "some_refresh_token"
    mock_from_file.return_value = mock_creds
    
    get_calendar_service()
    
    mock_creds.refresh.assert_called_once()
    mock_build.assert_called_once_with("calendar", "v3", credentials=mock_creds)


@patch("tools.calendar.calendar_tool.os.path.exists")
@patch("tools.calendar.calendar_tool.Credentials.from_authorized_user_file")
@patch("tools.calendar.calendar_tool.InstalledAppFlow.from_client_secrets_file")
@patch("tools.calendar.calendar_tool.build")
@patch("builtins.open", new_callable=mock_open)
def test_get_calendar_service_no_token_starts_flow(mock_file, mock_build, mock_flow_from_file, mock_from_file, mock_exists):
    """Test when token.json is missing, starting the OAuth flow."""
    mock_exists.return_value = False
    mock_flow = MagicMock()
    mock_creds = MagicMock()
    mock_flow.run_local_server.return_value = mock_creds
    mock_flow_from_file.return_value = mock_flow
    
    get_calendar_service()
    
    mock_flow_from_file.assert_called_once_with(CREDENTIALS_PATH, SCOPES)
    mock_flow.run_local_server.assert_called_once_with(port=0)
    mock_build.assert_called_once_with("calendar", "v3", credentials=mock_creds)

@patch("tools.calendar.calendar_tool.os.path.exists")
@patch("tools.calendar.calendar_tool.Credentials.from_authorized_user_file")
@patch("tools.calendar.calendar_tool.Request")
@patch("tools.calendar.calendar_tool.InstalledAppFlow.from_client_secrets_file")
@patch("tools.calendar.calendar_tool.build")
@patch("builtins.open", new_callable=mock_open)
def test_get_calendar_service_refresh_fails_starts_flow(mock_file, mock_build, mock_flow_from_file, mock_request, mock_from_file, mock_exists):
    """Test when token refresh fails, falling back to full OAuth flow."""
    mock_exists.return_value = True
    mock_expired_creds = MagicMock(spec=Credentials)
    mock_expired_creds.valid = False
    mock_expired_creds.expired = True
    mock_expired_creds.refresh_token = "bad_refresh_token"
    mock_expired_creds.refresh.side_effect = Exception("Refresh failed")
    mock_from_file.return_value = mock_expired_creds
    
    mock_flow = MagicMock()
    mock_new_creds = MagicMock()
    mock_flow.run_local_server.return_value = mock_new_creds
    mock_flow_from_file.return_value = mock_flow
    
    get_calendar_service()
    
    mock_expired_creds.refresh.assert_called_once()
    mock_flow_from_file.assert_called_once()
    mock_flow.run_local_server.assert_called_once()
    mock_build.assert_called_once_with("calendar", "v3", credentials=mock_new_creds)

# --- Tests for create_holiday_event ---

@patch("tools.calendar.calendar_tool.get_calendar_service")
def test_create_holiday_event_success(mock_get_service):
    """Test successful creation of a holiday event."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    mock_service.events().insert().execute.return_value = {
        "id": "event123",
        "summary": "🌍 Holiday: Paris",
        "start": {"date": "2025-07-14"},
        "end": {"date": "2025-07-21"},
        "htmlLink": "http://calendar.google.com/event123"
    }
    
    result = create_holiday_event("Paris", "2025-07-14", "2025-07-21")
    
    assert result["status"] == "success"
    assert result["data"]["event_id"] == "event123"

@patch("tools.calendar.calendar_tool.build_event_payload")
def test_create_holiday_event_validation_error(mock_build_payload):
    """Test create_holiday_event when payload building fails (validation error)."""
    mock_build_payload.side_effect = ValueError("Invalid date format")
    
    result = create_holiday_event("Paris", "bad-date", "2025-07-21")
    
    assert result["status"] == "error"
    assert "Invalid date format" in result["message"]

@patch("tools.calendar.calendar_tool.get_calendar_service")
def test_create_holiday_event_http_400_error(mock_get_service):
    """Test create_holiday_event handling of 400 Bad Request from API."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    
    error_resp = MagicMock()
    error_resp.status = 400
    mock_service.events().insert().execute.side_effect = HttpError(resp=error_resp, content=b"Bad Request")
    
    result = create_holiday_event("Paris", "2025-07-14", "2025-07-21")
    
    assert result["status"] == "error"
    assert "The API rejected the event data" in result["message"]

@patch("tools.calendar.calendar_tool.get_calendar_service")
def test_create_holiday_event_http_401_error(mock_get_service):
    """Test create_holiday_event handling of 401 Unauthorized from API."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    
    error_resp = MagicMock()
    error_resp.status = 401
    mock_service.events().insert().execute.side_effect = HttpError(resp=error_resp, content=b"Unauthorized")
    
    result = create_holiday_event("Paris", "2025-07-14", "2025-07-21")
    
    assert result["status"] == "error"
    assert "Unauthorized" in result["message"]

@patch("tools.calendar.calendar_tool.get_calendar_service")
def test_create_holiday_event_unexpected_exception(mock_get_service):
    """Test create_holiday_event handling of unexpected exceptions."""
    mock_get_service.side_effect = Exception("System crash")
    
    result = create_holiday_event("Paris", "2025-07-14", "2025-07-21")
    
    assert result["status"] == "error"
    assert "System crash" in result["message"]


# --- Tests for delete_holiday_event ---

@patch("tools.calendar.calendar_tool.get_calendar_service")
def test_delete_calendar_event_success(mock_get_service):
    """Test successful deletion of an event."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    
    result = delete_calendar_event("event123")
    
    assert result["status"] == "success"
    mock_service.events().delete.assert_called_once_with(calendarId="primary", eventId="event123")

@patch("tools.calendar.calendar_tool.get_calendar_service")
def test_delete_calendar_event_not_found(mock_get_service):
    """Test handling of 404 error when deleting an event."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    
    error_resp = MagicMock()
    error_resp.status = 404
    mock_service.events().delete().execute.side_effect = HttpError(resp=error_resp, content=b"Not Found")
    
    result = delete_calendar_event("non-existent-id")
    
    assert result["status"] == "error"
    assert "Not Found" in result["message"]


@patch("tools.calendar.calendar_tool.get_calendar_service")
def test_delete_calendar_event_http_401_error(mock_get_service):
    """Test delete_calendar_event handling of 401 Unauthorized from API."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    
    error_resp = MagicMock()
    error_resp.status = 401
    mock_service.events().delete().execute.side_effect = HttpError(resp=error_resp, content=b"Unauthorized")
    
    result = delete_calendar_event("event123")
    
    assert result["status"] == "error"
    assert "Unauthorized" in result["message"]

@patch("tools.calendar.calendar_tool.get_calendar_service")
def test_delete_calendar_event_http_500_error(mock_get_service):
    """Test delete_calendar_event handling of 500 Internal Server Error from API."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    
    error_resp = MagicMock()
    error_resp.status = 500
    mock_service.events().delete().execute.side_effect = HttpError(resp=error_resp, content=b"Server Error")
    
    result = delete_calendar_event("event123")
    
    assert result["status"] == "error"
    assert "API Error (500)" in result["message"]

@patch("tools.calendar.calendar_tool.get_calendar_service")
def test_delete_calendar_event_unexpected_exception(mock_get_service):
    """Test delete_calendar_event handling of unexpected exceptions."""
    mock_service = MagicMock()
    mock_get_service.return_value = mock_service
    mock_service.events().delete().execute.side_effect = Exception("Database failure")
    
    result = delete_calendar_event("event123")
    
    assert result["status"] == "error"
    assert "Database failure" in result["message"]
