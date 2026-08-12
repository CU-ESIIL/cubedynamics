# Write a custom verb project

CubeDynamics add-ons are usually small Python projects that contribute a
domain vocabulary of verbs. No registry, subclass, or plugin framework is
required: a verb is a callable from the current value to the next value.

## Start with a factory

This example turns a temperature cube into a heat-stress state cube while
preserving coordinates and lazy array behavior:

```python
import xarray as xr


def heat_stress(*, threshold: float = 35.0):
    """Classify temperature values at or above ``threshold``."""

    def _op(cube: xr.DataArray) -> xr.Dataset:
        if "time" not in cube.dims:
            raise ValueError("heat_stress requires a 'time' dimension")

        state = (cube >= threshold).rename("state")
        magnitude = (cube - threshold).where(state, 0).rename("magnitude")
        return xr.Dataset({"state": state, "magnitude": magnitude})

    return _op
```

Use it beside built-in verbs:

```python
from cubedynamics import pipe, verbs as v
from my_project.verbs import heat_stress

states = (
    pipe(temperature_cube)
    | v.anomaly(dim="time")
    | heat_stress(threshold=2.0)
).unwrap()
```

## Recommended project shape

```text
my-cubedynamics-project/
├── pyproject.toml
├── src/my_project/
│   ├── __init__.py
│   └── verbs.py
├── tests/
│   └── test_verbs.py
└── notebooks/
    └── analysis.ipynb
```

Depend on a compatible CubeDynamics range and import only its public surface.
Project notebooks should import verbs from `my_project.verbs`; do not keep the
only copy of scientific logic inside notebook cells.

## Contract checklist

A publishable custom verb should:

1. Do one interpretable operation.
2. Validate required dimensions and metadata instead of guessing.
3. Preserve coordinates, attributes, chunking, and laziness when feasible.
4. Avoid `.compute()`, downloads, or disk writes unless the verb explicitly
   represents materialization or I/O.
5. Return a predictable type and document any shape change.
6. Work both as a direct callable and in a pipe.
7. Have a deterministic small-cube regression test.

## Direct and pipe tests

```python
direct = heat_stress(threshold=35.0)(cube)
composed = (pipe(cube) | heat_stress(threshold=35.0)).unwrap()
xr.testing.assert_identical(direct, composed)
```

If the input is Dask-backed, also assert that the result still has chunks.

## One-off functions

Use `v.apply` when a named project verb would add ceremony without reuse:

```python
centered = (
    pipe(cube)
    | v.apply(lambda value, dim: value - value.mean(dim), dim="time")
).unwrap()
```

Promote the function into your project module when its assumptions, name, or
tests become part of the scientific method.

## Working example

The repository includes a minimal, tested scaffold in
[`examples/custom_verb_project/`](https://github.com/CU-ESIIL/cubedynamics/tree/main/examples/custom_verb_project)
and an executable [custom-verb vignette](../vignettes/custom_verb_project.ipynb).
