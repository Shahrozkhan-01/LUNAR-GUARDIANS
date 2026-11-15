# LUNAR GUARDIANS — Complete Project and Hackathon Guide

**Project:** Junior Astronaut Mission Trainer
**NASA Space Apps Hackathon team:** VOID DOMINATORS

**Team members:** Muhammad Shahroz Khan, Abdul Rafay, Maira, Urwa Asif
Qureshi, Fatima Bukhari, and Ayesha Ashraf
**Audience:** children aged approximately 7–12, families, and educators
**Last verified:** 2026-11-15
**Operation:** local React/Vite frontend and FastAPI backend; no hosted service is required

## 1. Project at a glance

LUNAR GUARDIANS is a browser-based lunar survival learning game. Players
configure a lunar outpost mission, manage simulated resources, make decisions
during mission events, and review a debrief. The NASA Data Explorer and
Mission Control introduce real NASA data with its source, date, units, and
limitations. Real observations, computed geometry, and fictional game effects
are explicitly distinguished.

The project is an independent educational implementation and is not endorsed
by NASA. It is not an operational mission-planning, radiation-dosimetry,
medical, or landing-safety tool.

### Team and project ownership

LUNAR GUARDIANS was prepared by **VOID DOMINATORS** for the NASA Space Apps
Hackathon. The team members are **Muhammad Shahroz Khan, Abdul Rafay, Maira,
Urwa Asif Qureshi, Fatima Bukhari, and Ayesha Ashraf**. The team confirms
ownership of the project's original artwork, including the visual assets listed below. NASA data products and
third-party dependencies remain subject to their own attribution and use
terms; the team does not claim ownership of those materials. No project-level
reuse license is supplied by this ownership statement.

## 2. Run the complete game locally

### Requirements

- Windows 10/11 with PowerShell.
- Python 3.10 or later.
- Node.js 20.19 or later, or Node.js 22.12 or later, and npm. These are the
  supported Node versions for the installed Vite 8 toolchain.
- Internet access is optional for the application itself. It is required for
  live DONKI requests and remote Google Fonts. Gameplay remains available if
  those services cannot be reached.

### First-time installation

Run these commands from PowerShell:

```powershell
cd D:\NASA\LUNAR-GUARDIANS

py -3 -m venv backend\venv
backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt

cd frontend
npm ci
cd ..
```

### Optional NASA API key

The app uses `DEMO_KEY` if no NASA API key is configured. It is rate-limited;
a personal key is optional and is used only by the backend.

```powershell
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

Set `NASA_API_KEY` and, optionally, `NASA_CACHE_SECONDS`. Keep `backend/.env`
private; it is ignored by Git. Never put a NASA key in a React/Vite variable.

### One-command launch

```powershell
cd D:\NASA\LUNAR-GUARDIANS
.\start-lunar-guardians.ps1
```

If PowerShell blocks the script, allow it for the current terminal only:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start-lunar-guardians.ps1
```

The launcher starts only services that are not already responding, waits for
both readiness checks, and opens the frontend.

| Service | Local address |
|---|---|
| Game | <http://127.0.0.1:5173> |
| FastAPI interactive API docs | <http://127.0.0.1:8000/docs> |
| Backend health check | <http://127.0.0.1:8000/health> |

### Manual launch

Use two PowerShell terminals:

