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

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview", contents="explain in a few words what the optimal diet is?"
)
print(response.text)
