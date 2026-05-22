import os
import logging
import datetime
from typing import Dict, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from tools.calendar.calendar_tool_config import (
    SCOPES,
    TOKEN_PATH,
    CREDENTIALS_PATH,
    DEFAULT_TIMEZONE,
    DEFAULT_REMINDERS,
)

logger = logging.getLogger(__name__)

def get_calendar_service():
    """
    Handles OAuth2 authentication and returns an authenticated Calendar service.
    
    - First run: opens a browser for the user to log in and grant permission.
    - Subsequent runs: loads saved credentials from token.json (no browser needed).
    """
    creds = None

    # token.json stores the user's access and refresh tokens after first login
    if os.path.exists(TOKEN_PATH):
        logger.debug(f"Loading credentials from {TOKEN_PATH}")
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If credentials are missing or expired, refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired credentials")
            creds.refresh(Request())
        else:
            logger.info("No valid credentials found, starting OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials so we don't need to log in again next time
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())
            logger.info(f"Credentials saved to {TOKEN_PATH}")

    # Build and return the Calendar API client
    return build("calendar", "v3", credentials=creds)


def build_event_payload(destination: str, start_date: str, end_date: str, notes: str = "") -> Dict[str, Any]:
    """
    Constructs the dictionary payload for a Google Calendar event with validation.
    
    Args:
        destination: e.g. "Paris, France"
        start_date:  e.g. "2025-07-14"
        end_date:    e.g. "2025-07-21"
        notes:       Optional extra details
        
    Returns:
        A dictionary formatted for the Google Calendar API.
        
    Raises:
        ValueError: If dates are invalid or in the wrong format.
    """
    # 1. Format Validation (YYYY-MM-DD)
    try:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid start_date format: '{start_date}'. Expected YYYY-MM-DD.")

    try:
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid end_date format: '{end_date}'. Expected YYYY-MM-DD.")

    # 2. Chronological Validation
    if end <= start:
        raise ValueError(f"End date ({end_date}) must be after start date ({start_date}).")

    return {
        "summary": f"🌍 Holiday: {destination}",
        "description": notes,
        "start": {
            "date": start_date,
            "timeZone": DEFAULT_TIMEZONE,
        },
        "end": {
            "date": end_date,
            "timeZone": DEFAULT_TIMEZONE,
        },
        "reminders": DEFAULT_REMINDERS,
    }


def create_holiday_event(destination: str, start_date: str, end_date: str, notes: str = ""):
    """
    Creates a multi-day holiday event on Google Calendar.

    Args:
        destination: e.g. "Paris, France"
        start_date:  e.g. "2025-07-14"  (YYYY-MM-DD)
        end_date:    e.g. "2025-07-21"  (YYYY-MM-DD, exclusive — the day AFTER return)
        notes:       Optional extra details (hotel, booking ref, etc.)

    Returns:
        A dict with the created event's id, summary, and a link to view it.
    """
    logger.info(f"Creating holiday event for {destination} from {start_date} to {end_date}")
    
    try:
        # 1. Validate inputs and build the event payload
        event = build_event_payload(destination, start_date, end_date, notes)

        # 2. Authenticate and get the service
        service = get_calendar_service()

        # 3. Insert the event into the primary calendar
        created_event = service.events().insert(
            calendarId="primary",
            body=event
        ).execute()

        logger.info(f"Event created successfully: {created_event.get('htmlLink')}")

        return {
            "status": "success",
            "data": {
                "event_id":   created_event["id"],
                "summary":    created_event["summary"],
                "start":      created_event["start"]["date"],
                "end":        created_event["end"]["date"],
                "event_link": created_event.get("htmlLink")
            }
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return {
            "status": "error",
            "message": f"Bad Request: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Failed to create holiday event: {e}")
        return {
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        }
