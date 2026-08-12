# Grammar of Streaming

Once data is accessible through a streaming interface, CubeDynamics gives you a grammar for computation.

The grammar is intentionally simple:

- `pipe(...)`
- verbs
- lazy evaluation where possible
- composable workflows

This simplicity is a feature for both scientists and AI agents.

## Core Pattern

```python
from cubedynamics import pipe, verbs as v

result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.mean(dim=("y", "x"), keep_dim=False)
)
```

## In This Section

- [Pipe](../api/pipe.md)
- [Verbs](../api/verbs.md)
- [Lazy evaluation](lazy_evaluation.md)
- [Workflow composition](workflow_composition.md)
- [Core grammar versus project verbs](../concepts/core_and_projects.md)
- [Runnable vignettes](../vignettes/index.md)

## Why Grammar Matters

The grammar makes workflows:

- readable
- inspectable
- reproducible
- easy to reason about in notebooks and agent-driven execution

The grammar is the core product. Dataset loaders and renderers are integrations;
synchrony, biology, and Fire VASE are examples of projects that add specialized
verbs. See [Core grammar, integrations, and project verbs](../concepts/core_and_projects.md).
