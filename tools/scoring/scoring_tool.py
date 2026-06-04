import logging
from typing import Any, Dict, List
from tools.scoring import scoring_tool_config as config

logger = logging.getLogger(__name__)

# =========================================================
# INDIVIDUAL FACTOR SCORES (0-100)
# =========================================================

def score_temperature(temp_max: float, temp_min: float) -> float:
    """Higher score = warmer day (weighted by max and min temps)."""
    
    temp = 0.7 * temp_max + 0.3 * temp_min

    thresholds = [
        (35, 100), (33, 95), (31, 90), (29, 85), (27, 80),
        (25, 75), (23, 70), (21, 65), (19, 60), (17, 50), 
        (15, 40), (13, 30), (11, 20), (9, 10),
    ]

    for threshold, score in thresholds:
        if temp >= threshold:
            return score

    return 0

def score_rain(rain_sum: float, precip_prob: int) -> float:
    rain_component = rain_sum * 7
    prob_component = precip_prob * 0.3

    return min(100, rain_component + prob_component)

def score_snow(snowfall_sum: float) -> float:
    """Higher score = more snow."""
    return min(100, (snowfall_sum / 20) * 100)

def score_wind(wind_speed: float) -> float:
    """Higher score = more wind."""
    return min(100, (wind_speed / 60) * 100)

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

    temp_score = score_temperature(temp_max, temp_min)
    rain_score = score_rain(rain_sum, precip_prob)
    snow_score = min(100, snowfall_sum * 5)      # 20cm = 100
    wind_score = min(100, wind_speed * 1.67)     # 60km/h = 100

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