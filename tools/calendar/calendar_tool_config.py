import os

# Scopes define what permissions we're requesting
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Authorisation file configuration
AUTH_DIR = "authorisation"
TOKEN_FILENAME = "token.json"
CREDENTIALS_FILENAME = "credentials.json"

# Derived paths
TOKEN_PATH = os.path.join(AUTH_DIR, TOKEN_FILENAME)
CREDENTIALS_PATH = os.path.join(AUTH_DIR, CREDENTIALS_FILENAME)

# Calendar event defaults
DEFAULT_TIMEZONE = "Europe/London"
DEFAULT_REMINDERS = {
    "useDefault": False
}
