# Public Python API

Use `import cubedynamics as cd` and `from cubedynamics import data, pipe, verbs as v`.
The [public API policy](../project/public_api.md) defines supported names and
compatibility boundaries.

| Surface | Reference |
| --- | --- |
| Scientific nouns and source flavors | [Noun library](../library/index.md) |
| Loaders, discovery, configuration, and revision helpers | [Data API](data.md) |
| Every public verb-namespace callable | [All public callables (A–Z)](../reference/verbs/a-z.md) |
| Composition, unwrapping, and coaching | [Pipe](pipe.md) and [semantic grammar](../concepts/semantic_grammar.md) |
| Pipe, VirtualCube, event/hull objects, and semantic states | [Objects](objects.md) |
| Visualization entry points | [Visualization API](viz.md) |

For examples of composing these interfaces, follow [Learn](../learn/index.md)
or the [vignettes](../vignettes/index.md).

The exhaustive internal-symbol inventory and deprecated module shims are kept
under [Developer documentation](../developer/index.md#technical-background-and-compatibility),
not mixed into the user reference.
