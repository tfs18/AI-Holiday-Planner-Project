# AI Holiday Planner

A CLI tool for people planning holidays to use. Users can input a prompt specifying details about their ideal holiday, and the tool will identify the best times and locations. The user can then choose the destination they want to go to, and the tool will book out the holiday in their calendar.

## Video

## Technologies

| Technology        | Purpose                                                                  |
| ----------------- | ------------------------------------------------------------------------ |
| Python3           | Core language used for tool's development                                |
| Gemini Agents SDK | Powers the conversational agent and function-calling for slot extraction |
| Google Calendar   | Books the selected holiday as an event on the user's calendar            |
| Pytest            | Unit testing for workflow logic and function-calling behavior            |

## Features

Here's what you can do with the AI Holiday Planner:

- **Conversational:** describe what you want in plain language
  and the agent asks only for what's missing, remembering
  what you've already told it across the conversation

- **Natural language:** automatically converts country
  names to ISO country codes and loose weather descriptions
  to valid preference categories, without asking you to reformat your answer

- **Real-time weather analysis:** cross-references live
  forecast data against the user's weather preference to identify suitable
  locations and dates

- **Calendar booking:** books the selected trip directly to
  Google Calendar via the Calendar API, so you don't need to manually do so.

## The Process

## What I learned

## How to Run the Project

To run the project in your local environment, follow these steps:

1. Clone the repository to your local machine.
2. Create a virtual environment, using the command: `python -m venv venv_name` in your terminal
3. Activate the virtual environment: `source venv/bin/activate` on mac/linux, or `venv\Scripts\activate` on windows
4. Run the project: `python agent.py`
