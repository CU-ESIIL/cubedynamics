# Climate cubes

Climate cubes are the core abstraction in CubeDynamics. They are `xarray`
objects with shared `(time, y, x)` axes (and optional `band` or `variable`
dimensions) produced by the streaming loaders.

## Creating cubes

```python
from cubedynamics import stream_gridmet_to_cube

cube = stream_gridmet_to_cube(
    aoi_geojson,
    variable="tmmx",
    dates=("2010-01-01", "2020-12-31"),
)
print(cube.dims)
```

The loader harmonizes CRS, attaches metadata, and returns a lazily-evaluated
`xarray.Dataset`. Other loaders follow the same interface (`stream_prism_to_cube`,
`stream_sentinel2_to_cube`).

## Derived diagnostics

Once a cube exists, run statistics directly on the labeled dimensions:

```python
from cubedynamics.stats.anomalies import zscore_over_time
from cubedynamics.lexcubes.variance import variance_cube

ndvi_z = zscore_over_time(ndvi_cube, dim="time")
var_cube = variance_cube(cube, dim="time")
```

Every helper keeps the input axes intact so that downstream visualizations and
exports can consume the resulting lexcube without regridding.

## Exporting cubes

`cubedynamics` exposes helpers like `cube.to_netcdf(...)`, `cube.to_zarr(...)`,
or `lexcube_to_dataset(...)` to persist results and integrate with dashboards.
Large analyses rely on chunked writes through `dask` so the same scripts run in
cloud environments.
