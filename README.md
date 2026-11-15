# LUNAR GUARDIANS

**Junior Astronaut Mission Trainer**

LUNAR GUARDIANS is an educational lunar survival simulation for children
approximately 7–12 years old. Players configure a lunar outpost, manage
simulated life-support resources, respond to mission events, explore NASA
datasets, and learn why real observations must be kept separate from fictional
training consequences.

This repository contains the complete student project implementation. It does
not publish secrets or API keys.

## Problem and objectives

Space science can be difficult to explore through static facts alone. This
project turns resource planning, communication delay, terrain context, and
space-weather education into an interactive mission while preserving the
scientific limits of each NASA source.

Objectives:

- Teach basic lunar mission planning and resource trade-offs.
- Present real NASA observations with provenance, dates, units, and caveats.
- Keep simulated game units and consequences visibly separate from NASA data.
- Provide safe offline and unavailable-data fallbacks.

## Main features

- React landing page, Mission Setup, Mission Control, and NASA Data Explorer.
- Explorer, Commander, and Expert difficulty modes.
- Two-, four-, or six-astronaut crews and 5-, 10-, or 15-day missions.
- Simulated oxygen, water, power, food, shield, crew, subsystem, and science
  management.
- Daily progression, normal events, player decisions, mission completion/failure,
  scoring, debrief, relaunch, and replay.
- NASA DONKI Solar Energetic Particle and Solar Flare integration with caching,
  status reporting, normalization, classification, and deduplication.
- NASA Mission Briefing presets:
  South Polar Exploration, Space Weather Preparedness, and Communication and
  Navigation.
- Optional NASA Training Events using Diviner, LOLA, ACE EPAM, STEREO-A IMPACT,
  Horizons, and cached DONKI context.
- NASA Data Explorer with metadata, summaries, bounded pagination, and charts.
- LRO SPICE navigation geometry with J2000 position and Moon-distance visualization.
- NASA OSD-53 historical astronaut gene-expression research metadata and summaries.
- Responsive NASA-inspired mission-control styling, reduced-motion support, and
  optional generated sound effects with a persisted preference.

## System architecture overview

The React/Vite frontend communicates with the FastAPI backend over HTTP. The
backend is authoritative for mission state, resource calculations, daily
progression, events, decisions, scoring, and debrief history. NASA DONKI is
accessed only by the backend, while the processed static datasets are
served through an allowlisted read-only dataset service. The frontend displays
NASA provenance and limitations separately from simulated game consequences.

See the detailed [system architecture](documentation/system_architecture.md)
and [NASA integration architecture](documentation/nasa_dataset_integration_architecture.md).

## Technology stack

- **Frontend:** React, Vite, React Router, Axios, Framer Motion, Recharts,
  Lucide React, and CSS.
- **Backend:** Python, FastAPI, Uvicorn, Pydantic, Requests, Pandas, NumPy,
  cdflib, and python-dotenv.
- **Data:** NASA DONKI API plus processed local NASA dataset products under
  `datasets/processed/`; original products remain under `datasets/raw/`.

## Requirements

- Windows PowerShell.
- Python 3.10+ recommended; the project environment was validated with the
  repository virtual environment.
- Node.js 18+ and npm.
- A NASA API key is optional for local startup because `DEMO_KEY` is supported,
  but a personal key is recommended for higher rate limits.

## Installation

```powershell
cd D:\NASA\LUNAR-GUARDIANS

# Create the backend virtual environment once
cd backend
py -3 -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt

# Install frontend dependencies
cd ..\frontend
npm install
cd ..
```

## Environment variables

Copy the template and edit the local file:

```powershell
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

Relevant values:

```env
NASA_API_KEY=DEMO_KEY
NASA_CACHE_SECONDS=900
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_URL=http://localhost:5173
```

`backend/.env` is local-only and must never be committed. The key is used only
by the backend and is never returned to the frontend.

## Run the application

### Recommended Windows launcher

From the project root:

```powershell
.\start-lunar-guardians.ps1
```

The launcher starts only missing services, waits for backend `/health` and the
Vite port, then opens the game:

- Frontend: <http://127.0.0.1:5173>
- Backend docs: <http://127.0.0.1:8000/docs>
- Backend health: <http://127.0.0.1:8000/health>

If script execution is restricted:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start-lunar-guardians.ps1
```

### Manual startup

Terminal 1:

```powershell
cd D:\NASA\LUNAR-GUARDIANS\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2:

```powershell
cd D:\NASA\LUNAR-GUARDIANS\frontend
npm run dev -- --host 127.0.0.1
```

## Tests and checks

```powershell
cd D:\NASA\LUNAR-GUARDIANS\backend
.\venv\Scripts\python.exe -m unittest discover -s tests -v

