from google import genai
from google.genai import types
import os
from tools.city.city_tool import get_top_cities
from tools.calendar.calendar_tool import create_holiday_event, delete_calendar_event
from tools.weather.weather_tool import get_weather_forecast
from tools.scoring.scoring_tool import rank_days

from agentConfig.sysInstructions import SYSTEM_INSTRUCTION

from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-2.5-flash-lite"

def agent_loop(user_input: str, history: list) -> str:
    """
    Main agent loop that handles user input, model generation, 
    and recursive tool execution with manual history management.
    """
    # 1. Add user input to history
    history.append(
        types.Content(role="user", parts=[types.Part(text=user_input)])
    )

    tools = [get_top_cities, create_holiday_event, delete_calendar_event, get_weather_forecast, rank_days]

    while True:
        # 2. Generate content using the full conversation history
        response = client.models.generate_content(
            model=MODEL,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=tools
            )
        )

        # 3. Append the model's entire response (including thoughts and function calls) to history
        history.append(response.candidates[0].content)

        # 4. Handle thoughts (if the model is using thought chains)
        for part in response.parts:
            if part.thought:
                print(f"\033[94m[Agent's Thoughts]:\033[0m\n{part.text}\n")

        # 5. Identify and execute function calls
        function_calls = [part.function_call for part in response.parts if part.function_call]

        # If no function calls, the model has reached its final answer
        if not function_calls:
            return response.text

        tool_responses = []
        for call in function_calls:
            print(f"\033[93m[Action]:\033[0m Calling {call.name} with {call.args}...")
            
            # Dispatch to the correct tool function
            if call.name == "get_top_cities":
                result = get_top_cities(**call.args)
            elif call.name == "get_weather_forecast":
                result = get_weather_forecast(**call.args)
            elif call.name == "rank_days":
                result = rank_days(**call.args)
            elif call.name == "create_holiday_event":
                result = create_holiday_event(**call.args)
            elif call.name == "delete_calendar_event":
                result = delete_calendar_event(**call.args)
            else:
                result = f"Error: Tool {call.name} not found."
                
            print(f"  └─ Result: {result}")
            
            # Wrap the tool result in a Part
            tool_responses.append(
                types.Part.from_function_response(name=call.name, response={'result': result})
            )

        # 6. Append the tool results as a 'user' turn to the history for the model to process
        history.append(types.Content(role="user", parts=tool_responses))
        
        # The loop continues back to step 2 to let the model react to the tool results
