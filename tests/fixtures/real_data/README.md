# Phase 1 real-data QA fixtures

`source_lessons/` contains a 99×99 native 3DEP elevation window and 528 Overture /
611 OSM road features near Boulder, frozen from the previously validated bounded
responses. The two provenance manifests bind the three files to SHA-256 hashes
and retain original acquisition metadata. The explicit freeze script is
`scripts/build_source_lesson_fixtures.py`; it only replays existing responses,
checks serialization identity, and refuses overwrite. No invented values,
resampling, or simplification. Preserve Overture/OSM ODbL attribution in reuse.
These small teaching inputs are not new production certification.

The `usgs_streamflow/` directory additionally retains exact modern USGS OGC
JSON response bodies (`.bin`) and request records for three stations on
August 26, 2026. `provenance.json` binds every file checksum. Acquisition was
explicit through `scripts/check_source_candidates.py --export-usgs-fixture`;
the export refuses overwrite. Values, native status and NetCDF round trips
were checked against the raw responses. All retained observations were
provisional; this is adapter regression evidence, not hydrologic certification.

These small NetCDF files are bounded extracts from observational products used
to keep publication QA deterministic and offline-capable. They are not
synthetic data and are not alternative production backends.

| Fixture | Product | Coverage | Purpose |
| --- | --- | --- | --- |
| `prism_boulder_january_2024.nc` | PRISM daily minimum and maximum temperature | Boulder region; January 2024 | Publication vignettes and full validation suite |
| `sd_working_lands_july_2024.nc` | PRISM daily maximum temperature and precipitation | Central South Dakota; July 2024 | Executable Decision Lab lesson and decision QA |
| `gridmet_badlands_july_2001.nc` | gridMET daily maximum temperature | Badlands, South Dakota; 10 days in July 2001 | Source, grid, time, units, range, and visual checks |
| `sentinel2_badlands_june_2023.nc` | Sentinel-2 L2A B04/B08 reflectance | Badlands, South Dakota; bounded June 2023 scenes | Source, CRS, bands, acquisition identity, scale, NDVI, and visual checks |

This directory is the repository-policy-approved home for checked-in test and
publication fixtures. Each fixture has a sibling provenance JSON containing
its source request, creation method, and SHA-256 checksum. The QA runners
refuse a fixture whose bytes no longer match that record.

The PRISM teaching and Decision Lab extracts live here as well. To rebuild the
gridMET and Sentinel-2 source-QA fixtures, run:

```bash
python scripts/build_phase1_qa_fixtures.py
```

That command uses public upstream services and therefore requires network
access. Routine validation is fully offline:

```bash
python scripts/run_source_qa.py
```

The reviewed report is published at `docs/data/phase1_qa.md`. A passing
fixture is evidence for the exact product, variable, place, and time window
listed above; it is not a claim that every variable or geography has received
scientific validation.
