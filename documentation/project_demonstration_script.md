# 7–10 Minute Project Demonstration

## 1. Introduction — 45 seconds

Introduce LUNAR GUARDIANS as a lunar survival learning game for ages 7–12.
Explain the central rule: **NASA observations are real, while resource
balances and game consequences are simulations.**

## 2. Landing page — 45 seconds

Show the lunar art, star field, decorative celestial bodies, and launch button.
Explain that the background bodies are illustrative, not scaled or live
astronomical positions. Sound is optional and off by default.

## 3. Mission Setup — 90 seconds

Choose Lunar Outpost, Explorer, a two-person crew, and a five-day mission.
Briefly show the other available difficulty, crew-size, and duration choices.

## 4. NASA briefing — 60 seconds

Show the three presets:

1. South Polar Exploration — historical Diviner and broad LOLA context.
2. Space Weather Preparedness — historical ACE/STEREO context.
3. Communication and Navigation — Horizons ephemerides and derived light-time
   explanation.

Explain that observations from different dates and spacecraft are not one
simultaneous lunar environment.

## 5. Mission Control — 90 seconds

Initialize the mission. Show resource meters, crew indicators, system status,
power allocation, and event/activity panels. Emphasize that the game meters
are simulated units.

## 6. Space weather and decisions — 90 seconds

Show NASA Space Weather status, retrieval time, event dates and NASA source
links. If records are available, identify them as `REAL NASA DATA`; if not,
explain that no fake observations are substituted. Show a training-event
decision and its `SIMULATED GAME CONSEQUENCE`.

## 7. NASA Data Explorer — 75 seconds

Open the Explorer and point out that it lists nine static dataset IDs plus
separate DONKI API information. Open a product's metadata, source/coverage,
units, validation state, and scientific limitations. Note that full Diviner
and LOLA grids are not returned as ordinary table rows.

## 8. Daily mission — 60 seconds

Resolve a normal event if present, advance a day, and show updated resources
and mission progress. Explain that historical dataset values do not directly
change game-resource formulas.

## 9. Completion and debrief — 90 seconds

For a complete demonstration, use the backend's deterministic test scenario or
advance a prepared short mission to its end. Show outcome, final resources,
Science Points, decisions, events, lessons, and improvement suggestions.
Relaunch Day 1 and show that the new mission starts cleanly.

## Presenter notes

- Start both local services before the presentation using
  `.\start-lunar-guardians.ps1`.
- Use `documentation/screenshots/` if NASA or network access is temporarily
  unavailable.
- Never describe particle flux, neutron counts, a flare class, or spacecraft
  geometry as a lunar astronaut dose or habitat measurement.
- See the [complete guide](lunar_guardians_complete_guide.md) for all nine
  dataset citations and project limitations.