```powershell
# Terminal 1
cd D:\NASA\LUNAR-GUARDIANS\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```powershell
# Terminal 2
cd D:\NASA\LUNAR-GUARDIANS\frontend
npm run dev -- --host 127.0.0.1
```

Press `Ctrl+C` in each terminal to stop its service.

### Offline and missing-data behavior

The simulation runs locally and does not require NASA to be online. If DONKI
cannot be reached, the status is reported and no replacement NASA observations
are fabricated. Static dataset views use the local files under
`datasets/processed/`. A fresh clone will not include the ignored 106 MB LOLA
full-resolution grid. The repository includes a compact 64,800-point LOLA
preview, sampled from every 16th row and column of that real source grid, so
the hosted Data Explorer can display paginated coordinates and elevations.
The preview is not the full grid and cannot support local landing-site or
hazard assessment.

## 3. How to play

1. Choose **Start Mission**.
2. Select the Lunar Outpost, a difficulty, crew size (2, 4, or 6), and mission
   duration (5, 10, or 15 days).
3. Choose one of the educational briefings:
   - **South Polar Exploration:** historical Diviner and broad LOLA context.
   - **Space Weather Preparedness:** historical ACE/STEREO context and
     live DONKI event information when available.
   - **Communication and Navigation:** saved JPL Horizons ephemerides.
4. Initialize the mission. In Mission Control, review crew indicators,
   resource meters, subsystems, event prompts, and power allocation.
5. Resolve required event decisions, perform available outpost actions, then
   advance the day. The backend applies resource use, generation, system
   effects, event outcomes, and score changes.
6. Reach the end of the selected mission or respond to a failure state. Review
   the debrief for the outcome, resources, Science Points, decisions, lessons,
   strengths, and improvement suggestions.
7. Use **Relaunch Day 1** for a fresh run or **Setup** for a new configuration.

**Explorer** is the gentler difficulty, **Commander** is balanced, and
**Expert** uses tighter starting reserves and higher challenge. Larger crews
consume more supplies; longer durations require planning for sustained
resources.

All resource meters, crew-health indicators, radiation/shelter effects,
Science Points, and scenario outcomes are **SIMULATED GAME UNITS**. They are
not NASA measurements or astronaut medical assessments. Sound is optional,
off by default, generated with the browser Web Audio API, and controlled in
the interface.

## 4. Screens and application structure

| Screen/feature | Route or source | Purpose |
|---|---|---|
| Landing page | `/` — `frontend/src/pages/Home.jsx` | Introduction, launch, feature and science sections |
| Mission setup | `/mission-setup` — `MissionSetup.jsx` | Destination, challenge, crew, duration, and briefing choices |
| Mission Control | `/mission-control` — `MissionControl.jsx` | Live game state, resources, events, decisions, progression, and debrief |
| NASA Data Explorer | `/nasa-data` — `NasaDataExplorer.jsx` | Dataset metadata, summaries, charts, and supported paginated records |
| Mission state/context | `frontend/src/context/MissionContext.jsx` | Frontend state, API calls, navigation, loading/errors, and replay |
| Game API client | `frontend/src/services/gameApi.js` | HTTP client, error display, and API base URL |
| Space-weather UI | Mission Control components | NASA status, event metadata, timestamps, and source links |
| Training-event UI | Mission Control components | Optional science scenarios and separately labeled simulated choices |

The landing page and application backgrounds include an animated star field,
local lunar/outpost artwork, and CSS-drawn decorative Moon, Saturn-like, and
Mars-like bodies. These decorative bodies are not to scale and do not represent
live astronomical positions.

### Repository map

```text
backend/
  app/main.py                FastAPI app, CORS, and router registration
  app/models/                Typed Pydantic request/response models
  app/routes/                Game, NASA, and dataset HTTP endpoints
  app/services/              Simulation, resources, event, NASA, and dataset rules
  tests/                     Backend unittest suite
  requirements.txt           Pinned Python dependencies
datasets/
  raw/                       Preserved NASA source products and labels
  processed/                 Derived products served by the backend
  metadata/dataset_catalog.csv
  scripts/                   Dataset-specific validators/processors
  validation_reports/        Machine-readable validation outcomes
documentation/
  screenshots/               Captures of the local application
  *_dataset.md               Product-specific source and science notes
frontend/
  public/                    Favicon and visual assets
  src/components/            Shared visual and mission UI components
  src/context/               Mission state provider
  src/pages/                 The four application screens
  src/services/              Backend and audio clients
  package.json               JavaScript dependencies and scripts
