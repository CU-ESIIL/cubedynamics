---
description: "Provenance and acceptance checks for the real PRISM and USGS inputs used by publication vignettes."
---

# Real-data validation

The eight core grammar vignettes use the observational teaching extract:
`tests/fixtures/real_data/prism_boulder_january_2024.nc`.

| Field | Reviewed value |
| --- | --- |
| Provider | PRISM Group, Oregon State University |
| Product | AN91d daily 4 km time series |
| Variables | daily minimum temperature, daily maximum temperature, derived daily range |
| Time | 1–30 January 2024, complete daily sequence |
| Bounds | −105.75 to −104.75 longitude; 39.50 to 40.50 latitude |
| Grid | 30 dates × 24 latitude rows × 24 longitude columns |
| CRS | EPSG:4269 |
| Accessed | 2026-08-25 |

![PRISM data diagnostic](../assets/validation/data/diagnostic.png)

## Acceptance checks

The validation module rejects the fixture unless:

- its SHA-256 matches the provenance record;
- the provider and non-generated-data flag are explicit;
- dates are complete and ordered, longitude increases, and latitude decreases;
- all 51,840 stored cells are finite;
- minimum temperature never exceeds maximum temperature;
- daily range equals `tmax - tmin` within the float32 storage tolerance; and
- all 60 official daily archives have URL, byte-count, and SHA-256 evidence.

The fixture provenance is machine readable at
[`tests/fixtures/real_data/prism_boulder_january_2024.provenance.json`](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/fixtures/real_data/prism_boulder_january_2024.provenance.json).

Source: [PRISM Group](https://prism.oregonstate.edu/),
[dataset documentation](https://www.prism.oregonstate.edu/documents/PRISM_datasets.pdf),
and [terms of use](https://prism.oregonstate.edu/terms/).

## Rebuild

```bash
python scripts/build_vignette_data.py --download-missing
python scripts/run_validation.py
```

Downloads are never implicit in the lessons or offline CI. The rebuild flag is
an explicit request to retrieve the 60 recorded official archives; each is
verified before the extract is written.

## USGS source lesson

The [streamflow lesson](../vignettes/streamflow_snapshots.ipynb) instead replays
real USGS continuous-discharge responses for Boulder Creek, the Potomac, and
Lees Ferry on August 26, 2026. Its manifest at
`tests/fixtures/real_data/usgs_streamflow/provenance.json` binds every request
record and raw response body to a SHA-256 checksum. Missing, additional, or
modified snapshot files fail the publication input check; replay never downloads
replacement observations.

The loader retains station identity, native units, UTC timestamps, and quality
status. Values and statuses were compared with the original provider JSON;
NetCDF round trips and pipe reductions were checked. All these samples were
provisional. This establishes retained-input integrity and adapter behavior,
not hydrologic suitability or broad production certification. See the
[candidate evidence and limitations](../data/source_projects/production.md).

## Terrain and road lessons

The [elevation lesson](../vignettes/elevation_landscape.ipynb) uses a retained
99×99 native 3DEP window. The [roads lesson](../vignettes/roads_local_network.ipynb)
uses 528 Overture and 611 OSM features from the same Boulder query area. These
serialized loader outputs live in `tests/fixtures/real_data/source_lessons/`.
Their manifests retain original request/response identities, source metadata,
and extract hashes. Export checks compare native cells, geometries, identifiers,
and provider records before and after serialization.

The fixtures are not simplified, regridded, or class-harmonized. Clipping and
projected-length calculations are explicit later transformations. Attribution
is retained; Overture and OSM are not independent ground truth.
