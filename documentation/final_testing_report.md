# Local Testing and Validation Report

**Verification date:** 2026-11-15

## Automated checks

| Check | Result |
|---|---|
| `.\venv\Scripts\python.exe -m unittest discover -s tests -v` from `backend/` | **49 passed, 0 failures** |
| `npm run lint` from `frontend/` | **Passed** |
| `npm run build` from `frontend/` | **Passed** |

The production frontend build emits a non-blocking advisory because one
minified JavaScript chunk exceeds 500 kB.

## Local service smoke checks

- `http://127.0.0.1:5173/` — frontend returned HTTP 200.
- `http://127.0.0.1:8000/health` — backend returned `{"status":"ok"}`.
- `GET /api/datasets` — returned 9 registered static datasets.
- `GET /api/datasets/lro_spice/metadata` and `/summary` — returned successfully.
- `GET /api/nasa/status` — DONKI reported active during this check; this
  depends on external network/API availability and can change.
- A game mission was created and its state endpoint responded.

## Browser checks

- Landing page loaded.
- Mission Setup displayed its configuration and briefing controls.
- Initializing a mission navigated to Mission Control.
- NASA Data Explorer route rendered.

This report records those executed checks. It does not claim that every
viewport, audio device, or external NASA response will behave identically on
another computer.

## Scientific and operational limitations

- NASA DONKI availability and request limits are controlled by NASA.
- The game remains playable when DONKI is unavailable; real observations are
  not fabricated.
- Historical remote-sensing and spacecraft datasets are not current lunar
  surface readings.
- NASA observations and computed geometry are not direct astronaut dose,
  habitat conditions, medical assessments, or operational navigation.
- The mission store is in memory and resets when the backend restarts.
