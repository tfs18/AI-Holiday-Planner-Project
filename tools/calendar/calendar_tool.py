import datetime
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes define what permissions we're requesting
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Define paths to authorisation files
AUTH_DIR = "authorisation"
TOKEN_PATH = os.path.join(AUTH_DIR, "token.json")
# This is the specific client secret file in the authorisation folder
CREDENTIALS_PATH = os.path.join(AUTH_DIR, "credentials.json")

def get_calendar_service():
    """
    Handles OAuth2 authentication and returns an authenticated Calendar service.
    
    - First run: opens a browser for the user to log in and grant permission.
    - Subsequent runs: loads saved credentials from token.json (no browser needed).
    """
    creds = None

    # token.json stores the user's access and refresh tokens after first login
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # If credentials are missing or expired, refresh or re-authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Silently refresh using stored refresh token
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)  # Opens browser for login

        # Save credentials so we don't need to log in again next time
        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    # Build and return the Calendar API client
    return build("calendar", "v3", credentials=creds)


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
    service = get_calendar_service()

    # Build the event payload
    event = {
        "summary": f"🌍 Holiday: {destination}",
        "description": notes,
        "start": {
            "date": start_date,       # "date" (not "dateTime") = all-day event
            "timeZone": "Europe/London",
        },
        "end": {
            "date": end_date,         # Google Calendar treats end date as exclusive
            "timeZone": "Europe/London",
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email",  "minutes": 7 * 24 * 60},  # Email 1 week before
                {"method": "popup",  "minutes": 24 * 60},       # Popup 1 day before
            ],
        },
    }

    # Insert the event into the primary calendar
    created_event = service.events().insert(
        calendarId="primary",
        body=event
    ).execute()

    return {
        "event_id":   created_event["id"],
        "summary":    created_event["summary"],
        "start":      created_event["start"]["date"],
        "end":        created_event["end"]["date"],
        "event_link": created_event.get("htmlLink"),
    }
