import pytest

from tools.scoring.scoring_tool import (
    score_temperature,
    score_rain,
    score_snow,
    score_wind,
    validate_preference,
    validate_forecast_fields,
    score_day,
    rank_days,
)

# =========================================================
# INDIVIDUAL SCORERS
# =========================================================

@pytest.mark.parametrize(
    "temp_max,temp_min,expected",
    [
        (35, 25, 90),
        (30, 20, 80),
        (20, 10, 50),
        (8, 4, 0),
    ],
)
def test_score_temperature(temp_max, temp_min, expected):
    assert score_temperature(temp_max, temp_min) == expected

@pytest.mark.parametrize(
    "rain_sum,precip_prob,expected",
    [
        (0, 0, 0),
        (1, 50, 22),   # 7 + 15
        (5, 50, 50),   # 35 + 15
        (20, 100, 100),
    ],
)
def test_score_rain(rain_sum, precip_prob, expected):
    assert round(score_rain(rain_sum, precip_prob)) == expected

@pytest.mark.parametrize(
    "snowfall_sum,expected",
    [
        (0, 0),
        (5, 25),
        (10, 50),
        (20, 100),
        (30, 100),
    ],
)
def test_score_snow(snowfall_sum, expected):
    assert score_snow(snowfall_sum) == expected

@pytest.mark.parametrize(
    "wind_speed,expected",
    [
        (0, 0),
        (15, 25),
        (30, 50),
        (60, 100),
        (80, 100),
    ],
)
def test_score_wind(wind_speed, expected):
    assert round(score_wind(wind_speed)) == expected

# =========================================================
# VALIDATION
# =========================================================

@pytest.mark.parametrize(
    "preference",
    [
        "warm",
        "cold",
        "dry",
        "sunny",
        "windy",
        "rainy",
        "skiing",
    ],
)
def test_validate_preference_valid(preference):
    assert validate_preference(preference) is True

@pytest.mark.parametrize(
    "preference",
    [
        "hot",
        "beach",
        "",
        None,
    ],
)
def test_validate_preference_invalid(preference):
    assert validate_preference(preference) is False

def test_validate_forecast_fields_success():
    day = {
        "date": "2025-07-01",
        "weather_code": 0,
        "temp_max": 28,
        "temp_min": 18,
        "rain_sum": 0,
        "snowfall_sum": 0,
        "wind_speed_max": 10,
        "precipitation_probability_max": 0,
    }

    validate_forecast_fields(day)

def test_validate_forecast_fields_missing():
    with pytest.raises(
        ValueError,
        match="Forecast day is missing required fields"
    ):
        validate_forecast_fields(
            {
                "date": "2025-07-01"
            }
        )

# =========================================================
# SCORE DAY
# =========================================================

def test_score_day_success():

    result = score_day(
        date="2025-07-01",
        temp_max=30,
        temp_min=20,
        rain_sum=0,
        snowfall_sum=0,
        precip_prob=0,
        wind_speed=5,
        weather_code=0,
        preference="warm",
    )

    assert result["date"] == "2025-07-01"
    assert result["description"] == "Clear sky"

    assert "factor_scores" in result
    assert "data" in result
    assert isinstance(result["score"], int)

def test_score_day_unknown_weather_code():

    result = score_day(
        date="2025-07-01",
        temp_max=25,
        temp_min=15,
        rain_sum=0,
        snowfall_sum=0,
        precip_prob=0,
        wind_speed=5,
        weather_code=999,
        preference="warm",
    )

    assert result["description"] == "Unknown"

# =========================================================
# RANK DAYS
# =========================================================

def test_rank_days_success():

    forecast = [
        {
            "date": "2025-07-01",
            "weather_code": 0,
            "temp_max": 30,
            "temp_min": 20,
            "rain_sum": 0,
            "snowfall_sum": 0,
            "wind_speed_max": 5,
            "precipitation_probability_max": 0,
        },
        {
            "date": "2025-07-02",
            "weather_code": 61,
            "temp_max": 18,
            "temp_min": 12,
            "rain_sum": 10,
            "snowfall_sum": 0,
            "wind_speed_max": 20,
            "precipitation_probability_max": 90,
        },
    ]

    result = rank_days(forecast, "warm")

    assert result["status"] == "success"
    assert len(result["data"]) == 2

    assert result["data"][0]["date"] == "2025-07-01"

def test_rank_days_invalid_preference():

    result = rank_days([], "beach")

    assert result["status"] == "error"
    assert "Unknown preference" in result["message"]

def test_rank_days_missing_field():

    forecast = [
        {
            "date": "2025-07-01",
            "weather_code": 0,
        }
    ]

    result = rank_days(forecast, "warm")

    assert result["status"] == "error"
    assert "missing required fields" in result["message"]

def test_warm_preference_prefers_hot_day():

    forecast = [
        {
            "date": "cold",
            "weather_code": 0,
            "temp_max": 10,
            "temp_min": 5,
            "rain_sum": 0,
            "snowfall_sum": 0,
            "wind_speed_max": 5,
            "precipitation_probability_max": 0,
        },
        {
            "date": "warm",
            "weather_code": 0,
            "temp_max": 30,
            "temp_min": 20,
            "rain_sum": 0,
            "snowfall_sum": 0,
            "wind_speed_max": 5,
            "precipitation_probability_max": 0,
        },
    ]

    result = rank_days(forecast, "warm")

    assert result["data"][0]["date"] == "warm"