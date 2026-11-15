# STEREO-A IMPACT HET daily data processing

## Dataset and provenance

This processing uses the existing NASA/SPDF file
[`AeH12Mar.1d`](../datasets/raw/space_weather/stereo_impact/AeH12Mar.1d), the
STEREO-Ahead IMPACT High Energy Telescope (HET) Level 2 daily-average ASCII
product for March 2012. Its source file is 10,532 bytes and its preserved
SHA-256 is
`917D10B7C89146A3F2F5962FD6AA41632EC142314E8A9BDD1229B82D53FC739B`.
No data were downloaded for this processing task.

Official documentation retained with the source includes the
[SPDF HET README](../datasets/raw/space_weather/stereo_impact/00readme_ascii_sta_impact_het)
and the
[HET instrument and file-format guide](../datasets/raw/space_weather/stereo_impact/HET_public.html).
The original dataset is
[hosted by NASA/SPDF](https://spdf.gsfc.nasa.gov/pub/data/stereo/ahead/l2/impact_ascii/het/1day/AeH12Mar.1d);
the official [HET documentation page](https://izw1.caltech.edu/STEREO/Level1/HET_public.html)
describes the channels, units, caveats, and ASCII format.

## Format and processing

The source is an ASCII List file. Its header contains the file's start and end
dates, a `#0 Rate` verse declaration, a `T2` declaration indicating that both
interval start and end timestamps are present, and one `F2` definition per
channel. The `#End` line terminates the header. Each data row contains 37
whitespace-delimited fields:

1. Verse number (`0` in every record).
2. Four date/time fields for the UTC interval start.
3. Four date/time fields for the UTC interval end.
4. Fourteen ordered intensity / one-sigma uncertainty pairs, in the same order
   as the 14 `F2` header definitions.

The processor reads each channel's species, energy limits, and declared value
bounds from its actual `F2` header line, and verifies the 14 definitions
against the existing validation report (which checks them against the official
guide). Dates are parsed as UTC and emitted in ISO-8601 form. Every original
numeric token is retained verbatim in a deterministic gzip-compressed CSV;
channel values are not combined, interpolated, or rounded.

From the repository root, reproduce the outputs with:

```powershell
.\backend\venv\Scripts\python.exe datasets\scripts\process_stereo_impact.py
```

The processor reopens the compressed CSV and verifies the row count, fields,
timestamps, and source numeric tokens. It also checks that the original raw
data and documentation file hashes are unchanged.

## Channels and units

There are **3 electron** and **11 proton** channels. Each intensity has a
corresponding one-sigma uncertainty. Both use the source's intensity unit:
**particles/(cm^2-sr-sec-MeV)**. Energy intervals are in MeV.

| Particle | Energy range (MeV) | Output columns |
|---|---:|---|
| Electron | 0.7–1.4 | `intensity_electron_0.7_1.4_MeV`, `uncertainty_electron_0.7_1.4_MeV` |
| Electron | 1.4–2.8 | `intensity_electron_1.4_2.8_MeV`, `uncertainty_electron_1.4_2.8_MeV` |
| Electron | 2.8–4.0 | `intensity_electron_2.8_4_MeV`, `uncertainty_electron_2.8_4_MeV` |
| Proton | 13.6–15.1 | `intensity_proton_13.6_15.1_MeV`, `uncertainty_proton_13.6_15.1_MeV` |
| Proton | 14.9–17.1 | `intensity_proton_14.9_17.1_MeV`, `uncertainty_proton_14.9_17.1_MeV` |
| Proton | 17.0–19.3 | `intensity_proton_17_19.3_MeV`, `uncertainty_proton_17_19.3_MeV` |
| Proton | 20.8–23.8 | `intensity_proton_20.8_23.8_MeV`, `uncertainty_proton_20.8_23.8_MeV` |
| Proton | 23.8–26.4 | `intensity_proton_23.8_26.4_MeV`, `uncertainty_proton_23.8_26.4_MeV` |
| Proton | 26.3–29.7 | `intensity_proton_26.3_29.7_MeV`, `uncertainty_proton_26.3_29.7_MeV` |
| Proton | 29.5–33.4 | `intensity_proton_29.5_33.4_MeV`, `uncertainty_proton_29.5_33.4_MeV` |
| Proton | 33.4–35.8 | `intensity_proton_33.4_35.8_MeV`, `uncertainty_proton_33.4_35.8_MeV` |
| Proton | 35.5–40.5 | `intensity_proton_35.5_40.5_MeV`, `uncertainty_proton_35.5_40.5_MeV` |
| Proton | 40.0–60.0 | `intensity_proton_40_60_MeV`, `uncertainty_proton_40_60_MeV` |
| Proton | 60.0–100.0 | `intensity_proton_60_100_MeV`, `uncertainty_proton_60_100_MeV` |

The machine-readable
[processing metadata](../datasets/processed/space_weather/stereo_impact/stereo_impact_processing_metadata.json)
retains the channel definitions, source header lines, column positions, units,
and per-channel `F2` bounds.

## Time coverage, missing values, and flags

The header covers **2012-03-01 00:00 UTC through 2012-04-01 00:00 UTC** as 31
daily intervals. All **31** start/end intervals are present, ordered,
contiguous, and exactly 24 hours long.

The official HET guide says data gaps are not filled; it does not specify a
numeric missing-value sentinel for this ASCII product. Therefore, no sentinel
is assumed and no numeric value is removed or replaced. All 868 measurement
and uncertainty values (31 records × 14 channels × 2 fields) are finite in
this sample: **31 valid values and zero missing/nonfinite values per
intensity and uncertainty series**. The first field is the verse number, which
is `0`; the file defines no separate per-record quality-flag field.

The `F2` lines declare value bounds of 0 to 500,000 for each channel. No
intensity or uncertainty in this sample falls outside those header bounds.
These are checks against the source header, not independent physical quality
criteria.

## Summary statistics

The table gives per-channel statistics over all 31 daily records. Intensity
and one-sigma uncertainty ranges and means are shown in the original units.
The JSON summary additionally contains medians, valid/missing/nonfinite counts,
and comparisons to each channel's header bounds.

| Particle | Energy (MeV) | Intensity min–max | Intensity mean | Intensity median | 1-sigma min–max | 1-sigma mean |
|---|---:|---:|---:|---:|---:|---:|
| Electron | 0.7–1.4 | 0.0286–17.2 | 2.63284 | 0.319 | 0.000904–0.053 | 0.00915519 |
| Electron | 1.4–2.8 | 0.0128–6.36 | 1.03525 | 0.114 | 0.000426–0.0228 | 0.00407394 |
| Electron | 2.8–4.0 | 0.0139–1.13 | 0.221023 | 0.0316 | 0.000472–0.0104 | 0.00211816 |
| Proton | 13.6–15.1 | 0.000213–1.56 | 0.368955 | 0.0746 | 5.18e-05–0.0108 | 0.00238121 |
| Proton | 14.9–17.1 | 9e-05–1.22 | 0.282752 | 0.0623 | 2.85e-05–0.00811 | 0.00176010 |
| Proton | 17.0–19.3 | 0.000107–0.935 | 0.203455 | 0.0397 | 2.97e-05–0.0068 | 0.00142833 |
| Proton | 20.8–23.8 | 3.77e-05–0.557 | 0.115778 | 0.014 | 1.54e-05–0.00458 | 0.000934729 |
| Proton | 23.8–26.4 | 7.11e-06–0.427 | 0.0841554 | 0.008 | 7.11e-06–0.00427 | 0.000842307 |
| Proton | 26.3–29.7 | 2.27e-05–0.328 | 0.0644583 | 0.0047 | 1.14e-05–0.00335 | 0.000655129 |
| Proton | 29.5–33.4 | 1.97e-05–0.246 | 0.0493221 | 0.00351 | 9.84e-06–0.0027 | 0.000526201 |
| Proton | 33.4–35.8 | 1.62e-05–0.188 | 0.036914 | 0.00231 | 1.14e-05–0.00303 | 0.000578039 |
| Proton | 35.5–40.5 | 3.49e-05–0.138 | 0.026477 | 0.00184 | 1.16e-05–0.00174 | 0.000336197 |
| Proton | 40.0–60.0 | 0.000133–0.0795 | 0.0145724 | 0.000831 | 1.13e-05–0.000627 | 0.000121710 |
| Proton | 60.0–100.0 | 0.000332–0.0232 | 0.00431994 | 0.000569 | 1.26e-05–0.000212 | 4.75355e-05 |

No values are flagged outside the file's declared `F2` bounds, and the source
contains no non-finite values. Intensities from different energy ranges are
kept separate; no cross-channel sum or derived particle dose is calculated.

## Validation and outputs

The original validator was rerun without changing its criteria. It reports
**PASS**, with zero errors and zero warnings. Its original checks include raw
file size and source-document checks, the 14 official species/energy
definitions, 31 contiguous daily intervals, 37-field row structure, finite
values, and values within the `F2` header bounds.

Independent processing checks confirmed all 31 records and all original
numeric text tokens in the reopened compressed CSV, channel/header mappings,
UTC timestamps and ordering, per-channel statistics, and output
readability. Repeated processing produced byte-identical outputs. The raw
source SHA-256 remained unchanged.

Outputs are under
[`datasets/processed/space_weather/stereo_impact/`](../datasets/processed/space_weather/stereo_impact/):

- `stereo_impact_het_201203_daily.csv.gz` — processed time series; 2,691 bytes.
- `stereo_impact_processing_metadata.json` — source, channel, units, and processing metadata; 13,462 bytes.
- `stereo_impact_summary_statistics.json` — statistics and per-channel validity/range checks; 21,506 bytes.

The existing raw-data validation report is
[`stereo_impact_validation.json`](../datasets/validation_reports/stereo_impact_validation.json).

## Scientific limitations

These are historical measurements collected by **STEREO-A at the spacecraft's
location**, not at the Moon. They are not direct lunar-surface measurements or
astronaut radiation-dose measurements. Do not convert particle intensities
into astronaut dose or present this March 2012 sample as current space weather.

The official HET documentation warns that electron-channel calibration is not
currently correct; these data should not be used directly to estimate
electron/proton intensity ratios or derive electron spectra. The data also
have no background corrections, which may matter during quiet conditions.
Gaps are not filled. These limitations apply even though the structural
validation passed. The dataset is cataloged for educational comparison of
spacecraft observations and remains separate from gameplay and any simulated
mission consequences.
