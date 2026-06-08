from google import genai
from google.genai import types
import os

from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3-flash-preview"
SYSTEM_INSTRUCTION = (
    "You are a helpful holiday planning assistant. "
    "Help users plan trips, suggest destinations, activities, "
    "accommodation, and travel tips."
)

def agent_loop(user_input: str, history: list) -> str:
    history.append(
        types.Content(role="user", parts=[types.Part(text=user_input)])
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=history,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
        )
    )

    reply = response.text

    history.append(
        types.Content(role="model", parts=[types.Part(text=reply)])
    )

    return reply