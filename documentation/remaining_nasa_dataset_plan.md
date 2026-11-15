# Remaining NASA Dataset Integration Plan

## Scope and guardrails

This is the Phase A/B research plan for dataset categories that are not yet
integrated. **No datasets were downloaded or modified during this phase.**
Existing Diviner, LOLA, ACE EPAM, STEREO IMPACT HET, JPL Horizons, and DONKI
integrations were not duplicated.

Every acquisition must preserve the original source files, labels, units,
timestamps, missing-value conventions, attribution, and license/access terms.
Human-health research must remain population-level educational context and must
not produce individual medical predictions. Mars observations must remain
labelled as Mars observations. Particle, LET, or flux measurements must not be
silently converted into astronaut dose or lunar surface exposure.

## Existing integrations excluded from this plan

| Existing integration | Existing role |
|---|---|
| LRO Diviner | Historical south-polar brightness-temperature context |
| LRO LOLA LDEM_16 | Broad lunar elevation context |
| ACE EPAM | Historical spacecraft energetic-particle observations |
| STEREO-A IMPACT HET | Historical spacecraft energetic-particle observations |
| JPL Horizons | Computed Earth–Moon ephemeris and light time |
| NASA DONKI FLR/SEP | Live catalog metadata for solar flares and SEP events |

## Candidate dataset matrix

The sizes below are acquisition estimates, not measured local files. They must
be confirmed from the selected archive product and date range before a
download. `Unknown` means the official landing page does not expose a stable
bounded size for the candidate.

