# LUNAR GUARDIANS
## Complete Project and NASA Space Apps Hackathon Report

**Team:** VOID DOMINATORS
**Team members:** Muhammad Shahroz Khan, Abdul Rafay, Maira, Urwa Asif Qureshi, Fatima Bukhari, and Ayesha Ashraf
**Project type:** Educational lunar-survival browser game
**Intended audience:** Children aged approximately 7–12, families, educators, and hackathon reviewers
**Report prepared:** 15 November 2026
**Project mode:** Local browser application; no hosting is needed to run it
**Project repository:** <https://github.com/Shahrozkhan-01/LUNAR-GUARDIANS>

## Contents

1. [The project in a minute](#1-the-project-in-a-minute)
2. [Why we made it](#2-why-we-made-it)
3. [What a player does](#3-what-a-player-does)
4. [How the software works](#4-how-the-software-works)
5. [NASA data used in the project](#5-nasa-data-used-in-the-project)
6. [Art, typography, and other visual sources](#6-art-typography-and-other-visual-sources)
7. [Software, libraries, and their roles](#7-software-libraries-and-their-roles)
8. [Running the game on a Windows computer](#8-running-the-game-on-a-windows-computer)
9. [Verification performed](#9-verification-performed)
10. [Scientific boundaries, safety, and known limitations](#10-scientific-boundaries-safety-and-known-limitations)
11. [Team, attribution, and project ownership](#11-team-attribution-and-project-ownership)
12. [Sources and further reading](#12-sources-and-further-reading)

---

## 1. The project in a minute

LUNAR GUARDIANS is an educational game about keeping a fictional lunar outpost operating. A player chooses a mission, crew, difficulty, and duration; makes decisions about supplies and equipment; responds to events; and receives a mission debrief. A NASA Data Explorer introduces real historical or near-real-time space-science information alongside its source, date, units, and limitations.

The central learning idea is simple: **good mission decisions use evidence, preserve essential supplies, and distinguish what scientists observed from what a game simulates.** The player can explore science without needing to read code or understand a spacecraft data format.

The game is a student-built learning tool. It is not endorsed by NASA and is not an operational mission-planning, lunar landing, radiation-dose, medical, or astronaut-safety system.

## 2. Why we made it

Space science is exciting, but scientific datasets can be hard to approach without context. LUNAR GUARDIANS turns resource planning and NASA data exploration into a guided activity:

- **Plan:** choose a crew size, mission length, challenge level, and learning briefing.
- **Manage:** balance simulated oxygen, water, food, electrical power, and outpost systems.
- **Respond:** make decisions during mission events and see how game rules affect the fictional crew and outpost.
- **Explore:** inspect NASA-derived charts, summaries, metadata, units, and source links.
- **Reflect:** review the mission result, score, lessons, decisions, strengths, and improvement suggestions.

The game is designed for learning and demonstration, not for teaching children that a simplified game meter is a real astronaut measurement.

## 3. What a player does

### A guided play-through

1. Open the landing page and select **Start Mission**.
2. In **Mission Setup**, select the Lunar Outpost, one of three difficulty levels, a crew of 2, 4, or 6, and a 5-, 10-, or 15-day mission.
3. Pick a briefing:
   - **South Polar Exploration** introduces historical lunar temperature and topography context.
   - **Space Weather Preparedness** introduces solar observations and the NASA DONKI event feed when available.
   - **Communication and Navigation** introduces Earth–Moon communication delay and saved spacecraft geometry.
4. Start the mission. **Mission Control** displays the current day, resource meters, crew and subsystem indicators, available actions, and mission events.
5. Resolve required event decisions, carry out available actions, and advance the simulated day. The backend applies the game's consumption, generation, and scoring rules.
6. Continue until the selected mission ends or the outpost reaches a failure condition.
7. Review the **mission debrief**, then relaunch or return to setup.

**Explorer** is the gentler challenge, **Commander** is balanced, and **Expert** starts with tighter reserves. Larger crews use more simulated supplies; longer missions require planning across more days. Outcomes are determined by the game mechanics, not by NASA datasets.

### Screens

| Screen | What it is for |
|---|---|
| Landing page | Introduces the mission and lets a visitor begin. |
| Mission Setup | Selects crew, difficulty, duration, and optional science briefing. |
| Mission Control | Shows the fictional mission state, decisions, actions, and day progression. |
| NASA Data Explorer | Presents dataset context, selected summaries, charts, units, and links to sources. |
| Mission debrief | Summarizes mission completion/failure, score, decisions, learning points, and areas to improve. |

### Optional sound and visual effects

Sound effects are generated by the browser's Web Audio API; there are no recorded NASA radio transmissions or sound recordings. Sound is optional and can be toggled in the interface. The background starfield and Moon/planet-like decorations are original CSS/component artwork, decorative only, not to scale, and not depictions of current celestial positions.

## 4. How the software works

The project has two cooperating local parts:

1. **Frontend (React and Vite):** the website shown in the browser. It displays the screens, charts, forms, and mission controls.
2. **Backend (Python and FastAPI):** the local service that owns active mission state, checks actions, advances the simulation, calculates game outcomes, and serves dataset information.

The browser sends game requests to FastAPI over HTTP. NASA DONKI requests are made on the backend, so the NASA API key is not placed in the React application. Static datasets are served through an allowlisted read-only dataset service. The mission store is in memory: restarting the backend ends active missions.

### Plain-language architecture map

| Part | Responsibility |
|---|---|
| `frontend/src/pages/` | Landing page, setup, mission control, and data explorer screens. |
| `frontend/src/components/` | Reusable panels, controls, visual effects, and NASA information displays. |
| `frontend/src/context/` | Frontend mission/session state and user interaction. |
| `frontend/src/services/` | HTTP client and optional sound effects. |
| `backend/app/routes/` | HTTP endpoints for the game, NASA status/events, and datasets. |
| `backend/app/services/` | Simulation rules, resource changes, event handling, NASA processing, and dataset access. |
| `backend/app/models/` | Typed request/response definitions. |
| `backend/tests/` | Automated backend tests. |
| `datasets/raw/` | Retrieved source products and related labels/metadata when available. |
| `datasets/processed/` | Selected, converted products used by the application. |
| `datasets/scripts/` | Dataset-specific processing and validation programs. |
| `datasets/validation_reports/` | Machine-readable validation outcomes. |
| `datasets/metadata/dataset_catalog.csv` | Machine-readable inventory of sources, coverage, units, validation, and caveats. |

### Main API groups

| Endpoint | Purpose |
|---|---|
| `POST /api/game/start` | Start a mission from its setup choices. |
| `GET /api/game/{mission_id}` | Retrieve current mission state. |
| `POST /api/game/{mission_id}/action` | Apply an outpost action or event decision. |
| `POST /api/game/{mission_id}/advance` | Advance one simulated day. |
| `GET /api/game/{mission_id}/events` | Retrieve current mission events. |
| `POST /api/game/{mission_id}/power` | Validate and update the simulated power allocation. |
| `/api/nasa/status`, `/api/nasa/solar-events`, `/api/nasa/sep`, `/api/nasa/flares`, `/api/nasa/last-updated` | Report live DONKI feed status and normalized event records. |
| `GET /api/datasets` | List supported static datasets and local file availability. |
| `GET /api/datasets/{id}/metadata` | Return dataset provenance, coverage, fields, units, and limitations. |
| `GET /api/datasets/{id}/summary` | Return saved summary information. |
| `GET /api/datasets/{id}/records` | Return bounded pages for datasets where record pagination is supported. |

## 5. NASA data used in the project

There are **nine static dataset IDs** in the backend registry. NASA DONKI is a separate live API integration. The project records dataset selections and scientific limitations in its catalog, product notes, processing metadata, and validation reports. Dataset availability depends on the corresponding local processed file being present.

| Dataset | What the source contains and what this project selected | Educational use in the game | Important limitation |
|---|---|---|---|
| **LRO Diviner** (`diviner`) | A historical Lunar Reconnaissance Orbiter cumulative south-polar brightness-temperature grid. The selected 70°S–80°S product spans 2009–2015 and has 1,382,400 grid rows. Coordinates are degrees, local time is hours, and brightness temperature is kelvin. [1] | Introduces historical lunar environment and temperature mapping. | Remote-sensing brightness temperature is not a live habitat or astronaut temperature. It is not a forecast. |
| **LRO LOLA** (`lola`) | A global LRO Lunar Orbiter Laser Altimeter LDEM_16 topography raster; 16,588,800 samples. Coordinate values are degrees and derived elevation is in metres. [2] | Provides broad lunar terrain/elevation context. | About 1.9 km/pixel context is not a local landing-hazard assessment, slope survey, or safety certification. A documented source/label extrema warning is retained. |
| **ACE EPAM** (`ace_epam`) | A bounded Level-2 Electron, Proton, and Alpha Monitor CDF sample from 1–2 January 2020 UTC: 277 records and 88 measurement/uncertainty channels. Original channel units and validity masks are preserved. [3] | Historical space-particle observation context for the space-weather briefing. | ACE is near Sun–Earth L1, not at the Moon or inside a habitat. Its instrument values are not astronaut dose. |
| **STEREO-A IMPACT HET** (`stereo_impact`) | A historical March 2012 daily-average sample with 31 daily intervals, three electron channels, and eleven proton channels. Intensity units and energy ranges are kept with the records. [4] | Demonstrates historical solar energetic-particle observations from a spacecraft. | These are spacecraft measurements at STEREO-A, not lunar surface conditions or astronaut dose. |
| **JPL Horizons** (`jpl_horizons`) | Eight saved daily Earth–Moon ephemeris epochs, 14–21 November 2026 UTC. Source range, range rate, and one-way light time retain km, km/s, and minutes; a two-way vacuum-time figure is derived from one-way light time. [5] | Explains why communication over interplanetary distances has delay. | Ephemerides are calculated geometry, and saved future epochs are predictions. Derived vacuum time excludes network and equipment delays. |
| **NASA OMNI2 hourly** (`omni_hourly`) | A bounded January 2020 selection from the 2020 annual hourly-means product: 744 hourly records and 55 fields. Units vary by field (including nT, cm⁻³, km/s, K, nPa, and mV/m). Official fill values are retained. [6] | Gives a historical view of solar-wind and interplanetary context. | OMNI is a merged/time-shifted near-Earth/L1 product, not lunar surface telemetry, a radiation dose, or a direct outpost hazard value. |
| **LRO LEND** (`lend`) | Lunar Exploration Neutron Detector DLD and DLX records for 1 January 2020 UTC: 85,308 aligned records per product. The associated PDS labels define time, location, count, corrected CSETN, and uncertainty fields. [7] | Introduces orbital neutron observations and careful interpretation of lunar measurements. | Orbital neutron observations alone do not prove local water ice and are not surface measurements or astronaut dose. Source markers and label anomalies are retained. |
| **LRO SPICE** (`lro_spice`) | A historical NAIF SPICE SPK kernel selection; 24 hourly epochs on 15 September 2017. SpiceyPy computes LRO position relative to the Moon in the J2000 frame and distance in kilometres. [8] | Visualizes spacecraft position and Moon-centre distance as computed geometry. | These are computed historical spacecraft geometry, not direct telemetry, current navigation, astronaut location, or habitat position. |
| **OSD-53 / GLDS-53** (`osd53`) | A historical human astronaut gene-expression study. The project includes public annotations for 13 samples and 244 processed gene-summary rows. [9] | Offers research context for studying biological responses to spaceflight. | Raw microarray data are reported unavailable in the study; identifying subject labels are excluded. This is not a clinical tool, a health prediction, lunar astronaut evidence, or a gameplay health input. |

### Live NASA DONKI space weather

The backend requests the previous seven days of Solar Energetic Particle (`SEP`) and Solar Flare (`FLR`) event-catalog records through NASA's DONKI API [10]. It normalizes the event-specific response fields, caches a snapshot in memory, reports feed status and retrieval time, handles empty/unavailable responses, and avoids repeatedly creating scenarios from the same event. When available, the interface identifies returned event details as **REAL NASA DATA** and links to the source.

DONKI catalog metadata are not a lunar outpost dosimeter. A SEP event does not automatically specify lunar surface dose; solar-flare class is not converted into astronaut radiation dose. The event classifier explicitly indicates insufficient data for a risk assessment where appropriate. Any shelter choices or resource/risk meters shown by gameplay are **SIMULATED GAME CONSEQUENCES**, calculated by the game rules. No NASA observation is fabricated when the feed is empty or unavailable.

### Local data and large files

Original available source files, processed products, scripts, metadata, and validation reports are maintained in the project workspace under `datasets/`. Two large products exceed GitHub's 100 MB individual-file limit and are excluded from normal Git tracking: the Diviner raw table (approximately 149 MB) and processed LOLA grid (approximately 101 MB). They remain local in the complete working copy. See `datasets/dataset_download_manifest.json` for file checksums and the complete guide for limitations when using an incomplete clone. Do not silently substitute synthetic data if a product is absent.

### Dataset processing and validation

Each dataset has a focused validator and processor in `datasets/scripts/`. Validation is recorded under `datasets/validation_reports/`; data format, field semantics, units, time coverage, missing values/fill values, and transformations are documented in the dataset notes and catalog. Some historical product validations are `PASS_WITH_WARNINGS`; those warnings are retained rather than hidden or “corrected” by inventing observations. The live DONKI service separately validates response shape and handles errors/empty arrays.

## 6. Art, typography, and other visual sources

| Visual element | Project use and origin |
|---|---|
| `frontend/public/hero-lunar.png` | Landing-page lunar landscape and mission-setup preview. The VOID DOMINATORS team confirms original project artwork is team-owned. |
| `frontend/public/outpost-overview.png` | Outpost illustration in the Mission Control experience. The team confirms original project artwork is team-owned. |
| `frontend/public/hero-lunar.svg` and `frontend/public/favicon.svg` | Original in-project vector artwork; the team confirms ownership. |
| Global starfield and CSS Moon/planet-like decorations | Generated by the project's React/CSS; decorative, not to scale, and not live NASA imagery or current astronomical positions. |
| `documentation/screenshots/01-landing.png` through `07-final-mission-debrief.png` | Captures of this application for project presentation. They are interface screenshots, not NASA source imagery. |
| Orbitron and Inter fonts | Requested from Google Fonts; local/system fallback fonts are used when offline. See the [Google Fonts CSS source](https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap). |
| Interface icons | Rendered by the Lucide React dependency, not copied from NASA. See the [Lucide project](https://lucide.dev/). |

Team ownership of original artwork does not grant NASA ownership or endorsement and does not determine the reuse terms of NASA data, fonts, or third-party packages. No project-level `LICENSE` file is currently included; ask the team before reusing project materials.

## 7. Software, libraries, and their roles

Exact resolved frontend versions are in `frontend/package-lock.json`; exact backend versions are in `backend/requirements.txt`.

### Browser application

| Library/tool | Plain-language purpose | Official project/source |
|---|---|---|
| React and React DOM | Build the screens from reusable interface components and render them in the browser. | [React](https://react.dev/), [npm package](https://www.npmjs.com/package/react) |
| React Router DOM | Move among the landing, setup, control, and data screens. | [React Router](https://reactrouter.com/) |
| Axios | Send browser requests to the local backend. | [Axios](https://axios-http.com/) |
| Framer Motion / Motion | Add screen and component transitions. | [Motion](https://motion.dev/) |
| Recharts | Draw charts in the data explorer. | [Recharts](https://recharts.org/) |
| Lucide React | Provide interface icon components. | [Lucide](https://lucide.dev/) |
| Vite and `@vitejs/plugin-react` | Run the local frontend development server and build static browser files. | [Vite](https://vite.dev/) |
| Oxlint | Check frontend source code for common problems. | [Oxlint](https://oxc.rs/docs/guide/usage/linter.html) |
| Web Audio API | Generate optional simple interface sounds inside the browser. | [MDN Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API) |

### Python backend and scientific processing

| Library/tool | Plain-language purpose | Official project/source |
|---|---|---|
| Python | Runs the backend and dataset scripts. | [Python documentation](https://docs.python.org/3/) |
| FastAPI | Defines the backend HTTP routes and interactive API documentation. | [FastAPI](https://fastapi.tiangolo.com/) |
| Uvicorn | Runs the FastAPI application locally. | [Uvicorn](https://www.uvicorn.org/) |
| Pydantic | Checks and structures API request/response data. | [Pydantic](https://docs.pydantic.dev/) |
| Requests | Calls the NASA DONKI web API from the backend. | [Requests](https://requests.readthedocs.io/) |
| python-dotenv | Loads optional local backend environment settings. | [python-dotenv](https://pypi.org/project/python-dotenv/) |
| NumPy and Pandas | Process scientific arrays, tables, and summaries. | [NumPy](https://numpy.org/), [Pandas](https://pandas.pydata.org/) |
| cdflib | Reads NASA Common Data Format (CDF) data. | [cdflib](https://github.com/MAVENSDC/cdflib) |
| SpiceyPy | Uses NAIF SPICE geometry routines for computed LRO position records. | [SpiceyPy](https://spiceypy.readthedocs.io/) |

Third-party packages retain their own licenses and notices. This report identifies their role and official project pages; it does not replace each dependency's license metadata.

## 8. Running the game on a Windows computer

### Requirements

- Windows 10/11 with PowerShell.
- Python 3.10 or later.
- Node.js 20.19 or later, or Node.js 22.12 or later, plus npm (required by the installed Vite 8 toolchain).
- Internet access is optional for basic gameplay. It is needed for live DONKI data and remote font download.

### First-time setup

Open PowerShell and run:

```powershell
cd D:\NASA\LUNAR-GUARDIANS
py -3 -m venv backend\venv
backend\venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend
npm ci
cd ..
```

### Start the game

```powershell
cd D:\NASA\LUNAR-GUARDIANS
.\start-lunar-guardians.ps1
```

The launcher starts the services and opens the local game in the browser:

- **Play:** <http://127.0.0.1:5173>
- **Backend health:** <http://127.0.0.1:8000/health>
- **Backend API documentation:** <http://127.0.0.1:8000/docs>

Keep the PowerShell window open while playing. Press **Ctrl+C** in the running service terminals to stop them. If script execution is blocked, run `Set-ExecutionPolicy -Scope Process Bypass` in that PowerShell window and start the launcher again.

### Optional NASA key

The app can use the shared NASA `DEMO_KEY` without first creating an account; it has stricter usage limits. A personal key is optional and belongs only in the backend's ignored `backend/.env` file. Never put it in React or a `VITE_` variable. The key is not required for offline gameplay.

### Offline and troubleshooting notes

- If the backend does not start, check `http://127.0.0.1:8000/health` and the backend terminal for the error.
- If the browser page does not load, ensure the frontend terminal is running and open `http://127.0.0.1:5173`.
- If NASA status says unavailable, check internet connectivity or try the refresh control. Empty/unavailable feeds do not create fake events; the game remains playable.
- Historical products may show a file-unavailable message if the local data file is absent. Metadata and limitations remain available, but no replacement readings are invented.
- The backend mission store is in memory. Restarting it ends the active mission.
- Sound is optional and controlled by the app's sound toggle and the browser/device volume settings.

## 9. Verification performed

The project documentation records the following local verification on 15 November 2026:

- **Backend:** 49 automated tests passed, including simulation, NASA integration, data APIs, training scenarios, mission progression, and failure handling.
- **Frontend lint:** `npm run lint` passed.
- **Production build:** `npm run build` passed. Vite emitted a non-blocking advisory that a JavaScript chunk is larger than 500 kB after minification.
- **Local smoke checks:** frontend returned HTTP 200; backend `/health` returned `ok`; dataset API listed nine IDs; metadata and summary APIs responded.
- **Browser smoke checks:** the local application opened; the new CSS Moon/Saturn/Mars-style decorations rendered; mission setup, mission control, and the data explorer were checked in the browser.
- **Documentation:** 120 internal Markdown links were checked and resolved during submission preparation.

These are local project checks, not independent scientific validation or certification by NASA. Live NASA availability depends on the network and NASA service.

## 10. Scientific boundaries, safety, and known limitations

1. **No fake observations:** if NASA data are missing, malformed, empty, or unavailable, the application reports that condition rather than inventing a replacement event or measurement.
2. **Observation is not simulation:** NASA source records and computed geometry are labelled separately from fictional game meters, decisions, and outcomes.
3. **No radiation-dose conversion:** DONKI event records and ACE, STEREO, OMNI, or LEND fields are not converted into astronaut dose or a lunar habitat exposure estimate.
4. **No medical inference:** OSD-53 is historical human research metadata/summary context, not a medical diagnosis or health forecast.
5. **No landing certification:** broad LOLA topography and Diviner remote-sensing products do not certify a site as safe or predict current habitat conditions.
6. **Navigation clarification:** LRO SPICE positions describe computed spacecraft geometry in a stated frame; they are not astronaut positions or direct telemetry.
7. **Communication simplification:** a vacuum light-time calculation is not actual network latency; real equipment, routing, and operations add delay.
8. **Availability:** static dataset records require the relevant local product; two large products are excluded from normal Git tracking because of individual-file size limits. Use the complete working copy and its download manifest.
9. **Persistence:** mission state is held in backend memory and does not survive a backend restart.
10. **Not a NASA product:** this is an independent student project; NASA data sources do not imply NASA endorsement.

## 11. Team, attribution, and project ownership

### VOID DOMINATORS

- Muhammad Shahroz Khan
- Abdul Rafay
- Maira
- Urwa Asif Qureshi
- Fatima Bukhari
- Ayesha Ashraf

The team confirms ownership of the project's original artwork. NASA datasets and NASA/JPL/NAIF services remain NASA/JPL source materials and must be cited accurately; the team does not claim their authorship or endorsement. Third-party libraries, fonts, and icons retain their respective owners and applicable terms. The repository currently has no project-level open-source license, so this report does not grant permission to reuse the code or artwork.

## 12. Sources and further reading

### NASA data and scientific source material

1. **Diviner:** [NASA PDS Geosciences Node product file](https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gcp/global_cumul_avg_cyl_80s70s_002.tab); [Diviner dataset notes](diviner_dataset.md).
2. **LOLA:** [NASA PDS LDEM_16 raster](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/ldem_16.img); [LOLA dataset notes](lola_dataset.md).
3. **ACE EPAM:** [NASA Goddard SPDF archive](https://spdf.gsfc.nasa.gov/pub/data/ace/epam/); [CDAWeb AC_H1_EPM](https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/AC_H1_EPM/); [ACE dataset notes](ace_epam_dataset.md).
4. **STEREO-A IMPACT HET:** [NASA SPDF selected daily product](https://spdf.gsfc.nasa.gov/pub/data/stereo/ahead/l2/impact_ascii/het/1day/AeH12Mar.1d); [STEREO dataset notes](stereo_impact_dataset.md).
5. **JPL Horizons:** [Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html); [JPL Horizons system](https://ssd.jpl.nasa.gov/horizons/); [project selection notes](jpl_horizons_dataset.md).
6. **OMNI2:** [NASA SPDF 2020 annual file](https://spdf.gsfc.nasa.gov/pub/data/omni/low_res_omni/omni2_2020.dat); [OMNIWeb variable guide](https://omniweb.gsfc.nasa.gov/html/ow_data.html); [project notes](omni_dataset.md).
7. **LEND:** [NASA PDS LEND archive](https://pds-geosciences.wustl.edu/missions/lro/lend.htm); [project notes](lend_dataset.md).
8. **LRO SPICE:** [NAIF archived data](https://naif.jpl.nasa.gov/naif/data_archived.html); [selected LRO archive](https://naif.jpl.nasa.gov/pub/naif/pds/data/lro-l-spice-6-v1.0/lrosp_1000/); [project notes](lro_spice_dataset.md).
9. **OSD-53 / GLDS-53:** [NASA OSDR study page](https://osdr.nasa.gov/bio/repo/data/studies/OSD-53); [study API](https://osdr.nasa.gov/geode-py/ws/repo/studies/OSD-53); [project notes](osd53_dataset.md).
10. **DONKI:** [NASA Open APIs](https://api.nasa.gov/); [DONKI dashboard](https://ccmc.gsfc.nasa.gov/DONKI/).
11. **Project-wide NASA source and validation notes:** [NASA data sources and validation](nasa_data_sources_and_validation.md); [dataset catalog](../datasets/metadata/dataset_catalog.csv); [NASA dataset integration architecture](nasa_dataset_integration_architecture.md).
12. **NASA mission and archive context:** [NASA PDS Geosciences Node](https://pds-geosciences.wustl.edu/); [NASA SPDF](https://spdf.gsfc.nasa.gov/); [NASA Open Science Data Repository](https://osdr.nasa.gov/); [NAIF](https://naif.jpl.nasa.gov/naif/data_archived.html).

### Software, libraries, and visual source references

- [Python](https://docs.python.org/3/), [FastAPI](https://fastapi.tiangolo.com/), [Uvicorn](https://www.uvicorn.org/), [Pydantic](https://docs.pydantic.dev/), [Requests](https://requests.readthedocs.io/), [python-dotenv](https://pypi.org/project/python-dotenv/).
- [NumPy](https://numpy.org/), [Pandas](https://pandas.pydata.org/), [cdflib](https://github.com/MAVENSDC/cdflib), [SpiceyPy](https://spiceypy.readthedocs.io/).
- [React](https://react.dev/), [React Router](https://reactrouter.com/), [Axios](https://axios-http.com/), [Motion](https://motion.dev/), [Recharts](https://recharts.org/), [Lucide](https://lucide.dev/), [Vite](https://vite.dev/), [Oxlint](https://oxc.rs/docs/guide/usage/linter.html).
- [Google Fonts stylesheet for Orbitron and Inter](https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap); [MDN Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API).
- Original project illustrations and CSS decorations: VOID DOMINATORS team ownership confirmation, as recorded in the complete project guide. Interface screenshots are project captures, not NASA images.

### Project documents

- [Complete project guide](lunar_guardians_complete_guide.md)
- [User manual](user_manual.md)
- [System architecture](system_architecture.md)
- [NASA data sources and validation](nasa_data_sources_and_validation.md)
- [Dataset catalog](../datasets/metadata/dataset_catalog.csv)
- [Project demonstration script](project_demonstration_script.md)
- [Local application screenshots](screenshots/)

---

**LUNAR GUARDIANS — VOID DOMINATORS**
An educational lunar mission game that makes space science approachable while being honest about what the data can and cannot tell us.
