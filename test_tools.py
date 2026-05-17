# test_tools.py
import json
from tools.weather.weather_tool import get_forecasts_for_country

result = get_forecasts_for_country("GB")
print(json.dumps(result, indent=4))