# API support contract for 0.1

Target: **0.1.0, first public alpha / early scientific software release**.
This is a maintenance commitment for documented behavior, not a claim that the
whole namespace or every scientific workflow is stable. Read the individual
[references](../reference/verbs/index.md) for argument and object contracts.

| Classification | Surface | Commitment / boundary |
| --- | --- | --- |
| Stable for 0.1 | `pipe`, `Pipe`, `|`, `unwrap()`; ordinary callable stages and the custom verb-factory pattern | Composition invokes callables in order; `unwrap()` returns the current object without forcing computation; no registration required. Preserve pass-through viewer attachment behavior. |
| Stable for 0.1 | Documented `v.apply`, `v.mean`, `v.variance`, `v.anomaly`, `v.zscore`, `v.month_filter`, `v.flatten_space`, `v.flatten_cube`, `v.overlap` | Preserve documented supported arguments and numerical/dimension semantics. This is not a promise to accept all xarray or vector shapes; overlap requires aligned boolean/state rasters. |
| Stable for 0.1 | Eight catalog noun entry points; `data.list_sources()`, `data.sources()`, `data.describe()` | Explicit supported sources and statistics, discoverable metadata, preserved source provenance, no synthetic fallback. Remote availability, additions to metadata, and source scientific suitability are separate. |
| Supported but may evolve during 0.x | `verbs` namespace beyond the named stable subset; provider/streaming helpers, plotting and I/O | Check factory versus direct-helper signatures and side effects. Being exported is not evidence of a complete implementation. Dask/laziness guarantees are operation-specific. |
| Supported but may evolve during 0.x | `explain()`, `suggest()`, `validate()`, `semantic_state`, `semantic_trace`; `cubedynamics.grammar` | Metadata-only inspection must not rewrite or execute analyses. Report fields, coaching rules, wording, suggestion ordering and inferred vocabulary may evolve. Do not treat text or metadata schema as a permanent interchange format. |
| Supported but may evolve during 0.x | Source lifecycle, schema, QA, revision and promotion helpers | Preserve explicit distinction between scientific revision, endpoint health and evidence. Exact schemas are early interfaces; successful validation does not publish or promote. |
| Deprecated compatibility | `climate_cube_math`; warning-emitting legacy loader/ops shims | Remain installed and importable in 0.1 with migration warnings. Use `cubedynamics` and canonical verbs for new code. No removal in this pass. |
| Project-specific | Fire VASE / FireHull / FireEventDaily, synchrony, biology, tubes | Ship for compatibility with narrow domain contracts. Their assumptions and renderers do not enlarge the core grammar; no physical extraction in 0.1. |
| Experimental / candidate | `cubedynamics.data.three_dep.elevation`, `.roads.roads`, `.usgs.streamflow`; Daymet candidate | Explicit installed imports and real-data lessons are valid, but do not imply promotion, production serving revisions or a frozen API. Daymet is blocked, not a usable catalog source. |
| Reserved / not implemented | `v.correlation_cube`, `v.fit_model` | Raise rather than provide the planned analysis. Other implemented correlation helpers are distinct APIs. |

Compatibility without deprecation is a separate case: `v.exceedance` is an
alias; AOI/block workflow names have documented differences; `TimeHull` is a
compatibility name. Do not invent warning/removal promises for these. The
maintained `v.month_filter` is not deprecated; its legacy ops import warns.

## Catalog and candidate boundary

Catalog nouns: temperature, precipitation, humidity, radiation, vpd, wind,
surface_reflectance, vegetation_index. Current production catalog flavors:
**gridMET, PRISM, Sentinel-2**. Their recorded serving status is not a new live
certification of all locations or dates.

3DEP, Overture, OSM and modern USGS streamflow retain **candidate** status and
no production serving revision. They remain absent from `data.list_sources()`.
Their [noun references](../library/index.md), import tests and twelve supported
notebooks do not substitute for evidence-bound promotion. Overture and OSM
are not independent scientific equivalents; provisional USGS status and native
elevation vertical reference must remain visible.

## Change policy before 1.0

Patch releases preserve the documented stable subset while correcting bugs.
0.x minor releases may evolve early APIs with release notes and migration
guidance; do not casually break the named stable behavior or silently remove
compatibility imports. Future major module extraction requires a separate
deprecation and archival decision. Internal modules remain implementation
details except where an explicit public adapter is documented.

[Release notes](release_0_1_0.md) · [Full API scope](public_api.md) ·
[Dependency audit](dependency_audit_0_1.md)
