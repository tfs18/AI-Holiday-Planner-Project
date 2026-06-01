from logs.logging_config import setup_logging
setup_logging()

from tools.city.city_tool import get_top_cities
from tools.weather.weather_tool import get_weather_forecast
from tools.scoring.scoring_tool import rank_days


def print_cities(cities_result):
    print("\n🌍 TOP CITIES")
    print("=" * 50)

    if cities_result["status"] != "success":
        print("Error:", cities_result["message"])
        return

    for i, city in enumerate(cities_result["data"], 1):
        print(f"{i:>2}. {city['name']} ({city['latitude']}, {city['longitude']})")


def print_scored_forecast(rank_result, city_name):
    print(f"\n📊 SCORED FORECAST — {city_name}")
    print("=" * 50)

    if rank_result["status"] != "success":
        print("Error:", rank_result["message"])
        return

    for day in rank_result["data"]:
        fs = day["factor_scores"]
        d = day["data"]

        print(
            f"{day['date']} | ⭐ {day['score']:>3} | {day['description']}"
        )
        print(
            f"   🌡 temp:{fs['temperature']:>3} ({d['temp_min']}–{d['temp_max']}°C) | "
            f"🌧 rain:{fs['rain']:>3} ({d['rain_sum']}mm, {d['precip_prob']}%) | "
            f"❄ snow:{fs['snow']:>3} ({d['snowfall_sum']}cm) | "
            f"💨 wind:{fs['wind']:>3} ({d['wind_speed']}km/h)"
        )


# -------------------
# RUN TEST FLOW
# -------------------

cities = get_top_cities("ES")
print_cities(cities)

if cities["status"] == "success" and cities["data"]:
    city = cities["data"][0]

    forecast = get_weather_forecast(city)

    if forecast["status"] == "success":
        ranked = rank_days(
            forecast["data"]["forecast"],
            preference="warm"   # change this as needed
        )

        print_scored_forecast(ranked, city["name"])