# NASA LRO SPICE dataset

The project preserves a bounded sample from the official NASA/JPL NAIF PDS3
archive `LRO-L-SPICE-6-V1.0`.

- **Source:** [NAIF archived PDS SPICE data](https://naif.jpl.nasa.gov/naif/data_archived.html)
- **Selected kernel:** `lrorg_2017258_2017349_v01.bsp`
- **Kernel coverage:** 2017-09-15 through 2017-12-15 UTC
- **Processed selection:** 24 hourly epochs on 2017-09-15 UTC
- **Supporting kernel:** `naif0012.tls` for UTC conversion
- **Frame/reference:** LRO (NAIF -85) relative to Moon (301), J2000, kilometers

`validate_lro_spice.py` checks the preserved files, PDS label identity and
coverage metadata. `process_lro_spice.py` uses the official NAIF SPICE
calculation (`spkpos`) to generate Cartesian positions, lunar-center distance,
and one-way light time. No values are fabricated or interpolated.

The output is computed spacecraft geometry, not direct telemetry. It does not
represent an astronaut, habitat, surface location, or current navigation state.
