# JPL Horizons Earth–Moon ephemeris sample

## Source and acquisition

This bounded sample was retrieved from the official
[NASA/JPL Horizons API](https://ssd-api.jpl.nasa.gov/doc/horizons.html).
The official [Horizons system manual](https://ssd.jpl.nasa.gov/horizons/manual.html)
is also preserved with the raw acquisition files.

The request used the Moon (target `301`) as seen from the Earth geocenter
(`CENTER=500@399`). The Horizons manual identifies Earth station code `500` as
the geocenter. The API response identifies the center as Earth (`399`) and its
ephemeris source as DE441.

The requested interval is 2026-11-14 through 2026-11-21 at daily UTC epochs:
eight samples over seven elapsed days. The original JSON response,
request parameters, retrieval timestamp and official documentation are in
[`datasets/raw/communication_navigation/jpl_horizons/`](../datasets/raw/communication_navigation/jpl_horizons/).

## Exact request

Endpoint:

```text
https://ssd.jpl.nasa.gov/api/horizons.api
```

Parameters (also retained in `request_metadata.json`):

| Parameter | Value | Purpose |
|---|---|---|
| `format` | `json` | JSON wrapper around the Horizons result |
| `COMMAND` | `301` | Moon target NAIF ID |
| `OBJ_DATA` | `YES` | Include target information |
| `MAKE_EPHEM` | `YES` | Generate an ephemeris |
| `EPHEM_TYPE` | `OBSERVER` | Observer table |
| `CENTER` | `500@399` | Earth geocenter |
| `START_TIME` / `STOP_TIME` | `2026-11-14` / `2026-11-21` | Seven elapsed days, inclusive |
| `STEP_SIZE` | `1d` | Daily samples |
| `TIME_TYPE` | `UT` | Universal Time |
| `TIME_ZONE` | `+00:00` | UTC offset |
| `QUANTITIES` | `20,21` | Target range/range-rate and one-way down-leg light time |
| `RANGE_UNITS` | `KM` | Range in kilometres |
| `TIME_DIGITS` | `SECONDS` | Timestamp precision in output |

## Variables and units

The Horizons manual defines quantity 20 as the target's apparent range
(`delta`) and range rate (`deldot`) relative to the observer. With
`RANGE_UNITS=KM`, the range is in kilometres; range rate is in kilometres per
second. A positive range rate means the target is moving away; a negative
value means it is moving toward the observer.

Quantity 21 (`1-way_down_LT`) is the target's one-way down-leg light time, in
minutes. It is the light travel time from the target to the observer for the
ephemeris solution, not a round-trip time.

The response contains eight ordered, daily UTC epochs from 2026-11-14 00:00:00
through 2026-11-21 00:00:00. Example values:

| UTC epoch | `delta` (km) | `deldot` (km/s) | `1-way_down_LT` (min) |
|---|---:|---:|---:|
| 2026-11-14 00:00:00 | 405,615.89143 | -0.0031111 | 0.02254982 |
| 2026-11-21 00:00:00 | 377,764.35156 | -0.0715223 | 0.02100144 |

These are JPL Horizons computed ephemeris values, not direct measurements
collected at the Moon. The response was retrieved on 2026-11-14 UTC; the
2026-11-15 through 2026-11-21 epochs are therefore forward ephemeris
calculations, not observations made on those dates.

## Validation

Run the validator from the project root:

```powershell
.\backend\venv\Scripts\python.exe .\datasets\scripts\validate_jpl_horizons.py
```

The validator checks the retained JSON and request metadata, HTTP/API success,
target and observer identities, DE441 source label, time interval, daily UTC
ordering, expected quantity labels, documented units, missing/non-finite
values, and the integrity hash of the response file. Its machine-readable
result is [`datasets/validation_reports/jpl_horizons_validation.json`](../datasets/validation_reports/jpl_horizons_validation.json).

## Limitations and game relevance

The sample is a model-derived geometric ephemeris, not an observation of an
operational communication link. One-way light time can illustrate signal
travel time for Earth–Moon distances. It is not the total communication delay
for every mission situation: relay geometry, spacecraft and ground systems,
network routing, protocol handling and operations add other delays. This
dataset has not been connected to gameplay, and no simulated game values
should be represented as NASA measurements.
