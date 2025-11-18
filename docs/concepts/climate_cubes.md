# What is a climate cube?

A **climate cube** is an `xarray.DataArray` or `xarray.Dataset` whose data are
organized along shared space-time axes. The most common arrangement in this
project is `(time, y, x)` for single-band cubes or `(time, y, x, band)` for
multi-band collections. Each pixel stores the value of an environmental
variable (e.g., reflectance, temperature, precipitation) measured at a given
location `(y, x)` and instant `time`.

## Why cubes?

Satellite constellations (Sentinel-2, Landsat), gridded climate products
(GRIDMET, PRISM), and model reanalyses are all naturally expressed as climate
cubes because their data are already gridded over regular spatio-temporal
coordinates. By sticking with `xarray`, we get labeled dimensions, lazy loading
(with `dask`), and robust metadata handling.

This package focuses on *streaming* cubes rather than requiring local
downloads. Utilities such as `cubedynamics.data.sentinel2.load_s2_cube`
wrap remote APIs (e.g., Cubo) so that users can request an area/time window and
immediately operate on the returned `xarray` cube inside notebooks or scripts.

## Cube processing layers

The rest of the documentation walks through the primary layers of the
`cubedynamics` workflow:

1. **Data layer** – load space-time cubes (`load_s2_cube`).
2. **Indices & anomalies layer** – derive vegetation indices and z-scores
   (`compute_ndvi_from_s2`, `zscore_over_time`).
3. **Synchrony layer** – measure rolling correlation and tail dependence versus
   a reference pixel (`rolling_corr_vs_center`, `rolling_tail_dep_vs_center`).
4. **Visualization layer** – explore cubes interactively with the Lexcube
   widget (`show_cube_lexcube`) and QA plots (`plot_median_over_space`).

## Conceptual cube example

```python
import xarray as xr

# Generic climate cube shape
# time: T time steps, y: rows, x: columns
cube = xr.DataArray(
    data,  # shape (T, Y, X)
    coords={"time": time_coords, "y": y_coords, "x": x_coords},
    dims=("time", "y", "x"),
    name="my_variable",
)
```

Once data are in this form, every operation in `cubedynamics` simply
composes transformations on the cube without ever breaking the labeled axes.
