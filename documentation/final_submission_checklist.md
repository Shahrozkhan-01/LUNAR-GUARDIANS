# Final Submission Checklist

## Project requirements

- [x] Educational lunar survival simulation for children approximately 7–12.
- [x] React/Vite frontend with FastAPI backend.
- [x] Mission setup, resource management, daily progression, events, decisions,
      scoring, completion, debrief, and relaunch.
- [x] NASA information is separated from simulated game consequences.

## Implemented NASA integration

- [x] NASA DONKI Solar Energetic Particle and Solar Flare services.
- [x] Five read-only processed datasets: Diviner, LOLA, ACE EPAM, STEREO-A
      IMPACT, and JPL Horizons.
- [x] NASA Mission Briefing, NASA Space Weather, NASA Training Events, and
      NASA Data Explorer.
- [x] Dataset metadata, dates, units, provenance, availability, and scientific
      limitations are displayed.
- [x] Offline and unavailable-data fallbacks are covered by the backend tests.
- [x] No spacecraft particle measurements are converted into astronaut dose.

## Setup and operation

- [x] Windows PowerShell setup is documented in [README.md](../README.md).
- [x] Backend environment template exists at
      [backend/.env.example](../backend/.env.example).
- [x] Personal API keys are kept in the ignored local `backend/.env` file.
- [x] The documented launcher starts the backend and frontend and waits for
      readiness.
- [x] Manual backend and frontend startup commands were checked.

## Automated validation

- [x] Backend unit suite: 49 tests passed, 0 failures.
- [x] Frontend lint: passed.
- [x] Frontend production build: passed.
- [x] Documentation link validation: all checked Markdown links resolve.
- [x] Vite bundle-size message reviewed; it is a non-blocking advisory.

## Live application validation

- [x] Landing page loaded.
- [x] Mission Setup loaded with destination, difficulty, crew, duration, and
      NASA briefing controls.
- [x] NASA Mission Briefing preset was selected and displayed.
- [x] A mission was initialized and Mission Control loaded.
- [x] Resource monitoring, daily progression, normal mission activity, NASA
      Space Weather, and NASA Training Events were visible.
- [x] A 10-day mission reached the completion state and displayed the mission
      debrief state.
- [x] Relaunch Day 1 reset the day and removed the previous completion state.
- [x] NASA Data Explorer loaded all five dataset cards and metadata headings.
- [x] Genuine screenshots were captured under
      [documentation/screenshots](screenshots/).

## Screenshot set

- [Landing page](screenshots/01-landing.png)
- [Mission Setup](screenshots/02-mission-setup.png)
- [NASA Mission Briefing](screenshots/03-nasa-mission-briefing.png)
- [Mission Control](screenshots/04-mission-control.png)
- [NASA Training Events](screenshots/05-nasa-training-events.png)
- [NASA Data Explorer](screenshots/06-nasa-data-explorer.png)
- [Final mission debrief](screenshots/07-final-mission-debrief.png)

## Security and project hygiene

- [x] `.gitignore` covers virtual environments, `node_modules`, environment
      files, caches, logs, coverage, and build output.
- [x] No personal NASA API key was found in the source scan.
- [x] `DEMO_KEY` appears only as the documented placeholder/template value.
- [x] Backend and frontend dependency manifests contain the required runtime
      packages.
- [x] No root-level temporary or unexpected files were found.
- [x] Existing raw datasets and documentation were preserved.
- [ ] A final manual review of the submission archive remains recommended
      before upload.

## Demonstration preparation

- [x] Follow [project_demonstration_script.md](project_demonstration_script.md)
      for the 7–10 minute walkthrough.
- [x] Keep the backend and frontend running before the demonstration.
- [x] Use the captured screenshots as a fallback if live NASA requests are
      temporarily unavailable.
- [x] Explain the difference between real NASA observations, computed or
      derived values, and simulated game consequences.

## Known limitations and manual checks

- NASA DONKI availability and rate limits depend on the external NASA service.
- The mission store is in memory; restarting FastAPI invalidates active mission
  IDs.
- The production build reports a non-blocking large-chunk advisory.
- Physical speaker or headphone output cannot be verified through browser
  automation; manually check sound on the presentation computer.
- Before submission, manually confirm that no local `backend/.env` file or
  other secret-bearing file is included in the archive.
- Before submission, manually open the application once on the target machine
  and confirm the required browser, Python, Node.js, and dependency versions.
