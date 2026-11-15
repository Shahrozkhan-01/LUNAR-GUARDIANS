# NASA-informed gameplay training events

## Scope and separation

Mission Control provides three optional, decision-based learning scenarios:
South Polar Environment, Space Weather Preparedness, and Earth-Moon
Communication. They are `SIMULATED TRAINING EVENT`s, not NASA alerts, and are
stored separately from the existing `active_events` queue. Resolving or
ignoring them does not gate mission progression or apply passive event
consequences.

The backend snapshots available context when a mission starts using the
existing local `dataset_service`. It reads only saved summaries and bounded
first pages for record-supported datasets; Diviner and LOLA remain summary-only.
DONKI context comes only from the already-fresh in-memory cache. Mission start
does not make NASA network requests. Missing data are identified as unavailable
and never replaced with invented measurements.

The game-state API distinguishes:

- `REAL NASA DATA` — actual source records or measurements and their original
  source date.
- `COMPUTED EPHEMERIS` — the Horizons calculated range and one-way light time
  for the supplied epoch.
- `DERIVED VALUE` — saved summary statistics and the derived two-way vacuum
  light time.
- `SIMULATED TRAINING EVENT` — the fictional learning scenario.
- `SIMULATED GAME CONSEQUENCE` — the fixed game-only effect of a selected
  response.

None of the NASA values is converted to a resource, habitat temperature, crew
dose, or real-time lunar condition. ACE, STEREO-A, Diviner, LOLA, DONKI, and
Horizons values retain separate dataset dates and are not presented as one
simultaneous event.

## Event and dataset mapping

| Training event | NASA context shown | Player choices |
|---|---|---|
| **South Polar Environment Challenge** | Diviner bolometric brightness-temperature mean from the saved summary (`DERIVED VALUE`) and LOLA global mean elevation relative to its reference radius (`DERIVED VALUE`), each with catalog coverage and source. | Review habitat power reserves; schedule a broad terrain-context review; keep the plan and record the limitations. |
| **Space Weather Preparedness** | One valid ACE EPAM P7/P8 sample from the bounded first record page (when available); one STEREO-A electron and proton intensity sample from its first valid records; a fresh eligible DONKI SEP event record, if cached. Each item retains its own timestamp, units, source, and spacecraft/event identity. | Enter simulated protected-operation mode; postpone an optional outdoor activity; continue with a simulated monitoring plan. |
| **Earth-Moon Communication Challenge** | The first saved Horizons epoch's Earth-Moon range and one-way down-leg light time (`COMPUTED EPHEMERIS`) plus the saved two-way vacuum light-time calculation (`DERIVED VALUE`). | Wait for a complete response; use a pre-approved autonomous procedure; schedule a non-urgent communication session. |

These are educational presets, not claims that records with different dates
describe the same event. Each data point displays its dataset name, source,
measurement, value, units, date or coverage, and a limitation note. Source
links are shown when the catalog provides one.

## Decision effects

The effects are constants in the game rules and do not depend on NASA
measurements:

| Choice | Simulated effect |
|---|---|
| Review environment power-reserve plan | -2 Power; +3 practice Science points. |
| Schedule broad terrain-context review | -3 Power; +4 practice Science points. |
| Keep environment plan and record limitations | No resource change; +1 practice Science point. |
| Enter protected-operation mode | Calls the existing radiation-shelter mechanic: -10 Power, up to +15 Shield, up to -8 on the simulated radiation indicator, three simulated shelter days, and existing power-allocation/research rules. All values are clamped by the existing resource system. |
| Postpone optional outdoor activity | No resource change; defers up to 2 practice Science points. It does not alter crew dose. |
| Continue with simulated monitoring | -2 Power; +3 practice Science points. |
| Wait for a complete communication response | -2 Power; +2 practice Science points. |
| Use pre-approved autonomous procedure | No resource change; +3 practice Science points. |
| Schedule a non-urgent communication session | -1 Power; +1 practice Science point. |

Decision results are stored on the training event and displayed in Mission
Control under `SIMULATED GAME CONSEQUENCE`, including changed game indicators.
Resource requirements are supplied with each choice; unavailable choices are
disabled in the UI and rejected by the backend if resources changed or a client
submits an unaffordable action. A resolved choice cannot be replayed.

## Scientific limitations

- Diviner brightness temperature is historical surface context, not live
  habitat or astronaut temperature.
- LOLA global elevation is broad terrain context, not detailed landing hazard
  information.
- ACE EPAM values are spacecraft observations from ACE, not lunar-surface
  conditions or astronaut radiation dose.
- STEREO-A IMPACT values are spacecraft observations from STEREO-A, not lunar
  conditions or astronaut radiation dose.
- A DONKI SEP record is event metadata, not lunar surface dosimetry. It does not
  by itself establish the outpost's current risk.
- Horizons values are computed ephemerides for their saved epochs, not
  observations. The two-way vacuum light time is derived, and neither
  light-time value includes network or processing delays.
- Game resources, Science points, shield, and radiation indicators are
  simulation values; none is a NASA measurement.

## Offline and persistence behavior

The event definitions are created with each mission. Dataset-service errors or
missing processed files result in an unavailable/partial context status and a
plain explanation; the decision lesson remains usable. No dataset is fetched
from the internet and no API key is used by this feature. A fresh DONKI SEP
record can be attached as context; its existing deduplication key is recorded
so the same observation is not separately triggered as a duplicate DONKI
mission scenario. When no eligible cached record is available, the scenario
explicitly says it is simulated and not a NASA alert.

Training events and their resolved choices are part of the existing
`GameState`, so they use the existing mission-store fetch/action flow. They do
not enter the active-event queue and do not change resource calculations or
event consequences during day advancement.

## Implementation and validation

- Context assembly: `backend/app/services/nasa_training_service.py`.
- Training choice handling: `backend/app/services/event_manager.py`.
- Mission creation and action routing: `backend/app/services/simulation.py`.
- State and response models: `backend/app/models/schemas.py`.
- Mission Control cards: `frontend/src/components/NasaTrainingEvents.jsx` and
  `frontend/src/components/NasaTrainingEvents.css`.
- Backend coverage: `backend/tests/test_nasa_training_events.py`, including
  all nine choices, bounds, missing datasets, duplicate DONKI prevention,
  progression, and event labels.

Validation completed:

- Backend: `python -m unittest discover -s tests -v` — **48 tests passed**.
- Frontend: `npm run lint` — **passed**.
- Production build: `npm run build` — **passed**. Vite emitted an advisory
  that the main minified bundle exceeds 500 kB; it did not fail the build.
- Browser: launched a mission using the existing Mission Setup flow; verified
  all three Mission Control event cards, real/computed/derived context labels,
  dates and units, and the separate NASA Space Weather Alerts panel. Selected
  the autonomous-procedure decision and verified the event resolved with a
  visible `SIMULATED GAME CONSEQUENCE`. At a 390 px viewport, the training
  cards collapsed to one column and fit their container.
- Backend fallback tests cover unavailable and partial dataset context,
  playable progression, bounded resource effects, and duplicate DONKI SEP
  prevention.
