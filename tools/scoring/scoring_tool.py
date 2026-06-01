import logging
from typing import Any, Dict, List
# from tools.city.city_tool import get_top_cities
# from tools.weather.weather_tool import get_weather_forecast
from tools.scoring import scoring_tool_config as config

logger = logging.getLogger(__name__)

# =========================================================
# INDIVIDUAL FACTOR SCORES (0-100)
# =========================================================

def score_temperature(temp_max: float) -> float:
    """Higher score = warmer day."""
    thresholds = [
        (28, 100), (27, 95), (26, 90), (25, 85), (24, 80),
        (23, 75),  (22, 70), (21, 65), (20, 60), (19, 55),
        (18, 50),  (17, 45), (16, 40), (15, 35), (14, 30),
        (13, 25),  (12, 20), (11, 15), (10, 10), (9, 5), (8, 3),
    ]
    for threshold, score in thresholds:
        if temp_max >= threshold:
            return score
    return 0


def score_rain(rain_sum: float, precip_prob: int) -> float:
    """Higher score = more rain."""
    base = (precip_prob * 0.6) + (rain_sum * 8)
    return min(100, base)


def score_snow(snowfall_sum: float) -> float:
    """Higher score = more snow."""
    if snowfall_sum >= 10:  return 100
    if snowfall_sum >= 5:   return 75
    if snowfall_sum >= 2:   return 50
    if snowfall_sum >= 0.5: return 25
    return 0


def score_wind(wind_speed: float) -> float:
    """Higher score = more wind."""
    if wind_speed > 40: return 100
    if wind_speed > 30: return 75
    if wind_speed > 20: return 50
    if wind_speed > 10: return 25
    return 0


# def score_sunshine(weather_code: int) -> float:
#     """Higher score = sunnier day."""
#     if weather_code in config.WMO_CLEAR:           base = 100
#     elif weather_code in config.WMO_PARTLY_CLOUDY: base = 60
#     elif weather_code in config.WMO_RAIN:          base = 20
#     elif weather_code in config.WMO_STORM:         base = 0
#     else:                                          base = 40
#     return min(100, base)


# =========================================================
# VALIDATION
# =========================================================

def validate_preference(preference: str) -> bool:
    """
    Validates that the preference is a known scoring profile.

    Args:
        preference: The preference string to validate.

    Returns:
        True if valid, False otherwise.
    """
    return preference in config.PREFERENCE_WEIGHTS


def validate_forecast_fields(day: Dict[str, Any]) -> None:
    required_fields = [
        "date",
        "weather_code",
        "temp_max",
        "temp_min",
        "rain_sum",
        "snowfall_sum",
        "wind_speed_max",
        "precipitation_probability_max",
    ]

    missing = [f for f in required_fields if f not in day]

    if missing:
        raise ValueError(f"Forecast day is missing required fields: {missing}")


# =========================================================
# COMBINED SCORER
# =========================================================

def score_day(
    date: str,
    temp_max: float,
    temp_min: float,
    rain_sum: float,
    snowfall_sum: float,
    precip_prob: int,
    wind_speed: float,
    weather_code: int,
    preference: str,
) -> Dict[str, Any]:
    weights = config.PREFERENCE_WEIGHTS[preference]

    temp_score = score_temperature(temp_max)
    rain_score = score_rain(rain_sum, precip_prob)
    snow_score = score_snow(snowfall_sum)
    wind_score = score_wind(wind_speed)

    total = (
        temp_score * weights["temperature"] +
        rain_score * weights["rain"] +
        snow_score * weights["snow"] +
        wind_score * weights["wind"]
    )

    logger.debug(
        f"{date} | score={round(total)} | "
        f"temp={round(temp_score)} rain={round(rain_score)} "
        f"snow={round(snow_score)} wind={round(wind_score)}"
    )

    return {
        "date":        date,
        "score":       round(total),
        "description": config.WMO_DESCRIPTIONS.get(weather_code, "Unknown"),
        "factor_scores": {
            "temperature": round(temp_score),
            "rain":        round(rain_score),
            "snow":        round(snow_score),
            "wind":        round(wind_score),
        },
        "data": {
            "temp_max":     temp_max,
            "temp_min":     temp_min,
            "rain_sum":     rain_sum,
            "snowfall_sum": snowfall_sum,
            "precip_prob":  precip_prob,
            "wind_speed":   wind_speed,
        }
    }


