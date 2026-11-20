"""Basic regression tests; run with `python -m unittest discover -s tests`."""

import unittest
import tempfile
from pathlib import Path

from src.weather_alert.alerts import AlertThresholds, generate_alerts
from src.weather_alert.reports import save_report
from src.weather_alert.service import WeatherService
from src.weather_alert.weather_client import WeatherAPIError, fetch_demo_weather
from api import health, weather as api_weather


class WeatherAlertTests(unittest.TestCase):
    def test_demo_forecast_has_requested_length(self):
        report = fetch_demo_weather("test city", 3)
        self.assertEqual(len(report.forecast), 3)
        self.assertEqual(report.city, "Test City")

    def test_demo_triggers_multiple_alert_categories(self):
        report = fetch_demo_weather("Test City", 5)
        alerts = generate_alerts(report, AlertThresholds())
        self.assertTrue(any("Heat risk" in alert for alert in alerts))
        self.assertTrue(any("humidity" in alert.lower() for alert in alerts))
        self.assertTrue(any("Rain risk" in alert for alert in alerts))
        self.assertTrue(any("wind" in alert.lower() for alert in alerts))

    def test_empty_city_is_rejected(self):
        with self.assertRaises(WeatherAPIError):
            fetch_demo_weather("   ")

    def test_days_are_validated(self):
        with self.assertRaises(WeatherAPIError):
            fetch_demo_weather("Paris", 0)

    def test_service_returns_demo_report_and_alerts(self):
        report, alerts = WeatherService().get_report("Paris", "demo", 2)
        self.assertEqual(report.source, "Offline demo data (not a live observation)")
        self.assertGreater(len(alerts), 0)

    def test_report_writer_creates_csv_json_and_chart(self):
        report, alerts = WeatherService().get_report("Paris", "demo", 2)
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = save_report(report, alerts, AlertThresholds(), temp_dir)
            self.assertEqual(set(paths), {"csv", "json", "chart"})
            self.assertTrue(all(Path(path).is_file() and Path(path).stat().st_size > 0
                                for path in paths.values()))

    def test_api_health_and_offline_weather_route(self):
        self.assertEqual(health()["status"], "ok")
        payload = api_weather("Paris", source="demo", days=3)
        self.assertEqual(len(payload["weather"]["forecast"]), 3)
        self.assertGreater(len(payload["alerts"]), 0)

    def test_api_rejects_invalid_parameters(self):
        from fastapi import HTTPException

        with self.assertRaises(HTTPException) as caught:
            api_weather("Paris", source="unknown")
        self.assertEqual(caught.exception.status_code, 422)


if __name__ == "__main__":
    unittest.main()
