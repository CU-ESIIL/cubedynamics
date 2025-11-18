# Pipe Syntax & Verbs

CubeDynamics introduces a lightweight pipe system inspired by ggplot/dplyr so your cube math reads like a recipe. Every verb returns a callable that accepts an `xarray` cube. The `Pipe` object manages chaining and execution.

## Pipe object

```python
import cubedynamics as cd

pipe_obj = cd.pipe(cube)
```

`pipe()` wraps any `xarray.DataArray` or `xarray.Dataset` in a `Pipe`. You can append verbs with the `|` operator. Nothing runs until you call `.unwrap()` (or `.compute()` if you prefer) on the pipe.

## Basic chaining

```python
result = (
    cd.pipe(cube)
    | cd.anomaly(dim="time")
    | cd.month_filter([6, 7, 8])
    | cd.variance(dim="time")
).unwrap()
```

Each verb receives the output from the previous step. Pipes are composable, so you can store sub-pipes or branch into different analyses.

## Writing your own verbs

Verbs are just callables that accept keyword arguments now and return a function that operates on the cube later. A minimal template:

```python
from cubedynamics.ops.piping import ensure_dataarray  # optional helper


def my_center(dim):
    def _inner(cube):
        data = ensure_dataarray(cube)
        return data - data.mean(dim=dim)
    return _inner
```

Once defined, register it inside `cubedynamics/__init__.py` (or import from your own module) so you can call `cd.pipe(cube) | cd.my_center(dim="time")`.

## Error handling

Pipes propagate exceptions from verbs. If you need custom validation, raise informative errors inside your verb so users know which operation failed.

## Mixing verbs and direct calls

The pipe syntax is optional. Every verb can still be invoked directly: `cd.variance(dim="time")(cube)` returns the variance cube immediately. Pipes simply improve readability for long workflows and standardize streaming-first processing.
