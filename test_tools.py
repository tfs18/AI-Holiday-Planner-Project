from pprint import pprint

from logs.logging_config import setup_logging
from tools.scoring.scoring_tool import rank_days_for_country, pretty_print_rankings

setup_logging()

from tools.city.city_tool import get_top_cities
from tools.weather.weather_tool import get_weather_forecast

cities = get_top_cities("ES")
pprint(cities)

city = cities["data"][0]
forecast = get_weather_forecast(city)
pprint(forecast)