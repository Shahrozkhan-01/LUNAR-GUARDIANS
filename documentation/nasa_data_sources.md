# NASA DONKI space-weather data

LUNAR GUARDIANS uses NASA's **Space Weather Database Of Notifications,
Knowledge, Information (DONKI)** to show recent solar activity in Mission
Control. The NASA observations are real; gameplay resources and outcomes remain
educational simulations.

## What the DONKI records mean

- **Solar Energetic Particles (SEP):** DONKI SEP records report observed or
  analyzed solar energetic-particle events. Energetic particles can be relevant
  to astronaut radiation safety. A DONKI SEP record is not a measurement of
  radiation dose at the Moon, a habitat, or an astronaut.
- **Solar flares (FLR):** flare records describe solar flare events, including
  their timing and, when reported, a `classType`. Flare class describes flare
  X-ray brightness; it is not an astronaut radiation dose and is not converted
  into one by this application.

NASA DONKI is a space-weather event catalog, not a lunar-outpost dosimeter.

## Endpoints and attribution

The backend first calls NASA Open APIs' DONKI gateway:

- SEP: `https://api.nasa.gov/DONKI/SEP`
- Solar flares: `https://api.nasa.gov/DONKI/FLR`

Both requests use NASA's `startDate` and `endDate` parameters for the latest
seven UTC calendar dates, plus the key held by the backend. If the gateway
returns a rate limit, is unavailable, or does not provide the requested route,
the backend retries the same feed using the public CCMC DONKI API v2 endpoint:

- SEP: `https://ccmc.gsfc.nasa.gov/DONKI-API/get/SEP`
- Solar flares: `https://ccmc.gsfc.nasa.gov/DONKI-API/get/FLR`

The CCMC fallback does not require an API key. An unauthorized gateway response
is reported instead of hidden by fallback. The date range and retrieval time
are included in application responses. NASA's public references are the
[NASA Open APIs portal](https://api.nasa.gov/) and the
[CCMC DONKI dashboard](https://ccmc.gsfc.nasa.gov/DONKI/). NASA is the source of
the event records. Each normalized record keeps its original DONKI fields and,
when supplied by NASA, the source link, event identifier, event time, linked
events, instruments, flare class, note, and other event-specific fields. The
dashboard links to NASA's event record when a source link is present.

## Retrieval, processing, and caching

`backend/app/services/nasa_service.py` calls NASA from the backend using the
documented public DONKI API. It uses a bounded request timeout and an in-memory
cache. `NASA_CACHE_SECONDS` controls the cache lifetime (900 seconds
by default). The dashboard loads data when opened and offers a refresh button;
it does not call NASA on every React render. Refresh bypasses the cache.

`backend/app/services/nasa_data_processor.py` normalizes the event types to a
shared shape (`event_type`, `event_id`, `event_time`, `linked_events`,
`instruments`, `source_url`, `description`, `notes`, `category`, and
`classification_explanation`) while preserving the original record. DONKI
fields that are optional or absent are represented as `null` or empty lists.
An empty NASA array is a successful retrieval with zero events, not an error.

`backend/app/services/nasa_event_classifier.py` contains the editable
`CLASSIFICATION_RULES` policy:

- A timed SEP report is labeled **INSUFFICIENT DATA FOR RISK ASSESSMENT** because
  these records do not supply a lunar surface dose or sufficient particle-flux
  information to calculate astronaut exposure.
- A timed flare record is labeled **INFORMATIONAL**. Its flare class is not used
  to calculate radiation risk.
- Records without a usable event time, or with an unsupported event type, are
  labeled **INSUFFICIENT DATA FOR RISK ASSESSMENT**.

These are educational information labels, not operational space-weather
warnings or safety assessments. No thresholds, particle measurements, dose
values, or observations are invented.

## Gameplay and the real/simulated distinction

When fresh DONKI data is available, a timed SEP record can create one
low-severity awareness scenario on the next mission-day transition. An event's
stable key and timestamp are tracked in that mission's state, so it cannot
create a second scenario in that mission. A record without a usable event time
cannot create a timed scenario. Solar-flare records are shown for learning but
do not automatically trigger a shelter scenario.

The scenario identifies its observation as **REAL NASA DATA**, explains why
energetic particles may be relevant to astronauts, and links to the NASA record
when possible. The player may activate the Radiation Shelter using existing
game action rules. Resource changes and any result of leaving the scenario
unresolved are labeled **SIMULATED GAME CONSEQUENCE** and use the game's
fictional units. They do not represent actual radiation exposure or a
prediction about astronauts.

The pre-existing simulated training-event system continues to run independently.
Mission advancement reads only already-cached SEP observations; it never waits
for an external NASA request. NASA availability is not required to start or
play a mission.

## Configuration and failure handling

Create `backend/.env` from `backend/.env.example` and configure:

```env
NASA_API_KEY=DEMO_KEY
NASA_CACHE_SECONDS=900
```

Replace `DEMO_KEY` with a personal key from [NASA Open APIs](https://api.nasa.gov/)
when available; NASA's shared demo key has strict rate limits. If no key is
configured, the backend uses `DEMO_KEY` for the gateway and can use the public
CCMC fallback. The API key remains server-side and is never returned to React.
`NASA_CACHE_SECONDS` is configurable; `.env` remains excluded by `.gitignore`.
The frontend receives normalized NASA event data and status only.

The API distinguishes active, partial, and unavailable connections. It reports
timeouts, connection errors, invalid keys, rate limits, NASA server errors, and
malformed responses with safe messages. A failure is not converted into fake
observations. If NASA is unavailable, the dashboard says
**NASA DATA TEMPORARILY UNAVAILABLE**, and the existing game remains playable.
The last successful retrieval time is retained where available.

## API routes exposed by this application

- `GET /api/nasa/status` — connection state, date window, event count, and last
  successful retrieval time. Add `?refresh=true` to bypass the cache.
- `GET /api/nasa/solar-events` — normalized SEP and flare records.
- `GET /api/nasa/events` — alias for normalized SEP and flare records.
- `GET /api/nasa/sep` — normalized SEP records.
- `GET /api/nasa/flares` — normalized flare records.
- `GET /api/nasa/last-updated` — last successful retrieval time.

These application routes never include the NASA API key in their responses.
