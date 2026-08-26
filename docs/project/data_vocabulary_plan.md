# Scientific data vocabulary: audit and phased publication plan

## Publication objective

CubeDynamics should let a scientist select a defensible environmental noun,
then keep the analysis readable:

```python
pipe(data.some_environmental_noun(...))
| v.some_general_scientific_verb(...)
| v.some_general_scientific_verb(...)
```

Source mechanics stay below the noun. Original fields, provider, product,
query, CRS, versions, normalization, and derivation state stay visible in
metadata.

## Repository audit

The audit found a strong core grammar and three established data integrations,
but no single noun-first public namespace. `variables.py` offered temperature
and NDVI shortcuts while provider loaders lived separately. PRISM already had
the strongest streaming contract: server-side daily AOI subsets, Dask-delayed
requests, explicit synthetic opt-in, and focused tests. Sentinel-2 used lazy
`cubo` access but lacked standardized provenance. The gridMET high-level loader
contained a critical defect: its default “streaming” and “download” paths
generated random arrays while identifying them as real gridMET. That path has
been replaced with authoritative annual NetCDF access; generated values now
require explicit low-level opt-in and are refused by scientific nouns.

The documentation was organized mainly around provider products. Phase 1 adds
a noun-first layer without deleting the provider pages needed for detailed
source methods and citations.

## Phase ledger

| Phase | Goal | Status | Gate before advancing |
| --- | --- | --- | --- |
| 1 | Rationalize gridMET, PRISM, and Sentinel-2; noun/source discovery; provenance; publication structure | architecture implemented; QA partially complete | reviewed gridMET and Sentinel-2 real fixtures and visual/numerical QA |
| 2 | Climate depth: Daymet, ERA5-Land, ERA5, TerraClimate; then justified NLDAS/GLDAS sources | not started | each flavor meets source definition of done |
| 3 | Raster nouns: HLS, Landsat, MODIS, ECOSTRESS, surface water, land cover, elevation; GEDI if clean | not started | independent source QA and source-choice docs |
| 4 | Decision/feature nouns: mining claims, buildings, roads, protected areas, land management, hydrography, fire | not started | defensible schema and geometry/time semantics |
| 5 | Ecology, agriculture, extraction, and exposure nouns | not started | provider definitions and non-conflation checks |
| 6 | Infrastructure breadth | not started | stable authoritative services and bounded tests |
| 7 | Historical and derived nouns | not started | defensible temporal semantics; no invented dates |

## Phase 1 public nouns

- Climate: `temperature`, `precipitation`, `vpd`, `wind`, `humidity`,
  `radiation`
- Surface observation: `surface_reflectance`
- Vegetation: `vegetation_index`
- Discovery: `sources`, `describe`, `list_sources`

Provider-specific loaders remain supported for backward compatibility. The
registry includes implemented sources only; planned sources do not appear as
placeholders.

## Phase 1 known limitations

- gridMET uses real annual NetCDF retrieval but does not yet crop on the server.
- PRISM's current real NcSS path covers daily `ppt`, `tmean`, `tmin`, and
  `tmax`; other published PRISM variables are not registered prematurely.
- Sentinel-2 scene cloud percentage is not a pixel cloud mask.
- Automatic cross-source harmonization, unit conversion, regridding, and
  categorical handling are intentionally deferred to explicit verbs.
- Reviewed real visual/numerical source QA currently covers PRISM temperature.
  gridMET and Sentinel-2 remain visibly pending on the QA page.

## Next recommended work

Finish Phase 1 evidence before adding nouns: implement a stable server-side
gridMET subset path and create checksum-controlled real gridMET and Sentinel-2
fixtures with orientation, CRS, units, nodata/cloud, physical range, and visual
checks. Then add Daymet first in Phase 2 because it provides authoritative,
well-documented North American daily climate through a robust THREDDS subset
service and makes source-flavor comparison immediately useful.

