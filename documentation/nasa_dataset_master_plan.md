# NASA scientific dataset master plan

**Scope:** inventory, acquisition planning, and dataset status. Dataset-specific
acquisition details and validation outcomes are maintained in their own
documentation and reports. Static datasets are not dependencies of the game
simulation's resource calculations or mission progression. The NASA Data
Explorer and informational Mission Setup briefing display them through a
read-only local backend API, which exposes metadata and saved summaries for
the processed datasets and bounded records for ACE EPAM, STEREO-A,
Horizons, OMNI, and LEND
Horizons. Mission Control may show available values as context in optional,
clearly labeled training events; DONKI remains a separate network-backed
integration.

The current DONKI integration and static dataset API are described in the
[NASA dataset integration architecture](nasa_dataset_integration_architecture.md).
The static API details are in
[NASA static dataset backend documentation](nasa_dataset_backend.md).
The frontend display is documented in
[NASA Data Explorer](nasa_data_explorer.md).
The Mission Setup briefing is documented in
[NASA Mission Briefing](nasa_mission_briefing.md).
The optional Mission Control scenarios are documented in
[NASA gameplay integration](nasa_gameplay_integration.md).

The machine-readable inventory is
[`datasets/metadata/dataset_catalog.csv`](../datasets/metadata/dataset_catalog.csv).
It records purpose, authoritative source, acquisition route, access conditions,
formats, variables and units (or the required product-label check), coverage,
gameplay relevance, status, validation status, known storage, limitations and
priority.

## What is in the project now

- **Diviner:** one unmodified PDS table,
  `global_cumul_avg_cyl_80s70s_002.tab`, in the 70°S–80°S global-longitude
  band, plus its PDS labels, format definition and SIS. Its validation report
  records 1,382,400 rows, 11 columns, 156,211,313 bytes and `PASSED`. A
  separate deterministic gzip-CSV conversion and summary statistics are
  available; the raw PDS source remains unchanged. See
  [`documentation/diviner_processing.md`](diviner_processing.md).
- **LOLA:** the original PDS `LDEM_16` global elevation raster, its labels,
  projection reference and RDR SIS; the raw data remain unchanged. A processed
  NumPy grid and global/latitude-band summaries are available under
  `datasets/processed/lunar_environment/lola/`. See
  [`documentation/lola_dataset.md`](lola_dataset.md),
  [`documentation/lola_processing.md`](lola_processing.md), and the validation
  report. The label-versus-observed extrema warning is retained.
- **ACE EPAM:** a bounded one-day `AC_H1_EPM` five-minute Level 2 CDF sample,
  with CDAWeb metadata and EPAM documentation. Its original CDF remains
  unchanged; a processed NumPy archive and per-variable summaries are now
  available under `datasets/processed/space_weather/ace_epam/`. See
  [`documentation/ace_epam_dataset.md`](ace_epam_dataset.md) and
  [`documentation/ace_epam_processing.md`](ace_epam_processing.md).
- **STEREO IMPACT:** one STEREO-A HET daily-average monthly file, with its
  SPDF README and instrument guide. The original source remains unchanged; a
  reproducible, token-preserving compressed CSV and channel summaries are
  available under `datasets/processed/space_weather/stereo_impact/`. See
  [`documentation/stereo_impact_dataset.md`](stereo_impact_dataset.md) and
  [`documentation/stereo_impact_processing.md`](stereo_impact_processing.md).
- **JPL Horizons:** one bounded Earth–Moon observer-table response covering
  seven elapsed days, with eight daily UTC samples, request metadata and the
  official API documentation/manual. Its source values are preserved in a
  normalized CSV alongside a clearly labeled derived two-way vacuum light
  time. See [`documentation/jpl_horizons_dataset.md`](jpl_horizons_dataset.md),
  [`documentation/jpl_horizons_processing.md`](jpl_horizons_processing.md),
  and the validation report.
- **OMNI2:** the official 2020 annual OMNI2 hourly source is preserved with its
  format documentation. A bounded January 2020 selection contains 744 hourly
  records, official fill values, and all 55 documented fields. See
  [`documentation/omni_dataset.md`](omni_dataset.md) and the validation report.
- **DONKI:** the backend currently integrates the FLR and SEP JSON feeds. It
  uses a server-side key and cache, with a public CCMC DONKI fallback documented
  in the integration notes. These are API observations, not downloaded static
  datasets. CME and GST are not currently integrated.
- **Not present:** OSDR study files, other Diviner products, LOLA illumination
  products, an Artemis-specific environmental product, Mars environmental
  files, or bulk ephemeris archives. Processed Diviner, LOLA, ACE EPAM, and
  STEREO HET data remain separate from gameplay.