| Dataset / product | Folder | Official NASA source and download link | Product identifier | Variables and units | Coverage | Format / estimated size | Intended game application | Validation method | Status |
|---|---|---|---|---|---|---|---|---|---|
| OSDR human spaceflight physiology study | `astronaut_health/osdr_osd53` | [NASA OSDR OSD-53](https://osdr.nasa.gov/bio/repo/data/studies/OSD-53) | OSD-53; GeneLab GLDS-53; DOI 10.25966/qsf7-cr81 | Human whole-blood gene-expression measurements; array/platform-specific normalized signal or dimensionless expression values; study metadata include collection timing and tissue | Pre/post-flight astronaut samples; exact study timepoints in OSDR metadata | OSDR study package; exact file size and downloadable-file list must be confirmed; likely small-to-moderate for a selected processed subset | Population-level lesson about biological adaptation and recovery; no individual health prediction | Verify anonymization, consent/access terms, platform, normalization, batch effects, missing values, sample counts, and study metadata | **APPROVED**, subject to file-level terms review |
| NASA Life Sciences Data Archive / NLSP physiological records | `astronaut_health/nlsp_selected` | [NASA Life Sciences Data Archive](https://www.nasa.gov/hrp/nlsp/) and [NLSP search](https://nlsp.nasa.gov/) | Study-specific; no single common product ID | Study-dependent cardiovascular, pulmonary, exercise, vestibular, or biomedical variables; units and access vary by record | Study-specific flight and analog intervals | Study-specific; size and public-file availability unknown | Explain that human-research evidence is population-level and protocol-specific | Confirm open/de-identified status, restrictions, human-subjects conditions, units, calibration, and citation requirements | **NEEDS INVESTIGATION** |
| InSight APSS TWINS calibrated/derived data | `mars_environment/insight_twins` | [PDS TWINS bundle](https://pds.nasa.gov/ds-view/pds/viewBundle.jsp?identifier=urn%3Anasa%3Apds%3Ainsight_twins&version=3.2); [online archive](https://atmos.nmsu.edu/PDS/data/PDS4/InSight/twins_bundle/) | `urn:nasa:pds:insight_twins::3.2`; calibrated collection `urn:nasa:pds:insight_twins:data_calibrated` | Air/surface temperature and wind observations; exact field units from PDS4 labels; timestamps, channel, quality/status metadata | Mars surface at InSight, 2018-11-30 through 2022-08-27 | PDS4 products; selected calibrated/derived interval likely MB-to-GB; exact size unknown | Mars weather comparison, thermal cycles, and wind/dust educational scenario | Parse PDS4 labels; verify units, UTC timestamps, calibration level, quality flags, missing values, local solar time, and coverage | **APPROVED** using calibrated/derived products |
| MSL REMS meteorology | `mars_environment/msl_rems` | [PDS REMS dataset profile](https://pds.nasa.gov/ds-view/pds/viewDataset.jsp?dsid=MSL-M-REMS-5-MODRDR-V1.0) | `MSL-M-REMS-5-MODRDR-V1.0`; DOI 10.17189/ghbc-qr41 | Air/ground temperature, pressure, wind and related meteorological channels in label-defined physical units | Mars surface at Curiosity; mission archive coverage | PDS products; selected MODRDR interval likely MB-to-GB; exact size unknown | Mars environmental operations and dust/wind lesson | Prefer corrected/model-derived records; validate calibration version, outages, rover geometry, timestamps, fill values, and dust-season effects | **APPROVED** |
| LRO SPICE selected kernels | `communication_navigation/lro_spice` | [NAIF data](https://naif.jpl.nasa.gov/naif/data.html); [NAIF PDS archive](https://naif.jpl.nasa.gov/pub/naif/pds/data/) | `LRO-L-SPICE-6-V1.0` | SPK position/velocity in km and km/s; CK attitude; FK/IK frames; SCLK/LSK time conversion; PCK constants | LRO mission intervals vary by kernel; select a bounded interval | DAF binary/text kernels; selected subset MB-to-hundreds of MB; full archive may be GB-scale | Geometry, line-of-sight, antenna pointing, occultation timing, and navigation education | Verify kernel comments, coverage intervals, frame IDs, precedence, leap seconds, time conversions, and consistency with PDS labels | **APPROVED** as a bounded versioned subset |
| MGS radio science derived products | `communication_navigation/mgs_radio_science` | [PDS profile](https://pds.nasa.gov/ds-view/pds/viewProfile.jsp?dsid=MGS-M-RSS-5-SDP-V1.0) | `MGS-M-RSS-5-SDP-V1.0` | Product-dependent atmospheric temperature/pressure profiles, gravity coefficients/covariances, and surface-reflection values with label-defined units | Mars Global Surveyor mission-era radio observations, including early occultation intervals | PDS tables/ancillary files; selected product likely MB-to-GB; exact size unknown | Distinguish radio observations and retrievals from computed ephemerides; teach occultation/geometry | Validate link geometry, inversion assumptions, quality flags, reference frame, covariance meaning, units, and time coverage | **APPROVED** for a bounded derived product |
| DSN archival tracking examples / TRK-2-25 documentation | `communication/dsn_archival_reference` | [PDS DSN TRK-2-25 collection](https://pds.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=urn:nasa:pds:radiosci.documentation:dsn.trk-2-25); [archive directory](https://pds-geosciences.wustl.edu/radiosciencedocs/urn-nasa-pds-radiosci_documentation/DSN_TRK-2-25/) | `urn:nasa:pds:radiosci.documentation:dsn.trk-2-25::1.3` | Archival tracking-file interface and examples; fields/units depend on TDF/ATDF product and mission | Example Voyager/Cassini archival files, not a current DSN activity stream | Small documentation/examples; actual mission data selection unknown | Explain tracking observations versus real-time station status | Parse TDF specification; verify mission, time tags, tracking observable, units, and archival terms | **NEEDS INVESTIGATION** |
| DSN Now | `communication/` (reference only) | [NASA DSN Now](https://eyes.jpl.nasa.gov/apps/dsn-now/dsn.html); [NASA DSN](https://www.nasa.gov/communicating-with-missions/dsn/) | DSN Now, no stable archive product ID | Current antenna/site, spacecraft/contact, transmit/receive state, signal/contact status; field schema/API not documented | Real-time network state, updated about every 5 seconds; not historical | Browser visualization; downloadable format and retention unknown | Optional live communication-status demonstration only | Confirm documented API/export, update latency, dropped contacts, station clocks, and redistribution terms | **REJECTED for static acquisition; NEEDS INVESTIGATION for live reference** |
| LRO LEND derived neutron products | `lunar_environment/lend` | [LEND archive](https://pds-geosciences.wustl.edu/missions/lro/lend.htm); [PDS derived collection](https://pds.nasa.gov/ds-view/pds/viewCollection.jsp?identifier=urn%3Anasa%3Apds%3Alro_lend%3Adata_science_derived&version=8.0) | `urn:nasa:pds:lro_lend:data_science_derived::8.0`; legacy `LRO-L-LEND-2-EDR-V1.0` | Neutron counts/rates/maps; SHEN high-energy neutron range approximately 0.3–15 MeV; exact units from labels | Lunar orbit from 2009-06-18 onward; product-dependent spatial/time bins | PDS4 derived products; selected release likely MB-to-GB; exact size unknown | Volatile/hydrogen prospecting and neutron-count educational context; no dose inference | Validate detector efficiency, collimation, orbital altitude, counting statistics, background correction, spatial resolution, and missing values | **APPROVED** using derived products |
| LRO Mini-RF selected derived radar products | `lunar_environment/mini_rf` | [Mini-RF archive](https://pds-geosciences.wustl.edu/missions/lro/mrf.htm); [PDS4 bundle](https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_minirf_bistatic/) | `urn:nasa:pds:lro_minirf_bistatic::8.0` | Radar backscatter, polarization/Stokes values, derived backplanes and CPR; units/product definitions from labels | Lunar orbit; product-dependent 2011–2026 coverage | PDS4 products and browse images; selected tiles likely MB-to-GB; full archive large | Polar radar/roughness/ice-prospecting lesson, not proof of water ice or landing safety | Validate incidence angle, polarization convention, calibration, geolocation, terrain, and cautious CPR interpretation | **APPROVED** for selected derived products |
| LRO LROC selected image tiles | `lunar_environment/lroc` | [LROC PDS archive via LRO page](https://pds-geosciences.wustl.edu/missions/lro/default.htm); PDS profile `LRO-L-LROC-3-CDR-V1.0` | `LRO-L-LROC-2-EDR-V1.0` / `LRO-L-LROC-3-CDR-V1.0` | NAC panchromatic approximately 0.5 m-scale; WAC approximately 100 m/pixel seven-band imagery; pointing/housekeeping metadata | Lunar orbit from 2009-06-18 onward | PDS image files; full archive is likely TB-scale; selected tiles MB-to-GB | Landmark recognition and visual terrain context using selected tiles | Validate camera calibration, phase angle/illumination, projection, pointing uncertainty, label/image dimensions, and provenance | **NEEDS INVESTIGATION** for selected tiles; reject full archive |
| OMNI low-resolution hourly solar wind/IMF | `space_weather/omni` | [OMNIWeb](https://omniweb.gsfc.nasa.gov/); [OMNI documentation](https://omniweb.gsfc.nasa.gov/html/ow_data.html); [record definitions](https://omniweb.gsfc.nasa.gov/html/ow_min_data.html) | OMNI low-resolution hourly record; no single PDS ID | IMF B/Bx/By/Bz in nT; solar-wind speed/components in km/s; proton density cm^-3; proton temperature K; quality, spacecraft ID, time-shift fields | Near-Earth/geocentric or L1 compilation, 1963-current; selected date range recommended | Fixed-width ASCII/FTP or subset output; selected 1–7 day interval likely KB-to-MB; full archive larger | Solar-wind context, communications/power planning, and space-weather comparison; not lunar dose | Validate time shifting, source spacecraft, interpolation percentage, fill values, cadence, units, and record definitions | **APPROVED** |
| OMNI high-resolution 5-minute records | `space_weather/omni_high_resolution` | [OMNI high-resolution documentation](https://omniweb.gsfc.nasa.gov/omniweb/html/ow_min_data.html) | OMNI high-resolution 5-minute product | Higher-cadence IMF/plasma variables with product-defined units and quality fields | 1981-current, product/source dependent | Fixed-width ASCII; bounded interval likely MB; full archive potentially large | Short space-weather event timeline; use as a separate cadence, not duplicate ACE EPAM/STEREO particle data | Validate cadence, time shifts, source spacecraft, quality/fill fields, and merged-product semantics | **APPROVED** after choosing a bounded interval |

## Candidate decisions by folder

### `datasets/astronaut_health/`

- **Approve first:** OSD-53, but acquire only a public, de-identified,
  processed subset after checking the current study license and file-level
  access.
- **Needs investigation:** NLSP physiological records. There is no uniform
  public format or access policy across records.
- **Reject for initial game integration:** raw or restricted individual-level
  medical/genomic files. They are unnecessary for an educational simulation
  and introduce privacy, consent, and interpretation risk.

### `datasets/communication/`

- **Reference only:** DSN Now. NASA describes it as a real-time visualization
  updated every five seconds, not a historical downloadable dataset.
- **Needs investigation:** PDS TRK-2-25 archival tracking examples. They are
  useful for understanding genuine tracking observables but are not a general
  historical DSN activity feed.

### `datasets/communication_navigation/`

- **Approve first:** a bounded LRO SPICE kernel subset with versioned kernel
  comments and a reproducible coverage manifest.
- **Second option:** a bounded MGS radio-science derived product, kept clearly
  separate from computed Horizons ephemerides.
- **Needs investigation:** raw Odyssey radio-science products because
  specialist processing is required.

### `datasets/mars_environment/`

- **Approve first:** calibrated/derived InSight TWINS interval.
- **Second option:** selected corrected MSL REMS meteorology.
- Every UI label must say **Mars measurement** and must not imply lunar
  conditions.

### `datasets/lunar_environment/`

- **Approve first:** LEND derived neutron product for lunar environmental
  context.
- **Second option:** selected Mini-RF derived tiles.
- **Needs investigation:** selected LROC tiles only; do not mirror the
  full image archive.
- No Diviner or LOLA duplicate should be acquired.

### `datasets/space_weather/`

- **Approve first:** bounded OMNI hourly records.
- **Second option:** a bounded OMNI 5-minute interval for event timelines.
- OMNI is a merged, time-shifted near-Earth product, not a lunar-surface
  measurement and not a direct astronaut dose.

## Recommended acquisition order

1. **OMNI hourly bounded interval** — compact, machine-readable, well
   documented, and directly useful for space-weather education without
   duplicating ACE EPAM or STEREO IMPACT.
2. **InSight TWINS calibrated/derived interval** — clear Mars weather
   application and stable PDS4 archive identity.
3. **LEND derived neutron product** — meaningful lunar environmental extension
   without duplicating Diviner or LOLA.
4. **OSD-53 processed public subset** — only after current OSDR file access,
   anonymization, and reuse terms are verified.
6. **LRO SPICE bounded kernel subset** — navigation/geometry integration after
   kernel coverage and time-system validation.
7. **Mini-RF selected derived products** — selected tiles only, after
   calibration and interpretation review.
8. **MSL REMS selected corrected interval** — useful Mars comparison but not
   required for the first lunar gameplay extension.
9. **MGS radio-science derived product** — technically valuable but requires
   more specialized processing.
10. **LROC selected tiles** — defer because image volume and processing burden
    are high.
11. **NLSP records, DSN Now, Odyssey raw radio science** — investigate only
    after access, export, and privacy/processing questions are resolved.

## Acquisition and validation gate

Before any approved dataset is downloaded:

1. Confirm the exact product URL, identifier, current archive version, file
   size, and access/redistribution terms.
2. Save the original under `datasets/raw/<category>/<dataset_name>/` without
   renaming or altering it.
3. Save source documentation, labels, citation, and access date.
4. Calculate and record SHA-256.
5. Validate structure, timestamps, units, coverage, flags, and missing values.
6. Create an independent processing script and deterministic processed output.
7. Generate summary statistics and a validation report.
8. Add catalog metadata only after the product passes the validation gate.
9. Integrate read-only dataset access before considering any Mission Briefing
   or training-event use.
10. Add tests for missing files, unavailable data, units, scientific labels,
    and offline fallback.

No acquisition or gameplay integration is authorized by this plan alone.
Proceeding to the first download requires review of this plan and approval of
the selected candidate and exact product interval.