cd ..\frontend
npm run lint
npm run build
```

The verified baseline is 49 backend tests passing, frontend lint passing, and
production build passing. Vite still reports a non-blocking bundle-size
advisory.

## NASA sources

- NASA DONKI: <https://ccmc.gsfc.nasa.gov/DONKI/> and
  <https://api.nasa.gov/>
- LRO Diviner: NASA PDS Geosciences Node.
- LRO LOLA: NASA PDS Geosciences Node.
- ACE EPAM: NASA Goddard SPDF/CDAWeb.
- STEREO-A IMPACT HET: NASA Goddard SPDF and instrument team.
- JPL Horizons: <https://ssd.jpl.nasa.gov/horizons/>
- NASA OMNI2 hourly: <https://spdf.gsfc.nasa.gov/pub/data/omni/low_res_omni/>
- LRO LEND: <https://pds-geosciences.wustl.edu/missions/lro/lend.htm>

See [NASA data sources and validation](documentation/nasa_data_sources_and_validation.md).

### Dataset publication note

The local source and processed products are preserved for reproducibility. The
large products listed in
[dataset_download_manifest.json](datasets/dataset_download_manifest.json) are
distributed as assets of the `datasets-v1` GitHub Release because GitHub
rejects individual files of 100 MB or more. Verify the recorded SHA-256 values
after uploading those assets. Smaller products may be explicitly force-added
when their source terms permit publication.

Two local files also exceed GitHub's 100 MB individual-file limit:

- `datasets/raw/lunar_environment/diviner/global_cumul_avg_cyl_80s70s_002.tab`
  (about 149 MB)
- `datasets/processed/lunar_environment/lola/ldem_16_processed.npz`
  (about 101 MB)

They are preserved in the project workspace and excluded from normal Git
staging. See [deployment.md](documentation/deployment.md) for Render setup and
the required backend environment variables.

## Free public deployment

The GitHub Pages frontend URL is
<https://shahrozkhan-01.github.io/LUNAR-GUARDIANS/>. The
[Pages workflow](.github/workflows/pages.yml) deploys automatically when
frontend files are pushed to `main`. Enable **Settings → Pages → Build and
deployment → Source → GitHub Actions** once in the repository.

The backend blueprint in [render.yaml](render.yaml) explicitly selects Render's
free plan. After creating the service, set the GitHub Actions repository
variable `VITE_API_BASE_URL` to its actual `onrender.com` URL if it differs
from the default. Keep `NASA_API_KEY` only in Render's backend environment.

## Screenshots

Genuine application screenshots are available in
[`documentation/screenshots/`](documentation/screenshots/):

| Screen | Preview |
|---|---|
| Landing page | [01-landing.png](documentation/screenshots/01-landing.png) |
| Mission Setup | [02-mission-setup.png](documentation/screenshots/02-mission-setup.png) |
| NASA Mission Briefing | [03-nasa-mission-briefing.png](documentation/screenshots/03-nasa-mission-briefing.png) |
| Mission Control | [04-mission-control.png](documentation/screenshots/04-mission-control.png) |
| NASA Training Events | [05-nasa-training-events.png](documentation/screenshots/05-nasa-training-events.png) |
| NASA Data Explorer | [06-nasa-data-explorer.png](documentation/screenshots/06-nasa-data-explorer.png) |
| Final mission debrief | [07-final-mission-debrief.png](documentation/screenshots/07-final-mission-debrief.png) |

## Scientific limitations

- Diviner brightness temperature is historical remote-sensing context, not
  live habitat temperature.
- LOLA is broad elevation context, not detailed landing hazard information.
- ACE and STEREO-A measurements are spacecraft observations, not lunar-surface
  measurements or astronaut radiation dose.
- DONKI event metadata is not lunar dosimetry; flare class is not dose.
- Horizons values are computed ephemerides; two-way vacuum light time is
  derived and excludes network and processing delay.
- OMNI is a merged, time-shifted near-Earth/L1 historical dataset, not a lunar
  surface measurement or astronaut radiation-dose measurement.
- Resources, shield, exposure indicators, Science Points, and all event
  consequences are simulated game values.

## Project structure

```text
backend/
  app/main.py
  app/routes/              # game, NASA, and dataset APIs
  app/services/            # simulation, NASA, dataset, and event logic
  app/models/              # Pydantic state and API schemas
  tests/
frontend/
  src/pages/               # Home, Mission Setup, Mission Control, Explorer
  src/components/          # reusable UI and NASA panels
  src/context/             # mission state provider
  src/services/            # API and sound services
datasets/
  raw/                     # preserved NASA source products
  processed/               # deterministic products used by the backend
  metadata/                # catalog and processing metadata
documentation/             # requirements, architecture, science, testing
start-lunar-guardians.ps1
```

For the complete document set, see [documentation/README.md](documentation/README.md).

## Documentation

- [User manual](documentation/user_manual.md)
- [Software requirements specification](documentation/software_requirements_specification.md)
- [System architecture](documentation/system_architecture.md)
- [NASA data sources and validation](documentation/nasa_data_sources_and_validation.md)
- [Full gameplay testing](documentation/full_gameplay_testing.md)
- [Final testing report](documentation/final_testing_report.md)
- [Demonstration script](documentation/project_demonstration_script.md)
- [Public repository guide](documentation/github_repository_guide.md)
- [Publication checklist](documentation/github_publication_checklist.md)

## Future improvements

- Add a durable account or save-game store instead of the current in-memory
  mission store.
- Use code splitting to reduce the production bundle-size advisory.
- Add a controlled dataset-download or Git LFS workflow for the two oversized
  products.
- Expand automated browser coverage while preserving the scientific data
  boundaries.

## License and publication status

No project license file is currently present. This means the owner retains
copyright and public viewers should not assume permission to reuse, modify, or
redistribute the project. Choose and add an appropriate license before
publication if reuse is intended; review NASA and third-party dataset terms
separately. See the [public repository guide](documentation/github_repository_guide.md).
