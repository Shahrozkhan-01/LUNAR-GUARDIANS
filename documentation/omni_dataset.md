# NASA OMNI2 hourly solar-wind and IMF dataset

## Product and source

This integration uses the official NASA SPDF OMNI2 annual ASCII product:

- Product: `OMNI2_2020.DAT`
- Source: [NASA SPDF OMNI archive](https://spdf.gsfc.nasa.gov/pub/data/omni/low_res_omni/omni2_2020.dat)
- Format documentation: [OMNIWeb data documentation](https://omniweb.gsfc.nasa.gov/html/ow_data.html)
- Retrieval date: 2026-11-15
- Original file: `datasets/raw/space_weather/omni/omni2_2020.dat`

The annual source and official `omni2.text` format description are preserved
unchanged. The processed product selects 2020-01-01 00:00 UTC inclusive through
2020-02-01 00:00 UTC exclusive: 744 hourly records.

## Variables and units

The 55 official fields are retained, including IMF magnitude and components,
proton density, proton temperature, solar-wind speed and flow, pressure,
electric field, plasma/Alfven/magnetosonic Mach numbers, Kp, Dst, AE, ap,
f10.7, PC(N), AL, AU, and the documented energetic-proton flux fields.
Units remain those in the official format description: nT, cm^-3, km/s, K,
nPa, mV/m, and index-specific or dimensionless units.

OMNI uses numeric fill values (for example `999.9`, `9999`, and `9999999.`)
for missing fields. They remain in the source and processed CSV; validation
reports their counts rather than silently dropping or imputing them.

## Validation and processing

Run:

```powershell
python datasets/scripts/validate_omni_dataset.py
python datasets/scripts/process_omni_dataset.py
```

The validation report is
`datasets/validation_reports/omni_hourly_validation.json`. The result is
`PASS_WITH_WARNINGS` because official fill values occur in the bounded records.
The processed CSV, metadata, and summary are in
`datasets/processed/space_weather/omni/`.

Processing is lossless with respect to selected source values: it parses the
official fields, constructs UTC timestamps from year/day/hour, and performs no
unit conversion, rescaling, interpolation, or scientific imputation.

## Application use and limitations

The backend exposes metadata, summary information, and paginated records through
the normal dataset API under `omni_hourly`. NASA Data Explorer labels these
records `REAL NASA DATA`, shows source units, and displays official fill values
as missing.

OMNI is a merged and time-shifted near-Earth/L1 product. It is not a lunar
surface measurement, current telemetry, or a direct astronaut radiation-dose
measurement. The game does not convert any OMNI value into dose or use it to
change shelter effects, resources, or simulated exposure. It is historical
context for the Space Weather Preparedness lesson only.
