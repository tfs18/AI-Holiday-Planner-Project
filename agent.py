from google import genai
from dotenv import load_dotenv
import os
from logs.logging_config import setup_logging
import logging

load_dotenv()

setup_logging()

#This is how to get the right logging instance.
logger = logging.getLogger("holiday-agent")

logger.info("App started")

# # The client gets the API key from the environment variable `GEMINI_API_KEY`.
# client = genai.Client()

# response = client.models.generate_content(
#     model="gemini-3-flash-preview", contents="explain in a few words what the optimal diet is?"
# )
# print(response.text)

# from tools.calendar.calendar_tool import *

# # holiday_event = create_holiday_event("fdsadf", "2026-05-27", "2026-05-28","fdasf")

# # print(holiday_event)
# #print(delete_calendar_event(holiday_event["data"]["event_id"]))
# print(delete_calendar_event('fe0d0dmvqfp4b3o2q8irrus4t8'))