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

#TODO!
#Add validation of call.args, using inspect module, maybe pydantic model
#Test tool map when ted fixes his side of the code. 

client = genai.Client(api_key=os.environ["GEMINI_API_KEY_MAX"])
MODEL = "gemini-2.5-flash-lite"
tools = [get_top_cities, create_holiday_event, delete_calendar_event, get_weather_forecast]
tool_map = {tool.__name__: tool for tool in tools}
MAX_TURNS = 20

# uses the model to handle preference synonyms etc
# system instructions need to be more detailed - just a placeholder for now
def extract_preference(user_input: str) -> str:
    response = client.models.generate_content(
        model=MODEL,
        contents=user_input,
        config=types.GenerateContentConfig(
            system_instruction=(
                "Extract the user's weather preference. Return exactly one of: warm, sunny, cold, rainy, windy, snowy, balanced"
                "Examples: 'I want somewhere hot' -> warm, 'I hate rain' -> sunny, 'Not cold please' -> warm, 'I love snow' -> snowy, "
                "'I don't care' -> balanced. Return only the single word."
            )
        )
    )
    preference = response.text.strip().lower()
    print(f"\033[96m[Preference]:\033[0m {preference}")  # should print "rainy"
    valid = {"warm", "sunny", "cold", "rainy", "windy", "snowy", "balanced"}
    return preference if preference in valid else "balanced"

def agent_loop(user_input: str, history: list) -> str:
    preference = extract_preference(user_input)

    history.append(types.Content(role="user", parts=[types.Part(text=user_input)]))
    history.append(types.Content(role="model", parts=[types.Part(text=f"[system] preference={preference}")]))

    all_forecasts: list = []
    first_turn = True  # explicit flag instead of len(history) check

    for i in range(MAX_TURNS):
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
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                tool_config=tool_config
            )
        )

        # Guard against empty response before accessing .parts
        if response.candidates is None or not response.candidates:
            print("Warning: empty response from model")
            break

        candidate = response.candidates[0]
        if candidate.content is None or candidate.content.parts is None:
            print(f"Warning: empty candidate content. Finish reason: {candidate.finish_reason}")
            break

        history.append(candidate.content)

        for part in response.parts:
            if part.thought:
                print(f"\033[94m[Agent's Thoughts]:\033[0m\n{part.text}\n")
        
        # rest of loop continues...

        # 5. Identify and execute function calls
        function_calls = [part.function_call for part in response.parts if part.function_call]

        # If no function calls, the model has reached its final answer
        if not function_calls:
            print("\n=== FINAL AGENT RESPONSE ===")
            print(response.text)
            print("============================\n")
            return response.text

        tool_responses = []
        for call in function_calls:
            try:
                print(f"\033[93m[Action]:\033[0m Calling {call.name} with {call.args}...")

                if call.name == "get_top_cities":
                    result = get_top_cities(**call.args)
                elif call.name == "get_weather_forecast":
                    result = get_weather_forecast(**call.args)
                    print(f"  └─ Scoring {len(all_forecasts)} days with preference='{preference}'")

                    if isinstance(result, dict) and result.get("status") == "success":
                        for city_forecast in result.get("data", []):
                            city_name = city_forecast.get("city", "unknown")
                            for day in city_forecast.get("forecast", []):
                                day["city"] = city_name
                                all_forecasts.append(day)

                    print(f"  └─ Scoring {len(all_forecasts)} days with preference='{preference}'")
                    ranked = rank_days(all_forecasts, preference)
                    print(f"  └─ Ranked status: {ranked.get('status')}")

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
                        tool_responses.append(
                            types.Part.from_function_response(
                                name="get_weather_forecast",
                                response={
                                    "status": "success",
                                    "data": result["data"],
                                    "ranking": ranking_payload
                                }
                            )
                        )   
                    continue

                elif call.name == "create_holiday_event":
                    result = create_holiday_event(**call.args)
                elif call.name == "delete_calendar_event":
                    result = delete_calendar_event(**call.args)
                else:
                    result = f"Error: Tool {call.name} not found."

                print(f"  └─ Result: {result}")
                tool_responses.append(
                    types.Part.from_function_response(name=call.name, response={"result": result})
                )

            except Exception as e:
                import traceback
                print(f"  └─ ERROR in {call.name}: {e}")
                traceback.print_exc()  # prints the full stack trace with line numbers
                tool_responses.append(
                    types.Part.from_function_response(name=call.name, response={"error": str(e)})
                )
            
            # Wrap the tool result in a Part
            tool_responses.append(
                types.Part.from_function_response(name=call.name, response={'result': result})
            )

        # 6. Append the tool results as a 'user' turn to the history for the model to process
        history.append(types.Content(role="user", parts=tool_responses))
        
        # The loop continues back to step 2 to let the model react to the tool results

    # Final else loop to send final summarising prompt if max turns is reached
    else:
        print("Warning: reached the maximum number of turns without breaking")
        final_response = client.models.generate_content(
            model=MODEL,
            contents=history + [types.Content(
                role="user",
                parts=[types.Part(text="You've reached the maximum number of steps. Please summarise what you've done and what you found so far.")]
            )],
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
            # Note: no tools passed here, so model is forced to respond in text
        )
        return final_response.text
