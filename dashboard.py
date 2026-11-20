"""Streamlit dashboard: run with `streamlit run dashboard.py`."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.weather_alert.config import thresholds_from_environment
from src.weather_alert.reports import save_report
from src.weather_alert.service import WeatherService
from src.weather_alert.weather_client import WeatherAPIError

load_dotenv(ROOT / ".env")
st.set_page_config(page_title="SkyWatch | Weather Alerts", page_icon="🌦️", layout="wide")
st.markdown("""
<style>
  .stApp { background: linear-gradient(150deg, #f4f9ff 0%, #f7f5ff 56%, #fffaf3 100%); }
  .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3,
  .stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stMarkdownContainer"] { color: #172033; }
  [data-testid="stMetric"] { background: rgba(255,255,255,.82); border: 1px solid #dce7f3;
    padding: 16px 18px; border-radius: 16px; box-shadow: 0 5px 18px rgba(31,61,89,.06); }
  [data-testid="stSidebar"] { background: #f0f6fc; }
  [data-baseweb="input"] input, [data-baseweb="select"] > div,
  [data-baseweb="textarea"] textarea { background: #fff; color: #172033; }
  h1 { letter-spacing: -1.4px; }
</style>
""", unsafe_allow_html=True)
st.title("🌦️ SkyWatch")
st.caption("Forecasts and configurable weather risk alerts · Open-Meteo · demo mode works offline")

with st.sidebar:
    st.header("Forecast settings")
    city = st.text_input("City", value="London")
    source = st.radio("Data source", ["demo", "live"], format_func=lambda x: "Offline demo" if x == "demo" else "Open-Meteo live API")
    days = st.slider("Forecast days", min_value=1, max_value=7, value=5)
    defaults = thresholds_from_environment()
    max_temp = st.number_input("Heat threshold (°C)", value=float(defaults.max_temperature_c), step=1.0)
    rain_probability = st.slider("Rain probability threshold (%)", 0, 100, int(defaults.rain_probability_pct))
    max_humidity = st.slider("Humidity threshold (%)", 0, 100, int(defaults.max_humidity_pct))
    max_wind = st.number_input("Wind threshold (km/h)", value=float(defaults.max_wind_kmh), step=1.0)
    load_button = st.button("Get forecast", type="primary", use_container_width=True)

if load_button:
    if not city.strip():
        st.error("Enter a city name first.")
    else:
        try:
            from src.weather_alert.alerts import AlertThresholds
            thresholds = AlertThresholds(max_temp, rain_probability, max_humidity, max_wind, defaults.max_aqi)
            report, alerts = WeatherService().get_report(city.strip(), source, days, thresholds)
            st.session_state["weather_data"] = (report, alerts, thresholds)
        except (WeatherAPIError, ValueError) as exc:
            st.error(str(exc))

if "weather_data" in st.session_state:
    report, alerts, thresholds = st.session_state["weather_data"]
    st.subheader(f"{report.city}, {report.country}")
    st.caption(f"{report.source} · {report.observed_at} · {report.timezone}")
    cols = st.columns(2)
    cols[0].metric("Temperature", f"{report.temperature_c:.1f} °C", f"Feels like {report.feels_like_c:.1f} °C")
    cols[1].metric("Conditions", report.description)
    cols = st.columns(2)
    cols[0].metric("Humidity", f"{report.humidity_pct}%")
    cols[1].metric("Wind", f"{report.wind_kmh:.1f} km/h")
    if report.aqi is not None:
        st.metric("AQI (US scale)", str(report.aqi))
    st.subheader("Risk alerts")
    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("No configured risk thresholds were triggered.")
    frame = pd.DataFrame([day.as_dict() for day in report.forecast])
    st.subheader("Daily forecast")
    st.dataframe(frame, use_container_width=True, hide_index=True)
    chart_frame = frame.set_index("date")[["temp_max_c", "temp_min_c"]].rename(
        columns={"temp_max_c": "High °C", "temp_min_c": "Low °C"})
    st.line_chart(chart_frame)
    rain_frame = frame.set_index("date")[["rain_probability_pct"]].rename(
        columns={"rain_probability_pct": "Rain probability (%)"})
    st.subheader("Rain probability")
    st.bar_chart(rain_frame)
    if report.source.startswith("Open-Meteo") and (report.latitude or report.longitude):
        st.subheader("Location")
        st.map(pd.DataFrame({"lat": [report.latitude], "lon": [report.longitude]}), zoom=8)
    if st.button("Save CSV, JSON & PNG report"):
        paths = save_report(report, alerts, thresholds, ROOT / "outputs")
        st.success("Saved report files")
        st.json(paths)
    st.caption("Risk notices are educational threshold checks, not official emergency warnings. Always follow local authorities.")
else:
    st.info("Choose a city and data source, then select **Get forecast**. Try offline demo to explore without internet.")
