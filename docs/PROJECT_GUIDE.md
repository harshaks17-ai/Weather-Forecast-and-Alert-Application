# Student project guide: Weather Forecast & Alert Application

This guide contains the project explanation, options, architecture, implementation phases, GitHub workflow, portfolio evidence plan, and interview preparation.

## 1. What the application does

**Simple explanation:** A user selects a city; the app looks up the city's weather, shows current conditions and the coming days, checks user-set limits, and flags conditions that may need attention. It can save the forecast and a chart for later.

**Technical explanation:** The client calls a geocoding endpoint to convert a free-text place name into coordinates, requests current and daily forecast JSON, validates and normalizes those fields into Python dataclasses, evaluates configurable rules, then serves the result through a CLI, FastAPI, or Streamlit. Pandas writes forecast rows to CSV, `json` serializes the full report, and Matplotlib creates a PNG chart.

It is useful as a planning aid for travelers, farmers, event planners, logistics teams, and outdoor businesses. It demonstrates an integration pattern rather than providing guaranteed or authoritative warnings. Actual businesses should use an appropriate provider, licensed data, calibrated risk models, monitoring, and official alert feeds.

**Workflow:** user enters city → geocoding and forecast API requests → JSON parsing/validation → forecast analysis → threshold checks → CLI/API/dashboard output → optional CSV/JSON/chart report.

## 2. Stack options

| Option | Tools | Difficulty | Expected result |
|---|---|---:|---|
| A — Easy | Python, `requests`, `json`, `datetime`, terminal, CSV | Beginner | Current city weather and printed alert |
| B — Student recommended | Python, Open-Meteo, `requests`, Pandas, Matplotlib, Streamlit, dotenv, `unittest` | Intermediate | Working dashboard, risk rules, offline demo, chart and downloadable/saved reports |
| C — Advanced | Option B + FastAPI, database, scheduled automation, containers, CI, official alerts and secured notification provider | Advanced | Deployable multi-interface service with persistence and monitored automation |

This repository implements **Option B and a small API from Option C**. Open-Meteo was chosen over a key-required provider to keep setup simple. The same client boundary can later be replaced with OpenWeatherMap or WeatherAPI; read the selected provider's current terms and plans first.

## 3. Architecture

```text
CLI (main.py) ──────┐
FastAPI (api.py) ───┼──> WeatherService
Streamlit dashboard┘          │
                              ├──> Open-Meteo geocoding + forecast (+ optional AQI)
                              ├──> Demo provider (offline)
                              ├──> WeatherReport / ForecastDay models
                              ├──> Alert rules: heat, rain, humidity, wind, optional AQI
                              └──> CSV + JSON + PNG report writer
```

**Input:** city, data source, forecast length, alert limits. **Processing:** location lookup, weather API request, response validation and normalization, rule evaluation. **Output:** current conditions, daily forecast, risk notices, API JSON, and optional files. API key: none required by the current live provider; use environment variables for any future key-based provider and never place secrets in source code.

## 4. Phase-wise implementation plan

| Phase | What / why | Expected output | Beginner pitfalls |
|---|---|---|---|
| 1 Setup | Install Python 3.10+, Git; create/activate venv to isolate packages | `python --version`, active `.venv` | Wrong Python on PATH; forgetting to activate the venv |
| 2 Folders | Make `src/weather_alert`, `data`, `outputs`, `images`, `reports`, `docs`, `tests` | Organized project, easier maintenance | Running commands from parent directory rather than project directory |
| 3 Configuration | Copy `.env.example` to local `.env`; review `.gitignore` | Safe local threshold config | Committing `.env`; assuming Open-Meteo needs a key |
| 4 Fetch | Geocode city, request live API with timeout; keep demo provider for offline work | Location and JSON payload | No internet, misspelled city, rate limits, trusting unchecked JSON |
| 5 Parse | Map keys to typed models, validate missing/null values, map WMO codes | Consistent report object | Confusing Celsius/Fahrenheit, units, local time and UTC |
| 6 Analyze | Extract daily min/max, precipitation chance/amount, wind | Forecast rows in CLI/table | Treating chance of rain as rainfall amount; ignoring missing data |
| 7 Alerts | Compare values to visible, configurable thresholds | Readable threshold notices | Claiming a threshold is an official warning; too many duplicate alerts |
| 8 Visualize | Render highs/lows in chart or dashboard | Dashboard chart | Plotting strings, missing labels, blocking GUI backend on server |
| 9 Reports | Write timestamped CSV, JSON, PNG | Files under `outputs/` | Overwriting files, uploading secrets/location data, committing noisy outputs |
| 10 GitHub | Commit source/docs/tests/screenshots; push to a public repo | Reviewable portfolio | Pushing `.env`, committing virtual environment, forgetting README |

