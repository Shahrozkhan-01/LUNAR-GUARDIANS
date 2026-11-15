# NASA Data Sources and Validation

Static products are acquired and processed with their original sources preserved.
Each section records the product-specific retrieval and validation method.

## Diviner

- **Official source:** NASA PDS Geosciences Node / UCLA Diviner Science Team.
- **Purpose/type:** Historical LRO Diviner global cumulative south-polar
  brightness-temperature product; processed gridded remote-sensing data.
- **Coverage:** 2009-07-05 through 2015-04-01; 70°S–80°S planetocentric
  latitude band, all longitudes.
- **Units:** Coordinates in degrees, local time in hours, brightness
  temperatures in kelvin.
- **Acquisition/validation:** Public PDS product and labels; deterministic
  streaming conversion; processed readback verified for 1,382,400 rows.
- **Processing:** Fixed-length source conversion to compressed CSV, documented
  missing-value handling, metadata and summary generation.
- **Limitations/use:** Historical environmental context only; not live habitat
  temperature or astronaut temperature. The game uses metadata/summaries.

## LOLA

- **Official source:** NASA PDS Geosciences Node, LRO LOLA.
- **Purpose/type:** Global LDEM_16 elevation grid; processed raster context.
- **Coverage:** Global lunar elevation product, nominally about 1.9 km/pixel.
- **Units:** Preserved integer samples plus processed elevation/reference-radius
  metadata.
- **Acquisition/validation:** Public PDS product and labels; processed NPZ
  and summary validation.
- **Processing:** Raster conversion with coordinate axes, preserved source
  samples, derived elevation summaries, and extrema warnings.
- **Limitations/use:** Broad terrain context, not detailed landing hazard,
  slope, boulder, or local safety data. The game exposes summaries only.

## ACE EPAM

- **Official source:** NASA Goddard SPDF/CDAWeb and ACE EPAM team.
- **Purpose/type:** Historical five-minute Level 2 electron and ion
  observations from ACE near Sun–Earth L1.
- **Coverage:** 2020-01-01 through 2020-01-02 UTC; 277 records with 216x300
  second and 60x360 second intervals.
- **Units:** Source CDF variable units, including differential/integral flux
  and uncertainty conventions.
- **Acquisition/validation:** Bounded CDAWeb AC_H1_EPM request; raw CDF and
  official metadata retained; validation passed with documented warnings.
- **Processing:** Deterministic cdflib conversion to NPZ, separate validity
  masks, original values and metadata preserved.
- **Limitations/use:** ACE is not the lunar surface and measurements are not
  astronaut radiation dose. The game uses bounded historical context only.

## STEREO-A IMPACT HET

- **Official source:** NASA Goddard SPDF, STEREO IMPACT team, and Caltech
  STEREO Science Center.
- **Purpose/type:** Historical STEREO-A IMPACT HET electron/proton intensity
  observations.
- **Coverage:** The processed product is a bounded 2012 daily-average sample.
- **Units:** Source HET electron/proton intensity and uncertainty units,
  preserved in metadata and record fields.
- **Acquisition/validation:** Public SPDF ASCII List source plus source README
  and HET guide; token-preserving processing and readback checks.
- **Processing:** Deterministic gzip CSV conversion preserving source precision
  and separate channels/uncertainties.
- **Limitations/use:** STEREO-A is a spacecraft, not the Moon; values are not
  astronaut dose or lunar surface conditions. The game uses historical
  educational context only.

## JPL Horizons

- **Official source:** NASA/JPL Solar System Dynamics Horizons.
- **Purpose/type:** Earth–Moon range and one-way light-time ephemeris.
- **Coverage:** Saved eight daily epochs from 2026-11-14 through 2026-11-21.
- **Units:** UTC, kilometers, km/s, minutes, and derived seconds.
- **Acquisition/validation:** Bounded Horizons query saved as a normalized CSV
  with processing metadata and summary.
- **Processing:** Normalized source rows; two-way vacuum light time is computed
  as twice the one-way value.
- **Limitations/use:** Values are computed ephemerides, not observations;
  future epochs are predictions. Light time excludes network, equipment,
  routing, and processing delay. The game uses it for communication education.

## NASA OMNI2 hourly

- **Official source:** NASA SPDF OMNI archive and OMNIWeb documentation.
- **Product:** `OMNI2_2020.DAT`, the official 55-field hourly-means product.
- **Coverage:** The preserved annual source contains 2020 data; the processed
  selection is 2020-01-01 00:00 UTC inclusive through 2020-02-01 00:00 UTC
  exclusive, with 744 hourly records.
