# Phase 1 source QA

Phase 1 establishes noun/source discovery and rationalizes the existing
gridMET, PRISM, and Sentinel-2 integrations. Each Phase 1 source adapter now
has a checksum-controlled real-data baseline, numerical checks, and a reviewed
figure. This does **not** imply that every variable or AOI has been validated.

## Current evidence status

| Source flavor | Offline contracts | Scheduled live endpoint test | Reviewed real numerical QA | Reviewed real visual QA |
| --- | --- | --- | --- | --- |
| PRISM temperature | pass | yes | pass | pass |
| gridMET maximum temperature | pass | yes | pass | pass |
| Sentinel-2 B04/B08 and derived NDVI | pass | yes | pass | pass |

The pass applies to the exact products and bounded extracts named in the table.
Other gridMET variables still require variable-specific scientific QA.

## Reviewed PRISM result

![PRISM temperature source QA: one map and one point-in-time summary](../assets/source_qa/prism_temperature.png)

The offline QA workflow checks:

- the NetCDF fixture SHA-256 against its provenance manifest;
- observational/source flags and explicit CRS;
- strictly increasing requested dates;
- finite values and nonempty dimensions;
- minimum temperature never exceeding maximum temperature;
- broad physical temperature bounds;
- coordinate bounds overlapping the documented AOI.

Machine-readable evidence:

- [PRISM result JSON](../assets/source_qa/prism_temperature.json)
- [Phase 1 source manifest](../assets/source_qa/manifest.json)
- [Underlying fixture provenance](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/fixtures/real_data/prism_boulder_january_2024.provenance.json)

## Reviewed gridMET result

![gridMET maximum-temperature source QA](../assets/source_qa/gridmet_temperature.png)

The gridMET baseline checks the source and SHA-256 record, EPSG:4326 CRS,
strict daily dates, finite values, 1/24° resolution, known coordinate
orientation, requested bounds, and a broad physically plausible Kelvin range.

- [gridMET result JSON](../assets/source_qa/gridmet_temperature.json)
- [gridMET fixture provenance](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/fixtures/real_data/gridmet_badlands_july_2001.provenance.json)

## Reviewed Sentinel-2 result

![Sentinel-2 B04, B08, and derived NDVI source QA](../assets/source_qa/sentinel2_reflectance.png)

The Sentinel-2 baseline checks source and checksum records, native UTM CRS,
B04/B08 availability, unique ordered acquisition dates, finite pixels, 10 m
spacing, coordinate orientation, provider reflectance scale, and NDVI bounds.
QA exposed duplicate STAC processing records for the same acquisitions; the
loader now keeps the record with the latest `s2:generation_time` while leaving
imagery lazy.

- [Sentinel-2 result JSON](../assets/source_qa/sentinel2_surface_reflectance.json)
- [Sentinel-2 fixture provenance](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/fixtures/real_data/sentinel2_badlands_june_2023.provenance.json)

## Reproduce it

```bash
python scripts/run_source_qa.py
```

The command writes fresh evidence to `artifacts/source_qa/`. CI runs it beside
the broader publication validation suite and uploads both artifact trees. The
checked website image and JSON were produced by pointing `--output` at
`docs/assets/source_qa` after review.

## Remaining limitations

gridMET still retrieves annual files before client-side AOI selection, so a
server-side subset path should replace it before Phase 2 climate expansion.
The reviewed gridMET extract covers maximum temperature only. Sentinel-2 cloud
metadata are retained, but the baseline does not implement pixel-level cloud
masking and covers only one small South Dakota window. Live endpoint tests
remain separate because an offline fixture cannot detect provider outages.
