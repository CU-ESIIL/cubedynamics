# Sentinel-2 NDVI z-score cube + Lexcube

This recipe walks through an end-to-end workflow to produce NDVI z-score cubes
from Sentinel-2 Level-2A data and visualize the results with the Lexcube
widget. It is the vegetation counterpart to the [PRISM](prism_variance_cube.md)
and [gridMET](gridmet_variance_cube.md) variance examples so that every cube can
be correlated at the pixel level.

1. **Load Sentinel-2** – `load_s2_cube` requests a chip centered on your
   latitude/longitude, with configurable time range, edge length, spatial
   resolution, and maximum cloud fraction.
2. **Compute NDVI + z-scores via the verbs namespace** – chain
   `v.ndvi_from_s2()` and `v.zscore(dim="time")` inside a pipe for clear,
   reusable code.
3. **Optional coarsening/striding** – `coarsen_and_stride` reduces spatial and
   temporal resolution to make exploratory visualization faster.
4. **Lexcube visualization** – `show_cube_lexcube` renders the cube in an
   interactive widget, and `plot_median_over_space` creates a QA time series of
   the spatial median.

Prefer to stream through [`cubo`](https://github.com/carbonplan/cubo) instead of
`cd.load_s2_cube`? Drop the snippet below at the top of the notebook and pipe
the resulting `s2` cube through the same verbs:

```python
from __future__ import annotations

import warnings

import cubo

from cubedynamics import pipe, verbs as v

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
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

```python
import cubedynamics as cd
from cubedynamics import pipe, verbs as v
from cubedynamics.utils.chunking import coarsen_and_stride
from cubedynamics.viz.qa_plots import plot_median_over_space

# 1. Load Sentinel-2 cube
s2 = cd.load_s2_cube(
    lat=43.89,
    lon=-102.18,
    start="2023-06-01",
    end="2023-09-30",
    edge_size=512,
    resolution=10,
    cloud_lt=40,
)

# 2. Pipe: reflectance -> NDVI -> z-score
ndvi_z = (
    pipe(s2)
    | v.ndvi_from_s2()
    | v.zscore(dim="time")
)

# 3. Optional: coarsen spatially and subsample in time
ndvi_z_ds = coarsen_and_stride(
    ndvi_z,
    coarsen_factor=4,
    time_stride=2,
)

# 4. Lexcube visualization (pipe verb + helper)
ndvi_z_clip = ndvi_z_ds.clip(-3, 3)
pipe(ndvi_z_clip) | v.show_cube_lexcube(
    title="Sentinel-2 NDVI z-scores (coarsened)",
    cmap="RdBu_r",
    vmin=-3,
    vmax=3,
)

# Outside of a pipe you can call the helper directly
cd.show_cube_lexcube(ndvi_z_clip)

# 5. QA plot of median z-score over space
ax = plot_median_over_space(
    ndvi_z_ds,
    ylabel="Median NDVI z-score",
    title="Median NDVI z-score over time",
)
# In a notebook: display(ax.figure)
```

The same pattern works for other sensors as long as you can derive the target
index cube and feed it into the anomaly functions. Correlate NDVI anomalies with
PRISM or gridMET cubes via `v.correlation_cube` to uncover joint climate and
vegetation behavior.
