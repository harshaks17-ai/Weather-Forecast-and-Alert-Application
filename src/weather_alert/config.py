"""Environment-backed defaults for alert thresholds."""

import os

from .alerts import AlertThresholds


def thresholds_from_environment() -> AlertThresholds:
    """Read optional numeric thresholds; malformed values use safe defaults."""

    def number(name: str, default: float) -> float:
        try:
            return float(os.getenv(name, default))
        except (TypeError, ValueError):
            return default

    return AlertThresholds(
        max_temperature_c=number("ALERT_MAX_TEMPERATURE_C", 35),
        rain_probability_pct=number("ALERT_RAIN_PROBABILITY_PCT", 60),
        max_humidity_pct=number("ALERT_MAX_HUMIDITY_PCT", 80),
        max_wind_kmh=number("ALERT_MAX_WIND_KMH", 50),
        max_aqi=number("ALERT_MAX_AQI", 100),
    )