# =========================================================
# RANK ALL DAYS
# =========================================================

def rank_days(forecast_days: List[Dict[str, Any]], preference: str) -> Dict[str, Any]:

    if not validate_preference(preference):
        return {
            "status": "error",
            "message": f"Unknown preference '{preference}'. Valid options: {list(config.PREFERENCE_WEIGHTS.keys())}"
        }

    scored = []

    try:
        for day_data in forecast_days:

            validate_forecast_fields(day_data)

            day = score_day(
                date=day_data["date"],
                temp_max=day_data["temp_max"],
                temp_min=day_data["temp_min"],
                rain_sum=day_data["rain_sum"],
                snowfall_sum=day_data["snowfall_sum"],
                precip_prob=day_data["precipitation_probability_max"],
                wind_speed=day_data["wind_speed_max"],
                weather_code=day_data["weather_code"],
                preference=preference,
            )

            scored.append(day)

    except ValueError as e:
        return {
            "status": "error",
            "message": str(e)
        }

    return {
        "status": "success",
        "data": sorted(scored, key=lambda x: x["score"], reverse=True)
    }

# gives the agent a single score value for each city (this is probably later implementation 
# (outside scope as this is for if a user wants to go somewhre for a week etc, provides average score))
# def score_forecast(forecast_days: List[Dict[str, Any]], preference: str,) -> Dict[str, Any]:

#     ranked = rank_days(forecast_days, preference)

#     if ranked["status"] == "error":
#         return ranked

#     days = ranked["data"]

#     scores = [d["score"] for d in days]

#     return {
#         "status": "success",
#         "data": {
#             "destination_score": round(sum(scores) / len(scores)),
#             "best_day_score": max(scores),
#             "ranked_days": days
#         }
#     }


# =========================================================
# RANK FOR A COUNTRY - OUT OF SCOPE, too many actions being performed in one tool, should have tool separation
# =========================================================

# def rank_days_for_country(country_code: str, preference: str) -> Dict[str, Any]:
#     """
#     Fetches cities and forecasts for a country and ranks each city's days.

#     Args:
#         country_code: ISO 3166-1 alpha-2 country code (e.g., 'GB', 'US').
#         preference: Scoring profile key from PREFERENCE_WEIGHTS.

#     Returns:
#         A dictionary containing:
#         - status: "success" or "error"
#         - data: List of {city, ranked_days} dicts (if success)
#         - message: Error description (if error)
#     """
#     if not validate_preference(preference):
#         return {
#             "status": "error",
#             "message": f"Unknown preference '{preference}'. Valid options: {list(config.PREFERENCE_WEIGHTS.keys())}"
#         }

#     logger.info(f"Ranking days for country: {country_code}, preference: {preference}")

#     cities = get_top_cities(country_code)
#     if cities["status"] == "error":
#         return cities

#     results = []
#     for city in cities["data"]:
#         forecast = get_weather_forecast(city)
#         if forecast["status"] == "error":
#             logger.warning(f"Skipping {city['name']}: {forecast['message']}")
#             continue

#         ranked = rank_days(forecast["data"]["forecast"], preference)
#         if ranked["status"] == "error":
#             logger.warning(f"Skipping {city['name']}: {ranked['message']}")
#             continue

#         results.append({
#             "city": city["name"],
#             "ranked_days": ranked["data"]
#         })

#     return {
#         "status": "success",
#         "data": results
#     }


# =========================================================
# PRETTY PRINT
# =========================================================

def pretty_print_rankings(result: Dict[str, Any]) -> None:
    if result["status"] == "error":
        print(f"Error: {result['message']}")
        return

    for city_result in result["data"]:
        print(f"\n{'='*50}")
        print(f"  {city_result['city']}")
        print(f"{'='*50}")
        for day in city_result["ranked_days"]:
            print(f"  {day['date']} | score: {day['score']:>4} | {day['description']}")
            print(f"    Temp (score: {day['factor_scores']['temperature']}):    {day['data']['temp_min']}°C - {day['data']['temp_max']}°C")
            print(f"    Rain (score: {day['factor_scores']['rain']}):    {day['data']['rain_sum']}mm, {day['data']['precip_prob']}%")
            print(f"    Snow (score: {day['factor_scores']['snow']}):    {day['data']['snowfall_sum']}cm")
            print(f"    Wind (score: {day['factor_scores']['wind']}):    {day['data']['wind_speed']}km/h")
            print()