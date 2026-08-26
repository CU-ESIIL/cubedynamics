# Phase 1 real-data QA fixtures

These small NetCDF files are bounded extracts from observational products used
to keep publication QA deterministic and offline-capable. They are not
synthetic data and are not alternative production backends.

| Fixture | Product | Coverage | Purpose |
| --- | --- | --- | --- |
| `gridmet_badlands_july_2001.nc` | gridMET daily maximum temperature | Badlands, South Dakota; 10 days in July 2001 | Source, grid, time, units, range, and visual checks |
| `sentinel2_badlands_june_2023.nc` | Sentinel-2 L2A B04/B08 reflectance | Badlands, South Dakota; bounded June 2023 scenes | Source, CRS, bands, acquisition identity, scale, NDVI, and visual checks |

Each fixture has a sibling provenance JSON containing its source request,
creation method, and SHA-256 checksum. The QA runner refuses a fixture whose
bytes no longer match that record.

PRISM uses the existing real-data fixture in `data/vignettes/`. To rebuild the
two fixtures in this directory, run:

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
