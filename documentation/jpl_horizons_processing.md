# JPL Horizons Earth–Moon ephemeris processing

## Dataset and provenance

The processed data come from the already downloaded
[NASA/JPL Horizons API response](../datasets/raw/communication_navigation/jpl_horizons/horizons_response.json).
The original response, request metadata, official API documentation, and
Horizons manual are retained unchanged in
[`datasets/raw/communication_navigation/jpl_horizons/`](../datasets/raw/communication_navigation/jpl_horizons/).
No new API request was made for processing.

The query specifies the **Moon (NAIF ID 301)** as viewed from the **Earth
geocenter**, observer center `500@399`. The response identifies the ephemeris
source as **DE441**. It contains eight daily UTC epochs from 2026-11-14
00:00:00 through 2026-11-21 00:00:00. The saved response was retrieved on
2026-11-14 at 17:42:47 UTC, so seven of the eight epochs are forward
ephemeris calculations, not observations.

Sources: [JPL Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
and [Horizons manual](https://ssd.jpl.nasa.gov/horizons/manual.html), both
preserved alongside the original response.

## Quantities and units

| Output column | Horizons label | Meaning | Units |
|---|---|---|---|
| `epoch_utc` | `Date__(UT)__HR:MN:SS` | Ephemeris epoch, represented in UTC | UTC |
| `earth_moon_range_km` | `delta` | Target apparent range relative to the observer; Horizons documents this as light-time aberrated | km |
| `range_rate_km_s` | `deldot` | Range rate; positive means receding, negative means approaching | km/s |
| `one_way_down_leg_light_time_minutes` | `1-way_down_LT` | One-way down-leg light time from target center to observer | minutes |
| `two_way_vacuum_light_time_seconds_derived` | Derived | Twice the Horizons one-way value, converted to seconds | seconds |

Horizons quantity 20 provides `delta` and `deldot`; the retained request sets
`RANGE_UNITS=KM`, and the official manual defines range-rate units as km/s.
Quantity 21 provides `1-way_down_LT` in minutes. The processing script copies
the original decimal text tokens for these three values directly from the
response into CSV; it does not round-trip them through binary floating-point.
The UTC timestamp format follows the API's requested second precision.

## Processing and derived communication time

Run from the repository root:

```powershell
.\backend\venv\Scripts\python.exe datasets\scripts\process_jpl_horizons.py
```

The script verifies the saved API response and request metadata against the
existing validator report, checks target/observer/DE441 identifiers and
official units, parses all table rows, and validates the eight ordered daily
UTC epochs. It writes a normalized CSV and JSON metadata and summary. The CSV
is reopened and checked against the exact original decimal strings.

For each epoch, the requested derived value is:

```text
two_way_vacuum_light_time_seconds
    = 2 × one_way_down_leg_light_time_minutes × 60 seconds/minute
```

The computation uses decimal arithmetic. This is a **mathematical,
idealized two-way vacuum light-time derivation**, not a separate Horizons
measurement. It doubles the one-way value for a simple symmetric path
illustration; it does not model changing geometry during a round trip or any
equipment, relay, network, routing, protocol, operations, or processing delay.

## Summary statistics

Statistics cover the eight computed daily epochs:

| Quantity | Minimum | Maximum | Mean | Median |
|---|---:|---:|---:|---:|
| Earth–Moon apparent range (km) | 377,764.35156 | 405,615.89143 | 394,951.38676375 | 397,388.936995 |
| Range rate (km/s) | -0.0715223 | -0.0031111 | -0.0447979625 | -0.0501036 |
| One-way down-leg light time (min) | 0.02100144 | 0.02254982 | 0.021956935 | 0.02209245 |
| Derived two-way vacuum light time (s) | 2.52017280 | 2.70597840 | 2.63483220 | 2.65109400 |

All eight values are present and finite. The negative range rates indicate
that the target is approaching the geocenter over these listed epochs. Exact
per-epoch values and machine-readable statistics are in the processed files.

## Validation and outputs

The existing validator was rerun without changing its criteria. Its result is
**`PASSED_WITH_WARNINGS`**, with zero errors and one warning:

> 7 requested epoch(s) are after retrieval time; these are forward ephemeris calculations, not observations.

Independent checks verified the eight UTC epochs, all three original
quantities against the raw JSON response, units and header labels, each
two-way decimal calculation, and the reopened CSV. The original response
SHA-256 remains
`C90CAAC120D90F227373BF8927ACA1F55DD667E66800F42F006A8703B215C958`.
Repeated processing produced byte-identical CSV and JSON outputs.

Outputs are under
[`datasets/processed/communication_navigation/jpl_horizons/`](../datasets/processed/communication_navigation/jpl_horizons/):

- `jpl_horizons_moon_earth_geocenter_20261114_20261121.csv` — normalized time series; 692 bytes.
- `jpl_horizons_processing_metadata.json` — request, provenance, source hashes, and field semantics; 4,320 bytes.
- `jpl_horizons_summary_statistics.json` — range, range-rate, one-way and derived light-time statistics; 2,693 bytes.

The raw validation report remains at
[`jpl_horizons_validation.json`](../datasets/validation_reports/jpl_horizons_validation.json).

## Scientific and communications limitations

Horizons provides **computed ephemerides**, not direct measurements at the
Moon or a real-time communication test. Future epochs in this sample are
predictions/calculations. The one-way down-leg light time is only geometric
signal travel time for the specified target and observer solution; it is not
the complete communication delay for every mission configuration.

Real links also involve mission geometry, spacecraft or relay equipment,
network routing, signal processing, protocol handling, operations, and other
system delays. None of these are included in the Horizons values or the
derived two-way vacuum calculation. This dataset remains separate from
gameplay and any simulated mission consequences.
