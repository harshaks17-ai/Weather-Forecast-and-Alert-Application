"""Small typed data models shared by the app entry points."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ForecastDay:
    date: str
    temp_max_c: float
    temp_min_c: float
    rain_probability_pct: int
    precipitation_mm: float
    max_wind_kmh: float
    weather_code: int
    description: str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class WeatherReport:
    city: str
    country: str
    latitude: float
    longitude: float
    timezone: str
    source: str
    observed_at: str
    temperature_c: float
    feels_like_c: float
    humidity_pct: int
    wind_kmh: float
    weather_code: int
    description: str
    forecast: list[ForecastDay]
    aqi: int | None = None

    def as_dict(self) -> dict:
        result = asdict(self)
        result["forecast"] = [day.as_dict() for day in self.forecast]
        return result
