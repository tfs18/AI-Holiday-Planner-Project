import os
from google import genai
from google.genai import types

from tools.workflow.workflow_tool import call_workflow
from agentConfig.sysInstructions import SYSTEM_INSTRUCTION

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Single exposed "function" — the model can only call this
call_workflow_declaration = types.FunctionDeclaration(
    name="call_workflow",
    description=(
        """
        Runs the full find and book a holiday workflow. The function
        finds the necessary locations, finds the weather forecast,
        identifies the best days, asks for user opinion, then books the 
        holiday to their calendar.
        """
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
        "country_code": types.Schema(
            type="STRING",
            description="ISO 3166-1 alpha-2 country code, e.g. 'US', 'JP', 'FR'",
        ),
        "weather_pref": types.Schema(
            type="STRING",
            enum=["warm", "cold", "dry", "sunny", "windy", "rainy", "skiing"],
            description="The kind of weather the user wants recommendations for",
        ),
    },
        required=["country_code", "weather_pref"],
    ),
)

workflow_tool = types.Tool(function_declarations=[call_workflow_declaration])

chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[workflow_tool]),
)

def agent_turn(user_message: str) -> str:
    response = chat.send_message(user_message)

    # response.function_calls is a convenience list the SDK provides
    calls = response.function_calls

    if not calls:
        # Model answered directly without invoking the workflow
        return response.text

    call = calls[0]

    if call.name == "call_workflow":
        workflow_result = call_workflow(**call.args)

        # Send the tool's result back so the model can produce
        # a final natural-language response
        follow_up = chat.send_message(
            types.Part.from_function_response(
                name="call_workflow",
                response={"result": workflow_result},
            )
        )
        return follow_up.text