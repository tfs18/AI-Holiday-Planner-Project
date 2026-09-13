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

client = genai.Client(api_key=os.environ["GEMINI_API_KEY_MAX"])
MODEL = "gemini-2.5-flash-lite"
MAX_TURNS = 20

# Tools available to the agent — rank_days is intentionally excluded.
# It is called internally after get_weather_forecast and its result is
# injected into the tool response, so the agent sees scores without
# being able to invoke the scorer directly.
tools = [get_top_cities, create_holiday_event, delete_calendar_event, get_weather_forecast]


def extract_preference(user_input: str) -> str:
    """
    Uses the model to extract a weather preference from the user's message.
    Handles synonyms and negations (e.g. 'not cold' -> 'warm') more robustly
    than simple keyword matching.
    """
    response = client.models.generate_content(
        model=MODEL,
        contents=user_input,
        config=types.GenerateContentConfig(
            system_instruction=(
                "Extract the user's weather preference. Return exactly one of: warm, sunny, cold, rainy, windy, snowy, balanced. "
                "Examples: 'I want somewhere hot' -> warm, 'I hate rain' -> sunny, 'Not cold please' -> warm, 'I love snow' -> snowy, "
                "'I don't care' -> balanced. Return only the single word."
            )
        )
    )
    preference = response.text.strip().lower()
    valid = {"warm", "sunny", "cold", "rainy", "windy", "snowy", "balanced"}
    return preference if preference in valid else "balanced"


def agent_loop(user_input: str, history: list) -> str:
    """
    Main agent loop. Handles user input, model generation, and tool execution.

    rank_days is called internally within the get_weather_forecast dispatch block
    and its scores are injected into the tool response before being sent back to
    the model. This means the agent receives weather + scores as one atomic result
    without ever being able to call rank_days itself.
    """
    preference = extract_preference(user_input)
    print(f"\033[96m[Preference]:\033[0m {preference}")

    # Add user message to history
    history.append(types.Content(role="user", parts=[types.Part(text=user_input)]))

    # Inject extracted preference as a model turn so it's visible in context
    history.append(types.Content(role="model", parts=[types.Part(text=f"[system] preference={preference}")]))

    # Accumulates forecast day dicts across all cities for scoring
    all_forecasts: list = []

    # Forces get_top_cities on the first turn so the model always fetches
    # real city data rather than relying on its own knowledge
    first_turn = True

    for i in range(MAX_TURNS):

        # First turn: force get_top_cities to ensure real data is fetched.
        # Subsequent turns: AUTO lets the model decide what to do next.
        tool_config = types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="ANY",
                allowed_function_names=["get_top_cities"]
            )
        ) if first_turn else types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="AUTO")
        )
        first_turn = False

        response = client.models.generate_content(
            model=MODEL,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=tools,
                # Disable automatic function calling so we can manage
                # tool dispatch and history manually
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                tool_config=tool_config
            )
        )

        # Guard against empty responses from the model
        if not response.candidates:
            print("Warning: empty response from model")
            break

        candidate = response.candidates[0]
        if candidate.content is None or candidate.content.parts is None:
            print(f"Warning: empty candidate content. Finish reason: {candidate.finish_reason}")
            break

        # Append the full model response (including any function calls) to history
        history.append(candidate.content)

        # Print any internal reasoning/thought chains if present
        for part in response.parts:
            if part.thought:
                print(f"\033[94m[Agent's Thoughts]:\033[0m\n{part.text}\n")

        function_calls = [part.function_call for part in response.parts if part.function_call]

        # No function calls means the model has produced its final text response
        if not function_calls:
            return response.text

        tool_responses = []
        for call in function_calls:
            try:
                print(f"\033[93m[Action]:\033[0m Calling {call.name} with {call.args}...")

                if call.name == "get_top_cities":
                    result = get_top_cities(**call.args)
                    tool_responses.append(
                        types.Part.from_function_response(name=call.name, response={"result": result})
                    )

                elif call.name == "get_weather_forecast":
                    result = get_weather_forecast(**call.args)

                    # Collect all forecast days from the batch result and tag
                    # each day with its city name for use in scoring and display
                    if isinstance(result, dict) and result.get("status") == "success":
                        for city_forecast in result.get("data", []):
                            city_name = city_forecast.get("city", "unknown")
                            for day in city_forecast.get("forecast", []):
                                day["city"] = city_name
                                all_forecasts.append(day)

                    # Score all collected forecast days using the user's preference.
                    # rank_days is not exposed as an agent tool — it runs here and
                    # its output is embedded directly in the tool response so the
                    # model receives weather + scores as one enriched result.
                    ranked = rank_days(all_forecasts, preference)

                    if ranked.get("status") == "success" and ranked.get("data"):
                        top_3 = ranked["data"][:3]
                        ranking_payload = {
                            "top_3": [
                                {
                                    "city": d.get("city", "unknown"),
                                    "date": d["date"],
                                    "score": d["score"],
                                    "reason": d.get("description")
                                }
                                for d in top_3
                            ]
                        }

                    # Inject the enriched response — raw forecast data plus
                    # the top 3 scored days — back to the model as one result
                    tool_responses.append(
                        types.Part.from_function_response(
                            name="get_weather_forecast",
                            response={
                                "status": "success",
                                "data": result.get("data"),
                                "ranking": ranking_payload
                            }
                        )
                    )

                elif call.name == "create_holiday_event":
                    result = create_holiday_event(**call.args)
                    tool_responses.append(
                        types.Part.from_function_response(name=call.name, response={"result": result})
                    )

                elif call.name == "delete_calendar_event":
                    result = delete_calendar_event(**call.args)
                    tool_responses.append(
                        types.Part.from_function_response(name=call.name, response={"result": result})
                    )

                else:
                    tool_responses.append(
                        types.Part.from_function_response(name=call.name, response={"error": f"Tool {call.name} not found."})
                    )

                print(f"  └─ {call.name} completed")

            except Exception as e:
                import traceback
                print(f"  └─ ERROR in {call.name}: {e}")
                traceback.print_exc()
                tool_responses.append(
                    types.Part.from_function_response(name=call.name, response={"error": str(e)})
                )

        # Append all tool results as a user turn for the model to process
        history.append(types.Content(role="user", parts=tool_responses))

    # If MAX_TURNS is reached without a final response, ask the model to summarise
    print("Warning: reached the maximum number of turns without a final response")
    final_response = client.models.generate_content(
        model=MODEL,
        contents=history + [types.Content(
            role="user",
            parts=[types.Part(text="You've reached the maximum number of steps. Please summarise what you've found so far.")]
        )],
        config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
    )
    return final_response.text