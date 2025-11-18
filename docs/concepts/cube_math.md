# Climate cube math primitives

The `cubedynamics` package collects reusable *cube math* primitives that
operate directly on `xarray` DataArrays without breaking their labeled
dimensions. These primitives fall into two main groups: temporal operators and
spatial operators.

## Temporal operators

Temporal functions act along the time axis (default name `time`). They share a
common design: respect existing coordinates, work lazily with Dask arrays, and
return cubes whose metadata explains the transformation.

### `temporal_anomaly`

Compute departures from a baseline mean along a time-like dimension. By default
it uses the entire time span, but you can also pass a slice for a specific
baseline period.

```python
from cubedynamics.stats.anomalies import temporal_anomaly

anoms = temporal_anomaly(ndvi_z, dim="time")
seasonal_anoms = temporal_anomaly(
    ndvi_z,
    dim="time",
    baseline_slice=slice("2018-01-01", "2019-12-31"),
)
```

### `temporal_difference`

Take lagged differences, e.g., month-over-month change. NaNs are inserted for
the first `lag` entries automatically via `xarray.shift`.

```python
from cubedynamics.stats.anomalies import temporal_difference

diffs = temporal_difference(temp_cube, lag=1, dim="time")
annual_diffs = temporal_difference(temp_cube, lag=12, dim="time")
```

### `rolling_mean`

A thin wrapper over `xarray.DataArray.rolling(...).mean()` that defaults to
`min_periods=window` and preserves long-name metadata.

```python
from cubedynamics.stats.anomalies import rolling_mean

smooth = rolling_mean(diffs, window=3, dim="time")
```

### `zscore_over_time`

Standardize each pixel over time by subtracting its mean and dividing by its
standard deviation, with `STD_EPS` guarding against division by near-zero.

## Spatial operators

Spatial functions assume `y`/`x` axes (overridable via arguments). They never
collapse time or variable dimensions, so the output stays compatible with other
cube math utilities.

### `spatial_coarsen_mean`

Aggregate over non-overlapping blocks of size `factor_y` × `factor_x` with
`boundary="trim"` so partial tiles are dropped.

```python
from cubedynamics.stats.spatial import spatial_coarsen_mean

# Coarsen from 1 km to 4 km resolution by averaging 4×4 neighborhoods
coarse = spatial_coarsen_mean(temp_cube, factor_y=4, factor_x=4)
```

### `spatial_smooth_mean`

Apply a centered rolling mean (boxcar) kernel over both spatial axes. The
`kernel_size` must be an odd integer.

```python
from cubedynamics.stats.spatial import spatial_smooth_mean

smooth_map = spatial_smooth_mean(temp_cube.isel(time=0), kernel_size=3)
```

### `mask_by_threshold`

Create boolean masks for threshold-based filtering. The mask carries through the
input metadata and can be used with `xr.where` or `.where()`.

```python
from cubedynamics.stats.spatial import mask_by_threshold

# Keep only pixels warmer than 20 °C
warm_mask = mask_by_threshold(temp_cube, threshold=20.0, direction=">")
```

## Putting it together

By composing these primitives we can:

1. Load a cube.
2. Apply temporal standardization (z-scores or anomalies).
3. Reduce spatial resolution or mask invalid data.
4. Derive rolling synchrony metrics.
5. Visualize the resulting cubes via Lexcube and QA plots.

The abstraction lets you swap in other backends (e.g., GRIDMET temperature
cubes) while keeping the same math pipeline.