- **Units:** IMF in nT, proton density in cm^-3, solar-wind speed in km/s,
  temperature in K, pressure in nPa, electric field in mV/m, and the
  product-specific index units documented in `omni2.text`.
- **Acquisition/validation:** The annual ASCII source and official format
  description are preserved. Validation passed with warnings because official
  fill values are present; timestamps are hourly and continuous.
- **Processing:** A bounded CSV was generated without rescaling, interpolation,
  imputation, or removal of source fields. Fill values remain explicit.
- **Limitations/use:** OMNI is a merged, time-shifted near-Earth/L1 product,
  not lunar-surface telemetry or astronaut dose. It supplies historical

## NASA LRO LEND

- **Official source:** [PDS Geosciences LEND archive](https://pds-geosciences.wustl.edu/missions/lro/lend.htm).
- **Products:** `LEND_RDR_DLD_20200101_DAT` and `LEND_RDR_DLX_20200101_DAT`,
  PDS identifiers are recorded in `documentation/lend_dataset.md`.
- **Variables:** UTC, lunar-centric latitude/longitude, collection duration,
  detector/background counts, corrected CSETN sum, and count sigma fields.
- **Validation:** fixed binary record sizes, 85,308 aligned records, timestamp
  continuity/order, duplicate detection, coordinate ranges, and finite values.
  Result: `PASS_WITH_WARNINGS`; source-defined negative corrected values are
  preserved.
- **Limitations/use:** LEND is an orbital lunar neutron detector. Counts are
  not lunar-surface flux or astronaut radiation dose and are not sufficient
  alone to confirm water ice at a specific location. It supplies historical

 It supplies historical
  space-weather preparedness context only and does not change gameplay
  resources, shelter effects, or simulated exposure.

## NASA DONKI

- **Official source:** NASA Open APIs gateway and NASA CCMC DONKI dashboard.
- **Purpose/type:** Recent catalog records for Solar Energetic Particles and
  Solar Flares.
- **Coverage:** Application-configured previous-seven-day request window.
- **Units:** Event-specific metadata and source fields; flare class is not a
  dose unit.
- **Acquisition/validation:** Backend requests NASA, uses documented public
  fallback behavior for eligible failures, validates response shape, preserves
  raw records, normalizes fields, classifies cautiously, and caches in memory.
- **Processing:** Event-specific normalization, missing-field safety, empty
  response handling, status/error reporting, and event deduplication.
- **Limitations/use:** DONKI records are not lunar dosimetry. The game creates
  low-severity educational monitoring/shelter scenarios only when metadata
  supports them; game consequences remain simulated.

## NASA LRO SPICE

- **Official source:** NASA/JPL NAIF PDS archive, dataset
  `LRO-L-SPICE-6-V1.0`.
- **Selection:** `lrorg_2017258_2017349_v01.bsp`, covering
  2017-09-15 through 2017-12-15 UTC; 24 hourly epochs from 2017-09-15 were
  processed.
- **Validation:** SPK, PDS label, leap-second kernel, file sizes, SHA-256
  hashes, label identity, coverage, frame, and source metadata were checked.
- **Processing:** NAIF SPICE `spkpos` computes LRO (NAIF -85) relative to the
  Moon (301) in J2000. Cartesian positions and distance are in kilometers.
- **Limitations/use:** This is computed historical spacecraft geometry, not
  direct telemetry, current navigation, astronaut position, or habitat
  location. No gameplay resource or dose value is derived from it.

## NASA OSD-53 / GLDS-53

- **Official source:** [NASA OSDR OSD-53 study](https://osdr.nasa.gov/bio/repo/data/studies/OSD-53)
  and its public study API.
- **Contents:** 13 public sample annotations and a processed
  `GSE47126_Fold_change_data.txt` summary from the public OSDR archives.
- **Validation:** Public archive members, file sizes, SHA-256 hashes, 13
  sample tables, processed fold-change data, and ISA metadata were checked.
- **Processing:** Sample phase metadata and source fold-change fields were
  normalized without imputation; identifying study-subject labels were omitted
  from processed output.
- **Limitations/use:** Original raw microarray data are reported unavailable.
  This is historical human research, not lunar astronaut data, medical advice,
  health prediction, or a gameplay health model.

## Cross-cutting distinctions

| Label | Meaning |
|---|---|
| `REAL NASA DATA` | Source observation or DONKI record retained from NASA. |
| `COMPUTED EPHEMERIS` | Horizons calculated range/light-time values. |
| `DERIVED VALUE` | A project calculation such as two-way vacuum light time or a saved summary. |
| `SIMULATED TRAINING EVENT` | Fictional educational scenario. |
| `SIMULATED GAME CONSEQUENCE` | Fixed game-only resource, shield, exposure, or Science Point effect. |
