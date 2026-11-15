# STEREO-A IMPACT HET daily energetic-particle sample

## Dataset selected

- **Dataset:** STEREO-A (Ahead), IMPACT High Energy Telescope (HET), daily
  electron and proton intensities.
- **SPDF archive product:** `AeH12Mar.1d`, in the SPDF `l2/impact_ascii/het/1day/`
  directory.
- **Coverage:** 2012-03-01 00:00 UTC through 2012-04-01 00:00 UTC, represented
  by 31 consecutive daily intervals.
- **Format:** self-describing ASCII List file; the header describes the
  averaging interval, timestamp layout, energy channels, and data-field
  bounds.
- **Data file size:** 10,532 bytes. The local SHA-256 is
  `917D10B7C89146A3F2F5962FD6AA41632EC142314E8A9BDD1229B82D53FC739B`.
- **Retrieved:** 2026-11-14.

Both STEREO-Ahead and STEREO-Behind have official SPDF IMPACT HET daily product
directories. The March 2012 daily-average products were available for each
spacecraft; only the Ahead file was selected and downloaded for this task.

## Official source files

- [Original `AeH12Mar.1d` data file](../datasets/raw/space_weather/stereo_impact/AeH12Mar.1d)
  — NASA/SPDF Ahead HET daily product (10,532 bytes).
- [SPDF Ahead HET README](../datasets/raw/space_weather/stereo_impact/00readme_ascii_sta_impact_het)
  — identifies the HET cadence products and points to the instrument
  documentation (1,444 bytes).
- [HET instrument documentation](../datasets/raw/space_weather/stereo_impact/HET_public.html)
  — official STEREO HET data guide saved from Caltech (8,526 bytes).

The direct data URL is
[`AeH12Mar.1d`](https://spdf.gsfc.nasa.gov/pub/data/stereo/ahead/l2/impact_ascii/het/1day/AeH12Mar.1d).
The byte count was checked against the official HTTP `Content-Length` of 10,532
before download. The SPDF directory's human-readable listing rounds its size
to 10 KB. A source checksum for this data file was not listed; the validator
records a SHA-256 for the preserved local file.

## Variables, channel energies, and units

The data file contains 14 channel intensities, each followed by a one-sigma
uncertainty. The channel header and HET guide identify:

| Particle | Energy range (MeV) |
|---|---|
| Electrons | 0.7–1.4 |
| Electrons | 1.4–2.8 |
| Electrons | 2.8–4.0 |
| Protons | 13.6–15.1 |
| Protons | 14.9–17.1 |
| Protons | 17.0–19.3 |
| Protons | 20.8–23.8 |
| Protons | 23.8–26.4 |
| Protons | 26.3–29.7 |
| Protons | 29.5–33.4 |
| Protons | 33.4–35.8 |
| Protons | 35.5–40.5 |
| Protons | 40.0–60.0 |
| Protons | 60.0–100.0 |

Intensities are reported in
`particles/(cm^2-sr-sec-MeV)`. Each following uncertainty field is a one-sigma
uncertainty for that intensity, in the same units. The rows contain the daily
interval start and end times followed by channel/uncertainty pairs. The
preserved ASCII file is the authoritative source for the field ordering.

## Missing values and validation

The HET guide says data gaps are **not filled** in these files and does not
specify a numeric missing-value sentinel for this ASCII product. Accordingly,
the validator does not infer a sentinel or replace values. It checks row
structure, daily timestamp coverage, finite numeric values, and the per-channel
lower/upper bounds declared in each `F2` header line. Those are source-file
header bounds, not a separate assessment of detector calibration, saturation,
or physical validity.

Validation result: **PASS**.

- The file decoded as ASCII and matched the documented self-describing list
  format.
- All 31 daily intervals from March 1 to April 1 were present, ordered, and
  contiguous.
- The header's 14 electron/proton channel definitions matched the official HET
  guide; every row had the expected 28 intensity/uncertainty fields.
- No non-finite numeric values, missing daily intervals, or values outside the
  source-file header bounds were found.
- The file byte count matched SPDF's pre-download `Content-Length`; the
  SHA-256 is stored in the validation report. No independent source checksum
  was published for this data file.

The detailed report is
[`stereo_impact_validation.json`](../datasets/validation_reports/stereo_impact_validation.json).
Run the validator from the project root:

```powershell
.\backend\venv\Scripts\python.exe datasets\scripts\validate_stereo_impact.py
```

## Limitations and possible educational use

STEREO-A measurements are made by the spacecraft at its own heliocentric
location, not at the Moon or at a lunar outpost. These intensities are not
direct lunar particle measurements, astronaut exposures, or radiation doses.
Do not convert them directly to crew dose or describe them as lunar conditions.

The official HET documentation warns that electron-channel calibration is not
currently correct; it specifically cautions against using those data directly
to estimate electron/proton intensity ratios or derive electron spectra. HET
data have no background correction, which can matter during quiet conditions.
Gaps are not filled. These caveats apply even though this selected file passed
structural and metadata validation.

This month of daily observations can support an educational comparison of
spacecraft particle-intensity channels, energy ranges, and how observations
change over time. Such a lesson must be labeled as **real STEREO-A data at the
spacecraft**. Any shelter choice, astronaut exposure, or resource effect in
the game must remain a separately labeled **simulated game consequence**.
This dataset is cataloged only: it is not connected to gameplay and does not
modify the game engine.

## References

- [NASA/SPDF STEREO archive](https://spdf.gsfc.nasa.gov/pub/data/stereo/)
- [STEREO-Ahead IMPACT HET Level 2 daily products](https://spdf.gsfc.nasa.gov/pub/data/stereo/ahead/l2/impact_ascii/het/1day/)
- [STEREO-Behind IMPACT HET Level 2 daily products](https://spdf.gsfc.nasa.gov/pub/data/stereo/behind/l2/impact_ascii/het/1day/)
- [SPDF HET product README](https://spdf.gsfc.nasa.gov/pub/data/stereo/ahead/l2/impact_ascii/het/00readme_ascii_sta_impact_het)
- [STEREO HET data and documentation](https://izw1.caltech.edu/STEREO/Level1/HET_public.html)
