# NASA dataset integration architecture

## Purpose and scope

This document records the current DONKI integration and proposes safe,
incremental paths for the project's processed NASA datasets. The static
datasets are exposed through read-only backend endpoints and an optional
Mission Setup briefing. They do not affect simulation state, resources, or
event consequences. The existing DONKI integration is preserved.

The governing boundary is:

1. **NASA source data** retain their source, time, units, and provenance.
2. **Educational interpretation** explains what those data can and cannot
   establish.
3. **Simulated game consequences** remain fictional game mechanics, never
   reported as NASA measurements or safety assessments.

## Current DONKI integration

### Backend services and routes

| Component | Current responsibility |
|---|---|
| `backend/app/services/nasa_service.py` | Retrieves DONKI SEP and FLR feeds; requests the previous seven UTC calendar dates concurrently; uses the server-side `NASA_API_KEY`; has a bounded `(10, 20)` second connect/read timeout; and caches a combined snapshot in memory for `NASA_CACHE_SECONDS` (900 seconds by default). The NASA gateway is tried first and CCMC's public DONKI API is used as a fallback for request or malformed-response failures, except gateway 401/403 responses. |
| `backend/app/services/nasa_data_processor.py` | Validates array/object response shapes and normalizes event-specific fields while retaining the original NASA record. Missing optional fields are represented as nulls or empty lists. |
| `backend/app/services/nasa_event_classifier.py` | Labels SEP records `INSUFFICIENT DATA FOR RISK ASSESSMENT`, since DONKI event metadata is not lunar dose data. Labels timed FLR records `INFORMATIONAL`; flare class is not treated as astronaut dose. |
| `backend/app/services/event_manager.py` | Creates low-severity, educational scenarios from eligible dated SEP or FLR records. It deduplicates by event key, waits for unresolved scenarios, and labels game effects separately from real source records. |
| `backend/app/services/simulation.py` | Reads only fresh cached NASA records during mission-day advancement. It does not make a NASA request as part of the gameplay step; with no eligible record it proceeds to the existing simulated-event behavior. |
| `backend/app/routes/nasa.py` | Exposes the NASA status and event routes listed below, with meaningful service-unavailable errors for unavailable feeds. |

The registered read-only routes are:

| Route | Current response |
|---|---|
| `GET /api/nasa/status` | Active, partial, or unavailable feed status, date window, event count, endpoint errors, and last successful retrieval time. |
| `GET /api/nasa/events` | Combined normalized SEP and FLR records. |
| `GET /api/nasa/solar-events` | Legacy alias for combined normalized solar events. |
| `GET /api/nasa/sep` | Normalized SEP records. |
| `GET /api/nasa/flares` | Normalized FLR records. |
| `GET /api/nasa/last-updated` | Last successful retrieval time and connection status. |

`?refresh=true` requests a new backend snapshot on status and event routes.
An empty event array is a successful response, not an outage. When only one
feed succeeds, the service reports partial availability and can return the
successful feed. When both are unavailable, routes return a clear service
error; no replacement NASA events are fabricated.

The key is loaded by the backend from its environment or local `backend/.env`,
with `DEMO_KEY` as the code default. It is not part of frontend requests or
application responses. The actual local `.env` contents and key validity were
not inspected or tested.

### Frontend and gameplay behavior

`frontend/src/services/gameApi.js` fetches status and then requests FLR and SEP
in parallel. A feed-specific failure is handled independently. The Mission
Control NASA panel shows status, retrieval time, feed counts, normalized event
details, source links when provided, and a refresh action. It labels source
events `REAL NASA DATA` and explains that gameplay outcomes are simulated.
Event times are parsed as JavaScript dates and displayed with
`toLocaleString()`, so the displayed clock time follows the user's browser
timezone and is not explicitly labeled UTC. The source timestamp is retained
in the normalized record; explicitly labeling the display timezone is a
potential clarity improvement, not a blocking failure found by the tests.

SEP shelter choices and their resource/exposure indicators use existing game
mechanics. Those values are not NASA dosimetry. FLR scenarios are monitoring
and science-scheduling exercises, not radiation warnings. Event IDs/timestamps
and a stable deduplication key prevent the same source event from being
replayed within a mission.

If NASA is unavailable, the dashboard reports the outage and mission
advancement does not wait on the network. A fresh cached NASA event may be used
until the cache expires; after expiration, no NASA records are used for that
step and ordinary game-event behavior remains available.

## Dataset-to-game mapping

