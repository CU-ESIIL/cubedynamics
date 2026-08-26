# Phase 1 source QA

Phase 1 establishes noun/source discovery and rationalizes the existing
gridMET, PRISM, and Sentinel-2 integrations. It does **not** claim that every
source has completed the full future-source definition of done.

## Current evidence status

| Source flavor | Offline contracts | Scheduled live endpoint test | Reviewed real numerical QA | Reviewed real visual QA |
| --- | --- | --- | --- | --- |
| PRISM temperature | pass | yes | pass | pass |
| gridMET nouns | pass | yes | pending checked fixture | pending checked fixture |
| Sentinel-2 nouns | pass | yes | pending checked fixture | pending checked fixture |

“Pending” is deliberate. Existing preview images are not promoted to validation
evidence merely because they render. A visual pass requires reproducible source
records, numerical invariants, and human review.

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
- [Underlying fixture provenance](https://github.com/CU-ESIIL/cubedynamics/blob/main/data/vignettes/prism_boulder_january_2024.provenance.json)

## Reproduce it

```bash
python scripts/run_source_qa.py
```

The command writes fresh evidence to `artifacts/source_qa/`. CI runs it beside
the broader publication validation suite and uploads both artifact trees. The
checked website image and JSON were produced by pointing `--output` at
`docs/assets/source_qa` after review.

## What blocks a full source pass

gridMET still retrieves annual files before client-side AOI selection, so a
server-side subset path should replace it before Phase 2 climate expansion.
Sentinel-2 needs a small checksum-controlled real reflectance fixture with
cloud/nodata, orientation, CRS, band, and reflectance-range checks. These are
tracked as open Phase 1 QA work rather than silently treated as complete.
