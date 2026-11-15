# Final Testing and Validation Report

## Automated tests

- Backend command:
  `.\venv\Scripts\python.exe -m unittest discover -s tests -v`
  — **49 tests passed, 0 failures**.
- Frontend `npm run lint` — **passed**.
- Frontend `npm run build` — **passed**.
- Build limitation: Vite emits a non-blocking advisory for minified chunks
  larger than 500 kB.

## Browser validation

Verified with the local frontend and backend:

- Landing page navigation to Mission Setup.
- All three NASA briefing presets.
- Mission initialization and Mission Control loading.
- NASA Space Weather panel and NASA Training Events.
- Five-day mission completion with healthy crew and final debrief.
- Final report fields: outcome, final day, resources, Science Points,
  decisions, events, strengths, improvements, and lessons.
- Relaunch Day 1 resets resources/day/history and removes the old debrief.
- Sound control toggles and persists its localStorage preference.

## Responsive validation

| Viewport | Result |
|---|---|
| 1366×768 | No horizontal overflow |
| 1024×768 | No horizontal overflow |
| 390×844 | No horizontal overflow |

Measured Mission Control document widths were 1358, 1021, and 383 pixels
respectively, all within their viewport widths.

## NASA and dataset validation

Backend tests cover DONKI normalization, empty feeds, malformed payloads,
timeouts, HTTP/rate errors, caching, duplicate prevention, dataset listing,
metadata, summaries, pagination, invalid IDs, missing files, empty datasets,
large-grid protection, units, and scientific limitations. The processed
dataset reports document source preservation and validation warnings.

## Known limitations

- DONKI availability and rate limits depend on external services.
- Static dataset files must remain present under `datasets/processed/`.
- The local mission store is in memory; it is not a production account/save
  database.
- NASA data is educational context, not operational flight or medical advice.
- Vite's bundle-size advisory remains non-blocking.