## 5. Project folders

- `src/weather_alert/`: reusable client, models, alert rules, shared service, and report writer.
- `data/`: checked-in, non-sensitive example data for explanation.
- `outputs/`: generated timestamped CSV/JSON/PNG; ignored by Git by default.
- `images/`: screenshots that you choose to add to GitHub.
- `reports/`: optional curated sanitized sample reports for the portfolio.
- `docs/`: this guide and additional project notes.
- `tests/`: offline regression tests.
- `api.py`, `dashboard.py`, `main.py`: API, dashboard, and terminal entry points.

## 6. Install and configure

Windows PowerShell:
```powershell
cd Weather-Forecast-Alert-Application
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` for that terminal session, or run `.venv\Scripts\python.exe` directly. macOS/Linux:
```bash
cd Weather-Forecast-Alert-Application
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Open-Meteo is used here and needs no key. Optional `.env` defaults are `ALERT_MAX_TEMPERATURE_C`, `ALERT_RAIN_PROBABILITY_PCT`, `ALERT_MAX_HUMIDITY_PCT`, `ALERT_MAX_WIND_KMH`, `ALERT_MAX_AQI`. For another provider, put its key in a local `.env`, read it with `os.getenv`/`python-dotenv`, add it to `.gitignore`, and commit only a blank placeholder in `.env.example`. If a key is accidentally pushed, revoke/rotate it immediately—deleting the file in a later commit does not erase Git history.

## 7–9. Run, API, and simulation

From the project folder, run offline first:
```bash
python main.py --city "London" --source demo
python -m unittest discover -s tests -v
```

Then live API (internet required):
```bash
python main.py --city "London" --source live --days 5
```

Dashboard and API:
```bash
streamlit run dashboard.py
uvicorn api:app --reload
```
Browse `http://127.0.0.1:8000/docs`, or request `/weather/London?source=demo&days=5`. Expected files are `outputs/weather_<city>_<timestamp>.csv`, `.json`, `.png`. The demo uses clearly labelled, fixed sample conditions including 38°C current temperature, high humidity, rain probabilities, and a windy forecast day; dates are generated relative to today. Alert rules emit one notice for each matching current/day condition. The checked-in `data/sample_weather.json` is a human-readable example with relative sample-day labels; the executable demo is in `fetch_demo_weather`.

In real use, the same service fetches the provider's current forecast rather than fixed values. This project does not send e-mail/SMS, persist user profiles, or issue official warnings. Never present a demo result as real weather.

## 10. GitHub upload

Suggested repository: **`weather-forecast-alert-app`**. Description: *Python weather forecast and configurable risk alerts with Open-Meteo, FastAPI, Streamlit, offline simulation, and report charts.* Suggested topics: `python`, `weather-api`, `fastapi`, `streamlit`, `pandas`, `data-visualization`, `alert-system`, `student-project`.

1. Create a public GitHub repository with that name; do not initialize an additional README if pushing this existing README.
2. In the project directory, verify `git status` and confirm `.env` and `.venv` are not staged.
3. Initialize and push (replace the URL with your own):
   ```bash
   git init
   git add .
   git status
   git commit -m "feat: build weather forecast and alert application"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/weather-forecast-alert-app.git
   git push -u origin main
   ```
4. Add screenshots under `images/`, reference them in README with Markdown, then commit with e.g. `docs: add project screenshots and setup guide`.
5. Never upload real `.env`, API keys, tokens, passwords, private location data, virtual environments, or unreviewed API payloads. `.env.example` is safe; inspect `git status` before each push.

Useful incremental commit messages: `chore: scaffold Python project`, `feat: integrate Open-Meteo forecast`, `feat: add offline demo provider`, `feat: add configurable weather alerts`, `feat: generate forecast reports and charts`, `feat: add FastAPI and Streamlit interfaces`, `test: cover demo and alert behavior`, `docs: document setup and portfolio evidence`.

## 11. README contents

The top-level [README.md](../README.md) is the repository landing page and includes overview, problem, industry context, features, stack, folders, installation, run commands, sample output, reports, tests, learning outcomes, extensions, and source attribution. Keep commands and screenshots current as your code evolves.

## 12–13. Six-day proof-of-work and screenshot checklist

