"""A shared service layer used by the CLI, FastAPI, and Streamlit UI."""

from .alerts import AlertThresholds, generate_alerts
from .models import WeatherReport
from .weather_client import fetch_demo_weather, fetch_live_weather


class WeatherService:
    def get_report(self, city: str, source: str = "live", days: int = 5,
                   thresholds: AlertThresholds | None = None) -> tuple[WeatherReport, list[str]]:
        if source == "demo":
            report = fetch_demo_weather(city, days)
        elif source == "live":
            report = fetch_live_weather(city, days)
        else:
            raise ValueError("Source must be either 'live' or 'demo'.")
        return report, generate_alerts(report, thresholds or AlertThresholds())
