# Climate cubes

Climate cubes are the core abstraction in CubeDynamics. They are `xarray`
objects with shared `(time, y, x)` axes (and optional `band` or `variable`
dimensions) produced by the streaming loaders.

## Creating cubes

```python
import cubedynamics as cd

cube = cd.load_gridmet_cube(
    lat=40.05,
    lon=-105.275,
    variable="pr",
    start="2000-01-01",
    end="2020-12-31",
    freq="MS",
    chunks={"time": 120},
)
print(cube.dims)
```

The loader harmonizes CRS, attaches metadata, and returns a lazily-evaluated
`xarray.Dataset`. Other loaders follow the same interface (`cd.load_prism_cube`,
`cd.load_sentinel2_cube`, `cd.load_sentinel2_ndvi_cube`,
`cd.load_sentinel2_ndvi_zscore_cube`), using the keyword-only AOI grammar:
pick a `lat`/`lon` point, a `[min_lon, min_lat, max_lon, max_lat]` bounding box,
or a GeoJSON Feature/FeatureCollection via `aoi_geojson` (for loaders that
support it).

## Derived diagnostics

Once a cube exists, run statistics directly on the labeled dimensions:

```python
from cubedynamics import pipe, verbs as v

ndvi_z = pipe(ndvi_cube) | v.zscore(dim="time")
var_cube = pipe(cube) | v.variance(dim="time")
```

Every helper keeps the input axes intact so that downstream visualizations and
exports can consume the resulting lexcube without regridding.

## Exporting cubes

`cubedynamics` exposes helpers like `cube.to_netcdf(...)`, `cube.to_zarr(...)`,
and visualization verbs such as `v.show_cube_lexcube` for interactive dashboards.
Large analyses rely on chunked writes through `dask` so the same scripts run in
cloud environments.