DONKI retains its dedicated live API service, routes, and gameplay event
handling. The five processed static datasets have read-only backend
metadata/summary access, with bounded record pages for ACE EPAM, STEREO-A, and
Horizons. Mission Setup uses them for an optional educational briefing, and
Mission Control snapshots available dataset context into optional training
events. These datasets are not resource-calculation dependencies.

| Dataset | Information and data nature | Appropriate educational use | Limitations and prohibited interpretation | Backend access | Unavailable/offline behavior |
|---|---|---|---|---|---|
| **DONKI SEP and FLR** | Recent NASA DONKI event-catalog records retrieved through NASA's API (with a public CCMC DONKI fallback). Records contain event-specific metadata; they are not an outpost dosimeter. | Identify real solar activity, discuss why particle events prompt attention, and offer a fictional shelter/monitoring decision. | A SEP record does not automatically provide lunar surface dose. Flare class is not astronaut radiation dose. Never elevate a gameplay severity based on a flare class alone or present simulated consequences as observations. | Existing `nasa_service.py` → `nasa_data_processor.py` → `nasa_event_classifier.py`; current routes and event-manager integration remain authoritative. | Dashboard reports feed-level partial/unavailable status. Gameplay stays playable and uses its regular simulated-event behavior. No fabricated observation. |
| **Diviner** | Processed historical LRO Diviner global cumulative product for 70°S–80°S, with longitude, latitude, local time, and brightness-temperature channels; data span 2009–2015. The converted source is a gridded remote-sensing product. | Optional historical lunar south-polar environment comparison or a map/learning activity using clearly named locations and observation context. | Brightness temperature is not live habitat, astronaut, or forecast temperature. It is a historical remote-sensing product and must retain documented missing-value and unit semantics. | `dataset_service.py` exposes catalog metadata and saved summaries. Record-level access is disabled to avoid returning 1,382,400 rows. | Show explicit file availability; do not substitute current conditions or invented readings. Missions continue using existing simulated values. |
| **LOLA LDEM_16** | Processed global, simple-cylindrical LRO elevation grid with preserved integer samples, derived elevation, and coordinate axes. Broad-scale terrain; nominally about 1.9 km/pixel. | Broad regional elevation context or a comparison of large-scale lunar terrain. | Not detailed landing-site hazard, slope, boulder, or local safety data. Preserve the observed-versus-label extrema warning and the documented reference-radius conversion. Never infer a safe landing site. | `dataset_service.py` exposes catalog metadata and saved summaries. Record-level access is disabled; the full 16,588,800-sample raster is never loaded for an API response. | If files or coverage are unavailable, disclose this and omit the contextual layer. Do not invent terrain values; keep the game playable. |
| **ACE EPAM** | A 277-record, one-day 2020 `AC_H1_EPM` sample from ACE near Sun–Earth L1, with measurement and uncertainty variables preserved in a compressed NumPy archive. | Historical example for teaching how spacecraft particle instruments report channels, units, uncertainty, and missing measurements. | ACE is not at the Moon; these are neither lunar surface conditions nor astronaut dose. The sample is historical and not real-time lunar weather. Never convert channels into dose. | `dataset_service.py` returns bounded record pages, preserving original values and separate validity masks; metadata and summaries describe channel units. It is separate from DONKI. | Missing archive files return an explicit unavailable error; no fill values are replaced, no interpolation occurs, and gameplay proceeds without it. |
| **STEREO-A IMPACT HET** | 31 daily records from March 2012 in the processed STEREO-A HET Level 2 daily-average file; 3 electron and 11 proton channels with corresponding one-sigma uncertainties. | Historical comparison of particle channel values, uncertainty, and instrument-specific daily intervals. | STEREO-A is not at the Moon; measurements are not lunar surface conditions or astronaut dose, and do not represent current space weather. Preserve channel energy ranges, units, and uncertainty. | `dataset_service.py` streams bounded pages from the compressed CSV; channel definitions and uncertainty remain distinct. | Missing archive files return an explicit unavailable error. No synthetic sample is returned; the game has no dependency on it. |
| **JPL Horizons Earth–Moon** | A saved eight-epoch Earth–Moon computed ephemeris with UTC epochs, range, range rate, and one-way down-leg light time; two-way vacuum light time is a derived calculation. | Demonstrate changing Earth–Moon distance and explain idealized light travel time. | Computed ephemerides are not direct observations. Future epochs in the saved query were predictions relative to retrieval time. Two-way vacuum light time is not total network/equipment/processing delay. Do not call saved values live. | `dataset_service.py` serves bounded pages of the saved CSV and includes the computed/derived distinctions and provenance. It does not query Horizons. | Missing files return an explicit unavailable error; out-of-range data is not extrapolated. The simulation remains playable. |

