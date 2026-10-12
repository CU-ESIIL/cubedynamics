# Source comparison and bounded evidence

SI S9–S11, Tables S10–S15, distinguish discovery, scientific interpretation,
and evidence. This page preserves that dated comparison; the generated
[noun library](../library/index.md), [source directory](../library/sources/index.md),
and [Phase 1 QA](phase1_qa.md) own current source details.

## Shared names retain different products

| Temperature property | PRISM | gridMET |
| --- | --- | --- |
| Daily statistics | Maximum, minimum, mean | Maximum and minimum; no native mean |
| Native variables | `tmax`, `tmin`, `tmean` | `tmmx`, `tmmn` |
| Units | Degrees Celsius | Kelvin |
| Native grid | Approximately 4 km | 1/24 degree |
| Documented span in the SI | 1981 onward | 1979 onward |
| Daily support | Product-specific convention retained | A different product-specific convention retained |
| Revision behavior | Recent daily grids can be remodeled | Recent observations progress through maturity stages |
| Reviewed scope | Bounded temperature extract | Bounded maximum-temperature extract |

Unit conversion or regridding can produce computational compatibility without
establishing measurement equivalence. Provider, product, native variable,
statistic, units, support, grid, retrieval query, and source revision remain
part of the analysis. See [temperature](../library/nouns/temperature.md) and
[temporal alignment](../concepts/temporal_alignment.md).

The SI discovery inventory includes temperature and precipitation from PRISM
and gridMET; vpd, wind, humidity, and radiation from gridMET; and surface
reflectance and vegetation index from Sentinel-2. Wind, humidity, and radiation
are umbrella names: native variable, height or aggregation where applicable,
and units determine the actual quantity. Catalog presence is not evidence
that all possible interpretations have received scientific QA. Sentinel-2
retains spectral, acquisition, spatial, and cloud/scene constraints; its index
is linked to reflectance inputs and provenance.

## Installed candidates have narrower boundaries

| Candidate | Bounded implementation described in the SI | Boundary |
| --- | --- | --- |
| USGS streamflow | One station, continuous discharge, native status/units, time × station | Dates, batches, observations, retries, bytes; no hydrologic decision validation |
| USGS 3DEP | One fully covering CONUS 1/3 arc-second tile, native static raster | No mosaicking, silent clipping, value reprojection, or invented time axis |
| Overture roads | Explicit release, native features and classes | AOI, partitions, row groups, features, attempts, bytes |
| OpenStreetMap roads | Small Overpass way query, native tags and identifiers | No claim of a production backend or complete routable network |

These remain outside production source discovery and have no production
serving revision. A roads comparison does not rank provider quality nationally.
Current promotion and transport contracts live in
[operational readiness](source_projects/production.md); historical project
proofs and installed candidate adapters are separate evidence objects.

## What each evidence layer establishes

| Layer | Supports | Does not establish |
| --- | --- | --- |
| Retrieval/live health | Recorded endpoint and access behavior | Future availability or scientific correctness |
| Fixture/provenance | Reviewed bytes, query, identity, checksum | All places, dates, products, or observations |
| Structural interpretation | Variables, dimensions, coordinates, units, CRS, masks, schema | Observational accuracy |
| Numerical QA | Broad ranges, finiteness, ordering, source relationships | Independent ground truth or causality |
| Visual review | Detectable orientation, clipping, spatial/temporal and rendering problems | Universal validity |
| Semantic tests | Transitions, order, metadata, expected rejection | A complete scientific rule catalog |
| Publication checks | Executable notebooks, references, links, rendering | Productivity or superiority |

A serving revision identifies the adapter and interpretation contract, not
the provider's scientific version. Schema fingerprints describe structure
without requiring value computation. Fixture certification and live health
must retain independent records.

SI Table S14 records bounded Phase 1 evidence for
`temperature.prism@2026-08-26.1`, `temperature.gridmet@2026-08-26.1`, and
`surface_reflectance.sentinel2@2026-08-26.1`. PRISM checks include source flags,
checksum, CRS, dates, finiteness, physical bounds, AOI overlap, and minimum
temperature not exceeding maximum. gridMET adds spacing, orientation, and
kelvin bounds; annual-file retrieval remains a caveat. Sentinel-2 checks B04/B08,
ordered acquisitions, finite pixels, 10 m native UTM spacing, scaling, and NDVI
bounds; baseline pixel cloud masking is absent. These are bounded adapter
checks, not certifications of every variable.

The September 25 live record reports a bounded PRISM pass with caveats and
Daymet blocked by a missing Earthdata token. Daymet is a separate credentialed
certification target, not a production noun or one of the installed candidates.
This intake performs no new live certification.

The vignette inventory spans cube construction, grammar, states/events,
project callables, deferred execution, native terrain/road/station shapes, and
Working Lands. Each lesson should retain context, question, pipe, figures,
interpretation, data record, and reproduction instructions. Missing fixtures
are errors rather than grounds to generate substitute observations. See
[vignettes](../vignettes/index.md) for the current manifest.

Source: [SI, pp. 14–18](../assets/manuscripts/2026-10-12/supplement-11.pdf#page=14).