The project has a local `backend/.env`; its contents were not read or reported.
The `NASA_API_KEY` value and validity were not tested as part of this inventory.
The existing service falls back to `DEMO_KEY` if its process environment does
not supply a key. Never copy a key into this catalog, documentation, frontend,
or an API response.

## Inventory by science category

| Candidate | Official source / access route | Useful data and coverage | Status and main caveat |
|---|---|---|---|
| DONKI FLR | [NASA Open APIs](https://api.nasa.gov/) / [CCMC DONKI](https://ccmc.gsfc.nasa.gov/DONKI/) JSON API | Solar flare times, catalog class and linked event metadata; API query window | **Integrated.** A flare class is not a dose or lunar radiation measurement. |
| DONKI CME | [CCMC DONKI](https://ccmc.gsfc.nasa.gov/DONKI/) JSON API | CME event metadata and available coronagraph analyses | Not integrated. Record fields and linked analyses vary; not direct lunar dose. |
| DONKI SEP | [NASA Open APIs](https://api.nasa.gov/) / [CCMC DONKI](https://ccmc.gsfc.nasa.gov/DONKI/) JSON API | SEP event times, instruments, linked events, and event-specific metadata | **Integrated.** Does not measure outpost exposure or crew dose. |
| DONKI GST | [CCMC DONKI](https://ccmc.gsfc.nasa.gov/DONKI/) JSON API | Geomagnetic storm intervals and Kp-index records | Not integrated. Earth's geomagnetic environment is not a lunar surface measurement. |
| ACE EPAM | [NASA SPDF archive](https://spdf.gsfc.nasa.gov/pub/data/ace/epam/) and [CDAWeb](https://cdaweb.gsfc.nasa.gov/) | One-day 2020-01-01 `AC_H1_EPM` five-minute Level 2 CDF sample, 277 UTC records and 88 measurement/uncertainty variables | **Downloaded and processed; raw validation PASSED_WITH_WARNINGS.** Deterministic NPZ and per-variable metadata/summaries retained; see [ACE processing documentation](ace_epam_processing.md) and [validation report](../datasets/validation_reports/ace_epam_validation.json). ACE L1 data are not lunar dosimetry. |
| STEREO IMPACT HET/LET/SIT | [NASA SPDF STEREO archive](https://spdf.gsfc.nasa.gov/pub/data/stereo/); selected [Ahead HET ASCII product](https://spdf.gsfc.nasa.gov/pub/data/stereo/ahead/l2/impact_ascii/het/1day/AeH12Mar.1d) | One STEREO-A HET March 2012 monthly file; 31 daily intervals, 3 electron and 11 proton channels, each with one-sigma uncertainty | **STEREO-A HET sample downloaded and processed; raw validation PASS.** Token-preserving compressed CSV and per-channel metadata/statistics are available; see [STEREO processing documentation](stereo_impact_processing.md) and [validation report](../datasets/validation_reports/stereo_impact_validation.json). Spacecraft observations are not lunar dose. Other HET/LET/SIT products remain candidates. |
| NASA OMNI2 hourly | [NASA SPDF OMNI archive](https://spdf.gsfc.nasa.gov/pub/data/omni/low_res_omni/omni2_2020.dat) and [OMNIWeb documentation](https://omniweb.gsfc.nasa.gov/html/ow_data.html) | January 2020 bounded selection from the 55-field hourly OMNI2 product: IMF, plasma, solar-wind and geomagnetic context; 744 records | **Downloaded and processed; validation PASS_WITH_WARNINGS.** Official fill values are retained. OMNI is merged/time-shifted near-Earth context, not lunar surface telemetry or astronaut dose. |
| LRO LEND RDR DLD/DLX | [NASA PDS LEND archive](https://pds-geosciences.wustl.edu/missions/lro/lend.htm) and [RDR SIS](https://pds-geosciences.wustl.edu/lro/lro-l-lend-2-edr-v1/lrolen_0xxx/document/lend_rdr_sis.htm) | 2020-01-01 derived and extended-derived products; 85,308 paired orbital records with coordinates, detector counts, corrected CSETN sum, and sigma fields | **Downloaded and processed; validation PASS_WITH_WARNINGS.** Original binaries, labels, XML labels, SIS, hashes, processed CSV, metadata, and summary retained. Orbital counts are not surface flux, dose, or direct water-ice confirmation; see [LEND documentation](lend_dataset.md). |
| OSDR human physiology | [NASA OSDR](https://osdr.nasa.gov/bio/repo/) | Study-specific physiology and omics from flight and analog investigations | Not downloaded. Select individual public studies; check consent, restrictions, metadata and endpoints. |
| OSDR radiation biology | [NASA OSDR](https://osdr.nasa.gov/bio/repo/) | Study-specific biological endpoints and exposure protocols | Not downloaded. Exposure units and shielding must come from study dosimetry and methods; no direct game dose conversion. |
| OSDR plant growth / space biology | [NASA OSDR](https://osdr.nasa.gov/bio/repo/) | Study-specific growth, environmental, imagery or omics data | Not downloaded. Species, hardware, protocols and conditions limit transfer to lunar agriculture. |
| Existing Diviner GCP | [PDS Geosciences Diviner archive](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm), [selected product](https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gcp/global_cumul_avg_cyl_80s70s_002.tab) | Historical gridded `clon`, `clat`, `ltim`, `t3`–`t9`, `tbol`; 70°S–80°S, 2009–2015 | **Downloaded and validated.** 148.95 MiB; historical brightness temperatures, not a local thermometer or forecast. |
| Additional Diviner calibrated RDR | [PDS Diviner release page](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm) | Calibrated orbital observations; LRO archive from 2009 onward, product-dependent | Not downloaded. Full archive is large; subset before transfer. Check labels for field units, quality, coverage and missing channel data. |
| Diviner GHRM | [PDS GHRM collection](https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_ghrm/) | High-resolution mapped thermal layers; global, layer-specific coverage through the reported collection period | Not downloaded. Select one GeoTIFF/IMG layer and verify label, projection and size before transfer. |
| Diviner Polar Resource Products | [PDS PRP collection](https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_prp/) | North and south polar derived products | Not downloaded. Each listed north/south table is 604,800,210 bytes (~576.4 MiB), so acquire only after checking use and storage. |
| Lunar illumination / solar availability | [LOLA PDS archive](https://pds-geosciences.wustl.edu/missions/lro/lola.htm), [Lunar Orbital Data Explorer](https://ode.rsl.wustl.edu/moon/) | Candidate terrain/illumination products; exact variables, temporal assumptions and region depend on selected product | No specific product selected. Search by polar location; inspect the original model and product labels before deriving sunlight duration or power. |
| Artemis-era environmental science | [PDS Data Search](https://pds.nasa.gov/datasearch/data-search/) | Mission/instrument-specific released data, if an appropriate product is archived | No Artemis surface-environment product selected or verified. “Artemis data” is not one dataset; distinguish direct surface observations from precursor orbital data and future/planned measurements. |
| Perseverance MEDA | [PDS Atmospheres Node Mars holdings](https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/MARS/) and [PDS Data Search](https://pds.nasa.gov/datasearch/data-search/) | Rover-local atmospheric/ground environmental channels, product dependent, since 2021 | Not downloaded. Retrieve a short interval only; use product labels for units and flags. Mars is not a lunar environmental analog. |
| Curiosity REMS | [PDS Atmospheres Node Mars holdings](https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/MARS/) and [PDS Data Search](https://pds.nasa.gov/datasearch/data-search/) | Rover-local weather channels, product dependent, since 2012 | Not downloaded. Product units and coverage vary; use only for explicitly comparative Mars lessons. |
| JPL Horizons Earth–Moon geometry | [JPL Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html) | Moon (301) from Earth geocenter (500@399); eight daily UTC range/range-rate and one-way down-leg light-time epochs for 2026-11-14 through 2026-11-21 | **Bounded sample downloaded and processed; raw validation PASSED_WITH_WARNINGS.** Seven epochs postdate retrieval and are forward calculations. Normalized CSV retains source precision; two-way vacuum value is explicitly derived, not a separate Horizons measurement. See [Horizons acquisition documentation](jpl_horizons_dataset.md), [processing documentation](jpl_horizons_processing.md), and validation report. Geometric light time excludes communications-system/network latency. |
| JPL Horizons Earth–Mars geometry | [JPL Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html) | Earth–Mars distance and ephemeris values over selected epochs | Not integrated. Useful for a Mars comparison, not for lunar communication calculations. |

The CSV is the authoritative detail table where an inventory cell calls for
product-specific metadata. Variables, units, file structure, temporal
coverage, null values, and data volume must be verified against the selected
product's own label/guide or API response before acquisition. Similar product
names do not guarantee identical schemas.

## Access and size assessment

- **Public direct downloads:** PDS Diviner/LOLA products and listed SPDF ACE and
  STEREO archives do not require a NASA Open API key. Archive access is public,
  but product documentation and allowable study use still apply.
- **API access:** DONKI's `api.nasa.gov` gateway uses the backend-only
  `NASA_API_KEY`; `DEMO_KEY` is a low-limit testing fallback, not a permanent
  integration credential. Current FLR/SEP feeds are cached by the backend.
  Horizons documents a public query API; this plan uses bounded requests, not
  bulk ephemeris extraction.
- **OSDR:** study search and public files are available through the NASA
  repository. Availability and conditions are study-specific. Do not assume
  every human-subject file is open; check access controls, privacy/consent,
  data-use terms and the study's data dictionary before downloading.
- **Artemis:** access depends on mission data release and archive deposition.
  Search NASA/PDS holdings for an actual released product before describing it
  as available.
- **Known storage:** existing Diviner GCP is 156,211,313 bytes. The two
  Diviner polar-resource tables are each listed at 604,800,210 bytes. The
  additional candidate datasets do not have a planned selection or bounded
  interval yet, so aggregate sizes are intentionally marked unknown. Check
  PDS/SPDF inventories, manifests, and `Content-Length`/listed file sizes
  before any large transfer; do not mirror entire archives.

## Recommended acquisition order

Priorities are for a safe, useful educational collection, not an instruction
to download now.

1. **P1 — Bound Diviner/LOLA local-environment choices.** First investigate
   polar illumination/topography and a small set of applicable Diviner
   products. Confirm the outpost coordinates, projection, local-time meaning,
   epochs, data size, and product limitations. The existing Diviner band is
   broad and historical.
2. **P1 — Keep space weather API-first.** Continue using already-integrated
   FLR/SEP. Consider CME next if its exact API fields support a distinct,
   scientifically bounded lesson. Do not add ACE/STEREO flux to a lunar dose
   model.
3. **P2 — Keep particle archives bounded.** Initial ACE EPAM and STEREO-A HET
   samples have been downloaded and validated. Do not expand to multi-year
   archives without a specific science question; any additional STEREO
   instrument, spacecraft, cadence or interval requires a separate product
   review and validation.
4. **P2 — Horizons light-time demonstration.** A bounded Earth–Moon sample is
   now acquired and validated. Further queries should answer a specific
   educational question and record frame, observer, units and time scale.
   Earth–Mars remains an optional comparison.
5. **P2 — Artemis product discovery.** Search PDS by actual mission,
   instrument, target and data-product identifiers. Do not treat plans or
   analog/orbital products as a measured Artemis surface environment.
6. **P3 — Carefully selected OSDR and Mars examples.** These have educational
   value but require additional interpretation and have limited direct
   relevance to a lunar outpost. Choose one open OSDR study or short Mars
   rover interval only after reviewing protocols, privacy/access terms,
   units, missing-value conventions and storage.
7. **Defer bulk products.** Avoid full Diviner RDR collections, both 576 MiB
   PRP tables, multi-decade ACE/STEREO archives, large omics/images and broad
   PDS mirrors until a concrete question and storage budget justify them.

## Validation and scientific-use rules

For each future acquisition, capture the official product identifier, source
URL, retrieval date, byte size and cryptographic checksum before parsing.
Preserve original raw bytes. Keep labels, dictionaries, calibration notes,
quality flags and licenses/terms alongside the raw source. Validate the format
with its intended reader, units and sentinel values with the product
documentation, time and spatial bounds, row/record counts, and known quality
indicators. Write a report; never overwrite raw files to make them parse.

NASA observations must remain separate from any fictional mission values.
ACE and STEREO are spacecraft measurements at their own locations; DONKI is an
event catalog; Diviner is remote infrared/radiance-derived surface brightness
temperature; Mars sensors describe Mars; and Horizons gives computed
ephemerides. None alone directly measures radiation dose, temperature inside
the game habitat, actual lunar surface illumination at every instant, or
real-world communication-network delay. The processed static datasets can
inform the Mission Setup educational briefing and optional Mission Control
training-event context. They are not connected to resource calculations or
mission progression. Training-event choices use fixed simulated effects and
remain separate from ordinary and DONKI event queues. DONKI remains the
separate, existing real-event integration; its game consequences are
simulated.

## Official source references

- [NASA Open APIs](https://api.nasa.gov/) and [CCMC DONKI](https://ccmc.gsfc.nasa.gov/DONKI/)
- [NASA SPDF ACE archive](https://spdf.gsfc.nasa.gov/pub/data/ace/epam/), [NASA SPDF STEREO archive](https://spdf.gsfc.nasa.gov/pub/data/stereo/), and [CDAWeb](https://cdaweb.gsfc.nasa.gov/)
- [NASA OSDR](https://osdr.nasa.gov/bio/repo/)
- [PDS LRO Diviner](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm), [PDS LRO LOLA](https://pds-geosciences.wustl.edu/missions/lro/lola.htm), [Lunar ODE](https://ode.rsl.wustl.edu/moon/), and [PDS Data Search](https://pds.nasa.gov/datasearch/data-search/)
- [PDS Atmospheres Node Mars holdings](https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/MARS/)
- [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/) and [Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
