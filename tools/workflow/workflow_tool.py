from datetime import datetime, timedelta

from tools.city.city_tool import get_top_cities
from tools.weather.weather_tool import get_weather_forecast
from tools.scoring.scoring_tool import rank_days
from tools.selection_box.selection_box_tool import selection_box_tool
from tools.calendar.calendar_tool import create_holiday_event

import os
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def generate_event_description(destination: str, weather_pref: str) -> str:
    prompt = (
        f"Write a short, friendly calendar event description (2-3 sentences) for a holiday trip.\n"
        f"Destination: {destination}\n"
        f"Weather preference: {weather_pref}\n"
        f"Keep it concise and suitable for a calendar event body — no headers, no markdown."
        f"Describe the sort of thing that the user could do at this destination and weather."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text

def call_workflow(country_code, weather_pref):
    try:
        cities = get_top_cities(country_code)["data"]

        all_forecasts = []
        for city in cities:
            city_forecast = get_weather_forecast(
                city['name'], 
                city['latitude'], 
                city['longitude']) ['data']['forecast']

            for forecast in city_forecast:
                forecast['city'] = city['name'] 
                all_forecasts.append(forecast)

        final_ranks = rank_days(all_forecasts, weather_pref)['data'][0:3]

        choices = []
        for day in final_ranks:
            choices.append({
                'city': day['city'],
                'date': day['date'],
                'weather': day['description'],
                'score': day['score']
            })

        initial_result = selection_box_tool(choices)

        if initial_result['status'] == 'failure':
            return "You have aborted the booking process."

        result = initial_result['data']
        date = result['date']
        next_date = (
        datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")

        notes = generate_event_description(result['city'], weather_pref)

        create_holiday_event(
        destination= result['city'],
        start_date= date,
        end_date= next_date,
        notes= notes
        )
    except Exception as e:
        return "unfortunately there was an error with the function call"
    return f"A holiday to {result['city']} on the {result['date']} was successfully booked to your google calendar"