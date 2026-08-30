# Inspectable environmental grammar

CubeDynamics places a small semantic grammar around ordinary scientific Python
objects. Source-qualified nouns identify observations; configured verbs describe
transformations; and the pipe preserves authored order. State and trace make the
resulting scientific statement inspectable while xarray, Dask, NumPy, and
geospatial libraries retain numerical ownership.

The grammar is intentionally simple:

- `pipe(...)`
- verbs
- semantic state and an ordered trace
- lazy evaluation where the underlying operation permits it
- composable workflows

This simplicity is a feature for both scientists and AI agents.

## Core Pattern

```python
from cubedynamics import pipe, verbs as v

result = (
    pipe(cube)
    | v.anomaly(over="time")
    | v.mean(over=("y", "x"), keep_dim=False)
)
```

## In This Section

- [Scientific inspectability](../concepts/scientific_inspectability.md)
- [Pipe](../api/pipe.md)
- [Verbs](../api/verbs.md)
- [Lazy evaluation](lazy_evaluation.md)
- [Workflow composition](workflow_composition.md)
- [Core grammar versus project verbs](../concepts/core_and_projects.md)
- [Semantic grammar and analysis coaching](../concepts/semantic_grammar.md)
- [Runnable vignettes](../vignettes/index.md)

## Why Grammar Matters

The grammar makes analytical statements:

- readable
- inspectable
- reproducible
- explicit about authored order and information loss
- connected to source identity and bounded evidence

It does not make source products interchangeable, establish that a method is
scientifically appropriate, or turn a semantic trace into complete workflow
provenance. `unwrap()` returns the ordinary value without forcing computation
or certifying the result.

The grammar is the core product. Dataset loaders and renderers are integrations;
synchrony, biology, and Fire VASE are examples of projects that add specialized
verbs. See [Core grammar, integrations, and project verbs](../concepts/core_and_projects.md).
