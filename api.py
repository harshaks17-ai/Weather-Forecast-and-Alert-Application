"""FastAPI interface: run with `uvicorn api:app --reload`."""

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from src.weather_alert.alerts import AlertThresholds
from src.weather_alert.config import thresholds_from_environment
from src.weather_alert.service import WeatherService
from src.weather_alert.weather_client import WeatherAPIError

load_dotenv()

app = FastAPI(
    title="Weather Forecast & Alert API",
    description="Current conditions, daily forecast, and configurable risk alerts. Demo mode is offline sample data.",
    version="1.0.0",
)
service = WeatherService()


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "service": "weather-forecast-alert"}


@app.get("/weather/{city}", tags=["weather"])
def weather(
    city: str,
    source: str = "live",
    days: int = 5,
    max_temp: float | None = None,
    rain_probability: float | None = None,
    max_humidity: float | None = None,
    max_wind: float | None = None,
) -> dict:
    if source not in {"live", "demo"}:
        raise HTTPException(status_code=422, detail="source must be either 'live' or 'demo'.")
    if not 1 <= days <= 7:
        raise HTTPException(status_code=422, detail="days must be between 1 and 7.")
    if max_temp is not None and not -80 <= max_temp <= 70:
        raise HTTPException(status_code=422, detail="max_temp must be between -80 and 70.")
    if rain_probability is not None and not 0 <= rain_probability <= 100:
        raise HTTPException(status_code=422, detail="rain_probability must be between 0 and 100.")
    if max_humidity is not None and not 0 <= max_humidity <= 100:
        raise HTTPException(status_code=422, detail="max_humidity must be between 0 and 100.")
    if max_wind is not None and not 0 <= max_wind <= 500:
        raise HTTPException(status_code=422, detail="max_wind must be between 0 and 500.")
    defaults = thresholds_from_environment()
    thresholds = AlertThresholds(
        max_temperature_c=max_temp if max_temp is not None else defaults.max_temperature_c,
        rain_probability_pct=rain_probability if rain_probability is not None else defaults.rain_probability_pct,
        max_humidity_pct=max_humidity if max_humidity is not None else defaults.max_humidity_pct,
        max_wind_kmh=max_wind if max_wind is not None else defaults.max_wind_kmh,
        max_aqi=defaults.max_aqi,
    )
    try:
        report, alerts = service.get_report(city, source, days, thresholds)
        return {"weather": report.as_dict(), "alerts": alerts, "thresholds": thresholds.__dict__}
    except (WeatherAPIError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
