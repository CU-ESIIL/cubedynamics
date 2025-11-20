# Pipe Syntax & Verbs

CubeDynamics exposes a lightweight `Pipe` object so `xarray` workflows read like a recipe. Every verb returns a callable that accepts the cube later, keeping the `|` chaining syntax clean.

## The Pipe object

```python
from cubedynamics import pipe

pipe_obj = pipe(cube)
```

`pipe(value)` wraps any `xarray.DataArray` or `xarray.Dataset` without altering it. Use the `|` operator to apply verbs. In notebooks the last `Pipe` expression in a cell auto-displays the wrapped object, so calling `.unwrap()` is optional unless you immediately need the `xarray` object.

## Chaining verbs

```python
from cubedynamics import pipe, verbs as v

result = (
    pipe(cube)
    | v.anomaly(dim="time")
    | v.variance(dim="time")
)
```

Each verb receives the previous output. Pipes simply pass the cube along, so as long as the object behaves like an `xarray` structure the chain continues.

## Core verbs

All examples below use in-memory data so you can run them in any notebook.

### `anomaly(dim="time")`

```python
import numpy as np
import xarray as xr
from cubedynamics import pipe, verbs as v

time = np.arange(4)
cube = xr.DataArray([1.0, 2.0, 3.0, 4.0], dims=["time"], coords={"time": time})

anoms = pipe(cube) | v.anomaly(dim="time")
```

`anomaly` subtracts the mean along the dimension you specify.

### `month_filter(months)`

```python
import numpy as np
import pandas as pd
import xarray as xr
from cubedynamics import pipe, verbs as v

time = pd.date_range("2000-01-01", periods=12, freq="MS")
values = np.arange(12)

cube = xr.DataArray(values, dims=["time"], coords={"time": time})

summer = pipe(cube) | v.month_filter([6, 7, 8])
```

`month_filter` keeps only the months you list (in numeric form) based on the `time` coordinate.

### `variance(dim="time")`

```python
from cubedynamics import pipe, verbs as v

var = pipe(cube) | v.variance(dim="time")
```

`variance` runs `xarray.var` under the hood, so any axis can be supplied.

### `to_netcdf(path)`

```python
from pathlib import Path
from cubedynamics import pipe, verbs as v

path = Path("example.nc")
pipe(cube) | v.to_netcdf(path)
```

`to_netcdf` writes the incoming cube to disk (returning the original object so the pipe can continue). When running docs examples you can point to a temporary directory such as `/tmp/example.nc`.

### `correlation_cube(other, dim="time")` (planned)

The exported factory currently raises `NotImplementedError` and is reserved for a future streaming implementation. Use `xr.corr` or the rolling helpers in `cubedynamics.stats.correlation`/`stats.tails` today:

```python
import xarray as xr
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ppt_anom = (pipe(prism_cube) | v.anomaly(dim="time")).unwrap()["ppt"]
ndvi_z = pipe(cd.load_sentinel2_ndvi_cube(...)) | v.zscore(dim="time")

per_pixel_corr = xr.corr(ndvi_z, ppt_anom, dim="time")
```

### `show_cube_lexcube(**kwargs)`

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    start="2000-01-01",
    end="2020-12-31",
    variable="pr",
)

pipe(cube) | v.month_filter([6, 7, 8]) | v.show_cube_lexcube(cmap="RdBu_r")
```

`show_cube_lexcube` integrates [Lexcube](https://github.com/carbonplan/lexcube) for interactive `(time, y, x)` exploration. The verb displays the widget as a side-effect and returns the original cube so the pipeline can keep flowing. The helper also exists as `cubedynamics.show_cube_lexcube(cube, **kwargs)` for non-pipe contexts.

## Example: chaining a streamed cube

Define a simple bounding box and stream gridMET data directly into the pipe:

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    start="2000-01-01",
    end="2020-12-31",
    variable="pr",
    freq="MS",
    chunks={"time": 120},
)

pipe(cube) | v.month_filter([6, 7, 8]) | v.variance(dim="time")
```

The streamed cube already carries a datetime `time` coordinate so verbs such as `month_filter` and `variance` work without any
extra preparation.

## How Pipe.unwrap works

`Pipe.unwrap()` simply returns the wrapped `xarray` object after the final verb. It does not copy data; it only exposes the last computed value. Because `Pipe` implements `_repr_html_`/`__repr__`, notebooks display the inner object automatically so `.unwrap()` is only necessary when you need the DataArray/Dataset immediately (e.g., assigning to a variable mid-cell).

## Define your own verbs

Verbs follow a small factory pattern: accept configuration parameters now, return a callable that receives the cube later.

```python
def my_custom_op(param):
    def _inner(da):
        # operate on da (xarray DataArray/Dataset)
        return da
    return _inner

from cubedynamics import pipe

result = pipe(cube) | my_custom_op(param=42)
```

Register your verb in your own module or import it in your notebook, then use it alongside the built-in operations.