| Day | Work to show | Example commit | Screenshot/file evidence |
|---|---|---|---|
| 1 Setup | Python, venv, requirements, structure, README start | `chore: scaffold Python project` | Folder tree; successful install/test command |
| 2 API | Geocoding and live request/error handling | `feat: integrate Open-Meteo forecast` | Live CLI/API response (hide personal details) |
| 3 Parsing | Dataclasses, units, WMO descriptions, sample data | `feat: normalize forecast data` | Current weather and forecast table |
| 4 Alerts | Configurable heat/rain/humidity/wind checks and tests | `feat: add configurable weather risk alerts` | Demo risk notices and passing unit tests |
| 5 Visual/report | Streamlit chart and CSV/JSON/PNG exports | `feat: add dashboard and forecast reports` | Dashboard, saved chart, CSV opened in spreadsheet |
| 6 Documentation | API docs, README, guide, reviewed screenshots and GitHub push | `docs: finish GitHub portfolio documentation` | GitHub repo preview, README rendering, commit history |

Capture these exact views where possible: (1) project folder/tree, (2) demo terminal output, (3) live terminal output if reachable, (4) current weather block, (5) forecast rows, (6) risk alert block, (7) generated CSV in spreadsheet/editor, (8) PNG chart, (9) Streamlit dashboard, (10) FastAPI `/docs` and a demo response, (11) GitHub repository overview. Use fake/demo data where practical; do not show API keys, tokens, email addresses, private paths, or exact personal location. The repository includes `images/dashboard-demo.png` and `images/demo-forecast-chart.png` as generated demo examples; replace them with your own captures as you develop. Outputs are ignored intentionally, so only commit sanitized, stable examples if useful.

## 14. Interview preparation

### “Explain your project.”

“I built a Python weather forecast and alert application with three interfaces: a command-line app, FastAPI endpoints, and a Streamlit dashboard. It geocodes a city using Open-Meteo, fetches current conditions and a multi-day forecast, normalizes the response into typed models, then checks configurable heat, rain, humidity, and wind thresholds. It can also run on deterministic offline sample data, which makes the alerts and unit tests reproducible without a key or network. Users can save a forecast as CSV and JSON and view a temperature chart. I separated API fetching, domain rules, reporting, and presentation so each part can be tested or replaced. It is a planning/demo aid, not an official warning service.”

### 10 technical questions and strong answers

1. **What problem does it solve?** It brings a city forecast and user-selected risk limits into one view, making planning-relevant conditions easier to scan; it does not replace official meteorological alerts.
2. **How does the app get live data?** It first calls Open-Meteo geocoding for coordinates, then requests current and daily forecast fields with latitude, longitude, and automatic timezone. Responses are JSON, with a finite request timeout and HTTP/shape checks.
3. **Why use a geocoding step?** Most forecast APIs work on coordinates. Geocoding converts free-text city input into latitude/longitude and gives a canonical place name/country.
4. **How are alerts generated?** `generate_alerts` compares current values and each forecast day against an `AlertThresholds` object. A match creates a clear message; thresholds come from defaults, `.env`, CLI flags, or UI/API inputs.
5. **What does the offline simulation do?** It returns a deterministic, clearly labelled demo report with known heat, humidity, rain, and wind cases. This supports demos/tests without network access and avoids pretending sample values are live.
6. **How do you handle API errors?** Requests have a timeout; network, HTTP status, invalid JSON, unknown city, and missing expected fields become actionable `WeatherAPIError` messages. The optional AQI lookup is isolated so its failure does not break the forecast.
7. **How do you protect secrets?** Current provider requires no key. Any future provider key belongs in local `.env`, read at runtime, excluded by `.gitignore`; only placeholders/configuration names go in `.env.example`. Rotate keys if exposed.
8. **Why CSV, JSON, and PNG?** CSV is easy to inspect/analyze in Pandas or spreadsheets, JSON preserves structured metadata/alerts, and PNG makes the trend easy to share. Each output is timestamped to avoid overwriting earlier runs.
9. **How would you test the live API safely?** Unit tests use deterministic demo data. I would mock `requests.get` to test success, timeout, HTTP error, malformed payload, and missing fields without depending on the network or API availability.
10. **What would you improve for production?** Add provider-specific official alerts and attribution checks, persistence and caching, retry/backoff and observability, stronger schemas, authentication/rate limiting, deployment/CI, accessibility, and carefully consented notification integrations. I would validate thresholds with domain experts and clearly communicate uncertainty.

### HR / non-technical explanation

“I chose a practical problem that affects everyday planning and built a complete Python solution rather than a single script. I made it easy to try without credentials by adding an offline demo, documented how to run it, tested its core rules, and considered responsible handling of keys and weather safety. The work demonstrates learning across API integration, data processing, automation, visualization, and clear documentation. I can explain what is real, what is simulated, and what I would need before using it for real safety decisions.”
