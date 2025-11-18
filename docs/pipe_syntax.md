# Pipe Syntax & Verbs

CubeDynamics exposes a lightweight `Pipe` object so `xarray` workflows read like a recipe. Every verb returns a callable that accepts the cube later, keeping the `|` chaining syntax clean.

## The Pipe object

```python
import cubedynamics as cd

pipe_obj = cd.pipe(cube)
```

`cd.pipe(value)` wraps any `xarray.DataArray` or `xarray.Dataset` without altering it. Use the `|` operator to apply verbs, then call `.unwrap()` to retrieve the final object.

## Chaining verbs

```python
result = (
    cd.pipe(cube)
    | cd.anomaly(dim="time")
    | cd.variance(dim="time")
).unwrap()
```

Each verb receives the previous output. Pipes simply pass the cube along, so as long as the object behaves like an `xarray` structure the chain continues.

## Core verbs

All examples below use in-memory data so you can run them in any notebook.

### `anomaly(dim="time")`

```python
import numpy as np
import xarray as xr
import cubedynamics as cd

time = np.arange(4)
cube = xr.DataArray([1.0, 2.0, 3.0, 4.0], dims=["time"], coords={"time": time})

anoms = (cd.pipe(cube) | cd.anomaly(dim="time")).unwrap()
```

`anomaly` subtracts the mean along the dimension you specify.

### `month_filter(months)`

```python
import numpy as np
import pandas as pd
import xarray as xr
import cubedynamics as cd

time = pd.date_range("2000-01-01", periods=12, freq="MS")
values = np.arange(12)

cube = xr.DataArray(values, dims=["time"], coords={"time": time})

summer = (cd.pipe(cube) | cd.month_filter([6, 7, 8])).unwrap()
```

`month_filter` keeps only the months you list (in numeric form) based on the `time` coordinate.

### `variance(dim="time")`

```python
var = (cd.pipe(cube) | cd.variance(dim="time")).unwrap()
```

`variance` runs `xarray.var` under the hood, so any axis can be supplied.

### `to_netcdf(path)`

```python
from pathlib import Path

path = Path("example.nc")
(cd.pipe(cube) | cd.to_netcdf(path)).unwrap()
```

`to_netcdf` writes the incoming cube to disk (returning the original object so the pipe can continue). When running docs examples you can point to a temporary directory such as `/tmp/example.nc`.

### `correlation_cube(other, dim="time")`

```python
other = xr.DataArray([0.5, 1.5, 2.5, 3.5], dims=["time"], coords={"time": time})

corr = (
    cd.pipe(cube)
    | cd.correlation_cube(other, dim="time")
).unwrap()
```

`correlation_cube` computes correlations between the pipeline cube and another cube along the dimension provided.

## How Pipe.unwrap works

`Pipe.unwrap()` simply returns the wrapped `xarray` object after the final verb. It does not copy data; it only exposes the last computed value.

## Define your own verbs

Verbs follow a small factory pattern: accept configuration parameters now, return a callable that receives the cube later.

```python
def my_custom_op(param):
    def _inner(da):
        # operate on da (xarray DataArray/Dataset)
        return da
    return _inner

result = (cd.pipe(cube) | my_custom_op(param=42)).unwrap()
```

Register your verb in your own module or import it in your notebook, then use it alongside the built-in operations.