Dataset paths, provenance, processing details, and validation are documented
in the linked per-dataset documentation and in
[`datasets/metadata/dataset_catalog.csv`](../datasets/metadata/dataset_catalog.csv).
The present file inventory includes the Diviner gzip CSV, LOLA NPZ, ACE EPAM
NPZ, STEREO-A compressed CSV, and Horizons CSV under their respective
`datasets/processed/` subdirectories.

## Static dataset API currently available

The read-only API uses fixed dataset IDs and local project files; it accepts no
filesystem paths and performs no network calls. It exposes:

- `GET /api/datasets` for catalog metadata and file availability.
- `GET /api/datasets/{dataset_id}/metadata` for source, coverage, units,
  validation status, and curated processing metadata.
- `GET /api/datasets/{dataset_id}/summary` for the saved processing summary.
- `GET /api/datasets/{dataset_id}/records?page=1&page_size=50` for bounded
  ACE EPAM, STEREO-A, and Horizons pages (maximum 100 records).

Diviner and LOLA record access returns `409`; these large products expose only
metadata and saved summaries. Missing or unreadable files produce explicit
unavailable responses. See
[`documentation/nasa_dataset_backend.md`](nasa_dataset_backend.md) for
response examples, pagination, and error semantics. The NASA Data Explorer and
Mission Setup briefing consume these endpoints without changing the game state.

## Mission Setup NASA briefing

`frontend/src/components/NasaMissionBriefing.jsx` fetches the dataset catalog,
metadata, summaries, and bounded first-page records for ACE EPAM, STEREO-A, and
Horizons. It presents five separate dataset cards and three selectable
educational presets: South Polar Exploration (Diviner and LOLA), Space Weather
Preparedness (ACE EPAM and STEREO-A), and Communication and Navigation
(Horizons). The selected preset is retained with local setup preferences only;
the game-start request and simulation do not consume it.

The briefing displays source-provided coverage, units, summary statistics, and
sample records where available. It labels Horizons as a computed ephemeris and
two-way vacuum light time as derived. ACE and STEREO periods are shown
separately, not combined as a simultaneous event. Dataset limitations are
presented from API metadata alongside contextual explanations.

When the catalog request fails, the briefing reports the service outage and
offers retry; dataset-specific errors are shown independently. Empty or missing
measurements remain unavailable rather than being replaced. The briefing is
informational: it does not change initial resources, invoke DONKI, alter the
simulation engine, or change event consequences. Mission launch remains
available when dataset APIs or files are unavailable.

## NASA-informed Mission Control training events

Mission Control now offers three optional, persisted training-event categories:
South Polar Environment (Diviner and LOLA), Space Weather Preparedness (ACE,
STEREO-A, and eligible cached DONKI SEP context), and Earth-Moon Communication
(Horizons). Their data points preserve source, units, and original dates, with
explicit `REAL NASA DATA`, `COMPUTED EPHEMERIS`, or `DERIVED VALUE` labels.
Each card also explains limitations and provides three decisions.

Training events are a separate `GameState.nasa_training_events` collection;
they do not enter `active_events`, cause passive effects on day advancement,
or gate mission progression. Resolution uses a distinct action ID and existing
bounded resource/shelter mechanics with fixed, explicitly simulated outcomes.
An event can be resolved once. The existing DONKI scenario system and alert
panel remain unchanged; a fresh eligible SEP event used as training context is
marked seen by its existing deduplication key to avoid showing the same source
event again as a separate alert.

Context is assembled at mission creation from the existing local
`dataset_service` summaries and bounded record pages. Diviner/LOLA remain
summary-only; ACE, STEREO-A, and Horizons access at most 50 records. DONKI is
read through the fresh in-memory cache only, without a gameplay network
request. Missing files, empty records, and unavailable DONKI context are
reported as unavailable/partial; the lessons remain playable without invented
values. These scenarios do not combine unrelated historical dates into a
single real event and do not convert measurements into radiation dose,
habitat temperature, or resource consequences.

Implementation details, fixed choice effects, and category mapping are in
[`documentation/nasa_gameplay_integration.md`](nasa_gameplay_integration.md).

## Integration rules and proposed changes

These rules govern this read-only API and any later gameplay integration:

1. **Preserve provenance:** every returned value should identify its dataset,
   product/version, source timestamp or coverage, units, and whether it is an
   observation, a remote-sensing product, a computed ephemeris, or a derived
   quantity.
