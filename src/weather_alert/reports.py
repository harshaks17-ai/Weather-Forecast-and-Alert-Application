"""CSV, JSON, and chart output helpers."""

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import matplotlib.dates as mdates

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .alerts import AlertThresholds
from .models import WeatherReport


def save_report(report: WeatherReport, alerts: list[str], thresholds: AlertThresholds,
                output_dir: str | Path = "outputs") -> dict[str, str]:
    """Save one normalized forecast CSV, JSON summary, and PNG chart."""
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    slug = "_".join(report.city.lower().split()) or "city"
    base = folder / f"weather_{slug}_{stamp}"
    frame = pd.DataFrame([day.as_dict() for day in report.forecast])
    csv_path, json_path, chart_path = base.with_suffix(".csv"), base.with_suffix(".json"), base.with_suffix(".png")
    frame.to_csv(csv_path, index=False)
    payload = report.as_dict()
    payload["alerts"] = alerts
    payload["thresholds"] = thresholds.__dict__
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    fig, axis = plt.subplots(figsize=(9, 4.8))
    dates = [datetime.strptime(day.date, "%Y-%m-%d") for day in report.forecast]
    axis.plot(dates, [day.temp_max_c for day in report.forecast], marker="o", label="High °C", color="#f97316")
    axis.plot(dates, [day.temp_min_c for day in report.forecast], marker="o", label="Low °C", color="#0284c7")
    axis.set_title(f"{report.city} — {len(report.forecast)}-day temperature forecast")
    axis.set_ylabel("Temperature (°C)")
    axis.set_xlabel("Local forecast date")
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    axis.grid(True, alpha=0.25)
    axis.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    return {"csv": str(csv_path), "json": str(json_path), "chart": str(chart_path)}
