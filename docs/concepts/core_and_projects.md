# Core grammar, integrations, and project verbs

CubeDynamics is a grammar first. The shortest complete description is:

```python
from cubedynamics import pipe, verbs as v

result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.variance(dim="time")
).unwrap()
```

`pipe` carries a value. Each verb accepts that value and returns the next one.
The grammar does not require a particular data source, renderer, or scientific
domain.

## The four layers

| Layer | Responsibility | Examples in this repository |
| --- | --- | --- |
| Core grammar | Composition and execution contract | `pipe`, `Pipe`, verb factories, cube dimension conventions |
| Maintained vocabulary | Common operations useful across projects | `v.mean`, `v.anomaly`, `v.variance`, `v.zscore`, `v.apply` |
| Integrations | Translate external systems into or out of the grammar | PRISM, gridMET, Sentinel-2, plotting backends |
| Project extensions | Express a domain analysis as custom verbs and workflows | synchrony, biological coupling, Fire VASE |

This is an ownership boundary, not yet a breaking package boundary. Existing
public imports remain available throughout the `0.x` compatibility window.

## What makes something a verb?

A verb is an ordinary callable that accepts the current pipe value:

```python
def clip_values(low, high):
    def _op(cube):
        return cube.clip(min=low, max=high)

    return _op
```

It can now be composed without registration:

```python
clipped = (pipe(cube) | clip_values(0, 1)).unwrap()
```

The outer function stores user configuration. The inner function performs one
operation on the incoming value. This small protocol is the extension system.

For a one-off operation, `v.apply(function, **kwargs)` avoids writing the outer
factory. For a reusable project vocabulary, named factories are easier to test,
document, and review.

## When a verb belongs to a project

A verb is probably project-specific when it encodes one or more of:

- a domain threshold or scientific interpretation;
- a study-area, cohort, event, or instrument convention;
- an output schema owned by one analysis;
- access to project credentials or unpublished data;
- dependencies most CubeDynamics users do not need.

Keep those verbs in the project that owns the assumptions. Import them next to
the shared grammar:

```python
from cubedynamics import pipe, verbs as v
from my_fire_project import verbs as fire_v

result = (
    pipe(cube)
    | v.anomaly()
    | fire_v.classify_burn_weather(threshold=2.5)
)
```

The grammar stays common while the scientific vocabulary remains attributable.

## Read next

- [Write a custom verb](../extending/custom_verbs.md)
- [Runnable vignettes](../vignettes/index.md)
- [Public API and stability](../project/public_api.md)
- [Publication audit and plan](../project/publication_plan.md)
