# ACE EPAM CDF processing

## Dataset and provenance

This processed sample uses the already acquired, one-day all-variable CDAWeb
CDF product `AC_H1_EPM` (`AC_H1S_EPM`) for 2020-01-01 through 2020-01-02.
The source CDF and its original request metadata, official variable XML, and
EPAM instrument guide remain unchanged under
[`datasets/raw/space_weather/ace_epam/`](../datasets/raw/space_weather/ace_epam/).
The selected input is
[`ac_h1s_epm_20200101000000_20200102000000_allvars.cdf`](../datasets/raw/space_weather/ace_epam/ac_h1s_epm_20200101000000_20200102000000_allvars.cdf),
a NASA CDF 3.9.0 file generated from CDAWeb. No new data was downloaded.

The acquisition interval yielded **277 records** from 2020-01-01 00:00:00 UTC
through 2020-01-02 00:00:00 UTC, inclusive. CDF `Epoch` is a one-dimensional
`CDF_EPOCH` variable stored as float64 with a `ms` units attribute. The archive
preserves each original Epoch value as well as a decoded ISO-8601 UTC
timestamp string.

Sources: [NASA SPDF ACE EPAM archive](https://spdf.gsfc.nasa.gov/pub/data/ace/epam/),
[NASA CDAWeb AC_H1_EPM dataset](https://cdaweb.gsfc.nasa.gov/WS/cdasr/1/dataviews/sp_phys/datasets/AC_H1_EPM/),
the retained official CDAWeb variable descriptions, and the
[ACE Science Center EPAM Level 2 guide](https://izw1.caltech.edu/ACE/ASC/level2/epam_l2desc.html).

## Variables, channels, and units

The CDF contains the `Epoch` support variable and **88 numeric time-series
variables**: 44 measurement channels and 44 associated uncertainty variables.
Every data variable is a one-dimensional 277-record float32 array in this
sample. The official variable XML and each variable's own CDF attributes
(`CATDESC`, `UNITS`, `FILLVAL`, `VALIDMIN`, `VALIDMAX`, and dependency
metadata) are captured in
[`ace_epam_processing_metadata.json`](../datasets/processed/space_weather/ace_epam/ace_epam_processing_metadata.json).
Names are preserved exactly; channels are not merged.

| Channel family | Channels and source descriptions | CDF units |
|---|---|---|
| LEMS30 ion flux | `P1`–`P8`; energy passbands are channel-specific and appear in each official description | `1/(cm**2-s-sr-MeV)` |
| LEMS120 ion flux | `P1p`–`P8p`; channel-specific ion energy passbands | `1/(cm**2-s-sr-MeV)` |
| Deflected-electron flux | `DE1`–`DE4`; 0.038–0.315 MeV by channel | `1/(cm**2-s-sr-MeV)` |
| CA60 composition channels | `W3`–`W8`; helium, CNO, and Fe-group species with channel-specific energy per nucleon | `1/(cm**2-s-sr-MeV/nuc.)` |
| LEFS60 / LEFS150 channels | `E1`–`E4`, `E1p`–`E4p`, `FP5`–`FP7`, `FP5p`–`FP7p`; species and passbands are in the official per-channel description | `1/(cm**2-s-sr-MeV)` |
| WARTD integral ion flux | `Z2`, `Z2A`, `Z3`, `Z4`; each has a different documented species/energy threshold | `1/(cm**2-s-sr)` |
| Fractional uncertainty | `unc_` counterpart for each of the 44 measurement channels | `[fraction]` |

The full official descriptions in the metadata specify the energy bounds and
species for every individual channel; the family table does not replace those
per-variable definitions.

## Processing and missing values

Run from the repository root:

```powershell
.\backend\venv\Scripts\python.exe .\datasets\scripts\process_ace_epam.py
```

The script uses the already installed `cdflib` library, verifies that the CDF
variable names agree with the official CDAWeb XML, and checks every array's
record alignment. For each variable, valid samples are finite values that are
not equal to that variable's CDF `FILLVAL`. The sample's fill value is
approximately `-1e31`, as recorded in the variable-specific CDF metadata.
Nonfinite values are tracked separately.

Both original value arrays and boolean validity masks are retained in the
processed archive. Fill values are not overwritten or removed, and variables
that have only fill values remain present with an all-false mask. No gaps are
interpolated and no measurements are estimated. The generic `-999.9` missing
marker mentioned by the EPAM guide applies to the documented source products;
for this CDAWeb-created CDF the processor follows its actual per-variable CDF
`FILLVAL` attributes.

The output is a deterministic compressed NumPy NPZ, opened with
`allow_pickle=False`. It includes original `Epoch` values, UTC strings, all 88
originally named numeric arrays, one validity mask per data array, and
serialized processing/variable metadata.

## Coverage and summary

The 276 intervals comprise **216 intervals of 300 seconds** and **60 intervals
of 360 seconds**. The irregular cadence is retained; timestamps are neither
regularized nor interpolated.

Across 88 arrays of 277 values each, there are **24,376 numeric values**:
**16,945 valid**, **7,431 CDF fill values**, and **zero nonfinite values**.
There are **21 variables containing only fill values**:

`P1`–`P6`, `unc_P1`–`unc_P6`, `unc_W5`, `unc_W7`, `unc_W8`, `E1`–`E3`,
`unc_E1`–`unc_E3`.

The EPAM guide explains that P1–P6 contain fill data after day 302 of 2003
because detector noise made those channels unreliable. The other all-fill
channels are retained without assigning an unverified cause. A valid zero is
distinct from a fill value and is retained as a measurement.

Among measurement channels, 35 have 276 valid records and 9 have no valid
records. The uncertainty channels have variable coverage: 25 have 276 valid
records, the 12 all-fill uncertainty arrays have none, and the remaining
7 have 1–257 valid records. Exact valid, fill, and nonfinite counts and
minimum, maximum, mean, and median for every variable are in
[`ace_epam_summary_statistics.json`](../datasets/processed/space_weather/ace_epam/ace_epam_summary_statistics.json).

Examples of measurement statistics (valid samples only):

| Variable | Valid records | Minimum | Maximum | Mean | Median | Units |
|---|---:|---:|---:|---:|---:|---|
| `P7` | 276/277 | 0.029718 | 0.396060 | 0.198970 | 0.190150 | `1/(cm**2-s-sr-MeV)` |
| `DE1` | 276/277 | 953.3300 | 1573.8000 | 1234.2613 | 1208.3500 | `1/(cm**2-s-sr-MeV)` |
| `W3` | 276/277 | 0 | 0.075912 | 0.008145 | 0 | `1/(cm**2-s-sr-MeV/nuc.)` |
| `Z2` | 276/277 | 0 | 0.137530 | 0.034855 | 0.031142 | `1/(cm**2-s-sr)` |

Four channels (`Z2`, `Z2A`, `Z3`, `Z4`) have respectively 19, 269, 247, and
273 valid values below their CDF `VALIDMIN` metadata. This comparison is
reported but does not cause samples to be discarded or changed; these metadata
bounds should not be assumed to be universal physical rejection criteria.

## Validation and preserved warnings

The processing pass reopened the NPZ with `allow_pickle=False` and verified all
members, original arrays, timestamps, and fill masks. Source CDF hashes were
checked before and after processing. The existing raw validator was rerun and
remains **`PASSED_WITH_WARNINGS`**, with zero errors.

All four existing validator warnings are preserved verbatim in the processing
metadata and summary:

1. The time intervals are not uniformly five minutes (216 at 300 seconds and
   60 at 360 seconds); original timestamps are retained.
2. The CDAWeb response metadata contains 89 dimension-reformation warnings,
   even though the CDF is readable and the variable records align.
3. The 21 variables listed above contain only CDF fill/nonfinite values in
   this interval; in this file there are no nonfinite values.
4. `Z2`, `Z2A`, `Z3`, and `Z4` have values below their CDF `VALIDMIN`; values
   were not changed.

Output files are in
[`datasets/processed/space_weather/ace_epam/`](../datasets/processed/space_weather/ace_epam/):

- `ace_epam_20200101_processed.npz`
- `ace_epam_processing_metadata.json`
- `ace_epam_summary_statistics.json`

## Scientific limitations

ACE is near Sun–Earth L1, not at the Moon. The data are measured at the
spacecraft and reflect the instrument's detector response, species and energy
passbands, data gaps, and quality characteristics. They do **not** directly
measure lunar-surface particle exposure or astronaut radiation dose and must
not be converted to crew dose or represented as real-time lunar conditions.
This processed dataset is for analysis and educational context only; it is not
connected to gameplay.
