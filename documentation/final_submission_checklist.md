# Hackathon Submission Checklist

## Project and demo

- [x] Complete nontechnical project report is available in Word, with a
      contents page, text-only cover, editable Markdown source, team roster,
      NASA data and software citations, setup instructions, and limitations.
- [x] Team is credited as **VOID DOMINATORS** for the NASA Space Apps
      Hackathon; members: Muhammad Shahroz Khan, Abdul Rafay, Maira, Urwa Asif
      Qureshi, Fatima Bukhari, and Ayesha Ashraf.
- [x] The team confirms ownership of the original bundled project artwork;
      NASA data and third-party dependencies remain separately attributed.
- [x] Local React/Vite game and FastAPI backend run together with the Windows
      launcher.
- [x] Mission Setup, Mission Control, NASA Data Explorer, mission progression,
      decisions, scoring, and debrief are implemented.
- [x] NASA information is distinguished from computed or derived values and
      simulated game consequences.
- [x] No hosting service is needed to present the local project.
- [x] A presentation walkthrough and screenshot set are available:
      [demo script](project_demonstration_script.md) and
      [screenshots](screenshots/).

## Data and science

- [x] Nine static dataset IDs are implemented in the backend registry; NASA
      DONKI SEP/FLR is an additional live API integration.
- [x] Product sources, record selections, variables, units, temporal coverage,
      processing, validation, and caveats are documented in the
      [complete guide](lunar_guardians_complete_guide.md) and product notes.
- [x] Original available files, labels, metadata, scripts, and validation
      reports are preserved under `datasets/`.
- [x] The local `backend/.env`, Python environment, and frontend dependencies
      are ignored from normal Git tracking.
- [x] Missing NASA responses do not fabricate observations; offline gameplay
      remains available.
- [x] No human gene-expression values are used to make health claims or game
      consequences; no particle or neutron values are converted to astronaut
      dose.

## Automated and local verification

- [x] Backend unittest suite: 49 passed on 2026-11-15.
- [x] `npm run lint`: passed on 2026-11-15.
- [x] `npm run build`: passed on 2026-11-15.
- [x] Local HTTP smoke test: frontend responds, backend `/health` is `ok`,
      nine dataset IDs are listed, and metadata/summary routes respond.
- [x] Browser smoke test: Mission Setup launched into Mission Control and
      NASA Data Explorer rendered.
- [x] Vite's >500 kB chunk notice is a non-blocking advisory, not a build error.

## Confirm before external submission

- [ ] Decide whether to add a root project `LICENSE`; none is present, so the
      team's ownership confirmation does not grant public reuse permission.
- [ ] On the presentation computer, verify browser behavior, keyboard focus,
      sound hardware, screen size, and external DONKI access.
- [ ] If distributing a source archive, exclude `backend/.env`,
      `backend/venv/`, `frontend/node_modules/`, local build output, and caches.
      State that the oversized ignored LOLA processed grid and Diviner original
      are not included in a fresh repository checkout.
- [ ] Cite NASA/PDS product pages when discussing observations. The project is
      independent and not NASA-endorsed.

## Known limitations

- NASA DONKI requires network access and is subject to external availability
  and DEMO_KEY rate limits.
- The mission store is in memory; active missions do not persist across backend
  restarts.
- A fresh checkout does not contain the ignored 106 MB LOLA processed grid;
  its records are unavailable unless the local file is restored.
- The player model is educational and not an operational or medical simulator.
