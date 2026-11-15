# NASA Mission Briefing

## Overview

Mission Setup includes an optional, read-only NASA Mission Briefing. Players
can review processed NASA context and select one of three educational presets
before initializing a mission. The preset is retained in browser session
setup preferences; it is not sent to the game simulation API. It does not
change resources, event schedules, event consequences, or the simulation
engine. Existing DONKI behavior is unchanged.

The briefing uses the existing FastAPI dataset service. It does not query NASA
directly, access arbitrary file paths, or require the static data service for
mission launch.

## Briefing presets and dataset mapping

| Preset | Objective | Datasets | Planning challenge |
|---|---|---|---|
| **South Polar Exploration** | Plan an outpost expedition using historical surface-environment context and broad regional terrain data. | Diviner; LOLA | Identify what additional local measurements are needed before selecting a precise landing or habitat site. |
| **Space Weather Preparedness** | Explore energetic-particle instrument measurements and consider what further information is needed for crew safety assessment. | ACE EPAM; STEREO-A IMPACT | Identify the location, timing, shielding, and dosimetry information required before assessing crew exposure. |
| **Communication and Navigation** | Distinguish Earth–Moon range, one-way light time, and an idealized two-way vacuum calculation. | JPL Horizons | Explain why ideal light travel time is not a complete operational communication delay. |

Presets select educational focus only. Space Weather Preparedness is
radiation-protection education, not a dose estimate. Historical ACE EPAM and
STEREO-A samples are displayed with their own dates; they are not represented
as a simultaneous space-weather event.

## Dataset information displayed

- **Diviner:** saved brightness-temperature summary values, channel units,
  valid/missing counts, and product coverage. Brightness temperature is
  historical remote-sensing information, not live habitat or air temperature.
- **LOLA:** saved global relative-height summary values, units, sample count,
  and coverage. The global product is broad terrain context, not detailed
  landing-hazard information.
- **ACE EPAM:** historical period, channel/uncertainty counts, and one valid
  sample from a bounded record page when present. Its timestamp and channel
  units come from API data and metadata. ACE is a spacecraft near Sun–Earth
  L1, not the lunar surface; its particle observations are not astronaut dose.
- **STEREO-A IMPACT:** historical coverage, electron/proton channel counts,
  and a sample channel value with its energy interval and corresponding
  one-sigma uncertainty when available. Measurements were collected at
  STEREO-A, not at the Moon, and are not astronaut dose.
- **JPL Horizons:** computed mean Earth–Moon range, one-way down-leg light
  time, and the separately labeled derived mean two-way vacuum light time.
  Epochs and sample values are shown from the processed API response.
  Horizons values are computed ephemerides; forward calculations in the
  archived request are predictions. The derived two-way value is not a
  separate Horizons measurement. Network, equipment, routing, and processing
  delays are not included.

Units, coverage, summary values, and sample measurements come from the backend
dataset catalog, metadata, summary, or record responses. Explanatory text and
the planning challenges are educational framing, not measurements.

## API usage

The Mission Setup component is
[`frontend/src/components/NasaMissionBriefing.jsx`](../frontend/src/components/NasaMissionBriefing.jsx).
It uses the existing functions in `frontend/src/services/gameApi.js`:

- `GET /api/datasets` for catalog names, coverage, units, availability, and
  scientific limitations.
- `GET /api/datasets/{dataset_id}/metadata` for processing metadata and channel
  definitions.
- `GET /api/datasets/{dataset_id}/summary` for saved statistics.
- `GET /api/datasets/{dataset_id}/records?page=1&page_size=20` for a bounded
  sample from ACE EPAM, STEREO-A, and Horizons.

The briefing does not request records for Diviner or LOLA. It uses no new
backend endpoints and does not change the dataset service or DONKI routes.

## Fallback behavior

- If the catalog request fails, a clear service-unavailable message and retry
  button are shown. The briefing presets remain selectable and mission setup
  remains usable.
- If an individual dataset's metadata, summary, records, or processed files are
  unavailable, that dataset is identified as unavailable or its missing
  information is stated. Other dataset cards can still display successfully.
- Empty records and missing measurements are not replaced with sample values,
  interpolation, or fabricated observations.
- Mission launch does not wait on NASA dataset calls and remains available
  during backend outages. The normal game-start request and simulation are
  unchanged.

## Scientific and gameplay boundaries

- Diviner brightness temperature is not live habitat temperature.
- LOLA global elevation is not detailed landing hazard data.
- ACE and STEREO-A measurements are spacecraft observations, not lunar surface
  measurements or astronaut radiation dose. No dose conversion is performed.
- ACE and STEREO-A archive periods are not combined into one real-world event.
- Horizons forward epochs are computed predictions, not observations.
- Horizons one-way light time is not end-to-end communication delay; derived
  two-way vacuum light time excludes network and processing delays.
- NASA archive observations, computed ephemerides, derived values, and
  simulated game consequences use distinct labels.
- No NASA data modifies oxygen, water, power, food, radiation protection, or
  other game resources in this phase.

## Verification

- Backend unittest suite: **49 tests passed** using `backend/venv`.
- Frontend lint: **passed**.
- Frontend production build: **passed**. Vite reports the existing main-bundle
  size advisory; the NASA Data Explorer remains separately bundled.
- Browser/API checks using the current local dataset responses confirmed
  the preset mappings, source date coverage, displayed units, scientific
  limitations, ACE/STEREO sample values, and Horizons range/light-time labels.
- With the dataset catalog request intentionally failed, the briefing displayed
  an unavailable message while presets remained selectable. Selecting a
  briefing and starting the mission succeeded; the captured game-start payload
  retained the existing fields and contained no NASA preset or measurements.
- The launch navigated to Mission Control. The browser's pre-test mission
  session storage was restored afterward.
- Screenshots were captured for the selected preset and the dataset cards.
