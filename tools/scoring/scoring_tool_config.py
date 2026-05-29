# scoring_tool_config.py

WMO_CLEAR = {0, 1}
WMO_PARTLY_CLOUDY = {2, 3}
WMO_RAIN = {51, 53, 55, 61, 63, 65, 80, 81, 82}
WMO_SNOW = {71, 73, 75, 77, 85, 86}
WMO_STORM = {95, 96, 99}

WMO_DESCRIPTIONS = {
    0:  "Clear sky",        1:  "Mainly clear",
    2:  "Partly cloudy",    3:  "Overcast",
    45: "Fog",              48: "Rime fog",
    51: "Light drizzle",    53: "Moderate drizzle",    55: "Dense drizzle",
    56: "Light freezing drizzle",                      57: "Dense freezing drizzle",
    61: "Slight rain",      63: "Moderate rain",       65: "Heavy rain",
    66: "Light freezing rain",                         67: "Heavy freezing rain",
    71: "Slight snowfall",  73: "Moderate snowfall",   75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

PREFERENCE_WEIGHTS = {
    "warm": {
        "temperature": 0.50,
        "rain":        -0.30,
        "wind":        -0.10,
        "snow":        -0.10,
    },
    "cold": {
        "temperature": -0.55,
        "snow":        0.30,
        "wind":        -0.15,
        "rain":        -0.00,
    },
    "dry": {
        "rain":        -0.60,
        "wind":        -0.15,
        "temperature": 0.15,
        "snow":        -0.10,
    },
    "sunny": {
        "rain":        -0.50,
        "temperature": 0.30,
        "wind":        -0.10,
        "snow":        -0.10,
    },
    "windy": {
        "wind":        0.70,
        "temperature": 0.20,
        "rain":        -0.10,
        "snow":        0.00,
    },
    "skiing": {
        "snow":        0.60,
        "temperature": -0.25,
        "wind":        -0.15,
        "rain":        0.00,
    },
}