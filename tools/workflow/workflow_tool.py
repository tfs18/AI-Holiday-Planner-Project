from datetime import datetime, timedelta

from tools.city.city_tool import get_top_cities
from tools.weather.weather_tool import get_weather_forecast
from tools.scoring.scoring_tool import rank_days
from tools.selection_box.selection_box_tool import selection_box_tool
from tools.calendar.calendar_tool import create_holiday_event

# city1 = get_top_cities('GB')["data"][0]
# forecast1 = get_weather_forecast(city1['name'], city1['latitude'], city1['longitude'])['data']['forecast']
# ranked_days = rank_days(forecast1, 'warm')['data'][0:3]

# choices = []
# for day in ranked_days:
#     choices.append({
#         'city': city1['name'],
#         'date': day['date'],
#         'weather': day['description'],
#         'score': day['score']
#     })
# #print(choices)
# result = selection_box_tool(choices)['data']

# create_holiday_event(
#     destination= result['city'],
#     start_date= result['date'],
#     end_date= '2026-09-13',
#     notes= "Test run"
# )

def call_workflow(country_code, weather_pref):
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

    result = selection_box_tool(choices)['data']

    date = result['date']
    next_date = (
    datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    create_holiday_event(
    destination= result['city'],
    start_date= date,
    end_date= next_date,
    notes= "Test run"
)