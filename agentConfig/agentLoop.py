from google import genai
from google.genai import types
import os
from tools.city.city_tool import get_top_cities
from tools.calendar.calendar_tool import create_holiday_event, delete_calendar_event
from tools.weather.weather_tool import get_weather_forecast
from functions.scoring.scoring import rank_days

from agentConfig.sysInstructions import SYSTEM_INSTRUCTION

from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-2.5-flash"

# uses the model to handle preference synonyms etc
# system instructions need to be more detailed - just a placeholder for now
def extract_preference(user_input: str) -> str:
    response = client.models.generate_content(
        model=MODEL,
        contents=user_input,
        config=types.GenerateContentConfig(
            system_instruction=(
                "Extract the user's weather preference from their message. "
                "Reply with exactly one word from: warm, sunny, cold, rainy, windy, snowy, balanced. "
                "If they express a negative preference (e.g. 'not sunny', 'avoid rain'), "
                "return 'balanced'. If unclear, return 'balanced'."
            )
        )
    )
    preference = response.text.strip().lower()
    print(f"\033[96m[Preference]:\033[0m {preference}")  # should print "rainy"
    valid = {"warm", "sunny", "cold", "rainy", "windy", "snowy", "balanced"}
    return preference if preference in valid else "balanced"

# A placeholder so the SDK can resolve the rank_days name in history
# without the model being able to invoke it as a real tool
def rank_days_placeholder(forecast_days: list[dict], preference: str) -> dict:
    """Internal scoring tool — not called by the agent."""
    pass
def agent_loop(user_input: str, history: list) -> str:
    """
    Main agent loop that handles user input, model generation, 
    and recursive tool execution with manual history management.
    """
    # need to dynamically extract preference and pass it to scoring function
    preference = extract_preference(user_input)

    # 1. Add user input to history
    history.append(
        types.Content(role="user", parts=[types.Part(text=user_input)])
    )

    tools = [get_top_cities, create_holiday_event, delete_calendar_event, get_weather_forecast, rank_days_placeholder]

    # Flat list of forecast day dicts across all cities
    all_forecasts: list = []  

    while True:
        # 2. Generate content using the full conversation history
        response = client.models.generate_content(
            model=MODEL,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=tools,
                # managing tool dispatch manually in the loop, the SDK's automatic function calling consuming the response and returning an empty result. Disabling it gives you full control back.
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )
        )

        # 3. Append the model's entire response (including thoughts and function calls) to history
        history.append(response.candidates[0].content)
        
        # THIS IS CAUSING A 'NoneType' error? idk why
        # 4. Handle thoughts (if the model is using thought chains)
        # for part in response.parts:
        #     if part.thought:
        #         print(f"\033[94m[Agent's Thoughts]:\033[0m\n{part.text}\n")

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
                # extracts the forecast days from the weather tools response and adds them to all_forecasts
                if isinstance(result, dict) and result.get("status") == "success":
                    days = result.get("data", {}).get("forecast", [])
                    city_name = result.get("data", {}).get("city", "unknown")
                    for day in days:
                        day["city"] = city_name  # tag each day with its city before extending
                    all_forecasts.extend(days)
                    print(f"\033[96m[Forecasts Collected]:\033[0m {len(all_forecasts)} days total so far")
            # SDK still tries to call rank_days - so need a dummy version here
            elif call.name == "rank_days_placeholder":
                result = {"status": "error", "message": "This tool is not available."}
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
        
        # Score after each dispatch round once we have forecast data.
        # rank_days validates each day's fields internally and returns
        # {"status": "success", "data": [sorted day dicts...]} or {"status": "error", ...}
        if all_forecasts:
            ranked = rank_days(forecast_days=all_forecasts, preference=preference)
            print(f"\033[92m[Scorer]:\033[0m rank_days → {ranked['status']}")
            if ranked["status"] == "success":
                for day in ranked["data"][:3]:  # top 3 ranked days
                    print(f"  └─ {day['date']} | score={day['score']} | {day['description']} | factors={day['factor_scores']}")
            history.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(
                        name="rank_days",
                        response={"result": ranked}
                    )]
                )
            )
            # Reset to avoid re-scoring on the next loop iteration
            all_forecasts = []  