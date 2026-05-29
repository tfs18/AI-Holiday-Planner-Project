# from logs.logging_config import setup_logging
# setup_logging()

# from tools.weather.weather_tool import get_forecasts_for_country, pretty_print_forecasts

# result = get_forecasts_for_country("GB")
# pretty_print_forecasts(result)

from logs.logging_config import setup_logging
from tools.scoring.scoring_tool import rank_days_for_country, pretty_print_rankings

setup_logging()

result = rank_days_for_country("GB", "warm")
pretty_print_rankings(result)