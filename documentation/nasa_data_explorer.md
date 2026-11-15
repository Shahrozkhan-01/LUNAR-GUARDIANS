# NASA Data Explorer

## Overview

The NASA Data Explorer is a responsive, read-only frontend page at `/nasa-data`.
It presents processed project datasets using the existing FastAPI dataset API.
It does not query NASA directly, access local dataset files from the browser,
or connect any dataset to game state. The Mission Control simulation and its
resource/event calculations remain unchanged.

The page shows the eight backend dataset IDs:

- `diviner` — historical lunar south-polar brightness-temperature context.
- `lola` — broad-scale lunar elevation context.
- `ace_epam` — historical measurements from ACE EPAM near Sun-Earth L1.
- `stereo_impact` — historical STEREO-A IMPACT HET measurements.
- `jpl_horizons` — a saved, computed Earth–Moon ephemeris.
- `omni_hourly` — bounded historical OMNI2 near-Earth solar-wind and IMF observations.
- `lend` — one-day historical LRO LEND orbital neutron observations.
- `lro_spice` — computed historical LRO spacecraft positions from NAIF SPICE.
- `osd53` — historical human astronaut gene-expression research.

## API integration

`frontend/src/services/gameApi.js` provides:

- `fetchDatasetsApi()` → `GET /api/datasets`
- `fetchDatasetMetadataApi(datasetId)` → `GET /api/datasets/{dataset_id}/metadata`
- `fetchDatasetSummaryApi(datasetId)` → `GET /api/datasets/{dataset_id}/summary`
- `fetchDatasetRecordsApi(datasetId, page, pageSize)` →
  `GET /api/datasets/{dataset_id}/records?page=…&page_size=…`

The React page uses backend catalog values for names, source organization,
category, coverage, important variables, units, validation status, availability,
purpose, and limitations. It uses backend processing metadata to describe
fields/channels and uses actual summary/record responses for plots and tables.
Dataset IDs select the backend allowlist; the browser never submits a file path.

Catalog, detail, and record requests have independent loading and error states.
The catalog has a retry action; metadata/summary and record failures have their
own retries. A backend outage does not affect the rest of the application or
Mission Control.

## Page and navigation components

- `frontend/src/pages/NasaDataExplorer.jsx` implements the dataset cards,
  selected-dataset detail view, scientific labels, charts, records tables, and
  pagination.
- `frontend/src/pages/NasaDataExplorer.css` defines the responsive dark lunar
  dashboard layout, mobile card stacking, chart, and horizontally scrollable
  record table.
- `frontend/src/App.jsx` registers `/nasa-data`.
- `frontend/src/components/Navbar.jsx` adds a Data Explorer navigation item
  for desktop and mobile navigation.
- `frontend/src/components/MissionHeader.jsx` provides a link from Mission
  Control without changing simulation behavior.

Each dataset card displays the source-backed catalog name, category, source,
coverage, measurement fields, units, validation status, availability, and a
detail action. The detail panel includes scientific purpose, geographic or
spacecraft coverage, processing metadata, official source links where
provided, and the dataset-specific scientific limitations.

## Visualizations and record display

- **Diviner:** a summary chart and channel statistics table of available
  brightness temperatures in kelvin, including valid/missing counts and
  minimum, median, mean, and maximum. It uses saved summary statistics; no
  table/record endpoint is requested.
- **LOLA:** a summary chart and statistics table of global and latitude-band
  height, including sample counts and minimum, median, mean, and maximum. These
  values are identified as derived elevation. No raster rows are requested or
  loaded.
- **ACE EPAM:** a selectable, historical particle channel chart and a paginated
  UTC table. The chart plots only valid channel samples from the current record
  page; fill/invalid points stay blank and are not interpolated. The table
  indicates when a sample is missing/fill.
- **STEREO-A IMPACT:** a selectable electron/proton intensity channel chart
  with its corresponding one-sigma uncertainty series and a paginated
  interval table. Channel energy ranges and source units are shown from API
  metadata.
- **JPL Horizons:** computed Earth–Moon range by epoch and a paginated table
  containing range, range rate, one-way down-leg light time, and derived
  two-way vacuum light time. Decimal text tokens are preserved in the table;
  the two-way value is labeled `DERIVED VALUE`.
- **OMNI2:** historical solar-wind speed chart and paginated records showing
  proton density, IMF magnitude, units, and official fill-value status.
- **LEND:** historical corrected neutron-count chart and paginated records
  showing UTC, lunar-centric coordinates, CSETN sum, and one-sigma count
  uncertainty. Counts are not converted to flux, dose, or water-ice claims.
- **LRO SPICE:** historical LRO distance-from-Moon chart and paginated J2000
  position records. These are computed geometry, not telemetry.
- **OSD-53:** sample-phase count chart and paginated public sample metadata.
  Processed gene-expression summaries are historical research context only.

The three record-capable datasets use the backend's one-based pagination with
20 records per frontend page (the API maximum is 100). Charts for those
datasets reflect the loaded page and say so; they do not imply values between
records. The frontend displays an empty response as empty, not as substitute
data. Diviner and LOLA only consume their backend metadata and summaries.

## Scientific labels and limitations

The page uses `REAL NASA DATA` for archive observations, `COMPUTED EPHEMERIS`
for Horizons, and `DERIVED VALUE` for derived summaries/quantities. It includes
the `SIMULATED GAME CONSEQUENCE` legend as a reminder that game mechanics are
not part of this explorer; it does not display simulated consequences.

The detail panel states that:

- ACE EPAM observations are from ACE near Sun-Earth L1; they are not lunar
  surface measurements or astronaut radiation dose.
- STEREO-A IMPACT observations are from STEREO-A; they are not lunar surface
  measurements or astronaut radiation dose.
- Particle measurements are never converted into astronaut dose.
- Diviner brightness temperature is historical remote-sensing context, not
  habitat temperature.
- LOLA LDEM_16 is broad terrain context at about 1.9 km/pixel, not detailed
  landing hazard information.
- Horizons values are computed; future epochs are predictions, and one-way
  light time is not total communication delay.
- OMNI is a merged, time-shifted near-Earth/L1 product, not a lunar-surface
  measurement or astronaut radiation dose.
- LEND is an orbital lunar neutron observation; its counts are not surface
  flux or astronaut radiation dose, and do not alone confirm water ice.
- Missing channel values remain missing; the charts do not interpolate.
- These products are archive data, not live mission telemetry.

## Verification

- Backend unittest suite: **38 tests passed**, including dataset API, DONKI,
  and simulation regression tests.
- Frontend lint: **passed** with no lint warnings.
- Frontend production build: **passed**. Vite reports a bundle-size advisory
  for the minified JavaScript chunk exceeding 500 kB.
- Local browser/API verification: all eight dataset cards loaded; Diviner and
  LOLA summary-statistics tables and charts rendered without record requests;
  ACE EPAM, STEREO-A, and
  Horizons charts and record tables loaded; ACE page navigation advanced from
  page 1 to page 2; 390-pixel viewport showed five cards and no horizontal page
  overflow. Mission Control remained accessible and showed its expected
  no-active-mission state.
- The frontend is read-only and no static dataset is integrated into gameplay.
