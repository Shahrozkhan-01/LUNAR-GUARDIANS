# ACE EPAM Level 2 energetic-particle sample

## Dataset acquired

- **Product:** ACE Electron, Proton, and Alpha Monitor (EPAM), `AC_H1_EPM`,
  five-minute Level 2 data.
- **CDAWeb logical source:** `AC_H1S_EPM`.
- **Interval requested:** 2020-01-01 00:00:00 through 2020-01-02 00:00:00 UTC.
- **Records:** 277 time records, including the endpoint timestamp.
- **Format:** NASA Common Data Format (CDF), version 3.9.0.
- **Source:** [NASA SPDF ACE EPAM archive](https://spdf.gsfc.nasa.gov/pub/data/ace/epam/)
  and the [NASA CDAWeb service](https://cdaweb.gsfc.nasa.gov/).
- **Download method:** a one-day, variable-bounded CDF generated from CDAWeb's
  official `AC_H1_EPM` dataset. No annual archive was downloaded.
- **Retrieved:** 2026-11-14.

The primary CDF is
[`ac_h1s_epm_20200101000000_20200102000000_allvars.cdf`](../datasets/raw/space_weather/ace_epam/ac_h1s_epm_20200101000000_20200102000000_allvars.cdf).
It contains all 88 data and uncertainty variables documented by CDAWeb for
this dataset. Its byte size is 209,959. The raw folder also retains the earlier
40,932-byte, three-variable CDF request unchanged; that preliminary subset
included `P1`, which is entirely fill-valued for this interval, so the
all-variable CDF is the selected dataset for validation.

Supporting originals saved beside the CDF:

- [`cdaweb_full_request_metadata.xml`](../datasets/raw/space_weather/ace_epam/cdaweb_full_request_metadata.xml) —
  CDAWeb response metadata, including the requested interval, generated file
  size, transient download URL and response warnings.
- [`cdaweb_ac_h1_epm_variables.xml`](../datasets/raw/space_weather/ace_epam/cdaweb_ac_h1_epm_variables.xml) —
  official CDAWeb descriptions for the 88 variable names and their channel
  descriptions.
- [`epam_l2desc.html`](../datasets/raw/space_weather/ace_epam/epam_l2desc.html) —
  ACE Science Center EPAM Level 2 instrument documentation.
- [`cdaweb_request_metadata.xml`](../datasets/raw/space_weather/ace_epam/cdaweb_request_metadata.xml) —
  metadata for the retained preliminary subset.

The generated CDF link in the CDAWeb response is temporary. The stable
provenance is the public CDAWeb dataset and bounded data-service request, not
the transient link. The CDF's source-parent metadata identifies
`ac_h1_epm_20200101_v05` and `ac_h1_epm_20200102_v05`.

## Instrument and measurements

EPAM is an instrument aboard the **Advanced Composition Explorer (ACE)**. It
measures energetic electrons and ions. The ACE Science Center describes the
Level 2 data as spin-averaged flux/intensity products at five-minute, hourly,
and daily cadences. This sample is the five-minute product. CDAWeb's CDF
attributes and variable descriptions are the authority for each channel's
units, fill value, valid-range metadata and energy band.

The CDF includes 88 measurement and uncertainty variables, plus `Epoch`.
Important channel groups include:

| Variables | Measurement | Energy information in the source metadata | Units |
|---|---|---|---|
| `P1`–`P8` | LEMS30 ion flux | 0.047–4.75 MeV, channel-specific; for example `P7` is 1.06–1.91 MeV and `P8` is 1.91–4.75 MeV | `1/(cm**2-s-sr-MeV)` |
| `DE1`–`DE4` | Deflected-electron flux | 0.038–0.315 MeV, channel-specific | `1/(cm**2-s-sr-MeV)` |
| `W3`–`W8` | CA60 helium, CNO and Fe-group ion channels | Channel-specific energy per nucleon; see each CDF `CATDESC` | `1/(cm**2-s-sr-MeV/nuc.)` |
| `Z2`, `Z2A`, `Z3`, `Z4` | WARTD60 integral ion flux above channel-specific thresholds | Thresholds are given in each CDF `CATDESC` | `1/(cm**2-s-sr)` |
| `unc_*` | Fractional statistical uncertainty for corresponding flux variables | The ACE guide defines these as fractional counting uncertainties | `[fraction]` |
| `Epoch` | Beginning time for each measurement interval | UTC timestamps | CDF epoch; CDF attribute reports `ms` |

Other `E*`, `FP*`, and primed/unprimed channels remain in the original CDF.
Their detailed species, channel passbands, units and notes must be read from
their own CDF attributes and the accompanying official documentation; this
summary does not infer a channel meaning from its name alone.

## Missing values and validation findings

The validator uses the actual CDF `FILLVAL` and non-finite-value checks. It
does not replace or remove measurements. The ACE guide describes `-999.9` as a
generic missing marker for its documented files, while this CDAWeb-generated
CDF encodes missing values with the per-variable CDF `FILLVAL` (approximately
`-1e31`); the CDF metadata is used for this file.

The official EPAM guide says `P1`–`P6` contain fill data after day 302 of 2003
because of a detector noise increase. Their all-fill values in this 2020
sample are therefore documented behavior, not evidence that measurements
should be fabricated. Other all-fill channels in this interval are listed in
the machine-readable validation report without an assumed cause.

Validation findings:

- CDF opens with `cdflib`; all 88 documented variable names are present and
  all have 277 one-dimensional records aligned with `Epoch`.
- The requested and decoded coverage is 2020-01-01 00:00:00 to
  2020-01-02 00:00:00 UTC.
- The time series is not uniformly spaced: 216 gaps are 300 seconds and 60
  gaps are 360 seconds. This is reported as a warning; the original timestamps
  are preserved.
- CDAWeb's response XML contains 89 “dimension mismatch” reformation warnings.
  The resulting CDF is readable and the validator confirms record alignment;
  the source warnings are nevertheless retained and reported.
- Some values in `Z2`, `Z2A`, `Z3`, and `Z4` fall below their CDF `VALIDMIN`.
  The validator records these comparisons as warnings, not as a reason to
  rewrite the source or silently discard data.
- **Overall status: `PASSED_WITH_WARNINGS`.** The report is
  [`ace_epam_validation.json`](../datasets/validation_reports/ace_epam_validation.json).

Run the validator from the repository root:

```powershell
.\backend\venv\Scripts\python.exe datasets\scripts\validate_ace_epam.py
```

`cdflib` is pinned in `backend/requirements.txt` for repeatable CDF reading.

## Scientific limitations and gameplay boundary

ACE operates near the **Sun–Earth L1 Lagrange point**, about 1.4 million
kilometres from Earth, not at the Moon or on the lunar surface. It samples
particles at its spacecraft location and its detectors have particular
species, geometry, energy bands, cadence, and data gaps. Particle transport
between ACE and the Moon and the lunar/outpost shielding environment are not
measured by this dataset.

These measurements are **not** direct lunar astronaut radiation-dose or
outpost-exposure measurements. Do not convert the flux channels to crew dose,
or represent ACE values as measurements at the lunar habitat. The dataset is
cataloged for educational context only; it is not connected to gameplay and
does not alter simulated resources or consequences.

## References

- [NASA SPDF ACE EPAM archive](https://spdf.gsfc.nasa.gov/pub/data/ace/epam/)
- [NASA CDAWeb](https://cdaweb.gsfc.nasa.gov/)
- [CDAWeb AC_H1_EPM dataset](https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/AC_H1_EPM/)
- [ACE EPAM Level 2 documentation](https://izw1.caltech.edu/ACE/ASC/level2/epam_l2desc.html)
- [NASA ACE mission overview](https://science.nasa.gov/mission/ace/)
