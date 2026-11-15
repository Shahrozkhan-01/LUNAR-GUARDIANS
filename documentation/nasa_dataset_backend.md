# NASA static dataset backend

## Scope and separation

The backend exposes a read-only API for five NASA datasets that were already
processed and validated in this project. The service reads only files under
`datasets/processed/` and catalog metadata under
`datasets/metadata/dataset_catalog.csv`. It does not download NASA data, alter
raw products, call DONKI, or connect any static dataset to gameplay or the
frontend.

DONKI continues to use its existing `nasa_service.py` and `/api/nasa/*` routes.
Static files have a separate service and route group, require no network
connection, and use no NASA API key.

## Service structure and files

- `backend/app/services/dataset_service.py` contains a fixed allowlist of
  dataset IDs and relative product filenames, reads catalog and processed
  sidecar metadata, reads saved summaries, and serves bounded time-series
  pages.
- `backend/app/routes/datasets.py` defines the read-only `/api/datasets`
  endpoints, validates page parameters, and returns safe HTTP errors.
- `backend/app/main.py` registers the dataset router alongside the existing
  game and DONKI routers.
- `backend/tests/test_dataset_api.py` covers listing, metadata, summaries,
  pagination, unavailable and empty data, invalid IDs, and scientific labels.

The allowlisted IDs and processed locations are:

| Dataset ID | Processed product | Processing metadata | Summary |
|---|---|---|---|
| `diviner` | `datasets/processed/lunar_environment/diviner/global_cumul_avg_cyl_80s70s_002.csv.gz` | `diviner_processing_metadata.json` | `diviner_summary_statistics.json` |
| `lola` | `datasets/processed/lunar_environment/lola/ldem_16_processed.npz` | `lola_processing_metadata.json` | `lola_summary_statistics.json` |
| `ace_epam` | `datasets/processed/space_weather/ace_epam/ace_epam_20200101_processed.npz` | `ace_epam_processing_metadata.json` | `ace_epam_summary_statistics.json` |
| `stereo_impact` | `datasets/processed/space_weather/stereo_impact/stereo_impact_het_201203_daily.csv.gz` | `stereo_impact_processing_metadata.json` | `stereo_impact_summary_statistics.json` |
| `jpl_horizons` | `datasets/processed/communication_navigation/jpl_horizons/jpl_horizons_moon_earth_geocenter_20261114_20261121.csv` | `jpl_horizons_processing_metadata.json` | `jpl_horizons_summary_statistics.json` |

These are fixed server-side paths. Requests accept only a dataset ID, page, and
page size; callers cannot supply a filesystem path or filename.

## API endpoints

### `GET /api/datasets`

Returns all six supported IDs and their catalog fields: dataset name,
category, scientific purpose, important variables, source organization and
URL, coverage, geographic/spacecraft coverage, units, validation status, data
type, scientific limitations, record-access support, and file availability.
Availability is checked against the processed product and its sidecars. The
returned file locations are project-relative and fixed by the allowlist.

Example:

```json
{
  "dataset_count": 6,
  "datasets": [
    {
      "dataset_id": "jpl_horizons",
      "dataset_name": "JPL Horizons Earth-Moon and lunar ephemerides",
      "data_type": "computed_ephemeris",
      "coverage": "2026-11-14T00:00:00Z through 2026-11-21T00:00:00Z; eight daily epochs",
      "units": "UTC; km; km/s; minutes; derived seconds",
      "validation_status": "Raw validation PASSED_WITH_WARNINGS; ...",
      "availability": {
        "status": "available",
        "processed_data": true,
        "processing_metadata": true,
        "summary": true
      }
    }
  ]
}
```

### `GET /api/datasets/{dataset_id}/metadata`

Returns the catalog information, data type, scientific limitations, availability,
record-access support, project-relative fixed product filenames, and selected processing metadata.
Processing metadata is curated from the existing sidecar files; absolute paths
and unrelated internal processing details are not returned. If the processed
product is absent, catalog metadata remains available and marks the product
unavailable; `processing_metadata` is `null` if that sidecar is also absent.

For variable-based data, metadata identifies relevant field names, units,
shapes, and fill-value/validity rules when supplied by the processing sidecar.
For Horizons, it preserves that the ephemeris is computed and the two-way
vacuum light-time field is derived, not a direct Horizons measurement.