start-lunar-guardians.ps1     Windows local launcher
README.md                    Quick start
```

## 5. System and API architecture

React renders the browser experience and calls the local FastAPI service.
FastAPI owns mission state and applies game rules. The mission store is in
memory, so stopping/restarting the backend ends active sessions. Dataset APIs
read an allowlisted set of local processed files. Only the backend requests
DONKI; the API key is not returned to the frontend.

### Backend route groups

| Routes | Purpose |
|---|---|
| `POST /api/game/start` | Create a mission from its setup payload |
| `GET /api/game/{mission_id}` | Retrieve current state |
| `POST /api/game/{mission_id}/action` | Apply an outpost action or event decision |
| `POST /api/game/{mission_id}/advance` | Advance one simulated day |
| `GET /api/game/{mission_id}/events` | Read active mission events |
| `POST /api/game/{mission_id}/power` | Validate and update power allocation |
| `/api/nasa/status`, `/solar-events`, `/sep`, `/flares`, `/last-updated` | DONKI state and normalized event records |
| `GET /api/datasets` | List supported datasets and local file availability |
| `GET /api/datasets/{id}/metadata` | Dataset provenance, coverage, fields, units, and limits |
| `GET /api/datasets/{id}/summary` | Saved summary statistics |
| `GET /api/datasets/{id}/records?page=1&page_size=50` | Bounded, paginated records where supported |

Dataset IDs are allowlisted in `backend/app/services/dataset_service.py`.
Page sizes are limited by the service; the full Diviner/LOLA grids are not
transferred as ordinary paginated rows. LOLA record pages use only the
documented coarse preview; its full-resolution raster is not deployed.

## 6. NASA datasets and sources

The active static dataset API has nine IDs. DONKI is a separate live API
integration, not a local static dataset. Original inputs, product labels,
metadata, and supporting documentation are kept under each `datasets/raw/`
subdirectory. Processed outputs, metadata, and summaries are under the
corresponding `datasets/processed/` directory. The CSV catalog and validation
reports are the machine-readable inventory.

| API ID | Data and selected coverage | Source / detail | Validation and important limit |
|---|---|---|---|
| `diviner` | LRO Diviner cumulative south-polar brightness-temperature grid; 2009–2015, 70°S–80°S; 1,382,400 rows. Coordinates in degrees, local time in hours, temperature in K. | [Official PDS product](https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gcp/global_cumul_avg_cyl_80s70s_002.tab); [product guide](diviner_dataset.md), [processing](diviner_processing.md). | PASS; missing-value policy and readback are documented. Historical remote sensing, not live outpost temperature. |
| `lola` | LRO LOLA LDEM_16 global topography; 16,588,800 source samples. The hosted record preview contains 64,800 original cells (every 16th row and column), with DN and derived elevation in meters and coordinates in degrees. | [Official PDS raster](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/ldem_16.img); [product guide](lola_dataset.md), [processing](lola_processing.md). | PASS_WITH_WARNINGS; documented extrema mismatch retained. The ~30 km equatorial preview spacing and ~1.9 km/pixel source context are not landing-hazard certification. Full raster is not deployed. |
| `ace_epam` | ACE EPAM Level-2 CDF, 2020-01-01 to 2020-01-02 UTC; 277 records and 88 measurement/uncertainty channels. Source channel units are preserved in metadata. | [NASA SPDF archive](https://spdf.gsfc.nasa.gov/pub/data/ace/epam/); [CDAWeb dataset](https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/AC_H1_EPM/); [guide](ace_epam_dataset.md), [processing](ace_epam_processing.md). | PASS_WITH_WARNINGS; fill values and cadence warnings retained. ACE is near L1, not the Moon or a crew dosimeter. |
| `stereo_impact` | STEREO-A IMPACT HET, March 2012; 31 daily intervals with 3 electron and 11 proton channels. Intensity units: particles/(cm²·sr·s·MeV), with energy ranges in MeV. | [Official SPDF product](https://spdf.gsfc.nasa.gov/pub/data/stereo/ahead/l2/impact_ascii/het/1day/AeH12Mar.1d); [guide](stereo_impact_dataset.md), [processing](stereo_impact_processing.md). | PASS; source tokens retained. Historical spacecraft observations, not lunar conditions or astronaut dose. |
| `jpl_horizons` | Earth–Moon ephemeris, eight daily epochs, 2026-11-14 through 2026-11-21 UTC. Range km, range rate km/s, light time minutes; derived two-way vacuum time in seconds. | [Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html); [guide](jpl_horizons_dataset.md), [processing](jpl_horizons_processing.md). | PASS_WITH_WARNINGS; saved source values checked. Computed ephemeris; derived two-way value is not a direct measurement and excludes network delay. |
| `omni_hourly` | OMNI2 2020 annual source; bounded January 2020 selection, 744 hourly records and 55 fields. Units are variable-specific: nT, cm⁻³, km/s, K, nPa, mV/m, and index units. | [Official OMNI2 file](https://spdf.gsfc.nasa.gov/pub/data/omni/low_res_omni/omni2_2020.dat); [field guide](https://omniweb.gsfc.nasa.gov/html/ow_data.html); [project notes](omni_dataset.md). | PASS_WITH_WARNINGS; official fill values retained. Merged/time-shifted near-Earth/L1 data, not lunar dosimetry. |
| `lend` | LRO LEND DLD/DLX, 2020-01-01; 85,308 aligned records per product. UTC, latitude/longitude, time/count fields, corrected CSETN and sigma as defined by product labels. | [PDS LEND archive](https://pds-geosciences.wustl.edu/missions/lro/lend.htm); [RDR guide](lend_dataset.md). | PASS_WITH_WARNINGS; source markers and label anomalies retained. Orbital neutron observations do not by themselves confirm local water ice or astronaut dose. |
| `lro_spice` | LRO SPICE `LRO-L-SPICE-6-V1.0`, SPK `lrorg_2017258_2017349_v01.bsp`; 24 hourly epochs on 2017-09-15. J2000 position and Moon-center distance in km. | [NAIF archive](https://naif.jpl.nasa.gov/naif/data_archived.html); [selected LRO archive](https://naif.jpl.nasa.gov/pub/naif/pds/data/lro-l-spice-6-v1.0/lrosp_1000/); [guide](lro_spice_dataset.md). | PASS; kernel, label, coverage, and calculations checked. Computed historic spacecraft geometry, not telemetry, astronaut, or habitat position. |
| `osd53` | OSD-53 / GLDS-53, historical astronaut gene-expression study; 13 public sample annotations and 244 processed gene-summary rows. | [Official OSDR study](https://osdr.nasa.gov/bio/repo/data/studies/OSD-53); [study API](https://osdr.nasa.gov/geode-py/ws/repo/studies/OSD-53); [guide](osd53_dataset.md). | PASS; raw microarray data reported unavailable; identifying subject labels excluded. Not clinical guidance or gameplay health input. |

### Live DONKI integration

The backend requests the previous seven days of Solar Energetic Particle (`SEP`)
and Solar Flare (`FLR`) records from the [NASA DONKI API](https://api.nasa.gov/)
and links to the [DONKI dashboard](https://ccmc.gsfc.nasa.gov/DONKI/). Responses
are normalized, cached server-side, checked for empty/malformed/error cases,
and surfaced with update status. Event deduplication prevents repeat scenarios.
Unavailable or empty responses do not create fake observations.

A DONKI record is not a lunar surface dose measurement. Solar flare class is
not a dose conversion. A game event is created only when the supported metadata
meets the documented rule; its shelter/resource effects remain simulated.

### Validation and processing script index

Each validator writes JSON to `datasets/validation_reports/`; each processor
documents transformations in its processed metadata and the linked dataset
notes.

| Product | Validator | Processor |
|---|---|---|
| Diviner | `datasets/scripts/validate_diviner_dataset.py` | `datasets/scripts/process_diviner_dataset.py` |
| LOLA | `datasets/scripts/validate_lola_ldem.py` | `datasets/scripts/process_lola_dataset.py` |
| ACE EPAM | `datasets/scripts/validate_ace_epam.py` | `datasets/scripts/process_ace_epam.py` |
| STEREO IMPACT | `datasets/scripts/validate_stereo_impact.py` | `datasets/scripts/process_stereo_impact.py` |
| JPL Horizons | `datasets/scripts/validate_jpl_horizons.py` | `datasets/scripts/process_jpl_horizons.py` |
| OMNI2 | `datasets/scripts/validate_omni_dataset.py` | `datasets/scripts/process_omni_dataset.py` |
| LEND | `datasets/scripts/validate_lend_dataset.py` | `datasets/scripts/process_lend_dataset.py` |
| LRO SPICE | `datasets/scripts/validate_lro_spice.py` | `datasets/scripts/process_lro_spice.py` |
| OSD-53 | `datasets/scripts/validate_osdr.py` | `datasets/scripts/process_osdr.py` |

`datasets/metadata/dataset_catalog.csv` records the authoritative source,
coverage, variables, units, access, validation state, and scientific caveats.

## 7. Images, visual assets, and typography

| File | Use | Provenance record |
|---|---|---|
| `frontend/public/hero-lunar.png` | Landing-page lunar landscape and mission-setup preview | Original project artwork; the VOID DOMINATORS team confirms it is team-owned. |
| `frontend/public/outpost-overview.png` | Mission Control outpost overview | Original project artwork; the VOID DOMINATORS team confirms it is team-owned. |
| `frontend/public/hero-lunar.svg` | CSS background fallback / vector lunar scene | Original project artwork; the VOID DOMINATORS team confirms it is team-owned. |
| `frontend/public/favicon.svg` | Browser tab icon | Original project artwork; the VOID DOMINATORS team confirms it is team-owned. |
| `documentation/screenshots/*.png` | Evidence captures of the project screens | Screenshots are captures of this application, stored with descriptive names; they are not NASA source imagery. |
| CSS celestial objects and starfield | Decorative global background | Generated by local CSS and deterministic component styles; no image files or external astronomy-position service. They are decorative and not to scale. |
| Orbitron and Inter | Display/body typefaces requested by `frontend/index.html` | [Google Fonts CSS](https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap); browser/system fallback fonts are used when offline. |

UI icon shapes are rendered by the `lucide-react` dependency, not copied icon
files. `frontend/public/icons.svg` and the unused Vite starter images were
removed after confirming no application imports/references them.

**Submission note:** the team confirms ownership of the original project art;
do not describe it as NASA imagery or NASA-provided. NASA datasets, sources,
and third-party packages are separate materials and must retain their own
attribution and applicable terms. Ownership does not itself grant a public
reuse license for the project.

## 8. Software libraries and sources

Version declarations are maintained in `frontend/package.json`,
`frontend/package-lock.json`, and `backend/requirements.txt`. Those lock/requirement
files, not this table, are the exact install source of truth.

### Frontend

| Package | Role | Project/source |
|---|---|---|
| React, React DOM | UI and browser rendering | [react.dev](https://react.dev/), [npm](https://www.npmjs.com/package/react) |
| React Router DOM | Client-side route navigation | [React Router](https://reactrouter.com/), [npm](https://www.npmjs.com/package/react-router-dom) |
| Axios | HTTP calls to local FastAPI | [Axios](https://axios-http.com/), [npm](https://www.npmjs.com/package/axios) |
| Framer Motion | Screen and component transitions | [Motion](https://motion.dev/), [npm](https://www.npmjs.com/package/framer-motion) |
| Lucide React | Interface icons | [Lucide](https://lucide.dev/), [npm](https://www.npmjs.com/package/lucide-react) |
| Recharts | Data charts in the explorer | [Recharts](https://recharts.org/), [npm](https://www.npmjs.com/package/recharts) |
| Vite, `@vitejs/plugin-react` | Local dev server and production bundling | [Vite](https://vite.dev/), [npm](https://www.npmjs.com/package/vite) |
| Oxlint | Frontend static lint | [Oxlint](https://oxc.rs/docs/guide/usage/linter.html), [npm](https://www.npmjs.com/package/oxlint) |

### Backend

| Package | Role | Project/source |
|---|---|---|
| FastAPI | HTTP routes and OpenAPI docs | [FastAPI](https://fastapi.tiangolo.com/), [PyPI](https://pypi.org/project/fastapi/) |
| Uvicorn | ASGI server for local API | [Uvicorn](https://www.uvicorn.org/), [PyPI](https://pypi.org/project/uvicorn/) |
| Pydantic | API data models and validation | [Pydantic](https://docs.pydantic.dev/), [PyPI](https://pypi.org/project/pydantic/) |
| Requests | DONKI HTTP requests | [Requests](https://requests.readthedocs.io/), [PyPI](https://pypi.org/project/requests/) |
| python-dotenv | Optional local backend `.env` loading | [PyPI](https://pypi.org/project/python-dotenv/) |
| NumPy, Pandas | Scientific arrays, processing, and summaries | [NumPy](https://numpy.org/), [Pandas](https://pandas.pydata.org/), [PyPI](https://pypi.org/project/numpy/), [PyPI](https://pypi.org/project/pandas/) |
| cdflib | NASA CDF reading and processing | [CDF library](https://github.com/MAVENSDC/cdflib), [PyPI](https://pypi.org/project/cdflib/) |
| SpiceyPy | NAIF SPICE kernel geometry calculations | [SpiceyPy](https://spiceypy.readthedocs.io/), [PyPI](https://pypi.org/project/spiceypy/) |

Python versions are pinned in `backend/requirements.txt`; JavaScript exact
resolved versions are recorded in `frontend/package-lock.json`. Check each
dependency's included license metadata when redistributing a bundled copy.
There is currently no root project `LICENSE` file, so the project owners must
select and add an appropriate license if they intend to license the project
for reuse.

## 9. Automated checks and current submission checks

From the project root:

```powershell
cd backend
.\venv\Scripts\python.exe -m unittest discover -s tests -v
cd ..\frontend
npm run lint
npm run build
```

Last local verification (2026-11-15):

- Backend: **49 tests passed**.
- Frontend lint: **passed**.
- Standard local production build: **passed**; Vite reports a non-blocking
  advisory because a minified JavaScript chunk exceeds 500 kB.
- Local smoke test: frontend responds at port 5173, backend health is `ok`,
  all 9 dataset IDs are listed, dataset metadata/summary endpoints respond,
  and a mission can be created and retrieved.
- Browser smoke test: Mission Setup launched into Mission Control; NASA Data
  Explorer rendered.

### Remaining human checks before sending/submitting

- [x] Record the VOID DOMINATORS team's confirmation that the original
  bundled artwork is team-owned.
- [ ] Decide whether to provide a project-level `LICENSE`; team ownership does
  not grant third parties permission to reuse the project.
- [ ] Run the local game on the actual presentation computer; test keyboard,
  sound hardware, browser size, and external NASA availability.
- [ ] If submitting a ZIP, include the required source and processed data, or
  clearly state that the ignored oversized products are absent. Do not include
  `backend/.env`, `backend/venv`, `frontend/node_modules`, or build caches.
- [ ] Include NASA product citations in any presentation or demo that discusses
  measurements; do not imply NASA endorsement.

## 10. Primary official data and software references

- [NASA Open APIs](https://api.nasa.gov/) and [DONKI](https://ccmc.gsfc.nasa.gov/DONKI/)
- [NASA PDS Geosciences Node](https://pds-geosciences.wustl.edu/)
- [NASA SPDF / OMNIWeb](https://spdf.gsfc.nasa.gov/) and [OMNIWeb documentation](https://omniweb.gsfc.nasa.gov/html/ow_data.html)
- [NASA CDAWeb](https://cdaweb.gsfc.nasa.gov/)
- [NASA/JPL Horizons](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
- [NASA/JPL NAIF](https://naif.jpl.nasa.gov/naif/data_archived.html)
- [NASA Open Science Data Repository](https://osdr.nasa.gov/)
- [NASA Open Source Agreement](https://code.nasa.gov/)

All product-specific retrieval, raw filenames, labels, transformations,
validation details, record counts, source hashes, and missing-data policy are
described in the linked dataset notes and stored in the `datasets/` tree.
