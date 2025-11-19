# Operations – statistic verbs

**In plain English:**  
Statistic verbs summarize or standardize a cube along one dimension.
They build on transforms to answer questions like “how variable is summer rainfall?”

**You will learn:**  
- How to compute means, variances, and z-scores
- How to control dimensions you keep or drop
- Where the deeper technical notes live

## What this is

These functions live in `cubedynamics.ops.stats` and are also available under `cubedynamics.verbs`.
They expect an `xarray` cube and return an object with the same labeled coordinates unless you choose to drop dimensions.

## Why it matters

Summaries like variance or z-score highlight unusual events and trends.
Keeping the cube structure intact makes it easy to compare climate and vegetation or to hand off results to visualization tools.

## How to use it

### `mean(dim="time", keep_dim=True)`
Computes the average along a dimension.

```python
from cubedynamics import pipe, verbs as v

avg = pipe(cube) | v.mean(dim="time", keep_dim=True)
```
Setting `keep_dim=True` leaves the dimension in place with length 1, which helps when you want to broadcast results later.

### `variance(dim="time", keep_dim=True)`
Measures spread along a dimension.

```python
var = pipe(cube) | v.variance(dim="time", keep_dim=True)
```
Use this to see how much a season or band varies over time.

### `zscore(dim="time", std_eps=1e-4)`
Standardizes values by subtracting the mean and dividing by the standard deviation.

```python
z = pipe(cube) | v.zscore(dim="time")
```
This returns unitless scores that show how unusual each timestep is relative to its own history.

---

## Original Reference (kept for context)
# Operations Reference – Stats

Statistic verbs summarize cubes along dimensions or compare axes. They live in `cubedynamics.ops.stats` and are re-exported via `cubedynamics.verbs`. Examples assume `from cubedynamics import pipe, verbs as v` and a `cube` variable bound to an `xarray` object.

## `mean(dim="time", keep_dim=True)`

Compute the mean along a dimension.

```python
result = pipe(cube) | v.mean(dim="time", keep_dim=True)
```

- **Parameters**
  - `dim`: dimension to summarize.
  - `keep_dim`: retain the dimension as length 1 (default) or drop it entirely.

## `variance(dim="time", keep_dim=True)`

Compute the variance along a dimension.

```python
result = pipe(cube) | v.variance(dim="time", keep_dim=True)
```

- **Parameters**
  - `dim`: dimension to collapse.
  - `keep_dim`: retain the dimension as length 1 (default) or drop it entirely.
- **Returns**: variance cube matching the input layout when `keep_dim=True`.

## `zscore(dim="time", std_eps=1e-4)`

Standardize each pixel/voxel along a dimension by subtracting the mean and dividing by the standard deviation.

```python
result = pipe(cube) | v.zscore(dim="time")
```

- **Parameters**
  - `dim`: dimension to standardize along.
  - `std_eps`: mask threshold to avoid dividing by values with near-zero spread.
- **Returns**: anomaly cube whose values are unitless z-scores per pixel. The verb always preserves the original cube shape.

## `correlation_cube` (planned)

The exported factory currently raises `NotImplementedError` and is reserved for a future streaming implementation.

- **Intended behavior**: compute rolling or full-period correlations between named data variables or coordinates, returning an `xarray` cube with correlation coefficients.
- **Alternatives today**: use `xr.corr` for per-pixel correlations or the rolling helpers in `cubedynamics.stats.correlation`/`stats.tails`.

Combine these stats with transforms and IO verbs to produce complete analyses.
