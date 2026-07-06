# Pipe syntax & verbs

CubeDynamics exposes a lightweight `Pipe` object so `xarray` workflows read like recipes. Each verb is a factory that returns a callable, letting you configure parameters upfront and apply them later with the `|` operator.

## The Pipe object

```python
from cubedynamics import pipe

pipe_obj = pipe(cube)
```

`pipe(value)` wraps any `xarray.DataArray` or `xarray.Dataset` without altering it. Use the `|` operator to apply verbs. In notebooks the last `Pipe` expression in a cell auto-displays the wrapped object, so calling `.unwrap()` is optional unless you immediately need the `xarray` object.

## Chaining verbs

```python
from cubedynamics import pipe, verbs as v

out = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.variance(dim="time")
).unwrap()
```

Each verb receives the previous output. Pipes simply pass the cube along, so as long as the object behaves like an `xarray` structure the chain continues. The pattern mirrors tidyverse pipes, but in Python.

## Core verb categories

Verbs are grouped into focused namespaces:

- **Transform verbs** – reshape, filter, or derive indices (`v.anomaly`, `v.month_filter`, `v.ndvi_from_s2`).
- **Stats verbs** – summarize cubes along dimensions (`v.mean`, `v.variance`, `v.zscore`) or convert units (`v.anomaly`).
- **IO verbs** – persist results without breaking the chain (`v.to_netcdf`).
- **Visualization verbs** – preview cubes inline (`v.show_cube_lexcube`, QA plots) before exporting.
- **Models (coming soon)** – wrappers around ML/statistical models that accept cubes as inputs.

Cross-dataset correlation verbs are reserved for a future release: the exported `v.correlation_cube` factory currently raises `NotImplementedError`. Use `v.rolling_median_split_synchrony` for below/above-quantile synchrony, or the lower-level helpers in `cubedynamics.stats.correlation`/`stats.tails` for custom analyses.

See the [Verbs Reference](../reference/verbs_transforms.md) section for detailed signatures and examples.

## Lexcube integration

Lexcube visualizations follow the same pattern:

```python
pipe(cube) | v.show_cube_lexcube(title="NDVI anomalies")
```

The verb renders the widget as a side effect and returns the original cube. Helpers such as `cd.show_cube_lexcube` are available when you are not inside a pipe chain.

## Define your own verbs

Verbs follow a simple factory pattern—accept configuration parameters now, return a callable that receives the cube later:

```python
def my_custom_op(param):
    def _inner(da):
        # operate on da (xarray DataArray/Dataset)
        return da
    return _inner

from cubedynamics import pipe

result = pipe(cube) | my_custom_op(param=42)
```

Register your verb in your own module or import it into notebooks, then use it alongside the built-in operations. Tests under `tests/` cover both direct invocation and pipe usage, so mirror that pattern when adding new verbs.