2. **Keep measurements and game state separate:** do not write raw or derived
   dataset values into crew dose, habitat temperature, resources, or safety
   state. A teaching scenario may reference a source fact, but its choices and
   outcomes must remain explicitly simulated.
3. **Keep static archive and live API paths distinct:** DONKI remains the
   existing network-backed event service. Static products should be read
   locally, read-only, with their historical coverage shown; they should not
   require an internet connection.
4. **Bound data access:** avoid loading large products on every request.
   Validate file existence, schema, coordinates/timestamps, and requested
   bounds; return small summaries or tiles rather than an entire raster or
   multi-million-row table.
5. **Make absence explicit:** missing files, out-of-range time/coordinates,
   missing measurements, and service errors must remain distinct from valid
   empty results. Never fabricate, interpolate, or silently substitute
   measurements.
6. **Preserve current gameplay:** new contextual data is optional. When
   unavailable, the game continues with existing game mechanics and simulated
   events.
7. **Protect secrets:** only the existing DONKI backend path uses its NASA API
   key. Static-data APIs have no reason to expose or receive that key.

The first optional gameplay integration described above is complete. Future
dataset integrations should continue with this sequence:

1. Select one additional bounded educational use case and define its UI labels,
   valid coverage, and non-goals before connecting another dataset to gameplay.
2. Keep the current static data service read-only and separate from DONKI;
   extend its API only for a documented need, preserving bounded reads and
   provenance.
3. Validate any newly exposed value against the original processed file and
   source metadata. Add client display only after backend and scientific checks
   pass.
4. If future work adds gameplay effects, do so separately from this briefing
   and only after offline behavior, UI labels, and simulation-only consequences
   have dedicated tests.

## Regression tests to retain as integration expands

The first backend phase adds API tests for supported-dataset listing, metadata
and summary retrieval, pagination, invalid IDs, missing files, empty datasets,
large-grid record restrictions, and scientific metadata. These tests are in
`backend/tests/test_dataset_api.py`; they do not imply simulation integration.
Mission Setup regression checks should retain preset-to-dataset mapping,
source-backed dates/units, independent missing-data handling, API-outage
fallback, mission launch with a selected preset, and unchanged game resource
initialization.

### Current DONKI regression checks

- SEP and FLR successful retrieval, normalization, cache use, last-updated
  status, and route response shape.
- Empty array as successful zero-event data; partial and total outages; timeout,
  connection, HTTP error, unauthorized, rate-limit, malformed JSON, and
  malformed event object behavior.
- No API key in API responses or frontend code; no NASA request during
  mission-day progression.
- Deduplication, event time eligibility, and no fabricated event when feeds
  are empty or unavailable.
- SEP and FLR educational classifications, source provenance, event links, and
  separation between NASA observations and simulated game effects.
- Mission remains playable with both feeds unavailable and with either feed
  independently unavailable.

### Additional checks for further gameplay integrations

- Deterministic readback of dimensions, record counts, variable/channel names,
  units, coordinate/time coverage, and source metadata against the processed
  files and validation reports.
- Missing/fill-value preservation and valid-value statistics; no interpolation,
  fabricated records, channel merging, or hidden extrema changes.
- Out-of-bounds requests, absent/corrupt files, and empty selections return
  explicit statuses without crashing or producing success-shaped fake data.
- Large-file access is bounded and does not reload entire products on every
  request; verify memory/runtime at realistic request sizes.
- Offline mode requires no NASA network call for static products and never
  changes game availability.
- UI and API tests assert source/units/coverage labels and the distinct
  `REAL NASA DATA` versus `SIMULATED GAME CONSEQUENCE` meaning.
- Dataset-specific scientific guardrails: ACE/STEREO are not lunar dose;
  Diviner is not live habitat temperature; LOLA is not landing hazard data;
  Horizons future epochs are not observations and derived two-way vacuum time
  is not end-to-end communication delay.

## Validation note

The previous DONKI audit verified the existing DONKI tests, frontend lint, and
production build. The static dataset backend's current test and build results
are recorded in
[`documentation/nasa_dataset_backend.md`](nasa_dataset_backend.md). Static
dataset access does not make live NASA requests and does not change game
availability. The Mission Control training-event test coverage and current
validation results are documented in
[`documentation/nasa_gameplay_integration.md`](nasa_gameplay_integration.md).
The gameplay phase completed with 48 backend tests passing, frontend lint and
production build passing, and a browser check of Mission Control event display
and decision resolution. The production build reports a bundle-size advisory
for the main minified JavaScript chunk; the build succeeds.
