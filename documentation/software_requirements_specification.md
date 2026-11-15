# Software Requirements Specification

## 1. Introduction

This specification describes the implemented LUNAR GUARDIANS educational lunar
mission trainer, its interfaces, NASA-data boundaries, and acceptance criteria.

## 2. Purpose

The system teaches children basic mission planning through an interactive
simulation while showing how real NASA observations, historical datasets,
computed ephemerides, derived values, and fictional game consequences differ.

## 3. Scope

In scope: mission configuration, simulation progression, resources, events,
decisions, scoring/debrief, NASA DONKI, five processed NASA datasets, NASA
briefings/training events, responsive UI, accessibility polish, and local
offline fallbacks. Dataset values are not used to calculate game resources.

Out of scope: live lunar telemetry, astronaut dosimetry, detailed landing
hazard mapping, network-delay modeling, user accounts, and persistent database
storage.

## 4. Intended users

- Primary: learners approximately 7–12 years old.
- Secondary: teachers, parents, and demonstrators.
- Operator: a local user running the documented Windows development setup.

## 5. Functional requirements

| ID | Requirement |
|---|---|
| FR-01 | The system shall allow a user to select lunar destination, difficulty, crew size, and duration. |
| FR-02 | The system shall initialize missions through `POST /api/game/start`. |
| FR-03 | The system shall display simulated oxygen, water, power, food, shield, crew, subsystem, and Science Point state. |
| FR-04 | The system shall advance missions by day and apply existing simulation rules. |
| FR-05 | The system shall display and resolve normal events and player decisions. |
| FR-06 | The system shall provide three optional NASA briefing presets. |
| FR-07 | The system shall provide NASA Training Events without making them required for progression. |
| FR-08 | The system shall integrate cached DONKI SEP and FLR records without exposing API keys. |
| FR-09 | The system shall list dataset metadata and summaries through read-only endpoints. |
| FR-10 | The system shall paginate supported ACE EPAM, STEREO-A, and Horizons records and refuse normal record responses for Diviner/LOLA grids. |
| FR-11 | The system shall show source dates, units, provenance, labels, and scientific limitations where available. |
| FR-12 | The system shall provide mission completion/failure status, score, final resources, decisions, events, lessons, and replay actions. |
| FR-13 | The system shall remain playable when NASA or dataset services are unavailable. |
| FR-14 | The system shall provide responsive navigation and an opt-in persisted sound control. |

## 6. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | The frontend shall use semantic, keyboard-accessible controls with visible focus. |
| NFR-02 | Reduced-motion preferences shall suppress non-essential animation. |
| NFR-03 | NASA keys shall remain server-side and local `.env` files shall not be committed. |
| NFR-04 | Dataset endpoints shall use a fixed server-side allowlist and never accept arbitrary filesystem paths. |
| NFR-05 | Large datasets shall not be loaded entirely into ordinary API responses. |
| NFR-06 | Service failures shall produce explicit user-facing status/errors rather than fabricated data. |
| NFR-07 | The UI shall avoid horizontal overflow at tested desktop and mobile widths. |
| NFR-08 | Changes shall preserve existing gameplay formulas and scoring. |

## 7. System requirements

Windows PowerShell, Python 3.10+, Node.js/npm, the repository virtual
environment, and a modern browser with JavaScript enabled are required.

## 8. External interface requirements

Frontend routes: `/`, `/mission-setup`, `/mission-control`, `/nasa-data`.

Backend game routes include `POST /api/game/start`, `GET /api/game/{mission_id}`,
`POST /api/game/{mission_id}/action`, `POST /api/game/{mission_id}/advance`,
`GET /api/game/{mission_id}/events`, and
`POST /api/game/{mission_id}/power`.

Dataset routes include `/api/datasets`, `/{dataset_id}/metadata`,
`/{dataset_id}/summary`, and `/{dataset_id}/records`.

NASA routes include `/api/nasa/status`, `/events`, `/solar-events`, `/sep`,
`/flares`, and `/last-updated`.

## 9. NASA API requirements

DONKI requests use backend environment configuration, a previous-seven-day
window, bounded timeouts, in-memory caching, normalized event-specific fields,
empty-response handling, rate/error handling, and no frontend key exposure.

## 10. Constraints and assumptions

The local mission store is in memory. NASA data may be historical, empty,
partially available, or unavailable. The game is educational and does not
provide operational safety advice or dose estimates.

## 11. Acceptance criteria

- A user can configure and launch a mission.
- Daily progression, events, decisions, completion, failure, and relaunch work.
- NASA and dataset screens clearly distinguish real, computed, derived, and
  simulated information.
- Missing services keep the mission setup/play path usable.
- The backend suite, frontend lint, and production build pass.
- Tested responsive viewports have no horizontal overflow.
