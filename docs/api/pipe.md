# Pipe API

A pipe applies the written operations in order. It does not rearrange the
analysis or implicitly turn a plot into data.

## Usage

```python
from cubedynamics import data, pipe, verbs as v

# Live data request; use the Learn shared setup for an offline fixture.
cube = data.temperature(
    source="prism", bbox=[-105.55, 39.85, -105.05, 40.15],
    start="2024-06-01", end="2024-06-03",
)
analysis = pipe(cube) | v.anomaly(dim="time") | v.mean(dim=("y", "x"), keep_dim=False)
print(analysis.explain())
result = analysis.unwrap()
```

Inspection methods report semantic state, trace and checks; they do not execute
new analytical stages. Display a plotting pipe in Jupyter to use its attached
viewer; unwrapping returns the data rather than the viewer.

The pipe records only the statement written inside it. Preparation before
`pipe(...)` and transformations after `unwrap()` remain outside its trace.
`unwrap()` returns the wrapped value; it does not force computation, certify a
result, or complete the wider workflow.

## pipe

::: cubedynamics.piping.pipe
    options:
      show_docstring_examples: false

## Pipe methods and properties

The [object reference](objects.md#pipe) renders the Pipe methods from source.
See the [short pipes lesson](../learn/pipes.md) for a tested, real-data example.

## Verb wrapper

Most users call factories in the [verbs namespace](../reference/verbs/index.md)
rather than constructing this wrapper directly.

::: cubedynamics.piping.Verb
    options:
      show_docstring_examples: false

## See also

[Scientific inspectability](../concepts/scientific_inspectability.md) ·
[Semantic grammar](../concepts/semantic_grammar.md) ·
[Custom verbs](../extending/custom_verbs.md) · [API stability](../project/public_api.md)
