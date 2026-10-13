# Scientific data contract

This is the user-facing contract boundary for current development behavior.
The [semantic model](semantic_grammar.md) describes the interpretation layer;
generated [nouns](../library/index.md) and [verbs](../reference/verbs/index.md)
define specific accepted objects and arguments. Different operations need
different dimensions: static terrain, vector roads, station series, summaries,
and spatiotemporal rasters do not share one universal cube shape.

| Aspect | Implemented checks or propagation | Assumptions and limits |
| --- | --- | --- |
| Dimensions | Named reductions require their dimension; canonical raster names are `time`, `y`, `x`, optional `band` | Adapters may retain native names. Not every callable normalizes them |
| Coordinates | Overlap requires exact labels; harmless dimension ordering can normalize | Equality does not establish matching observation footprints |
| CRS | Nouns retain source CRS; overlap preflight rejects known conflicts; spatial operations have specific inference/reprojection rules | Absent CRS is a review condition in semantic reports, not a universal execution error |
| Temporal meaning | State tracks labels and known support; explicit alignment can require exact support | Missing support stays unknown; daily labels alone do not authorize PRISM/gridMET interchange |
| Units | State retains known units; variance squares them; conditions/proportions are dimensionless where defined | There is no complete dimensional algebra or automatic cross-source conversion |
| Metadata | Maintained verbs update result meaning, dimensions, units and definition records | Metadata inference cannot prove source descriptions correct |
| Provenance | Nouns retain provider/product, native variable, query and source/revision records | Pipe traces do not capture all preparation, branches or downstream work |
| Missingness | Threshold comparisons and condition means follow documented two-valued rules | No general valid-observation denominator, uncertainty propagation, or minimum-valid threshold |

## Units and compatibility

PRISM temperature is Celsius; gridMET temperature is kelvin. Converting units
is a visible analytical operation, not an automatic benefit of a shared noun.
Threshold numbers must use the input unit. Overlap's coordinate/CRS/support
checks do not certify compatible thresholds or physically equivalent products.
Unknown units remain unknown, and `validate()` reports metadata conditions
without computing values to discover their true physical interpretation.

See [condition/reduction semantics](condition_contracts.md),
[temporal support](temporal_alignment.md), and
[source contracts](../library/sources/index.md). The internal
[spatial contract](../design/spatial_dataset_contract.md) includes legacy CRS
fallbacks; follow each operation's actual API instead of assuming every spatial
helper fails on missing CRS or every non-spatial object requires time.

## Serialization

Source and continuous-summary scalar metadata are NetCDF-safe under the
documented export policy. For condition/state Datasets, use
[to_netcdf](../reference/verbs/to_netcdf.md): Boolean variables become flagged
int8 in a write-only copy, preserving the in-memory object. Structured metadata
is serialized canonically; unsupported custom objects fail rather than yielding
unstable representations. A downstream reader must interpret flags explicitly;
writing a file does not certify its later scientific use.

The checks are in [first-use acceptance tests](https://github.com/CU-ESIIL/cubedynamics/blob/main/tests/test_first_use_acceptance.py).
This is object serialization, not automatic export of complete workflow lineage.

## Where protection stops

**Enforced:** cataloged input kinds/required information, operation-specific
coordinate/support checks, explicit export constraints.

**Advisory/inferred:** inferred semantic state, unknown metadata checks, order
messages, suggestions and explanations. These expose software interpretations
without choosing a scientifically correct method.

**Planned/unresolved:** three-valued conditions, durable merged branch lineage,
complete uncertainty propagation, automatic scientific harmonization, and
universal semantic rule coverage. Reserved names are not implementation.

A valid Python expression and a successful computation can still answer the
wrong question. The analyst must justify source, support, thresholds, weights,
missing-value handling and interpretation. Review the
[evidence matrix](../validation/methods.md#claim-to-evidence-matrix) for exactly
which software claims have test coverage.
