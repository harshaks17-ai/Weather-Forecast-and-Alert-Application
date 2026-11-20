"""Transparent, user-configurable weather risk rules (not official warnings)."""

from dataclasses import dataclass

from .models import WeatherReport


@dataclass(frozen=True)
class AlertThresholds:
    max_temperature_c: float = 35
    rain_probability_pct: float = 60
    max_humidity_pct: float = 80
    max_wind_kmh: float = 50
    max_aqi: float = 100


def generate_alerts(report: WeatherReport, thresholds: AlertThresholds) -> list[str]:
    """Return current and next-days risk notices based on forecast data."""
    alerts: list[str] = []
    storm_codes = {95, 96, 99}
    if report.weather_code in storm_codes:
        alerts.append(f"Thunderstorm risk: current conditions are {report.description}.")
    if report.temperature_c >= thresholds.max_temperature_c:
        alerts.append(f"Heat risk: current temperature is {report.temperature_c:.1f} deg C.")
    if report.humidity_pct >= thresholds.max_humidity_pct:
        alerts.append(f"High humidity: currently {report.humidity_pct}%.")
    if report.wind_kmh >= thresholds.max_wind_kmh:
        alerts.append(f"Strong wind: currently {report.wind_kmh:.1f} km/h.")
    for day in report.forecast:
        if day.weather_code in storm_codes:
            alerts.append(f"Thunderstorm risk on {day.date}: forecast is {day.description}.")
        if day.rain_probability_pct >= thresholds.rain_probability_pct:
            alerts.append(
                f"Rain risk on {day.date}: probability {day.rain_probability_pct}% "
                f"({day.precipitation_mm:.1f} mm forecast)."
            )
        if day.temp_max_c >= thresholds.max_temperature_c:
            alerts.append(f"Heat risk on {day.date}: maximum {day.temp_max_c:.1f} deg C.")
        if day.max_wind_kmh >= thresholds.max_wind_kmh:
            alerts.append(f"Strong wind risk on {day.date}: maximum {day.max_wind_kmh:.1f} km/h.")
    if report.aqi is not None and report.aqi >= thresholds.max_aqi:
        alerts.append(f"Air-quality notice: AQI is {report.aqi} (configured limit {thresholds.max_aqi:g}).")
    return list(dict.fromkeys(alerts))
