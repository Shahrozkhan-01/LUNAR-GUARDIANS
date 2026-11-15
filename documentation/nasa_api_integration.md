# NASA DONKI API integration

LUNAR GUARDIANS fetches NASA DONKI solar-flare (`FLR`) and Solar Energetic
Particle (`SEP`) event records on the backend. No external datasets are
downloaded or required. NASA event records shown in the monitor are real
observations; mission resources and any gameplay changes remain simulated.

## Endpoints

The backend first requests the NASA API endpoints:

- `GET https://api.nasa.gov/DONKI/FLR`
- `GET https://api.nasa.gov/DONKI/SEP`

Both use `startDate` and `endDate` set to the last seven UTC calendar days and
the server-side `NASA_API_KEY`. If NASA's API gateway returns `404` or `429`,
or cannot be reached, the backend retries that feed using the corresponding
public endpoints in CCMC's current DONKI API v2:

- `GET https://ccmc.gsfc.nasa.gov/DONKI-API/get/FLR`
- `GET https://ccmc.gsfc.nasa.gov/DONKI-API/get/SEP`

The fallback receives the same date parameters and no API key. Both endpoint
families return NASA DONKI records; this fallback accommodates gateway
migration and key-based rate limits without using cached or fabricated
observations. Unauthorized responses (`401`/`403`) are reported rather than
hidden by fallback.

The application exposes:

- `GET /api/nasa/status`
- `GET /api/nasa/flares`
- `GET /api/nasa/sep`
- `GET /api/nasa/events`

Legacy routes `/api/nasa/solar-events` and `/api/nasa/last-updated` remain
available. Add `?refresh=true` to a data or status route to bypass the cache.

## Configuration and key safety

Create `backend/.env` from `backend/.env.example`:

```env
NASA_API_KEY=DEMO_KEY
NASA_CACHE_SECONDS=900
```

Replace `DEMO_KEY` with a personal key from [NASA Open APIs](https://api.nasa.gov/)
when available. `DEMO_KEY` has strict shared rate limits. The backend loads the
key from its environment (including the local `.env`) and never sends it to the
React app or includes it in an application response. `backend/.env` is ignored
by Git. If no key is configured, the backend uses `DEMO_KEY` for the NASA API
gateway; the public CCMC fallback itself does not require a key.

## Retrieval, validation, and cache

`backend/app/services/nasa_service.py` makes bounded-timeout HTTP requests,
checks HTTP status, parses JSON, validates that the response is an array of
event objects, and delegates event-specific normalization to
`backend/app/services/nasa_data_processor.py`. Missing fields remain `null` or
empty lists; the full original NASA record is retained. Each event and
response includes a retrieval timestamp.

The server caches both feeds for `NASA_CACHE_SECONDS` (900 seconds by default).
Opening or rendering the dashboard uses the backend cache; it does not call
NASA on every React render. The dashboard refresh button requests a forced
refresh.

Empty arrays are successful responses, not failures. An empty tab displays
**“No relevant events found for the selected period.”** Connection and error
messages distinguish unavailable data from an empty successful result. Timeout,
network, authorization, rate-limit, server, and malformed-response failures
never generate replacement events.

## Scientific limitations and gameplay separation

DONKI is an event catalog, not a lunar-outpost radiation dosimeter. SEP records
may be relevant to astronaut safety but do not by themselves give the crew's
lunar surface dose. A flare's X-ray class is not converted into particle
exposure or astronaut radiation dose. The event cards show only metadata NASA
actually supplied and a source link where available.

`REAL NASA DATA` identifies the observed event records. Game resource values,
shelter choices, and consequences use fictional simulation mechanics and are
labeled `SIMULATED GAME CONSEQUENCE`. They are not NASA measurements or
operational safety advice. The existing game remains playable when either or
both NASA feeds are unavailable.

## How NASA observations enter mission events

The Mission Control monitor loads and caches both feeds. On each mission-day
advance, the simulation reads only the server's still-fresh cached records; it
does not make a NASA request while advancing gameplay. If a valid, dated SEP or
FLR record is available and has not already appeared in that mission, the game
can add one NASA-informed alert. It waits until the current active event is
resolved, and tracks stable event identities to avoid repeating an observation.
If there is no fresh eligible record, the normal simulated event system
continues unchanged.

- A dated **SEP** observation can create a **Solar Energetic Particle Alert**.
  It explains that energetic particles may matter for astronaut safety, while
  explicitly stating DONKI does not provide lunar crew dose. Choices are to
  use the game's existing shelter action, pause outdoor work and monitor, or
  continue normal operations.
- A dated **FLR** observation can create a **Solar Activity Monitoring Alert**.
  This is a monitoring and science-scheduling exercise, not a radiation
  warning. Its choices are to monitor updates, pause outdoor observations, or
  continue scheduled research. Flare class is never used to infer astronaut
  radiation risk.

The dedicated **NASA Space Weather Alerts** panel identifies the NASA event
type, date, identifier, source link, child-friendly explanation, and mission
situation. Each choice uses the existing `resolve_event` action path. Game-only
changes (such as power, shield indicator, exposure indicator, or science points)
are returned in a feedback message labeled **SIMULATED GAME CONSEQUENCE**.
SEP shelter and exposure changes reuse the existing game mechanics; FLR choices
only affect simulated power/science scheduling and do not alter radiation
indicators. These simple outcomes do not represent real operational guidance.

NASA references: [NASA Open APIs](https://api.nasa.gov/),
[CCMC DONKI](https://ccmc.gsfc.nasa.gov/DONKI/), and its
[OpenAPI specification](https://ccmc.gsfc.nasa.gov/DONKI/api/).
