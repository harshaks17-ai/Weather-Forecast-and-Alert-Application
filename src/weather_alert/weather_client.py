"""Open-Meteo client and deterministic offline demo provider."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import requests

from .models import ForecastDay, WeatherReport

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


class WeatherAPIError(RuntimeError):
    """An actionable error from geocoding or a weather API request."""


def weather_description(code: int) -> str:
    """Translate WMO weather interpretation codes to short labels."""
    descriptions = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Drizzle",
        55: "Dense drizzle", 56: "Freezing drizzle", 57: "Dense freezing drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 66: "Freezing rain",
        67: "Heavy freezing rain", 71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
        77: "Snow grains", 80: "Slight rain showers", 81: "Rain showers", 82: "Violent rain showers",
        85: "Snow showers", 86: "Heavy snow showers", 95: "Thunderstorm",
        96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
    }
    return descriptions.get(code, "Unknown conditions")


def _request_json(url: str, params: dict) -> dict:
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise WeatherAPIError("The weather service returned an unexpected JSON structure.")
        return payload
    except requests.Timeout as exc:
        raise WeatherAPIError("The weather service timed out. Please try again.") from exc
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        raise WeatherAPIError(f"Weather service returned HTTP {status}.") from exc
    except requests.RequestException as exc:
        raise WeatherAPIError("Could not reach the weather service. Check your connection.") from exc
    except ValueError as exc:
        raise WeatherAPIError("The weather service returned invalid JSON.") from exc


def fetch_live_weather(city: str, forecast_days: int = 5) -> WeatherReport:
    """Fetch geocoded current conditions and daily forecast from Open-Meteo."""
    city = city.strip()
    if not city:
        raise WeatherAPIError("City cannot be empty.")
    if not 1 <= forecast_days <= 7:
        raise WeatherAPIError("Forecast days must be between 1 and 7.")
    location_data = _request_json(GEOCODING_URL, {"name": city, "count": 1, "language": "en", "format": "json"})
    locations = location_data.get("results") or []
    if not isinstance(locations, list) or not locations:
        raise WeatherAPIError(f"No location found for '{city}'. Check the spelling and try again.")
    location = locations[0]
    if not isinstance(location, dict) or "latitude" not in location or "longitude" not in location:
        raise WeatherAPIError("Location service returned incomplete coordinates.")
    try:
        latitude, longitude = float(location["latitude"]), float(location["longitude"])
    except (TypeError, ValueError) as exc:
        raise WeatherAPIError("Location service returned invalid coordinates.") from exc
    params = {
        "latitude": latitude, "longitude": longitude, "current":
        "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max",
        "forecast_days": forecast_days, "timezone": "auto",
    }
    payload = _request_json(FORECAST_URL, params)
    # Air quality is optional and is not available for every location/time.
    # A separate endpoint keeps AQI failure from taking down the weather forecast.
    aqi: int | None = None
    try:
        air_payload = _request_json(AIR_QUALITY_URL, {
            "latitude": latitude, "longitude": longitude,
            "current": "us_aqi", "timezone": "auto",
        })
        air_current = air_payload.get("current") or {}
        if air_current.get("us_aqi") is not None:
            aqi = int(round(float(air_current["us_aqi"])))
    except (WeatherAPIError, TypeError, ValueError):
        pass
    current = payload.get("current") or {}
    daily = payload.get("daily") or {}
    required = ("time", "temperature_2m", "relative_humidity_2m", "apparent_temperature", "weather_code", "wind_speed_10m")
    if not isinstance(current, dict) or any(key not in current for key in required):
        raise WeatherAPIError("Weather response is missing current-condition fields.")
    daily_fields = ("time", "temperature_2m_max", "temperature_2m_min", "precipitation_probability_max", "precipitation_sum", "wind_speed_10m_max", "weather_code")
    if not isinstance(daily, dict) or any(key not in daily for key in daily_fields):
        raise WeatherAPIError("Weather response is missing daily forecast fields.")
    if not isinstance(daily["time"], list) or any(
        not isinstance(daily[field], list) or len(daily[field]) != len(daily["time"])
        for field in daily_fields[1:]
    ):
        raise WeatherAPIError("Weather service returned mismatched daily forecast fields.")
    forecast: list[ForecastDay] = []
    for index, date in enumerate(daily["time"]):
        try:
            code = int(daily["weather_code"][index])
            forecast.append(ForecastDay(
                date=date,
                temp_max_c=float(daily["temperature_2m_max"][index]),
                temp_min_c=float(daily["temperature_2m_min"][index]),
                rain_probability_pct=int(daily["precipitation_probability_max"][index] or 0),
                precipitation_mm=float(daily["precipitation_sum"][index] or 0),
                max_wind_kmh=float(daily["wind_speed_10m_max"][index]),
                weather_code=code, description=weather_description(code),
            ))
        except (IndexError, TypeError, ValueError) as exc:
            raise WeatherAPIError("Weather service returned an incomplete daily forecast.") from exc
    try:
        current_code = int(current["weather_code"])
        observed = str(current.get("time") or datetime.now(timezone.utc).isoformat())
        return WeatherReport(
            city=location.get("name", city), country=location.get("country", ""),
            latitude=latitude, longitude=longitude, timezone=payload.get("timezone", "UTC"),
            source="Open-Meteo live API", observed_at=observed,
            temperature_c=float(current["temperature_2m"]), feels_like_c=float(current["apparent_temperature"]),
            humidity_pct=int(current["relative_humidity_2m"]), wind_kmh=float(current["wind_speed_10m"]),
            weather_code=current_code, description=weather_description(current_code), forecast=forecast, aqi=aqi,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise WeatherAPIError("Weather service returned invalid current conditions.") from exc


def fetch_demo_weather(city: str, forecast_days: int = 5) -> WeatherReport:
    """Return a plausible, stable sample forecast without network access."""
    city = city.strip()
    if not city:
        raise WeatherAPIError("City cannot be empty.")
    if not 1 <= forecast_days <= 7:
        raise WeatherAPIError("Forecast days must be between 1 and 7.")
    sample = [
        (38, 27, 78, 0.0, 18, 1), (36, 26, 85, 8.2, 24, 63),
        (34, 25, 30, 0.0, 56, 2), (32, 24, 20, 0.0, 20, 3),
        (31, 23, 65, 4.5, 22, 61), (30, 22, 15, 0.0, 17, 1),
        (33, 24, 40, 0.2, 19, 2),
    ]
    today = date.today()
    forecast = [
        ForecastDay((today + timedelta(days=offset)).isoformat(), high, low, rain, mm, wind, code,
                    weather_description(code))
        for offset, (high, low, rain, mm, wind, code) in enumerate(sample[:forecast_days])
    ]
    return WeatherReport(
        city=city.title(), country="Demo", latitude=0.0, longitude=0.0, timezone="UTC",
        source="Offline demo data (not a live observation)",
        observed_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        temperature_c=38.0, feels_like_c=41.0, humidity_pct=84, wind_kmh=18.0,
        weather_code=1, description="Mainly clear (demo)", forecast=forecast,
    )
