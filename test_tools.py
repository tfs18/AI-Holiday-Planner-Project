from logs.logging_config import setup_logging
setup_logging()

from tools.weather.weather_tool import get_forecasts_for_country, pretty_print_forecasts

result = get_forecasts_for_country("GB")
pretty_print_forecasts(result)