---
description: "Validation status, provenance, acceptance checks, and dependency ledger for the South Dakota Decision Lab."
---

# Decision Lab Validation

This page prevents the collection from implying more capability or evidence
than the package currently provides. Publication status is based on public API
existence, observed-data provenance, notebook execution, visible QA, tests, and
a strict documentation build.

## Collection status

| Decision vignette | Status | Why |
|---|---|---|
| Black Hills | Dependency design | Feature nouns and general vector/raster intersection missing |
| Missouri & watersheds | Dependency design | Surface-water/human-system nouns and categorical change missing |
| Working Lands | **Executable** | Public PRISM nouns, strict aligned-state overlap, observed fixture, QA and decision figures |
| Habitat Squeeze | Dependency design | Conservation and pressure nouns missing |
| Communities | Dependency design | Exposure and hazard/history nouns missing |
| Wildcard | Template | API-current starter plus rules for unavailable nouns |

“Dependency design” pages contain no computed decision result and no runnable
calls to nonexistent APIs.

## Working Lands evidence

| Field | Published value |
|---|---|
| Provider | PRISM Climate Group, Oregon State University |
| Product | PRISM AN81d/AN91d daily time series |
| Public loaders | `data.temperature`, `data.precipitation` |
| Source flavor | `prism` |
| AOI | `[-101.2, 43.7, -100.4, 44.3]` (WGS84) |
| Time | 1–31 July 2024, daily |
| Cube size | 31 × 15 × 19 per noun |
| Temperature range | 21.922–40.386 °C |
| Precipitation range | 0–40.260 mm/day |
| Finite cells | 8,835 per noun |
| Fixture SHA-256 | `f9f3f0da6c621383b60d4895e661a185d3d58e7393b4f339ee91d36d83228a6a` |
| Generated measurements | None |

The fixture is checked in as
[`tests/fixtures/real_data/sd_working_lands_july_2024.nc`](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/fixtures/real_data/sd_working_lands_july_2024.nc)
with a checked
[`provenance record`](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/fixtures/real_data/sd_working_lands_july_2024.provenance.json).
It is a small publication/QA extract, not a replacement data backend. The
builder calls the public loaders and refuses generated fallback. PRISM grids
may be revised; the checksum freezes the values rendered here.

## Acceptance checks

The fixture and notebook fail validation if any of these contracts break:

- source or fixture reports generated measurements;
- dimensions are not exactly `(time=31, y=15, x=19)`;
- dates are not daily and complete;
- units are not °C and mm;
- cells are non-finite or outside broad physical QA ranges;
- temperature and precipitation coordinates are not exactly aligned;
- the notebook omits either its source-QA figure or decision figure;
- public loaders/verbs named by executable code do not exist;
- documentation links or the strict MkDocs build fail.

The working notebook's thresholds are analytical definitions, not provider
quality flags: “warm” is the cell-specific upper July quartile and “dry day”
is precipitation ≤ 0.1 mm. The page explicitly avoids calling these definitions
a drought classification or long-term anomaly.

## Implemented vocabulary used here

At this publication revision, the discoverable noun catalog includes:

- climate/weather: `temperature`, `precipitation`, `vpd`, `wind`, `humidity`,
  and `radiation`;
- surface observations: `surface_reflectance` and `vegetation_index`.

The executable page uses `quantile_state`, `threshold_state`, `overlap`, and
`mean`. `overlap` combines exactly aligned boolean/state rasters; it does not
reproject, resample, intersect vector geometries, or calculate risk.

## Missing noun ledger

| Planned noun | Blocks | Minimum integration evidence |
|---|---|---|
| Buildings | Black Hills, Communities | Authoritative source, date/completeness limits, geometry/count QA |
| Roads | Black Hills, Missouri, Habitat, Communities | Network provenance, class semantics, topology and scale checks |
| Fire history | Black Hills, Communities | Authoritative events, dates, perimeter validation, duplicates |
| Mining claims | Black Hills, Habitat | Status/date semantics, geometry and duplicate QA |
| Protected areas / land management | Black Hills, Habitat | Designation categories, manager, effective dates, boundaries |
| Surface water / hydrography / streamflow | Missouri | Temporal classifications, topology/gauge semantics, cloud/ice QA |
| Cropland / land cover | Missouri, Working Lands, Habitat | Year-specific classes, accuracy, resolution and transition rules |
| Critical habitat | Habitat | Species/designation identity, effective date, legal-use caveat |
| Population | Communities | Census vintage, unit, spatial allocation and uncertainty |
| Soil moisture | Working Lands | Depth/product meaning, units, temporal/spatial support and QA |

## Missing reusable verb ledger

| Capability | Why it matters | Required contract |
|---|---|---|
| Geometry-aware `intersect` | Feature/raster overlap | Explicit CRS, boundary semantics, output type, source identity |
| Transparent `summarize` | Review-unit counts/areas | Units, weights, missingness, grouping and denominator |
| Categorical `change` | Surface-water/land-cover transitions | Named classes, early/recent support, no subtraction of codes |
| Proximity/density | Nearby systems and pressure context | Distance units, projection, edge effects, feature vs area meaning |
| Cross-grid alignment | Climate + Sentinel-2 + features | Explicit reprojection, resolution, temporal support and no silent loss |

These are package roadmap items, not APIs promised by the dependency pages.

## Reproduce validation

```bash
pytest tests/test_overlap_verb.py tests/test_decision_vignettes.py -q
python scripts/run_vignettes.py docs/decision_vignettes/working_lands.ipynb
python scripts/run_decision_qa.py
mkdocs build --strict
```

The online smoke test for the source acquisition is marked `online` and
`integration`; ordinary CI uses the checksum-controlled observational fixture.