### `GET /api/datasets/{dataset_id}/summary`

Returns the saved processing summary without reopening or loading the original
large data product. Diviner and LOLA are initially limited to this summary and
their metadata: their multi-million-row table and 16,588,800-sample raster are
never placed in an API response.

### `GET /api/datasets/{dataset_id}/records?page=1&page_size=50`

Returns paginated records only for `ace_epam`, `stereo_impact`, and
`jpl_horizons`. `page` is one-based; the default page size is 50 and the
maximum is 100. Responses include record count and page navigation fields.
Out-of-range pages return an empty `records` list with the actual totals.
Empty datasets return HTTP 200 with zero records and `total_pages: 0`.

- **ACE EPAM:** records contain the original CDF epoch value, UTC timestamp,
  and original measurement/uncertainty values with a separate `valid` flag from
  the processed CDF fill-value mask. Fill values are not interpreted as
  measurements. Non-finite values are represented as `null` in JSON; their
  validity remains false. Per-variable units and descriptions are available
  from the metadata endpoint. No particle values are converted into dose.
- **STEREO-A IMPACT HET:** records are read from the compressed CSV using a
  streaming gzip reader. CSV values are returned as their saved text tokens to
  preserve their processed precision. Electron/proton channels and their
  uncertainty columns remain separate.
- **JPL Horizons:** rows are read from the saved normalized CSV. Numeric fields
  remain strings to preserve original decimal tokens. Each response identifies
  a computed ephemeris; the two-way vacuum light-time value is derived.

Record-level access for `diviner` and `lola` returns HTTP 409 with a message to
use metadata and summaries. This avoids returning large grids or tables as
ordinary API responses.

## Scientific interpretation constraints

| Dataset | Required distinction |
|---|---|
| Diviner | Historical south-polar brightness temperature is not live habitat, astronaut, or forecast temperature. |
| LOLA | Global LDEM_16 elevation is broad terrain context at about 1.9 km/pixel, not detailed landing-site hazard information. The observed-versus-label extrema warning remains in the summary and metadata. |
| ACE EPAM | Measurements are from ACE near Sun-Earth L1, not the lunar surface. They are not astronaut radiation dose and must not be converted into dose. |
| STEREO IMPACT | Measurements are from STEREO-A, not the lunar surface. They are not astronaut radiation dose and must not be converted into dose. |
| JPL Horizons | Values are computed ephemerides; future epochs are calculations rather than observations. One-way light time is not total communication delay. Two-way vacuum light time is a mathematical derivation, not another direct measurement. |

The API is educational/contextual only. It does not write any dataset value into
mission resources, crew state, simulated radiation exposure, event decisions,
or other game mechanics.

## Errors and unavailable files

| Status | Meaning |
|---|---|
| `404` | Unknown dataset ID. |
| `409` | Record access is intentionally disabled for a large grid dataset. |
| `422` | Invalid pagination values (page below 1 or page size outside 1–100). |
| `503` | Catalog, summary, or requested processed file is missing, malformed, or unreadable. The response includes a safe message and does not expose an absolute path. |

The listing and metadata endpoints report file availability explicitly. A
missing data file does not create substitute records. Missing summaries return
503. A successfully read saved summary may still be returned when the primary
data file is absent, but its `availability` indicates that the processed data
are unavailable. No endpoint contacts NASA, so the static API remains usable
offline when its local products are present. The game remains independent of
these endpoints.

## Tests and verification

`backend/tests/test_dataset_api.py` covers:

- The nine active static dataset IDs and route registration.
- Catalog source, units, validation status, processing metadata, and scientific
  limitations.
- Saved summaries for all active products.
- Paginated CSV/CDF-derived records and ACE validity-mask behavior.
- Maximum page-size enforcement, invalid IDs, and disabled Diviner/LOLA records.
- Missing files and an empty CSV dataset.

**Latest local verification (2026-11-15):** the complete backend suite passed
49 tests. Frontend lint and production build passed; Vite emitted its
non-blocking advisory that a minified JavaScript chunk exceeds 500 kB. Live
local HTTP smoke checks confirmed the health route, nine-dataset listing,
metadata and summary routes, mission creation/state retrieval, and the browser
Data Explorer route.

The React NASA Data Explorer uses these endpoints. Full Diviner/LOLA grids are
not sent as paginated rows; their metadata and saved summaries are exposed
separately.
