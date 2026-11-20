"""Command-line entry point for the Weather Forecast & Alert Application."""

from __future__ import annotations

import argparse
import logging
import sys

from dotenv import load_dotenv

from src.weather_alert.alerts import AlertThresholds
from src.weather_alert.config import thresholds_from_environment
from src.weather_alert.reports import save_report
from src.weather_alert.service import WeatherService
from src.weather_alert.weather_client import WeatherAPIError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch a forecast, check weather risks, and save a report.")
    parser.add_argument("--city", help="City to look up (if omitted, you will be prompted).")
    parser.add_argument("--source", choices=("live", "demo"), default="live", help="Use live Open-Meteo API or offline sample data.")
    parser.add_argument("--days", type=int, default=5, help="Forecast length (1-7 days).")
    parser.add_argument("--max-temp", type=float, help="Heat alert threshold in °C.")
    parser.add_argument("--rain-probability", type=float, help="Rain alert threshold in percent.")
    parser.add_argument("--max-humidity", type=float, help="Humidity alert threshold in percent.")
    parser.add_argument("--max-wind", type=float, help="Wind alert threshold in km/h.")
    parser.add_argument("--output-dir", default="outputs", help="Folder for generated CSV, JSON, and PNG files.")
    return parser


def main() -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = build_parser().parse_args()
    city = (args.city or input("Enter a city: ")).strip()
    if not city:
        print("Error: city cannot be empty.", file=sys.stderr)
        return 2
    defaults = thresholds_from_environment()
    thresholds = AlertThresholds(
        max_temperature_c=args.max_temp if args.max_temp is not None else defaults.max_temperature_c,
        rain_probability_pct=args.rain_probability if args.rain_probability is not None else defaults.rain_probability_pct,
        max_humidity_pct=args.max_humidity if args.max_humidity is not None else defaults.max_humidity_pct,
        max_wind_kmh=args.max_wind if args.max_wind is not None else defaults.max_wind_kmh,
        max_aqi=defaults.max_aqi,
    )
    try:
        report, alerts = WeatherService().get_report(city, args.source, args.days, thresholds)
        print(f"\nWeather Forecast & Alert Application - {report.city}, {report.country}")
        print(f"Source: {report.source} | Local time: {report.observed_at} | {report.timezone}")
        print(f"Now: {report.temperature_c:.1f} deg C (feels like {report.feels_like_c:.1f} deg C), "
              f"{report.description}, humidity {report.humidity_pct}%, wind {report.wind_kmh:.1f} km/h")
        if report.aqi is not None:
            print(f"Current AQI (US scale): {report.aqi}")
        print("\nForecast:")
        for day in report.forecast:
            print(f"  {day.date}: {day.description}; {day.temp_min_c:.1f}-{day.temp_max_c:.1f} deg C; "
                  f"rain {day.rain_probability_pct}% ({day.precipitation_mm:.1f} mm); wind {day.max_wind_kmh:.1f} km/h")
        print("\nAlerts:")
        if alerts:
            for alert in alerts:
                print(f"  [ALERT] {alert}")
        else:
            print("  No configured risk thresholds were triggered.")
        paths = save_report(report, alerts, thresholds, args.output_dir)
        print("\nSaved files:")
        for kind, path in paths.items():
            print(f"  {kind.upper()}: {path}")
        if args.source == "demo":
            print("\nNote: demo conditions are illustrative sample data, not a live forecast.")
        return 0
    except (WeatherAPIError, ValueError, OSError) as exc:
        logging.error("%s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
