# Sentinel-2 NDVI z-score cube

This guide combines the Sentinel-2 NDVI z-score recipe with Lexcube visualization tips.

## Story

We request Sentinel-2 Level-2A data (via CubeDynamics loaders or `cubo`), compute NDVI, standardize the time axis with z-scores, and preview the result in Lexcube. Z-scores are useful for highlighting vegetation departures from normal conditions because they normalize for per-pixel mean and variance.

## Load the cube

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v

ndvi = cd.load_sentinel2_ndvi_cube(
    lat=40.0,
    lon=-105.25,
    start="2018-01-01",
    end="2020-12-31",
)

ndvi_z = pipe(ndvi) | v.zscore(dim="time")
```

Need raw reflectance instead? Call `cd.load_sentinel2_ndvi_cube(...)` (shown above) to get NDVI in the physical range `[-1, 1]` and optionally request the underlying B04/B08 stack with `return_raw=True`.

Prefer to stream via [`cubo`](https://github.com/carbonplan/cubo)? Use the original recipe snippet:

```python
import cubo

from cubedynamics import pipe, verbs as v

s2 = cubo.create(
    lat=43.89,
    lon=-102.18,
    collection="sentinel-2-l2a",
    bands=["B04", "B08"],
    start_date="2023-06-01",
    end_date="2024-09-30",
    edge_size=512,
    resolution=10,
    query={"eo:cloud_cover": {"lt": 40}},
)

ndvi_z = (
    pipe(s2)
    | v.ndvi_from_s2(nir_band="B08", red_band="B04")
    | v.zscore(dim="time")
).unwrap()
```

## Lexcube preview

```python
pipe(ndvi_z) | v.show_cube_lexcube(title="Sentinel-2 NDVI z-score", cmap="RdBu_r")
```

Lexcube only renders in live notebooks, so include screenshots or Binder links when sharing results.

## Optional coarsening + QA plot

```python
from cubedynamics.utils.chunking import coarsen_and_stride
from cubedynamics.viz.qa_plots import plot_median_over_space

ndvi_z_ds = coarsen_and_stride(
    ndvi_z,
    coarsen_factor=4,
    time_stride=2,
)

ndvi_z_clip = ndvi_z_ds.clip(-3, 3)
pipe(ndvi_z_clip) | v.show_cube_lexcube(
    title="Sentinel-2 NDVI z-scores (coarsened)",
    cmap="RdBu_r",
    vmin=-3,
    vmax=3,
)

ax = plot_median_over_space(
    ndvi_z_ds,
    ylabel="Median NDVI z-score",
    title="Median NDVI z-score over time",
)
```

## Related examples

- [PRISM JJA variance](prism_jja_variance.md)
- [Climate–NDVI correlation cube](climate_ndvi_correlation.md)
